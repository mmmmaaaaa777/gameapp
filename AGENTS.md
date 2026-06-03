# gameapp Three.jsデモ版 ルール

- 技術構成は React + TypeScript + Vite + Three.js。Three.jsは直接利用し、`@react-three/fiber` は追加しない。
- 開発サーバーは `npm run dev`、テストは `npm run test`、Lintは `npm run lint`、buildは `npm run build`。
- Firebase、ログイン、課金、広告、DB、外部通信、外部アセットは追加しない。
- スマホ幅375pxでの操作性を重視し、Canvasまたはバトルエリアには `touch-action: none;` を設定する。
- Pointer Eventsでタップ、スワイプ、フリックを扱い、UIボタン操作がCanvas攻撃に化けないようにする。
- HP、属性、クールダウン、討伐時間、与ダメージ、被ダメージはクライアント内の一時状態で管理する。
- 秘密情報やAPIキーを作らない。`.env` に秘密情報を入れない。
- 文字化けやその他エラーを起こした場合は、原因と対処方法をファイルにまとめる。
