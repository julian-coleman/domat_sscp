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
OPT_TEMPERATURE_TARGET = "temperature_target"
OPT_TEMPERATURE = "temperature"
OPT_HUMIDITY = "humidity"
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
OPT_UID = "uid"
OPT_OFFSET = "offset"
OPT_LENGTH = "length"
OPT_MINIMUM = "minimum"
OPT_MAXIMUM = "maximum"
OPT_STEP = "step"

# Variable defaults
OPT_TEMPERATURE_TARGET_MINIMUM = 16
OPT_TEMPERATURE_TARGET_MAXIMUM = 30
OPT_TEMPERATURE_TARGET_STEP = 0.5
OPT_VENTILATION_FLOW_MINIMUM = 80
OPT_VENTILATION_FLOW_MAXIMUM = 200

# Name defaults
OPT_ROOM_CONTROLS_NAME_EN="Room Controls"
OPT_TEMPERATURE_NAME_EN="Actual temperature"
OPT_HUMIDITY_NAME_EN="Actual humidity"
OPT_TEMPERATURE_TARGET_NAME_EN="Target temperature"
OPT_ROOM_CONTROLS_NAME_CS="Ovládání pokoje"
OPT_TEMPERATURE_NAME_CS="Teplota aktuální"
OPT_HUMIDITY_NAME_CS="Vlhkost aktuální"
OPT_TEMPERATURE_TARGET_NAME_CS="Teplota žádaná"

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
