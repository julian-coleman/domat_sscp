"""Constants for the Domat SSCP integration."""

# Integration name
DOMAIN = "domat_sscp"

# Configuration flow constants
CONF_CONNECTION_NAME = "connection_name"
CONF_SSCP_ADDRESS = "sscp_address"
CONF_LANGUAGE = "language"

# Configuration defaults
DEFAULT_SCAN_INTERVAL = 300
DEFAULT_FAST_INTERVAL = 3
DEFAULT_FAST_COUNT = 5
DEFAULT_WRITE_RETRIES = 5
DEFAULT_SSCP_PORT = 12346
DEFAULT_SSCP_ADDRESS = 1

# Options flow constants
OPT_POLLING = "polling"
OPT_SCAN_INTERVAL = "scan_interval"
OPT_FAST_INTERVAL = "fast_interval"
OPT_FAST_COUNT = "fast_count"
OPT_WRITE_RETRIES = "write_retries"

OPT_DEVICE = "device"
OPT_NAME = "name"
OPT_UID = "uid"
OPT_OFFSET = "offset"
OPT_LENGTH = "length"
OPT_MINIMUM = "minimum"
OPT_MAXIMUM = "maximum"
OPT_STEP = "step"

OPT_TEMPERATURE = "temperature"
OPT_HUMIDITY = "humidity"
OPT_TEMPERATURE_SETTING = "temperature_setting"
OPT_TEMPERATURE_TARGET = "temperature_target"
OPT_LOW_SETTING = "low_setting"
OPT_LOW_TARGET = "low_target"
OPT_VALVE_HEATING = "valve_heating"
OPT_VALVE_COOLING = "valve_cooling"

OPT_APARTMENT_MODE = "apartment_mode"
OPT_APARTMENT_ACTUAL = "apartment_actual"
OPT_HOLIDAY_SETTING = "holiday_setting"
OPT_HOLIDAY_TARGET = "holiday_target"
OPT_APARTMENT_STATE = "apartment_state"
OPT_APARTMENT_HEATING = "apartment_heating"
OPT_APARTMENT_COOLING = "apartment_cooling"

OPT_METER_ELECTRICITY = "meter_electricity"
OPT_METER_WATER_COLD = "meter_water_cold"
OPT_METER_WATER_HOT = "meter_water_hot"
OPT_CALORIMETER_HOT = "calorimeter_hot"
OPT_CALORIMETER_COLD = "calorimeter_cold"

OPT_VENTILATION_ERROR = "ventilator_error"
OPT_VENTILATION_FILTER = "ventilator_filter"
OPT_VENTILATION_STATE = "ventilator_state"
OPT_CO2_TARGET = "cotwo_target"
OPT_CO2_ACTUAL = "cotwo_actual"
OPT_VENTILATION_FLOW_TARGET = "ventilator_flow_target"
OPT_VENTILATION_IN = "ventilator_in"
OPT_VENTILATION_OUT = "ventilator_out"
OPT_VENTILATION_FLOW_SETTING = "ventilator_flow_setting"

# Variable defaults
OPT_TEMPERATURE_SETTING_MINIMUM = 16
OPT_TEMPERATURE_SETTING_MAXIMUM = 30
OPT_TEMPERATURE_SETTING_STEP = 0.5
OPT_LOW_SETTING_MINIMUM = 0
OPT_LOW_SETTING_MAXIMUM = 4
OPT_LOW_SETTING_STEP = 0.1

OPT_HOLIDAY_SETTING_MINIMUM = 12
OPT_HOLIDAY_SETTING_MAXIMUM = 26
OPT_HOLIDAY_SETTING_STEP = 0.5

OPT_VENTILATION_FLOW_MINIMUM = 80
OPT_VENTILATION_FLOW_MAXIMUM = 200

# Name defaults
OPT_ROOM_CONTROLS_NAME_EN="Room Controls"
OPT_TEMPERATURE_NAME_EN="Actual temperature"
OPT_HUMIDITY_NAME_EN="Actual humidity"
OPT_TEMPERATURE_SETTING_NAME_EN="Set target temperature"
OPT_TEMPERATURE_TARGET_NAME_EN="Target temperature"
OPT_LOW_SETTING_NAME_EN = "Set minimum temperature"
OPT_LOW_TARGET_NAME_EN = "Minimum temperature"
OPT_VALVE_HEATING_NAME_EN = "Heating valve"
OPT_VALVE_COOLING_NAME_EN = "Cooling valve"
OPT_ROOM_CONTROLS_NAME_CS="Ovládání pokoje"
OPT_TEMPERATURE_NAME_CS="Teplota aktuální"
OPT_HUMIDITY_NAME_CS="Vlhkost aktuální"
OPT_TEMPERATURE_SETTING_NAME_CS="Teplota žádaná - nastavení"
OPT_TEMPERATURE_TARGET_NAME_CS="Teplota žádaná nastavená"
OPT_LOW_SETTING_NAME_CS = "Útlum - nastavení"
OPT_LOW_TARGET_NAME_CS = "Útlum nastavený"
OPT_VALVE_HEATING_NAME_CS = "Ventil topení"
OPT_VALVE_COOLING_NAME_CS = "Ventil chlazení"

OPT_APARTMENT_CONTROLS_NAME_EN = "Apartment Controls"
OPT_APARTMENT_MODE_NAME_EN = "Set apartment mode"
OPT_APARTMENT_ACTUAL_NAME_EN = "Apartment mode"
OPT_HOLIDAY_SETTING_NAME_EN = "Set holiday temperature"
OPT_HOLIDAY_TARGET_NAME_EN = "Holiday temperature"
OPT_APARTMENT_STATE_NAME_EN = "Apartment state"
OPT_APARTMENT_HEATING_NAME_EN = "Heating mode"
OPT_APARTMENT_COOLING_NAME_EN = "Cooling mode"
OPT_APARTMENT_CONTROLS_NAME_CS = "Ovládání bytu"
OPT_APARTMENT_MODE_NAME_CS = "Režím bytu - nastavení"
OPT_APARTMENT_ACTUAL_NAME_CS = "Režím bytu nastavený"
OPT_HOLIDAY_SETTING_NAME_CS = "Teplota prázdniny - nastavení"
OPT_HOLIDAY_TARGET_NAME_CS = "Teplota prázdniny nastavená"
OPT_APARTMENT_STATE_NAME_CS = "Aktualní stav bytu"
OPT_APARTMENT_HEATING_NAME_CS = "Režim topení"
OPT_APARTMENT_COOLING_NAME_CS = "Režim chlazení"

# Select states
OPT_APARTMENT_MODE_STATES_EN = {
    "2": "Time plan + heating",
    "4": "Time plan + cooling",
    "8": "Heating komfort",
    "16": "Cooling komfort",
    "32": "Holiday"
}
OPT_APARTMENT_ACTUAL_STATES_EN = {
    "1": "Time plan + heating",
    "2": "Time plan + cooling",
    "4": "Heating komfort",
    "8": "Cooling komfort",
    "16": "Holiday"
}
OPT_APARTMENT_STATE_STATES_EN = {
    "0": "Minimum",
    "1": "Komfort",
}
OPT_APARTMENT_MODE_STATES_CS = {
    "2": "Časový plán + topení",
    "4": "Časový plán + chlazení",
    "8": "Topení komfort",
    "16": "Chlazení komfort",
    "32": "Prázdniny"
}
OPT_APARTMENT_ACTUAL_STATES_CS = {
    "1": "Časový plán + topení",
    "2": "Časový plán + chlazení",
    "4": "Topení komfort",
    "8": "Chlazení komfort",
    "16": "Prázdniny"
}
OPT_APARTMENT_STATE_STATES_CS = {
    "0": "Útlum",
    "1": "Komfort",
}

OPT_ENERGY_NAME_EN = "Energy Readings"
OPT_METER_ELECTRICITY_NAME_EN = "Electricity Meter"
OPT_METER_WATER_COLD_NAME_EN = "Cold Water Meter"
OPT_METER_WATER_HOT_NAME_EN = "Hot Water Meter"
OPT_CALORIMETER_HOT_NAME_EN = "Hot Calorimeter"
OPT_CALORIMETER_COLD_NAME_EN = "Cold Calorimeter"
OPT_ENERGY_NAME_CS = "Odečty energií"
OPT_METER_ELECTRICITY_NAME_CS = "Elektroměr"
OPT_METER_WATER_COLD_NAME_CS = "Voda - studená"
OPT_METER_WATER_HOT_NAME_CS = "Voda - teplá"
OPT_CALORIMETER_HOT_NAME_CS = "Kalorimetr topení"
OPT_CALORIMETER_COLD_NAME_CS = "Kalorimetr chlazení"

OPT_VENTILATION_NAME_EN = "Ventilation"
OPT_VENTILATION_ERROR_NAME_EN = "Fault"
OPT_VENTILATION_FILTER_NAME_EN = "Filters Clogged"
OPT_VENTILATION_STATE_NAME_EN = "State"
OPT_CO2_TARGET_NAME_EN = "CO2 Target"
OPT_CO2_ACTUAL_NAME_EN = "CO2 Actual"
OPT_VENTILATION_FLOW_TARGET_NAME_EN = "Flow Target"
OPT_VENTILATION_IN_NAME_EN = "Inflow"
OPT_VENTILATION_OUT_NAME_EN = "Outflow"
OPT_VENTILATION_FLOW_SETTING_NAME_EN = "Set Flow Target"
OPT_VENTILATION_NAME_CS = "Vzduchotechnika"
OPT_VENTILATION_ERROR_NAME_CS = "Porucha"
OPT_VENTILATION_FILTER_NAME_CS = "Filtry zanešeny"
OPT_VENTILATION_STATE_NAME_CS = "Stav"
OPT_CO2_TARGET_NAME_CS = "CO2 žádaná"
OPT_CO2_ACTUAL_NAME_CS = "CO2 aktuální"
OPT_VENTILATION_FLOW_TARGET_NAME_CS = "Požadovaný průtok ventilátorů"
OPT_VENTILATION_IN_NAME_CS = "Výkon vent.přívod"
OPT_VENTILATION_OUT_NAME_CS = "Výkon vent.odtah"
OPT_VENTILATION_FLOW_SETTING_NAME_CS = "Průtok ventilátorů - nastavení"
