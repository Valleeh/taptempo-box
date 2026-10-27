"""Perfboard (Lochraster) layout for the tap-tempo box.

Single source of truth for: connectivity check against the schematic, the
SVG build drawings and the simplified 3D model used in the enclosure.

Grid: columns A..R (18), rows 1..24 on a standard 50 x 70 mm board.
Seen from the component side, row 1 is the rear edge (USB side), column A is left.
"""
from collections import defaultdict

COLS = "ABCDEFGHIJKLMNOPQR"
ROWS = 24
PITCH = 2.54
BOARD_W, BOARD_H = 50.0, 70.0
X0 = (BOARD_W - (len(COLS) - 1) * PITCH) / 2      # board edge -> column A centre
Y0 = (BOARD_H - (ROWS - 1) * PITCH) / 2           # rear edge  -> row 1 centre
MOUNT_HOLES = [(2.5, 2.5), (BOARD_W - 2.5, 2.5), (2.5, BOARD_H - 2.5), (BOARD_W - 2.5, BOARD_H - 2.5)]


def hole_xy(h):
    """'K12' -> board-local mm (x from left edge, y from rear edge)."""
    return X0 + COLS.index(h[0]) * PITCH, Y0 + (int(h[1:]) - 1) * PITCH


def cr(h):
    return COLS.index(h[0]), int(h[1:])


def name(c, r):
    return f"{COLS[c]}{r}"


# ---------------------------------------------------------------- components
# kind decides how it is drawn / modelled; pins map hole -> (pin label, net)
NANO_LEFT = ["D13", "3V3", "REF", "A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "5V", "RST", "GND", "VIN"]
NANO_RIGHT = ["D12", "D11", "D10", "D9", "D8", "D7", "D6", "D5", "D4", "D3", "D2", "GND", "RST", "RX0", "TX1"]
NANO_NETS = {"A4": "SDA", "A5": "SCL", "5V": "+5V", "VIN": "VIN", "D10": "OPTO1", "D9": "OPTO2",
             "D5": "TAP", "D4": "STARTSTOP", "D3": "ENC_A", "D2": "ENC_B", "TX1": "MIDI_TX"}

COMPONENTS = []


def comp(ref, kind, value, pins, **kw):
    COMPONENTS.append(dict(ref=ref, kind=kind, value=value, pins=pins, **kw))


nano_pins = {}
for i, p in enumerate(NANO_LEFT):
    nano_pins[f"E{i+1}"] = (p, "GND" if (p == "GND" and i == 13) else NANO_NETS.get(p))
for i, p in enumerate(NANO_RIGHT):
    nano_pins[f"K{i+1}"] = (p, NANO_NETS.get(p))
comp("U1", "nano", "Arduino Nano (in 2 Buchsenleisten 15-pol.)", nano_pins)

comp("R3", "res", "220 Ω", {"L3": ("1", "OPTO1"), "L7": ("2", "OK1_A")})
comp("R4", "res", "220 Ω", {"L8": ("1", "OPTO2"), "L12": ("2", "OK2_A")})
comp("U2", "dip4", "PC817 (im Sockel)", {"M7": ("1", "OK1_A"), "M8": ("2", "GND"), "P8": ("3", "SLEEVE"), "P7": ("4", "TIP")})
comp("U3", "dip4", "PC817 (im Sockel)", {"M12": ("1", "OK2_A"), "M13": ("2", "GND"), "P13": ("3", "SLEEVE"), "P12": ("4", "RING")})
comp("J7", "hdr", "Klinke (TIP, SLEEVE, RING)", {"R7": ("T", "TIP"), "R8": ("S", "SLEEVE"), "R9": ("R", "RING")})
comp("J4", "hdr", "OLED (5V, SDA, SCL, GND)", {"B7": ("5V", "+5V"), "B8": ("SDA", "SDA"), "B9": ("SCL", "SCL"), "B10": ("GND", "GND")})
comp("D1", "diode", "1N5817 (Ring zur Mitte!)", {"A20": ("A", "VIN9"), "E20": ("K", "VIN")})
comp("J3", "hdr90", "9 V (+, −)", {"A24": ("+", "VIN9"), "B24": ("−", "GND")})
comp("C1", "cap", "100 nF", {"G23": ("", "ENC_A"), "F23": ("", "GND")})
comp("C2", "cap", "100 nF", {"I23": ("", "ENC_B"), "J23": ("", "GND")})
comp("J5", "hdr90", "Drehgeber (A, C, B, SW, SW)", {"G24": ("A", "ENC_A"), "H24": ("C", "GND"), "I24": ("B", "ENC_B"),
                                                    "J24": ("SW", "STARTSTOP"), "K24": ("SW", "GND")})
comp("SW1", "hdr90", "TAP-Taster", {"M24": ("1", "TAP"), "N24": ("2", "GND")})
comp("R1", "res", "220 Ω", {"P19": ("1", "+5V"), "P23": ("2", "MIDI_4")})
comp("R2", "res", "220 Ω", {"R19": ("1", "MIDI_TX"), "R23": ("2", "MIDI_5")})
comp("J1", "hdr90", "MIDI (DIN 4, 2, 5)", {"P24": ("4", "MIDI_4"), "Q24": ("2", "GND"), "R24": ("5", "MIDI_5")})

# ---------------------------------------------------------------- wiring (solder side)
# bare: tinned wire / bent leg along a row or column, soldered at every listed point
# ins:  insulated wire between two points (may cross things)
BARE = [
    ("OPTO1", ["K3", "L3"]), ("OK1_A", ["L7", "M7"]), ("OK2_A", ["L12", "M12"]),
    ("TIP", ["P7", "R7"]), ("SLEEVE", ["P8", "R8"]), ("SLEEVE", ["Q8", "Q13"]), ("SLEEVE", ["Q13", "P13"]),
    ("SDA", ["E8", "B8"]), ("SCL", ["E9", "B9"]),
    ("GND", ["B10", "B22"]), ("GND", ["E14", "D14", "D22"]), ("GND", ["M13", "L13", "L22"]),
    ("GND", ["B22", "Q22"]),
    ("GND", ["B24", "B22"]), ("GND", ["H24", "H22"]), ("GND", ["K24", "K22"]), ("GND", ["N24", "N22"]),
    ("GND", ["Q24", "Q22"]), ("GND", ["F23", "F22"]), ("GND", ["J23", "J22"]),
    ("ENC_A", ["G23", "G24"]), ("ENC_B", ["I23", "I24"]),
    ("MIDI_4", ["P23", "P24"]), ("MIDI_5", ["R23", "R24"]),
    ("VIN9", ["A24", "A20"]), ("VIN", ["E20", "E15"]),
]
INSULATED = [
    ("OPTO2", "K4", "L8", "gelb"), ("GND", "M8", "M13", "schwarz"), ("RING", "P12", "R9", "grün"),
    ("+5V", "E12", "B7", "rot"), ("+5V", "E12", "P19", "rot"), ("MIDI_TX", "K15", "R19", "orange"),
    ("TAP", "K8", "M24", "weiß"), ("STARTSTOP", "K9", "J24", "violett"),
    ("ENC_A", "K10", "G24", "blau"), ("ENC_B", "K11", "I24", "blau"),
]

# what the schematic says (net -> pins), used for the check
EXPECTED = {
    "OPTO1": {"U1.D10", "R3.1"}, "OK1_A": {"R3.2", "U2.1"}, "OPTO2": {"U1.D9", "R4.1"}, "OK2_A": {"R4.2", "U3.1"},
    "TIP": {"U2.4", "J7.T"}, "SLEEVE": {"U2.3", "U3.3", "J7.S"}, "RING": {"U3.4", "J7.R"},
    "SDA": {"U1.A4", "J4.SDA"}, "SCL": {"U1.A5", "J4.SCL"}, "+5V": {"U1.5V", "J4.5V", "R1.1"},
    "MIDI_4": {"R1.2", "J1.4"}, "MIDI_TX": {"U1.TX1", "R2.1"}, "MIDI_5": {"R2.2", "J1.5"},
    "TAP": {"U1.D5", "SW1.1"}, "STARTSTOP": {"U1.D4", "J5.SW@J24"}, "ENC_A": {"U1.D3", "J5.A", "C1.ENC_A"},
    "ENC_B": {"U1.D2", "J5.B", "C2.ENC_B"}, "VIN9": {"J3.+", "D1.A"}, "VIN": {"D1.K", "U1.VIN"},
    "GND": {"U1.GND@E14", "U2.2", "U3.2", "J4.GND", "J3.−", "J5.C", "J5.SW@K24", "C1.GND", "C2.GND", "SW1.2", "J1.2"},
}


def pin_id(c, hole, label, net):
    if c["ref"] in ("C1", "C2"):
        return f"{c['ref']}.{net}"
    if c["ref"] == "J5" and label == "SW" or c["ref"] == "U1" and label == "GND":
        return f"{c['ref']}.{label}@{hole}"
    return f"{c['ref']}.{label}"


def check():
    errors = []
    pin_at = {}
    for c in COMPONENTS:
        for h, (label, net) in c["pins"].items():
            if h in pin_at:
                errors.append(f"hole {h} used twice ({pin_at[h][0]} and {c['ref']})")
            pin_at[h] = (c["ref"], pin_id(c, h, label, net), net)
            col, row = cr(h)
            assert 0 <= col < len(COLS) and 1 <= row <= ROWS, h

    parent = {}
    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def union(a, b): parent[find(a)] = find(b)

    bare_owner = {}
    for net, pts in BARE:
        for a, b in zip(pts, pts[1:]):
            (ca, ra), (cb, rb) = cr(a), cr(b)
            if ca != cb and ra != rb:
                errors.append(f"bare wire {a}-{b} not straight")
                continue
            steps = max(abs(cb - ca), abs(rb - ra))
            for k in range(steps + 1):
                h = name(ca + (cb - ca) * k // steps, ra + (rb - ra) * k // steps)
                if h in pin_at and pin_at[h][2] != net:
                    errors.append(f"bare wire {net} {a}-{b} touches {h} ({pin_at[h][1]}, net {pin_at[h][2]})")
                if h in bare_owner and bare_owner[h] != net:
                    errors.append(f"bare wires {bare_owner[h]} and {net} share hole {h}")
                bare_owner[h] = net
                union(h, a)
    for net, a, b, _ in INSULATED:
        for h in (a, b):
            if h not in pin_at and h not in bare_owner:
                errors.append(f"insulated wire {net} ends at empty hole {h}")
        union(a, b)

    groups = defaultdict(set)
    for h, (ref, pid, net) in pin_at.items():
        groups[find(h)].add(pid)
    found = {frozenset(g) for g in groups.values() if len(g) > 1}
    want = {frozenset(v) for v in EXPECTED.values()}
    for g in want - found:
        errors.append("net incomplete or merged: " + ", ".join(sorted(g)))
    for g in found - want:
        errors.append("unexpected connection: " + ", ".join(sorted(g)))
    return errors


if __name__ == "__main__":
    errs = check()
    print("\n".join(errs) if errs else f"OK: {len(EXPECTED)} Netze stimmen mit dem Schaltplan überein, "
          f"{len(BARE)} blanke Brücken, {len(INSULATED)} isolierte Drähte")
