"""Generate the detailed v2 male/female guild trainee models with Blender.

Run from PowerShell:
  & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" `
    --background --python scripts\\generate_realistic_characters.py

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
        slug="initial-male-v2",
        display_name="Initial Male Guild Trainee v2",
        height=1.78,
        shoulder_x=0.255,
        chest_x=0.225,
        waist_x=0.175,
        hip_x=0.185,
        skin=(0.67, 0.43, 0.30, 1.0),
        hair=(0.075, 0.043, 0.028, 1.0),
    ),
    CharacterSpec(
        slug="initial-female-v2",
        display_name="Initial Female Guild Trainee v2",
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


def srgb_to_linear_channel(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def linear_hex(value: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    value = value.removeprefix("#")
    channels = [int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)]
    return tuple(srgb_to_linear_channel(channel) for channel in channels) + (alpha,)


def create_materials(spec: CharacterSpec) -> dict[str, bpy.types.Material]:
    skin_hex = "D2A07F" if not spec.female else "D8A98D"
    hair_hex = "2B211D" if not spec.female else "66352F"
    return {
        "skin": make_material("Skin", linear_hex(skin_hex), 0.53),
        "skin_shadow": make_material("Skin_Shadow", linear_hex("B87763"), 0.58),
        "hair": make_material("Hair", linear_hex(hair_hex), 0.54),
        "hair_highlight": make_material(
            "Hair_Highlight",
            linear_hex("49372D" if not spec.female else "87483F"),
            0.50,
        ),
        "teal": make_material("Guild_Teal", linear_hex("274B4D"), 0.76),
        "teal_dark": make_material("Guild_Teal_Dark", linear_hex("183639"), 0.80),
        "charcoal": make_material("Charcoal_Cloth", linear_hex("28282A"), 0.86),
        "linen": make_material("Undyed_Linen", linear_hex("CDBB96"), 0.92),
        "leather": make_material("Worn_Leather", linear_hex("46362D"), 0.78),
        "leather_dark": make_material("Worn_Leather_Dark", linear_hex("2A211D"), 0.84),
        "sole": make_material("Boot_Sole", linear_hex("181615"), 0.94),
        "bronze": make_material("Aged_Bronze", linear_hex("A67A3C"), 0.36, 0.82),
        "eye": make_material("Eye_Pupil", linear_hex("16110F"), 0.34),
        "eye_white": make_material("Eye_Sclera", linear_hex("E8E1D7"), 0.42),
        "iris": make_material("Eye_Iris", linear_hex("5B3A24"), 0.38),
        "mouth": make_material("Mouth", linear_hex("9B554F"), 0.62),
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


def create_loft_mesh(
    name: str,
    profiles: list[tuple[Vector, float, float, dict[str, float]]],
    material: bpy.types.Material,
    segments: int = 20,
    subdivision: int = 1,
) -> bpy.types.Object:
    """Create a smooth anatomical tube from elliptical profile rings."""
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    previous_axis_u: Vector | None = None
    for index, (center, radius_u, radius_v, _weights) in enumerate(profiles):
        previous_center = profiles[max(index - 1, 0)][0]
        next_center = profiles[min(index + 1, len(profiles) - 1)][0]
        tangent = (next_center - previous_center).normalized()
        reference = Vector((0.0, 1.0, 0.0))
        axis_u = reference.cross(tangent)
        if axis_u.length < 0.001:
            axis_u = Vector((1.0, 0.0, 0.0))
        else:
            axis_u.normalize()
        if previous_axis_u is not None and axis_u.dot(previous_axis_u) < 0.0:
            axis_u.negate()
        axis_v = tangent.cross(axis_u).normalized()
        previous_axis_u = axis_u.copy()

        for segment in range(segments):
            angle = 2.0 * math.pi * segment / segments
            position = center + axis_u * (math.cos(angle) * radius_u) + axis_v * (
                math.sin(angle) * radius_v
            )
            vertices.append(tuple(position))

    for ring in range(len(profiles) - 1):
        start = ring * segments
        following = (ring + 1) * segments
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append(
                (
                    start + segment,
                    start + next_segment,
                    following + next_segment,
                    following + segment,
                )
            )

    faces.append(tuple(reversed(range(segments))))
    last_start = (len(profiles) - 1) * segments
    faces.append(tuple(last_start + segment for segment in range(segments)))

    mesh_data = bpy.data.meshes.new(f"{name}-data")
    mesh_data.from_pydata(vertices, [], faces)
    mesh_data.update()
    obj = bpy.data.objects.new(name, mesh_data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    smooth_mesh(obj)

    weight_names = sorted({bone for _center, _u, _v, weights in profiles for bone in weights})
    groups = {bone: obj.vertex_groups.new(name=bone) for bone in weight_names}
    for ring, (_center, _u, _v, weights) in enumerate(profiles):
        vertex_indices = list(range(ring * segments, (ring + 1) * segments))
        total = sum(weights.values()) or 1.0
        for bone, weight in weights.items():
            groups[bone].add(vertex_indices, weight / total, "REPLACE")

    if subdivision > 0:
        bpy.context.view_layer.objects.active = obj
        modifier = obj.modifiers.new(name="Anatomical_Subdivision", type="SUBSURF")
        modifier.subdivision_type = "CATMULL_CLARK"
        modifier.levels = subdivision
        modifier.render_levels = subdivision
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def join_mesh_objects(objects: list[bpy.types.Object], name: str) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    result = bpy.context.object
    result.name = name
    result.data.name = f"{name}-data"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    smooth_mesh(result)
    return result


def rig_mesh(obj: bpy.types.Object, armature: bpy.types.Object) -> bpy.types.Object:
    modifier = next((item for item in obj.modifiers if item.type == "ARMATURE"), None)
    if modifier is None:
        modifier = obj.modifiers.new(name="Armature", type="ARMATURE")
    modifier.object = armature
    modifier.use_deform_preserve_volume = False
    obj.parent = armature
    obj.matrix_parent_inverse = armature.matrix_world.inverted()
    return obj


def add_rigid_group(obj: bpy.types.Object, bone_name: str) -> None:
    for group in list(obj.vertex_groups):
        obj.vertex_groups.remove(group)
    group = obj.vertex_groups.new(name=bone_name)
    group.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")


def create_curve_tube(
    name: str,
    coordinates: list[Vector],
    radii: list[float],
    bevel_depth: float,
    material: bpy.types.Material,
    bone_name: str,
) -> bpy.types.Object:
    curve_data = bpy.data.curves.new(name=f"{name}-curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 2
    curve_data.bevel_resolution = 2
    curve_data.bevel_depth = bevel_depth
    curve_data.resolution_u = 2
    spline = curve_data.splines.new("NURBS")
    spline.points.add(len(coordinates) - 1)
    for point, coordinate, radius in zip(spline.points, coordinates, radii, strict=True):
        point.co = (*coordinate, 1.0)
        point.radius = radius
    spline.order_u = min(3, len(coordinates))
    spline.use_endpoint_u = True
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    curve_data.materials.append(material)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    add_rigid_group(obj, bone_name)
    smooth_mesh(obj)
    return obj


def create_shaped_head(
    spec: CharacterSpec,
    material: bpy.types.Material,
    parts: list[bpy.types.Object],
) -> bpy.types.Object:
    s = spec.height / 1.78
    center = Vector((0.0, -0.006 * s, 1.635 * s))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=22, location=center)
    head = bpy.context.object
    head.name = "Head_Organic"
    width = (0.105 if not spec.female else 0.102) * s
    depth = (0.094 if not spec.female else 0.091) * s
    height = (0.132 if not spec.female else 0.128) * s
    head.scale = (width, depth, height)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    for vertex in head.data.vertices:
        normalized_z = max(-1.0, min(1.0, vertex.co.z / height))
        if normalized_z < -0.10:
            jaw_factor = 0.68 + 0.32 * ((normalized_z + 1.0) / 0.90)
            vertex.co.x *= jaw_factor
            if vertex.co.y < 0.0:
                vertex.co.y *= 0.91
        elif normalized_z > 0.55:
            vertex.co.x *= 0.95
        if vertex.co.y < 0.0 and -0.30 < normalized_z < 0.45:
            vertex.co.y *= 0.94

    head.data.materials.append(material)
    smooth_mesh(head)
    group = head.vertex_groups.new(name="Head")
    group.add(list(range(len(head.data.vertices))), 1.0, "REPLACE")
    subdivision = head.modifiers.new(name="Face_Subdivision", type="SUBSURF")
    subdivision.levels = 1
    subdivision.render_levels = 1
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.modifier_apply(modifier=subdivision.name)
    parts.append(head)
    return head


def create_hand_with_fingers(
    side: str,
    sign: float,
    wrist: Vector,
    hand_end: Vector,
    scale: float,
    skin: bpy.types.Material,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    direction = (hand_end - wrist).normalized()
    palm_end = wrist + (hand_end - wrist) * 0.63
    palm = create_loft_mesh(
        f"{side}_Palm",
        [
            (wrist, 0.043 * scale, 0.030 * scale, {f"{side}Hand": 1.0}),
            (lerp(wrist, palm_end, 0.45), 0.052 * scale, 0.034 * scale, {f"{side}Hand": 1.0}),
            (palm_end, 0.047 * scale, 0.029 * scale, {f"{side}Hand": 1.0}),
        ],
        skin,
        segments=14,
        subdivision=1,
    )
    objects.append(palm)

    finger_offsets = (-0.027, -0.009, 0.009, 0.027)
    finger_lengths = (0.070, 0.082, 0.078, 0.063)
    for index, (offset, length) in enumerate(zip(finger_offsets, finger_lengths, strict=True)):
        base = palm_end + Vector((0.0, offset * scale, 0.0))
        tip = base + direction * (length * scale)
        finger = create_loft_mesh(
            f"{side}_Finger_{index + 1}",
            [
                (base, 0.012 * scale, 0.010 * scale, {f"{side}Hand": 1.0}),
                (lerp(base, tip, 0.55), 0.010 * scale, 0.009 * scale, {f"{side}Hand": 1.0}),
                (tip, 0.006 * scale, 0.006 * scale, {f"{side}Hand": 1.0}),
            ],
            skin,
            segments=10,
            subdivision=1,
        )
        objects.append(finger)

    thumb_base = lerp(wrist, palm_end, 0.43) + Vector((-sign * 0.035 * scale, -0.018 * scale, 0.0))
    thumb_tip = thumb_base + Vector((-sign * 0.048 * scale, -0.014 * scale, -0.035 * scale))
    thumb = create_loft_mesh(
        f"{side}_Thumb",
        [
            (thumb_base, 0.014 * scale, 0.012 * scale, {f"{side}Hand": 1.0}),
            (lerp(thumb_base, thumb_tip, 0.55), 0.011 * scale, 0.010 * scale, {f"{side}Hand": 1.0}),
            (thumb_tip, 0.007 * scale, 0.006 * scale, {f"{side}Hand": 1.0}),
        ],
        skin,
        segments=10,
        subdivision=1,
    )
    objects.append(thumb)
    return objects


def create_panel(
    name: str,
    x_left: float,
    x_right: float,
    y: float,
    z_top: float,
    z_bottom: float,
    bottom_spread: float,
    material: bpy.types.Material,
    bone_name: str,
) -> bpy.types.Object:
    vertices = [
        (x_left, y, z_top),
        (x_right, y, z_top),
        (x_right + bottom_spread, y, z_bottom),
        (x_left - bottom_spread, y, z_bottom),
    ]
    mesh_data = bpy.data.meshes.new(f"{name}-data")
    mesh_data.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh_data.update()
    obj = bpy.data.objects.new(name, mesh_data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    group = obj.vertex_groups.new(name=bone_name)
    group.add(list(range(4)), 1.0, "REPLACE")
    bpy.context.view_layer.objects.active = obj
    solidify = obj.modifiers.new(name="Garment_Thickness", type="SOLIDIFY")
    solidify.thickness = 0.005
    bpy.ops.object.modifier_apply(modifier=solidify.name)
    bevel = obj.modifiers.new(name="Garment_Edge", type="BEVEL")
    bevel.width = 0.0025
    bevel.segments = 2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def build_detailed_character(
    spec: CharacterSpec,
    armature: bpy.types.Object,
    points: dict[str, Vector],
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    s = spec.height / 1.78
    meshes: list[bpy.types.Object] = []
    body_parts: list[bpy.types.Object] = []

    # Continuous lofted torso and limbs beneath the fitted clothing.
    body_parts.append(
        create_loft_mesh(
            "Body_Torso",
            [
                (Vector((0.0, 0.0, 0.84 * s)), spec.hip_x * 0.60 * s, 0.082 * s, {"Hips": 1.0}),
                (Vector((0.0, 0.0, 0.96 * s)), spec.hip_x * 0.68 * s, 0.088 * s, {"Hips": 0.8, "Spine": 0.2}),
                (Vector((0.0, 0.0, 1.08 * s)), spec.waist_x * 0.65 * s, 0.073 * s, {"Spine": 1.0}),
                (Vector((0.0, 0.0, 1.23 * s)), spec.chest_x * 0.70 * s, 0.086 * s, {"Spine": 0.25, "Chest": 0.75}),
                (Vector((0.0, 0.0, 1.37 * s)), spec.shoulder_x * 0.60 * s, 0.083 * s, {"Chest": 0.35, "UpperChest": 0.65}),
                (Vector((0.0, 0.0, 1.43 * s)), 0.082 * s, 0.068 * s, {"UpperChest": 1.0}),
            ],
            materials["skin"],
            segments=24,
            subdivision=1,
        )
    )

    for side, sign in (("Left", 1.0), ("Right", -1.0)):
        shoulder = points[f"{side}_shoulder"]
        elbow = points[f"{side}_elbow"]
        wrist = points[f"{side}_wrist"]
        hip = points[f"{side}_hip"]
        knee = points[f"{side}_knee"]
        ankle = points[f"{side}_ankle"]

        body_parts.append(
            create_loft_mesh(
                f"{side}_Arm_Anatomy",
                [
                    (shoulder, 0.078 * s, 0.075 * s, {f"{side}Shoulder": 0.25, f"{side}Arm": 0.75}),
                    (lerp(shoulder, elbow, 0.28), 0.068 * s, 0.064 * s, {f"{side}Arm": 1.0}),
                    (lerp(shoulder, elbow, 0.72), 0.061 * s, 0.058 * s, {f"{side}Arm": 0.8, f"{side}ForeArm": 0.2}),
                    (elbow, 0.050 * s, 0.047 * s, {f"{side}Arm": 0.45, f"{side}ForeArm": 0.55}),
                    (lerp(elbow, wrist, 0.38), 0.058 * s, 0.052 * s, {f"{side}ForeArm": 1.0}),
                    (lerp(elbow, wrist, 0.75), 0.047 * s, 0.042 * s, {f"{side}ForeArm": 0.85, f"{side}Hand": 0.15}),
                    (wrist, 0.035 * s, 0.030 * s, {f"{side}ForeArm": 0.35, f"{side}Hand": 0.65}),
                ],
                materials["skin"],
                segments=18,
                subdivision=1,
            )
        )
        body_parts.extend(
            create_hand_with_fingers(
                side,
                sign,
                wrist,
                points[f"{side}_hand_end"],
                s,
                materials["skin"],
            )
        )
        body_parts.append(
            create_loft_mesh(
                f"{side}_Leg_Anatomy",
                [
                    (hip, 0.066 * s, 0.062 * s, {"Hips": 0.22, f"{side}UpLeg": 0.78}),
                    (lerp(hip, knee, 0.30), 0.069 * s, 0.064 * s, {f"{side}UpLeg": 1.0}),
                    (lerp(hip, knee, 0.75), 0.052 * s, 0.048 * s, {f"{side}UpLeg": 0.82, f"{side}Leg": 0.18}),
                    (knee, 0.045 * s, 0.043 * s, {f"{side}UpLeg": 0.42, f"{side}Leg": 0.58}),
                    (lerp(knee, ankle, 0.35), 0.052 * s, 0.048 * s, {f"{side}Leg": 1.0}),
                    (lerp(knee, ankle, 0.72), 0.040 * s, 0.036 * s, {f"{side}Leg": 1.0}),
                    (ankle, 0.032 * s, 0.029 * s, {f"{side}Leg": 0.42, f"{side}Foot": 0.58}),
                ],
                materials["skin"],
                segments=18,
                subdivision=1,
            )
        )

    create_shaped_head(spec, materials["skin"], body_parts)
    add_segment(
        "Neck_Organic",
        Vector((0.0, 0.0, 1.415 * s)),
        Vector((0.0, 0.0, 1.535 * s)),
        0.058 * s,
        0.061 * s,
        materials["skin"],
        "Neck",
        body_parts,
        vertices=18,
    )

    # Ears and a three-part nose establish a readable facial profile.
    for sign in (-1.0, 1.0):
        add_ellipsoid(
            f"Ear_{sign:+.0f}",
            Vector((sign * 0.104 * s, 0.0, 1.635 * s)),
            Vector((0.013 * s, 0.009 * s, 0.029 * s)),
            materials["skin"],
            "Head",
            body_parts,
            segments=12,
            rings=8,
        )
    add_ellipsoid(
        "Nose_Bridge",
        Vector((0.0, -0.096 * s, 1.648 * s)),
        Vector((0.015 * s, 0.016 * s, 0.042 * s)),
        materials["skin"],
        "Head",
        body_parts,
        segments=14,
        rings=8,
    )
    add_ellipsoid(
        "Nose_Tip",
        Vector((0.0, -0.112 * s, 1.613 * s)),
        Vector((0.020 * s, 0.018 * s, 0.017 * s)),
        materials["skin"],
        "Head",
        body_parts,
        segments=14,
        rings=8,
    )
    body = join_mesh_objects(body_parts, "Body_Skin_Detailed")
    body["source_reference"] = f"docs/character-concepts/{'initial-female' if spec.female else 'initial-male'}-turnaround.png"
    rig_mesh(body, armature)
    meshes.append(body)

    # Eyes, irises, pupils, eyebrows, and two subtle lip forms.
    face_parts: list[bpy.types.Object] = []
    for sign in (-1.0, 1.0):
        add_ellipsoid(
            f"Eye_White_{sign:+.0f}",
            Vector((sign * 0.039 * s, -0.095 * s, 1.653 * s)),
            Vector((0.021 * s, 0.0065 * s, 0.0105 * s)),
            materials["eye_white"],
            "Head",
            face_parts,
            segments=16,
            rings=10,
        )
        add_ellipsoid(
            f"Iris_{sign:+.0f}",
            Vector((sign * 0.039 * s, -0.105 * s, 1.653 * s)),
            Vector((0.0075 * s, 0.003 * s, 0.0075 * s)),
            materials["iris"],
            "Head",
            face_parts,
            segments=12,
            rings=8,
        )
        add_ellipsoid(
            f"Pupil_{sign:+.0f}",
            Vector((sign * 0.039 * s, -0.109 * s, 1.653 * s)),
            Vector((0.0035 * s, 0.0015 * s, 0.0035 * s)),
            materials["eye"],
            "Head",
            face_parts,
            segments=10,
            rings=6,
        )
        face_parts.append(
            create_curve_tube(
                f"Brow_{sign:+.0f}",
                [
                    Vector((sign * 0.068 * s, -0.103 * s, 1.687 * s)),
                    Vector((sign * 0.041 * s, -0.108 * s, 1.693 * s)),
                    Vector((sign * 0.016 * s, -0.103 * s, 1.688 * s)),
                ],
                [0.75, 1.0, 0.65],
                0.0032 * s,
                materials["hair"],
                "Head",
            )
        )
    for z, radius in ((1.582, 0.0034), (1.576, 0.0028)):
        face_parts.append(
            create_curve_tube(
                f"Lip_{z}",
                [
                    Vector((-0.032 * s, -0.105 * s, z * s)),
                    Vector((0.0, -0.110 * s, (z + 0.002) * s)),
                    Vector((0.032 * s, -0.105 * s, z * s)),
                ],
                [0.6, 1.0, 0.6],
                radius * s,
                materials["mouth"],
                "Head",
            )
        )
    face = join_mesh_objects(face_parts, "Face_Details")
    rig_mesh(face, armature)
    meshes.append(face)

    # Hair cap and layered tapered locks, with different silhouettes per character.
    hair_parts: list[bpy.types.Object] = []
    add_ellipsoid(
        "Hair_Scalp_Cap",
        Vector((0.0, 0.020 * s, 1.700 * s)),
        Vector((0.112 * s, 0.101 * s, (0.093 if spec.female else 0.083) * s)),
        materials["hair"],
        "Head",
        hair_parts,
        segments=24,
        rings=14,
    )
    if spec.female:
        add_ellipsoid(
            "Bob_Back_Volume",
            Vector((0.0, 0.061 * s, 1.615 * s)),
            Vector((0.108 * s, 0.061 * s, 0.108 * s)),
            materials["hair"],
            "Head",
            hair_parts,
            segments=20,
            rings=12,
        )
        for sign in (-1.0, 1.0):
            add_ellipsoid(
                f"Bob_Side_{sign:+.0f}",
                Vector((sign * 0.102 * s, -0.003 * s, 1.615 * s)),
                Vector((0.034 * s, 0.055 * s, 0.098 * s)),
                materials["hair_highlight" if sign > 0 else "hair"],
                "Head",
                hair_parts,
                segments=16,
                rings=10,
            )
        lock_specs = []
        for index in range(18):
            angle = 2.0 * math.pi * index / 18
            x = math.cos(angle) * 0.094 * s
            y = math.sin(angle) * 0.076 * s + 0.018 * s
            end_z = (1.545 + 0.018 * abs(math.cos(angle))) * s
            lock_specs.append(
                (
                    Vector((x * 0.75, y * 0.72, 1.735 * s)),
                    Vector((x, y, 1.640 * s)),
                    Vector((x * 1.02, y - 0.004 * s, end_z)),
                )
            )
    else:
        add_ellipsoid(
            "Male_Hair_Back",
            Vector((0.0, 0.067 * s, 1.655 * s)),
            Vector((0.096 * s, 0.046 * s, 0.074 * s)),
            materials["hair"],
            "Head",
            hair_parts,
            segments=18,
            rings=10,
        )
        for index, x in enumerate((-0.075, -0.050, -0.024, 0.004, 0.034, 0.064)):
            lock = add_ellipsoid(
                f"Male_Fringe_{index}",
                Vector((x * s, -0.073 * s, (1.720 + 0.010 * (index % 2)) * s)),
                Vector((0.025 * s, 0.018 * s, (0.050 + 0.006 * (index % 3)) * s)),
                materials["hair_highlight" if index % 3 == 0 else "hair"],
                "Head",
                hair_parts,
                segments=12,
                rings=8,
            )
            lock.rotation_euler.y = math.radians(-18 + index * 7)
        lock_specs = []
        for index in range(14):
            angle = 2.0 * math.pi * index / 14
            x = math.cos(angle) * 0.086 * s
            y = math.sin(angle) * 0.073 * s + 0.005 * s
            tip_offset = (0.018 + 0.010 * (index % 3)) * s
            lock_specs.append(
                (
                    Vector((x * 0.55, y * 0.55, 1.740 * s)),
                    Vector((x, y, 1.705 * s)),
                    Vector((x * 1.18, y - tip_offset * 0.35, (1.690 + tip_offset) * s)),
                )
            )
    for index, coordinates in enumerate(lock_specs):
        hair_parts.append(
            create_curve_tube(
                f"Hair_Lock_{index:02d}",
                list(coordinates),
                [1.15, 1.0, 0.16],
                (0.014 if spec.female else 0.013) * s,
                materials["hair_highlight" if index % 4 == 0 else "hair"],
                "Head",
            )
        )
    hair = join_mesh_objects(hair_parts, "Hair_Layered")
    rig_mesh(hair, armature)
    meshes.append(hair)

    # Reference-specific fitted teal tunic and sleeves.
    tunic_parts: list[bpy.types.Object] = []
    tunic_parts.append(
        create_loft_mesh(
            "Tunic_Fitted_Body",
            [
                (Vector((0.0, 0.0, 0.89 * s)), spec.hip_x * 1.08 * s, 0.132 * s, {"Hips": 0.9, "Spine": 0.1}),
                (Vector((0.0, 0.0, 1.01 * s)), spec.waist_x * 1.07 * s, 0.116 * s, {"Hips": 0.42, "Spine": 0.58}),
                (Vector((0.0, 0.0, 1.13 * s)), spec.waist_x * 1.00 * s, 0.111 * s, {"Spine": 1.0}),
                (Vector((0.0, 0.0, 1.27 * s)), spec.chest_x * 0.98 * s, 0.134 * s, {"Spine": 0.22, "Chest": 0.78}),
                (Vector((0.0, 0.0, 1.39 * s)), spec.shoulder_x * 0.86 * s, 0.126 * s, {"Chest": 0.35, "UpperChest": 0.65}),
                (Vector((0.0, 0.0, 1.435 * s)), 0.105 * s, 0.081 * s, {"UpperChest": 1.0}),
                (Vector((0.0, 0.0, 1.485 * s)), 0.072 * s, 0.061 * s, {"UpperChest": 0.35, "Neck": 0.65}),
            ],
            materials["teal"],
            segments=24,
            subdivision=1,
        )
    )
    linen_parts: list[bpy.types.Object] = []
    for side in ("Left", "Right"):
        shoulder = points[f"{side}_shoulder"]
        elbow = points[f"{side}_elbow"]
        wrist = points[f"{side}_wrist"]
        sleeve_end = lerp(shoulder, elbow, 0.45)
        tunic_parts.append(
            create_loft_mesh(
                f"{side}_Teal_Outer_Sleeve",
                [
                    (shoulder, 0.076 * s, 0.073 * s, {f"{side}Shoulder": 0.2, f"{side}Arm": 0.8}),
                    (lerp(shoulder, sleeve_end, 0.48), 0.073 * s, 0.069 * s, {f"{side}Arm": 1.0}),
                    (sleeve_end, 0.068 * s, 0.064 * s, {f"{side}Arm": 1.0}),
                ],
                materials["teal"],
                segments=18,
                subdivision=1,
            )
        )
        linen_end = lerp(elbow, wrist, 0.48)
        linen_parts.append(
            create_loft_mesh(
                f"{side}_Linen_Undersleeve",
                [
                    (sleeve_end, 0.070 * s, 0.066 * s, {f"{side}Arm": 1.0}),
                    (elbow, 0.057 * s, 0.053 * s, {f"{side}Arm": 0.42, f"{side}ForeArm": 0.58}),
                    (linen_end, 0.058 * s, 0.052 * s, {f"{side}ForeArm": 1.0}),
                ],
                materials["linen"],
                segments=18,
                subdivision=1,
            )
        )
    tunic = join_mesh_objects(tunic_parts, "Guild_Tunic_Fitted")
    rig_mesh(tunic, armature)
    meshes.append(tunic)
    linen = join_mesh_objects(linen_parts, "Linen_Undersleeves")
    rig_mesh(linen, armature)
    meshes.append(linen)

    # Tapered trousers with anatomical knee/calf landmarks.
    trouser_parts: list[bpy.types.Object] = []
    trouser_parts.append(
        create_loft_mesh(
            "Trousers_Pelvis",
            [
                (Vector((0.0, 0.0, 0.78 * s)), spec.hip_x * 0.80 * s, 0.105 * s, {"Hips": 1.0}),
                (Vector((0.0, 0.0, 0.89 * s)), spec.hip_x * 1.02 * s, 0.122 * s, {"Hips": 1.0}),
                (Vector((0.0, 0.0, 0.98 * s)), spec.hip_x * 0.96 * s, 0.116 * s, {"Hips": 1.0}),
            ],
            materials["charcoal"],
            segments=24,
            subdivision=1,
        )
    )
    for side in ("Left", "Right"):
        hip = points[f"{side}_hip"]
        knee = points[f"{side}_knee"]
        ankle = points[f"{side}_ankle"]
        boot_top = lerp(knee, ankle, 0.67)
        trouser_parts.append(
            create_loft_mesh(
                f"{side}_Trouser_Leg",
                [
                    (hip, (0.101 if spec.female else 0.096) * s, 0.094 * s, {"Hips": 0.18, f"{side}UpLeg": 0.82}),
                    (lerp(hip, knee, 0.30), 0.099 * s, 0.092 * s, {f"{side}UpLeg": 1.0}),
                    (lerp(hip, knee, 0.76), 0.075 * s, 0.068 * s, {f"{side}UpLeg": 0.82, f"{side}Leg": 0.18}),
                    (knee, 0.065 * s, 0.060 * s, {f"{side}UpLeg": 0.42, f"{side}Leg": 0.58}),
                    (lerp(knee, boot_top, 0.45), 0.073 * s, 0.065 * s, {f"{side}Leg": 1.0}),
                    (boot_top, 0.057 * s, 0.051 * s, {f"{side}Leg": 1.0}),
                ],
                materials["charcoal"],
                segments=18,
                subdivision=1,
            )
        )
    trousers = join_mesh_objects(trouser_parts, "Charcoal_Trousers_Tapered")
    rig_mesh(trousers, armature)
    meshes.append(trousers)

    # Boots are built from ankle/heel/midfoot/toe lasts rather than boxes.
    leather_parts: list[bpy.types.Object] = []
    sole_parts: list[bpy.types.Object] = []
    for side in ("Left", "Right"):
        knee = points[f"{side}_knee"]
        ankle = points[f"{side}_ankle"]
        toe = points[f"{side}_toe"]
        boot_top = lerp(knee, ankle, 0.67)
        leather_parts.append(
            create_loft_mesh(
                f"{side}_Boot_Shaft",
                [
                    (boot_top, 0.066 * s, 0.060 * s, {f"{side}Leg": 1.0}),
                    (lerp(boot_top, ankle, 0.50), 0.061 * s, 0.056 * s, {f"{side}Leg": 0.82, f"{side}Foot": 0.18}),
                    (ankle, 0.058 * s, 0.052 * s, {f"{side}Leg": 0.38, f"{side}Foot": 0.62}),
                ],
                materials["leather"],
                segments=18,
                subdivision=1,
            )
        )
        heel = ankle + Vector((0.0, 0.055 * s, -0.045 * s))
        midfoot = lerp(ankle, toe, 0.52) + Vector((0.0, -0.012 * s, -0.020 * s))
        toe_tip = toe + Vector((0.0, -0.035 * s, 0.0))
        leather_parts.append(
            create_loft_mesh(
                f"{side}_Boot_Last",
                [
                    (ankle, 0.058 * s, 0.050 * s, {f"{side}Foot": 1.0}),
                    (heel, 0.067 * s, 0.054 * s, {f"{side}Foot": 1.0}),
                    (midfoot, 0.073 * s, 0.050 * s, {f"{side}Foot": 1.0}),
                    (toe_tip, 0.070 * s, 0.039 * s, {f"{side}Foot": 1.0}),
                ],
                materials["leather"],
                segments=18,
                subdivision=1,
            )
        )
        sole_parts.append(
            create_loft_mesh(
                f"{side}_Boot_Sole",
                [
                    (heel + Vector((0.0, 0.0, -0.046 * s)), 0.071 * s, 0.018 * s, {f"{side}Foot": 1.0}),
                    (midfoot + Vector((0.0, 0.0, -0.047 * s)), 0.078 * s, 0.018 * s, {f"{side}Foot": 1.0}),
                    (toe_tip + Vector((0.0, 0.0, -0.039 * s)), 0.075 * s, 0.015 * s, {f"{side}Foot": 1.0}),
                ],
                materials["sole"],
                segments=18,
                subdivision=1,
            )
        )
    boots = join_mesh_objects(leather_parts, "Leather_Boots_Shaped")
    rig_mesh(boots, armature)
    meshes.append(boots)
    soles = join_mesh_objects(sole_parts, "Boot_Soles")
    rig_mesh(soles, armature)
    meshes.append(soles)

    # Sash/belt, layered skirt panels, asymmetrical placket, piping, frog closures and seams.
    detail_parts: list[bpy.types.Object] = []
    bronze_parts: list[bpy.types.Object] = []
    belt_depth = 0.125 * s
    if spec.female:
        add_elliptic_cone(
            "Wide_Wrapped_Sash",
            Vector((0.0, 0.0, 1.00 * s)),
            0.105 * s,
            spec.waist_x * 1.11 * s,
            spec.waist_x * 1.08 * s,
            belt_depth / (spec.waist_x * s),
            materials["leather"],
            "Hips",
            detail_parts,
            vertices=20,
        )
    else:
        for z in (0.985, 1.025):
            add_elliptic_cone(
                f"Double_Belt_{z}",
                Vector((0.0, 0.0, z * s)),
                0.035 * s,
                spec.waist_x * 1.10 * s,
                spec.waist_x * 1.08 * s,
                belt_depth / (spec.waist_x * s),
                materials["leather"],
                "Hips",
                detail_parts,
                vertices=20,
            )

    front_y = -0.139 * s
    panel_width = (0.115 if spec.female else 0.105) * s
    detail_parts.extend(
        [
            create_panel(
                "Front_Skirt_Panel_Left",
                -panel_width,
                -0.006 * s,
                front_y,
                0.99 * s,
                0.78 * s,
                0.018 * s,
                materials["teal"],
                "Hips",
            ),
            create_panel(
                "Front_Skirt_Panel_Right",
                0.006 * s,
                panel_width,
                front_y,
                0.99 * s,
                0.78 * s,
                0.018 * s,
                materials["teal"],
                "Hips",
            ),
            create_panel(
                "Back_Skirt_Panel",
                -panel_width,
                panel_width,
                0.139 * s,
                0.99 * s,
                0.80 * s,
                0.015 * s,
                materials["teal_dark"],
                "Hips",
            ),
        ]
    )

    placket_coordinates = (
        [
            Vector((-0.015 * s, -0.105 * s, 1.415 * s)),
            Vector((-0.080 * s, -0.135 * s, 1.335 * s)),
            Vector((-0.045 * s, -0.128 * s, 1.220 * s)),
            Vector((-0.020 * s, -0.118 * s, 1.075 * s)),
        ]
        if spec.female
        else [
            Vector((0.015 * s, -0.105 * s, 1.415 * s)),
            Vector((-0.075 * s, -0.135 * s, 1.335 * s)),
            Vector((-0.085 * s, -0.124 * s, 1.160 * s)),
            Vector((-0.075 * s, -0.117 * s, 1.055 * s)),
        ]
    )
    bronze_parts.append(
        create_curve_tube(
            "Asymmetric_Plaquet_Piping",
            placket_coordinates,
            [0.8, 1.0, 1.0, 0.72],
            0.0042 * s,
            materials["bronze"],
            "Chest",
        )
    )
    closure_zs = (1.345,) if spec.female else (1.34, 1.275, 1.21)
    for index, z in enumerate(closure_zs):
        bronze_parts.append(
            create_curve_tube(
                f"Frog_Closure_{index}",
                [
                    Vector((-0.075 * s, -0.136 * s, z * s)),
                    Vector((-0.025 * s, -0.141 * s, z * s)),
                    Vector((0.025 * s, -0.136 * s, z * s)),
                ],
                [0.65, 1.0, 0.65],
                0.005 * s,
                materials["bronze"],
                "Chest",
            )
        )
    add_beveled_box(
        "Belt_Buckle_Detailed",
        Vector((0.0, -belt_depth * 1.06, 1.005 * s)),
        Vector((0.060 * s, 0.018 * s, 0.046 * s)),
        materials["bronze"],
        "Hips",
        bronze_parts,
        bevel=0.007 * s,
    )
    details = join_mesh_objects(detail_parts, "Garment_Layers_And_Belts")
    rig_mesh(details, armature)
    meshes.append(details)
    bronze = join_mesh_objects(bronze_parts, "Bronze_Piping_Closures")
    rig_mesh(bronze, armature)
    meshes.append(bronze)

    for mesh in meshes:
        mesh.data.validate(verbose=False, clean_customdata=True)
        mesh.data.update(calc_edges=True)
        mesh["model_version"] = "v2-detailed"
        mesh["style"] = "stylized realistic ancient guild trainee"
    return meshes


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
    meshes: list[bpy.types.Object],
) -> tuple[Path, Path]:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    blend_path = SOURCE_DIR / f"{spec.slug}.blend"
    glb_path = MODEL_DIR / f"{spec.slug}.glb"

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    for mesh in meshes:
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
    meshes = build_detailed_character(spec, armature, points, materials)
    actions = create_animations(armature, spec.height / 1.78)
    blend_path, glb_path = save_and_export(spec, armature, meshes)
    preview_path = render_preview(spec, armature)

    vertex_count = sum(len(mesh.data.vertices) for mesh in meshes)
    triangle_count = sum(
        sum(len(polygon.vertices) - 2 for polygon in mesh.data.polygons) for mesh in meshes
    )
    print(
        f"GENERATED {spec.slug}: "
        f"vertices={vertex_count} triangles={triangle_count} meshes={len(meshes)} "
        f"bones={len(armature.data.bones)} animations={','.join(action.name for action in actions)} "
        f"blend={blend_path} glb={glb_path} preview={preview_path}"
    )


def main() -> None:
    for spec in CHARACTERS:
        generate_character(spec)
    print("All initial character models generated successfully.")


if __name__ == "__main__":
    main()
