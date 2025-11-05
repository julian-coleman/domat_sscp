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
    Converts 4-byte floats to and from IEEE754 format.
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
        increment: float | None = None,
        maximum: float | None = None,
        decrement: float | None = None,
        minimum: float | None = None,
        states: dict[str, Any] | None = None,
        format: str | None = None,
        perm: str | None = None,
    ) -> None:
        """Configure the SSCP variable with individual parameters."""

        self.uid = uid
        self.length = length
        self.offset = offset
        self.type = type
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if page is not None:
            self.page = page
        if increment is not None:
            self.increment = increment
        if maximum is not None:
            self.maximum = maximum
        if decrement is not None:
            self.decrement = decrement
        if minimum is not None:
            self.minimum = minimum
        if states is not None:
            self.states = states
        if format is not None:
            self.format = format
        if perm is not None:
            self.perm = "rw"
        else:
            self.perm = "ro"

        self.uid_bytes = self.uid.to_bytes(4, SSCP_DATA_ORDER)
        self.length_bytes = self.length.to_bytes(4, SSCP_DATA_ORDER)
        self.offset_bytes = self.offset.to_bytes(4, SSCP_DATA_ORDER)
        self.raw = bytearray("\x00", encoding="iso-8859-1")
        self.val = 0
        self.states = None
        self.state = ""

    # TODO: Initialisation from yaml
    #    @classmethod
    #    def from_yaml(cls, yaml) -> None:
    #        "Configure the SSCP variable with paramaters via YAML."
    #
    #        cls(
    #        )

    def to_string(self):
        """Return a string representation of the variable."""
        if self.type in {13, 2, 0}:
            if len(self.states) > 0:
                return self.state
            if self.format is not None:
                return self.format % (self.val)
            return str(self.val)
        return self.raw.hex()

    def set_value(self, raw: bytearray) -> None:
        """Set the variable to the new raw value.

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
                self.state = self.val  # Default
                if len(self.states) > 0:
                    for state in self.states:
                        if state["state"] == self.val:
                            self.state = state["text"]
            case 0:  # bool (1-byte int)
                self.val = int.from_bytes(raw, SSCP_DATA_ORDER)
                self.state = self.val  # Default
                for state in self.states:
                    if state["state"] == self.val:
                        self.state = state["text"]
            case _:  # unknown type
                _LOGGER.error("Set unknown type for %d", self.uid)
                self.val = int.from_bytes(raw, SSCP_DATA_ORDER)

    def change_value(self, value: str) -> bytearray:
        """Change the variable to the new readable value.

        Parses readable values and state changes and updates the raw value.
        """

        # TODO: Fix placeholder
        _LOGGER.debug("Change %d to 0x%x", self.uid, value)
        return (0).to_bytes(self.length, SSCP_DATA_ORDER)


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
        sign = 1
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
