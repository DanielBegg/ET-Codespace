"""ETB2 CAD tutorial - generate the GUI import helpers (DXF + SolidWorks XYZ).

Writes the course-supplied outline files the GUI appendices refer to, straight
from the same NACA 0012 + linear chord/twist laws as the reference model:

    ../outlines/naca0012-unit.dxf              one unit-chord section outline,
                                               quarter chord at the origin
                                               (Onshape / Fusion 360 / FreeCAD
                                               import this, then scale + twist
                                               + place each station themselves)
    ../outlines/solidworks-xyz/
        ETB2-blade-section-00-r16mm.txt ...    ten ready-positioned station
        ETB2-blade-section-09-r100mm.txt       outlines (x y z, in mm) for
                                               SolidWorks "Curve Through XYZ
                                               Points", lofted root -> tip

This script is PURE standard-library Python on purpose: a student can rerun it
after editing the PARAMETERS below (for a blade of their own) with nothing but
    python3 gen_gui_helpers.py
No CadQuery, no third-party packages.

The geometry functions below are a verbatim mirror of blade_rotor_cq.py (the
reference solution); keep the two in sync.  gen_gui_helpers_check.py asserts
they still agree, point for point, with the reference model.
"""
import math
import os
import zipfile

# ============================ PARAMETERS =====================================
# (identical to blade_rotor_cq.py and to the spreadsheet's yellow input cells)
R_TIP       = 100.0   # mm   tip radius
R_ROOT      = 20.0    # mm   radius where the aerofoil begins
HUB_D       = 36.0    # mm   hub diameter
N_BLADES    = 3       # -    number of blades
CHORD_ROOT  = 24.0    # mm   chord at the root station
CHORD_TIP   = 9.0     # mm   chord at the tip
TWIST_ROOT  = 25.0    # deg  twist at the root station
TWIST_TIP   = 5.0     # deg  twist at the tip
NACA_T      = 0.12    # -    section thickness ratio (0.12 -> NACA 0012)
PITCH_AXIS  = 0.25    # -    twist axis as a fraction of chord (quarter chord)
N_STATIONS  = 9       # -    number of aerofoil stations from root to tip
ROOT_EMBED  = 2.0     # mm   how far the root section sinks into the hub

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outlines")
XYZ = os.path.join(OUT, "solidworks-xyz")


# ------------------------- geometry (mirror of blade_rotor_cq.py) ------------
def naca_coords(t=NACA_T, n=40):
    """Closed outline of a symmetric NACA 00xx section, unit chord.

    Cosine-spaced x from leading edge (0) to trailing edge (1); returns a list
    of (x, y) going round the outline: upper surface LE->TE, then lower TE->LE.
    """
    xs = [0.5 * (1 - math.cos(math.pi * i / n)) for i in range(n + 1)]
    yt = [5 * t * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x**2
                   + 0.2843 * x**3 - 0.1015 * x**4) for x in xs]
    upper = [(x, +y) for x, y in zip(xs, yt)]
    lower = [(xs[i], -yt[i]) for i in range(n, 0, -1)]
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
    r0 = HUB_D / 2.0 - ROOT_EMBED
    tip_stations = [R_ROOT + (R_TIP - R_ROOT) * i / (N_STATIONS - 1)
                    for i in range(N_STATIONS)]
    return [r0] + tip_stations


def unit_outline():
    """Unit-chord NACA 0012 outline with the quarter chord at the origin."""
    return [(x - PITCH_AXIS, y) for x, y in naca_coords()]


def section_points(r):
    """3-D points (x, y, z) in mm of one aerofoil section placed at radius r.

    Scaled to the local chord, pitch axis at the origin, rotated by the local
    twist about the spanwise (Y) axis, then lifted to radius r.
    """
    c = chord_at(r)
    theta = math.radians(twist_at(r))
    ct, st = math.cos(theta), math.sin(theta)
    out = []
    for x, y in naca_coords():
        xs = (x - PITCH_AXIS) * c
        zs = y * c
        xr = xs * ct + zs * st
        zr = -xs * st + zs * ct
        out.append((xr, r, zr))
    return out


# ------------------------------- writers -------------------------------------
def write_dxf(path, pts):
    """A closed polyline of pts (list of (x, y)) as a minimal R12 DXF.

    R12 (AC1009) with an old-style POLYLINE is the most widely importable DXF
    flavour - Onshape, Fusion 360 and FreeCAD all read it.
    """
    L = ["0", "SECTION", "2", "HEADER",
         "9", "$ACADVER", "1", "AC1009",
         "0", "ENDSEC",
         "0", "SECTION", "2", "ENTITIES",
         "0", "POLYLINE", "8", "0", "66", "1", "70", "1"]
    for x, y in pts:
        L += ["0", "VERTEX", "8", "0",
              "10", f"{x:.6f}", "20", f"{y:.6f}", "30", "0.0"]
    L += ["0", "SEQEND",
          "0", "ENDSEC", "0", "EOF"]
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def write_xyz(path, pts):
    """Pure numeric x<TAB>y<TAB>z rows for SolidWorks Curve Through XYZ Points.

    No header line: the Curve Through XYZ Points reader wants numbers only.
    """
    with open(path, "w") as f:
        for x, y, z in pts:
            f.write(f"{x:.5f}\t{y:.5f}\t{z:.5f}\n")


def station_name(i, r):
    return f"ETB2-blade-section-{i:02d}-r{int(round(r))}mm.txt"


def main():
    os.makedirs(XYZ, exist_ok=True)

    dxf_path = os.path.join(OUT, "naca0012-unit.dxf")
    write_dxf(dxf_path, unit_outline())
    print("wrote", os.path.relpath(dxf_path, HERE),
          f"({len(unit_outline())} vertices, unit chord, 1/4-chord at origin)")

    xyz_paths = []
    for i, r in enumerate(stations()):
        p = os.path.join(XYZ, station_name(i, r))
        write_xyz(p, section_points(r))
        xyz_paths.append(p)
        print("wrote", os.path.relpath(p, HERE),
              f"(r={r:g} mm, chord={chord_at(r):.3f} mm, twist={twist_at(r):.3f} deg)")

    # One zip for easy upload to Moodle.
    zip_path = os.path.join(OUT, "ETB2-cad-outlines.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(dxf_path, "naca0012-unit.dxf")
        for p in xyz_paths:
            z.write(p, os.path.join("solidworks-xyz", os.path.basename(p)))
    print("wrote", os.path.relpath(zip_path, HERE), "(bundle for Moodle)")


if __name__ == "__main__":
    main()
