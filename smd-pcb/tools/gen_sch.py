"""Generate kicad/taptempo-smd.kicad_sch from design.py.

Every pin gets a local net label right at its connection point (no wires), unused pins get a
no-connect flag. Library symbols are copied from the KiCad 10 system libraries (derived symbols flattened).
UUIDs are deterministic (uuid5) so the PCB keeps its links when the schematic is regenerated.
"""
import os
import uuid
import copy
import sexp
from sexp import Sym, find, find1
import design as D

SYMDIR = "/usr/share/kicad/symbols"
OUT = os.path.join(os.path.dirname(__file__), "..", "kicad", D.PROJECT + ".kicad_sch")
NS = uuid.UUID("6b7d1f9e-3c2a-4e7b-9a51-7a0c2d4e8f10")
ROOT = str(uuid.uuid5(NS, "root"))


def uid(*k):
    return str(uuid.uuid5(NS, "/".join(map(str, k))))


_libcache = {}


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _libcache:
        _libcache[lib] = sexp.parse(open(os.path.join(SYMDIR, lib + ".kicad_sym")).read())
    t = _libcache[lib]
    syms = {e[1]: e for e in t if isinstance(e, list) and e[0] == "symbol"}
    s = copy.deepcopy(syms[name])
    ext = find1(s, "extends")
    if ext:
        parent = copy.deepcopy(syms[ext[1]])
        pname = parent[1]
        props = {p[1]: p for p in find(s, "property")}
        out = [Sym("symbol"), name]
        for e in parent[2:]:
            if isinstance(e, list) and e[0] == "property" and e[1] in props:
                out.append(props.pop(e[1]))
            elif isinstance(e, list) and e[0] == "symbol":
                e[1] = e[1].replace(pname + "_", name + "_", 1)
                out.append(e)
            else:
                out.append(e)
        # child-only properties go before the first sub-symbol
        idx = next(i for i, e in enumerate(out) if isinstance(e, list) and e[0] == "symbol")
        for p in props.values():
            out.insert(idx, p)
        s = out
    s = [Sym("symbol"), lib_id] + s[2:]
    return s


def pins_of(sym):
    """[(number, x, y, angle, etype)] in symbol coordinates (y up)"""
    res = []

    def walk(x):
        for e in x:
            if isinstance(e, list):
                if e[0] == "pin":
                    at = find1(e, "at")
                    res.append((find1(e, "number")[1], float(at[1]), float(at[2]), float(at[3]), str(e[1])))
                else:
                    walk(e)
    walk(sym)
    return res


def eff(justify=None, hide=False, size=1.27):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), size, size]]]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify.split()])
    return e


def prop(name, value, x, y, ang=0, hide=False, justify=None):
    p = [Sym("property"), name, value, [Sym("at"), x, y, ang]]
    if hide:
        p.append([Sym("hide"), Sym("yes")])
    p.append(eff(justify))
    return p


def label(net, x, y, ang, key):
    just = "left bottom" if ang in (0, 90) else "right bottom"
    return [Sym("label"), net, [Sym("at"), x, y, ang], eff(just), [Sym("uuid"), uid("lbl", key)]]


def instance(ref, lib_id, value, fp, lcsc, x, y, libsym, in_bom=True):
    u = uid("sym", ref)
    props = {p[1]: p for p in find(libsym, "property")}

    def ppos(name, dflt):
        p = props.get(name)
        if p:
            at = find1(p, "at")
            return x + float(at[1]), y - float(at[2]), float(at[3])
        return x, y + dflt, 0
    rx, ry, ra = ppos("Reference", -5)
    vx, vy, va = ppos("Value", 5)
    hidden_ref = ref.startswith("#")
    s = [Sym("symbol"), [Sym("lib_id"), lib_id], [Sym("at"), x, y, 0], [Sym("unit"), 1],
         [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes" if in_bom else "no")],
         [Sym("on_board"), Sym("no" if ref.startswith("#") else "yes")], [Sym("dnp"), Sym("no")],
         [Sym("uuid"), u],
         prop("Reference", ref, rx, ry, ra, hide=hidden_ref),
         prop("Value", value, vx, vy, va),
         prop("Footprint", fp, x, y, 0, hide=True),
         prop("Datasheet", props["Datasheet"][2] if "Datasheet" in props else "", x, y, 0, hide=True),
         prop("Description", props["Description"][2] if "Description" in props else "", x, y, 0, hide=True)]
    if lcsc:
        s.append(prop("LCSC", lcsc, x, y, 0, hide=True))
    for num, *_ in pins_of(libsym):
        s.append([Sym("pin"), num, [Sym("uuid"), uid("pin", ref, num)]])
    s.append([Sym("instances"), [Sym("project"), D.PROJECT,
                                 [Sym("path"), "/" + ROOT, [Sym("reference"), ref], [Sym("unit"), 1]]]])
    return s


def build():
    libs = {}
    body = []
    items = list(D.P.values())
    flags = [dict(ref=r, lib="power:PWR_FLAG", value="PWR_FLAG", fp="", lcsc="", pins={"1": n},
                  sch=(30.48 + 15.24 * i, 271.78), bom=False) for i, (r, n) in enumerate(D.PWR_FLAGS.items())]
    for p in items + flags:
        if p["lib"] not in libs:
            libs[p["lib"]] = lib_symbol(p["lib"])
        ls = libs[p["lib"]]
        x, y = p["sch"]
        body.append(instance(p["ref"], p["lib"], p["value"], p["fp"], p["lcsc"], x, y, ls, p.get("bom", True)))
        done = set()
        for num, px, py, pa, et in pins_of(ls):
            cx, cy = round(x + px, 3), round(y - py, 3)
            if (cx, cy) in done:
                continue
            done.add((cx, cy))
            if num not in p["pins"]:
                raise SystemExit(f"{p['ref']} pin {num} not assigned")
            net = p["pins"][num]
            if net is None:
                if et != "no_connect":
                    body.append([Sym("no_connect"), [Sym("at"), cx, cy], [Sym("uuid"), uid("nc", p["ref"], num)]])
            else:
                body.append(label(net, cx, cy, int((pa + 180) % 360), (p["ref"], num)))
    # a few headings
    texts = [("USB-C + CH340C (USB-Seriell)", 30, 30), ("Versorgung 9 V (Minus innen) / USB", 30, 140),
             ("ATmega328P-AU (Nano-kompatibel)", 100, 115), ("Schaltausgänge Optokoppler -> 3,5-mm-Klinke", 260, 30),
             ("MIDI OUT (DIN extern)", 260, 108), ("Stecker zu Deckel/Display/Drehgeber", 300, 145),
             ("ISP: Bootloader brennen", 225, 212), ("Befestigungslöcher", 350, 245)]
    for i, (t, x, y) in enumerate(texts):
        body.append([Sym("text"), t, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), x, y, 0],
                     eff("left bottom", size=2.0), [Sym("uuid"), uid("txt", i)]])
    sch = [Sym("kicad_sch"), [Sym("version"), 20260101], [Sym("generator"), "eeschema"],
           [Sym("generator_version"), "10.0"], [Sym("uuid"), ROOT], [Sym("paper"), "A3"],
           [Sym("title_block"), [Sym("title"), "Tap-Tempo / MIDI-Clock Box - SMD (JLCPCB)"],
            [Sym("date"), "2026-10-25"], [Sym("rev"), "1.0"],
            [Sym("comment"), 1, "Pinbelegung identisch zur Arduino-Nano-Version (Firmware unveraendert)"]],
           [Sym("lib_symbols")] + list(libs.values())] + body + [
        [Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]],
        [Sym("embedded_fonts"), Sym("no")]]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(sexp.dump(sch) + "\n")
    print("wrote", os.path.abspath(OUT), len(items), "parts")


if __name__ == "__main__":
    build()
