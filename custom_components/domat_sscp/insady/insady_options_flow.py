"""InSady options flow for the Domat SSCP integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.water_heater import WaterHeaterEntityFeature
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    PRECISION_TENTHS,
    Platform,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from ..const import OPT_DEVICE, OPT_EXISTING_DEVICE, OPT_NAME, OPT_UID
from .insady_const import (
    OPT_APARTMENT_ACTUAL,
    OPT_APARTMENT_ACTUAL_NAME_CS,
    OPT_APARTMENT_ACTUAL_NAME_EN,
    OPT_APARTMENT_ACTUAL_STATES_CS,
    OPT_APARTMENT_ACTUAL_STATES_EN,
    OPT_APARTMENT_CONTROLS_NAME_CS,
    OPT_APARTMENT_CONTROLS_NAME_EN,
    OPT_APARTMENT_COOLING,
    OPT_APARTMENT_COOLING_NAME_CS,
    OPT_APARTMENT_COOLING_NAME_EN,
    OPT_APARTMENT_HEATING,
    OPT_APARTMENT_HEATING_NAME_CS,
    OPT_APARTMENT_HEATING_NAME_EN,
    OPT_APARTMENT_MODE,
    OPT_APARTMENT_MODE_NAME_CS,
    OPT_APARTMENT_MODE_NAME_EN,
    OPT_APARTMENT_MODE_STATES_CS,
    OPT_APARTMENT_MODE_STATES_EN,
    OPT_APARTMENT_STATE,
    OPT_APARTMENT_STATE_NAME_CS,
    OPT_APARTMENT_STATE_NAME_EN,
    OPT_APARTMENT_STATE_STATES_CS,
    OPT_APARTMENT_STATE_STATES_EN,
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
    OPT_COOLING_SETTING,
    OPT_COOLING_SETTING_NAME_CS,
    OPT_COOLING_SETTING_NAME_EN,
    OPT_COOLING_SPEED,
    OPT_COOLING_SPEED_NAME_CS,
    OPT_COOLING_SPEED_NAME_EN,
    OPT_COOLING_SPEED_SETTING,
    OPT_COOLING_SPEED_SETTING_NAME_CS,
    OPT_COOLING_SPEED_SETTING_NAME_EN,
    OPT_COOLING_VALVE,
    OPT_COOLING_VALVE_NAME_CS,
    OPT_COOLING_VALVE_NAME_EN,
    OPT_ENERGY_NAME_CS,
    OPT_ENERGY_NAME_EN,
    OPT_FAN_MAXIMUM,
    OPT_FAN_MINIMUM,
    OPT_FAN_STEP,
    OPT_HEATING_SETTING,
    OPT_HEATING_SETTING_NAME_CS,
    OPT_HEATING_SETTING_NAME_EN,
    OPT_HEATING_VALVE,
    OPT_HEATING_VALVE_NAME_CS,
    OPT_HEATING_VALVE_NAME_EN,
    OPT_HOLIDAY_SETTING,
    OPT_HOLIDAY_SETTING_MAXIMUM,
    OPT_HOLIDAY_SETTING_MINIMUM,
    OPT_HOLIDAY_SETTING_NAME_CS,
    OPT_HOLIDAY_SETTING_NAME_EN,
    OPT_HOLIDAY_SETTING_STEP,
    OPT_HOLIDAY_TARGET,
    OPT_HOLIDAY_TARGET_NAME_CS,
    OPT_HOLIDAY_TARGET_NAME_EN,
    OPT_HUMIDITY,
    OPT_HUMIDITY_NAME_CS,
    OPT_HUMIDITY_NAME_EN,
    OPT_LOW_SETTING,
    OPT_LOW_SETTING_MAXIMUM,
    OPT_LOW_SETTING_MINIMUM,
    OPT_LOW_SETTING_NAME_CS,
    OPT_LOW_SETTING_NAME_EN,
    OPT_LOW_SETTING_STEP,
    OPT_LOW_TARGET,
    OPT_LOW_TARGET_NAME_CS,
    OPT_LOW_TARGET_NAME_EN,
    OPT_METER_ELECTRICITY,
    OPT_METER_ELECTRICITY_NAME_CS,
    OPT_METER_ELECTRICITY_NAME_EN,
    OPT_METER_WATER_COLD,
    OPT_METER_WATER_COLD_NAME_CS,
    OPT_METER_WATER_COLD_NAME_EN,
    OPT_METER_WATER_HOT,
    OPT_METER_WATER_HOT_NAME_CS,
    OPT_METER_WATER_HOT_NAME_EN,
    OPT_ROOM_CONTROLS_NAME_CS,
    OPT_ROOM_CONTROLS_NAME_EN,
    OPT_TEMPERATURE,
    OPT_TEMPERATURE_NAME_CS,
    OPT_TEMPERATURE_NAME_EN,
    OPT_TEMPERATURE_SETTING,
    OPT_TEMPERATURE_SETTING_MAXIMUM,
    OPT_TEMPERATURE_SETTING_MINIMUM,
    OPT_TEMPERATURE_SETTING_NAME_CS,
    OPT_TEMPERATURE_SETTING_NAME_EN,
    OPT_TEMPERATURE_SETTING_STEP,
    OPT_TEMPERATURE_TARGET,
    OPT_TEMPERATURE_TARGET_NAME_CS,
    OPT_TEMPERATURE_TARGET_NAME_EN,
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
    OPT_VENTILATION_FLOW_STEP,
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
)

_LOGGER = logging.getLogger(__name__)

# Options flows schemas
_UID_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=0, max=0xFFFFFFFF, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)

def get_room_configs() -> dict[str, dict]:
    """Return a dictionary of entities for a room controls device."""

    return {
        OPT_TEMPERATURE: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.TEMPERATURE,
            "unit": UnitOfTemperature.CELSIUS,
            "state": SensorStateClass.MEASUREMENT,
            "precision": 1,
            "entity": Platform.SENSOR,
            "device": None,
        },
        OPT_HUMIDITY: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.HUMIDITY,
            "unit": PERCENTAGE,
            "state": SensorStateClass.MEASUREMENT,
            "precision": 1,
            "entity": Platform.SENSOR,
            "device": None,
        },
        OPT_TEMPERATURE_SETTING: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "feature": WaterHeaterEntityFeature.TARGET_TEMPERATURE,
            "unit": UnitOfTemperature.CELSIUS,
            "precision": PRECISION_TENTHS,
            "max": OPT_TEMPERATURE_SETTING_MAXIMUM,
            "min": OPT_TEMPERATURE_SETTING_MINIMUM,
            "step": OPT_TEMPERATURE_SETTING_STEP,
            "entity": Platform.WATER_HEATER,
            "device": None,
            "icon": "mdi:thermometer-lines",
        },
        OPT_TEMPERATURE_TARGET: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.TEMPERATURE,
            "unit": UnitOfTemperature.CELSIUS,
            "state": SensorStateClass.MEASUREMENT,
            "precision": 1,
            "entity": Platform.SENSOR,
            "device": None,
        },
        OPT_LOW_SETTING: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "feature": WaterHeaterEntityFeature.TARGET_TEMPERATURE,
            "unit": UnitOfTemperature.CELSIUS,
            "precision": PRECISION_TENTHS,
            "max": OPT_LOW_SETTING_MAXIMUM,
            "min": OPT_LOW_SETTING_MINIMUM,
            "step": OPT_LOW_SETTING_STEP,
            "entity": Platform.WATER_HEATER,
            "device": None,
            "icon": "mdi:thermometer-lines",
        },
        OPT_LOW_TARGET: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.TEMPERATURE,
            "unit": UnitOfTemperature.CELSIUS,
            "state": SensorStateClass.MEASUREMENT,
            "precision": 1,
            "entity": Platform.SENSOR,
            "device": OPT_DEVICE
        },
        OPT_HEATING_VALVE: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 1,
            "type": 0,
            "class": BinarySensorDeviceClass.OPENING,
            "on": 1,
            "off": 0,
            "entity": Platform.BINARY_SENSOR,
            "device": None,
            "icon": "mdi:valve",
        },
        OPT_HEATING_SETTING: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 2,
            "type": 2,
            "on": 2,
            "off": 1,
            "entity": Platform.SWITCH,
            "device": None,
        },
        OPT_COOLING_VALVE: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 1,
            "type": 0,
            "class": BinarySensorDeviceClass.OPENING,
            "on": 1,
            "off": 0,
            "entity": Platform.BINARY_SENSOR,
            "device": None,
            "icon": "mdi:valve",
        },
        OPT_COOLING_SPEED: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "unit": PERCENTAGE,
            "state": SensorStateClass.MEASUREMENT,
            "precision": 0,
            "entity": Platform.SENSOR,
            "device": None,
            "icon": "mdi:air-conditioner",
        },
        OPT_COOLING_SETTING: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 2,
            "type": 2,
            "on": 2,
            "off": 1,
            "entity": Platform.SWITCH,
            "device": None,
        },
        OPT_COOLING_SPEED_SETTING: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "max": OPT_FAN_MAXIMUM,
            "min": OPT_FAN_MINIMUM,
            "step": OPT_FAN_STEP,
            "class": NumberDeviceClass.POWER_FACTOR,
            "unit": PERCENTAGE,
            "precision": 0,
            "entity": Platform.NUMBER,
            "device": None,
            "icon": "mdi:air-conditioner",
        }
    }


def get_room_schema(
    lang: str,
    input_data: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return a room controls flow schema with defaults based on the user input."""

    # Fill in defaults from input or initial defaults
    if lang == "en":
        default_device = OPT_ROOM_CONTROLS_NAME_EN
        default_temperature_name = OPT_TEMPERATURE_NAME_EN
        default_humidity_name = OPT_HUMIDITY_NAME_EN
        default_temperature_setting_name = OPT_TEMPERATURE_SETTING_NAME_EN
        default_temperature_target_name = OPT_TEMPERATURE_TARGET_NAME_EN
        default_low_setting_name = OPT_LOW_SETTING_NAME_EN
        default_low_target_name = OPT_LOW_TARGET_NAME_EN
        default_heating_valve_name = OPT_HEATING_VALVE_NAME_EN
        default_heating_setting_name = OPT_HEATING_SETTING_NAME_EN
        default_cooling_valve_name = OPT_COOLING_VALVE_NAME_EN
        default_cooling_speed_name = OPT_COOLING_SPEED_NAME_EN
        default_cooling_setting_name = OPT_COOLING_SETTING_NAME_EN
        default_cooling_speed_setting_name = OPT_COOLING_SPEED_SETTING_NAME_EN
    if lang == "cs":
        default_device = OPT_ROOM_CONTROLS_NAME_CS
        default_temperature_name = OPT_TEMPERATURE_NAME_CS
        default_humidity_name = OPT_HUMIDITY_NAME_CS
        default_temperature_setting_name = OPT_TEMPERATURE_SETTING_NAME_CS
        default_temperature_target_name = OPT_TEMPERATURE_TARGET_NAME_CS
        default_low_setting_name = OPT_LOW_SETTING_NAME_CS
        default_low_target_name = OPT_LOW_TARGET_NAME_CS
        default_heating_valve_name = OPT_HEATING_VALVE_NAME_CS
        default_heating_setting_name = OPT_HEATING_SETTING_NAME_CS
        default_cooling_valve_name = OPT_COOLING_VALVE_NAME_CS
        default_cooling_speed_name = OPT_COOLING_SPEED_NAME_CS
        default_cooling_setting_name = OPT_COOLING_SETTING_NAME_CS
        default_cooling_speed_setting_name = OPT_COOLING_SPEED_SETTING_NAME_CS
    default_temperature_uid = default_humidity_uid = 0
    default_temperature_setting_uid = default_temperature_target_uid = 0
    default_low_setting_uid = default_low_target_uid = 0
    default_heating_valve_uid = default_heating_setting_uid = 0
    default_cooling_valve_uid = default_cooling_speed_uid = default_cooling_setting_uid = default_cooling_speed_setting_uid = 0
    default_existing_device = False
    if input_data is not None:
        default_device = input_data.get(OPT_DEVICE)
        temperature = input_data.get(OPT_TEMPERATURE)
        default_temperature_name = temperature.get(OPT_NAME)
        default_temperature_uid = temperature.get(OPT_UID, 0)
        humidity = input_data.get(OPT_HUMIDITY)
        default_humidity_name = humidity.get(OPT_NAME)
        default_humidity_uid = humidity.get(OPT_UID, 0)
        temperature_setting = input_data.get(OPT_TEMPERATURE_SETTING)
        default_temperature_setting_name = temperature_setting.get(OPT_NAME)
        default_temperature_setting_uid = temperature_setting.get(OPT_UID, 0)
        temperature_target = input_data.get(OPT_TEMPERATURE_TARGET)
        default_temperature_target_name = temperature_target.get(OPT_NAME)
        default_temperature_target_uid = temperature_target.get(OPT_UID, 0)
        low_setting = input_data.get(OPT_LOW_SETTING)
        default_low_setting_name = low_setting.get(OPT_NAME)
        default_low_setting_uid = low_setting.get(OPT_UID, 0)
        low_target = input_data.get(OPT_LOW_TARGET)
        default_low_target_name = low_target.get(OPT_NAME)
        default_low_target_uid = low_target.get(OPT_UID, 0)
        heating_valve = input_data.get(OPT_HEATING_VALVE)
        default_heating_valve_name = heating_valve.get(OPT_NAME)
        default_heating_valve_uid = heating_valve.get(OPT_UID, 0)
        heating_setting = input_data.get(OPT_HEATING_SETTING)
        default_heating_setting_name = heating_setting.get(OPT_NAME)
        default_heating_setting_uid = heating_setting.get(OPT_UID, 0)
        cooling_valve = input_data.get(OPT_COOLING_VALVE)
        default_cooling_valve_name = cooling_valve.get(OPT_NAME)
        default_cooling_valve_uid = cooling_valve.get(OPT_UID, 0)
        cooling_speed = input_data.get(OPT_COOLING_SPEED)
        default_cooling_speed_name = cooling_speed.get(OPT_NAME)
        default_cooling_speed_uid = cooling_speed.get(OPT_UID, 0)
        cooling_setting = input_data.get(OPT_COOLING_SETTING)
        default_cooling_setting_name = cooling_setting.get(OPT_NAME)
        default_cooling_setting_uid = cooling_setting.get(OPT_UID, 0)
        cooling_speed_setting = input_data.get(OPT_COOLING_SPEED_SETTING)
        default_cooling_speed_setting_name = cooling_speed_setting.get(OPT_NAME)
        default_cooling_speed_setting_uid = cooling_speed_setting.get(OPT_UID, 0)
        existing_device = input_data.get(OPT_EXISTING_DEVICE)
        default_existing_device = existing_device.get(OPT_EXISTING_DEVICE, False)
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
                        vol.Optional(OPT_NAME, default=default_temperature_setting_name): str,
                        vol.Optional(
                            OPT_UID, default=default_temperature_setting_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_TEMPERATURE_TARGET): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_temperature_target_name): str,
                        vol.Optional(
                            OPT_UID, default=default_temperature_target_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_LOW_SETTING): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_low_setting_name): str,
                        vol.Optional(
                            OPT_UID, default=default_low_setting_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_LOW_TARGET): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_low_target_name): str,
                        vol.Optional(
                            OPT_UID, default=default_low_target_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_HEATING_VALVE): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_heating_valve_name): str,
                        vol.Optional(
                            OPT_UID, default=default_heating_valve_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_HEATING_SETTING): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_heating_setting_name): str,
                        vol.Optional(
                            OPT_UID, default=default_heating_setting_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": True},
            ),
            vol.Required(OPT_COOLING_VALVE): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_cooling_valve_name): str,
                        vol.Optional(
                            OPT_UID, default=default_cooling_valve_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_COOLING_SPEED): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_cooling_speed_name): str,
                        vol.Optional(
                            OPT_UID, default=default_cooling_speed_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_COOLING_SETTING): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_cooling_setting_name): str,
                        vol.Optional(
                            OPT_UID, default=default_cooling_setting_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": True},
            ),
            vol.Required(OPT_COOLING_SPEED_SETTING): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_cooling_speed_setting_name): str,
                        vol.Optional(
                            OPT_UID, default=default_cooling_speed_setting_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": True},
            ),
            vol.Required(OPT_EXISTING_DEVICE): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_EXISTING_DEVICE, default=default_existing_device): BooleanSelector(),
                    }
                ),
                {"collapsed": True},
            ),
        }
    )


def get_apartment_configs(lang: str | None = None) -> dict[str, dict]:
    """Return a dictionary of entities for a apartment control device."""

    apartment_mode_states = OPT_APARTMENT_MODE_STATES_EN
    apartment_actual_states = OPT_APARTMENT_ACTUAL_STATES_EN
    apartment_state_states = OPT_APARTMENT_STATE_STATES_EN
    if lang == "cs":
        apartment_mode_states = OPT_APARTMENT_MODE_STATES_CS
        apartment_actual_states = OPT_APARTMENT_ACTUAL_STATES_CS
        apartment_state_states = OPT_APARTMENT_STATE_STATES_CS

    return {
        OPT_APARTMENT_MODE: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 2,
            "type": 2,
            "states": apartment_mode_states,
            "entity": Platform.SELECT,
            "device": None,
        },
        OPT_APARTMENT_ACTUAL: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 2,
            "type": 2,
            "states": apartment_actual_states,
            "class": SensorDeviceClass.ENUM,
            "entity": Platform.SENSOR,
            "device": None,
            "icon": "mdi:format-list-bulleted",
        },
        OPT_HOLIDAY_SETTING: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "feature": WaterHeaterEntityFeature.TARGET_TEMPERATURE,
            "unit": UnitOfTemperature.CELSIUS,
            "precision": PRECISION_TENTHS,
            "max": OPT_HOLIDAY_SETTING_MAXIMUM,
            "min": OPT_HOLIDAY_SETTING_MINIMUM,
            "step": OPT_HOLIDAY_SETTING_STEP,
            "entity": Platform.WATER_HEATER,
            "device": None,
            "icon": "mdi:thermometer-lines",
        },
        OPT_HOLIDAY_TARGET: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.TEMPERATURE,
            "unit": UnitOfTemperature.CELSIUS,
            "state": SensorStateClass.MEASUREMENT,
            "precision": 1,
            "entity": Platform.SENSOR,
            "device": None,
        },
        OPT_APARTMENT_STATE: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 1,
            "type": 0,
            "states": apartment_state_states,
            "class": SensorDeviceClass.ENUM,
            "entity": Platform.SENSOR,
            "device": None,
            "icon": "mdi:format-list-bulleted",
        },
        OPT_APARTMENT_HEATING: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 1,
            "type": 0,
            "class": BinarySensorDeviceClass.RUNNING,
            "on": 1,
            "off": 0,
            "entity": Platform.BINARY_SENSOR,
            "device": None,
            "icon": "mdi:heat-wave",
        },
        OPT_APARTMENT_COOLING: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 1,
            "type": 0,
            "class": BinarySensorDeviceClass.RUNNING,
            "on": 1,
            "off": 0,
            "entity": Platform.BINARY_SENSOR,
            "device": None,
            "icon": "mdi:snowflake",
        },
    }


def get_apartment_schema(
    lang: str,
    input_data: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return an apartment control flow schema with defaults based on the user input."""

    # Fill in defaults from input or initial defaults
    if lang == "en":
        default_device = OPT_APARTMENT_CONTROLS_NAME_EN
        default_apartment_mode_name = OPT_APARTMENT_MODE_NAME_EN
        default_apartment_actual_name = OPT_APARTMENT_ACTUAL_NAME_EN
        default_holiday_setting_name = OPT_HOLIDAY_SETTING_NAME_EN
        default_holiday_target_name = OPT_HOLIDAY_TARGET_NAME_EN
        default_apartment_state_name = OPT_APARTMENT_STATE_NAME_EN
        default_apartment_heating_name = OPT_APARTMENT_HEATING_NAME_EN
        default_apartment_cooling_name = OPT_APARTMENT_COOLING_NAME_EN
    if lang == "cs":
        default_device = OPT_APARTMENT_CONTROLS_NAME_CS
        default_apartment_mode_name = OPT_APARTMENT_MODE_NAME_CS
        default_apartment_actual_name = OPT_APARTMENT_ACTUAL_NAME_CS
        default_holiday_setting_name = OPT_HOLIDAY_SETTING_NAME_CS
        default_holiday_target_name = OPT_HOLIDAY_TARGET_NAME_CS
        default_apartment_state_name = OPT_APARTMENT_STATE_NAME_CS
        default_apartment_heating_name = OPT_APARTMENT_HEATING_NAME_CS
        default_apartment_cooling_name = OPT_APARTMENT_COOLING_NAME_CS
    default_apartment_mode_uid = default_apartment_actual_uid = 0
    default_holiday_setting_uid = default_holiday_target_uid = 0
    default_apartment_state_uid = 0
    default_apartment_heating_uid = default_apartment_cooling_uid = 0
    default_existing_device = False
    if input_data is not None:
        default_device = input_data.get(OPT_DEVICE)
        apartment_mode = input_data.get(OPT_APARTMENT_MODE)
        default_apartment_mode_name = apartment_mode.get(OPT_NAME)
        default_apartment_mode_uid = apartment_mode.get(OPT_UID,0)
        apartment_actual = input_data.get(OPT_APARTMENT_ACTUAL)
        default_apartment_actual_name = apartment_actual.get(OPT_NAME)
        default_apartment_actual_uid = apartment_actual.get(OPT_UID,0)
        holiday_setting = input_data.get(OPT_HOLIDAY_SETTING)
        default_holiday_setting_name = holiday_setting.get(OPT_NAME)
        default_holiday_setting_uid = holiday_setting.get(OPT_UID, 0)
        holiday_target = input_data.get(OPT_HOLIDAY_TARGET)
        default_holiday_target_name = holiday_target.get(OPT_NAME)
        default_holiday_target_uid = holiday_target.get(OPT_UID, 0)
        apartment_state = input_data.get(OPT_APARTMENT_STATE)
        default_apartment_state_name = apartment_state.get(OPT_NAME)
        default_apartment_state_uid = apartment_state.get(OPT_UID,0)
        apartment_heating = input_data.get(OPT_APARTMENT_HEATING)
        default_apartment_heating_name = apartment_heating.get(OPT_NAME)
        default_apartment_heating_uid = apartment_heating.get(OPT_UID,0)
        apartment_cooling = input_data.get(OPT_APARTMENT_COOLING)
        default_apartment_cooling_name = apartment_cooling.get(OPT_NAME)
        default_apartment_cooling_uid = apartment_cooling.get(OPT_UID,0)
        existing_device = input_data.get(OPT_EXISTING_DEVICE)
        default_existing_device = existing_device.get(OPT_EXISTING_DEVICE, False)
    return vol.Schema(
        {
            vol.Required(OPT_DEVICE, default=default_device): str,
            vol.Required(OPT_APARTMENT_MODE): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_apartment_mode_name): str,
                        vol.Optional(
                            OPT_UID, default=default_apartment_mode_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_APARTMENT_ACTUAL): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_apartment_actual_name): str,
                        vol.Optional(
                            OPT_UID, default=default_apartment_actual_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_HOLIDAY_SETTING): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_holiday_setting_name): str,
                        vol.Optional(
                            OPT_UID, default=default_holiday_setting_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_HOLIDAY_TARGET): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_holiday_target_name): str,
                        vol.Optional(
                            OPT_UID, default=default_holiday_target_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_APARTMENT_STATE): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_apartment_state_name): str,
                        vol.Optional(
                            OPT_UID, default=default_apartment_state_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_APARTMENT_HEATING): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_apartment_heating_name): str,
                        vol.Optional(
                            OPT_UID, default=default_apartment_heating_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_APARTMENT_COOLING): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_NAME, default=default_apartment_cooling_name): str,
                        vol.Optional(
                            OPT_UID, default=default_apartment_cooling_uid
                        ): _UID_SELECTOR,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(OPT_EXISTING_DEVICE): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_EXISTING_DEVICE, default=default_existing_device): BooleanSelector(),
                    }
                ),
                {"collapsed": True},
            ),
        }
    )


def get_energy_configs() -> dict[str, dict]:
    """Return a dictionary of entities for an energy usage device."""

    return {
        OPT_METER_ELECTRICITY: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.ENERGY,
            "unit": UnitOfEnergy.KILO_WATT_HOUR,
            "state": SensorStateClass.TOTAL_INCREASING,
            "precision": 3,
            "entity": Platform.SENSOR,
            "device": None,
        },
        OPT_METER_WATER_COLD: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.WATER,
            "unit": UnitOfVolume.CUBIC_METERS,
            "state": SensorStateClass.TOTAL_INCREASING,
            "precision": 3,
            "entity": Platform.SENSOR,
            "device": None,
        },
        OPT_METER_WATER_HOT: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.WATER,
            "unit": UnitOfVolume.CUBIC_METERS,
            "state": SensorStateClass.TOTAL_INCREASING,
            "precision": 3,
            "entity": Platform.SENSOR,
            "device": None,
        },
        OPT_CALORIMETER_HOT: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.ENERGY,
            "unit": UnitOfEnergy.GIGA_JOULE,
            "state": SensorStateClass.TOTAL_INCREASING,
            "precision": 3,
            "entity": Platform.SENSOR,
            "device": None,
        },
        OPT_CALORIMETER_COLD: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.ENERGY,
            "unit": UnitOfEnergy.KILO_WATT_HOUR,
            "state": SensorStateClass.TOTAL_INCREASING,
            "precision": 3,
            "entity": Platform.SENSOR,
            "device": None,
        },
    }


def get_energy_schema(
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
    default_existing_device = False
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
        existing_device = input_data.get(OPT_EXISTING_DEVICE)
        default_existing_device = existing_device.get(OPT_EXISTING_DEVICE, False)
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
            vol.Required(OPT_EXISTING_DEVICE): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_EXISTING_DEVICE, default=default_existing_device): BooleanSelector(),
                    }
                ),
                {"collapsed": True},
            ),
        }
    )


def get_air_configs() -> dict[str, dict]:
    """Return a dictionary of entities for an energy usage device."""

    return {
        OPT_VENTILATION_ERROR: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 1,
            "type": 0,
            "class": BinarySensorDeviceClass.PROBLEM,
            "on": 1,
            "off": 0,
            "entity": Platform.BINARY_SENSOR,
            "device": None,
            "icon": "mdi:bell",
        },
        OPT_VENTILATION_FILTER: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 1,
            "type": 0,
            "class": BinarySensorDeviceClass.PROBLEM,
            "on": 1,
            "off": 0,
            "entity": Platform.BINARY_SENSOR,
            "device": None,
            "icon": "mdi:wrench",
        },
        OPT_VENTILATION_STATE: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 1,
            "type": 0,
            "class": BinarySensorDeviceClass.RUNNING,
            "on": 1,
            "off": 0,
            "entity": Platform.BINARY_SENSOR,
            "device": None,
        },
        OPT_CO2_TARGET: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.CO2,
            "unit": CONCENTRATION_PARTS_PER_MILLION,
            "state": SensorStateClass.MEASUREMENT,
            "precision": 0,
            "entity": Platform.SENSOR,
            "device": None,
        },
        OPT_CO2_ACTUAL: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 2,
            "type": 2,
            "class": SensorDeviceClass.CO2,
            "unit": CONCENTRATION_PARTS_PER_MILLION,
            "state": SensorStateClass.MEASUREMENT,
            "precision": 0,
            "entity": Platform.SENSOR,
            "device": None,
        },
        OPT_VENTILATION_FLOW_TARGET: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "class": SensorDeviceClass.VOLUME_FLOW_RATE,
            "unit": UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
            "state": SensorStateClass.MEASUREMENT,
            "precision": 0,
            "entity": Platform.SENSOR,
            "device": None,
            "icon": "mdi:speedometer",
        },
        OPT_VENTILATION_IN: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 2,
            "type": 2,
            "unit": PERCENTAGE,
            "state": SensorStateClass.MEASUREMENT,
            "precision": 0,
            "entity": Platform.SENSOR,
            "device": None,
            "icon": "mdi:fan",
        },
        OPT_VENTILATION_OUT: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 2,
            "type": 2,
            "unit": PERCENTAGE,
            "state": SensorStateClass.MEASUREMENT,
            "precision": 0,
            "entity": Platform.SENSOR,
            "device": None,
            "icon": "mdi:fan",
        },
        OPT_VENTILATION_FLOW_SETTING: {
            "name": None,
            "uid": None,
            "offset": 0,
            "length": 4,
            "type": 13,
            "max": OPT_VENTILATION_FLOW_MAXIMUM,
            "min": OPT_VENTILATION_FLOW_MINIMUM,
            "step": OPT_VENTILATION_FLOW_STEP,
            "class": NumberDeviceClass.VOLUME_FLOW_RATE,
            "unit": UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
            "entity": Platform.NUMBER,
            "device": None,
            "icon": "mdi:speedometer",
        },
    }


def get_air_schema(
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
    default_existing_device = False
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
        existing_device = input_data.get(OPT_EXISTING_DEVICE)
        default_existing_device = existing_device.get(OPT_EXISTING_DEVICE, False)
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
            vol.Required(OPT_EXISTING_DEVICE): section(
                vol.Schema(
                    {
                        vol.Optional(OPT_EXISTING_DEVICE, default=default_existing_device): BooleanSelector(),
                    }
                ),
                {"collapsed": True},
            ),
        }
    )
