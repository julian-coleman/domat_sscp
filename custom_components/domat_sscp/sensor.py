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
    _LOGGER.debug("Sensor setup coordinator: %s", coordinator.name)
    _LOGGER.error("Sensor setup options: %s", config_entry.options)
    _LOGGER.debug("Sensor setup values: %s", coordinator.data)

    # TODO: Retrieve entities from er
    # Add sensors (class) with their initialisation data
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

        # Out unique values
        self.coordinator = coordinator
        _LOGGER.error("Initialising %s with: %s", entity_id, entity_data)
        self._attr_unique_id = entity_id
        # self._attr_name = entity_data["name"]
        self._attr_native_unit_of_measurement = entity_data["unit"]
        self._attr_device_class = entity_data["class"]
        self._attr_suggested_display_precision = entity_data.get("precision", 0)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entity_data.get("device"))},
            name=entity_data.get("device"),
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if self.unique_id not in self.coordinator.data:
            _LOGGER.error("No data for %s", self.unique_id)
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        """Return the current value."""

        # Retrieve our value from the coordinator
        if self.unique_id not in self.coordinator.data:
            return None
        value = self.coordinator.data[self.unique_id]

        if self.suggested_display_precision is not None:
            value = round(value, self.suggested_display_precision)
        else:
            value = round(value)
        return value

    @property
    def available(self) -> bool:
        """Is state available?"""

        if self.unique_id in self.coordinator.data:
            return True
        return False
