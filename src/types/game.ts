export type AppScreen =
  | "home"
  | "bossSelect"
  | "sortiePrep"
  | "battle"
  | "result"
  | "formation"
  | "equipment"
  | "settings";

export type ResultKind = "CLEAR" | "FAILED";

export type AttributeId =
  | "light"
  | "dark"
  | "fire"
  | "poison"
  | "water"
  | "wind";

export interface AttributeConfig {
  id: AttributeId;
  label: string;
  description: string;
  color: number;
  accent: number;
  cssColor: string;
  cssAccent: string;
}

export type SkillId = "quickSlash" | "attributeBurst" | "breakArts";

export interface SkillDefinition {
  id: SkillId;
  label: string;
  shortLabel: string;
  damage: number;
  cooldownMs: number;
  range: number;
  effectScale: number;
}

export type CooldownMap = Record<SkillId, number>;

export interface BattleStats {
  elapsedSeconds: number;
  dealtDamage: number;
  takenDamage: number;
  dodgeSuccessCount: number;
  breakCount: number;
}

export interface BattleResult {
  kind: ResultKind;
  stats: BattleStats;
}

export type MaterialId =
  | "beastClaw"
  | "fireStone"
  | "oldCloth"
  | "stonePiece"
  | "magicShard";

export type PlayerInventory = {
  coin: number;
} & Record<MaterialId, number>;

export type MaterialRewardMap = Record<MaterialId, number>;

export interface BattleReward {
  coin: number;
  materials: MaterialRewardMap;
}

export interface Vec2 {
  x: number;
  y: number;
}

export interface Vec3XZ {
  x: number;
  z: number;
}

export interface BattleUiSnapshot {
  playerHp: number;
  playerMaxHp: number;
  playerAttackPower: number;
  playerDefense: number;
  bossHp: number;
  bossMaxHp: number;
  elapsedSeconds: number;
  dealtDamage: number;
  takenDamage: number;
  activeAttribute: AttributeId;
  normalAttackDamage: number;
  skillDamagePreview: Record<SkillId, number>;
  skillCooldowns: CooldownMap;
  attackReady: boolean;
  dodgeReady: boolean;
  notice: string;
}

export interface SceneSnapshot {
  playerPosition: Vec3XZ;
  playerAngle: number;
  bossPosition: Vec3XZ;
  playerHpRatio: number;
  bossHpRatio: number;
  activeAttribute: AttributeId;
  isDodging: boolean;
  playerAttackPulse: number;
  playerMoveIntensity: number;
  bossHurt: boolean;
  shockwaveWarning?: {
    radius: number;
    progress: number;
  };
  beamWarning?: {
    direction: Vec3XZ;
    progress: number;
  };
}

export type EquipmentSlot = "weapon" | "head" | "body" | "feet";

export type EquipmentId =
  | "fireStoneSword"
  | "travelerBandana"
  | "adventurerClothes"
  | "lightBoots"
  | "waterMirrorSword"
  | "azureStreamSword";

export interface EquipmentCost {
  coin: number;
  materials: Partial<Record<MaterialId, number>>;
}

export interface EquipmentEffect {
  attackBonus?: number;
  maxHpBonus?: number;
  moveSpeedPercentBonus?: number;
}

export interface EquipmentDefinition {
  id: EquipmentId;
  slot: EquipmentSlot;
  name: string;
  imageSrc?: string;
  effectLabel: string;
  cost: EquipmentCost;
  effect: EquipmentEffect;
  element?: AttributeId;
  canCraft?: boolean;
  rebirthFrom?: EquipmentId;
}

export type OwnedEquipment = Record<EquipmentId, boolean>;

export type EquippedEquipment = Record<EquipmentSlot, EquipmentId | null>;

export type EquipmentLevel = 1 | 2 | 3 | 4 | 5;

export type EquipmentLevelMap = Partial<Record<EquipmentId, EquipmentLevel>>;

export interface EquipmentUpgradeCost {
  coin: number;
  magicShard: number;
}

export interface BattleEquipmentBonus {
  attackBonus: number;
  maxHpBonus: number;
  moveSpeedMultiplier: number;
}
