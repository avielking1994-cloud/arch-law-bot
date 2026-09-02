#!/usr/bin/env python3
"""
Pedestal with a 25 mm "fake faucet pipe" for a wire soap/sponge rack.

The rack's own plastic collet (25 mm bore) clamps onto the post exactly as it
would on a straight faucet.  The pedestal stands on the counter between the
faucet and the wall; its rear edge butts against the wall and the post leans
slightly toward the wall, so the rack's weight pushes the pedestal into the
wall instead of tipping it forward.

Coordinates: Z up, +X points toward the wall (rear edge of the base is at
x = BASE_D/2).  Printed base-down, no supports.

Requires:  pip install manifold3d numpy
Run:       python3 pedestal.py              -> pedestal_D75.stl
           python3 pedestal.py 50           -> post axis 50 mm from the wall
"""
import math
import struct
import sys

import numpy as np
from manifold3d import CrossSection, Manifold

# ----------------------------- parameters (mm) ------------------------------
POST_D      = 24.8   # post diameter (collet bore is 25.0)
POST_H      = 70.0   # post height above the base
POST_TILT   = 8.0    # lean toward the wall (degrees)
POST_CHAMF  = 2.0    # top chamfer so the collet slides on easily
COLLAR_D    = 34.0   # reinforcing collar at the post foot
COLLAR_H    = 8.0

POST_FROM_WALL = 75.0  # post axis -> wall (rear edge of the base)
BASE_FRONT  = 35.0   # base extends this far in front of the post axis
BASE_W      = 80.0   # base width
BASE_T      = 4.0    # base thickness
BASE_R      = 8.0    # base corner radius
LIP_H       = 10.0   # rear lip that rests against the wall
LIP_T       = 4.0
GUSSET_L    = 22.0   # ribs from the post to the base
GUSSET_T    = 4.0
SEG = 128
# ---------------------------------------------------------------------------


def ccw(pts):
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))
    return list(reversed(pts)) if area < 0 else list(pts)


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def rounded_rect(x0, x1, y0, y1, r, z0, z1, seg=32):
    cs = CrossSection([ccw([(x0 + r, y0), (x1 - r, y0), (x1, y0 + r), (x1, y1 - r),
                            (x1 - r, y1), (x0 + r, y1), (x0, y1 - r), (x0, y0 + r)])])
    corners = Manifold()
    for (cx, cy) in [(x0 + r, y0 + r), (x1 - r, y0 + r), (x1 - r, y1 - r), (x0 + r, y1 - r)]:
        corners = corners + Manifold.cylinder(z1 - z0, r, r, seg).translate([cx, cy, z0])
    return Manifold.extrude(cs, z1 - z0).translate([0, 0, z0]) + corners


def build(post_from_wall=POST_FROM_WALL, tilt=POST_TILT):
    wall_x = post_from_wall            # wall plane (rear edge of the base)
    x0 = -BASE_FRONT                   # front edge of the base
    base = rounded_rect(x0, wall_x, -BASE_W / 2, BASE_W / 2, BASE_R, 0, BASE_T)
    lip = box(wall_x - LIP_T, wall_x, -BASE_W / 2 + BASE_R, BASE_W / 2 - BASE_R, 0, BASE_T + LIP_H)

    # post: cylinder with a chamfered top, leaning toward +X (the wall)
    r = POST_D / 2
    post = Manifold.cylinder(POST_H - POST_CHAMF, r, r, SEG) + \
        Manifold.cylinder(POST_CHAMF, r, r - POST_CHAMF, SEG).translate([0, 0, POST_H - POST_CHAMF])
    post = post.translate([0, 0, -1.5])                       # sink into the base
    collar = Manifold.cylinder(COLLAR_H, COLLAR_D / 2, r + 0.5, SEG).translate([0, 0, -1.5])
    post = (post + collar).rotate([0, tilt, 0])             # +tilt about Y leans the top toward +X
    post = post.translate([0, 0, BASE_T])

    # four gusset ribs around the post foot (in the base plane, not tilted)
    rib_pts = ccw([(0, BASE_T - 0.5), (r + GUSSET_L, BASE_T - 0.5), (0, BASE_T + COLLAR_H + 6)])
    rib = Manifold.extrude(CrossSection([rib_pts]), GUSSET_T).rotate([90, 0, 0]).translate([0, GUSSET_T / 2, 0])
    ribs = Manifold()
    for ang in (0, 90, 180, 270):
        ribs = ribs + rib.rotate([0, 0, ang])
    ribs = ribs - Manifold.cylinder(60, r - 1, r - 1, SEG).rotate([0, tilt, 0]).translate([0, 0, BASE_T - 1])

    body = base + lip + post + ribs
    return body


def write_stl(m: Manifold, path: str):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=np.float32)[:, :3]
    tri = np.asarray(mesh.tri_verts, dtype=np.int64)
    p0, p1, p2 = v[tri[:, 0]], v[tri[:, 1]], v[tri[:, 2]]
    n = np.cross(p1 - p0, p2 - p0)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1
    rec = np.zeros(len(tri), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    rec["n"] = (n / ln).astype(np.float32)
    rec["v"][:, 0], rec["v"][:, 1], rec["v"][:, 2] = p0, p1, p2
    with open(path, "wb") as f:
        f.write(b"soap rack pedestal post".ljust(80, b"\0"))
        f.write(struct.pack("<I", len(tri)))
        f.write(rec.tobytes())


if __name__ == "__main__":
    d = float(sys.argv[1]) if len(sys.argv) > 1 else POST_FROM_WALL
    m = build(d)
    out = f"pedestal_D{int(round(d))}.stl"
    write_stl(m, out)
    bb = m.bounding_box()
    print(f"{out}: {m.num_tri()} tris, {m.volume()/1000:.1f} cm^3, "
          f"bbox {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm, "
          f"components {len(m.decompose())}, genus {m.genus()}")
