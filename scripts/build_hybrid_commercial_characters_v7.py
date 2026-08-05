"""Build v7.2 hybrid characters from sculpted costume geometry and MPFB skin.

The Hunyuan result is used strictly as untextured sculpted geometry for the
costume/body silhouette.  Its rough head and hands are removed.  The visible
head, eyes, brows, lashes and hands come from the clean MPFB topology, while a
53-bone game rig and authored gameplay clips drive every surface.

No turnaround image, generated texture, vertex colour, or camera projection is
present in the shipping model.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_clean_characters_v6 as v6
import build_clean_game_characters_v5 as v5
import build_commercial_characters_v7 as v7
import build_reference_characters_v3 as v3
import build_reference_projected_characters_v4 as v4


PROJECT_ROOT = SCRIPT_DIR.parent
CANDIDATE_DIR = PROJECT_ROOT / "art-source" / "characters" / "work" / "v3" / "hunyuan-candidates"
PREVIEW_ROOT = PROJECT_ROOT / "docs" / "character-concepts" / "model-history"

CANDIDATES = {
    "male": "male-seed-34567.glb",
    "female": "female-seed-23456.glb",
}


def candidate_profile(profile: v6.Profile) -> v4.CharacterProfile:
    empty = v4.ProjectionBox(0, 0, 1, 1)
    return v4.CharacterProfile(
        key=profile.key,
        slug=profile.slug,
        base_file=profile.base_file,
        candidate_file=CANDIDATES[profile.key],
        front_box=empty,
        right_box=empty,
        back_box=empty,
    )


def semantic_profile(profile: v6.Profile) -> v5.Profile:
    return v5.Profile(
        profile.key,
        profile.slug,
        profile.base_file,
        CANDIDATES[profile.key],
        profile.female,
    )


def remove_rough_skin(candidate: bpy.types.Object) -> dict[str, int]:
    """Remove the generated head/hair and fused hands at clean joint seams."""

    coords = np.asarray([vertex.co[:] for vertex in candidate.data.vertices], dtype=np.float32)
    z_min = float(np.min(coords[:, 2]))
    height = float(np.max(coords[:, 2]) - z_min)
    head = v5.group_strength(candidate, ("head", "neck_01"))
    hands = v5.group_strength(
        candidate,
        ("hand_", "thumb_", "index_", "middle_", "ring_", "pinky_"),
    )
    delete = np.zeros(len(candidate.data.polygons), dtype=bool)
    head_faces = hand_faces = 0
    for polygon in candidate.data.polygons:
        indices = np.fromiter(polygon.vertices, dtype=np.int32)
        center_z = float(np.mean(coords[indices, 2]))
        is_head = center_z >= z_min + height * 0.835 or float(np.mean(head[indices])) >= 0.42
        is_hand = float(np.mean(hands[indices])) >= 0.26
        if is_head or is_hand:
            delete[polygon.index] = True
            head_faces += int(is_head)
            hand_faces += int(is_hand and not is_head)
    v5.delete_selected_polygons(candidate, delete)
    candidate["removed_generated_head_faces"] = head_faces
    candidate["removed_generated_hand_faces"] = hand_faces
    return {"head": head_faces, "hands": hand_faces}


def decimate_costume(candidate: bpy.types.Object, target_triangles: int = 105_000) -> int:
    current = sum(max(0, len(polygon.vertices) - 2) for polygon in candidate.data.polygons)
    if current <= target_triangles:
        return current
    modifier = candidate.modifiers.new("V7_Game_Triangle_Budget", "DECIMATE")
    modifier.decimate_type = "COLLAPSE"
    modifier.ratio = target_triangles / current
    modifier.use_collapse_triangulate = True
    bpy.ops.object.select_all(action="DESELECT")
    candidate.hide_set(False)
    candidate.select_set(True)
    bpy.context.view_layer.objects.active = candidate
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    result = sum(max(0, len(polygon.vertices) - 2) for polygon in candidate.data.polygons)
    candidate["v7_decimated_from_triangles"] = current
    candidate["v7_target_triangles"] = target_triangles
    return result


def cleanup_scene(keep: set[bpy.types.Object], armature: bpy.types.Object) -> None:
    for pose_bone in armature.pose.bones:
        pose_bone.custom_shape = None
    for obj in tuple(bpy.context.scene.objects):
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)


def build(profile: v6.Profile):
    base = PROJECT_ROOT / "art-source" / "characters" / "work" / "v3" / profile.base_file
    candidate_file = CANDIDATE_DIR / CANDIDATES[profile.key]
    if not base.is_file() or not candidate_file.is_file():
        raise FileNotFoundError(base if not base.is_file() else candidate_file)

    bpy.ops.wm.open_mainfile(filepath=str(base))
    body = v4.find_body()
    armature = v4.find_armature()
    prefix = Path(profile.base_file).stem + "."
    face_parts = [
        obj for obj in bpy.context.scene.objects
        if obj.type == "MESH" and obj.name.startswith(prefix) and obj != body
    ]

    # Fit the UV-authored hairstyle before baking the body morphs.
    hair = v6.add_mpfb_asset(body, profile.hair_asset, "hair", "Hair")
    v3.bake_body_shape_mix(body)

    candidate = v4.import_candidate(candidate_profile(profile))
    candidate.name = f"{profile.slug}.SculptedCostume"
    candidate.data.name = f"{profile.slug}.SculptedCostumeMesh"
    v4.align_candidate(candidate, body)
    v4.transfer_game_rig(candidate, body, armature)

    material_profile = semantic_profile(profile)
    materials = v5.make_materials(material_profile)
    material_counts = v5.classify_materials(candidate, armature, material_profile, materials)
    removed = remove_rough_skin(candidate)
    v5.add_game_uv(candidate)
    triangles = decimate_costume(candidate)

    # Keep only clean anatomical surfaces that are exposed by the costume.
    v6.sanitize_mpfb_character_materials(profile)
    v3.tune_skin_material(body, profile)
    v6.remove_fully_clothed_body_surfaces(body)
    cleanup_scene({candidate, body, armature, hair, *face_parts}, armature)
    v7.tune_shipping_materials(profile)
    v7.install_authored_hair_and_eyes(profile)

    # Hair for the hybrid is intentionally a coherent UV-authored shell, not
    # the rejected v7.0 clump object.
    for obj in (candidate, body, armature, hair, *face_parts):
        obj["character_slug"] = profile.slug
        obj["model_version"] = "v7.2-hybrid-commercial-candidate"
        obj["uses_reference_projection"] = False
        obj["generator_script"] = "scripts/build_hybrid_commercial_characters_v7.py"
    candidate["geometry_source"] = CANDIDATES[profile.key]
    candidate["surface_authoring"] = "solid semantic PBR materials; no generated texture"
    hair["surface_authoring"] = "MPFB 2K UV hair material"

    v3.apply_reference_stance(armature)
    pruned = v6.bake_reference_pose_and_limit_weights(armature)
    v6.strip_rig_display_helpers(armature)
    armature["v6_pruned_to_four_joint_vertices"] = pruned
    metrics = v7.measure_complete_character()
    actions = v7.create_gameplay_actions(armature, metrics)
    bpy.context.view_layer.update()
    return body, armature, candidate, hair, face_parts, actions, {
        "triangles": triangles,
        "semantic_material_face_counts_before_decimate": material_counts,
        "removed_generated_faces": removed,
    }


def validate(body, armature, candidate, hair, face_parts, actions, build_stats) -> dict[str, object]:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render]
    if len(armature.data.bones) != 53:
        raise RuntimeError(f"Expected 53 bones, found {len(armature.data.bones)}")
    if not candidate.data.uv_layers:
        raise RuntimeError("Sculpted costume has no game UV")
    if candidate.data.color_attributes:
        raise RuntimeError("Hybrid candidate must not ship vertex colours")
    max_influences = max(
        (len([item for item in vertex.groups if item.weight > 0.0]) for obj in meshes for vertex in obj.data.vertices),
        default=0,
    )
    if max_influences > 4:
        raise RuntimeError(f"More than four joint influences: {max_influences}")
    names = sorted(action.name for action in actions)
    if names != ["Attack", "Dodge", "Idle", "Run"]:
        raise RuntimeError(f"Unexpected gameplay actions: {names}")
    return {
        "meshes": len(meshes),
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "triangles": sum(sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons) for obj in meshes),
        "bones": 53,
        "max_joint_influences": max_influences,
        "animation_clips": names,
        "reference_projection": False,
        "vertex_colors": False,
        "authored_face_parts": [obj.name for obj in face_parts],
        "hair": hair.name,
        **build_stats,
    }


def write_record(profile, revision, stats, blend_path, glb_path, previews, note) -> None:
    output = PREVIEW_ROOT / revision
    output.mkdir(parents=True, exist_ok=True)
    record = {
        "revision": revision,
        "status": "review-candidate",
        "acceptance_standard": "市販ゲームに登場して違和感のない完成キャラクター",
        "character": profile.key,
        "pipeline": "sculpted costume geometry + MPFB anatomical surfaces + 53-bone rig",
        "image_projection": False,
        "generated_texture": False,
        "blend": str(blend_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "glb": str(glb_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "previews": [str(path.relative_to(PROJECT_ROOT)).replace("\\", "/") for path in previews],
        "stats": stats,
        "note": note,
    }
    (output / f"{profile.key}-metadata.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def generate(profile, revision, note, skip_render):
    body, armature, candidate, hair, face_parts, actions, build_stats = build(profile)
    stats = validate(body, armature, candidate, hair, face_parts, actions, build_stats)
    blend_path, glb_path = v7.save_and_export(profile, revision, armature)
    previews = [] if skip_render else v7.render_acceptance(profile, revision, armature)
    write_record(profile, revision, stats, blend_path, glb_path, previews, note)
    print("V7_HYBRID_GENERATED " + json.dumps({
        "character": profile.key,
        "revision": revision,
        "stats": stats,
        "previews": [str(path) for path in previews],
    }, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--character", choices=("male", "female", "all"), default="all")
    parser.add_argument("--revision", default="v7.2")
    parser.add_argument("--revision-note", default="高密度衣装スカルプと正常なMPFB頭部・目・手を統合")
    parser.add_argument("--skip-render", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    selected = v7.PROFILES if args.character == "all" else tuple(profile for profile in v7.PROFILES if profile.key == args.character)
    for profile in selected:
        generate(profile, args.revision, args.revision_note, args.skip_render)


if __name__ == "__main__":
    main()
