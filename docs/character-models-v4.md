# 初期キャラクター3Dモデル v4

三方向のターンアラウンド画像を Hunyuan3D-2 の選定形状へ投影し、MPFB のゲーム用リグを転送した高精細版。v4 は投影結果を UV テクスチャではなく頂点カラー `ReferenceColor` として保持する。

## 成果物

| 種別 | 男性 | 女性 |
| --- | --- | --- |
| Blender 編集用 | `art-source/characters/initial-male-v4.blend` | `art-source/characters/initial-female-v4.blend` |
| ゲーム用 GLB | `public/models/characters/initial-male-v4.glb` | `public/models/characters/initial-female-v4.glb` |

プレビューは `docs/character-concepts/model-previews/v4/` に保存している。男女それぞれ正面、右側面、背面、斜め前の4枚がある。

## 入力と位置付け

- クロップ済みターンアラウンド: `docs/character-concepts/reconstruction-inputs/{male,female}/` の `front.png`、`right.png`、`back.png`
- Hunyuan3D-2 選定形状: 男性 `male-seed-12345.glb`、女性 `female-seed-23456.glb`
- MPFB リグベース: `art-source/characters/work/v3/initial-male-base.blend`、`initial-female-base.blend`

Hunyuan3D-2 の形状を表示面として残し、MPFB ベースから 53 ボーンのスキンウェイトを近接転送する。v3 の `initial-*-v3.blend` は、人体・衣服・髪をレイヤー別に編集できる代替版として引き続き保持する。

## 構造

| 項目 | 男性 | 女性 |
| --- | ---: | ---: |
| 頂点 | 152,210 | 139,263 |
| 三角形 | 304,416 | 278,526 |
| スキンメッシュ | 1 | 1 |
| マテリアル | 1 | 1 |
| ボーン | 53 | 53 |
| 1頂点あたり最大ウェイト | 4 | 4 |
| 内蔵アニメーションクリップ | 0 | 0 |

## 再ビルド

プロジェクトルートから Blender 5.2 を通常設定で実行する。MPFB は拡張機能として読み込むため、`--factory-startup` は付けない。

MPFB リグベースも作り直す場合:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background --python scripts\generate_mpfb_character_bases_v3.py
```

現在のクロップ画像、選定済み Hunyuan3D-2 候補、MPFB リグベースから男女の v4、GLB、プレビューを再生成する:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background --python scripts\build_reference_projected_characters_v4.py
```

片方だけ再生成する場合は末尾に `-- --character male` または `-- --character female` を付ける。プレビューを省略する場合は `-- --skip-render` を付ける。

制作途中の版は上書きせず、必ず `--revision` を付けて保存する。次の例では、4方向プレビューを `docs/character-concepts/model-history/v4.14/`、BLEND と GLB をそれぞれの `history/v4.14/` へ保存し、変更メモを `build.json` に残す。

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background --python scripts\build_reference_projected_characters_v4.py `
  -- --revision v4.14 `
  --revision-note "手首と指を裾・ズボン色補正から除外し、女性の額を正面投影へ復元"
```

版別 GLB の検証:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background --python scripts\validate_character_glbs_v4.py `
  -- --revision v4.14
```

## 検証範囲と制約

ビルド時には、10万頂点以上の形状、単一マテリアル、POINT ドメインの頂点カラー、単一 Armature モディファイア、全頂点のウェイト付与、最大4ウェイトを Blender シーン上で確認する。

ただし、選定済み Hunyuan3D-2 候補そのものの再生成、書き出した GLB の再読込、各ポーズでの変形・貫通、投影色の見た目、LOD や端末性能は自動検証しない。アニメーションクリップも含まないため、既存モーションのリターゲットは別工程となる。

## アプリ統合状況

現在のアプリは `src/three/createBattleScene.ts` で `/models/characterMedium.fbx` と FBX 形式の `idle`、`run`、`jump` を読み込んでいる。v4 GLB への切り替え、ローダー統合、既存モーションのリターゲットは未実施であり、本成果物の作成範囲には含まれない。
