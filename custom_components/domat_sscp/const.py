"""Constants for the Domat SSCP integration."""

# Integration name
DOMAIN = "domat_sscp"

# Configuration flow constants
CONF_CONNECTION_NAME = "connection_name"
CONF_SSCP_ADDRESS = "sscp_address"

# Configuration defaults
DEFAULT_SCAN_INTERVAL = 180
DEFAULT_FAST_INTERVAL = 3
DEFAULT_FAST_COUNT = 10
DEFAULT_SSCP_PORT = 12346
DEFAULT_SSCP_ADDRESS = 1

# Options flow constants
OPT_DEVICE = "device"
OPT_NAME = "name"
OPT_TEMPERATURE = "temperature"
OPT_HUMIDITY = "humidity"
OPT_METER_ELECTRICITY = "meter_electricity"
OPT_METER_WATER_COLD = "meter_water_cold"
OPT_METER_WATER_HOT = "meter_water_hot"
OPT_CALORIMETER_HOT = "calorimeter_hot"
OPT_CALORIMETER_COLD = "calorimeter_cold"
OPT_VENTILATION_IN = "ventilator_in"
OPT_VENTILATION_OUT = "ventilator_out"
OPT_CO2 = "cotwo"
OPT_VENTILATION_ERROR = "ventilator_error"
OPT_VENTILATION_FLOW = "ventilator_flow"
OPT_UID = "UID"
OPT_OFFSET = "offset"
OPT_LENGTH = "length"
OPT_MINIMUM = "minimum"
OPT_MAXIMUM = "minimum"

# Variable defaults
OPT_VENTILATION_FLOW_MINIMUM = 80
OPT_VENTILATION_FLOW_MAXIMUM = 200
