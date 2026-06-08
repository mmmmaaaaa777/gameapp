import { describe, expect, it } from "vitest";
import {
  addRewardToInventory,
  createEmptyInventory,
  INVENTORY_STORAGE_KEY,
  loadPlayerInventory,
  savePlayerInventory,
} from "../src/game/inventory";
import { generateBattleReward } from "../src/game/rewards";

class MemoryStorage {
  private values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

function sequenceRandom(values: number[]): () => number {
  let index = 0;

  return () => values[Math.min(index++, values.length - 1)] ?? 0;
}

describe("battle rewards", () => {
  it("CLEAR報酬は指定範囲の最小値を付与できる", () => {
    const reward = generateBattleReward("CLEAR", () => 0);

    expect(reward).toEqual({
      coin: 120,
      materials: {
        beastClaw: 1,
        fireStone: 1,
        oldCloth: 1,
        stonePiece: 1,
        magicShard: 1,
      },
    });
  });

  it("CLEAR報酬は指定範囲の最大値を付与できる", () => {
    const reward = generateBattleReward("CLEAR", () => 0.999);

    expect(reward.coin).toBe(180);
    expect(reward.materials.beastClaw).toBe(3);
    expect(reward.materials.fireStone).toBe(2);
    expect(reward.materials.oldCloth).toBe(3);
    expect(reward.materials.stonePiece).toBe(3);
    expect(reward.materials.magicShard).toBe(2);
  });

  it("FAILED報酬は少量コイン、ランダム素材、低確率の魔力の欠片を付与する", () => {
    const reward = generateBattleReward("FAILED", sequenceRandom([0, 0.5, 0.19]));

    expect(reward.coin).toBe(30);
    expect(reward.materials.oldCloth).toBe(1);
    expect(reward.materials.magicShard).toBe(1);
  });

  it("報酬を所持データへ加算できる", () => {
    const inventory = addRewardToInventory(createEmptyInventory(), {
      coin: 150,
      materials: {
        beastClaw: 2,
        fireStone: 1,
        oldCloth: 3,
        stonePiece: 1,
        magicShard: 2,
      },
    });

    expect(inventory.coin).toBe(150);
    expect(inventory.beastClaw).toBe(2);
    expect(inventory.magicShard).toBe(2);
  });
});

describe("inventory storage", () => {
  it("localStorageへ保存して読み戻せる", () => {
    const storage = new MemoryStorage();
    const inventory = {
      ...createEmptyInventory(),
      coin: 240,
      beastClaw: 2,
      magicShard: 1,
    };

    savePlayerInventory(inventory, storage);

    expect(storage.getItem(INVENTORY_STORAGE_KEY)).not.toBeNull();
    expect(loadPlayerInventory(storage)).toEqual(inventory);
  });

  it("保存値が壊れている場合は初期値へ戻す", () => {
    const storage = new MemoryStorage();
    storage.setItem(INVENTORY_STORAGE_KEY, "{broken");

    expect(loadPlayerInventory(storage)).toEqual(createEmptyInventory());
  });
});
