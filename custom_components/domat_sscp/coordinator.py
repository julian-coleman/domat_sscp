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
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CONNECTION_NAME,
    CONF_SSCP_ADDRESS,
    DEFAULT_FAST_COUNT,
    DEFAULT_FAST_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_WRITE_RETRIES,
    DOMAIN,
    OPT_CALENDAR_BASE,
    OPT_CALENDAR_EXCEPTIONS,
    OPT_FAST_COUNT,
    OPT_FAST_INTERVAL,
    OPT_POLLING,
    OPT_SCAN_INTERVAL,
    OPT_WRITE_RETRIES,
)
from .sscp.sscp_connection import sscp_connection
from .sscp.sscp_variable import sscp_variable

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

        if OPT_POLLING in self.config_entry.options:
            polling = self.config_entry.options[OPT_POLLING]
            self.scan_interval = polling.get(
                OPT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
            )
            self.fast_interval = polling.get(
                OPT_FAST_INTERVAL, DEFAULT_FAST_INTERVAL
            )
            self.fast_count = polling.get(
                OPT_FAST_COUNT, DEFAULT_FAST_COUNT
            )
            self.write_retries = polling.get(
                OPT_WRITE_RETRIES, DEFAULT_WRITE_RETRIES
            )
        else:
            self.scan_interval = DEFAULT_SCAN_INTERVAL
            self.fast_interval = DEFAULT_FAST_INTERVAL
            self.fast_count = DEFAULT_FAST_COUNT
            self.write_retries = DEFAULT_WRITE_RETRIES
        self.fast_max = min(self.scan_interval, self.fast_interval * self.fast_count)
        self.update_interval = timedelta(seconds=self.scan_interval)
        _LOGGER.debug(
            "Connection update intervals: %s %s %s (%s) %s",
            self.scan_interval,
            self.fast_interval,
            self.fast_count,
            self.fast_max,
            self.write_retries
        )
        self.last_connect: datetime = datetime.now(tz=None)

    async def _async_update_data(self):
        """Fetch entity data from the server/PLC."""

        # Don't display the password in the log
        conf_data = self.config_entry.data.copy()
        conf_data["password"] = "********"
        _LOGGER.debug("Fetching data for: %s", self.name)
        _LOGGER.debug("Config Data: %s", conf_data)
        _LOGGER.debug("Config Options: %s", self.config_entry.options)

        # Returned data should not be empty, so set at least one entry
        data = {"connection": self.config_entry.unique_id}

        if len(self.config_entry.options) == 0:
            self.data = data
            return self.data

        # Check the last connection time - we don't want to connect too quickly
        # Helps to avoid connecting at the same time as config flow validation and entity writes
        since = datetime.now(tz=None) - self.last_connect
        if since.seconds < self.fast_interval:
            await sleep(self.fast_interval)
        # Are we doing fast updates?  If so, do back-off
        if self.update_interval.seconds < self.fast_max:
            interval = min(
                self.scan_interval, self.update_interval.seconds + self.fast_interval
            )
            self.update_interval = timedelta(seconds=interval)
        else:
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
            _LOGGER.error(
                "Fetching data: could not create a connection for %s", self.name
            )
            raise UpdateFailed from error

        try:
            await conn.login()
            if conn.socket is None:
                _LOGGER.error("Fetching data: login failed for %s", self.name)
                raise ConfigEntryAuthFailed from None
        except TimeoutError:
            _LOGGER.error("Fetching data: login timeout for %s", self.name)
            raise ConfigEntryAuthFailed from None
        except (ValueError, OSError):
            _LOGGER.error("Fetching data: login connection error for %s", self.name)
            raise UpdateFailed from None

        sscp_vars: list[sscp_variable] = []
        sscp_vars.extend(
            sscp_variable(
                uid=self.config_entry.options[opt_var]["uid"],
                offset=self.config_entry.options[opt_var]["offset"],
                length=self.config_entry.options[opt_var]["length"],
                type=self.config_entry.options[opt_var]["type"],
            )
            for opt_var in self.config_entry.options if "uid" in self.config_entry.options[opt_var]
        )
        try:
            error_vars, _error_codes = await conn.sscp_read_variables(sscp_vars)
        except TimeoutError:
            _LOGGER.error("Fetching data: read variables timeout for %s", self.name)
            raise UpdateFailed from None
        except (ValueError, OSError):
            _LOGGER.error("Fetching data: read variables failed for %s", self.name)
            raise UpdateFailed from None
        finally:
            await conn.logout()

        if len(error_vars) > 0:
            _LOGGER.error(
                "Fetching data: read variable errors for %s: %s", self.name, error_vars
            )
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

        _LOGGER.debug("Fetched data: %s", data)
        self.data = data
        return self.data

    async def entity_update(self, vars: list[dict[str:Any]]) -> None:
        """An entity has changed a setting: write and update using fast polling."""

        sscp_vars: list[sscp_variable] = []
        uids: str = ""
        for var in vars:
            uid = var.get("uid")
            offset = var.get("offset")
            length = var.get("length")
            type = var.get("type")
            value = var.get("value")
            raw = var.get("raw")
            uids += str(uid) + " "
            _LOGGER.debug("Entity write: %s %s %s %s = %s", uid, offset, length, type, value)

            sscp_var = sscp_variable(
                uid=uid,
                offset=offset,
                length=length,
                type=type,
                maximum=var.get("maximum"),
                minimum=var.get("minimum"),
                step=var.get("step"),
                states=var.get("states"),
                perm="rw",
            )
            if value is not None:
                sscp_var.change_value(new=value)
            else:
                sscp_var.set_value(raw=raw)
            sscp_vars.append(sscp_var)

        since = datetime.now(tz=None) - self.last_connect
        if since.seconds < self.fast_interval:
            await sleep(self.fast_interval)
        # Try the write a few times, in case we clash with another connection
        retry = 0
        success = False
        while retry < self.write_retries:
            if retry > 0:
                await sleep(self.fast_interval)
                _LOGGER.debug("Retrying write for %s", uids)
            retry += 1
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
                _LOGGER.error(
                    "Entity write: could not create a connection for %s", self.name
                )
                continue

            try:
                await conn.login()
                if conn.socket is None:
                    _LOGGER.error("Entity write: login failed for %s", self.name)
                    continue
            except TimeoutError:
                _LOGGER.error("Entity write: login timeout for %s", self.name)
                continue
            except (ValueError, OSError):
                _LOGGER.error("Entity write: login connection error for %s", self.name)
                continue

            try:
                await conn.sscp_write_variables(vars=sscp_vars)
            except TimeoutError:
                _LOGGER.error("Entity write: write variable timeout for %s", self.name)
                continue
            except (ValueError, OSError) as e:
                _LOGGER.error(
                    "Entity write: write variable failed for %s: %s", self.name, e
                )
                continue
            finally:
                await conn.logout()

            # No exception when writing
            success = True
            break

        if success is not True:
            _LOGGER.error("Entity write failed: %s", uids)
            return

        # Re-read our data using fast polling and send updates to our platforms
        self.update_interval = timedelta(seconds=self.fast_interval)
        with suppress(UpdateFailed):
            await self._async_update_data()
        self.async_set_updated_data(self.data)

    async def schedule_update(self, schedule_id: str, raw: bytearray) -> None:
        """A schedule has changed: we must write base and exceptions together."""

        _LOGGER.debug("Schedule update for %s", schedule_id)

        # Find the base and exceptions schedule entities, and match "schedule_id"
        # Set the values (matched from raw, other from data)
        # Create a vars list and call update
        base = None
        exceptions = None
        base_raw = None
        exceptions_raw = None
        for entity_id in self.config_entry.options:
            if self.config_entry.options[entity_id].get("calendar") == OPT_CALENDAR_BASE:
                base = entity_id
                base_raw = self.data.get(entity_id)
            if self.config_entry.options[entity_id].get("calendar") == OPT_CALENDAR_EXCEPTIONS:
                exceptions = entity_id
                exceptions_raw = self.data.get(entity_id)
        if base is None or exceptions is None:
            _LOGGER.error("Schedule base or exceptions not configured")
            return
        if base_raw is None or exceptions_raw is None:
            _LOGGER.error("Schedule base or exceptions not in data")
            return

        if schedule_id == base:
            base_raw = raw
            _LOGGER.debug("set base: %s", base_raw.hex())
            exceptions_raw = self.data[exceptions]
            _LOGGER.debug("using exceptions: %s", exceptions_raw.hex())
        elif schedule_id == exceptions:
            base_raw = self.data[base]
            _LOGGER.debug("using base: %s", base_raw.hex())
            exceptions_raw = raw
            _LOGGER.debug("set exceptions: %s", exceptions_raw.hex())

        base_var: dict[str:Any] = {
            "uid": self.config_entry.options[base]["uid"],
            "length": self.config_entry.options[base]["length"],
            "offset": self.config_entry.options[base]["offset"],
            "type": self.config_entry.options[base]["type"],
            "raw": base_raw
        }
        exceptions_var: dict[str:Any] = {
            "uid": self.config_entry.options[exceptions]["uid"],
            "length": self.config_entry.options[exceptions]["length"],
            "offset": self.config_entry.options[exceptions]["offset"],
            "type": self.config_entry.options[exceptions]["type"],
            "raw": exceptions_raw
        }
        vars: list[dict[str:Any]] = [base_var, exceptions_var]
        await self.entity_update(vars=vars)

    @callback
    def set_last_connect(self):
        """Set the last connection time: called from other connect functions too."""
        self.last_connect = datetime.now(tz=None)
