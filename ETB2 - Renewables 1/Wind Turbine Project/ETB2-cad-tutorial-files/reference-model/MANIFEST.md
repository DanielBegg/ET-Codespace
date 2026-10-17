# Reference rotor model — provenance

Built 2026-10-12 for the ETB2 CAD tutorial (`cad-tutorial/`). All files here are
**ours** (not from `lily-design/`); safe to run.

## What this is
The reference solution for turning the simple blade spec
(`../spreadsheet/ETB2-blade-profile.xlsx`) into three blades on a hub and
exporting an STL. It is also the source of the handout's 3-D render figures.

## Geometry (tunable at the top of `blade_rotor_cq.py`; mirrors the spreadsheet inputs)
- Tip radius R = 100 mm, aerofoil root station r = 20 mm.
- Hub Ø36 mm × 20 mm long, central bore Ø10 mm, on the spin axis (z).
- 3 blades, 120° apart.
- Section: **NACA 0012** (symmetric, t/c = 0.12) at every station.
- Chord: linear taper 24 mm (root) → 9 mm (tip).
- Twist: linear 25° (root) → 5° (tip), about the quarter chord (pitch axis 0.25 c).
- The loft starts 2 mm inside the hub surface (`ROOT_EMBED`) so the print is one
  watertight solid; chord/twist are clamped to the root value inboard of r = 20 mm.
- Axes: rotor spins about +z; blade 1 reaches along +y; a section at radius r has
  its chord along x and thickness along z, and the twist tilts the chord into z.

## Files
- `blade_rotor_cq.py` — CadQuery reference model (the figure/STL source of truth).
- `blade_rotor_b123d.py` — build123d parity script (same geometry; native `loft` over section faces).
- `blade_rotor.scad` — OpenSCAD parity script (same geometry; a single `polyhedron` skin).
- `render.py` — **orchestrator**: runs the three steps below in the right venv (one command).
- `gen_render_meshes.py` — render-only tessellations → `out/render/*.stl` (finer than the print STL, plus one coarse blade). Runs in `design/cad-env`.
- `render_pv.py` — **3-D figures** (pyvista/VTK): rotor iso + front, blade, hub, coarse/fine mesh. Runs in `fig-env` with `DISPLAY=:0`.
- `render_2d.py` — **2-D figures** (matplotlib): NACA 0012 section, stacked twisted sections. Runs in `design/cad-env` (imports the model for exact geometry; bakes the handout's XCharter font).
- `fig-env/` — generated: the permanent figure venv (pyvista 0.49.1 + vtk 9.7.1 + trimesh + numpy + pillow). **Do not** put pyvista in `design/cad-env` (clashes with its vtk).
- `out/` — generated print meshes: `rotor.{stl,step}`, `blade.{stl,step}`, `hub.{stl,step}` (tolerance 0.02, **untouched** by the figure pipeline).
- `out/render/` — generated render meshes: `blade_xfine.stl`, `hub_xfine.stl` (tol 0.003), `blade_coarse.stl` (tol 1.2).

All three CAD backends share one parameter block (the spreadsheet inputs) and produce the same rotor.

## Regenerate
Model + print STL (unchanged):
```
cd reference-model
../../design/cad-env/bin/python -I blade_rotor_cq.py   # -> out/*.stl, *.step
```

All eight handout figures, one command (shells out to both venvs; needs hardware GL on `DISPLAY=:0`):
```
cd reference-model
python3 render.py                                      # -> ../figures/*.png (all 8)
```
Or the three steps by hand:
```
../../design/cad-env/bin/python -I gen_render_meshes.py        # out/render/*.stl
../../design/cad-env/bin/python -I render_2d.py                # fig-naca0012, fig-sections-stacked
DISPLAY=:0 ./fig-env/bin/python render_pv.py                   # the six 3-D figures (+ steel sample)
```
Build the figure venv once (if `fig-env/` is missing):
```
python3 -m venv fig-env
./fig-env/bin/pip install "pyvista==0.49.1" "vtk==9.7.1" trimesh numpy pillow
```
`design/cad-env` (cadquery 2.8.0) supplies the CAD + matplotlib steps, isolated (`-I`).
This box has hardware GL on `DISPLAY=:0`, so VTK renders off-screen directly (no Xvfb);
override the display with `ETB2_DISPLAY=...` if needed.

## Figure style (house spec — implemented in the render scripts)
3-D set (`render_pv.py`): the rotor is **composed from parts** (never the fused
`rotor.stl`) — `hub` (normals feature-angle 45°, crisp rim + bore) plus three
`blade` copies at 0/120/240° about +Z (feature-angle 180°, no loft striping).
Neutral clay body `#C9CDD4`; the part under discussion in house blue `#004896`
(the accent blade in the rotor, the lone blade); hub in clay. Matte Phong
(specular 0.12 / power 20 / diffuse 0.9 / ambient 0.30); 3 directional lights
(key/fill/rim); parallel projection with fixed reused views; vertical gradient
background `#FBFCFD→#E7ECF2`; SSAA. SSAO is off everywhere — it bands convex
parts (horizontal rings on the hub wall, faint striping on the blade tops) and
the 3-point lighting already carries the form. A soft
contact shadow is faked in PIL (object silhouette squashed, planted just below
the part, blurred — bottom-anchored, so it pools under the part, not above it).
A steel-blue (`#5E7BA6`) monochrome rotor variant is written to the compare
samples dir for reference. Output 1600×1200, no baked text (captions describe them).

2-D set (`render_2d.py`): matplotlib restyle — house blue outline, vermillion
`#BE2828` pitch axis, Tufte spines, ISO line-weight ladder, direct labels, the
handout's XCharter font (falls back to a serif if the OTFs move). Text baked large
so it reads ~body size once placed. `fig-sections-stacked` is a clean iso line
skeleton (a 2-D orthographic projection — no 3-D box clutter) with root and tip
in bold.

## Checks (2026-10-12) — all three backends verified by execution
- **CadQuery** (cadquery 2.8.0, `design/cad-env`): all solids `valid=True`; rotor volume ≈ 24929 mm³,
  bbox ±~90 mm × [−56,100] mm × ±10 mm; `rotor.stl` watertight (3978 triangles, every edge shared twice).
- **build123d** (0.13.0, `pip install build123d`): identical results — blade 2105 mm³, rotor 24929 mm³,
  same bounding box.
- **OpenSCAD** (2021.01): CGAL reports "Simple: yes"; rotor mesh watertight (every edge shared twice),
  signed volume 24888 mm³ (≈ CadQuery within mesh tolerance). The single `polyhedron` skin avoids the
  internal faces that a hull-of-thin-slices loft would leave.
- Reuses the NACA 00xx thickness formula and the STEP/STL `export()` pattern from
  `design/nacelle/make_nacelle.py`.

## FreeCAD appendix screenshots
`figures/fig-fc-{sections,blade,hub,rotor}.png` are REAL FreeCAD 1.1 screenshots,
captured by driving the FreeCAD GUI automatically (no hand-clicking). Regenerate:
```
cd freecad-shots && ./capture_freecad_shots.sh    # needs DISPLAY=:0, freecad snap, xdotool, imagemagick
```
See `freecad-shots/README.md`. Only FreeCAD is scripted this way (local Python API);
the other GUI tools keep schematic mock-UIs.
