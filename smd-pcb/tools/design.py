"""Single source of truth for the tap-tempo SMD board: parts, nets, LCSC numbers, placement.

Box coordinates (mm) like the enclosure model: x = width (0 left .. 60 right, seen from the front),
y = length (0 front/TAP .. 110 rear). The PCB lies at z = 7 (bottom) .. 8.6 (top).
KiCad coordinates: X = 100 + x, Y = 200 - y  (KiCad top edge = rear wall of the box).

Pin mapping is identical to the Arduino-Nano version (see PLAN.md section 1):
  D5 TAP, D4 Start/Stop, D3 ENC_A, D2 ENC_B, D10 opto1 -> tip, D9 opto2 -> ring,
  D1/TX MIDI (DIN5 via 220R, DIN4 via 220R to +5V), A4 SDA, A5 SCL, D13 LED.
"""

PROJECT = "taptempo-smd"

# ---------------- board outline (box coordinates) ----------------
BOARD_X0, BOARD_X1 = 4.0, 56.0
BOARD_Y0, BOARD_Y1 = 37.5, 107.5      # rear edge 0.5 mm in front of the inner rear wall (y = 108)
BOARD_R = 1.0                         # corner radius
# notch in the rear edge: the snout of the 3.5 mm jack (SJ1-3523N) hangs over the board edge and
# reaches 0.5 mm below the board surface, so the board is cut away under it (x0, x1, depth)
NOTCH = (42.4, 49.6, 2.2)
MOUNT_HOLES = [(8.0, 41.2), (52.0, 41.5), (7.0, 88.5), (52.5, 88.0)]   # M3, see H1..H4


def kxy(x, y):
    """box -> KiCad"""
    return 100.0 + x, 200.0 - y


# footprint shortcuts
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
HDR = "Connector_PinHeader_2.54mm:PinHeader_1x%02d_P2.54mm_Vertical"

# LCSC numbers (verified 2026-10-25 against the JLCPCB parts library, see tools/lcsc_check.py)
LCSC = {
    "220": "C22962", "1k": "C21190", "10k": "C25804", "5.1k": "C23186",
    "100nF": "C14663", "12pF": "C38523", "10uF": "C15850", "22uF": "C45783",
    "SS14": "C2480", "AMS1117-5.0": "C6187", "16MHz": "C13738",
    "LED_G": "C2297", "LED_R": "C2286",
    "ATmega328P-AU": "C14877", "CH340C": "C84681", "TYPE-C-31-M-12": "C165948", "PC817C": "C3025164",
    # through-hole parts (soldered by hand, not by JLCPCB) - LCSC numbers for ordering
    "PJ-102AH": "C3096093", "SJ1-3523N": "C20182914",
    "1x02": "C492401", "1x03": "C2937625", "1x04": "C2691448", "1x05": "C492404", "2x03": "C65114",
}

# ref: (lib_id, value, footprint, lcsc-key, {pin: net}, sch(x,y), pcb(x,y,rot), extra)
# pcb rot = KiCad rotation in degrees; nets: None = no-connect
P = {}


def part(ref, lib, value, fp, lcsc, pins, sch, pcb, tht=False, bom=True):
    P[ref] = dict(ref=ref, lib=lib, value=value, fp=fp, lcsc=LCSC.get(lcsc, "") if lcsc else "",
                  pins=pins, sch=sch, pcb=pcb, tht=tht, bom=bom)


# ---------------- MCU ----------------
part("U1", "MCU_Microchip_ATmega:ATmega328P-A", "ATmega328P-AU", "Package_QFP:TQFP-32_7x7mm_P0.8mm", "ATmega328P-AU",
     {"1": "ENC_A", "2": "STARTSTOP", "3": "GND", "4": "+5V", "5": "GND", "6": "+5V", "7": "XTAL1", "8": "XTAL2",
      "9": "TAP", "10": None, "11": None, "12": None, "13": "OPTO2", "14": "OPTO1", "15": "MOSI", "16": "MISO",
      "17": "SCK", "18": "+5V", "19": None, "20": "AREF", "21": "GND", "22": None, "23": None, "24": None,
      "25": None, "26": None, "27": "SDA", "28": "SCL", "29": "RESET", "30": "RXD", "31": "TXD", "32": "ENC_B"},
     (200.66, 116.84), (30.0, 74.0, 0))
part("Y1", "Device:Crystal_GND24", "16MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", "16MHz",
     {"1": "XTAL1", "2": "GND", "3": "XTAL2", "4": "GND"}, (147.32, 129.54), (21.2, 70.0, 0))
part("C10", "Device:C", "12pF", C0603, "12pF", {"1": "XTAL1", "2": "GND"}, (134.62, 144.78), (19.0, 73.0, 0))
part("C11", "Device:C", "12pF", C0603, "12pF", {"1": "XTAL2", "2": "GND"}, (160.02, 144.78), (19.0, 66.8, 0))
part("C12", "Device:C", "100nF", C0603, "100nF", {"1": "+5V", "2": "GND"}, (124.46, 177.8), (25.5, 80.6, 0))
part("C13", "Device:C", "100nF", C0603, "100nF", {"1": "+5V", "2": "GND"}, (134.62, 177.8), (23.4, 75.5, 90))
part("C14", "Device:C", "100nF", C0603, "100nF", {"1": "+5V", "2": "GND"}, (144.78, 177.8), (36.6, 72.0, 90))
part("C15", "Device:C", "100nF", C0603, "100nF", {"1": "AREF", "2": "GND"}, (154.94, 177.8), (36.6, 75.5, 90))
part("C16", "Device:C", "10uF", C0805, "10uF", {"1": "+5V", "2": "GND"}, (165.1, 177.8), (30.0, 82.2, 0))
part("R10", "Device:R", "10k", R0603, "10k", {"1": "+5V", "2": "RESET"}, (175.26, 177.8), (36.0, 80.0, 0))
part("R11", "Device:R", "1k", R0603, "1k", {"1": "SCK", "2": "LED_L"}, (185.42, 177.8), (37.0, 64.0, 90))
part("D10", "Device:LED", "LED_R (L, D13)", "LED_SMD:LED_0603_1608Metric", "LED_R", {"1": "GND", "2": "LED_L"},
     (198.12, 177.8), (37.0, 60.0, 90))

# ---------------- USB / serial ----------------
part("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C (TYPE-C-31-M-12)",
     "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "TYPE-C-31-M-12",
     {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
      "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN",
      "A8": None, "B8": None, "SH": "GND"},
     (40.64, 63.5), (28.0, 103.85, 180))
part("R1", "Device:R", "5.1k", R0603, "5.1k", {"1": "CC1", "2": "GND"}, (76.2, 50.8), (22.4, 97.0, 90))
part("R2", "Device:R", "5.1k", R0603, "5.1k", {"1": "CC2", "2": "GND"}, (86.36, 50.8), (33.8, 97.0, 90))
part("D2", "Diode:SS14", "SS14", "Diode_SMD:D_SMA", "SS14", {"1": "+5V", "2": "VBUS"}, (76.2, 83.82),
     (19.6, 101.6, 270))
part("U2", "Interface_USB:CH340C", "CH340C", "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", "CH340C",
     {"1": "GND", "2": "RXD", "3": "TXD", "4": "CH_V3", "5": "USB_DP", "6": "USB_DN", "7": None, "8": None,
      "9": None, "10": None, "11": None, "12": None, "13": "DTR", "14": None, "15": None, "16": "+5V"},
     (127.0, 63.5), (28.0, 91.0, 90))
part("C20", "Device:C", "100nF", C0603, "100nF", {"1": "+5V", "2": "GND"}, (106.68, 101.6), (35.0, 91.0, 90))
part("C21", "Device:C", "100nF", C0603, "100nF", {"1": "CH_V3", "2": "GND"}, (116.84, 101.6), (21.0, 89.6, 0))
part("C22", "Device:C", "100nF", C0603, "100nF", {"1": "DTR", "2": "RESET"}, (127.0, 101.6), (36.0, 84.0, 0))

# ---------------- power ----------------
part("J2", "Connector:Barrel_Jack_Switch", "9V DC (PJ-102AH), Minus innen",
     "Connector_BarrelJack:BarrelJack_CUI_PJ-102AH_Horizontal", "PJ-102AH",
     {"1": "GND", "2": "VIN_RAW", "3": None}, (40.64, 160.02), (11.5, 93.8, 180), tht=True)
part("D1", "Diode:SS14", "SS14", "Diode_SMD:D_SMA", "SS14", {"1": "VIN", "2": "VIN_RAW"}, (66.04, 157.48),
     (21.5, 83.5, 270))
part("U3", "Regulator_Linear:AMS1117-5.0", "AMS1117-5.0", "Package_TO_SOT_SMD:SOT-223-3_TabPin2", "AMS1117-5.0",
     {"1": "GND", "2": "+5V", "3": "VIN"}, (99.06, 157.48), (15.2, 84.0, 0))
part("C1", "Device:C", "10uF", C0805, "10uF", {"1": "VIN", "2": "GND"}, (83.82, 170.18), (12.5, 78.6, 0))
part("C2", "Device:C", "22uF", C0805, "22uF", {"1": "+5V", "2": "GND"}, (114.3, 170.18), (17.0, 78.6, 0))
part("R3", "Device:R", "1k", R0603, "1k", {"1": "+5V", "2": "LED_PWR"}, (127.0, 165.1), (15.5, 72.5, 0))
part("D3", "Device:LED", "LED_G (PWR)", "LED_SMD:LED_0805_2012Metric", "LED_G", {"1": "GND", "2": "LED_PWR"},
     (139.7, 165.1), (15.5, 75.3, 0))

# ---------------- outputs: optocouplers -> 3.5 mm TRS ----------------
part("R20", "Device:R", "220", R0603, "220", {"1": "OPTO1", "2": "OK1_A"}, (276.86, 50.8), (39.0, 86.0, 90))
part("R21", "Device:R", "220", R0603, "220", {"1": "OPTO2", "2": "OK2_A"}, (276.86, 83.82), (45.0, 74.0, 90))
part("U4", "Isolator:PC817", "PC817C", "Package_DIP:SMDIP-4_W9.53mm", "PC817C",
     {"1": "OK1_A", "2": "GND", "3": "SLEEVE", "4": "TIP"}, (304.8, 55.88), (44.0, 85.0, 90))
part("U5", "Isolator:PC817", "PC817C", "Package_DIP:SMDIP-4_W9.53mm", "PC817C",
     {"1": "OK2_A", "2": "GND", "3": "SLEEVE", "4": "RING"}, (304.8, 88.9), (50.5, 75.0, 90))
part("J3", "Connector_Audio:AudioJack3", "3.5mm TRS (SJ1-3523N)",
     "Connector_Audio:Jack_3.5mm_CUI_SJ1-3523N_Horizontal", "SJ1-3523N",
     {"T": "TIP", "R": "RING", "S": "SLEEVE"}, (355.6, 71.12), (46.0, 101.1, 180), tht=True)

# ---------------- MIDI ----------------
part("R30", "Device:R", "220", R0603, "220", {"1": "+5V", "2": "MIDI_4"}, (276.86, 121.92), (41.0, 57.0, 90))
part("R31", "Device:R", "220", R0603, "220", {"1": "TXD", "2": "MIDI_5"}, (289.56, 121.92), (46.1, 57.0, 90))
part("J7", "Connector_Generic:Conn_01x03", "MIDI DIN (4, 2=GND, 5)", HDR % 3, "1x03",
     {"1": "MIDI_4", "2": "GND", "3": "MIDI_5"}, (320.04, 124.46), (41.0, 52.0, 90), tht=True)

# ---------------- off-board controls ----------------
part("J4", "Connector_Generic:Conn_01x04", "OLED (5V SDA SCL GND)", HDR % 4, "1x04",
     {"1": "+5V", "2": "SDA", "3": "SCL", "4": "GND"}, (320.04, 160.02), (7.5, 75.0, 0), tht=True)
part("J5", "Connector_Generic:Conn_01x05", "Drehgeber (A GND B SW GND)", HDR % 5, "1x05",
     {"1": "ENC_A", "2": "GND", "3": "ENC_B", "4": "STARTSTOP", "5": "GND"}, (320.04, 195.58), (7.5, 57.0, 0),
     tht=True)
part("J6", "Connector_Generic:Conn_01x02", "TAP (TAP GND)", HDR % 2, "1x02",
     {"1": "TAP", "2": "GND"}, (320.04, 226.06), (7.5, 63.5, 0), tht=True)
part("C30", "Device:C", "100nF", C0603, "100nF", {"1": "ENC_A", "2": "GND"}, (276.86, 195.58), (15.0, 56.0, 90))
part("C31", "Device:C", "100nF", C0603, "100nF", {"1": "ENC_B", "2": "GND"}, (289.56, 195.58), (15.0, 51.0, 90))

# ---------------- ISP ----------------
part("J8", "Connector_Generic:Conn_02x03_Odd_Even", "ISP (Bootloader)",
     "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical", "2x03",
     {"1": "MISO", "2": "+5V", "3": "SCK", "4": "MOSI", "5": "RESET", "6": "GND"}, (243.84, 228.6),
     (42.0, 44.0, 270), tht=True)

# ---------------- mechanics ----------------
for i, (hx, hy) in enumerate(MOUNT_HOLES):
    part(f"H{i + 1}", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", None, {},
         (355.6 + 12.7 * i, 254.0), (hx, hy, 0), bom=False)

# power flags (schematic only)
PWR_FLAGS = {"#FLG01": "GND", "#FLG02": "VIN", "#FLG03": "VBUS"}

NETCLASS_POWER = ["+5V", "VIN", "VIN_RAW", "VBUS", "GND"]


def nets():
    n = {}
    for r, p in P.items():
        for pin, net in p["pins"].items():
            if net:
                n.setdefault(net, []).append((r, pin))
    return n


if __name__ == "__main__":
    for k, v in sorted(nets().items()):
        print(f"{k:10} {len(v):2}  {' '.join(a + '.' + b for a, b in v)}")
