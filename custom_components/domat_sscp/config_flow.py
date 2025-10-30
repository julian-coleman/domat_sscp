"""Config flow for the Domat SSCP integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_PORT,
    #    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .sscp_connection import sscp_connection
from .sscp_const import (
    CONF_CONNECTION_NAME,
    CONF_SSCP_ADDRESS,
    #    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSCP_ADDRESS,
    DEFAULT_SSCP_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

_PORT_SELECTOR = vol.All(
    selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1, max=65535, mode=selector.NumberSelectorMode.BOX
        ),
    ),
    vol.Coerce(int),
)
_ADDR_SELECTOR = vol.All(
    selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1, max=255, mode=selector.NumberSelectorMode.BOX
        ),
    ),
    vol.Coerce(int),
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate that the user input allows us to connect using the values provided by the user."""

    try:
        conn = sscp_connection(
            name=data[CONF_CONNECTION_NAME],
            ip_address=data[CONF_IP_ADDRESS],
            port=data[CONF_PORT],
            user_name=data[CONF_USERNAME],
            password=data[CONF_PASSWORD],
            sscp_address=data[CONF_SSCP_ADDRESS],
        )
    except ValueError as error:
        _LOGGER.error("Could not create a connection object")
        raise InvalidAuth from error

    try:
        await conn.login()
        if conn.socket is None:
            _LOGGER.debug("Login failed")
            raise InvalidAuth
    except TimeoutError:
        _LOGGER.debug("Login timeout")
        raise InvalidAuth from None
    except (ValueError, OSError):
        _LOGGER.debug("Login connection error")
        raise CannotConnect from None

    try:
        await conn.get_info()
        serial = conn.serial
    except TimeoutError:
        _LOGGER.debug("Info timeout")
        raise Timeout from None
    except (ValueError, OSError):
        _LOGGER.debug("Info failed")
        raise CannotConnect from None
    if serial is None:
        _LOGGER.error("No serial number for %s", data[CONF_CONNECTION_NAME])
        serial = CONF_USERNAME + "-" + CONF_SSCP_ADDRESS
    _LOGGER.info("Using unique ID: %s", serial)

    await conn.logout()

    # Return info that we want to store in the config entry.
    return {"title": data[CONF_CONNECTION_NAME], "serial": serial}


class DomatSSCPConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Domat SSCP."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        user_schema = vol.Schema(
            {
                vol.Required(CONF_CONNECTION_NAME): str,
                vol.Required(CONF_IP_ADDRESS): str,
                vol.Required(CONF_PORT, default=DEFAULT_SSCP_PORT): _PORT_SELECTOR,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(
                    CONF_SSCP_ADDRESS, default=DEFAULT_SSCP_ADDRESS
                ): _ADDR_SELECTOR,
                # vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }
        )
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Timeout:
                errors["base"] = "timeout_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(str(info["serial"]))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=user_schema, errors=errors
        )

    #    async def async_step_reconfigure(
    #        self, user_input: dict[str, Any] | None = None
    #    ) -> ConfigFlowResult:
    #        """Handle reconfiguration."""
    #        return await self.async_step_user(user_input)
    #                if self.source == SOURCE_RECONFIGURE:

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of an existing entry."""
        entry = self._get_reconfigure_entry()
        reconfigure_schema = vol.Schema(
            {
                vol.Required(
                    CONF_CONNECTION_NAME, default=entry.data[CONF_CONNECTION_NAME]
                ): str,
                vol.Required(CONF_IP_ADDRESS, default=entry.data[CONF_IP_ADDRESS]): str,
                vol.Required(CONF_PORT, default=entry.data[CONF_PORT]): _PORT_SELECTOR,
                vol.Required(CONF_USERNAME, default=entry.data[CONF_USERNAME]): str,
                vol.Required(CONF_PASSWORD, default=entry.data[CONF_PASSWORD]): str,
                vol.Required(
                    CONF_SSCP_ADDRESS, default=entry.data[CONF_SSCP_ADDRESS]
                ): _ADDR_SELECTOR,
                # vol.Optional(CONF_SCAN_INTERVAL, default=entry.data[CONF_SCAN_INTERVAL]): int,
            }
        )
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug("Reconfigure - old data: %s", entry.data)
            _LOGGER.debug("Reconfigure - new data: %s", user_input)
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Timeout:
                errors["base"] = "timeout_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(str(info["serial"]))
                self._abort_if_unique_id_mismatch(reason="wrong_plc")
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                )

        return self.async_show_form(
            step_id="reconfigure", data_schema=reconfigure_schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the server."""


class Timeout(HomeAssistantError):
    """Error to indicate we timed out whilst connecting to the server."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is authentication is invalid."""
