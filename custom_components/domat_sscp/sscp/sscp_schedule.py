"""SSCP (Shark Slave Communications Protocol) schedule variables.

See Also:
  https://kb.mervis.info/lib/exe/fetch.php/cs:mervis-ide:sharkprotocolspecification_user_2017_05_30.pdf
"""

from datetime import datetime, timedelta
import logging

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

_LOGGER = logging.getLogger(__name__)


class sscp_schedule:
    """SSCP Schedule.

    Handles base schedule and exceptions.
    Converts schedule time to Unix time and vice versa.
    """

    def __init__(
        self,
        uid: int,
        length: int,
        offset: int
    ) -> None:
        """Configure the SSCP schedule with individual parameters."""

        self.uid = uid
        self.uid_bytes = self.uid.to_bytes(4, SSCP_DATA_ORDER)
        self.length = length
        self.length_bytes = self.length.to_bytes(4, SSCP_DATA_ORDER)
        self.offset = offset
        self.offset_bytes = self.offset.to_bytes(4, SSCP_DATA_ORDER)

        # Initial values
        self.on_state = SCHEDULE_ON

    @classmethod
    def from_yaml(cls, yaml):
        "Configure the SSCP schedule with paramaters via YAML."

        # Required
        try:
            uid=yaml["uid"]
            length=yaml["length"]
            offset=yaml["offset"]
        except KeyError as e:
            e_str = "Missing parameter" + str(e)
            raise ValueError(e_str) from e

        return cls(
            uid=uid,
            length=length,
            offset=offset
        )


class sscp_schedule_basetpg(sscp_schedule):
    """Handle SSCP base schedules (TPG)."""

    def __init__(
        self,
        uid: int,
        length: int,
        offset: int
    ) -> None:
        """Configure the SSCP base schedule with individual parameters."""

        super().__init__(uid=uid, length=length, offset=offset)
        # Initial values
        self.item_count = int(self.length / SCHEDULE_BASETPG_LEN)
        if (self.length != self.item_count * SCHEDULE_BASETPG_LEN):
            raise ValueError("Schedule length mismatch:", self.length)
        self.times_raw=[]
        self.states_raw=[]
        for _i in range(self.item_count):
            self.times_raw.append(None)
            self.states_raw.append(None)


    @classmethod
    def from_yaml(cls, yaml):
        "Configure the SSCP schedule with paramaters via YAML."

        # Required
        try:
            uid=yaml["uid"]
            length=yaml["length"]
            offset=yaml["offset"]
        except KeyError as e:
            e_str = "Missing parameter" + str(e)
            raise ValueError(e_str) from e

        return cls(
            uid=uid,
            length=length,
            offset=offset
        )

    def set_value(self, raw: bytearray) -> None:
        """Set the variable to the new raw value from the PLC.

        Directly updates the raw value.
        Parses the raw value and calculates the base schedule.
        """

        _LOGGER.debug("var %d raw value: %s", self.uid, raw.hex())
        self.raw = raw
        on_state = SCHEDULE_OFF
        for i in range(self.item_count):
            start = i * SCHEDULE_BASETPG_LEN
            self.times_raw[i] = raw[start + SCHEDULE_BASETPG_MINS_START:start + SCHEDULE_BASETPG_MINS_END]
            self.states_raw[i] = raw[start + SCHEDULE_BASETPG_STATE_START:start + SCHEDULE_BASETPG_STATE_END]
            if self.states_raw[i] != SCHEDULE_OFF:
                if on_state == SCHEDULE_OFF:
                    on_state = self.states_raw[i]
                elif on_state != self.states_raw[i]:
                    raise ValueError("Multiple schedule on values")
        self.on_state = on_state

    def to_string(self, lang: str | None = None) -> str:
        """Return a string representation of the variable."""
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
                times: list[int] = scheduler_base_hex_to_time(self.times_raw[i])
                if times is not None:
                    string += f"{days[times[0]]} {times[1]:02d}:{times[2]:02d}"
                    if self.states_raw[i] == self.on_state:
                        string += f" {on}\n"
                    else:
                        string += f" {off}\n"
        return string

class sscp_schedule_exceptions(sscp_schedule):
    """Handle SSCP schedule exceptions."""

    def __init__(
        self,
        uid: int,
        length: int,
        offset: int
    ) -> None:
        """Configure the SSCP schedule exceptions with individual parameters."""

        super().__init__(uid=uid, length=length, offset=offset)
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
        on_state = SCHEDULE_OFF
        for i in range(self.item_count):
            start = i * SCHEDULE_EXCEPTIONS_LEN
            self.times1_raw[i] = raw[start + SCHEDULE_EXCEPTIONS_1_START:start + SCHEDULE_EXCEPTIONS_1_END]
            self.times2_raw[i] = raw[start + SCHEDULE_EXCEPTIONS_2_START:start + SCHEDULE_EXCEPTIONS_2_END]
            self.states_raw[i] = raw[start + SCHEDULE_EXCEPTIONS_STATE_START:start + SCHEDULE_EXCEPTIONS_STATE_END]
            if self.states_raw[i] != SCHEDULE_OFF:
                if on_state == SCHEDULE_OFF:
                    on_state = self.states_raw[i]
                elif on_state != self.states_raw[i]:
                    raise ValueError("Multiple schedule on values")
        self.on_state = on_state

    def to_string(self, lang: str | None = None) -> str:
        """Return a string representation of the variable."""
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
            times1: datetime = scheduler_exceptions_hex_to_time(self.times1_raw[i])
            times2: datetime = scheduler_exceptions_hex_to_time(self.times2_raw[i])
            if times1 is not None and times2 is not None:
                # TODO: Format datetime in locale
                string += f"{days[times1.weekday()]} {times1:%d.%m.%Y %H:%M}"
                string += " - "
                string += f"{days[times1.weekday()]} {times2:%d.%m.%Y %H:%M}"
                if self.states_raw[i] == self.on_state:
                    string += f" {on}\n"
                else:
                    string += f" {off}\n"
        return string


def scheduler_base_hex_to_time(byte2) -> list[int]:
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


def scheduler_exceptions_hex_to_time(byte4) -> datetime | None:
    """Convert scheduler exceptions hex to time."""

    year = int.from_bytes(byte4[SCHEDULE_EXCEPTIONS_YEAR_START:SCHEDULE_EXCEPTIONS_YEAR_END], SSCP_DATA_ORDER)
    mins = int.from_bytes(byte4[SCHEDULE_EXCEPTIONS_MINS_START:SCHEDULE_EXCEPTIONS_MINS_END], SSCP_DATA_ORDER)
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
