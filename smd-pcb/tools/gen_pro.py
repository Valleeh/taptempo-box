"""Write kicad/taptempo-smd.kicad_pro (design rules for JLCPCB 2-layer, net classes)."""
import copy, json, os
import design as D
import gen_sch

REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "nano-perfboard", "kicad", "taptempo.kicad_pro")      # read-only reference
OUT = os.path.join(os.path.dirname(__file__), "..", "kicad", D.PROJECT + ".kicad_pro")

d = json.load(open(REF))
d["meta"]["filename"] = D.PROJECT + ".kicad_pro"
d["sheets"] = [[gen_sch.ROOT, "Root"]]
d["boards"] = []
r = d["board"]["design_settings"]["rules"]
r.update({"min_clearance": 0.15, "min_track_width": 0.15, "min_via_diameter": 0.6, "min_through_hole_diameter": 0.3,
          "min_via_annular_width": 0.13, "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.25,
          "min_hole_to_hole": 0.5, "min_text_height": 0.8, "min_text_thickness": 0.15, "min_silk_clearance": 0.0, "min_resolved_spokes": 1})
ds = d["board"]["design_settings"]
ds["track_widths"] = [0.0, 0.25, 0.4, 0.5]
ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}]
sev = ds.setdefault("rule_severities", {})
sev["silk_over_copper"] = "ignore"        # JLCPCB clips silkscreen on pads anyway
sev["silk_overlap"] = "ignore"
sev["silk_edge_clearance"] = "ignore"
sev["lib_footprint_mismatch"] = "ignore"
sev["lib_footprint_issues"] = "ignore"
base = d["net_settings"]["classes"][0]
base.update({"track_width": 0.25, "clearance": 0.2, "via_diameter": 0.6, "via_drill": 0.3})
pw = copy.deepcopy(base)
pw.update({"name": "Power", "track_width": 0.5, "clearance": 0.2, "priority": 0})
usb = copy.deepcopy(base)
usb.update({"name": "USB", "track_width": 0.2, "clearance": 0.15, "priority": 1})
d["net_settings"]["classes"] = [base, pw, usb]
d["net_settings"]["netclass_patterns"] = ([{"netclass": "Power", "pattern": "/" + n} for n in D.NETCLASS_POWER] +
                                          [{"netclass": "USB", "pattern": "/" + n} for n in ("USB_DP", "USB_DN", "CC1", "CC2")])
json.dump(d, open(OUT, "w"), indent=2)
print("wrote", os.path.abspath(OUT))
