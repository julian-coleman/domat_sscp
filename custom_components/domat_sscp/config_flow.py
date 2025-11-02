"""Config flow for the Domat SSCP integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    #    OptionsFlowWithReload,
)
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_PORT,
    #    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import section
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_CONNECTION_NAME,
    CONF_SSCP_ADDRESS,
    #    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSCP_ADDRESS,
    DEFAULT_SSCP_PORT,
    DOMAIN,
    OPT_CALORIMETER_COLD,
    OPT_CALORIMETER_HOT,
    OPT_CO2,
    OPT_DESCRIPTION,
    OPT_HUMIDITY,
    OPT_MAXIMUM,
    OPT_MINIMUM,
    OPT_METER_ELECTRICITY,
    OPT_TEMPERATURE,
    OPT_UID,
    OPT_VENTILATOR_IN,
    OPT_VENTILATOR_OUT,
    OPT_VENTILATOR_ERROR,
    OPT_VENTILATOR_FLOW,
    OPT_VENTILATOR_FLOW_MINIMUM,
    OPT_VENTILATOR_FLOW_MAXIMUM,
    OPT_WATER_COLD,
    OPT_WATER_HOT,
)
from .sscp_connection import sscp_connection

_LOGGER = logging.getLogger(__name__)

# Config flow schemas
_PORT_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)
_ADDR_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=1, max=255, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)

# Options flow schemas
_DEVICE_MENU = ["temp_hum", "energy", "air"]


def get_user_schema(
    input_data: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return a config flow schema with defaults based on the step and user input."""

    # Fill in defaults from initial defaults or input
    if input_data is None:
        default_connection_name = ""
        default_ip_address = ""
        default_port = DEFAULT_SSCP_PORT
        default_username = ""
        default_password = ""
        default_sscp_address = DEFAULT_SSCP_ADDRESS
    else:
        default_connection_name = input_data.get(CONF_CONNECTION_NAME, "")
        default_ip_address = input_data.get(CONF_IP_ADDRESS, "")
        default_port = input_data.get(CONF_PORT, DEFAULT_SSCP_PORT)
        default_username = input_data.get(CONF_USERNAME, "")
        default_password = input_data.get(CONF_PASSWORD, "")
        default_sscp_address = input_data.get(CONF_SSCP_ADDRESS, DEFAULT_SSCP_ADDRESS)
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


def get_temp_hum_schema(
    input_data: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return a temperature/humidity flow schema with defaults based on the user input."""

    # Fill in defaults from input or initial defaults
    if input_data is None:
        default_description = ""
        default_temperature_uid = 0
        default_humidity_uid = 0
    else:
        default_description = input_data.get(OPT_DESCRIPTION, "")
        default_temperature_uid = 0
        temperature = input_data.get(OPT_TEMPERATURE, None)
        if temperature is not None:
            default_temperature_uid = temperature.get(OPT_UID, default_temperature_uid)
        default_humidity_uid = 0
        humidity = input_data.get(OPT_HUMIDITY, None)
        if humidity is not None:
            default_humidity_uid = humidity.get(OPT_UID, default_humidity_uid)

    schema = vol.Schema(
        {
            vol.Required(OPT_DESCRIPTION, default=default_description): str,
            vol.Required(OPT_TEMPERATURE): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_UID, default=default_temperature_uid): int,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_HUMIDITY): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_UID, default=default_humidity_uid): int,
                    }
                ),
                {"collapsed": False},
            ),
        }
    )

    return schema


async def validate_config(data: dict[str, Any]) -> dict[str, Any]:
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
        # TODO Always add the username and SSCP address
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
        if self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            input_data = entry.data
            step = "reconfigure"
        else:  # user
            input_data = None
            step = "user"

        # Ask for input - initial defaults
        if user_input is None:
            return self.async_show_form(
                step_id=step,
                data_schema=get_user_schema(input_data),
                errors=errors,
            )

        # Validate the user input and create an entry
        try:
            info = await validate_config(user_input)
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
            if self.source == SOURCE_RECONFIGURE:
                await self.async_set_unique_id(str(info["serial"]))
                self._abort_if_unique_id_mismatch(reason="wrong_plc")
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                )
            # user
            await self.async_set_unique_id(str(info["serial"]))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=info["title"], data=user_input)

        # There was some validation problem - previous input as defaults
        return self.async_show_form(
            step_id=step,
            data_schema=get_user_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration."""
        return await self.async_step_user(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Setup an options flow for this handler."""
        return DomatSSCPOptionsFlowHandler(config_entry)


class DomatSSCPOptionsFlowHandler(OptionsFlow):
    """Handles options flow for Domat SSCP."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for Domat SSCP."""

        return self.async_show_menu(step_id="init", menu_options=_DEVICE_MENU)

    async def async_step_temp_hum(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for a temperature/humidity device."""

        errors: dict[str, str] = {}
        step = "temp_hum"
        schema = get_temp_hum_schema(user_input)

        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema, errors=errors)

        _LOGGER.error("User input: %s", user_input)
        temperature = user_input.get(OPT_TEMPERATURE, None)
        if temperature is not None:
            temperature_uid = temperature.get(OPT_UID, 0)
            if temperature_uid != 0:
                _LOGGER.error("Temperature: %s %s %s", temperature_uid, 4, 0)
        humidity = user_input.get(OPT_HUMIDITY, None)
        if humidity is not None:
            humidity_uid = humidity.get(OPT_UID, 0)
            if humidity_uid != 0:
                _LOGGER.error("Humidity: %s %s %s", humidity_uid, 4, 0)

        # Validate the user input and create an entry
#        try:
#            error_variables = await validate_variables(variables)
#        except CannotConnect:
#            errors["base"] = "cannot_connect"
#        except Timeout:
#            errors["base"] = "timeout_connect"
#        except InvalidAuth:
#            errors["base"] = "invalid_auth"
#        except Exception:
#            _LOGGER.exception("Unexpected exception")
#            errors["base"] = "unknown"
#        else:

        error_variables_string = str(temperature_uid)
        description_placeholders = {"variables": error_variables_string}
        errors["base"] = "variable_length"
        # return self.async_create_entry(data=user_input)

        # There was some validation problem - previous input as defaults
        return self.async_show_form(
            step_id=step,
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_energy(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for an energy usage device."""

        errors: dict[str, str] = {}
        step = "energy"
        schema = vol.Schema(
            {
                vol.Required(OPT_METER_ELECTRICITY): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(OPT_WATER_COLD): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(OPT_WATER_HOT): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(OPT_CALORIMETER_COLD): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(OPT_CALORIMETER_HOT): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                        }
                    ),
                    {"collapsed": False},
                ),
            }
        )

        if user_input is None:
            return self.async_show_form(
                step_id="energy", data_schema=schema, errors=errors
            )

        # Validate the user input and create an entry
        try:
            error_variables = await validate_variables(variables)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Timeout:
            errors["base"] = "timeout_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
#        else:

        # There was some validation problem - previous input as defaults
        return self.async_show_form(
            step_id=step,
            data_schema=schema,
            errors=errors,
        )

    async def async_step_air(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for an air recuperation device."""

        errors: dict[str, str] = {}
        step = "air"

        schema = vol.Schema(
            {
                vol.Required(OPT_VENTILATOR_IN): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(OPT_VENTILATOR_OUT): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(OPT_CO2): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(OPT_VENTILATOR_ERROR): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Optional(OPT_VENTILATOR_FLOW): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                            vol.Optional(
                                OPT_MINIMUM, default=OPT_VENTILATOR_FLOW_MINIMUM
                            ): int,
                            vol.Optional(
                                OPT_MAXIMUM, default=OPT_VENTILATOR_FLOW_MAXIMUM
                            ): int,
                        }
                    ),
                    {"collapsed": False},
                ),
            }
        )

        if user_input is None:
            return self.async_show_form(
                step_id="air", data_schema=schema, errors=errors
            )

        # Validate the user input and create an entry
        try:
            error_variables = await validate_variables(variables)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Timeout:
            errors["base"] = "timeout_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
#        else:

        # There was some validation problem - previous input as defaults
        return self.async_show_form(
            step_id=step,
            data_schema=schema,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the server."""


class Timeout(HomeAssistantError):
    """Error to indicate we timed out whilst connecting to the server."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is authentication is invalid."""
