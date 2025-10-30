"""Data update co-ordinator for the Domat SSCP integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CONNECTION_NAME,
    CONF_SSCP_ADDRESS,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class DomatSSCPCoordinator(DataUpdateCoordinator):
    """A co-ordinator to manage fetching SSCP data."""

    data: list[dict[str, Any]]

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        self.ip = config_entry.data[CONF_IP_ADDRESS]
        self.port = config_entry.data[CONF_PORT]
        self.user = config_entry.data[CONF_USERNAME]
        self.addr = config_entry.data[CONF_SSCP_ADDRESS]

        self.poll_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_POLL_INTERVAL
        )

        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} {config_entry[CONF_CONNECTION_NAME]} ({config_entry.unique_id})",
            update_interval=timedelta(seconds=self.poll_interval),
        )

    async def _async_update_data(self):
        """Fetch data from the server and convert it to the right format."""
