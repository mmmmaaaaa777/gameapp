import type { CooldownMap, ResultKind, SkillId } from "../types/game";
import { clamp } from "./math";

export function applyDamage(currentHp: number, damage: number, maxHp: number): number {
  return clamp(currentHp - Math.max(damage, 0), 0, maxHp);
}

export function getBattleResult(playerHp: number, bossHp: number): ResultKind | null {
  if (bossHp <= 0) {
    return "CLEAR";
  }

  if (playerHp <= 0) {
    return "FAILED";
  }

  return null;
}

export function tickCooldowns(cooldowns: CooldownMap, deltaMs: number): CooldownMap {
  return {
    quickSlash: Math.max(0, cooldowns.quickSlash - deltaMs),
    attributeBurst: Math.max(0, cooldowns.attributeBurst - deltaMs),
    breakArts: Math.max(0, cooldowns.breakArts - deltaMs),
  };
}

export function canUseSkill(cooldowns: CooldownMap, skillId: SkillId): boolean {
  return cooldowns[skillId] <= 0;
}

export function setSkillCooldown(
  cooldowns: CooldownMap,
  skillId: SkillId,
  cooldownMs: number,
): CooldownMap {
  return {
    ...cooldowns,
    [skillId]: Math.max(0, cooldownMs),
  };
}

export function applyIncomingDamage(
  currentHp: number,
  damage: number,
  maxHp: number,
  invulnerable: boolean,
): { nextHp: number; appliedDamage: number } {
  if (invulnerable) {
    return { nextHp: currentHp, appliedDamage: 0 };
  }

  const nextHp = applyDamage(currentHp, damage, maxHp);

  return {
    nextHp,
    appliedDamage: currentHp - nextHp,
  };
}
