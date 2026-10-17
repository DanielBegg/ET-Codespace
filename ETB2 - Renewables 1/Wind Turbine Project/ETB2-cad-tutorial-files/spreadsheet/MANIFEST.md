# ETB2 blade-profile spreadsheet: provenance

`ETB2-blade-profile.xlsx` is the student input for the CAD tutorial: a simple
three-blade rotor with a NACA 0012 section and linear chord and twist.
Generated 2026-10-12 by `make_blade_xlsx.py` (openpyxl, system python3).

**Yellow cells are inputs; everything else is a formula.** The station table
and the chord/twist chart on sheet `Blade` are pure formulas of the inputs, so
changing an input updates the whole blade.

## Inputs (defaults)
R_tip 100 mm; r_root 20 mm (aerofoil starts); hub diameter 36 mm; hub length
20 mm; 3 blades; c_root 24 mm; c_tip 9 mm; root twist 25 deg; tip twist 5 deg;
section NACA0012; pitch axis 0.25 c; N = 9 stations.

## Linear laws (station i = 1..N)
- r = r_root + (R_tip - r_root)(i-1)/(N-1)
- r/R = r / R_tip
- c = c_root + (c_tip - c_root)(r - r_root)/(R_tip - r_root)
- twist = twist_root + (twist_tip - twist_root)(r - r_root)/(R_tip - r_root)

The table has a fixed 9 rows; N is used in the r formula, but changing N means
adding or deleting rows by hand.

## Sheet `NACA0012 section`
Normalised outline (unit chord, 81 points, plain values): upper surface LE to
TE, then lower surface TE to LE. Cosine-spaced x = 0.5(1 - cos(pi i/40)),
i = 0..40; half-thickness
yt = 5 t (0.2969 sqrt(x) - 0.1260 x - 0.3516 x^2 + 0.2843 x^3 - 0.1015 x^4),
t = 0.12. Same formula as `rod_boss()` in `design/nacelle/make_nacelle.py`
(the open trailing edge, 0.126% chord half-thickness at x = 1, is kept).

## Regenerate
    python3 make_blade_xlsx.py ETB2-blade-profile.xlsx
