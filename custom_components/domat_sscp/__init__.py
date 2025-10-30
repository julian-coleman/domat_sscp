"""The Domat SSCP integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
_PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Domat SSCP from a config entry."""

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # entry.runtime_data = MyAPI(...)

    # await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    _LOGGER.info("Setup done")
    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Update setup listener."""

    await hass.config_entries.async_reload(entry.entry_id)

    _LOGGER.info("Settings updated")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    #    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    return True
