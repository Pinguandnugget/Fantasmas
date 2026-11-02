#!/usr/bin/env python3
"""
Renderizador de verificacion (software, ortografico, con textura).

 A) render_bbmodel(): dibuja el .bbmodel TAL COMO LO MUESTRA BLOCKBENCH
    (caras UV guardadas en el propio .bbmodel, from/to, grupos, pivotes, animacion).
 B) render_geo():     dibuja un .geo.json (+ animacion .json) siguiendo la logica de GeckoLib 4
    (origin.x = -(origin.x+size.x), pivot.x invertido, rotacion [-x,-y,z], UV de caja Bedrock...).

Si A y B dan la misma imagen, el .geo.json exportado reproduce el .bbmodel.
"""
import json, math
import numpy as np
from PIL import Image

# ---------------------------------------------------------------- matematicas
def T(v):
    m = np.eye(4); m[:3, 3] = v; return m

def R(rx, ry, rz):
    """Rz * Ry * Rx (grados)."""
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0, 0], [0, cx, -sx, 0], [0, sx, cx, 0], [0, 0, 0, 1]])
    Ry = np.array([[cy, 0, sy, 0], [0, 1, 0, 0], [-sy, 0, cy, 0], [0, 0, 0, 1]])
    Rz = np.array([[cz, -sz, 0, 0], [sz, cz, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    return Rz @ Ry @ Rx

def about(pivot, rot_matrix, offset=(0, 0, 0)):
    return T(offset) @ T(pivot) @ rot_matrix @ T(-np.array(pivot, float))

# ---------------------------------------------------------------- caras de un cubo
def cube_faces(x0, y0, z0, x1, y1, z1):
    """Esquinas (tl, tr, bl, br) vistas desde fuera, convencion de modelos de bloque de Minecraft."""
    return {
        "north": [(x1, y1, z0), (x0, y1, z0), (x1, y0, z0), (x0, y0, z0)],
        "south": [(x0, y1, z1), (x1, y1, z1), (x0, y0, z1), (x1, y0, z1)],
        "east":  [(x1, y1, z1), (x1, y1, z0), (x1, y0, z1), (x1, y0, z0)],
        "west":  [(x0, y1, z0), (x0, y1, z1), (x0, y0, z0), (x0, y0, z1)],
        "up":    [(x0, y1, z0), (x1, y1, z0), (x0, y1, z1), (x1, y1, z1)],
        "down":  [(x0, y0, z1), (x1, y0, z1), (x0, y0, z0), (x1, y0, z0)],
    }

def box_uv_rects(u, v, w, h, d, mirror):
    f = {"north": [u + d, v + d, u + d + w, v + d + h], "east": [u, v + d, u + d, v + d + h],
         "south": [u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h], "west": [u + d + w, v + d, u + 2 * d + w, v + d + h],
         "up": [u + d + w, v + d, u + d, v], "down": [u + d + 2 * w, v, u + d + w, v + d]}
    if mirror:
        f["east"], f["west"] = f["west"], f["east"]
        f = {k: [r[2], r[1], r[0], r[3]] for k, r in f.items()}
    return f

def area_of(face, w, h, d):
    return {"north": w * h, "south": w * h, "east": d * h, "west": d * h, "up": w * d, "down": w * d}[face]

# ---------------------------------------------------------------- animacion
def sample(chan, t):
    """chan: lista [(time, [x,y,z])] ordenada. Lineal, mantiene primer/ultimo valor."""
    if not chan: return np.zeros(3)
    if t <= chan[0][0]: return np.array(chan[0][1], float)
    if t >= chan[-1][0]: return np.array(chan[-1][1], float)
    for (t0, a), (t1, b) in zip(chan, chan[1:]):
        if t0 <= t <= t1:
            k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return np.array(a, float) * (1 - k) + np.array(b, float) * k

def pose_from_bbmodel(bb, anim_name, t):
    u2n = {g["uuid"]: g["name"] for g in bb["groups"]}
    pose = {}
    if not anim_name: return pose
    a = next(x for x in bb["animations"] if x["name"] == anim_name)
    for uuid, an in a["animators"].items():
        ch = {}
        for kf in an.get("keyframes", []):
            dp = kf["data_points"][0]
            ch.setdefault(kf["channel"], []).append((float(kf["time"]), [float(dp["x"]), float(dp["y"]), float(dp["z"])]))
        pose[u2n[uuid]] = {k: sorted(v, key=lambda p: p[0]) for k, v in ch.items()}
    return {n: {k: sample(v, t) for k, v in c.items()} for n, c in pose.items()}

def pose_from_json(animdoc, anim_name, t):
    if not anim_name: return {}
    a = animdoc["animations"][anim_name]
    out = {}
    for bone, chans in a["bones"].items():
        out[bone] = {}
        for ch, kfs in chans.items():
            pts = sorted(((float(k), v) for k, v in kfs.items()), key=lambda p: p[0])
            out[bone][ch] = sample(pts, t)
    return out

def anim_transform(p):
    """Blockbench/GeckoLib: x de posicion y x,y de rotacion se invierten al mostrarse."""
    pos = np.zeros(3); rot = np.zeros(3)
    if "position" in p: v = p["position"]; pos = np.array([-v[0], v[1], v[2]])
    if "rotation" in p: v = p["rotation"]; rot = np.array([-v[0], -v[1], v[2]])
    return pos, rot

# ---------------------------------------------------------------- quads (A y B)
def quads_from_bbmodel(bb, pose):
    groups = {g["uuid"]: g for g in bb["groups"]}
    elements = {e["uuid"]: e for e in bb["elements"]}
    res = bb["resolution"]; quads = []

    def walk(node, parent_m):
        g = groups[node["uuid"]]
        pos, arot = anim_transform(pose.get(g["name"], {}))
        rot = np.array(g.get("rotation", [0, 0, 0]), float) + arot
        m = parent_m @ about(g["origin"], R(*rot), pos)
        for ch in node["children"]:
            if isinstance(ch, str):
                e = elements[ch]
                er = e.get("rotation", [0, 0, 0])
                me = m @ about(e["origin"], R(*er))
                fc = cube_faces(*e["from"], *e["to"])
                sz = [e["to"][i] - e["from"][i] for i in range(3)]
                for face, corners in fc.items():
                    if area_of(face, *sz[:2], sz[2]) == 0: continue
                    uv = e["faces"][face]["uv"]
                    pts = [(me @ np.array([*c, 1.0]))[:3] for c in corners]
                    quads.append((pts, uv, res["width"], res["height"]))
            else:
                walk(ch, m)
    for n in bb["outliner"]:
        walk(n, np.eye(4))
    return quads

def quads_from_geo(geo, pose):
    g = geo["minecraft:geometry"][0]
    tw, th = g["description"]["texture_width"], g["description"]["texture_height"]
    bones = {b["name"]: b for b in g["bones"]}
    children = {}
    for b in g["bones"]:
        children.setdefault(b.get("parent"), []).append(b["name"])
    quads = []

    def walk(name, parent_m):
        b = bones[name]
        pos, arot = anim_transform(pose.get(name, {}))
        brot = np.array(b.get("rotation", [0, 0, 0]), float) * [-1, -1, 1]
        pivot = np.array(b["pivot"], float) * [-1, 1, 1]
        m = parent_m @ about(pivot, R(*(brot + arot)), pos)
        for c in b.get("cubes", []):
            size = c["size"]; o = c["origin"]
            x0 = -(o[0] + size[0]); y0 = o[1]; z0 = o[2]       # GeckoLib: origin.x = -(origin.x + size.x)
            me = m
            if "rotation" in c:
                cp = np.array(c["pivot"], float) * [-1, 1, 1]
                cr = np.array(c["rotation"], float) * [-1, -1, 1]
                me = m @ about(cp, R(*cr))
            infl = c.get("inflate", 0)
            fc = cube_faces(x0 - infl, y0 - infl, z0 - infl, x0 + size[0] + infl, y0 + size[1] + infl, z0 + size[2] + infl)
            rects = box_uv_rects(*c["uv"], size[0], size[1], size[2], c.get("mirror", False))
            for face, corners in fc.items():
                if area_of(face, *size) == 0: continue
                pts = [(me @ np.array([*cc, 1.0]))[:3] for cc in corners]
                quads.append((pts, rects[face], tw, th))
        for ch in children.get(name, []):
            walk(ch, m)
    for r in children.get(None, []):
        walk(r, np.eye(4))
    return quads

# ---------------------------------------------------------------- rasterizador
def render(quads, tex, yaw=0, pitch=15, size=(360, 360), scale=22, center=(-2, 5.5, 2), bg=(70, 74, 92, 255)):
    tex = np.asarray(tex.convert("RGBA")); TH, TW = tex.shape[:2]
    W, H = size
    img = np.zeros((H, W, 4), np.uint8); img[:] = bg
    zbuf = np.full((H, W), -1e9)
    th, ph = math.radians(yaw), math.radians(pitch)
    cam = np.array([math.sin(th) * math.cos(ph), math.sin(ph), -math.cos(th) * math.cos(ph)])  # camara (yaw 0 = delante, -Z)
    f = -cam / np.linalg.norm(cam)
    right = np.cross(f, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, f)
    c = np.array(center, float)

    def proj(p):
        d = np.array(p) - c
        return np.array([W / 2 + scale * d @ right, H / 2 - scale * d @ up]), d @ cam   # profundidad hacia la camara

    for pts, uv, qw, qh in quads:
        u1, v1, u2, v2 = uv
        fu = lambda u: u / qw * TW
        fv = lambda v: v / qh * TH
        corner_uv = [(fu(u1), fv(v1)), (fu(u2), fv(v1)), (fu(u1), fv(v2)), (fu(u2), fv(v2))]
        P = [proj(p) for p in pts]
        for tri in ((0, 1, 2), (1, 3, 2)):
            (a, za), (b, zb), (cc, zc) = P[tri[0]], P[tri[1]], P[tri[2]]
            ua, ub, uc = (np.array(corner_uv[i]) for i in tri)
            mnx, mxx = int(max(0, math.floor(min(a[0], b[0], cc[0])))), int(min(W - 1, math.ceil(max(a[0], b[0], cc[0]))))
            mny, mxy = int(max(0, math.floor(min(a[1], b[1], cc[1])))), int(min(H - 1, math.ceil(max(a[1], b[1], cc[1]))))
            den = (b[1] - cc[1]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[1] - cc[1])
            if abs(den) < 1e-9: continue
            if mxx < mnx or mxy < mny: continue
            xs, ys = np.meshgrid(np.arange(mnx, mxx + 1) + 0.5, np.arange(mny, mxy + 1) + 0.5)
            l1 = ((b[1] - cc[1]) * (xs - cc[0]) + (cc[0] - b[0]) * (ys - cc[1])) / den
            l2 = ((cc[1] - a[1]) * (xs - cc[0]) + (a[0] - cc[0]) * (ys - cc[1])) / den
            l3 = 1 - l1 - l2
            inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
            z = l1 * za + l2 * zb + l3 * zc
            tx = np.clip((l1 * ua[0] + l2 * ub[0] + l3 * uc[0]).astype(int), 0, TW - 1)
            ty = np.clip((l1 * ua[1] + l2 * ub[1] + l3 * uc[1]).astype(int), 0, TH - 1)
            texel = tex[ty, tx]
            sub = zbuf[mny:mxy + 1, mnx:mxx + 1]
            ok = inside & (z > sub) & (texel[..., 3] >= 128)
            sub[ok] = z[ok]
            img[mny:mxy + 1, mnx:mxx + 1][ok] = texel[ok]
    return Image.fromarray(img)
