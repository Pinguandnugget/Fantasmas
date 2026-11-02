#!/usr/bin/env python3
"""
bb2geo.py - Convierte los .bbmodel de los fantasmas (formato Blockbench "modded_entity")
a los archivos que GeckoLib 4 espera:

    assets/fantasmas/geo/fantasma_<color>.geo.json                 (Bedrock geometry 1.12.0)
    assets/fantasmas/animations/fantasma_<color>.animation.json    (Bedrock animation 1.8.0)

Se replica exactamente lo que hace el exportador "Bedrock/GeckoLib" de Blockbench:
  * NO se invierte Y ni Z (eso era el error del geo.json anterior: estilo Java ModelPart).
  * X se espeja:  cube.origin.x = -(from.x + size.x),  pivot.x = -origin.x
  * rotacion:     [-rx, -ry, rz]
  * UV de caja:   uv = uv_offset, con la resolucion del proyecto (32x32) como texture_width/height
                  (la textura es de 64x64: el UV NO esta en pixeles de textura, esta en unidades de proyecto)
  * Los keyframes de animacion se copian tal cual (Blockbench guarda los valores ya en convencion Bedrock).
"""
import json, sys, os, copy

FLY_SOURCE = "blanco"          # fantasma cuya animacion "volando" se reutiliza
ANIM_NS = "animation.fantasmas."


def fmt(v):
    """-0.0 -> 0, 2.0 -> 2 (JSON limpio)."""
    v = round(float(v), 5)
    if v == 0:
        return 0
    return int(v) if v == int(v) else v


def vec(a, mul=(1, 1, 1)):
    return [fmt(a[i] * mul[i]) for i in range(3)]


def build_tree(bb):
    groups = {g["uuid"]: g for g in bb["groups"]}
    elements = {e["uuid"]: e for e in bb["elements"]}
    bones = []   # en orden de outliner (padres antes que hijos)

    def walk(node, parent):
        g = groups[node["uuid"]]
        entry = {"group": g, "parent": parent, "cubes": []}
        bones.append(entry)
        for ch in node["children"]:
            if isinstance(ch, str):
                entry["cubes"].append(elements[ch])
            else:
                walk(ch, g["name"])

    for n in bb["outliner"]:
        walk(n, None)
    return bones


def cube_json(e):
    size = [e["to"][i] - e["from"][i] for i in range(3)]
    c = {
        "origin": [fmt(-(e["from"][0] + size[0])), fmt(e["from"][1]), fmt(e["from"][2])],
        "size": [fmt(s) for s in size],
        "uv": [fmt(x) for x in e.get("uv_offset", [0, 0])],
    }
    if e.get("inflate"):
        c["inflate"] = fmt(e["inflate"])
    if e.get("mirror_uv"):
        c["mirror"] = True
    rot = e.get("rotation", [0, 0, 0])
    if any(abs(r) > 1e-9 for r in rot):
        c["pivot"] = vec(e["origin"], (-1, 1, 1))
        c["rotation"] = vec(rot, (-1, -1, 1))
    return c


def bone_json(entry):
    g = entry["group"]
    b = {"name": g["name"], "pivot": vec(g["origin"], (-1, 1, 1))}
    if entry["parent"]:
        b["parent"] = entry["parent"]
    rot = g.get("rotation", [0, 0, 0])
    if any(abs(r) > 1e-9 for r in rot):
        b["rotation"] = vec(rot, (-1, -1, 1))
    if entry["cubes"]:
        b["cubes"] = [cube_json(e) for e in entry["cubes"]]
    return b


def build_geo(bb, color, add_root_todo=False):
    bones = [bone_json(e) for e in build_tree(bb)]
    if add_root_todo:
        # Fantasmas rojo/negro: sus 3 raices (cuerpo + 2 brazos) no tienen padre comun.
        # Se anade el hueso vacio "todo" (identico al del blanco/amarillo) para que
        # la animacion de vuelo sea reutilizable sin tocar la geometria.
        roots = [b for b in bones if "parent" not in b]
        for b in roots:
            b["parent"] = "todo"
        bones.insert(0, {"name": "todo", "pivot": [0, 0, 0]})
    res = bb["resolution"]
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": f"geometry.fantasmas.{color}",
                # resolucion del PROYECTO (32x32); la textura png es 64x64 y se escala sola
                "texture_width": res["width"],
                "texture_height": res["height"],
                "visible_bounds_width": 4,
                "visible_bounds_height": 4,
                "visible_bounds_offset": [0, 1, 0],
            },
            "bones": bones,
        }],
    }


def tkey(t):
    t = round(float(t), 5)
    return "0" if t == 0 else repr(int(t)) if t == int(t) else repr(t)


def build_animation(anim, uuid_to_name):
    out = {"loop": anim["loop"] == "loop" or anim["loop"] is True,
           "animation_length": fmt(anim["length"]), "bones": {}}
    if anim["loop"] == "hold":
        out["loop"] = "hold_on_last_frame"
    for uuid, an in anim["animators"].items():
        kfs = an.get("keyframes", [])
        if not kfs:
            continue
        name = uuid_to_name[uuid]
        chans = {}
        for kf in kfs:
            assert len(kf["data_points"]) == 1 and kf["interpolation"] == "linear", kf
            dp = kf["data_points"][0]
            chans.setdefault(kf["channel"], []).append(
                (float(kf["time"]), [fmt(dp["x"]), fmt(dp["y"]), fmt(dp["z"])]))
        bd = {}
        for ch in ("rotation", "position", "scale"):
            if ch in chans:
                pts = sorted(chans[ch], key=lambda p: p[0])
                times = [round(p[0], 5) for p in pts]
                assert len(set(times)) == len(times), (name, ch, "keyframes duplicados")
                bd[ch] = {tkey(t): v for t, (_, v) in zip(times, pts)}
        out["bones"][name] = bd
    return out


def anim_name(bb_name):
    return ANIM_NS + bb_name


def convert_all(bb_dir, out_dir):
    colors = ["blanco", "amarillo", "rojo", "negro"]
    bbs = {c: json.load(open(f"{bb_dir}/{c}.bbmodel.json")) for c in colors}
    os.makedirs(f"{out_dir}/geo", exist_ok=True)
    os.makedirs(f"{out_dir}/animations", exist_ok=True)

    # animacion de vuelo compartida (blanco == amarillo, se verifica)
    def anims_of(c):
        bb = bbs[c]
        u2n = {g["uuid"]: g["name"] for g in bb["groups"]}
        return {a["name"]: build_animation(a, u2n) for a in bb["animations"]}

    A = {c: anims_of(c) for c in colors}
    assert A["blanco"]["volando"] == A["amarillo"]["volando"], "volando blanco != amarillo"
    fly = A[FLY_SOURCE]["volando"]

    for c in colors:
        has_todo = any(g["name"] == "todo" for g in bbs[c]["groups"])
        geo = build_geo(bbs[c], c, add_root_todo=not has_todo)
        json.dump(geo, open(f"{out_dir}/geo/fantasma_{c}.geo.json", "w"), indent=2)

        anims = {}
        anims[anim_name("golpear")] = A[c]["golpear"]            # ataque ORIGINAL de cada fantasma
        anims[anim_name("volando")] = copy.deepcopy(fly)         # vuelo compartido
        # La clase GhostEntity (jar 0.2.0) reproduce "animation.fantasmas.prueba": se deja
        # como alias del vuelo para que el fantasma se anime sin tocar Java.
        anims[anim_name("prueba")] = copy.deepcopy(fly)
        json.dump({"format_version": "1.8.0", "animations": anims},
                  open(f"{out_dir}/animations/fantasma_{c}.animation.json", "w"), indent=2)

    return bbs


if __name__ == "__main__":
    convert_all(sys.argv[1], sys.argv[2])
    print("ok")
