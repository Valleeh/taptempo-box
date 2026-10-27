"""Report volume overlaps between enclosure parts and components."""
import itertools, cadquery as cq
import enclosure as E
P = E.all_parts()
sh = lambda w: (lambda vs: vs[0] if len(vs) == 1 else cq.Compound.makeCompound(vs))([v for v in w.vals() if isinstance(v, cq.Shape)])
S = {k: sh(w) for k, (w, _) in P.items()}
ok_pairs = {frozenset(p) for p in [("perfboard", "sockets"), ("perfboard", "headers"), ("sockets", "ics"), ("sockets", "nano"),
            ("headers", "pins"), ("perfboard", "resistors"), ("perfboard", "diode"), ("perfboard", "caps"), ("perfboard", "pins"),
            ("encoder", "lid"), ("tap_body", "lid"), ("lid", "oled_pcb"), ("dc_jack", "tray"), ("trs_jack", "tray"),
            ("dc_nut", "dc_jack"), ("trs_nut", "trs_jack"), ("midi_din", "tray"), ("encoder", "encoder_nut"), ("perfboard", "tray")]}
bad = []
for a, b in itertools.combinations(S, 2):
    if frozenset((a, b)) in ok_pairs: continue
    try: v = S[a].intersect(S[b]).Volume()
    except Exception as e: v = -1
    if v > 0.3 or v < 0: bad.append((a, b, round(v, 1)))
print(bad or "keine Kollisionen")
