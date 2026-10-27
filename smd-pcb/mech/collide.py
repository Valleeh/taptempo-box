"""Collision check for the SMD board in the enclosure (run with the CadQuery venv).
Reports volume overlaps > 0.05 mm^3 between the PCB assembly (KiCad STEP + proxies + Dupont plugs)
and the enclosure/lid parts, and checks that mating plugs pass the rear-wall holes."""
import itertools
import cadquery as cq
import enclosure as E


def shape(w):
    vs = [v for v in w.vals() if isinstance(v, cq.Shape)]
    return vs[0] if len(vs) == 1 else cq.Compound.makeCompound(vs)


P = E.all_parts()
S = {k: shape(w) for k, (w, _) in P.items()}
board_side = ["pcb", "usb_c", "dc_jack", "dupont"]
enclosure_side = [k for k in S if k not in board_side]
ok_pairs = {frozenset(p) for p in [("encoder", "lid"), ("tap_body", "lid"), ("lid", "oled_pcb"),
                                   ("encoder", "encoder_nut"), ("midi_din", "tray"), ("lid", "oled_glass"),
                                   ("pcb", "usb_c"), ("pcb", "dc_jack"), ("pcb", "dupont")]}
bad = []
for a, b in itertools.product(board_side, enclosure_side):
    if frozenset((a, b)) in ok_pairs:
        continue
    try:
        v = S[a].intersect(S[b]).Volume()
    except Exception:
        v = -1
    if v > 0.05 or v < 0:
        bad.append((a, b, round(v, 2)))
print("PCB vs. Gehaeuse/Deckelteile:", bad or "keine Kollisionen")

tray = S["tray"]
names = ("USB-C-Stecker (Umspritzung 11.5 x 6)", "9V-Stecker (Umspritzung D9.5)", "Klinkenstecker (D6)")
for n, probe in zip(names, E.plug_probes()):
    v = shape(probe).intersect(tray).Volume()
    print(f"{n}: Ueberlappung mit Rueckwand {v:.2f} mm^3 ->", "passt" if v < 0.05 else "KOLLISION")

# clearances (z) of tall board parts below the lid parts
bb = S["dupont"].BoundingBox()
print(f"Dupont-Stecker Oberkante z={bb.zmax:.1f} (Deckel-Unterseite z={E.TRAY_H})")
bb = S["pcb"].BoundingBox()
print(f"PCB-Modell: x {bb.xmin:.1f}..{bb.xmax:.1f}, y {bb.ymin:.1f}..{bb.ymax:.1f}, z {bb.zmin:.1f}..{bb.zmax:.1f}")
