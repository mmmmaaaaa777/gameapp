"""Print raw and evaluated bounds for suspicious v3 character objects.

Run through Blender with a .blend file already opened.  The report is intended
for build-time validation and does not mutate or save the scene.
"""

from __future__ import annotations

import bpy
from mathutils import Vector


def bounds_from_points(points: list[Vector]) -> tuple[Vector, Vector, Vector]:
    minimum = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    maximum = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return minimum, maximum, maximum - minimum


def mesh_bounds(obj: bpy.types.Object, *, evaluated: bool) -> tuple[Vector, Vector, Vector]:
    target = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else obj
    mesh = target.to_mesh() if evaluated else target.data
    try:
        points = [target.matrix_world @ vertex.co for vertex in mesh.vertices]
        return bounds_from_points(points)
    finally:
        if evaluated:
            target.to_mesh_clear()


print("V3_GEOMETRY_DIAGNOSTIC_BEGIN")
for armature in (item for item in bpy.context.scene.objects if item.type == "ARMATURE"):
    print(
        f"ARMATURE {armature.name}|pose_position={armature.data.pose_position}"
        f"|location={tuple(round(value, 4) for value in armature.location)}"
        f"|rotation={tuple(round(value, 4) for value in armature.rotation_euler)}"
        f"|scale={tuple(round(value, 4) for value in armature.scale)}"
    )
    for pose_bone in armature.pose.bones:
        translation = pose_bone.matrix_basis.to_translation()
        scale = pose_bone.matrix_basis.to_scale()
        angle = pose_bone.matrix_basis.to_quaternion().angle
        if translation.length > 1e-5 or (scale - Vector((1.0, 1.0, 1.0))).length > 1e-5 or abs(angle) > 1e-5:
            print(
                f"POSE {pose_bone.name}|translation={tuple(round(value, 5) for value in translation)}"
                f"|scale={tuple(round(value, 5) for value in scale)}|angle={angle:.5f}"
            )
for body in (
    item
    for item in bpy.context.scene.objects
    if item.type == "MESH" and len(item.data.vertices) > 10_000 and item.vertex_groups.get("body")
):
    body_points = []
    body_group = body.vertex_groups["body"]
    for vertex in body.data.vertices:
        try:
            if body_group.weight(vertex.index) > 0.5:
                body_points.append(body.matrix_world @ vertex.co)
        except RuntimeError:
            pass
    body_z_min = min(point.z for point in body_points)
    body_z_max = max(point.z for point in body_points)
    body_height = body_z_max - body_z_min
    for normalized_z, half_width in ((0.50, 0.18), (0.72, 0.18), (0.835, 0.08)):
        target_z = body_z_min + body_height * normalized_z
        section = [
            point
            for point in body_points
            if abs(point.z - target_z) <= body_height * (0.010 if normalized_z > 0.8 else 0.014)
            and abs(point.x) < body_height * half_width
        ]
        x_min = min(point.x for point in section)
        x_max = max(point.x for point in section)
        y_min = min(point.y for point in section)
        y_max = max(point.y for point in section)
        print(
            f"SECTION z={normalized_z}|center=({(x_min + x_max) * 0.5:.4f},{(y_min + y_max) * 0.5:.4f})"
            f"|half=({(x_max - x_min) * 0.5:.4f},{(y_max - y_min) * 0.5:.4f})"
        )
    neck_group = body.vertex_groups.get("neck_01")
    if neck_group:
        neck_points = []
        for vertex in body.data.vertices:
            try:
                if body_group.weight(vertex.index) > 0.5 and neck_group.weight(vertex.index) > 0.25:
                    neck_points.append(body.matrix_world @ vertex.co)
            except RuntimeError:
                pass
        print(
            f"NECK_GROUP center=({(min(p.x for p in neck_points) + max(p.x for p in neck_points)) * 0.5:.4f},"
            f"{(min(p.y for p in neck_points) + max(p.y for p in neck_points)) * 0.5:.4f})"
            f"|half=({(max(p.x for p in neck_points) - min(p.x for p in neck_points)) * 0.5:.4f},"
            f"{(max(p.y for p in neck_points) - min(p.y for p in neck_points)) * 0.5:.4f})"
        )
    for slot in body.material_slots:
        material = slot.material
        if material is None or not material.use_nodes:
            continue
        print(f"BODY_MATERIAL {material.name}")
        for node in material.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                base = node.inputs.get("Base Color")
                print(
                    f"  PRINCIPLED {node.name}|base={tuple(round(value, 4) for value in base.default_value)}"
                    f"|linked={base.is_linked}|roughness={node.inputs['Roughness'].default_value:.4f}"
                )
for obj in sorted((item for item in bpy.context.scene.objects if item.type == "MESH"), key=lambda item: item.name):
    if not obj.data.vertices:
        continue
    raw_min, raw_max, raw_size = mesh_bounds(obj, evaluated=False)
    eval_min, eval_max, eval_size = mesh_bounds(obj, evaluated=True)
    largest = max(eval_size)
    ratio = largest / max(max(raw_size), 1e-6)
    armatures = [modifier.object.name if modifier.object else "NONE" for modifier in obj.modifiers if modifier.type == "ARMATURE"]
    groups = sorted(group.name for group in obj.vertex_groups)
    if largest > 2.5 or ratio > 2.0 or obj.get("v3_generated") or len(obj.data.vertices) > 10_000:
        modifiers = [f"{modifier.name}:{modifier.type}" for modifier in obj.modifiers]
        print(
            f"{obj.name}|raw={tuple(round(value, 4) for value in raw_size)}"
            f"|eval={tuple(round(value, 4) for value in eval_size)}|ratio={ratio:.3f}"
            f"|origin={tuple(round(value, 4) for value in obj.matrix_world.translation)}"
            f"|parent={obj.parent.name if obj.parent else 'NONE'}|armature={armatures}|groups={groups}"
            f"|modifiers={modifiers}"
        )
    if ratio > 2.0:
        visibility = [modifier.show_viewport for modifier in obj.modifiers]
        try:
            for modifier in obj.modifiers:
                modifier.show_viewport = False
            bpy.context.view_layer.update()
            for modifier in obj.modifiers:
                modifier.show_viewport = True
                bpy.context.view_layer.update()
                _step_min, _step_max, step_size = mesh_bounds(obj, evaluated=True)
                print(
                    f"STEP {obj.name}|through={modifier.name}:{modifier.type}"
                    f"|size={tuple(round(value, 4) for value in step_size)}"
                )
        finally:
            for modifier, visible in zip(obj.modifiers, visibility, strict=True):
                modifier.show_viewport = visible
            bpy.context.view_layer.update()
        target = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = target.to_mesh()
        try:
            ranked = sorted(
                enumerate(mesh.vertices),
                key=lambda item: (target.matrix_world @ item[1].co).length,
                reverse=True,
            )[:8]
            print(f"EXTREMES {obj.name}")
            for index, vertex in ranked:
                point = target.matrix_world @ vertex.co
                print(f"  evaluated[{index}]={tuple(round(value, 4) for value in point)}")
        finally:
            target.to_mesh_clear()
        for index, vertex in sorted(
            enumerate(obj.data.vertices),
            key=lambda item: (obj.matrix_world @ item[1].co).length,
            reverse=True,
        )[:8]:
            point = obj.matrix_world @ vertex.co
            weights = sorted(
                (
                    obj.vertex_groups[membership.group].name,
                    round(membership.weight, 5),
                )
                for membership in vertex.groups
            )
            print(f"  raw[{index}]={tuple(round(value, 4) for value in point)} weights={weights}")
print("V3_GEOMETRY_DIAGNOSTIC_END")
