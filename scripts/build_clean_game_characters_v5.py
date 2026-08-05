"""Build clean-material, rigged v5 characters without image projection.

The Hunyuan reconstruction is used only as sculpted geometry.  Every visible
surface receives a discrete game material from spatial and skeleton regions;
turnaround pixels and vertex colors are deliberately forbidden in this build.
Reference trim, facial features, and fasteners are modeled as separate meshes.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_reference_characters_v3 as v3
import build_reference_projected_characters_v4 as v4


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORK_DIR = PROJECT_ROOT / "art-source/characters/work/v3"
CANDIDATE_DIR = WORK_DIR / "hunyuan-candidates"
HISTORY_DIR = PROJECT_ROOT / "docs/character-concepts/model-history"
SOURCE_DIR = PROJECT_ROOT / "art-source/characters"
MODEL_DIR = PROJECT_ROOT / "public/models/characters"


@dataclass(frozen=True)
class Profile:
    key: str
    slug: str
    base_file: str
    candidate_file: str
    female: bool


PROFILES = (
    Profile("male", "initial-male-v5", "initial-male-base.blend", "male-seed-12345.glb", False),
    Profile("female", "initial-female-v5", "initial-female-base.blend", "female-seed-23456.glb", True),
)


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--character", choices=("male", "female", "all"), default="all")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--revision-note", default="")
    parser.add_argument(
        "--revision-status",
        choices=("candidate", "diagnostic", "rejected", "kept"),
        default="diagnostic",
    )
    parser.add_argument("--skip-render", action="store_true")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"v5\.\d+", args.revision):
        parser.error("--revision must use the form v5.<number>, for example v5.0")
    return args


def v4_profile(profile: Profile) -> v4.CharacterProfile:
    empty = v4.ProjectionBox(0, 0, 1, 1)
    return v4.CharacterProfile(
        key=profile.key,
        slug=profile.slug,
        base_file=profile.base_file,
        candidate_file=profile.candidate_file,
        front_box=empty,
        right_box=empty,
        back_box=empty,
    )


def v3_spec(profile: Profile) -> v3.CharacterSpec:
    return next(spec for spec in v3.CHARACTERS if spec.key == profile.key)


def make_materials(profile: Profile) -> dict[str, bpy.types.Material]:
    prefix = f"{profile.slug}.Material"
    colors = {
        "skin": ("C98D6B" if not profile.female else "E0B29A", 0.58, 0.0),
        "teal": ("1D3537", 0.82, 0.0),
        "teal_dark": ("112326", 0.86, 0.0),
        "linen": ("B6A78E", 0.92, 0.0),
        "charcoal": ("242526", 0.90, 0.0),
        "leather": ("493A32", 0.74, 0.0),
        "leather_dark": ("251D19", 0.86, 0.0),
        "bronze": ("9A6B37", 0.46, 0.55),
        "hair": ("2B211C" if not profile.female else "552724", 0.69, 0.0),
        "hair_highlight": ("4A382F" if not profile.female else "793A34", 0.64, 0.0),
        "eye_white": ("E8E2D8", 0.38, 0.0),
        "iris": ("2B211A", 0.32, 0.0),
        "lip": ("8B4A42" if not profile.female else "A85C59", 0.48, 0.0),
    }
    return {
        key: v3.create_pbr_material(
            f"{prefix}.{key}", value[0], roughness=value[1], metallic=value[2]
        )
        for key, value in colors.items()
    }


def group_strength(candidate: bpy.types.Object, tokens: tuple[str, ...]) -> np.ndarray:
    group_indices = {
        group.index
        for group in candidate.vertex_groups
        if any(token in group.name for token in tokens)
    }
    result = np.zeros(len(candidate.data.vertices), dtype=np.float32)
    for vertex in candidate.data.vertices:
        result[vertex.index] = sum(
            assignment.weight
            for assignment in vertex.groups
            if assignment.group in group_indices
        )
    return result


def exact_group_strength(candidate: bpy.types.Object, names: set[str]) -> np.ndarray:
    group_indices = {
        group.index for group in candidate.vertex_groups if group.name in names
    }
    result = np.zeros(len(candidate.data.vertices), dtype=np.float32)
    for vertex in candidate.data.vertices:
        result[vertex.index] = sum(
            assignment.weight
            for assignment in vertex.groups
            if assignment.group in group_indices
        )
    return result


def hand_group_names(side: str, *, fingers: bool) -> set[str]:
    names = {f"hand_{side}"}
    if fingers:
        for digit in ("thumb", "index", "middle", "ring", "pinky"):
            names.update(f"{digit}_{joint:02d}_{side}" for joint in (1, 2, 3))
    return names


def align_mpfb_skin_to_reconstruction(
    body: bpy.types.Object,
    face_parts: list[bpy.types.Object],
    candidate: bpy.types.Object,
) -> None:
    """Fit MPFB facial and hand topology into the reconstruction's pose."""

    source_coordinates = np.array(
        [(body.matrix_world @ vertex.co)[:] for vertex in body.data.vertices],
        dtype=np.float32,
    )
    target_coordinates = np.array(
        [(candidate.matrix_world @ vertex.co)[:] for vertex in candidate.data.vertices],
        dtype=np.float32,
    )
    source_head = exact_group_strength(body, {"head", "neck_01"}) >= 0.34
    target_head = exact_group_strength(candidate, {"head", "neck_01"}) >= 0.34
    if not np.any(source_head) or not np.any(target_head):
        raise RuntimeError("Cannot align authored head: head weights are missing")
    source_min = np.min(source_coordinates[source_head], axis=0)
    source_max = np.max(source_coordinates[source_head], axis=0)
    target_min = np.min(target_coordinates[target_head], axis=0)
    target_max = np.max(target_coordinates[target_head], axis=0)
    source_center = (source_min + source_max) * 0.5
    target_center = (target_min + target_max) * 0.5
    raw_scale = (target_max - target_min) / np.maximum(source_max - source_min, 1e-8)
    head_scale = raw_scale * np.array((0.82, 0.78, 0.90), dtype=np.float32)
    head_scale = np.clip(head_scale, 0.68, 1.18)

    inverse_body = body.matrix_world.inverted()
    for index in np.flatnonzero(source_head):
        world = source_coordinates[index]
        fitted = target_center + (world - source_center) * head_scale
        body.data.vertices[int(index)].co = inverse_body @ Vector(fitted)
    for obj in face_parts:
        inverse = obj.matrix_world.inverted()
        for vertex in obj.data.vertices:
            world = np.asarray(obj.matrix_world @ vertex.co, dtype=np.float32)
            fitted = target_center + (world - source_center) * head_scale
            vertex.co = inverse @ Vector(fitted)
        obj.data.update()

    # Hand replacement was rejected in v5.2-v5.4.  The reconstruction hands
    # remain continuous with their wrists, so only the authored face is fitted.
    for side in ():
        source_all_strength = exact_group_strength(body, hand_group_names(side, fingers=True))
        target_all_strength = exact_group_strength(candidate, hand_group_names(side, fingers=True))
        source_wrist_strength = exact_group_strength(body, {f"hand_{side}"})
        target_wrist_strength = exact_group_strength(candidate, {f"hand_{side}"})
        source_finger_strength = exact_group_strength(
            body, hand_group_names(side, fingers=True) - {f"hand_{side}"}
        )
        target_finger_strength = exact_group_strength(
            candidate, hand_group_names(side, fingers=True) - {f"hand_{side}"}
        )
        source_mask = source_all_strength >= 0.05
        target_mask = target_all_strength >= 0.03
        source_wrist_mask = (source_wrist_strength >= 0.36) & (source_finger_strength < 0.24)
        target_wrist_mask = (target_wrist_strength >= 0.30) & (target_finger_strength < 0.24)
        source_finger_mask = source_finger_strength >= 0.32
        target_finger_mask = target_finger_strength >= 0.28
        if not np.any(source_mask) or not np.any(target_mask):
            raise RuntimeError(
                f"Cannot align authored {side} hand: source={int(np.count_nonzero(source_mask))} "
                f"target={int(np.count_nonzero(target_mask))}"
            )
        target_hand_z = target_coordinates[target_mask, 2]
        # Transferred individual finger weights are not reliable enough to
        # define orientation on the fused reconstruction.  Its presentation
        # pose has a clear vertical hand silhouette, so use geometric ends.
        target_wrist_mask = target_mask & (
            target_coordinates[:, 2] >= np.quantile(target_hand_z, 0.72)
        )
        target_finger_mask = target_mask & (
            target_coordinates[:, 2] <= np.quantile(target_hand_z, 0.28)
        )
        if not np.any(source_wrist_mask) or not np.any(source_finger_mask):
            raise RuntimeError(
                f"Cannot align authored {side} hand source landmarks: "
                f"wrist={int(np.count_nonzero(source_wrist_mask))} "
                f"fingers={int(np.count_nonzero(source_finger_mask))}"
            )
        source_wrist = np.mean(source_coordinates[source_wrist_mask], axis=0)
        target_wrist = np.mean(target_coordinates[target_wrist_mask], axis=0)
        source_tip = np.mean(source_coordinates[source_finger_mask], axis=0)
        target_tip = np.mean(target_coordinates[target_finger_mask], axis=0)
        source_direction = Vector(source_tip - source_wrist)
        target_direction = Vector(target_tip - target_wrist)
        source_length = max(source_direction.length, 1e-8)
        target_length = max(target_direction.length, 1e-8)
        rotation = source_direction.normalized().rotation_difference(
            target_direction.normalized()
        ).to_matrix()
        scale = float(np.clip(target_length / source_length, 0.72, 1.25))
        for index in np.flatnonzero(source_mask):
            offset = Vector(source_coordinates[index] - source_wrist) * scale
            fitted = Vector(target_wrist) + rotation @ offset
            body.data.vertices[int(index)].co = inverse_body @ fitted
    body.data.update()
    print(
        "V5_SKIN_ALIGNMENT "
        f"head_source_center={tuple(round(float(v), 4) for v in source_center)} "
        f"head_target_center={tuple(round(float(v), 4) for v in target_center)} "
        f"head_scale={tuple(round(float(v), 4) for v in head_scale)}"
    )


def segment_parameters(
    coordinates: np.ndarray, start: Vector, end: Vector
) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(start, dtype=np.float32)
    b = np.asarray(end, dtype=np.float32)
    delta = b - a
    length_squared = float(np.dot(delta, delta))
    relative = coordinates - a
    t = relative @ delta / max(length_squared, 1e-8)
    clamped = np.clip(t, 0.0, 1.0)
    projected = a + clamped[:, None] * delta
    distance = np.linalg.norm(coordinates - projected, axis=1)
    return t, distance


def arm_chain_parameters(
    coordinates: np.ndarray, armature: bpy.types.Object, side: str
) -> tuple[np.ndarray, np.ndarray]:
    upper = v3.bone_points(armature, None, f"upperarm_{side}")
    lower = v3.bone_points(armature, None, f"lowerarm_{side}")
    upper_t, upper_distance = segment_parameters(coordinates, *upper)
    lower_t, lower_distance = segment_parameters(coordinates, *lower)
    use_upper = upper_distance <= lower_distance
    chain = np.where(use_upper, upper_t, 1.0 + lower_t)
    distance = np.where(use_upper, upper_distance, lower_distance)
    return chain, distance


def classify_materials(
    candidate: bpy.types.Object,
    armature: bpy.types.Object,
    profile: Profile,
    materials: dict[str, bpy.types.Material],
) -> dict[str, int]:
    mesh = candidate.data
    mesh.materials.clear()
    material_order = [
        "skin",
        "teal",
        "teal_dark",
        "linen",
        "charcoal",
        "leather",
        "leather_dark",
        "bronze",
        "hair",
        "hair_highlight",
    ]
    for name in material_order:
        mesh.materials.append(materials[name])
    material_index = {name: index for index, name in enumerate(material_order)}

    coordinates = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", coordinates)
    coordinates = coordinates.reshape((-1, 3))
    minimum = np.min(coordinates, axis=0)
    maximum = np.max(coordinates, axis=0)
    span = maximum - minimum
    z_fraction = np.clip((coordinates[:, 2] - minimum[2]) / span[2], 0.0, 1.0)
    x_center = float((minimum[0] + maximum[0]) * 0.5)
    y_center = float((minimum[1] + maximum[1]) * 0.5)

    head = group_strength(candidate, ("head", "neck_01"))
    left_arm = group_strength(
        candidate,
        ("clavicle_l", "upperarm_l", "lowerarm_l", "hand_l", "thumb_", "index_", "middle_", "ring_", "pinky_"),
    )
    right_arm = group_strength(
        candidate,
        ("clavicle_r", "upperarm_r", "lowerarm_r", "hand_r", "thumb_", "index_", "middle_", "ring_", "pinky_"),
    )
    hand = group_strength(candidate, ("hand_", "thumb_", "index_", "middle_", "ring_", "pinky_"))
    arm = np.maximum(left_arm, right_arm)
    left_chain, left_distance = arm_chain_parameters(coordinates, armature, "l")
    right_chain, right_distance = arm_chain_parameters(coordinates, armature, "r")
    use_left = left_distance <= right_distance
    chain = np.where(use_left, left_chain, right_chain)

    labels = np.full(len(mesh.vertices), material_index["teal"], dtype=np.int16)

    # Lower-body bands are intentionally discrete.  No sampled image color is
    # allowed to cross from boots to trousers or from trousers to the tunic.
    labels[z_fraction < 0.122] = material_index["leather_dark"]
    labels[(z_fraction >= 0.122) & (z_fraction < 0.158)] = material_index["leather"]
    labels[(z_fraction >= 0.158) & (z_fraction < 0.505)] = material_index["charcoal"]
    labels[(z_fraction >= 0.575) & (z_fraction <= 0.615) & (arm < 0.20)] = material_index["leather"]

    arm_distance = np.where(use_left, left_distance, right_distance)
    arm_mask = (
        ((arm >= 0.08) | (arm_distance < span[2] * 0.080))
        & (head < 0.22)
        & (z_fraction > 0.39)
    )
    if profile.female:
        labels[arm_mask & (chain < 0.91)] = material_index["teal"]
        labels[arm_mask & (chain >= 0.91) & (chain < 0.955)] = material_index["bronze"]
        labels[arm_mask & (chain >= 0.955) & (chain < 1.45)] = material_index["linen"]
        labels[arm_mask & (chain >= 1.45) & (chain < 1.72)] = material_index["skin"]
        labels[arm_mask & (chain >= 1.72) & (chain < 1.92)] = material_index["leather_dark"]
        labels[arm_mask & (chain >= 1.92)] = material_index["skin"]
    else:
        labels[arm_mask & (chain < 0.535)] = material_index["teal"]
        labels[arm_mask & (chain >= 0.535) & (chain < 0.585)] = material_index["bronze"]
        labels[arm_mask & (chain >= 0.585) & (chain < 1.25)] = material_index["linen"]
        labels[arm_mask & (chain >= 1.25) & (chain < 1.65)] = material_index["skin"]
        labels[arm_mask & (chain >= 1.65) & (chain < 1.92)] = material_index["leather_dark"]
        labels[arm_mask & (chain >= 1.92)] = material_index["skin"]
    labels[(hand >= 0.34) & (chain >= 1.90)] = material_index["skin"]
    spatial_hand = (
        (np.abs(coordinates[:, 0] - x_center) >= span[0] * 0.385)
        & (z_fraction >= 0.405)
        & (z_fraction <= 0.595)
    )
    labels[spatial_hand] = material_index["skin"]
    wrist_wrap = spatial_hand & (z_fraction >= 0.548) & (z_fraction <= 0.592)
    labels[wrist_wrap] = material_index["leather_dark"]
    boot_piping = (z_fraction >= 0.155) & (z_fraction <= 0.158)
    labels[boot_piping] = material_index["bronze"]

    head_mask = head >= 0.28
    if np.any(head_mask):
        head_points = coordinates[head_mask]
        head_min = np.min(head_points, axis=0)
        head_max = np.max(head_points, axis=0)
        head_span = head_max - head_min
        head_z = (coordinates[:, 2] - head_min[2]) / max(float(head_span[2]), 1e-8)
        side_hair = np.abs(coordinates[:, 0] - x_center) > head_span[0] * 0.31
        rear_hair = coordinates[:, 1] > y_center + head_span[1] * 0.05
        hair = head_mask & (
            (head_z > (0.66 if profile.female else 0.70))
            | (rear_hair & (head_z > (0.22 if profile.female else 0.42)))
            | (side_hair & (head_z > (0.30 if profile.female else 0.60)))
        )
        labels[head_mask] = material_index["skin"]
        labels[hair] = material_index["hair"]
        crown_highlight = hair & (head_z > 0.84) & (coordinates[:, 0] > x_center)
        labels[crown_highlight] = material_index["hair_highlight"]

    # Assign one flat semantic material per triangle.  Majority voting keeps
    # boundaries crisp and prevents interpolation between unrelated surfaces.
    counts = {name: 0 for name in material_order}
    for polygon in mesh.polygons:
        polygon_labels = labels[np.fromiter(polygon.vertices, dtype=np.int32)]
        selected = int(np.bincount(polygon_labels, minlength=len(material_order)).argmax())
        polygon.material_index = selected
        polygon.use_smooth = True
        counts[material_order[selected]] += 1
    mesh.update()
    candidate["surface_authoring"] = "discrete skeletal/spatial PBR regions"
    candidate["image_projection"] = False
    candidate["vertex_colors"] = False
    return counts


def add_game_uv(candidate: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    candidate.select_set(True)
    bpy.context.view_layer.objects.active = candidate
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    try:
        bpy.ops.uv.smart_project(
            angle_limit=math.radians(64.0),
            island_margin=0.002,
            area_weight=0.0,
            correct_aspect=True,
            scale_to_bounds=True,
        )
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
    if not candidate.data.uv_layers:
        raise RuntimeError("GameUV generation failed")
    candidate.data.uv_layers.active.name = "GameUV"


def delete_selected_polygons(obj: bpy.types.Object, polygon_mask: np.ndarray) -> None:
    if len(polygon_mask) != len(obj.data.polygons):
        raise ValueError("Polygon deletion mask has the wrong length")
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    selected = [bm.faces[index] for index in np.flatnonzero(polygon_mask)]
    bmesh.ops.delete(bm, geom=selected, context="FACES_ONLY")
    bm.to_mesh(mesh)
    bm.free()
    obj.data.update()


def retain_mpfb_skin_parts(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    profile: Profile,
) -> bpy.types.Object:
    """Keep the authored MPFB head and hands with their original UV skin material."""

    v3.bake_body_shape_mix(body)
    v3.tune_skin_material(body, v3_spec(profile))
    head = exact_group_strength(body, {"head"})
    hand = group_strength(body, ("hand_", "thumb_", "index_", "middle_", "ring_", "pinky_"))
    coordinates = np.array([vertex.co[:] for vertex in body.data.vertices], dtype=np.float32)
    z_min = float(np.min(coordinates[:, 2]))
    z_span = float(np.max(coordinates[:, 2]) - z_min)
    head_indices = np.flatnonzero(head >= 0.16)
    head_y_center = float(np.median(coordinates[head_indices, 1]))
    head_z_max = float(np.max(coordinates[head_indices, 2]))
    delete = np.ones(len(body.data.polygons), dtype=bool)
    for polygon in body.data.polygons:
        indices = np.fromiter(polygon.vertices, dtype=np.int32)
        center_z = float(np.mean(coordinates[indices, 2]))
        z_fraction = (center_z - z_min) / max(z_span, 1e-8)
        center_y = float(np.mean(coordinates[indices, 1]))
        is_head = (
            float(np.mean(head[indices])) >= 0.16
            and z_fraction >= 0.82
            and center_y <= head_y_center + z_span * 0.012
            and center_z <= head_z_max - z_span * 0.012
        )
        if is_head:
            delete[polygon.index] = False
    delete_selected_polygons(body, delete)
    body.name = f"{profile.slug}.AuthoredSkin"
    body.data.name = f"{profile.slug}.AuthoredSkinMesh"
    body["character_slug"] = profile.slug
    body["surface_authoring"] = "MPFB UV head and hands"
    v3.add_armature_modifier(body, armature)
    if not len(body.data.polygons):
        raise RuntimeError("MPFB skin extraction removed every face")
    return body


def remove_reconstructed_face_and_hands(candidate: bpy.types.Object) -> None:
    """Cut the rough reconstructed skin away while retaining modeled hair and clothing."""

    head = group_strength(candidate, ("head", "neck_01"))
    hand = exact_group_strength(
        candidate,
        hand_group_names("l", fingers=True) | hand_group_names("r", fingers=True),
    )
    skin_index = next(
        (
            index
            for index, slot in enumerate(candidate.material_slots)
            if slot.material and slot.material.name.endswith(".skin")
        ),
        None,
    )
    if skin_index is None:
        raise RuntimeError("Candidate skin material is missing")
    delete = np.zeros(len(candidate.data.polygons), dtype=bool)
    for polygon in candidate.data.polygons:
        indices = np.fromiter(polygon.vertices, dtype=np.int32)
        rough_face = float(np.mean(head[indices])) >= 0.20 and polygon.material_index == skin_index
        rough_hand = False
        delete[polygon.index] = rough_face or rough_hand
    deleted = int(np.count_nonzero(delete))
    if deleted < 1000:
        raise RuntimeError(f"Too few reconstructed skin faces selected: {deleted}")
    delete_selected_polygons(candidate, delete)
    candidate["removed_reconstruction_skin_faces"] = deleted


def cleanup_scene(keep: set[bpy.types.Object], armature: bpy.types.Object) -> None:
    for pose_bone in armature.pose.bones:
        pose_bone.custom_shape = None
    for obj in list(bpy.context.scene.objects):
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)


def front_surface(
    bvh: BVHTree, minimum: Vector, maximum: Vector, x: float, z: float
) -> Vector:
    origin = Vector((x, minimum.y - (maximum.y - minimum.y) * 2.0, z))
    hit, _normal, _index, _distance = bvh.ray_cast(origin, Vector((0.0, 1.0, 0.0)))
    if hit is None:
        return Vector((x, minimum.y, z))
    return Vector((x, hit.y - (maximum.z - minimum.z) * 0.0026, z))


def add_curve(
    name: str,
    xz_points: list[tuple[float, float]],
    bvh: BVHTree,
    minimum: Vector,
    maximum: Vector,
    material: bpy.types.Material,
    armature: bpy.types.Object,
    profile: Profile,
    *,
    depth_fraction: float = 0.0022,
) -> bpy.types.Object:
    points = [front_surface(bvh, minimum, maximum, x, z) for x, z in xz_points]
    obj = v3.create_curve_tube(
        name,
        points,
        material,
        armature,
        "spine_03",
        v3_spec(profile),
        "reference-trim",
        bevel_depth=(maximum.z - minimum.z) * depth_fraction,
        resolution=2,
    )
    obj["character_slug"] = profile.slug
    return obj


def add_face_and_trim(
    candidate: bpy.types.Object,
    armature: bpy.types.Object,
    profile: Profile,
    materials: dict[str, bpy.types.Material],
    *,
    include_generated_face: bool = True,
) -> list[bpy.types.Object]:
    minimum, maximum = v4.world_bounds(candidate)
    height = maximum.z - minimum.z
    center_x = (minimum.x + maximum.x) * 0.5
    bvh = BVHTree.FromObject(candidate, bpy.context.evaluated_depsgraph_get())
    created: list[bpy.types.Object] = []

    if profile.female:
        seam = [
            (center_x + height * 0.015, minimum.z + height * 0.842),
            (center_x - height * 0.036, minimum.z + height * 0.792),
            (center_x - height * 0.040, minimum.z + height * 0.700),
            (center_x - height * 0.022, minimum.z + height * 0.615),
        ]
        collar = [
            (center_x - height * 0.050, minimum.z + height * 0.838),
            (center_x, minimum.z + height * 0.818),
            (center_x + height * 0.050, minimum.z + height * 0.838),
        ]
        toggle_heights = (0.805,)
    else:
        seam = [
            (center_x + height * 0.055, minimum.z + height * 0.835),
            (center_x - height * 0.022, minimum.z + height * 0.765),
            (center_x - height * 0.020, minimum.z + height * 0.615),
        ]
        collar = [
            (center_x - height * 0.052, minimum.z + height * 0.846),
            (center_x, minimum.z + height * 0.815),
            (center_x + height * 0.052, minimum.z + height * 0.846),
        ]
        toggle_heights = (0.785, 0.745, 0.705)
    created.append(add_curve(f"{profile.slug}.CollarTrim", collar, bvh, minimum, maximum, materials["bronze"], armature, profile))
    created.append(add_curve(f"{profile.slug}.FrontFacing", seam, bvh, minimum, maximum, materials["bronze"], armature, profile, depth_fraction=0.0018))
    for index, fraction in enumerate(toggle_heights, 1):
        z = minimum.z + height * fraction
        width = height * (0.024 if profile.female else 0.030)
        points = [(center_x - width, z + height * 0.006), (center_x, z), (center_x + width, z + height * 0.006)]
        created.append(add_curve(f"{profile.slug}.Toggle.{index}", points, bvh, minimum, maximum, materials["bronze"], armature, profile, depth_fraction=0.0015))

    buckle_z = minimum.z + height * 0.594
    buckle_width = height * 0.024
    buckle_height = height * 0.010
    buckle = [
        (center_x - buckle_width, buckle_z),
        (center_x, buckle_z + buckle_height),
        (center_x + buckle_width, buckle_z),
        (center_x, buckle_z - buckle_height),
        (center_x - buckle_width, buckle_z),
    ]
    created.append(
        add_curve(
            f"{profile.slug}.BeltBuckle",
            buckle,
            bvh,
            minimum,
            maximum,
            materials["bronze"],
            armature,
            profile,
            depth_fraction=0.0014,
        )
    )

    # Eyes are true layered meshes, not painted pixels.
    head_strengths = group_strength(candidate, ("head",))
    head_indices = np.flatnonzero(head_strengths >= 0.42)
    if include_generated_face and len(head_indices):
        coordinates = np.array([candidate.data.vertices[int(i)].co[:] for i in head_indices], dtype=np.float32)
        head_min = np.min(coordinates, axis=0)
        head_max = np.max(coordinates, axis=0)
        head_height = float(head_max[2] - head_min[2])
        eye_z = float(head_min[2] + head_height * (0.575 if profile.female else 0.565))
        eye_separation = float((head_max[0] - head_min[0]) * 0.19)
        for side, sign in (("L", -1.0), ("R", 1.0)):
            eye_x = center_x + sign * eye_separation
            surface = front_surface(bvh, minimum, maximum, eye_x, eye_z)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=surface)
            eye = bpy.context.object
            eye.name = f"{profile.slug}.EyeWhite.{side}"
            eye.scale = (head_height * 0.040, head_height * 0.006, head_height * 0.013)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            eye.data.materials.append(materials["eye_white"])
            v3.rigid_weights(eye, armature, "head")
            eye["character_slug"] = profile.slug
            created.append(eye)

            iris_location = surface + Vector((0.0, -head_height * 0.008, 0.0))
            bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, location=iris_location)
            iris = bpy.context.object
            iris.name = f"{profile.slug}.Iris.{side}"
            iris.scale = (head_height * 0.009, head_height * 0.004, head_height * 0.009)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            iris.data.materials.append(materials["iris"])
            v3.rigid_weights(iris, armature, "head")
            iris["character_slug"] = profile.slug
            created.append(iris)

        mouth_z = float(head_min[2] + head_height * 0.34)
        mouth_width = float((head_max[0] - head_min[0]) * (0.12 if profile.female else 0.14))
        mouth = [
            (center_x - mouth_width, mouth_z),
            (center_x, mouth_z - head_height * 0.010),
            (center_x + mouth_width, mouth_z),
        ]
        mouth_obj = add_curve(
            f"{profile.slug}.Mouth",
            mouth,
            bvh,
            minimum,
            maximum,
            materials["lip"],
            armature,
            profile,
            depth_fraction=0.0010,
        )
        # add_curve defaults to torso weighting; replace it with head weights.
        for group in list(mouth_obj.vertex_groups):
            mouth_obj.vertex_groups.remove(group)
        for modifier in list(mouth_obj.modifiers):
            if modifier.type == "ARMATURE":
                mouth_obj.modifiers.remove(modifier)
        v3.rigid_weights(mouth_obj, armature, "head")
        created.append(mouth_obj)
    return created


def validate(
    candidate: bpy.types.Object,
    armature: bpy.types.Object,
    created: list[bpy.types.Object],
    skin_parts: bpy.types.Object | None,
    face_parts: list[bpy.types.Object],
) -> None:
    triangle_count = sum(len(poly.vertices) - 2 for poly in candidate.data.polygons)
    if triangle_count < 250_000:
        raise RuntimeError(f"Reconstructed garment surface is incomplete: {triangle_count} triangles")
    if candidate.data.color_attributes:
        raise RuntimeError("v5 clean build must not contain vertex colors")
    if len(candidate.data.materials) < 8:
        raise RuntimeError("Semantic game materials are incomplete")
    if not candidate.data.uv_layers or candidate.data.uv_layers.active.name != "GameUV":
        raise RuntimeError("GameUV is missing")
    if len(armature.data.bones) != 53:
        raise RuntimeError(f"Expected 53-bone rig, found {len(armature.data.bones)}")
    if skin_parts is not None:
        if len(skin_parts.data.polygons) < 1000:
            raise RuntimeError("Authored head/hand skin mesh is incomplete")
        if not any("Eyes" in obj.name for obj in face_parts):
            raise RuntimeError("Authored MPFB eyes are missing")
    elif not any("EyeWhite" in obj.name for obj in created):
        raise RuntimeError("Modeled eye surfaces are missing")
    print(
        f"V5_VALIDATE mesh={candidate.name} verts={len(candidate.data.vertices)} "
        f"tris={sum(len(poly.vertices) - 2 for poly in candidate.data.polygons)} "
        f"materials={len(candidate.data.materials)} uv={candidate.data.uv_layers.active.name} "
        f"bones={len(armature.data.bones)} details={len(created)} "
        f"skin_faces={len(skin_parts.data.polygons) if skin_parts else 0} "
        f"face_parts={len(face_parts)} vertex_colors=0"
    )


def save_and_export(
    candidate: bpy.types.Object,
    armature: bpy.types.Object,
    created: list[bpy.types.Object],
    supporting: list[bpy.types.Object],
    profile: Profile,
    revision: str,
) -> tuple[Path, Path]:
    source_dir = SOURCE_DIR / "history" / revision
    model_dir = MODEL_DIR / "history" / revision
    source_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    blend_path = source_dir / f"{profile.slug}.blend"
    glb_path = model_dir / f"{profile.slug}.glb"
    candidate["model_history_revision"] = revision
    candidate["reconstruction_source"] = profile.candidate_file
    candidate["rig_source"] = profile.base_file
    armature.name = f"{profile.slug}.Rig"
    armature.data.name = f"{profile.slug}.RigData"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    bpy.ops.object.select_all(action="DESELECT")
    for obj in (candidate, armature, *supporting, *created):
        obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        use_selection=True,
        export_apply=False,
        export_skins=True,
        export_all_influences=False,
        export_animations=False,
        export_materials="EXPORT",
        export_image_format="AUTO",
    )
    return blend_path, glb_path


def build(profile: Profile, revision: str, skip_render: bool) -> dict[str, object]:
    base_path = WORK_DIR / profile.base_file
    candidate_path = CANDIDATE_DIR / profile.candidate_file
    for path in (base_path, candidate_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    bpy.ops.wm.open_mainfile(filepath=str(base_path))
    body = v4.find_body()
    armature = v4.find_armature()
    face_parts: list[bpy.types.Object] = []
    proxy = v4_profile(profile)
    candidate = v4.import_candidate(proxy)
    candidate.name = f"{profile.slug}.CharacterSurface"
    candidate.data.name = f"{profile.slug}.CharacterSurfaceMesh"
    v4.align_candidate(candidate, body)
    v4.transfer_game_rig(candidate, body, armature)
    materials = make_materials(profile)
    counts = classify_materials(candidate, armature, profile, materials)
    add_game_uv(candidate)
    skin_parts = None
    cleanup_scene({candidate, armature}, armature)
    created = add_face_and_trim(
        candidate,
        armature,
        profile,
        materials,
        include_generated_face=True,
    )
    for obj in created:
        obj["model_history_revision"] = revision
    validate(candidate, armature, created, skin_parts, face_parts)

    preview_dir = HISTORY_DIR / revision
    previews = [] if skip_render else v4.render_previews(candidate, proxy, preview_dir)
    blend_path, glb_path = save_and_export(
        candidate,
        armature,
        created,
        [],
        profile,
        revision,
    )
    return {
        "character": profile.key,
        "blend": str(blend_path.relative_to(PROJECT_ROOT)),
        "glb": str(glb_path.relative_to(PROJECT_ROOT)),
        "previews": [str(path.relative_to(PROJECT_ROOT)) for path in previews],
        "vertices": len(candidate.data.vertices),
        "triangles": sum(len(poly.vertices) - 2 for poly in candidate.data.polygons),
        "bones": len(armature.data.bones),
        "surface_material_face_counts": counts,
        "modeled_detail_objects": len(created),
        "authored_skin_faces": 0,
        "authored_face_objects": len(face_parts),
        "uv": candidate.data.uv_layers.active.name,
        "vertex_colors": 0,
    }


def main() -> None:
    args = parse_args()
    selected = [profile for profile in PROFILES if args.character in ("all", profile.key)]
    results = [build(profile, args.revision, args.skip_render) for profile in selected]
    record = {
        "revision": args.revision,
        "pipeline": "v5-clean-semantic-materials",
        "status": args.revision_status,
        "note": args.revision_note,
        "image_projection": False,
        "vertex_colors": False,
        "characters": results,
    }
    history_dir = HISTORY_DIR / args.revision
    history_dir.mkdir(parents=True, exist_ok=True)
    (history_dir / "build.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("V5_DONE " + json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
