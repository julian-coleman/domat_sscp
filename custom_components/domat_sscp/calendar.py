"""Calendar for the Domat SSCP integration."""

import datetime
import logging
from typing import Any

from homeassistant.components.calendar import (
    EVENT_END,
    EVENT_START,
    EVENT_UID,
    CalendarEntity,
    CalendarEntityFeature,
    CalendarEvent,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import DomatSSCPConfigEntry
from .const import DOMAIN, OPT_CALENDAR_BASE, OPT_CALENDAR_EXCEPTIONS
from .coordinator import DomatSSCPCoordinator
from .sscp.sscp_schedule import sscp_schedule_basetpg, sscp_schedule_exceptions

# The co-ordinator is used to centralise the data updates
PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: DomatSSCPConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Calendars from option entries."""

    coordinator: DomatSSCPCoordinator = config_entry.coordinator
    _LOGGER.debug("Setup coordinator: %s", coordinator.name)
    _LOGGER.debug("Setup options: %s", config_entry.options)
    _LOGGER.debug("Setup values: %s", coordinator.data)

    # Add calendars (class) with their initialisation data
    calendars: list[CalendarEntity] = []
    for opt in config_entry.options:
        if (
            "entity" in config_entry.options[opt]
            and config_entry.options[opt]["entity"] == Platform.CALENDAR
        ):
            _LOGGER.debug("Adding calendar %s: %s", opt, config_entry.options[opt])
            calendars.append(
                DomatSSCPCalendar(
                    coordinator=coordinator,
                    entity_id=opt,
                    entity_data=config_entry.options[opt],
                )
            )
    async_add_entities(calendars)


class DomatSSCPCalendar(CoordinatorEntity, CalendarEntity):
    """Calendar types for SSCP, using coordinator for updates."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: DomatSSCPCoordinator,
        entity_id: str,
        entity_data: dict[str, Any],
    ) -> None:
        """Initialise a calendar with provided data."""

        super().__init__(coordinator)

        # Entity-specific values
        self.coordinator = coordinator
        self._attr_unique_id = entity_id
        if "name" in entity_data:
            self._attr_name = entity_data["name"]
        if "icon" in entity_data:
            self._attr_icon = entity_data["icon"]
        self.calendar = entity_data["calendar"]
        if self.calendar not in {OPT_CALENDAR_BASE, OPT_CALENDAR_EXCEPTIONS}:
            raise ValueError("Unknown calendar type")
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
        self.on = entity_data["on"]
        self.off = entity_data["off"]
        self._event: CalendarEvent = None
        self._events: list[CalendarEvent] = []
        self._update_events()
        self._attr_supported_features = (
            CalendarEntityFeature.CREATE_EVENT | \
            CalendarEntityFeature.DELETE_EVENT | \
            CalendarEntityFeature.UPDATE_EVENT
            )
        _LOGGER.error("Initialised new %s with: %s", entity_id, entity_data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._update_events()
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Is state available?"""

        if self.unique_id in self.coordinator.data:
            return True
        return False

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""

        return self._event

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""

        return [x for x in self._events if start_date <= x.start_datetime_local < end_date or start_date <= x.end_datetime_local < end_date]

    async def async_create_event(self, **kwargs: Any) -> None:
        """Add a new event to calendar."""

#        create_start = kwargs[EVENT_START]
#        create_end = kwargs[EVENT_START]
        _LOGGER.error("create event: %s", kwargs)

    async def async_delete_event(
        self,
        uid: str,
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        """Delete an event on the calendar."""

        _LOGGER.error("delete event: %s", uid)

    async def async_update_event(
        self,
        uid: str,
        event: dict[str, Any],
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        """Update an event on the calendar."""

        _LOGGER.error("update event: %s %s", uid, event)

    def set_native_value(self, value: float) -> None:
        """Set the value using the co-ordinator function."""

# TODO:
        self.hass.loop.create_task(
            self.coordinator.schedule_update(entity=self._attr_unique_id)
        )

    def async_get_all_events(
        self,
    ) -> list[CalendarEvent]:
        """Return calendar events."""
        return self.events

    def _update_events(self) -> None:
        """Retrieve our data from the co-ordinator and convert to events."""

        if self.unique_id not in self.coordinator.data:
            _LOGGER.error("No co-ordinator data for %s", self.unique_id)
            self._event = None
            self._events = []
            return

        calendar_events: list[CalendarEvent] = []
        current_event = None
        now = dt_util.now()
        tzinfo = dt_util.get_default_time_zone()
        raw = self.coordinator.data[self.unique_id]

        if self.calendar == OPT_CALENDAR_BASE:
            _LOGGER.debug("Getting base events from %s", raw.hex())
            sscp_class = sscp_schedule_basetpg
            sscp_string = "base_"
        if self.calendar == OPT_CALENDAR_EXCEPTIONS:
            _LOGGER.debug("Getting exception events from %s", raw.hex())
            sscp_class = sscp_schedule_exceptions
            sscp_string ="exceptions_"

        schedule = sscp_class(
            uid=self.sscp_uid,
            offset=self.sscp_offset,
            length=self.sscp_length,
            type=self.sscp_type
        )
        schedule.set_value(raw)

        for i, sscp_event in enumerate(schedule.to_events()):
            _LOGGER.error("event %s - %s : %s", sscp_event.start, sscp_event.end, sscp_event.name)
            calendar_string = sscp_string + str(i)
            if sscp_event.name == "1":
                description = self.on
            else:
                description = self.off
            calendar_event = CalendarEvent(
                start=sscp_event.start.replace(tzinfo=tzinfo),
                end=sscp_event.end.replace(tzinfo=tzinfo),
                summary=sscp_event.name,
                description=description,
                uid=calendar_string
            )
            calendar_events.append(calendar_event)
            if calendar_event.start_datetime_local <= now < calendar_event.end_datetime_local:
                current_event = calendar_event
        self._event = current_event
        self._events = calendar_events
