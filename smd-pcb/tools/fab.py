"""Create JLCPCB fabrication files in ../fab:
  taptempo-smd_gerber.zip   Gerber + Excellon drill files
  bom_jlcpcb.csv            Comment, Designator, Footprint, LCSC Part #   (SMD parts assembled by JLCPCB)
  cpl_jlcpcb.csv            Designator, Mid X, Mid Y, Layer, Rotation     (with JLCPCB rotation offsets)
  tht_selbst_loeten.csv     through-hole parts the user solders (LCSC numbers for ordering)
"""
import csv
import glob
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
K = os.path.abspath(os.path.join(HERE, "..", "kicad"))
FAB = os.path.abspath(os.path.join(HERE, "..", "fab"))
PCB = os.path.join(K, D.PROJECT + ".kicad_pcb")

# JLCPCB rotation/centre corrections per part, computed by jlc_rotation.py from the EasyEDA footprints
# of the actual LCSC parts (JLCPCB's 0 deg reference). Still check pin 1 in the JLCPCB placement preview.
import json, math
JLC = json.load(open(os.path.join(HERE, "jlc_rotation.json")))


def run(*a):
    subprocess.run(a, check=True, capture_output=True)


def gerbers():
    td = tempfile.mkdtemp()
    run("kicad-cli", "pcb", "export", "gerbers", "-o", td + "/",
        "-l", "F.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts",
        "--subtract-soldermask", "--use-drill-file-origin", PCB)
    run("kicad-cli", "pcb", "export", "drill", "-o", td + "/", "--format", "excellon", "--excellon-units", "mm",
        "--excellon-separate-th", "--drill-origin", "absolute", "--generate-map", "--map-format", "gerberx2", PCB)
    z = os.path.join(FAB, D.PROJECT + "_gerber.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for p in sorted(glob.glob(td + "/*")):
            f.write(p, os.path.basename(p))
    names = sorted(os.path.basename(p) for p in glob.glob(td + "/*"))
    shutil.rmtree(td)
    return z, names


def fp_name(p):
    return p["fp"].split(":")[1]


def bom():
    groups = {}
    for r, p in D.P.items():
        if not p["bom"] or p["tht"]:
            continue
        key = (p["value"].split(" (")[0], fp_name(p), p["lcsc"])
        groups.setdefault(key, []).append(r)
    rows = []
    for (val, fp, lcsc), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
        refs.sort(key=lambda s: (re.sub(r"\d", "", s), int(re.sub(r"\D", "", s))))
        rows.append([val, ",".join(refs), fp, lcsc])
    with open(os.path.join(FAB, "bom_jlcpcb.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        w.writerows(rows)
    tht = {}
    for r, p in D.P.items():
        if p["tht"]:
            tht.setdefault((p["value"], fp_name(p), p["lcsc"]), []).append(r)
    with open(os.path.join(FAB, "tht_selbst_loeten.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Bauteil", "Designator", "Footprint", "LCSC Part #", "Menge pro Platine"])
        for (val, fp, lcsc), refs in tht.items():
            w.writerow([val, ",".join(refs), fp, lcsc, len(refs)])
    return rows


def cpl():
    td = tempfile.mkdtemp()
    out = os.path.join(td, "pos.csv")
    run("kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "front",
        "--use-drill-file-origin", "-o", out, PCB)
    rows = list(csv.DictReader(open(out)))
    shutil.rmtree(td)
    res = []
    for r in rows:
        ref = r["Ref"]
        p = D.P.get(ref)
        if not p or p["tht"] or not p["bom"]:
            continue
        rot = float(r["Rot"])
        j = JLC[ref]
        ox, oy = j["centre_offset_mm"]                 # footprint coords (KiCad, y down)
        a = math.radians(rot)
        dx = ox * math.cos(a) + oy * math.sin(a)
        dy = -ox * math.sin(a) + oy * math.cos(a)
        x, y = float(r["PosX"]) + dx, float(r["PosY"]) - dy  # pos file has y up
        res.append([ref, "%.3fmm" % x, "%.3fmm" % y, "Top", "%g" % ((rot + j["phi"]) % 360)])
    res.sort(key=lambda x: (re.sub(r"\d", "", x[0]), int(re.sub(r"\D", "", x[0]))))
    with open(os.path.join(FAB, "cpl_jlcpcb.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(res)
    return res


if __name__ == "__main__":
    os.makedirs(FAB, exist_ok=True)
    z, names = gerbers()
    print("gerber zip:", z, names)
    b = bom()
    c = cpl()
    smd_refs = sum(len(r[1].split(",")) for r in b)
    print(f"BOM lines {len(b)}, SMD parts {smd_refs}, CPL rows {len(c)}")
    assert smd_refs == len(c), "BOM/CPL mismatch"
