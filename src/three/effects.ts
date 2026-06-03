import * as THREE from "three";
import { ATTRIBUTE_BY_ID } from "../game/constants";
import type { AttributeId, Vec3XZ } from "../types/game";
import { disposeObject3D } from "./dispose";

interface EffectItem {
  object: THREE.Object3D;
  velocity: THREE.Vector3;
  spin: THREE.Vector3;
}

export interface BattleEffect {
  group: THREE.Group;
  update(deltaMs: number): boolean;
  dispose(): void;
}

function makeMeshMaterial(color: number, opacity: number): THREE.MeshBasicMaterial {
  return new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity,
    depthWrite: false,
  });
}

function makeLineMaterial(color: number, opacity: number): THREE.LineBasicMaterial {
  return new THREE.LineBasicMaterial({
    color,
    transparent: true,
    opacity,
    depthWrite: false,
  });
}

function applyOpacity(object: THREE.Object3D, opacity: number): void {
  object.traverse((child) => {
    const mesh = child as THREE.Mesh;
    const material = mesh.material;

    if (Array.isArray(material)) {
      material.forEach((item) => {
        item.opacity = opacity;
      });
    } else if (material) {
      material.opacity = opacity;
    }
  });
}

export function createAttributeEffect(
  attributeId: AttributeId,
  position: Vec3XZ,
  scale = 1,
): BattleEffect {
  const attribute = ATTRIBUTE_BY_ID[attributeId];
  const group = new THREE.Group();
  const items: EffectItem[] = [];
  const lifetimeMs = attributeId === "poison" ? 1000 : 760;
  let ageMs = 0;

  group.position.set(position.x, 0.45, position.z);

  const addParticle = (
    object: THREE.Object3D,
    velocity: THREE.Vector3,
    spin = new THREE.Vector3(0, 0, 0),
  ) => {
    group.add(object);
    items.push({ object, velocity, spin });
  };

  const particleCount = Math.round(10 + scale * 5);
  const sphere = new THREE.SphereGeometry(0.055 * scale, 8, 8);

  for (let i = 0; i < particleCount; i += 1) {
    const angle = (i / particleCount) * Math.PI * 2;
    const height = attributeId === "fire" ? Math.random() * 0.7 + 0.25 : Math.random() * 0.45;
    const radial = 0.8 + Math.random() * 0.7;
    const material = makeMeshMaterial(i % 3 === 0 ? attribute.accent : attribute.color, 0.9);
    const mesh = new THREE.Mesh(sphere.clone(), material);
    mesh.position.set(0, 0, 0);

    let velocity = new THREE.Vector3(
      Math.cos(angle) * radial,
      height,
      Math.sin(angle) * radial,
    ).multiplyScalar(scale);

    if (attributeId === "water") {
      velocity = new THREE.Vector3(Math.cos(angle) * 0.35, 0.08, Math.sin(angle) * 0.35);
    }

    if (attributeId === "wind") {
      velocity = new THREE.Vector3(Math.cos(angle) * 1.1, 0.1, Math.sin(angle) * 0.35);
    }

    if (attributeId === "dark") {
      velocity = new THREE.Vector3(Math.cos(angle) * 0.45, 0.12, Math.sin(angle) * 0.45);
    }

    addParticle(mesh, velocity);
  }

  if (attributeId === "water" || attributeId === "light") {
    const rings = attributeId === "water" ? 3 : 2;

    for (let i = 0; i < rings; i += 1) {
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(0.2 + i * 0.13, 0.25 + i * 0.13, 32),
        makeMeshMaterial(i % 2 === 0 ? attribute.color : attribute.accent, 0.72),
      );
      ring.rotation.x = -Math.PI / 2;
      addParticle(ring, new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 1.6 + i, 0));
    }
  }

  if (attributeId === "dark" || attributeId === "wind") {
    const lines = attributeId === "dark" ? 4 : 6;

    for (let i = 0; i < lines; i += 1) {
      const geometry = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(-0.35 * scale, 0, 0),
        new THREE.Vector3(0.35 * scale, 0.12, 0),
      ]);
      const line = new THREE.Line(
        geometry,
        makeLineMaterial(i % 2 === 0 ? attribute.color : attribute.accent, 0.85),
      );
      line.rotation.y = (i / lines) * Math.PI * 2;
      addParticle(line, new THREE.Vector3(0, 0.08, 0), new THREE.Vector3(0, 2.2, 0));
    }
  }

  if (attributeId === "poison") {
    const cloud = new THREE.Mesh(
      new THREE.SphereGeometry(0.5 * scale, 12, 8),
      makeMeshMaterial(attribute.color, 0.22),
    );
    cloud.scale.set(1.1, 0.45, 1.1);
    addParticle(cloud, new THREE.Vector3(0, 0.08, 0), new THREE.Vector3(0, 0.45, 0));
  }

  return {
    group,
    update(deltaMs: number) {
      ageMs += deltaMs;
      const t = Math.min(ageMs / lifetimeMs, 1);
      const opacity = Math.max(0, 1 - t);

      items.forEach((item) => {
        item.object.position.addScaledVector(item.velocity, deltaMs / 1000);
        item.object.rotation.x += item.spin.x * (deltaMs / 1000);
        item.object.rotation.y += item.spin.y * (deltaMs / 1000);
        item.object.rotation.z += item.spin.z * (deltaMs / 1000);
      });

      group.scale.setScalar(1 + t * 0.8 * scale);
      applyOpacity(group, opacity);

      return ageMs < lifetimeMs;
    },
    dispose() {
      disposeObject3D(group);
    },
  };
}

export function createAttackFlash(
  attributeId: AttributeId,
  position: Vec3XZ,
  angle: number,
): BattleEffect {
  const attribute = ATTRIBUTE_BY_ID[attributeId];
  const group = new THREE.Group();
  const arc = new THREE.Mesh(
    new THREE.TorusGeometry(0.48, 0.035, 8, 36, Math.PI * 1.2),
    makeMeshMaterial(attribute.accent, 0.75),
  );
  let ageMs = 0;

  group.position.set(position.x, 0.75, position.z);
  group.rotation.y = angle - Math.PI * 0.62;
  arc.rotation.x = Math.PI / 2;
  group.add(arc);

  return {
    group,
    update(deltaMs: number) {
      ageMs += deltaMs;
      const t = Math.min(ageMs / 260, 1);
      group.scale.setScalar(1 + t * 1.2);
      applyOpacity(group, 1 - t);
      return ageMs < 260;
    },
    dispose() {
      disposeObject3D(group);
    },
  };
}
