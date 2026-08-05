"""Build reference-projected, rigged v4 characters from the Hunyuan reconstructions.

The v3 MPFB characters remain the editable anatomical/garment reconstruction.  This
pipeline is the high-fidelity presentation/game asset: it keeps the reference-
matched Hunyuan surface, projects the supplied front/right/back turnaround pixels
onto that surface, and transfers the 53-bone MPFB game rig by surface proximity.

Run with Blender 5.2 (normal startup so the MPFB extension remains available):

    blender.exe --background --python scripts/build_reference_projected_characters_v4.py

Use ``-- --character female`` or ``-- --character male`` for one character.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = PROJECT_ROOT / "art-source" / "characters" / "work" / "v3"
CANDIDATE_DIR = WORK_DIR / "hunyuan-candidates"
SOURCE_DIR = PROJECT_ROOT / "art-source" / "characters"
MODEL_DIR = PROJECT_ROOT / "public" / "models" / "characters"
INPUT_DIR = PROJECT_ROOT / "docs" / "character-concepts" / "reconstruction-inputs"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "character-concepts" / "model-previews" / "v4"
HISTORY_DIR = PROJECT_ROOT / "docs" / "character-concepts" / "model-history"


@dataclass(frozen=True)
class ProjectionBox:
    left: int
    top: int
    right: int
    bottom: int


@dataclass(frozen=True)
class CharacterProfile:
    key: str
    slug: str
    base_file: str
    candidate_file: str
    front_box: ProjectionBox
    right_box: ProjectionBox
    back_box: ProjectionBox


@dataclass(frozen=True)
class OutputLocations:
    preview_dir: Path
    source_dir: Path
    model_dir: Path
    revision: str | None = None


CHARACTERS = (
    CharacterProfile(
        key="male",
        slug="initial-male-v4",
        base_file="initial-male-base.blend",
        candidate_file="male-seed-12345.glb",
        front_box=ProjectionBox(284, 22, 747, 981),
        right_box=ProjectionBox(416, 22, 592, 984),
        back_box=ProjectionBox(278, 22, 745, 982),
    ),
    CharacterProfile(
        key="female",
        slug="initial-female-v4",
        base_file="initial-female-base.blend",
        candidate_file="female-seed-23456.glb",
        front_box=ProjectionBox(274, 22, 750, 992),
        right_box=ProjectionBox(420, 22, 596, 992),
        back_box=ProjectionBox(272, 22, 752, 992),
    ),
)


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--character", choices=("male", "female", "all"), default="all")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument(
        "--revision",
        help="Preserve outputs under model-history/art-source/public history directories, e.g. v4.14",
    )
    parser.add_argument("--revision-note", default="")
    parser.add_argument(
        "--revision-status",
        choices=("candidate", "diagnostic", "rejected", "kept"),
        default="candidate",
    )
    args = parser.parse_args(argv)
    if args.revision and not re.fullmatch(r"v4\.\d+", args.revision):
        parser.error("--revision must use the form v4.<number>, for example v4.14")
    return args


def output_locations(revision: str | None) -> OutputLocations:
    if revision is None:
        return OutputLocations(
            preview_dir=PREVIEW_DIR,
            source_dir=SOURCE_DIR,
            model_dir=MODEL_DIR,
        )
    return OutputLocations(
        preview_dir=HISTORY_DIR / revision,
        source_dir=SOURCE_DIR / "history" / revision,
        model_dir=MODEL_DIR / "history" / revision,
        revision=revision,
    )


def ensure_paths(profile: CharacterProfile) -> None:
    paths = (
        WORK_DIR / profile.base_file,
        CANDIDATE_DIR / profile.candidate_file,
        INPUT_DIR / profile.key / "front.png",
        INPUT_DIR / profile.key / "right.png",
        INPUT_DIR / profile.key / "back.png",
    )
    missing = [path for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing v4 inputs: " + ", ".join(str(path) for path in missing))


def world_bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return (
        Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
        Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
    )


def find_body() -> bpy.types.Object:
    candidates = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    with_body_group = [obj for obj in candidates if obj.vertex_groups.get("body")]
    return max(with_body_group or candidates, key=lambda obj: len(obj.data.vertices))


def find_armature() -> bpy.types.Object:
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise RuntimeError("The MPFB base has no armature")
    return max(armatures, key=lambda obj: len(obj.data.bones))


def import_candidate(profile: CharacterProfile) -> bpy.types.Object:
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(CANDIDATE_DIR / profile.candidate_file))
    imported = [obj for obj in bpy.context.scene.objects if obj not in before and obj.type == "MESH"]
    if len(imported) != 1:
        raise RuntimeError(f"Expected one Hunyuan mesh, found {len(imported)}")
    candidate = imported[0]
    candidate.name = f"{profile.slug}.ReferenceSurface"
    candidate.data.name = f"{profile.slug}.ReferenceSurfaceMesh"
    return candidate


def align_candidate(candidate: bpy.types.Object, body: bpy.types.Object) -> None:
    """Uniformly fit the candidate height and centres to the MPFB rest body."""

    candidate_min, candidate_max = world_bounds(candidate)
    body_min, body_max = world_bounds(body)
    candidate_height = candidate_max.z - candidate_min.z
    body_height = body_max.z - body_min.z
    scale = body_height / candidate_height
    candidate.scale = (scale, scale, scale)
    bpy.context.view_layer.update()

    candidate_min, candidate_max = world_bounds(candidate)
    candidate_center = (candidate_min + candidate_max) * 0.5
    body_center = (body_min + body_max) * 0.5
    candidate.location += Vector(
        (
            body_center.x - candidate_center.x,
            body_center.y - candidate_center.y,
            body_min.z - candidate_min.z,
        )
    )
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    candidate.select_set(True)
    bpy.context.view_layer.objects.active = candidate
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def transfer_game_rig(
    candidate: bpy.types.Object, body: bpy.types.Object, armature: bpy.types.Object
) -> None:
    """Transfer MPFB surface weights, then retain the strongest four per vertex."""

    deform_bones = {bone.name for bone in armature.data.bones if bone.use_deform}
    for source_group in body.vertex_groups:
        if source_group.name in deform_bones:
            candidate.vertex_groups.new(name=source_group.name)

    bpy.ops.object.select_all(action="DESELECT")
    candidate.select_set(True)
    bpy.context.view_layer.objects.active = candidate
    transfer = candidate.modifiers.new("V4_Mpfb_Surface_Weights", "DATA_TRANSFER")
    transfer.object = body
    transfer.use_vert_data = True
    transfer.data_types_verts = {"VGROUP_WEIGHTS"}
    transfer.vert_mapping = "POLYINTERP_NEAREST"
    transfer.layers_vgroup_select_src = "ALL"
    transfer.layers_vgroup_select_dst = "NAME"
    bpy.ops.object.modifier_apply(modifier=transfer.name)

    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)

    armature_modifier = candidate.modifiers.new("V4_Game_Rig", "ARMATURE")
    armature_modifier.object = armature
    armature_modifier.use_deform_preserve_volume = True
    candidate.parent = armature


def load_padded_reference_pixels(
    image_path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Remove the studio background by extending each scanline's nearest subject pixel.

    Projective reconstruction is deliberately a little wider than the painted
    silhouette in places.  Texture padding prevents those small registration
    differences from turning into white seams around hair, hands, and boots.
    """

    source = bpy.data.images.load(str(image_path), check_existing=False)
    width, height = source.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    source.pixels.foreach_get(pixels)
    rgba = pixels.reshape((height, width, 4))
    rgb = rgba[:, :, :3]
    saturation = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    luminance = np.mean(rgb, axis=2)
    foreground = (luminance < 0.72) | (saturation > 0.060)

    valid_rows = np.flatnonzero(np.any(foreground, axis=1))
    if not len(valid_rows):
        raise RuntimeError(f"Could not separate subject from background in {image_path}")

    padded = rgba.copy()
    x_coordinates = np.arange(width)
    row_left = np.zeros(height, dtype=np.float32)
    row_right = np.full(height, width - 1, dtype=np.float32)
    for row in range(height):
        source_row = row
        if not np.any(foreground[source_row]):
            source_row = int(valid_rows[np.argmin(np.abs(valid_rows - row))])
        indices = np.flatnonzero(foreground[source_row])
        row_left[row] = float(indices[0])
        row_right[row] = float(indices[-1])
        left_positions = np.maximum.accumulate(
            np.where(foreground[source_row], x_coordinates, -width * 2)
        )
        right_positions = np.minimum.accumulate(
            np.where(foreground[source_row], x_coordinates, width * 2)[::-1]
        )[::-1]
        choose_left = (x_coordinates - left_positions) <= (right_positions - x_coordinates)
        nearest = np.where(choose_left, left_positions, right_positions)
        nearest = np.clip(nearest, indices[0], indices[-1])
        padded[row, :, :3] = rgba[source_row, nearest, :3]
        padded[row, :, 3] = 1.0

    vertical_average = np.zeros_like(padded[:, :, :3])
    smoothing_radius = 7
    for offset in range(-smoothing_radius, smoothing_radius + 1):
        vertical_average += np.roll(padded[:, :, :3], offset, axis=0)
    vertical_average /= float(smoothing_radius * 2 + 1)
    padded[:, :, :3][~foreground] = vertical_average[~foreground]

    bpy.data.images.remove(source)
    return padded, row_left, row_right


def create_vertex_color_material(name: str) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (0.35, 0.35, 0.35, 1.0)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    vertex_color = nodes.new("ShaderNodeVertexColor")
    vertex_color.layer_name = "ReferenceColor"
    vertex_color.label = "Blended turnaround projection"
    shader.inputs["Roughness"].default_value = 0.88
    specular = shader.inputs.get("Specular IOR Level")
    if specular is not None:
        specular.default_value = 0.16
    emission_color = shader.inputs.get("Emission Color")
    emission_strength = shader.inputs.get("Emission Strength")
    links.new(vertex_color.outputs["Color"], shader.inputs["Base Color"])
    if emission_color is not None and emission_strength is not None:
        links.new(vertex_color.outputs["Color"], emission_color)
        emission_strength.default_value = 0.10
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    vertex_color.location = (-420.0, 20.0)
    shader.location = (-120.0, 20.0)
    output.location = (170.0, 20.0)
    return material


def box_uv(
    coordinate: float,
    source_min: float,
    source_max: float,
    pixel_min: int,
    pixel_max: int,
    *,
    flip: bool = False,
) -> float:
    fraction = (coordinate - source_min) / max(source_max - source_min, 1e-8)
    fraction = max(0.0, min(1.0, fraction))
    if flip:
        fraction = 1.0 - fraction
    return (pixel_min + (pixel_max - pixel_min) * fraction) / 1024.0


def apply_reference_projection(candidate: bpy.types.Object, profile: CharacterProfile) -> None:
    mesh = candidate.data
    mesh.materials.clear()
    mesh.materials.append(create_vertex_color_material(f"{profile.slug}.ReferenceMaterial"))

    projections = {
        "front": load_padded_reference_pixels(INPUT_DIR / profile.key / "front.png"),
        "back": load_padded_reference_pixels(INPUT_DIR / profile.key / "back.png"),
        "right": load_padded_reference_pixels(INPUT_DIR / profile.key / "right.png"),
    }

    minimum, maximum = world_bounds(candidate)
    color_layer = mesh.color_attributes.new(
        name="ReferenceColor", type="BYTE_COLOR", domain="POINT"
    )
    mesh.color_attributes.active_color = color_layer

    vertex_count = len(mesh.vertices)
    coordinates = np.empty(vertex_count * 3, dtype=np.float32)
    normals = np.empty(vertex_count * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", coordinates)
    mesh.vertices.foreach_get("normal", normals)
    coordinates = coordinates.reshape((-1, 3))
    normals = normals.reshape((-1, 3))
    normal_lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals /= np.maximum(normal_lengths, 1e-8)

    def vertex_group_strength(group_names: set[str]) -> np.ndarray:
        group_indices = {
            group.index for group in candidate.vertex_groups if group.name in group_names
        }
        strengths = np.zeros(vertex_count, dtype=np.float32)
        for vertex in mesh.vertices:
            strengths[vertex.index] = sum(
                assignment.weight
                for assignment in vertex.groups
                if assignment.group in group_indices
            )
        return strengths

    arm_group_names = {
        group.name
        for group in candidate.vertex_groups
        if any(
            token in group.name
            for token in ("upperarm_", "lowerarm_", "hand_", "thumb_", "index_", "middle_", "ring_", "pinky_")
        )
    }
    arm_strength = vertex_group_strength(arm_group_names)
    sleeve_group_names = {
        group.name
        for group in candidate.vertex_groups
        if "upperarm_" in group.name or "lowerarm_" in group.name
    }
    sleeve_strength = vertex_group_strength(sleeve_group_names)
    hand_group_names = {
        group.name
        for group in candidate.vertex_groups
        if any(
            token in group.name
            for token in ("hand_", "thumb_", "index_", "middle_", "ring_", "pinky_")
        )
    }
    hand_strength = vertex_group_strength(hand_group_names)
    head_strength = vertex_group_strength({"head", "neck_01"})

    z_fraction = np.clip(
        (coordinates[:, 2] - minimum.z) / max(maximum.z - minimum.z, 1e-8),
        0.0,
        1.0,
    )
    contour_bins = 1024
    z_bins = np.clip(np.rint(z_fraction * (contour_bins - 1)).astype(np.int32), 0, contour_bins - 1)

    def contour_spans(
        axis_values: np.ndarray,
        mask: np.ndarray | None = None,
        *,
        smoothing_radius: int = 3,
        smoothing_passes: int = 2,
    ) -> tuple[np.ndarray, np.ndarray]:
        lower = np.full(contour_bins, np.inf, dtype=np.float32)
        upper = np.full(contour_bins, -np.inf, dtype=np.float32)
        selected = np.ones(vertex_count, dtype=bool) if mask is None else mask
        np.minimum.at(lower, z_bins[selected], axis_values[selected])
        np.maximum.at(upper, z_bins[selected], axis_values[selected])
        valid = np.isfinite(lower) & np.isfinite(upper)
        valid_indices = np.flatnonzero(valid)
        if not len(valid_indices):
            raise RuntimeError("Could not derive a projection contour")
        all_indices = np.arange(contour_bins)
        lower = np.interp(all_indices, valid_indices, lower[valid_indices]).astype(np.float32)
        upper = np.interp(all_indices, valid_indices, upper[valid_indices]).astype(np.float32)
        for _pass in range(smoothing_passes):
            lower = sum(np.roll(lower, offset) for offset in range(-smoothing_radius, smoothing_radius + 1)) / (
                smoothing_radius * 2 + 1
            )
            upper = sum(np.roll(upper, offset) for offset in range(-smoothing_radius, smoothing_radius + 1)) / (
                smoothing_radius * 2 + 1
            )
        return lower[z_bins], upper[z_bins]

    x_lower, x_upper = contour_spans(coordinates[:, 0])
    y_lower, y_upper = contour_spans(coordinates[:, 1])

    def uv_array(
        values: np.ndarray,
        source_min: float,
        source_max: float,
        box_min: int,
        box_max: int,
        *,
        flip: bool = False,
    ) -> np.ndarray:
        fraction = np.clip((values - source_min) / max(source_max - source_min, 1e-8), 0.0, 1.0)
        if flip:
            fraction = 1.0 - fraction
        return (box_min + (box_max - box_min) * fraction) / 1024.0

    def sample_array(image: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        height, width, _channels = image.shape
        x = np.clip(u * (width - 1), 0.0, width - 1.0)
        y = np.clip(v * (height - 1), 0.0, height - 1.0)
        x0, y0 = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32)
        x1, y1 = np.minimum(width - 1, x0 + 1), np.minimum(height - 1, y0 + 1)
        tx, ty = (x - x0)[:, None], (y - y0)[:, None]
        return (
            image[y0, x0, :3] * (1.0 - tx) * (1.0 - ty)
            + image[y0, x1, :3] * tx * (1.0 - ty)
            + image[y1, x0, :3] * (1.0 - tx) * ty
            + image[y1, x1, :3] * tx * ty
        )

    def silhouette_u(
        projection: tuple[np.ndarray, np.ndarray, np.ndarray],
        axis_values: np.ndarray,
        axis_lower: np.ndarray,
        axis_upper: np.ndarray,
        v: np.ndarray,
        *,
        flip: bool = False,
        source_start: float = 0.0,
        source_end: float = 1.0,
    ) -> np.ndarray:
        image, source_left, source_right = projection
        height, width, _channels = image.shape
        row_position = np.clip(v * (height - 1), 0.0, height - 1.0)
        row0 = np.floor(row_position).astype(np.int32)
        row1 = np.minimum(height - 1, row0 + 1)
        blend = row_position - row0
        left = source_left[row0] * (1.0 - blend) + source_left[row1] * blend
        right = source_right[row0] * (1.0 - blend) + source_right[row1] * blend
        fraction = np.clip(
            (axis_values - axis_lower) / np.maximum(axis_upper - axis_lower, 1e-8), 0.0, 1.0
        )
        if flip:
            fraction = 1.0 - fraction
        source_fraction = source_start + (source_end - source_start) * fraction
        return (left + (right - left) * source_fraction) / float(width - 1)

    z_values = coordinates[:, 2]
    front_v = uv_array(
        z_values,
        minimum.z,
        maximum.z,
        1024 - profile.front_box.bottom,
        1024 - profile.front_box.top,
    )
    back_v = uv_array(
        z_values,
        minimum.z,
        maximum.z,
        1024 - profile.back_box.bottom,
        1024 - profile.back_box.top,
    )
    side_v = uv_array(
        z_values,
        minimum.z,
        maximum.z,
        1024 - profile.right_box.bottom,
        1024 - profile.right_box.top,
    )
    sleeve_surface = (
        (sleeve_strength >= 0.24)
        & (z_fraction >= 0.58)
        & (z_fraction < 0.79)
    )
    front_u = silhouette_u(
        projections["front"], coordinates[:, 0], x_lower, x_upper, front_v
    )
    back_u = silhouette_u(
        projections["back"],
        coordinates[:, 0],
        x_lower,
        x_upper,
        back_v,
        flip=True,
    )
    front_colors = sample_array(
        projections["front"][0],
        front_u,
        front_v,
    )
    back_colors = sample_array(
        projections["back"][0],
        back_u,
        back_v,
    )
    right_u = silhouette_u(
        projections["right"], coordinates[:, 1], y_lower, y_upper, side_v
    )
    left_u = silhouette_u(
        projections["right"],
        coordinates[:, 1],
        y_lower,
        y_upper,
        side_v,
        flip=True,
    )
    sleeve_y_lower, sleeve_y_upper = contour_spans(
        coordinates[:, 1],
        sleeve_surface,
        smoothing_radius=2,
        smoothing_passes=1,
    )
    right_sleeve_u = silhouette_u(
        projections["right"],
        coordinates[:, 1],
        sleeve_y_lower,
        sleeve_y_upper,
        side_v,
        source_start=0.53,
        source_end=0.92,
    )
    left_sleeve_u = silhouette_u(
        projections["right"],
        coordinates[:, 1],
        sleeve_y_lower,
        sleeve_y_upper,
        side_v,
        flip=True,
        source_start=0.53,
        source_end=0.92,
    )
    right_u = np.where(sleeve_surface, right_sleeve_u, right_u)
    left_u = np.where(sleeve_surface, left_sleeve_u, left_u)
    right_colors = sample_array(
        projections["right"][0],
        right_u,
        side_v,
    )
    left_colors = sample_array(
        projections["right"][0],
        left_u,
        side_v,
    )

    facings = np.stack(
        (-normals[:, 1], normals[:, 1], normals[:, 0], -normals[:, 0]), axis=1
    )
    facings = np.clip(facings, 0.0, None)
    weights = np.where(facings >= 0.01, (facings + 0.08) ** 4.0, 0.0)

    # A pure side photograph only contains the outer arm/leg.  Without this
    # approximate visibility gate, its hand pixels get painted onto the torso
    # and its foreground leg gets repeated on the hidden leg.  The head stays
    # ungated because its profile is a single connected silhouette.
    x_span = np.maximum(x_upper - x_lower, 1e-8)
    right_gate = np.clip(
        (coordinates[:, 0] - (x_lower + x_span * 0.52)) / (x_span * 0.48), 0.0, 1.0
    )
    left_gate = np.clip(
        ((x_upper - x_span * 0.52) - coordinates[:, 0]) / (x_span * 0.48), 0.0, 1.0
    )
    head_region = head_strength >= 0.40
    right_gate[head_region] = 1.0
    left_gate[head_region] = 1.0
    weights[:, 2] *= right_gate * right_gate
    weights[:, 3] *= left_gate * left_gate

    # The profile sheet contains only the near arm, superimposed over the
    # torso.  Applying it to both A-pose arms creates large teal/linen holes and
    # dirty hands.  On arm-weighted surfaces, use the clean front/back sheets
    # as the main source and retain only a little profile information.
    arm_surface = (arm_strength >= 0.24) & (z_fraction < 0.79)
    front_back_arm_surface = arm_surface & ~sleeve_surface
    projection_y_center = (minimum.y + maximum.y) * 0.5
    projection_y_span = max(maximum.y - minimum.y, 1e-8)
    front_position = np.clip(
        (projection_y_center - coordinates[:, 1]) / (projection_y_span * 0.5), 0.0, 1.0
    )
    back_position = np.clip(
        (coordinates[:, 1] - projection_y_center) / (projection_y_span * 0.5), 0.0, 1.0
    )
    weights[front_back_arm_surface, 2:4] *= 0.06
    weights[front_back_arm_surface, 0] += 0.20 + 0.62 * front_position[front_back_arm_surface]
    weights[front_back_arm_surface, 1] += 0.20 + 0.62 * back_position[front_back_arm_surface]
    total_weights = np.sum(weights, axis=1, keepdims=True)
    colors = (
        front_colors * weights[:, 0:1]
        + back_colors * weights[:, 1:2]
        + right_colors * weights[:, 2:3]
        + left_colors * weights[:, 3:4]
    )
    zero_weight = total_weights[:, 0] < 1e-8
    colors /= np.maximum(total_weights, 1e-8)
    colors[zero_weight] = front_colors[zero_weight]
    colors = np.clip(colors, 0.0, 1.0)

    # Repair the two repeatable multi-view failures without flattening valid
    # cloth/skin shading: teal torso pixels inside the linen sleeve tier, and
    # cool/black padding pixels on the hands.  Each replacement hue is measured
    # from valid projected pixels on the same character.
    projected_luminance = np.mean(colors, axis=1)
    projected_saturation = np.max(colors, axis=1) - np.min(colors, axis=1)
    linen_low, linen_high = (
        (0.64, 0.725) if profile.key == "male" else (0.60, 0.67)
    )
    linen_band = (
        (sleeve_strength >= 0.32)
        & (z_fraction >= linen_low)
        & (z_fraction <= linen_high)
    )
    cool_sleeve_outlier = (
        linen_band
        & (colors[:, 1] > colors[:, 0])
        & (colors[:, 2] > colors[:, 0])
        & (projected_luminance < 0.52)
    )
    if np.any(cool_sleeve_outlier):
        linen_hue = np.array(
            (0.62, 0.55, 0.45) if profile.key == "male" else (0.65, 0.58, 0.49),
            dtype=np.float32,
        )
        linen_hue /= float(np.mean(linen_hue))
        linen_luminance = np.clip(
            projected_luminance[cool_sleeve_outlier], 0.30, 0.52
        )
        colors[cool_sleeve_outlier] = linen_hue * linen_luminance[:, None]

    projection_x_center = (minimum.x + maximum.x) * 0.5
    projection_width = maximum.x - minimum.x
    hand_low, hand_high = (
        (0.42, 0.61) if profile.key == "male" else (0.435, 0.61)
    )
    hand_surface = (
        (arm_strength >= 0.24)
        & (z_fraction >= hand_low)
        & (z_fraction <= hand_high)
        & (np.abs(coordinates[:, 0] - projection_x_center) > projection_width * 0.28)
    )
    cool_hand = (
        hand_surface
        & (colors[:, 1] > colors[:, 0] * 1.02)
        & (colors[:, 2] > colors[:, 0] * 1.02)
    )
    distal_hand_surface = hand_surface & (
        np.abs(coordinates[:, 0] - projection_x_center) > projection_width * 0.42
    )
    black_hand = hand_surface & (projected_luminance < 0.075)
    black_hand |= distal_hand_surface & (projected_luminance < 0.20)
    background_hand = (
        hand_surface
        & (projected_luminance > 0.82)
        & (projected_saturation < 0.06)
    )
    hand_outlier = cool_hand | black_hand | background_hand
    if np.any(hand_outlier):
        skin_hue = np.array(
            (0.72, 0.50, 0.36) if profile.key == "male" else (0.82, 0.64, 0.54),
            dtype=np.float32,
        )
        skin_hue /= float(np.mean(skin_hue))
        skin_limits = (0.42, 0.62) if profile.key == "male" else (0.52, 0.72)
        skin_luminance = np.clip(
            projected_luminance[hand_outlier], skin_limits[0], skin_limits[1]
        )
        colors[hand_outlier] = skin_hue * skin_luminance[:, None]
    colors = np.clip(colors, 0.0, 1.0)

    # Reject colors which can only have come from an occluding limb or the
    # studio backdrop.  The multi-view sheets overlap arms with the torso and
    # legs in projection; these spatial material guards keep that information
    # on the limb which owns it instead of painting pale copies across cloth.
    x_center = (minimum.x + maximum.x) * 0.5
    y_center = (minimum.y + maximum.y) * 0.5
    full_width = maximum.x - minimum.x
    abs_x = np.abs(coordinates[:, 0] - x_center)
    luminance = np.mean(colors, axis=1)
    saturation = np.max(colors, axis=1) - np.min(colors, axis=1)

    leg_region = (
        (z_fraction >= 0.12)
        & (z_fraction <= 0.495)
        & (abs_x <= full_width * 0.40)
        & (arm_strength < 0.20)
    )
    charcoal = np.array((0.185, 0.182, 0.180), dtype=np.float32)
    charcoal_variation = (
        0.82 + 0.34 * np.clip(luminance[leg_region] / 0.30, 0.0, 1.0)
    )[:, None]
    colors[leg_region] = charcoal * charcoal_variation

    boot_region = (z_fraction < 0.14) & (abs_x <= full_width * 0.30)
    boot_brown = np.array((0.225, 0.175, 0.145), dtype=np.float32)
    boot_outlier = boot_region & (luminance > 0.40)
    colors[boot_outlier] = boot_brown

    skin_like = (
        (colors[:, 0] > colors[:, 1] * 1.10)
        & (colors[:, 1] > colors[:, 2] * 1.02)
        & (luminance > 0.34)
    )
    lower_tunic = (
        (z_fraction >= 0.495)
        & (z_fraction < 0.62)
        & (abs_x <= full_width * 0.43)
    )
    upper_tunic = (
        (z_fraction >= 0.62)
        & (z_fraction <= 0.83)
        & (abs_x <= full_width * 0.30)
    )
    tunic_region = lower_tunic | upper_tunic
    protect_front_trim = abs_x <= full_width * 0.055
    protect_belt = (z_fraction >= 0.555) & (z_fraction <= 0.625)
    gold_like = (
        (colors[:, 0] > colors[:, 1] * 1.08)
        & (colors[:, 1] > colors[:, 2] * 1.18)
        & (luminance < 0.52)
        & (saturation > 0.075)
    )
    tunic_outlier = (
        tunic_region
        & skin_like
        & ~protect_front_trim
        & ~protect_belt
        & ~gold_like
        & (arm_strength < 0.20)
    )
    teal = np.array((0.125, 0.235, 0.245), dtype=np.float32)
    colors[tunic_outlier] = teal

    # Hair occupies the top/back shell.  Any near-neutral bright value there is
    # background leakage, never skin or linen.
    crown_hair = z_fraction >= 0.945
    hair_outlier = (
        crown_hair
        & (np.mean(colors, axis=1) > 0.44)
        & (saturation < 0.22)
    )
    hair_brown = np.array(
        (0.160, 0.105, 0.075) if profile.key == "male" else (0.255, 0.105, 0.088),
        dtype=np.float32,
    )
    colors[hair_outlier] = hair_brown
    rear_head = (
        (head_strength >= 0.48)
        & (coordinates[:, 1] >= y_center + 0.015)
        & (z_fraction >= 0.84)
    )
    rear_leak = rear_head & (np.mean(colors, axis=1) > 0.42)
    colors[rear_leak] = hair_brown
    if profile.key == "female":
        female_front_forehead = (
            (head_strength >= 0.48)
            & (z_fraction >= 0.90)
            & (z_fraction <= 0.955)
            & (coordinates[:, 1] <= y_center - 0.02)
        )
        colors[female_front_forehead] = front_colors[female_front_forehead]

    rgba_colors = np.ones((vertex_count, 4), dtype=np.float32)
    rgba_colors[:, :3] = colors
    color_layer.data.foreach_set("color_srgb", rgba_colors.reshape(-1))

    for polygon in mesh.polygons:
        polygon.material_index = 0
        polygon.use_smooth = True
    mesh.update()


def remove_source_objects(candidate: bpy.types.Object, armature: bpy.types.Object) -> None:
    # Strip MPFB's viewport-only custom bone shapes from the editable source.
    # Blender's glTF importer may create its own display-only Icosphere later;
    # that helper lives in ``glTF_not_exported`` and is not a GLB primitive.
    for pose_bone in armature.pose.bones:
        pose_bone.custom_shape = None
    for obj in list(bpy.context.scene.objects):
        if obj not in {candidate, armature}:
            bpy.data.objects.remove(obj, do_unlink=True)


def validate_asset(candidate: bpy.types.Object, armature: bpy.types.Object) -> None:
    if len(candidate.data.vertices) < 100_000:
        raise RuntimeError("The reference surface unexpectedly lost reconstruction detail")
    reference_color = candidate.data.color_attributes.get("ReferenceColor")
    if (
        len(candidate.data.materials) != 1
        or reference_color is None
        or reference_color.domain != "POINT"
    ):
        raise RuntimeError("Reference projection is incomplete")
    armature_modifiers = [modifier for modifier in candidate.modifiers if modifier.type == "ARMATURE"]
    if len(armature_modifiers) != 1 or armature_modifiers[0].object != armature:
        raise RuntimeError("Game-rig modifier is missing")

    unweighted = 0
    over_limit = 0
    for vertex in candidate.data.vertices:
        weights = [item.weight for item in vertex.groups if item.weight > 1e-6]
        if not weights:
            unweighted += 1
        if len(weights) > 4:
            over_limit += 1
    if unweighted or over_limit:
        raise RuntimeError(f"Invalid weights: unweighted={unweighted}, over_limit={over_limit}")
    print(
        f"V4_VALIDATE mesh={candidate.name} verts={len(candidate.data.vertices)} "
        f"tris={sum(len(poly.vertices) - 2 for poly in candidate.data.polygons)} "
        f"bones={len(armature.data.bones)} groups={len(candidate.vertex_groups)}"
    )


def look_at(camera: bpy.types.Object, target: Vector) -> None:
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def setup_render(candidate: bpy.types.Object) -> tuple[bpy.types.Object, Vector, float]:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("V4_Preview_World")
    scene.world.color = (0.68, 0.66, 0.64)

    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.0

    minimum, maximum = world_bounds(candidate)
    center = (minimum + maximum) * 0.5
    height = maximum.z - minimum.z

    bpy.ops.object.light_add(type="AREA", location=(2.8, -3.8, maximum.z + 1.6))
    key = bpy.context.object
    key.name = "V4_Key_Light"
    key.data.energy = 540.0
    key.data.shape = "DISK"
    key.data.size = 4.5
    look_at(key, center)

    bpy.ops.object.light_add(type="AREA", location=(-3.0, 1.4, center.z + 1.0))
    fill = bpy.context.object
    fill.name = "V4_Fill_Light"
    fill.data.energy = 260.0
    fill.data.size = 4.0
    look_at(fill, center)

    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = "V4_Preview_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = height * 1.08
    camera.data.lens = 55.0
    scene.camera = camera
    return camera, center, height


def render_previews(
    candidate: bpy.types.Object,
    profile: CharacterProfile,
    preview_dir: Path,
) -> list[Path]:
    camera, center, height = setup_render(candidate)
    distance = height * 2.8
    views = {
        "front": Vector((center.x, center.y - distance, center.z)),
        "right-side": Vector((center.x + distance, center.y, center.z)),
        "back": Vector((center.x, center.y + distance, center.z)),
        "three-quarter": Vector((center.x + distance * 0.72, center.y - distance * 0.72, center.z)),
    }
    preview_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for label, location in views.items():
        camera.location = location
        look_at(camera, center)
        path = preview_dir / f"{profile.slug}-{label}.png"
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        paths.append(path)
    return paths


def save_and_export(
    candidate: bpy.types.Object,
    armature: bpy.types.Object,
    profile: CharacterProfile,
    locations: OutputLocations,
) -> tuple[Path, Path]:
    locations.source_dir.mkdir(parents=True, exist_ok=True)
    locations.model_dir.mkdir(parents=True, exist_ok=True)
    blend_path = locations.source_dir / f"{profile.slug}.blend"
    glb_path = locations.model_dir / f"{profile.slug}.glb"

    candidate["reference_projection"] = "front/right/back turnaround pixels"
    candidate["reconstruction_source"] = profile.candidate_file
    candidate["rig_source"] = profile.base_file
    if locations.revision:
        candidate["model_history_revision"] = locations.revision
    armature.name = f"{profile.slug}.Rig"
    armature.data.name = f"{profile.slug}.RigData"

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.object.select_all(action="DESELECT")
    candidate.select_set(True)
    armature.select_set(True)
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


def build_character(
    profile: CharacterProfile,
    *,
    skip_render: bool,
    locations: OutputLocations,
) -> dict[str, object]:
    ensure_paths(profile)
    bpy.ops.wm.open_mainfile(filepath=str(WORK_DIR / profile.base_file))
    body = find_body()
    armature = find_armature()
    candidate = import_candidate(profile)
    align_candidate(candidate, body)
    transfer_game_rig(candidate, body, armature)
    apply_reference_projection(candidate, profile)
    remove_source_objects(candidate, armature)
    validate_asset(candidate, armature)
    preview_paths = (
        []
        if skip_render
        else render_previews(candidate, profile, locations.preview_dir)
    )
    blend_path, glb_path = save_and_export(candidate, armature, profile, locations)
    print(
        f"V4_DONE character={profile.key} blend={blend_path} glb={glb_path} "
        f"previews={','.join(str(path) for path in preview_paths)}"
    )
    return {
        "character": profile.key,
        "blend": str(blend_path.relative_to(PROJECT_ROOT)),
        "glb": str(glb_path.relative_to(PROJECT_ROOT)),
        "previews": [str(path.relative_to(PROJECT_ROOT)) for path in preview_paths],
        "vertices": len(candidate.data.vertices),
        "triangles": sum(len(poly.vertices) - 2 for poly in candidate.data.polygons),
        "bones": len(armature.data.bones),
    }


def write_revision_record(
    revision: str,
    *,
    note: str,
    status: str,
    results: list[dict[str, object]],
) -> None:
    revision_dir = HISTORY_DIR / revision
    revision_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "revision": revision,
        "status": status,
        "note": note,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "pipeline": str(Path(__file__).resolve().relative_to(PROJECT_ROOT)),
        "characters": results,
    }
    (revision_dir / "build.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    locations = output_locations(args.revision)
    selected = CHARACTERS if args.character == "all" else tuple(
        profile for profile in CHARACTERS if profile.key == args.character
    )
    results = []
    for profile in selected:
        results.append(
            build_character(
                profile,
                skip_render=args.skip_render,
                locations=locations,
            )
        )
    if args.revision:
        write_revision_record(
            args.revision,
            note=args.revision_note,
            status=args.revision_status,
            results=results,
        )


if __name__ == "__main__":
    main()
