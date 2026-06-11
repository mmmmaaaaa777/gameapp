import { describe, expect, it } from "vitest";
import { createBattleBalanceSummary } from "../src/game/balance";
import { calculateEquipmentBonus, createEmptyEquippedEquipment } from "../src/game/equipment";
import { BOSS_OPTIONS } from "../src/game/menu";

describe("battle balance summary", () => {
  it("passes difficulty, boss HP, equipment, and elements into the sortie summary", () => {
    const equippedEquipment = {
      ...createEmptyEquippedEquipment(),
      weapon: "waterMirrorSword",
      body: "adventurerClothes",
    } as const;
    const equipmentLevels = {
      waterMirrorSword: 5,
      adventurerClothes: 5,
    } as const;
    const selection = {
      boss: BOSS_OPTIONS[1],
      difficulty: "Hard" as const,
    };

    const summary = createBattleBalanceSummary({
      activeAttribute: "light",
      equipmentBonus: calculateEquipmentBonus(equippedEquipment, equipmentLevels),
      equipmentLevels,
      equippedEquipment,
      selection,
    });

    expect(summary.difficulty).toBe("Hard");
    expect(summary.bossHp).toBe(6600);
    expect(summary.bossDefense).toBe(5);
    expect(summary.bossBreakGauge).toBe(100);
    expect(summary.bossDownDurationSeconds).toBe(6);
    expect(summary.bossRoleLabel).toBe("標準");
    expect(summary.rewardTier).toBe("standard");
    expect(summary.rewardTierCoinMultiplier).toBe(1);
    expect(summary.rewardTierMaterialMultiplier).toBe(1);
    expect(summary.difficultyRewardMultiplier).toBe(1.4);
    expect(summary.bossChargeAttackPower).toBe(25);
    expect(summary.bossAttribute).toBe("fire");
    expect(summary.equippedWeaponId).toBe("waterMirrorSword");
    expect(summary.weaponLevel).toBe(5);
    expect(summary.attackAttribute).toBe("water");
    expect(summary.defenseAttribute).toBe("light");
    expect(summary.attackRelation).toBe("advantage");
    expect(summary.defenseRelation).toBe("neutral");
    expect(summary.attackPower).toBe(26);
    expect(summary.maxHp).toBe(132);
    expect(summary.normalAttackDamage).toBe(29);
  });

  it("uses the selected attribute and no weapon level when no weapon is equipped", () => {
    const equippedEquipment = createEmptyEquippedEquipment();
    const selection = {
      boss: BOSS_OPTIONS[0],
      difficulty: "Normal" as const,
    };

    const summary = createBattleBalanceSummary({
      activeAttribute: "light",
      equipmentBonus: calculateEquipmentBonus(equippedEquipment),
      equipmentLevels: {},
      equippedEquipment,
      selection,
    });

    expect(summary.bossHp).toBe(1500);
    expect(summary.bossDefense).toBe(2);
    expect(summary.bossBreakGauge).toBe(70);
    expect(summary.bossDownDurationSeconds).toBe(6.5);
    expect(summary.bossRoleLabel).toBe("チュートリアル");
    expect(summary.rewardTier).toBe("tutorial");
    expect(summary.difficultyRewardMultiplier).toBe(1);
    expect(summary.equippedWeaponId).toBeNull();
    expect(summary.weaponLevel).toBeNull();
    expect(summary.attackAttribute).toBe("light");
    expect(summary.defenseAttribute).toBe("light");
    expect(summary.attackRelation).toBe("advantage");
    expect(summary.defenseRelation).toBe("disadvantage");
    expect(summary.normalAttackDamage).toBe(13);
  });
});
