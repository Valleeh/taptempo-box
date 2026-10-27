"""Perfboard variant with a second, separate TRS output (2 more PC817 optocouplers).

Everything from perfboard.py stays where it is. Added in the free area below the Nano:
  D7 -> R5 -> U4 (PC817) -> J8 Tip    (output 3)
  D6 -> R6 -> U5 (PC817) -> J8 Ring   (output 4)
J8 has its own sleeve (SLEEVE2), so the second jack is isolated from the first one
and from the box ground, just like J7.

Run: python3 perfboard_2trs.py   -> layout check against the schematic
"""
import copy

import perfboard as base
from perfboard import (COLS, ROWS, PITCH, BOARD_W, BOARD_H, X0, Y0, MOUNT_HOLES,  # noqa: F401  (same grid API)
                       hole_xy, cr, name)

NAME = "2trs"
TITLE = "2 Klinken"

COMPONENTS = copy.deepcopy(base.COMPONENTS)
BARE = list(base.BARE)
INSULATED = list(base.INSULATED)
EXPECTED = copy.deepcopy(base.EXPECTED)

# Nano pins D7 (K6) and D6 (K7) get nets
nano = next(c for c in COMPONENTS if c["ref"] == "U1")
nano["pins"]["K6"] = ("D7", "OPTO3")
nano["pins"]["K7"] = ("D6", "OPTO4")


def comp(ref, kind, value, pins, **kw):
    COMPONENTS.append(dict(ref=ref, kind=kind, value=value, pins=pins, **kw))


comp("R5", "res", "220 Ω", {"M15": ("1", "OPTO3"), "Q15": ("2", "OK3_A")})
comp("R6", "res", "220 Ω", {"M17": ("1", "OPTO4"), "Q17": ("2", "OK4_A")})
comp("U4", "dip4", "PC817 (im Sockel)", {"G17": ("1", "OK3_A"), "G18": ("2", "GND"), "J18": ("3", "SLEEVE2"), "J17": ("4", "TIP2")})
comp("U5", "dip4", "PC817 (im Sockel)", {"G20": ("1", "OK4_A"), "G21": ("2", "GND"), "J21": ("3", "SLEEVE2"), "J20": ("4", "RING2")})
comp("J8", "hdr", "Klinke 2 (TIP, SLEEVE, RING)", {"K17": ("T", "TIP2"), "K18": ("S", "SLEEVE2"), "K19": ("R", "RING2")})

BARE += [
    ("TIP2", ["J17", "K17"]),
    ("SLEEVE2", ["K18", "J18", "I18", "I21", "J21"]),
    ("RING2", ["J20", "K20", "K19"]),
    ("GND", ["G18", "F18", "F22"]),
    ("GND", ["G21", "G22"]),
]
INSULATED += [
    ("OPTO3", "K6", "M15", "gelb"), ("OK3_A", "Q15", "G17", "grün"),
    ("OPTO4", "K7", "M17", "gelb"), ("OK4_A", "Q17", "G20", "grün"),
]

EXPECTED.update({
    "OPTO3": {"U1.D7", "R5.1"}, "OK3_A": {"R5.2", "U4.1"}, "OPTO4": {"U1.D6", "R6.1"}, "OK4_A": {"R6.2", "U5.1"},
    "TIP2": {"U4.4", "J8.T"}, "SLEEVE2": {"U4.3", "U5.3", "J8.S"}, "RING2": {"U5.4", "J8.R"},
})
EXPECTED["GND"] = EXPECTED["GND"] | {"U4.2", "U5.2"}


def check():
    return base.check(COMPONENTS, BARE, INSULATED, EXPECTED)


if __name__ == "__main__":
    errs = check()
    print("\n".join(errs) if errs else f"OK: {len(EXPECTED)} Netze stimmen mit dem Schaltplan überein, "
          f"{len(BARE)} blanke Brücken, {len(INSULATED)} isolierte Drähte")
