import type { BattleEquipmentBonus, CooldownMap, ResultKind, SkillId } from "../types/game";
import { PLAYER_BASE_ATTACK, PLAYER_BASE_DEFENSE, PLAYER_MAX_HP } from "./constants";
import { clamp } from "./math";

export const DAMAGE_CONSTANT = 30;
export const NEUTRAL_ELEMENT_MULTIPLIER = 1;
export const NORMAL_CRITICAL_MULTIPLIER = 1;
export const NORMAL_SKILL_DAMAGE_MULTIPLIER = 1;
export const NORMAL_DOWN_MULTIPLIER = 1;
export const NORMAL_DAMAGE_TAKEN_MULTIPLIER = 1;

export interface DamageInput {
  attackPower: number;
  defense: number;
  elementMultiplier?: number;
  criticalMultiplier?: number;
  skillDamageMultiplier?: number;
  downMultiplier?: number;
  damageTakenMultiplier?: number;
}

export interface DamageResult {
  damage: number;
  rawDamage: number;
  attackPower: number;
  defense: number;
  elementMultiplier: number;
  criticalMultiplier: number;
  skillDamageMultiplier: number;
  downMultiplier: number;
  damageTakenMultiplier: number;
}

export interface PlayerBattleStats {
  attackPower: number;
  defense: number;
  maxHp: number;
  moveSpeedMultiplier: number;
}

export function getPlayerBattleStats(equipmentBonus: BattleEquipmentBonus): PlayerBattleStats {
  return {
    attackPower: PLAYER_BASE_ATTACK + equipmentBonus.attackBonus,
    defense: PLAYER_BASE_DEFENSE,
    maxHp: PLAYER_MAX_HP + equipmentBonus.maxHpBonus,
    moveSpeedMultiplier: equipmentBonus.moveSpeedMultiplier,
  };
}

export function calculateDamage({
  attackPower,
  defense,
  elementMultiplier = NEUTRAL_ELEMENT_MULTIPLIER,
  criticalMultiplier = NORMAL_CRITICAL_MULTIPLIER,
  skillDamageMultiplier = NORMAL_SKILL_DAMAGE_MULTIPLIER,
  downMultiplier = NORMAL_DOWN_MULTIPLIER,
  damageTakenMultiplier = NORMAL_DAMAGE_TAKEN_MULTIPLIER,
}: DamageInput): DamageResult {
  const effectiveDefense = Math.max(0, defense);
  const rawDamage =
    (1 + (attackPower * DAMAGE_CONSTANT) / (DAMAGE_CONSTANT + effectiveDefense)) *
    elementMultiplier *
    criticalMultiplier *
    skillDamageMultiplier *
    downMultiplier *
    damageTakenMultiplier;
  const damage = Math.max(1, Math.floor(rawDamage + 0.5));

  return {
    damage,
    rawDamage,
    attackPower,
    defense: effectiveDefense,
    elementMultiplier,
    criticalMultiplier,
    skillDamageMultiplier,
    downMultiplier,
    damageTakenMultiplier,
  };
}

export function rollCritical(criticalRate: number, rng: () => number = Math.random): boolean {
  return rng() < criticalRate;
}

export function getCriticalMultiplier(isCritical: boolean, criticalMultiplier: number): number {
  return isCritical ? criticalMultiplier : NORMAL_CRITICAL_MULTIPLIER;
}

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
