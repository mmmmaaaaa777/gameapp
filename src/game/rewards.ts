import type { BattleReward, MaterialId, ResultKind } from "../types/game";
import { createEmptyMaterialMap } from "./inventory";

type RandomSource = () => number;

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

export function generateBattleReward(
  resultKind: ResultKind,
  rng: RandomSource = Math.random,
): BattleReward {
  return resultKind === "CLEAR" ? createClearReward(rng) : createFailedReward(rng);
}
