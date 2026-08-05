"""Report suspicious projected colors on v4 hands and sleeves."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy
import numpy as np


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", type=Path, required=True)
    return parser.parse_args(argv)


def group_strength(obj: bpy.types.Object, tokens: tuple[str, ...]) -> np.ndarray:
    indices = {
        group.index
        for group in obj.vertex_groups
        if any(token in group.name for token in tokens)
    }
    strengths = np.zeros(len(obj.data.vertices), dtype=np.float32)
    for vertex in obj.data.vertices:
        strengths[vertex.index] = sum(
            assignment.weight
            for assignment in vertex.groups
            if assignment.group in indices
        )
    return strengths


def describe(label: str, mask: np.ndarray, values: dict[str, np.ndarray]) -> None:
    indices = np.flatnonzero(mask)
    if not len(indices):
        print(f"V4_COLOR_DIAGNOSTIC label={label} count=0")
        return
    fields = [f"label={label}", f"count={len(indices)}"]
    for name, value in values.items():
        selected = value[indices]
        fields.append(
            f"{name}=({float(np.min(selected)):.4f},"
            f"{float(np.median(selected)):.4f},{float(np.max(selected)):.4f})"
        )
    print("V4_COLOR_DIAGNOSTIC " + " ".join(fields))


def main() -> None:
    args = parse_args()
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    candidate = max(
        (obj for obj in bpy.context.scene.objects if obj.type == "MESH"),
        key=lambda obj: len(obj.data.vertices),
    )
    mesh = candidate.data
    color_layer = mesh.color_attributes.get("ReferenceColor")
    if color_layer is None or color_layer.domain != "POINT":
        raise RuntimeError("ReferenceColor POINT attribute is missing")

    coordinates = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    colors = np.empty(len(color_layer.data) * 4, dtype=np.float32)
    mesh.vertices.foreach_get("co", coordinates)
    color_layer.data.foreach_get("color_srgb", colors)
    coordinates = coordinates.reshape((-1, 3))
    colors = colors.reshape((-1, 4))[:, :3]
    minimum = np.min(coordinates, axis=0)
    maximum = np.max(coordinates, axis=0)
    z_fraction = (coordinates[:, 2] - minimum[2]) / (maximum[2] - minimum[2])
    x_fraction = np.abs(coordinates[:, 0] - (minimum[0] + maximum[0]) * 0.5) / (
        maximum[0] - minimum[0]
    )
    luminance = np.mean(colors, axis=1)
    arm_strength = group_strength(
        candidate,
        (
            "upperarm_",
            "lowerarm_",
            "hand_",
            "thumb_",
            "index_",
            "middle_",
            "ring_",
            "pinky_",
        ),
    )
    hand_strength = group_strength(
        candidate,
        ("hand_", "thumb_", "index_", "middle_", "ring_", "pinky_"),
    )
    outer_arm = (arm_strength >= 0.05) & (x_fraction >= 0.22) & (z_fraction < 0.62)
    teal = (
        outer_arm
        & (colors[:, 1] > colors[:, 0] * 1.05)
        & (colors[:, 2] > colors[:, 0] * 1.05)
        & (luminance < 0.42)
    )
    dark = outer_arm & (luminance < 0.16)
    describe(
        "teal_outer_arm",
        teal,
        {
            "z": z_fraction,
            "x": x_fraction,
            "lum": luminance,
            "arm": arm_strength,
            "hand": hand_strength,
        },
    )
    describe(
        "dark_outer_arm",
        dark,
        {
            "z": z_fraction,
            "x": x_fraction,
            "lum": luminance,
            "arm": arm_strength,
            "hand": hand_strength,
        },
    )
    for index in np.flatnonzero(dark):
        print(
            "V4_COLOR_VERTEX "
            f"index={int(index)} x={coordinates[index, 0]:.4f} "
            f"y={coordinates[index, 1]:.4f} z={z_fraction[index]:.4f} "
            f"x_fraction={x_fraction[index]:.4f} lum={luminance[index]:.4f} "
            f"rgb=({colors[index, 0]:.4f},{colors[index, 1]:.4f},{colors[index, 2]:.4f})"
        )


if __name__ == "__main__":
    main()
