import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import console from "node:console";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const modelFiles = [
  "public/models/characters/initial-male.glb",
  "public/models/characters/initial-female.glb",
];

const requiredBones = [
  "Hips",
  "Spine",
  "Chest",
  "Neck",
  "Head",
  "LeftArm",
  "LeftForeArm",
  "LeftHand",
  "RightArm",
  "RightForeArm",
  "RightHand",
  "LeftUpLeg",
  "LeftLeg",
  "LeftFoot",
  "RightUpLeg",
  "RightLeg",
  "RightFoot",
];

const requiredAnimations = ["idle", "jump", "run"];

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function loadGlb(file) {
  const buffer = fs.readFileSync(file);
  const arrayBuffer = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
  const loader = new GLTFLoader();

  return new Promise((resolve, reject) => {
    loader.parse(arrayBuffer, path.dirname(file), resolve, reject);
  });
}

for (const file of modelFiles) {
  const gltf = await loadGlb(file);
  const box = new THREE.Box3().setFromObject(gltf.scene);
  const size = box.getSize(new THREE.Vector3());
  const boneNames = new Set();
  const materialNames = new Set();
  let skinnedMeshCount = 0;
  let vertexCount = 0;
  let triangleCount = 0;

  gltf.scene.traverse((object) => {
    if (!object.isMesh) return;

    vertexCount += object.geometry.attributes.position.count;
    triangleCount += object.geometry.index
      ? object.geometry.index.count / 3
      : object.geometry.attributes.position.count / 3;

    const materials = Array.isArray(object.material) ? object.material : [object.material];
    materials.forEach((material) => materialNames.add(material.name));

    if (object.isSkinnedMesh) {
      skinnedMeshCount += 1;
      object.skeleton.bones.forEach((bone) => boneNames.add(bone.name));
    }
  });

  const animationNames = gltf.animations.map((clip) => clip.name).sort();
  assert(skinnedMeshCount > 0, `${file}: SkinnedMeshがありません`);
  assert(requiredBones.every((name) => boneNames.has(name)), `${file}: 必須ボーンが不足しています`);
  assert(
    requiredAnimations.every((name) => animationNames.includes(name)),
    `${file}: 必須アニメーションが不足しています`,
  );
  assert(size.y >= 1.6 && size.y <= 1.9, `${file}: 全高が想定範囲外です (${size.y.toFixed(3)}m)`);
  assert(box.min.y >= -0.01 && box.min.y <= 0.08, `${file}: 足元の原点がずれています`);

  console.log(
    `${file}: OK | ${vertexCount} vertices | ${Math.round(triangleCount)} triangles | ` +
      `${boneNames.size} bones | ${materialNames.size} materials | ` +
      `${animationNames.join(", ")} | ${size.y.toFixed(3)}m`,
  );
}

console.log("Character model validation passed.");
process.exitCode = 0;
