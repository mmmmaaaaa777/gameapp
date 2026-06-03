import type {
  AttributeConfig,
  AttributeId,
  CooldownMap,
  SkillDefinition,
  SkillId,
} from "../types/game";

export const FIELD_RADIUS = 8;
export const PLAYER_MAX_HP = 100;
export const BOSS_MAX_HP = 300;
export const PLAYER_SPEED_UNITS_PER_SEC = 4.2;
export const ATTACK_RANGE = 3.5;
export const ATTACK_DAMAGE = 10;
export const ATTACK_COOLDOWN_MS = 250;
export const DODGE_DISTANCE = 2.2;
export const DODGE_DURATION_MS = 310;
export const DODGE_COOLDOWN_MS = 800;
export const DODGE_INVULNERABLE_MS = 360;
export const SHOCKWAVE_INTERVAL_MS = 3500;
export const SHOCKWAVE_WARNING_MS = 850;
export const SHOCKWAVE_RANGE = 3.05;
export const SHOCKWAVE_DAMAGE = 12;
export const BEAM_INTERVAL_MS = 5200;
export const BEAM_WARNING_MS = 750;
export const BEAM_DAMAGE = 8;
export const BEAM_WIDTH = 0.72;
export const UI_SYNC_INTERVAL_MS = 80;

export const GESTURE_THRESHOLDS = {
  tapMaxDurationMs: 180,
  tapMaxDistancePx: 12,
  swipeStartDistancePx: 18,
  flickMaxDurationMs: 220,
  flickMinDistancePx: 70,
  flickMinVelocityPxPerMs: 0.45,
} as const;

export const ATTRIBUTES: AttributeConfig[] = [
  {
    id: "light",
    label: "煌",
    description: "金色の光",
    color: 0xffd95a,
    accent: 0xffffff,
    cssColor: "#ffd95a",
    cssAccent: "#fff6c6",
  },
  {
    id: "dark",
    label: "魔",
    description: "黒紫の魔力",
    color: 0x5c2d91,
    accent: 0xc47cff,
    cssColor: "#8d57df",
    cssAccent: "#3a214f",
  },
  {
    id: "fire",
    label: "炎",
    description: "赤い火花",
    color: 0xff4d2e,
    accent: 0xffb033,
    cssColor: "#ff6542",
    cssAccent: "#ffb033",
  },
  {
    id: "poison",
    label: "毒",
    description: "紫の霧",
    color: 0x9b5ad7,
    accent: 0xa4ff73,
    cssColor: "#a367dc",
    cssAccent: "#a4ff73",
  },
  {
    id: "water",
    label: "水",
    description: "青い波紋",
    color: 0x2f8dff,
    accent: 0x8ee7ff,
    cssColor: "#3e9cff",
    cssAccent: "#8ee7ff",
  },
  {
    id: "wind",
    label: "風",
    description: "緑の風",
    color: 0x48d37f,
    accent: 0xccffd5,
    cssColor: "#48d37f",
    cssAccent: "#ccffd5",
  },
];

export const ATTRIBUTE_BY_ID: Record<AttributeId, AttributeConfig> =
  ATTRIBUTES.reduce(
    (map, attribute) => ({
      ...map,
      [attribute.id]: attribute,
    }),
    {} as Record<AttributeId, AttributeConfig>,
  );

export const SKILLS: SkillDefinition[] = [
  {
    id: "quickSlash",
    label: "クイックスラッシュ",
    shortLabel: "斬",
    damage: 20,
    cooldownMs: 2000,
    range: 4.0,
    effectScale: 1,
  },
  {
    id: "attributeBurst",
    label: "属性バースト",
    shortLabel: "属",
    damage: 35,
    cooldownMs: 5000,
    range: 4.8,
    effectScale: 1.55,
  },
  {
    id: "breakArts",
    label: "ブレイクアーツ",
    shortLabel: "破",
    damage: 60,
    cooldownMs: 10000,
    range: 5.6,
    effectScale: 2.05,
  },
];

export const SKILL_BY_ID: Record<SkillId, SkillDefinition> = SKILLS.reduce(
  (map, skill) => ({
    ...map,
    [skill.id]: skill,
  }),
  {} as Record<SkillId, SkillDefinition>,
);

export const EMPTY_COOLDOWNS: CooldownMap = {
  quickSlash: 0,
  attributeBurst: 0,
  breakArts: 0,
};

export const INITIAL_ATTRIBUTE: AttributeId = "light";
