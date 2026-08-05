"""Build clean, fully modelled guild trainees from MPFB game topology.

Unlike the rejected v4/v5 experiments, this pipeline never projects the
turnaround sheet onto a generated surface.  The face, hands, hair, clothes and
boots are real meshes with a 53-bone game rig.  Small tileable material maps are
generated locally and embedded in the GLB; the turnaround is used only as a
shape and costume reference.

Run with the normal Blender profile so the MPFB extension is available::

    & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" `
      --background --python scripts\\build_clean_characters_v6.py -- `
      --revision v6.2
"""

from __future__ import annotations

import argparse
import bmesh
import importlib
import json
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import bpy
from mathutils import Vector

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import build_reference_characters_v3 as v3


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_ROOT / "art-source" / "characters" / "work" / "v3"
SOURCE_ROOT = PROJECT_ROOT / "art-source" / "characters" / "history"
MODEL_ROOT = PROJECT_ROOT / "public" / "models" / "characters" / "history"
PREVIEW_ROOT = PROJECT_ROOT / "docs" / "character-concepts" / "model-history"
TEXTURE_DIR = PROJECT_ROOT / "art-source" / "characters" / "textures" / "v6"
SCRIPT_PATH = "scripts/build_clean_characters_v6.py"


@dataclass(frozen=True)
class Profile:
    key: str
    slug: str
    base_file: str
    clothing_asset: str
    sleeve_asset: str
    hair_asset: str
    female: bool
    hair_hex: str

    @property
    def reference_file(self) -> str:
        return f"initial-{self.key}-turnaround.png"


PROFILES = (
    Profile(
        "male",
        "initial-male-v6",
        "initial-male-base.blend",
        "male_casualsuit02.mhclo",
        "male_casualsuit01.mhclo",
        "short02.mhclo",
        False,
        "241A16",
    ),
    Profile(
        "female",
        "initial-female-v6",
        "initial-female-base.blend",
        "female_casualsuit01.mhclo",
        "female_elegantsuit01.mhclo",
        "bob02.mhclo",
        True,
        "612D2A",
    ),
)


def mpfb_symbol(module_suffix: str, symbol: str):
    for module_name in tuple(sys.modules):
        if module_name.endswith(module_suffix):
            module = importlib.import_module(module_name)
            if hasattr(module, symbol):
                return getattr(module, symbol)
    raise RuntimeError(
        f"MPFB is not loaded ({module_suffix}); use the normal Blender profile"
    )


HumanService = mpfb_symbol("mpfb.services.humanservice", "HumanService")
AssetService = mpfb_symbol("mpfb.services.assetservice", "AssetService")


def bundled_asset(name: str, subdir: str) -> str:
    path = AssetService.find_asset_absolute_path(name, asset_subdir=subdir)
    if path is None or not Path(path).is_file():
        raise FileNotFoundError(f"Bundled MPFB asset is missing: {subdir}/{name}")
    return str(path)


def add_mpfb_asset(
    body: bpy.types.Object,
    name: str,
    subdir: str,
    asset_type: str,
) -> bpy.types.Object:
    obj = HumanService.add_mhclo_asset(
        bundled_asset(name, subdir),
        body,
        asset_type=asset_type,
        subdiv_levels=1,
        material_type="GAMEENGINE",
        set_up_rigging=True,
        interpolate_weights=True,
        import_subrig=True,
        import_weights=True,
    )
    obj.name = f"V6_{asset_type}_{Path(name).stem}"
    return obj


def linear_rgb(hex_value: str) -> tuple[float, float, float]:
    return v3.hex_color(hex_value)[:3]


def texture_pixels(
    base_hex: str,
    style: str,
    *,
    size: int = 512,
    seed: int = 0,
) -> list[float]:
    base = linear_rgb(base_hex)
    rng = random.Random(seed)
    pixels: list[float] = []
    phase_x = rng.random() * math.tau
    phase_y = rng.random() * math.tau
    for y in range(size):
        for x in range(size):
            u = x / size
            w = y / size
            grain = rng.uniform(-1.0, 1.0)
            if style == "fabric":
                weave = math.sin((x + 0.5) * math.pi) * 0.030
                weave += math.sin((y + 0.5) * math.pi) * 0.024
                diagonal = math.sin((u + w) * math.tau * 14.0 + phase_x) * 0.014
                shade = 1.0 + weave + diagonal + grain * 0.012
            elif style == "linen":
                warp = math.sin(x * math.tau / 3.0 + phase_x) * 0.040
                weft = math.sin(y * math.tau / 5.0 + phase_y) * 0.024
                shade = 1.0 + warp + weft + grain * 0.020
            elif style == "leather":
                broad = math.sin(u * math.tau * 3.0 + math.sin(w * 9.0)) * 0.020
                shade = 1.0 + broad + grain * 0.025
            elif style == "hair":
                strands = math.sin((x + math.sin(y * 0.12)) * math.tau / 7.0) * 0.050
                shade = 1.0 + strands + grain * 0.015
            else:
                shade = 1.0 + grain * 0.010
            pixels.extend((*[max(0.0, min(1.0, channel * shade)) for channel in base], 1.0))
    return pixels


def create_texture(name: str, base_hex: str, style: str, seed: int) -> bpy.types.Image:
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
    image = bpy.data.images.get(name)
    if image is None or image.size[:] != [512, 512]:
        if image is not None:
            bpy.data.images.remove(image)
        image = bpy.data.images.new(name, width=512, height=512)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(texture_pixels(base_hex, style, seed=seed))
    image.file_format = "PNG"
    image.filepath_raw = str(TEXTURE_DIR / f"{name}.png")
    image.save()
    image.pack()
    return image


def textured_material(
    name: str,
    base_hex: str,
    style: str,
    *,
    roughness: float,
    metallic: float = 0.0,
    bump_strength: float = 0.08,
    seed: int = 0,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = v3.hex_color(base_hex)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (420, 0)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (140, 0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    texture = nodes.new("ShaderNodeTexImage")
    texture.location = (-420, 40)
    texture.image = create_texture(name.lower(), base_hex, style, seed)
    texture.interpolation = "Linear"
    bump = nodes.new("ShaderNodeBump")
    bump.location = (-90, -150)
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.035
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def solid_material(
    name: str,
    base_hex: str,
    *,
    roughness: float,
    metallic: float = 0.0,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = v3.hex_color(base_hex)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = v3.hex_color(base_hex)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def create_materials(profile: Profile) -> dict[str, bpy.types.Material]:
    return {
        "teal": textured_material("V6_Guild_Teal", "10484B", "fabric", roughness=0.80, seed=11),
        "teal_dark": textured_material("V6_Guild_Teal_Dark", "092F32", "fabric", roughness=0.84, seed=12),
        "linen": textured_material("V6_Undyed_Linen", "B8AA8A", "linen", roughness=0.91, seed=21),
        "charcoal": textured_material("V6_Charcoal_Twill", "1A1E22", "fabric", roughness=0.88, seed=31),
        "leather": textured_material("V6_Brown_Leather", "2D231F", "leather", roughness=0.72, seed=41),
        "leather_dark": textured_material("V6_Dark_Leather", "15100F", "leather", roughness=0.80, seed=42),
        "hair": textured_material("V6_Hair", profile.hair_hex, "hair", roughness=0.60, seed=51 if profile.female else 52),
        "bronze": solid_material("V6_Aged_Bronze", "A7773D", roughness=0.43, metallic=0.55),
        "thread": solid_material("V6_Dark_Stitch", "121719", roughness=0.86),
    }


def sanitize_mpfb_character_materials(profile: Profile) -> None:
    """Make MPFB face materials deterministic for glTF export.

    MPFB creates a second image node for alpha even when it points at the same
    file as the diffuse node. The glTF exporter can interpret the skin image's
    alpha as transparency, exposing eyes, teeth and tongue through the face.
    Keep one image node and allow transparency only on eyebrows/eyelashes.
    """

    object_prefix = Path(profile.base_file).stem + "."
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or not obj.name.startswith(object_prefix):
            continue
        transparent_detail = obj.name.endswith(("Eyebrows", "Eyelashes"))
        for material in obj.data.materials:
            if material is None or not material.use_nodes:
                continue
            nodes = material.node_tree.nodes
            links = material.node_tree.links
            diffuse = nodes.get("DiffuseTexture")
            for node in tuple(nodes):
                if node.type == "TEX_IMAGE" and node != diffuse:
                    nodes.remove(node)
            for shader in (node for node in nodes if node.type == "BSDF_PRINCIPLED"):
                alpha = shader.inputs.get("Alpha")
                if alpha is not None:
                    for link in tuple(alpha.links):
                        links.remove(link)
                    alpha.default_value = 1.0
                    if transparent_detail and diffuse is not None:
                        links.new(diffuse.outputs["Alpha"], alpha)
            material.diffuse_color[3] = 1.0
            if hasattr(material, "surface_render_method"):
                material.surface_render_method = (
                    "DITHERED" if transparent_detail else "DITHERED"
                )


def replace_object_materials(obj: bpy.types.Object, materials: list[bpy.types.Material]) -> None:
    obj.data.materials.clear()
    for material in materials:
        obj.data.materials.append(material)


def object_group_weight(
    obj: bpy.types.Object,
    vertex_index: int,
    group_names: set[str],
) -> float:
    """Return the strongest matching deformation weight on an asset mesh."""

    matching = {
        group.index for group in obj.vertex_groups if group.name in group_names
    }
    return max(
        (
            membership.weight
            for membership in obj.data.vertices[vertex_index].groups
            if membership.group in matching
        ),
        default=0.0,
    )


def assign_clothing_materials(
    clothing: bpy.types.Object,
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: v3.BodyMetrics,
    materials: dict[str, bpy.types.Material],
    profile: Profile,
) -> None:
    # Keep a single authored garment surface. Overlaying a second garment for
    # the sleeves caused the torn double-shoulder silhouette in v6.2-v6.9.
    replace_object_materials(
        clothing,
        [materials["teal"], materials["charcoal"], materials["linen"]],
    )
    threshold = metrics.z(0.535 if profile.female else 0.510)
    chains = {
        side: (
            v3.bone_points(armature, body, f"upperarm_{side}"),
            v3.bone_points(armature, body, f"lowerarm_{side}"),
        )
        for side in ("l", "r")
    }
    color_break = 0.92 if profile.female else 0.44
    for polygon in clothing.data.polygons:
        center = clothing.matrix_world @ polygon.center
        chain_t, arm_distance = min(
            (
                v3.arm_chain_parameter(center, upper, lower)
                for upper, lower in chains.values()
            ),
            key=lambda result: result[1],
        )
        is_arm = arm_distance < metrics.height * 0.075 and -0.10 <= chain_t <= 1.65
        if center.z < threshold and not is_arm:
            polygon.material_index = 1
        elif is_arm and chain_t >= color_break:
            polygon.material_index = 2
        else:
            polygon.material_index = 0
    clothing["v6_role"] = "continuous fitted tunic, sleeves and trousers"
    clothing["source_asset"] = profile.clothing_asset


def add_garment_clearance(
    clothing: bpy.types.Object,
    metrics: v3.BodyMetrics,
    profile: Profile,
) -> None:
    """Keep the fitted garment outside the body after the reference pose bake.

    The female casual-suit shell sits exactly on the body at the bust apex.
    That produced two pin-sized skin leaks in renders and would flicker in a
    real-time depth buffer.  A small normal offset preserves the authored
    silhouette while giving the cloth a stable, game-ready clearance.
    """

    if not profile.female:
        return
    clearance = metrics.height * 0.0022
    for vertex in clothing.data.vertices:
        vertex.co += vertex.normal * clearance
    clothing.data.update(calc_edges=True)
    clothing["v6_surface_clearance_m"] = clearance


def remove_fully_clothed_body_surfaces(body: bpy.types.Object) -> int:
    """Remove skin that can never be seen beneath the full-body uniform.

    MPFB clothes can contain tiny gaps at extreme curvature.  Keeping the
    underlying torso and limbs makes those gaps show as skin pixels and also
    invites pose-dependent clipping.  This costume exposes only the head,
    neck and hands, so retain faces influenced by those bones and discard the
    permanently covered skin.
    """

    exposed_names = {"head", "neck_01", "hand_l", "hand_r"}
    exposed_names.update(
        group.name
        for group in body.vertex_groups
        if group.name.startswith(
            (
                "thumb_",
                "index_",
                "middle_",
                "ring_",
                "pinky_",
            )
        )
    )
    exposed_indices = {
        group.index for group in body.vertex_groups if group.name in exposed_names
    }
    if not exposed_indices:
        raise RuntimeError("Body has no exposed head/neck/hand deformation groups")

    bm = bmesh.new()
    bm.from_mesh(body.data)
    deform = bm.verts.layers.deform.active
    if deform is None:
        bm.free()
        raise RuntimeError("Body has no deformation layer")
    covered_faces = [
        face
        for face in bm.faces
        if max(
            (
                vertex[deform].get(group_index, 0.0)
                for vertex in face.verts
                for group_index in exposed_indices
            ),
            default=0.0,
        )
        < 0.05
    ]
    removed = len(covered_faces)
    bmesh.ops.delete(bm, geom=covered_faces, context="FACES")
    bm.to_mesh(body.data)
    bm.free()
    body.data.update(calc_edges=True)
    body["v6_removed_covered_skin_faces"] = removed
    return removed


def isolate_and_style_sleeves(
    sleeves: bpy.types.Object,
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: v3.BodyMetrics,
    materials: dict[str, bpy.types.Material],
    profile: Profile,
) -> None:
    """Keep only arm-weighted faces from a clean long-sleeve MHClO mesh."""

    arm_names = {"upperarm_l", "lowerarm_l", "upperarm_r", "lowerarm_r"}
    arm_indices = {
        group.index for group in sleeves.vertex_groups if group.name in arm_names
    }
    if not arm_indices:
        raise RuntimeError("Long-sleeve source has no arm deformation groups")
    chains = {
        side: (
            v3.bone_points(armature, body, f"upperarm_{side}"),
            v3.bone_points(armature, body, f"lowerarm_{side}"),
        )
        for side in ("l", "r")
    }

    bm = bmesh.new()
    bm.from_mesh(sleeves.data)
    deform = bm.verts.layers.deform.active
    if deform is None:
        bm.free()
        raise RuntimeError("Long-sleeve source has no deformation layer")
    remove_faces = []
    for face in bm.faces:
        arm_weight = sum(
            sum(vertex[deform].get(index, 0.0) for index in arm_indices)
            for vertex in face.verts
        ) / len(face.verts)
        center = sleeves.matrix_world @ face.calc_center_median()
        chain_t, _distance = min(
            (v3.arm_chain_parameter(center, upper, lower) for upper, lower in chains.values()),
            key=lambda result: result[1],
        )
        start_t = 0.36 if profile.female else -0.18
        if arm_weight < 0.18 or not start_t <= chain_t <= 1.58:
            remove_faces.append(face)
    bmesh.ops.delete(bm, geom=remove_faces, context="FACES")
    bm.to_mesh(sleeves.data)
    bm.free()
    sleeves.data.update(calc_edges=True)

    replace_object_materials(sleeves, [materials["teal"], materials["linen"]])
    color_break = 0.92 if profile.female else 0.44
    for polygon in sleeves.data.polygons:
        center = sleeves.matrix_world @ polygon.center
        chain_t, _distance = min(
            (v3.arm_chain_parameter(center, upper, lower) for upper, lower in chains.values()),
            key=lambda result: result[1],
        )
        polygon.material_index = 0 if chain_t <= color_break else 1
    sleeves["v6_role"] = "clean weighted two-material sleeves"
    sleeves["source_asset"] = profile.sleeve_asset
    sleeves["removed_non_sleeve_faces"] = len(remove_faces)


def ensure_uv(obj: bpy.types.Object) -> None:
    if obj.type != "MESH" or not obj.data.polygons:
        return
    if obj.data.uv_layers:
        return
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")


def arm_selector_factory(
    body: bpy.types.Object,
    metrics: v3.BodyMetrics,
    upper: tuple[Vector, Vector],
    lower: tuple[Vector, Vector],
    groups: set[str],
    start: float,
    end: float,
    *,
    min_weight: float = 0.07,
):
    def selector(poly, center: Vector, _zn: float) -> bool:
        weight = sum(v3.body_group_weight(body, index, groups) for index in poly.vertices) / len(poly.vertices)
        chain_t, distance = v3.arm_chain_parameter(center, upper, lower)
        return start <= chain_t <= end and weight > min_weight and distance < metrics.height * 0.09

    return selector


def create_sleeves_and_wraps(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: v3.BodyMetrics,
    profile: Profile,
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for side in ("l", "r"):
        upper = v3.bone_points(armature, body, f"upperarm_{side}")
        lower = v3.bone_points(armature, body, f"lowerarm_{side}")
        # The fitted MPFB shirt already owns the shoulder cap.  Restrict the
        # added shells to arm bones so clavicle-weighted chest faces cannot
        # form the jagged double shoulder seen in v6.2.
        groups = {f"upperarm_{side}", f"lowerarm_{side}"}
        label = side.upper()
        wrap_start = 1.67 if profile.female else 1.58
        wrap_end = 1.94
        for index in range(3):
            start = wrap_start + (wrap_end - wrap_start) * index / 3.0
            end = wrap_start + (wrap_end - wrap_start) * (index + 1) / 3.0 + 0.018
            objects.append(
                v3.extract_body_shell(
                    body,
                    armature,
                    metrics,
                    profile,
                    f"V6_Wrist_Wrap_{label}_{index + 1}",
                    materials["leather_dark" if index % 2 == 0 else "leather"],
                    arm_selector_factory(body, metrics, upper, lower, groups, start, end, min_weight=0.04),
                    base_offset=metrics.height * (0.0105 + index * 0.0004),
                    thickness=metrics.height * 0.0027,
                    category="modelled-wrist-wrap",
                )
            )
    return objects


def create_sleeve_transition_bands(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: v3.BodyMetrics,
    profile: Profile,
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    """Cover the teal/linen face boundary with an oriented bronze cuff."""

    objects: list[bpy.types.Object] = []
    chain_t = 0.92 if profile.female else 0.44
    for suffix, side in (("L", "l"), ("R", "r")):
        upper = v3.bone_points(armature, body, f"upperarm_{side}")
        lower = v3.bone_points(armature, body, f"lowerarm_{side}")
        if chain_t <= 1.0:
            start, end = upper
            point = start.lerp(end, chain_t)
            bone_name = f"upperarm_{side}"
        else:
            start, end = lower
            point = start.lerp(end, chain_t - 1.0)
            bone_name = f"lowerarm_{side}"
        direction = (end - start).normalized()
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=48,
            radius=metrics.height * (0.034 if profile.female else 0.038),
            depth=metrics.height * (0.006 if profile.female else 0.015),
            location=point,
        )
        band = bpy.context.object
        band.name = f"V6_Sleeve_Transition_Band_{suffix}"
        band.rotation_mode = "QUATERNION"
        band.rotation_quaternion = direction.to_track_quat("Z", "Y")
        band.data.materials.append(materials["bronze"])
        bevel = band.modifiers.new("V6_Band_Edge", "BEVEL")
        bevel.width = metrics.height * 0.0008
        bevel.segments = 2
        v3.rigid_weights(band, armature, bone_name)
        v3.mark_generated(band, profile, "modelled-sleeve-transition-band")
        objects.append(band)
    return objects


def create_uniform_details(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: v3.BodyMetrics,
    profile: Profile,
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    neck_x, neck_y, neck_width, neck_front, neck_back = v3.torso_section_at(
        body, metrics, 0.835, band=0.010, max_half_width=0.080
    )
    # Shoulder vertices share neck weights on this rig, so a raw torso slice
    # overestimates the collar by almost 2x. Use measured game-scale neck
    # radii while retaining the character's actual centre.
    neck_width = metrics.height * (0.033 if profile.female else 0.036)
    neck_front = metrics.height * (0.037 if profile.female else 0.039)
    neck_back = metrics.height * (0.020 if profile.female else 0.022)
    collar_center = Vector((neck_x, neck_y, metrics.z(0.854)))
    objects.append(
        v3.create_oval_band(
            "V6_Standing_Collar",
            collar_center,
            neck_width,
            neck_front,
            neck_back,
            metrics.height * (0.025 if profile.female else 0.028),
            materials["teal_dark"],
            armature,
            "neck_01",
            profile,
            "modelled-standing-collar",
            bevel=metrics.height * 0.0010,
        )
    )
    objects.append(
        v3.create_oval_band(
            "V6_Collar_Linen_Trim",
            Vector((neck_x, neck_y, metrics.z(0.869))),
            neck_width * 1.005,
            neck_front * 1.005,
            neck_back * 1.005,
            metrics.height * 0.0045,
            materials["linen"],
            armature,
            "neck_01",
            profile,
            "modelled-collar-trim",
            bevel=metrics.height * 0.0006,
        )
    )

    chest_x, chest_y, _width, chest_front, chest_back = v3.torso_section_at(body, metrics, 0.72)

    def front_surface_point(x_offset: float, z_norm: float, extra: float = 0.005) -> Vector:
        section_x, section_y, _section_width, section_front, _section_back = v3.torso_section_at(
            body,
            metrics,
            z_norm,
            band=0.016,
            max_half_width=0.19,
        )
        return Vector(
            (
                section_x + metrics.height * x_offset,
                section_y - section_front - metrics.height * extra,
                metrics.z(z_norm),
            )
        )

    if profile.female:
        placket = [
            front_surface_point(0.020, 0.842),
            front_surface_point(0.006, 0.802),
            front_surface_point(-0.010, 0.690),
            front_surface_point(-0.008, 0.610),
        ]
        closure_zs = (0.798,)
    else:
        placket = [
            front_surface_point(0.028, 0.842),
            front_surface_point(0.010, 0.790),
            front_surface_point(-0.010, 0.705),
            front_surface_point(-0.008, 0.525),
        ]
        closure_zs = (0.785, 0.735, 0.685)
    objects.append(
        v3.create_curve_tube(
            "V6_Asymmetric_Placket",
            placket,
            materials["bronze"],
            armature,
            "spine_03",
            profile,
            "modelled-front-placket",
            bevel_depth=metrics.height * 0.00135,
        )
    )
    for index, z_norm in enumerate(closure_zs, 1):
        span = metrics.height * (0.032 if profile.female else 0.043)
        z = metrics.z(z_norm)
        center_point = front_surface_point(0.004, z_norm, extra=0.007)
        x_center = center_point.x
        y = center_point.y
        objects.append(
            v3.create_curve_tube(
                f"V6_Frog_Closure_{index}",
                [
                    Vector((x_center - span, y, z)),
                    Vector((x_center - span * 0.35, y, z + metrics.height * 0.007)),
                    Vector((x_center, y, z)),
                    Vector((x_center + span * 0.35, y, z - metrics.height * 0.007)),
                    Vector((x_center + span, y, z)),
                ],
                materials["bronze"],
                armature,
                "spine_03",
                profile,
                "modelled-frog-closure",
                bevel_depth=metrics.height * 0.00175,
                radii=[0.72, 1.0, 1.15, 1.0, 0.72],
            )
        )

    waist_norm = 0.606 if profile.female else 0.505
    section_norm = 0.590 if profile.female else 0.515
    waist_x, waist_y, waist_width, waist_front, waist_back = v3.torso_section_at(
        body, metrics, section_norm
    )
    belt_extra = metrics.height * 0.012
    objects.append(
        v3.create_oval_band(
            "V6_Leather_Waist_Belt",
            Vector((waist_x, waist_y, metrics.z(waist_norm))),
            waist_width + belt_extra,
            waist_front + belt_extra,
            waist_back + belt_extra,
            metrics.height * (0.040 if profile.female else 0.025),
            materials["leather"],
            armature,
            "pelvis",
            profile,
            "modelled-waist-belt",
            bevel=metrics.height * 0.0015,
        )
    )
    buckle_y = waist_y - waist_front - belt_extra - metrics.height * 0.007
    buckle_x = waist_x + (metrics.height * 0.036 if profile.female else 0.0)
    objects.append(
        v3.create_beveled_box(
            "V6_Belt_Buckle",
            Vector((buckle_x, buckle_y, metrics.z(waist_norm))),
            Vector((metrics.height * 0.024, metrics.height * 0.008, metrics.height * 0.024)),
            materials["bronze"],
            armature,
            "pelvis",
            profile,
            "modelled-belt-buckle",
            bevel=metrics.height * 0.0022,
            rotation=(0.0, math.radians(45.0), 0.0),
        )
    )

    back_y = chest_y + chest_back + metrics.height * 0.011
    objects.append(
        v3.create_curve_tube(
            "V6_Back_Center_Seam",
            [
                Vector((chest_x, back_y, metrics.z(0.820))),
                Vector((chest_x, back_y, metrics.z(0.680))),
                Vector((chest_x, back_y, metrics.z(0.610 if profile.female else 0.525))),
            ],
            materials["thread"],
            armature,
            "spine_03",
            profile,
            "modelled-back-seam",
            bevel_depth=metrics.height * 0.00055,
        )
    )
    return objects


def create_boot_trim(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: v3.BodyMetrics,
    profile: Profile,
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for suffix, side in (("L", "l"), ("R", "r")):
        ankle, _toe = v3.bone_points(armature, body, f"foot_{side}")
        for index, (z_norm, material_name, height) in enumerate(
            (
                (0.108, "leather_dark", 0.015),
                (0.132, "leather", 0.013),
                (0.149, "bronze", 0.005),
            ),
            1,
        ):
            objects.append(
                v3.create_oval_band(
                    f"V6_Boot_Band_{suffix}_{index}",
                    Vector((ankle.x, ankle.y, metrics.z(z_norm))),
                    metrics.height * 0.039,
                    metrics.height * 0.035,
                    metrics.height * 0.033,
                    metrics.height * height,
                    materials[material_name],
                    armature,
                    f"calf_{side}",
                    profile,
                    "modelled-boot-trim",
                    segments=48,
                    bevel=metrics.height * 0.0007,
                )
            )
    return objects


def create_boot_soles(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: v3.BodyMetrics,
    profile: Profile,
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    """Give the fitted ankle boots a readable outsole and low heel."""

    objects: list[bpy.types.Object] = []
    for suffix, side in (("L", "l"), ("R", "r")):
        foot_head, foot_tail = v3.bone_points(armature, body, f"foot_{side}")
        direction = (foot_tail - foot_head).normalized()
        center = foot_head + direction * metrics.height * 0.045
        center.z = metrics.z(0.008)
        objects.append(
            v3.create_beveled_box(
                f"V6_Boot_Sole_{suffix}",
                center,
                Vector((metrics.height * 0.064, metrics.height * 0.142, metrics.height * 0.009)),
                materials["leather_dark"],
                armature,
                f"foot_{side}",
                profile,
                "modelled-boot-sole",
                bevel=metrics.height * 0.0045,
            )
        )
        heel_center = foot_head - direction * metrics.height * 0.020
        heel_center.z = metrics.z(0.014)
        objects.append(
            v3.create_beveled_box(
                f"V6_Boot_Heel_{suffix}",
                heel_center,
                Vector((metrics.height * 0.052, metrics.height * 0.038, metrics.height * 0.022)),
                materials["leather_dark"],
                armature,
                f"foot_{side}",
                profile,
                "modelled-boot-heel",
                bevel=metrics.height * 0.0035,
            )
        )
    return objects


def refine_skirt_panels(
    panels: list[bpy.types.Object],
    metrics: v3.BodyMetrics,
    profile: Profile,
) -> None:
    if profile.female:
        return
    top = metrics.z(0.515)
    for obj in panels:
        if obj.get("category") != "tunic-skirt-panel":
            continue
        inverse = obj.matrix_world.inverted()
        for vertex in obj.data.vertices:
            world = obj.matrix_world @ vertex.co
            if world.z < top:
                world.z = top + (world.z - top) * 0.60
            world.x = metrics.center_x + (world.x - metrics.center_x) * 0.95
            vertex.co = inverse @ world
        obj.data.update(calc_edges=True)


def add_male_hair_tufts(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: v3.BodyMetrics,
    profile: Profile,
    material: bpy.types.Material,
) -> list[bpy.types.Object]:
    if profile.female:
        return []
    scalp = [
        body.matrix_world @ vertex.co
        for vertex in body.data.vertices
        if v3.is_body_vertex(body, vertex.index)
        and v3.body_group_weight(body, vertex.index, {"scalp"}) > 0.5
    ]
    if not scalp:
        return []
    center = Vector(
        (
            (min(point.x for point in scalp) + max(point.x for point in scalp)) * 0.5,
            (min(point.y for point in scalp) + max(point.y for point in scalp)) * 0.5,
            (min(point.z for point in scalp) + max(point.z for point in scalp)) * 0.5,
        )
    )
    radius_x = (max(point.x for point in scalp) - min(point.x for point in scalp)) * 0.52
    radius_y = (max(point.y for point in scalp) - min(point.y for point in scalp)) * 0.52
    top = max(point.z for point in scalp)
    rng = random.Random(6206)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for index in range(18):
        angle = math.tau * index / 18.0 + rng.uniform(-0.10, 0.10)
        ring = 0.35 + 0.48 * (index % 3) / 2.0
        root = Vector(
            (
                center.x + math.cos(angle) * radius_x * ring,
                center.y + math.sin(angle) * radius_y * ring,
                top - metrics.height * (0.004 + 0.022 * ring),
            )
        )
        outward = Vector((math.cos(angle), math.sin(angle), 0.35)).normalized()
        lean = Vector((rng.uniform(-0.012, 0.018), rng.uniform(-0.010, 0.012), 0.0))
        length = metrics.height * rng.uniform(0.022, 0.038)
        tip = root + outward * length + lean
        controls = (
            root,
            root + outward * length * 0.34 + Vector((0, 0, metrics.height * 0.006)),
            tip - outward * length * 0.20,
            tip,
        )
        v3.append_tapered_clump(
            vertices,
            faces,
            controls,
            metrics.height * rng.uniform(0.0050, 0.0072),
            metrics.height * rng.uniform(0.0015, 0.0022),
            rings=8,
            sides=6,
            tip_fraction=0.08,
            taper_power=0.55,
        )
    tufts = v3.create_mesh_object("V6_Male_Tousled_Hair_Tufts", vertices, faces, material)
    v3.rigid_weights(tufts, armature, "head")
    v3.mark_generated(tufts, profile, "modelled-hair-tufts")
    return [tufts]


def sculpt_female_fringe(hair: bpy.types.Object, metrics: v3.BodyMetrics) -> None:
    """Open only the eye-covering front polygons without stretching the bob.

    v6.5 tried to push a wide vertex region aside.  On the low-cage MHClO bob
    that pulled the whole side shell into wing shapes.  A small, intentional
    opening keeps the authored silhouette and exposes both eyes cleanly.
    """

    mesh = hair.data
    if not mesh.polygons:
        return
    bm = bmesh.new()
    bm.from_mesh(mesh)
    delete_faces = []
    x_min = metrics.center_x - metrics.height * 0.070
    x_max = metrics.center_x + metrics.height * 0.010
    front_limit = metrics.center_y - metrics.height * 0.022
    for face in bm.faces:
        center = hair.matrix_world @ face.calc_center_median()
        zn = metrics.zn(center.z)
        if x_min <= center.x <= x_max and center.y < front_limit and 0.885 <= zn <= 0.955:
            delete_faces.append(face)
    if delete_faces:
        bmesh.ops.delete(bm, geom=delete_faces, context="FACES")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    hair["v6_fringe_opening_faces"] = len(delete_faces)
    print(f"V6_FRINGE_OPENING faces={len(delete_faces)}")


def remove_preview_only_objects() -> None:
    for obj in tuple(bpy.context.scene.objects):
        if obj.type in {"CAMERA", "LIGHT"} or obj.name.startswith("V6_Preview_"):
            bpy.data.objects.remove(obj, do_unlink=True)


def strip_rig_display_helpers(armature: bpy.types.Object) -> None:
    """Remove editor-only bone shapes before the GLB dependency walk.

    The MPFB base rig references a hidden two-metre Icosphere as a custom bone
    shape. Blender's glTF exporter follows that dependency even when the helper
    itself is not selected, so a fresh GLB import would contain an unrigged
    sphere. It is useful only inside the editor and must not ship to the game.
    """

    for pose_bone in armature.pose.bones:
        pose_bone.custom_shape = None
    for obj in tuple(bpy.context.scene.objects):
        if obj.type == "MESH" and obj.hide_render and not obj.get("character_slug"):
            bpy.data.objects.remove(obj, do_unlink=True)


def bake_reference_pose_and_limit_weights(armature: bpy.types.Object) -> int:
    """Make the approved A-pose the bind pose and cap skinning at four joints.

    The source rig can carry more than four interpolated MPFB weights. glTF
    correctly limits those to four, but doing that only during export changed
    the posed face and hands. Baking first and pruning explicitly guarantees
    that the .blend preview and re-imported GLB use identical skinning data.
    """

    bpy.ops.object.select_all(action="DESELECT")
    armature.hide_set(False)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    pruned_vertices = 0
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if not any(
            modifier.type == "ARMATURE" and modifier.object == armature
            for modifier in obj.modifiers
        ):
            continue
        for vertex in obj.data.vertices:
            memberships = sorted(
                ((item.group, item.weight) for item in vertex.groups if item.weight > 0.0),
                key=lambda item: item[1],
                reverse=True,
            )
            if len(memberships) <= 4:
                continue
            pruned_vertices += 1
            kept = memberships[:4]
            total = sum(weight for _group, weight in kept)
            for group_index, _weight in memberships:
                obj.vertex_groups[group_index].remove([vertex.index])
            for group_index, weight in kept:
                obj.vertex_groups[group_index].add(
                    [vertex.index], weight / total, "REPLACE"
                )
    print(f"V6_WEIGHT_LIMIT pruned_vertices={pruned_vertices}")
    return pruned_vertices


def build_character(
    profile: Profile,
) -> tuple[bpy.types.Object, bpy.types.Object, list[bpy.types.Object], dict[str, bpy.types.Material]]:
    bpy.ops.wm.open_mainfile(filepath=str(BASE_DIR / profile.base_file))
    body = v3.find_body()
    armature = v3.find_armature(body)

    clothing = add_mpfb_asset(body, profile.clothing_asset, "clothes", "Clothes")
    sleeves = (
        add_mpfb_asset(body, profile.sleeve_asset, "clothes", "Sleeves")
        if profile.female
        else None
    )
    shoes = add_mpfb_asset(body, "shoes02.mhclo", "clothes", "Shoes")
    hair = add_mpfb_asset(body, profile.hair_asset, "hair", "Hair")

    # Preserve the already-fitted MPFB asset geometry, then bake the body so
    # every subsequently copied garment shell uses the visible character shape.
    v3.bake_body_shape_mix(body)
    metrics = v3.measure_body(body)
    materials = create_materials(profile)
    sanitize_mpfb_character_materials(profile)
    v3.tune_skin_material(body, profile)
    assign_clothing_materials(clothing, body, armature, metrics, materials, profile)
    add_garment_clearance(clothing, metrics, profile)
    if sleeves is not None:
        isolate_and_style_sleeves(sleeves, body, armature, metrics, materials, profile)
    replace_object_materials(shoes, [materials["leather_dark"]])
    replace_object_materials(hair, [materials["hair"]])

    created: list[bpy.types.Object] = [clothing, shoes, hair]
    if sleeves is not None:
        created.append(sleeves)
    created.extend(create_sleeves_and_wraps(body, armature, metrics, profile, materials))
    created.extend(create_sleeve_transition_bands(body, armature, metrics, profile, materials))
    skirt_parts = v3.create_skirt_panels(body, armature, metrics, profile, materials)
    refine_skirt_panels(skirt_parts, metrics, profile)
    created.extend(skirt_parts)
    created.extend(create_uniform_details(body, armature, metrics, profile, materials))
    created.extend(create_boot_trim(body, armature, metrics, profile, materials))
    created.extend(create_boot_soles(body, armature, metrics, profile, materials))
    # v6.2 proved that thin radial add-on tufts read as needles in silhouette.
    # Keep the coherent authored hair volume until a broad-clump sculpt passes
    # the same four-view bar.

    remove_fully_clothed_body_surfaces(body)

    for obj in [body, armature, *created]:
        obj["character_slug"] = profile.slug
        obj["model_version"] = "v6-clean-modelled"
        obj["source_reference"] = (
            f"docs/character-concepts/initial-{profile.key}-turnaround.png"
        )
        obj["uses_reference_projection"] = False
        obj["generator_script"] = SCRIPT_PATH
    for obj in created:
        ensure_uv(obj)

    v3.apply_reference_stance(armature)
    pruned_vertices = bake_reference_pose_and_limit_weights(armature)
    strip_rig_display_helpers(armature)
    armature["v6_pruned_to_four_joint_vertices"] = pruned_vertices
    bpy.context.view_layer.update()
    return body, armature, created, materials


def validate_scene(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    created: list[bpy.types.Object],
) -> dict[str, object]:
    mesh_objects = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and not obj.hide_render
    ]
    missing_uv = [obj.name for obj in mesh_objects if obj.data.polygons and not obj.data.uv_layers]
    unrigged = []
    for obj in mesh_objects:
        modifiers = [modifier for modifier in obj.modifiers if modifier.type == "ARMATURE"]
        if not modifiers or not any(modifier.object == armature for modifier in modifiers):
            unrigged.append(obj.name)
    if missing_uv:
        raise RuntimeError("Renderable meshes without UV maps: " + ", ".join(missing_uv))
    if unrigged:
        raise RuntimeError("Renderable meshes without the game rig: " + ", ".join(unrigged))
    if len(armature.data.bones) != 53:
        raise RuntimeError(f"Expected 53 game bones, found {len(armature.data.bones)}")

    max_joint_influences = max(
        (
            len([item for item in vertex.groups if item.weight > 0.0])
            for obj in mesh_objects
            for vertex in obj.data.vertices
        ),
        default=0,
    )
    if max_joint_influences > 4:
        raise RuntimeError(
            f"Expected at most four joint influences, found {max_joint_influences}"
        )

    vertices = sum(len(obj.data.vertices) for obj in mesh_objects)
    triangles = sum(
        sum(max(0, len(polygon.vertices) - 2) for polygon in obj.data.polygons)
        for obj in mesh_objects
    )
    return {
        "meshes": len(mesh_objects),
        "vertices": vertices,
        "triangles": triangles,
        "bones": len(armature.data.bones),
        "max_joint_influences": max_joint_influences,
        "pruned_to_four_joint_vertices": armature.get(
            "v6_pruned_to_four_joint_vertices", 0
        ),
        "uv_meshes": len(mesh_objects),
        "generated_parts": len(created),
        "reference_projection": False,
    }


def save_and_export(
    profile: Profile,
    revision: str,
    armature: bpy.types.Object,
) -> tuple[Path, Path]:
    source_dir = SOURCE_ROOT / revision
    model_dir = MODEL_ROOT / revision
    source_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    blend_path = source_dir / f"{profile.slug}.blend"
    glb_path = model_dir / f"{profile.slug}.glb"
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), compress=True)

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
        export_animations=False,
        export_apply=True,
        export_materials="EXPORT",
    )
    return blend_path, glb_path


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_turnaround(
    profile: Profile,
    revision: str,
    body: bpy.types.Object,
) -> list[Path]:
    output_dir = PREVIEW_ROOT / revision
    output_dir.mkdir(parents=True, exist_ok=True)
    character_meshes = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and not obj.hide_render
    ]
    bounds = [
        obj.matrix_world @ Vector(corner)
        for obj in character_meshes
        for corner in obj.bound_box
    ]
    if not bounds:
        raise RuntimeError("Character preview has no visible mesh bounds")
    z_min = min(point.z for point in bounds)
    z_max = max(point.z for point in bounds)
    metrics = v3.BodyMetrics(
        z_min=z_min,
        z_max=z_max,
        height=z_max - z_min,
        center_x=(min(point.x for point in bounds) + max(point.x for point in bounds)) * 0.5,
        center_y=(min(point.y for point in bounds) + max(point.y for point in bounds)) * 0.5,
    )
    scene = bpy.context.scene

    world = scene.world or bpy.data.worlds.new("V6_Preview_World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.032, 0.037, 0.046, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.34

    floor_material = solid_material("V6_Preview_Floor_Material", "34383D", roughness=0.88)
    bpy.ops.mesh.primitive_plane_add(
        size=metrics.height * 5.0,
        location=(metrics.center_x, metrics.center_y, metrics.z_min - metrics.height * 0.005),
    )
    floor = bpy.context.object
    floor.name = "V6_Preview_Floor"
    floor.data.materials.append(floor_material)

    camera_data = bpy.data.cameras.new("V6_Preview_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = metrics.height * 1.09
    camera = bpy.data.objects.new("V6_Preview_Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera

    lights: list[bpy.types.Object] = []
    for name, energy, size, color in (
        ("Key", 650.0, 3.2, (1.0, 0.89, 0.80)),
        ("Fill", 330.0, 2.8, (0.74, 0.84, 1.0)),
        ("Rim", 540.0, 2.7, (0.82, 0.96, 0.92)),
    ):
        data = bpy.data.lights.new(f"V6_Preview_{name}", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = color
        light = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(light)
        lights.append(light)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.72

    target = Vector((metrics.center_x, metrics.center_y, metrics.z(0.50)))
    distance = metrics.height * 3.1
    views = {
        "front": Vector((metrics.center_x, metrics.center_y - distance, target.z)),
        "right-side": Vector((metrics.center_x - distance, metrics.center_y, target.z)),
        "back": Vector((metrics.center_x, metrics.center_y + distance, target.z)),
        "three-quarter": Vector(
            (metrics.center_x - distance * 0.68, metrics.center_y - distance * 0.78, target.z + metrics.height * 0.025)
        ),
    }
    paths: list[Path] = []
    for view_name, position in views.items():
        camera.location = position
        look_at(camera, target)
        view_direction = (position - target).normalized()
        screen_right = (-view_direction).cross(Vector((0.0, 0.0, 1.0))).normalized()
        key, fill, rim = lights
        key.location = target + view_direction * 2.2 - screen_right * 1.3 + Vector((0, 0, 1.5))
        fill.location = target + view_direction * 1.7 + screen_right * 1.2 + Vector((0, 0, 0.45))
        rim.location = target - view_direction * 2.0 + Vector((0, 0, 1.3))
        for light in lights:
            look_at(light, target)
        path = output_dir / f"{profile.slug}-{view_name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        paths.append(path)
        print(f"V6_PREVIEW {profile.key} {view_name} {path}")
    return paths


def write_metadata(
    profile: Profile,
    revision: str,
    stats: dict[str, object],
    blend_path: Path,
    glb_path: Path,
    previews: Iterable[Path],
    note: str,
) -> None:
    output_dir = PREVIEW_ROOT / revision
    payload = {
        "revision": revision,
        "status": "candidate",
        "character": profile.key,
        "pipeline": "clean modelled MPFB topology; no reference projection",
        "reference": f"docs/character-concepts/initial-{profile.key}-turnaround.png",
        "blend": str(blend_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "glb": str(glb_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "previews": [str(path.relative_to(PROJECT_ROOT)).replace("\\", "/") for path in previews],
        "materials": [
            "embedded tileable fabric",
            "embedded tileable linen",
            "embedded tileable leather",
            "embedded tileable hair",
            "PBR bronze",
        ],
        "source_assets": {
            "body": profile.base_file,
            "clothing_topology": profile.clothing_asset,
            "sleeve_topology": "continuous with clothing topology",
            "hair_topology": profile.hair_asset,
            "footwear_topology": "shoes02.mhclo",
        },
        "stats": stats,
        "note": note,
    }
    (output_dir / f"{profile.key}-metadata.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def generate(profile: Profile, revision: str, note: str, *, skip_render: bool) -> None:
    body, armature, created, _materials = build_character(profile)
    stats = validate_scene(body, armature, created)
    blend_path, glb_path = save_and_export(profile, revision, armature)
    previews = [] if skip_render else render_turnaround(profile, revision, body)
    write_metadata(profile, revision, stats, blend_path, glb_path, previews, note)
    print(
        "V6_GENERATED "
        + json.dumps(
            {
                "character": profile.key,
                "revision": revision,
                "blend": str(blend_path),
                "glb": str(glb_path),
                "previews": [str(path) for path in previews],
                "stats": stats,
            },
            ensure_ascii=False,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--character", choices=("male", "female", "all"), default="all")
    parser.add_argument("--revision", default="v6.2")
    parser.add_argument(
        "--revision-note",
        default="MPFBの正常な顔・手・53ボーンを維持し、衣服・髪・靴を実メッシュと埋込PBR素材で再構築",
    )
    parser.add_argument("--skip-render", action="store_true")
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parser.parse_args(script_args)
    selected = PROFILES if args.character == "all" else tuple(
        profile for profile in PROFILES if profile.key == args.character
    )
    for profile in selected:
        generate(profile, args.revision, args.revision_note, skip_render=args.skip_render)


if __name__ == "__main__":
    main()
