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
