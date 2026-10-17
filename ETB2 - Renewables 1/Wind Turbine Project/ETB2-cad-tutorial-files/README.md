# ETB2 CAD tutorial — from a blade spreadsheet to a printable rotor

A self-contained tutorial/exercise for the ETB2 wind-turbine lab. Students take a simple blade
spreadsheet (linear chord taper, linear twist, a NACA 0012 section) and build three blades on a hub,
exported as an STL. It covers the tool-independent workflow once, then one module per CAD tool
(Onshape, Fusion 360, SolidWorks, FreeCAD) and a programming-only route (CadQuery, build123d,
OpenSCAD). Separate from the main `lab-handout/`; it can later feed the `cad.tex` stub there.

## Build the handout
```
make                 # = latexmk -pdf -interaction=nonstopmode -auxdir=aux cad-tutorial
```
Output: `cad-tutorial.pdf` (aux files in `aux/`). `make clean` to clear.

### Modular switches (top of `cad-tutorial.tex`)
- `\includeOnshapetrue/false`, `…Fusion…`, `…SolidWorks…`, `…FreeCAD…` — per GUI tool module.
- `\includeCadQuerytrue/false`, `…Buildd…` (build123d), `…OpenSCAD…` — per code backend.
- `\showTBCtrue/false` — show or hide the draft "to be confirmed" list at the front.
Set a single tool true and the rest false to produce a one-tool variant.

## The input file (students start here)
`spreadsheet/ETB2-blade-profile.xlsx` — two sheets: "Blade" (yellow input cells drive a
formula-only station table + a chord/twist chart) and "NACA0012 section" (unit-chord coordinates).
Regenerate:
```
cd spreadsheet && python3 make_blade_xlsx.py ETB2-blade-profile.xlsx     # system python3 + openpyxl
```

## Reference model + figures (the solution and the figure source)
`reference-model/` holds the CadQuery reference (`blade_rotor_cq.py`) and the build123d and OpenSCAD
twins, all sharing one tunable parameter block (= the spreadsheet inputs). Regenerate the STL/STEP
and the handout figures:
```
cd reference-model
../../design/cad-env/bin/python -I blade_rotor_cq.py    # -> out/rotor.{stl,step}, blade.*, hub.*
../../design/cad-env/bin/python -I render.py            # -> ../figures/*.png
# optional, the other two backends (same rotor):
python blade_rotor_b123d.py            # needs: pip install build123d
openscad -o out/rotor.stl blade_rotor.scad   # needs: openscad
```
All three verified 2026-10-12 to produce the same watertight rotor (≈ 24.9 cm³). See
`reference-model/MANIFEST.md`.

## Layout
```
cad-tutorial.tex        main file (house style, modular toggles, box + listings setup)
sections/               one .tex per section / tool / code backend
figures/                authentic renders from the reference model (PNG)
spreadsheet/            the student input .xlsx + its openpyxl generator
reference-model/        CadQuery / build123d / OpenSCAD scripts + renderer + out/
```

## Conventions
- House style matches `lab-handout/` (Charter fonts, linkblue, `\notebox`, `\tbc`, `\sref`).
- Figures are authentic renders from the reference model, plus TikZ concept diagrams and schematic
  mock-UI sketches (labelled "schematic") with `\shot{}` placeholders for real screenshots.
- Main narrative carries the theory; incidental/example/peripheral material is in `example`,
  `aside` and `advanced` boxes.
- Blade spec (lab-aligned): R = 100 mm, 3 blades, hub Ø36 mm, NACA 0012, chord 24→9 mm, twist
  25°→5°, about the quarter chord.
