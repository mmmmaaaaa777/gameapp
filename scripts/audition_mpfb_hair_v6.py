"""Render the bundled MPFB hairstyles on the approved v3 anatomical bases.

The contact sheets produced by this script are selection evidence for the v6
characters.  All inputs are bundled CC0 MPFB system assets; nothing is fetched
at build or game runtime.

Run with the normal Blender profile so the MPFB extension is available::

    & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" `
      --background --python scripts\\audition_mpfb_hair_v6.py
"""

from __future__ import annotations

import argparse
import importlib
import sys
from dataclasses import dataclass
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_ROOT / "art-source" / "characters" / "work" / "v3"
OUTPUT_DIR = (
    PROJECT_ROOT / "docs" / "character-concepts" / "model-history" / "v6.0-hair-audition"
)


@dataclass(frozen=True)
class Profile:
    key: str
    base_file: str
    assets: tuple[str, ...]
    color: tuple[float, float, float, float]


PROFILES = (
    Profile(
        "male",
        "initial-male-base.blend",
        ("short01.mhclo", "short02.mhclo", "short03.mhclo", "short04.mhclo"),
        (0.035, 0.022, 0.016, 1.0),
    ),
    Profile(
        "female",
        "initial-female-base.blend",
        ("bob01.mhclo", "bob02.mhclo", "short03.mhclo", "short04.mhclo"),
        (0.095, 0.027, 0.020, 1.0),
    ),
)


def mpfb_symbol(module_suffix: str, symbol: str):
    for module_name in tuple(sys.modules):
        if module_name.endswith(module_suffix):
            module = importlib.import_module(module_name)
            if hasattr(module, symbol):
                return getattr(module, symbol)
    raise RuntimeError(
        f"MPFB is not loaded ({module_suffix}); run Blender with normal preferences"
    )


HumanService = mpfb_symbol("mpfb.services.humanservice", "HumanService")
AssetService = mpfb_symbol("mpfb.services.assetservice", "AssetService")


def find_body() -> bpy.types.Object:
    candidates = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and len(obj.data.vertices) > 10_000
    ]
    if not candidates:
        raise RuntimeError("MPFB body is missing")
    return max(candidates, key=lambda obj: len(obj.data.vertices))


def add_hair(body: bpy.types.Object, asset_name: str) -> bpy.types.Object:
    asset_path = AssetService.find_asset_absolute_path(asset_name, asset_subdir="hair")
    if asset_path is None or not Path(asset_path).is_file():
        raise FileNotFoundError(f"MPFB hair asset is missing: {asset_name}")
    hair = HumanService.add_mhclo_asset(
        str(asset_path),
        body,
        asset_type="Hair",
        subdiv_levels=1,
        material_type="GAMEENGINE",
        set_up_rigging=True,
        interpolate_weights=True,
        import_subrig=True,
        import_weights=True,
    )
    hair.name = f"Audition_{Path(asset_name).stem}"
    return hair


def recolor_hair(hair: bpy.types.Object, color: tuple[float, float, float, float]) -> None:
    for slot in hair.material_slots:
        material = slot.material
        if material is None:
            continue
        material.diffuse_color = color
        material.use_nodes = True
        principled = next(
            (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"),
            None,
        )
        if principled is None:
            continue
        base = principled.inputs.get("Base Color")
        if base is not None:
            for link in tuple(base.links):
                material.node_tree.links.remove(link)
            base.default_value = color
        principled.inputs["Roughness"].default_value = 0.63


def bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    return (
        Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
        Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
    )


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_views(profile: Profile, asset_name: str, body: bpy.types.Object, hair: bpy.types.Object) -> None:
    scene = bpy.context.scene
    # Some legacy MHClO files retain an authoring-space bounding box even
    # though their fitted vertices are correctly placed by the MPFB modifier.
    # Frame from the known-good anatomical body so those stale bounds cannot
    # push the camera away from the character.
    minimum, maximum = bounds([body])
    height = maximum.z - minimum.z
    center = (minimum + maximum) * 0.5
    target = Vector((center.x, center.y, minimum.z + height * 0.79))

    world = scene.world or bpy.data.worlds.new("Hair_Audition_World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.035, 0.040, 0.050, 1.0)
    background.inputs["Strength"].default_value = 0.40

    camera_data = bpy.data.cameras.new("Hair_Audition_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = height * 0.43
    camera = bpy.data.objects.new("Hair_Audition_Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera

    lights: list[bpy.types.Object] = []
    for name, energy, size, color in (
        ("Key", 700.0, 2.5, (1.0, 0.89, 0.80)),
        ("Fill", 420.0, 2.0, (0.75, 0.84, 1.0)),
        ("Rim", 620.0, 2.2, (0.82, 0.96, 0.92)),
    ):
        data = bpy.data.lights.new(f"Hair_Audition_{name}", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = color
        light = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(light)
        lights.append(light)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.35

    distance = height * 2.3
    views = {
        "front": Vector((center.x, center.y - distance, target.z)),
        "right": Vector((center.x - distance, center.y, target.z)),
        "back": Vector((center.x, center.y + distance, target.z)),
    }
    for view_name, position in views.items():
        camera.location = position
        look_at(camera, target)
        view_direction = (position - target).normalized()
        screen_right = (-view_direction).cross(Vector((0.0, 0.0, 1.0))).normalized()
        key, fill, rim = lights
        key.location = target + view_direction * 1.6 - screen_right * 0.8 + Vector((0, 0, 1.0))
        fill.location = target + view_direction * 1.2 + screen_right * 0.9 + Vector((0, 0, 0.3))
        rim.location = target - view_direction * 1.4 + Vector((0, 0, 0.8))
        for light in lights:
            look_at(light, target)
        output_path = OUTPUT_DIR / f"{profile.key}-{Path(asset_name).stem}-{view_name}.png"
        scene.render.filepath = str(output_path)
        bpy.ops.render.render(write_still=True)
        print(f"HAIR_AUDITION {profile.key} {asset_name} {view_name} {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--character", choices=("male", "female", "all"), default="all")
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parser.parse_args(script_args)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    selected = PROFILES if args.character == "all" else tuple(
        profile for profile in PROFILES if profile.key == args.character
    )
    for profile in selected:
        for asset_name in profile.assets:
            bpy.ops.wm.open_mainfile(filepath=str(BASE_DIR / profile.base_file))
            body = find_body()
            hair = add_hair(body, asset_name)
            recolor_hair(hair, profile.color)
            render_views(profile, asset_name, body, hair)


if __name__ == "__main__":
    main()
