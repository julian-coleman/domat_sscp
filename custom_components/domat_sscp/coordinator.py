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

from .const import (
    CONF_CONNECTION_NAME,
    CONF_SSCP_ADDRESS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .sscp_connection import sscp_connection
from .sscp_variable import sscp_variable

_LOGGER = logging.getLogger(__name__)


type DomatSSCPConfigEntry = ConfigEntry[list[DomatSSCPCoordinator]]


class DomatSSCPCoordinator(DataUpdateCoordinator):
    """A co-ordinator to manage fetching SSCP data."""

    data: dict[str, Any]
    config_entry: DomatSSCPConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: DomatSSCPConfigEntry) -> None:
        """Initialize coordinator."""

        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} {config_entry.data[CONF_CONNECTION_NAME]} ({config_entry.unique_id})",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch data from the server and convert it to the right format."""

        # Data should not be empty, so set at least one entry
        data: dict[str, Any] = {"connection": self.config_entry.unique_id}

        conf_data = self.config_entry.data.copy()
        conf_data["password"] = "********"
        _LOGGER.error("Updating data %s", self.name)
        _LOGGER.debug("Data: %s", conf_data)
        _LOGGER.error("Options: %s", self.config_entry.options)

        # TODO Retrieve entities from er
        # Are there any variables to fetch?
        if len(self.config_entry.options) == 0:
            _LOGGER.error("No variables to fetch")
            return data

        try:
            conn = sscp_connection(
                name=self.config_entry.data[CONF_CONNECTION_NAME],
                ip_address=self.config_entry.data[CONF_IP_ADDRESS],
                port=self.config_entry.data[CONF_PORT],
                user_name=self.config_entry.data[CONF_USERNAME],
                password=self.config_entry.data[CONF_PASSWORD],
                sscp_address=self.config_entry.data[CONF_SSCP_ADDRESS],
            )
        except ValueError as error:
            _LOGGER.error("Could not create a connection for %s", self.name)
            raise UpdateFailed from error

        try:
            await conn.login()
            if conn.socket is None:
                _LOGGER.error("Login failed for %s", self.name)
                raise ConfigEntryAuthFailed from None
        except TimeoutError:
            _LOGGER.error("Login timeout for %s", self.name)
            raise ConfigEntryAuthFailed from None
        except (ValueError, OSError):
            _LOGGER.error("Login connection error for %s", self.name)
            raise UpdateFailed from None

        # Fetch variables data
        sscp_vars: list[sscp_variable] = []
        sscp_vars.extend(
            sscp_variable(
                uid=self.config_entry.options[opt_var]["uid"],
                offset=self.config_entry.options[opt_var]["offset"],
                length=self.config_entry.options[opt_var]["length"],
                type=self.config_entry.options[opt_var]["type"],
            )
            for opt_var in self.config_entry.options
        )
        try:
            error_vars, _error_codes = await conn.sscp_read_variables(sscp_vars)
        except TimeoutError:
            _LOGGER.error("Get sscp_var timeout for %s", self.name)
            raise UpdateFailed from None
        except (ValueError, OSError):
            _LOGGER.error("Get variables failed for %s", self.name)
            raise UpdateFailed from None
        finally:
            await conn.logout()

        if len(error_vars) > 0:
            _LOGGER.error("Variable errors for %s: %s", self.name, error_vars)
            raise UpdateFailed from None

        # Update variables with converted data
        for sscp_var in sscp_vars:
            _LOGGER.debug(
                "Updated %d to 0x%s (%s)",
                sscp_var.uid,
                sscp_var.raw.hex(),
                sscp_var.val,
            )
            # Our entity ID's are uid-length-offset of the variable
            entity_id = (
                str(sscp_var.uid)
                + "-"
                + str(sscp_var.offset)
                + "-"
                + str(sscp_var.length)
            )
            data[entity_id] = sscp_var.val

        return data
