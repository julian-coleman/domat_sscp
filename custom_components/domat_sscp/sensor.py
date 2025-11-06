"""Sensor for the Domat SSCP integration."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_SENSOR_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DomatSSCPConfigEntry
from .const import DOMAIN
from .coordinator import DomatSSCPCoordinator

# TODO: Add a common entity
# from .entity import DomatSSCPEntity

# The co-ordinator is used to centralise the data updates
PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: DomatSSCPConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Sensors from option entries."""

    coordinator: DomatSSCPCoordinator = config_entry.coordinator
    _LOGGER.debug("Setup coordinator: %s", coordinator.name)
    _LOGGER.debug("Setup options: %s", config_entry.options)
    _LOGGER.debug("Setup values: %s", coordinator.data)

    # Add sensors (class) with their initialisation data
    # TODO: Skip sensors that are already in er
    sensors: list[SensorEntity] = []
    for opt in config_entry.options:
        if (
            "entity" in config_entry.options[opt]
            and config_entry.options[opt]["entity"] == CONF_SENSOR_TYPE
        ):
            _LOGGER.debug("Adding sensor %s: %s", opt, config_entry.options[opt])
            sensors.append(
                DomatSSCPSensor(
                    coordinator=coordinator,
                    entity_id=opt,
                    entity_data=config_entry.options[opt],
                )
            )
    async_add_entities(sensors)


class DomatSSCPSensor(CoordinatorEntity, SensorEntity):
    """Sensor types for SSCP, using coordinator for updates."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: DomatSSCPCoordinator,
        entity_id: str,
        entity_data: dict[str, Any],
    ) -> None:
        """Initialise a sensor with provided data."""

        super().__init__(coordinator)

        # Entity-specific values
        self.coordinator = coordinator
        self._attr_unique_id = entity_id
        # self._attr_name = entity_data["name"]
        self._attr_native_unit_of_measurement = entity_data["unit"]
        self._attr_device_class = entity_data["class"]
        self._attr_suggested_display_precision = entity_data.get("precision", 0)

        self.value = self._update_value()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entity_data.get("device"))},
            name=entity_data.get("device"),
            manufacturer="Domat",
            model="SSCP Device",
        )
        _LOGGER.error("Initialised new %s with: %s", entity_id, entity_data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self.value = self._update_value()
        self.async_write_ha_state()

    # TODO: Add a callback for when the entity is disabled/enabled and update runtime

    @property
    def native_value(self) -> float | None:
        """Return the current value."""

        return self.value

    @property
    def available(self) -> bool:
        """Is state available?"""

        if self.unique_id in self.coordinator.data:
            return True
        return False

    def _update_value(self) -> float | None:
        """Retrieve our value from the co-ordinator."""

        if self.unique_id not in self.coordinator.data:
            _LOGGER.error("No co-ordinator data for %s", self.unique_id)
            return None

        new_value = self.coordinator.data[self.unique_id]
        if self.suggested_display_precision is not None:
            new_value = round(new_value, self.suggested_display_precision)
        else:
            new_value = round(new_value)
        return new_value
