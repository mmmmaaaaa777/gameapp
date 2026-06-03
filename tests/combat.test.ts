import { describe, expect, it } from "vitest";
import { EMPTY_COOLDOWNS, PLAYER_MAX_HP } from "../src/game/constants";
import {
  applyDamage,
  applyIncomingDamage,
  canUseSkill,
  getBattleResult,
  setSkillCooldown,
} from "../src/game/combat";

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
});
