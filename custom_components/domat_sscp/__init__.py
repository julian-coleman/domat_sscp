"""The Domat SSCP integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .coordinator import DomatSSCPConfigEntry, DomatSSCPCoordinator

_LOGGER = logging.getLogger(__name__)
_PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: DomatSSCPConfigEntry
) -> bool:
    """Set up Domat SSCP from a config entry."""

    coordinator = DomatSSCPCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()
    if not coordinator.data:
        raise ConfigEntryNotReady
    # Store the coordinator for later uses.
    config_entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, _PLATFORMS)

    _LOGGER.info("Setup done")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    return True
