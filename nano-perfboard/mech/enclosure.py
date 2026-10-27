"""Tap-tempo box: parametric enclosure (tray + lid) and full 3D assembly.

Box coordinates (mm): x = width (0..60, left->right seen from the front),
y = length (0 = front/TAP end, 110 = rear/display end), z = height (0 = floor).
The perfboard layout comes from ../perfboard/perfboard.py.
Run:  .venv/bin/python enclosure.py   -> writes STEP/STL/GLB into ./out
"""
import os
import sys
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "perfboard"))
import perfboard as PB  # noqa: E402

# ---------------- parameters ----------------
W, L, H = 60.0, 110.0, 36.0      # outer size
T = 2.0                          # wall thickness
FLOOR = 2.0
LID = 2.0
R_CORNER = 3.0
TRAY_H = H - LID

# perfboard placement (50 x 70 mm, component side up, row 1 at the rear)
BOARD_X0 = 5.0                   # left board edge
BOARD_Y_REAR = 107.5             # rear board edge (0.5 mm from the inner rear wall)
STANDOFF_H = 5.0
PCB_Z = FLOOR + STANDOFF_H
PCB_T = 1.6
PCB_TOP = PCB_Z + PCB_T
SOCKET_H = 8.5                   # female header height under the Nano
BOARD_SCREW_PILOT = 1.6          # M2 self-tapping into the standoffs

# lid controls (x, y)
TAP_POS, TAP_HOLE = (30.0, 20.0), 16.2        # 16 mm momentary pushbutton
ENC_POS, ENC_HOLE = (30.0, 52.0), 7.2         # EC11 encoder with push switch (M7 bushing)
DISP_POS = (30.0, 92.0)                       # centre of the OLED module
DISP_PCB = (27.3, 27.8)                       # 0.96" SSD1306 I2C module
DISP_HOLES = (23.3, 23.8)                     # M2 hole spacing (x, y)
DISP_GLASS = (26.7, 19.3, 1.6)                # glass w, h, thickness
DISP_WIN = (24.0, 13.0)                       # visible window cut-out
DISP_WIN_DY = 2.0                             # active area sits ~2 mm towards the pin header (rear)

# rear wall (y = L): panel-mount jacks + USB of the socketed Nano
DC_X, DC_Z, DC_D = 10.0, 21.0, 8.0            # 5.5/2.1 panel jack (start small, drill up if needed)
TRS_X, TRS_Z, TRS_D = 44.0, 21.0, 6.2         # 3.5 mm stereo panel jack, M6 thread
USB_W, USB_H = 13.0, 9.0

# right wall (x = W): panel-mount MIDI DIN socket
DIN_Y, DIN_Z, DIN_D = 68.0, 23.0, 16.0
DIN_SCREW_SP, DIN_SCREW_D = 22.4, 3.2

# lid screws into corner bosses
BOSS_D, BOSS_HOLE, LID_SCREW = 7.0, 2.6, 3.4
BOSS_POS = [(T + 3.6, T + 3.6), (W - T - 3.6, T + 3.6),
            (T + 3.6, L - T - 3.6), (W - T - 3.6, L - T - 3.6)]
REAR_BOSS_Z0 = 28.0             # rear bosses hang from the top, above the panel jacks

OUT = os.path.join(HERE, "out")


def board_xy(bx, by):
    """board-local mm (from left edge / rear edge) -> box x, y"""
    return BOARD_X0 + bx, BOARD_Y_REAR - by


def hole_box(h):
    return board_xy(*PB.hole_xy(h))


def nano_axis():
    (xe, _), (xk, y1) = hole_box("E1"), hole_box("K1")
    return (xe + xk) / 2, y1


USB_X = nano_axis()[0]
USB_Z = PCB_TOP + SOCKET_H + 1.6 + 2.0
BOARD_HOLES = [board_xy(*p) for p in PB.MOUNT_HOLES]


def tray():
    outer = cq.Workplane("XY").box(W, L, TRAY_H, centered=False).edges("|Z").fillet(R_CORNER)
    inner = (cq.Workplane("XY").workplane(offset=FLOOR)
             .center(T, T).box(W - 2 * T, L - 2 * T, TRAY_H, centered=False)
             .edges("|Z").fillet(max(R_CORNER - T, 0.5)))
    t = outer.cut(inner)

    for x, y in BOARD_HOLES:                     # standoffs for the perfboard
        t = t.union(cq.Workplane("XY").workplane(offset=FLOOR - 0.01).center(x, y)
                    .circle(2.6).extrude(STANDOFF_H + 0.01))
        t = t.cut(cq.Workplane("XY").workplane(offset=1.0).center(x, y)
                  .circle(BOARD_SCREW_PILOT / 2).extrude(STANDOFF_H + 2))

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
    t = t.cut(rear.center(DC_X, DC_Z).circle(DC_D / 2).extrude(T + 2))
    t = t.cut(rear.center(TRS_X, TRS_Z).circle(TRS_D / 2).extrude(T + 2))
    t = t.cut(rear.center(USB_X, USB_Z).rect(USB_W, USB_H).extrude(T + 2).edges("|Y").fillet(1.5))

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
    post_len = DISP_GLASS[2]          # posts rest on the module PCB next to the glass
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


# ---------------- perfboard model (from the layout data) ----------------
def _box(cx, cy, z0, w, d, h):
    return cq.Workplane("XY").workplane(offset=z0).center(cx, cy).rect(w, d).extrude(h)


def perfboard_parts():
    """returns dict name -> (workplane, rgb)"""
    parts = {}
    b = _box(BOARD_X0 + PB.BOARD_W / 2, BOARD_Y_REAR - PB.BOARD_H / 2, PCB_Z, PB.BOARD_W, PB.BOARD_H, PCB_T)
    for p in PB.MOUNT_HOLES:
        b = b.cut(cq.Workplane("XY").workplane(offset=PCB_Z - 1).center(*board_xy(*p)).circle(1.0).extrude(PCB_T + 2))
    parts["perfboard"] = (b, (0.78, 0.62, 0.38))

    dark, metal, gold = (0.12, 0.13, 0.15), (0.75, 0.76, 0.78), (0.85, 0.7, 0.3)
    sockets = None; bodies = {}
    def add(key, wp, col):
        if key in bodies:
            bodies[key] = (bodies[key][0].union(wp), col)
        else:
            bodies[key] = (wp, col)

    for c in PB.COMPONENTS:
        pins = [hole_box(h) for h in c["pins"]]
        xs = [p[0] for p in pins]; ys = [p[1] for p in pins]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        k = c["kind"]
        if k == "nano":
            for col in "EK":
                (x1, y1), (_, y2) = hole_box(f"{col}1"), hole_box(f"{col}15")
                add("sockets", _box(x1, (y1 + y2) / 2, PCB_TOP, 2.5, abs(y1 - y2) + 2.5, SOCKET_H), dark)
            ax, y_usb_row = nano_axis()
            zb = PCB_TOP + SOCKET_H
            ny0, ny1 = hole_box("E15")[1] - 3.2, y_usb_row + 6.35 - 1.5
            add("nano", _box(ax, (ny0 + ny1) / 2, zb, 18.0, ny1 - ny0, 1.6), (0.1, 0.35, 0.7))
            add("nano", _box(ax, y_usb_row + 6.35 - 4.6, zb + 1.6, 7.7, 9.2, 3.9), metal)
            add("nano", _box(ax, (ny0 + ny1) / 2 - 4, zb + 1.6, 7.0, 7.0, 1.2), dark)
        elif k == "dip4":
            add("sockets", _box(cx, cy, PCB_TOP, abs(max(xs) - min(xs)) + 2.6, abs(max(ys) - min(ys)) + 2.8, 3.0), dark)
            add("ics", _box(cx, cy, PCB_TOP + 3.0, abs(max(xs) - min(xs)) - 1.6, abs(max(ys) - min(ys)) + 2.2, 3.5), (0.2, 0.2, 0.22))
        elif k in ("res", "diode"):
            (x1, y1), (x2, y2) = pins
            vertical = abs(x1 - x2) < 0.1
            ln, d = (6.3, 2.5) if k == "res" else (5.2, 2.7)
            wp = (cq.Workplane("XZ" if vertical else "YZ", origin=(cx, cy, PCB_TOP + d / 2))
                  .circle(d / 2).extrude(ln / 2, both=True))
            add("resistors" if k == "res" else "diode", wp, (0.85, 0.72, 0.52) if k == "res" else dark)
        elif k == "cap":
            add("caps", _box(cx, cy, PCB_TOP + 0.5, 5.0, 2.5, 4.5), (0.88, 0.62, 0.2))
        elif k == "hdr":
            for (x, y) in pins:
                add("headers", _box(x, y, PCB_TOP, 2.5, 2.5, 2.5), dark)
                add("pins", _box(x, y, PCB_TOP + 2.5, 0.64, 0.64, 6.0), gold)
        elif k == "hdr90":
            for (x, y) in pins:
                add("headers", _box(x, y - 1.3, PCB_TOP, 2.5, 2.5, 2.5), dark)
                add("pins", _box(x, y - 1.3 - 4.25, PCB_TOP + 1.27 - 0.32, 0.64, 8.5, 0.64), gold)
    parts.update(bodies)
    return parts


# ---------------- lid / wall parts (for the assembly only) ----------------
def encoder():
    x, y = ENC_POS
    bush_top = H + 2.5
    body = _box(x, y, bush_top - 7.0 - 6.5, 12.4, 13.2, 6.5)
    bush = cq.Workplane("XY").workplane(offset=bush_top - 7.0).center(x, y).circle(3.5).extrude(7.0)
    nut = cq.Workplane("XY").workplane(offset=H).center(x, y).polygon(6, 11).extrude(2.0).cut(
        cq.Workplane("XY").workplane(offset=H).center(x, y).circle(3.5).extrude(2.0))
    return body.union(bush), nut


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
    pcb = _box(x, y, glass_z - 1.2, *DISP_PCB, 1.2)
    glass = _box(x, y, glass_z, DISP_GLASS[0], DISP_GLASS[1], DISP_GLASS[2] - 0.05)
    return pcb, glass


def din_socket():
    x_in = W - T
    flange = cq.Workplane("YZ", origin=(x_in - 1.5, 0, 0)).center(DIN_Y, DIN_Z).rect(DIN_SCREW_SP + 6, 19).extrude(1.5)
    body = cq.Workplane("YZ", origin=(x_in - 1.5, 0, 0)).center(DIN_Y, DIN_Z).circle(8.0).extrude(-16)
    face = cq.Workplane("YZ", origin=(x_in - 0.01, 0, 0)).center(DIN_Y, DIN_Z).circle(7.6).extrude(T + 0.01)
    return flange.union(body).union(face)


def panel_jack(x, z, d_body, depth, d_thread):
    y_in = L - T
    body = cq.Workplane("XZ", origin=(0, y_in, 0)).center(x, z).circle(d_body / 2).extrude(depth)
    thread = cq.Workplane("XZ", origin=(0, L + 1.5, 0)).center(x, z).circle(d_thread / 2 - 0.1).extrude(T + 1.5)
    nut = cq.Workplane("XZ", origin=(0, L + 1.6, 0)).center(x, z).polygon(6, d_thread + 4).extrude(-1.6)
    return body.union(thread), nut


PARTS_ON_LID = ("lid", "encoder", "encoder_nut", "knob", "tap_body", "tap_cap", "oled_pcb", "oled_glass")


def all_parts():
    enc, nut = encoder(); tb, tc = tap_button(); op, og = oled()
    dc, dcn = panel_jack(DC_X, DC_Z, 10.0, 16.0, DC_D)
    trs, trsn = panel_jack(TRS_X, TRS_Z, 8.0, 12.0, TRS_D)
    P = {"tray": (tray(), (0.20, 0.22, 0.25)), "lid": (lid(), (0.20, 0.22, 0.25))}
    P.update(perfboard_parts())
    P.update({"encoder": (enc, (0.75, 0.75, 0.78)), "encoder_nut": (nut, (0.8, 0.8, 0.82)),
              "knob": (knob(), (0.08, 0.08, 0.08)), "tap_body": (tb, (0.75, 0.75, 0.78)),
              "tap_cap": (tc, (0.85, 0.1, 0.1)), "oled_pcb": (op, (0.05, 0.25, 0.6)),
              "oled_glass": (og, (0.02, 0.02, 0.04)), "midi_din": (din_socket(), (0.7, 0.7, 0.72)),
              "dc_jack": (dc, (0.15, 0.15, 0.16)), "dc_nut": (dcn, (0.75, 0.75, 0.78)),
              "trs_jack": (trs, (0.15, 0.15, 0.16)), "trs_nut": (trsn, (0.75, 0.75, 0.78))})
    return P


def build():
    os.makedirs(OUT, exist_ok=True)
    P = all_parts()
    for n in ("tray", "lid"):
        cq.exporters.export(P[n][0], os.path.join(OUT, f"{n}.stl"), tolerance=0.05, angularTolerance=0.1)
        cq.exporters.export(P[n][0], os.path.join(OUT, f"{n}.step"))
    a = cq.Assembly(name="taptempo")
    for n, (wp, col) in P.items():
        a.add(wp, name=n, color=cq.Color(*col, 1))
    a.save(os.path.join(OUT, "assembly.step"))
    a.save(os.path.join(OUT, "assembly.glb"))
    return P


if __name__ == "__main__":
    build()
    print("USB opening centre x=%.1f z=%.1f; board holes %s" % (USB_X, USB_Z, [(round(x, 1), round(y, 1)) for x, y in BOARD_HOLES]))
