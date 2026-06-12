import { BOSS_OPTIONS } from "./bosses";
import type { BossOption } from "./bosses";

export type BossDifficulty = "Normal" | "Hard" | "Extreme";

export { BOSS_OPTIONS };
export type { BossAttackStats, BossBaseStats, BossOption, BossRewardTier, BossRole } from "./bosses";

export interface BossSelection {
  boss: BossOption;
  difficulty: BossDifficulty;
}

export interface MainSkillOption {
  id: string;
  name: string;
  role: string;
  description: string;
}

export const DIFFICULTIES: BossDifficulty[] = ["Normal", "Hard", "Extreme"];

export const DIFFICULTY_LABELS: Record<BossDifficulty, string> = {
  Normal: "ノーマル",
  Hard: "ハード",
  Extreme: "エクストリーム",
};

export function getDifficultyLabel(difficulty: string): string {
  return (DIFFICULTY_LABELS as Record<string, string>)[difficulty] ?? difficulty;
}

export const MAIN_SKILLS: MainSkillOption[] = [
  {
    id: "assault",
    name: "アサルト",
    role: "近接攻撃",
    description: "前方に踏み込み、短い間隔でダメージを稼ぐ基本攻撃型。",
  },
  {
    id: "rapid",
    name: "ラピッド",
    role: "連撃",
    description: "素早い手数で攻撃機会を増やす追撃型。",
  },
  {
    id: "break",
    name: "ブレイク",
    role: "高威力",
    description: "大きな一撃でボスの体勢を崩す破壊型。",
  },
  {
    id: "fortress",
    name: "フォートレス",
    role: "防御",
    description: "被弾リスクを抑えながら安定して戦う防御型。",
  },
  {
    id: "support",
    name: "サポート",
    role: "支援",
    description: "属性や回避を補助して継戦力を高める支援型。",
  },
];

export const SUB_SKILLS = ["攻撃力UP", "回避距離UP", "煌属性ダメージUP"];

export const EQUIPMENT = [
  ["武器", "初期武器"],
  ["頭", "初期頭防具"],
  ["胴体", "初期胴体防具"],
  ["足", "初期足防具"],
] as const;

export const MATERIALS = [
  ["共通素材", "0"],
  ["属性素材", "0"],
  ["ボス素材", "0"],
  ["コイン", "0"],
] as const;
