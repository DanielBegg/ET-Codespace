"""ETB2 CAD tutorial - reference rotor built with CadQuery.

Turns the simple blade spec (linear chord taper, linear twist, NACA 0012
section) into three blades on a hub and exports an STL (+ STEP).  This is the
reference solution for the programming-only route and the source of the
handout's 3-D render figures.

Run (uses the project's CadQuery venv, isolated):
    ../../design/cad-env/bin/python -I blade_rotor_cq.py
Writes out/rotor.stl, out/rotor.step, out/blade.stl, out/hub.stl and prints
validity / volume / bounding box for each.

Everything about the blade is tunable from the PARAMETERS block below; the
same twelve values are the yellow inputs of the companion spreadsheet
(spreadsheet/ETB2-blade-profile.xlsx).  Axes: the rotor spins about +Z; each
blade reaches out along a radius (blade 1 along +Y); an aerofoil section at
radius r lies in a plane of constant radius with its chord along X and its
thickness along Z, and the twist tilts that chord out of the rotor (X-Y) plane.
"""

import math
import os
import cadquery as cq

# ============================ PARAMETERS =====================================
# (one-to-one with the spreadsheet's yellow input cells; edit and re-run)
R_TIP       = 100.0   # mm   tip radius
R_ROOT      = 20.0    # mm   radius where the aerofoil begins
HUB_D       = 36.0    # mm   hub diameter
HUB_L       = 20.0    # mm   hub length (along the spin axis)
BORE_D      = 10.0    # mm   central bore for the shaft adapter (0 = no bore)
N_BLADES    = 3       # -    number of blades
CHORD_ROOT  = 24.0    # mm   chord at the root station
CHORD_TIP   = 9.0     # mm   chord at the tip
TWIST_ROOT  = 25.0    # deg  twist at the root station
TWIST_TIP   = 5.0     # deg  twist at the tip
NACA_T      = 0.12    # -    section thickness ratio (0.12 -> NACA 0012)
PITCH_AXIS  = 0.25    # -    twist axis as a fraction of chord (quarter chord)
N_STATIONS  = 9       # -    number of aerofoil stations from root to tip

# How far the root is sunk into the hub so the print is one watertight solid.
ROOT_EMBED  = 2.0     # mm   (loft starts this far inside the hub surface)

# Export mesh quality (same meaning as make_nacelle.py's export()).
STL_TOL     = 0.02    # mm   max chord deviation of the triangle mesh
STL_ANG     = 0.1     # rad  max angular deviation

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


# ---------------------------------------------------------------------------
def naca_coords(t=NACA_T, n=40):
    """Closed outline of a symmetric NACA 00xx section, unit chord.

    Cosine-spaced x from leading edge (0) to trailing edge (1); returns a list
    of (x, y) going round the outline: upper surface LE->TE, then lower TE->LE.
    Same thickness formula as design/nacelle/make_nacelle.py (rod_boss).
    """
    xs = [0.5 * (1 - math.cos(math.pi * i / n)) for i in range(n + 1)]
    yt = [5 * t * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x**2
                   + 0.2843 * x**3 - 0.1015 * x**4) for x in xs]
    upper = [(x, +y) for x, y in zip(xs, yt)]          # LE -> TE, top
    lower = [(xs[i], -yt[i]) for i in range(n, 0, -1)]  # TE -> LE, bottom (skip LE dup)
    return upper + lower


def chord_at(r):
    """Linear chord taper, clamped to the root value inboard of R_ROOT."""
    rr = max(r, R_ROOT)
    f = (rr - R_ROOT) / (R_TIP - R_ROOT)
    return CHORD_ROOT + (CHORD_TIP - CHORD_ROOT) * f


def twist_at(r):
    """Linear twist, clamped to the root value inboard of R_ROOT."""
    rr = max(r, R_ROOT)
    f = (rr - R_ROOT) / (R_TIP - R_ROOT)
    return TWIST_ROOT + (TWIST_TIP - TWIST_ROOT) * f


def stations():
    """Radii of the loft sections, root (sunk into the hub) -> tip."""
    r0 = HUB_D / 2.0 - ROOT_EMBED               # start inside the hub
    tip_stations = [R_ROOT + (R_TIP - R_ROOT) * i / (N_STATIONS - 1)
                    for i in range(N_STATIONS)]
    return [r0] + tip_stations


def section_points(r):
    """3-D points of one aerofoil section placed at radius r.

    Scaled to the local chord, pitch axis moved to the origin, rotated by the
    local twist about the spanwise (Y) axis, then lifted to radius r.  Returns
    a list of (x, y, z) tuples going round the outline.
    """
    c = chord_at(r)
    theta = math.radians(twist_at(r))
    ct, st = math.cos(theta), math.sin(theta)
    out = []
    for x, y in naca_coords():
        xs = (x - PITCH_AXIS) * c      # chord direction, pitch axis at 0
        zs = y * c                     # thickness direction
        xr = xs * ct + zs * st         # rotate about +Y (twist -> pitch)
        zr = -xs * st + zs * ct
        out.append((xr, r, zr))
    return out


def section_wire(r):
    """One aerofoil section at radius r as a closed CadQuery wire."""
    return cq.Wire.makePolygon([cq.Vector(*p) for p in section_points(r)], close=True)


def build_blade():
    """Loft the twisted, tapering sections into one solid blade."""
    wires = [section_wire(r) for r in stations()]
    solid = cq.Solid.makeLoft(wires)
    return cq.Workplane("XY").add(solid)


def build_hub():
    """A plain cylindrical hub on the spin axis, with a central shaft bore."""
    hub = (cq.Workplane("XY").workplane(offset=-HUB_L / 2.0)
           .circle(HUB_D / 2.0).extrude(HUB_L))
    if BORE_D > 0:
        hub = hub.cut(cq.Workplane("XY").workplane(offset=-HUB_L / 2.0 - 1)
                      .circle(BORE_D / 2.0).extrude(HUB_L + 2))
    return hub


def build_rotor():
    """Hub + N_BLADES blades, evenly spaced about the spin axis, fused."""
    blade = build_blade()
    rotor = build_hub()
    for k in range(N_BLADES):
        b = blade if k == 0 else blade.rotate((0, 0, 0), (0, 0, 1), 360.0 / N_BLADES * k)
        rotor = rotor.union(b)
    return rotor


# ---------------------------------------------------------------------------
def export(wp, name):
    os.makedirs(OUT, exist_ok=True)
    cq.exporters.export(wp, os.path.join(OUT, name + ".step"))
    cq.exporters.export(wp, os.path.join(OUT, name + ".stl"),
                        tolerance=STL_TOL, angularTolerance=STL_ANG)
    v = wp.val()
    bb = v.BoundingBox()
    print(f"{name}: valid={v.isValid()} volume={v.Volume():.0f} mm3 "
          f"bbox x[{bb.xmin:.1f},{bb.xmax:.1f}] y[{bb.ymin:.1f},{bb.ymax:.1f}] "
          f"z[{bb.zmin:.1f},{bb.zmax:.1f}]")


if __name__ == "__main__":
    blade = build_blade()
    export(blade, "blade")
    hub = build_hub()
    export(hub, "hub")
    rotor = build_rotor()
    export(rotor, "rotor")
    print("done ->", OUT)
