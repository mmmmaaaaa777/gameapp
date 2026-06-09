import { describe, expect, it } from "vitest";
import {
  calculateEquipmentBonus,
  canCraftEquipment,
  canUpgradeEquipment,
  consumeEquipmentCost,
  consumeEquipmentUpgradeCost,
  createEmptyEquippedEquipment,
  createEmptyEquipmentLevels,
  createEmptyOwnedEquipment,
  equipEquipment,
  EQUIPMENT_BY_ID,
  EQUIPMENT_LEVEL_STORAGE_KEY,
  EQUIPPED_STORAGE_KEY,
  getCraftableEquipmentIds,
  getUpgradeableEquipmentIds,
  loadEquippedEquipment,
  loadEquipmentLevels,
  loadOwnedEquipment,
  OWNED_EQUIPMENT_STORAGE_KEY,
  saveEquippedEquipment,
  saveEquipmentLevels,
  saveOwnedEquipment,
  upgradeEquipmentLevel,
} from "../src/game/equipment";
import { createEmptyInventory } from "../src/game/inventory";
import type { EquippedEquipment } from "../src/types/game";

class MemoryStorage {
  private values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

describe("equipment crafting", () => {
  it("素材とコインが足りる場合だけ作成できる", () => {
    const inventory = {
      ...createEmptyInventory(),
      coin: 100,
      beastClaw: 3,
      fireStone: 2,
    };

    expect(canCraftEquipment(inventory, EQUIPMENT_BY_ID.fireStoneSword)).toBe(true);
    expect(canCraftEquipment(createEmptyInventory(), EQUIPMENT_BY_ID.fireStoneSword)).toBe(false);
  });

  it("未作成で素材が足りる装備だけ作成可能として返す", () => {
    const inventory = {
      ...createEmptyInventory(),
      coin: 180,
      beastClaw: 5,
      fireStone: 2,
      oldCloth: 0,
    };
    const ownedEquipment = {
      ...createEmptyOwnedEquipment(),
      travelerBandana: true,
    };

    expect(getCraftableEquipmentIds(inventory, ownedEquipment)).toEqual(["fireStoneSword"]);
  });

  it("作成時に必要素材とコインを消費する", () => {
    const inventory = {
      ...createEmptyInventory(),
      coin: 180,
      oldCloth: 6,
    };

    const nextInventory = consumeEquipmentCost(inventory, EQUIPMENT_BY_ID.travelerBandana);

    expect(nextInventory.coin).toBe(100);
    expect(nextInventory.oldCloth).toBe(3);
  });

  it("装備作成直後に使うLv初期値はLv1になる", () => {
    const levels = createEmptyEquipmentLevels();

    expect(levels.fireStoneSword).toBe(1);
    expect(levels.adventurerClothes).toBe(1);
  });

  it("作成済み装備を同じスロットへ装備できる", () => {
    const equipped = equipEquipment(createEmptyEquippedEquipment(), "fireStoneSword");

    expect(equipped.weapon).toBe("fireStoneSword");
    expect(equipped.head).toBeNull();
  });

  it("装備中効果からバトル補正を計算できる", () => {
    const equipped = {
      ...createEmptyEquippedEquipment(),
      weapon: "fireStoneSword",
      head: "travelerBandana",
      body: "adventurerClothes",
      feet: "lightBoots",
    } as const;

    expect(calculateEquipmentBonus(equipped)).toEqual({
      attackBonus: 6,
      maxHpBonus: 30,
      moveSpeedMultiplier: 1.05,
    });
  });

  it("強化するとLvが上がり、魔力の欠片とコインを消費する", () => {
    const inventory = {
      ...createEmptyInventory(),
      coin: 80,
      magicShard: 2,
    };
    const levels = createEmptyEquipmentLevels();

    const nextInventory = consumeEquipmentUpgradeCost(inventory, levels.fireStoneSword);
    const nextLevels = upgradeEquipmentLevel(levels, "fireStoneSword");

    expect(nextInventory.coin).toBe(30);
    expect(nextInventory.magicShard).toBe(1);
    expect(nextLevels.fireStoneSword).toBe(2);
  });

  it("素材不足では強化できない", () => {
    const owned = {
      ...createEmptyOwnedEquipment(),
      fireStoneSword: true,
    };
    const inventory = {
      ...createEmptyInventory(),
      coin: 999,
      magicShard: 0,
    };

    expect(
      canUpgradeEquipment(
        inventory,
        owned,
        createEmptyEquipmentLevels(),
        EQUIPMENT_BY_ID.fireStoneSword,
      ),
    ).toBe(false);
  });

  it("最大Lvを超えて強化できない", () => {
    const owned = {
      ...createEmptyOwnedEquipment(),
      fireStoneSword: true,
    };
    const levels = {
      ...createEmptyEquipmentLevels(),
      fireStoneSword: 5,
    } as const;
    const inventory = {
      ...createEmptyInventory(),
      coin: 999,
      magicShard: 999,
    };

    expect(canUpgradeEquipment(inventory, owned, levels, EQUIPMENT_BY_ID.fireStoneSword)).toBe(false);
    expect(upgradeEquipmentLevel(levels, "fireStoneSword").fireStoneSword).toBe(5);
  });

  it("強化可能な作成済み装備だけ返す", () => {
    const owned = {
      ...createEmptyOwnedEquipment(),
      travelerBandana: true,
    };
    const inventory = {
      ...createEmptyInventory(),
      coin: 50,
      magicShard: 1,
    };

    expect(getUpgradeableEquipmentIds(inventory, owned, createEmptyEquipmentLevels())).toEqual([
      "travelerBandana",
    ]);
  });

  it("強化倍率がバトル用ステータスに反映される", () => {
    const equipped = {
      ...createEmptyEquippedEquipment(),
      weapon: "fireStoneSword",
      body: "adventurerClothes",
      feet: "lightBoots",
    } as const;
    const levels = {
      ...createEmptyEquipmentLevels(),
      fireStoneSword: 5,
      adventurerClothes: 5,
      lightBoots: 5,
    } as const;

    expect(calculateEquipmentBonus(equipped, levels)).toEqual({
      attackBonus: 10,
      maxHpBonus: 32,
      moveSpeedMultiplier: 1.08,
    });
  });
});

describe("equipment storage", () => {
  it("作成済み装備と装備中状態を保存して読み戻せる", () => {
    const storage = new MemoryStorage();
    const owned = {
      ...createEmptyOwnedEquipment(),
      fireStoneSword: true,
    };
    const equipped: EquippedEquipment = {
      ...createEmptyEquippedEquipment(),
      weapon: "fireStoneSword",
    };

    saveOwnedEquipment(owned, storage);
    saveEquippedEquipment(equipped, storage);
    saveEquipmentLevels(
      {
        ...createEmptyEquipmentLevels(),
        fireStoneSword: 3,
      },
      storage,
    );

    expect(storage.getItem(OWNED_EQUIPMENT_STORAGE_KEY)).not.toBeNull();
    expect(storage.getItem(EQUIPPED_STORAGE_KEY)).not.toBeNull();
    expect(storage.getItem(EQUIPMENT_LEVEL_STORAGE_KEY)).not.toBeNull();
    expect(loadOwnedEquipment(storage)).toEqual(owned);
    expect(loadEquippedEquipment(storage)).toEqual(equipped);
    expect(loadEquipmentLevels(storage).fireStoneSword).toBe(3);
  });

  it("リセット用のLv初期化は全装備をLv1へ戻す", () => {
    expect(createEmptyEquipmentLevels()).toEqual({
      fireStoneSword: 1,
      travelerBandana: 1,
      adventurerClothes: 1,
      lightBoots: 1,
      waterMirrorSword: 1,
      azureStreamSword: 1,
    });
  });
});
