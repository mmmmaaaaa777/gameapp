export type AppScreen = "title" | "battle" | "result";

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
}

export interface BattleResult {
  kind: ResultKind;
  stats: BattleStats;
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
  bossHp: number;
  elapsedSeconds: number;
  dealtDamage: number;
  takenDamage: number;
  activeAttribute: AttributeId;
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
