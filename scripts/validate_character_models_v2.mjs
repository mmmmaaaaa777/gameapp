import console from "node:console";
import fs from "node:fs";
import path from "node:path";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const models = [
  {
    file: "public/models/characters/initial-male-v2.glb",
    heightRange: [1.72, 1.9],
  },
  {
    file: "public/models/characters/initial-female-v2.glb",
    heightRange: [1.62, 1.78],
  },
];

const requiredBones = [
  "Hips",
  "Spine",
  "Chest",
  "UpperChest",
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
const requiredMaterialRoles = [
  "skin",
  "hair",
  "teal",
  "charcoal",
  "linen",
  "leather",
  "bronze",
  "eye",
];

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function loadGlb(file) {
  const buffer = fs.readFileSync(file);
  const arrayBuffer = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
  const loader = new GLTFLoader();

  const gltf = await new Promise((resolve, reject) => {
    loader.parse(arrayBuffer, `${path.dirname(file)}/`, resolve, reject);
  });

  return { buffer, gltf };
}

function countTriangles(geometry) {
  if (geometry.index) return geometry.index.count / 3;
  return geometry.attributes.position.count / 3;
}

for (const model of models) {
  const { buffer, gltf } = await loadGlb(model.file);
  const box = new THREE.Box3().setFromObject(gltf.scene);
  const size = box.getSize(new THREE.Vector3());
  const boneNames = new Set();
  const materialNames = new Set();
  let meshCount = 0;
  let skinnedMeshCount = 0;
  let vertexCount = 0;
  let triangleCount = 0;
  let invalidNumbers = 0;
  let weightedVertexCount = 0;
  let blendedVertexCount = 0;

  gltf.scene.traverse((object) => {
    if (!object.isMesh) return;

    meshCount += 1;
    const { geometry } = object;
    const positions = geometry.attributes.position;
    vertexCount += positions.count;
    triangleCount += countTriangles(geometry);

    for (const value of positions.array) {
      if (!Number.isFinite(value)) invalidNumbers += 1;
    }

    const materials = Array.isArray(object.material) ? object.material : [object.material];
    materials.forEach((material) => materialNames.add(material.name.toLowerCase()));

    if (!object.isSkinnedMesh) return;
    skinnedMeshCount += 1;
    object.skeleton.bones.forEach((bone) => boneNames.add(bone.name));

    const weights = geometry.attributes.skinWeight;
    if (!weights) return;

    for (let vertex = 0; vertex < weights.count; vertex += 1) {
      let sum = 0;
      let influences = 0;

      for (let component = 0; component < weights.itemSize; component += 1) {
        const weight = weights.array[vertex * weights.itemSize + component];
        sum += weight;
        if (weight > 0.001) influences += 1;
      }

      if (sum > 0.001) weightedVertexCount += 1;
      if (influences >= 2) blendedVertexCount += 1;
      if (Math.abs(sum - 1) > 0.002) invalidNumbers += 1;
    }
  });

  const animationNames = gltf.animations.map((clip) => clip.name).sort();
  const blendedRatio = weightedVertexCount > 0 ? blendedVertexCount / weightedVertexCount : 0;

  assert(buffer.length <= 25 * 1024 * 1024, `${model.file}: GLBが25MiBを超えています`);
  assert(meshCount > 0 && meshCount <= 32, `${model.file}: draw call相当のメッシュ数が不適切です`);
  assert(skinnedMeshCount > 0, `${model.file}: SkinnedMeshがありません`);
  assert(vertexCount >= 8_000, `${model.file}: v2として頂点密度が不足しています`);
  assert(triangleCount >= 12_000, `${model.file}: v2として形状密度が不足しています`);
  assert(triangleCount <= 120_000, `${model.file}: モバイル向け上限を超えています`);
  assert(invalidNumbers === 0, `${model.file}: 座標またはウェイトに不正値があります`);
  assert(weightedVertexCount > 0, `${model.file}: 有効なスキンウェイトがありません`);
  assert(blendedRatio >= 0.015, `${model.file}: 関節のブレンドウェイトが不足しています`);
  assert(requiredBones.every((name) => boneNames.has(name)), `${model.file}: 必須ボーンが不足しています`);
  assert(
    requiredAnimations.every((name) => animationNames.includes(name)),
    `${model.file}: 必須アニメーションが不足しています`,
  );
  assert(
    requiredMaterialRoles.every((role) => [...materialNames].some((name) => name.includes(role))),
    `${model.file}: 設定画を構成する必須マテリアルが不足しています`,
  );
  assert(
    size.y >= model.heightRange[0] && size.y <= model.heightRange[1],
    `${model.file}: 全高が想定範囲外です (${size.y.toFixed(3)}m)`,
  );
  assert(box.min.y >= -0.015 && box.min.y <= 0.08, `${model.file}: 足底と原点がずれています`);

  for (const clip of gltf.animations) {
    assert(clip.duration > 0 && Number.isFinite(clip.duration), `${model.file}: 無効なアニメーション時間です`);
    for (const track of clip.tracks) {
      assert([...track.values].every(Number.isFinite), `${model.file}: animation trackに不正値があります`);
    }

    const mixer = new THREE.AnimationMixer(gltf.scene);
    const action = mixer.clipAction(clip);
    action.play();
    for (const ratio of [0, 0.25, 0.5, 0.75, 1]) {
      mixer.setTime(clip.duration * ratio);
      gltf.scene.updateMatrixWorld(true);
      const animatedBox = new THREE.Box3().setFromObject(gltf.scene);
      const animatedSize = animatedBox.getSize(new THREE.Vector3());
      assert(
        animatedSize.toArray().every(Number.isFinite),
        `${model.file}: ${clip.name}の変形後boundsが不正です`,
      );
      assert(
        animatedSize.x <= 2.0 && animatedSize.y <= 3.0 && animatedSize.z <= 2.0,
        `${model.file}: ${clip.name}でメッシュが異常に飛散しています`,
      );
    }
    action.stop();
    mixer.uncacheRoot(gltf.scene);
  }

  console.log(
    `${model.file}: OK | ${(buffer.length / 1024).toFixed(0)}KiB | ${vertexCount} vertices | ` +
      `${Math.round(triangleCount)} triangles | ${boneNames.size} bones | ${materialNames.size} materials | ` +
      `${(blendedRatio * 100).toFixed(1)}% blended | ${animationNames.join(", ")} | ${size.y.toFixed(3)}m`,
  );
}

console.log("Detailed v2 character validation passed.");
