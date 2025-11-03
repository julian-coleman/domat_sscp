"""SSCP Constants."""

# SSCP packet format constants
# Wire endianness
SSCP_DATA_ORDER = "big"
# Start and end bytes of received status
SSCP_STATUS_START = 1
SSCP_STATUS_END = 3
# Start and end bytes of received data length
SSCP_DATALEN_START = 3
SSCP_DATALEN_END = 5

# Login function
SSCP_LOGIN_REQUEST = bytes("\x01\x00", encoding="iso-8859-1")
# Parameters we send
# Version we offer
SSCP_PROTOCOL_VERSION = bytes("\x01", encoding="iso-8859-1")
# Max. size of received data (arbitrary value)
SSCP_RECV_MAX = 2048
SSCP_RECV_MAX_BYTES = SSCP_RECV_MAX.to_bytes(2, SSCP_DATA_ORDER)
# Parameters we receive
# Start and end bytes of received version
SSCP_VERSION_START = 5
SSCP_VERSION_END = 6
# Start and end bytes of received maxdata value
SSCP_MAXDATA_START = 6
SSCP_MAXDATA_END = 8
# Start and end bytes of received group value
SSCP_GROUP_START = 8
SSCP_GROUP_END = 9
# Start and end bytes of received guid value
SSCP_GUID_START = 9
SSCP_GUID_END = 25

# Logout function
SSCP_LOGOUT_REQUEST = bytes("\x01\x01", encoding="iso-8859-1")
# Fixed logout length
SSCP_LOGOUT_DATA_LEN = bytes("\x00\x00", encoding="iso-8859-1")

# Get info function
SSCP_INFO_REQUEST = bytes("\x00\x00", encoding="iso-8859-1")
# Version we offer
SSCP_INFO_VERSION = bytes("\x01", encoding="iso-8859-1")
# Our serial number
SSCP_INFO_SERIAL = bytes("\x00", encoding="iso-8859-1")
# Memory region offset
SSCP_INFO_OFFSET = bytes("\x00\x00", encoding="iso-8859-1")
# Size of block
SSCP_INFO_SIZE = bytes("\x00\x00", encoding="iso-8859-1")
# Start and end bytes of received serial length
SSCP_INFO_SERIAL_START = 7
SSCP_INFO_SERIAL_END = 8
# Byte lengths of received parameters
SSCP_INFO_ENDIAN_LEN = 1
SSCP_INFO_PLATFORM_LEN = 4
SSCP_INFO_VERSION_LEN = 1

# Maximum variables for read or write requests
SSCP_DATA_MAX_VAR = 64
# Read data function
SSCP_READ_DATA_REQUEST = bytes("\x05\x00", encoding="iso-8859-1")
# Flags for offset + length
SSCP_READ_DATA_FLAGS = bytes("\x80", encoding="iso-8859-1")
# Read succesfull for all variables
SSCP_READ_DATA_SUCCESS = bytes("\x85\x00", encoding="iso-8859-1")
# Write data function
SSCP_WRITE_DATA_REQUEST = bytes("\x05\x10", encoding="iso-8859-1")
# Flags for offset + length (as per read)
SSCP_WRITE_DATA_FLAGS = SSCP_READ_DATA_FLAGS
# Write len for 1 variable
SSCP_WRITE_DATA_1VARIABLE = bytes("\x01", encoding="iso-8859-1")
# Write succesfull for all variables
SSCP_WRITE_DATA_SUCCESS = bytes("\x85\x10", encoding="iso-8859-1")
# Start and end bytes of received error code
SSCP_ERROR_CODE_START = 7
SSCP_ERROR_CODE_END = 9
# Start and end bytes of received error variables
SSCP_ERROR_VARS_START = 9
SSCP_ERROR_VARS_END = 17

# Error codes (not all)
SSCP_ERRORS = {
    0x0103: "No Such Variable",
    0x010A: "Write Failed",
    0x010D: "Data Too Long",
    0x0110: "Variable Count Limit Exceeded",
    0x0112: "Size Mismatch",
}

# Schedule constants
SCHEDULE_OFF = (0).to_bytes(2, SSCP_DATA_ORDER)
SCHEDULE_ON = (1).to_bytes(2, SSCP_DATA_ORDER)
# Start and end bytes of schedule parameters
SCHEDULE_BASETPG_LEN = 8
SCHEDULE_BASETPG_MINS_START = 0
SCHEDULE_BASETPG_MINS_END = 2
SCHEDULE_BASETPG_STATE_START = 4
SCHEDULE_BASETPG_STATE_END = 6
SCHEDULE_EXCEPTIONS_LEN = 12
SCHEDULE_EXCEPTIONS_BASE_YEAR = 2000
SCHEDULE_EXCEPTIONS_YEAR1_START = 0
SCHEDULE_EXCEPTIONS_YEAR1_END = 1
SCHEDULE_EXCEPTIONS_MINS1_START = 1
SCHEDULE_EXCEPTIONS_MINS1_END = 4
SCHEDULE_EXCEPTIONS_YEAR2_START = 4
SCHEDULE_EXCEPTIONS_YEAR2_END = 5
SCHEDULE_EXCEPTIONS_MINS2_START = 5
SCHEDULE_EXCEPTIONS_MINS2_END = 8
SCHEDULE_EXCEPTIONS_STATE_START = 8
SCHEDULE_EXCEPTIONS_STATE_END = 10
SCHEDULE_EXCEPTIONS_BASE_EPOCH_SECS = 946681200  # 01.01.2000 00:00

# Time constants
MINS_PER_DAY = 1440

# IEEE754 constants
IEEE754_SIGN = 0x80000000
IEEE754_EXPONENT = 0x7F800000
IEEE754_SIGNIFICAND = 0x007FFFFF
IEEE754_MAXIMUM_BITS = 32
IEEE754_EXPONENT_SHIFT = 23
IEEE754_EXPONENT_BIAS = 127
IEEE754_SIGNIFICAND_LENGTH = IEEE754_EXPONENT_SHIFT

# Timeout defaults
SSCP_TIMEOUT_CONNECT = 30
SSCP_TIMEOUT_DATA = 10
