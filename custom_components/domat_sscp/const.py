"""Constants for the Domat SSCP integration."""

# Integration name
DOMAIN = "domat_sscp"

# Configuration flow constants
CONF_CONNECTION_NAME = "connection_name"
CONF_SSCP_ADDRESS = "sscp_address"
CONF_LANGUAGE = "language"
CONF_INSADY = "insady"

# Configuration defaults
DEFAULT_SCAN_INTERVAL = 300
DEFAULT_FAST_INTERVAL = 3
DEFAULT_FAST_COUNT = 5
DEFAULT_WRITE_RETRIES = 5
DEFAULT_SSCP_PORT = 12346
DEFAULT_SSCP_ADDRESS = 1

# Options flow constants
OPT_VARIABLES = "variables"
OPT_SCHEDULES = "schedules"
OPT_POLLING = "polling"
OPT_SCAN_INTERVAL = "scan_interval"
OPT_FAST_INTERVAL = "fast_interval"
OPT_FAST_COUNT = "fast_count"
OPT_WRITE_RETRIES = "write_retries"

OPT_DEVICE = "device"
OPT_EXISTING_DEVICE = "existing_device"
OPT_NAME = "name"
OPT_UID = "uid"
OPT_OFFSET = "offset"
OPT_LENGTH = "length"
OPT_MINIMUM = "minimum"
OPT_MAXIMUM = "maximum"
OPT_STEP = "step"
OPT_ENTITY = "entity"

# Calendar constants
OPT_CALENDAR_BASE = "calendar_base"
OPT_CALENDAR_EXCEPTIONS = "calendar_exceptions"
