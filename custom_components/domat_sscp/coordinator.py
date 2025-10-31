"""Data update co-ordinator for the Domat SSCP integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .sscp_connection import sscp_connection
from .sscp_const import (
    CONF_CONNECTION_NAME,
    CONF_SSCP_ADDRESS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


type DomatSSCPConfigEntry = ConfigEntry[list[DomatSSCPCoordinator]]


class DomatSSCPCoordinator(DataUpdateCoordinator):
    """A co-ordinator to manage fetching SSCP data."""

    data: list[dict[str, Any]]

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # From config flow
        self.connection_name = config_entry.data[CONF_CONNECTION_NAME]
        self.ip_address = config_entry.data[CONF_IP_ADDRESS]
        self.port = config_entry.data[CONF_PORT]
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data[CONF_PASSWORD]
        self.sscp_address = config_entry.data[CONF_SSCP_ADDRESS]

        # From options
        self.poll_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} {config_entry.data[CONF_CONNECTION_NAME]} ({config_entry.unique_id})",
            update_interval=timedelta(seconds=self.poll_interval),
        )

    async def _async_update_data(self):
        """Fetch data from the server and convert it to the right format."""

        _LOGGER.error("Updating %s", self.connection_name)
        try:
            conn = sscp_connection(
                name=self.connection_name,
                ip_address=self.ip_address,
                port=self.port,
                user_name=self.username,
                password=self.password,
                sscp_address=self.sscp_address,
            )
        except ValueError as error:
            _LOGGER.error("Could not create a connection object")
            raise UpdateFailed from error

        try:
            await conn.login()
            if conn.socket is None:
                _LOGGER.debug("Login failed")
                _LOGGER.error("Login failed")
                raise ConfigEntryAuthFailed from None
        except TimeoutError:
            _LOGGER.debug("Login timeout")
            _LOGGER.error("Login timeout")
            raise ConfigEntryAuthFailed from None
        except (ValueError, OSError):
            _LOGGER.debug("Login connection error")
            _LOGGER.error("Login connection error")
            raise UpdateFailed from None

        data = ["dummy", "dummy"]

        await conn.logout()
        _LOGGER.error("All OK")
        return data
