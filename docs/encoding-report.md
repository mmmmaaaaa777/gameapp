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

## その他エラー: Playwright検証スクリプトの日本語正規表現化け

### 発生内容

選択状態の375px確認用にPowerShellのインラインスクリプトからNode.jsを実行したところ、`getByRole('button', { name: /出撃/ })` などの日本語正規表現が ` /??/ ` のように崩れ、`SyntaxError: Invalid regular expression: /??/: Nothing to repeat` が発生した。

### 原因

PowerShellのヒア文字列を標準入力経由でNode.jsへ渡す実行経路で、日本語を含む正規表現リテラルが期待したUTF-8として扱われず、疑問符へ置換されたため。

### 対処方法

検証スクリプト内の日本語文字列はUnicodeエスケープ表記に変更し、正規表現リテラルではなく `new RegExp(...)` と文字列指定を使って再実行する。

## その他エラー: Playwrightモジュール未導入

### 発生内容

選択状態の375px確認用にNode.jsから `require('playwright')` を実行したところ、`Error: Cannot find module 'playwright'` が発生した。

### 原因

このプロジェクトの `node_modules` にはPlaywrightがインストールされておらず、ローカルの検証スクリプトから直接読み込めなかったため。

### 対処方法

アプリ本体へ新しい依存は追加せず、利用可能なブラウザ検証ツールまたは既存の開発サーバーと手動確認に切り替える。外部依存を追加しない方針を維持する。

## その他エラー: ブラウザ検証APIのnetworkidle非対応

### 発生内容

 in-app browser の検証APIで `waitForLoadState({ state: 'networkidle' })` を実行したところ、`playwright_wait_for_load_state does not support networkidle` が発生した。

### 原因

このブラウザ検証環境では、通常のPlaywrightで使える `networkidle` 待機がサポートされていなかったため。

### 対処方法

`load` または `domcontentloaded` を使って待機し、必要に応じて短い追加待機とDOM状態確認で画面が描画済みか確認する。

## その他エラー: ブラウザ検証でlocalStorage投入不可

### 発生内容

v3.1.1の375px確認で作成可能装備の状態を作るため、in-app browser の `evaluate()` から `localStorage.setItem(...)` を呼んだところ、`Cannot read properties of undefined (reading 'setItem')` が発生した。続けて `javascript:` URLで同じ状態投入を試したところ、ブラウザ安全ポリシーにより拒否された。

### 原因

このブラウザ検証環境のページ評価は読み取り用途に制限されており、localStorageへの直接書き込みや `javascript:` URLによる状態変更は許可されていないため。

### 対処方法

ブラウザ検証では通常の画面操作で到達できる範囲を確認する。作成可能判定そのものは `getCraftableEquipmentIds()` のユニットテストで確認し、ブラウザ側では実際の報酬ループ後に装備画面へ遷移できることを確認する。

## その他エラー: ブラウザ検証のロールクリックタイムアウト

### 発生内容

v3.2の375px確認で、リザルト画面の `装備を確認` ボタンを `getByRole` 経由でクリックしたところ、ブラウザ検証APIのCDPコマンドがタイムアウトした。

### 原因

対象ボタンはDOM上に存在していたが、in-app browserのロール解決またはクリック待機が一時的に不安定になり、通常のPlaywrightロケータ操作が完了しなかったため。

### 対処方法

DOM読み取りで対象ボタンの矩形と表示状態を確認し、同じボタンを座標クリックで操作した。クリック後は画面テキストとボタン状態を再取得して、装備画面への遷移とLv5強化表示を確認した。
