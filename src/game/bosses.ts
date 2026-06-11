import type { AttributeId } from "../types/game";

export type BossRole = "tutorial" | "standard" | "advanced";
export type BossRewardTier = BossRole;

export interface BossAttackStats {
  frontal: number;
  charge: number;
  area: number;
}

export interface BossTelegraphSeconds {
  frontal: number;
  charge: number;
  area: number;
}

export interface BossBaseStats {
  normalHp: number;
  defense: number;
  breakGauge: number;
  downDurationSeconds: number;
  attacks: BossAttackStats;
  telegraphs: BossTelegraphSeconds;
}

export interface BossOption {
  id: string;
  name: string;
  attributeId: AttributeId;
  description: string;
  role: BossRole;
  roleLabel: string;
  roleDescription: string;
  rewardTier: BossRewardTier;
  baseStats: BossBaseStats;
}

export const BOSS_OPTIONS: BossOption[] = [
  {
    id: "growl",
    name: "魔獣グラウル",
    attributeId: "dark",
    description: "操作を覚えるための弱めの魔獣。初期装備でも挑みやすい。",
    role: "tutorial",
    roleLabel: "チュートリアル",
    roleDescription: "初心者向け",
    rewardTier: "tutorial",
    baseStats: {
      normalHp: 1500,
      defense: 2,
      breakGauge: 70,
      downDurationSeconds: 6.5,
      attacks: {
        frontal: 8,
        charge: 14,
        area: 12,
      },
      telegraphs: {
        frontal: 1.2,
        charge: 1.4,
        area: 1.3,
      },
    },
  },
  {
    id: "flamehorn",
    name: "炎角の獣",
    attributeId: "fire",
    description: "現在の基準となる標準的な討伐対象。",
    role: "standard",
    roleLabel: "標準",
    roleDescription: "基準ボス",
    rewardTier: "standard",
    baseStats: {
      normalHp: 3000,
      defense: 5,
      breakGauge: 100,
      downDurationSeconds: 6,
      attacks: {
        frontal: 15,
        charge: 25,
        area: 20,
      },
      telegraphs: {
        frontal: 0.8,
        charge: 1.1,
        area: 1,
      },
    },
  },
  {
    id: "crystal-warden",
    name: "水晶の守護者",
    attributeId: "water",
    description: "慣れてきた人向けの硬めで強い守護者。",
    role: "advanced",
    roleLabel: "上級寄り",
    roleDescription: "慣れた人向け",
    rewardTier: "advanced",
    baseStats: {
      normalHp: 4200,
      defense: 8,
      breakGauge: 130,
      downDurationSeconds: 5.5,
      attacks: {
        frontal: 18,
        charge: 30,
        area: 24,
      },
      telegraphs: {
        frontal: 0.75,
        charge: 1,
        area: 0.9,
      },
    },
  },
];
