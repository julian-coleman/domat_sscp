"""Calendar for the Domat SSCP integration."""

import datetime
import logging
from typing import Any

from homeassistant.components.calendar import (
    EVENT_END,
    EVENT_START,
    EVENT_SUMMARY,
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
        if self.calendar == OPT_CALENDAR_BASE:
            self.sscp_class = sscp_schedule_basetpg
        if self.calendar == OPT_CALENDAR_EXCEPTIONS:
            self.sscp_class = sscp_schedule_exceptions
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
        self.updating: bool = False
        self._update_events()
        self._attr_supported_features = (
            CalendarEntityFeature.CREATE_EVENT | \
            CalendarEntityFeature.DELETE_EVENT | \
            CalendarEntityFeature.UPDATE_EVENT
            )
        _LOGGER.debug("Initialised new %s with: %s", entity_id, entity_data)

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

        # Make base events repeat each week
        if self.calendar == OPT_CALENDAR_BASE:
            weeks_before = 0
            weeks_after = 0
            events: list[CalendarEvent] = []
            week_delta = datetime.timedelta(days=7)

            _LOGGER.error("Start = %s", self._events[0].start_datetime_local)
            _LOGGER.error("From: %s", start_date)
            _LOGGER.error("To: %s", end_date)
            start = self._events[0].start_datetime_local
            while start > start_date:
                weeks_before -= 1
                start -= week_delta
            start = self._events[0].start_datetime_local
            while start < end_date:
                weeks_after += 1
                start += week_delta

            for offset in range(weeks_before, weeks_after + 1):
                _LOGGER.error("Adding weeks %s", offset)

        return [x for x in self._events if start_date <= x.start_datetime_local < end_date or start_date <= x.end_datetime_local < end_date]

    async def async_create_event(self, **kwargs: Any) -> None:
        """Add a new event to calendar."""

        _LOGGER.error("create event: %s", kwargs)

        start = kwargs[EVENT_START]
        end = kwargs[EVENT_END]
        # If all day, subtract 1 minute from the end time
        if type(kwargs[EVENT_START]) is datetime.date:
            start = datetime.datetime(
                year=start.year,
                month=start.month,
                day=start.day
            )
            end = datetime.datetime(
                year=end.year,
                month=end.month,
                day=end.day
            ) - datetime.timedelta(minutes=1)
        if kwargs[EVENT_SUMMARY] == "0":
            on = False
        else:
            on = True

        # Update using the co-ordinator function
        schedule = self.sscp_class(
            uid=self.sscp_uid,
            offset=self.sscp_offset,
            length=self.sscp_length,
            type=self.sscp_type
        )
        schedule.set_value(self.coordinator.data[self.unique_id])
        raw = schedule.add_event(start=start, end=end, on=on)
        self.hass.loop.create_task(
            self.coordinator.schedule_update(
                schedule_id=self._attr_unique_id,
                raw=raw
            )
        )

    async def async_delete_event(
        self,
        uid: str,
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        """Delete an event on the calendar."""

        _LOGGER.error("delete event: %s", uid)

        for calendar_event in self._events:
            if calendar_event.uid == uid:
                # Update using the co-ordinator function
                schedule = self.sscp_class(
                    uid=self.sscp_uid,
                    offset=self.sscp_offset,
                    length=self.sscp_length,
                    type=self.sscp_type
                )
                if calendar_event.summary == "0":
                    on = False
                else:
                    on = True
                schedule.set_value(self.coordinator.data[self.unique_id])
                raw = schedule.remove_event(
                    start=calendar_event.start_datetime_local,
                    end=calendar_event.end_datetime_local,
                    on=on
                )
                self.hass.loop.create_task(
                    self.coordinator.schedule_update(
                        schedule_id=self._attr_unique_id,
                        raw=raw
                    )
                )
                return
        _LOGGER.error("No event found for %s", uid)

    async def async_update_event(
        self,
        uid: str,
        event: dict[str, Any],
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        """Update an event on the calendar."""

        _LOGGER.error("update event: %s %s", uid, event)

        new_start = event[EVENT_START]
        new_end = event[EVENT_END]
        # If all day, subtract 1 minute from the end time
        if type(event[EVENT_START]) is datetime.date:
            new_start = datetime.datetime(
                year=new_start.year,
                month=new_start.month,
                day=new_start.day
            )
            new_end = datetime.datetime(
                year=new_end.year,
                month=new_end.month,
                day=new_end.day
            ) - datetime.timedelta(minutes=1)
        for calendar_event in self._events:
            if calendar_event.uid == uid:
                # Update using the co-ordinator function
                schedule = self.sscp_class(
                    uid=self.sscp_uid,
                    offset=self.sscp_offset,
                    length=self.sscp_length,
                    type=self.sscp_type
                )
                if calendar_event.summary == "0":
                    on = False
                else:
                    on = True
                if event["summary"] == "0":
                    new_on = False
                else:
                    new_on = True
                schedule.set_value(self.coordinator.data[self.unique_id])
                raw = schedule.change_event(
                    start=calendar_event.start_datetime_local,
                    end=calendar_event.end_datetime_local,
                    on=on,
                    new_start=new_start,
                    new_end=new_end,
                    new_on=new_on
                )
                self.hass.loop.create_task(
                    self.coordinator.schedule_update(
                        schedule_id=self._attr_unique_id,
                        raw=raw
                    )
                )
                return
        _LOGGER.error("No event found for %s", uid)

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

        _LOGGER.debug("Getting %s events from %s", self.calendar, self.coordinator.data[self.unique_id].hex())

        schedule = self.sscp_class(
            uid=self.sscp_uid,
            offset=self.sscp_offset,
            length=self.sscp_length,
            type=self.sscp_type
        )
        schedule.set_value(self.coordinator.data[self.unique_id])

        for sscp_event in schedule.to_events():
            _LOGGER.debug("event %s : %s - %s : %s", sscp_event.id, sscp_event.start, sscp_event.end, sscp_event.on)
            if sscp_event.on is True:
                description = self.on
                summary = "1"
            else:
                description = self.off
                summary = "0"
            calendar_event = CalendarEvent(
                start=sscp_event.start.replace(tzinfo=tzinfo),
                end=sscp_event.end.replace(tzinfo=tzinfo),
                summary=summary,
                description=description,
                uid=sscp_event.id
            )
            calendar_events.append(calendar_event)
            if calendar_event.start_datetime_local <= now < calendar_event.end_datetime_local:
                current_event = calendar_event
        self._event = current_event
        self._events = calendar_events
