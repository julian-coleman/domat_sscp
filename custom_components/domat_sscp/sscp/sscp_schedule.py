"""SSCP (Shark Slave Communications Protocol) schedule variables.

See Also:
  https://kb.mervis.info/lib/exe/fetch.php/cs:mervis-ide:sharkprotocolspecification_user_2017_05_30.pdf
"""

from datetime import datetime, timedelta
import logging
from typing import Any

from .sscp_const import (
    EXCEPTIONS_NAME_CS,
    EXCEPTIONS_NAME_EN,
    MINS_PER_DAY,
    OFF_NAME_CS,
    OFF_NAME_EN,
    ON_NAME_CS,
    ON_NAME_EN,
    SCHEDULE_BASETPG_END,
    SCHEDULE_BASETPG_LEN,
    SCHEDULE_BASETPG_MINS_END,
    SCHEDULE_BASETPG_MINS_START,
    SCHEDULE_BASETPG_START,
    SCHEDULE_BASETPG_STATE_END,
    SCHEDULE_BASETPG_STATE_START,
    SCHEDULE_EXCEPTIONS_1_END,
    SCHEDULE_EXCEPTIONS_1_START,
    SCHEDULE_EXCEPTIONS_2_END,
    SCHEDULE_EXCEPTIONS_2_START,
    SCHEDULE_EXCEPTIONS_BASE_DAY,
    SCHEDULE_EXCEPTIONS_BASE_MONTH,
    SCHEDULE_EXCEPTIONS_BASE_YEAR,
    SCHEDULE_EXCEPTIONS_LEN,
    SCHEDULE_EXCEPTIONS_MINS_END,
    SCHEDULE_EXCEPTIONS_MINS_START,
    SCHEDULE_EXCEPTIONS_STATE_END,
    SCHEDULE_EXCEPTIONS_STATE_START,
    SCHEDULE_EXCEPTIONS_YEAR_END,
    SCHEDULE_EXCEPTIONS_YEAR_START,
    SCHEDULE_NAME_CS,
    SCHEDULE_NAME_EN,
    SCHEDULE_OFF,
    SCHEDULE_ON,
    SSCP_DATA_ORDER,
    WEEKDAYS_NAME_CS,
    WEEKDAYS_NAME_EN,
)
from .sscp_variable import sscp_variable

_LOGGER = logging.getLogger(__name__)

BYTE2_0 = bytes("\x00\x00", encoding="iso-8859-1")
BYTE4_0 = bytes("\x00\x00\x00\x00", encoding="iso-8859-1")


class sscp_schedule(sscp_variable):
    """SSCP Schedule.

    Handles base schedule and exceptions.
    Converts schedule time to Unix time and vice versa.
    """

    def __init__(
        self,
        uid: int,
        length: int,
        offset: int,
        type: int,
        base: dict[str: Any],
        exceptions: dict[str: Any],
        format: str | None = None,
        default: dict[str: Any] | None = None,
        out: dict[str: Any] | None = None
    ) -> None:
        """Configure the SSCP schedule with individual parameters."""

        super().__init__(uid=uid, length=length, offset=offset, type=type)
        self.base = sscp_schedule_basetpg(
            uid=base.get("uid"),
            length=base.get("length"),
            offset=base.get("offset"),
            type=base.get("type")
        )
        self.exceptions = sscp_schedule_exceptions(
            uid=exceptions.get("uid"),
            length=exceptions.get("length"),
            offset=exceptions.get("offset"),
            type=exceptions.get("type")
        )
        if default is not None:
            self.default = sscp_variable(
                uid=default.get("uid"),
                length=default.get("length"),
                offset=default.get("offset"),
                type=default.get("type")
            )
        if out is not None:
            self.out = sscp_variable(
                uid=out.get("uid"),
                length=out.get("length"),
                offset=out.get("offset"),
                type=out.get("type")
            )

        # Initial values
        self.on_state = SCHEDULE_ON

    @classmethod
    def from_yaml(cls, yaml) -> None:
        "Configure the SSCP schedule with paramaters via YAML."

        _LOGGER.debug("yaml: %s", yaml)
        # Required
        try:
            uid = yaml["uid"]
            length = yaml["length"]
            offset = yaml["offset"]
            type = yaml["type"]
            baseyaml = yaml["base"]
            exceptionsyaml = yaml["exceptions"]
        except KeyError as e:
            e_str = "Missing parameter" + str(e)
            raise ValueError(e_str) from e
        # Optional
        format = yaml.get("format")
        defaultyaml = yaml.get("default")
        outyaml = yaml.get("out")

        base = {}
        exceptions = {}
        default = {}
        out = {}
        for key in "uid", "length", "offset", "type":
            base[key] = baseyaml.get(key)
            exceptions[key] = exceptionsyaml.get(key)
            if defaultyaml is not None:
                default[key] = defaultyaml.get(key)
            if outyaml is not None:
                out[key] = outyaml.get(key)
        return cls(
            uid=uid,
            length=length,
            offset=offset,
            type=type,
            base=base,
            exceptions=exceptions,
            format=format,
            default=default,
            out=out
        )

    def to_string(self) -> str:
        """Return a string representation of the schedule."""
        string = "Schedule:\n"
        string += self.base.to_string()
        string += self.exceptions.to_string()
        if self.default is not None:
            string += "  Default:\n"
            string += self.default.to_string()
            string += "\n"
        if self.out is not None:
            string += "  Out:\n"
            string += self.out.to_string()
            string += "\n"
        return string

    def set_value(self, raw) -> None:
        """Set the variable to the new raw value from the PLC.

        Directly updates the base and exceptions raw values.
        """

        string = ""
        if _LOGGER.getEffectiveLevel() == logging.DEBUG:
            for i in range(0, self.length, 4):
                string += raw[i:i+4].hex()
                string += " "
        _LOGGER.debug("Set schedule to %s", string)

        self.raw = raw
        self.base.set_val(raw[self.base.offset:self.base.offset+self.base.length])
        self.exceptions.set_val(
            raw[self.exceptions.offset:self.base.offset+self.exceptions.length]
        )
        if self.default is not None:
            self.default.set_val(
                raw[self.default.offset:self.default.offset+self.default.length]
            )
        if self.out is not None:
            self.out.set_val(raw[self.out.offset:self.out.offset+self.out.length])


class sscp_schedule_event:
    """Event representation for SSCP schedules."""

    def __init__(self):
        """Initialise an empty event."""

        self.start = None
        self.end = None
        self.on = None
        self.id = None


class sscp_schedule_basetpg(sscp_variable):
    """Handle SSCP base schedules (TPG)."""

    def __init__(
        self,
        uid: int,
        length: int,
        offset: int,
        type: int
    ) -> None:
        """Configure the SSCP base schedule with individual parameters."""

        super().__init__(uid=uid, length=length, offset=offset, type=type)
        # Initial values
        self.item_count = int(self.length / SCHEDULE_BASETPG_LEN)
        if (self.length != self.item_count * SCHEDULE_BASETPG_LEN):
            raise ValueError("Schedule length mismatch:", self.length)
        self.raw = None
        self.times_raw: list[bytearray] = []
        self.states_raw: list[bytearray] = []
        for _i in range(self.item_count):
            self.times_raw.append(None)
            self.states_raw.append(None)

    def set_value(self, raw: bytearray) -> None:
        """Set the variable to the new raw value from the PLC.

        Directly updates the raw value.
        Parses the raw value and calculates the base schedule.
        """

        string = ""
        if _LOGGER.getEffectiveLevel() == logging.DEBUG:
            string = _scheduler_raw_to_string(raw)
        _LOGGER.debug("var %d raw value: %s", self.uid, string)

        self.raw = raw
        self.val = raw
        for i in range(self.item_count):
            start = i * SCHEDULE_BASETPG_LEN
            self.times_raw[i] = \
                raw[start + SCHEDULE_BASETPG_MINS_START:start + SCHEDULE_BASETPG_MINS_END]
            self.states_raw[i] = \
                raw[start + SCHEDULE_BASETPG_STATE_START:start + SCHEDULE_BASETPG_STATE_END]


    def to_string(self, lang: str | None = None) -> str:
        """Return a string representation of the schedule."""

        if lang == "cs":
            string = f"{SCHEDULE_NAME_CS}:\n"
            days = WEEKDAYS_NAME_CS
            on = ON_NAME_CS
            off = OFF_NAME_CS
        else: # default
            string = f"{SCHEDULE_NAME_EN}:\n"
            days = WEEKDAYS_NAME_EN
            on = ON_NAME_EN
            off = OFF_NAME_EN
        for i in range(self.item_count):
            if self.times_raw[i] is not None:
                times: list[int] = _scheduler_base_hex_to_time(self.times_raw[i])
                if times is not None:
                    string += f"{days[times[0]]} {times[1]:02d}:{times[2]:02d}"
                    if self.states_raw[i] == self.on_state:
                        string += f" {on}\n"
                    else:
                        string += f" {off}\n"
        return string

    def to_events(self) -> list[sscp_schedule_event]:
        """Convert the schedule to a list of events."""

        events: list[sscp_schedule_event] = []
        event = None

        now = datetime.now()
        mon = now - timedelta(days=now.weekday())
        mon00 = datetime(year=mon.year, month=mon.month, day=mon.day)
        _LOGGER.debug("Base start time: %s", mon00)

        for i in range(self.item_count):
            if self.times_raw[i] is not None:
                mins = int.from_bytes(self.times_raw[i], SSCP_DATA_ORDER)
                if event is None and self.states_raw[i] != SCHEDULE_OFF:
                    event = sscp_schedule_event()
                    event.on = True
                    events.append(event)
                    event.start = mon00 + timedelta(minutes=mins)
                    event.id = f"{i:02d}"
                elif event is not None and self.states_raw[i] == SCHEDULE_OFF:
                    event.end = mon00 + timedelta(minutes=mins)
                    _LOGGER.debug("event %s - %s : %s", event.start, event.end, event.on)
                    event = None

        return events

    def add_event(self, start: datetime, end: datetime, on: bool) -> bytearray:
        """Add an event, converting start and end times."""

        if self.raw is None:
            raise ValueError("No existing events")

        _LOGGER.debug("Adding %s %s", start, end)
        start_raw, end_raw = _scheduler_base_event_to_time(start=start, end=end)

        # Insert start/end times into the list (the last 1 or 2 times are lost)
        i = 0
        new_times_raw = []
        new_states_raw = []
        count = self.item_count - 2

        # If new_start is 00:00, replace off at 00:00
        if start_raw == SCHEDULE_BASETPG_START and self.times_raw[0] == SCHEDULE_BASETPG_START and self.states_raw[0] == SCHEDULE_OFF:
            i = 1
            count = self.item_count - 1
            _LOGGER.debug("Replacing 0 at: 0000")

        for i in range(i, count):
            if start_raw >= self.times_raw[i]:
                new_times_raw.append(self.times_raw[i])
                new_states_raw.append(self.states_raw[i])
            else:
                break
        new_times_raw.append(start_raw)
        new_states_raw.append(SCHEDULE_ON)
        _LOGGER.debug("Added start at: %d", i)

        for i in range(i, count):
            if end_raw > self.times_raw[i]:
                new_times_raw.append(self.times_raw[i])
                new_states_raw.append(self.states_raw[i])
            else:
                break
        new_times_raw.append(end_raw)
        new_states_raw.append(SCHEDULE_OFF)
        _LOGGER.debug("Added end at: %d", i)

        for i in range(i, count):
            new_times_raw.append(self.times_raw[i])
            new_states_raw.append(self.states_raw[i])

        if len(new_times_raw) != self.item_count:
            raise ValueError("Add failed: %s %s %s", start, end, on)

        raw = _scheduler_base_times_states_to_raw(
            times_raw=new_times_raw,
            states_raw=new_states_raw
        )
        self.set_value(raw)
        return self.raw

    def remove_event(self, start: datetime, end: datetime, on: bool) -> bytearray:
        """Remove an event, both start and end times."""

        if self.raw is None:
            raise ValueError("No existing events")

        _LOGGER.debug("Removing %s %s", start, end)
        start_raw, end_raw = _scheduler_base_event_to_time(start=start, end=end)

        # Remove start/end times from the list and append empty times
        i = 0
        a = 2
        new_times_raw = []
        new_states_raw = []

        # Make sure that we have an entry at 00:00
        if start_raw == SCHEDULE_BASETPG_START and self.times_raw[0] == SCHEDULE_BASETPG_START and self.states_raw[0] != SCHEDULE_OFF:
            new_times_raw.append(SCHEDULE_BASETPG_START)
            new_states_raw.append(SCHEDULE_OFF)
            a = 1
            _LOGGER.debug("Added 0 at: 0000")

        for i in range(self.item_count):
            if self.states_raw[i] == SCHEDULE_OFF or start_raw != self.times_raw[i]:
                new_times_raw.append(self.times_raw[i])
                new_states_raw.append(self.states_raw[i])
            else:
                break
        _LOGGER.debug("Removed start at: %d", i)

        i += 1
        for i in range(i, self.item_count):
            if self.states_raw[i] != SCHEDULE_OFF or end_raw != self.times_raw[i]:
                new_times_raw.append(self.times_raw[i])
                new_states_raw.append(self.states_raw[i])
            else:
                break
        _LOGGER.debug("Removed end at: %d", i)

        i += 1
        for i in range(i, self.item_count):
            new_times_raw.append(self.times_raw[i])
            new_states_raw.append(self.states_raw[i])

        for _ in range(a):
            new_times_raw.append(SCHEDULE_BASETPG_END)
            new_states_raw.append(SCHEDULE_OFF)

        if len(new_times_raw) != self.item_count:
            raise ValueError("Remove failed: %s %s %s", start, end, on)

        raw = _scheduler_base_times_states_to_raw(
            times_raw=new_times_raw,
            states_raw=new_states_raw
        )
        self.set_value(raw)
        return self.raw

    def change_event(
        self,
        start: datetime,
        end: datetime,
        on: bool,
        new_start: datetime,
        new_end: datetime,
        new_on:bool
    ):
        """Change an event, moving both start and end times."""

        self.remove_event(start=start, end=end, on=on)
        return self.add_event(start=new_start, end=new_end, on=new_on)


class sscp_schedule_exceptions(sscp_variable):
    """Handle SSCP exceptions schedules."""

    def __init__(
        self,
        uid: int,
        length: int,
        offset: int,
        type: int
    ) -> None:
        """Configure the SSCP exceptions schedule with individual parameters."""

        super().__init__(uid=uid, length=length, offset=offset, type=type)
        # Initial values
        self.item_count = int(self.length / SCHEDULE_EXCEPTIONS_LEN)
        if (self.length != self.item_count * SCHEDULE_EXCEPTIONS_LEN):
            raise ValueError("Schedule length mismatch:", self.length)
        self.raw = None
        self.times1_raw: list[bytearray] = []
        self.times2_raw: list[bytearray] = []
        self.states_raw: list[bytearray] = []
        for _i in range(self.item_count):
            self.times1_raw.append(None)
            self.times2_raw.append(None)
            self.states_raw.append(None)

    def set_value(self, raw: bytearray) -> None:
        """Set the variable to the new raw value from the PLC.

        Directly updates the raw value.
        Parses the raw value and calculates the schedule exceptions.
        """

        string = ""
        if _LOGGER.getEffectiveLevel() == logging.DEBUG:
            string = _scheduler_raw_to_string(raw)
        _LOGGER.debug("var %d raw value: %s", self.uid, string)

        self.raw = raw
        self.val = raw
        for i in range(self.item_count):
            start = i * SCHEDULE_EXCEPTIONS_LEN
            self.times1_raw[i] = \
                raw[start + SCHEDULE_EXCEPTIONS_1_START:start + SCHEDULE_EXCEPTIONS_1_END]
            self.times2_raw[i] = \
                raw[start + SCHEDULE_EXCEPTIONS_2_START:start + SCHEDULE_EXCEPTIONS_2_END]
            self.states_raw[i] = \
                raw[start + SCHEDULE_EXCEPTIONS_STATE_START:start + SCHEDULE_EXCEPTIONS_STATE_END]

    def to_string(self, lang: str | None = None) -> str:
        """Return a string representation of the schedule."""

        if lang == "cs":
            string = f"{EXCEPTIONS_NAME_CS}:\n"
            days = WEEKDAYS_NAME_CS
            on = ON_NAME_CS
            off = OFF_NAME_CS
        else: # default
            string = f"{EXCEPTIONS_NAME_EN}:\n"
            days = WEEKDAYS_NAME_EN
            on = ON_NAME_EN
            off = OFF_NAME_EN
        for i in range(self.item_count):
            times1: datetime = _scheduler_exceptions_hex_to_time(self.times1_raw[i])
            times2: datetime = _scheduler_exceptions_hex_to_time(self.times2_raw[i])
            if times1 is not None and times2 is not None:
                # TODO: Format datetime in locale
                string += f"{days[times1.weekday()]} {times1:%d.%m.%Y %H:%M}"
                string += " - "
                string += f"{days[times1.weekday()]} {times2:%d.%m.%Y %H:%M}"
                if self.states_raw[i] == SCHEDULE_ON:
                    string += f" {on}\n"
                else:
                    string += f" {off}\n"
        return string

    def to_events(self) -> list[sscp_schedule_event]:
        """Convert the schedule to a list of events."""

        events: list[sscp_schedule_event] = []
        event = None

        for i in range(self.item_count):
            times1: datetime = _scheduler_exceptions_hex_to_time(self.times1_raw[i])
            times2: datetime = _scheduler_exceptions_hex_to_time(self.times2_raw[i])
            if times1 is not None and times2 is not None:
                event = sscp_schedule_event()
                if self.states_raw[i] == SCHEDULE_ON:
                    event.on = True
                else:
                    event.on = False
                events.append(event)
                event.start = times1
                event.end = times2
                event.id = f"{i:02d}"
                _LOGGER.debug("event %s - %s : %s", event.start, event.end, event.on)

        return events

    def add_event(self, start: datetime, end: datetime, on: bool) -> bytearray:
        """Add an event."""

        _LOGGER.debug("Adding %s %s %s", start, end, on)
        new_start_raw = _scheduler_exceptions_time_to_hex(start)
        new_end_raw = _scheduler_exceptions_time_to_hex(end)
        if on is True:
            state_raw = SCHEDULE_ON
        else:
            state_raw = SCHEDULE_OFF

        # Insert event into the list (the last 1 is lost)
        new_times1_raw: list[bytearray] = []
        new_times2_raw: list[bytearray] = []
        new_states_raw: list[bytearray] = []
        for i in range(self.item_count):
            if self.times1_raw[i] != BYTE4_0 and new_start_raw > self.times1_raw[i]:
                new_times1_raw.append(self.times1_raw[i])
                new_times2_raw.append(self.times2_raw[i])
                new_states_raw.append(self.states_raw[i])
            else:
                break

        new_times1_raw.append(new_start_raw)
        new_times2_raw.append(new_end_raw)
        new_states_raw.append(state_raw)
        _LOGGER.debug("Added event at: %d", i)

        for i in range(i, self.item_count - 1):
            new_times1_raw.append(self.times1_raw[i])
            new_times2_raw.append(self.times2_raw[i])
            new_states_raw.append(self.states_raw[i])

        if len(new_times1_raw) != self.item_count:
            raise ValueError("Add failed: %s %s %s", start, end, on)

        raw = _scheduler_exceptions_times_states_to_raw(
            times1_raw=new_times1_raw,
            times2_raw=new_times2_raw,
            states_raw=new_states_raw
        )
        self.set_value(raw)
        return self.raw

    def remove_event(self, start: datetime, end: datetime, on: bool) -> bytearray:
        """Remove an event."""

        if self.raw is None:
            raise ValueError("No existing events")

        _LOGGER.debug("Removing %s %s %s", start, end, on)

        start_raw = _scheduler_exceptions_time_to_hex(start)
        end_raw = _scheduler_exceptions_time_to_hex(end)
        if on is True:
            state_raw = SCHEDULE_ON
        else:
            state_raw = SCHEDULE_OFF

        new_times1_raw: list[bytearray] = []
        new_times2_raw: list[bytearray] = []
        new_states_raw: list[bytearray] = []
        for i in range(self.item_count):
            if self.times1_raw[i] == start_raw and self.times2_raw[i] == end_raw and self.states_raw[i] == state_raw:
                _LOGGER.debug("Removed start at: %d", i)
            else:
                new_times1_raw.append(self.times1_raw[i])
                new_times2_raw.append(self.times2_raw[i])
                new_states_raw.append(self.states_raw[i])

        new_times1_raw.append(BYTE4_0)
        new_times2_raw.append(BYTE4_0)
        new_states_raw.append(BYTE2_0)

        if len(new_times1_raw) != self.item_count:
            raise ValueError("Remove failed: %s %s %s", start, end, on)

        raw = _scheduler_exceptions_times_states_to_raw(
            times1_raw=new_times1_raw,
            times2_raw=new_times2_raw,
            states_raw=new_states_raw
        )
        self.set_value(raw)
        return self.raw

    def change_event(
        self,
        start: datetime,
        end: datetime,
        on: bool,
        new_start: datetime,
        new_end: datetime,
        new_on:bool
    ):
        """Change an event."""

        self.remove_event(start=start, end=end, on=on)
        return self.add_event(start=new_start, end=new_end, on=new_on)


def _scheduler_base_hex_to_time(byte2) -> list[int]:
    """Convert scheduler base hex to time."""

    mins = int.from_bytes(byte2, SSCP_DATA_ORDER)
    _LOGGER.debug("Base schedule time: %d", mins)
    if mins >= MINS_PER_DAY * 7:
        return None

    day = 0
    while mins > MINS_PER_DAY:
       mins -= MINS_PER_DAY
       day += 1

    hours = mins // 60
    mins = mins - hours * 60
    return [day, hours, mins]

def _scheduler_base_event_to_time(start: datetime, end: datetime) -> tuple[bytes, bytes]:
    """Convert events to base hex."""

    # Assume times are without timezone
    start=datetime(year=start.year,
        month=start.month,
        day=start.day,
        hour=start.hour,
        minute=start.minute
    )
    end=datetime(year=end.year,
        month=end.month,
        day=end.day,
        hour=end.hour,
        minute=end.minute
    )
    now = datetime.now()
    mon = now - timedelta(days=now.weekday())
    mon00 = datetime(year=mon.year, month=mon.month, day=mon.day)
    sun = now + timedelta(days=6 - now.weekday())
    sun24 = datetime(year=sun.year, month=sun.month, day=sun.day, hour=23, minute=59)
    _LOGGER.debug("Base time range: %s - %s", mon00, sun24)

    # Move the event to this week and check the end
    week_delta = timedelta(days=7)
    while start < mon00:
        start = start + week_delta
        end = end + week_delta
    while start > sun24:
        start = start - week_delta
        end = end - week_delta
    if end > sun24:
        raise ValueError("Event crosses Sunday midnight")

    # Convert to hex
    start_diff = int((start - mon00).total_seconds() // 60)
    end_diff = int((end - mon00).total_seconds() // 60)
    start_raw = start_diff.to_bytes(2, SSCP_DATA_ORDER)
    end_raw = end_diff.to_bytes(2, SSCP_DATA_ORDER)

    return start_raw, end_raw

def _scheduler_base_times_states_to_raw(
    times_raw: list[bytes], states_raw: list[bytes]
) -> bytearray:
    """Convert base times and states to bytearray."""

    raw = bytearray()
    for i in range(len(times_raw)):
        raw += times_raw[i] + BYTE2_0 + states_raw[i] + BYTE2_0

    return raw

def _scheduler_exceptions_hex_to_time(byte4) -> datetime | None:
    """Convert scheduler exceptions hex to time."""

    year = int.from_bytes(
        byte4[SCHEDULE_EXCEPTIONS_YEAR_START:SCHEDULE_EXCEPTIONS_YEAR_END],
        SSCP_DATA_ORDER
    )
    mins = int.from_bytes(
        byte4[SCHEDULE_EXCEPTIONS_MINS_START:SCHEDULE_EXCEPTIONS_MINS_END],
        SSCP_DATA_ORDER
    )
    _LOGGER.debug("Exceptions schedule time: %d %d", year, mins)
    if year == 0 and mins == 0:
        return None

    # Subtract 1 day if year > 0!
    if year > 0:
        if mins < MINS_PER_DAY:
            return None
        mins -= MINS_PER_DAY

    return datetime(
        year=year + SCHEDULE_EXCEPTIONS_BASE_YEAR,
        month=SCHEDULE_EXCEPTIONS_BASE_MONTH,
        day=SCHEDULE_EXCEPTIONS_BASE_DAY
    ) + timedelta(minutes=mins)

def _scheduler_exceptions_time_to_hex(dt: datetime) -> bytearray | None:
    """Convert scheduler exceptions time to hex."""

    ex = bytearray()

    year = dt.year - SCHEDULE_EXCEPTIONS_BASE_YEAR
    if year < 0 or year > 255:
        raise ValueError("Year out of range")
    ex = year.to_bytes(1, SSCP_DATA_ORDER)

    year00 = datetime(year=dt.year, month=1, day=1, hour=0, minute=0, tzinfo=dt.tzinfo)
    mins = int((dt - year00).total_seconds() // 60)
    if (year > 0):
        mins += MINS_PER_DAY
    ex += mins.to_bytes(3, SSCP_DATA_ORDER)

    return ex

def _scheduler_exceptions_times_states_to_raw(
    times1_raw: list[bytes], times2_raw: list[bytes], states_raw: list[bytes]
) -> bytearray:
    """Convert base times and states to bytearray."""

    raw = bytearray()
    for i in range(len(times1_raw)):
        raw += times1_raw[i] + times2_raw[i] + states_raw[i] + BYTE2_0

    return raw

def _scheduler_raw_to_string(raw: bytearray) -> str:
    """Print raw in blocks."""

    string = ""
    for i in range(0, len(raw), 4):
        string += raw[i:i+4].hex()
        string += " "
    return string
