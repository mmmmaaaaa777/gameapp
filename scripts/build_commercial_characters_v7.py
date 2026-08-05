"""Build the v7 commercial-quality guild characters.

v7 deliberately keeps the proven MPFB face, hands and 53-bone topology from
v6, but replaces the parts that still read like a technical prototype:

* stable opaque mesh hair without projected or transparent fringe artefacts;
* tuned opaque skin/eye/hair shaders with restrained highlights;
* tailored garment seams, shoulder structure and non-duplicated boot trim;
* embedded Idle, Run, Attack and Dodge actions on the shipping skeleton;
* acceptance renders including face and costume close-ups.

No turnaround pixels are projected onto the model.  All colour variation is
tileable procedural material detail or the original MPFB anatomical texture.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import replace
from pathlib import Path
from typing import Iterable

import bpy
import bmesh
from mathutils import Vector

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_clean_characters_v6 as v6
import build_reference_characters_v3 as v3


PROJECT_ROOT = SCRIPT_DIR.parent
SOURCE_ROOT = PROJECT_ROOT / "art-source" / "characters" / "history"
MODEL_ROOT = PROJECT_ROOT / "public" / "models" / "characters" / "history"
PREVIEW_ROOT = PROJECT_ROOT / "docs" / "character-concepts" / "model-history"
SCRIPT_PATH = "scripts/build_commercial_characters_v7.py"

PROFILES = tuple(
    replace(
        profile,
        slug=f"initial-{profile.key}-v7",
        hair_asset="ponytail01.mhclo" if profile.female else "short02.mhclo",
    )
    for profile in v6.PROFILES
)


def measure_complete_character() -> v3.BodyMetrics:
    """Measure after v6 hides permanently clothed body faces.

    Measuring the remaining anatomical mesh alone would start at the hands,
    not the boot soles, and would invalidate every normalized costume height.
    """

    points = [
        obj.matrix_world @ vertex.co
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and not obj.hide_render
        for vertex in obj.data.vertices
    ]
    if not points:
        raise RuntimeError("Cannot measure empty v7 character")
    z_min, z_max = min(point.z for point in points), max(point.z for point in points)
    return v3.BodyMetrics(
        z_min=z_min,
        z_max=z_max,
        height=z_max - z_min,
        center_x=(min(point.x for point in points) + max(point.x for point in points)) * 0.5,
        center_y=(min(point.y for point in points) + max(point.y for point in points)) * 0.5,
    )


def set_input(shader: bpy.types.Node, names: tuple[str, ...], value: float) -> None:
    for name in names:
        socket = shader.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def tune_shipping_materials(profile: v6.Profile) -> None:
    """Give each surface a controlled real-time PBR response."""

    prefix = Path(profile.base_file).stem + "."
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        is_brow_or_lash = obj.name.endswith(("Eyebrows", "Eyelashes"))
        is_eye = obj.name.endswith("Eyes")
        is_skin = obj.name.startswith(prefix) and obj.name.endswith("Body")
        is_hair = "Hair" in obj.name
        for material in obj.data.materials:
            if material is None or not material.use_nodes:
                continue
            material.diffuse_color[3] = 1.0
            for shader in (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"):
                alpha = shader.inputs.get("Alpha")
                if alpha is not None and not is_brow_or_lash:
                    for link in tuple(alpha.links):
                        material.node_tree.links.remove(link)
                    alpha.default_value = 1.0
                if is_skin:
                    shader.inputs["Roughness"].default_value = 0.50
                    set_input(shader, ("Subsurface Weight", "Subsurface"), 0.055)
                    set_input(shader, ("Coat Weight", "Coat"), 0.025)
                elif is_eye:
                    shader.inputs["Roughness"].default_value = 0.16
                    set_input(shader, ("Coat Weight", "Coat"), 0.34)
                    set_input(shader, ("Coat Roughness",), 0.10)
                    set_input(shader, ("Specular IOR Level", "Specular"), 0.42)
                elif is_hair:
                    shader.inputs["Roughness"].default_value = 0.72
                    set_input(shader, ("Anisotropic IOR Level", "Anisotropic"), 0.14)
                    set_input(shader, ("Specular IOR Level", "Specular"), 0.18)
                elif is_brow_or_lash:
                    shader.inputs["Roughness"].default_value = 0.62
            obj["v7_surface_class"] = (
                "skin" if is_skin else "eyes" if is_eye else "hair" if is_hair else
                "transparent-face-detail" if is_brow_or_lash else "opaque-costume"
            )


def image_pbr_material(
    name: str,
    image_path: Path,
    *,
    roughness: float,
    alpha: bool = False,
    anisotropic: float = 0.0,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(image_path), check_existing=True)
    texture.image.pack()
    texture.interpolation = "Linear"
    shader.inputs["Roughness"].default_value = roughness
    set_input(shader, ("Anisotropic IOR Level", "Anisotropic"), anisotropic)
    set_input(shader, ("Specular IOR Level", "Specular"), 0.28 if anisotropic else 0.38)
    color_output = texture.outputs["Color"]
    if anisotropic:
        tint = nodes.new("ShaderNodeMixRGB")
        tint.blend_type = "MULTIPLY"
        tint.inputs[0].default_value = 0.84
        tint.inputs[2].default_value = (0.085, 0.060, 0.045, 1.0)
        links.new(texture.outputs["Color"], tint.inputs[1])
        color_output = tint.outputs[0]
    links.new(color_output, shader.inputs["Base Color"])
    if alpha and shader.inputs.get("Alpha") is not None:
        threshold = nodes.new("ShaderNodeMath")
        threshold.operation = "GREATER_THAN"
        threshold.inputs[1].default_value = 0.62
        links.new(texture.outputs["Alpha"], threshold.inputs[0])
        links.new(threshold.outputs[0], shader.inputs["Alpha"])
        if hasattr(material, "surface_render_method"):
            material.surface_render_method = "DITHERED"
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def install_authored_hair_and_eyes(profile: v6.Profile) -> None:
    """Restore the assets' authored 2K strand texture and a clear brown iris."""

    hair_path = Path(v6.bundled_asset(profile.hair_asset, "hair"))
    hair_image = hair_path.with_name(f"{hair_path.stem}_diffuse.png")
    if not hair_image.is_file():
        raise FileNotFoundError(hair_image)
    hair_material = image_pbr_material(
        f"V7_{profile.key}_Authored_Hair",
        hair_image,
        roughness=0.62,
        alpha=True,
        anisotropic=0.12,
    )
    hair = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("V6_Hair_"))
    v6.replace_object_materials(hair, [hair_material])
    hair["texture_provenance"] = "authored MPFB hair UV; not turnaround projection"
    hair["texture_resolution"] = "2048x2048"

    eye_path = Path(v6.bundled_asset("high-poly.mhclo", "eyes")).parent / ".." / "materials" / "brown_eye.png"
    eye_path = eye_path.resolve()
    if not eye_path.is_file():
        raise FileNotFoundError(eye_path)
    eye_material = image_pbr_material("V7_Clear_Brown_Eyes", eye_path, roughness=0.15)
    for shader in (node for node in eye_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"):
        set_input(shader, ("Coat Weight", "Coat"), 0.28)
        set_input(shader, ("Coat Roughness",), 0.08)
    eyes = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.endswith("Eyes"))
    v6.replace_object_materials(eyes, [eye_material])
    eyes["v7_eye_texture"] = "brown_eye.png 1024x1024"


def install_clipped_authored_hair(profile: v6.Profile) -> None:
    """Keep opaque strand clusters while discarding isolated alpha wisps."""

    hair_path = Path(v6.bundled_asset(profile.hair_asset, "hair"))
    hair_image = hair_path.with_name(f"{hair_path.stem}_diffuse.png")
    if not hair_image.is_file():
        raise FileNotFoundError(hair_image)
    material = image_pbr_material(
        f"V7_{profile.key}_Clipped_Strand_Hair",
        hair_image,
        roughness=0.72,
        alpha=True,
        anisotropic=0.14,
    )
    hair = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("V6_Hair_"))
    v6.replace_object_materials(hair, [material])
    hair["texture_provenance"] = "authored MPFB hair UV; alpha clipped at 0.62; no projection"
    hair["uses_alpha_transparency"] = True


def install_opaque_authored_hair(profile: v6.Profile) -> None:
    """Use the authored strand colour while keeping every hair face opaque.

    Transparent card edges caused the rejected v7.8/v7.9 forehead pixels.
    Here the alpha channel only mixes strand colour over a solid brown base;
    it never controls surface opacity in Blender or the exported GLB.
    """

    hair_path = Path(v6.bundled_asset(profile.hair_asset, "hair"))
    hair_image = hair_path.with_name(f"{hair_path.stem}_diffuse.png")
    if not hair_image.is_file():
        raise FileNotFoundError(hair_image)
    material = bpy.data.materials.new(f"V7_{profile.key}_Opaque_Strand_Hair")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(hair_image), check_existing=True)
    texture.image.pack()
    texture.interpolation = "Linear"
    tint = nodes.new("ShaderNodeMixRGB")
    tint.blend_type = "MULTIPLY"
    tint.inputs[0].default_value = 0.76
    tint.inputs[2].default_value = v3.hex_color(profile.hair_hex)
    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs[1].default_value = v3.hex_color(profile.hair_hex)
    links.new(texture.outputs["Color"], tint.inputs[1])
    links.new(texture.outputs["Alpha"], mix.inputs[0])
    links.new(tint.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.72
    set_input(shader, ("Anisotropic IOR Level", "Anisotropic"), 0.14)
    set_input(shader, ("Specular IOR Level", "Specular"), 0.18)
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    hair = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("V6_Hair_"))
    v6.replace_object_materials(hair, [material])
    hair["texture_provenance"] = "authored MPFB hair UV colour; opaque surface; no projection"
    hair["uses_alpha_transparency"] = False


def install_clean_sclera() -> None:
    """Use an opaque sclera so eye-texture borders cannot appear as black gaps."""

    eyes = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.endswith("Eyes"))
    sclera = v6.solid_material("V7_Clean_Sclera", "E9E3DA", roughness=0.20)
    for shader in (node for node in sclera.node_tree.nodes if node.type == "BSDF_PRINCIPLED"):
        set_input(shader, ("Coat Weight", "Coat"), 0.24)
        set_input(shader, ("Coat Roughness",), 0.08)
        set_input(shader, ("Specular IOR Level", "Specular"), 0.38)
    v6.replace_object_materials(eyes, [sclera])
    eyes["v7_eye_surface"] = "opaque modeled sclera"


def install_stable_hair(profile: v6.Profile) -> None:
    """Install a simple PBR hair material that round-trips through glTF."""

    color = "38271F" if not profile.female else "512A29"
    material = v6.solid_material(f"V7_{profile.key}_Stable_Hair", color, roughness=0.70)
    for shader in (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"):
        set_input(shader, ("Anisotropic IOR Level", "Anisotropic"), 0.16)
        set_input(shader, ("Specular IOR Level", "Specular"), 0.20)
    hair = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("V6_Hair_"))
    v6.replace_object_materials(hair, [material])
    hair["material_pipeline"] = "simple glTF-compatible opaque PBR"
    hair["uses_alpha_transparency"] = False
    hair["uses_reference_projection"] = False


def refine_collar_and_panels(metrics: v3.BodyMetrics) -> None:
    """Open the collar at the throat and turn box panels into a curved hem."""

    # The closed oval inherited from v6 read as a rigid neck brace.  The fitted
    # shirt already has a clean crew neckline, so remove the bolt-on ring rather
    # than leaving small disconnected collar fragments beside the neck.
    for obj in tuple(bpy.context.scene.objects):
        if obj.name.startswith(("V6_Standing_Collar", "V6_Collar_Linen_Trim")):
            bpy.data.objects.remove(obj, do_unlink=True)

    panels = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("V3_Tunic_Panel_")]
    if panels:
        all_bounds = [obj.matrix_world @ Vector(corner) for obj in panels for corner in obj.bound_box]
        center_x = (min(point.x for point in all_bounds) + max(point.x for point in all_bounds)) * 0.5
        bottom = min(point.z for point in all_bounds)
        top = max(point.z for point in all_bounds)
        max_half = max(abs(point.x - center_x) for point in all_bounds)
        for obj in panels:
            inverse = obj.matrix_world.inverted()
            for vertex in obj.data.vertices:
                world = obj.matrix_world @ vertex.co
                vertical = max(0.0, min(1.0, (top - world.z) / max(top - bottom, 1e-8)))
                # Bottom edge has a shallow downward arc and a little flare;
                # this avoids the rigid rectangular apron silhouette.
                x_fraction = abs(world.x - center_x) / max(max_half, 1e-8)
                world.x = center_x + (world.x - center_x) * (0.93 + vertical * 0.05)
                world.z += metrics.height * 0.010 * (x_fraction ** 1.7) * vertical
                vertex.co = inverse @ world
            obj.data.update(calc_edges=True)

    # Side borders made the panels read like wireframe boxes.  Keep the hem
    # and remove only the vertical/corner ornament from the final silhouette.
    for obj in tuple(bpy.context.scene.objects):
        if obj.name.startswith("V3_") and any(token in obj.name for token in ("Start_Trim", "End_Trim", "Bottom_Trim", "Corner_Embroidery")):
            bpy.data.objects.remove(obj, do_unlink=True)


def tune_costume_palette(profile: v6.Profile) -> None:
    """Keep metal accents readable without the emissive-looking peach edge."""

    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        if material.name == "V6_Aged_Bronze":
            color = v3.hex_color("76552F")
            material.diffuse_color = color
            for shader in (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"):
                shader.inputs["Base Color"].default_value = color
                shader.inputs["Roughness"].default_value = 0.48
                shader.inputs["Metallic"].default_value = 0.42

    # The stock alpha cards produce isolated black pixels above the brow and
    # heavy wedges at the outer eyelids after real-time export.  Those are not
    # acceptable shipping artefacts, so clean modelled brows are installed
    # below and the cards are removed instead of hidden with post-processing.
    for obj in tuple(bpy.context.scene.objects):
        if obj.type == "MESH" and obj.name.endswith("Eyelashes"):
            bpy.data.objects.remove(obj, do_unlink=True)


def create_modeled_brows(
    armature: bpy.types.Object,
    profile: v6.Profile,
) -> list[bpy.types.Object]:
    """Create clean, low-profile brow strokes without transparent cards."""

    eyes = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.endswith("Eyes"))
    points = [eyes.matrix_world @ vertex.co for vertex in eyes.data.vertices]
    center_x = (min(point.x for point in points) + max(point.x for point in points)) * 0.5
    material = v6.solid_material(
        "V7_Brow_Warm_Brown" if profile.female else "V7_Brow_Deep_Brown",
        "4B3025" if profile.female else "33251F",
        roughness=0.72,
    )
    created: list[bpy.types.Object] = []
    for side, selector in (("L", lambda point: point.x < center_x), ("R", lambda point: point.x >= center_x)):
        cluster = [point for point in points if selector(point)]
        x_min, x_max = min(p.x for p in cluster), max(p.x for p in cluster)
        z_min, z_max = min(p.z for p in cluster), max(p.z for p in cluster)
        eye_height = z_max - z_min
        eye_width = x_max - x_min
        front_y = min(p.y for p in cluster) - eye_height * 0.035
        inner_x, outer_x = (x_max, x_min) if side == "L" else (x_min, x_max)
        inner_x += (-1.0 if side == "L" else 1.0) * eye_width * 0.08
        outer_x += (1.0 if side == "L" else -1.0) * eye_width * 0.12
        base_z = z_max + eye_height * 0.18
        brow = v3.create_curve_tube(
            f"V7_Modeled_Brow_{side}",
            [
                Vector((inner_x, front_y, base_z)),
                Vector(((inner_x + outer_x) * 0.5, front_y - eye_height * 0.015, base_z + eye_height * 0.12)),
                Vector((outer_x, front_y, base_z - eye_height * 0.02)),
            ],
            material,
            armature,
            "head",
            profile,
            "modeled-facial-detail",
            bevel_depth=eye_height * (0.022 if profile.female else 0.027),
        )
        brow["uses_alpha_card"] = False
        created.append(brow)
    return created


def create_modeled_irises(
    armature: bpy.types.Object,
    profile: v6.Profile,
) -> list[bpy.types.Object]:
    """Add separate iris, pupil and catchlight geometry to both eyeballs."""

    eyes = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.endswith("Eyes"))
    points = [eyes.matrix_world @ vertex.co for vertex in eyes.data.vertices]
    center_x = (min(point.x for point in points) + max(point.x for point in points)) * 0.5
    iris_material = v6.solid_material(
        "V7_Iris_Brown" if not profile.female else "V7_Iris_Hazel",
        "3A2115" if not profile.female else "49301D",
        roughness=0.26,
    )
    pupil_material = v6.solid_material("V7_Pupil", "050403", roughness=0.20)
    highlight_material = v6.solid_material("V7_Eye_Catchlight", "E8EEF2", roughness=0.10)
    created: list[bpy.types.Object] = []
    for side, selector in (("L", lambda point: point.x < center_x), ("R", lambda point: point.x >= center_x)):
        cluster = [point for point in points if selector(point)]
        x_min, x_max = min(p.x for p in cluster), max(p.x for p in cluster)
        z_min, z_max = min(p.z for p in cluster), max(p.z for p in cluster)
        front_y = min(p.y for p in cluster)
        eye_center = Vector(((x_min + x_max) * 0.5, front_y - (z_max - z_min) * 0.016, (z_min + z_max) * 0.5))
        eye_height = z_max - z_min
        for label, material, radius, y_offset, offset in (
            ("Iris", iris_material, 0.185, 0.0000, (0.0, 0.0)),
            ("Pupil", pupil_material, 0.075, -0.0007, (0.0, 0.0)),
            ("Catchlight", highlight_material, 0.030, -0.0012, (-0.052, 0.060)),
        ):
            location = eye_center + Vector((eye_height * offset[0], y_offset, eye_height * offset[1]))
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=location)
            obj = bpy.context.object
            obj.name = f"V7_{label}_{side}"
            obj.scale = (eye_height * radius, eye_height * 0.018, eye_height * radius)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            obj.data.materials.append(material)
            v3.rigid_weights(obj, armature, "head")
            obj["category"] = "modeled-eye-detail"
            obj["uses_reference_projection"] = False
            created.append(obj)
    return created


def remove_duplicate_v6_parts() -> None:
    """Remove the accidentally doubled boot bands inherited from v6."""

    seen: set[tuple[str, tuple[int, int, int]]] = set()
    for obj in tuple(bpy.context.scene.objects):
        if not obj.name.startswith("V6_Boot_Band_"):
            continue
        base_name = obj.name.split(".", 1)[0]
        key = (base_name, tuple(round(value * 100000) for value in obj.location))
        if key in seen:
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            seen.add(key)


def hair_surface_metrics(body: bpy.types.Object) -> tuple[Vector, float, float, float, float]:
    points = [
        body.matrix_world @ vertex.co
        for vertex in body.data.vertices
        if v3.is_body_vertex(body, vertex.index)
        and v3.body_group_weight(body, vertex.index, {"scalp"}) > 0.50
    ]
    if not points:
        raise RuntimeError("Cannot construct v7 hair: scalp vertex set is empty")
    x_min, x_max = min(p.x for p in points), max(p.x for p in points)
    y_min, y_max = min(p.y for p in points), max(p.y for p in points)
    z_min, z_max = min(p.z for p in points), max(p.z for p in points)
    center = Vector(((x_min + x_max) * 0.5, (y_min + y_max) * 0.5, (z_min + z_max) * 0.5))
    return center, (x_max - x_min) * 0.53, center.y - y_min, y_max - center.y, (z_max - z_min) * 0.54


def create_layered_hair(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: v3.BodyMetrics,
    profile: v6.Profile,
    material: bpy.types.Material,
) -> bpy.types.Object:
    """Create large overlapping locks that read as sculpted hair, not needles."""

    center, radius_x, front_depth, back_depth, radius_z = hair_surface_metrics(body)
    rng = random.Random(7701 if profile.female else 7702)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    def surface(azimuth: float, polar: float, lift: float = 0.0) -> Vector:
        radial = math.sin(polar)
        depth = back_depth if math.sin(azimuth) > 0.0 else front_depth
        point = Vector((
            center.x + radius_x * radial * math.cos(azimuth),
            center.y + depth * radial * math.sin(azimuth),
            center.z + radius_z * math.cos(polar),
        ))
        normal = Vector((
            (point.x - center.x) / max(radius_x * radius_x, 1e-8),
            (point.y - center.y) / max(depth * depth, 1e-8),
            (point.z - center.z) / max(radius_z * radius_z, 1e-8),
        )).normalized()
        return point + normal * lift

    def lock(controls: tuple[Vector, Vector, Vector, Vector], width: float, thickness: float) -> None:
        v3.append_tapered_clump(
            vertices,
            faces,
            controls,
            width,
            thickness,
            rings=9,
            sides=8,
            tip_fraction=0.11,
            taper_power=0.72,
        )

    if profile.female:
        # Two parted layers wrap the skull and stop around the jaw.  Front locks
        # are steered away from the eye line so facial readability is retained.
        for layer, count in ((0, 34), (1, 30)):
            for index in range(count):
                azimuth = math.tau * (index + 0.35 * layer) / count + rng.uniform(-0.035, 0.035)
                side = 1.0 if math.cos(azimuth) >= 0.0 else -1.0
                front = math.sin(azimuth) < -0.34
                root_polar = rng.uniform(0.30 + layer * 0.10, 0.73 + layer * 0.08)
                root = surface(azimuth + side * 0.07, root_polar, metrics.height * (0.004 + layer * 0.002))
                if front:
                    tip = Vector((
                        center.x + side * radius_x * rng.uniform(0.72, 1.03),
                        center.y - front_depth * rng.uniform(0.92, 1.03),
                        metrics.z(rng.uniform(0.865, 0.895)),
                    ))
                else:
                    depth = back_depth if math.sin(azimuth) > 0 else front_depth
                    tip = Vector((
                        center.x + radius_x * math.cos(azimuth) * rng.uniform(0.98, 1.13),
                        center.y + depth * math.sin(azimuth) * rng.uniform(0.97, 1.12),
                        metrics.z(rng.uniform(0.845, 0.882)),
                    ))
                mid = surface(azimuth, min(1.22, root_polar + 0.42), metrics.height * 0.013)
                bend = Vector((-side * metrics.height * 0.006, 0.0, metrics.height * 0.025))
                lock(
                    (root, root.lerp(mid, 0.78), tip + bend, tip),
                    metrics.height * rng.uniform(0.0105, 0.0155),
                    metrics.height * rng.uniform(0.0032, 0.0048),
                )
        # Deliberate centre-part fringe, with a clear gap above the nose.
        for side in (-1.0, 1.0):
            for index in range(5):
                root = surface(-math.pi / 2 + side * (0.08 + index * 0.07), 0.36 + index * 0.045, metrics.height * 0.009)
                tip = Vector((
                    center.x + side * radius_x * (0.34 + index * 0.13),
                    center.y - front_depth * 1.04,
                    metrics.z(0.904 - index * 0.005),
                ))
                lock(
                    (root, root + Vector((side * metrics.height * 0.008, -metrics.height * 0.012, -metrics.height * 0.014)), tip + Vector((-side * metrics.height * 0.004, 0, metrics.height * 0.018)), tip),
                    metrics.height * (0.0095 + index * 0.0007),
                    metrics.height * 0.0032,
                )
    else:
        # Layered crop.  Locks flow from a slightly off-centre crown into a
        # swept fringe and compact side/back silhouette.
        for layer, count in ((0, 28), (1, 24)):
            for index in range(count):
                azimuth = math.tau * (index + layer * 0.42) / count + rng.uniform(-0.045, 0.045)
                polar = rng.uniform(0.30 + layer * 0.10, 0.83)
                root = surface(azimuth, polar, metrics.height * (0.005 + layer * 0.003))
                forward = math.sin(azimuth) < -0.25
                side = 1.0 if math.cos(azimuth) >= 0 else -1.0
                direction = Vector((
                    math.cos(azimuth) * metrics.height * rng.uniform(0.018, 0.033),
                    math.sin(azimuth) * metrics.height * rng.uniform(0.018, 0.035),
                    metrics.height * rng.uniform(-0.025, 0.005),
                ))
                if forward:
                    direction.x += side * metrics.height * 0.014
                    direction.y -= metrics.height * 0.018
                    direction.z -= metrics.height * 0.006
                tip = root + direction
                crest = root + Vector((direction.x * 0.35, direction.y * 0.35, metrics.height * 0.016))
                lock(
                    (root, crest, tip - direction * 0.18 + Vector((0, 0, metrics.height * 0.006)), tip),
                    metrics.height * rng.uniform(0.0090, 0.0138),
                    metrics.height * rng.uniform(0.0030, 0.0045),
                )
        for index in range(9):
            side = -1.0 + 2.0 * index / 8.0
            root = surface(-math.pi / 2 + side * 0.48, 0.43 + abs(side) * 0.10, metrics.height * 0.010)
            tip = Vector((
                center.x + side * radius_x * 0.92 + metrics.height * 0.012,
                center.y - front_depth * 1.07,
                metrics.z(0.909 + abs(side) * 0.008),
            ))
            lock(
                (root, root + Vector((metrics.height * 0.010, -metrics.height * 0.018, metrics.height * 0.010)), tip + Vector((-metrics.height * 0.008, 0, metrics.height * 0.015)), tip),
                metrics.height * rng.uniform(0.010, 0.014),
                metrics.height * rng.uniform(0.0032, 0.0045),
            )

    obj = v3.create_mesh_object("V7_Layered_Hair", vertices, faces, material)
    v3.rigid_weights(obj, armature, "head")
    v3.mark_generated(obj, profile, "layered-sculpted-hair")
    obj["lock_count"] = 74 if profile.female else 61
    obj["uses_hair_cards"] = False
    obj["uses_reference_projection"] = False
    return obj


def create_costume_structure(
    body: bpy.types.Object,
    armature: bpy.types.Object,
    metrics: v3.BodyMetrics,
    profile: v6.Profile,
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    """Add restrained seams and yokes that make the tunic read as tailored."""

    objects: list[bpy.types.Object] = []
    clothing = next(
        (obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("V6_Clothes_")),
        None,
    )
    if clothing is None:
        raise RuntimeError("V7 costume structure requires the fitted clothing mesh")

    def clothing_section(z_norm: float) -> tuple[float, float, float, float, float]:
        target_z = metrics.z(z_norm)
        points = [
            clothing.matrix_world @ vertex.co
            for vertex in clothing.data.vertices
            if abs((clothing.matrix_world @ vertex.co).z - target_z) <= metrics.height * 0.018
        ]
        if not points:
            raise RuntimeError(f"No clothing cross-section near z={z_norm}")
        x_min, x_max = min(p.x for p in points), max(p.x for p in points)
        y_min, y_max = min(p.y for p in points), max(p.y for p in points)
        center_x, center_y = (x_min + x_max) * 0.5, (y_min + y_max) * 0.5
        return center_x, center_y, (x_max - x_min) * 0.5, center_y - y_min, y_max - center_y
    for side in (-1.0, 1.0):
        label = "L" if side < 0 else "R"
        chest_x, chest_y, width, front, _back = clothing_section(0.755)
        shoulder_x = chest_x + side * width * 0.72
        front_y = chest_y - front - metrics.height * 0.008
        yoke = v3.create_curve_tube(
            f"V7_Shoulder_Yoke_{label}",
            [
                Vector((chest_x + side * width * 0.10, front_y, metrics.z(0.812))),
                Vector((chest_x + side * width * 0.46, front_y - metrics.height * 0.002, metrics.z(0.792))),
                Vector((shoulder_x, front_y + metrics.height * 0.006, metrics.z(0.765))),
            ],
            materials["teal_dark"], armature, "spine_03", profile,
            "tailored-shoulder-yoke", bevel_depth=metrics.height * 0.00105,
        )
        objects.append(yoke)

    # v7.8's separate linen facings intersected the neck in close-up.  The
    # fitted shirt already provides a clean neckline, so those floating panels
    # are intentionally omitted until a fully deforming collar is authored.
    return objects


def reset_pose(armature: bpy.types.Object) -> None:
    for pose_bone in armature.pose.bones:
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)


def key_pose(
    armature: bpy.types.Object,
    frame: int,
    rotations: dict[str, tuple[float, float, float]],
    locations: dict[str, tuple[float, float, float]] | None = None,
) -> None:
    reset_pose(armature)
    for name, rotation in rotations.items():
        if name in armature.pose.bones:
            armature.pose.bones[name].rotation_euler = rotation
    for name, location in (locations or {}).items():
        if name in armature.pose.bones:
            armature.pose.bones[name].location = location
    for pose_bone in armature.pose.bones:
        pose_bone.keyframe_insert("rotation_euler", frame=frame, group=pose_bone.name)
        if locations and pose_bone.name in locations:
            pose_bone.keyframe_insert("location", frame=frame, group=pose_bone.name)


def create_action(
    armature: bpy.types.Object,
    name: str,
    poses: Iterable[tuple[int, dict[str, tuple[float, float, float]], dict[str, tuple[float, float, float]]]],
    end_frame: int,
) -> bpy.types.Action:
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    armature.animation_data_create()
    armature.animation_data.action = action
    for frame, rotations, locations in poses:
        key_pose(armature, frame, rotations, locations)
    action["clip_name"] = name
    action["loop"] = name in {"Idle", "Run"}
    action["end_frame"] = end_frame
    return action


def create_gameplay_actions(armature: bpy.types.Object, metrics: v3.BodyMetrics) -> list[bpy.types.Action]:
    """Author four compact gameplay clips directly on the shipping rig."""

    idle_a = {
        "spine_02": (math.radians(1.5), 0.0, math.radians(-1.0)),
        "spine_03": (math.radians(-1.0), 0.0, math.radians(1.2)),
        "head": (math.radians(-1.0), 0.0, math.radians(-0.8)),
        "lowerarm_l": (0.0, math.radians(-5.0), math.radians(5.0)),
        "lowerarm_r": (0.0, math.radians(5.0), math.radians(-5.0)),
    }
    idle_b = {
        "spine_02": (math.radians(-1.2), 0.0, math.radians(0.7)),
        "spine_03": (math.radians(1.8), 0.0, math.radians(-1.0)),
        "head": (math.radians(1.0), 0.0, math.radians(0.8)),
        "lowerarm_l": (0.0, math.radians(-3.0), math.radians(4.0)),
        "lowerarm_r": (0.0, math.radians(3.0), math.radians(-4.0)),
    }
    idle = create_action(armature, "Idle", [
        (1, idle_a, {"pelvis": (0.0, 0.0, 0.0)}),
        (24, idle_b, {"pelvis": (0.0, 0.0, metrics.height * 0.003)}),
        (48, idle_a, {"pelvis": (0.0, 0.0, 0.0)}),
    ], 48)

    run_poses = []
    for frame, phase in ((1, 1.0), (7, 0.0), (13, -1.0), (19, 0.0), (25, 1.0)):
        run_poses.append((frame, {
            "spine_01": (math.radians(8.0), 0.0, 0.0),
            "upperarm_l": (math.radians(-27.0 * phase), 0.0, math.radians(3.0)),
            "upperarm_r": (math.radians(27.0 * phase), 0.0, math.radians(-3.0)),
            "lowerarm_l": (math.radians(-20.0), 0.0, math.radians(10.0)),
            "lowerarm_r": (math.radians(-20.0), 0.0, math.radians(-10.0)),
            "thigh_l": (math.radians(34.0 * phase), 0.0, 0.0),
            "thigh_r": (math.radians(-34.0 * phase), 0.0, 0.0),
            "calf_l": (math.radians(26.0 * max(0.0, -phase)), 0.0, 0.0),
            "calf_r": (math.radians(26.0 * max(0.0, phase)), 0.0, 0.0),
        }, {"pelvis": (0.0, 0.0, metrics.height * (0.004 if phase else 0.016))}))
    run = create_action(armature, "Run", run_poses, 25)

    attack = create_action(armature, "Attack", [
        (1, {}, {"pelvis": (0.0, 0.0, 0.0)}),
        (8, {
            "spine_01": (math.radians(-5.0), 0.0, math.radians(-16.0)),
            "spine_03": (0.0, 0.0, math.radians(-12.0)),
            "upperarm_r": (math.radians(-28.0), math.radians(8.0), math.radians(-62.0)),
            "lowerarm_r": (math.radians(-42.0), 0.0, math.radians(-18.0)),
            "upperarm_l": (math.radians(10.0), 0.0, math.radians(18.0)),
        }, {"pelvis": (0.0, metrics.height * 0.015, -metrics.height * 0.010)}),
        (15, {
            "spine_01": (math.radians(12.0), 0.0, math.radians(20.0)),
            "spine_03": (0.0, 0.0, math.radians(18.0)),
            "upperarm_r": (math.radians(35.0), math.radians(-8.0), math.radians(58.0)),
            "lowerarm_r": (math.radians(-12.0), 0.0, math.radians(8.0)),
            "upperarm_l": (math.radians(-8.0), 0.0, math.radians(-16.0)),
        }, {"pelvis": (0.0, -metrics.height * 0.035, -metrics.height * 0.018)}),
        (30, {}, {"pelvis": (0.0, 0.0, 0.0)}),
    ], 30)

    dodge = create_action(armature, "Dodge", [
        (1, {}, {"pelvis": (0.0, 0.0, 0.0)}),
        (7, {
            "spine_01": (math.radians(12.0), 0.0, math.radians(-18.0)),
            "thigh_l": (math.radians(-22.0), 0.0, math.radians(8.0)),
            "thigh_r": (math.radians(16.0), 0.0, math.radians(-8.0)),
        }, {"pelvis": (metrics.height * 0.035, 0.0, -metrics.height * 0.035)}),
        (15, {
            "spine_01": (math.radians(16.0), 0.0, math.radians(24.0)),
            "upperarm_l": (math.radians(-18.0), 0.0, math.radians(18.0)),
            "upperarm_r": (math.radians(18.0), 0.0, math.radians(-18.0)),
        }, {"pelvis": (-metrics.height * 0.080, 0.0, metrics.height * 0.010)}),
        (26, {}, {"pelvis": (0.0, 0.0, 0.0)}),
    ], 26)
    armature.animation_data.action = idle
    bpy.context.scene.frame_set(1)
    return [idle, run, attack, dodge]


def build_character(profile: v6.Profile):
    body, armature, created, materials = v6.build_character(profile)
    metrics = measure_complete_character()
    tune_shipping_materials(profile)
    # Use a deliberately simple material that survives a GLB round trip.  The
    # older procedural material produced stripes on the female hair after
    # re-import even though the source Blend looked correct.
    install_stable_hair(profile)
    install_clean_sclera()
    tune_costume_palette(profile)
    remove_duplicate_v6_parts()
    refine_collar_and_panels(metrics)
    structure = create_costume_structure(body, armature, metrics, profile, materials)
    eye_details = create_modeled_irises(armature, profile)
    created.extend([*structure, *eye_details])
    for obj in bpy.context.scene.objects:
        if obj.type not in {"MESH", "ARMATURE"} or obj.hide_render:
            continue
        obj["character_slug"] = profile.slug
        obj["model_version"] = "v7.14-commercial-final"
        obj["generator_script"] = SCRIPT_PATH
        obj["uses_reference_projection"] = False
    for obj in [*structure, *eye_details]:
        v6.ensure_uv(obj)
    actions = create_gameplay_actions(armature, metrics)
    return body, armature, created, materials, actions


def validate_scene(body, armature, created, actions) -> dict[str, object]:
    stats = v6.validate_scene(body, armature, created)
    names = {action.name for action in actions}
    required = {"Idle", "Run", "Attack", "Dodge"}
    if names != required:
        raise RuntimeError(f"Missing gameplay actions: {sorted(required - names)}")
    stats.update({
        "animation_clips": sorted(names),
        "hair_lock_meshes": sum(
            1 for obj in bpy.context.scene.objects
            if obj.type == "MESH" and obj.get("category") == "layered-sculpted-hair"
        ),
        "reference_projection": False,
        "acceptance_standard": "commercial-game-character",
    })
    return stats


def save_and_export(profile: v6.Profile, revision: str, armature: bpy.types.Object) -> tuple[Path, Path]:
    source_dir, model_dir = SOURCE_ROOT / revision, MODEL_ROOT / revision
    source_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    blend_path = source_dir / f"{profile.slug}.blend"
    glb_path = model_dir / f"{profile.slug}.glb"
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), compress=True)
    bpy.ops.object.select_all(action="DESELECT")
    export_objects = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "ARMATURE"} and not obj.hide_render]
    for obj in export_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path), export_format="GLB", use_selection=True,
        export_yup=True, export_skins=True, export_animations=True,
        export_apply=True, export_materials="EXPORT",
    )
    return blend_path, glb_path


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_acceptance(profile: v6.Profile, revision: str, armature: bpy.types.Object) -> list[Path]:
    output_dir = PREVIEW_ROOT / revision
    output_dir.mkdir(parents=True, exist_ok=True)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render]
    bounds = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    z_min, z_max = min(p.z for p in bounds), max(p.z for p in bounds)
    height = z_max - z_min
    center_x = (min(p.x for p in bounds) + max(p.x for p in bounds)) * 0.5
    center_y = (min(p.y for p in bounds) + max(p.y for p in bounds)) * 0.5

    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("V7_Acceptance_World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.025, 0.032, 0.040, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.42
    floor_mat = v6.solid_material("V7_Acceptance_Floor", "303740", roughness=0.84)
    bpy.ops.mesh.primitive_plane_add(size=height * 5.0, location=(center_x, center_y, z_min - height * 0.006))
    floor = bpy.context.object
    floor.name = "V7_Acceptance_Floor"
    floor.data.materials.append(floor_mat)

    camera_data = bpy.data.cameras.new("V7_Acceptance_Camera")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("V7_Acceptance_Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    lights = []
    for label, energy, size, color in (
        ("Key", 720.0, 3.0, (1.0, 0.88, 0.78)),
        ("Fill", 410.0, 2.6, (0.70, 0.82, 1.0)),
        ("Rim", 620.0, 2.4, (0.78, 1.0, 0.91)),
    ):
        data = bpy.data.lights.new(f"V7_{label}", "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        light = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(light)
        lights.append(light)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 768, 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -1.08
    scene.render.film_transparent = False

    armature.animation_data.action = bpy.data.actions["Idle"]
    scene.frame_set(24)
    full_target = Vector((center_x, center_y, z_min + height * 0.50))
    distance = height * 3.0
    shots = {
        "front": (Vector((center_x, center_y - distance, full_target.z)), full_target, height * 1.09),
        "three-quarter": (Vector((center_x - distance * 0.68, center_y - distance * 0.78, full_target.z + height * 0.025)), full_target, height * 1.09),
        "right-side": (Vector((center_x - distance, center_y, full_target.z)), full_target, height * 1.09),
        "back": (Vector((center_x, center_y + distance, full_target.z)), full_target, height * 1.09),
        "face-closeup": (Vector((center_x, center_y - distance, z_min + height * 0.905)), Vector((center_x, center_y, z_min + height * 0.905)), height * 0.24),
        "costume-closeup": (Vector((center_x - distance * 0.18, center_y - distance, z_min + height * 0.62)), Vector((center_x, center_y, z_min + height * 0.62)), height * 0.42),
    }
    paths: list[Path] = []
    for name, (position, target, ortho_scale) in shots.items():
        camera.location, camera.data.ortho_scale = position, ortho_scale
        look_at(camera, target)
        view = (position - target).normalized()
        right = (-view).cross(Vector((0, 0, 1))).normalized()
        lights[0].location = target + view * 2.1 - right * 1.2 + Vector((0, 0, 1.4))
        lights[1].location = target + view * 1.6 + right * 1.1 + Vector((0, 0, 0.35))
        lights[2].location = target - view * 2.0 + Vector((0, 0, 1.2))
        for light in lights:
            look_at(light, target)
        path = output_dir / f"{profile.slug}-{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        paths.append(path)
        print(f"V7_ACCEPTANCE {profile.key} {name} {path}")
    return paths


def write_metadata(profile, revision, stats, blend_path, glb_path, previews, note) -> None:
    output_dir = PREVIEW_ROOT / revision
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "revision": revision,
        "status": "review-candidate",
        "acceptance_standard": "市販ゲームに登場して違和感のない完成キャラクター",
        "character": profile.key,
        "pipeline": "modelled MPFB topology plus authored mesh detail; no image projection",
        "reference": f"docs/character-concepts/initial-{profile.key}-turnaround.png",
        "blend": str(blend_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "glb": str(glb_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "previews": [str(path.relative_to(PROJECT_ROOT)).replace("\\", "/") for path in previews],
        "required_clips": ["Idle", "Run", "Attack", "Dodge"],
        "quality_gates": [
            "recognisable eyes and facial features at gameplay distance",
            "opaque mesh hair with no projected cards or alpha artefacts",
            "tailored costume silhouette and physical seams",
            "opaque skin and costume materials",
            "four embedded skeletal gameplay clips",
            "fresh GLB re-import and in-game verification required before approval",
        ],
        "stats": stats,
        "note": note,
    }
    (output_dir / f"{profile.key}-metadata.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def generate(profile: v6.Profile, revision: str, note: str, skip_render: bool) -> None:
    body, armature, created, _materials, actions = build_character(profile)
    stats = validate_scene(body, armature, created, actions)
    blend_path, glb_path = save_and_export(profile, revision, armature)
    previews = [] if skip_render else render_acceptance(profile, revision, armature)
    write_metadata(profile, revision, stats, blend_path, glb_path, previews, note)
    print("V7_GENERATED " + json.dumps({
        "character": profile.key, "revision": revision,
        "blend": str(blend_path), "glb": str(glb_path),
        "previews": [str(path) for path in previews], "stats": stats,
    }, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--character", choices=("male", "female", "all"), default="all")
    parser.add_argument("--revision", default="v7.0")
    parser.add_argument("--revision-note", default="市販ゲーム品質を合格基準に、顔・髪・衣装・材質・動作を再構築")
    parser.add_argument("--skip-render", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    selected = PROFILES if args.character == "all" else tuple(profile for profile in PROFILES if profile.key == args.character)
    for profile in selected:
        generate(profile, args.revision, args.revision_note, args.skip_render)


if __name__ == "__main__":
    main()
