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
    SCHEDULE_BASETPG_LEN,
    SCHEDULE_BASETPG_MINS_END,
    SCHEDULE_BASETPG_MINS_START,
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
    def from_yaml(cls, yaml):
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

    def to_string(self):
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

    def set_value(self, raw):
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
        self.name = None
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
        self.times_raw=[]
        self.states_raw=[]
        for _i in range(self.item_count):
            self.times_raw.append(None)
            self.states_raw.append(None)
 
    def set_value(self, raw: bytearray) -> None:
        """Set the variable to the new raw value from the PLC.

        Directly updates the raw value.
        Parses the raw value and calculates the base schedule.
        """

        _LOGGER.debug("base raw value: %s", raw.hex())
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
                if self.states_raw[i] != SCHEDULE_OFF:
                    event = sscp_schedule_event()
                    event.name = "1"
                    events.append(event)
                    event.start = mon00 + timedelta(minutes=mins)
                    event.id = f"{i:02d}"
                elif event is not None:
                    event.end = mon00 + timedelta(minutes=mins)
                    _LOGGER.debug("event %s - %s : %s", event.start, event.end, event.name)
                    event = None

        return events


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
        self.times1_raw=[]
        self.times2_raw=[]
        self.states_raw=[]
        for _i in range(self.item_count):
            self.times1_raw.append(None)
            self.times2_raw.append(None)
            self.states_raw.append(None)

    def set_value(self, raw: bytearray) -> None:
        """Set the variable to the new raw value from the PLC.

        Directly updates the raw value.
        Parses the raw value and calculates the schedule exceptions.
        """

        _LOGGER.debug("var %d raw value: %s", self.uid, raw.hex())
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
                    event.name = "1"
                else:
                    event.name = "0"
                events.append(event)
                event.start = times1
                event.end = times2
                event.id = f"{i:02d}"
                _LOGGER.debug("event %s - %s : %s", event.start, event.end, event.name)

        return events


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
