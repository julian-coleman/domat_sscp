"""Switch for the Domat SSCP integration."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DomatSSCPConfigEntry
from .const import DOMAIN
from .coordinator import DomatSSCPCoordinator

# The co-ordinator is used to centralise the data updates
PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: DomatSSCPConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Switches from option entries."""

    coordinator: DomatSSCPCoordinator = config_entry.coordinator
    _LOGGER.debug("Setup coordinator: %s", coordinator.name)
    _LOGGER.debug("Setup options: %s", config_entry.options)
    _LOGGER.debug("Setup values: %s", coordinator.data)

    # Add switches (class) with their initialisation data
    switches: list[SwitchEntity] = []
    for opt in config_entry.options:
        if (
            "entity" in config_entry.options[opt]
            and config_entry.options[opt]["entity"] == Platform.SWITCH
        ):
            _LOGGER.debug("Adding switch %s: %s", opt, config_entry.options[opt])
            switches.append(
                DomatSSCPSwitch(
                    coordinator=coordinator,
                    entity_id=opt,
                    entity_data=config_entry.options[opt],
                )
            )
    async_add_entities(switches)


class DomatSSCPSwitch(CoordinatorEntity, SwitchEntity):
    """Switch types for SSCP, using coordinator for updates."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: DomatSSCPCoordinator,
        entity_id: str,
        entity_data: dict[str, Any],
    ) -> None:
        """Initialise a switch with provided data."""

        super().__init__(coordinator)

        # Entity-specific values
        self.coordinator = coordinator
        self._attr_unique_id = entity_id
        if "name" in entity_data:
            self._attr_name = entity_data["name"]
        if "icon" in entity_data:
            self._attr_icon = entity_data["icon"]
        if "class" in entity_data:
            self._attr_device_class = entity_data["class"]
        self.on_value = entity_data.get("on", 1)
        self.off_value = entity_data.get("off", 0)
        self.state_on = self._update_state()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entity_data.get("device"))},
            name=entity_data.get("device"),
            manufacturer="Domat",
            model="SSCP Device",
        )
        self.sscp_uid = entity_data["uid"]
        self.sscp_offset = entity_data["offset"]
        self.sscp_length = entity_data["length"]
        self.sscp_type = entity_data["type"]
        _LOGGER.debug("Initialised new %s with: %s", entity_id, entity_data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self.state_on = self._update_state()
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return the current state."""

        return self.state_on

    @property
    def available(self) -> bool:
        """Is state available?"""

        if self.unique_id in self.coordinator.data:
            return True
        return False

    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""

        new_value = self.on_value
        _LOGGER.debug("Updated %s: on", self.unique_id)
        self.hass.loop.create_task(
            self.coordinator.entity_update(
                uid=self.sscp_uid,
                offset=self.sscp_offset,
                length=self.sscp_length,
                type=self.sscp_type,
                value=new_value
            )
        )

    def turn_off(self, **kwargs) -> None:
        """Turn the entity off."""

        new_value = self.off_value
        _LOGGER.debug("Updated %s: off", self.unique_id)
        self.hass.loop.create_task(
            self.coordinator.entity_update(
                uid=self.sscp_uid,
                offset=self.sscp_offset,
                length=self.sscp_length,
                type=self.sscp_type,
                value=new_value
            )
        )

    def _update_state(self) -> bool:
        """Retrieve our value from the co-ordinator."""

        if self.unique_id not in self.coordinator.data:
            _LOGGER.error("No co-ordinator data for %s", self.unique_id)
            return None

        # Convert value to state
        new_value = self.coordinator.data[self.unique_id]
        if new_value == self.on_value:
            return True
        if new_value == self.off_value:
            return False

        _LOGGER.error("Unexpected value: %s = %s", self.unique_id, new_value)
        return False
