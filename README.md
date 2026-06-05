# gameapp Three.js Demo

React + TypeScript + Vite + Three.js で作成した、スマホ向けファンタジーRPG風の協力ボス戦デモです。

ホーム、ボス選択、出撃準備、編成、装備、設定、バトル、リザルトの一連の導線を React state だけで動かしています。Firebase、DB、ログイン、課金、広告、本物のマルチプレイは入れていません。

## 環境

- Node.js
- npm
- Windows PowerShell の場合、npm は `npm.cmd` で実行すると安全です。

## セットアップ

```powershell
npm.cmd install
```

## 起動方法

```powershell
npm.cmd run dev
```

Vite の開発サーバーが起動します。

通常は以下のURLで確認できます。

```text
http://localhost:5173/
```

スマホ実機で確認する場合は、PCとスマホを同じネットワークに接続し、Viteの表示に出る Network URL またはPCのローカルIPを使ってアクセスしてください。

例:

```text
http://192.168.x.x:5173/
```

## よく使うコマンド

```powershell
npm.cmd run dev
npm.cmd run test
npm.cmd run lint
npm.cmd run build
npm.cmd audit
```

内容:

- `npm.cmd run dev`: 開発サーバー起動
- `npm.cmd run test`: Vitest 実行
- `npm.cmd run lint`: ESLint 実行
- `npm.cmd run build`: TypeScriptチェック + Viteビルド
- `npm.cmd audit`: 依存関係の脆弱性確認

## 操作方法

バトル画面では Pointer Events で操作します。

- スワイプ: 移動
- タップ: 攻撃
- フリック: 回避
- スキルボタン: スキル発動
- 属性ボタン: 属性切り替え

スマホ幅375pxを主な確認基準にしています。

## 画面構成

- ホーム
- ボス選択
- 出撃準備
- 編成
- 装備
- 設定
- バトル
- リザルト

画面遷移は `src/App.tsx` の React state で管理しています。

## 主要ファイル

- `src/App.tsx`: 画面遷移と全体state
- `src/components/MenuScreens.tsx`: ホーム、ボス選択、出撃準備、編成、装備、設定
- `src/components/BattleScreen.tsx`: バトル画面のReact側
- `src/components/BattleHud.tsx`: バトルHUD
- `src/components/ResultScreen.tsx`: リザルト画面
- `src/three/createBattleScene.ts`: Three.jsシーン、FBXモデル、ボス、カメラ、操作反映
- `src/three/effects.ts`: 属性エフェクト
- `src/game/constants.ts`: 属性、スキルなどの定義
- `src/game/menu.ts`: メニュー画面用の仮データ
- `src/styles.css`: 画面全体のUI/CSS

## 3Dモデルとアニメーション

以下のFBXを使用します。

```text
public/models/characterMedium.fbx
public/models/animations/idle.fbx
public/models/animations/run.fbx
public/models/animations/jump.fbx
```

モデルやアニメーションが読み込めない場合は、簡易人型や既存モーションにフォールバックします。

`attack.fbx` と `dodge.fbx` は参照しません。

## 実装上の方針

- Three.jsは直接利用します。
- `@react-three/fiber` は使いません。
- 外部画像、外部音声、外部3Dモデルの追加はしません。
- Firebase、ログイン、DB、課金、広告、本物のマルチプレイは追加しません。
- バトルやメニューのデータはクライアント内の一時stateで扱います。
- Canvasまたはバトルエリアはスマホ操作のため `touch-action: none;` を維持します。

## 検証メモ

変更後は最低限以下を実行してください。

```powershell
npm.cmd run test
npm.cmd run lint
npm.cmd run build
npm.cmd audit
```

375px幅で確認したい項目:

- ホーム画面
- ボス選択画面
- 出撃準備画面
- 編成画面
- 装備画面
- 設定画面
- バトル画面
- リザルト画面
- ホームへ戻る導線
- 同じボスに再挑戦
- 横スクロールなし
- コンソールエラーなし

## トラブルシュート

### PowerShellでnpmが実行できない

`npm` ではなく `npm.cmd` を使ってください。

```powershell
npm.cmd run dev
```

### 日本語がPowerShell上で文字化けする

ブラウザ表示が正常なら、PowerShell側の文字コード表示だけが原因のことがあります。ファイル内容を確認する場合はUTF-8を指定してください。

```powershell
Get-Content README.md -Encoding UTF8
```

### Viteのbuildで500kB超チャンク警告が出る

Three.jsやFBX関連を含むため、現状では警告が出ます。ビルドが成功していれば実行自体は可能です。
