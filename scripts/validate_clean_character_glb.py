"""Re-import production GLBs and validate their game-facing contents.

This intentionally starts from an empty Blender file.  It verifies what the
game receives rather than trusting the source .blend, and writes one proof
render per character from the imported GLB.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_blender_import_rig_helper(obj: bpy.types.Object) -> bool:
    """Match only the editor helper created by Blender's glTF rig importer.

    This object is absent from the glTF mesh-node import log and is generated
    locally to display bones. It has no parent, material, weights or armature.
    Three.js never receives it.
    """

    return (
        obj.type == "MESH"
        and obj.name == "Icosphere"
        and obj.parent is None
        and len(obj.data.materials) == 0
        and len(obj.vertex_groups) == 0
        and len(obj.modifiers) == 0
    )


def validate_import(path: Path) -> dict[str, object]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    bpy.context.view_layer.update()

    imported_helpers = [
        obj for obj in bpy.context.scene.objects if is_blender_import_rig_helper(obj)
    ]
    for helper in imported_helpers:
        helper.hide_render = True
    meshes = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and not is_blender_import_rig_helper(obj)
    ]
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if not meshes:
        raise RuntimeError(f"No meshes imported from {path}")
    if len(armatures) != 1:
        raise RuntimeError(f"Expected one armature in {path}, found {len(armatures)}")
    armature = armatures[0]
    # Root is an authored member of the MPFB game rig, even though it does not
    # directly deform vertices.  Older rejected exports also caused Blender to
    # synthesize an extra `neutral_bone` for zero-weight vertices.  Requiring
    # the exact 53 authored bones catches that exporter artifact without
    # incorrectly discarding the real Root bone.
    game_bones = list(armature.data.bones)
    if len(game_bones) != 53:
        raise RuntimeError(
            f"Expected 53 game bones in {path}, found {len(game_bones)} "
            f"({len(armature.data.bones)} total imported bones)"
        )

    missing_uv = [obj.name for obj in meshes if obj.data.polygons and not obj.data.uv_layers]
    if missing_uv:
        raise RuntimeError("Meshes without UV maps: " + ", ".join(missing_uv))

    unrigged = []
    max_influences = 0
    non_finite_vertices = []
    for obj in meshes:
        modifiers = [modifier for modifier in obj.modifiers if modifier.type == "ARMATURE"]
        if not any(modifier.object == armature for modifier in modifiers):
            unrigged.append(obj.name)
        for vertex in obj.data.vertices:
            max_influences = max(max_influences, len(vertex.groups))
            world = obj.matrix_world @ vertex.co
            if not all(math.isfinite(value) for value in world):
                non_finite_vertices.append(f"{obj.name}:{vertex.index}")
    if unrigged:
        raise RuntimeError("Meshes without imported game rig: " + ", ".join(unrigged))
    if max_influences > 4:
        raise RuntimeError(f"GLB contains {max_influences} joint influences on one vertex")
    if non_finite_vertices:
        raise RuntimeError("Non-finite vertices: " + ", ".join(non_finite_vertices[:8]))

    external_images = []
    image_nodes = 0
    for image in bpy.data.images:
        if image.type == "RENDER_RESULT":
            continue
        if image.filepath and image.packed_file is None:
            external_images.append(image.filepath)
    for material in bpy.data.materials:
        if material.use_nodes:
            image_nodes += sum(
                1 for node in material.node_tree.nodes if node.type == "TEX_IMAGE" and node.image
            )
    if external_images:
        raise RuntimeError("GLB depends on external images: " + ", ".join(external_images))
    if image_nodes == 0:
        raise RuntimeError(f"No embedded material textures found in {path}")

    required_actions = {"Idle", "Run", "Attack", "Dodge"}
    imported_actions = {action.name for action in bpy.data.actions}
    missing_actions = required_actions - imported_actions
    if missing_actions:
        raise RuntimeError(
            f"Missing embedded gameplay actions in {path}: {sorted(missing_actions)}"
        )

    bounds = [
        obj.matrix_world @ Vector(corner)
        for obj in meshes
        for corner in obj.bound_box
    ]
    minimum = Vector((
        min(point.x for point in bounds),
        min(point.y for point in bounds),
        min(point.z for point in bounds),
    ))
    maximum = Vector((
        max(point.x for point in bounds),
        max(point.y for point in bounds),
        max(point.z for point in bounds),
    ))
    size = maximum - minimum
    if size.z <= 0.5 or size.z >= 3.0:
        raise RuntimeError(f"Unexpected imported height {size.z:.4f}m in {path}")

    return {
        "file": path.as_posix(),
        "bytes": path.stat().st_size,
        "meshes": len(meshes),
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "triangles": sum(
            sum(max(0, len(polygon.vertices) - 2) for polygon in obj.data.polygons)
            for obj in meshes
        ),
        "materials": len(bpy.data.materials),
        "embedded_images": len([image for image in bpy.data.images if image.type != "RENDER_RESULT"]),
        "image_texture_nodes": image_nodes,
        "external_images": 0,
        "animation_clips": sorted(imported_actions),
        "armatures": 1,
        "bones": len(game_bones),
        "authored_root_bone": "Root" in armature.data.bones,
        "max_joint_influences": max_influences,
        "uv_meshes": len(meshes),
        "blender_import_helpers_excluded": [obj.name for obj in imported_helpers],
        "bounds_m": {
            "min": [round(value, 6) for value in minimum],
            "max": [round(value, 6) for value in maximum],
            "size": [round(value, 6) for value in size],
        },
    }


def render_proof(output_path: Path) -> None:
    meshes = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and not is_blender_import_rig_helper(obj)
    ]
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    minimum = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    maximum = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    size = maximum - minimum
    center = (minimum + maximum) * 0.5

    world = bpy.data.worlds.new("GLB_Proof_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.025, 0.03, 0.04, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.42

    camera_data = bpy.data.cameras.new("GLB_Proof_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = size.z * 1.10
    camera = bpy.data.objects.new("GLB_Proof_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    camera.location = center + Vector((-size.z * 1.9, -size.z * 2.2, size.z * 0.08))
    look_at(camera, center)

    for name, energy, location, color, light_size in (
        ("Key", 720, (-2.4, -3.2, 3.8), (1.0, 0.90, 0.82), 3.0),
        ("Fill", 360, (2.6, -1.2, 2.2), (0.72, 0.84, 1.0), 2.7),
        ("Rim", 600, (0.7, 3.0, 3.3), (0.80, 0.96, 0.92), 2.5),
    ):
        light_data = bpy.data.lights.new(f"GLB_Proof_{name}", "AREA")
        light_data.energy = energy
        light_data.color = color
        light_data.shape = "DISK"
        light_data.size = light_size
        light = bpy.data.objects.new(light_data.name, light_data)
        bpy.context.scene.collection.objects.link(light)
        light.location = center + Vector(location)
        look_at(light, center)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.5
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--male", required=True)
    parser.add_argument("--female", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--render-dir", required=True)
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parser.parse_args(script_args)

    output_path = Path(args.output).resolve()
    render_dir = Path(args.render_dir).resolve()
    results: dict[str, object] = {
        "validator": "scripts/validate_clean_character_glb.py",
        "status": "passed",
        "characters": {},
    }
    for key, value in (("male", args.male), ("female", args.female)):
        path = Path(value).resolve()
        result = validate_import(path)
        proof_path = render_dir / f"{path.stem}-glb-proof.png"
        render_proof(proof_path)
        result["proof_render"] = proof_path.as_posix()
        results["characters"][key] = result

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("GLB_VALIDATION " + json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
