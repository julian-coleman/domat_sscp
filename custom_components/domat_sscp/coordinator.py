"""Data update co-ordinator for the Domat SSCP integration."""

from __future__ import annotations

from asyncio import sleep
from datetime import datetime, timedelta
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
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
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
        if "default_scan_interval" in self.config_entry.data:
            self.scan_interval = self.config_entry.data["default_scan_interval"]
        else:
            self.scan_interval = DEFAULT_SCAN_INTERVAL
        self.update_interval = timedelta(seconds=self.scan_interval)
        if "default_fast_interval" in self.config_entry.data:
            self.fast_interval = self.config_entry.data["default_fast_interval"]
        else:
            self.fast_interval = DEFAULT_SCAN_INTERVAL
        if "default_fast_count" in self.config_entry.data:
            self.fast_count = self.config_entry.data["default_fast_count"]
        else:
            self.fast_count = DEFAULT_SCAN_INTERVAL
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
        """Fetch data from the server and convert it to the right format."""

        # TODO: Change update interval (based on entity state changes)

        # Data should not be empty, so set at least one entry
        self.data = {"connection": self.config_entry.unique_id}

        conf_data = self.config_entry.data.copy()
        conf_data["password"] = "********"
        _LOGGER.error("Updating data for: %s", self.name)
        _LOGGER.debug("Data: %s", conf_data)
        _LOGGER.debug("Options: %s", self.config_entry.options)

        if len(self.config_entry.options) == 0:
            return self.data

        # Check the last connection time
        since = datetime.now(tz=None) - self.last_connect
        if since.seconds < DEFAULT_FAST_INTERVAL:
            _LOGGER.error("Connecting too quickly: %s", self.update_interval)
            await sleep(DEFAULT_FAST_INTERVAL - since.seconds)
        _LOGGER.error("Time since last update: %s", since)

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
            _LOGGER.error("Variable errors for %s: %s", self.name, error_vars)
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
            self.data[entity_id] = sscp_var.val

        self.last_connect = datetime.now(tz=None)

        _LOGGER.debug("Data: %s", self.data)
        return self.data

    async def validate_config(
        self,
        data: dict[str, Any],
        variables: list[sscp_variable] | None,
    ) -> dict[str, Any]:
        """Validate the config_flow input using the values provided.

        Check that we can connect and login.
        Check that we can fetch variables.

        Can raise InvalidAuth or exceptions from sscp methods.
        """

        # Data config flow info
        serial = ""
        # Options config flow info
        error_code = 0
        error_vars_str = ""

        # Check the last connection time
        since = datetime.now(tz=None) - self.last_connect
        if since.seconds < DEFAULT_FAST_INTERVAL:
            _LOGGER.error("Validating too quickly: %s", self.update_interval)
            await sleep(DEFAULT_FAST_INTERVAL - since.seconds)
        _LOGGER.error("Time since last update: %s", since)

        conn = sscp_connection(
            name=data[CONF_CONNECTION_NAME],
            ip_address=data[CONF_IP_ADDRESS],
            port=data[CONF_PORT],
            user_name=data[CONF_USERNAME],
            password=data[CONF_PASSWORD],
            sscp_address=data[CONF_SSCP_ADDRESS],
            md5_hash=None,
        )

        await conn.login()
        if conn.socket is None:
            _LOGGER.debug("Login failed")
            raise InvalidAuth from None

        if variables is None:
            # Config flow
            await conn.get_info()
            if conn.serial is None:
                _LOGGER.error("No serial number for %s", data[CONF_CONNECTION_NAME])
                serial = CONF_USERNAME + "-" + CONF_SSCP_ADDRESS + "-00000000"
            else:
                serial = CONF_USERNAME + "-" + CONF_SSCP_ADDRESS + "-" + conn.serial
            _LOGGER.info("Using unique ID: %s", serial)
        else:
            # Options flow
            error_vars, error_codes = await conn.sscp_read_variables(variables)
            if len(error_vars) > 0:
                error_code = error_codes[0]  # We only display the first error
            for var in error_vars:
                error_vars_str = error_vars_str + str(var) + " "

        await conn.logout()

        self.last_connect = datetime.now(tz=None)

        # Return info about the connection or variables.
        return {
            "title": data[CONF_CONNECTION_NAME],
            "serial": serial,
            "error_code": error_code,
            "error_variables": error_vars_str,
        }


class InvalidAuth(HomeAssistantError):
    """Error to indicate that the authentication is invalid."""
