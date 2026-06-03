import type { Vec2, Vec3XZ } from "../types/game";

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function distance2d(a: Vec3XZ, b: Vec3XZ): number {
  return Math.hypot(a.x - b.x, a.z - b.z);
}

export function length2d(vector: Vec3XZ): number {
  return Math.hypot(vector.x, vector.z);
}

export function normalize2d(vector: Vec3XZ): Vec3XZ {
  const length = length2d(vector);

  if (length <= 0.0001) {
    return { x: 0, z: -1 };
  }

  return {
    x: vector.x / length,
    z: vector.z / length,
  };
}

export function clampToCircle(position: Vec3XZ, radius: number): Vec3XZ {
  const length = length2d(position);

  if (length <= radius) {
    return position;
  }

  const ratio = radius / length;

  return {
    x: position.x * ratio,
    z: position.z * ratio,
  };
}

export function addScaled(
  position: Vec3XZ,
  direction: Vec3XZ,
  scale: number,
): Vec3XZ {
  return {
    x: position.x + direction.x * scale,
    z: position.z + direction.z * scale,
  };
}

export function angleFromDirection(direction: Vec3XZ): number {
  return Math.atan2(-direction.x, -direction.z);
}

export function screenDeltaToWorldDirection(delta: Vec2): Vec3XZ {
  return normalize2d({
    x: delta.x,
    z: delta.y,
  });
}

export function pointLineDistance(
  point: Vec3XZ,
  origin: Vec3XZ,
  direction: Vec3XZ,
): number {
  const normalized = normalize2d(direction);
  const px = point.x - origin.x;
  const pz = point.z - origin.z;
  const projection = px * normalized.x + pz * normalized.z;

  if (projection < 0) {
    return Number.POSITIVE_INFINITY;
  }

  const closest = {
    x: origin.x + normalized.x * projection,
    z: origin.z + normalized.z * projection,
  };

  return distance2d(point, closest);
}

export function smoothStep(value: number): number {
  const x = clamp(value, 0, 1);
  return x * x * (3 - 2 * x);
}
