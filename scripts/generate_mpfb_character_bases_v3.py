r"""Generate the v3 MPFB anatomical bases and CPU reference previews.

Run from PowerShell at the project root (do not use --factory-startup):

  & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python scripts\generate_mpfb_character_bases_v3.py

MPFB is a Blender extension, so this script discovers its modules dynamically
in the same way as the official MPFB scripting examples. The generated files
intentionally contain no hair or clothing.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = PROJECT_ROOT / "art-source" / "characters" / "work" / "v3"
PREVIEW_DIR = WORK_DIR / "previews"
SCRIPT_RELATIVE_PATH = "scripts/generate_mpfb_character_bases_v3.py"
PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 800
PREVIEW_SAMPLES = 32


@dataclass(frozen=True)
class CharacterSpec:
    slug: str
    label: str
    concept_reference: str
    skin_asset: str
    eyebrow_asset: str
    eyelash_asset: str
    gender: float
    age: float
    muscle: float
    weight: float
    proportions: float
    height: float
    target_height_m: float
    cupsize: float
    firmness: float
    asian: float
    caucasian: float
    african: float
    detail_targets: tuple[tuple[str, float], ...]

    @property
    def output_path(self) -> Path:
        return WORK_DIR / f"{self.slug}.blend"

    @property
    def macro_settings(self) -> dict[str, object]:
        return {
            "gender": self.gender,
            "age": self.age,
            "muscle": self.muscle,
            "weight": self.weight,
            "proportions": self.proportions,
            "height": self.height,
            "cupsize": self.cupsize,
            "firmness": self.firmness,
            "race": {
                "asian": self.asian,
                "caucasian": self.caucasian,
                "african": self.african,
            },
        }


# Conservative detail weights refine the supplied silhouettes while keeping all
# target shape keys editable for the later sculpt pass.
MALE_DETAIL_TARGETS = (
    ("torso/measure-shoulder-dist-incr.target.gz", 0.18),
    ("torso/torso-vshape-incr.target.gz", 0.20),
    ("torso/torso-muscle-pectoral-incr.target.gz", 0.10),
    ("torso/torso-muscle-dorsi-incr.target.gz", 0.10),
    ("torso/measure-waist-circ-decr.target.gz", 0.07),
    ("neck/measure-neck-circ-incr.target.gz", 0.07),
    ("arms/l-upperarm-shoulder-muscle-incr.target.gz", 0.10),
    ("arms/r-upperarm-shoulder-muscle-incr.target.gz", 0.10),
    ("arms/l-upperarm-muscle-incr.target.gz", 0.10),
    ("arms/r-upperarm-muscle-incr.target.gz", 0.10),
    ("arms/l-lowerarm-muscle-incr.target.gz", 0.07),
    ("arms/r-lowerarm-muscle-incr.target.gz", 0.07),
    ("legs/l-upperleg-muscle-incr.target.gz", 0.07),
    ("legs/r-upperleg-muscle-incr.target.gz", 0.07),
    ("legs/l-lowerleg-muscle-incr.target.gz", 0.06),
    ("legs/r-lowerleg-muscle-incr.target.gz", 0.06),
    ("head/head-rectangular.target.gz", 0.14),
    ("head/head-scale-horiz-incr.target.gz", 0.03),
    ("cheek/l-cheek-bones-incr.target.gz", 0.10),
    ("cheek/r-cheek-bones-incr.target.gz", 0.10),
    ("cheek/l-cheek-volume-decr.target.gz", 0.04),
    ("cheek/r-cheek-volume-decr.target.gz", 0.04),
    ("chin/chin-width-incr.target.gz", 0.10),
    ("chin/chin-height-incr.target.gz", 0.04),
    ("chin/chin-prominent-incr.target.gz", 0.04),
    ("eyes/l-eye-epicanthus-in.target.gz", 0.12),
    ("eyes/r-eye-epicanthus-in.target.gz", 0.12),
    ("eyes/l-eye-height2-decr.target.gz", 0.05),
    ("eyes/r-eye-height2-decr.target.gz", 0.05),
    ("eyes/l-eye-corner1-down.target.gz", 0.04),
    ("eyes/r-eye-corner1-down.target.gz", 0.04),
    ("eyes/l-eye-corner2-up.target.gz", 0.06),
    ("eyes/r-eye-corner2-up.target.gz", 0.06),
    ("eyes/l-eye-eyefold-up.target.gz", 0.06),
    ("eyes/r-eye-eyefold-up.target.gz", 0.06),
    ("nose/nose-scale-depth-decr.target.gz", 0.06),
    ("nose/nose-scale-horiz-decr.target.gz", 0.04),
    ("nose/nose-point-width-decr.target.gz", 0.04),
    ("nose/nose-nostrils-width-decr.target.gz", 0.03),
    ("mouth/mouth-upperlip-volume-decr.target.gz", 0.06),
    ("mouth/mouth-lowerlip-volume-decr.target.gz", 0.04),
    ("ears/l-ear-scale-decr.target.gz", 0.04),
    ("ears/r-ear-scale-decr.target.gz", 0.04),
)


FEMALE_DETAIL_TARGETS = (
    ("torso/measure-shoulder-dist-decr.target.gz", 0.22),
    ("torso/torso-vshape-decr.target.gz", 0.06),
    ("torso/measure-bust-circ-decr.target.gz", 0.03),
    ("torso/measure-waist-circ-decr.target.gz", 0.13),
    ("torso/measure-hips-circ-incr.target.gz", 0.07),
    ("hip/hip-scale-horiz-incr.target.gz", 0.05),
    ("buttocks/buttocks-volume-incr.target.gz", 0.06),
    ("neck/measure-neck-circ-decr.target.gz", 0.07),
    ("hands/l-hand-scale-decr.target.gz", 0.04),
    ("hands/r-hand-scale-decr.target.gz", 0.04),
    ("arms/measure-upperarm-circ-decr.target.gz", 0.08),
    ("arms/l-upperarm-shoulder-muscle-decr.target.gz", 0.12),
    ("arms/r-upperarm-shoulder-muscle-decr.target.gz", 0.12),
    ("arms/l-upperarm-scale-horiz-decr.target.gz", 0.05),
    ("arms/r-upperarm-scale-horiz-decr.target.gz", 0.05),
    ("arms/l-lowerarm-scale-horiz-decr.target.gz", 0.03),
    ("arms/r-lowerarm-scale-horiz-decr.target.gz", 0.03),
    ("feet/l-foot-scale-decr.target.gz", 0.03),
    ("feet/r-foot-scale-decr.target.gz", 0.03),
    ("legs/l-upperleg-scale-horiz-decr.target.gz", 0.025),
    ("legs/r-upperleg-scale-horiz-decr.target.gz", 0.025),
    ("legs/l-lowerleg-scale-horiz-decr.target.gz", 0.035),
    ("legs/r-lowerleg-scale-horiz-decr.target.gz", 0.035),
    ("legs/l-lowerleg-fat-decr.target.gz", 0.035),
    ("legs/r-lowerleg-fat-decr.target.gz", 0.035),
    ("head/head-oval.target.gz", 0.16),
    ("head/head-scale-horiz-incr.target.gz", 0.025),
    ("head/head-scale-vert-incr.target.gz", 0.030),
    ("cheek/l-cheek-bones-incr.target.gz", 0.08),
    ("cheek/r-cheek-bones-incr.target.gz", 0.08),
    ("cheek/l-cheek-volume-incr.target.gz", 0.03),
    ("cheek/r-cheek-volume-incr.target.gz", 0.03),
    ("chin/chin-width-decr.target.gz", 0.11),
    ("chin/chin-height-decr.target.gz", 0.04),
    ("chin/chin-prominent-decr.target.gz", 0.04),
    ("chin/chin-triangle.target.gz", 0.06),
    ("eyes/l-eye-scale-incr.target.gz", 0.06),
    ("eyes/r-eye-scale-incr.target.gz", 0.06),
    ("eyes/l-eye-height1-incr.target.gz", 0.03),
    ("eyes/r-eye-height1-incr.target.gz", 0.03),
    ("eyes/l-eye-height2-incr.target.gz", 0.04),
    ("eyes/r-eye-height2-incr.target.gz", 0.04),
    ("eyes/l-eye-epicanthus-in.target.gz", 0.11),
    ("eyes/r-eye-epicanthus-in.target.gz", 0.11),
    ("eyes/l-eye-corner1-down.target.gz", 0.02),
    ("eyes/r-eye-corner1-down.target.gz", 0.02),
    ("eyes/l-eye-corner2-up.target.gz", 0.035),
    ("eyes/r-eye-corner2-up.target.gz", 0.035),
    ("eyes/l-eye-eyefold-up.target.gz", 0.07),
    ("eyes/r-eye-eyefold-up.target.gz", 0.07),
    ("eyebrows/eyebrows-angle-up.target.gz", 0.02),
    ("nose/nose-scale-depth-decr.target.gz", 0.13),
    ("nose/nose-scale-horiz-decr.target.gz", 0.07),
    ("nose/nose-scale-vert-decr.target.gz", 0.04),
    ("nose/nose-point-width-decr.target.gz", 0.07),
    ("nose/nose-nostrils-width-decr.target.gz", 0.05),
    ("nose/nose-compression-compress.target.gz", 0.05),
    ("mouth/mouth-scale-horiz-decr.target.gz", 0.03),
    ("mouth/mouth-upperlip-volume-incr.target.gz", 0.07),
    ("mouth/mouth-lowerlip-volume-incr.target.gz", 0.06),
    ("mouth/mouth-cupidsbow-incr.target.gz", 0.05),
    ("ears/l-ear-scale-decr.target.gz", 0.05),
    ("ears/r-ear-scale-decr.target.gz", 0.05),
)


CHARACTERS = (
    CharacterSpec(
        slug="initial-male-base",
        label="Initial Male Anatomical Base v3",
        concept_reference="docs/character-concepts/initial-male-turnaround.png",
        skin_asset="young_asian_male.mhmat",
        eyebrow_asset="eyebrow012.mhclo",
        eyelash_asset="eyelashes01.mhclo",
        gender=1.0,
        age=0.48,
        muscle=0.66,
        weight=0.51,
        proportions=0.62,
        # Calibrated in Blender 5.2 / MPFB 2.0.17 to an evaluated height of
        # approximately 1.78 m after subdivision and fitted body parts.
        height=0.630,
        target_height_m=1.78,
        cupsize=0.50,
        firmness=0.50,
        asian=0.92,
        caucasian=0.08,
        african=0.0,
        detail_targets=MALE_DETAIL_TARGETS,
    ),
    CharacterSpec(
        slug="initial-female-base",
        label="Initial Female Anatomical Base v3",
        concept_reference="docs/character-concepts/initial-female-turnaround.png",
        skin_asset="young_asian_female.mhmat",
        eyebrow_asset="eyebrow004.mhclo",
        eyelash_asset="eyelashes01.mhclo",
        gender=0.0,
        age=0.47,
        muscle=0.35,
        weight=0.40,
        proportions=0.43,
        # The Asian female neutral is relatively short; this value was
        # measured rather than inferred from the macro slider position.
        height=0.662,
        target_height_m=1.68,
        cupsize=0.42,
        firmness=0.62,
        asian=0.95,
        caucasian=0.05,
        african=0.0,
        detail_targets=FEMALE_DETAIL_TARGETS,
    ),
)


def mpfb_symbol(module_suffix: str, symbol: str):
    """Resolve an MPFB symbol without depending on its repository ID."""

    for module_name in tuple(sys.modules):
        if module_name.endswith(module_suffix):
            module = importlib.import_module(module_name)
            if not hasattr(module, symbol):
                raise AttributeError(f"{module_name} does not expose {symbol}")
            return getattr(module, symbol)
    raise RuntimeError(
        f"MPFB is not loaded ({module_suffix}). Start Blender with normal user "
        "preferences and do not pass --factory-startup."
    )


HumanService = mpfb_symbol("mpfb.services.humanservice", "HumanService")
TargetService = mpfb_symbol("mpfb.services.targetservice", "TargetService")
AssetService = mpfb_symbol("mpfb.services.assetservice", "AssetService")
LocationService = mpfb_symbol("mpfb.services.locationservice", "LocationService")
ObjectService = mpfb_symbol("mpfb.services.objectservice", "ObjectService")


def clear_scene() -> None:
    """Remove scene data while preserving MPFB preferences and registration."""

    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    for obj in tuple(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    scene = bpy.context.scene
    scene.camera = None
    scene.world = None
    scene.name = "Scene"

    for collection in tuple(bpy.data.collections):
        bpy.data.collections.remove(collection)

    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.worlds,
        bpy.data.actions,
        bpy.data.images,
        bpy.data.node_groups,
    ):
        for datablock in tuple(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def configure_source_scene(spec: CharacterSpec) -> None:
    scene = bpy.context.scene
    scene.name = f"{spec.slug}.Scene"
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.unit_settings.scale_length = 1.0
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene["character_label"] = spec.label
    scene["character_stage"] = "v3 anatomical base; no clothing or hair"
    scene["concept_reference"] = spec.concept_reference
    scene["generator_script"] = SCRIPT_RELATIVE_PATH
    scene["mpfb_version"] = "2.0.17"
    scene["blender_version"] = bpy.app.version_string

    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass


def resolved_asset(filename: str, subdir: str) -> str:
    path = AssetService.find_asset_absolute_path(filename, asset_subdir=subdir)
    if path is None or not Path(path).is_file():
        raise FileNotFoundError(
            f"Required MakeHuman System Asset is missing: {subdir}/{filename}"
        )
    return str(path)


def apply_detail_targets(
    body: bpy.types.Object,
    target_specs: Iterable[tuple[str, float]],
) -> None:
    targets_root = Path(LocationService.get_mpfb_data("targets"))
    for relative_path, weight in target_specs:
        target_path = targets_root / relative_path
        if not target_path.is_file():
            raise FileNotFoundError(f"Required MPFB target is missing: {target_path}")
        TargetService.load_target(body, str(target_path), weight=weight)

    body.update_tag()
    bpy.context.view_layer.update()


def put_feet_on_ground(body: bpy.types.Object) -> None:
    """Re-ground the body after non-macro shape keys have been applied."""

    lowest_point = float(ObjectService.get_lowest_point(body))
    if abs(lowest_point) < 1.0e-6:
        return
    body.location.z -= lowest_point
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    body.select_set(False)


def add_source_subdivision(obj: bpy.types.Object, *, render_levels: int) -> None:
    modifier = obj.modifiers.get("Source_Subdivision")
    if modifier is None:
        modifier = obj.modifiers.new("Source_Subdivision", "SUBSURF")
    modifier.subdivision_type = "CATMULL_CLARK"
    modifier.levels = 1
    modifier.render_levels = render_levels
    modifier.show_only_control_edges = True
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def move_to_collection(
    objects: Iterable[bpy.types.Object],
    collection: bpy.types.Collection,
) -> None:
    for obj in objects:
        if collection.objects.get(obj.name) is None:
            collection.objects.link(obj)
        for current_collection in tuple(obj.users_collection):
            if current_collection != collection:
                current_collection.objects.unlink(obj)


def create_character(
    spec: CharacterSpec, *, render_base_previews: bool = True
) -> dict[str, object]:
    clear_scene()
    configure_source_scene(spec)

    body = HumanService.create_human(
        mask_helpers=True,
        detailed_helpers=True,
        extra_vertex_groups=True,
        feet_on_ground=True,
        scale=0.1,
        macro_detail_dict=spec.macro_settings,
    )
    body.name = f"{spec.slug}.Body"

    apply_detail_targets(body, spec.detail_targets)
    put_feet_on_ground(body)

    HumanService.set_character_skin(
        resolved_asset(spec.skin_asset, "skins"),
        body,
        skin_type="GAMEENGINE",
        material_instances=False,
    )

    # Rig first: MPFB uses it while parenting and weighting every body part.
    rig = HumanService.add_builtin_rig(body, "game_engine", import_weights=True)
    if rig is None:
        raise RuntimeError(f"MPFB did not create a game_engine rig for {spec.slug}")
    rig.name = rig.data.name = f"{spec.slug}.Rig"
    rig.show_in_front = True

    body_part_specs = (
        ("eyes", "high-poly.mhclo", "Eyes", 1),
        ("eyebrows", spec.eyebrow_asset, "Eyebrows", 0),
        ("eyelashes", spec.eyelash_asset, "Eyelashes", 0),
        ("teeth", "teeth_base.mhclo", "Teeth", 1),
        ("tongue", "tongue01.mhclo", "Tongue", 1),
    )
    parts: dict[str, bpy.types.Object] = {}
    for subdir, filename, asset_type, subdiv_levels in body_part_specs:
        part = HumanService.add_mhclo_asset(
            resolved_asset(filename, subdir),
            body,
            asset_type=asset_type,
            subdiv_levels=subdiv_levels,
            material_type="GAMEENGINE",
            set_up_rigging=True,
            interpolate_weights=True,
            import_subrig=True,
            import_weights=True,
        )
        part.name = f"{spec.slug}.{asset_type}"
        parts[asset_type] = part

    add_source_subdivision(body, render_levels=2)
    for asset_type in ("Eyes", "Teeth", "Tongue"):
        existing = parts[asset_type].modifiers.get("Subdivision")
        if existing is not None:
            existing.levels = 1
            existing.render_levels = 2

    character_collection = bpy.data.collections.new(f"CHARACTER_{spec.slug}")
    bpy.context.scene.collection.children.link(character_collection)
    model_objects = (rig, body, *parts.values())
    move_to_collection(model_objects, character_collection)

    body["character_label"] = spec.label
    body["character_stage"] = "v3 anatomical base"
    body["concept_reference"] = spec.concept_reference
    body["generator_script"] = SCRIPT_RELATIVE_PATH
    body["mpfb_version"] = "2.0.17"
    body["mpfb_macro_settings"] = json.dumps(spec.macro_settings, sort_keys=True)
    body["target_height_m"] = spec.target_height_m
    body["mpfb_detail_targets"] = json.dumps(dict(spec.detail_targets), sort_keys=True)
    body["contains_clothing"] = False
    body["contains_hair"] = False
    body["skin_material_profile"] = "GAMEENGINE"
    rig["rig_profile"] = "game_engine"

    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.context.view_layer.update()

    report = validate_character(spec, body, rig, parts, model_objects)
    save_source(spec)
    if render_base_previews:
        render_previews(spec, report["bounds"])
    return report


def object_bounds(objects: Iterable[bpy.types.Object]) -> tuple[Vector, Vector]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    points: list[Vector] = []
    for obj in objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        points.extend(
            evaluated.matrix_world @ Vector(corner)
            for corner in evaluated.bound_box
        )
    if not points:
        raise RuntimeError("No renderable character geometry was found")
    minimum = Vector(
        tuple(min(point[axis] for point in points) for axis in range(3))
    )
    maximum = Vector(
        tuple(max(point[axis] for point in points) for axis in range(3))
    )
    return minimum, maximum


def evaluated_vertex_count(obj: bpy.types.Object) -> int:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return len(mesh.vertices)
    finally:
        evaluated.to_mesh_clear()


def validate_character(
    spec: CharacterSpec,
    body: bpy.types.Object,
    rig: bpy.types.Object,
    parts: dict[str, bpy.types.Object],
    model_objects: tuple[bpy.types.Object, ...],
) -> dict[str, object]:
    expected_parts = {"Eyes", "Eyebrows", "Eyelashes", "Teeth", "Tongue"}
    if set(parts) != expected_parts:
        raise RuntimeError(
            f"Unexpected body-part inventory for {spec.slug}: {sorted(parts)}"
        )
    if len(body.data.vertices) < 19_000:
        raise RuntimeError(f"{spec.slug} basemesh is unexpectedly low resolution")
    if len(rig.data.bones) < 50:
        raise RuntimeError(f"{spec.slug} game_engine rig is incomplete")
    if not body.material_slots:
        raise RuntimeError(f"{spec.slug} has no skin material")
    if any(
        "hair" in obj.name.lower() or "clothes" in obj.name.lower()
        for obj in model_objects
    ):
        raise RuntimeError(f"{spec.slug} unexpectedly contains hair or clothing")

    minimum, maximum = object_bounds(model_objects)
    dimensions = maximum - minimum
    if not 1.45 <= dimensions.z <= 2.10:
        raise RuntimeError(
            f"{spec.slug} height is outside the expected adult range: "
            f"{dimensions.z:.3f}m"
        )
    height_error = dimensions.z - spec.target_height_m
    if abs(height_error) > 0.02:
        raise RuntimeError(
            f"{spec.slug} missed the calibrated target height: "
            f"{dimensions.z:.3f}m vs {spec.target_height_m:.3f}m"
        )

    object_rows = []
    for obj in sorted(model_objects, key=lambda item: item.name):
        row: dict[str, object] = {"name": obj.name, "type": obj.type}
        if obj.type == "MESH":
            row["vertices"] = len(obj.data.vertices)
            row["polygons"] = len(obj.data.polygons)
            row["evaluated_viewport_vertices"] = evaluated_vertex_count(obj)
        elif obj.type == "ARMATURE":
            row["bones"] = len(obj.data.bones)
        object_rows.append(row)

    return {
        "slug": spec.slug,
        "blend": str(spec.output_path),
        "objects": object_rows,
        "dimensions_m": [round(value, 4) for value in dimensions],
        "target_height_m": spec.target_height_m,
        "height_error_m": round(height_error, 4),
        "bounds_min_m": [round(value, 4) for value in minimum],
        "bounds_max_m": [round(value, 4) for value in maximum],
        "detail_target_count": len(spec.detail_targets),
        "bounds": (minimum, maximum),
    }


def save_source(spec: CharacterSpec) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    # Make the art-source portable by packing loaded CC0 system textures.
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(spec.output_path), compress=True)
    if not spec.output_path.is_file():
        raise RuntimeError(f"Blender did not write {spec.output_path}")


def make_principled_material(
    name: str,
    color: tuple[float, float, float, float],
    roughness: float,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = color
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Roughness"].default_value = roughness
    return material


def create_preview_setup(
    minimum: Vector,
) -> tuple[bpy.types.Object, tuple[bpy.types.Object, ...]]:
    scene = bpy.context.scene
    preview_collection = bpy.data.collections.new("Preview_Setup")
    scene.collection.children.link(preview_collection)

    bpy.ops.mesh.primitive_plane_add(
        size=30.0,
        location=(0.0, 0.0, minimum.z - 0.008),
    )
    ground = bpy.context.object
    ground.name = "Preview_Ground"
    ground.data.materials.append(
        make_principled_material(
            "Preview_Ground_Material",
            (0.075, 0.083, 0.095, 1.0),
            0.88,
        )
    )
    move_to_collection((ground,), preview_collection)

    camera_data = bpy.data.cameras.new("Preview_Camera")
    camera_data.type = "ORTHO"
    camera_data.lens = 70.0
    camera = bpy.data.objects.new("Preview_Camera", camera_data)
    preview_collection.objects.link(camera)
    scene.camera = camera

    lights = []
    for name, energy, size in (
        ("Preview_Key", 850.0, 4.0),
        ("Preview_Fill", 430.0, 3.5),
        ("Preview_Rim", 720.0, 3.0),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(name, data)
        preview_collection.objects.link(light)
        lights.append(light)

    world = bpy.data.worlds.new("Preview_World")
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.055, 0.060, 0.070, 1.0)
    background.inputs["Strength"].default_value = 0.32
    scene.world = world
    return camera, tuple(lights)


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def position_preview_rig(
    camera: bpy.types.Object,
    lights: tuple[bpy.types.Object, ...],
    minimum: Vector,
    maximum: Vector,
    camera_side: Vector,
) -> None:
    dimensions = maximum - minimum
    height = dimensions.z
    target = (minimum + maximum) * 0.5
    target.z = minimum.z + height * 0.51
    camera_side = camera_side.normalized()
    view_direction = -camera_side
    screen_right = view_direction.cross(Vector((0.0, 0.0, 1.0))).normalized()
    world_up = Vector((0.0, 0.0, 1.0))

    camera.location = target + camera_side * height * 3.0
    camera.data.ortho_scale = height * 1.12
    point_at(camera, target)

    key, fill, rim = lights
    key.location = (
        target
        + camera_side * height * 1.20
        - screen_right * height * 0.72
        + world_up * height * 0.72
    )
    fill.location = (
        target
        + camera_side * height * 0.85
        + screen_right * height * 0.72
        + world_up * height * 0.28
    )
    rim.location = (
        target
        - camera_side * height * 0.70
        + screen_right * height * 0.28
        + world_up * height * 0.72
    )
    point_at(key, target)
    point_at(fill, target)
    point_at(rim, target + world_up * height * 0.10)


def configure_cpu_render() -> None:
    scene = bpy.context.scene
    # Preserve subtle facial planes and skin texture in the comparison renders.
    scene.view_settings.exposure = -0.75
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = PREVIEW_SAMPLES
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.cycles.transmission_bounces = 2
    scene.render.resolution_x = PREVIEW_WIDTH
    scene.render.resolution_y = PREVIEW_HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False


def render_previews(
    spec: CharacterSpec,
    stored_bounds: tuple[Vector, Vector],
) -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    minimum, maximum = stored_bounds
    camera, lights = create_preview_setup(minimum)
    configure_cpu_render()

    for view_name, camera_side in (
        ("front", Vector((0.0, -1.0, 0.0))),
        ("right-side", Vector((-1.0, 0.0, 0.0))),
    ):
        position_preview_rig(camera, lights, minimum, maximum, camera_side)
        output_path = PREVIEW_DIR / f"{spec.slug}-{view_name}.png"
        bpy.context.scene.render.filepath = str(output_path)
        bpy.ops.render.render(write_still=True)
        if not output_path.is_file():
            raise RuntimeError(f"Blender did not render {output_path}")
        print(f"V3_PREVIEW {spec.slug} {view_name} {output_path}")


def serializable_report(report: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in report.items() if key != "bounds"}


def main() -> None:
    if bpy.app.version < (5, 2, 0):
        raise RuntimeError(
            f"This script was validated for Blender 5.2; got "
            f"{bpy.app.version_string}"
        )

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--character", choices=("male", "female", "all"), default="all")
    parser.add_argument("--skip-render", action="store_true")
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parser.parse_args(script_args)

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    selected = (
        CHARACTERS
        if args.character == "all"
        else tuple(spec for spec in CHARACTERS if args.character in spec.slug)
    )
    reports = []
    for spec in selected:
        print(f"V3_GENERATE_START {spec.slug}")
        report = create_character(spec, render_base_previews=not args.skip_render)
        reports.append(serializable_report(report))
        print("V3_CHARACTER_REPORT " + json.dumps(reports[-1], sort_keys=True))

    print("V3_GENERATION_COMPLETE " + json.dumps(reports, sort_keys=True))


if __name__ == "__main__":
    main()
