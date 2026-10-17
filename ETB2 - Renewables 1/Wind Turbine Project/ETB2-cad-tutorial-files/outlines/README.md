# CAD outline helper files (for the GUI tool appendices)

Course-supplied import files for students doing the rotor in a graphical CAD
tool. All are generated from the same NACA 0012 + linear chord/twist laws as the
reference model, so they match the handout figures exactly.

| File | For | What it is |
|---|---|---|
| `naca0012-unit.dxf` | Onshape, Fusion 360, FreeCAD | One **unit-chord** NACA 0012 section outline (closed), with the **quarter chord at the origin**. Import it, then scale to each station's chord and rotate by its twist. |
| `solidworks-xyz/ETB2-blade-section-00-r16mm.txt` … `-09-r100mm.txt` | SolidWorks | **Ten ready-positioned** station outlines (root plug first at r=16 mm, tip last at r=100 mm). Plain `x  y  z` rows in **millimetres**. Use Insert → Curve → Curve Through XYZ Points on each (tick *Closed curve*), then loft them in order. |
| `ETB2-cad-outlines.zip` | — | All of the above zipped, for one Moodle upload. |

## Regenerate (e.g. for a different blade)
```
cd ../reference-model
python3 gen_gui_helpers.py      # pure Python, no CadQuery needed
```
Edit the `PARAMETERS` block at the top of `gen_gui_helpers.py` (identical to the
spreadsheet's yellow inputs) and rerun. The generator's geometry is a verbatim
mirror of `blade_rotor_cq.py`; they are checked to agree to 0.00 mm.
