import * as THREE from "three";
import { ATTRIBUTE_BY_ID, FIELD_RADIUS } from "../game/constants";
import type { AttributeId, SceneSnapshot, Vec3XZ } from "../types/game";
import { disposeObject3D } from "./dispose";
import { createAttackFlash, createAttributeEffect, type BattleEffect } from "./effects";

export interface BattleScene {
  canvas: HTMLCanvasElement;
  update(snapshot: SceneSnapshot, deltaMs: number): void;
  spawnHitEffect(attributeId: AttributeId, position: Vec3XZ, scale?: number): void;
  spawnAttackFlash(attributeId: AttributeId, position: Vec3XZ, angle: number): void;
  resize(): void;
  dispose(): void;
}

function setSize(renderer: THREE.WebGLRenderer, camera: THREE.PerspectiveCamera, mount: HTMLElement) {
  const width = Math.max(mount.clientWidth, 1);
  const height = Math.max(mount.clientHeight, 1);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function makePlayer(): {
  group: THREE.Group;
  bodyMaterial: THREE.MeshStandardMaterial;
  headMaterial: THREE.MeshStandardMaterial;
} {
  const group = new THREE.Group();
  const bodyMaterial = new THREE.MeshStandardMaterial({
    color: 0x3fd4bd,
    roughness: 0.58,
    metalness: 0.08,
  });
  const headMaterial = new THREE.MeshStandardMaterial({
    color: 0xf6f1df,
    roughness: 0.55,
  });
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.42, 0.95, 18), bodyMaterial);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.34, 18, 12), headMaterial);
  const pointer = new THREE.Mesh(
    new THREE.ConeGeometry(0.18, 0.48, 12),
    new THREE.MeshStandardMaterial({ color: 0xffd95a, roughness: 0.4 }),
  );

  body.position.y = 0.55;
  head.position.y = 1.18;
  pointer.rotation.x = Math.PI / 2;
  pointer.position.set(0, 0.72, -0.5);
  group.add(body, head, pointer);

  return { group, bodyMaterial, headMaterial };
}

function makeBoss(): {
  group: THREE.Group;
  coreMaterial: THREE.MeshStandardMaterial;
  shellMaterial: THREE.MeshStandardMaterial;
} {
  const group = new THREE.Group();
  const coreMaterial = new THREE.MeshStandardMaterial({
    color: 0xb83f4b,
    roughness: 0.5,
    metalness: 0.04,
  });
  const shellMaterial = new THREE.MeshStandardMaterial({
    color: 0x3a2931,
    roughness: 0.62,
  });
  const core = new THREE.Mesh(new THREE.DodecahedronGeometry(0.95, 1), coreMaterial);
  const shell = new THREE.Mesh(new THREE.TorusGeometry(1.05, 0.12, 12, 36), shellMaterial);
  const crown = new THREE.Mesh(
    new THREE.ConeGeometry(0.42, 0.75, 5),
    new THREE.MeshStandardMaterial({ color: 0xffb033, roughness: 0.42 }),
  );

  core.position.y = 1;
  shell.position.y = 1;
  shell.rotation.x = Math.PI / 2;
  crown.position.y = 1.85;
  group.add(core, shell, crown);

  return { group, coreMaterial, shellMaterial };
}

export function createBattleScene(mount: HTMLElement): BattleScene {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x171a17);
  scene.fog = new THREE.Fog(0x171a17, 12, 24);

  const camera = new THREE.PerspectiveCamera(58, 1, 0.1, 80);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.domElement.className = "battle-canvas";
  mount.appendChild(renderer.domElement);

  const ambient = new THREE.HemisphereLight(0xe7ffd6, 0x2b231e, 1.25);
  const key = new THREE.DirectionalLight(0xffffff, 1.35);
  key.position.set(-3.5, 7, 4.5);
  scene.add(ambient, key);

  const floorMaterial = new THREE.MeshStandardMaterial({
    color: 0x263627,
    roughness: 0.9,
    metalness: 0.02,
  });
  const floor = new THREE.Mesh(new THREE.CircleGeometry(FIELD_RADIUS, 80), floorMaterial);
  floor.rotation.x = -Math.PI / 2;
  scene.add(floor);

  const ring = new THREE.Mesh(
    new THREE.RingGeometry(FIELD_RADIUS - 0.08, FIELD_RADIUS + 0.08, 96),
    new THREE.MeshBasicMaterial({ color: 0xd2b56d, transparent: true, opacity: 0.88 }),
  );
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = 0.018;
  scene.add(ring);

  const gridGroup = new THREE.Group();
  for (let i = 0; i < 12; i += 1) {
    const spoke = new THREE.Mesh(
      new THREE.BoxGeometry(FIELD_RADIUS * 1.86, 0.012, 0.02),
      new THREE.MeshBasicMaterial({ color: 0x6b7d58, transparent: true, opacity: 0.23 }),
    );
    spoke.rotation.y = (i / 12) * Math.PI;
    spoke.position.y = 0.03;
    gridGroup.add(spoke);
  }
  scene.add(gridGroup);

  const player = makePlayer();
  const boss = makeBoss();
  scene.add(player.group, boss.group);

  const shockwaveWarning = new THREE.Mesh(
    new THREE.RingGeometry(0.92, 1, 64),
    new THREE.MeshBasicMaterial({ color: 0xff3434, transparent: true, opacity: 0.0, depthWrite: false }),
  );
  shockwaveWarning.rotation.x = -Math.PI / 2;
  shockwaveWarning.position.y = 0.06;
  shockwaveWarning.visible = false;
  scene.add(shockwaveWarning);

  const beamWarning = new THREE.Mesh(
    new THREE.BoxGeometry(0.72, 0.04, FIELD_RADIUS * 1.8),
    new THREE.MeshBasicMaterial({ color: 0xff4638, transparent: true, opacity: 0.0, depthWrite: false }),
  );
  beamWarning.position.y = 0.08;
  beamWarning.visible = false;
  scene.add(beamWarning);

  const effects: BattleEffect[] = [];
  const clock = new THREE.Clock();
  const targetCamera = new THREE.Vector3();
  const lookTarget = new THREE.Vector3();

  setSize(renderer, camera, mount);

  const sceneApi: BattleScene = {
    canvas: renderer.domElement,
    update(snapshot: SceneSnapshot, deltaMs: number) {
      const attribute = ATTRIBUTE_BY_ID[snapshot.activeAttribute];
      const elapsed = clock.getElapsedTime();

      player.group.position.set(snapshot.playerPosition.x, 0, snapshot.playerPosition.z);
      player.group.rotation.y = snapshot.playerAngle;
      player.bodyMaterial.color.setHex(snapshot.isDodging ? 0xd2fff4 : 0x3fd4bd);
      player.headMaterial.emissive.setHex(snapshot.isDodging ? 0x2bb59f : 0x000000);

      boss.group.position.set(snapshot.bossPosition.x, 0, snapshot.bossPosition.z);
      boss.group.rotation.y += deltaMs * 0.00024;
      boss.group.position.y = Math.sin(elapsed * 2.1) * 0.06;
      boss.coreMaterial.color.setHex(snapshot.bossHurt ? attribute.accent : 0xb83f4b);
      boss.coreMaterial.emissive.setHex(snapshot.bossHurt ? attribute.color : 0x180305);
      boss.shellMaterial.color.setHex(snapshot.bossHpRatio < 0.25 ? 0x5a2228 : 0x3a2931);

      if (snapshot.shockwaveWarning) {
        shockwaveWarning.visible = true;
        shockwaveWarning.position.set(snapshot.bossPosition.x, 0.06, snapshot.bossPosition.z);
        shockwaveWarning.scale.setScalar(snapshot.shockwaveWarning.radius);
        const material = shockwaveWarning.material as THREE.MeshBasicMaterial;
        material.opacity = 0.18 + snapshot.shockwaveWarning.progress * 0.55;
      } else {
        shockwaveWarning.visible = false;
      }

      if (snapshot.beamWarning) {
        const direction = snapshot.beamWarning.direction;
        beamWarning.visible = true;
        beamWarning.position.set(
          snapshot.bossPosition.x + direction.x * (FIELD_RADIUS * 0.62),
          0.08,
          snapshot.bossPosition.z + direction.z * (FIELD_RADIUS * 0.62),
        );
        beamWarning.rotation.y = Math.atan2(direction.x, direction.z);
        const material = beamWarning.material as THREE.MeshBasicMaterial;
        material.opacity = 0.16 + snapshot.beamWarning.progress * 0.42;
      } else {
        beamWarning.visible = false;
      }

      for (let index = effects.length - 1; index >= 0; index -= 1) {
        const effect = effects[index];
        const alive = effect.update(deltaMs);

        if (!alive) {
          scene.remove(effect.group);
          effect.dispose();
          effects.splice(index, 1);
        }
      }

      targetCamera.set(
        snapshot.playerPosition.x,
        5.2,
        snapshot.playerPosition.z + 6.3,
      );
      camera.position.lerp(targetCamera, 0.09);
      lookTarget.set(
        snapshot.playerPosition.x * 0.35 + snapshot.bossPosition.x * 0.65,
        0.95,
        snapshot.playerPosition.z * 0.35 + snapshot.bossPosition.z * 0.65,
      );
      camera.lookAt(lookTarget);
      renderer.render(scene, camera);
    },
    spawnHitEffect(attributeId: AttributeId, position: Vec3XZ, scale = 1) {
      const effect = createAttributeEffect(attributeId, position, scale);
      effects.push(effect);
      scene.add(effect.group);
    },
    spawnAttackFlash(attributeId: AttributeId, position: Vec3XZ, angle: number) {
      const effect = createAttackFlash(attributeId, position, angle);
      effects.push(effect);
      scene.add(effect.group);
    },
    resize() {
      setSize(renderer, camera, mount);
    },
    dispose() {
      effects.forEach((effect) => effect.dispose());
      effects.splice(0, effects.length);
      mount.removeChild(renderer.domElement);
      renderer.dispose();
      disposeObject3D(scene);
    },
  };

  return sceneApi;
}
