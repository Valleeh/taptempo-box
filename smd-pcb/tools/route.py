"""Autoroute the board with Freerouting, then add GND pours on both layers and fill them.

Each pcbnew step runs in its own fresh Python process (pcbnew gets flaky after edits in a long-lived process).
Usage: python3 route.py [passes]
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
K = os.path.abspath(os.path.join(HERE, "..", "kicad"))
PCB = os.path.join(K, "taptempo-smd.kicad_pcb")
DSN = os.path.join(K, "taptempo-smd.dsn")
SES = os.path.join(K, "taptempo-smd.ses")
FR = os.path.expanduser("~/.kicad-mcp/freerouting.jar")


def py(code):
    subprocess.run([sys.executable, "-c", code], check=True, cwd=HERE)


STRIP = f"""
import pcbnew
b = pcbnew.LoadBoard({PCB!r})
for t in list(b.GetTracks()):
    b.Remove(t)
for z in list(b.Zones()):
    b.Remove(z)
b.Save({PCB!r})
"""

EXPORT = f"""
import pcbnew
b = pcbnew.LoadBoard({PCB!r})
assert pcbnew.ExportSpecctraDSN(b, {DSN!r})
"""

IMPORT = f"""
import pcbnew
b = pcbnew.LoadBoard({PCB!r})
assert pcbnew.ImportSpecctraSES(b, {SES!r})
b.Save({PCB!r})
"""

POUR = f"""
import pcbnew, design as D
b = pcbnew.LoadBoard({PCB!r})
MM = pcbnew.FromMM
gnd = b.FindNet("/GND")
x0, y1 = D.kxy(D.BOARD_X0, D.BOARD_Y0); x1, y0 = D.kxy(D.BOARD_X1, D.BOARD_Y1)
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(gnd)
    z.SetLocalClearance(MM(0.3))
    z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName("GND_" + ("F" if layer == pcbnew.F_Cu else "B"))
    ol = z.Outline()
    ol.NewOutline()
    a, _ = D.kxy(D.NOTCH[0], 0); c, _ = D.kxy(D.NOTCH[1], 0); nd = D.NOTCH[2]
    for x, y in [(x0, y0), (a, y0), (a, y0 + nd), (c, y0 + nd), (c, y0), (x1, y0), (x1, y1), (x0, y1)]:
        ol.Append(MM(x), MM(y))
    b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
# GND stitching vias wherever both pours have solid copper around the point
zs = list(b.Zones())
n = 0
import math
gx = D.BOARD_X0 + 2.0
while gx < D.BOARD_X1 - 1.5:
    gy = D.BOARD_Y0 + 2.0
    while gy < D.BOARD_Y1 - 1.5:
        X, Y = D.kxy(gx, gy)
        ok = True
        for z in zs:
            for dx, dy in [(0, 0), (0.75, 0), (-0.75, 0), (0, 0.75), (0, -0.75), (0.53, 0.53), (-0.53, -0.53), (0.53, -0.53), (-0.53, 0.53)]:
                if not z.HitTestFilledArea(z.GetLayer(), pcbnew.VECTOR2I(MM(X + dx), MM(Y + dy)), 0):
                    ok = False; break
            if not ok: break
        if ok:
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(MM(X), MM(Y)))
            v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3))
            v.SetNet(gnd)
            b.Add(v); n += 1
        gy += 4.0
    gx += 4.0
print("stitching vias:", n)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save({PCB!r})
"""

FILL = f"""
import pcbnew
b = pcbnew.LoadBoard({PCB!r})
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save({PCB!r})
"""

if __name__ == "__main__":
    if sys.argv[1:2] == ["fill"]:
        py(FILL); sys.exit()
    passes = sys.argv[1] if len(sys.argv) > 1 else "100"
    py(STRIP)
    py(EXPORT)
    if os.path.exists(SES):
        os.remove(SES)
    subprocess.run(["java", "-jar", FR, "-de", DSN, "-do", SES, "-mp", passes, "-mt", "4"],
                   check=True, cwd=K, timeout=1800)
    py(IMPORT)
    py(POUR)
    print("routed + poured:", PCB)
