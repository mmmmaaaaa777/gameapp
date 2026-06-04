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

function makePrimitiveBadge(attributeId: AttributeId, scale: number): THREE.Group {
  const attribute = ATTRIBUTE_BY_ID[attributeId];
  const badge = new THREE.Group();
  const base = new THREE.Mesh(
    new THREE.RingGeometry(0.18 * scale, 0.24 * scale, 30),
    makeMeshMaterial(attribute.color, 0.82),
  );
  base.rotation.x = -Math.PI / 2;
  badge.add(base);

  if (attributeId === "light") {
    const star = new THREE.Mesh(
      new THREE.OctahedronGeometry(0.14 * scale, 0),
      makeMeshMaterial(attribute.accent, 0.92),
    );
    badge.add(star);
    addRadialLines(badge, [], attribute.accent, 8, scale * 0.36);
  }

  if (attributeId === "dark") {
    for (let i = 0; i < 2; i += 1) {
      const arc = new THREE.Mesh(
        new THREE.TorusGeometry((0.12 + i * 0.05) * scale, 0.014 * scale, 6, 24, Math.PI * 1.35),
        makeMeshMaterial(i === 0 ? attribute.accent : attribute.color, 0.9),
      );
      arc.rotation.set(Math.PI / 2, i * 0.9, i * 1.8);
      badge.add(arc);
    }
  }

  if (attributeId === "fire") {
    for (let i = 0; i < 3; i += 1) {
      const flame = new THREE.Mesh(
        new THREE.ConeGeometry((0.055 + i * 0.012) * scale, (0.24 - i * 0.035) * scale, 8),
        makeMeshMaterial(i === 1 ? attribute.accent : attribute.color, 0.9),
      );
      flame.position.set((i - 1) * 0.07 * scale, 0.07 * scale, 0);
      flame.rotation.x = i === 1 ? 0 : 0.18 * (i - 1);
      badge.add(flame);
    }
  }

  if (attributeId === "poison") {
    const fog = new THREE.Mesh(
      new THREE.SphereGeometry(0.15 * scale, 10, 8),
      makeMeshMaterial(attribute.color, 0.32),
    );
    fog.scale.set(1.45, 0.62, 1.45);
    badge.add(fog);

    const core = new THREE.Mesh(
      new THREE.SphereGeometry(0.055 * scale, 8, 8),
      makeMeshMaterial(attribute.accent, 0.9),
    );
    core.position.y = 0.03 * scale;
    badge.add(core);
  }

  if (attributeId === "water") {
    const ripple = new THREE.Mesh(
      new THREE.RingGeometry(0.08 * scale, 0.14 * scale, 30),
      makeMeshMaterial(attribute.accent, 0.86),
    );
    ripple.rotation.x = -Math.PI / 2;
    badge.add(ripple);

    const drop = new THREE.Mesh(
      new THREE.SphereGeometry(0.07 * scale, 10, 8),
      makeMeshMaterial(attribute.color, 0.9),
    );
    drop.scale.set(0.82, 1.45, 0.82);
    drop.position.y = 0.1 * scale;
    badge.add(drop);
  }

  if (attributeId === "wind") {
    for (let i = 0; i < 3; i += 1) {
      const arc = new THREE.Mesh(
        new THREE.TorusGeometry((0.09 + i * 0.045) * scale, 0.012 * scale, 6, 26, Math.PI * 1.25),
        makeMeshMaterial(i % 2 === 0 ? attribute.color : attribute.accent, 0.88),
      );
      arc.rotation.set(Math.PI / 2, i * 0.95, i * 0.75);
      badge.add(arc);
    }
  }

  badge.position.set(0, 1.2, 0);
  return badge;
}

function addRadialLines(
  group: THREE.Group,
  items: EffectItem[],
  color: number,
  count: number,
  scale: number,
) {
  for (let i = 0; i < count; i += 1) {
    const angle = (i / count) * Math.PI * 2;
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(Math.cos(angle) * 0.14 * scale, 0.18, Math.sin(angle) * 0.14 * scale),
      new THREE.Vector3(Math.cos(angle) * 0.9 * scale, 0.34, Math.sin(angle) * 0.9 * scale),
    ]);
    const line = new THREE.Line(geometry, makeLineMaterial(color, 0.95));
    group.add(line);
    if (items.length > 0) {
      items.push({
        object: line,
        velocity: new THREE.Vector3(Math.cos(angle) * 0.28, 0.16, Math.sin(angle) * 0.28),
        spin: new THREE.Vector3(0, 0, 0),
      });
    }
  }
}

export function createAttributeEffect(
  attributeId: AttributeId,
  position: Vec3XZ,
  scale = 1,
): BattleEffect {
  const attribute = ATTRIBUTE_BY_ID[attributeId];
  const group = new THREE.Group();
  const items: EffectItem[] = [];
  const lifetimeMs = attributeId === "poison" ? 1180 : 920;
  let ageMs = 0;

  group.position.set(position.x, 0.58, position.z);

  const addParticle = (
    object: THREE.Object3D,
    velocity: THREE.Vector3,
    spin = new THREE.Vector3(0, 0, 0),
  ) => {
    group.add(object);
    items.push({ object, velocity, spin });
  };

  const impactRing = new THREE.Mesh(
    new THREE.RingGeometry(0.3 * scale, 0.4 * scale, 48),
    makeMeshMaterial(attribute.accent, 0.92),
  );
  impactRing.rotation.x = -Math.PI / 2;
  addParticle(impactRing, new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 3.6, 0));

  const outerSigil = new THREE.Mesh(
    new THREE.RingGeometry(0.58 * scale, 0.63 * scale, 54),
    makeMeshMaterial(attribute.color, 0.58),
  );
  outerSigil.rotation.x = -Math.PI / 2;
  outerSigil.position.y = 0.012;
  addParticle(outerSigil, new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, -1.6, 0));

  const badge = makePrimitiveBadge(attributeId, scale);
  addParticle(badge, new THREE.Vector3(0, 0.42, 0), new THREE.Vector3(0, 2.2, 0));

  const particleCount = Math.round(11 + scale * 6);
  const sphere = new THREE.SphereGeometry(0.065 * scale, 8, 8);

  for (let i = 0; i < particleCount; i += 1) {
    const angle = (i / particleCount) * Math.PI * 2;
    const height = attributeId === "fire" ? Math.random() * 1.25 + 0.55 : Math.random() * 0.5 + 0.12;
    const radial = 0.75 + Math.random() * 0.82;
    const material = makeMeshMaterial(i % 3 === 0 ? attribute.accent : attribute.color, 0.9);
    const mesh = new THREE.Mesh(sphere.clone(), material);
    mesh.position.set(0, 0, 0);

    let velocity = new THREE.Vector3(
      Math.cos(angle) * radial,
      height,
      Math.sin(angle) * radial,
    ).multiplyScalar(scale);

    if (attributeId === "water") {
      velocity = new THREE.Vector3(Math.cos(angle) * 0.52, 0.06, Math.sin(angle) * 0.52);
    }

    if (attributeId === "wind") {
      velocity = new THREE.Vector3(Math.cos(angle) * 1.42, 0.08, Math.sin(angle) * 0.42);
    }

    if (attributeId === "dark") {
      mesh.position.set(Math.cos(angle) * 0.56, 0.14, Math.sin(angle) * 0.56);
      velocity = new THREE.Vector3(-Math.cos(angle) * 0.34, 0.08, -Math.sin(angle) * 0.34);
    }

    if (attributeId === "poison") {
      velocity = new THREE.Vector3(Math.cos(angle) * 0.28, 0.18, Math.sin(angle) * 0.28);
    }

    addParticle(mesh, velocity);
  }

  if (attributeId === "light") {
    addRadialLines(group, items, attribute.accent, 10, scale);
    const beam = new THREE.Mesh(
      new THREE.CylinderGeometry(0.035 * scale, 0.07 * scale, 1.32 * scale, 8),
      makeMeshMaterial(attribute.accent, 0.48),
    );
    beam.position.y = 0.68 * scale;
    addParticle(beam, new THREE.Vector3(0, 0.24, 0), new THREE.Vector3(0, 2.8, 0));

    const flash = new THREE.Mesh(
      new THREE.OctahedronGeometry(0.34 * scale, 0),
      makeMeshMaterial(attribute.color, 0.86),
    );
    flash.position.y = 0.28;
    addParticle(flash, new THREE.Vector3(0, 0.18, 0), new THREE.Vector3(2.4, 2.2, 0.8));
  }

  if (attributeId === "water") {
    const rings = 4;

    for (let i = 0; i < rings; i += 1) {
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(0.22 + i * 0.18, 0.27 + i * 0.18, 40),
        makeMeshMaterial(i % 2 === 0 ? attribute.color : attribute.accent, 0.72),
      );
      ring.rotation.x = -Math.PI / 2;
      addParticle(ring, new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 1.1 + i * 0.35, 0));
    }

    for (let i = 0; i < 5; i += 1) {
      const angle = (i / 5) * Math.PI * 2;
      const shard = new THREE.Mesh(
        new THREE.ConeGeometry(0.06 * scale, 0.34 * scale, 6),
        makeMeshMaterial(i % 2 === 0 ? attribute.accent : attribute.color, 0.68),
      );
      shard.position.set(Math.cos(angle) * 0.34 * scale, 0.16, Math.sin(angle) * 0.34 * scale);
      shard.rotation.set(0.52, angle, 0);
      addParticle(shard, new THREE.Vector3(Math.cos(angle) * 0.16, 0.34, Math.sin(angle) * 0.16));
    }
  }

  if (attributeId === "dark") {
    addRadialLines(group, items, attribute.accent, 8, scale);

    const shadowPulse = new THREE.Mesh(
      new THREE.SphereGeometry(0.66 * scale, 16, 10),
      makeMeshMaterial(attribute.color, 0.24),
    );
    shadowPulse.position.y = 0.1;
    shadowPulse.scale.set(1.15, 0.42, 1.15);
    addParticle(shadowPulse, new THREE.Vector3(0, 0.04, 0), new THREE.Vector3(0, -0.9, 0));

    for (let i = 0; i < 3; i += 1) {
      const swirl = new THREE.Mesh(
        new THREE.TorusGeometry(0.42 + i * 0.16, 0.032, 8, 36, Math.PI * 1.55),
        makeMeshMaterial(i % 2 === 0 ? attribute.accent : attribute.color, 0.9),
      );
      swirl.position.y = 0.18 + i * 0.08;
      swirl.rotation.set(Math.PI / 2.05, i * 0.9, i * 1.8);
      addParticle(swirl, new THREE.Vector3(0, 0.08, 0), new THREE.Vector3(0.5, -3.3, 0.7));
    }

    const voidCore = new THREE.Mesh(
      new THREE.SphereGeometry(0.18 * scale, 10, 8),
      makeMeshMaterial(0x120516, 0.74),
    );
    voidCore.position.y = 0.28;
    addParticle(voidCore, new THREE.Vector3(0, 0.05, 0), new THREE.Vector3(0, -2.6, 0));
  }

  if (attributeId === "fire") {
    const fireColumn = new THREE.Mesh(
      new THREE.ConeGeometry(0.18 * scale, 0.92 * scale, 10),
      makeMeshMaterial(attribute.accent, 0.46),
    );
    fireColumn.position.y = 0.38 * scale;
    addParticle(fireColumn, new THREE.Vector3(0, 0.45, 0), new THREE.Vector3(0, 2.6, 0));

    addRadialLines(group, items, attribute.color, 8, scale * 0.72);

    for (let i = 0; i < 6; i += 1) {
      const angle = (i / 6) * Math.PI * 2;
      const ember = new THREE.Mesh(
        new THREE.ConeGeometry(0.065 * scale, 0.34 * scale, 8),
        makeMeshMaterial(i % 2 === 0 ? attribute.color : attribute.accent, 0.86),
      );
      ember.rotation.x = Math.PI;
      addParticle(
        ember,
        new THREE.Vector3(Math.cos(angle) * 0.38, 1.18, Math.sin(angle) * 0.38),
        new THREE.Vector3(3.4, 1.2, 0.8),
      );
    }

    const blastRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.54 * scale, 0.05 * scale, 8, 34, Math.PI * 1.55),
      makeMeshMaterial(attribute.accent, 0.8),
    );
    blastRing.position.y = 0.2 * scale;
    blastRing.rotation.x = Math.PI / 2;
    addParticle(blastRing, new THREE.Vector3(0, 0.22, 0), new THREE.Vector3(0.3, 3.6, 0.4));
  }

  if (attributeId === "wind") {
    const lines = 7;

    for (let i = 0; i < lines; i += 1) {
      const geometry = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(-0.62 * scale, 0.04 + i * 0.035, 0),
        new THREE.Vector3(0.62 * scale, 0.16 + i * 0.035, 0),
      ]);
      const line = new THREE.Line(
        geometry,
        makeLineMaterial(i % 2 === 0 ? attribute.color : attribute.accent, 0.85),
      );
      line.rotation.y = (i / lines) * Math.PI * 2 + Math.PI / 8;
      addParticle(line, new THREE.Vector3(Math.cos(i) * 0.2, 0.12, Math.sin(i) * 0.5), new THREE.Vector3(0, 3.2, 0));
    }

    for (let i = 0; i < 2; i += 1) {
      const helix = new THREE.Mesh(
        new THREE.TorusGeometry((0.42 + i * 0.18) * scale, 0.024 * scale, 7, 34, Math.PI * 1.35),
        makeMeshMaterial(i === 0 ? attribute.color : attribute.accent, 0.76),
      );
      helix.position.y = 0.2 + i * 0.12;
      helix.rotation.set(Math.PI / 2.3, i * 0.9, i * 1.25);
      addParticle(helix, new THREE.Vector3(0.12 * (i === 0 ? 1 : -1), 0.22, 0), new THREE.Vector3(0.5, 3.4, 0.6));
    }
  }

  if (attributeId === "poison") {
    for (let i = 0; i < 3; i += 1) {
      const cloud = new THREE.Mesh(
        new THREE.SphereGeometry((0.34 + i * 0.12) * scale, 12, 8),
        makeMeshMaterial(i % 2 === 0 ? attribute.color : attribute.accent, 0.18),
      );
      cloud.position.set((i - 1) * 0.22, 0.16 + i * 0.08, i % 2 === 0 ? 0.18 : -0.18);
      cloud.scale.set(1.15, 0.48, 1.15);
      addParticle(cloud, new THREE.Vector3((i - 1) * 0.06, 0.1, 0.02), new THREE.Vector3(0, 0.5, 0));
    }

    const miasmaRing = new THREE.Mesh(
      new THREE.RingGeometry(0.52 * scale, 0.68 * scale, 36),
      makeMeshMaterial(attribute.accent, 0.28),
    );
    miasmaRing.rotation.x = -Math.PI / 2;
    miasmaRing.position.y = 0.04;
    addParticle(miasmaRing, new THREE.Vector3(0, 0.02, 0), new THREE.Vector3(0, 0.9, 0));
  }

  return {
    group,
    update(deltaMs: number) {
      ageMs += deltaMs;
      const t = Math.min(ageMs / lifetimeMs, 1);
      const appear = Math.min(ageMs / 120, 1);
      const opacity = Math.max(0, (1 - t) * appear);

      items.forEach((item) => {
        item.object.position.addScaledVector(item.velocity, deltaMs / 1000);
        item.object.rotation.x += item.spin.x * (deltaMs / 1000);
        item.object.rotation.y += item.spin.y * (deltaMs / 1000);
        item.object.rotation.z += item.spin.z * (deltaMs / 1000);
      });

      group.scale.setScalar(0.86 + appear * 0.18 + t * 0.74 * scale);
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
