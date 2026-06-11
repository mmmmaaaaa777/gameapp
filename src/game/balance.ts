import type {
  AttributeId,
  BattleEquipmentBonus,
  EquipmentId,
  EquipmentLevel,
  EquipmentLevelMap,
  EquippedEquipment,
} from "../types/game";
import { calculateDamage, getPlayerBattleStats } from "./combat";
import { INITIAL_ATTRIBUTE } from "./constants";
import { getBossStatsForSelection } from "./difficulty";
import {
  getAttackElement,
  getAttributeLabel,
  getDefenseElement,
  getElementMultiplier,
  getElementRelation,
  type ElementRelation,
} from "./elements";
import { EQUIPMENT_BY_ID, getEquipmentLevel } from "./equipment";
import type { BossSelection } from "./menu";
import {
  getDifficultyRewardMultiplier,
  getRewardTierMultiplier,
} from "./rewards";

export interface BattleBalanceSummary {
  difficulty: string;
  bossName: string;
  bossHp: number;
  bossDefense: number;
  bossBreakGauge: number;
  bossDownDurationSeconds: number;
  bossRoleLabel: string;
  bossRoleDescription: string;
  rewardTier: string;
  rewardTierCoinMultiplier: number;
  rewardTierMaterialMultiplier: number;
  difficultyRewardMultiplier: number;
  bossFrontalAttackPower: number;
  bossChargeAttackPower: number;
  bossAreaAttackPower: number;
  bossAttribute: AttributeId;
  bossAttributeLabel: string;
  equippedWeaponId: EquipmentId | null;
  equippedWeaponName: string;
  weaponLevel: EquipmentLevel | null;
  attackAttribute: AttributeId;
  attackAttributeLabel: string;
  defenseAttribute: AttributeId;
  defenseAttributeLabel: string;
  attackRelation: ElementRelation;
  attackRelationLabel: string;
  attackMultiplier: number;
  defenseRelation: ElementRelation;
  defenseRelationLabel: string;
  defenseMultiplier: number;
  attackPower: number;
  defense: number;
  maxHp: number;
  normalAttackDamage: number;
}

interface CreateBattleBalanceSummaryInput {
  activeAttribute?: AttributeId;
  equipmentBonus: BattleEquipmentBonus;
  equipmentLevels: EquipmentLevelMap;
  equippedEquipment: EquippedEquipment;
  selection: BossSelection;
}

const RELATION_LABELS: Record<ElementRelation, string> = {
  advantage: "有利",
  neutral: "等倍",
  disadvantage: "不利",
};

function formatMultiplier(multiplier: number): string {
  return `x${multiplier.toFixed(2)}`;
}

export function getBattleRelationLabel(relation: ElementRelation, multiplier: number): string {
  return `${RELATION_LABELS[relation]} ${formatMultiplier(multiplier)}`;
}

export function createBattleBalanceSummary({
  activeAttribute = INITIAL_ATTRIBUTE,
  equipmentBonus,
  equipmentLevels,
  equippedEquipment,
  selection,
}: CreateBattleBalanceSummaryInput): BattleBalanceSummary {
  const bossStats = getBossStatsForSelection(selection);
  const playerStats = getPlayerBattleStats(equipmentBonus);
  const equippedWeaponId = equippedEquipment.weapon;
  const equippedWeapon = equippedWeaponId ? EQUIPMENT_BY_ID[equippedWeaponId] : null;
  const attackAttribute = getAttackElement(equippedWeapon, activeAttribute);
  const defenseAttribute = getDefenseElement(activeAttribute);
  const attackRelation = getElementRelation(attackAttribute, selection.boss.attributeId);
  const defenseRelation = getElementRelation(selection.boss.attributeId, defenseAttribute);
  const attackMultiplier = getElementMultiplier(attackAttribute, selection.boss.attributeId);
  const defenseMultiplier = getElementMultiplier(selection.boss.attributeId, defenseAttribute);
  const rewardTierMultiplier = getRewardTierMultiplier(selection.boss.rewardTier);
  const normalAttackDamage = calculateDamage({
    attackPower: playerStats.attackPower,
    defense: bossStats.defense,
    elementMultiplier: attackMultiplier,
  }).damage;

  return {
    difficulty: selection.difficulty,
    bossName: selection.boss.name,
    bossHp: bossStats.maxHp,
    bossDefense: bossStats.defense,
    bossBreakGauge: bossStats.breakGauge,
    bossDownDurationSeconds: bossStats.downDurationMs / 1000,
    bossRoleLabel: bossStats.roleLabel,
    bossRoleDescription: bossStats.roleDescription,
    rewardTier: selection.boss.rewardTier,
    rewardTierCoinMultiplier: rewardTierMultiplier.coinMultiplier,
    rewardTierMaterialMultiplier: rewardTierMultiplier.materialMultiplier,
    difficultyRewardMultiplier: getDifficultyRewardMultiplier(selection.difficulty),
    bossFrontalAttackPower: bossStats.attacks.frontal,
    bossChargeAttackPower: bossStats.attacks.charge,
    bossAreaAttackPower: bossStats.attacks.area,
    bossAttribute: selection.boss.attributeId,
    bossAttributeLabel: getAttributeLabel(selection.boss.attributeId),
    equippedWeaponId,
    equippedWeaponName: equippedWeapon?.name ?? "初期武器",
    weaponLevel: equippedWeaponId ? getEquipmentLevel(equipmentLevels, equippedWeaponId) : null,
    attackAttribute,
    attackAttributeLabel: getAttributeLabel(attackAttribute),
    defenseAttribute,
    defenseAttributeLabel: getAttributeLabel(defenseAttribute),
    attackRelation,
    attackRelationLabel: getBattleRelationLabel(attackRelation, attackMultiplier),
    attackMultiplier,
    defenseRelation,
    defenseRelationLabel: getBattleRelationLabel(defenseRelation, defenseMultiplier),
    defenseMultiplier,
    attackPower: playerStats.attackPower,
    defense: playerStats.defense,
    maxHp: playerStats.maxHp,
    normalAttackDamage,
  };
}
