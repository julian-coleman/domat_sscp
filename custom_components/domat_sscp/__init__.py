"""The Domat SSCP integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry

from .coordinator import DomatSSCPConfigEntry, DomatSSCPCoordinator

_LOGGER = logging.getLogger(__name__)
_PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.WATER_HEATER
]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: DomatSSCPConfigEntry
) -> bool:
    """Set up Domat SSCP from a config entry."""

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

    # Call the setup on our platforms
    await hass.config_entries.async_forward_entry_setups(config_entry, _PLATFORMS)

    return True


# TODO: Remove update listener and use OptionsFlowWithReload
async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle config options update.

    Called from our listener created earlier.
    """

    _LOGGER.debug("Update listener")
    # Call the setup on our platforms
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Allow devices to be deleted from the UI."""

    data: dict[str, Any] = config_entry.options.copy()
    devices: list = []
    remove: list = []

    # Remove entities for these devices from our options
    for tup in device_entry.identifiers:
        device = tup[1]
        _LOGGER.debug(
            "Removing entities with device: %s",
            device_entry.identifiers,
        )
        devices.append(device)
    for opt, val in data.items():
        if "device" in val:
            for device in devices:
                if val["device"] == device:
                    remove.append(opt)
    for opt in remove:
        _LOGGER.debug("Removing entity: %s", opt)
        data.pop(opt, None)

    _LOGGER.debug("New options: %s", data)
    hass.config_entries.async_update_entry(config_entry, options=data)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    _LOGGER.debug("Unload entry")
    return await hass.config_entries.async_unload_platforms(config_entry, _PLATFORMS)
