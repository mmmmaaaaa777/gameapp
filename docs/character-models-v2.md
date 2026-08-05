# 初期キャラクター3Dモデル v2

`docs/character-concepts/initial-*-turnaround.png`の三面図を基準に、v1のプリミティブ人形構造を全面的に作り直したスタイライズド・リアル寄りモデル。

## 成果物

### ゲーム用GLB

- 男性: `public/models/characters/initial-male-v2.glb`
- 女性: `public/models/characters/initial-female-v2.glb`

### Blender編集用

- 男性: `art-source/characters/initial-male-v2.blend`
- 女性: `art-source/characters/initial-female-v2.blend`

### プレビュー

`docs/character-concepts/model-previews/v2/`に、男女それぞれ次の4枚を保存している。

- 正面・右側面・背面の同縮尺オルソ表示
- 斜め前からのビューティー表示

## v1からの主な変更

| 項目 | v1 | v2 |
| --- | --- | --- |
| 形状 | 分割プリミティブ中心 | 断面リングから作る滑らかな人体・衣服 |
| 男性三角形 | 4,588 | 25,600 |
| 女性三角形 | 4,848 | 25,304 |
| 手 | ミトン状 | 左右5本指を個別造形 |
| 顔 | 球と箱による記号表現 | 顎形状、鼻梁・鼻先、白目・虹彩・瞳、眉、上下唇 |
| 髪 | 単一キャップ | 男性の前髪束、女性のレイヤードボブ |
| 衣服 | 単純な胴体形状 | 非対称前合わせ、留め具、二重ベルト／帯、前後パネル |
| ブーツ | 角丸箱 | 足首・踵・中足・爪先の断面から造形 |
| ウェイト | 全頂点が単一ボーン100% | 約25%の頂点を複数ボーンでブレンド |
| 色 | sRGB値を直接使用 | sRGBからscene-linearへ変換してGLB色を一致 |

## 検証結果

| 項目 | 男性 | 女性 |
| --- | ---: | ---: |
| GLBサイズ | 約902KiB | 約887KiB |
| GLB頂点 | 14,067 | 13,801 |
| 三角形 | 25,600 | 25,304 |
| ボーン | 21 | 21 |
| マテリアル | 14 | 14 |
| 全高 | 1.771m | 1.675m |
| 複数ボーンウェイト | 25.0% | 25.5% |

- `idle`、`run`、`jump`を内蔵
- Three.js `GLTFLoader`で再読込済み
- 全頂点の位置・ウェイトが有限値
- 全アニメーションを5時点ずつ評価し、メッシュ飛散なし
- Blender GLBエクスポーターのmesh validation警告なし

## 再生成

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background --python scripts\generate_realistic_characters.py
```

## 三方向プレビューの再生成

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background --factory-startup `
  --python scripts\render_character_v2_turnarounds.py
```

## 構造検証

```powershell
node scripts\validate_character_models_v2.mjs
```

## 表現範囲

このv2はスマホゲーム向けの軽量なスタイライズド・リアルモデルであり、人体スキャンを用いたフォトリアルモデルではない。Blender編集用ファイルを残しているため、顔の彫刻、手描きテクスチャ、髪カード、衣服の皺などは後続工程で非破壊的に追加できる。
