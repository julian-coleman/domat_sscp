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


def get_user_schema(
    input: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return a schema with defaults based on the step and user input."""

    # Fill in defaults from initial defaults or input
    if input is None:
        default_connection_name = ""
        default_ip_address = ""
        default_port = DEFAULT_SSCP_PORT
        default_username = ""
        default_password = ""
        default_sscp_address = DEFAULT_SSCP_ADDRESS
    else:
        default_connection_name = input.get(CONF_CONNECTION_NAME, "")
        default_ip_address = input.get(CONF_IP_ADDRESS, "")
        default_port = input.get(CONF_PORT, DEFAULT_SSCP_PORT)
        default_username = input.get(CONF_USERNAME, "")
        default_password = input.get(CONF_PASSWORD, "")
        default_sscp_address = input.get(CONF_SSCP_ADDRESS, DEFAULT_SSCP_ADDRESS)
    return vol.Schema(
        {
            vol.Required(CONF_CONNECTION_NAME, default=default_connection_name): str,
            vol.Required(CONF_IP_ADDRESS, default=default_ip_address): str,
            vol.Required(CONF_PORT, default=default_port): _PORT_SELECTOR,
            vol.Required(CONF_USERNAME, default=default_username): str,
            vol.Required(CONF_PASSWORD, default=default_password): str,
            vol.Required(
                CONF_SSCP_ADDRESS, default=default_sscp_address
            ): _ADDR_SELECTOR,
            # vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
        }
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
        raise CannotConnect from error

    try:
        await conn.login()
        if conn.socket is None:
            _LOGGER.debug("Login failed")
            raise InvalidAuth from None
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
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Ask for input - initial defaults
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=get_user_schema(),
                errors=errors,
            )

        # Validate the user input and create an entry
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

        # There was some validation problem - previous input as defaults
        return self.async_show_form(
            step_id="user",
            data_schema=get_user_schema(input=user_input),
            errors=errors,
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
        errors: dict[str, str] = {}

        # Ask for input - initial defaults
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=get_user_schema(input=entry.data),
                errors=errors,
            )

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
            step_id="reconfigure",
            data_schema=get_user_schema(input=user_input),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the server."""


class Timeout(HomeAssistantError):
    """Error to indicate we timed out whilst connecting to the server."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is authentication is invalid."""
