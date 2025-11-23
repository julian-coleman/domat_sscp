"""Number for the Domat SSCP integration."""

import logging
from typing import Any

from homeassistant.components.number import (
    DEFAULT_MAX_VALUE,
    DEFAULT_MIN_VALUE,
    DEFAULT_STEP,
    NumberEntity,
)
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
    """Set up the Numbers from option entries."""

    coordinator: DomatSSCPCoordinator = config_entry.coordinator
    _LOGGER.debug("Setup coordinator: %s", coordinator.name)
    _LOGGER.debug("Setup options: %s", config_entry.options)
    _LOGGER.debug("Setup values: %s", coordinator.data)

    # Add numbers (class) with their initialisation data
    numbers: list[NumberEntity] = []
    for opt in config_entry.options:
        if (
            "entity" in config_entry.options[opt]
            and config_entry.options[opt]["entity"] == Platform.NUMBER
        ):
            _LOGGER.debug("Adding number %s: %s", opt, config_entry.options[opt])
            numbers.append(
                DomatSSCPNumber(
                    coordinator=coordinator,
                    entity_id=opt,
                    entity_data=config_entry.options[opt],
                )
            )
    async_add_entities(numbers)


class DomatSSCPNumber(CoordinatorEntity, NumberEntity):
    """Number types for SSCP, using coordinator for updates."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: DomatSSCPCoordinator,
        entity_id: str,
        entity_data: dict[str, Any],
    ) -> None:
        """Initialise a number with provided data."""

        super().__init__(coordinator)

        # Entity-specific values
        self.coordinator = coordinator
        self._attr_unique_id = entity_id
        self._attr_native_unit_of_measurement = entity_data["unit"]
        if "name" in entity_data:
            self._attr_name = entity_data["name"]
        if "icon" in entity_data:
            self._attr_icon = entity_data["icon"]
        if "class" in entity_data:
            self._attr_device_class = entity_data["class"]
        self._attr_max_value = entity_data.get("max", DEFAULT_MAX_VALUE)
        self._attr_min_value = entity_data.get("min", DEFAULT_MIN_VALUE)
        self._attr_step = entity_data.get("step", DEFAULT_STEP)
        self._attr_native_value = self._update_value()
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

        self._attr_native_value = self._update_value()
        self.async_write_ha_state()

    @property
    def native_max_value(self) -> float:
        """Return the maximum value."""

        return self._attr_max_value

    @property
    def native_min_value(self) -> float:
        """Return the minimum value."""

        return self._attr_min_value

    @property
    def native_step(self) -> float | None:
        """Return the step."""

        return self._attr_step

    @property
    def native_value(self) -> float | None:
        """Return the current value."""

        return self._attr_native_value

    @property
    def available(self) -> bool:
        """Is state available?"""

        if self.unique_id in self.coordinator.data:
            return True
        return False

    def set_native_value(self, value: float) -> None:
        """Set the value using the co-ordinator function."""

        self.hass.loop.create_task(
            self.coordinator.entity_update(
                uid=self.sscp_uid,
                offset=self.sscp_offset,
                length=self.sscp_length,
                type=self.sscp_type,
                value=value,
                increment=self._attr_step,
                maximum=self._attr_max_value,
                decrement=self._attr_step,
                minimum=self._attr_min_value,
            )
        )

    def _update_value(self) -> float | None:
        """Retrieve our value from the co-ordinator."""

        if self.unique_id not in self.coordinator.data:
            _LOGGER.error("No co-ordinator data for %s", self.unique_id)
            return None

        return self.coordinator.data[self.unique_id]
