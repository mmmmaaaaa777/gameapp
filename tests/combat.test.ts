import { describe, expect, it } from "vitest";
import {
  BOSS_CHARGE_ATTACK_POWER,
  EMPTY_COOLDOWNS,
  PLAYER_BASE_DEFENSE,
  PLAYER_MAX_HP,
} from "../src/game/constants";
import {
  applyDamage,
  applyIncomingDamage,
  calculateDamage,
  canUseSkill,
  DAMAGE_CONSTANT,
  getBattleResult,
  setSkillCooldown,
} from "../src/game/combat";
import {
  createRetryBattleSelection,
  getBossStatsForDifficulty,
} from "../src/game/difficulty";
import { BOSS_OPTIONS } from "../src/game/menu";

describe("combat logic", () => {
  it("ダメージでHPが減る", () => {
    expect(applyDamage(100, 24, 100)).toBe(76);
  });

  it("HPが0未満にならない", () => {
    expect(applyDamage(8, 24, 100)).toBe(0);
  });

  it("ボスHP0でCLEAR条件になる", () => {
    expect(getBattleResult(100, 0)).toBe("CLEAR");
  });

  it("プレイヤーHP0でFAILED条件になる", () => {
    expect(getBattleResult(0, 120)).toBe("FAILED");
  });

  it("クールダウン中のスキルは発動できない", () => {
    const cooldowns = setSkillCooldown(EMPTY_COOLDOWNS, "quickSlash", 1200);

    expect(canUseSkill(cooldowns, "quickSlash")).toBe(false);
  });

  it("回避無敵中は被ダメージを受けない", () => {
    const result = applyIncomingDamage(PLAYER_MAX_HP, 12, PLAYER_MAX_HP, true);

    expect(result.nextHp).toBe(PLAYER_MAX_HP);
    expect(result.appliedDamage).toBe(0);
  });

  it("DAMAGE_CONSTANTは30である", () => {
    expect(DAMAGE_CONSTANT).toBe(30);
  });

  it("防御力0なら攻撃力部分がほぼそのまま通る", () => {
    expect(calculateDamage({ attackPower: 10, defense: 0 }).damage).toBe(11);
  });

  it("防御力5なら攻撃力10が約10ダメージになる", () => {
    expect(calculateDamage({ attackPower: 10, defense: 5 }).damage).toBe(10);
  });

  it("防御力5なら攻撃力16が約15ダメージになる", () => {
    expect(calculateDamage({ attackPower: 16, defense: 5 }).damage).toBe(15);
  });

  it("防御力30なら攻撃力部分がおおよそ半分になる", () => {
    expect(calculateDamage({ attackPower: 10, defense: 30 }).damage).toBe(6);
  });

  it("最低ダメージは1になる", () => {
    expect(
      calculateDamage({
        attackPower: 0,
        defense: 999,
        damageTakenMultiplier: 0,
      }).damage,
    ).toBe(1);
  });

  it("負の防御力は0として扱う", () => {
    const result = calculateDamage({ attackPower: 10, defense: -12 });

    expect(result.defense).toBe(0);
    expect(result.damage).toBe(11);
  });

  it("クリティカル時は1.5倍になる", () => {
    const normal = calculateDamage({ attackPower: 10, defense: 5 });
    const critical = calculateDamage({
      attackPower: 10,
      defense: 5,
      criticalMultiplier: 1.5,
    });

    expect(critical.rawDamage).toBeCloseTo(normal.rawDamage * 1.5, 5);
    expect(critical.damage).toBe(14);
  });

  it("属性相性倍率がダメージに反映される", () => {
    const result = calculateDamage({
      attackPower: 10,
      defense: 5,
      elementMultiplier: 1.25,
    });

    expect(result.elementMultiplier).toBe(1.25);
    expect(result.damage).toBe(12);
  });

  it("ボス攻撃もプレイヤー防御力を通して計算される", () => {
    const result = calculateDamage({
      attackPower: BOSS_CHARGE_ATTACK_POWER,
      defense: PLAYER_BASE_DEFENSE,
    });

    expect(result.damage).toBe(22);
  });

  it("Normal / Hard / Extreme でボスHPが変わる", () => {
    expect(getBossStatsForDifficulty("Normal").maxHp).toBe(3000);
    expect(getBossStatsForDifficulty("Hard").maxHp).toBe(6600);
    expect(getBossStatsForDifficulty("Extreme").maxHp).toBe(12000);
  });

  it("HardのHPはNormalより高く、ExtremeのHPはHardより高い", () => {
    expect(getBossStatsForDifficulty("Hard").maxHp).toBeGreaterThan(
      getBossStatsForDifficulty("Normal").maxHp,
    );
    expect(getBossStatsForDifficulty("Extreme").maxHp).toBeGreaterThan(
      getBossStatsForDifficulty("Hard").maxHp,
    );
  });

  it("もう一度出撃用の選択は同じ難易度を維持する", () => {
    const selection = {
      boss: BOSS_OPTIONS[1],
      difficulty: "Extreme" as const,
    };

    expect(createRetryBattleSelection(selection)).toEqual(selection);
  });
});
