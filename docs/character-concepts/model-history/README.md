# キャラクター3Dモデル 制作履歴

同じプレビュー名へ上書きされていた途中画像を、Codexセッションに埋め込まれた確認時点のPNGから復元した履歴。画像を再生成・加工したものではなく、当時実際に目視確認したバイト列をそのまま保存している。

> 注意: レンダリングされてもチャット上で目視しなかった方向はセッションに埋め込まれていないため、版によって方向画像の枚数が異なる。今後の版は生成時点で全方向を版別保存する。

## 一覧

| 版 | 判定 | 内容 | 保存画像 |
| --- | --- | --- | ---: |
| [v1.0](#v10) | 旧版 | 初期軽量モデル | 2 |
| [v2.0](#v20) | 不採用 | v2 初回造形 | 2 |
| [v2.1](#v21) | 不採用 | 断面リング修正 | 2 |
| [v2.2](#v22) | 候補 | 脚・髪・衣装接続修正 | 2 |
| [v2.3](#v23) | 診断 | 右側面 QA | 2 |
| [v2.4](#v24) | 旧版 | v2 最終多方向確認 | 4 |
| [v3.0](#v30) | 不採用 | MPFB 高密度版の初回 | 3 |
| [v3.1](#v31) | 候補 | スパイク修正 | 3 |
| [v3.2](#v32) | 候補 | 男性シルエット再設計 | 3 |
| [v3.3](#v33) | 候補 | 衣装の断面中心補正 | 3 |
| [v3.4](#v34) | 候補 | 男性立ち姿と首回り | 2 |
| [v3.5](#v35) | 不採用 | 女性高密度版の初回 | 3 |
| [v3.6](#v36) | 候補 | 女性ボブと体型調整 | 3 |
| [v3.7](#v37) | 候補 | 女性シルエット部品再設計 | 3 |
| [v3.8](#v38) | 候補 | 女性衣装の監査修正 | 3 |
| [v3.9](#v39) | 保持 | 女性背面被覆の修正 | 2 |
| [v4.0](#v40) | 不採用 | 三方向投影の初回 | 3 |
| [v4.1](#v41) | 候補 | 輪郭追従投影 | 3 |
| [v4.2](#v42) | 候補 | 男女共通投影処理 | 4 |
| [v4.3](#v43) | 診断 | v3/v4 横並び監査 | 2 |
| [v4.4](#v44) | 候補 | 裾・腰色補正 | 8 |
| [v4.5](#v45) | 不採用 | 背景差分拡張テスト | 6 |
| [v4.6](#v46) | 候補 | 背景除去ロールバック | 4 |
| [v4.7](#v47) | 診断 | 腕全体の前後投影診断 | 4 |
| [v4.8](#v48) | 診断 | 腕部位別・袖クランプ比較 | 6 |
| [v4.9](#v49) | 診断 | 女性の腕部位別投影 | 4 |
| [v4.10](#v410) | 診断 | 髪の背景漏れ診断 | 2 |
| [v4.11](#v411) | 候補 | 男性の袖領域分離版 | 4 |
| [v4.12](#v412) | 不採用 | 女性の固定幅袖補助投影 | 4 |
| [v4.13](#v413) | 旧版 | 女性の袖領域分離版 | 4 |
| [v4.14](#v414) | 不採用 | 手首と指を裾・ズボン色補正から除外し、女性の額を正面投影へ復元 | 8 |
| [v4.15](#v415) | 不採用 | 手領域の上限をAポーズの実位置まで広げ、手首の青緑ブロックと黒い指先を補正 | 8 |
| [v4.16](#v416) | 不採用 | 遠位の手指に残る暗色投影を肌色へ補正し、黒い指先を除去 | 8 |
| [v5.0](#v50) | 不採用 | 投影・頂点色を廃止。骨領域別PBR材質と別メッシュの顔・衣装ディテールを検証する初回診断版。 | 4 |
| [v5.1](#v51) | 不採用 | v5.0の生成眼球を廃止。MPFBのUV付き頭部・手・眼・眉・睫毛を再構成衣装と統合し、腕材質帯を再設計。 | 4 |
| [v5.2](#v52) | 不採用 | bmesh面削除へ修正し、衣装面数下限を追加。MPFB頭部・手と再構成衣装のハイブリッドを再検証。 | 4 |
| [v5.3](#v53) | 不採用 | MPFB頭部を再構成頭部内へ三軸フィットし、左右の手を手首—指先方向で回転・拡縮して衣装へ接続。 | 4 |
| [v5.4](#v54) | 不採用 | 再構成側の手面を全削除し、MPFB手を幾何学的な上下端で下向き接続。顔面・耳だけを残し頭頂・後頭・首面を除外。 | 4 |
| [v5.5](#v55) | 不採用 | MPFB手の移植を廃止。再構成手を衣装と連続したまま肌PBR化し、MPFBは顔面・眼・眉・睫毛だけを使用。 | 4 |
| [v5.6](#v56) | 不採用 | 眼球以外の移植顔パーツを除外。手甲・靴口を材質帯で復元し、前裾縁と帯金具を別メッシュ追加。 | 4 |
| [v5.7](#v57) | 不採用 | 浮いた前裾線を削除。靴口金属帯を細線化し、男性の側頭・後頭髪境界を上げて顎周辺を顔面へ戻す。 | 4 |
| [v5.8](#v58) | 不採用 | 顔面移植を廃止し一体再構成頭部へ復帰。極薄・小型の眼球と虹彩のみ別メッシュ化して背面透けと首切断面を除去。 | 4 |
| [v6.0](v6.0-hair-audition/) | 選定 | 男女の髪型候補を三方向で比較 | 24 |
| [v6.1](v6.1-clothing-audition/) | 選定 | 衣装・長袖・靴候補を比較 | 25 |
| [v6.2](v6.2/) | 不採用 | 実メッシュ初回。二重肩・針状髪・前合わせを診断 | 4 |
| [v6.3](v6.3/) | 不採用 | 髪と前合わせを修正、上袖と靴底を再診断 | 4 |
| [v6.4](v6.4/) | 不採用 | 女性全身を追加、男女の袖境界を監査 | 8 |
| [v6.5](v6.5/) | 不採用 | 追加上袖と女性前髪を再構成 | 8 |
| [v6.6](v6.6/) | 不採用 | 女性の目周りと肩境界を再監査 | 4 |
| [v6.7](v6.7/) | 不採用 | 女性長袖トポロジーの初回抽出 | 4 |
| [v6.8](v6.8/) | 不採用 | 女性専用長袖と切替バンドを検証 | 4 |
| [v6.9](v6.9/) | 不採用 | 男女別袖を採用、男性二重肩を検出 | 8 |
| [v6.10](v6.10/) | 不採用 | 連続衣装の材質分割と512px PBR化 | 8 |
| [v6.11](v6.11/) | 不採用 | 女性長袖復元と一体型立ち襟 | 8 |
| [v6.12](v6.12/) | 不採用 | 襟の再採寸と袖切替被覆 | 8 |
| [v6.13](v6.13/) | 不採用 | 四方向候補。GLBへ編集ヘルパー混入 | 8 |
| [v6.14](v6.14/) | 不採用 | ヘルパー除去。GLBジョイント上限差を検出 | 10 |
| [v6.15](v6.15/) | 不採用 | バインド姿勢と最大4ジョイントを確定 | 10 |
| [v6.16](v6.16/) | 不採用 | 皮膚Alpha修正。女性衣装下の皮膚露出を検出 | 8 |
| [v6.17](v6.17/) | 不採用 | 女性衣装の法線オフセットを検証 | 4 |
| [v6.18](v6.18/) | 不採用 | 衣服内の隠れた体表面を除去 | 4 |
| [v6.19](v6.19/) | 不採用 | 女性裾シームと深度を調整 | 4 |
| [v6.20](v6.20/) | 旧技術候補 | リグ・GLB・ゲーム統合を通過。外観完成版としては不採用 | 12 |
| [v7.0](v7.0/) | 不採用 | 広い造形毛束の初回。針状・房状髪 | 6 |
| [v7.1](v7.1/) | 不採用 | short03。片目隠れと髪色不整合 | 6 |
| [v7.2](v7.2/) | 不採用 | Hunyuanハイブリッド。手の重複と首境界破綻 | 6 |
| [v7.3](v7.3/) | 不採用 | 立体眼を追加。髪が帽子状 | 6 |
| [v7.4](v7.4/) | 不採用 | 衣装構造追加。内襟が過大 | 6 |
| [v7.5](v7.5/) | 不採用 | 男性候補、女性ボブが片目を隠す | 12 |
| [v7.6](v7.6/) | 不採用 | 前髪処理で顔面穴と腕欠落 | 6 |
| [v7.7](v7.7/) | 候補 | 女性ポニーテールと袖を復元 | 6 |
| [v7.8](v7.8/) | 不採用 | 4動作統合。額黒点、眼球黒潰れ、襟交差 | 12 |
| [v7.9](v7.9/) | 不採用 | 透過顔部品除去。短い眉と片目隠れ | 12 |
| [v7.10](v7.10/) | 不採用 | 不透明髪へ復帰。眼球外縁の黒欠け | 12 |
| [v7.11](v7.11/) | 不採用 | 眼球を修正。GLB再読込で女性髪に横縞 | 14 |
| [v7.12](v7.12/) | 不採用 | 不透明毛流れ。前髪下に色帯 | 12 |
| [v7.13](v7.13/) | 不採用 | アルファクリップ。額黒点と髪際ギザつき | 12 |
| [v7.14](v7.14/) | **採用** | 6方向・GLB再読込・4動作・PC/375pxゲーム表示を通過 | 18 |

v7の判定理由と検証値は[「v7 キャラクターモデル制作記録」](../../character-models-v7.md)にまとめている。

## v1 系

<a id="v10"></a>

### v1.0 — 初期軽量モデル

- 判定: 旧版
- 確認時刻: 2026-08-04T00:58:35.266Z
- 変更内容: 単純形状で構成した最初の男女モデル。リグとゲーム読込の成立を優先。

![v1.0 female-preview](v1.0/female-preview.png)

![v1.0 male-preview](v1.0/male-preview.png)

## v2 系

<a id="v20"></a>

### v2.0 — v2 初回造形

- 判定: 不採用
- 確認時刻: 2026-08-04T01:56:41.812Z
- 変更内容: 顔・指・衣装・髪を高密度化した初回。断面リングのねじれが残る。

![v2.0 female-preview](v2.0/female-preview.png)

![v2.0 male-preview](v2.0/male-preview.png)

<a id="v21"></a>

### v2.1 — 断面リング修正

- 判定: 不採用
- 確認時刻: 2026-08-04T02:02:49.019Z
- 変更内容: 袖とズボンのねじれを修正した途中確認。

![v2.1 female-preview](v2.1/female-preview.png)

![v2.1 male-preview](v2.1/male-preview.png)

<a id="v22"></a>

### v2.2 — 脚・髪・衣装接続修正

- 判定: 候補
- 確認時刻: 2026-08-04T02:05:39.361Z
- 変更内容: 脚の肌抜けを解消し、ズボンを足首まで連続化。髪型も再調整。

![v2.2 female-preview](v2.2/female-preview.png)

![v2.2 male-preview](v2.2/male-preview.png)

<a id="v23"></a>

### v2.3 — 右側面 QA

- 判定: 診断
- 確認時刻: 2026-08-04T02:10:57.903Z
- 変更内容: 頭身、襟、前合わせ、ブーツ、手を右側面から検査。

![v2.3 female-right-side](v2.3/female-right-side.png)

![v2.3 male-right-side](v2.3/male-right-side.png)

<a id="v24"></a>

### v2.4 — v2 最終多方向確認

- 判定: 旧版
- 確認時刻: 2026-08-04T02:13:50.400Z
- 変更内容: v2 の正面・右側面を男女同条件で比較した最終確認。

![v2.4 female-front](v2.4/female-front.png)

![v2.4 female-right-side](v2.4/female-right-side.png)

![v2.4 male-front](v2.4/male-front.png)

![v2.4 male-right-side](v2.4/male-right-side.png)

## v3 系

<a id="v30"></a>

### v3.0 — MPFB 高密度版の初回

- 判定: 不採用
- 確認時刻: 2026-08-04T03:28:32.090Z
- 変更内容: MPFB 人体と別メッシュ衣装の初回。髪・縁取り・脚にスパイク変形あり。

![v3.0 male-back](v3.0/male-back.png)

![v3.0 male-front](v3.0/male-front.png)

![v3.0 male-three-quarter](v3.0/male-three-quarter.png)

<a id="v31"></a>

### v3.1 — スパイク修正

- 判定: 候補
- 確認時刻: 2026-08-04T03:44:45.488Z
- 変更内容: 厚み付けとモディファイア確定範囲を修正し、髪・襟・ブーツ・素材を再構築。

![v3.1 male-back](v3.1/male-back.png)

![v3.1 male-front](v3.1/male-front.png)

![v3.1 male-three-quarter](v3.1/male-three-quarter.png)

<a id="v32"></a>

### v3.2 — 男性シルエット再設計

- 判定: 候補
- 確認時刻: 2026-08-04T03:51:12.687Z
- 変更内容: 頭頂、前髪、裾パネル、白飛び、箱型つま先を修正。

![v3.2 male-back](v3.2/male-back.png)

![v3.2 male-front](v3.2/male-front.png)

![v3.2 male-three-quarter](v3.2/male-three-quarter.png)

<a id="v33"></a>

### v3.3 — 衣装の断面中心補正

- 判定: 候補
- 確認時刻: 2026-08-04T04:00:24.478Z
- 変更内容: 首・胸・腰の実断面へ襟、前立て、帯、裾を密着。

![v3.3 male-back](v3.3/male-back.png)

![v3.3 male-front](v3.3/male-front.png)

![v3.3 male-three-quarter](v3.3/male-three-quarter.png)

<a id="v34"></a>

### v3.4 — 男性立ち姿と首回り

- 判定: 候補
- 確認時刻: 2026-08-04T04:04:54.579Z
- 変更内容: レスト姿勢を保った腕下げ、襟開口、肌色、髪、留め具を調整。

![v3.4 male-front](v3.4/male-front.png)

![v3.4 male-three-quarter](v3.4/male-three-quarter.png)

<a id="v35"></a>

### v3.5 — 女性高密度版の初回

- 判定: 不採用
- 確認時刻: 2026-08-04T04:11:23.909Z
- 変更内容: 衣装は成立したが、直線的なボブと広い肩幅が課題。

![v3.5 female-back](v3.5/female-back.png)

![v3.5 female-front](v3.5/female-front.png)

![v3.5 female-three-quarter](v3.5/female-three-quarter.png)

<a id="v36"></a>

### v3.6 — 女性ボブと体型調整

- 判定: 候補
- 確認時刻: 2026-08-04T04:22:31.536Z
- 変更内容: ボブの面密度、毛先幅、分け目、頭身、肩、腕、脚を再調整。

![v3.6 female-back](v3.6/female-back.png)

![v3.6 female-front](v3.6/female-front.png)

![v3.6 female-three-quarter](v3.6/female-three-quarter.png)

<a id="v37"></a>

### v3.7 — 女性シルエット部品再設計

- 判定: 候補
- 確認時刻: 2026-08-04T04:29:53.609Z
- 変更内容: 髪、裾区画、肩幅、腰帯、ブーツの輪郭を作り直し。

![v3.7 female-back](v3.7/female-back.png)

![v3.7 female-front](v3.7/female-front.png)

![v3.7 female-three-quarter](v3.7/female-three-quarter.png)

<a id="v38"></a>

### v3.8 — 女性衣装の監査修正

- 判定: 候補
- 確認時刻: 2026-08-04T05:56:02.264Z
- 変更内容: 腰位置、裾の回り込み、襟高、顎丈ボブを再調整。

![v3.8 female-back](v3.8/female-back.png)

![v3.8 female-front](v3.8/female-front.png)

![v3.8 female-three-quarter](v3.8/female-three-quarter.png)

<a id="v39"></a>

### v3.9 — 女性背面被覆の修正

- 判定: 保持
- 確認時刻: 2026-08-04T06:05:01.379Z
- 変更内容: 正面裾幅を保ちながら背面の腰・臀部露出を修正した編集可能版。

![v3.9 female-back](v3.9/female-back.png)

![v3.9 female-front](v3.9/female-front.png)

## v4 系

<a id="v40"></a>

### v4.0 — 三方向投影の初回

- 判定: 不採用
- 確認時刻: 2026-08-04T05:25:47.333Z
- 変更内容: Hunyuan 形状へ三面図を投影した初回。方向境界と二重写りが残る。

![v4.0 female-back](v4.0/female-back.png)

![v4.0 female-front](v4.0/female-front.png)

![v4.0 female-three-quarter](v4.0/female-three-quarter.png)

<a id="v41"></a>

### v4.1 — 輪郭追従投影

- 判定: 候補
- 確認時刻: 2026-08-04T05:38:08.655Z
- 変更内容: 高さ別輪郭補正と衣類領域ごとの色制約を追加。

![v4.1 female-back](v4.1/female-back.png)

![v4.1 female-front](v4.1/female-front.png)

![v4.1 female-three-quarter](v4.1/female-three-quarter.png)

<a id="v42"></a>

### v4.2 — 男女共通投影処理

- 判定: 候補
- 確認時刻: 2026-08-04T05:46:19.815Z
- 変更内容: 脚の白斑、脇の袖写り、輪郭と衣装色を男女共通処理で修正。

![v4.2 female-front](v4.2/female-front.png)

![v4.2 female-three-quarter](v4.2/female-three-quarter.png)

![v4.2 male-front](v4.2/male-front.png)

![v4.2 male-three-quarter](v4.2/male-three-quarter.png)

<a id="v43"></a>

### v4.3 — v3/v4 横並び監査

- 判定: 診断
- 確認時刻: 2026-08-04T05:59:01.445Z
- 変更内容: 編集可能な v3 と高忠実度 v4 の斜め表示を比較。

![v4.3 female-three-quarter](v4.3/female-three-quarter.png)

![v4.3 male-three-quarter](v4.3/male-three-quarter.png)

<a id="v44"></a>

### v4.4 — 裾・腰色補正

- 判定: 候補
- 確認時刻: 2026-08-04T06:06:48.308Z / 2026-08-04T06:10:16.997Z
- 変更内容: 裾の色潰れと女性腰の肌色誤投影を修正。正面と斜めを確認。

![v4.4 female-back](v4.4/female-back.png)

![v4.4 female-front](v4.4/female-front.png)

![v4.4 female-right-side](v4.4/female-right-side.png)

![v4.4 female-three-quarter](v4.4/female-three-quarter.png)

![v4.4 male-back](v4.4/male-back.png)

![v4.4 male-front](v4.4/male-front.png)

![v4.4 male-right-side](v4.4/male-right-side.png)

![v4.4 male-three-quarter](v4.4/male-three-quarter.png)

<a id="v45"></a>

### v4.5 — 背景差分拡張テスト

- 判定: 不採用
- 確認時刻: 2026-08-04T06:19:21.551Z
- 変更内容: 輪郭の白いハローを人物として拾ったため不採用。

![v4.5 female-back](v4.5/female-back.png)

![v4.5 female-front](v4.5/female-front.png)

![v4.5 female-three-quarter](v4.5/female-three-quarter.png)

![v4.5 male-back](v4.5/male-back.png)

![v4.5 male-front](v4.5/male-front.png)

![v4.5 male-three-quarter](v4.5/male-three-quarter.png)

<a id="v46"></a>

### v4.6 — 背景除去ロールバック

- 判定: 候補
- 確認時刻: 2026-08-04T06:26:22.883Z
- 変更内容: 厳しい背景除去へ戻し、腕の投影元切替だけを残した男性版。

![v4.6 male-back](v4.6/male-back.png)

![v4.6 male-front](v4.6/male-front.png)

![v4.6 male-right-side](v4.6/male-right-side.png)

![v4.6 male-three-quarter](v4.6/male-three-quarter.png)

<a id="v47"></a>

### v4.7 — 腕全体の前後投影診断

- 判定: 診断
- 確認時刻: 2026-08-04T06:29:20.322Z
- 変更内容: 腕全体を前後画像へ寄せた比較用診断。

![v4.7 armglobal/male-back](v4.7/armglobal/male-back.png)

![v4.7 armglobal/male-front](v4.7/armglobal/male-front.png)

![v4.7 armglobal/male-right-side](v4.7/armglobal/male-right-side.png)

![v4.7 armglobal/male-three-quarter](v4.7/armglobal/male-three-quarter.png)

<a id="v48"></a>

### v4.8 — 腕部位別・袖クランプ比較

- 判定: 診断
- 確認時刻: 2026-08-04T06:37:39.675Z
- 変更内容: 腕の部位別投影と横画像内の袖領域制限を比較。

![v4.8 armcomponent/male-front](v4.8/armcomponent/male-front.png)

![v4.8 armcomponent/male-right-side](v4.8/armcomponent/male-right-side.png)

![v4.8 armcomponent/male-three-quarter](v4.8/armcomponent/male-three-quarter.png)

![v4.8 sleeveclamp/male-front](v4.8/sleeveclamp/male-front.png)

![v4.8 sleeveclamp/male-right-side](v4.8/sleeveclamp/male-right-side.png)

![v4.8 sleeveclamp/male-three-quarter](v4.8/sleeveclamp/male-three-quarter.png)

<a id="v49"></a>

### v4.9 — 女性の腕部位別投影

- 判定: 診断
- 確認時刻: 2026-08-04T06:40:05.810Z
- 変更内容: 男性で試した腕部位別方式を女性へ適用して確認。

![v4.9 armcomponent-female/female-back](v4.9/armcomponent-female/female-back.png)

![v4.9 armcomponent-female/female-front](v4.9/armcomponent-female/female-front.png)

![v4.9 armcomponent-female/female-right-side](v4.9/armcomponent-female/female-right-side.png)

![v4.9 armcomponent-female/female-three-quarter](v4.9/armcomponent-female/female-three-quarter.png)

<a id="v410"></a>

### v4.10 — 髪の背景漏れ診断

- 判定: 診断
- 確認時刻: 2026-08-04T06:47:34.741Z
- 変更内容: 後頭部と側面の明るい背景漏れを確認した男性診断。

![v4.10 hairleak/male-back](v4.10/hairleak/male-back.png)

![v4.10 hairleak/male-right-side](v4.10/hairleak/male-right-side.png)

<a id="v411"></a>

### v4.11 — 男性の袖領域分離版

- 判定: 候補
- 確認時刻: 2026-08-04T06:52:33.093Z
- 変更内容: 上腕・前腕の袖だけを横画像の実腕領域へ割り当てた男性版。

![v4.11 male-back](v4.11/male-back.png)

![v4.11 male-front](v4.11/male-front.png)

![v4.11 male-right-side](v4.11/male-right-side.png)

![v4.11 male-three-quarter](v4.11/male-three-quarter.png)

<a id="v412"></a>

### v4.12 — 女性の固定幅袖補助投影

- 判定: 不採用
- 確認時刻: 2026-08-04T06:55:01.521Z
- 変更内容: 女性に大きな矩形境界が出たため補助投影を不採用。

![v4.12 female-back](v4.12/female-back.png)

![v4.12 female-front](v4.12/female-front.png)

![v4.12 female-right-side](v4.12/female-right-side.png)

![v4.12 female-three-quarter](v4.12/female-three-quarter.png)

<a id="v413"></a>

### v4.13 — 女性の袖領域分離版

- 判定: 旧版
- 確認時刻: 2026-08-04T07:00:32.443Z
- 変更内容: 固定幅補助投影を撤回し、横画像の袖領域分離だけを残した版。

![v4.13 female-back](v4.13/female-back.png)

![v4.13 female-front](v4.13/female-front.png)

![v4.13 female-right-side](v4.13/female-right-side.png)

![v4.13 female-three-quarter](v4.13/female-three-quarter.png)

<a id="v414"></a>

### v4.14 — 手首と指を裾・ズボン色補正から除外し、女性の額を正面投影へ復元

- 判定: 不採用
- 確認時刻: 2026-08-04T07:34:52.239729+00:00
- 変更内容: 手首と指を裾・ズボン色補正から除外し、女性の額を正面投影へ復元

![v4.14 initial-female-v4-back](v4.14/initial-female-v4-back.png)

![v4.14 initial-female-v4-front](v4.14/initial-female-v4-front.png)

![v4.14 initial-female-v4-right-side](v4.14/initial-female-v4-right-side.png)

![v4.14 initial-female-v4-three-quarter](v4.14/initial-female-v4-three-quarter.png)

![v4.14 initial-male-v4-back](v4.14/initial-male-v4-back.png)

![v4.14 initial-male-v4-front](v4.14/initial-male-v4-front.png)

![v4.14 initial-male-v4-right-side](v4.14/initial-male-v4-right-side.png)

![v4.14 initial-male-v4-three-quarter](v4.14/initial-male-v4-three-quarter.png)

<a id="v415"></a>

### v4.15 — 手領域の上限をAポーズの実位置まで広げ、手首の青緑ブロックと黒い指先を補正

- 判定: 不採用
- 確認時刻: 2026-08-04T07:40:18.484510+00:00
- 変更内容: 手領域の上限をAポーズの実位置まで広げ、手首の青緑ブロックと黒い指先を補正

![v4.15 initial-female-v4-back](v4.15/initial-female-v4-back.png)

![v4.15 initial-female-v4-front](v4.15/initial-female-v4-front.png)

![v4.15 initial-female-v4-right-side](v4.15/initial-female-v4-right-side.png)

![v4.15 initial-female-v4-three-quarter](v4.15/initial-female-v4-three-quarter.png)

![v4.15 initial-male-v4-back](v4.15/initial-male-v4-back.png)

![v4.15 initial-male-v4-front](v4.15/initial-male-v4-front.png)

![v4.15 initial-male-v4-right-side](v4.15/initial-male-v4-right-side.png)

![v4.15 initial-male-v4-three-quarter](v4.15/initial-male-v4-three-quarter.png)

<a id="v416"></a>

### v4.16 — 遠位の手指に残る暗色投影を肌色へ補正し、黒い指先を除去

- 判定: 不採用
- 確認時刻: 2026-08-04T07:44:54.704190+00:00
- 変更内容: 遠位の手指に残る暗色投影を肌色へ補正し、黒い指先を除去

![v4.16 initial-female-v4-back](v4.16/initial-female-v4-back.png)

![v4.16 initial-female-v4-front](v4.16/initial-female-v4-front.png)

![v4.16 initial-female-v4-right-side](v4.16/initial-female-v4-right-side.png)

![v4.16 initial-female-v4-three-quarter](v4.16/initial-female-v4-three-quarter.png)

![v4.16 initial-male-v4-back](v4.16/initial-male-v4-back.png)

![v4.16 initial-male-v4-front](v4.16/initial-male-v4-front.png)

![v4.16 initial-male-v4-right-side](v4.16/initial-male-v4-right-side.png)

![v4.16 initial-male-v4-three-quarter](v4.16/initial-male-v4-three-quarter.png)

## v5 系

<a id="v50"></a>

### v5.0 — 投影・頂点色を廃止。骨領域別PBR材質と別メッシュの顔・衣装ディテールを検証する初回診断版。

- 判定: 不採用
- 確認時刻:
- 変更内容: 投影・頂点色を廃止。骨領域別PBR材質と別メッシュの顔・衣装ディテールを検証する初回診断版。

![v5.0 initial-male-v5-back](v5.0/initial-male-v5-back.png)

![v5.0 initial-male-v5-front](v5.0/initial-male-v5-front.png)

![v5.0 initial-male-v5-right-side](v5.0/initial-male-v5-right-side.png)

![v5.0 initial-male-v5-three-quarter](v5.0/initial-male-v5-three-quarter.png)

<a id="v51"></a>

### v5.1 — v5.0の生成眼球を廃止。MPFBのUV付き頭部・手・眼・眉・睫毛を再構成衣装と統合し、腕材質帯を再設計。

- 判定: 不採用
- 確認時刻:
- 変更内容: v5.0の生成眼球を廃止。MPFBのUV付き頭部・手・眼・眉・睫毛を再構成衣装と統合し、腕材質帯を再設計。

![v5.1 initial-male-v5-back](v5.1/initial-male-v5-back.png)

![v5.1 initial-male-v5-front](v5.1/initial-male-v5-front.png)

![v5.1 initial-male-v5-right-side](v5.1/initial-male-v5-right-side.png)

![v5.1 initial-male-v5-three-quarter](v5.1/initial-male-v5-three-quarter.png)

<a id="v52"></a>

### v5.2 — bmesh面削除へ修正し、衣装面数下限を追加。MPFB頭部・手と再構成衣装のハイブリッドを再検証。

- 判定: 不採用
- 確認時刻:
- 変更内容: bmesh面削除へ修正し、衣装面数下限を追加。MPFB頭部・手と再構成衣装のハイブリッドを再検証。

![v5.2 initial-male-v5-back](v5.2/initial-male-v5-back.png)

![v5.2 initial-male-v5-front](v5.2/initial-male-v5-front.png)

![v5.2 initial-male-v5-right-side](v5.2/initial-male-v5-right-side.png)

![v5.2 initial-male-v5-three-quarter](v5.2/initial-male-v5-three-quarter.png)

<a id="v53"></a>

### v5.3 — MPFB頭部を再構成頭部内へ三軸フィットし、左右の手を手首—指先方向で回転・拡縮して衣装へ接続。

- 判定: 不採用
- 確認時刻:
- 変更内容: MPFB頭部を再構成頭部内へ三軸フィットし、左右の手を手首—指先方向で回転・拡縮して衣装へ接続。

![v5.3 initial-male-v5-back](v5.3/initial-male-v5-back.png)

![v5.3 initial-male-v5-front](v5.3/initial-male-v5-front.png)

![v5.3 initial-male-v5-right-side](v5.3/initial-male-v5-right-side.png)

![v5.3 initial-male-v5-three-quarter](v5.3/initial-male-v5-three-quarter.png)

<a id="v54"></a>

### v5.4 — 再構成側の手面を全削除し、MPFB手を幾何学的な上下端で下向き接続。顔面・耳だけを残し頭頂・後頭・首面を除外。

- 判定: 不採用
- 確認時刻:
- 変更内容: 再構成側の手面を全削除し、MPFB手を幾何学的な上下端で下向き接続。顔面・耳だけを残し頭頂・後頭・首面を除外。

![v5.4 initial-male-v5-back](v5.4/initial-male-v5-back.png)

![v5.4 initial-male-v5-front](v5.4/initial-male-v5-front.png)

![v5.4 initial-male-v5-right-side](v5.4/initial-male-v5-right-side.png)

![v5.4 initial-male-v5-three-quarter](v5.4/initial-male-v5-three-quarter.png)

<a id="v55"></a>

### v5.5 — MPFB手の移植を廃止。再構成手を衣装と連続したまま肌PBR化し、MPFBは顔面・眼・眉・睫毛だけを使用。

- 判定: 不採用
- 確認時刻:
- 変更内容: MPFB手の移植を廃止。再構成手を衣装と連続したまま肌PBR化し、MPFBは顔面・眼・眉・睫毛だけを使用。

![v5.5 initial-male-v5-back](v5.5/initial-male-v5-back.png)

![v5.5 initial-male-v5-front](v5.5/initial-male-v5-front.png)

![v5.5 initial-male-v5-right-side](v5.5/initial-male-v5-right-side.png)

![v5.5 initial-male-v5-three-quarter](v5.5/initial-male-v5-three-quarter.png)

<a id="v56"></a>

### v5.6 — 眼球以外の移植顔パーツを除外。手甲・靴口を材質帯で復元し、前裾縁と帯金具を別メッシュ追加。

- 判定: 不採用
- 確認時刻:
- 変更内容: 眼球以外の移植顔パーツを除外。手甲・靴口を材質帯で復元し、前裾縁と帯金具を別メッシュ追加。

![v5.6 initial-male-v5-back](v5.6/initial-male-v5-back.png)

![v5.6 initial-male-v5-front](v5.6/initial-male-v5-front.png)

![v5.6 initial-male-v5-right-side](v5.6/initial-male-v5-right-side.png)

![v5.6 initial-male-v5-three-quarter](v5.6/initial-male-v5-three-quarter.png)

<a id="v57"></a>

### v5.7 — 浮いた前裾線を削除。靴口金属帯を細線化し、男性の側頭・後頭髪境界を上げて顎周辺を顔面へ戻す。

- 判定: 不採用
- 確認時刻:
- 変更内容: 浮いた前裾線を削除。靴口金属帯を細線化し、男性の側頭・後頭髪境界を上げて顎周辺を顔面へ戻す。

![v5.7 initial-male-v5-back](v5.7/initial-male-v5-back.png)

![v5.7 initial-male-v5-front](v5.7/initial-male-v5-front.png)

![v5.7 initial-male-v5-right-side](v5.7/initial-male-v5-right-side.png)

![v5.7 initial-male-v5-three-quarter](v5.7/initial-male-v5-three-quarter.png)

<a id="v58"></a>

### v5.8 — 顔面移植を廃止し一体再構成頭部へ復帰。極薄・小型の眼球と虹彩のみ別メッシュ化して背面透けと首切断面を除去。

- 判定: 不採用
- 確認時刻:
- 変更内容: 顔面移植を廃止し一体再構成頭部へ復帰。極薄・小型の眼球と虹彩のみ別メッシュ化して背面透けと首切断面を除去。

![v5.8 initial-male-v5-back](v5.8/initial-male-v5-back.png)

![v5.8 initial-male-v5-front](v5.8/initial-male-v5-front.png)

![v5.8 initial-male-v5-right-side](v5.8/initial-male-v5-right-side.png)

![v5.8 initial-male-v5-three-quarter](v5.8/initial-male-v5-three-quarter.png)

## v6 系

v6.0〜v6.20 は、参照画像を表面へ投影せず、人体・顔・手・髪・衣装・靴を実メッシュとUV付きPBR素材で構成した系列。各版の実施内容、却下理由、最終GLB検査値、ゲーム統合画像は [キャラクター3Dモデル v6 制作記録](../../character-models-v6.md) にまとめている。

### v6.20 — 実メッシュ最終採用版

- 判定: 採用
- 変更内容: 隠れた体表面、女性裾の側面シーム、衣装内クリアランスを確定。空のBlenderシーンへのGLB再読込で、53ボーン、最大4ジョイント、UV、埋め込み画像、外部依存0を検証。
- ゲーム確認: PC 1280×720、モバイル 375×812。ブラウザ例外0、最終GLBのGET 200を確認。

![v6.20 男性 正面](v6.20/initial-male-v6-front.png)

![v6.20 女性 正面](v6.20/initial-female-v6-front.png)

![v6.20 男性 GLB再読込](v6.20/glb-proof/initial-male-v6-glb-proof.png)

![v6.20 女性 GLB再読込](v6.20/glb-proof/initial-female-v6-glb-proof.png)

![v6.20 375pxゲーム表示](v6.20/gameplay-375.png)
