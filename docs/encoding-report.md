# 文字化け原因と対処

## 発生内容

貼り付けファイル `C:\Users\t_maruyama\.codex\attachments\ddcc97a7-2668-4408-b722-009605e5707b\pasted-text.txt` を最初に通常の `Get-Content` で読んだところ、日本語が `逶ｮ逧・` のように文字化けして表示された。

## 原因

ファイル自体はUTF-8で保存されていたが、読み取り時にWindowsのShift-JIS系エンコーディングとして解釈されたため、UTF-8のバイト列が誤って表示された。

## 対処方法

以降の読み取りでは `Get-Content -Encoding UTF8` を指定して内容を確認した。実装ファイルもUTF-8前提で作成し、HTMLには `<meta charset="UTF-8" />` を設定した。

## 再発防止

- 日本語を含むファイルをPowerShellで読む場合は `-Encoding UTF8` を指定する。
- HTMLではUTF-8のmeta charsetを維持する。
- 文字化けが見えた場合は、先にバイト列とエンコーディングを確認してから作業する。

## その他エラー: npm.ps1 実行ポリシー

### 発生内容

`npm install` をPowerShellから実行したところ、`C:\Program Files\nodejs\npm.ps1 cannot be loaded because running scripts is disabled on this system` で失敗した。

### 原因

PowerShellの実行ポリシーにより、npmのPowerShellラッパー `npm.ps1` の実行が許可されていなかった。

### 対処方法

同じnpmをコマンド実行ファイル経由で呼び出すため、`npm.cmd install` を使用した。以降のnpmコマンドも `npm.cmd run ...` で実行した。

## その他エラー: build時のVitest設定型エラー

### 発生内容

`npm.cmd run build` の初回実行時に、`vite.config.ts` の `test` プロパティがViteの型に存在しないというTypeScriptエラーが発生した。

### 原因

Vitest 4系へ更新した後も `defineConfig` を `vite` からimportしていたため、Vitestの `test` 設定を含む型として解釈されていなかった。

### 対処方法

`vite.config.ts` の `defineConfig` import元を `vitest/config` に変更した。その後 `npm.cmd run build` は成功した。

## その他エラー: ブラウザ検証中のスクリーンショット取得タイムアウト

### 発生内容

Codex内蔵ブラウザの `tab.screenshot()` が `Page.captureScreenshot` のタイムアウトで失敗した。

### 原因

内蔵ブラウザ側のCDPスクリーンショット取得が不安定になっていた。DOM操作自体は復帰できたが、同じAPIでのスクリーンショット取得は継続して失敗した。

### 対処方法

開いているタブを取り直してDOM検証を継続した。スクリーンショットとCanvasピクセル確認は、既存Chromeを `playwright-core` の一時導入で起動して実行した。

## その他エラー: Playwright検証スクリプトの日本語ロール名

### 発生内容

PowerShellのインラインスクリプトから `getByRole('button', { name: '炎' })` を実行したところ、日本語名が崩れてボタンを見つけられなかった。

### 原因

PowerShellからNodeへ渡すインラインスクリプト内の日本語文字列が、実行経路で期待通りに扱われなかった。

### 対処方法

検証では属性ボタンをCSSセレクタ `button.attribute-button` と順番で指定した。アプリ本体のUI表示はブラウザ上で正常に日本語表示されている。

## その他エラー: 画像ピクセル確認スクリプトのPathInfo変換

### 発生内容

PowerShellで `System.Drawing.Bitmap` を作成する際、`Resolve-Path` の戻り値をそのまま渡して失敗した。

### 原因

`Resolve-Path` は文字列ではなく `PathInfo` を返すため、Bitmapコンストラクタの引数型と合わなかった。

### 対処方法

`(Resolve-Path $file).Path` で文字列パスを渡すように修正し、スクリーンショットのピクセル確認を再実行した。

## その他エラー: v1.1検証スクリプトのdocument参照

### 発生内容

CLEAR到達確認のNodeスクリプトで、ブラウザ内の `document` をNode側トップレベルから参照して `ReferenceError: document is not defined` が発生した。

### 原因

Playwrightの外側で実行されるNode.js環境にはDOMが存在しないため。

### 対処方法

DOM参照は `page.evaluate()` の中に移し、リザルト画面の確認と再挑戦ボタン操作をブラウザコンテキストまたはCSSセレクタ経由で行うようにした。

## その他エラー: 外部画像参照検索時のrg正規表現

### 発生内容

外部画像やCanvasテクスチャ参照の有無を `rg` で検索する際、PowerShell上の引用符と正規表現が噛み合わず `regex parse error: unclosed group` が発生した。

### 原因

`createElement(\"canvas\")` を含む複合正規表現を1本の文字列として渡したため、括弧とクォートの解釈が崩れた。

### 対処方法

`rg -e ...` で検索パターンを個別に渡す形へ変更して再実行した。

## その他エラー: FBXモデル読み込み後の非表示

### 発生内容

`public/models/characterMedium.fbx` は `FBXLoader` で読み込めていたが、ブラウザ検証スクリーンショット上ではモデル本体が表示されず、向き表示用のマーカーだけが見えていた。

### 原因

FBX内の元マテリアルが `transparent: true` かつ `opacity: 0` で読み込まれており、メッシュ自体は存在していても透明な状態だった。

### 対処方法

FBX読み込み後にメッシュを走査し、元マテリアルをdisposeしてから軽量な `MeshStandardMaterial` に置き換えた。再検証ではFBXモデル本体と、FBXが無い場合の簡易人型フォールバックの両方を確認した。

## その他エラー: run.fbx再生時のTポーズ表示

### 発生内容

`idle.fbx` と `jump.fbx` は動くが、移動中に `run.fbx` を再生するとTポーズに近い表示になった。

### 原因

`run.fbx` には複数の `AnimationClip` があり、先頭clipが短い `Root|0.Targeting Pose` だった。実際の走りclipは2本目の `Root|Run` だったが、実装が先頭clipだけを採用していた。

### 対処方法

読み込んだFBXの `animations` について、track数、duration、キャラクター骨名との対応を確認し、対象名を含む有効clipを優先して採用するようにした。run clipが空または不採用の場合は、idleを維持しながらモデル全体の上下揺れ、前傾、足元リングで移動感を補うようにした。
