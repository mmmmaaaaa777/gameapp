"""Generate the initial male/female guild trainee models with Blender.

Run from PowerShell:
  & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" `
    --background --python scripts\\generate_initial_characters.py

The script intentionally uses only Blender primitives and materials.  This keeps the
source reproducible and avoids introducing third-party meshes or textures.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "public" / "models" / "characters"
SOURCE_DIR = PROJECT_ROOT / "art-source" / "characters"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "character-concepts" / "model-previews"


@dataclass(frozen=True)
class CharacterSpec:
    slug: str
    display_name: str
    height: float
    shoulder_x: float
    chest_x: float
    waist_x: float
    hip_x: float
    skin: tuple[float, float, float, float]
    hair: tuple[float, float, float, float]
    female: bool = False


CHARACTERS = (
    CharacterSpec(
        slug="initial-male",
        display_name="Initial Male Guild Trainee",
        height=1.78,
        shoulder_x=0.255,
        chest_x=0.225,
        waist_x=0.175,
        hip_x=0.185,
        skin=(0.67, 0.43, 0.30, 1.0),
        hair=(0.075, 0.043, 0.028, 1.0),
    ),
    CharacterSpec(
        slug="initial-female",
        display_name="Initial Female Guild Trainee",
        height=1.68,
        shoulder_x=0.225,
        chest_x=0.205,
        waist_x=0.158,
        hip_x=0.205,
        skin=(0.73, 0.49, 0.37, 1.0),
        hair=(0.23, 0.065, 0.043, 1.0),
        female=True,
    ),
)


def reset_blender() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for collection in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.actions,
    ):
        for block in list(collection):
            collection.remove(block)


def make_material(
    name: str,
    color: tuple[float, float, float, float],
    roughness: float = 0.72,
    metallic: float = 0.0,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    node = material.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = color
    node.inputs["Roughness"].default_value = roughness
    node.inputs["Metallic"].default_value = metallic
    return material


def create_materials(spec: CharacterSpec) -> dict[str, bpy.types.Material]:
    return {
        "skin": make_material("Skin", spec.skin, 0.72),
        "hair": make_material("Hair", spec.hair, 0.82),
        "teal": make_material("Guild_Teal", (0.055, 0.19, 0.20, 1.0), 0.78),
        "charcoal": make_material("Charcoal_Cloth", (0.035, 0.040, 0.050, 1.0), 0.86),
        "linen": make_material("Undyed_Linen", (0.62, 0.53, 0.39, 1.0), 0.92),
        "leather": make_material("Worn_Leather", (0.105, 0.070, 0.052, 1.0), 0.80),
        "sole": make_material("Boot_Sole", (0.025, 0.022, 0.021, 1.0), 0.94),
        "bronze": make_material("Aged_Bronze", (0.38, 0.22, 0.085, 1.0), 0.48, 0.48),
        "eye": make_material("Eyes", (0.012, 0.010, 0.008, 1.0), 0.42),
        "mouth": make_material("Mouth", (0.20, 0.055, 0.045, 1.0), 0.76),
    }


def smooth_mesh(obj: bpy.types.Object) -> None:
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def register_part(
    obj: bpy.types.Object,
    material: bpy.types.Material,
    bone_name: str,
    parts: list[bpy.types.Object],
    smooth: bool = True,
) -> bpy.types.Object:
    obj.data.materials.append(material)
    if smooth:
        smooth_mesh(obj)
    group = obj.vertex_groups.new(name=bone_name)
    group.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    parts.append(obj)
    return obj


def add_ellipsoid(
    name: str,
    location: Vector,
    scale: Vector,
    material: bpy.types.Material,
    bone_name: str,
    parts: list[bpy.types.Object],
    rotation=None,
    segments: int = 16,
    rings: int = 10,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if rotation is not None:
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return register_part(obj, material, bone_name, parts)


def add_segment(
    name: str,
    start: Vector,
    end: Vector,
    radius_start: float,
    radius_end: float,
    material: bpy.types.Material,
    bone_name: str,
    parts: list[bpy.types.Object],
    vertices: int = 12,
) -> bpy.types.Object:
    direction = end - start
    length = direction.length
    midpoint = (start + end) * 0.5
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius_start,
        radius2=radius_end,
        depth=length,
        location=midpoint,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized())
    return register_part(obj, material, bone_name, parts)


def add_elliptic_cone(
    name: str,
    location: Vector,
    depth: float,
    radius_bottom: float,
    radius_top: float,
    depth_ratio: float,
    material: bpy.types.Material,
    bone_name: str,
    parts: list[bpy.types.Object],
    vertices: int = 12,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius_bottom,
        radius2=radius_top,
        depth=depth,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale.y = depth_ratio
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return register_part(obj, material, bone_name, parts)


def add_beveled_box(
    name: str,
    location: Vector,
    dimensions: Vector,
    material: bpy.types.Material,
    bone_name: str,
    parts: list[bpy.types.Object],
    bevel: float = 0.01,
    rotation_z: float = 0.0,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=(0.0, 0.0, rotation_z))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        modifier = obj.modifiers.new(name="Soft_Edges", type="BEVEL")
        modifier.width = min(bevel, min(dimensions) * 0.24)
        modifier.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return register_part(obj, material, bone_name, parts)


def add_torus(
    name: str,
    location: Vector,
    major_radius: float,
    minor_radius: float,
    scale_y: float,
    material: bpy.types.Material,
    bone_name: str,
    parts: list[bpy.types.Object],
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=16,
        minor_segments=6,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale.y = scale_y
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return register_part(obj, material, bone_name, parts)


def create_armature(spec: CharacterSpec) -> tuple[bpy.types.Object, dict[str, Vector]]:
    s = spec.height / 1.78
    shoulder = spec.shoulder_x * s
    hip = min(spec.hip_x * 0.58, 0.118) * s

    points = {
        "root": Vector((0.0, 0.0, 0.02 * s)),
        "hips": Vector((0.0, 0.0, 0.91 * s)),
        "spine": Vector((0.0, 0.0, 1.08 * s)),
        "chest": Vector((0.0, 0.0, 1.25 * s)),
        "upper_chest": Vector((0.0, 0.0, 1.39 * s)),
        "neck": Vector((0.0, 0.0, 1.48 * s)),
        "head": Vector((0.0, 0.0, 1.56 * s)),
        "head_top": Vector((0.0, 0.0, 1.77 * s)),
    }

    for side, sign in (("Left", 1.0), ("Right", -1.0)):
        points[f"{side}_shoulder"] = Vector((sign * shoulder, 0.0, 1.40 * s))
        points[f"{side}_elbow"] = Vector((sign * (shoulder + 0.125 * s), 0.0, 1.13 * s))
        points[f"{side}_wrist"] = Vector((sign * (shoulder + 0.245 * s), 0.0, 0.89 * s))
        points[f"{side}_hand_end"] = Vector((sign * (shoulder + 0.275 * s), 0.0, 0.76 * s))
        points[f"{side}_hip"] = Vector((sign * hip, 0.0, 0.91 * s))
        points[f"{side}_knee"] = Vector((sign * hip, 0.008 * s, 0.50 * s))
        points[f"{side}_ankle"] = Vector((sign * hip, 0.0, 0.14 * s))
        points[f"{side}_toe"] = Vector((sign * hip, -0.19 * s, 0.07 * s))

    armature_data = bpy.data.armatures.new(f"{spec.slug}-rig")
    armature = bpy.data.objects.new(f"{spec.slug}-rig", armature_data)
    bpy.context.collection.objects.link(armature)
    armature.show_in_front = True
    armature.data.display_type = "OCTAHEDRAL"
    armature["character_name"] = spec.display_name
    armature["forward_axis"] = "Blender -Y / glTF +Z"
    armature["height_meters"] = round(spec.height, 3)

    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    def bone(name: str, head: Vector, tail: Vector, parent: str | None = None) -> None:
        edit_bone = armature_data.edit_bones.new(name)
        edit_bone.head = head
        edit_bone.tail = tail
        edit_bone.use_connect = False
        if parent is not None:
            edit_bone.parent = armature_data.edit_bones[parent]

    bone("Root", points["root"], Vector((0.0, 0.0, 0.18 * s)))
    bone("Hips", points["hips"], points["spine"], "Root")
    bone("Spine", points["spine"], points["chest"], "Hips")
    bone("Chest", points["chest"], points["upper_chest"], "Spine")
    bone("UpperChest", points["upper_chest"], points["neck"], "Chest")
    bone("Neck", points["neck"], points["head"], "UpperChest")
    bone("Head", points["head"], points["head_top"], "Neck")

    for side in ("Left", "Right"):
        bone(
            f"{side}Shoulder",
            points["upper_chest"],
            points[f"{side}_shoulder"],
            "UpperChest",
        )
        bone(
            f"{side}Arm",
            points[f"{side}_shoulder"],
            points[f"{side}_elbow"],
            f"{side}Shoulder",
        )
        bone(
            f"{side}ForeArm",
            points[f"{side}_elbow"],
            points[f"{side}_wrist"],
            f"{side}Arm",
        )
        bone(
            f"{side}Hand",
            points[f"{side}_wrist"],
            points[f"{side}_hand_end"],
            f"{side}ForeArm",
        )
        bone(
            f"{side}UpLeg",
            points[f"{side}_hip"],
            points[f"{side}_knee"],
            "Hips",
        )
        bone(
            f"{side}Leg",
            points[f"{side}_knee"],
            points[f"{side}_ankle"],
            f"{side}UpLeg",
        )
        bone(
            f"{side}Foot",
            points[f"{side}_ankle"],
            points[f"{side}_toe"],
            f"{side}Leg",
        )

    bpy.ops.object.mode_set(mode="OBJECT")
    armature.select_set(False)
    return armature, points


def lerp(start: Vector, end: Vector, factor: float) -> Vector:
    return start + (end - start) * factor


def build_character_mesh(
    spec: CharacterSpec,
    armature: bpy.types.Object,
    points: dict[str, Vector],
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    s = spec.height / 1.78
    parts: list[bpy.types.Object] = []
    chest_depth = (0.125 if not spec.female else 0.118) * s
    waist_depth = 0.105 * s
    hip_depth = 0.115 * s

    # Torso and guild trainee tunic.
    add_elliptic_cone(
        "Tunic_Hem",
        Vector((0.0, 0.0, 0.965 * s)),
        0.19 * s,
        spec.hip_x * s,
        spec.waist_x * s,
        hip_depth / (spec.hip_x * s),
        materials["teal"],
        "Hips",
        parts,
    )
    add_elliptic_cone(
        "Tunic_Abdomen",
        Vector((0.0, 0.0, 1.115 * s)),
        0.30 * s,
        spec.waist_x * s,
        spec.chest_x * 0.91 * s,
        waist_depth / (spec.waist_x * s),
        materials["teal"],
        "Spine",
        parts,
    )
    add_elliptic_cone(
        "Tunic_Chest",
        Vector((0.0, 0.0, 1.325 * s)),
        0.20 * s,
        spec.chest_x * 0.91 * s,
        spec.shoulder_x * 0.82 * s,
        chest_depth / (spec.chest_x * s),
        materials["teal"],
        "Chest",
        parts,
    )
    add_elliptic_cone(
        "Trousers_Hips",
        Vector((0.0, 0.0, 0.865 * s)),
        0.19 * s,
        spec.hip_x * 0.85 * s,
        spec.hip_x * s,
        hip_depth / (spec.hip_x * s),
        materials["charcoal"],
        "Hips",
        parts,
    )

    # Belt, buckle, collar, front inset, and restrained aged-bronze trim.
    add_elliptic_cone(
        "Leather_Belt",
        Vector((0.0, 0.0, 1.015 * s)),
        0.055 * s,
        spec.waist_x * 1.06 * s,
        spec.waist_x * 1.06 * s,
        waist_depth * 1.08 / (spec.waist_x * s),
        materials["leather"],
        "Hips",
        parts,
    )
    add_beveled_box(
        "Belt_Buckle",
        Vector((0.0, -waist_depth * 1.09, 1.015 * s)),
        Vector((0.058 * s, 0.018 * s, 0.042 * s)),
        materials["bronze"],
        "Hips",
        parts,
        bevel=0.006 * s,
    )
    add_beveled_box(
        "Tunic_Front_Inset",
        Vector((0.0, -chest_depth * 1.015, 1.255 * s)),
        Vector((0.050 * s, 0.010 * s, 0.30 * s)),
        materials["linen"],
        "Chest",
        parts,
        bevel=0.004 * s,
    )
    add_beveled_box(
        "Tunic_Front_Trim",
        Vector((-0.031 * s, -chest_depth * 1.035, 1.255 * s)),
        Vector((0.009 * s, 0.010 * s, 0.31 * s)),
        materials["bronze"],
        "Chest",
        parts,
        bevel=0.002 * s,
    )
    add_torus(
        "Collar_Trim",
        Vector((0.0, 0.0, 1.455 * s)),
        0.069 * s,
        0.008 * s,
        0.82,
        materials["bronze"],
        "UpperChest",
        parts,
    )

    # Neck and head.
    add_segment(
        "Neck",
        Vector((0.0, 0.0, 1.425 * s)),
        Vector((0.0, 0.0, 1.525 * s)),
        0.060 * s,
        0.064 * s,
        materials["skin"],
        "Neck",
        parts,
    )
    head_center = Vector((0.0, -0.004 * s, 1.625 * s))
    head_scale = Vector((0.112 * s, 0.102 * s, (0.145 if not spec.female else 0.142) * s))
    add_ellipsoid("Head", head_center, head_scale, materials["skin"], "Head", parts, segments=20, rings=14)
    for sign in (-1.0, 1.0):
        add_ellipsoid(
            f"Ear_{sign:+.0f}",
            head_center + Vector((sign * 0.111 * s, 0.0, 0.0)),
            Vector((0.015 * s, 0.010 * s, 0.031 * s)),
            materials["skin"],
            "Head",
            parts,
            segments=10,
            rings=6,
        )

    face_y = -0.105 * s
    eye_size = 0.0145 if spec.female else 0.013
    for sign in (-1.0, 1.0):
        add_ellipsoid(
            f"Eye_{sign:+.0f}",
            Vector((sign * 0.041 * s, face_y, 1.648 * s)),
            Vector((eye_size * s, 0.006 * s, 0.009 * s)),
            materials["eye"],
            "Head",
            parts,
            segments=10,
            rings=6,
        )
        add_beveled_box(
            f"Brow_{sign:+.0f}",
            Vector((sign * 0.041 * s, face_y - 0.002 * s, 1.683 * s)),
            Vector((0.040 * s, 0.005 * s, 0.007 * s)),
            materials["hair"],
            "Head",
            parts,
            bevel=0.002 * s,
            rotation_z=math.radians(-sign * 4.0),
        )
    add_ellipsoid(
        "Nose",
        Vector((0.0, face_y - 0.008 * s, 1.615 * s)),
        Vector((0.013 * s, 0.012 * s, 0.025 * s)),
        materials["skin"],
        "Head",
        parts,
        segments=10,
        rings=6,
    )
    add_beveled_box(
        "Mouth",
        Vector((0.0, face_y - 0.004 * s, 1.573 * s)),
        Vector((0.052 * s, 0.005 * s, 0.008 * s)),
        materials["mouth"],
        "Head",
        parts,
        bevel=0.003 * s,
    )

    # Hair: a readable short cut for the male and a compact layered bob for the female.
    if spec.female:
        add_ellipsoid(
            "Hair_Cap",
            Vector((0.0, 0.012 * s, 1.690 * s)),
            Vector((0.124 * s, 0.112 * s, 0.112 * s)),
            materials["hair"],
            "Head",
            parts,
            segments=18,
            rings=10,
        )
        add_ellipsoid(
            "Hair_Back",
            Vector((0.0, 0.067 * s, 1.590 * s)),
            Vector((0.116 * s, 0.065 * s, 0.104 * s)),
            materials["hair"],
            "Head",
            parts,
            segments=16,
            rings=9,
        )
        for sign in (-1.0, 1.0):
            add_ellipsoid(
                f"Hair_Side_{sign:+.0f}",
                Vector((sign * 0.103 * s, 0.005 * s, 1.590 * s)),
                Vector((0.036 * s, 0.064 * s, 0.096 * s)),
                materials["hair"],
                "Head",
                parts,
                segments=12,
                rings=8,
            )
    else:
        add_ellipsoid(
            "Hair_Cap",
            Vector((0.0, 0.014 * s, 1.698 * s)),
            Vector((0.121 * s, 0.109 * s, 0.096 * s)),
            materials["hair"],
            "Head",
            parts,
            segments=16,
            rings=9,
        )
        for index, (x, y, z, sx, sy, sz, angle) in enumerate(
            (
                (-0.075, -0.055, 1.748, 0.039, 0.033, 0.070, -18),
                (-0.018, -0.072, 1.762, 0.041, 0.032, 0.075, -5),
                (0.045, -0.063, 1.756, 0.040, 0.031, 0.072, 13),
                (0.088, -0.033, 1.724, 0.032, 0.030, 0.064, 22),
            )
        ):
            obj = add_ellipsoid(
                f"Hair_Lock_{index}",
                Vector((x * s, y * s, z * s)),
                Vector((sx * s, sy * s, sz * s)),
                materials["hair"],
                "Head",
                parts,
                segments=10,
                rings=6,
            )
            obj.rotation_euler.z = math.radians(angle)

    # Arms, sleeves, wraps, and hands.
    for side, sign in (("Left", 1.0), ("Right", -1.0)):
        shoulder = points[f"{side}_shoulder"]
        elbow = points[f"{side}_elbow"]
        wrist = points[f"{side}_wrist"]
        hand_end = points[f"{side}_hand_end"]
        sleeve_end = lerp(shoulder, elbow, 0.44)

        add_ellipsoid(
            f"{side}_Shoulder_Cap",
            shoulder,
            Vector((0.080 * s, 0.078 * s, 0.080 * s)),
            materials["teal"],
            f"{side}Arm",
            parts,
            segments=12,
            rings=8,
        )
        add_segment(
            f"{side}_Short_Sleeve",
            shoulder,
            sleeve_end,
            0.082 * s,
            0.074 * s,
            materials["teal"],
            f"{side}Arm",
            parts,
        )
        add_segment(
            f"{side}_Linen_Sleeve",
            sleeve_end,
            elbow,
            0.074 * s,
            0.060 * s,
            materials["linen"],
            f"{side}Arm",
            parts,
        )
        add_segment(
            f"{side}_Forearm",
            elbow,
            wrist,
            0.060 * s,
            0.043 * s,
            materials["skin"],
            f"{side}ForeArm",
            parts,
        )
        wrap_start = lerp(elbow, wrist, 0.72)
        add_segment(
            f"{side}_Wrist_Wrap",
            wrap_start,
            wrist,
            0.050 * s,
            0.047 * s,
            materials["leather"],
            f"{side}ForeArm",
            parts,
        )
        hand_rotation = Vector((0.0, 0.0, 1.0)).rotation_difference((hand_end - wrist).normalized())
        add_ellipsoid(
            f"{side}_Hand",
            (wrist + hand_end) * 0.5,
            Vector((0.048 * s, 0.032 * s, 0.073 * s)),
            materials["skin"],
            f"{side}Hand",
            parts,
            rotation=hand_rotation,
            segments=12,
            rings=8,
        )

    # Trousers and boots.
    thigh_top = (0.092 if not spec.female else 0.097) * s
    for side in ("Left", "Right"):
        hip = points[f"{side}_hip"]
        knee = points[f"{side}_knee"]
        ankle = points[f"{side}_ankle"]
        toe = points[f"{side}_toe"]
        boot_top = lerp(knee, ankle, 0.63)

        add_segment(
            f"{side}_Trouser_Thigh",
            hip,
            knee,
            thigh_top,
            0.070 * s,
            materials["charcoal"],
            f"{side}UpLeg",
            parts,
        )
        add_segment(
            f"{side}_Trouser_Calf",
            knee,
            boot_top,
            0.071 * s,
            0.057 * s,
            materials["charcoal"],
            f"{side}Leg",
            parts,
        )
        add_segment(
            f"{side}_Boot_Shaft",
            boot_top,
            ankle,
            0.067 * s,
            0.061 * s,
            materials["leather"],
            f"{side}Leg",
            parts,
        )
        add_segment(
            f"{side}_Boot_Cuff",
            lerp(boot_top, ankle, 0.02),
            lerp(boot_top, ankle, 0.20),
            0.074 * s,
            0.073 * s,
            materials["leather"],
            f"{side}Leg",
            parts,
        )
        foot_center = (ankle + toe) * 0.5 + Vector((0.0, -0.015 * s, -0.005 * s))
        add_beveled_box(
            f"{side}_Boot_Foot",
            foot_center,
            Vector((0.145 * s, 0.255 * s, 0.105 * s)),
            materials["leather"],
            f"{side}Foot",
            parts,
            bevel=0.025 * s,
        )
        add_beveled_box(
            f"{side}_Boot_Sole",
            foot_center + Vector((0.0, 0.0, -0.055 * s)),
            Vector((0.153 * s, 0.265 * s, 0.026 * s)),
            materials["sole"],
            f"{side}Foot",
            parts,
            bevel=0.008 * s,
        )

    # Join the parts into one skinned mesh; the per-part vertex groups survive the join.
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    mesh = bpy.context.object
    mesh.name = f"{spec.slug}-mesh"
    mesh.data.name = f"{spec.slug}-mesh-data"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    modifier = mesh.modifiers.new(name="Armature", type="ARMATURE")
    modifier.object = armature
    modifier.use_deform_preserve_volume = True
    mesh.parent = armature
    mesh.matrix_parent_inverse = armature.matrix_world.inverted()
    mesh["source_reference"] = f"docs/character-concepts/{spec.slug}-turnaround.png"
    mesh["style"] = "stylized low-poly ancient guild trainee"
    return mesh


def clear_pose(armature: bpy.types.Object) -> None:
    for pose_bone in armature.pose.bones:
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)


def key_pose_bone(
    armature: bpy.types.Object,
    bone_name: str,
    frame: int,
    rotation_x: float = 0.0,
    location_z: float = 0.0,
) -> None:
    bone = armature.pose.bones[bone_name]
    bone.rotation_mode = "XYZ"
    bone.rotation_euler.x = math.radians(rotation_x)
    bone.location.z = location_z
    bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=bone_name)
    bone.keyframe_insert(data_path="location", frame=frame, group=bone_name)


def build_action(
    armature: bpy.types.Object,
    name: str,
    frames: list[int],
    poses: dict[str, list[tuple[float, float]]],
) -> bpy.types.Action:
    clear_pose(armature)
    action = bpy.data.actions.new(name=name)
    armature.animation_data_create()
    armature.animation_data.action = action
    for bone_name, values in poses.items():
        for frame, (rotation_x, location_z) in zip(frames, values, strict=True):
            key_pose_bone(armature, bone_name, frame, rotation_x, location_z)
    action.use_fake_user = True
    return action


def create_animations(armature: bpy.types.Object, scale: float) -> list[bpy.types.Action]:
    idle_frames = [1, 31, 61]
    idle = build_action(
        armature,
        "idle",
        idle_frames,
        {
            "Hips": [(0.0, 0.0), (0.0, 0.012 * scale), (0.0, 0.0)],
            "Chest": [(-1.0, 0.0), (1.2, 0.0), (-1.0, 0.0)],
            "LeftArm": [(0.5, 0.0), (-0.8, 0.0), (0.5, 0.0)],
            "RightArm": [(-0.5, 0.0), (0.8, 0.0), (-0.5, 0.0)],
        },
    )

    run_frames = [1, 7, 13, 19, 25]
    run = build_action(
        armature,
        "run",
        run_frames,
        {
            "Hips": [(0.0, 0.0), (0.0, 0.025 * scale), (0.0, 0.0), (0.0, 0.025 * scale), (0.0, 0.0)],
            "LeftUpLeg": [(34.0, 0.0), (0.0, 0.0), (-34.0, 0.0), (0.0, 0.0), (34.0, 0.0)],
            "RightUpLeg": [(-34.0, 0.0), (0.0, 0.0), (34.0, 0.0), (0.0, 0.0), (-34.0, 0.0)],
            "LeftLeg": [(-16.0, 0.0), (30.0, 0.0), (8.0, 0.0), (4.0, 0.0), (-16.0, 0.0)],
            "RightLeg": [(8.0, 0.0), (4.0, 0.0), (-16.0, 0.0), (30.0, 0.0), (8.0, 0.0)],
            "LeftArm": [(-26.0, 0.0), (0.0, 0.0), (26.0, 0.0), (0.0, 0.0), (-26.0, 0.0)],
            "RightArm": [(26.0, 0.0), (0.0, 0.0), (-26.0, 0.0), (0.0, 0.0), (26.0, 0.0)],
        },
    )

    jump_frames = [1, 10, 22, 34, 46]
    jump = build_action(
        armature,
        "jump",
        jump_frames,
        {
            "Hips": [(0.0, 0.0), (0.0, -0.03 * scale), (0.0, 0.20 * scale), (0.0, 0.08 * scale), (0.0, 0.0)],
            "LeftUpLeg": [(0.0, 0.0), (20.0, 0.0), (-12.0, 0.0), (16.0, 0.0), (0.0, 0.0)],
            "RightUpLeg": [(0.0, 0.0), (20.0, 0.0), (-12.0, 0.0), (16.0, 0.0), (0.0, 0.0)],
            "LeftLeg": [(0.0, 0.0), (-34.0, 0.0), (18.0, 0.0), (-28.0, 0.0), (0.0, 0.0)],
            "RightLeg": [(0.0, 0.0), (-34.0, 0.0), (18.0, 0.0), (-28.0, 0.0), (0.0, 0.0)],
            "LeftArm": [(0.0, 0.0), (-12.0, 0.0), (36.0, 0.0), (14.0, 0.0), (0.0, 0.0)],
            "RightArm": [(0.0, 0.0), (-12.0, 0.0), (36.0, 0.0), (14.0, 0.0), (0.0, 0.0)],
        },
    )

    armature.animation_data.action = idle
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 61
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_set(1)
    return [idle, run, jump]


def save_and_export(
    spec: CharacterSpec,
    armature: bpy.types.Object,
    mesh: bpy.types.Object,
) -> tuple[Path, Path]:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    blend_path = SOURCE_DIR / f"{spec.slug}.blend"
    glb_path = MODEL_DIR / f"{spec.slug}.glb"

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_skins=True,
        export_animations=True,
        export_animation_mode="ACTIONS",
    )
    return blend_path, glb_path


def render_preview(spec: CharacterSpec, armature: bpy.types.Object) -> Path:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    preview_path = PREVIEW_DIR / f"{spec.slug}-model-preview.png"
    s = spec.height / 1.78

    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.055, 0.048, 0.043, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.55

    bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0.0, 0.0, -0.003))
    floor = bpy.context.object
    floor.name = "Preview_Floor"
    floor_material = make_material("Preview_Floor_Material", (0.10, 0.085, 0.070, 1.0), 0.88)
    floor.data.materials.append(floor_material)

    def add_area(name: str, location, energy: float, size: float, color) -> None:
        light_data = bpy.data.lights.new(name=name, type="AREA")
        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size
        light_data.color = color
        light = bpy.data.objects.new(name, light_data)
        bpy.context.collection.objects.link(light)
        light.location = location
        direction = Vector((0.0, 0.0, 0.95 * s)) - light.location
        light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    add_area("Key_Light", (-2.2, -3.0, 3.6), 980.0, 3.0, (1.0, 0.78, 0.55))
    add_area("Fill_Light", (2.7, -1.4, 2.3), 720.0, 2.5, (0.50, 0.78, 1.0))
    add_area("Rim_Light", (0.8, 2.8, 3.0), 880.0, 2.0, (0.58, 0.86, 0.80))

    camera_data = bpy.data.cameras.new("Preview_Camera")
    camera = bpy.data.objects.new("Preview_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (2.55 * s, -4.25 * s, 2.15 * s)
    target = Vector((0.0, 0.0, 0.91 * s))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.lens = 62
    bpy.context.scene.camera = camera

    if armature.animation_data:
        armature.animation_data.action = bpy.data.actions.get("idle")
    bpy.context.scene.frame_set(1)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(preview_path)
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    bpy.ops.render.render(write_still=True)
    return preview_path


def generate_character(spec: CharacterSpec) -> None:
    reset_blender()
    materials = create_materials(spec)
    armature, points = create_armature(spec)
    mesh = build_character_mesh(spec, armature, points, materials)
    actions = create_animations(armature, spec.height / 1.78)
    blend_path, glb_path = save_and_export(spec, armature, mesh)
    preview_path = render_preview(spec, armature)

    triangle_count = sum(len(polygon.vertices) - 2 for polygon in mesh.data.polygons)
    print(
        f"GENERATED {spec.slug}: "
        f"vertices={len(mesh.data.vertices)} triangles={triangle_count} "
        f"bones={len(armature.data.bones)} animations={','.join(action.name for action in actions)} "
        f"blend={blend_path} glb={glb_path} preview={preview_path}"
    )


def main() -> None:
    for spec in CHARACTERS:
        generate_character(spec)
    print("All initial character models generated successfully.")


if __name__ == "__main__":
    main()
