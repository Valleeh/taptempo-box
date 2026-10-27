"""Generate the unrouted board kicad/taptempo-smd.kicad_pcb from design.py (pcbnew API, fresh process).

Footprints come from the KiCad 10 system libraries, pads get the nets from design.py,
each footprint is linked to its schematic symbol (same deterministic UUIDs as gen_sch.py).
"""
import os
import pcbnew
import design as D
import gen_sch

FPDIR = "/usr/share/kicad/footprints"
OUT = os.path.join(os.path.dirname(__file__), "..", "kicad", D.PROJECT + ".kicad_pcb")
MM = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def seg(board, a, b, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(*a)); s.SetEnd(V(*b))
    s.SetLayer(layer); s.SetWidth(MM(w))
    board.Add(s)


def arc(board, c, start, ang, layer=pcbnew.Edge_Cuts, w=0.1):
    """arc around centre c from start, sweeping ang degrees (positive = clockwise on screen)"""
    import math
    r = math.hypot(start[0] - c[0], start[1] - c[1])
    a0 = math.atan2(start[1] - c[1], start[0] - c[0])
    pt = lambda a: (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetArcGeometry(V(*start), V(*pt(a0 + math.radians(ang / 2))), V(*pt(a0 + math.radians(ang))))
    s.SetLayer(layer); s.SetWidth(MM(w))
    board.Add(s)


def rect(board, x0, y0, x1, y1, layer=pcbnew.Dwgs_User, w=0.15):
    """rectangle in box coordinates"""
    a, b = D.kxy(x0, y0), D.kxy(x1, y1)
    for p, q in [((a[0], a[1]), (b[0], a[1])), ((b[0], a[1]), (b[0], b[1])), ((b[0], b[1]), (a[0], b[1])), ((a[0], b[1]), (a[0], a[1]))]:
        seg(board, p, q, layer, w)


def outline(board):
    x0, y1 = D.kxy(D.BOARD_X0, D.BOARD_Y0)     # front-left -> KiCad bottom-left
    x1, y0 = D.kxy(D.BOARD_X1, D.BOARD_Y1)
    r = D.BOARD_R
    nx0, nx1, nd = D.NOTCH
    a, _ = D.kxy(nx0, 0); b, _ = D.kxy(nx1, 0)
    seg(board, (x0 + r, y0), (a, y0)); seg(board, (a, y0), (a, y0 + nd)); seg(board, (a, y0 + nd), (b, y0 + nd))
    seg(board, (b, y0 + nd), (b, y0)); seg(board, (b, y0), (x1 - r, y0))
    seg(board, (x1, y0 + r), (x1, y1 - r))
    seg(board, (x1 - r, y1), (x0 + r, y1)); seg(board, (x0, y1 - r), (x0, y0 + r))
    arc(board, (x1 - r, y0 + r), (x1 - r, y0), 90)
    arc(board, (x1 - r, y1 - r), (x1, y1 - r), 90)
    arc(board, (x0 + r, y1 - r), (x0 + r, y1), 90)
    arc(board, (x0 + r, y0 + r), (x0, y0 + r), 90)


def text(board, s, x, y, size=1.0, layer=pcbnew.F_SilkS, rot=0, bold=False, just="center"):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(V(*D.kxy(x, y)))
    t.SetLayer(layer)
    t.SetTextSize(V(size, size))
    t.SetTextThickness(MM(max(0.15, size * 0.15)))
    t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    t.SetBold(bold)
    t.SetHorizJustify({"left": pcbnew.GR_TEXT_H_ALIGN_LEFT, "right": pcbnew.GR_TEXT_H_ALIGN_RIGHT,
                       "center": pcbnew.GR_TEXT_H_ALIGN_CENTER}[just])
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)


def schematic_unconnected():
    """names KiCad gives to single-pin 'unconnected-(...)' nets, read from the exported netlist"""
    import subprocess, tempfile, xml.etree.ElementTree as ET
    sch = os.path.abspath(os.path.join(os.path.dirname(OUT), D.PROJECT + ".kicad_sch"))
    with tempfile.TemporaryDirectory() as td:
        x = os.path.join(td, "n.xml")
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", x, sch],
                       check=True, capture_output=True)
        r = ET.parse(x).getroot()
    res = {}
    for n in r.iter("net"):
        if n.get("name").startswith("unconnected-"):
            for nd in n.iter("node"):
                res[(nd.get("ref"), nd.get("pin"))] = n.get("name")
    return res


def keepouts(board):
    """enclosure parts above the board, drawn on Dwgs.User for orientation (box coordinates)"""
    rect(board, 23.8, 45.4, 36.2, 58.6)          # encoder body (lid), legs end at z ~21
    rect(board, 16.35, 78.1, 43.65, 105.9)       # OLED module (lid), underside z ~29
    rect(board, 40.0, 54.0, 56.0, 82.0)          # MIDI DIN socket body (right wall) z 13.5..32.5
    T = text
    T(board, "Drehgeber (Deckel)", 30, 52, 0.8, layer=pcbnew.Dwgs_User)
    T(board, "OLED (Deckel)", 30, 104, 0.8, layer=pcbnew.Dwgs_User)
    T(board, "DIN-Buchse (Wand) - nur flache Teile", 48, 68, 0.8, layer=pcbnew.Dwgs_User, rot=90)


def build():
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(1.6))
    nets = {}
    for n in sorted(D.nets()):
        ni = pcbnew.NETINFO_ITEM(board, "/" + n)
        board.Add(ni)
        nets[n] = ni
    unconn = schematic_unconnected()
    for (r, pin), n in unconn.items():
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        nets[n] = ni
    outline(board)
    keepouts(board)
    for ref, p in D.P.items():
        lib, name = p["fp"].split(":")
        fp = pcbnew.FootprintLoad(os.path.join(FPDIR, lib + ".pretty"), name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(p["value"])
        desc = gen_sch.lib_symbol(p["lib"])
        dp = [e for e in desc if isinstance(e, list) and e[0] == "property" and e[1] == "Description"]
        fp.GetField(pcbnew.FIELD_T_DESCRIPTION).SetText(dp[0][2] if dp else "")
        dsp = [e for e in desc if isinstance(e, list) and e[0] == "property" and e[1] == "Datasheet"]
        fp.GetField(pcbnew.FIELD_T_DATASHEET).SetText(dsp[0][2] if dsp else "")
        if p["lcsc"]:
            f = pcbnew.PCB_FIELD(fp, fp.GetNextFieldOrdinal(), "LCSC")
            f.SetText(p["lcsc"]); f.SetVisible(False); f.SetLayer(pcbnew.F_Fab)
            fp.Add(f)
        fp.SetPath(pcbnew.KIID_PATH("/" + gen_sch.uid("sym", ref)))
        fp.SetSheetname("/")
        fp.SetSheetfile(D.PROJECT + ".kicad_sch")
        x, y, rot = p["pcb"]
        for item in list(fp.GraphicalItems()):
            if item.GetLayer() == pcbnew.Edge_Cuts:      # J3 carries a board-edge marker
                fp.Remove(item)
        fp.SetExcludedFromBOM(not p["bom"])
        fp.SetExcludedFromPosFiles(not p["bom"])
        board.Add(fp)
        fp.SetPosition(V(*D.kxy(x, y)))
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            num = pad.GetNumber()
            net = p["pins"].get(num) or unconn.get((ref, num))
            if net:
                pad.SetNet(nets[net])
        # small reference text, keep it readable
        rf = fp.Reference()
        rf.SetTextSize(V(0.8, 0.8)); rf.SetTextThickness(MM(0.15))
        if ref[0] in "JH":
            rf.SetVisible(False)          # connectors/holes get descriptive silkscreen instead
    # silkscreen labels (box coordinates)
    T = text
    T(board, "TAP-TEMPO SMD v1.0", 22.5, 39.6, 1.2, bold=True)
    T(board, "TAP-TEMPO SMD v1.0", 22.5, 39.6, 1.2, bold=True)
    labels = {"J4": ("OLED", ["5V", "SDA", "SCL", "GND"]), "J6": ("TAP", ["TAP", "GND"]),
              "J5": ("DREHGEBER", ["A", "GND", "B", "SW", "GND"])}
    for ref, (title, names) in labels.items():
        x, y, _ = D.P[ref]["pcb"]
        T(board, title, x + 1.0, y + 1.95, 0.9, bold=True, just="left")
        for i, n in enumerate(names):
            T(board, n, x + 2.0, y - 2.54 * i, 0.9, just="left")
    x, y, _ = D.P["J7"]["pcb"]
    T(board, "MIDI-DIN:", x - 2.0, y - 2.4, 0.9, just="right")
    for i, n in enumerate(["4", "2", "5"]):
        T(board, n, x + 2.54 * i, y - 2.4, 0.9)
    x, y, _ = D.P["J8"]["pcb"]
    T(board, "ISP", x - 2.5, y + 2.4, 0.9, bold=True)
    T(board, "1", x + 2.0, y, 0.9)
    T(board, "9V  (-)-(o-(+)", 17.7, 97.5, 0.9, rot=90, bold=True)
    T(board, "USB-C", 28.0, 95.9, 0.8)
    T(board, "TIP=D10  RING=D9", 46.0, 92.4, 0.8)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    board.Save(OUT)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    build()
