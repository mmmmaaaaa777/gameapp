import { describe, expect, it } from "vitest";
import {
  BOSS_DIFFICULTY_HP_MULTIPLIERS,
  createRetryBattleSelection,
  getBossStatsForDifficulty,
} from "../src/game/difficulty";
import { BOSS_OPTIONS } from "../src/game/menu";

const tutorialBoss = BOSS_OPTIONS[0];
const standardBoss = BOSS_OPTIONS[1];
const advancedBoss = BOSS_OPTIONS[2];

describe("boss base stats", () => {
  it("uses boss-specific Normal HP", () => {
    expect(getBossStatsForDifficulty("Normal", tutorialBoss).maxHp).toBe(1500);
    expect(getBossStatsForDifficulty("Normal", standardBoss).maxHp).toBe(3000);
    expect(getBossStatsForDifficulty("Normal", advancedBoss).maxHp).toBe(4200);
  });

  it("applies the Hard HP multiplier per boss", () => {
    expect(BOSS_DIFFICULTY_HP_MULTIPLIERS.Hard).toBe(2.2);
    expect(getBossStatsForDifficulty("Hard", tutorialBoss).maxHp).toBe(3300);
    expect(getBossStatsForDifficulty("Hard", standardBoss).maxHp).toBe(6600);
    expect(getBossStatsForDifficulty("Hard", advancedBoss).maxHp).toBe(9240);
  });

  it("applies the Extreme HP multiplier per boss", () => {
    expect(BOSS_DIFFICULTY_HP_MULTIPLIERS.Extreme).toBe(4);
    expect(getBossStatsForDifficulty("Extreme", tutorialBoss).maxHp).toBe(6000);
    expect(getBossStatsForDifficulty("Extreme", standardBoss).maxHp).toBe(12000);
    expect(getBossStatsForDifficulty("Extreme", advancedBoss).maxHp).toBe(16800);
  });

  it("keeps defense, attacks, break gauge, and down time different by boss", () => {
    const tutorial = getBossStatsForDifficulty("Normal", tutorialBoss);
    const standard = getBossStatsForDifficulty("Normal", standardBoss);
    const advanced = getBossStatsForDifficulty("Normal", advancedBoss);

    expect(tutorial.defense).toBe(2);
    expect(standard.defense).toBe(5);
    expect(advanced.defense).toBe(8);
    expect(tutorial.attacks).toEqual({ frontal: 8, charge: 14, area: 12 });
    expect(standard.attacks).toEqual({ frontal: 15, charge: 25, area: 20 });
    expect(advanced.attacks).toEqual({ frontal: 18, charge: 30, area: 24 });
    expect(tutorial.breakGauge).toBe(70);
    expect(standard.breakGauge).toBe(100);
    expect(advanced.breakGauge).toBe(130);
    expect(tutorial.downDurationMs).toBe(6500);
    expect(standard.downDurationMs).toBe(6000);
    expect(advanced.downDurationMs).toBe(5500);
  });

  it("orders tutorial, standard, and advanced bosses by strength", () => {
    const tutorial = getBossStatsForDifficulty("Normal", tutorialBoss);
    const standard = getBossStatsForDifficulty("Normal", standardBoss);
    const advanced = getBossStatsForDifficulty("Normal", advancedBoss);

    expect(tutorial.maxHp).toBeLessThan(standard.maxHp);
    expect(tutorial.defense).toBeLessThan(standard.defense);
    expect(tutorial.attacks.charge).toBeLessThan(standard.attacks.charge);
    expect(standard.maxHp).toBeLessThan(advanced.maxHp);
    expect(standard.defense).toBeLessThan(advanced.defense);
    expect(standard.attacks.charge).toBeLessThan(advanced.attacks.charge);
  });

  it("keeps the same boss and difficulty for retry", () => {
    const selection = {
      boss: advancedBoss,
      difficulty: "Extreme" as const,
    };

    expect(createRetryBattleSelection(selection)).toEqual(selection);
  });
});
