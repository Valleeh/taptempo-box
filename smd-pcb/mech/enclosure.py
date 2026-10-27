"""Tap-tempo box, SMD version: enclosure (tray + lid) adapted to the JLCPCB board.

Adapted copy of ../nano-perfboard/mech/enclosure.py (perfboard version). Changes:
  * the board (../tools/design.py) carries USB-C, 9 V barrel jack and 3.5 mm jack on its rear edge,
    so the rear wall gets holes at the real connector positions (no panel-mount jacks any more);
  * 4 standoffs (M3 self-tapping, pilot 2.5 mm) at the board's mounting holes;
  * the board model is the KiCad STEP export (out/pcb.step) plus simple proxies for the two connectors
    without a KiCad 3D model (USB-C, PJ-102AH) and for the Dupont plugs on the pin headers.

Box coordinates (mm): x = width (0..60, left->right seen from the front), y = length (0 = front/TAP,
110 = rear/display), z = height (0 = floor).
Run:  ../../nano-perfboard/mech/.venv/bin/python enclosure.py   -> out/*.stl / *.step
"""
import os
import sys
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import design as D  # noqa: E402

# ---------------- parameters (shell, lid, controls: unchanged from the perfboard version) ----------------
W, L, H = 60.0, 110.0, 36.0
T = 2.0
FLOOR = 2.0
LID = 2.0
R_CORNER = 3.0
TRAY_H = H - LID

STANDOFF_H = 5.0
PCB_Z = FLOOR + STANDOFF_H        # board underside z = 7
PCB_T = 1.6
PCB_TOP = PCB_Z + PCB_T           # 8.6
STANDOFF_D = 6.5
SCREW_PILOT = 2.5                 # M3 self-tapping screw (e.g. 3 x 8 mm) into the printed standoff

TAP_POS, TAP_HOLE = (30.0, 20.0), 16.2
ENC_POS, ENC_HOLE = (30.0, 52.0), 7.2
DISP_POS = (30.0, 92.0)
DISP_PCB = (27.3, 27.8)
DISP_HOLES = (23.3, 23.8)
DISP_GLASS = (26.7, 19.3, 1.6)
DISP_WIN = (24.0, 13.0)
DISP_WIN_DY = 2.0

DIN_Y, DIN_Z, DIN_D = 68.0, 23.0, 16.0
DIN_SCREW_SP, DIN_SCREW_D = 22.4, 3.2

BOSS_D, BOSS_HOLE, LID_SCREW = 7.0, 2.6, 3.4
BOSS_POS = [(T + 3.6, T + 3.6), (W - T - 3.6, T + 3.6),
            (T + 3.6, L - T - 3.6), (W - T - 3.6, L - T - 3.6)]
REAR_BOSS_Z0 = 28.0

# ---------------- rear-wall connectors (positions from the PCB) ----------------
USB_X = D.P["J1"]["pcb"][0]
USB_Z = PCB_TOP + 3.26 / 2         # HRO TYPE-C-31-M-12: shell 8.94 x 3.26 mm, sits on the board
USB_OPEN = (13.0, 7.5)             # big enough for the plug overmould -> plug seats fully
DC_X = D.P["J2"]["pcb"][0]
DC_Z = PCB_TOP + 6.5               # PJ-102AH: barrel axis ~6.5 mm above the board (body 9 x 14.2 x 11)
DC_HOLE = 10.5                     # plug overmould (~9.5 mm) passes the 2 mm wall
TRS_X = D.P["J3"]["pcb"][0]
TRS_Z = PCB_TOP + 2.5              # SJ1-3523N: snout 6 x 6 mm, axis 2.5 mm above the board
TRS_HOLE = 7.0

OUT = os.path.join(HERE, "out")
PCB_STEP = os.path.join(OUT, "pcb.step")


def _box(cx, cy, z0, w, d, h):
    return cq.Workplane("XY").workplane(offset=z0).center(cx, cy).rect(w, d).extrude(h)


def tray():
    outer = cq.Workplane("XY").box(W, L, TRAY_H, centered=False).edges("|Z").fillet(R_CORNER)
    inner = (cq.Workplane("XY").workplane(offset=FLOOR)
             .center(T, T).box(W - 2 * T, L - 2 * T, TRAY_H, centered=False)
             .edges("|Z").fillet(max(R_CORNER - T, 0.5)))
    t = outer.cut(inner)

    for x, y in D.MOUNT_HOLES:                   # standoffs for the PCB
        t = t.union(cq.Workplane("XY").workplane(offset=FLOOR - 0.01).center(x, y)
                    .circle(STANDOFF_D / 2).extrude(STANDOFF_H + 0.01))
        t = t.cut(cq.Workplane("XY").workplane(offset=1.0).center(x, y)
                  .circle(SCREW_PILOT / 2).extrude(STANDOFF_H + 2))

    for x, y in BOSS_POS:                        # corner bosses for the lid screws
        z0 = FLOOR - 0.01 if y < L / 2 else REAR_BOSS_Z0
        sx = -1 if x < W / 2 else 1
        sy = -1 if y < L / 2 else 1
        boss = (cq.Workplane("XY").workplane(offset=z0).center(x, y).rect(BOSS_D, BOSS_D)
                .extrude(TRAY_H - z0).translate((sx * 1.0, sy * 1.0, 0)))
        t = t.union(boss)
        t = t.cut(cq.Workplane("XY").workplane(offset=TRAY_H - 10).center(x, y)
                  .circle(BOSS_HOLE / 2).extrude(11))

    rear = cq.Workplane("XZ", origin=(0, L + 1, 0))
    t = t.cut(rear.center(DC_X, DC_Z).circle(DC_HOLE / 2).extrude(T + 2))
    t = t.cut(rear.center(TRS_X, TRS_Z).circle(TRS_HOLE / 2).extrude(T + 2))
    t = t.cut(rear.center(USB_X, USB_Z).rect(*USB_OPEN).extrude(T + 2).edges("|Y").fillet(1.5))

    side = cq.Workplane("YZ", origin=(W - T - 1, 0, 0))
    t = t.cut(side.center(DIN_Y, DIN_Z).circle(DIN_D / 2).extrude(T + 2))
    for dy in (-DIN_SCREW_SP / 2, DIN_SCREW_SP / 2):
        t = t.cut(side.center(DIN_Y + dy, DIN_Z).circle(DIN_SCREW_D / 2).extrude(T + 2))
    return t


def lid():
    p = (cq.Workplane("XY").workplane(offset=TRAY_H)
         .box(W, L, LID, centered=False).edges("|Z").fillet(R_CORNER))
    top = cq.Workplane("XY").workplane(offset=TRAY_H - 1)
    p = p.cut(top.center(*TAP_POS).circle(TAP_HOLE / 2).extrude(LID + 2))
    p = p.cut(top.center(*ENC_POS).circle(ENC_HOLE / 2).extrude(LID + 2))
    wx, wy = DISP_POS[0], DISP_POS[1] + DISP_WIN_DY
    p = p.cut(top.center(wx, wy).rect(*DISP_WIN).extrude(LID + 2).edges("|Z").fillet(1.0))
    p = p.cut(cq.Workplane("XY").workplane(offset=H - 0.8).center(wx, wy)
              .rect(DISP_WIN[0] + 1.6, DISP_WIN[1] + 1.6).workplane(offset=0.81)
              .rect(DISP_WIN[0] + 3.2, DISP_WIN[1] + 3.2).loft())
    post_len = DISP_GLASS[2]
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = DISP_POS[0] + sx * DISP_HOLES[0] / 2
            y = DISP_POS[1] + sy * DISP_HOLES[1] / 2
            post = (cq.Workplane("XY").workplane(offset=TRAY_H + 0.01).center(x, y)
                    .circle(1.8).extrude(-post_len - 0.01))
            p = p.union(post).cut(cq.Workplane("XY").workplane(offset=TRAY_H - post_len - 0.1)
                                  .center(x, y).circle(0.8).extrude(post_len + 1.2))
    for x, y in BOSS_POS:
        p = p.cut(top.center(x, y).circle(LID_SCREW / 2).extrude(LID + 2))
        p = p.cut(cq.Workplane("XY").workplane(offset=H - 1.6).center(x, y)
                  .circle(LID_SCREW / 2).workplane(offset=1.61).circle(3.2).loft())
    return p


# ---------------- PCB (KiCad STEP) + proxies ----------------
def pcb():
    """KiCad export: X = 100 + x, STEP-Y = y - 200 (KiCad Y is mirrored in STEP), z from the board underside"""
    s = cq.importers.importStep(PCB_STEP)
    return s.translate((-100.0, 200.0, PCB_Z))


def connector_proxies():
    """USB-C and barrel jack have no KiCad 3D model -> datasheet boxes (front face at the board edge)"""
    edge = D.BOARD_Y1
    usb = _box(USB_X, edge - 7.35 / 2, PCB_TOP, 8.94, 7.35, 3.26)
    dc = _box(DC_X, edge - 14.2 / 2, PCB_TOP, 9.0, 14.2, 11.0)
    return usb, dc


def dupont_plugs():
    """female Dupont housings plugged onto every off-board header: 2.54 x 2.54 x 14 mm on top of the
    2.5 mm header plastic, plus 6 mm for the cable bend"""
    plugs = None
    for ref in ("J4", "J5", "J6", "J7"):
        x, y, rot = D.P[ref]["pcb"]
        n = len(D.P[ref]["pins"])
        for i in range(n):
            if rot == 0:
                px, py = x, y - 2.54 * i
            else:                                  # rot 90: pins run to +x
                px, py = x + 2.54 * i, y
            b = _box(px, py, PCB_TOP + 2.5, 2.54, 2.54, 14.0 + 6.0)
            plugs = b if plugs is None else plugs.union(b)
    return plugs


# ---------------- lid / wall parts ----------------
def encoder():
    x, y = ENC_POS
    bush_top = H + 2.5
    body = _box(x, y, bush_top - 7.0 - 6.5, 12.4, 13.2, 6.5)
    legs = _box(x, y, 21.0, 12.4, 13.2, bush_top - 7.0 - 6.5 - 21.0)   # pins/solder tags down to z ~21
    bush = cq.Workplane("XY").workplane(offset=bush_top - 7.0).center(x, y).circle(3.5).extrude(7.0)
    nut = cq.Workplane("XY").workplane(offset=H).center(x, y).polygon(6, 11).extrude(2.0).cut(
        cq.Workplane("XY").workplane(offset=H).center(x, y).circle(3.5).extrude(2.0))
    return body.union(bush).union(legs), nut


def knob():
    x, y = ENC_POS
    k = cq.Workplane("XY").workplane(offset=H + 2.6).center(x, y).circle(10.0).workplane(offset=15).circle(9.0).loft()
    return k.faces(">Z").edges().fillet(1.5)


def tap_button():
    x, y = TAP_POS
    body = cq.Workplane("XY").workplane(offset=H - 22).center(x, y).circle(8.0).extrude(22)
    ring = cq.Workplane("XY").workplane(offset=H).center(x, y).circle(9.5).extrude(1.5)
    cap = cq.Workplane("XY").workplane(offset=H + 1.5).center(x, y).circle(7.0).extrude(2.5).faces(">Z").edges().fillet(1.0)
    return body.union(ring), cap


def oled():
    x, y = DISP_POS
    glass_z = TRAY_H - DISP_GLASS[2]
    pcb_ = _box(x, y, glass_z - 1.2, *DISP_PCB, 1.2)
    glass = _box(x, y, glass_z, DISP_GLASS[0], DISP_GLASS[1], DISP_GLASS[2] - 0.05)
    hdr = _box(x, y + DISP_PCB[1] / 2 - 1.5, glass_z - 1.2 - 2.5 - 6.0, 10.2, 2.54, 8.5)  # pin header + Dupont
    return pcb_.union(hdr), glass


def din_socket():
    x_in = W - T
    flange = cq.Workplane("YZ", origin=(x_in - 1.5, 0, 0)).center(DIN_Y, DIN_Z).rect(DIN_SCREW_SP + 6, 19).extrude(1.5)
    body = cq.Workplane("YZ", origin=(x_in - 1.5, 0, 0)).center(DIN_Y, DIN_Z).circle(8.0).extrude(-16)
    face = cq.Workplane("YZ", origin=(x_in - 0.01, 0, 0)).center(DIN_Y, DIN_Z).circle(7.6).extrude(T + 0.01)
    return flange.union(body).union(face)


def plug_probes():
    """mating plugs, used to check that each connector is reachable through its wall hole"""
    usb_mould = cq.Workplane("XZ", origin=(0, D.BOARD_Y1 + 0.3, 0)).center(USB_X, USB_Z).rect(11.5, 6.0).extrude(-15)
    dc = (cq.Workplane("XZ", origin=(0, D.BOARD_Y1 + 0.3, 0)).center(DC_X, DC_Z).circle(4.75).extrude(-15))
    trs = (cq.Workplane("XZ", origin=(0, D.BOARD_Y1 + 0.5, 0)).center(TRS_X, TRS_Z).circle(3.0).extrude(-15))
    return usb_mould, dc, trs


PARTS_ON_LID = ("lid", "encoder", "encoder_nut", "knob", "tap_body", "tap_cap", "oled_pcb", "oled_glass")


def all_parts(with_pcb=True):
    enc, nut = encoder(); tb, tc = tap_button(); op, og = oled()
    usb, dc = connector_proxies()
    P = {"tray": (tray(), (0.20, 0.22, 0.25)), "lid": (lid(), (0.20, 0.22, 0.25))}
    if with_pcb:
        P["pcb"] = (pcb(), (0.10, 0.45, 0.20))
    P.update({"usb_c": (usb, (0.75, 0.76, 0.78)), "dc_jack": (dc, (0.12, 0.12, 0.13)),
              "dupont": (dupont_plugs(), (0.1, 0.1, 0.1)),
              "encoder": (enc, (0.75, 0.75, 0.78)), "encoder_nut": (nut, (0.8, 0.8, 0.82)),
              "knob": (knob(), (0.08, 0.08, 0.08)), "tap_body": (tb, (0.75, 0.75, 0.78)),
              "tap_cap": (tc, (0.85, 0.1, 0.1)), "oled_pcb": (op, (0.05, 0.25, 0.6)),
              "oled_glass": (og, (0.02, 0.02, 0.04)), "midi_din": (din_socket(), (0.7, 0.7, 0.72))})
    return P


def build():
    os.makedirs(OUT, exist_ok=True)
    P = all_parts()
    for n in ("tray", "lid"):
        cq.exporters.export(P[n][0], os.path.join(OUT, f"{n}.stl"), tolerance=0.05, angularTolerance=0.1)
        cq.exporters.export(P[n][0], os.path.join(OUT, f"{n}.step"))
    a = cq.Assembly(name="taptempo_smd")
    for n, (wp, col) in P.items():
        a.add(wp, name=n, color=cq.Color(*col, 1))
    a.save(os.path.join(OUT, "assembly.step"))
    return P


if __name__ == "__main__":
    build()
    print("rear wall: USB-C x=%.1f z=%.2f | 9V x=%.1f z=%.2f | 3.5mm x=%.1f z=%.2f" % (USB_X, USB_Z, DC_X, DC_Z, TRS_X, TRS_Z))
    print("standoffs:", D.MOUNT_HOLES)
