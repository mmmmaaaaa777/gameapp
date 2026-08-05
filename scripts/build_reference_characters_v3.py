"""Build the v3 reference-matched guild trainees on MPFB human bases.

This script deliberately treats the turnaround sheets as reconstruction drawings:
the anatomically complete MPFB mesh supplies the body, hands, face and deformation
topology, while every visible garment and hairstyle is rebuilt as a separate mesh.

Run after ``generate_mpfb_character_bases_v3.py``:

    & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" `
      --background --python scripts\\build_reference_characters_v3.py

The generated GLBs are intentionally detailed source assets.  A later LOD pass can
reduce them after the reference match has been approved.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import bpy
from mathutils import Matrix, Vector


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = PROJECT_ROOT / "art-source" / "characters" / "work" / "v3"
SOURCE_DIR = PROJECT_ROOT / "art-source" / "characters"
MODEL_DIR = PROJECT_ROOT / "public" / "models" / "characters"
PREVIEW_DIR = (
    PROJECT_ROOT / "docs" / "character-concepts" / "model-previews" / "v3"
)


@dataclass(frozen=True)
class CharacterSpec:
    key: str
    slug: str
    base_file: str
    female: bool
    reference_file: str
    hair_hex: str
    hair_highlight_hex: str


CHARACTERS = (
    CharacterSpec(
        key="male",
        slug="initial-male-v3",
        base_file="initial-male-base.blend",
        female=False,
        reference_file="initial-male-turnaround.png",
        hair_hex="2A201B",
        hair_highlight_hex="49352C",
    ),
    CharacterSpec(
        key="female",
        slug="initial-female-v3",
        base_file="initial-female-base.blend",
        female=True,
        reference_file="initial-female-turnaround.png",
        hair_hex="45211F",
        hair_highlight_hex="68332F",
    ),
)


def srgb_channel(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def hex_color(value: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    value = value.removeprefix("#")
    rgb = [int(value[index : index + 2], 16) / 255.0 for index in (0, 2, 4)]
    return tuple(srgb_channel(channel) for channel in rgb) + (alpha,)


def principled_input(node: bpy.types.Node, *names: str):
    for name in names:
        if name in node.inputs:
            return node.inputs[name]
    return None


def create_pbr_material(
    name: str,
    base_hex: str,
    *,
    roughness: float,
    metallic: float = 0.0,
    texture_scale: float | None = None,
    bump_strength: float = 0.12,
    anisotropic: float = 0.0,
    specular_ior_level: float | None = None,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (520, 0)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (210, 0)
    color = hex_color(base_hex)
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    aniso = principled_input(shader, "Anisotropic IOR Level", "Anisotropic")
    if aniso is not None:
        aniso.default_value = anisotropic
    if specular_ior_level is not None:
        specular = principled_input(shader, "Specular IOR Level", "Specular")
        if specular is not None:
            specular.default_value = specular_ior_level
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    if texture_scale:
        texcoord = nodes.new("ShaderNodeTexCoord")
        texcoord.location = (-720, -120)
        noise = nodes.new("ShaderNodeTexNoise")
        noise.location = (-510, -120)
        noise.inputs["Scale"].default_value = texture_scale
        noise.inputs["Detail"].default_value = 5.0
        noise.inputs["Roughness"].default_value = 0.72
        bump = nodes.new("ShaderNodeBump")
        bump.location = (-60, -170)
        bump.inputs["Strength"].default_value = bump_strength
        bump.inputs["Distance"].default_value = 0.002
        links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])

    material.diffuse_color = color
    material["pbr_base_hex"] = base_hex
    material["pbr_roughness"] = roughness
    material["pbr_metallic"] = metallic
    return material


def create_materials(spec: CharacterSpec) -> dict[str, bpy.types.Material]:
    return {
        "teal": create_pbr_material(
            "V3_Guild_Teal_Woven", "172B2C", roughness=0.82, texture_scale=145.0
        ),
        "teal_dark": create_pbr_material(
            "V3_Guild_Teal_Shadow", "0E1D1E", roughness=0.86, texture_scale=135.0
        ),
        "linen": create_pbr_material(
            "V3_Undyed_Linen", "A99573", roughness=0.93, texture_scale=185.0
        ),
        "charcoal": create_pbr_material(
            "V3_Charcoal_Twill", "17191A", roughness=0.91, texture_scale=120.0
        ),
        "leather": create_pbr_material(
            "V3_Worn_Brown_Leather", "40332D", roughness=0.78, texture_scale=18.0
        ),
        "leather_dark": create_pbr_material(
            "V3_Dark_Leather_Edges", "211A17", roughness=0.87, texture_scale=22.0
        ),
        "sole": create_pbr_material(
            "V3_Boot_Sole", "0C0A09", roughness=0.96, texture_scale=15.0
        ),
        "bronze": create_pbr_material(
            "V3_Aged_Bronze", "7A552E", roughness=0.52, metallic=0.48, texture_scale=12.0
        ),
        "thread": create_pbr_material(
            "V3_Dark_Stitching", "181B1B", roughness=0.86, texture_scale=80.0
        ),
        "hair": create_pbr_material(
            "V3_Hair_Main",
            spec.hair_hex,
            roughness=0.76,
            anisotropic=0.14,
            specular_ior_level=0.22,
        ),
        "hair_highlight": create_pbr_material(
            "V3_Hair_Highlight",
            spec.hair_highlight_hex,
            roughness=0.72,
            anisotropic=0.18,
            specular_ior_level=0.24,
        ),
    }


def tune_skin_material(body: bpy.types.Object, spec: CharacterSpec) -> None:
    """Warm the neutral MPFB skin texture toward the painted turnaround."""

    tint = (1.0, 0.88, 0.79, 1.0) if spec.female else (1.0, 0.79, 0.66, 1.0)
    for slot in body.material_slots:
        material = slot.material
        if material is None or not material.use_nodes:
            continue
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        for shader in (node for node in nodes if node.type == "BSDF_PRINCIPLED"):
            base_color = shader.inputs.get("Base Color")
            if base_color is None or not base_color.is_linked:
                continue
            source_socket = base_color.links[0].from_socket
            links.remove(base_color.links[0])
            multiply = nodes.new("ShaderNodeMixRGB")
            multiply.name = "V3_Reference_Skin_Tint"
            multiply.label = "Reference skin warmth"
            multiply.blend_type = "MULTIPLY"
            multiply.inputs[0].default_value = 1.0
            multiply.inputs[2].default_value = tint
            multiply.location = (shader.location.x - 230.0, shader.location.y + 60.0)
            links.new(source_socket, multiply.inputs[1])
            links.new(multiply.outputs[0], base_color)
            shader.inputs["Roughness"].default_value = 0.58


def body_group_weight(body: bpy.types.Object, vertex_index: int, names: set[str]) -> float:
    vertex = body.data.vertices[vertex_index]
    return sum(
        item.weight
        for item in vertex.groups
        if body.vertex_groups[item.group].name in names
    )


def is_body_vertex(body: bpy.types.Object, vertex_index: int) -> bool:
    group = body.vertex_groups.get("body")
    if group is None:
        return True
    try:
        return group.weight(vertex_index) > 0.5
    except RuntimeError:
        return False


def find_body() -> bpy.types.Object:
    candidates = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and len(obj.data.vertices) > 10_000
    ]
    if not candidates:
        raise RuntimeError("MPFB basemesh not found in the base .blend")
    with_body_group = [obj for obj in candidates if obj.vertex_groups.get("body")]
    return max(with_body_group or candidates, key=lambda obj: len(obj.data.vertices))


def find_armature(body: bpy.types.Object) -> bpy.types.Object:
    for modifier in body.modifiers:
        if modifier.type == "ARMATURE" and modifier.object:
            return modifier.object
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise RuntimeError("MPFB game-engine armature not found")
    return armatures[0]


def bake_body_shape_mix(body: bpy.types.Object) -> None:
    """Bake the approved MPFB target mix before copying garment surfaces.

    ``Mesh.vertices`` stores the undeformed Basis coordinates while MPFB targets
    remain as shape keys.  Garments copied from those coordinates would therefore
    fit the neutral human instead of the character visible in the viewport.  The
    v3 source bases remain untouched on disk; only the opened working copy is baked.
    """

    shape_keys = body.data.shape_keys
    if shape_keys is None or len(shape_keys.key_blocks) <= 1:
        return
    bpy.ops.object.select_all(action="DESELECT")
    body.hide_set(False)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    body.data.update(calc_edges=True)
    bpy.context.view_layer.update()


@dataclass(frozen=True)
class BodyMetrics:
    z_min: float
    z_max: float
    height: float
    center_x: float
    center_y: float

    def z(self, normalized: float) -> float:
        return self.z_min + self.height * normalized

    def zn(self, z_value: float) -> float:
        return (z_value - self.z_min) / self.height


def measure_body(body: bpy.types.Object) -> BodyMetrics:
    points = [
        body.matrix_world @ vertex.co
        for vertex in body.data.vertices
        if is_body_vertex(body, vertex.index)
    ]
    if not points:
        raise RuntimeError("MPFB body vertex group is empty")
    x_min = min(point.x for point in points)
    x_max = max(point.x for point in points)
    y_min = min(point.y for point in points)
    y_max = max(point.y for point in points)
    z_min = min(point.z for point in points)
    z_max = max(point.z for point in points)
    return BodyMetrics(
        z_min=z_min,
        z_max=z_max,
        height=z_max - z_min,
        center_x=(x_min + x_max) * 0.5,
        center_y=(y_min + y_max) * 0.5,
    )


def mark_generated(obj: bpy.types.Object, spec: CharacterSpec, category: str) -> None:
    obj["v3_generated"] = True
    obj["model_version"] = "v3-reference-reconstruction"
    obj["category"] = category
    obj["source_reference"] = f"docs/character-concepts/{spec.reference_file}"


def smooth_object(obj: bpy.types.Object) -> None:
    if obj.type != "MESH":
        return
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def add_armature_modifier(obj: bpy.types.Object, armature: bpy.types.Object) -> None:
    modifier = next((item for item in obj.modifiers if item.type == "ARMATURE"), None)
    if modifier is None:
        modifier = obj.modifiers.new("V3_Armature", "ARMATURE")
    modifier.object = armature
    modifier.use_deform_preserve_volume = True
    obj.parent = armature
    obj.matrix_parent_inverse = armature.matrix_world.inverted()


FaceSelector = Callable[[bpy.types.MeshPolygon, Vector, float], bool]
OffsetFunction = Callable[[Vector, Vector, float], float]


def extract_body_shell(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: BodyMetrics,
    spec: CharacterSpec,
    name: str,
    material: bpy.types.Material,
    selector: FaceSelector,
    *,
    base_offset: float,
    thickness: float,
    category: str,
    offset_function: OffsetFunction | None = None,
) -> bpy.types.Object:
    """Copy selected MPFB skin faces and preserve their exact deformation weights."""

    normal_matrix = body.matrix_world.to_3x3()
    source_to_new: dict[int, int] = {}
    source_indices: list[int] = []
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    for polygon in body.data.polygons:
        if not all(is_body_vertex(body, index) for index in polygon.vertices):
            continue
        source_points = [body.matrix_world @ body.data.vertices[index].co for index in polygon.vertices]
        center = sum(source_points, Vector((0.0, 0.0, 0.0))) / len(source_points)
        normalized_z = metrics.zn(center.z)
        if not selector(polygon, center, normalized_z):
            continue

        face: list[int] = []
        for source_index in polygon.vertices:
            if source_index not in source_to_new:
                source_vertex = body.data.vertices[source_index]
                point = body.matrix_world @ source_vertex.co
                normal = (normal_matrix @ source_vertex.normal).normalized()
                extra = offset_function(point, normal, metrics.zn(point.z)) if offset_function else 0.0
                source_to_new[source_index] = len(vertices)
                source_indices.append(source_index)
                vertices.append(tuple(point + normal * (base_offset + extra)))
            face.append(source_to_new[source_index])
        faces.append(tuple(face))

    if not faces:
        raise RuntimeError(f"No faces selected for garment {name}")

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(clean_customdata=True)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)

    group_names: set[str] = set()
    for source_index in source_indices:
        for membership in body.data.vertices[source_index].groups:
            group_name = body.vertex_groups[membership.group].name
            if group_name in armature.data.bones:
                group_names.add(group_name)
    groups = {group_name: obj.vertex_groups.new(name=group_name) for group_name in sorted(group_names)}
    for new_index, source_index in enumerate(source_indices):
        weights: list[tuple[str, float]] = []
        for membership in body.data.vertices[source_index].groups:
            group_name = body.vertex_groups[membership.group].name
            if group_name in groups and membership.weight > 0.0001:
                weights.append((group_name, membership.weight))
        total = sum(weight for _name, weight in weights) or 1.0
        for group_name, weight in weights:
            groups[group_name].add([new_index], weight / total, "REPLACE")

    solidify = obj.modifiers.new("V3_Garment_Thickness", "SOLIDIFY")
    solidify.thickness = thickness
    solidify.offset = 0.0
    # Even-offset compensation becomes effectively unbounded around the tiny,
    # near-collinear triangles present at MakeHuman region boundaries.  It made
    # otherwise millimetre-thick shells shoot several metres across the render.
    solidify.use_even_offset = False
    bevel = obj.modifiers.new("V3_Soft_Garment_Edges", "BEVEL")
    bevel.width = min(thickness * 0.35, metrics.height * 0.0012)
    bevel.segments = 2
    add_armature_modifier(obj, armature)
    smooth_object(obj)
    mark_generated(obj, spec, category)
    return obj


def bone_points(
    armature: bpy.types.Object, body: bpy.types.Object, bone_name: str
) -> tuple[Vector, Vector]:
    bone = armature.data.bones[bone_name]
    head_world = armature.matrix_world @ bone.head_local
    tail_world = armature.matrix_world @ bone.tail_local
    return head_world, tail_world


def segment_projection(point: Vector, start: Vector, end: Vector) -> tuple[float, float]:
    delta = end - start
    length_squared = delta.length_squared
    if length_squared < 1e-12:
        return 0.0, (point - start).length
    t = (point - start).dot(delta) / length_squared
    projected = start + delta * max(0.0, min(1.0, t))
    return t, (point - projected).length


def arm_chain_parameter(
    point: Vector, upper: tuple[Vector, Vector], lower: tuple[Vector, Vector]
) -> tuple[float, float]:
    upper_t, upper_distance = segment_projection(point, *upper)
    lower_t, lower_distance = segment_projection(point, *lower)
    if upper_distance <= lower_distance:
        return upper_t, upper_distance
    return 1.0 + lower_t, lower_distance


def rigid_weights(obj: bpy.types.Object, armature: bpy.types.Object, bone_name: str) -> None:
    group = obj.vertex_groups.new(name=bone_name)
    group.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    add_armature_modifier(obj, armature)


def create_mesh_object(
    name: str,
    vertices: Iterable[tuple[float, float, float]],
    faces: Iterable[tuple[int, ...]],
    material: bpy.types.Material,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(list(vertices), [], list(faces))
    mesh.validate(clean_customdata=True)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    smooth_object(obj)
    return obj


def create_oval_band(
    name: str,
    center: Vector,
    half_width: float,
    front_depth: float,
    back_depth: float,
    height: float,
    material: bpy.types.Material,
    armature: bpy.types.Object,
    bone_name: str,
    spec: CharacterSpec,
    category: str,
    *,
    segments: int = 96,
    bevel: float = 0.0015,
) -> bpy.types.Object:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for z_offset in (-height * 0.5, height * 0.5):
        for index in range(segments):
            angle = math.tau * index / segments
            depth = front_depth if math.sin(angle) < 0.0 else back_depth
            vertices.append(
                (
                    center.x + half_width * math.cos(angle),
                    center.y + depth * math.sin(angle),
                    center.z + z_offset,
                )
            )
    for index in range(segments):
        nxt = (index + 1) % segments
        faces.append((index, nxt, segments + nxt, segments + index))
    obj = create_mesh_object(name, vertices, faces, material)
    solidify = obj.modifiers.new("V3_Band_Thickness", "SOLIDIFY")
    solidify.thickness = max(height * 0.08, 0.0015)
    solidify.offset = 0.0
    edge = obj.modifiers.new("V3_Band_Bevel", "BEVEL")
    edge.width = bevel
    edge.segments = 2
    rigid_weights(obj, armature, bone_name)
    mark_generated(obj, spec, category)
    return obj


def create_open_oval_band(
    name: str,
    center: Vector,
    half_width: float,
    front_depth: float,
    back_depth: float,
    height: float,
    material: bpy.types.Material,
    armature: bpy.types.Object,
    bone_name: str,
    spec: CharacterSpec,
    category: str,
    *,
    gap_angle: float = math.radians(24.0),
    segments: int = 80,
    bevel: float = 0.0015,
) -> bpy.types.Object:
    """Create a Mandarin-collar band with a deliberate opening at the throat."""

    start_angle = -math.pi * 0.5 + gap_angle
    end_angle = math.pi * 1.5 - gap_angle
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for z_offset in (-height * 0.5, height * 0.5):
        for index in range(segments + 1):
            angle = start_angle + (end_angle - start_angle) * index / segments
            depth = front_depth if math.sin(angle) < 0.0 else back_depth
            edge_factor = min(1.0, index / max(1.0, segments * 0.10), (segments - index) / max(1.0, segments * 0.10))
            edge_factor = edge_factor * edge_factor * (3.0 - 2.0 * edge_factor)
            local_z_offset = z_offset
            if z_offset < 0.0:
                local_z_offset += height * 0.48 * (1.0 - edge_factor)
            vertices.append(
                (
                    center.x + half_width * math.cos(angle),
                    center.y + depth * math.sin(angle),
                    center.z + local_z_offset,
                )
            )
    stride = segments + 1
    for index in range(segments):
        faces.append((index, index + 1, stride + index + 1, stride + index))
    obj = create_mesh_object(name, vertices, faces, material)
    solidify = obj.modifiers.new("V3_Open_Band_Thickness", "SOLIDIFY")
    solidify.thickness = max(height * 0.075, 0.0012)
    solidify.offset = 0.0
    solidify.use_even_offset = False
    edge = obj.modifiers.new("V3_Open_Band_Bevel", "BEVEL")
    edge.width = bevel
    edge.segments = 3
    rigid_weights(obj, armature, bone_name)
    mark_generated(obj, spec, category)
    return obj


def create_beveled_box(
    name: str,
    location: Vector,
    dimensions: Vector,
    material: bpy.types.Material,
    armature: bpy.types.Object,
    bone_name: str,
    spec: CharacterSpec,
    category: str,
    *,
    bevel: float,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    modifier = obj.modifiers.new("V3_Box_Bevel", "BEVEL")
    modifier.width = min(bevel, min(dimensions) * 0.46)
    modifier.segments = 5
    rigid_weights(obj, armature, bone_name)
    mark_generated(obj, spec, category)
    return obj


def create_curve_tube(
    name: str,
    coordinates: list[Vector],
    material: bpy.types.Material,
    armature: bpy.types.Object,
    bone_name: str,
    spec: CharacterSpec,
    category: str,
    *,
    bevel_depth: float,
    radii: list[float] | None = None,
    resolution: int = 2,
) -> bpy.types.Object:
    curve_data = bpy.data.curves.new(f"{name}_Curve", "CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = resolution
    curve_data.bevel_resolution = 3
    curve_data.bevel_depth = bevel_depth
    spline = curve_data.splines.new("NURBS")
    spline.points.add(len(coordinates) - 1)
    radii = radii or [1.0] * len(coordinates)
    for point, coordinate, radius in zip(spline.points, coordinates, radii, strict=True):
        point.co = (*coordinate, 1.0)
        point.radius = radius
    spline.order_u = min(3, len(coordinates))
    spline.use_endpoint_u = True
    curve_data.materials.append(material)
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    # object.convert acts on every selected object, not just the active curve.
    # Leaving the body or an earlier detail selected applies and removes its
    # rig, helper mask and subdivision modifiers as an accidental side effect.
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    rigid_weights(obj, armature, bone_name)
    smooth_object(obj)
    mark_generated(obj, spec, category)
    return obj


def torso_section_at(
    body: bpy.types.Object,
    metrics: BodyMetrics,
    normalized_z: float,
    band: float = 0.014,
    max_half_width: float = 0.18,
) -> tuple[float, float, float, float, float]:
    target_z = metrics.z(normalized_z)
    points = []
    for vertex in body.data.vertices:
        if not is_body_vertex(body, vertex.index):
            continue
        point = body.matrix_world @ vertex.co
        if (
            abs(point.z - target_z) <= metrics.height * band
            and abs(point.x - metrics.center_x) < metrics.height * max_half_width
        ):
            points.append(point)
    if not points:
        raise RuntimeError(f"No torso cross-section near z={normalized_z}")
    x_min = min(point.x for point in points)
    x_max = max(point.x for point in points)
    y_min = min(point.y for point in points)
    y_max = max(point.y for point in points)
    center_x = (x_min + x_max) * 0.5
    center_y = (y_min + y_max) * 0.5
    return center_x, center_y, (x_max - x_min) * 0.5, center_y - y_min, y_max - center_y


def create_skirt_panels(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: BodyMetrics,
    spec: CharacterSpec,
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    top_z = metrics.z(0.610 if spec.female else 0.515)
    bottom_z = metrics.z(0.505 if spec.female else 0.390)
    panel_section_z = 0.600 if spec.female else 0.50
    panel_center_x, panel_center_y, width, front, back = torso_section_at(
        body, metrics, panel_section_z
    )
    if spec.female:
        # The raised waistband is narrower/shallower than the upper hip.  Size
        # the lower edge from the hip section as well so the back panel clears
        # the gluteal silhouette instead of exposing two crescents of body.
        _hip_x, _hip_y, _hip_width, _hip_front, hip_back = torso_section_at(
            body, metrics, 0.515
        )
        back = max(back, hip_back * 1.08)
    width += metrics.height * (0.018 if spec.female else 0.007)
    front += metrics.height * (0.020 if spec.female else 0.009)
    back += metrics.height * (0.020 if spec.female else 0.009)
    flare = 1.22 if spec.female else 1.07
    center_gap = 0.050 if spec.female else 0.055
    panel_specs = (
        ("Back", -1.0, 1.0, 1.0, back, 40),
        ("Front_Left", -1.0, -center_gap, -1.0, front, 20),
        ("Front_Right", center_gap, 1.0, -1.0, front, 20),
    )
    objects: list[bpy.types.Object] = []
    vertical_segments = 10

    def panel_curvature(u: float) -> float:
        if spec.female:
            # Wrap the raised skirt around the waist instead of retaining an
            # almost full front/back depth at its side edges.  The small v6.18
            # minimum left a visible triangular opening between the front and
            # back pieces, so converge both edges at the side seam.
            return max(0.0, 1.0 - abs(u) ** 3.0) ** (1.0 / 3.0)
        return 0.875 + 0.125 * (1.0 - abs(u) ** 1.7)

    for label, u_start, u_end, depth_sign, depth, horizontal_segments in panel_specs:
        vertices: list[tuple[float, float, float]] = []
        faces: list[tuple[int, ...]] = []
        for vertical in range(vertical_segments + 1):
            v = vertical / vertical_segments
            z_value = top_z + (bottom_z - top_z) * v
            radial_scale = 1.0 + (flare - 1.0) * (v * v)
            for horizontal in range(horizontal_segments + 1):
                t = horizontal / horizontal_segments
                u = u_start + (u_end - u_start) * t
                curvature = panel_curvature(u)
                wrinkle = metrics.height * 0.0014 * math.sin(t * math.tau * 3.0 + v * 5.0) * v
                vertices.append(
                    (
                        panel_center_x + width * radial_scale * u,
                        panel_center_y + depth_sign * (depth * radial_scale * curvature + wrinkle),
                        z_value,
                    )
                )
        stride = horizontal_segments + 1
        for vertical in range(vertical_segments):
            for horizontal in range(horizontal_segments):
                start = vertical * stride + horizontal
                faces.append((start, start + 1, start + stride + 1, start + stride))
        panel = create_mesh_object(f"V3_Tunic_Panel_{label}", vertices, faces, materials["teal"])
        solidify = panel.modifiers.new("V3_Panel_Thickness", "SOLIDIFY")
        solidify.thickness = metrics.height * 0.0022
        solidify.offset = 0.0
        solidify.use_even_offset = False
        bevel = panel.modifiers.new("V3_Panel_Bevel", "BEVEL")
        bevel.width = metrics.height * 0.00065
        bevel.segments = 2
        rigid_weights(panel, armature, "pelvis")
        mark_generated(panel, spec, "tunic-skirt-panel")
        objects.append(panel)

        def panel_point(vertical: float, u: float) -> Vector:
            z_value = top_z + (bottom_z - top_z) * vertical
            radial_scale = 1.0 + (flare - 1.0) * vertical * vertical
            curvature = panel_curvature(u)
            return Vector(
                (
                    panel_center_x + width * radial_scale * u,
                    panel_center_y + depth_sign * depth * radial_scale * curvature,
                    z_value,
                )
            )

        for suffix, coordinates in (
            (
                "Bottom_Trim",
                [panel_point(1.0, u_start + (u_end - u_start) * index / 20) for index in range(21)],
            ),
            ("Start_Trim", [panel_point(index / 8, u_start) for index in range(9)]),
            ("End_Trim", [panel_point(index / 8, u_end) for index in range(9)]),
        ):
            objects.append(
                create_curve_tube(
                    f"V3_{label}_{suffix}",
                    coordinates,
                    materials["bronze"],
                    armature,
                    "pelvis",
                    spec,
                    "tunic-piping",
                    bevel_depth=metrics.height * 0.0009,
                )
            )

        if not spec.female:
            motif_edges: tuple[tuple[float, float], ...] = (
                ((u_start, 1.0), (u_end, -1.0))
                if label == "Back"
                else (((u_start, 1.0),) if label == "Front_Left" else ((u_end, -1.0),))
            )
            for motif_index, (outer_u, inward_direction) in enumerate(motif_edges, 1):
                motif_u = outer_u + inward_direction * 0.09
                motif_inner_u = outer_u + inward_direction * 0.24
                objects.append(
                    create_curve_tube(
                        f"V3_{label}_Corner_Embroidery_{motif_index}",
                        [
                            panel_point(0.76, motif_u),
                            panel_point(0.91, motif_u),
                            panel_point(0.91, motif_inner_u),
                        ],
                        materials["bronze"],
                        armature,
                        "pelvis",
                        spec,
                        "tunic-corner-embroidery",
                        bevel_depth=metrics.height * 0.00075,
                    )
                )

    return objects


def create_linen_front_insert(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: BodyMetrics,
    spec: CharacterSpec,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    section_x, section_y, width, front, _back = torso_section_at(body, metrics, 0.72)
    y = section_y - front - metrics.height * 0.009
    if spec.female:
        points = [
            (-0.010, 0.870),
            (0.021, 0.870),
            (0.010, 0.838),
            (0.003, 0.835),
        ]
    else:
        points = [
            (-0.010, 0.872),
            (0.022, 0.872),
            (0.010, 0.838),
            (0.002, 0.808),
        ]
    vertices = [
        (section_x + x * metrics.height, y, metrics.z(z)) for x, z in points
    ]
    obj = create_mesh_object(
        "V3_Linen_Collar_Insert", vertices, [(0, 1, 2, 3)], materials["linen"]
    )
    solidify = obj.modifiers.new("V3_Insert_Thickness", "SOLIDIFY")
    solidify.thickness = metrics.height * 0.002
    solidify.offset = 0.0
    rigid_weights(obj, armature, "spine_03")
    mark_generated(obj, spec, "inner-collar")
    return obj


def create_tunic_details(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: BodyMetrics,
    spec: CharacterSpec,
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    waist_norm = 0.630 if spec.female else 0.505
    waist_section_norm = 0.600 if spec.female else 0.515
    waist_x, waist_y, waist_width, waist_front, waist_back = torso_section_at(
        body, metrics, waist_section_norm
    )
    chest_x, chest_y, _chest_width, chest_front, chest_back = torso_section_at(body, metrics, 0.72)
    neck_x, neck_y, neck_width, neck_front, neck_back = torso_section_at(
        body, metrics, 0.835, band=0.010, max_half_width=0.080
    )
    neck_width = min(neck_width, metrics.height * 0.052)
    neck_front = min(neck_front, metrics.height * 0.055)
    neck_back = min(neck_back, metrics.height * 0.050)

    collar_gap = math.radians(14.0 if spec.female else 15.0)
    collar_height = metrics.height * (0.026 if spec.female else 0.034)
    collar_trim_height = metrics.height * (0.0055 if spec.female else 0.008)
    collar_top_norm = 0.873 if spec.female else 0.878
    collar_mid_norm = 0.858 if spec.female else 0.859
    collar_bottom_norm = 0.845 if spec.female else 0.841
    collar_center = Vector((neck_x, neck_y, metrics.z(0.858)))
    objects.append(
        create_open_oval_band(
            "V3_Standing_Collar_Teal",
            collar_center,
            neck_width * 1.045,
            neck_front * 1.055,
            neck_back * 1.055,
            collar_height,
            materials["teal"],
            armature,
            "neck_01",
            spec,
            "standing-collar-outer",
            gap_angle=collar_gap,
            bevel=metrics.height * 0.0011,
        )
    )
    objects.append(
        create_open_oval_band(
            "V3_Standing_Collar_Linen_Trim",
            Vector((neck_x, neck_y, metrics.z(0.873))),
            neck_width * 1.010,
            neck_front * 1.020,
            neck_back * 1.020,
            collar_trim_height,
            materials["linen"],
            armature,
            "neck_01",
            spec,
            "standing-collar-inner-trim",
            gap_angle=collar_gap * 1.04,
            bevel=metrics.height * 0.0007,
        )
    )

    collar_start = -math.pi * 0.5 + collar_gap
    collar_end = math.pi * 1.5 - collar_gap

    def collar_point(angle: float, z_norm: float, radial_scale: float = 1.07) -> Vector:
        depth = neck_front if math.sin(angle) < 0.0 else neck_back
        return Vector(
            (
                neck_x + neck_width * radial_scale * math.cos(angle),
                neck_y + depth * radial_scale * math.sin(angle),
                metrics.z(z_norm),
            )
        )

    objects.append(
        create_curve_tube(
            "V3_Standing_Collar_Top_Piping",
            [
                collar_point(
                    collar_start + (collar_end - collar_start) * index / 48,
                    collar_top_norm,
                )
                for index in range(49)
            ],
            materials["bronze"],
            armature,
            "neck_01",
            spec,
            "standing-collar-piping",
            bevel_depth=metrics.height * 0.0010,
        )
    )
    for side_index, angle in enumerate((collar_start, collar_end), 1):
        objects.append(
            create_curve_tube(
                f"V3_Standing_Collar_End_Piping_{side_index}",
                [
                    collar_point(angle, z_norm)
                    for z_norm in (collar_bottom_norm, collar_mid_norm, collar_top_norm)
                ],
                materials["bronze"],
                armature,
                "neck_01",
                spec,
                "standing-collar-piping",
                bevel_depth=metrics.height * 0.0009,
            )
        )

    objects.append(create_linen_front_insert(body, armature, metrics, spec, materials))
    front_y = chest_y - chest_front - metrics.height * 0.012
    if spec.female:
        placket = [
            Vector((chest_x + metrics.height * 0.025, front_y, metrics.z(0.845))),
            Vector((chest_x + metrics.height * 0.005, front_y, metrics.z(0.805))),
            Vector((chest_x - metrics.height * 0.006, front_y, metrics.z(0.690))),
            Vector((chest_x - metrics.height * 0.004, front_y, metrics.z(0.615))),
        ]
    else:
        placket = [
            Vector((chest_x + metrics.height * 0.033, front_y, metrics.z(0.845))),
            Vector((chest_x + metrics.height * 0.013, front_y, metrics.z(0.790))),
            Vector((chest_x - metrics.height * 0.007, front_y, metrics.z(0.710))),
            Vector((chest_x - metrics.height * 0.006, front_y, metrics.z(0.525))),
        ]
    objects.append(
        create_curve_tube(
            "V3_Asymmetric_Placket_Piping",
            placket,
            materials["bronze"],
            armature,
            "spine_03",
            spec,
            "front-placket-piping",
            bevel_depth=metrics.height * 0.00165,
        )
    )

    closure_zs = (0.800,) if spec.female else (0.785, 0.735, 0.685)
    for index, z_norm in enumerate(closure_zs, 1):
        z = metrics.z(z_norm)
        x_center = chest_x + metrics.height * (0.010 if spec.female else 0.004)
        span = metrics.height * (0.036 if spec.female else 0.046)
        knot_y = front_y - metrics.height * 0.004
        path = [
            Vector((x_center - span * 0.58, knot_y, z)),
            Vector((x_center - span * 0.22, knot_y, z + metrics.height * 0.007)),
            Vector((x_center, knot_y, z)),
            Vector((x_center + span * 0.22, knot_y, z - metrics.height * 0.007)),
            Vector((x_center + span * 0.58, knot_y, z)),
        ]
        objects.append(
            create_curve_tube(
                f"V3_Frog_Closure_{index}",
                path,
                materials["bronze"],
                armature,
                "spine_03",
                spec,
                "frog-closure",
                bevel_depth=metrics.height * 0.0021,
                radii=[0.75, 1.0, 1.20, 1.0, 0.75],
            )
        )
        objects.append(
            create_beveled_box(
                f"V3_Frog_Closure_Knot_{index}",
                Vector((x_center, knot_y - metrics.height * 0.0025, z)),
                Vector((metrics.height * 0.010, metrics.height * 0.006, metrics.height * 0.010)),
                materials["bronze"],
                armature,
                "spine_03",
                spec,
                "frog-closure-knot",
                bevel=metrics.height * 0.0025,
                rotation=(0.0, math.radians(45), 0.0),
            )
        )

    belt_center = Vector((waist_x, waist_y, metrics.z(waist_norm)))
    belt_extra = metrics.height * (0.012 if spec.female else 0.012)
    objects.append(
        create_oval_band(
            "V3_Leather_Waist_Sash",
            belt_center,
            waist_width + belt_extra,
            waist_front + belt_extra,
            waist_back + belt_extra,
            metrics.height * (0.050 if spec.female else 0.027),
            materials["leather"],
            armature,
            "pelvis",
            spec,
            "waist-sash",
            bevel=metrics.height * 0.0015,
        )
    )
    if not spec.female:
        objects.append(
            create_oval_band(
                "V3_Male_Lower_Belt",
                Vector((waist_x, waist_y, metrics.z(0.489))),
                waist_width + metrics.height * 0.005,
                waist_front + metrics.height * 0.005,
                waist_back + metrics.height * 0.005,
                metrics.height * 0.012,
                materials["leather_dark"],
                armature,
                "pelvis",
                spec,
                "secondary-belt",
                bevel=metrics.height * 0.0012,
            )
        )

    buckle_y = waist_y - waist_front - belt_extra - metrics.height * 0.010
    buckle_x = waist_x + (metrics.height * 0.038 if spec.female else 0.0)
    buckle = create_beveled_box(
        "V3_Belt_Buckle",
        Vector((buckle_x, buckle_y, metrics.z(waist_norm))),
        Vector(
            (
                metrics.height * (0.017 if spec.female else 0.027),
                metrics.height * 0.007,
                metrics.height * (0.017 if spec.female else 0.027),
            )
        ),
        materials["bronze"],
        armature,
        "pelvis",
        spec,
        "belt-buckle",
        bevel=metrics.height * 0.0025,
        rotation=(0.0, math.radians(45), 0.0),
    )
    objects.append(buckle)

    ornament_y = buckle_y - metrics.height * 0.006
    if spec.female:
        ornament_center_x = buckle_x
        ornament_width = metrics.height * 0.026
        ornament_height = metrics.height * 0.012
        ornament_paths = (
            [
                Vector((ornament_center_x - ornament_width, ornament_y, metrics.z(waist_norm))),
                Vector((ornament_center_x - ornament_width * 0.35, ornament_y, metrics.z(waist_norm) + ornament_height)),
                Vector((ornament_center_x, ornament_y, metrics.z(waist_norm))),
                Vector((ornament_center_x - ornament_width * 0.35, ornament_y, metrics.z(waist_norm) - ornament_height)),
                Vector((ornament_center_x - ornament_width, ornament_y, metrics.z(waist_norm))),
            ],
            [
                Vector((ornament_center_x, ornament_y, metrics.z(waist_norm))),
                Vector((ornament_center_x + ornament_width * 0.35, ornament_y, metrics.z(waist_norm) + ornament_height)),
                Vector((ornament_center_x + ornament_width, ornament_y, metrics.z(waist_norm))),
                Vector((ornament_center_x + ornament_width * 0.35, ornament_y, metrics.z(waist_norm) - ornament_height)),
                Vector((ornament_center_x, ornament_y, metrics.z(waist_norm))),
            ],
        )
    else:
        ornament_width = metrics.height * 0.032
        ornament_height = metrics.height * 0.014
        ornament_paths = tuple(
            [
                Vector((waist_x + direction * ornament_width * 1.45, ornament_y, metrics.z(waist_norm))),
                Vector((waist_x + direction * ornament_width * 0.70, ornament_y, metrics.z(waist_norm) + ornament_height)),
                Vector((waist_x, ornament_y, metrics.z(waist_norm))),
                Vector((waist_x + direction * ornament_width * 0.70, ornament_y, metrics.z(waist_norm) - ornament_height)),
                Vector((waist_x + direction * ornament_width * 1.45, ornament_y, metrics.z(waist_norm))),
            ]
            for direction in (-1.0, 1.0)
        )
    for index, path in enumerate(ornament_paths, 1):
        objects.append(
            create_curve_tube(
                f"V3_Belt_Ornament_{index}",
                path,
                materials["bronze"],
                armature,
                "pelvis",
                spec,
                "belt-ornament",
                bevel_depth=metrics.height * 0.00145,
            )
        )

    if spec.female:
        sash_surface_y = waist_y - waist_front - belt_extra - metrics.height * 0.002
        sash_half_span = waist_width * 0.82
        for index, z_shift in enumerate((-0.008, 0.006), 1):
            objects.append(
                create_curve_tube(
                    f"V3_Female_Sash_Diagonal_Stitch_{index}",
                    [
                        Vector((waist_x - sash_half_span, sash_surface_y, metrics.z(waist_norm + 0.014 + z_shift))),
                        Vector((waist_x, sash_surface_y, metrics.z(waist_norm + z_shift))),
                        Vector((waist_x + sash_half_span, sash_surface_y, metrics.z(waist_norm - 0.014 + z_shift))),
                    ],
                    materials["leather_dark"],
                    armature,
                    "pelvis",
                    spec,
                    "female-sash-stitching",
                    bevel_depth=metrics.height * 0.00065,
                )
            )

    back_y = chest_y + chest_back + metrics.height * 0.010
    objects.append(
        create_curve_tube(
            "V3_Back_Center_Seam",
            [
                Vector((chest_x, back_y, metrics.z(0.825))),
                Vector((chest_x, back_y, metrics.z(0.675))),
                Vector((chest_x, back_y, metrics.z(0.615 if spec.female else 0.525))),
            ],
            materials["thread"],
            armature,
            "spine_03",
            spec,
            "back-seam",
            bevel_depth=metrics.height * 0.00075,
        )
    )

    if not spec.female:
        cross_z = metrics.z(0.835)
        ornament_y = neck_y + neck_back + metrics.height * 0.008
        objects.extend(
            [
                create_curve_tube(
                    "V3_Back_Collar_Ornament_H",
                    [
                        Vector((neck_x - metrics.height * 0.015, ornament_y, cross_z)),
                        Vector((neck_x, ornament_y, cross_z + metrics.height * 0.009)),
                        Vector((neck_x + metrics.height * 0.015, ornament_y, cross_z)),
                    ],
                    materials["bronze"],
                    armature,
                    "neck_01",
                    spec,
                    "back-collar-ornament",
                    bevel_depth=metrics.height * 0.0016,
                ),
                create_curve_tube(
                    "V3_Back_Collar_Ornament_V",
                    [
                        Vector((neck_x, ornament_y, cross_z - metrics.height * 0.012)),
                        Vector((neck_x, ornament_y, cross_z + metrics.height * 0.013)),
                    ],
                    materials["bronze"],
                    armature,
                    "neck_01",
                    spec,
                    "back-collar-ornament",
                    bevel_depth=metrics.height * 0.0016,
                ),
            ]
        )

    return objects


def cubic_bezier(a: Vector, b: Vector, c: Vector, d: Vector, t: float) -> Vector:
    u = 1.0 - t
    return a * (u**3) + b * (3.0 * u * u * t) + c * (3.0 * u * t * t) + d * (t**3)


def append_tapered_clump(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    controls: tuple[Vector, Vector, Vector, Vector],
    width: float,
    thickness: float,
    *,
    rings: int = 10,
    sides: int = 6,
    tip_fraction: float = 0.035,
    taper_power: float = 0.55,
) -> None:
    base_index = len(vertices)
    previous_side = Vector((1.0, 0.0, 0.0))
    for ring in range(rings):
        t = ring / (rings - 1)
        center = cubic_bezier(*controls, t)
        t2 = min(1.0, t + 0.01)
        tangent = (cubic_bezier(*controls, t2) - center).normalized()
        side = tangent.cross(Vector((0.0, 0.0, 1.0)))
        if side.length < 0.01:
            side = previous_side.copy()
        else:
            side.normalize()
        if side.dot(previous_side) < 0.0:
            side.negate()
        up = tangent.cross(side).normalized()
        previous_side = side.copy()
        taper = max(tip_fraction, (1.0 - t) ** taper_power)
        for segment in range(sides):
            angle = math.tau * segment / sides
            point = (
                center
                + side * math.cos(angle) * width * taper
                + up * math.sin(angle) * thickness * taper
            )
            vertices.append(tuple(point))
    for ring in range(rings - 1):
        start = base_index + ring * sides
        following = start + sides
        for segment in range(sides):
            nxt = (segment + 1) % sides
            faces.append((start + segment, start + nxt, following + nxt, following + segment))
    faces.append(tuple(base_index + segment for segment in reversed(range(sides))))
    end = base_index + (rings - 1) * sides
    faces.append(tuple(end + segment for segment in range(sides)))


def create_hair(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: BodyMetrics,
    spec: CharacterSpec,
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    scalp_names = {"scalp"}

    head_vertices = [
        body.matrix_world @ vertex.co
        for vertex in body.data.vertices
        if is_body_vertex(body, vertex.index)
        and body_group_weight(body, vertex.index, scalp_names) > 0.50
    ]
    if not head_vertices:
        raise RuntimeError("Head vertex set is empty; cannot construct reference hair")
    head_x_min = min(point.x for point in head_vertices)
    head_x_max = max(point.x for point in head_vertices)
    head_y_min = min(point.y for point in head_vertices)
    head_y_max = max(point.y for point in head_vertices)
    z_bottom = min(point.z for point in head_vertices)
    z_top = max(point.z for point in head_vertices)
    head_center_x = (head_x_min + head_x_max) * 0.5
    head_center_y = (head_y_min + head_y_max) * 0.5
    x_radius = (head_x_max - head_x_min) * 0.535
    y_front = head_center_y - head_y_min
    y_back = head_y_max - head_center_y
    center = Vector((head_center_x, head_center_y, (z_bottom + z_top) * 0.5))
    z_radius = (z_top - z_bottom) * 0.535

    def scalp_selector(poly, center: Vector, zn: float) -> bool:
        weights = [body_group_weight(body, index, scalp_names) for index in poly.vertices]
        return sum(weight > 0.50 for weight in weights) >= len(weights) - 1

    cap = extract_body_shell(
        body,
        armature,
        metrics,
        spec,
        "V3_Sculpted_Hair_Cap",
        materials["hair"],
        scalp_selector,
        base_offset=metrics.height * 0.0019,
        thickness=metrics.height * 0.0011,
        category="hair-cap",
    )

    def head_surface(azimuth: float, polar: float, lift: float = 0.0) -> Vector:
        radial = math.sin(polar)
        depth = y_back if math.sin(azimuth) > 0.0 else y_front
        point = Vector(
            (
                center.x + x_radius * radial * math.cos(azimuth),
                center.y + depth * radial * math.sin(azimuth),
                center.z + z_radius * math.cos(polar),
            )
        )
        normal = Vector(
            (
                (point.x - center.x) / max(x_radius * x_radius, 1e-8),
                (point.y - center.y) / max(depth * depth, 1e-8),
                (point.z - center.z) / max(z_radius * z_radius, 1e-8),
            )
        ).normalized()
        return point + normal * lift

    def surface_controls(
        root_azimuth: float,
        root_polar: float,
        tip_azimuth: float,
        tip_polar: float,
        root_lift: float,
        crest_lift: float,
        tip_lift: float,
    ) -> tuple[Vector, Vector, Vector, Vector]:
        azimuth_delta = tip_azimuth - root_azimuth
        while azimuth_delta > math.pi:
            azimuth_delta -= math.tau
        while azimuth_delta < -math.pi:
            azimuth_delta += math.tau
        root = head_surface(root_azimuth, root_polar, root_lift)
        first = head_surface(
            root_azimuth + azimuth_delta * 0.34,
            root_polar + (tip_polar - root_polar) * 0.34,
            crest_lift,
        )
        second = head_surface(
            root_azimuth + azimuth_delta * 0.72,
            root_polar + (tip_polar - root_polar) * 0.72,
            crest_lift * 0.75,
        )
        tip = head_surface(tip_azimuth, tip_polar, tip_lift)
        return root, first, second, tip

    rng = random.Random(5107 if spec.female else 3109)
    main_vertices: list[tuple[float, float, float]] = []
    main_faces: list[tuple[int, ...]] = []
    highlight_vertices: list[tuple[float, float, float]] = []
    highlight_faces: list[tuple[int, ...]] = []

    clump_index = 0

    def add_clump(
        controls: tuple[Vector, Vector, Vector, Vector],
        width: float,
        thickness: float,
        rings: int,
        *,
        tip_fraction: float = 0.035,
        taper_power: float = 0.55,
    ) -> None:
        nonlocal clump_index
        target_vertices, target_faces = (
            (highlight_vertices, highlight_faces)
            if clump_index % (11 if spec.female else 10) == 0
            else (main_vertices, main_faces)
        )
        append_tapered_clump(
            target_vertices,
            target_faces,
            controls,
            width,
            thickness,
            rings=rings,
            tip_fraction=tip_fraction,
            taper_power=taper_power,
        )
        clump_index += 1

    if spec.female:
        # Layered jaw-length bob: broad, flattened locks descend from a soft
        # centre part and bend around the cheeks instead of projecting radially.
        for index in range(132):
            azimuth = math.tau * index / 132 + rng.uniform(-0.025, 0.025)
            root_polar = rng.uniform(0.34, 0.84)
            front_region = math.sin(azimuth) < -0.38
            side_sign = 1.0 if math.cos(azimuth) >= 0.0 else -1.0
            root_azimuth = azimuth + side_sign * rng.uniform(0.035, 0.11)
            root = head_surface(root_azimuth, root_polar, metrics.height * 0.0060)
            local_depth = y_back if math.sin(azimuth) > 0.0 else y_front
            if front_region:
                target_x = center.x + side_sign * x_radius * rng.uniform(0.78, 1.02)
                target_y = center.y - y_front * rng.uniform(0.70, 0.88)
                target_z = metrics.z(rng.uniform(0.872, 0.894))
            else:
                target_x = center.x + x_radius * rng.uniform(1.00, 1.12) * math.cos(azimuth)
                target_y = center.y + local_depth * rng.uniform(0.92, 1.08) * math.sin(azimuth)
                target_z = metrics.z(rng.uniform(0.858, 0.886))
            target = Vector((target_x, target_y, target_z))
            first = root.lerp(
                head_surface(azimuth, min(1.18, root_polar + 0.42), metrics.height * 0.018),
                0.74,
            )
            second = target + Vector(
                (
                    -side_sign * metrics.height * 0.006 if front_region else -math.cos(azimuth) * metrics.height * 0.006,
                    -math.sin(azimuth) * metrics.height * 0.004,
                    metrics.height * 0.020,
                )
            )
            tip = target + Vector(
                (
                    side_sign * metrics.height * rng.uniform(0.001, 0.006),
                    -metrics.height * rng.uniform(0.001, 0.005),
                    metrics.height * rng.uniform(-0.006, 0.006),
                )
            )
            add_clump(
                (root, first, second, tip),
                metrics.height * rng.uniform(0.0052, 0.0082),
                metrics.height * rng.uniform(0.00065, 0.0010),
                13,
                tip_fraction=0.22,
                taper_power=0.34,
            )

        # Side-parted face-framing locks sweep away from the centre of the
        # forehead and retain width until their jaw-length tips.
        for index in range(32):
            u = -1.0 + 2.0 * index / 31
            side_sign = -1.0 if u < -0.10 else 1.0
            root_azimuth = -math.pi * 0.5 + u * 0.22
            root = head_surface(
                root_azimuth,
                0.20 + 0.18 * abs(u),
                metrics.height * 0.005,
            )
            target = Vector(
                (
                    center.x + side_sign * x_radius * (0.62 + 0.38 * abs(u)),
                    center.y - y_front * (0.90 + 0.06 * abs(u)),
                    metrics.z(0.894 - 0.028 * abs(u)),
                )
            )
            first = head_surface(
                root_azimuth + side_sign * 0.18,
                0.66 + 0.14 * abs(u),
                metrics.height * 0.020,
            )
            second = target + Vector(
                (
                    -side_sign * metrics.height * 0.008,
                    metrics.height * 0.004,
                    metrics.height * 0.020,
                )
            )
            add_clump(
                (root, first, second, target),
                metrics.height * rng.uniform(0.0050, 0.0078),
                metrics.height * rng.uniform(0.00065, 0.0010),
                13,
                tip_fraction=0.20,
                taper_power=0.34,
            )

        # Short inner nape locks close the silhouette beneath the outer bob.
        for index in range(26):
            azimuth = math.radians(18.0) + math.radians(144.0) * index / 25
            azimuth += rng.uniform(-0.035, 0.035)
            controls = surface_controls(
                azimuth,
                rng.uniform(0.62, 0.90),
                azimuth + rng.uniform(-0.08, 0.08),
                rng.uniform(1.62, 1.92),
                metrics.height * 0.003,
                metrics.height * 0.006,
                metrics.height * 0.004,
            )
            add_clump(
                controls,
                metrics.height * rng.uniform(0.0038, 0.0056),
                metrics.height * 0.0009,
                10,
                tip_fraction=0.11,
                taper_power=0.42,
            )
    else:
        # Three overlapping scalp rows form short, swept layers.  Their tips
        # stay on the head ellipsoid; a small crest lift supplies volume.
        for row, (count, root_min, root_max, travel) in enumerate(
            ((30, 0.10, 0.34, 0.34), (38, 0.30, 0.57, 0.40), (42, 0.52, 0.80, 0.43))
        ):
            for index in range(count):
                azimuth = math.tau * index / count + rng.uniform(-0.045, 0.045)
                root_polar = rng.uniform(root_min, root_max)
                flow = rng.uniform(-0.10, 0.10) + math.sin(azimuth * 2.0) * 0.035
                tip_polar = min(1.30, root_polar + travel + rng.uniform(-0.05, 0.07))
                controls = surface_controls(
                    azimuth,
                    root_polar,
                    azimuth + flow,
                    tip_polar,
                    metrics.height * 0.0035,
                    metrics.height * (0.0200 + row * 0.0030),
                    metrics.height * 0.0045,
                )
                add_clump(
                    controls,
                    metrics.height * rng.uniform(0.0037, 0.0060),
                    metrics.height * rng.uniform(0.00085, 0.00125),
                    10,
                )

        # Forward fringe separates around the brow line, matching the tousled
        # reference without covering the eyes or turning into vertical spikes.
        for index in range(24):
            u = -1.0 + 2.0 * index / 23
            side_sign = -1.0 if u < 0.0 else 1.0
            azimuth = -math.pi * 0.5 + u * 0.72 + rng.uniform(-0.035, 0.035)
            root_polar = 0.38 + 0.20 * (1.0 - u * u) + rng.uniform(-0.05, 0.06)
            tip_azimuth = azimuth + side_sign * rng.uniform(0.015, 0.095)
            tip_polar = 1.92 - 0.32 * abs(u) + rng.uniform(-0.055, 0.055)
            controls = surface_controls(
                azimuth,
                root_polar,
                tip_azimuth,
                tip_polar,
                metrics.height * 0.004,
                metrics.height * 0.012,
                metrics.height * 0.003,
            )
            add_clump(
                controls,
                metrics.height * rng.uniform(0.0058, 0.0088),
                metrics.height * rng.uniform(0.0011, 0.0016),
                11,
            )

        # Side and nape locks extend just below the cap and taper along the
        # skull, producing the reference's close-cut side/back silhouette.
        for index in range(30):
            azimuth = math.radians(-5.0) + math.radians(190.0) * index / 29
            azimuth += rng.uniform(-0.035, 0.035)
            controls = surface_controls(
                azimuth,
                rng.uniform(0.55, 0.82),
                azimuth + rng.uniform(-0.07, 0.07),
                rng.uniform(1.52, 1.90),
                metrics.height * 0.003,
                metrics.height * 0.006,
                metrics.height * 0.003,
            )
            add_clump(
                controls,
                metrics.height * rng.uniform(0.0036, 0.0054),
                metrics.height * rng.uniform(0.0008, 0.0011),
                10,
            )

        # A few lower temple locks break the cap's geometric edge above each
        # ear and form the short sideburns visible in the turnaround.
        for temple_index, base_azimuth in enumerate((-0.28, -math.pi + 0.28)):
            side_sign = 1.0 if temple_index == 0 else -1.0
            for layer in range(6):
                azimuth = base_azimuth + side_sign * (layer - 2.5) * 0.045
                controls = surface_controls(
                    azimuth,
                    0.72 + layer * 0.025,
                    azimuth - side_sign * 0.035,
                    1.72 + layer * 0.045,
                    metrics.height * 0.003,
                    metrics.height * 0.007,
                    metrics.height * 0.0025,
                )
                add_clump(
                    controls,
                    metrics.height * rng.uniform(0.0038, 0.0053),
                    metrics.height * 0.0009,
                    10,
                )

    objects = [cap]
    for name, vertices, faces, material in (
        ("V3_Hair_Layered_Clumps", main_vertices, main_faces, materials["hair"]),
        ("V3_Hair_Highlight_Clumps", highlight_vertices, highlight_faces, materials["hair_highlight"]),
    ):
        if not faces:
            continue
        obj = create_mesh_object(name, vertices, faces, material)
        rigid_weights(obj, armature, "head")
        mark_generated(obj, spec, "hair-clumps")
        objects.append(obj)
    return objects


def create_boot_details(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: BodyMetrics,
    spec: CharacterSpec,
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for suffix, side_sign in (("L", 1.0), ("R", -1.0)):
        side = suffix.lower()
        foot_head, foot_tail = bone_points(armature, body, f"foot_{side}")
        ankle = foot_head
        toe_direction = (foot_tail - foot_head).normalized()
        sole_center = ankle + toe_direction * metrics.height * 0.060
        sole_center.z = metrics.z(0.009)
        objects.append(
            create_beveled_box(
                f"V3_Boot_Sole_{suffix}",
                sole_center,
                Vector((metrics.height * 0.067, metrics.height * 0.148, metrics.height * 0.010)),
                materials["sole"],
                armature,
                f"foot_{side}",
                spec,
                "boot-sole",
                bevel=metrics.height * 0.006,
            )
        )
        objects.append(
            create_beveled_box(
                f"V3_Boot_Rounded_Toe_{suffix}",
                sole_center + toe_direction * metrics.height * 0.030 + Vector((0.0, 0.0, metrics.height * 0.022)),
                Vector((metrics.height * 0.064, metrics.height * 0.118, metrics.height * 0.030)),
                materials["leather"],
                armature,
                f"foot_{side}",
                spec,
                "boot-toe",
                bevel=metrics.height * 0.012,
            )
        )
        objects.append(
            create_beveled_box(
                f"V3_Boot_Heel_{suffix}",
                Vector(
                    (
                        (ankle - toe_direction * metrics.height * 0.026).x,
                        (ankle - toe_direction * metrics.height * 0.026).y,
                        metrics.z(0.014),
                    )
                ),
                Vector((metrics.height * 0.054, metrics.height * 0.040, metrics.height * 0.024)),
                materials["sole"],
                armature,
                f"foot_{side}",
                spec,
                "boot-heel",
                bevel=metrics.height * 0.004,
            )
        )
        leg_x = ankle.x
        for index, z_norm in enumerate((0.110, 0.135), 1):
            objects.append(
                create_oval_band(
                    f"V3_Boot_Strap_{suffix}_{index}",
                    Vector((leg_x, ankle.y, metrics.z(z_norm))),
                    metrics.height * 0.039,
                    metrics.height * 0.035,
                    metrics.height * 0.033,
                    metrics.height * (0.016 if index == 1 else 0.013),
                    materials["leather_dark" if index == 1 else "leather"],
                    armature,
                    f"calf_{side}",
                    spec,
                    "boot-strap",
                    segments=48,
                    bevel=metrics.height * 0.0009,
                )
            )
        objects.append(
            create_oval_band(
                f"V3_Boot_Top_Piping_{suffix}",
                Vector((leg_x, ankle.y, metrics.z(0.148))),
                metrics.height * 0.039,
                metrics.height * 0.035,
                metrics.height * 0.033,
                metrics.height * 0.0055,
                materials["bronze"],
                armature,
                f"calf_{side}",
                spec,
                "boot-top-piping",
                segments=48,
                bevel=metrics.height * 0.0006,
            )
        )
        front_y = ankle.y - metrics.height * 0.041
        objects.append(
            create_curve_tube(
                f"V3_Boot_Front_Seam_{suffix}",
                [
                    Vector((leg_x, front_y, metrics.z(0.055))),
                    Vector((leg_x, front_y, metrics.z(0.095))),
                    Vector((leg_x, front_y, metrics.z(0.140))),
                ],
                materials["thread"],
                armature,
                f"calf_{side}",
                spec,
                "boot-front-seam",
                bevel_depth=metrics.height * 0.0007,
            )
        )
    return objects


def apply_reference_stance(armature: bpy.types.Object) -> None:
    """Lower the upper arms into the relaxed turnaround stance.

    The source rig keeps an animation-friendly wide A-pose.  The supplied
    drawings use a much narrower presentation pose, so the saved rig carries a
    reversible pose-bone offset while retaining the original rest skeleton.
    """

    for side, side_sign in (("l", 1.0), ("r", -1.0)):
        bone = armature.data.bones[f"upperarm_{side}"]
        pose_bone = armature.pose.bones[bone.name]
        rest_direction = (bone.tail_local - bone.head_local).normalized()
        desired_direction = Vector((side_sign * 0.30, -0.015, -0.954)).normalized()
        rotation = rest_direction.rotation_difference(desired_direction)
        pivot = bone.head_local
        pose_matrix = (
            Matrix.Translation(pivot)
            @ rotation.to_matrix().to_4x4()
            @ Matrix.Translation(-pivot)
            @ bone.matrix_local
        )
        pose_bone.matrix = pose_matrix
        pose_bone["reference_stance"] = True
    bpy.context.view_layer.update()


def validate_character_geometry(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    created: list[bpy.types.Object],
    metrics: BodyMetrics,
) -> None:
    """Reject modifier loss and explosive evaluated geometry before saving."""

    body_modifier_types = {modifier.type for modifier in body.modifiers}
    required_body_modifiers = {"ARMATURE", "MASK", "SUBSURF"}
    missing_body_modifiers = required_body_modifiers - body_modifier_types
    if missing_body_modifiers:
        raise RuntimeError(
            "Body modifier stack was altered during construction; missing "
            + ", ".join(sorted(missing_body_modifiers))
        )

    depsgraph = bpy.context.evaluated_depsgraph_get()
    failures: list[str] = []
    for obj in created:
        if obj.type != "MESH":
            continue
        if not any(modifier.type == "ARMATURE" and modifier.object == armature for modifier in obj.modifiers):
            failures.append(f"{obj.name}: missing armature modifier")
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            if not mesh.vertices:
                failures.append(f"{obj.name}: empty evaluated mesh")
                continue
            points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
            dimensions = Vector(
                tuple(
                    max(point[axis] for point in points) - min(point[axis] for point in points)
                    for axis in range(3)
                )
            )
            if max(dimensions) > metrics.height * 1.25:
                failures.append(
                    f"{obj.name}: explosive evaluated bounds "
                    f"({dimensions.x:.3f}, {dimensions.y:.3f}, {dimensions.z:.3f})m"
                )
        finally:
            evaluated.to_mesh_clear()

    if failures:
        raise RuntimeError("V3 geometry validation failed:\n- " + "\n- ".join(failures))


def build_character(spec: CharacterSpec) -> tuple[bpy.types.Object, bpy.types.Object, list[bpy.types.Object]]:
    base_path = WORK_DIR / spec.base_file
    if not base_path.exists():
        raise FileNotFoundError(
            f"Missing {base_path}. Run scripts/generate_mpfb_character_bases_v3.py first."
        )
    bpy.ops.wm.open_mainfile(filepath=str(base_path))
    body = find_body()
    armature = find_armature(body)
    bake_body_shape_mix(body)
    metrics = measure_body(body)
    materials = create_materials(spec)
    tune_skin_material(body, spec)
    created: list[bpy.types.Object] = []

    torso_groups = {"pelvis", "spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r"}

    def torso_selector(poly, center: Vector, zn: float) -> bool:
        weight = sum(
            body_group_weight(body, index, torso_groups) for index in poly.vertices
        ) / len(poly.vertices)
        lower_bound = 0.595 if spec.female else 0.505
        return lower_bound <= zn <= 0.838 and weight > 0.12 and abs(center.x - metrics.center_x) < metrics.height * 0.205

    def torso_offset(point: Vector, _normal: Vector, zn: float) -> float:
        belt_tension_center = 0.620 if spec.female else 0.545
        belt_tension = math.exp(-((zn - belt_tension_center) / 0.060) ** 2)
        fine_fold = math.sin((point.x - metrics.center_x) * 95.0 + point.z * 33.0)
        return metrics.height * 0.00115 * fine_fold * belt_tension

    created.append(
        extract_body_shell(
            body,
            armature,
            metrics,
            spec,
            "V3_Fitted_Tunic_Bodice",
            materials["teal"],
            torso_selector,
            base_offset=metrics.height * 0.0075,
            thickness=metrics.height * 0.0035,
            category="tunic-bodice",
            offset_function=torso_offset,
        )
    )

    for side in ("l", "r"):
        upper = bone_points(armature, body, f"upperarm_{side}")
        lower = bone_points(armature, body, f"lowerarm_{side}")
        arm_groups = {f"clavicle_{side}", f"upperarm_{side}", f"lowerarm_{side}"}
        outer_end = 0.94 if spec.female else 0.56
        linen_end = 1.55 if spec.female else 1.48
        linen_start = 0.86 if spec.female else 0.50

        def arm_selector(start: float, end: float, min_weight: float = 0.08):
            def selector(poly, center: Vector, _zn: float) -> bool:
                weight = sum(
                    body_group_weight(body, index, arm_groups) for index in poly.vertices
                ) / len(poly.vertices)
                chain_t, distance = arm_chain_parameter(center, upper, lower)
                return start <= chain_t <= end and weight > min_weight and distance < metrics.height * 0.085

            return selector

        def sleeve_offset(point: Vector, _normal: Vector, _zn: float) -> float:
            chain_t, _distance = arm_chain_parameter(point, upper, lower)
            elbow_fold = math.exp(-((chain_t - 1.0) / 0.20) ** 2)
            return metrics.height * 0.0018 * math.sin(chain_t * math.tau * 5.0) * elbow_fold

        side_label = side.upper()
        created.append(
            extract_body_shell(
                body,
                armature,
                metrics,
                spec,
                f"V3_Teal_Outer_Sleeve_{side_label}",
                materials["teal"],
                arm_selector(-0.08, outer_end),
                base_offset=metrics.height * 0.0095,
                thickness=metrics.height * 0.0038,
                category="outer-sleeve",
                offset_function=sleeve_offset,
            )
        )
        created.append(
            extract_body_shell(
                body,
                armature,
                metrics,
                spec,
                f"V3_Linen_Under_Sleeve_{side_label}",
                materials["linen"],
                arm_selector(linen_start, linen_end),
                base_offset=metrics.height * 0.0075,
                thickness=metrics.height * 0.0030,
                category="linen-under-sleeve",
                offset_function=sleeve_offset,
            )
        )
        wrap_start = 1.69 if spec.female else 1.43
        wrap_end = 1.94
        wrap_count = 3 if spec.female else 5
        wrap_step = (wrap_end - wrap_start) / wrap_count
        for wrap_index in range(wrap_count):
            segment_start = wrap_start + wrap_step * wrap_index - (0.014 if wrap_index else 0.0)
            segment_end = wrap_start + wrap_step * (wrap_index + 1) + 0.018
            created.append(
                extract_body_shell(
                    body,
                    armature,
                    metrics,
                    spec,
                    f"V3_Layered_Wrist_Wrap_{side_label}_{wrap_index + 1}",
                    materials["leather_dark" if wrap_index % 2 == 0 else "leather"],
                    arm_selector(segment_start, segment_end),
                    base_offset=metrics.height * (0.0100 + 0.0010 * (wrap_index % 2)),
                    thickness=metrics.height * 0.0031,
                    category="layered-wrist-wrap",
                    offset_function=lambda point, normal, zn, phase=wrap_index: metrics.height
                    * 0.0010
                    * math.sin(
                        arm_chain_parameter(point, upper, lower)[0] * math.tau * 9.0
                        + phase * 0.9
                    ),
                )
            )

        for band_index, chain_t in enumerate((outer_end - 0.035, outer_end + 0.015), 1):
            created.append(
                extract_body_shell(
                    body,
                    armature,
                    metrics,
                    spec,
                    f"V3_Sleeve_Piping_{side_label}_{band_index}",
                    materials["bronze"],
                    arm_selector(chain_t - 0.025, chain_t + 0.025, min_weight=0.04),
                    base_offset=metrics.height * 0.014,
                    thickness=metrics.height * 0.0022,
                    category="sleeve-piping",
                )
            )

    pants_groups = {"pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r"}

    def pants_selector(poly, center: Vector, zn: float) -> bool:
        weight = sum(
            body_group_weight(body, index, pants_groups) for index in poly.vertices
        ) / len(poly.vertices)
        return 0.125 <= zn <= 0.535 and weight > 0.08

    def pants_offset(point: Vector, _normal: Vector, zn: float) -> float:
        knee = math.exp(-((zn - 0.285) / 0.045) ** 2)
        ankle = math.exp(-((zn - 0.105) / 0.030) ** 2)
        phase = point.y * 78.0 + point.x * 37.0 + point.z * 52.0
        return metrics.height * (0.0028 * knee + 0.0022 * ankle) * math.sin(phase)

    created.append(
        extract_body_shell(
            body,
            armature,
            metrics,
            spec,
            "V3_Tailored_Charcoal_Trousers",
            materials["charcoal"],
            pants_selector,
            base_offset=metrics.height * (0.0085 if spec.female else 0.0105),
            thickness=metrics.height * (0.0028 if spec.female else 0.0032),
            category="trousers",
            offset_function=pants_offset,
        )
    )

    boot_groups = {"calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r"}

    def boot_selector(poly, center: Vector, zn: float) -> bool:
        # Position includes the complete merged toes; relying only on foot/ball
        # weights left several toe faces bare in the earlier boot shell.
        weight = sum(
            body_group_weight(body, index, boot_groups) for index in poly.vertices
        ) / len(poly.vertices)
        return zn <= (0.145 if spec.female else 0.140) and weight > 0.015

    created.append(
        extract_body_shell(
            body,
            armature,
            metrics,
            spec,
            "V3_Shaped_Leather_Boots",
            materials["leather"],
            boot_selector,
            base_offset=metrics.height * 0.010,
            thickness=metrics.height * 0.0038,
            category="boots",
        )
    )

    created.extend(create_skirt_panels(body, armature, metrics, spec, materials))
    created.extend(create_tunic_details(body, armature, metrics, spec, materials))
    created.extend(create_boot_details(body, armature, metrics, spec, materials))
    created.extend(create_hair(body, armature, metrics, spec, materials))

    apply_reference_stance(armature)

    for obj in [body, armature, *created]:
        obj["character_slug"] = spec.slug
        obj["source_reference"] = f"docs/character-concepts/{spec.reference_file}"

    validate_character_geometry(body, armature, created, metrics)
    return body, armature, created


def save_and_export(
    spec: CharacterSpec,
    body: bpy.types.Object,
    armature: bpy.types.Object,
    created: list[bpy.types.Object],
) -> tuple[Path, Path]:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    blend_path = SOURCE_DIR / f"{spec.slug}.blend"
    glb_path = MODEL_DIR / f"{spec.slug}.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    bpy.ops.object.select_all(action="DESELECT")
    export_objects = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type in {"MESH", "ARMATURE"} and not obj.hide_render
    ]
    for obj in export_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_skins=True,
        export_animations=True,
        export_apply=True,
        export_materials="EXPORT",
    )
    return blend_path, glb_path


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_turnaround(
    spec: CharacterSpec,
    body: bpy.types.Object,
    armature: bpy.types.Object,
    created: list[bpy.types.Object],
) -> list[Path]:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    metrics = measure_body(body)
    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("V3_Studio_World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.080, 0.074, 0.070, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.52

    stage_objects: list[bpy.types.Object] = []
    floor_material = create_pbr_material("V3_Studio_Floor", "807B75", roughness=0.88)
    bpy.ops.mesh.primitive_plane_add(
        size=metrics.height * 5.0,
        location=(metrics.center_x, metrics.center_y, metrics.z_min - metrics.height * 0.006),
    )
    floor = bpy.context.object
    floor.name = "V3_Preview_Floor"
    floor.data.materials.append(floor_material)
    stage_objects.append(floor)

    def add_area(name: str, location: Vector, energy: float, size: float, color):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = color
        light = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(light)
        light.location = location
        look_at(light, Vector((metrics.center_x, metrics.center_y, metrics.z(0.60))))
        stage_objects.append(light)

    add_area(
        "V3_Key",
        Vector((metrics.center_x - metrics.height * 1.5, metrics.center_y - metrics.height * 2.0, metrics.z(1.35))),
        560.0,
        metrics.height * 1.6,
        (1.0, 0.91, 0.82),
    )
    add_area(
        "V3_Fill",
        Vector((metrics.center_x + metrics.height * 1.6, metrics.center_y - metrics.height * 1.2, metrics.z(0.95))),
        320.0,
        metrics.height * 1.4,
        (0.76, 0.84, 1.0),
    )
    add_area(
        "V3_Rim",
        Vector((metrics.center_x, metrics.center_y + metrics.height * 1.7, metrics.z(1.15))),
        480.0,
        metrics.height * 1.2,
        (0.82, 0.96, 0.92),
    )

    camera_data = bpy.data.cameras.new("V3_Turnaround_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = metrics.height * 1.10
    camera = bpy.data.objects.new("V3_Turnaround_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    stage_objects.append(camera)
    scene.camera = camera
    target = Vector((metrics.center_x, metrics.center_y, metrics.z(0.50)))
    distance = metrics.height * 3.2
    views = {
        "front": Vector((metrics.center_x, metrics.center_y - distance, target.z)),
        "right-side": Vector((metrics.center_x + distance, metrics.center_y, target.z)),
        "back": Vector((metrics.center_x, metrics.center_y + distance, target.z)),
        "three-quarter": Vector((metrics.center_x + distance * 0.68, metrics.center_y - distance * 0.78, target.z + metrics.height * 0.035)),
    }

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.film_transparent = False
    scene.render.image_settings.color_depth = "8"
    scene.render.fps = 30
    scene.frame_set(1)

    paths: list[Path] = []
    for label, location in views.items():
        camera.location = location
        look_at(camera, target)
        path = PREVIEW_DIR / f"{spec.slug}-{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        paths.append(path)

    for obj in stage_objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    return paths


def generate(spec: CharacterSpec, *, render_previews: bool = True) -> None:
    body, armature, created = build_character(spec)
    blend_path, glb_path = save_and_export(spec, body, armature, created)
    preview_paths = (
        render_turnaround(spec, body, armature, created) if render_previews else []
    )
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render]
    vertices = sum(len(obj.data.vertices) for obj in mesh_objects)
    triangles = sum(
        sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)
        for obj in mesh_objects
    )
    print(
        f"GENERATED_V3 {spec.slug} vertices={vertices} triangles={triangles} "
        f"bones={len(armature.data.bones)} created_parts={len(created)} "
        f"blend={blend_path} glb={glb_path} previews={','.join(str(p) for p in preview_paths)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--character", choices=("male", "female", "all"), default="all")
    parser.add_argument("--skip-render", action="store_true")
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parser.parse_args(script_args)
    selected = CHARACTERS if args.character == "all" else tuple(
        spec for spec in CHARACTERS if spec.key == args.character
    )
    for spec in selected:
        generate(spec, render_previews=not args.skip_render)
    print("All v3 reference reconstruction characters generated successfully.")


if __name__ == "__main__":
    main()
