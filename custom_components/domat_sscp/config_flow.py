"""Config flow for the Domat SSCP integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.water_heater import WaterHeaterEntityFeature
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    #    OptionsFlowWithReload,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    PERCENTAGE,
    PRECISION_TENTHS,
    Platform,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    LanguageSelector,
    LanguageSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_CONNECTION_NAME,
    CONF_LANGUAGE,
    CONF_SSCP_ADDRESS,
    DEFAULT_FAST_COUNT,
    DEFAULT_FAST_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSCP_ADDRESS,
    DEFAULT_SSCP_PORT,
    DEFAULT_WRITE_RETRIES,
    DOMAIN,
    OPT_CALORIMETER_COLD,
    OPT_CALORIMETER_COLD_NAME_CS,
    OPT_CALORIMETER_COLD_NAME_EN,
    OPT_CALORIMETER_HOT,
    OPT_CALORIMETER_HOT_NAME_CS,
    OPT_CALORIMETER_HOT_NAME_EN,
    OPT_CO2_ACTUAL,
    OPT_CO2_ACTUAL_NAME_CS,
    OPT_CO2_ACTUAL_NAME_EN,
    OPT_CO2_TARGET,
    OPT_CO2_TARGET_NAME_CS,
    OPT_CO2_TARGET_NAME_EN,
    OPT_DEVICE,
    OPT_ENERGY_NAME_CS,
    OPT_ENERGY_NAME_EN,
    OPT_FAST_COUNT,
    OPT_FAST_INTERVAL,
    OPT_HUMIDITY,
    OPT_HUMIDITY_NAME_CS,
    OPT_HUMIDITY_NAME_EN,
    OPT_MAXIMUM,
    OPT_METER_ELECTRICITY,
    OPT_METER_ELECTRICITY_NAME_CS,
    OPT_METER_ELECTRICITY_NAME_EN,
    OPT_METER_WATER_COLD,
    OPT_METER_WATER_COLD_NAME_CS,
    OPT_METER_WATER_COLD_NAME_EN,
    OPT_METER_WATER_HOT,
    OPT_METER_WATER_HOT_NAME_CS,
    OPT_METER_WATER_HOT_NAME_EN,
    OPT_MINIMUM,
    OPT_NAME,
    OPT_POLLING,
    OPT_ROOM_CONTROLS_NAME_CS,
    OPT_ROOM_CONTROLS_NAME_EN,
    OPT_SCAN_INTERVAL,
    OPT_STEP,
    OPT_TEMPERATURE,
    OPT_TEMPERATURE_NAME_CS,
    OPT_TEMPERATURE_NAME_EN,
    OPT_TEMPERATURE_SETTING,
    OPT_TEMPERATURE_SETTING_MAXIMUM,
    OPT_TEMPERATURE_SETTING_MINIMUM,
    OPT_TEMPERATURE_SETTING_NAME_CS,
    OPT_TEMPERATURE_SETTING_NAME_EN,
    OPT_TEMPERATURE_SETTING_STEP,
    OPT_UID,
    OPT_VENTILATION_ERROR,
    OPT_VENTILATION_ERROR_NAME_CS,
    OPT_VENTILATION_ERROR_NAME_EN,
    OPT_VENTILATION_FILTER,
    OPT_VENTILATION_FILTER_NAME_CS,
    OPT_VENTILATION_FILTER_NAME_EN,
    OPT_VENTILATION_FLOW_MAXIMUM,
    OPT_VENTILATION_FLOW_MINIMUM,
    OPT_VENTILATION_FLOW_SETTING,
    OPT_VENTILATION_FLOW_SETTING_NAME_CS,
    OPT_VENTILATION_FLOW_SETTING_NAME_EN,
    OPT_VENTILATION_FLOW_TARGET,
    OPT_VENTILATION_FLOW_TARGET_NAME_CS,
    OPT_VENTILATION_FLOW_TARGET_NAME_EN,
    OPT_VENTILATION_IN,
    OPT_VENTILATION_IN_NAME_CS,
    OPT_VENTILATION_IN_NAME_EN,
    OPT_VENTILATION_NAME_CS,
    OPT_VENTILATION_NAME_EN,
    OPT_VENTILATION_OUT,
    OPT_VENTILATION_OUT_NAME_CS,
    OPT_VENTILATION_OUT_NAME_EN,
    OPT_VENTILATION_STATE,
    OPT_VENTILATION_STATE_NAME_CS,
    OPT_VENTILATION_STATE_NAME_EN,
    OPT_WRITE_RETRIES,
)
from .coordinator import DomatSSCPCoordinator
from .sscp_connection import sscp_connection
from .sscp_const import SSCP_ERRORS
from .sscp_variable import sscp_variable

_LOGGER = logging.getLogger(__name__)

# Config flow schemas

# Languages matching our translations
_LANG_SELECTOR = vol.All(
    LanguageSelector(LanguageSelectorConfig(languages=["en", "cs"]))
)

# Config flow
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
# Options flows schemas
_UID_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=0, max=0xFFFFFFFF, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)
_TEMPERATURE_SETTING_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(
            min=OPT_TEMPERATURE_SETTING_MINIMUM,
            max=OPT_TEMPERATURE_SETTING_MAXIMUM,
            mode=NumberSelectorMode.BOX,
        ),
    ),
    vol.Coerce(int),
)
_TEMPERATURE_SETTING_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(
            min=OPT_TEMPERATURE_SETTING_MINIMUM,
            max=OPT_TEMPERATURE_SETTING_MAXIMUM,
            mode=NumberSelectorMode.BOX,
        ),
    ),
    vol.Coerce(int),
)
_TARGET_STEP_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=0.1, max=1.0, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(float),
)
_SCAN_INTERVAL_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=15, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)
_FAST_INTERVAL_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=2, max=15, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)
_FAST_COUNT_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=1, max=10, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)
_WRITE_RETRIES_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=2, max=10, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)

# Options flow menu
_DEVICE_MENU = ["room", "energy", "air", "poll", "info"]


class DomatSSCPConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Domat SSCP."""

    # Config flow version
    VERSION = 1
    MINOR_VERSION = 3

    # TODO: Add a checkbox for InSady
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}
        if self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            coordinator: DomatSSCPCoordinator = entry.coordinator
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
            info = await _validate_config(
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
            await self.async_set_unique_id(info["unique_id"])
            if self.source == SOURCE_RECONFIGURE:
                coordinator.set_last_connect()
                # Don't abort on unique ID mismatch, in case the PLC has a new serial number
                # self._abort_if_unique_id_mismatch(reason="wrong_plc")
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

        # TODO: Use a different menu for InSady
        # Display a menu with step id's
        return self.async_show_menu(step_id="init", menu_options=_DEVICE_MENU)

    async def async_step_room(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for adding a temperature/humidity device."""

        data: dict[str, Any] = self.config_entry.options.copy()
        coordinator: DomatSSCPCoordinator = self.config_entry.coordinator
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}
        variables: list[sscp_variable] = []
        entity_ids: dict[str, str] = {}
        step = "room"
        lang=self.config_entry.data.get(CONF_LANGUAGE, "en")
        schema = _get_room_schema(lang, user_input)

        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema, errors=errors)

        # Create variables list from user input
        # Our entity ID's are uid-length-offset of the variable
        _LOGGER.debug("User input: %s", user_input)
        temperature = user_input.get(OPT_TEMPERATURE)
        temperature_uid = temperature.get(OPT_UID)
        humidity = user_input.get(OPT_HUMIDITY)
        humidity_uid = humidity.get(OPT_UID)
        temperature_setting = user_input.get(OPT_TEMPERATURE_SETTING)
        temperature_setting_uid = temperature_setting.get(OPT_UID)
        temperature_setting_max = temperature_setting.get(OPT_MAXIMUM)
        temperature_setting_min = temperature_setting.get(OPT_MINIMUM)
        temperature_setting_step = temperature_setting.get(OPT_STEP)
        if temperature_uid != 0:
            variables.append(
                sscp_variable(uid=temperature_uid, offset=0, length=4, type=13)
            )
            temperature_entity_id = str(temperature_uid) + "-0-4"
            entity_ids.update({temperature_entity_id: temperature_uid})
        if humidity_uid != 0:
            variables.append(
                sscp_variable(uid=humidity_uid, offset=0, length=4, type=13)
            )
            humidity_entity_id = str(humidity_uid) + "-0-4"
            entity_ids.update({humidity_entity_id: humidity_uid})
        if temperature_setting_uid != 0:
            variables.append(sscp_variable(uid=temperature_setting_uid, offset=0, length=4, type=13))
            temperature_setting_entity_id = str(temperature_setting_uid) + "-0-4"
            entity_ids.update({temperature_setting_entity_id: temperature_setting_uid})

        if len(variables) == 0:
            # No user variables
            errors["base"] = "variable_error"
            description_placeholders = {"error": "UID All Zero", "variables": "0"}
        else:
            err_info = self._check_exists(
                device_name=user_input.get(OPT_DEVICE), entity_ids=entity_ids
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
            coordinator.set_last_connect()
            try:
                info = await _validate_config(
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
                    if temperature_uid != 0:
                        data.update(
                            {
                                temperature_entity_id: {
                                    "name": temperature.get(OPT_NAME),
                                    "uid": temperature_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.TEMPERATURE,
                                    "unit": UnitOfTemperature.CELSIUS,
                                    "precision": 1,
                                    "entity": Platform.SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                },
                            }
                        )
                    if humidity_uid != 0:
                        data.update(
                            {
                                humidity_entity_id: {
                                    "name": humidity.get(OPT_NAME),
                                    "uid": humidity_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.HUMIDITY,
                                    "unit": PERCENTAGE,
                                    "precision": 1,
                                    "entity": Platform.SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                },
                            }
                        )
                    if temperature_setting_uid != 0:
                        data.update(
                            {
                                temperature_setting_entity_id: {
                                    "name": temperature_setting.get(OPT_NAME),
                                    "uid": temperature_setting_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "feature": WaterHeaterEntityFeature.TARGET_TEMPERATURE,
                                    "unit": UnitOfTemperature.CELSIUS,
                                    "precision": PRECISION_TENTHS,
                                    "max": temperature_setting_max,
                                    "min": temperature_setting_min,
                                    "step": temperature_setting_step,
                                    "entity": Platform.WATER_HEATER,
                                    "device": user_input.get(OPT_DEVICE),
                                    "icon": "mdi:thermometer-lines",
                                }
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
        lang=self.config_entry.data.get(CONF_LANGUAGE, "en")
        schema = _get_energy_schema(lang, user_input)

        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema, errors=errors)

        # Create variables and entities lists to check from user input
        # Our entity ID's are uid-length-offset of the variable
        _LOGGER.debug("User input: %s", user_input)
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
            coordinator.set_last_connect()
            try:
                info = await _validate_config(
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
                                    "name": meter_electricity.get(OPT_NAME),
                                    "uid": meter_electricity_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.ENERGY,
                                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                                    "state": SensorStateClass.TOTAL_INCREASING,
                                    "precision": 4,
                                    "entity": Platform.SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                },
                            }
                        )
                    if meter_water_cold_uid != 0:
                        data.update(
                            {
                                meter_water_cold_entity_id: {
                                    "name": meter_water_cold.get(OPT_NAME),
                                    "uid": meter_water_cold_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.WATER,
                                    "unit": UnitOfVolume.CUBIC_METERS,
                                    "state": SensorStateClass.TOTAL_INCREASING,
                                    "precision": 4,
                                    "entity": Platform.SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                },
                            }
                        )
                    if meter_water_hot_uid != 0:
                        data.update(
                            {
                                meter_water_hot_entity_id: {
                                    "name": meter_water_hot.get(OPT_NAME),
                                    "uid": meter_water_hot_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.WATER,
                                    "unit": UnitOfVolume.CUBIC_METERS,
                                    "state": SensorStateClass.TOTAL_INCREASING,
                                    "precision": 4,
                                    "entity": Platform.SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                },
                            }
                        )
                    if calorimeter_hot_uid != 0:
                        data.update(
                            {
                                calorimeter_hot_entity_id: {
                                    "name": calorimeter_hot.get(OPT_NAME),
                                    "uid": calorimeter_hot_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.ENERGY,
                                    "unit": UnitOfEnergy.GIGA_JOULE,
                                    "state": SensorStateClass.TOTAL_INCREASING,
                                    "precision": 4,
                                    "entity": Platform.SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                },
                            }
                        )
                    if calorimeter_cold_uid != 0:
                        data.update(
                            {
                                calorimeter_cold_entity_id: {
                                    "name": calorimeter_cold.get(OPT_NAME),
                                    "uid": calorimeter_cold_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.ENERGY,
                                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                                    "state": SensorStateClass.TOTAL_INCREASING,
                                    "precision": 4,
                                    "entity": Platform.SENSOR,
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

    async def async_step_air(  # noqa: C901
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for adding an air recuperation device."""

        data: dict[str, Any] = self.config_entry.options.copy()
        coordinator = self.config_entry.coordinator
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}
        variables: list[sscp_variable] = []
        entity_ids: dict[str, str] = {}
        step = "air"
        lang=self.config_entry.data.get(CONF_LANGUAGE, "en")
        schema = _get_air_schema(lang, user_input)

        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema, errors=errors)

        # Create variables list from user input
        # Our entity ID's are uid-length-offset of the variable
        _LOGGER.debug("User input: %s", user_input)
        ventilation_error = user_input.get(OPT_VENTILATION_ERROR)
        ventilation_error_uid = ventilation_error.get(OPT_UID)
        ventilation_filter = user_input.get(OPT_VENTILATION_FILTER)
        ventilation_filter_uid = ventilation_filter.get(OPT_UID)
        ventilation_state = user_input.get(OPT_VENTILATION_STATE)
        ventilation_state_uid = ventilation_state.get(OPT_UID)
        co2_target = user_input.get(OPT_CO2_TARGET)
        co2_target_uid = co2_target.get(OPT_UID)
        co2_actual = user_input.get(OPT_CO2_ACTUAL)
        co2_actual_uid = co2_actual.get(OPT_UID)
        ventilation_flow_target = user_input.get(OPT_VENTILATION_FLOW_TARGET)
        ventilation_flow_target_uid = ventilation_flow_target.get(OPT_UID)
        ventilation_in = user_input.get(OPT_VENTILATION_IN)
        ventilation_in_uid = ventilation_in.get(OPT_UID)
        ventilation_out = user_input.get(OPT_VENTILATION_OUT)
        ventilation_out_uid = ventilation_out.get(OPT_UID)
        ventilation_flow_setting = user_input.get(OPT_VENTILATION_FLOW_SETTING)
        ventilation_flow_setting_uid = ventilation_flow_setting.get(OPT_UID)
        if ventilation_error_uid != 0:
            variables.append(
                sscp_variable(uid=ventilation_error_uid, offset=0, length=1, type=0)
            )
            ventilation_error_entity_id = str(ventilation_error_uid) + "-0-1"
            entity_ids.update({ventilation_error_entity_id: ventilation_error_uid})
        if ventilation_filter_uid != 0:
            variables.append(
                sscp_variable(uid=ventilation_filter_uid, offset=0, length=1, type=0)
            )
            ventilation_filter_entity_id = str(ventilation_filter_uid) + "-0-1"
            entity_ids.update({ventilation_filter_entity_id: ventilation_filter_uid})
        if ventilation_state_uid != 0:
            variables.append(
                sscp_variable(uid=ventilation_state_uid, offset=0, length=1, type=0)
            )
            ventilation_state_entity_id = str(ventilation_state_uid) + "-0-1"
            entity_ids.update({ventilation_state_entity_id: ventilation_state_uid})
        if co2_target_uid != 0:
            variables.append(
                sscp_variable(uid=co2_target_uid, offset=0, length=4, type=13)
            )
            co2_target_entity_id = str(co2_target_uid) + "-0-4"
            entity_ids.update({co2_target_entity_id: co2_target_uid})
        if co2_actual_uid != 0:
            variables.append(
                sscp_variable(uid=co2_actual_uid, offset=0, length=2, type=2)
            )
            co2_actual_entity_id = str(co2_actual_uid) + "-0-2"
            entity_ids.update({co2_actual_entity_id: co2_actual_uid})
        if ventilation_flow_target_uid != 0:
            variables.append(
                sscp_variable(
                    uid=ventilation_flow_target_uid, offset=0, length=4, type=13
                )
            )
            ventilation_flow_target_entity_id = (
                str(ventilation_flow_target_uid) + "-0-4"
            )
            entity_ids.update(
                {ventilation_flow_target_entity_id: ventilation_flow_target_uid}
            )
        if ventilation_in_uid != 0:
            variables.append(
                sscp_variable(uid=ventilation_in_uid, offset=0, length=2, type=2)
            )
            ventilation_in_entity_id = str(ventilation_in_uid) + "-0-2"
            entity_ids.update({ventilation_in_entity_id: ventilation_in_uid})
        if ventilation_out_uid != 0:
            variables.append(
                sscp_variable(uid=ventilation_out_uid, offset=0, length=2, type=2)
            )
            ventilation_out_entity_id = str(ventilation_out_uid) + "-0-2"
            entity_ids.update({ventilation_out_entity_id: ventilation_out_uid})
        if ventilation_flow_setting_uid != 0:
            variables.append(
                sscp_variable(
                    uid=ventilation_flow_setting_uid, offset=0, length=4, type=13
                )
            )
            ventilation_flow_setting_entity_id = (
                str(ventilation_flow_setting_uid) + "-0-4"
            )
            entity_ids.update(
                {ventilation_flow_setting_entity_id: ventilation_flow_setting_uid}
            )

        if len(variables) == 0:
            # No user variables
            errors["base"] = "variable_error"
            description_placeholders = {"error": "UID All Zero", "variables": "0"}
        else:
            err_info = self._check_exists(
                device_name=user_input.get(OPT_DEVICE),
                entity_ids=entity_ids,
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
            coordinator.set_last_connect()
            try:
                info = await _validate_config(
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
                    if ventilation_error_uid != 0:
                        data.update(
                            {
                                ventilation_error_entity_id: {
                                    "name": ventilation_error.get(OPT_NAME),
                                    "uid": ventilation_error_uid,
                                    "offset": 0,
                                    "length": 1,
                                    "type": 0,
                                    "class": BinarySensorDeviceClass.PROBLEM,
                                    "on": 1,
                                    "off": 0,
                                    "entity": Platform.BINARY_SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                    "icon": "mdi:bell",
                                },
                            }
                        )
                    if ventilation_filter_uid != 0:
                        data.update(
                            {
                                ventilation_filter_entity_id: {
                                    "name": ventilation_filter.get(OPT_NAME),
                                    "uid": ventilation_filter_uid,
                                    "offset": 0,
                                    "length": 1,
                                    "type": 0,
                                    "class": BinarySensorDeviceClass.PROBLEM,
                                    "on": 1,
                                    "off": 0,
                                    "entity": Platform.BINARY_SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                    "icon": "mdi:wrench",
                                },
                            }
                        )
                    if ventilation_state_uid != 0:
                        data.update(
                            {
                                ventilation_state_entity_id: {
                                    "name": ventilation_state.get(OPT_NAME),
                                    "uid": ventilation_state_uid,
                                    "offset": 0,
                                    "length": 1,
                                    "type": 0,
                                    "class": BinarySensorDeviceClass.RUNNING,
                                    "on": 1,
                                    "off": 0,
                                    "entity": Platform.BINARY_SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                },
                            }
                        )
                    if co2_target_uid != 0:
                        data.update(
                            {
                                co2_target_entity_id: {
                                    "name": co2_target.get(OPT_NAME),
                                    "uid": co2_target_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.CO2,
                                    "unit": CONCENTRATION_PARTS_PER_MILLION,
                                    "precision": 0,
                                    "entity": Platform.SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                },
                            }
                        )
                    if co2_actual_uid != 0:
                        data.update(
                            {
                                co2_actual_entity_id: {
                                    "name": co2_actual.get(OPT_NAME),
                                    "uid": co2_actual_uid,
                                    "offset": 0,
                                    "length": 2,
                                    "type": 2,
                                    "class": SensorDeviceClass.CO2,
                                    "unit": CONCENTRATION_PARTS_PER_MILLION,
                                    "precision": 0,
                                    "entity": Platform.SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                },
                            }
                        )
                    if ventilation_flow_target_uid != 0:
                        data.update(
                            {
                                ventilation_flow_target_entity_id: {
                                    "name": ventilation_flow_target.get(OPT_NAME),
                                    "uid": ventilation_flow_target_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "class": SensorDeviceClass.VOLUME_FLOW_RATE,
                                    "unit": UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
                                    "precision": 0,
                                    "entity": Platform.SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                    "icon": "mdi:speedometer",
                                },
                            }
                        )
                    if ventilation_in_uid != 0:
                        data.update(
                            {
                                ventilation_in_entity_id: {
                                    "name": ventilation_in.get(OPT_NAME),
                                    "uid": ventilation_in_uid,
                                    "offset": 0,
                                    "length": 2,
                                    "type": 2,
                                    "unit": PERCENTAGE,
                                    "precision": 0,
                                    "entity": Platform.SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                    "icon": "mdi:fan",
                                },
                            }
                        )
                    if ventilation_out_uid != 0:
                        data.update(
                            {
                                ventilation_out_entity_id: {
                                    "name": ventilation_out.get(OPT_NAME),
                                    "uid": ventilation_out_uid,
                                    "offset": 0,
                                    "length": 2,
                                    "type": 2,
                                    "unit": PERCENTAGE,
                                    "precision": 0,
                                    "entity": Platform.SENSOR,
                                    "device": user_input.get(OPT_DEVICE),
                                    "icon": "mdi:fan",
                                },
                            }
                        )
                    if ventilation_flow_setting_uid != 0:
                        data.update(
                            {
                                ventilation_flow_setting_entity_id: {
                                    "name": ventilation_flow_setting.get(OPT_NAME),
                                    "uid": ventilation_flow_setting_uid,
                                    "offset": 0,
                                    "length": 4,
                                    "type": 13,
                                    "max": OPT_VENTILATION_FLOW_MAXIMUM,
                                    "min": OPT_VENTILATION_FLOW_MINIMUM,
                                    "step": 1,
                                    "class": SensorDeviceClass.VOLUME_FLOW_RATE,
                                    "unit": UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
                                    "entity": Platform.NUMBER,
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

    async def async_step_poll(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change polling parameters."""

        data: dict[str, Any] = self.config_entry.options.copy()
        step = "poll"

        default_scan_interval = DEFAULT_SCAN_INTERVAL
        default_fast_interval = DEFAULT_FAST_INTERVAL
        default_fast_count = DEFAULT_FAST_COUNT
        default_write_retries = DEFAULT_WRITE_RETRIES
        if OPT_POLLING in data:
            polling = data[OPT_POLLING]
            default_scan_interval = polling.get(OPT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            default_fast_interval = polling.get(OPT_FAST_INTERVAL, DEFAULT_FAST_INTERVAL)
            default_fast_count = polling.get(OPT_FAST_COUNT, DEFAULT_FAST_COUNT)
            default_write_retries = polling.get(OPT_WRITE_RETRIES, DEFAULT_WRITE_RETRIES)
        if user_input is not None:
            default_scan_interval = user_input.get(OPT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            default_fast_interval = user_input.get(OPT_FAST_INTERVAL, DEFAULT_FAST_INTERVAL)
            default_fast_count = user_input.get(OPT_FAST_COUNT, DEFAULT_FAST_COUNT)
            default_write_retries = user_input.get(OPT_WRITE_RETRIES, DEFAULT_WRITE_RETRIES)
        schema = vol.Schema(
            {
                vol.Required(OPT_SCAN_INTERVAL, default=default_scan_interval): _SCAN_INTERVAL_SELECTOR,
                vol.Required(OPT_FAST_INTERVAL, default=default_fast_interval): _FAST_INTERVAL_SELECTOR,
                vol.Required(OPT_FAST_COUNT, default=default_fast_count): _FAST_COUNT_SELECTOR,
                vol.Required(OPT_WRITE_RETRIES, default=default_write_retries): _WRITE_RETRIES_SELECTOR,
            }
        )
        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema)

        data.update(
            {
                OPT_POLLING: {
                    OPT_SCAN_INTERVAL: user_input.get(OPT_SCAN_INTERVAL),
                    OPT_FAST_INTERVAL: user_input.get(OPT_FAST_INTERVAL),
                    OPT_FAST_COUNT: user_input.get(OPT_FAST_COUNT),
                    OPT_WRITE_RETRIES: user_input.get(OPT_WRITE_RETRIES)
                }
            }
        )
        return self.async_create_entry(data=data)

    async def async_step_info(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Write our configuration and  options to the log."""

        conf_data: dict[str, Any] = self.config_entry.data.copy()
        conf_data["password"] = "********"
        coordinator: DomatSSCPCoordinator = self.config_entry.coordinator
        level = _LOGGER.getEffectiveLevel()

        _LOGGER.setLevel(logging.INFO)
        _LOGGER.info("Co-ordinator name: %s", coordinator.name)
        _LOGGER.info("Configuration data: %s", conf_data)
        _LOGGER.info("Options: %s", self.config_entry.options)
        _LOGGER.setLevel(level)
        return self.async_abort(reason="info_written")

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
            if entity_id in self.config_entry.options:
                variables = variables + str(entity_uid) + " "
        return {"variables": variables}


class InvalidAuth(HomeAssistantError):
    """Error to indicate that the authentication is invalid."""


# Helpers
async def _validate_config(
    data: dict[str, Any],
    variables: list[sscp_variable] | None,
) -> dict[str, Any]:
    """Validate that the user input allows us to connect using the values provided by the user.

    Catches some exceptions to raise InvalidAuth.
    Returns either information or errors in info[].
    """

    # Config flow info
    unique_id = ""
    # Options flow info
    error_code = 0
    error_vars_str = ""

    conn = sscp_connection(
        name=data[CONF_CONNECTION_NAME],
        ip_address=data[CONF_IP_ADDRESS],
        port=data[CONF_PORT],
        user_name=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        sscp_address=data[CONF_SSCP_ADDRESS],
        md5_hash=None,
    )

    # Only catch some exceptions specific to authentication
    try:
        await conn.login()
        if conn.socket is None:
            _LOGGER.debug("Login failed")
            raise InvalidAuth from None
    except TimeoutError:
        _LOGGER.debug("Login timeout")
        raise InvalidAuth from None

    if variables is None:
        # Config flow
        # Use user name, SSCP address and PLC serial for unique ID
        await conn.get_info()
        if conn.serial is None:
            _LOGGER.error("No serial number for %s", data[CONF_CONNECTION_NAME])
            unique_id = (
                data[CONF_USERNAME]
                + "-"
                + str(data[CONF_SSCP_ADDRESS])
                + "-0000000000000000"
            )
        else:
            unique_id = (
                data[CONF_USERNAME]
                + "-"
                + str(data[CONF_SSCP_ADDRESS])
                + "-"
                + conn.serial
            )
        _LOGGER.info("Using unique ID: %s", unique_id)
    else:
        # Options flow
        error_vars, error_codes = await conn.sscp_read_variables(variables)
        if len(error_vars) > 0:
            error_code = error_codes[0]  # We only display the first error
            for var in error_vars:
                error_vars_str = error_vars_str + str(var) + " "

    await conn.logout()

    # Return info about the connection or errors.
    return {
        "title": data[CONF_CONNECTION_NAME],
        "unique_id": unique_id,
        "error_code": error_code,
        "error_variables": error_vars_str,
    }


def _get_user_schema(
    input_data: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return a config flow schema with defaults based on the step and user input."""

    # Fill in defaults from initial defaults or input
    default_connection_name = ""
    default_ip_address = ""
    default_port = DEFAULT_SSCP_PORT
    default_username = ""
    default_password = ""
    default_sscp_address = DEFAULT_SSCP_ADDRESS
    default_language = "en"  # TODO: Choose system language
    if input_data is not None:
        default_connection_name = input_data.get(
            CONF_CONNECTION_NAME, default_connection_name
        )
        default_ip_address = input_data.get(CONF_IP_ADDRESS, default_ip_address)
        default_port = input_data.get(CONF_PORT, default_port)
        default_username = input_data.get(CONF_USERNAME, default_username)
        default_password = input_data.get(CONF_PASSWORD, default_password)
        default_sscp_address = input_data.get(CONF_SSCP_ADDRESS, default_sscp_address)
        default_language = input_data.get(CONF_LANGUAGE, default_language)
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
            vol.Required(CONF_LANGUAGE, default=default_language): _LANG_SELECTOR,
        }
    )


def _get_room_schema(
    lang: str,
    input_data: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return a temperature/humidity flow schema with defaults based on the user input."""

    # Fill in defaults from input or initial defaults
    if lang == "en":
        default_device = OPT_ROOM_CONTROLS_NAME_EN
        default_temperature_name =OPT_TEMPERATURE_NAME_EN
        default_humidity_name = OPT_HUMIDITY_NAME_EN
        default_target_name = OPT_TEMPERATURE_SETTING_NAME_EN
    if lang == "cs":
        default_device = OPT_ROOM_CONTROLS_NAME_CS
        default_temperature_name =OPT_TEMPERATURE_NAME_CS
        default_humidity_name = OPT_HUMIDITY_NAME_CS
        default_target_name = OPT_TEMPERATURE_SETTING_NAME_CS
    default_temperature_uid = default_humidity_uid = 0
    default_target_uid = 0
    default_target_max = OPT_TEMPERATURE_SETTING_MAXIMUM
    default_target_min = OPT_TEMPERATURE_SETTING_MINIMUM
    default_target_step = OPT_TEMPERATURE_SETTING_STEP
    if input_data is not None:
        default_device = input_data.get(OPT_DEVICE)
        temperature = input_data.get(OPT_TEMPERATURE)
        default_temperature_name = temperature.get(OPT_NAME)
        default_temperature_uid = temperature.get(OPT_UID, 0)
        humidity = input_data.get(OPT_HUMIDITY)
        default_humidity_name = humidity.get(OPT_NAME)
        default_humidity_uid = humidity.get(OPT_UID, 0)
        target = input_data.get(OPT_TEMPERATURE_SETTING)
        default_target_name = target.get(OPT_NAME)
        default_target_uid = target.get(OPT_UID, 0)
        default_target_max = target.get(
            OPT_TEMPERATURE_SETTING_MAXIMUM, default_target_max
        )
        default_target_min = target.get(
            OPT_TEMPERATURE_SETTING_MINIMUM, default_target_min
        )
        default_target_step = target.get(
            OPT_TEMPERATURE_SETTING_STEP, default_target_step
        )
    return vol.Schema(
        {
            vol.Required(OPT_DEVICE, default=default_device): str,
            vol.Required(OPT_TEMPERATURE): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_temperature_name): str,
                        vol.Optional(
                            OPT_UID, default=default_temperature_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_HUMIDITY): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_humidity_name): str,
                        vol.Optional(
                            OPT_UID, default=default_humidity_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_TEMPERATURE_SETTING): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_target_name): str,
                        vol.Optional(
                            OPT_UID, default=default_target_uid
                        ): _UID_SELECTOR,
                        vol.Optional(
                            OPT_MINIMUM, default=default_target_min
                        ): _TEMPERATURE_SETTING_SELECTOR,
                        vol.Optional(
                            OPT_MAXIMUM, default=default_target_max
                        ): _TEMPERATURE_SETTING_SELECTOR,
                        vol.Optional(
                            OPT_STEP, default=default_target_step
                        ): _TARGET_STEP_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
        }
    )


def _get_energy_schema(
    lang: str,
    input_data: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return an energy flow schema with defaults based on the user input."""

    # Fill in defaults from input or initial defaults
    # Order is the same as in the app
    if lang == "en":
        default_device = OPT_ENERGY_NAME_EN
        default_meter_electricity_name = OPT_METER_ELECTRICITY_NAME_EN
        default_meter_water_cold_name = OPT_METER_WATER_COLD_NAME_EN
        default_meter_water_hot_name = OPT_METER_WATER_HOT_NAME_EN
        default_calorimeter_hot_name = OPT_CALORIMETER_HOT_NAME_EN
        default_calorimeter_cold_name = OPT_CALORIMETER_COLD_NAME_EN
    if lang == "cs":
        default_device = OPT_ENERGY_NAME_CS
        default_meter_electricity_name = OPT_METER_ELECTRICITY_NAME_CS
        default_meter_water_cold_name = OPT_METER_WATER_COLD_NAME_CS
        default_meter_water_hot_name = OPT_METER_WATER_HOT_NAME_CS
        default_calorimeter_hot_name = OPT_CALORIMETER_HOT_NAME_CS
        default_calorimeter_cold_name = OPT_CALORIMETER_COLD_NAME_CS
    default_meter_electricity_uid = 0
    default_meter_water_cold_uid = default_meter_water_hot_uid = 0
    default_calorimeter_hot_uid = default_calorimeter_cold_uid = 0
    if input_data is not None:
        default_device = input_data.get(OPT_DEVICE, default_device)
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
            vol.Required(OPT_DEVICE, default=default_device): str,
            vol.Required(OPT_METER_ELECTRICITY): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_meter_electricity_name
                        ): str,
                        vol.Optional(
                            OPT_UID, default=default_meter_electricity_uid
                        ): _UID_SELECTOR,
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
                        ): _UID_SELECTOR,
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
                        vol.Optional(
                            OPT_UID, default=default_meter_water_hot_uid
                        ): _UID_SELECTOR,
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
                        vol.Optional(
                            OPT_UID, default=default_calorimeter_hot_uid
                        ): _UID_SELECTOR,
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
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
        }
    )


def _get_air_schema(
    lang: str,
    input_data: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return an air ventilation schema with defaults based on the user input."""

    # Fill in defaults from input or initial defaults
    # Order is the same as in the app
    if lang == "en":
        default_device = OPT_VENTILATION_NAME_EN
        default_ventilation_error_name = OPT_VENTILATION_ERROR_NAME_EN
        default_ventilation_filter_name = OPT_VENTILATION_FILTER_NAME_EN
        default_ventilation_state_name = OPT_VENTILATION_STATE_NAME_EN
        default_co2_target_name = OPT_CO2_TARGET_NAME_EN
        default_co2_actual_name = OPT_CO2_ACTUAL_NAME_EN
        default_ventilation_flow_target_name = OPT_VENTILATION_FLOW_TARGET_NAME_EN
        default_ventilation_in_name = OPT_VENTILATION_IN_NAME_EN
        default_ventilation_out_name = OPT_VENTILATION_OUT_NAME_EN
        default_ventilation_flow_setting_name = OPT_VENTILATION_FLOW_SETTING_NAME_EN
    if lang == "cs":
        default_device = OPT_VENTILATION_NAME_CS
        default_ventilation_error_name = OPT_VENTILATION_ERROR_NAME_CS
        default_ventilation_filter_name = OPT_VENTILATION_FILTER_NAME_CS
        default_ventilation_state_name = OPT_VENTILATION_STATE_NAME_CS
        default_co2_target_name = OPT_CO2_TARGET_NAME_CS
        default_co2_actual_name = OPT_CO2_ACTUAL_NAME_CS
        default_ventilation_flow_target_name = OPT_VENTILATION_FLOW_TARGET_NAME_CS
        default_ventilation_in_name = OPT_VENTILATION_IN_NAME_CS
        default_ventilation_out_name = OPT_VENTILATION_OUT_NAME_CS
        default_ventilation_flow_setting_name = OPT_VENTILATION_FLOW_SETTING_NAME_CS
    default_ventilation_error_uid = 0
    default_ventilation_filter_uid = default_ventilation_state_uid = 0
    default_co2_target_uid = default_co2_actual_uid = 0
    default_ventilation_flow_target_uid = 0
    default_ventilation_in_uid = default_ventilation_out_uid = 0
    default_ventilation_flow_setting_uid = 0
    if input_data is not None:
        default_device = input_data.get(OPT_DEVICE, default_device)
        default_ventilation_error = input_data.get(OPT_VENTILATION_ERROR)
        default_ventilation_error_uid = default_ventilation_error.get(
            OPT_UID, default_ventilation_error_uid
        )
        default_ventilation_filter = input_data.get(OPT_VENTILATION_FILTER)
        default_ventilation_filter_uid = default_ventilation_filter.get(
            OPT_UID, default_ventilation_filter_uid
        )
        default_ventilation_state = input_data.get(OPT_VENTILATION_STATE)
        default_ventilation_state_uid = default_ventilation_state.get(
            OPT_UID, default_ventilation_state_uid
        )
        default_co2_target = input_data.get(OPT_CO2_TARGET)
        default_co2_target_uid = default_co2_target.get(OPT_UID, default_co2_target_uid)
        default_co2_actual = input_data.get(OPT_CO2_ACTUAL)
        default_co2_actual_uid = default_co2_actual.get(OPT_UID, default_co2_actual_uid)
        default_ventilation_flow_target = input_data.get(OPT_VENTILATION_FLOW_TARGET)
        default_ventilation_flow_target_uid = default_ventilation_flow_target.get(
            OPT_UID, default_ventilation_flow_target_uid
        )
        default_ventilation_in = input_data.get(OPT_VENTILATION_IN)
        default_ventilation_in_uid = default_ventilation_in.get(
            OPT_UID, default_ventilation_in_uid
        )
        default_ventilation_out = input_data.get(OPT_VENTILATION_OUT)
        default_ventilation_out_uid = default_ventilation_out.get(
            OPT_UID, default_ventilation_out_uid
        )
        default_ventilation_flow_setting = input_data.get(OPT_VENTILATION_FLOW_SETTING)
        default_ventilation_flow_setting_uid = default_ventilation_flow_setting.get(
            OPT_UID, default_ventilation_flow_setting_uid
        )

    return vol.Schema(
        {
            vol.Required(OPT_DEVICE, default=default_device): str,
            vol.Required(OPT_VENTILATION_ERROR): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_ventilation_error_name
                        ): str,
                        vol.Optional(
                            OPT_UID, default=default_ventilation_error_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_VENTILATION_FILTER): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_ventilation_filter_name
                        ): str,
                        vol.Optional(
                            OPT_UID, default=default_ventilation_filter_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_VENTILATION_STATE): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_ventilation_state_name
                        ): str,
                        vol.Optional(
                            OPT_UID, default=default_ventilation_state_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_CO2_TARGET): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_co2_target_name): str,
                        vol.Optional(
                            OPT_UID, default=default_co2_target_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_CO2_ACTUAL): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_co2_actual_name): str,
                        vol.Optional(
                            OPT_UID, default=default_co2_actual_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Optional(OPT_VENTILATION_FLOW_TARGET): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_ventilation_flow_target_name
                        ): str,
                        vol.Optional(
                            OPT_UID, default=default_ventilation_flow_target_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_VENTILATION_IN): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_ventilation_in_name
                        ): str,
                        vol.Optional(
                            OPT_UID, default=default_ventilation_in_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_VENTILATION_OUT): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_ventilation_out_name
                        ): str,
                        vol.Optional(
                            OPT_UID, default=default_ventilation_out_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Optional(OPT_VENTILATION_FLOW_SETTING): section(
                vol.Schema(
                    {
                        vol.Optional(
                            OPT_NAME, default=default_ventilation_flow_setting_name
                        ): str,
                        vol.Optional(
                            OPT_UID, default=default_ventilation_flow_setting_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": True},
            ),
        }
    )
