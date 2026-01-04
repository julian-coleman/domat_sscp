"""Select for the Domat SSCP integration."""

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
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
    """Set up the Selects from option entries."""

    coordinator: DomatSSCPCoordinator = config_entry.coordinator
    _LOGGER.debug("Setup coordinator: %s", coordinator.name)
    _LOGGER.debug("Setup options: %s", config_entry.options)
    _LOGGER.debug("Setup values: %s", coordinator.data)

    # Add selects (class) with their initialisation data
    selects: list[SelectEntity] = []
    for opt in config_entry.options:
        if (
            "entity" in config_entry.options[opt]
            and config_entry.options[opt]["entity"] == Platform.SELECT
        ):
            _LOGGER.debug("Adding select %s: %s", opt, config_entry.options[opt])
            selects.append(
                DomatSSCPSelect(
                    coordinator=coordinator,
                    entity_id=opt,
                    entity_data=config_entry.options[opt],
                )
            )
    async_add_entities(selects)


class DomatSSCPSelect(CoordinatorEntity, SelectEntity):
    """Select types for SSCP, using coordinator for updates."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: DomatSSCPCoordinator,
        entity_id: str,
        entity_data: dict[str, Any],
    ) -> None:
        """Initialise a select with provided data."""

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
        self.states = entity_data["states"]
        self._attr_options = []
        self._attr_options.extend(option for option in self.states.values())
        self._attr_current_option = self._update_option()
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

        self._attr_current_option = self._update_option()
        self.async_write_ha_state()

    @property
    def options(self) -> list[str]:
        """Return the selectable options."""

        return self._attr_options

    @property
    def current_option(self) -> str | None:
        """Return the current option."""

        return self._attr_current_option

    @property
    def available(self) -> bool:
        """Is state available?"""

        if self.unique_id in self.coordinator.data:
            return True
        return False

    def select_option(self, option: str) -> None:
        """Set the option using the co-ordinator function."""

        # Convert state to value
        new_value = 0
        for value, state in self.states.items():
            if state == option:
                new_value = int(value)
                break
        _LOGGER.debug("Updated %s: %d %s", self.unique_id, new_value, option)
        self.hass.loop.create_task(
            self.coordinator.entity_update(
                uid=self.sscp_uid,
                offset=self.sscp_offset,
                length=self.sscp_length,
                type=self.sscp_type,
                value=new_value
            )
        )

    def _update_option(self) -> str | None:
        """Retrieve our value from the co-ordinator."""

        if self.unique_id not in self.coordinator.data:
            _LOGGER.error("No co-ordinator data for %s", self.unique_id)
            return None

        # Convert value to state
        new_value = str(self.coordinator.data[self.unique_id])
        for value, state in self.states.items():
            if value == new_value:
                return state

        _LOGGER.error("Unexpected value: %s = %s", self.unique_id, new_value)
        return ""
