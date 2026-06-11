import { describe, expect, it } from "vitest";
import {
  addDemoMaterialsToInventory,
  addRewardToInventory,
  createEmptyInventory,
  DEMO_MATERIAL_GRANT,
  INVENTORY_STORAGE_KEY,
  loadPlayerInventory,
  savePlayerInventory,
} from "../src/game/inventory";
import { BOSS_OPTIONS } from "../src/game/menu";
import {
  applyRewardScaling,
  generateBattleReward,
  getDifficultyRewardMultiplier,
  getRewardTierMultiplier,
} from "../src/game/rewards";

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
  it("CLEAR reward can generate the previous standard Normal minimum", () => {
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

  it("CLEAR reward can generate the previous standard Normal maximum", () => {
    const reward = generateBattleReward("CLEAR", () => 0.999);

    expect(reward.coin).toBe(180);
    expect(reward.materials.beastClaw).toBe(3);
    expect(reward.materials.fireStone).toBe(2);
    expect(reward.materials.oldCloth).toBe(3);
    expect(reward.materials.stonePiece).toBe(3);
    expect(reward.materials.magicShard).toBe(2);
  });

  it("FAILED reward keeps the existing small coin, random material, and shard chance behavior", () => {
    const reward = generateBattleReward("FAILED", sequenceRandom([0, 0.5, 0.19]));

    expect(reward.coin).toBe(30);
    expect(reward.materials.oldCloth).toBe(1);
    expect(reward.materials.magicShard).toBe(1);
  });

  it("standard Normal rewards remain the existing baseline", () => {
    const reward = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Normal",
      rewardTier: "standard",
    });

    expect(getRewardTierMultiplier("standard")).toEqual({
      coinMultiplier: 1,
      materialMultiplier: 1,
    });
    expect(getDifficultyRewardMultiplier("Normal")).toBe(1);
    expect(reward.coin).toBe(120);
    expect(reward.materials.beastClaw).toBe(1);
    expect(reward.materials.magicShard).toBe(1);
  });

  it("tutorial Normal gives fewer coins than standard Normal", () => {
    const tutorial = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Normal",
      rewardTier: BOSS_OPTIONS[0].rewardTier,
    });
    const standard = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Normal",
      rewardTier: BOSS_OPTIONS[1].rewardTier,
    });

    expect(tutorial.coin).toBeLessThan(standard.coin);
    expect(tutorial.coin).toBe(84);
  });

  it("advanced Normal gives more coins than standard Normal", () => {
    const standard = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Normal",
      rewardTier: BOSS_OPTIONS[1].rewardTier,
    });
    const advanced = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Normal",
      rewardTier: BOSS_OPTIONS[2].rewardTier,
    });

    expect(advanced.coin).toBeGreaterThan(standard.coin);
    expect(advanced.coin).toBe(150);
  });

  it("difficulty reward multipliers increase rewards", () => {
    const normal = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Normal",
      rewardTier: "standard",
    });
    const hard = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Hard",
      rewardTier: "standard",
    });
    const extreme = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Extreme",
      rewardTier: "standard",
    });

    expect(hard.coin).toBeGreaterThan(normal.coin);
    expect(extreme.coin).toBeGreaterThan(hard.coin);
    expect(hard.coin).toBe(168);
    expect(extreme.coin).toBe(240);
  });

  it("same reward tier gives more rewards at higher difficulty", () => {
    const tutorialNormal = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Normal",
      rewardTier: "tutorial",
    });
    const tutorialHard = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Hard",
      rewardTier: "tutorial",
    });
    const advancedNormal = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Normal",
      rewardTier: "advanced",
    });
    const advancedExtreme = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Extreme",
      rewardTier: "advanced",
    });

    expect(tutorialHard.coin).toBeGreaterThan(tutorialNormal.coin);
    expect(advancedExtreme.coin).toBeGreaterThan(advancedNormal.coin);
  });

  it("CLEAR materials keep at least one item after scaling", () => {
    const reward = applyRewardScaling(
      {
        coin: 120,
        materials: {
          beastClaw: 1,
          fireStone: 1,
          oldCloth: 1,
          stonePiece: 1,
          magicShard: 1,
        },
      },
      "CLEAR",
      {
        difficulty: "Normal",
        rewardTier: "tutorial",
      },
    );

    expect(Object.values(reward.materials).every((amount) => amount >= 1)).toBe(true);
  });

  it("adds rewards to inventory", () => {
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

  it("adds scaled rewards to inventory and keeps storage shape", () => {
    const storage = new MemoryStorage();
    const reward = generateBattleReward("CLEAR", () => 0, {
      difficulty: "Extreme",
      rewardTier: "advanced",
    });
    const inventory = addRewardToInventory(createEmptyInventory(), reward);

    expect(reward.coin).toBe(300);
    expect(reward.materials.beastClaw).toBe(2);
    expect(inventory.coin).toBe(300);
    expect(inventory.beastClaw).toBe(2);

    savePlayerInventory(inventory, storage);
    expect(loadPlayerInventory(storage)).toEqual(inventory);
  });

  it("adds demo materials and coins for development checks", () => {
    const inventory = addDemoMaterialsToInventory(createEmptyInventory());

    expect(inventory).toEqual(DEMO_MATERIAL_GRANT);
  });

  it("adds demo materials to the existing inventory counts", () => {
    const inventory = addDemoMaterialsToInventory({
      ...createEmptyInventory(),
      coin: 5,
      beastClaw: 1,
      fireStone: 2,
      oldCloth: 3,
      stonePiece: 4,
      magicShard: 5,
    });

    expect(inventory.coin).toBe(2005);
    expect(inventory.beastClaw).toBe(31);
    expect(inventory.fireStone).toBe(32);
    expect(inventory.oldCloth).toBe(33);
    expect(inventory.stonePiece).toBe(34);
    expect(inventory.magicShard).toBe(35);
  });
});

describe("inventory storage", () => {
  it("saves inventory to localStorage-compatible storage and loads it", () => {
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

  it("falls back to the initial value when saved data is broken", () => {
    const storage = new MemoryStorage();
    storage.setItem(INVENTORY_STORAGE_KEY, "{broken");

    expect(loadPlayerInventory(storage)).toEqual(createEmptyInventory());
  });
});

describe("demo inventory grant storage", () => {
  it("keeps the inventory storage shape after demo grant and reset", () => {
    const storage = new MemoryStorage();
    const grantedInventory = addDemoMaterialsToInventory(createEmptyInventory());

    savePlayerInventory(grantedInventory, storage);
    expect(loadPlayerInventory(storage)).toEqual(DEMO_MATERIAL_GRANT);

    savePlayerInventory(createEmptyInventory(), storage);
    expect(loadPlayerInventory(storage)).toEqual(createEmptyInventory());
  });
});
