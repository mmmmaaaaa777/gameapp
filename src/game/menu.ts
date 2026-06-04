import type { AttributeId } from "../types/game";

export type BossDifficulty = "Normal" | "Hard" | "Extreme";

export interface BossOption {
  id: string;
  name: string;
  attributeId: AttributeId;
  description: string;
}

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

export const BOSS_OPTIONS: BossOption[] = [
  {
    id: "growl",
    name: "魔獣グラウル",
    attributeId: "dark",
    description: "闇をまとう古代闘技場の番獣。",
  },
  {
    id: "flamehorn",
    name: "炎角の獣",
    attributeId: "fire",
    description: "燃える角で突進する荒ぶる魔獣。",
  },
  {
    id: "crystal-warden",
    name: "水晶の守護者",
    attributeId: "water",
    description: "冷たい結晶装甲を持つ守護者。",
  },
];

export const DIFFICULTIES: BossDifficulty[] = ["Normal", "Hard", "Extreme"];

export const MAIN_SKILLS: MainSkillOption[] = [
  {
    id: "assault",
    name: "アサルト",
    role: "近接攻撃",
    description: "前方に踏み込み、短い隙でダメージを稼ぐ基本攻撃型。",
  },
  {
    id: "rapid",
    name: "ラピッド",
    role: "連撃",
    description: "素早い手数で攻撃機会を増やす軽量型。",
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
