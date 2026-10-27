"""Determine JLCPCB rotation offsets by comparing each KiCad footprint with the EasyEDA/JLCPCB
footprint of the LCSC part (which defines JLCPCB's 0 deg).

For each assembled part: fetch the EasyEDA footprint, centre both pad sets on their centroids and find the
rotation phi (0/90/180/270, counter-clockwise as seen from the top) with  KiCad_pads = R(phi) * EasyEDA_pads.
JLCPCB rotation = KiCad rotation + phi.   Writes jlc_rotation.json (used by fab.py).
"""
import json
import math
import os
import subprocess
import pcbnew
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "jlc_rotation.json")
FPDIR = "/usr/share/kicad/footprints"


CACHE = os.path.join(HERE, "easyeda_cache")


def fetch(lcsc):
    import time
    os.makedirs(CACHE, exist_ok=True)
    fn = os.path.join(CACHE, lcsc + ".json")
    if os.path.exists(fn):
        return json.load(open(fn))
    for attempt in range(6):
        r = subprocess.run(["curl", "-s", "-m", "30", "-A", "curl/8.0", "--compressed",
                            f"https://easyeda.com/api/products/{lcsc}/components?version=6.4.19.5"],
                           capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
            json.dump(d, open(fn, "w"))
            return d
        except ValueError:
            time.sleep(5 * (attempt + 1))
    raise SystemExit("EasyEDA API not reachable for " + lcsc)


def easyeda_pads(lcsc):
    d = fetch(lcsc)["result"]["packageDetail"]
    ds = d["dataStr"]
    ox, oy = float(ds["head"]["x"]), float(ds["head"]["y"])
    pads = {}
    for s in ds["shape"]:
        if s.startswith("PAD~"):
            f = s.split("~")
            # PAD~shape~x~y~w~h~layer~net~number~...   units: 10 mil, y down
            x, y, num = (float(f[2]) - ox) * 0.254, (float(f[3]) - oy) * 0.254, f[8]
            pads.setdefault(num, []).append((x, y))
    return d.get("title", ""), pads


def kicad_pads(fp):
    lib, name = fp.split(":")
    f = pcbnew.FootprintLoad(os.path.join(FPDIR, lib + ".pretty"), name)
    pads = {}
    for p in f.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or not p.GetNumber():
            continue
        v = p.GetPosition()
        pads.setdefault(p.GetNumber(), []).append((pcbnew.ToMM(v.x), pcbnew.ToMM(v.y)))
    return pads


def centre(pads):
    pts = [p for v in pads.values() for p in v]
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    return {k: [(x - cx, y - cy) for x, y in v] for k, v in pads.items()}, (cx, cy)


def rot(p, phi):
    # counter-clockwise on screen with y pointing down
    a = math.radians(phi)
    x, y = p
    return (x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))


def best_phi(kp, ep):
    common = [k for k in kp if k in ep]
    res = []
    for phi in (0, 90, 180, 270):
        err = 0.0
        for k in common:
            for a in kp[k]:
                err += min(math.dist(a, rot(b, phi)) for b in ep[k])
        res.append((err / max(1, len(common)), phi))
    res.sort()
    return res, common


if __name__ == "__main__":
    out = {}
    seen = {}
    for ref, p in D.P.items():
        if p["tht"] or not p["bom"] or not p["lcsc"]:
            continue
        key = (p["fp"], p["lcsc"])
        if key not in seen:
            title, ep = easyeda_pads(p["lcsc"])
            kraw = kicad_pads(p["fp"])
            common = [k for k in kraw if k in ep and len(kraw[k]) == len(ep[k])]
            kp, kc = centre({k: kraw[k] for k in common})
            ep2, ec = centre({k: ep[k] for k in common})
            res, common = best_phi(kp, ep2)
            phi = res[0][1]
            # EasyEDA origin (= JLCPCB part centre) expressed in KiCad footprint coordinates
            eo = rot((-ec[0], -ec[1]), phi)
            off = (round(kc[0] + eo[0], 3), round(kc[1] + eo[1], 3))
            seen[key] = (phi, res[0][0], res[1][0], title, off, len(common), len(kraw))
        phi, e0, e1, title, off, nc, nk = seen[key]
        out[ref] = {"phi": phi, "err": round(e0, 3), "next_err": round(e1, 3), "easyeda": title,
                    "centre_offset_mm": off, "matched_pads": f"{nc}/{nk}"}
        print(f"{ref:4} {p['fp'].split(':')[1]:38} {p['lcsc']:9} phi={phi:3} err={e0:.3f} (next {e1:.3f}) pads {nc}/{nk} off={off} {title}")
    json.dump(out, open(OUT, "w"), indent=1)
