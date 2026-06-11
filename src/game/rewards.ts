import type { BattleReward, MaterialId, ResultKind } from "../types/game";
import { createEmptyMaterialMap } from "./inventory";
import type { BossDifficulty, BossRewardTier } from "./menu";

type RandomSource = () => number;

export interface RewardTierMultiplier {
  coinMultiplier: number;
  materialMultiplier: number;
}

export interface BattleRewardContext {
  difficulty: BossDifficulty;
  rewardTier: BossRewardTier;
}

export const REWARD_TIER_MULTIPLIERS: Record<BossRewardTier, RewardTierMultiplier> = {
  tutorial: {
    coinMultiplier: 0.7,
    materialMultiplier: 0.8,
  },
  standard: {
    coinMultiplier: 1,
    materialMultiplier: 1,
  },
  advanced: {
    coinMultiplier: 1.25,
    materialMultiplier: 1.15,
  },
};

export const DIFFICULTY_REWARD_MULTIPLIERS: Record<BossDifficulty, number> = {
  Normal: 1,
  Hard: 1.4,
  Extreme: 2,
};

export const STANDARD_NORMAL_REWARD_CONTEXT: BattleRewardContext = {
  difficulty: "Normal",
  rewardTier: "standard",
};

const FAILED_RANDOM_MATERIALS = [
  "beastClaw",
  "fireStone",
  "oldCloth",
  "stonePiece",
] as const satisfies readonly MaterialId[];

const MAGIC_SHARD_FAILED_DROP_RATE = 0.2;

function normalizedRandom(rng: RandomSource): number {
  return Math.min(Math.max(rng(), 0), 0.999999999);
}

function randomInt(rng: RandomSource, min: number, max: number): number {
  return min + Math.floor(normalizedRandom(rng) * (max - min + 1));
}

function randomItem<T>(rng: RandomSource, items: readonly T[]): T {
  return items[Math.floor(normalizedRandom(rng) * items.length)];
}

function createClearReward(rng: RandomSource): BattleReward {
  return {
    coin: randomInt(rng, 120, 180),
    materials: {
      ...createEmptyMaterialMap(),
      beastClaw: randomInt(rng, 1, 3),
      fireStone: randomInt(rng, 1, 2),
      oldCloth: randomInt(rng, 1, 3),
      stonePiece: randomInt(rng, 1, 3),
      magicShard: randomInt(rng, 1, 2),
    },
  };
}

function createFailedReward(rng: RandomSource): BattleReward {
  const coin = randomInt(rng, 30, 60);
  const materials = createEmptyMaterialMap();
  materials[randomItem(rng, FAILED_RANDOM_MATERIALS)] = 1;

  if (normalizedRandom(rng) < MAGIC_SHARD_FAILED_DROP_RATE) {
    materials.magicShard += 1;
  }

  return {
    coin,
    materials,
  };
}

export function getRewardTierMultiplier(rewardTier: BossRewardTier): RewardTierMultiplier {
  return REWARD_TIER_MULTIPLIERS[rewardTier];
}

export function getDifficultyRewardMultiplier(difficulty: BossDifficulty): number {
  return DIFFICULTY_REWARD_MULTIPLIERS[difficulty];
}

function scaleRewardAmount(
  amount: number,
  multiplier: number,
  minimumWhenPresent = 0,
): number {
  if (amount <= 0) {
    return 0;
  }

  return Math.max(minimumWhenPresent, Math.round(amount * multiplier));
}

export function applyRewardScaling(
  reward: BattleReward,
  resultKind: ResultKind,
  context: BattleRewardContext = STANDARD_NORMAL_REWARD_CONTEXT,
): BattleReward {
  const tierMultiplier = getRewardTierMultiplier(context.rewardTier);
  const difficultyMultiplier = getDifficultyRewardMultiplier(context.difficulty);
  const coinMultiplier = tierMultiplier.coinMultiplier * difficultyMultiplier;
  const materialMultiplier = tierMultiplier.materialMultiplier * difficultyMultiplier;
  const materialMinimum = resultKind === "CLEAR" ? 1 : 0;

  return {
    coin: scaleRewardAmount(reward.coin, coinMultiplier),
    materials: {
      beastClaw: scaleRewardAmount(reward.materials.beastClaw, materialMultiplier, materialMinimum),
      fireStone: scaleRewardAmount(reward.materials.fireStone, materialMultiplier, materialMinimum),
      oldCloth: scaleRewardAmount(reward.materials.oldCloth, materialMultiplier, materialMinimum),
      stonePiece: scaleRewardAmount(reward.materials.stonePiece, materialMultiplier, materialMinimum),
      magicShard: scaleRewardAmount(reward.materials.magicShard, materialMultiplier, materialMinimum),
    },
  };
}

export function generateBattleReward(
  resultKind: ResultKind,
  rng: RandomSource = Math.random,
  context: BattleRewardContext = STANDARD_NORMAL_REWARD_CONTEXT,
): BattleReward {
  const baseReward = resultKind === "CLEAR" ? createClearReward(rng) : createFailedReward(rng);

  return applyRewardScaling(baseReward, resultKind, context);
}
