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
  EQUIPMENT_DEFINITIONS,
  EQUIPMENT_LEVEL_STORAGE_KEY,
  EQUIPPED_STORAGE_KEY,
  getCraftModeEquipmentBySlot,
  getCraftableEquipmentIds,
  getEquipmentLevel,
  getEquipmentImageSrc,
  getEquipmentListForMode,
  getEquipmentLevelMultiplier,
  getRebirthModeEquipmentBySlot,
  getRebirthableWeaponIds,
  getUpgradeModeEquipmentBySlot,
  getUpgradeableEquipmentIds,
  loadEquippedEquipment,
  loadEquipmentLevels,
  loadOwnedEquipment,
  OWNED_EQUIPMENT_STORAGE_KEY,
  rebirthWeapon,
  saveEquippedEquipment,
  saveEquipmentLevels,
  saveOwnedEquipment,
  upgradeEquipment,
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

    expect(getEquipmentLevel(levels, "fireStoneSword")).toBe(1);
    expect(getEquipmentLevel(levels, "adventurerClothes")).toBe(1);
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

    const nextInventory = consumeEquipmentUpgradeCost(
      inventory,
      getEquipmentLevel(levels, "fireStoneSword"),
    );
    const nextLevels = upgradeEquipmentLevel(levels, "fireStoneSword");

    expect(nextInventory.coin).toBe(30);
    expect(nextInventory.magicShard).toBe(1);
    expect(getEquipmentLevel(nextLevels, "fireStoneSword")).toBe(2);
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

  it("Lv1からLv2へ強化すると素材とコインが減りLvが1上がる", () => {
    const owned = {
      ...createEmptyOwnedEquipment(),
      fireStoneSword: true,
    };
    const inventory = {
      ...createEmptyInventory(),
      coin: 50,
      magicShard: 1,
    };

    const result = upgradeEquipment(
      inventory,
      owned,
      createEmptyEquipmentLevels(),
      "fireStoneSword",
    );

    expect(result.result).toEqual({ success: true, nextLevel: 2 });
    expect(result.inventory.coin).toBe(0);
    expect(result.inventory.magicShard).toBe(0);
    expect(getEquipmentLevel(result.equipmentLevels, "fireStoneSword")).toBe(2);
  });

  it("コイン不足では強化できない", () => {
    const owned = {
      ...createEmptyOwnedEquipment(),
      fireStoneSword: true,
    };
    const inventory = {
      ...createEmptyInventory(),
      coin: 49,
      magicShard: 1,
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

  it("Lv倍率が各上位武器の攻撃力に反映される", () => {
    expect(getEquipmentLevelMultiplier(5)).toBe(1.6);

    expect(
      calculateEquipmentBonus(
        { ...createEmptyEquippedEquipment(), weapon: "fireStoneSword" },
        { fireStoneSword: 5 },
      ).attackBonus,
    ).toBe(10);
    expect(
      calculateEquipmentBonus(
        { ...createEmptyEquippedEquipment(), weapon: "waterMirrorSword" },
        { waterMirrorSword: 5 },
      ).attackBonus,
    ).toBe(16);
    expect(
      calculateEquipmentBonus(
        { ...createEmptyEquippedEquipment(), weapon: "azureStreamSword" },
        { azureStreamSword: 5 },
      ).attackBonus,
    ).toBe(22);
  });

  it("Lv5装備のバトル表示目安に合う補正を返す", () => {
    expect(
      calculateEquipmentBonus(
        { ...createEmptyEquippedEquipment(), weapon: "fireStoneSword" },
        { fireStoneSword: 5 },
      ).attackBonus + 10,
    ).toBe(20);
    expect(
      calculateEquipmentBonus(
        { ...createEmptyEquippedEquipment(), weapon: "waterMirrorSword" },
        { waterMirrorSword: 5 },
      ).attackBonus + 10,
    ).toBe(26);
    expect(
      calculateEquipmentBonus(
        { ...createEmptyEquippedEquipment(), weapon: "azureStreamSword" },
        { azureStreamSword: 5 },
      ).attackBonus + 10,
    ).toBe(32);
    expect(
      calculateEquipmentBonus(
        { ...createEmptyEquippedEquipment(), body: "adventurerClothes" },
        { adventurerClothes: 5 },
      ).maxHpBonus + 100,
    ).toBe(132);
  });

  it("転生時にLvを引き継ぎ、転生元のLv記録を削除する", () => {
    const owned = {
      ...createEmptyOwnedEquipment(),
      fireStoneSword: true,
    };
    const inventory = {
      ...createEmptyInventory(),
      coin: 250,
      beastClaw: 4,
      stonePiece: 3,
      magicShard: 2,
    };

    const result = rebirthWeapon(
      inventory,
      owned,
      { fireStoneSword: 3 },
      "fireStoneSword",
    );

    expect(result.result).toEqual({ success: true, nextWeaponId: "waterMirrorSword" });
    expect(result.ownedEquipment.fireStoneSword).toBe(false);
    expect(result.ownedEquipment.waterMirrorSword).toBe(true);
    expect(result.equipmentLevels.fireStoneSword).toBeUndefined();
    expect(getEquipmentLevel(result.equipmentLevels, "waterMirrorSword")).toBe(3);
  });

  it("転生可能と強化可能は装備通知印の条件に含められる", () => {
    const owned = {
      ...createEmptyOwnedEquipment(),
      fireStoneSword: true,
      travelerBandana: true,
    };
    const inventory = {
      ...createEmptyInventory(),
      coin: 300,
      beastClaw: 4,
      stonePiece: 3,
      magicShard: 2,
    };

    expect(getRebirthableWeaponIds(inventory, owned)).toEqual(["fireStoneSword"]);
    expect(getUpgradeableEquipmentIds(inventory, owned, createEmptyEquipmentLevels())).toContain(
      "travelerBandana",
    );
  });
  it("returns only craft targets for the selected equipment slot", () => {
    expect(getEquipmentListForMode("craft", "weapon").map((equipment) => equipment.id)).toEqual([
      "fireStoneSword",
    ]);
    expect(getCraftModeEquipmentBySlot("head").map((equipment) => equipment.id)).toEqual([
      "travelerBandana",
    ]);
    expect(getCraftModeEquipmentBySlot("body").map((equipment) => equipment.id)).toEqual([
      "adventurerClothes",
    ]);
    expect(getCraftModeEquipmentBySlot("feet").map((equipment) => equipment.id)).toEqual([
      "lightBoots",
    ]);
  });

  it("returns weapon rebirth targets and no armor targets for rebirth mode", () => {
    expect(getEquipmentListForMode("rebirth", "weapon").map((equipment) => equipment.id)).toEqual([
      "fireStoneSword",
      "waterMirrorSword",
      "azureStreamSword",
    ]);
    expect(getRebirthModeEquipmentBySlot("head")).toEqual([]);
    expect(getRebirthModeEquipmentBySlot("body")).toEqual([]);
    expect(getRebirthModeEquipmentBySlot("feet")).toEqual([]);
  });

  it("returns owned equipment only for upgrade mode by selected slot", () => {
    const owned = {
      ...createEmptyOwnedEquipment(),
      fireStoneSword: true,
      adventurerClothes: true,
    };

    expect(getEquipmentListForMode("upgrade", "weapon", owned).map((equipment) => equipment.id)).toEqual([
      "fireStoneSword",
    ]);
    expect(getUpgradeModeEquipmentBySlot("body", owned).map((equipment) => equipment.id)).toEqual([
      "adventurerClothes",
    ]);
    expect(getUpgradeModeEquipmentBySlot("head", owned)).toEqual([]);
  });

  it("defines placeholder image paths and falls back by equipment slot", () => {
    expect(EQUIPMENT_DEFINITIONS.every((equipment) => Boolean(equipment.imageSrc))).toBe(true);
    expect(getEquipmentImageSrc(EQUIPMENT_BY_ID.fireStoneSword)).toBe(
      "/assets/equipment/placeholder-weapon.svg",
    );
    expect(getEquipmentImageSrc({ slot: "head" })).toBe(
      "/assets/equipment/placeholder-head.svg",
    );
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

  it("リセット用のLv初期化は保存Lvを空にし、未保存装備はLv1として扱う", () => {
    const levels = createEmptyEquipmentLevels();

    expect(levels).toEqual({});
    expect(getEquipmentLevel(levels, "fireStoneSword")).toBe(1);
  });
});
