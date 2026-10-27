"""Quick matplotlib renders straight from the CadQuery parts (for checking fit)."""
import os, sys, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import cadquery as cq
import enclosure as E

def tess(wp, tol=0.2):
    shape = wp.val() if isinstance(wp, cq.Workplane) else wp
    if isinstance(wp, cq.Workplane) and len(wp.vals()) > 1:
        shape = cq.Compound.makeCompound([v for v in wp.vals() if isinstance(v, cq.Shape)])
    v, f = shape.tessellate(tol, 0.3)
    v = np.array([(p.x, p.y, p.z) for p in v]); f = np.array(f)
    return v[f]

def load_parts(tol=0.2):
    return [(n, tess(w, tol), np.array(c)) for n, (w, c) in E.all_parts().items()]

def view(parts, fname, elev, azim, hide=(), title="", lims=None):
    fig = plt.figure(figsize=(9, 9)); ax = fig.add_subplot(projection="3d")
    el, az = np.radians(elev), np.radians(azim)
    eye = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    light = eye + np.array([0.3, 0.2, 0.6]); light /= np.linalg.norm(light)
    T, C = [], []
    for name, tri, c in parts:
        if name in hide: continue
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        sh = 0.45 + 0.55 * np.abs(n @ light)
        T.append(tri); C.append(np.clip(c * sh[:, None], 0, 1))
    ax.add_collection3d(Poly3DCollection(np.concatenate(T), facecolors=np.concatenate(C), linewidths=0))
    (x0, x1), (y0, y1), (z0, z1) = lims or ((-5, 65), (-5, 115), (-15, 55))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_zlim(z0, z1)
    ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0)); ax.view_init(elev, azim); ax.set_axis_off()
    ax.set_title(title, fontsize=14); fig.tight_layout(); fig.savefig(fname, dpi=100); plt.close(fig)

if __name__ == "__main__":
    parts = load_parts()
    o = E.OUT
    view(parts, f"{o}/view_top.png", 32, -60, title="komplett, von vorne oben")
    view(parts, f"{o}/view_open.png", 45, -55, hide=E.PARTS_ON_LID, title="ohne Deckel")
    view(parts, f"{o}/view_rear.png", 12, 70, title="Rückseite: 9V, USB, 3.5mm")
    view(parts, f"{o}/view_side.png", 8, 0, hide=(), title="rechte Seite: MIDI")
    view(parts, f"{o}/view_section.png", 0, 0, hide=("tray", "midi_din", "dc_jack", "trs_jack", "dc_nut", "trs_nut"), title="Schnitt: Höhen", lims=((-5, 65), (-5, 115), (-5, 60)))
