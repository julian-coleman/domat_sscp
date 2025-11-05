"""The Domat SSCP integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry

from .coordinator import DomatSSCPConfigEntry, DomatSSCPCoordinator

_LOGGER = logging.getLogger(__name__)
_PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: DomatSSCPConfigEntry
) -> bool:
    """Set up Domat SSCP from a config entry."""

    # Remove any left-over options
    # _LOGGER.error("Setup entry started - removing options")
    # hass.config_entries.async_update_entry(config_entry, options={})
    coordinator = DomatSSCPCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()
    if not coordinator.data:
        raise ConfigEntryNotReady
    # Store the coordinator for later use.
    config_entry.coordinator = coordinator

    # Setup an update listener for options changes
    config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )
    _LOGGER.error("Setup entry data: %s", coordinator.data)

    # Call the setup on our platforms
    await hass.config_entries.async_forward_entry_setups(config_entry, _PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle config options update.

    Called from our listener created earlier.
    """

    conf_data = config_entry.data.copy()
    conf_data["password"] = "********"
    _LOGGER.error("Update listener data: %s", conf_data)
    _LOGGER.error("Update listener options: %s", config_entry.options)
    # TODO: Add devices
    # Call the setup on our platforms
    await hass.config_entries.async_reload(config_entry.entry_id)
    _LOGGER.error("Removing options")
    config_entry.async_update_entry(config_entry, options={})


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Allow devices to be deleted from the UI."""

    _LOGGER.error("Remove config entry device: %s", device_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    _LOGGER.error("Unload entry")
    return await hass.config_entries.async_unload_platforms(config_entry, _PLATFORMS)
