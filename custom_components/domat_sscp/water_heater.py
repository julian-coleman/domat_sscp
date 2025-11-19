"""Water heater for the Domat SSCP integration."""

import logging
from typing import Any

from homeassistant.components.water_heater import (
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, Platform
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
    """Set up the Water heaters from option entries."""

    coordinator: DomatSSCPCoordinator = config_entry.coordinator
    _LOGGER.debug("Setup coordinator: %s", coordinator.name)
    _LOGGER.debug("Setup options: %s", config_entry.options)
    _LOGGER.debug("Setup values: %s", coordinator.data)

    # Add climates (class) with their initialisation data
    water_heaters: list[WaterHeaterEntity] = []
    for opt in config_entry.options:
        if (
            "entity" in config_entry.options[opt]
            and config_entry.options[opt]["entity"] == Platform.WATER_HEATER
        ):
            _LOGGER.debug("Adding water heater %s: %s", opt, config_entry.options[opt])
            water_heaters.append(
                DomatSSCPWaterHeater(
                    coordinator=coordinator,
                    entity_id=opt,
                    entity_data=config_entry.options[opt],
                )
            )
    async_add_entities(water_heaters)


class DomatSSCPWaterHeater(CoordinatorEntity, WaterHeaterEntity):
    """Water heater type for SSCP, using coordinator for updates."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: DomatSSCPCoordinator,
        entity_id: str,
        entity_data: dict[str, Any],
    ) -> None:
        """Initialise a water heater with provided data."""

        super().__init__(coordinator)

        # We only use target temperature
        self._attr_supported_features = WaterHeaterEntityFeature.TARGET_TEMPERATURE

        # Entity-specific values
        self.coordinator = coordinator
        self._attr_unique_id = entity_id
        self._attr_native_unit_of_measurement = entity_data["unit"]
        if "name" in entity_data:
            self._attr_name = entity_data["name"]
        if "icon" in entity_data:
            self._attr_icon = entity_data["icon"]
        if "unit" in entity_data:
            self._attr_temperature_unit = entity_data["unit"]
        self._attr_max_temp = entity_data.get("max", DEFAULT_MAX_TEMP)
        self._attr_min_temp = entity_data.get("min", DEFAULT_MIN_TEMP)
        self._attr_target_temperature_step = entity_data.get("step")
        self._attr_precision = entity_data.get("precision")
        self._attr_target_temperature = self._update_target()
        # We must set current_operation to something
        self._attr_current_operation = ""
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

        self._attr_target_temperature = self._update_target()
        self.async_write_ha_state()

    # TODO: Add a callback for when the entity is disabled/enabled and update runtime

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature value."""

        return self._attr_target_temperature

    @property
    def available(self) -> bool:
        """Is state available?"""

        if self.unique_id in self.coordinator.data:
            return True
        return False

    def set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature using the co-ordinator function."""

        _LOGGER.error("New target temperature: %s %s", self._attr_unique_id, kwargs)

        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        value = float(temperature)
        self.hass.loop.create_task(
            self.coordinator.entity_update(
                uid=self.sscp_uid,
                offset=self.sscp_offset,
                length=self.sscp_length,
                type=self.sscp_type,
                value=value,
                increment=self._attr_target_temperature_step,
                maximum=self._attr_max_temp,
                decrement=self._attr_target_temperature_step,
                minimum=self._attr_min_temp,
            )
        )

    def _update_target(self) -> float | None:
        """Retrieve target temperature value from the co-ordinator."""

        if self.unique_id not in self.coordinator.data:
            _LOGGER.error("No co-ordinator data for %s", self.unique_id)
            return None

        return self.coordinator.data[self.unique_id]
