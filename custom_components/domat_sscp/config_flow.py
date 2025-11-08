"""Config flow for the Domat SSCP integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
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
    CONF_SENSOR_TYPE,
    # TODO: support changing the scan interval via reconfigure (min value should what?)
    #    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_CONNECTION_NAME,
    CONF_SSCP_ADDRESS,
    # TODO: Change the scan interval and add a fast scan after changes
    #    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSCP_ADDRESS,
    DEFAULT_SSCP_PORT,
    DOMAIN,
    OPT_CALORIMETER_COLD,
    OPT_CALORIMETER_HOT,
    OPT_CO2,
    OPT_DEVICE,
    OPT_HUMIDITY,
    OPT_MAXIMUM,
    OPT_METER_ELECTRICITY,
    OPT_METER_WATER_COLD,
    OPT_METER_WATER_HOT,
    OPT_MINIMUM,
    # TODO: Add translated name and czech translations
    OPT_NAME,
    OPT_TEMPERATURE,
    OPT_UID,
    OPT_VENTILATION_ERROR,
    OPT_VENTILATION_FLOW,
    OPT_VENTILATION_FLOW_MAXIMUM,
    OPT_VENTILATION_FLOW_MINIMUM,
    OPT_VENTILATION_IN,
    OPT_VENTILATION_OUT,
)
from .coordinator import InvalidAuth
from .sscp_connection import sscp_connection
from .sscp_const import SSCP_ERRORS
from .sscp_variable import sscp_variable

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


class DomatSSCPConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Domat SSCP."""

    # Config flow version
    VERSION = 1
    MINOR_VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        coordinator = self.config_entry.coordinator
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
                data_schema=_get_user_schema(input_data),
                errors=errors,
            )

        # Validate the user input and create an entry
        try:
            info = await coordinator.validate_config(
                data=user_input,
                variables=None,
            )
        except TimeoutError:
            errors["base"] = "timeout_connect"
        except (ValueError, OSError):
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        else:
            # No exception, so either abort or return
            await self.async_set_unique_id(info["serial"])
            if self.source == SOURCE_RECONFIGURE:
                self._abort_if_unique_id_mismatch(reason="wrong_plc")
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                )
            # user
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=info["title"], data=user_input)

        # There was some validation problem - previous input as defaults
        return self.async_show_form(
            step_id=step,
            data_schema=_get_user_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration."""
        return await self.async_step_user(user_input)

    # TODO: reauth

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

        # Display a menu with step id's
        return self.async_show_menu(step_id="init", menu_options=_DEVICE_MENU)

    async def async_step_temp_hum(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for adding a temperature/humidity device."""

        data: dict[str, Any] = self.config_entry.options.copy()
        coordinator = self.config_entry.coordinator
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}
        variables: list[sscp_variable] = []
        step = "temp_hum"
        schema = _get_temp_hum_schema(user_input)

        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema, errors=errors)

        _LOGGER.error("Found coordinator: %s", coordinator)
        # Create variables list from user input
        # Our entity ID's are uid-length-offset of the variable
        _LOGGER.debug("User input: %s", user_input)
        temperature = user_input.get(OPT_TEMPERATURE)
        temperature_uid = temperature.get(OPT_UID)
        humidity = user_input.get(OPT_HUMIDITY)
        humidity_uid = humidity.get(OPT_UID)
        if temperature_uid != 0:
            variables.append(
                sscp_variable(uid=temperature_uid, offset=0, length=4, type=13)
            )
            temperature_entity_id = str(temperature_uid) + "-0-4"
        if humidity_uid != 0:
            variables.append(
                sscp_variable(uid=humidity_uid, offset=0, length=4, type=13)
            )
            humidity_entity_id = str(humidity_uid) + "-0-4"

        if len(variables) == 0:
            # No user variables
            errors["base"] = "variable_error"
            description_placeholders = {"error": "UID All Zero", "variables": "0"}
        else:
            err_info = self._check_exists(
                device_name=user_input.get(OPT_DEVICE),
                entity_ids={
                    temperature_entity_id: temperature_uid,
                    humidity_entity_id: humidity_uid,
                },
            )
            if "device" in err_info:
                errors["base"] = "variable_error"
                err_str = "Device Already Exists"
                description_placeholders = {
                    "error": err_str,
                    "variables": user_input.get(OPT_DEVICE),
                }
            elif len(err_info["variables"]) > 0:
                errors["base"] = "variable_error"
                err_str = "UID Already Exists"
                description_placeholders = {
                    "error": err_str,
                    "variables": err_info["variables"],
                }

        if "base" not in errors:
            # Validate the user input and create an entry
            try:
                info = await coordinator.validate_config(
                    data=self.config_entry.data,
                    variables=variables,
                )
            except TimeoutError:
                errors["base"] = "timeout_connect"
            except (ValueError, OSError):
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            else:
                # No exception, so either generate an error or return
                if info["error_code"] != 0:
                    errors["base"] = "variable_error"
                    err_str = SSCP_ERRORS.get(info["error_code"], "unknown")
                    description_placeholders = {
                        "error": err_str,
                        "variables": info["error_variables"],
                    }
                else:
                    data.update(
                        {
                            temperature_entity_id: {
                                # "name": temperature.get(OPT_NAME),
                                "uid": temperature_uid,
                                "offset": 0,
                                "length": 4,
                                "type": 13,
                                "class": SensorDeviceClass.TEMPERATURE,
                                "unit": UnitOfTemperature.CELSIUS,
                                "precision": 1,
                                "entity": CONF_SENSOR_TYPE,
                                "device": user_input.get(OPT_DEVICE),
                            },
                            humidity_entity_id: {
                                # "name": humidity.get(OPT_NAME),
                                "uid": humidity_uid,
                                "offset": 0,
                                "length": 4,
                                "type": 13,
                                "class": SensorDeviceClass.HUMIDITY,
                                "unit": PERCENTAGE,
                                "precision": 1,
                                "entity": CONF_SENSOR_TYPE,
                                "device": user_input.get(OPT_DEVICE),
                            },
                        }
                    )
                    return self.async_create_entry(data=data)

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
        """Manage the options for adding an energy usage device."""

        data: dict[str, Any] = self.config_entry.options.copy()
        coordinator = self.config_entry.coordinator
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}
        variables: list[sscp_variable] = []
        entity_ids: dict[str, str] = {}
        step = "energy"
        schema = _get_energy_schema(user_input)

        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema, errors=errors)

        # Create variables and entities lists to check from user input
        # Our entity ID's are uid-length-offset of the variable
        _LOGGER.error("User input: %s", user_input)
        meter_electricity = user_input.get(OPT_METER_ELECTRICITY)
        meter_electricity_uid = meter_electricity.get(OPT_UID)
        meter_water_cold = user_input.get(OPT_METER_WATER_COLD)
        meter_water_cold_uid = meter_water_cold.get(OPT_UID)
        meter_water_hot = user_input.get(OPT_METER_WATER_HOT)
        meter_water_hot_uid = meter_water_hot.get(OPT_UID)
        calorimeter_hot = user_input.get(OPT_CALORIMETER_HOT)
        calorimeter_hot_uid = calorimeter_hot.get(OPT_UID)
        calorimeter_cold = user_input.get(OPT_CALORIMETER_COLD)
        calorimeter_cold_uid = calorimeter_cold.get(OPT_UID)
        if meter_electricity_uid != 0:
            variables.append(
                sscp_variable(uid=meter_electricity_uid, offset=0, length=4, type=13)
            )
            meter_electricity_entity_id = str(meter_electricity_uid) + "-0-4"
            entity_ids.update({meter_electricity_entity_id: meter_electricity_uid})
        if meter_water_cold_uid != 0:
            variables.append(
                sscp_variable(uid=meter_water_cold_uid, offset=0, length=4, type=13)
            )
            meter_water_cold_entity_id = str(meter_water_cold_uid) + "-0-4"
            entity_ids.update({meter_water_cold_entity_id: meter_water_cold_uid})
        if meter_water_hot_uid != 0:
            variables.append(
                sscp_variable(uid=meter_water_hot_uid, offset=0, length=4, type=13)
            )
            meter_water_hot_entity_id = str(meter_water_hot_uid) + "-0-4"
            entity_ids.update({meter_water_hot_entity_id: meter_water_hot_uid})
        if calorimeter_hot_uid != 0:
            variables.append(
                sscp_variable(uid=calorimeter_hot_uid, offset=0, length=4, type=13)
            )
            calorimeter_hot_entity_id = str(calorimeter_hot_uid) + "-0-4"
            entity_ids.update({calorimeter_hot_entity_id: calorimeter_hot_uid})
        if calorimeter_cold_uid != 0:
            variables.append(
                sscp_variable(uid=calorimeter_cold_uid, offset=0, length=4, type=13)
            )
            calorimeter_cold_entity_id = str(calorimeter_cold_uid) + "-0-4"
            entity_ids.update({calorimeter_cold_entity_id: calorimeter_cold_uid})

        if len(variables) == 0:
            # No user variables
            errors["base"] = "variable_error"
            description_placeholders = {"error": "UID All Zero", "variables": "0"}
        else:
            err_info = self._check_exists(device_name=None, entity_ids=entity_ids)
            if "device" in err_info:
                errors["base"] = "variable_error"
                err_str = "Device Already Exists"
                description_placeholders = {
                    "error": err_str,
                    "variables": user_input.get(OPT_DEVICE),
                }
            elif len(err_info["variables"]) > 0:
                errors["base"] = "variable_error"
                err_str = "UID Already Exists"
                description_placeholders = {
                    "error": err_str,
                    "variables": err_info["variables"],
                }

        if "base" not in errors:
            # Validate the user input and create an entry
            try:
                info = await coordinator.validate_config(
                    data=self.config_entry.data,
                    variables=variables,
                )
            except TimeoutError:
                errors["base"] = "timeout_connect"
            except (ValueError, OSError):
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            else:
                # No exception, so either generate an error or return
                if info["error_code"] != 0:
                    errors["base"] = "variable_error"
                    err_str = SSCP_ERRORS.get(info["error_code"], "unknown")
                    description_placeholders = {
                        "error": err_str,
                        "variables": info["error_variables"],
                    }
                else:
                    if meter_electricity_uid != 0:
                        data.update(
                            {
                                meter_electricity_entity_id: {
                                    "uid": meter_electricity_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.ENERGY,
                                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                                    "state": SensorStateClass.TOTAL_INCREASING,
                                    "precision": 1,
                                    "entity": CONF_SENSOR_TYPE,
                                    "device": meter_electricity.get(OPT_NAME),
                                },
                            }
                        )
                    if meter_water_cold_uid != 0:
                        data.update(
                            {
                                meter_water_cold_entity_id: {
                                    "uid": meter_water_cold_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.WATER,
                                    "unit": UnitOfVolume.CUBIC_METERS,
                                    "state": SensorStateClass.TOTAL_INCREASING,
                                    "precision": 1,
                                    "entity": CONF_SENSOR_TYPE,
                                    "device": meter_water_cold.get(OPT_NAME),
                                },
                            }
                        )
                    if meter_water_hot_uid != 0:
                        data.update(
                            {
                                meter_water_hot_entity_id: {
                                    "uid": meter_water_hot_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.WATER,
                                    "unit": UnitOfVolume.CUBIC_METERS,
                                    "state": SensorStateClass.TOTAL_INCREASING,
                                    "precision": 1,
                                    "entity": CONF_SENSOR_TYPE,
                                    "device": meter_water_hot.get(OPT_NAME),
                                },
                            }
                        )
                    if calorimeter_hot_uid != 0:
                        data.update(
                            {
                                calorimeter_hot_entity_id: {
                                    "uid": calorimeter_hot_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.ENERGY,
                                    "unit": UnitOfEnergy.GIGA_JOULE,
                                    "state": SensorStateClass.TOTAL_INCREASING,
                                    "precision": 1,
                                    "entity": CONF_SENSOR_TYPE,
                                    "device": calorimeter_hot.get(OPT_NAME),
                                },
                            }
                        )
                    if calorimeter_cold_uid != 0:
                        data.update(
                            {
                                calorimeter_cold_entity_id: {
                                    "uid": calorimeter_cold_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.ENERGY,
                                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                                    "state": SensorStateClass.TOTAL_INCREASING,
                                    "precision": 1,
                                    "entity": CONF_SENSOR_TYPE,
                                    "device": calorimeter_cold.get(OPT_NAME),
                                },
                            }
                        )
                    return self.async_create_entry(data=data)

        # There was some validation problem - previous input as defaults
        return self.async_show_form(
            step_id=step,
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_air(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for adding an air recuperation device."""

        # TODO: Clone temp_hum
        data: dict[str, Any] = self.config_entry.options.copy()
        coordinator = self.config_entry.coordinator
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}
        variables: list[sscp_variable] = []
        step = "air"
        schema = vol.Schema(
            {
                vol.Required(OPT_VENTILATION_IN): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(OPT_VENTILATION_OUT): section(
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
                vol.Required(OPT_VENTILATION_ERROR): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Optional(OPT_VENTILATION_FLOW): section(
                    vol.Schema(
                        {
                            vol.Optional(OPT_UID, default=0): int,
                            vol.Optional(
                                OPT_MINIMUM, default=OPT_VENTILATION_FLOW_MINIMUM
                            ): int,
                            vol.Optional(
                                OPT_MAXIMUM, default=OPT_VENTILATION_FLOW_MAXIMUM
                            ): int,
                        }
                    ),
                    {"collapsed": False},
                ),
            }
        )

        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema, errors=errors)

        # There was some validation problem - previous input as defaults
        return self.async_show_form(
            step_id=step,
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    def _check_exists(
        self, device_name: str | None, entity_ids: dict[str, str]
    ) -> dict[str, str]:
        """Check if entity already exists."""

        variables: str = ""
        for option in self.config_entry.options:
            if (
                device_name is not None
                and self.config_entry.options[option]["device"] == device_name
            ):
                return {"device": device_name}
        for entity_id, entity_uid in entity_ids.items():
            _LOGGER.debug("Check exists for %s (%s)", entity_id, entity_uid)
            if entity_id in self.config_entry.options:
                variables = variables + str(entity_uid) + " "
        return {"variables": variables}


# Helpers
def _get_user_schema(
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


def _get_temp_hum_schema(
    input_data: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return a temperature/humidity flow schema with defaults based on the user input."""

    # Fill in defaults from input or initial defaults
    if input_data is None:
        default_device = ""
        default_temperature_uid = default_humidity_uid = 0
        # default_temperature_name = "Temperature"
        # default_humidity_name = "Humidity"
    else:
        default_device = input_data.get(OPT_DEVICE, "")
        temperature = input_data.get(OPT_TEMPERATURE)
        default_temperature_uid = temperature.get(OPT_UID, 0)
        # default_temperature_name = temperature.get(OPT_NAME)
        humidity = input_data.get(OPT_HUMIDITY)
        default_humidity_uid = humidity.get(OPT_UID, 0)
        # default_humidity_name = humidity.get(OPT_NAME)
    return vol.Schema(
        {
            vol.Required(OPT_DEVICE, default=default_device): str,
            vol.Required(OPT_TEMPERATURE): section(
                vol.Schema(
                    {
                        # vol.Optional(OPT_NAME, default=default_temperature_name): str,
                        vol.Optional(OPT_UID, default=default_temperature_uid): int,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_HUMIDITY): section(
                vol.Schema(
                    {
                        # vol.Optional(OPT_NAME, default=default_humidity_name): str,
                        vol.Optional(OPT_UID, default=default_humidity_uid): int,
                    }
                ),
                {"collapsed": False},
            ),
        }
    )


def _get_energy_schema(
    input_data: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return an energy flow schema with defaults based on the user input."""

    # Fill in defaults from input or initial defaults
    # Order is the same as in the app
    default_meter_electricity_uid = 0
    default_meter_water_cold_uid = default_meter_water_hot_uid = 0
    default_calorimeter_hot_uid = default_calorimeter_cold_uid = 0
    default_meter_electricity_name = "Electricity Meter"
    default_meter_water_cold_name = "Cold Water Meter"
    default_meter_water_hot_name = "Hot Water Meter"
    default_calorimeter_hot_name = "Hot Calorimeter"
    default_calorimeter_cold_name = "Cold Calorimeter"
    if input_data is not None:
        meter_electricity = input_data.get(OPT_METER_ELECTRICITY)
        default_meter_electricity_uid = meter_electricity.get(
            OPT_UID, default_meter_electricity_uid
        )
        default_meter_electricity_name = meter_electricity.get(
            OPT_NAME, default_meter_electricity_name
        )
        meter_water_cold = input_data.get(OPT_METER_WATER_COLD)
        default_meter_water_cold_uid = meter_water_cold.get(
            OPT_UID, default_meter_water_cold_uid
        )
        default_meter_water_cold_name = meter_water_cold.get(
            OPT_NAME, default_meter_water_cold_name
        )
        meter_water_hot = input_data.get(OPT_METER_WATER_HOT)
        default_meter_water_hot_uid = meter_water_hot.get(
            OPT_UID, default_meter_water_hot_uid
        )
        default_meter_water_hot_name = meter_water_hot.get(
            OPT_NAME, default_meter_water_hot_name
        )
        calorimeter_hot = input_data.get(OPT_CALORIMETER_HOT)
        default_calorimeter_hot_uid = calorimeter_hot.get(
            OPT_UID, default_calorimeter_hot_uid
        )
        default_calorimeter_hot_name = calorimeter_hot.get(
            OPT_NAME, default_calorimeter_hot_name
        )
        calorimeter_cold = input_data.get(OPT_CALORIMETER_COLD)
        default_calorimeter_cold_uid = calorimeter_cold.get(
            OPT_UID, default_calorimeter_cold_uid
        )
        default_calorimeter_cold_name = calorimeter_cold.get(
            OPT_NAME, default_calorimeter_cold_name
        )

    return vol.Schema(
        {
            vol.Required(OPT_METER_ELECTRICITY): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_meter_electricity_name
                        ): str,
                        vol.Optional(
                            OPT_UID, default=default_meter_electricity_uid
                        ): int,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_METER_WATER_COLD): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_meter_water_cold_name
                        ): str,
                        vol.Optional(
                            OPT_UID, default=default_meter_water_cold_uid
                        ): int,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_METER_WATER_HOT): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_meter_water_hot_name
                        ): str,
                        vol.Optional(OPT_UID, default=default_meter_water_hot_uid): int,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_CALORIMETER_HOT): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_calorimeter_hot_name
                        ): str,
                        vol.Optional(OPT_UID, default=default_calorimeter_hot_uid): int,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_CALORIMETER_COLD): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_calorimeter_cold_name
                        ): str,
                        vol.Optional(
                            OPT_UID, default=default_calorimeter_cold_uid
                        ): int,
                    }
                ),
                {"collapsed": False},
            ),
        }
    )
