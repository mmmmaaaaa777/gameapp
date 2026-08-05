"""Print topology islands and bounds for a Hunyuan reconstruction GLB."""

from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

import bpy
from mathutils import Vector


def arguments() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--glb", type=Path, required=True)
    return parser.parse_args(argv)


def main() -> None:
    args = arguments()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
    mesh_object = max(
        (obj for obj in bpy.context.scene.objects if obj.type == "MESH"),
        key=lambda obj: len(obj.data.polygons),
    )
    mesh = mesh_object.data
    vertex_faces: list[list[int]] = [[] for _ in mesh.vertices]
    for polygon in mesh.polygons:
        for vertex_index in polygon.vertices:
            vertex_faces[vertex_index].append(polygon.index)

    unseen = set(range(len(mesh.polygons)))
    components: list[list[int]] = []
    while unseen:
        first = unseen.pop()
        component = [first]
        queue = deque([first])
        while queue:
            polygon_index = queue.popleft()
            for vertex_index in mesh.polygons[polygon_index].vertices:
                for neighbor in vertex_faces[vertex_index]:
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        component.append(neighbor)
                        queue.append(neighbor)
        components.append(component)

    components.sort(key=len, reverse=True)
    print(
        f"HUNYUAN_TOPOLOGY mesh={mesh_object.name} vertices={len(mesh.vertices)} "
        f"faces={len(mesh.polygons)} islands={len(components)}"
    )
    for index, component in enumerate(components[:40]):
        vertex_indices = {
            vertex_index
            for polygon_index in component
            for vertex_index in mesh.polygons[polygon_index].vertices
        }
        points = [mesh_object.matrix_world @ mesh.vertices[i].co for i in vertex_indices]
        minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
        maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
        print(
            f"HUNYUAN_ISLAND index={index} faces={len(component)} vertices={len(vertex_indices)} "
            f"min=({minimum.x:.5f},{minimum.y:.5f},{minimum.z:.5f}) "
            f"max=({maximum.x:.5f},{maximum.y:.5f},{maximum.z:.5f})"
        )


if __name__ == "__main__":
    main()
