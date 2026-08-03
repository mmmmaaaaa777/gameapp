# Mobile Boss Battle RPG Demo

スマートフォン操作に特化した、ボス戦中心の3DアクションRPGデモです。

React・TypeScript・Vite・Three.jsを使用し、ホーム画面、ボス選択、編成、装備、バトル、リザルトまでの一連のゲームフローをクライアント側だけで実装しています。

Unityなどで本制作へ進む前に、スマートフォンでの操作感、画面構成、戦闘ロジックを検証するためのプロトタイプとして開発しました。

## 主な機能

- ホームからバトル、リザルトまでの画面遷移
- スワイプ移動、タップ攻撃、フリック回避
- スキル発動と属性切り替え
- ボス戦、HP管理、戦闘結果、報酬処理
- 装備・編成・設定画面
- FBXモデルとアニメーションの読み込み
- モデル読み込み失敗時のフォールバック表示
- 戦闘計算やゲームロジックの自動テスト
- 幅375pxを基準としたスマートフォン向けUI

## 使用技術

| 分類 | 技術 |
| --- | --- |
| フロントエンド | React 19 / TypeScript |
| 3D | Three.js |
| 開発環境 | Vite |
| テスト | Vitest |
| 静的解析 | ESLint |
| スタイリング | CSS |

## セットアップ

### PowerShell

```powershell
npm.cmd install
npm.cmd run dev
```

### bash

```bash
npm install
npm run dev
```

起動後、次のURLを開きます。

```text
http://localhost:5173/
```

同じWi-Fiに接続したスマートフォンから確認する場合は、Viteが表示するNetwork URLを開いてください。

## 操作方法

| 操作 | 動作 |
| --- | --- |
| スワイプ | キャラクター移動 |
| タップ | 通常攻撃 |
| フリック | 回避 |
| 画面下部のボタン | スキル発動・属性切り替え |

バトル画面ではPointer Eventsを使用しています。

## コマンド

```bash
npm run dev
npm run test
npm run lint
npm run build
```

## ディレクトリ構成

```text
src/
├─ components/
│  ├─ BattleScreen.tsx
│  ├─ BattleHud.tsx
│  ├─ ResultScreen.tsx
│  └─ MenuScreens.tsx
├─ game/
│  └─ 戦闘計算・属性・スキル・装備・報酬ロジック
├─ three/
│  ├─ createBattleScene.ts
│  └─ effects.ts
├─ App.tsx
└─ styles.css
```

## 実装上の方針

- Three.jsを直接使用し、`@react-three/fiber`には依存しない
- 外部の画像・音声・追加モデルに依存せず、UIやエフェクトをコードとCSSで構築する
- サーバーやデータベースを持たないクライアント完結型とする
- データは一時的なstateとして保持し、リロード時に初期化する
- スマートフォン操作を優先し、バトル領域では`touch-action: none`を維持する

## 現在の制限

このリポジトリは操作感とゲームフローを検証するためのデモです。次の機能は含まれていません。

- ログイン・ユーザー管理
- Firebaseや独自APIとの連携
- データベースへの保存
- 課金
- 実際のマルチプレイ
- 本番用のサウンド・アセット管理

## 品質確認

変更後は次を実行します。

```bash
npm run test
npm run lint
npm run build
```

あわせて、幅375pxの表示で次を確認します。

- 横スクロールが発生していないこと
- コンソールエラーがないこと
- ホームへ戻れること
- バトルを再挑戦できること
- タッチ操作と画面スクロールが競合しないこと

## 今後の改善候補

- 各メニュー画面のコンポーネント分割
- 3Dアセットとチャンクの最適化
- デモ動画・スクリーンショットの追加
- CIによるtest・lint・buildの自動実行
- 公開デモ環境の用意

## License

ライセンスは未設定です。コードやアセットを再利用する場合は、事前にリポジトリ所有者へ確認してください。
