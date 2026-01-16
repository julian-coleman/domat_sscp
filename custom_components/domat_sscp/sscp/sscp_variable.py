"""SSCP (Shark Slave Communications Protocol) variables.

See Also:
  https://kb.mervis.info/lib/exe/fetch.php/cs:mervis-ide:sharkprotocolspecification_user_2017_05_30.pdf
"""

import logging
from typing import Any

from .sscp_const import (
    IEEE754_EXPONENT,
    IEEE754_EXPONENT_BIAS,
    IEEE754_EXPONENT_SHIFT,
    IEEE754_MAXIMUM_BITS,
    IEEE754_SIGN,
    IEEE754_SIGNIFICAND,
    IEEE754_SIGNIFICAND_LENGTH,
    SSCP_DATA_ORDER,
)

_LOGGER = logging.getLogger(__name__)


class sscp_variable:
    """SSCP Variable.

    Handles known types and their properties.
    Converts type 13 4-byte floats to and from IEEE754 format.
    Converts states to values and vice versa.
    """

    def __init__(
        self,
        uid: int,
        length: int,
        offset: int,
        type: int,
        name: str | None = None,
        description: str | None = None,
        page: str | None = None,
        maximum: float | None = None,
        minimum: float | None = None,
        step: float | None = None,
        states: dict[str, Any] | None = None,
        format: str | None = None,
        perm: str | None = None,
    ) -> None:
        """Configure the SSCP variable with individual parameters."""

        self.uid = uid
        self.length = length
        self.offset = offset
        self.type = type
        # We support a subset of types
        if self.type not in {64, 18, 13, 2, 0}:
            _LOGGER.warning("Unknown type for %d", self.uid)
        self.name = name
        self.description = description
        self.page = page
        self.maximum = maximum
        self.minimum = minimum
        if step is not None:
            self.step = step
        else:
            self.step = 0
        self.states = states
        self.format = format
        if perm is None or perm == "ro":
            self.perm = "ro"
        elif perm == "rw":
            self.perm = "rw"
        else:
            raise ValueError("Invalid permission")

        self.uid_bytes = self.uid.to_bytes(4, SSCP_DATA_ORDER)
        self.length_bytes = self.length.to_bytes(4, SSCP_DATA_ORDER)
        self.offset_bytes = self.offset.to_bytes(4, SSCP_DATA_ORDER)
        self.raw = bytearray("\x00", encoding="iso-8859-1")
        self.val = None
        self.state = "unknown"

    @classmethod
    def from_yaml(cls, yaml):
        "Configure the SSCP variable with paramaters via YAML."

        # Required
        try:
            uid = yaml["uid"]
            length = yaml["length"]
            offset = yaml["offset"]
            type = yaml["type"]
        except KeyError as e:
            e_str = "Missing parameter" + str(e)
            raise ValueError(e_str) from e
        # Can be None
        name = yaml.get("name")
        description = yaml.get("description")
        page = yaml.get("page")
        maximum = yaml.get("max")
        minimum = yaml.get("min")
        if "step_incr" in yaml:
            step = yaml["step_incr"]
        elif "step_incr" in yaml:
            step = yaml["step_decr"]
        else:
            step = 0
        states = yaml.get("states")
        format = yaml.get("format")
        perm = yaml.get("perm")

        return cls(
            uid=uid,
            length=length,
            offset=offset,
            type=type,
            name=name,
            description=description,
            page=page,
            maximum=maximum,
            minimum=minimum,
            step=step,
            states=states,
            format=format,
            perm=perm
        )

    def to_string(self):
        """Return a string representation of the variable."""

        # We haven't read the value yet
        if self.val is None:
            return None

        if self.type in {13, 2, 0}:
            if self.states is not None:
                return self.state
            if self.format is not None:
                return self.format % (self.val)
            return self.raw.hex()
        if self.length >= 16:
            string = ""
            for i in range(0, self.length, 4):
                string += self.raw[i:i+4].hex() + " "
            return string
        return self.raw.hex()

    def set_value(self, raw: bytearray) -> None:
        """Set the variable to the new raw value from the PLC.

        Directly updates the raw value.
        Parses the raw value depending on the variable type.
        """

        self.raw = raw
        _LOGGER.debug("Set %d to 0x%s", self.uid, self.raw.hex())

        match self.type:
            case 18:  # 8-byte int
                self.val = int.from_bytes(raw, SSCP_DATA_ORDER)
            case 13:  # 4-byte float
                self.val = ieee754_to_float(raw)
            case 2:  # 2-byte int or state
                self.val = int.from_bytes(raw, SSCP_DATA_ORDER)
                if self.states is not None:
                    self.state = "unknown"  # Default
                    for state in self.states:
                        if state["state"] == self.val:
                            self.state = state["text"]
            case 0:  # bool (1-byte int)
                self.val = int.from_bytes(raw, SSCP_DATA_ORDER)
                if self.states is not None:
                    self.state = "unknown"  # Default
                    for state in self.states:
                        if state["state"] == self.val:
                            self.state = state["text"]
            case 64:  # scehdule (converted in schedule classes)
                self.val = raw
            case _:  # unknown type
                _LOGGER.warning("Set unknown type for %d", self.uid)
                self.val = int.from_bytes(raw, SSCP_DATA_ORDER)

    def change_value(self, new: Any) -> None:
        """Change the variable using the new readable value.

        Parses readable values and state changes and updates the value and raw value.
        """

        _LOGGER.debug("Change %d to %s", self.uid, new)

        if self.perm != "rw":
            msg = f"Variable is read-only: {self.uid}"
            raise ValueError(msg)
        # We haven't read the value yet
        if self.val is None and new in ("+", "-"):
            msg = f"Variable has no current value: {self.uid}"
            raise ValueError(msg)
        if new is None:
            msg = f"Variable has no new value: {self.uid}"
            raise ValueError(msg)

        match self.type:
            case 13:  # 4-byte float
                if new == "+" and self.step != 0:
                    self.val = self.val + self.step
                elif new == "-" and self.step != 0:
                    self.val = self.val - self.step
                else:
                    self.val = float(new)
                if self.maximum is not None and self.val > self.maximum:
                    self.val = self.maximum
                if self.minimum is not None and self.val < self.minimum:
                    self.val = self.minimum
                self.raw = float_to_ieee754(self.val)
                _LOGGER.debug("New 4-byte: %s (%s)", self.val, self.raw.hex())
                return

            case 2:  # 2-byte int or state
                if self.states is not None:
                    self.val, self.raw = change_state(
                        uid=self.uid,
                        length=self.length,
                        states=self.states,
                        old=self.val,
                        new=new,
                    )
                if isinstance(new, str) and new.lower().startswith("0x"):
                    self.val = int(new, 16)
                else:
                    self.val = int(new)
                self.raw = self.val.to_bytes(2, SSCP_DATA_ORDER)
                _LOGGER.debug("New 2-byte: %s (%s)", self.val, self.raw.hex())
                return

            case 0:  # 1-byte int (bool) or state
                if self.states is not None:
                    self.val, self.raw = change_state(
                        uid=self.uid,
                        length=self.length,
                        states=self.states,
                        old=self.val,
                        new=new,
                    )
                if new in {"+", "-"}:
                    if self.val == 0:
                        self.val = 1
                    else:
                        self.val = 0
                elif isinstance(new, str) and new.lower().startswith("0x"):
                    self.val = int(new, 16)
                else:
                    self.val = int(new)
                self.raw = self.val.to_bytes(1, SSCP_DATA_ORDER)
                _LOGGER.debug("New 1-byte: %s (%s)", self.val, self.raw.hex())
                return

            case _:
                _LOGGER.debug("Change unknown type: %d", self.uid)
                if isinstance(new, str) and new.lower().startswith("0x"):
                    self.val = int(new, 16)
                else:
                    self.val = int(new)
                self.raw = self.val.to_bytes(self.length, SSCP_DATA_ORDER)
                _LOGGER.debug("New %s-byte: %s (%s)", self.length, self.val, self.raw.hex())
                return

        msg = f"Unmatched variable type: {self.uid}"
        raise ValueError(msg)


def ieee754_to_float(byte4) -> float:
    """Convert IEEE754 hex representation to float."""
    if len(byte4) != 4:
        return 0.0

    val = int.from_bytes(byte4, SSCP_DATA_ORDER)
    if val == 0:
        return 0.0
    if val & IEEE754_SIGN:
        sign = 1
    else:
        sign = 0
    exp = ((val & IEEE754_EXPONENT) >> IEEE754_EXPONENT_SHIFT) - IEEE754_EXPONENT_BIAS
    sig = val & IEEE754_SIGNIFICAND
    res = pow(2, exp)
    mult = 1
    for i in range(1, IEEE754_SIGNIFICAND_LENGTH + 1):
        if sig & (1 << (IEEE754_SIGNIFICAND_LENGTH - i)):
            mult += 1.0 / pow(2, i)
    res *= mult
    if sign == 1:
        res = 0.0 - res
    _LOGGER.debug("IEEE754: 0x%08x = %f", (sign + exp + sig), res)
    return res


def float_to_ieee754(val) -> bytes:
    """Convert float to IEEE754 hex representation."""
    if val == 0:
        return (0).to_bytes(4, SSCP_DATA_ORDER)
    if val < 0:
        sign = IEEE754_SIGN
        val = 0 - val
    else:
        sign = 0
    max2 = 0
    for i in range(IEEE754_MAXIMUM_BITS):
        if (1 << i) < val:
            max2 = i
    exp = (max2 + IEEE754_EXPONENT_BIAS) << IEEE754_EXPONENT_SHIFT
    mult = val / (1 << max2) - 1
    sig = 0
    for i in range(1, IEEE754_SIGNIFICAND_LENGTH):
        div = 1.0 / pow(2, i)
        if div <= mult:
            sig = sig | (1 << (IEEE754_SIGNIFICAND_LENGTH - i))
            mult -= div
    _LOGGER.debug("IEEE754: %f = 0x%08x", val, (sign + exp + sig))
    return (sign + exp + sig).to_bytes(4, SSCP_DATA_ORDER)


def change_state(
    uid: int, length: int, states: dict[str, Any], old: int, new: str | int
) -> tuple[int, bytearray]:
    """Find the next, previous or matching state."""

    if new == "+":
        for state in states:
            if (state["state"] == old) and state.get("nextstate") is not None:
                _LOGGER.debug("new state +: %s %s", uid, state["nextstate"])
                val = state["nextstate"]
                raw = state["nextstate"].to_bytes(length, SSCP_DATA_ORDER)
                return [val, raw]
    elif new == "-":
        for state in states:
            if state.get("nextstate") is not None and state["nextstate"] == old:
                _LOGGER.debug("new state -: %s %s", uid, state["state"])
                val = state["state"]
                raw = state["state"].to_bytes(length, SSCP_DATA_ORDER)
                return [val, raw]
    else:
        val = int(new)
        for state in states:
            if state["state"] == val:
                _LOGGER.debug("new state: %s %s", uid, state["state"])
                raw = state["state"].to_bytes(length, SSCP_DATA_ORDER)
                return [val, raw]
    msg = f"Unknown state or next state: {uid}"
    raise ValueError(msg)
