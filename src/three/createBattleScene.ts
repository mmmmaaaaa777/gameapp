import * as THREE from "three";
import { FBXLoader } from "three/examples/jsm/loaders/FBXLoader.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { ATTRIBUTE_BY_ID, FIELD_RADIUS } from "../game/constants";
import type { AttributeId, SceneSnapshot, Vec3XZ } from "../types/game";
import { disposeObject3D } from "./dispose";
import { createAttackFlash, createAttributeEffect, type BattleEffect } from "./effects";

const PLAYER_MODEL_URL = "/models/characters/initial-male-v6.glb";
const PLAYER_VISUAL_HEIGHT = 1.82;
const PLAYER_ANIMATION_URLS = {
  idle: "/models/animations/idle.fbx",
  run: "/models/animations/run.fbx",
  jump: "/models/animations/jump.fbx",
} as const;
const PLAYER_ANIMATION_KEYS = ["idle", "run", "jump"] as const;
const MIN_PLAYER_ANIMATION_DURATION_SECONDS = 0.12;

type PlayerAnimationKey = (typeof PLAYER_ANIMATION_KEYS)[number];

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

interface PlayerModel {
  group: THREE.Group;
  fallbackGroup: THREE.Group;
  bodyMaterial: THREE.MeshStandardMaterial;
  headMaterial: THREE.MeshStandardMaterial;
  limbMaterial: THREE.MeshStandardMaterial;
  markerMaterial: THREE.MeshStandardMaterial;
  backCoreMaterial: THREE.MeshBasicMaterial;
  dodgeMaterial: THREE.MeshBasicMaterial;
  footstepMaterial: THREE.MeshBasicMaterial;
  characterModel: THREE.Group | null;
  fbxMixer: THREE.AnimationMixer | null;
  fbxActions: Partial<Record<PlayerAnimationKey, THREE.AnimationAction>>;
  fbxActiveAction: PlayerAnimationKey | null;
  characterBaseScale: number;
  characterBasePosition: THREE.Vector3;
  torso: THREE.Mesh;
  head: THREE.Mesh;
  leftArm: THREE.Mesh;
  rightArm: THREE.Mesh;
  leftLeg: THREE.Mesh;
  rightLeg: THREE.Mesh;
  frontMarker: THREE.Mesh;
  headingMarker: THREE.Mesh;
  backCore: THREE.Mesh;
  backHalo: THREE.Mesh;
  dodgeAura: THREE.Mesh;
  leftStepRing: THREE.Mesh;
  rightStepRing: THREE.Mesh;
}

interface ArenaModel {
  group: THREE.Group;
  runeGroup: THREE.Group;
  pulseMaterial: THREE.MeshBasicMaterial;
}

interface LoadedPlayerAnimationState {
  mixer: THREE.AnimationMixer | null;
  actions: Partial<Record<PlayerAnimationKey, THREE.AnimationAction>>;
}

function makeStandardMaterial(
  color: number,
  roughness = 0.72,
  metalness = 0.04,
  emissive = 0x000000,
): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color,
    roughness,
    metalness,
    emissive,
  });
}

function makeGlowMaterial(color: number, opacity: number): THREE.MeshBasicMaterial {
  return new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity,
    depthWrite: false,
  });
}

async function assetExists(url: string): Promise<boolean> {
  try {
    const response = await fetch(url, {
      method: "HEAD",
      cache: "no-store",
    });

    return response.ok;
  } catch {
    return false;
  }
}

function getAnimationTrackTargetName(trackName: string): string {
  const separatorIndex = trackName.search(/[.[\]]/);
  const rawTargetName = separatorIndex >= 0 ? trackName.slice(0, separatorIndex) : trackName;
  const pathSeparatorIndex = rawTargetName.lastIndexOf("/");

  return pathSeparatorIndex >= 0 ? rawTargetName.slice(pathSeparatorIndex + 1) : rawTargetName;
}

function collectAnimationTargetNames(model: THREE.Object3D): Set<string> {
  const targetNames = new Set<string>();

  model.traverse((child) => {
    if (child.name) {
      targetNames.add(child.name);
    }
  });

  return targetNames;
}

function getClipBindableTargetCount(clip: THREE.AnimationClip, targetNames: Set<string>): number {
  const trackTargets = new Set(clip.tracks.map((track) => getAnimationTrackTargetName(track.name)));

  return [...trackTargets].filter((target) => targetNames.has(target)).length;
}

function isUsablePlayerAnimationClip(clip: THREE.AnimationClip, targetNames: Set<string>): boolean {
  const trackTargets = new Set(clip.tracks.map((track) => getAnimationTrackTargetName(track.name)));
  const bindableTargetCount = getClipBindableTargetCount(clip, targetNames);
  const requiredTargetCount = Math.min(8, Math.ceil(trackTargets.size * 0.5));

  return (
    clip.tracks.length > 0
    && clip.duration >= MIN_PLAYER_ANIMATION_DURATION_SECONDS
    && bindableTargetCount >= requiredTargetCount
  );
}

function selectPlayerAnimationClip(
  key: PlayerAnimationKey,
  clips: THREE.AnimationClip[],
  model: THREE.Group,
): THREE.AnimationClip | null {
  const targetNames = collectAnimationTargetNames(model);
  const keyName = key.toLowerCase();
  const candidates = clips
    .filter((clip) => isUsablePlayerAnimationClip(clip, targetNames))
    .map((clip) => {
      const clipName = clip.name.toLowerCase();
      const hasMatchingName = clipName.includes(keyName);
      const bindableTargetCount = getClipBindableTargetCount(clip, targetNames);

      return {
        clip,
        score: (hasMatchingName ? 1000 : 0) + bindableTargetCount + clip.duration,
      };
    })
    .sort((a, b) => b.score - a.score);

  return candidates[0]?.clip.clone() ?? null;
}

function fitModelToPlayer(model: THREE.Group): void {
  const initialBox = new THREE.Box3().setFromObject(model);
  const size = initialBox.getSize(new THREE.Vector3());
  const largestAxis = Math.max(size.x, size.y, size.z);

  if (largestAxis > 0.001) {
    model.scale.setScalar(PLAYER_VISUAL_HEIGHT / largestAxis);
  }

  model.rotation.y = Math.PI;
  model.updateWorldMatrix(true, true);

  const fittedBox = new THREE.Box3().setFromObject(model);
  const center = fittedBox.getCenter(new THREE.Vector3());
  model.position.x -= center.x;
  model.position.z -= center.z;
  model.position.y -= fittedBox.min.y;
}

function preparePlayerModel(model: THREE.Group, maxAnisotropy: number): void {
  fitModelToPlayer(model);

  model.traverse((child) => {
    const mesh = child as THREE.Mesh;

    if (!mesh.isMesh) {
      return;
    }

    mesh.frustumCulled = false;
    mesh.castShadow = true;
    mesh.receiveShadow = true;

    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    materials.forEach((material) => {
      if (!(material instanceof THREE.MeshStandardMaterial)) {
        return;
      }

      const textures = [
        material.map,
        material.normalMap,
        material.roughnessMap,
        material.metalnessMap,
        material.aoMap,
      ];
      textures.forEach((texture) => {
        if (texture) {
          texture.anisotropy = Math.min(maxAnisotropy, 8);
          texture.needsUpdate = true;
        }
      });
    });
  });
}

function makeSkyDome(): THREE.Mesh {
  const material = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    uniforms: {
      topColor: { value: new THREE.Color(0x06070d) },
      bottomColor: { value: new THREE.Color(0x1b1714) },
      hazeColor: { value: new THREE.Color(0x4b3c2a) },
    },
    vertexShader: `
      varying vec3 vWorldPosition;
      void main() {
        vec4 worldPosition = modelMatrix * vec4(position, 1.0);
        vWorldPosition = worldPosition.xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      varying vec3 vWorldPosition;
      uniform vec3 topColor;
      uniform vec3 bottomColor;
      uniform vec3 hazeColor;
      void main() {
        float h = normalize(vWorldPosition).y;
        float gradient = smoothstep(-0.35, 0.72, h);
        vec3 color = mix(bottomColor, topColor, gradient);
        float haze = 1.0 - smoothstep(-0.18, 0.42, abs(h));
        gl_FragColor = vec4(mix(color, hazeColor, haze * 0.16), 1.0);
      }
    `,
  });
  return new THREE.Mesh(new THREE.SphereGeometry(42, 24, 14), material);
}

function createStoneFloorTexture(): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;

  const context = canvas.getContext("2d");
  if (!context) {
    return new THREE.CanvasTexture(canvas);
  }

  context.fillStyle = "#3b3d35";
  context.fillRect(0, 0, canvas.width, canvas.height);

  for (let y = 0; y < canvas.height; y += 62) {
    const rowOffset = y % 124 === 0 ? 0 : 46;

    for (let x = -rowOffset; x < canvas.width; x += 92) {
      const shade = 56 + Math.abs((x * 13 + y * 9) % 32);
      const width = 86 + ((x + y) % 13);
      const height = 56 + ((x * 3 + y) % 9);

      context.fillStyle = `rgb(${shade + 9}, ${shade + 7}, ${shade})`;
      context.fillRect(x + 3, y + 3, width, height);

      context.strokeStyle = "rgba(6, 5, 4, 0.72)";
      context.lineWidth = 5;
      context.strokeRect(x + 3, y + 3, width, height);

      context.strokeStyle = "rgba(236, 211, 158, 0.16)";
      context.lineWidth = 2;
      context.beginPath();
      context.moveTo(x + 7, y + 8);
      context.lineTo(x + width - 6, y + 7 + ((x + y) % 8));
      context.stroke();

      context.strokeStyle = "rgba(13, 11, 9, 0.28)";
      context.lineWidth = 2;
      context.beginPath();
      context.moveTo(x + 16 + ((x + y) % 18), y + 18);
      context.lineTo(x + 35 + ((x + y) % 12), y + 28 + ((x + y) % 10));
      context.lineTo(x + 55 + ((x + y) % 8), y + 36 + ((x + y) % 12));
      context.stroke();
    }
  }

  for (let i = 0; i < 420; i += 1) {
    const x = (i * 47 + 19) % canvas.width;
    const y = (i * 89 + 31) % canvas.height;
    const size = 1 + (i % 4);
    const alpha = 0.07 + (i % 5) * 0.02;
    context.fillStyle = i % 3 === 0
      ? `rgba(245, 225, 170, ${alpha})`
      : `rgba(14, 12, 9, ${alpha + 0.04})`;
    context.fillRect(x, y, size, size);
  }

  for (let i = 0; i < 22; i += 1) {
    const startX = (i * 37 + 28) % canvas.width;
    const startY = (i * 53 + 21) % canvas.height;
    context.strokeStyle = "rgba(8, 7, 6, 0.55)";
    context.lineWidth = 3;
    context.beginPath();
    context.moveTo(startX, startY);
    context.lineTo(startX + 20 + (i % 4) * 7, startY + 8 + (i % 3) * 8);
    context.lineTo(startX + 38 + (i % 2) * 12, startY + 22 + (i % 5));
    context.stroke();
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(2.05, 2.05);
  texture.needsUpdate = true;

  return texture;
}

function makeArena(): ArenaModel {
  const group = new THREE.Group();
  const runeGroup = new THREE.Group();
  const floorTexture = createStoneFloorTexture();
  const floorMaterial = new THREE.MeshStandardMaterial({
    color: 0x8a8d80,
    map: floorTexture,
    roughness: 0.98,
    metalness: 0,
    emissive: 0x040504,
  });
  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(FIELD_RADIUS, 96),
    floorMaterial,
  );
  floor.rotation.x = -Math.PI / 2;
  group.add(floor);

  const pulseMaterial = makeGlowMaterial(0xffd66e, 0.28);
  const ringMaterial = makeGlowMaterial(0xd5b46e, 0.42);
  const dimLineMaterial = makeGlowMaterial(0x75805c, 0.3);
  const crackMaterial = new THREE.MeshBasicMaterial({
    color: 0x090806,
    transparent: true,
    opacity: 0.52,
    depthWrite: false,
  });
  const groutMaterial = new THREE.MeshBasicMaterial({
    color: 0x11100d,
    transparent: true,
    opacity: 0.44,
    depthWrite: false,
  });
  const stoneMaterial = makeStandardMaterial(0x33342f, 0.88, 0.02);
  const darkStoneMaterial = makeStandardMaterial(0x24251f, 0.9, 0.02);
  const crystalMaterial = makeStandardMaterial(0x285f58, 0.45, 0.05, 0x0b3a35);

  [2.05, 3.85, 5.8, 7.62].forEach((radius, index) => {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(radius - 0.025, radius + 0.025, 96),
      index === 1 ? pulseMaterial : ringMaterial,
    );
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.026 + index * 0.004;
    runeGroup.add(ring);
  });

  for (let i = 0; i < 18; i += 1) {
    const angle = (i / 18) * Math.PI * 2;
    const spoke = new THREE.Mesh(
      new THREE.BoxGeometry(FIELD_RADIUS * 1.54, 0.014, i % 3 === 0 ? 0.035 : 0.018),
      i % 3 === 0 ? ringMaterial : dimLineMaterial,
    );
    spoke.rotation.y = angle;
    spoke.position.y = 0.034;
    runeGroup.add(spoke);
  }

  for (let i = 0; i < 12; i += 1) {
    const angle = (i / 12) * Math.PI * 2;
    const marker = new THREE.Mesh(
      new THREE.BoxGeometry(0.38, 0.018, 0.08),
      pulseMaterial,
    );
    marker.position.set(Math.cos(angle) * 4.8, 0.045, Math.sin(angle) * 4.8);
    marker.rotation.y = -angle;
    runeGroup.add(marker);
  }

  for (let i = -3; i <= 3; i += 1) {
    const offset = i * 1.86;
    const length = Math.sqrt(Math.max(FIELD_RADIUS * FIELD_RADIUS - offset * offset, 0)) * 1.84;
    const horizontal = new THREE.Mesh(
      new THREE.BoxGeometry(length, 0.012, 0.045),
      groutMaterial,
    );
    horizontal.position.set(0, 0.018, offset);
    group.add(horizontal);

    const vertical = new THREE.Mesh(
      new THREE.BoxGeometry(length, 0.012, 0.045),
      groutMaterial,
    );
    vertical.position.set(offset, 0.019, 0);
    vertical.rotation.y = Math.PI / 2;
    group.add(vertical);
  }

  for (let i = 0; i < 10; i += 1) {
    const angle = (i / 10) * Math.PI * 2 + 0.18;
    const distance = 1.3 + (i % 5) * 1.14;
    const crack = new THREE.Mesh(
      new THREE.BoxGeometry(0.72 + (i % 3) * 0.22, 0.01, 0.018),
      crackMaterial,
    );
    crack.position.set(Math.cos(angle) * distance, 0.022, Math.sin(angle) * distance);
    crack.rotation.y = angle + (i % 4) * 0.32;
    group.add(crack);
  }

  const outerTorus = new THREE.Mesh(
    new THREE.TorusGeometry(FIELD_RADIUS + 0.18, 0.13, 8, 96),
    makeStandardMaterial(0x4c3e2d, 0.76, 0.06, 0x100904),
  );
  outerTorus.rotation.x = Math.PI / 2;
  outerTorus.position.y = 0.13;
  group.add(runeGroup, outerTorus);

  for (let i = 0; i < 24; i += 1) {
    const angle = (i / 24) * Math.PI * 2;
    const block = new THREE.Mesh(
      new THREE.BoxGeometry(0.56, 0.46 + (i % 2) * 0.1, 0.24),
      i % 4 === 0 ? stoneMaterial : darkStoneMaterial,
    );
    block.position.set(Math.cos(angle) * 8.55, 0.23, Math.sin(angle) * 8.55);
    block.rotation.y = -angle;
    group.add(block);
  }

  for (let i = 0; i < 8; i += 1) {
    const angle = (i / 8) * Math.PI * 2 + Math.PI / 8;
    const radius = 9.35;
    const pillar = new THREE.Group();
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.42, 0.24, 8), darkStoneMaterial);
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.28, 1.45, 8), stoneMaterial);
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.24, 0.2, 8), darkStoneMaterial);
    const crystal = new THREE.Mesh(new THREE.OctahedronGeometry(0.22, 0), crystalMaterial);
    base.position.y = 0.12;
    shaft.position.y = 0.86;
    cap.position.y = 1.62;
    crystal.position.y = 1.92;
    pillar.add(base, shaft, cap, crystal);
    pillar.position.set(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
    pillar.rotation.y = -angle;
    group.add(pillar);
  }

  for (let i = 0; i < 10; i += 1) {
    const angle = (i / 10) * Math.PI * 2 + 0.22;
    const radius = 8.95 + (i % 2) * 0.55;
    const shard = new THREE.Mesh(
      new THREE.ConeGeometry(0.16 + (i % 3) * 0.035, 0.58 + (i % 2) * 0.22, 5),
      i % 2 === 0 ? stoneMaterial : crystalMaterial,
    );
    shard.position.set(Math.cos(angle) * radius, 0.28, Math.sin(angle) * radius);
    shard.rotation.set(0.15 * (i % 2), -angle, 0.18 * (i % 3 - 1));
    group.add(shard);
  }

  return { group, runeGroup, pulseMaterial };
}

async function loadFbxAnimationClip(key: PlayerAnimationKey, model: THREE.Group): Promise<THREE.AnimationClip | null> {
  const url = PLAYER_ANIMATION_URLS[key];

  if (!(await assetExists(url))) {
    return null;
  }

  try {
    const asset = await new FBXLoader().loadAsync(url);
    const clip = selectPlayerAnimationClip(key, asset.animations, model);
    disposeObject3D(asset);
    return clip;
  } catch {
    return null;
  }
}

async function loadFbxPlayerAnimations(model: THREE.Group): Promise<LoadedPlayerAnimationState> {
  const targetNames = collectAnimationTargetNames(model);
  const hasV6GameRig = ["pelvis", "spine_01", "upperarm_l", "thigh_l", "head"].every(
    (name) => targetNames.has(name),
  );

  // The bundled FBX clips use a different Mixamo-style skeleton.  Binding
  // only their shared Root track moves the v6 rig out of the arena while the
  // remaining tracks fail.  Keep the clean rest pose and synthetic movement
  // until those clips have been explicitly retargeted to the MPFB bone names.
  if (hasV6GameRig) {
    return { mixer: null, actions: {} };
  }

  const clips = await Promise.all(
    PLAYER_ANIMATION_KEYS.map(async (key) => ({
      key,
      clip: await loadFbxAnimationClip(key, model),
    })),
  );
  const loadedClips = clips.filter(
    (entry): entry is { key: PlayerAnimationKey; clip: THREE.AnimationClip } => entry.clip !== null,
  );

  if (loadedClips.length === 0) {
    return { mixer: null, actions: {} };
  }

  const mixer = new THREE.AnimationMixer(model);
  const actions: Partial<Record<PlayerAnimationKey, THREE.AnimationAction>> = {};

  loadedClips.forEach(({ key, clip }) => {
    const action = mixer.clipAction(clip);
    action.enabled = true;
    action.setEffectiveWeight(1);

    if (key === "jump") {
      action.setLoop(THREE.LoopOnce, 1);
      action.clampWhenFinished = true;
    } else {
      action.setLoop(THREE.LoopRepeat, Infinity);
      action.clampWhenFinished = false;
      action.timeScale = key === "run" ? 1.08 : 1;
    }

    actions[key] = action;
  });

  return { mixer, actions };
}

function selectFbxPlayerAnimation(player: PlayerModel, snapshot: SceneSnapshot): PlayerAnimationKey | null {
  if (snapshot.isDodging && player.fbxActions.jump) {
    return "jump";
  }

  if (snapshot.playerMoveIntensity > 0.08 && player.fbxActions.run) {
    return "run";
  }

  return player.fbxActions.idle ? "idle" : null;
}

function playFbxPlayerAnimation(player: PlayerModel, key: PlayerAnimationKey, fadeDuration = 0.14): void {
  const nextAction = player.fbxActions[key];

  if (!nextAction || player.fbxActiveAction === key) {
    return;
  }

  const previousAction = player.fbxActiveAction ? player.fbxActions[player.fbxActiveAction] : undefined;
  nextAction.enabled = true;
  nextAction.setEffectiveWeight(1);
  nextAction.reset();
  nextAction.play();

  if (previousAction) {
    previousAction.crossFadeTo(nextAction, fadeDuration, false);
  } else if (fadeDuration > 0) {
    nextAction.fadeIn(fadeDuration);
  }

  player.fbxActiveAction = key;
}

async function loadGlbPlayer(
  player: PlayerModel,
  maxAnisotropy: number,
  onLoaded: (model: THREE.Group, animations: LoadedPlayerAnimationState) => void,
): Promise<void> {
  if (!(await assetExists(PLAYER_MODEL_URL))) {
    player.fallbackGroup.visible = true;
    return;
  }

  try {
    const asset = await new GLTFLoader().loadAsync(PLAYER_MODEL_URL);
    const model = asset.scene;
    preparePlayerModel(model, maxAnisotropy);
    const animations = await loadFbxPlayerAnimations(model);
    onLoaded(model, animations);
  } catch {
    player.fallbackGroup.visible = true;
  }
}

function makePlayer(): PlayerModel {
  const group = new THREE.Group();
  const fallbackGroup = new THREE.Group();
  const bodyMaterial = new THREE.MeshStandardMaterial({
    color: 0x34c5ad,
    roughness: 0.56,
    metalness: 0.08,
  });
  const headMaterial = new THREE.MeshStandardMaterial({
    color: 0xf6f1df,
    roughness: 0.55,
  });
  const limbMaterial = new THREE.MeshStandardMaterial({
    color: 0x258d83,
    roughness: 0.58,
    metalness: 0.04,
  });
  const markerMaterial = new THREE.MeshStandardMaterial({
    color: 0xffd95a,
    roughness: 0.36,
    emissive: 0x332100,
  });
  const backCoreMaterial = makeGlowMaterial(0x8fffea, 0.86);
  const bootMaterial = new THREE.MeshStandardMaterial({
    color: 0x183d3a,
    roughness: 0.7,
  });
  const dodgeMaterial = new THREE.MeshBasicMaterial({
    color: 0x9affef,
    transparent: true,
    opacity: 0,
    depthWrite: false,
  });
  const footstepMaterial = new THREE.MeshBasicMaterial({
    color: 0x87ffe3,
    transparent: true,
    opacity: 0,
    depthWrite: false,
  });
  const modelRearLight = new THREE.PointLight(0xc4efff, 5.4, 6.5, 1.8);
  const modelFrontLight = new THREE.PointLight(0xffe6c2, 2.8, 5.4, 1.8);
  modelRearLight.position.set(-0.9, 2.6, 1.75);
  modelFrontLight.position.set(1.15, 2.25, -1.25);

  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.43, 0.92, 18), bodyMaterial);
  const chest = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.36, 0.5), bodyMaterial);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.34, 18, 12), headMaterial);
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.16, 0.14, 12), limbMaterial);
  const shoulderLine = new THREE.Mesh(new THREE.BoxGeometry(0.88, 0.12, 0.18), limbMaterial);
  const leftArm = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.095, 0.74, 10), limbMaterial);
  const rightArm = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.095, 0.74, 10), limbMaterial);
  const leftLeg = new THREE.Mesh(new THREE.CylinderGeometry(0.105, 0.12, 0.72, 10), limbMaterial);
  const rightLeg = new THREE.Mesh(new THREE.CylinderGeometry(0.105, 0.12, 0.72, 10), limbMaterial);
  const leftFoot = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.12, 0.34), bootMaterial);
  const rightFoot = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.12, 0.34), bootMaterial);
  const frontMarker = new THREE.Mesh(
    new THREE.ConeGeometry(0.14, 0.42, 12),
    markerMaterial,
  );
  const backStripe = new THREE.Mesh(
    new THREE.BoxGeometry(0.12, 0.7, 0.045),
    new THREE.MeshStandardMaterial({ color: 0x123330, roughness: 0.66 }),
  );
  const backCore = new THREE.Mesh(
    new THREE.SphereGeometry(0.085, 12, 8),
    backCoreMaterial,
  );
  const backHalo = new THREE.Mesh(
    new THREE.RingGeometry(0.12, 0.18, 24),
    backCoreMaterial,
  );
  const dodgeAura = new THREE.Mesh(
    new THREE.RingGeometry(0.48, 0.7, 36),
    dodgeMaterial,
  );
  const leftStepRing = new THREE.Mesh(
    new THREE.RingGeometry(0.08, 0.18, 20),
    footstepMaterial,
  );
  const rightStepRing = new THREE.Mesh(
    new THREE.RingGeometry(0.08, 0.18, 20),
    footstepMaterial,
  );

  torso.position.y = 0.76;
  chest.position.y = 1.08;
  head.position.y = 1.58;
  neck.position.y = 1.32;
  shoulderLine.position.y = 1.16;
  leftArm.position.set(-0.53, 0.9, -0.02);
  rightArm.position.set(0.53, 0.9, -0.02);
  leftLeg.position.set(-0.19, 0.36, 0.02);
  rightLeg.position.set(0.19, 0.36, 0.02);
  leftFoot.position.set(-0.19, 0.08, -0.1);
  rightFoot.position.set(0.19, 0.08, -0.1);
  frontMarker.rotation.x = Math.PI / 2;
  frontMarker.position.set(0, 1.08, -0.36);
  backStripe.position.set(0, 0.94, 0.35);
  backCore.position.set(0, 1.16, 0.45);
  backHalo.position.set(0, 1.16, 0.452);
  backHalo.rotation.x = Math.PI / 2;
  dodgeAura.rotation.x = -Math.PI / 2;
  dodgeAura.position.y = 0.035;
  leftStepRing.rotation.x = -Math.PI / 2;
  rightStepRing.rotation.x = -Math.PI / 2;
  leftStepRing.position.set(-0.2, 0.045, 0.22);
  rightStepRing.position.set(0.2, 0.045, 0.22);
  leftStepRing.visible = false;
  rightStepRing.visible = false;

  const headingMarker = new THREE.Mesh(
    new THREE.ConeGeometry(0.12, 0.34, 12),
    markerMaterial,
  );
  headingMarker.rotation.x = Math.PI / 2;
  headingMarker.position.set(0, 0.2, -0.62);

  fallbackGroup.add(
    torso,
    chest,
    neck,
    head,
    shoulderLine,
    leftArm,
    rightArm,
    leftLeg,
    rightLeg,
    leftFoot,
    rightFoot,
    frontMarker,
    backStripe,
  );

  group.add(
    fallbackGroup,
    modelRearLight,
    modelFrontLight,
    headingMarker,
    backCore,
    backHalo,
    dodgeAura,
    leftStepRing,
    rightStepRing,
  );

  return {
    group,
    fallbackGroup,
    bodyMaterial,
    headMaterial,
    limbMaterial,
    markerMaterial,
    backCoreMaterial,
    dodgeMaterial,
    footstepMaterial,
    characterModel: null,
    fbxMixer: null,
    fbxActions: {},
    fbxActiveAction: null,
    characterBaseScale: 1,
    characterBasePosition: new THREE.Vector3(),
    torso,
    head,
    leftArm,
    rightArm,
    leftLeg,
    rightLeg,
    frontMarker,
    headingMarker,
    backCore,
    backHalo,
    dodgeAura,
    leftStepRing,
    rightStepRing,
  };
}

interface BossModel {
  group: THREE.Group;
  coreMaterial: THREE.MeshStandardMaterial;
  shellMaterial: THREE.MeshStandardMaterial;
  hideMaterial: THREE.MeshStandardMaterial;
  glowMaterial: THREE.MeshBasicMaterial;
  eyeMaterial: THREE.MeshBasicMaterial;
}

function makeBoss(): BossModel {
  const group = new THREE.Group();
  const coreMaterial = makeStandardMaterial(0xb83f4b, 0.46, 0.06, 0x260509);
  const shellMaterial = makeStandardMaterial(0x2d2226, 0.68, 0.04, 0x0b0305);
  const hideMaterial = makeStandardMaterial(0x5b2530, 0.58, 0.05, 0x150405);
  const hornMaterial = makeStandardMaterial(0xbfa46a, 0.5, 0.08, 0x1e1204);
  const clawMaterial = makeStandardMaterial(0x171315, 0.72, 0.02);
  const glowMaterial = makeGlowMaterial(0xff6e65, 0.8);
  const eyeMaterial = makeGlowMaterial(0xffd66e, 0.94);

  const body = new THREE.Mesh(new THREE.SphereGeometry(1, 18, 14), hideMaterial);
  body.scale.set(1.42, 0.95, 1.08);
  body.position.y = 1.08;

  const chest = new THREE.Mesh(new THREE.SphereGeometry(0.82, 16, 12), shellMaterial);
  chest.scale.set(1.05, 0.72, 0.9);
  chest.position.set(0, 1.28, -0.25);

  const head = new THREE.Mesh(new THREE.SphereGeometry(0.68, 16, 12), shellMaterial);
  head.scale.set(1.12, 0.78, 0.9);
  head.position.set(0, 1.98, -0.58);

  const snout = new THREE.Mesh(new THREE.ConeGeometry(0.42, 0.62, 5), shellMaterial);
  snout.rotation.x = -Math.PI / 2;
  snout.position.set(0, 1.92, -1.02);

  const core = new THREE.Mesh(new THREE.DodecahedronGeometry(0.42, 1), coreMaterial);
  core.position.set(0, 1.32, -0.96);

  const coreHalo = new THREE.Mesh(
    new THREE.TorusGeometry(0.52, 0.035, 8, 32),
    glowMaterial,
  );
  coreHalo.position.copy(core.position);
  coreHalo.rotation.x = Math.PI / 2;

  const spineRing = new THREE.Mesh(
    new THREE.TorusGeometry(1.06, 0.045, 8, 42, Math.PI * 1.68),
    glowMaterial,
  );
  spineRing.position.set(0, 1.24, 0.08);
  spineRing.rotation.set(Math.PI / 2, 0, Math.PI * 0.16);

  for (let side = -1; side <= 1; side += 2) {
    const horn = new THREE.Mesh(new THREE.ConeGeometry(0.16, 0.72, 7), hornMaterial);
    horn.position.set(side * 0.44, 2.5, -0.54);
    horn.rotation.set(0.28, 0, side * -0.48);
    group.add(horn);

    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.06, 8, 6), eyeMaterial);
    eye.position.set(side * 0.26, 2.04, -1.16);
    group.add(eye);

    const upperArm = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.24, 0.92, 8), hideMaterial);
    upperArm.position.set(side * 1.08, 1.15, -0.34);
    upperArm.rotation.z = side * 0.54;
    upperArm.rotation.x = -0.18;

    const foreArm = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.22, 0.78, 8), shellMaterial);
    foreArm.position.set(side * 1.46, 0.65, -0.64);
    foreArm.rotation.z = side * 0.28;
    foreArm.rotation.x = -0.38;

    const claw = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.38, 6), clawMaterial);
    claw.position.set(side * 1.6, 0.28, -0.78);
    claw.rotation.x = Math.PI;
    group.add(upperArm, foreArm, claw);
  }

  for (let i = 0; i < 5; i += 1) {
    const spike = new THREE.Mesh(new THREE.ConeGeometry(0.16 - i * 0.012, 0.5 - i * 0.035, 6), hornMaterial);
    spike.position.set(0, 1.92 - i * 0.16, 0.06 + i * 0.34);
    spike.rotation.x = 0.34 + i * 0.12;
    group.add(spike);
  }

  for (let i = 0; i < 4; i += 1) {
    const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.13 - i * 0.018, 0.18 - i * 0.015, 0.62, 8), hideMaterial);
    tail.position.set(0, 0.72 - i * 0.06, 0.88 + i * 0.48);
    tail.rotation.x = 1.12 + i * 0.16;
    group.add(tail);
  }

  const crown = new THREE.Mesh(new THREE.ConeGeometry(0.34, 0.54, 5), hornMaterial);
  crown.position.y = 2.72;

  const baseShadow = new THREE.Mesh(
    new THREE.CircleGeometry(1.55, 40),
    makeGlowMaterial(0x090506, 0.38),
  );
  baseShadow.rotation.x = -Math.PI / 2;
  baseShadow.position.y = 0.045;

  group.add(baseShadow, body, chest, head, snout, core, coreHalo, spineRing, crown);

  return { group, coreMaterial, shellMaterial, hideMaterial, glowMaterial, eyeMaterial };
}

export function createBattleScene(mount: HTMLElement): BattleScene {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x08090d);
  scene.fog = new THREE.Fog(0x141018, 10, 27);
  scene.add(makeSkyDome());

  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 80);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.domElement.className = "battle-canvas";
  mount.appendChild(renderer.domElement);

  const ambient = new THREE.HemisphereLight(0xd8ecff, 0x241610, 1.18);
  const key = new THREE.DirectionalLight(0xfff4dc, 1.48);
  const rim = new THREE.DirectionalLight(0x6dd8ff, 0.74);
  const bossAuraLight = new THREE.PointLight(0xff5d5d, 1.8, 11, 1.7);
  key.position.set(-4.8, 7.2, 4.8);
  rim.position.set(4.5, 5.4, -6.2);
  bossAuraLight.position.set(0, 2.1, 0);
  scene.add(ambient, key, rim, bossAuraLight);

  const arena = makeArena();
  scene.add(arena.group);

  const player = makePlayer();
  const boss = makeBoss();
  scene.add(player.group, boss.group);
  let disposed = false;

  void loadGlbPlayer(player, renderer.capabilities.getMaxAnisotropy(), (model, animations) => {
    if (disposed) {
      animations.mixer?.stopAllAction();
      animations.mixer?.uncacheRoot(model);
      disposeObject3D(model);
      return;
    }

    player.characterModel = model;
    player.fbxMixer = animations.mixer;
    player.fbxActions = animations.actions;
    player.fbxActiveAction = null;
    player.characterBaseScale = model.scale.x;
    player.characterBasePosition.copy(model.position);
    player.fallbackGroup.visible = false;
    player.backCore.visible = false;
    player.backHalo.visible = false;
    player.group.add(model);

    if (player.fbxActions.idle) {
      playFbxPlayerAnimation(player, "idle", 0);
    }
  });

  const shockwaveWarning = new THREE.Group();
  const shockwaveWarningMaterial = makeGlowMaterial(0xff4438, 0);
  const shockwaveFillMaterial = makeGlowMaterial(0xff2b1f, 0);
  const shockwaveOuter = new THREE.Mesh(new THREE.RingGeometry(0.9, 1.02, 72), shockwaveWarningMaterial);
  const shockwaveInner = new THREE.Mesh(new THREE.RingGeometry(0.54, 0.6, 64), shockwaveWarningMaterial);
  const shockwaveFill = new THREE.Mesh(new THREE.CircleGeometry(0.98, 64), shockwaveFillMaterial);
  shockwaveOuter.rotation.x = -Math.PI / 2;
  shockwaveInner.rotation.x = -Math.PI / 2;
  shockwaveFill.rotation.x = -Math.PI / 2;
  shockwaveOuter.position.y = 0.07;
  shockwaveInner.position.y = 0.075;
  shockwaveFill.position.y = 0.052;
  shockwaveWarning.add(shockwaveFill, shockwaveInner, shockwaveOuter);
  shockwaveWarning.visible = false;
  scene.add(shockwaveWarning);

  const beamWarningMaterial = makeGlowMaterial(0xff493c, 0);
  const beamWarningCoreMaterial = makeGlowMaterial(0xffd0a6, 0);
  const beamWarning = new THREE.Group();
  const beamWarningWide = new THREE.Mesh(
    new THREE.BoxGeometry(0.72, 0.04, FIELD_RADIUS * 1.8),
    beamWarningMaterial,
  );
  const beamWarningCore = new THREE.Mesh(
    new THREE.BoxGeometry(0.12, 0.045, FIELD_RADIUS * 1.8),
    beamWarningCoreMaterial,
  );
  beamWarningWide.position.y = 0.08;
  beamWarningCore.position.y = 0.086;
  beamWarning.add(beamWarningWide, beamWarningCore);
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

      arena.runeGroup.rotation.y += deltaMs * 0.000045;
      arena.pulseMaterial.opacity = 0.23 + Math.sin(elapsed * 1.8) * 0.06;

      player.group.position.set(snapshot.playerPosition.x, 0, snapshot.playerPosition.z);
      player.group.rotation.y = snapshot.playerAngle;
      player.bodyMaterial.color.setHex(snapshot.isDodging ? 0xd2fff4 : 0x34c5ad);
      player.limbMaterial.color.setHex(snapshot.isDodging ? 0x9affef : 0x258d83);
      player.markerMaterial.emissive.setHex(snapshot.playerAttackPulse > 0 ? attribute.color : 0x332100);
      player.headMaterial.emissive.setHex(snapshot.isDodging ? 0x2bb59f : 0x000000);
      player.backCoreMaterial.color.setHex(snapshot.isDodging ? 0x9affef : attribute.accent);
      player.backCoreMaterial.opacity = snapshot.playerAttackPulse > 0 ? 0.95 : 0.74;
      player.backCore.scale.setScalar(1 + Math.sin(elapsed * 4.5) * 0.12 + snapshot.playerAttackPulse * 0.42);
      player.backHalo.rotation.z += deltaMs * 0.0032;
      player.backHalo.scale.setScalar(1 + snapshot.playerAttackPulse * 0.55);

      const walkSwing = Math.sin(elapsed * 10.5) * 0.42 * snapshot.playerMoveIntensity;
      const attackPulse = snapshot.playerAttackPulse;
      player.fallbackGroup.position.y = Math.sin(elapsed * 8) * 0.025 * snapshot.playerMoveIntensity;
      player.torso.rotation.x = -attackPulse * 0.18;
      player.head.rotation.x = -attackPulse * 0.08;
      player.frontMarker.scale.setScalar(1 + attackPulse * 0.55);
      player.headingMarker.scale.setScalar(1 + attackPulse * 0.35);
      player.leftArm.rotation.x = -0.22 - walkSwing * 0.65 + attackPulse * 0.6;
      player.rightArm.rotation.x = -0.22 + walkSwing * 0.65 - attackPulse * 1.2;
      player.leftArm.rotation.z = 0.22 + attackPulse * 0.26;
      player.rightArm.rotation.z = -0.22 - attackPulse * 0.26;
      player.leftLeg.rotation.x = walkSwing;
      player.rightLeg.rotation.x = -walkSwing;
      if (player.characterModel) {
        const selectedAnimation = selectFbxPlayerAnimation(player, snapshot);
        if (selectedAnimation) {
          playFbxPlayerAnimation(player, selectedAnimation);
        }

        player.fbxMixer?.update(deltaMs / 1000);

        const isMoving = snapshot.playerMoveIntensity > 0.08;
        const usesSyntheticRun = isMoving && !snapshot.isDodging && !player.fbxActions.run;
        const movePulse = Math.sin(elapsed * 11);
        const runBob = Math.sin(elapsed * 8) * (usesSyntheticRun ? 0.065 : 0.035) * snapshot.playerMoveIntensity;
        const dodgeLift = snapshot.isDodging ? 0.12 + Math.sin(elapsed * 24) * 0.035 : 0;
        player.characterModel.position.set(
          player.characterBasePosition.x,
          player.characterBasePosition.y + runBob + dodgeLift,
          player.characterBasePosition.z - attackPulse * 0.14,
        );
        player.characterModel.rotation.x = (
          -attackPulse * 0.14
          + (snapshot.isDodging ? -0.08 : 0)
          - (usesSyntheticRun ? 0.1 * snapshot.playerMoveIntensity : 0)
        );
        player.characterModel.scale.setScalar(player.characterBaseScale * (1 + attackPulse * 0.035));
        player.leftStepRing.visible = usesSyntheticRun;
        player.rightStepRing.visible = usesSyntheticRun;
        player.footstepMaterial.opacity = usesSyntheticRun ? 0.12 + Math.abs(movePulse) * 0.16 : 0;
        player.leftStepRing.position.z = 0.26 + movePulse * 0.06;
        player.rightStepRing.position.z = 0.26 - movePulse * 0.06;
        player.leftStepRing.scale.setScalar(1 + Math.max(0, movePulse) * 0.45);
        player.rightStepRing.scale.setScalar(1 + Math.max(0, -movePulse) * 0.45);
      } else {
        player.leftStepRing.visible = false;
        player.rightStepRing.visible = false;
        player.footstepMaterial.opacity = 0;
      }
      player.dodgeAura.visible = snapshot.isDodging;
      player.dodgeMaterial.opacity = snapshot.isDodging ? 0.34 : 0;
      player.dodgeAura.scale.setScalar(snapshot.isDodging ? 1.35 + Math.sin(elapsed * 28) * 0.12 : 1);

      boss.group.position.set(snapshot.bossPosition.x, 0, snapshot.bossPosition.z);
      boss.group.rotation.y += deltaMs * 0.00024;
      boss.group.position.y = Math.sin(elapsed * 2.1) * 0.06;
      boss.group.scale.setScalar(snapshot.bossHurt ? 0.94 + Math.sin(elapsed * 24) * 0.025 : 0.9);
      boss.coreMaterial.color.setHex(snapshot.bossHurt ? attribute.accent : 0xb83f4b);
      boss.coreMaterial.emissive.setHex(snapshot.bossHurt ? attribute.color : 0x180305);
      boss.shellMaterial.color.setHex(snapshot.bossHpRatio < 0.25 ? 0x4d1e25 : 0x2d2226);
      boss.hideMaterial.emissive.setHex(snapshot.bossHurt ? 0x42110f : 0x150405);
      boss.glowMaterial.color.setHex(snapshot.bossHurt ? attribute.accent : 0xff6e65);
      boss.glowMaterial.opacity = snapshot.bossHurt ? 0.95 : 0.64 + Math.sin(elapsed * 2.4) * 0.12;
      boss.eyeMaterial.color.setHex(snapshot.bossHurt ? attribute.accent : 0xffd66e);
      bossAuraLight.position.set(snapshot.bossPosition.x, 2.2, snapshot.bossPosition.z);
      bossAuraLight.color.setHex(snapshot.bossHurt ? attribute.color : 0xff5d5d);
      bossAuraLight.intensity = snapshot.bossHurt ? 2.8 : 1.45 + Math.sin(elapsed * 2.1) * 0.24;

      if (snapshot.shockwaveWarning) {
        shockwaveWarning.visible = true;
        shockwaveWarning.position.set(snapshot.bossPosition.x, 0.06, snapshot.bossPosition.z);
        shockwaveWarning.scale.setScalar(snapshot.shockwaveWarning.radius);
        shockwaveWarning.rotation.y += deltaMs * 0.0018;
        shockwaveWarningMaterial.opacity = 0.22 + snapshot.shockwaveWarning.progress * 0.64;
        shockwaveFillMaterial.opacity = 0.05 + snapshot.shockwaveWarning.progress * 0.18;
      } else {
        shockwaveWarning.visible = false;
        shockwaveWarningMaterial.opacity = 0;
        shockwaveFillMaterial.opacity = 0;
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
        beamWarningMaterial.opacity = 0.18 + snapshot.beamWarning.progress * 0.5;
        beamWarningCoreMaterial.opacity = 0.28 + snapshot.beamWarning.progress * 0.56;
      } else {
        beamWarning.visible = false;
        beamWarningMaterial.opacity = 0;
        beamWarningCoreMaterial.opacity = 0;
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
        4.55,
        snapshot.playerPosition.z + 6.2,
      );
      camera.position.lerp(targetCamera, 0.09);
      lookTarget.set(
        snapshot.playerPosition.x * 0.58 + snapshot.bossPosition.x * 0.42,
        1.02,
        snapshot.playerPosition.z * 0.58 + snapshot.bossPosition.z * 0.42,
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
      disposed = true;
      if (player.characterModel && player.fbxMixer) {
        player.fbxMixer.stopAllAction();
        player.fbxMixer.uncacheRoot(player.characterModel);
      }
      effects.forEach((effect) => effect.dispose());
      effects.splice(0, effects.length);
      mount.removeChild(renderer.domElement);
      renderer.dispose();
      disposeObject3D(scene);
    },
  };

  return sceneApi;
}
