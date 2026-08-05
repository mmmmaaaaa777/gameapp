"""Smoke-test the exported v4 character GLBs by importing them into Blender."""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

import bpy


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "public" / "models" / "characters"
MODEL_PATHS = (
    MODEL_DIR / "initial-male-v4.glb",
    MODEL_DIR / "initial-female-v4.glb",
)


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision")
    args = parser.parse_args(argv)
    if args.revision and not re.fullmatch(r"v4\.\d+", args.revision):
        parser.error("--revision must use the form v4.<number>, for example v4.14")
    return args


def model_paths(revision: str | None) -> tuple[Path, Path]:
    directory = MODEL_DIR if revision is None else MODEL_DIR / "history" / revision
    return (
        directory / "initial-male-v4.glb",
        directory / "initial-female-v4.glb",
    )


def validate_model(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))

    meshes = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH"
        and all(collection.name != "glTF_not_exported" for collection in obj.users_collection)
    ]
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if len(meshes) != 1 or len(armatures) != 1:
        raise RuntimeError(
            f"{path.name}: expected one mesh and one armature, got "
            f"meshes={len(meshes)} armatures={len(armatures)}"
        )

    mesh_object = meshes[0]
    armature = armatures[0]
    mesh = mesh_object.data
    triangles = sum(len(polygon.vertices) - 2 for polygon in mesh.polygons)
    if len(mesh.vertices) < 100_000 or triangles < 200_000:
        raise RuntimeError(f"{path.name}: reconstruction detail was lost")
    if len(armature.data.bones) != 53:
        raise RuntimeError(f"{path.name}: expected 53 bones")
    if len(mesh.materials) != 1:
        raise RuntimeError(f"{path.name}: expected one material")
    if not mesh.color_attributes:
        raise RuntimeError(f"{path.name}: reference colors are missing")
    armature_modifiers = [
        modifier for modifier in mesh_object.modifiers if modifier.type == "ARMATURE"
    ]
    if len(armature_modifiers) != 1 or armature_modifiers[0].object != armature:
        raise RuntimeError(f"{path.name}: imported skin is not bound to its armature")

    unweighted = 0
    over_limit = 0
    for vertex in mesh.vertices:
        weights = [group.weight for group in vertex.groups if group.weight > 1e-6]
        unweighted += not weights
        over_limit += len(weights) > 4
        if any(not math.isfinite(weight) for weight in weights):
            raise RuntimeError(f"{path.name}: non-finite skin weight")
    if unweighted or over_limit:
        raise RuntimeError(
            f"{path.name}: invalid weights unweighted={unweighted} over_limit={over_limit}"
        )
    if bpy.data.actions:
        raise RuntimeError(f"{path.name}: unexpected animation clips")

    print(
        "V4_GLB_OK "
        f"file={path.name} bytes={path.stat().st_size} "
        f"verts={len(mesh.vertices)} tris={triangles} bones={len(armature.data.bones)} "
        f"groups={len(mesh_object.vertex_groups)} materials={len(mesh.materials)} "
        f"colors={','.join(attribute.name for attribute in mesh.color_attributes)}"
    )


def main() -> None:
    args = parse_args()
    for path in model_paths(args.revision):
        validate_model(path)


if __name__ == "__main__":
    main()
