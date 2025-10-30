"""SSCP (Shark Slave Communications Protocol) basic communications.

See Also:
  https://kb.mervis.info/lib/exe/fetch.php/cs:mervis-ide:sharkprotocolspecification_user_2017_05_30.pdf
"""

import asyncio
from errno import errorcode
from hashlib import md5
import logging
import select
import socket

from .sscp_const import (
    SSCP_DATA_ORDER,
    SSCP_DATALEN_END,
    SSCP_DATALEN_START,
    SSCP_GROUP_END,
    SSCP_GROUP_START,
    SSCP_GUID_END,
    SSCP_GUID_START,
    SSCP_INFO_ENDIAN_LEN,
    SSCP_INFO_OFFSET,
    SSCP_INFO_PLATFORM_LEN,
    SSCP_INFO_REQUEST,
    SSCP_INFO_SERIAL,
    SSCP_INFO_SERIAL_END,
    SSCP_INFO_SERIAL_START,
    SSCP_INFO_SIZE,
    SSCP_INFO_VERSION,
    SSCP_INFO_VERSION_LEN,
    SSCP_LOGIN_REQUEST,
    SSCP_LOGOUT_DATA_LEN,
    SSCP_LOGOUT_REQUEST,
    SSCP_MAXDATA_END,
    SSCP_MAXDATA_START,
    SSCP_PROTOCOL_VERSION,
    SSCP_RECV_MAX,
    SSCP_RECV_MAX_BYTES,
    SSCP_TIMEOUT_CONNECT,
    SSCP_TIMEOUT_DATA,
    SSCP_VERSION_END,
    SSCP_VERSION_START,
)

_LOGGER = logging.getLogger(__name__)


class sscp_connection:
    """SSCP Connection.

    Handles configuration, login, logout, read variables and write variables.
    """

    def __init__(
        self,
        name,
        ip_address,
        port,
        user_name,
        sscp_address,
        password=None,
        md5_hash=None,
    ) -> None:
        """Configure the SSCP connection with individual parameters.

        Either a password or an MD5 hash can be passed in.
        """

        self.name = name
        self.ip_address = ip_address
        self.port = int(port)
        self.user_name = user_name
        self.password = password
        self.md5_hash = md5_hash
        self.sscp_address = int(sscp_address)

        self.user_enc = user_name.encode("utf-8")
        self.user_len = len(self.user_enc).to_bytes(1, SSCP_DATA_ORDER)
        if self.md5_hash is None:
            if self.password is None:
                raise (ValueError("Missing password or MD5"))
            self.md5_hash = md5(self.password.encode()).hexdigest()
            self.md5_bytes = bytearray()
            for i in range(0, 31, 2):
                self.md5_bytes += int(self.md5_hash[i : i + 2], 16).to_bytes(
                    1, SSCP_DATA_ORDER
                )
        self.md5_len = len(self.md5_bytes).to_bytes(1, SSCP_DATA_ORDER)
        self.addr_byte = self.sscp_address.to_bytes(1, SSCP_DATA_ORDER)

        self.socket = None
        self.sockfd = 0
        self.send_max = 0
        self.serial = None
        self.platform = None

    @classmethod
    def from_yaml(cls, yaml) -> None:
        "Configure the SSCP connection with paramaters via YAML."

        cls(
            name=yaml["name"],
            ip_address=yaml["ipAddress"],
            port=yaml["port"],
            sscp_address=yaml["sscpAddress"],
            user_name=yaml["userName"],
            md5_hash=yaml["md5"],
        )

    async def login(self) -> bool:
        """Log in to the SSCP server/PLC.

        Create a socket connection to the server.
        Use the connection parameters to log in.
        Can raise ConnectionError, OSError, or exceptions from sendrecv().
        """

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(SSCP_TIMEOUT_CONNECT)
        self.socket.setblocking(False)
        self.sockfd = self.socket.fileno()
        try:
            self.socket.connect((self.ip_address, self.port))
        except ConnectionError as e:
            _LOGGER.error("Login: Connect failed: %s", e)
            if self.socket is not None:
                self.socket.close()
                self.socket = None
            raise ConnectionError from e
        except OSError as e:
            if e.errno != 115:  # Operation in progress
                _LOGGER.error("Login: Connect failed: %s", e)
                if self.socket is not None:
                    self.socket.close()
                    self.socket = None
                raise OSError from e
        # Wait for the socket to connect, or timeout
        t = 0
        while True:
            if self.socket is None:
                _LOGGER.error("Socket connect failed")
                raise ConnectionError("Socket connect failed")
            stat = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if stat != 0:
                _LOGGER.error("Login: connect failed: %s", errorcode[stat])
                raise ConnectionError(errorcode[stat])
            _rlist, wlist, _xlist = select.select([], [self.sockfd], [], 0)
            if len(wlist) == 0:
                await asyncio.sleep(1)
                t += 1
                if t == SSCP_TIMEOUT_CONNECT:
                    _LOGGER.error("Socket connect timeout")
                    raise ConnectionError("Socket connect timeout")
            else:
                break

        data = bytearray()
        data += SSCP_PROTOCOL_VERSION
        data += SSCP_RECV_MAX_BYTES
        data += self.user_len
        data += self.user_enc
        data += self.md5_len
        data += self.md5_bytes
        data_len = len(data)

        request = bytearray()
        request += self.addr_byte
        request += SSCP_LOGIN_REQUEST
        request += data_len.to_bytes(2, SSCP_DATA_ORDER)
        request += data

        # Pass exceptions back to our caller
        reply = await self.sscp_sendrecv(request, "Login")
        if len(reply) == 0:
            if self.socket is not None:
                self.socket.close()
                self.socket = None
            return False

        self.send_max = int.from_bytes(reply[SSCP_MAXDATA_START:SSCP_MAXDATA_END])
        _LOGGER.debug(
            "protocol vers.: %d",
            int.from_bytes(reply[SSCP_VERSION_START:SSCP_VERSION_END], SSCP_DATA_ORDER),
        )
        _LOGGER.debug("max. data len.: %d", self.send_max)
        _LOGGER.debug(
            "rights group: %d",
            int.from_bytes(reply[SSCP_GROUP_START:SSCP_GROUP_END], SSCP_DATA_ORDER),
        )
        _LOGGER.debug("image guid: %s", reply[SSCP_GUID_START:SSCP_GUID_END].hex())
        if len(reply) > SSCP_GUID_END:
            _LOGGER.debug("optional data: %s", reply[SSCP_GUID_END:].hex())

        return True

    async def logout(self):
        """Log out from the SSCP server/PLC."""

        request = bytearray()
        request += self.addr_byte
        request += SSCP_LOGOUT_REQUEST
        request += SSCP_LOGOUT_DATA_LEN

        await self.sscp_sendrecv(request, "Logout", close_after_send=True)

    async def get_info(self):
        """Get basic info about the SSCP server/PLC.

        Can raise exceptions from sendrecv().
        """

        data = bytearray()
        data += SSCP_INFO_VERSION
        data += SSCP_INFO_SERIAL
        data += self.user_len
        data += self.user_enc
        data += self.md5_len
        data += self.md5_bytes
        data += SSCP_INFO_OFFSET
        data += SSCP_INFO_SIZE
        data_len = len(data)

        request = bytearray()
        request += self.addr_byte
        request += SSCP_INFO_REQUEST
        request += data_len.to_bytes(2, SSCP_DATA_ORDER)
        request += data

        # Pass exceptions back to our caller
        reply = await self.sscp_sendrecv(request, "Info ")
        if len(reply) == 0:
            return False

        start = SSCP_INFO_SERIAL_START
        end = SSCP_INFO_SERIAL_END
        serial_len = int.from_bytes(reply[start:end], SSCP_DATA_ORDER)
        start = end
        end = start + serial_len
        self.serial = reply[start:end].hex()
        _LOGGER.debug("serial number: %s", self.serial)
        start = end
        end += SSCP_INFO_ENDIAN_LEN
        _LOGGER.debug("endianness %s", reply[start:end].hex())
        start = end
        end += SSCP_INFO_PLATFORM_LEN
        self.platform = reply[start:end].hex()
        _LOGGER.debug("platform id: %s", self.platform)
        start = end
        end += SSCP_INFO_VERSION_LEN
        version_len = int.from_bytes(reply[start:end], SSCP_DATA_ORDER)
        start = end
        end += version_len
        _LOGGER.debug("runtime vers.: %s", reply[start:end].hex())
        if len(reply) > end:
            _LOGGER.debug("information: %s", reply[end:].hex())

        return True

    async def sscp_sendrecv(
        self, request, prefix="Socket", close_after_send=False
    ) -> bytearray:
        """Send/receive data on the socket.

        Ensure that socket is ready for write or read.
        Ensure that we read enough data from the socket for a complete reply.
        Handle socket errors.
        Can raise ConnectionError or OSError if no data can be sent.
        Can raise TimeoutError if no data can be received.
        Can raise ValueError if unexpected data is received.
        If close_after_send is True, no exceptions are raised and the socket is always closed.
        """

        if self.socket is None:
            if close_after_send is not True:
                _LOGGER.error("%s: send/recv without socket", prefix)
                raise ConnectionError("Socket not writeable")
            return bytearray()

        # Write the request
        try:
            _rlist, wlist, _xlist = select.select([], [self.sockfd], [], 0)
            if len(wlist) == 0:
                if self.socket is not None:
                    self.socket.close()
                    self.socket = None
                if close_after_send is not True:
                    _LOGGER.error("%s: socket not writeable", prefix)
                    raise ConnectionError("Socket not writeable")
                return bytearray()

            _LOGGER.debug("%s request: %s", prefix, request.hex())
            self.socket.sendall(request)
        except OSError as e:
            if self.socket is not None:
                self.socket.close()
                self.socket = None
            if close_after_send is not True:
                _LOGGER.error("%s: send failed: %s", prefix, e)
                raise OSError from e
            return bytearray()

        if close_after_send is True:
            self.socket.close()
            self.socket = None
            return bytearray()

        reply = bytearray()

        # Read at least as far as the data length
        t = 0
        while len(reply) < SSCP_DATALEN_END:
            rlist, _wlist, _xlist = select.select([self.sockfd], [], [], 0)
            if len(rlist) > 0:
                reply += self.socket.recv(SSCP_RECV_MAX - len(reply))
            if len(reply) < SSCP_DATALEN_END:
                await asyncio.sleep(1)
                t += 1
                if t >= SSCP_TIMEOUT_DATA:
                    _LOGGER.error("%s: receive header timeout", prefix)
                    if self.socket is not None:
                        self.socket.close()
                        self.socket = None
                    raise TimeoutError("Receive header timeout")

        data_len = int.from_bytes(
            reply[SSCP_DATALEN_START:SSCP_DATALEN_END], SSCP_DATA_ORDER
        )
        if data_len > SSCP_RECV_MAX:
            _LOGGER.error("%s: unexpected data received", prefix)
            self.socket.close()
            self.socket = None
            raise ValueError("Unexpected data received")

        # Read the rest of the data
        t = 0
        while len(reply) < SSCP_DATALEN_END + data_len:
            rlist, _wlist, _xlist = select.select([self.sockfd], [], [], 0)
            if len(rlist) > 0:
                reply += self.socket.recv(SSCP_RECV_MAX - len(reply))
            if len(reply) < SSCP_DATALEN_END + data_len:
                await asyncio.sleep(1)
                t += 1
                if t >= SSCP_TIMEOUT_DATA:
                    _LOGGER.error("%s: receive data timeout", prefix)
                    if self.socket is not None:
                        self.socket.close()
                        self.socket = None
                    raise TimeoutError("Receive data timeout")

        _LOGGER.debug("%s reply: %s", prefix, reply.hex())
        return reply
