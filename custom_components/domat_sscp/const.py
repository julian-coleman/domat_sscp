"""Constants for the Domat SSCP integration."""

# Integration name
DOMAIN = "domat_sscp"

# Configuration flow constants
CONF_CONNECTION_NAME = "connection_name"
CONF_SSCP_ADDRESS = "sscp_address"

# Configuration defaults
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_SSCP_PORT = 12346
DEFAULT_SSCP_ADDRESS = 1

# Options flow constants
OPT_NAME = "name"
OPT_TEMPERATURE = "temperature"
OPT_HUMIDITY = "humidity"
OPT_METER_ELECTRICITY = "meter_electricity"
OPT_WATER_COLD = "water_cold"
OPT_WATER_HOT = "water_hot"
OPT_CALORIMETER_COLD = "calorimeter_cold"
OPT_CALORIMETER_HOT = "calorimeter_hot"
OPT_VENTILATOR_IN = "ventilator_in"
OPT_VENTILATOR_OUT = "ventilator_out"
OPT_CO2 = "cotwo"
OPT_VENTILATOR_ERROR = "ventilator_error"
OPT_VENTILATOR_FLOW = "ventilator_flow"
OPT_UID = "UID"
OPT_OFFSET = "offset"
OPT_LENGTH = "length"
OPT_MINIMUM = "minimum"
OPT_MAXIMUM = "minimum"

# Variable defaults
OPT_VENTILATOR_FLOW_MINIMUM = 80
OPT_VENTILATOR_FLOW_MAXIMUM = 200
