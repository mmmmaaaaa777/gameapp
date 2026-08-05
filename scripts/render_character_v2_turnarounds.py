"""Render consistent turnaround sheets for the detailed v2 characters.

Run from the project root in PowerShell:

  & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" `
    --background --factory-startup `
    --python scripts\\render_character_v2_turnarounds.py

The script imports the two generated v2 GLBs, places both characters on the same
ground line, and uses one shared orthographic scale for the three reference
views.  It does not download assets or create substitute character models when
an input GLB is missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "public" / "models" / "characters"
OUTPUT_DIR = (
    PROJECT_ROOT
    / "docs"
    / "character-concepts"
    / "model-previews"
    / "v2"
)
CHARACTER_SLUGS = ("initial-male-v2", "initial-female-v2")

IMAGE_SIZE = 1024
TURNAROUND_MARGIN = 1.20
GROUND_SIZE = 1000.0


@dataclass(frozen=True)
class Bounds:
    minimum: Vector
    maximum: Vector

    @property
    def center(self) -> Vector:
        return (self.minimum + self.maximum) * 0.5

    @property
    def dimensions(self) -> Vector:
        return self.maximum - self.minimum


@dataclass(frozen=True)
class ImportedCharacter:
    slug: str
    source_path: Path
    objects: tuple[bpy.types.Object, ...]
    geometry: tuple[bpy.types.Object, ...]
    bounds: Bounds


@dataclass(frozen=True)
class TurnaroundView:
    suffix: str
    # Direction from the subject toward the camera in Blender coordinates.
    camera_side: Vector


# The source rigs face Blender -Y.  Their named right side is Blender -X.
TURNAROUND_VIEWS = (
    TurnaroundView("front", Vector((0.0, -1.0, 0.0))),
    TurnaroundView("right-side", Vector((-1.0, 0.0, 0.0))),
    TurnaroundView("back", Vector((0.0, 1.0, 0.0))),
)


def validate_inputs() -> tuple[Path, ...]:
    paths = tuple(MODEL_DIR / f"{slug}.glb" for slug in CHARACTER_SLUGS)
    missing = [path for path in paths if not path.is_file()]
    if missing:
        missing_lines = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(
            "Cannot render the v2 turnarounds because these generated GLBs "
            f"are missing:\n{missing_lines}\n"
            "Run scripts/generate_realistic_characters.py first. No placeholder "
            "models were created."
        )
    return paths


def reset_scene() -> None:
    """Remove startup-scene objects without changing Blender preferences."""

    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Keep the scene deterministic when the script is launched without
    # --factory-startup.  Imported datablocks are removed after their objects.
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.armatures,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.materials,
    ):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def world_bounds(objects: Iterable[bpy.types.Object]) -> Bounds:
    """Return evaluated world-space bounds for renderable imported geometry."""

    depsgraph = bpy.context.evaluated_depsgraph_get()
    points: list[Vector] = []
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        points.extend(
            evaluated.matrix_world @ Vector(corner)
            for corner in evaluated.bound_box
        )

    if not points:
        raise ValueError("The imported GLB does not contain renderable geometry.")

    return Bounds(
        minimum=Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
        maximum=Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
    )


def is_rig_geometry(
    obj: bpy.types.Object,
    imported_armatures: set[bpy.types.Object],
) -> bool:
    """Identify geometry that belongs to an imported character rig.

    Some GLBs contain auxiliary root meshes used as editor helpers.  They must
    not enlarge the camera bounds or appear in the reference render.
    """

    if any(
        modifier.type == "ARMATURE" and modifier.object in imported_armatures
        for modifier in obj.modifiers
    ):
        return True

    parent = obj.parent
    while parent is not None:
        if parent in imported_armatures:
            return True
        parent = parent.parent
    return False


def import_character(slug: str, source_path: Path) -> ImportedCharacter:
    before_names = set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=str(source_path))
    imported = tuple(
        obj for obj in bpy.data.objects if obj.name not in before_names
    )
    if not imported:
        raise RuntimeError(f"Blender imported no objects from {source_path}")

    # Reference renders should use the authored bind/rest pose, not whichever
    # animation happens to be selected by the glTF importer.
    for obj in imported:
        if obj.type == "ARMATURE":
            obj.data.pose_position = "REST"
            if obj.animation_data is not None:
                obj.animation_data.action = None
        elif obj.type in {"CAMERA", "LIGHT"}:
            # Model files should not contain these, but they must never affect
            # this controlled studio render if one is added later.
            obj.hide_render = True

    geometry_candidates = tuple(
        obj
        for obj in imported
        if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}
    )
    imported_armatures = {obj for obj in imported if obj.type == "ARMATURE"}
    rig_geometry = tuple(
        obj
        for obj in geometry_candidates
        if is_rig_geometry(obj, imported_armatures)
    )
    # The expected v2 models are rigged.  Keeping this fallback makes the
    # renderer useful if a future export intentionally bakes the rig away.
    geometry = rig_geometry or geometry_candidates
    for auxiliary in (obj for obj in geometry_candidates if obj not in geometry):
        auxiliary.hide_render = True

    bpy.context.view_layer.update()
    bounds = world_bounds(geometry)

    return ImportedCharacter(
        slug=slug,
        source_path=source_path,
        objects=imported,
        geometry=geometry,
        bounds=bounds,
    )


def make_principled_material(
    name: str,
    color: tuple[float, float, float, float],
    roughness: float,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Roughness"].default_value = roughness
    return material


def add_ground() -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=GROUND_SIZE, location=(0.0, 0.0, -0.004))
    ground = bpy.context.object
    ground.name = "Turnaround_Neutral_Ground"
    ground.data.materials.append(
        make_principled_material(
            "Turnaround_Neutral_Ground_Material",
            (0.115, 0.125, 0.135, 1.0),
            0.93,
        )
    )
    return ground


def add_area_light(name: str) -> bpy.types.Object:
    light_data = bpy.data.lights.new(name=name, type="AREA")
    light_data.shape = "DISK"
    light = bpy.data.objects.new(name=name, object_data=light_data)
    bpy.context.scene.collection.objects.link(light)
    return light


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def configure_lights(
    lights: tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object],
    camera: bpy.types.Object,
    target: Vector,
    subject_height: float,
    *,
    beauty: bool,
) -> None:
    """Place lights in camera space so every turnaround view is readable."""

    camera_rotation = camera.rotation_euler.to_quaternion()
    screen_right = camera_rotation @ Vector((1.0, 0.0, 0.0))
    screen_up = camera_rotation @ Vector((0.0, 1.0, 0.0))
    toward_camera = (camera.location - target).normalized()

    key, fill, rim = lights
    key.location = (
        target
        + toward_camera * subject_height * 1.55
        - screen_right * subject_height * 1.05
        + screen_up * subject_height * 1.25
    )
    fill.location = (
        target
        + toward_camera * subject_height * 1.25
        + screen_right * subject_height * 1.25
        + screen_up * subject_height * 0.50
    )
    rim.location = (
        target
        - toward_camera * subject_height * 1.20
        + screen_right * subject_height * 0.55
        + screen_up * subject_height * 1.10
    )

    energy_factor = subject_height * subject_height
    key.data.energy = (560.0 if beauty else 500.0) * energy_factor
    fill.data.energy = (250.0 if beauty else 330.0) * energy_factor
    rim.data.energy = (510.0 if beauty else 390.0) * energy_factor
    key.data.color = (1.0, 0.84, 0.68) if beauty else (1.0, 0.93, 0.84)
    fill.data.color = (0.62, 0.78, 1.0)
    rim.data.color = (0.57, 0.84, 1.0)

    for light, size_factor in zip(lights, (1.35, 1.70, 1.10), strict=True):
        light.data.size = subject_height * size_factor
        point_at(light, target)


def configure_scene() -> tuple[
    bpy.types.Object,
    tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object],
    bpy.types.Object,
]:
    scene = bpy.context.scene
    for engine_name in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine_name
            break
        except TypeError:
            continue
    else:
        raise RuntimeError("No supported Eevee render engine is available.")

    scene.render.resolution_x = IMAGE_SIZE
    scene.render.resolution_y = IMAGE_SIZE
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.fps = 30

    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.0

    world = scene.world or bpy.data.worlds.new("Turnaround_Neutral_World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.035, 0.042, 0.050, 1.0)
        background.inputs["Strength"].default_value = 0.42

    camera_data = bpy.data.cameras.new("Turnaround_Camera")
    camera = bpy.data.objects.new("Turnaround_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera_data.clip_start = 0.01
    camera_data.clip_end = 500.0
    scene.camera = camera

    lights = (
        add_area_light("Turnaround_Key"),
        add_area_light("Turnaround_Fill"),
        add_area_light("Turnaround_Rim"),
    )
    ground = add_ground()
    return camera, lights, ground


def set_active_character(
    characters: Iterable[ImportedCharacter], active: ImportedCharacter
) -> None:
    for character in characters:
        visible = character is active
        for obj in character.geometry:
            obj.hide_render = not visible


def render_still(output_path: Path) -> None:
    bpy.context.scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)
    if not output_path.is_file():
        raise RuntimeError(f"Blender did not create the expected render: {output_path}")


def render_turnaround_views(
    character: ImportedCharacter,
    camera: bpy.types.Object,
    lights: tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object],
    target: Vector,
    subject_height: float,
    ortho_scale: float,
) -> list[Path]:
    output_paths: list[Path] = []
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    camera.data.lens = 70.0

    for view in TURNAROUND_VIEWS:
        # A small, identical elevation exposes the ground contact while keeping
        # each requested azimuth exactly front, right-side, or back.
        camera.location = (
            target
            + view.camera_side * subject_height * 3.25
            + Vector((0.0, 0.0, subject_height * 0.035))
        )
        point_at(camera, target)
        configure_lights(
            lights,
            camera,
            target,
            subject_height,
            beauty=False,
        )
        output_path = OUTPUT_DIR / f"{character.slug}-{view.suffix}.png"
        render_still(output_path)
        output_paths.append(output_path)

    return output_paths


def render_beauty_view(
    character: ImportedCharacter,
    camera: bpy.types.Object,
    lights: tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object],
    target: Vector,
    subject_height: float,
) -> Path:
    camera.data.type = "PERSP"
    camera.data.lens = 68.0
    camera.data.sensor_width = 36.0

    # Front-left camera placement reveals the face, costume depth, and silhouette.
    camera_side = Vector((0.52, -0.82, 0.25)).normalized()
    camera.location = target + camera_side * subject_height * 2.55
    point_at(camera, target + Vector((0.0, 0.0, subject_height * 0.015)))
    configure_lights(
        lights,
        camera,
        target,
        subject_height,
        beauty=True,
    )

    output_path = OUTPUT_DIR / f"{character.slug}-three-quarter-beauty.png"
    render_still(output_path)
    return output_path


def main() -> None:
    source_paths = validate_inputs()
    reset_scene()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    characters = tuple(
        import_character(slug, source_path)
        for slug, source_path in zip(CHARACTER_SLUGS, source_paths, strict=True)
    )
    if not characters:
        raise RuntimeError("No v2 characters were available to render.")

    global_height = max(character.bounds.dimensions.z for character in characters)
    global_horizontal_extent = max(
        max(character.bounds.dimensions.x, character.bounds.dimensions.y)
        for character in characters
    )
    if global_height <= 0.0 or global_horizontal_extent <= 0.0:
        raise ValueError("The imported v2 character bounds are invalid.")

    ortho_scale = max(
        global_height * TURNAROUND_MARGIN,
        global_horizontal_extent * TURNAROUND_MARGIN,
    )
    camera, lights, ground = configure_scene()
    bpy.context.scene.frame_set(0)

    rendered_paths: list[Path] = []
    for character in characters:
        set_active_character(characters, character)
        target = Vector(
            (
                character.bounds.center.x,
                character.bounds.center.y,
                character.bounds.minimum.z + global_height * 0.5,
            )
        )
        ground.location = Vector(
            (
                character.bounds.center.x,
                character.bounds.center.y,
                character.bounds.minimum.z - 0.004,
            )
        )
        rendered_paths.extend(
            render_turnaround_views(
                character,
                camera,
                lights,
                target,
                global_height,
                ortho_scale,
            )
        )
        rendered_paths.append(
            render_beauty_view(
                character,
                camera,
                lights,
                target,
                global_height,
            )
        )

    print(
        "Rendered v2 character previews with shared "
        f"ortho_scale={ortho_scale:.4f}:"
    )
    for output_path in rendered_paths:
        print(f"  {output_path}")


if __name__ == "__main__":
    main()
