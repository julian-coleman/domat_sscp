"""Data update co-ordinator for the Domat SSCP integration."""

from __future__ import annotations

from asyncio import sleep
from contextlib import suppress
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CONNECTION_NAME,
    CONF_SSCP_ADDRESS,
    DEFAULT_FAST_COUNT,
    DEFAULT_FAST_INTERVAL,
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
        )

        self.data: dict[str, Any] = {}
        self.scan_interval = self.config_entry.data.get(
            "default_scan_interval", DEFAULT_SCAN_INTERVAL
        )
        self.fast_interval = self.config_entry.data.get(
            "default_fast_interval", DEFAULT_FAST_INTERVAL
        )
        self.fast_count = self.config_entry.data.get(
            "default_fast_count", DEFAULT_FAST_COUNT
        )
        self.fast_remaining = self.fast_count
        self.update_interval = timedelta(seconds=self.scan_interval)
        _LOGGER.error(
            "Coordinator update intevals: %s %s (%s)",
            self.scan_interval,
            self.fast_interval,
            self.fast_count,
        )
        # Set to the past because we'll update ~immediately on first refresh
        self.last_connect: datetime = datetime.now(tz=None) - timedelta(
            seconds=DEFAULT_FAST_INTERVAL
        )
        entity_registry = er.async_get(self.hass)

        # Check entity registry against options
        for entity in entity_registry.entities.get_entries_for_config_entry_id(
            self.config_entry.entry_id
        ):
            if entity.unique_id not in self.config_entry.options:
                _LOGGER.error(
                    "Entity %s in registry but not in options", entity.unique_id
                )

    async def _async_update_data(self):
        """Fetch entity data from the server/PLC."""

        # Returned data should not be empty, so set at least one entry
        data = {"connection": self.config_entry.unique_id}

        conf_data = self.config_entry.data.copy()
        conf_data["password"] = "********"
        _LOGGER.error("Updating data for: %s", self.name)
        _LOGGER.debug("Config Data: %s", conf_data)
        _LOGGER.debug("Config Options: %s", self.config_entry.options)

        if len(self.config_entry.options) == 0:
            self.data = data
            return self.data

        # Check the last connection time
        # We set the time when we finish, so want a pause if the server is slow
        # Helps to avoid connecting at the same time as config flow validation and entity writes
        since = datetime.now(tz=None) - self.last_connect
        if since.seconds < DEFAULT_FAST_INTERVAL:
            await sleep(DEFAULT_FAST_INTERVAL - since.seconds)
        # Are we doing fast updates?
        if self.update_interval.seconds == self.fast_interval:
            self.fast_remaining -= 1
            if self.fast_remaining <= 0:
                self.fast_remaining = self.fast_count
                self.update_interval = timedelta(seconds=self.scan_interval)

        # Fetch variables data
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
            _LOGGER.error("Read variables timeout for %s", self.name)
            raise UpdateFailed from None
        except (ValueError, OSError):
            _LOGGER.error("Read variables failed for %s", self.name)
            raise UpdateFailed from None
        finally:
            await conn.logout()

        if len(error_vars) > 0:
            _LOGGER.error("Read variable errors for %s: %s", self.name, error_vars)
            raise UpdateFailed from None

        # Update variables with converted data
        for sscp_var in sscp_vars:
            # Recreate entity ID's (uid-length-offset) for our data
            entity_id = (
                str(sscp_var.uid)
                + "-"
                + str(sscp_var.offset)
                + "-"
                + str(sscp_var.length)
            )
            data[entity_id] = sscp_var.val

        self.set_last_connect()

        _LOGGER.debug("Data: %s", data)
        self.data = data
        return self.data

    async def entity_update(
        self,
        uid: int,
        offset: int,
        length: int,
        type: int,
        value: Any,
        increment: float | None = None,
        maximum: float | None = None,
        decrement: float | None = None,
        minimum: float | None = None,
        states: dict[str, Any] | None = None,
    ) -> None:
        """An entity has changed a setting: update using fast polling."""

        _LOGGER.error("Entity update: %s %s %s %s %s", uid, offset, length, type, value)
        since = datetime.now(tz=None) - self.last_connect
        if since.seconds < DEFAULT_FAST_INTERVAL:
            await sleep(DEFAULT_FAST_INTERVAL - since.seconds)

        sscp_var = sscp_variable(
            uid=uid,
            offset=offset,
            length=length,
            type=type,
            increment=increment,
            maximum=maximum,
            decrement=decrement,
            minimum=minimum,
            states=states,
            perm="rw",
        )

        self.set_last_connect()
        try:
            conn = sscp_connection(
                name=self.config_entry.data[CONF_CONNECTION_NAME],
                ip_address=self.config_entry.data[CONF_IP_ADDRESS],
                port=self.config_entry.data[CONF_PORT],
                user_name=self.config_entry.data[CONF_USERNAME],
                password=self.config_entry.data[CONF_PASSWORD],
                sscp_address=self.config_entry.data[CONF_SSCP_ADDRESS],
            )
        except ValueError:
            _LOGGER.error("Could not create a connection for %s", self.name)
            return

        try:
            await conn.login()
            if conn.socket is None:
                _LOGGER.error("Login failed for %s", self.name)
                return
        except TimeoutError:
            _LOGGER.error("Login timeout for %s", self.name)
            return
        except (ValueError, OSError):
            _LOGGER.error("Login connection error for %s", self.name)
            return
        try:
            res = await conn.sscp_write_variable(var=sscp_var, new=value)
        except TimeoutError:
            _LOGGER.error("Write variable timeout for %s", self.name)
            return
        except (ValueError, OSError) as e:
            _LOGGER.error("Write variable failed for %s: %s", self.name, e)
            return
        finally:
            await conn.logout()

        if res:
            _LOGGER.error("Write variable error for %s", self.name)
            return

        # Re-read our data using fast polling and send updates to our platforms
        self.update_interval = timedelta(seconds=self.fast_interval)
        with suppress(UpdateFailed):
            await self._async_update_data()
        self.async_set_updated_data(self.data)

    @callback
    def set_last_connect(self):
        """Set the last connection time: called from other connect functions too."""
        self.last_connect = datetime.now(tz=None)
