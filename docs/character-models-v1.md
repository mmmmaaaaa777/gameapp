# 初期キャラクター3Dモデル v1

`docs/character-concepts/` の正面・右側面・背面の設定画を基準に、Blender 5.2で作成した軽量な初期プレイヤーモデル。

## ゲーム用ファイル

- 男性: `public/models/characters/initial-male.glb`
- 女性: `public/models/characters/initial-female.glb`

Three.jsでは`GLTFLoader`で読み込む。GLBにはメッシュ、マテリアル、人型リグ、アニメーションがすべて含まれている。

## Blender編集用ファイル

- 男性: `art-source/characters/initial-male.blend`
- 女性: `art-source/characters/initial-female.blend`

`.blend`はViteの公開対象に含めないため、`public/`とは分離している。

## モデル仕様

| 項目 | 男性 | 女性 |
| --- | ---: | ---: |
| GLBサイズ | 約272KB | 約281KB |
| 三角形 | 4,588 | 4,848 |
| GLB頂点 | 3,555 | 3,692 |
| ボーン | 21 | 21 |
| 全高 | 約1.81m | 約1.67m |
| マテリアル | 10 | 10 |

- 単一のスキンメッシュを素材ごとの10プリミティブとして格納
- Aポーズをバインドポーズとして使用
- ボーン名は既存FBXに合わせて`Hips`、`Spine`、`LeftArm`、`LeftUpLeg`などを採用
- Blender上ではZ-up・-Y前方。GLB出力時にThree.js向けY-upへ変換
- テクスチャ画像は使わず、軽量なPBRマテリアルだけで配色

## 内蔵アニメーション

| クリップ | 長さ | 用途 |
| --- | ---: | --- |
| `idle` | 約2.03秒 | 待機時の呼吸と重心移動 |
| `run` | 約0.83秒 | 左右交互の走行サイクル |
| `jump` | 約1.53秒 | 予備動作、上昇、着地 |

## 再生成

PowerShellでプロジェクト直下から実行する。

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background --python scripts\generate_initial_characters.py
```

生成スクリプトは外部モデルや外部テクスチャを取得せず、Blenderのプリミティブだけから男女モデル、GLB、プレビューを再構築する。

## Three.js読込例

```ts
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const loader = new GLTFLoader();
loader.load("/models/characters/initial-male.glb", (gltf) => {
  scene.add(gltf.scene);

  const mixer = new THREE.AnimationMixer(gltf.scene);
  const idle = THREE.AnimationClip.findByName(gltf.animations, "idle");
  if (idle) mixer.clipAction(idle).play();
});
```

## プレビュー

- `docs/character-concepts/model-previews/initial-male-model-preview.png`
- `docs/character-concepts/model-previews/initial-female-model-preview.png`
