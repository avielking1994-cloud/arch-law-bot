#!/usr/bin/env python3
"""
Faucet-mounted support bracket for a wire soap/sponge rack.

Use-orientation (before print rotation):
  * Z up, the faucet pipe axis is the Z axis at (0,0).
  * The wall is the plane x = ARM_L (+X points from the faucet toward the wall).
  * The arm rises toward the wall at ANGLE degrees, so if the bracket tries to
    rotate downward its tip is pushed harder into the wall (a wedge).

The STL is exported in PRINT orientation: the arm lies flat on the bed and the
clamp ring is tilted by ANGLE.  No supports needed.

Requires:  pip install manifold3d numpy
Run:       python3 bracket.py            -> bracket_L110.stl
           python3 bracket.py 120        -> bracket_L120.stl  (other arm length)
"""
import math
import struct
import sys

import numpy as np
from manifold3d import CrossSection, Manifold

# ----------------------------- parameters (mm) ------------------------------
PIPE_D   = 25.0   # faucet pipe diameter
CLEAR    = 0.6    # bore clearance (bore = PIPE_D + CLEAR)
WALL     = 4.5    # ring wall thickness
RING_H   = 24.0   # ring height above the arm bottom
RING_EXT = 8.0    # extra ring height below (clipped flat in print orientation)
SLOT_W   = 23.0   # opening width of the C-ring (snap-on onto the pipe)
EAR_LEN  = 10.0   # clamp ears length (beyond the ring)
EAR_T    = 8.0    # clamp ears thickness
BOLT_D   = 4.4    # M4 bolt clearance hole
NUT_AF   = 7.3    # M4 nut pocket, across flats
NUT_DEPTH = 3.5

ARM_L    = 110.0  # horizontal distance pipe-centre -> wall  (user: 11 cm)
ANGLE    = 15.0   # arm rise angle toward the wall (degrees)
ARM_W    = 16.0   # arm width
ARM_T    = 10.0   # arm thickness
GUSSET_L = 32.0   # gusset length along the arm at the ring joint

PAD_T    = 4.0    # wall pad thickness
PAD_W    = 32.0   # wall pad width
PAD_H    = 42.0   # wall pad height
BLOCK_L  = 18.0   # cradle block length (along X)
BLOCK_W  = 20.0   # cradle block width
BLOCK_UP = 18.0   # cradle block height above the arm top
WIRE_D   = 5.0    # rack wire diameter
GROOVE_W = WIRE_D + 2.5
GROOVE_DEPTH = 9.0
GROOVE_FROM_WALL = 7.5   # groove centre distance from the wall face

SEG = 96          # circle segments
# ---------------------------------------------------------------------------


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl_z(r, z0, z1, x=0.0, y=0.0, seg=SEG):
    return Manifold.cylinder(z1 - z0, r, r, seg).translate([x, y, z0])


def cyl_y(r, y0, y1, x=0.0, z=0.0, seg=SEG):
    # cylinder along +Y from y0 to y1
    return Manifold.cylinder(y1 - y0, r, r, seg).rotate([-90, 0, 0]).translate([x, y0, z])


def ccw(pts):
    """Return the polygon with counter-clockwise winding (required by CrossSection)."""
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))
    return list(reversed(pts)) if area < 0 else list(pts)


def xz_polygon_extrude_y(pts, y0, y1):
    """Extrude a polygon given in the XZ plane between y0..y1."""
    cs = CrossSection([ccw(pts)])
    m = Manifold.extrude(cs, y1 - y0)          # along +Z, polygon in XY
    m = m.rotate([90, 0, 0])                   # (x,y,z) -> (x,-z,y): poly y -> z
    return m.translate([0, y1, 0])             # extrusion now spans y0..y1


def build(arm_l=ARM_L, angle=ANGLE):
    a = math.radians(angle)
    t = math.tan(a)
    r_in = PIPE_D / 2 + CLEAR / 2
    r_out = r_in + WALL

    def arm_bottom(x):
        return x * t

    def arm_top(x):
        return x * t + ARM_T / math.cos(a)

    z_lo = -RING_EXT

    # ---- clamp ring with ears (opening toward -X, away from the wall) ----
    ring = cyl_z(r_out, z_lo, RING_H)
    ears = box(-(r_out + EAR_LEN), 0.0, -(SLOT_W / 2 + EAR_T), (SLOT_W / 2 + EAR_T), z_lo, RING_H)
    clamp = ring + ears

    # ---- arm (tilted box, overshoots and is cut at the wall plane) ----
    arm_len = (arm_l + 20) / math.cos(a)
    arm = Manifold.cube([arm_len, ARM_W, ARM_T]).translate([0, -ARM_W / 2, 0]).rotate([0, -angle, 0])
    x_arm0 = r_out - 3.0
    arm = arm.translate([x_arm0, 0, arm_bottom(x_arm0)])

    # gusset filling ring wall -> arm top
    gx0 = r_out - 3.0
    gx1 = gx0 + GUSSET_L
    gusset = xz_polygon_extrude_y(
        [(gx0, arm_top(gx0) - 1), (gx0, RING_H), (gx1, arm_top(gx1))],
        -ARM_W / 2, ARM_W / 2)
    # ---- tip: cradle block + wall pad ----
    bx0 = arm_l - BLOCK_L
    block_top = arm_top(arm_l) + BLOCK_UP
    block = box(bx0, arm_l, -BLOCK_W / 2, BLOCK_W / 2, arm_bottom(bx0) + 0.5, block_top)
    pad_zc = (arm_bottom(arm_l) + block_top) / 2
    pad = box(arm_l - PAD_T, arm_l, -PAD_W / 2, PAD_W / 2, pad_zc - PAD_H / 2, pad_zc + PAD_H / 2)
    # small fillet-like braces from pad to block sides
    brace = xz_polygon_extrude_y(
        [(arm_l - PAD_T, pad_zc - PAD_H / 2), (arm_l - PAD_T, arm_bottom(bx0) + 0.5), (bx0, arm_bottom(bx0) + 0.5)],
        -BLOCK_W / 2, BLOCK_W / 2)

    body = clamp + arm + gusset + block + pad + brace

    # ---- cuts ----
    bore = cyl_z(r_in, z_lo - 1, RING_H + 1)
    slot = box(-(r_out + EAR_LEN + 5), 0, -SLOT_W / 2, SLOT_W / 2, z_lo - 1, RING_H + 1)
    # lead-in chamfer at the slot mouth (widens the opening in the XY plane)
    ex = -(r_out + EAR_LEN)
    ch = 3.0
    def mouth_wedge(sign):
        pts = [(ex - 1, sign * (SLOT_W / 2 - 0.01)),
               (ex + ch, sign * (SLOT_W / 2 - 0.01)),
               (ex - 1, sign * (SLOT_W / 2 + ch))]
        cs = CrossSection([ccw(pts)])
        return Manifold.extrude(cs, RING_H - z_lo + 2).translate([0, 0, z_lo - 1])
    chamfer = mouth_wedge(1) + mouth_wedge(-1)
    # bolt through the ears (along Y) + nut pocket on +Y ear
    bxc = -(r_out + EAR_LEN / 2 + 1)
    bzc = (z_lo + RING_H) / 2 + 2
    bolt = cyl_y(BOLT_D / 2, -60, 60, x=bxc, z=bzc, seg=48)
    nut_r = NUT_AF / (2 * math.cos(math.radians(30)))
    nut = cyl_y(nut_r, SLOT_W / 2 + EAR_T - NUT_DEPTH, SLOT_W / 2 + EAR_T + 1, x=bxc, z=bzc, seg=6)
    # wire groove (U) across the cradle block, parallel to the wall
    gxc = arm_l - GROOVE_FROM_WALL
    gzc = block_top - GROOVE_DEPTH + GROOVE_W / 2
    groove = cyl_y(GROOVE_W / 2, -BLOCK_W, BLOCK_W, x=gxc, z=gzc, seg=48) \
        + box(gxc - GROOVE_W / 2, gxc + GROOVE_W / 2, -BLOCK_W, BLOCK_W, gzc, block_top + 2)
    # nothing beyond the wall plane
    beyond = box(arm_l, arm_l + 200, -200, 200, -200, 400)

    body = body - bore - slot - chamfer - bolt - nut - groove - beyond

    # ---- print orientation: arm flat on the bed, clip below the bed ----
    body = body.rotate([0, angle, 0])
    bed_cut = box(-300, 300, -300, 300, -300, 0)
    body = body - bed_cut
    return body


def write_stl(m: Manifold, path: str):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=np.float32)[:, :3]
    tri = np.asarray(mesh.tri_verts, dtype=np.int64)
    p0, p1, p2 = v[tri[:, 0]], v[tri[:, 1]], v[tri[:, 2]]
    n = np.cross(p1 - p0, p2 - p0)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1
    n = (n / ln).astype(np.float32)
    with open(path, "wb") as f:
        f.write(b"soap rack faucet bracket".ljust(80, b"\0"))
        f.write(struct.pack("<I", len(tri)))
        rec = np.zeros(len(tri), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
        rec["n"] = n
        rec["v"][:, 0], rec["v"][:, 1], rec["v"][:, 2] = p0, p1, p2
        f.write(rec.tobytes())


if __name__ == "__main__":
    arm_l = float(sys.argv[1]) if len(sys.argv) > 1 else ARM_L
    m = build(arm_l)
    out = f"bracket_L{int(round(arm_l))}.stl"
    write_stl(m, out)
    bb = m.bounding_box()
    print(f"{out}: {m.num_tri()} triangles, volume {m.volume()/1000:.1f} cm^3, "
          f"bbox {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm, genus {m.genus()}")
