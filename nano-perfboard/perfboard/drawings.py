"""SVG build drawings for the perfboard (component side + mirrored solder side)."""
import importlib
import math
import sys
import perfboard as P


def use(module):
    """switch the layout the drawings are made from (perfboard or a variant like perfboard_2trs)"""
    global P
    P = module

S = 9.0                      # px per mm
M = 34                       # margin for grid labels
W, H = P.BOARD_W * S + 2 * M, P.BOARD_H * S + 2 * M + 26

WIRE_HEX = {"rot": "#d62828", "schwarz": "#222", "gelb": "#e8b400", "grün": "#2a9d3a", "blau": "#1f6fd1",
            "orange": "#f07f13", "weiß": "#f4f4f4", "violett": "#8e44ad"}


def xy(h, mirror=False):
    x, y = P.hole_xy(h)
    if mirror:
        x = P.BOARD_W - x
    return M + x * S, M + y * S


def head(title, mirror):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" class="pb" role="img" aria-label="{title}">',
         f'<rect x="{M}" y="{M}" width="{P.BOARD_W*S:.1f}" height="{P.BOARD_H*S:.1f}" rx="6" class="board"/>']
    for mx, my in P.MOUNT_HOLES:
        mx = P.BOARD_W - mx if mirror else mx
        o.append(f'<circle cx="{M+mx*S:.1f}" cy="{M+my*S:.1f}" r="{1.0*S:.1f}" class="mhole"/>')
    for c in range(len(P.COLS)):
        for r in range(1, P.ROWS + 1):
            x, y = xy(P.name(c, r), mirror)
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{0.75*S:.1f}" class="pad"/>'
                     f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{0.38*S:.1f}" class="drill"/>')
    for c, letter in enumerate(P.COLS):
        x, _ = xy(f"{letter}1", mirror)
        o.append(f'<text x="{x:.1f}" y="{M-10}" class="gl">{letter}</text>'
                 f'<text x="{x:.1f}" y="{M+P.BOARD_H*S+20}" class="gl">{letter}</text>')
    for r in range(1, P.ROWS + 1):
        _, y = xy(f"A{r}")
        o.append(f'<text x="{M-14}" y="{y+4:.1f}" class="gl">{r}</text>'
                 f'<text x="{M+P.BOARD_W*S+14}" y="{y+4:.1f}" class="gl">{r}</text>')
    o.append(f'<text x="{W/2:.0f}" y="{M-22}" class="edge">▲ hinten (Rückwand, USB)</text>')
    o.append(f'<text x="{W/2:.0f}" y="{H-6:.0f}" class="edge">▼ vorne (TAP-Seite)</text>')
    return o


def lead(a, b, cls="leg"):
    (x1, y1), (x2, y2) = xy(a), xy(b)
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}"/>'


def body_between(a, b, length_mm, thick_mm, cls, label="", band=None):
    (x1, y1), (x2, y2) = xy(a), xy(b)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    L, T = length_mm * S, thick_mm * S
    o = [lead(a, b), f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({ang:.1f})">',
         f'<rect x="{-L/2:.1f}" y="{-T/2:.1f}" width="{L:.1f}" height="{T:.1f}" rx="{T/2.6:.1f}" class="{cls}"/>']
    if band is not None:      # band towards b (cathode) if band == "b"
        bx = L / 2 - 0.22 * L if band == "b" else -L / 2 + 0.08 * L
        o.append(f'<rect x="{bx:.1f}" y="{-T/2:.1f}" width="{0.14*L:.1f}" height="{T:.1f}" class="band"/>')
    if label:
        flip = 180 if ang > 90 or ang < -90 else 0
        o.append(f'<text y="4" class="blbl{" inv" if cls == "diode" else ""}" text-anchor="middle" '
                 f'transform="rotate({flip})">{label}</text>')
    o.append('</g>')
    return o


def component_side():
    o = head("Bestückungsseite, von oben", False)
    for c in P.COMPONENTS:
        pins = list(c["pins"])
        k = c["kind"]
        if k == "nano":
            (lx, ly), (rx, ry) = xy("E1"), xy("K15")
            o.append(f'<rect x="{lx-12:.1f}" y="{ly-30:.1f}" width="{rx-lx+24:.1f}" height="{ry-ly+42:.1f}" rx="4" class="nano"/>')
            o.append(f'<rect x="{(lx+rx)/2-36:.1f}" y="{ly-42:.1f}" width="72" height="34" rx="3" class="usb"/>'
                     f'<text x="{(lx+rx)/2:.1f}" y="{ly-20:.1f}" class="lbl inv" text-anchor="middle">USB</text>')
            for col in "EK":
                (sx, sy), (_, ey) = xy(f"{col}1"), xy(f"{col}15")
                o.append(f'<rect x="{sx-11:.1f}" y="{sy-11:.1f}" width="22" height="{ey-sy+22:.1f}" rx="2" class="socket"/>')
            for h, (lab, net) in c["pins"].items():
                x, y = xy(h)
                o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" class="spin{" used" if net else ""}"/>')
                left = h[0] == "E"
                o.append(f'<text x="{x+(13 if left else -13):.1f}" y="{y+4:.1f}" class="np{" used" if net else ""}" '
                         f'text-anchor="{"start" if left else "end"}">{lab}</text>')
            o.append(f'<text x="{(lx+rx)/2:.1f}" y="{ry+24:.1f}" class="ref" text-anchor="middle">U1 Arduino Nano</text>')
        elif k == "res":
            o += body_between(pins[0], pins[1], 6.3, 2.5, "res", c["ref"])
        elif k == "diode":
            o += body_between(pins[0], pins[1], 5.2, 2.7, "diode", "D1", band="b")
        elif k == "cap":
            (x1, y1), (x2, y2) = xy(pins[0]), xy(pins[1])
            o.append(lead(pins[0], pins[1]))
            o.append(f'<ellipse cx="{(x1+x2)/2:.1f}" cy="{(y1+y2)/2:.1f}" rx="{2.6*S:.1f}" ry="{1.2*S:.1f}" class="cap"/>'
                     f'<text x="{(x1+x2)/2:.1f}" y="{(y1+y2)/2-14:.1f}" class="lbl" text-anchor="middle">{c["ref"]}</text>')
        elif k == "dip4":
            xs = [xy(h)[0] for h in pins]; ys = [xy(h)[1] for h in pins]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            o.append(f'<rect x="{x0-9:.1f}" y="{y0-12:.1f}" width="{x1-x0+18:.1f}" height="{y1-y0+24:.1f}" rx="2" class="socket"/>'
                     f'<rect x="{x0+6:.1f}" y="{y0-9:.1f}" width="{x1-x0-12:.1f}" height="{y1-y0+18:.1f}" rx="2" class="ic"/>')
            p1 = next(h for h, v in c["pins"].items() if v[0] == "1")
            px, py = xy(p1)
            o.append(f'<circle cx="{px+13:.1f}" cy="{py-3:.1f}" r="3.2" class="dot"/>')
            for h in pins:
                x, y = xy(h)
                o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" class="spin used"/>')
            o.append(f'<text x="{(x0+x1)/2:.1f}" y="{(y0+y1)/2+4:.1f}" class="lbl inv" text-anchor="middle">{c["ref"]}</text>')
        elif k in ("hdr", "hdr90"):
            for h, (lab, net) in c["pins"].items():
                x, y = xy(h)
                o.append(f'<rect x="{x-9:.1f}" y="{y-9:.1f}" width="18" height="18" class="hdr"/>'
                         f'<rect x="{x-3:.1f}" y="{y-3:.1f}" width="6" height="6" class="hpin"/>')
                if k == "hdr90":
                    o.append(f'<rect x="{x-2.5:.1f}" y="{y+9:.1f}" width="5" height="{4.2*S:.1f}" class="hpin"/>')
                    o.append(f'<text x="{x:.1f}" y="{y+9+4.2*S+12:.1f}" class="pl" text-anchor="middle">{lab}</text>')
                else:
                    o.append(f'<text x="{x+(-14 if h[0] in "AB" else 14):.1f}" y="{y+4:.1f}" class="pl" '
                             f'text-anchor="{"end" if h[0] in "AB" else "start"}">{lab}</text>')
            xs = [xy(h)[0] for h in pins]; ys = [xy(h)[1] for h in pins]
            if k == "hdr":
                tx = max(xs) + 30 if pins[0][0] not in "AB" else min(xs) - 40
                o.append(f'<text x="{(min(xs)+max(xs))/2 + (0 if k=="hdr90" else (-42 if pins[0][0]=="R" else 40)):.1f}" '
                         f'y="{min(ys)-14:.1f}" class="ref" text-anchor="middle">{c["ref"]}</text>')
            else:
                o.append(f'<text x="{(min(xs)+max(xs))/2:.1f}" y="{min(ys)-13:.1f}" class="ref" text-anchor="middle">{c["ref"]}</text>')
    o.append("</svg>")
    return "\n".join(o)


def solder_side():
    o = head("Lötseite, von unten gesehen (gespiegelt)", True)
    pins = {h: net for c in P.COMPONENTS for h, (_, net) in c["pins"].items()}
    for net, pts in P.BARE:
        d = " ".join(("M" if i == 0 else "L") + f"{xy(h, True)[0]:.1f},{xy(h, True)[1]:.1f}" for i, h in enumerate(pts))
        o.append(f'<path d="{d}" class="bare{" gnd" if net == "GND" else ""}"/>')
    for h in pins:
        x, y = xy(h, True)
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.2" class="joint"/>')
    for i, (net, a, b, color) in enumerate(P.INSULATED):
        (x1, y1), (x2, y2) = xy(a, True), xy(b, True)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        bend = 18 + 6 * (i % 3)
        cx, cy = mx - dy / L * bend, my + dx / L * bend
        col = WIRE_HEX[color]
        o.append(f'<path d="M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}" class="ins-out"/>'
                 f'<path d="M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}" class="ins" stroke="{col}"/>')
        tx, ty = 0.25 * x1 + 0.5 * cx + 0.25 * x2, 0.25 * y1 + 0.5 * cy + 0.25 * y2
        o.append(f'<g transform="translate({tx:.1f},{ty:.1f})"><circle r="9" class="tag" stroke="{col}"/>'
                 f'<text y="4" class="tagt" text-anchor="middle">{i+1}</text></g>')
    o.append("</svg>")
    return "\n".join(o)


CSS = """
.pb { width: 100%; height: auto; font-family: var(--mono, monospace); }
.pb .board { fill: var(--pb-board); stroke: var(--pb-edge); stroke-width: 2; }
.pb .pad { fill: var(--pb-pad); } .pb .drill { fill: var(--pb-drill); }
.pb .mhole { fill: var(--pb-drill); stroke: var(--pb-edge); stroke-width: 1.5; }
.pb .gl { font-size: 11px; fill: var(--muted); text-anchor: middle; }
.pb .edge { font-size: 12px; fill: var(--muted); text-anchor: middle; font-family: var(--body, sans-serif); }
.pb .leg { stroke: #9aa3ad; stroke-width: 2.4; }
.pb .res { fill: #d9b98a; stroke: #8a6d45; stroke-width: 1; }
.pb .diode { fill: #2a2a2a; stroke: #111; } .pb .band { fill: #d0d0d0; }
.pb .cap { fill: #e0a33a; stroke: #9a6a16; }
.pb .socket { fill: #2b2f36; stroke: #14161a; stroke-width: 1; }
.pb .ic { fill: #3a3f47; } .pb .dot { fill: #f4f4f4; }
.pb .nano { fill: rgba(30,110,200,.16); stroke: #1f6fd1; stroke-width: 1.5; stroke-dasharray: 5 4; }
.pb .usb { fill: #b8bec6; stroke: #7a828c; }
.pb .spin { fill: #555b63; } .pb .spin.used { fill: #e6c34a; }
.pb .np { font-size: 9.5px; fill: var(--muted); } .pb .np.used { fill: var(--ink); font-weight: 600; }
.pb .hdr { fill: #1e2126; } .pb .hpin { fill: #e6c34a; }
.pb .pl { font-size: 10.5px; fill: var(--ink); font-weight: 600; }
.pb .np, .pb .pl, .pb .lbl, .pb .ref, .pb .edge { paint-order: stroke; stroke: var(--pb-board); stroke-width: 3.5px; stroke-linejoin: round; }
.pb .edge { stroke: var(--panel); }
.pb .blbl { font-size: 10px; font-weight: 700; fill: #3b2a12; } .pb .blbl.inv { fill: #fff; }
.pb .lbl { font-size: 11px; fill: var(--ink); font-weight: 600; } .pb .lbl.inv { fill: #fff; }
.pb .ref { font-size: 12px; fill: var(--accent); font-weight: 700; }
.pb .bare { fill: none; stroke: #b9c0c8; stroke-width: 5; stroke-linecap: round; stroke-linejoin: round; }
.pb .bare.gnd { stroke: #8d96a0; }
.pb .joint { fill: #c9ced4; stroke: #6b737c; stroke-width: 1; }
.pb .ins-out { fill: none; stroke: #111; stroke-width: 6.5; stroke-linecap: round; opacity: .55; }
.pb .ins { fill: none; stroke-width: 4; stroke-linecap: round; }
.pb .tag { fill: var(--panel); stroke-width: 2.5; } .pb .tagt { font-size: 11px; font-weight: 700; fill: var(--ink); }
"""

STANDALONE_VARS = """:root, svg { --muted:#5d6874; --ink:#1d232b; --accent:#c8282d; --panel:#ffffff;
  --pb-board:#c9a46a; --pb-edge:#8a6a3a; --pb-pad:#e4e4e4; --pb-drill:#5a4a30;
  --mono: "DejaVu Sans Mono", Menlo, Consolas, monospace; --body: "DejaVu Sans", Arial, sans-serif; }"""


def standalone(svg, title):
    """same drawing, but self-contained: white background, own colours and a title line"""
    svg = svg.replace('class="pb"', 'class="pb" style="background:#ffffff"', 1)
    head_end = svg.index(">") + 1
    return (svg[:head_end] + f"<style>{STANDALONE_VARS}{CSS}</style>"
            + f'<rect width="100%" height="100%" fill="#ffffff"/>' + svg[head_end:])


def suffix():
    return "_" + P.NAME if hasattr(P, "NAME") else ""


if __name__ == "__main__":
    # python3 drawings.py            -> component_side.svg / solder_side.svg
    # python3 drawings.py 2trs       -> component_side_2trs.svg / solder_side_2trs.svg
    if len(sys.argv) > 1:
        use(importlib.import_module("perfboard_" + sys.argv[1]))
    assert not P.check(), P.check()
    for side, fn, title in (("component_side", component_side, "Bestückungsseite"), ("solder_side", solder_side, "Lötseite")):
        open(f"{side}{suffix()}.svg", "w").write(standalone(fn(), title))
    print("ok")
