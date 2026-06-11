import { BOSS_OPTIONS } from "./bosses";
import type { BossAttackStats, BossOption, BossRole, BossSelection, BossRewardTier } from "./menu";
import type { BossDifficulty } from "./menu";

export interface BossDifficultyStats {
  maxHp: number;
  defense: number;
  breakGauge: number;
  downDurationMs: number;
  attacks: BossAttackStats;
  telegraphsMs: BossAttackStats;
  role: BossRole;
  roleLabel: string;
  roleDescription: string;
  rewardTier: BossRewardTier;
}

export const BOSS_DIFFICULTY_HP_MULTIPLIERS: Record<BossDifficulty, number> = {
  Normal: 1,
  Hard: 2.2,
  Extreme: 4,
};

function getDefaultBoss(): BossOption {
  return BOSS_OPTIONS.find((boss) => boss.role === "standard") ?? BOSS_OPTIONS[0];
}

export function getBossStatsForDifficulty(
  difficulty: BossDifficulty,
  boss: BossOption = getDefaultBoss(),
): BossDifficultyStats {
  return {
    maxHp: Math.round(boss.baseStats.normalHp * BOSS_DIFFICULTY_HP_MULTIPLIERS[difficulty]),
    defense: boss.baseStats.defense,
    breakGauge: boss.baseStats.breakGauge,
    downDurationMs: Math.round(boss.baseStats.downDurationSeconds * 1000),
    attacks: boss.baseStats.attacks,
    telegraphsMs: {
      frontal: Math.round(boss.baseStats.telegraphs.frontal * 1000),
      charge: Math.round(boss.baseStats.telegraphs.charge * 1000),
      area: Math.round(boss.baseStats.telegraphs.area * 1000),
    },
    role: boss.role,
    roleLabel: boss.roleLabel,
    roleDescription: boss.roleDescription,
    rewardTier: boss.rewardTier,
  };
}

export function getBossStatsForSelection(selection: BossSelection): BossDifficultyStats {
  return getBossStatsForDifficulty(selection.difficulty, selection.boss);
}

export function createRetryBattleSelection(selection: BossSelection): BossSelection {
  return {
    boss: selection.boss,
    difficulty: selection.difficulty,
  };
}
