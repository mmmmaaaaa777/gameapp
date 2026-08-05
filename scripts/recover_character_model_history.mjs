/* global Buffer, console, process */

/**
 * Recover character-review renders embedded in a Codex JSONL session.
 *
 * The model previews were repeatedly rendered to the same filenames while the
 * characters were being refined. Codex stores every image that was visually
 * reviewed as a base64 PNG in the session log, so the overwritten checkpoints
 * can be reconstructed without re-creating or approximating them.
 *
 * Usage:
 *   node scripts/recover_character_model_history.mjs /path/to/session.jsonl
 */

import { createReadStream } from "node:fs";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import readline from "node:readline";
import { fileURLToPath } from "node:url";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const historyRoot = path.join(
  projectRoot,
  "docs",
  "character-concepts",
  "model-history",
);

const revisionDefinitions = [
  ["2026-08-04T00:58:35.266Z", "v1.0", "superseded", "初期軽量モデル", "単純形状で構成した最初の男女モデル。リグとゲーム読込の成立を優先。"],
  ["2026-08-04T01:56:41.812Z", "v2.0", "rejected", "v2 初回造形", "顔・指・衣装・髪を高密度化した初回。断面リングのねじれが残る。"],
  ["2026-08-04T02:02:49.019Z", "v2.1", "rejected", "断面リング修正", "袖とズボンのねじれを修正した途中確認。"],
  ["2026-08-04T02:05:39.361Z", "v2.2", "candidate", "脚・髪・衣装接続修正", "脚の肌抜けを解消し、ズボンを足首まで連続化。髪型も再調整。"],
  ["2026-08-04T02:10:57.903Z", "v2.3", "diagnostic", "右側面 QA", "頭身、襟、前合わせ、ブーツ、手を右側面から検査。"],
  ["2026-08-04T02:13:50.400Z", "v2.4", "superseded", "v2 最終多方向確認", "v2 の正面・右側面を男女同条件で比較した最終確認。"],
  ["2026-08-04T03:28:32.090Z", "v3.0", "rejected", "MPFB 高密度版の初回", "MPFB 人体と別メッシュ衣装の初回。髪・縁取り・脚にスパイク変形あり。"],
  ["2026-08-04T03:44:45.488Z", "v3.1", "candidate", "スパイク修正", "厚み付けとモディファイア確定範囲を修正し、髪・襟・ブーツ・素材を再構築。"],
  ["2026-08-04T03:51:12.687Z", "v3.2", "candidate", "男性シルエット再設計", "頭頂、前髪、裾パネル、白飛び、箱型つま先を修正。"],
  ["2026-08-04T04:00:24.478Z", "v3.3", "candidate", "衣装の断面中心補正", "首・胸・腰の実断面へ襟、前立て、帯、裾を密着。"],
  ["2026-08-04T04:04:54.579Z", "v3.4", "candidate", "男性立ち姿と首回り", "レスト姿勢を保った腕下げ、襟開口、肌色、髪、留め具を調整。"],
  ["2026-08-04T04:11:23.909Z", "v3.5", "rejected", "女性高密度版の初回", "衣装は成立したが、直線的なボブと広い肩幅が課題。"],
  ["2026-08-04T04:22:31.536Z", "v3.6", "candidate", "女性ボブと体型調整", "ボブの面密度、毛先幅、分け目、頭身、肩、腕、脚を再調整。"],
  ["2026-08-04T04:29:53.609Z", "v3.7", "candidate", "女性シルエット部品再設計", "髪、裾区画、肩幅、腰帯、ブーツの輪郭を作り直し。"],
  ["2026-08-04T05:56:02.264Z", "v3.8", "candidate", "女性衣装の監査修正", "腰位置、裾の回り込み、襟高、顎丈ボブを再調整。"],
  ["2026-08-04T06:05:01.379Z", "v3.9", "kept", "女性背面被覆の修正", "正面裾幅を保ちながら背面の腰・臀部露出を修正した編集可能版。"],
  ["2026-08-04T05:25:47.333Z", "v4.0", "rejected", "三方向投影の初回", "Hunyuan 形状へ三面図を投影した初回。方向境界と二重写りが残る。"],
  ["2026-08-04T05:38:08.655Z", "v4.1", "candidate", "輪郭追従投影", "高さ別輪郭補正と衣類領域ごとの色制約を追加。"],
  ["2026-08-04T05:46:19.815Z", "v4.2", "candidate", "男女共通投影処理", "脚の白斑、脇の袖写り、輪郭と衣装色を男女共通処理で修正。"],
  ["2026-08-04T05:59:01.445Z", "v4.3", "diagnostic", "v3/v4 横並び監査", "編集可能な v3 と高忠実度 v4 の斜め表示を比較。"],
  ["2026-08-04T06:06:48.308Z", "v4.4", "candidate", "裾・腰色補正", "裾の色潰れと女性腰の肌色誤投影を修正。正面と斜めを確認。"],
  ["2026-08-04T06:10:16.997Z", "v4.4", "candidate", "裾・腰色補正", "同じ生成物の右側面と背面を追加確認。"],
  ["2026-08-04T06:19:21.551Z", "v4.5", "rejected", "背景差分拡張テスト", "輪郭の白いハローを人物として拾ったため不採用。"],
  ["2026-08-04T06:26:22.883Z", "v4.6", "candidate", "背景除去ロールバック", "厳しい背景除去へ戻し、腕の投影元切替だけを残した男性版。"],
  ["2026-08-04T06:29:20.322Z", "v4.7", "diagnostic", "腕全体の前後投影診断", "腕全体を前後画像へ寄せた比較用診断。"],
  ["2026-08-04T06:37:39.675Z", "v4.8", "diagnostic", "腕部位別・袖クランプ比較", "腕の部位別投影と横画像内の袖領域制限を比較。"],
  ["2026-08-04T06:40:05.810Z", "v4.9", "diagnostic", "女性の腕部位別投影", "男性で試した腕部位別方式を女性へ適用して確認。"],
  ["2026-08-04T06:47:34.741Z", "v4.10", "diagnostic", "髪の背景漏れ診断", "後頭部と側面の明るい背景漏れを確認した男性診断。"],
  ["2026-08-04T06:52:33.093Z", "v4.11", "candidate", "男性の袖領域分離版", "上腕・前腕の袖だけを横画像の実腕領域へ割り当てた男性版。"],
  ["2026-08-04T06:55:01.521Z", "v4.12", "rejected", "女性の固定幅袖補助投影", "女性に大きな矩形境界が出たため補助投影を不採用。"],
  ["2026-08-04T07:00:32.443Z", "v4.13", "superseded", "女性の袖領域分離版", "固定幅補助投影を撤回し、横画像の袖領域分離だけを残した版。"],
].map(([timestamp, revision, status, title, summary]) => ({
  timestamp,
  revision,
  status,
  title,
  summary,
}));

const definitionsByTimestamp = new Map(
  revisionDefinitions.map((definition) => [definition.timestamp, definition]),
);

function extractImagePaths(input) {
  return [
    ...input.matchAll(
      /(?:\/mnt\/c|\/home|\/tmp)[^"'\s]+\.(?:png|jpg|jpeg|webp)/giu,
    ),
  ].map((match) => match[0]);
}

function diagnosticLabel(sourcePath) {
  return sourcePath.match(/\/v4-([^/]+)-diagnostic\//iu)?.[1] ?? null;
}

function normalizedFilename(sourcePath, index) {
  const basename = path.basename(sourcePath).toLowerCase();
  const character = basename.match(/(?:initial-)?(male|female)/u)?.[1] ?? "unknown";
  const angle =
    ["three-quarter", "right-side", "front", "back", "right", "preview"].find(
      (candidate) => basename.includes(candidate),
    ) ?? `image-${String(index + 1).padStart(2, "0")}`;
  const normalizedAngle = angle === "right" ? "right-side" : angle;
  return `${character}-${normalizedAngle}.png`;
}

async function uniqueTargetPath(directory, filename, pngBuffer) {
  const extension = path.extname(filename);
  const stem = filename.slice(0, -extension.length);
  const digest = createHash("sha256").update(pngBuffer).digest("hex").slice(0, 12);
  let candidate = path.join(directory, filename);
  let suffix = 2;
  while (true) {
    try {
      const existing = await readFile(candidate);
      const existingDigest = createHash("sha256")
        .update(existing)
        .digest("hex")
        .slice(0, 12);
      if (existingDigest === digest) return { targetPath: candidate, digest, duplicate: true };
      candidate = path.join(directory, `${stem}-${suffix}${extension}`);
      suffix += 1;
    } catch (error) {
      if (error?.code === "ENOENT") return { targetPath: candidate, digest, duplicate: false };
      throw error;
    }
  }
}

async function recover(sessionPath) {
  const pendingCalls = new Map();
  const recoveredByRevision = new Map();
  const input = createReadStream(sessionPath, { encoding: "utf8" });
  const lines = readline.createInterface({ input, crlfDelay: Infinity });

  for await (const line of lines) {
    let record;
    try {
      record = JSON.parse(line);
    } catch {
      continue;
    }
    if (record.type !== "response_item") continue;
    const payload = record.payload ?? {};

    if (payload.type === "custom_tool_call" && payload.name === "exec") {
      const definition = definitionsByTimestamp.get(record.timestamp);
      if (!definition || !String(payload.input ?? "").includes("view_image")) continue;
      pendingCalls.set(payload.call_id, {
        definition,
        sourcePaths: extractImagePaths(String(payload.input ?? "")),
      });
      continue;
    }

    if (payload.type !== "custom_tool_call_output") continue;
    const pending = pendingCalls.get(payload.call_id);
    if (!pending || !Array.isArray(payload.output)) continue;
    const imageBlocks = payload.output.filter(
      (block) =>
        block?.type === "input_image" &&
        String(block.image_url ?? "").startsWith("data:image/png;base64,"),
    );
    if (imageBlocks.length === 0) continue;

    const revisionDirectory = path.join(historyRoot, pending.definition.revision);
    const revisionRecord = recoveredByRevision.get(pending.definition.revision) ?? {
      revision: pending.definition.revision,
      status: pending.definition.status,
      title: pending.definition.title,
      summary: pending.definition.summary,
      recoveredFrom: path.resolve(sessionPath),
      reviewTimestamps: [],
      images: [],
    };
    revisionRecord.reviewTimestamps.push(pending.definition.timestamp);

    for (let index = 0; index < imageBlocks.length; index += 1) {
      const sourcePath = pending.sourcePaths[index] ?? `unmapped-image-${index + 1}.png`;
      const label = diagnosticLabel(sourcePath);
      const outputDirectory = label
        ? path.join(revisionDirectory, label)
        : revisionDirectory;
      await mkdir(outputDirectory, { recursive: true });
      const pngBuffer = Buffer.from(
        imageBlocks[index].image_url.slice("data:image/png;base64,".length),
        "base64",
      );
      const filename = normalizedFilename(sourcePath, index);
      const { targetPath, digest, duplicate } = await uniqueTargetPath(
        outputDirectory,
        filename,
        pngBuffer,
      );
      if (!duplicate) await writeFile(targetPath, pngBuffer);
      const relativePath = path.relative(revisionDirectory, targetPath).replaceAll(path.sep, "/");
      if (!revisionRecord.images.some((image) => image.sha256 === digest)) {
        revisionRecord.images.push({
          file: relativePath,
          sourcePath,
          sha256: digest,
        });
      }
    }
    recoveredByRevision.set(pending.definition.revision, revisionRecord);
  }

  await mkdir(historyRoot, { recursive: true });
  for (const entry of await readdir(historyRoot, { withFileTypes: true })) {
    if (!entry.isDirectory() || !/^v\d+\.\d+$/u.test(entry.name)) continue;
    const revisionDirectory = path.join(historyRoot, entry.name);
    let build;
    try {
      build = JSON.parse(await readFile(path.join(revisionDirectory, "build.json"), "utf8"));
    } catch (error) {
      if (error?.code === "ENOENT") continue;
      throw error;
    }
    if (recoveredByRevision.has(entry.name)) continue;
    const images = [];
    for (const file of await readdir(revisionDirectory)) {
      if (!file.toLowerCase().endsWith(".png")) continue;
      const pngBuffer = await readFile(path.join(revisionDirectory, file));
      images.push({
        file,
        sourcePath: file,
        sha256: createHash("sha256").update(pngBuffer).digest("hex").slice(0, 12),
      });
    }
    recoveredByRevision.set(entry.name, {
      revision: entry.name,
      status: build.status ?? "candidate",
      title: build.note || `${entry.name} 版別ビルド`,
      summary: build.note || "版別出力として保存した生成物。",
      recoveredFrom: null,
      reviewTimestamps: [build.generatedAt].filter(Boolean),
      images,
      build: "build.json",
    });
  }

  const orderedRevisions = [...recoveredByRevision.values()].sort((left, right) => {
    const [, leftMajor, leftMinor] = left.revision.match(/^v(\d+)\.(\d+)$/u) ?? [];
    const [, rightMajor, rightMinor] = right.revision.match(/^v(\d+)\.(\d+)$/u) ?? [];
    return Number(leftMajor) - Number(rightMajor) || Number(leftMinor) - Number(rightMinor);
  });
  for (const revision of orderedRevisions) {
    const revisionDirectory = path.join(historyRoot, revision.revision);
    revision.reviewTimestamps = [...new Set(revision.reviewTimestamps)].sort();
    revision.images.sort((left, right) => left.file.localeCompare(right.file));
    await writeFile(
      path.join(revisionDirectory, "metadata.json"),
      `${JSON.stringify(revision, null, 2)}\n`,
      "utf8",
    );
  }
  await writeFile(
    path.join(historyRoot, "manifest.json"),
    `${JSON.stringify({ generatedAt: new Date().toISOString(), revisions: orderedRevisions }, null, 2)}\n`,
    "utf8",
  );
  const statusLabels = {
    kept: "保持",
    candidate: "候補",
    diagnostic: "診断",
    rejected: "不採用",
    superseded: "旧版",
  };
  const markdown = [
    "# キャラクター3Dモデル 制作履歴",
    "",
    "同じプレビュー名へ上書きされていた途中画像を、Codexセッションに埋め込まれた確認時点のPNGから復元した履歴。画像を再生成・加工したものではなく、当時実際に目視確認したバイト列をそのまま保存している。",
    "",
    "> 注意: レンダリングされてもチャット上で目視しなかった方向はセッションに埋め込まれていないため、版によって方向画像の枚数が異なる。今後の版は生成時点で全方向を版別保存する。",
    "",
    "## 一覧",
    "",
    "| 版 | 判定 | 内容 | 保存画像 |",
    "| --- | --- | --- | ---: |",
    ...orderedRevisions.map(
      (revision) =>
        `| [${revision.revision}](#${revision.revision.replace(".", "")}) | ${statusLabels[revision.status] ?? revision.status} | ${revision.title} | ${revision.images.length} |`,
    ),
    "",
  ];
  let lastMajor = null;
  for (const revision of orderedRevisions) {
    const major = revision.revision.split(".")[0];
    if (major !== lastMajor) {
      markdown.push(`## ${major} 系`, "");
      lastMajor = major;
    }
    markdown.push(
      `<a id="${revision.revision.replace(".", "")}"></a>`,
      "",
      `### ${revision.revision} — ${revision.title}`,
      "",
      `- 判定: ${statusLabels[revision.status] ?? revision.status}`,
      `- 確認時刻: ${revision.reviewTimestamps.join(" / ")}`,
      `- 変更内容: ${revision.summary}`,
      "",
    );
    for (const image of revision.images) {
      const label = `${revision.revision} ${image.file.replace(/\.png$/u, "")}`;
      markdown.push(`![${label}](${revision.revision}/${image.file})`, "");
    }
  }
  await writeFile(path.join(historyRoot, "README.md"), `${markdown.join("\n")}\n`, "utf8");
  return orderedRevisions;
}

const sessionPath = process.argv[2];
if (!sessionPath) {
  throw new Error("Pass the Codex JSONL session path as the first argument.");
}

const revisions = await recover(sessionPath);
const imageCount = revisions.reduce((total, revision) => total + revision.images.length, 0);
console.log(
  `RECOVERED_CHARACTER_HISTORY revisions=${revisions.length} images=${imageCount} output=${historyRoot}`,
);
