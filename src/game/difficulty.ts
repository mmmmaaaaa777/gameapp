import type { BossDifficulty, BossSelection } from "./menu";

export interface BossDifficultyStats {
  maxHp: number;
  defense: number;
}

export const BOSS_DIFFICULTY_STATS: Record<BossDifficulty, BossDifficultyStats> = {
  Normal: {
    maxHp: 3000,
    defense: 5,
  },
  Hard: {
    maxHp: 6500,
    defense: 5,
  },
  Extreme: {
    maxHp: 12000,
    defense: 5,
  },
};

export function getBossStatsForDifficulty(difficulty: BossDifficulty): BossDifficultyStats {
  return BOSS_DIFFICULTY_STATS[difficulty];
}

export function getBossStatsForSelection(selection: BossSelection): BossDifficultyStats {
  return getBossStatsForDifficulty(selection.difficulty);
}

export function createRetryBattleSelection(selection: BossSelection): BossSelection {
  return {
    boss: selection.boss,
    difficulty: selection.difficulty,
  };
}
