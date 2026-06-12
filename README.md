# gameapp Three.js Demo

スマホ向けのボス戦RPGデモ。React + TypeScript + Vite + Three.js で、ホームからバトル、リザルトまでの一連の流れをクライアントだけで回している。Unity本番前の操作感確認用なので、Firebase・ログイン・課金・本物のマルチプレイみたいなサーバー側の仕組みは一切ない。

## 動かし方

```powershell
npm.cmd install
npm.cmd run dev
```

http://localhost:5173/ で開く。

PowerShellだと `npm` が実行ポリシーで弾かれることがあるので `npm.cmd` にしている。bashなら普通に `npm` でいい。

スマホ実機で見たいときは、PCと同じWi-Fiにつないで Vite が表示する Network のURL(`http://192.168.x.x:5173/` みたいなやつ)を開く。

そのほかのコマンド:

```powershell
npm.cmd run test    # Vitest
npm.cmd run lint    # ESLint
npm.cmd run build   # tsc + vite build
```

## 操作

バトルは Pointer Events で全部拾っている。

- スワイプ: 移動
- タップ: 攻撃
- フリック: 回避
- 画面下のボタン: スキル発動と属性切り替え

レイアウトは幅375pxを基準に作ってある。

## 画面とファイルの対応

画面遷移は [src/App.tsx](src/App.tsx) の state 管理だけ。ホーム / ボス選択 / 出撃準備 / 編成 / 装備 / 設定は [MenuScreens.tsx](src/components/MenuScreens.tsx) に全部入っている(そろそろ分割したい)。

- `src/components/BattleScreen.tsx` … バトルのReact側
- `src/components/BattleHud.tsx` … HPバーやスキルボタン
- `src/components/ResultScreen.tsx` … リザルト
- `src/three/createBattleScene.ts` … Three.jsシーン本体。FBX読み込み、ボス、カメラ、入力の反映
- `src/three/effects.ts` … 属性エフェクト
- `src/game/` … 属性・スキル定義、戦闘計算、装備、報酬まわりのロジック(ここはテストあり)
- `src/styles.css` … UI全部。色やサイズは `:root` のCSS変数にまとめてある

## 3Dモデル

`public/models/characterMedium.fbx` と `public/models/animations/` 下の idle / run / jump を使う。読み込みに失敗したら簡易人型と既存モーションにフォールバックするので、モデルがなくても一応動く。attack と dodge のFBXは使っていない。

## 縛り(意図的なもの)

- Three.js は直接使う。`@react-three/fiber` は入れない
- 外部の画像・音・モデルを足さない(エフェクトやUI質感は全部CSSとコード生成)
- データはクライアントの一時state。リロードで消えるのは仕様
- バトルエリアは `touch-action: none;` を維持する。これを外すとスマホでスクロールと攻撃が喧嘩する

## 変更したら

`test` / `lint` / `build` を回した上で、375px幅で一通り画面を見る。特に横スクロールが出ていないか、コンソールにエラーが出ていないか、ホームに戻る導線と再挑戦がちゃんと動くか。

## ハマりどころ

- PowerShellで日本語が化けるのは大体表示側の問題。`Get-Content README.md -Encoding UTF8` で読めば中身は無事
- build時に500kB超のチャンク警告が出るが、Three.jsとFBXローダーを含んでいる以上仕方ないので放置している
