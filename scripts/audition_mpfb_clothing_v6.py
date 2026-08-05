"""Render bundled MPFB clothing candidates for the clean v6 reconstruction.

These previews document why a fitted topology was selected before the guild
uniform panels and trim are authored on top of it.
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
    PROJECT_ROOT / "docs" / "character-concepts" / "model-history" / "v6.1-clothing-audition"
)


@dataclass(frozen=True)
class Profile:
    key: str
    base_file: str
    assets: tuple[str, ...]


PROFILES = (
    Profile(
        "male",
        "initial-male-base.blend",
        tuple(f"male_casualsuit{index:02d}.mhclo" for index in range(1, 7))
        + ("male_worksuit01.mhclo",),
    ),
    Profile(
        "female",
        "initial-female-base.blend",
        (
            "female_casualsuit01.mhclo",
            "female_casualsuit02.mhclo",
            "female_sportsuit01.mhclo",
            "female_elegantsuit01.mhclo",
        ),
    ),
)


def mpfb_symbol(module_suffix: str, symbol: str):
    for module_name in tuple(sys.modules):
        if module_name.endswith(module_suffix):
            module = importlib.import_module(module_name)
            if hasattr(module, symbol):
                return getattr(module, symbol)
    raise RuntimeError(f"MPFB is not loaded ({module_suffix})")


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


def add_clothing(body: bpy.types.Object, asset_name: str) -> bpy.types.Object:
    asset_path = AssetService.find_asset_absolute_path(asset_name, asset_subdir="clothes")
    if asset_path is None or not Path(asset_path).is_file():
        raise FileNotFoundError(f"MPFB clothing asset is missing: {asset_name}")
    clothing = HumanService.add_mhclo_asset(
        str(asset_path),
        body,
        asset_type="Clothes",
        subdiv_levels=1,
        material_type="GAMEENGINE",
        set_up_rigging=True,
        interpolate_weights=True,
        import_subrig=True,
        import_weights=True,
    )
    clothing.name = f"Audition_{Path(asset_name).stem}"
    return clothing


def bounds(body: bpy.types.Object) -> tuple[Vector, Vector]:
    points = [body.matrix_world @ Vector(corner) for corner in body.bound_box]
    return (
        Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
        Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
    )


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def simple_material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = color
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = 0.72
    return material


def replace_materials(clothing: bpy.types.Object) -> None:
    # Neutral teal makes silhouette and construction seams readable without
    # judging a candidate by its bundled diffuse artwork.
    material = simple_material("Audition_Guild_Teal", (0.025, 0.080, 0.085, 1.0))
    if not clothing.data.materials:
        clothing.data.materials.append(material)
    else:
        for index in range(len(clothing.data.materials)):
            clothing.data.materials[index] = material


def render_views(
    profile: Profile,
    asset_name: str,
    body: bpy.types.Object,
    *,
    front_only: bool = False,
) -> None:
    scene = bpy.context.scene
    minimum, maximum = bounds(body)
    height = maximum.z - minimum.z
    center = (minimum + maximum) * 0.5
    target = Vector((center.x, center.y, minimum.z + height * 0.50))

    world = scene.world or bpy.data.worlds.new("Clothing_Audition_World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.035, 0.040, 0.050, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.38

    camera_data = bpy.data.cameras.new("Clothing_Audition_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = height * 1.08
    camera = bpy.data.objects.new("Clothing_Audition_Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera

    lights: list[bpy.types.Object] = []
    for name, energy, size, color in (
        ("Key", 760.0, 3.4, (1.0, 0.89, 0.80)),
        ("Fill", 410.0, 3.0, (0.75, 0.84, 1.0)),
        ("Rim", 650.0, 3.0, (0.82, 0.96, 0.92)),
    ):
        data = bpy.data.lights.new(f"Clothing_Audition_{name}", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = color
        light = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(light)
        lights.append(light)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 384
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.40

    distance = height * 3.0
    views = (
        ("front", Vector((center.x, center.y - distance, target.z))),
        ("right", Vector((center.x - distance, center.y, target.z))),
        ("back", Vector((center.x, center.y + distance, target.z))),
    )
    if front_only:
        views = views[:1]
    for view_name, position in views:
        camera.location = position
        look_at(camera, target)
        view_direction = (position - target).normalized()
        screen_right = (-view_direction).cross(Vector((0.0, 0.0, 1.0))).normalized()
        key, fill, rim = lights
        key.location = target + view_direction * 2.2 - screen_right * 1.2 + Vector((0, 0, 1.5))
        fill.location = target + view_direction * 1.8 + screen_right * 1.3 + Vector((0, 0, 0.5))
        rim.location = target - view_direction * 2.0 + Vector((0, 0, 1.2))
        for light in lights:
            look_at(light, target)
        output_path = OUTPUT_DIR / f"{profile.key}-{Path(asset_name).stem}-{view_name}.png"
        scene.render.filepath = str(output_path)
        bpy.ops.render.render(write_still=True)
        print(f"CLOTHING_AUDITION {profile.key} {asset_name} {view_name} {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--character", choices=("male", "female", "all"), default="all")
    parser.add_argument("--asset", default=None)
    parser.add_argument("--front-only", action="store_true")
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parser.parse_args(script_args)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    selected = PROFILES if args.character == "all" else tuple(
        profile for profile in PROFILES if profile.key == args.character
    )
    for profile in selected:
        assets = profile.assets
        if args.asset is not None:
            assets = tuple(asset for asset in assets if Path(asset).stem == args.asset)
            if not assets:
                # Also allow a direct bundled asset name such as ``shoes05``
                # so footwear can be evaluated with the same reproducible rig.
                assets = (f"{args.asset}.mhclo",)
        for asset_name in assets:
            bpy.ops.wm.open_mainfile(filepath=str(BASE_DIR / profile.base_file))
            body = find_body()
            clothing = add_clothing(body, asset_name)
            replace_materials(clothing)
            render_views(profile, asset_name, body, front_only=args.front_only)


if __name__ == "__main__":
    main()
