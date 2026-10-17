// ETB2 CAD tutorial - reference rotor in OpenSCAD.
//
// Same blade spec, and the SAME PARAMETERS block (names + values), as the
// CadQuery reference blade_rotor_cq.py: linear chord taper, linear twist
// about the quarter chord, NACA 0012 sections, three blades on a bored hub,
// written out as one STL.
//
// To install and render an STL:
//
//     (Ubuntu)  sudo apt install openscad
//     (macOS)   brew install --cask openscad
//     openscad -o rotor.stl blade_rotor.scad
//
// OpenSCAD has no lofting primitive, so the blade is lofted the robust,
// library-free way: every aerofoil station is turned into a ring of 3-D
// points, and all the rings are stitched into ONE polyhedron - a single
// watertight skin, with quad side faces between neighbouring sections and a
// triangle fan capping the root and the tip.  (A tempting shortcut -
// hull() between thin extruded slices - leaves internal faces where the
// slices meet, so the result is not a clean single-volume solid; the
// polyhedron avoids that.)
//
// OpenSCAD builds the blade with its span along +Z, then rotates it so the
// blades lie radially in the X-Y plane with the rotor spinning about Z - the
// SAME final result as the other backends (rotor about z, blades radial).

// ============================ PARAMETERS =====================================
// (one-to-one with the spreadsheet / the CadQuery script; edit and re-render)
R_TIP      = 100.0;  // mm   tip radius
R_ROOT     = 20.0;   // mm   radius where the aerofoil begins
HUB_D      = 36.0;   // mm   hub diameter
HUB_L      = 20.0;   // mm   hub length (along the spin axis)
BORE_D     = 10.0;   // mm   central bore for the shaft adapter (0 = no bore)
N_BLADES   = 3;      // -    number of blades
CHORD_ROOT = 24.0;   // mm   chord at the root station
CHORD_TIP  = 9.0;    // mm   chord at the tip
TWIST_ROOT = 25.0;   // deg  twist at the root station
TWIST_TIP  = 5.0;    // deg  twist at the tip
NACA_T     = 0.12;   // -    section thickness ratio (0.12 -> NACA 0012)
PITCH_AXIS = 0.25;   // -    twist axis as a fraction of chord (quarter chord)
N_STATIONS = 9;      // -    number of aerofoil stations from root to tip

// How far the root is sunk into the hub so the print is one watertight solid.
ROOT_EMBED = 2.0;    // mm   (loft starts this far inside the hub surface)

NACA_N  = 40;        // points per surface of the NACA outline (= cq naca_coords n)
$fn     = 96;        // facets for the hub cylinder and bore

// (The CadQuery script's STL_TOL / STL_ANG have no OpenSCAD equivalent;
//  OpenSCAD meshes curves from $fn/$fs/$fa instead - here $fn above.)

// ========================= AEROFOIL + LINEAR LAWS ============================
// Linear chord taper and twist, clamped to the root value inboard of R_ROOT.
function chord_at(r) = let (rr = max(r, R_ROOT))
    CHORD_ROOT + (CHORD_TIP - CHORD_ROOT) * (rr - R_ROOT) / (R_TIP - R_ROOT);

function twist_at(r) = let (rr = max(r, R_ROOT))
    TWIST_ROOT + (TWIST_TIP - TWIST_ROOT) * (rr - R_ROOT) / (R_TIP - R_ROOT);

// Loft station radii: station 0 is sunk into the hub, then N_STATIONS out to
// the tip (N_STATIONS + 1 stations in all, indices 0 .. N_STATIONS).
function station(i) = (i == 0)
    ? HUB_D / 2 - ROOT_EMBED
    : R_ROOT + (R_TIP - R_ROOT) * (i - 1) / (N_STATIONS - 1);

// Symmetric NACA 00xx outline on a unit chord.  OpenSCAD trig is in degrees,
// so cos(180*i/n) here is the cosine-spacing cos(pi*i/n) of the other scripts.
function naca_x(i) = 0.5 * (1 - cos(180 * i / NACA_N));
function naca_yt(x) = 5 * NACA_T * (0.2969 * sqrt(x) - 0.1260 * x
    - 0.3516 * x * x + 0.2843 * x * x * x - 0.1015 * x * x * x * x);

// Closed outline scaled to chord c, with the quarter chord shifted to origin:
// upper surface LE->TE, then lower surface TE->LE.
function naca_points(c) = concat(
    [ for (i = [0 : NACA_N])      [ (naca_x(i) - PITCH_AXIS) * c,  naca_yt(naca_x(i)) * c ] ],
    [ for (i = [NACA_N : -1 : 1]) [ (naca_x(i) - PITCH_AXIS) * c, -naca_yt(naca_x(i)) * c ] ]
);

// =============================== MODELLING ===================================
// STEP 1 - one aerofoil section placed in 3-D: scale to the local chord, twist
// about the quarter chord (the origin), and lift to spanwise height z = r.
// sec2d gives the rotated 2-D outline; PTS places every section's outline at
// its own station height to make the full list of blade-surface points.
function sec2d(r) = let (c = chord_at(r), a = twist_at(r))
    [ for (p = naca_points(c)) [ p[0]*cos(a) - p[1]*sin(a), p[0]*sin(a) + p[1]*cos(a) ] ];

NS   = N_STATIONS;              // sections are indexed 0 .. NS  (NS + 1 of them)
MPTS = len(naca_points(1));     // points per section outline
PTS  = [ for (i = [0:NS]) for (p = sec2d(station(i))) [ p[0], p[1], station(i) ] ];
function pid(i, j) = i * MPTS + j;

// STEP 2 - loft: stitch the ordered sections into ONE polyhedron (a clean,
// watertight skin).  SIDES are the quad faces (two triangles each) joining
// each section ring to the next; ROOTCAP and TIPCAP are triangle fans that
// close the two ends.  The point order round each ring makes the faces come
// out with outward normals.
SIDES = [ for (i = [0:NS-1]) for (j = [0:MPTS-1]) let (jn = (j + 1) % MPTS)
          each [ [pid(i,j), pid(i,jn), pid(i+1,jn)], [pid(i,j), pid(i+1,jn), pid(i+1,j)] ] ];
ROOTCAP = [ for (j = [1:MPTS-2]) [pid(0, 0),  pid(0, j+1), pid(0, j)] ];
TIPCAP  = [ for (j = [1:MPTS-2]) [pid(NS, 0), pid(NS, j),  pid(NS, j+1)] ];

// The blade, span running along +Z, root -> tip.
module blade_along_z() {
    polyhedron(points = PTS, faces = concat(SIDES, ROOTCAP, TIPCAP), convexity = 10);
}

// STEP 3 - hub: a cylinder on the Z axis (centred) minus the central bore.
module hub() {
    difference() {
        cylinder(h = HUB_L, d = HUB_D, center = true);
        cylinder(h = HUB_L + 2, d = BORE_D, center = true);
    }
}

// STEPS 4 & 5 - pattern the blade: orient each blade from +Z to radial +Y,
// then step it round the spin axis by 120 deg; union with the hub.  Rendering
// to STL (openscad -o rotor.stl ...) is the export step.
module rotor() {
    hub();
    for (k = [0 : N_BLADES - 1])
        rotate([0, 0, 360 / N_BLADES * k])   // N blades, evenly spaced about Z
            rotate([-90, 0, 0])              // span Z -> radial +Y, thickness -> Z
                blade_along_z();
}

rotor();
