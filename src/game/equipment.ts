import type {
  BattleEquipmentBonus,
  EquipmentDefinition,
  EquipmentId,
  EquipmentLevel,
  EquipmentLevelMap,
  EquipmentSlot,
  EquipmentUpgradeCost,
  EquippedEquipment,
  OwnedEquipment,
  MaterialId,
  PlayerInventory,
} from "../types/game";
import { MATERIAL_IDS, type InventoryStorage } from "./inventory";

export const OWNED_EQUIPMENT_STORAGE_KEY = "gameapp_demo_owned_equipment";
export const EQUIPPED_STORAGE_KEY = "gameapp_demo_equipped";
export const EQUIPMENT_LEVEL_STORAGE_KEY = "gameapp_demo_equipment_levels";
export const EQUIPMENT_MAX_LEVEL: EquipmentLevel = 5;

export const EQUIPMENT_LEVEL_MULTIPLIERS: Record<EquipmentLevel, number> = {
  1: 1,
  2: 1.15,
  3: 1.3,
  4: 1.45,
  5: 1.6,
};

export const EQUIPMENT_UPGRADE_COSTS: Partial<Record<EquipmentLevel, EquipmentUpgradeCost>> = {
  1: {
    coin: 50,
    magicShard: 1,
  },
  2: {
    coin: 100,
    magicShard: 2,
  },
  3: {
    coin: 150,
    magicShard: 3,
  },
  4: {
    coin: 250,
    magicShard: 5,
  },
};

export const EQUIPMENT_SLOT_LABELS: Record<EquipmentSlot, string> = {
  weapon: "武器",
  head: "頭",
  body: "胴体",
  feet: "足",
};

export const EQUIPMENT_DEFINITIONS: EquipmentDefinition[] = [
  {
    id: "fireStoneSword",
    slot: "weapon",
    name: "炎石の剣",
    effectLabel: "通常攻撃 +6",
    element: "fire",
    cost: {
      coin: 100,
      materials: {
        beastClaw: 3,
        fireStone: 2,
      },
    },
    effect: {
      attackBonus: 6,
    },
  },
  {
    id: "waterMirrorSword",
    slot: "weapon",
    name: "水鏡の剣",
    effectLabel: "通常攻撃 +10",
    element: "water",
    cost: {
      coin: 0,
      materials: {},
    },
    effect: {
      attackBonus: 10,
    },
    canCraft: false,
    rebirthFrom: "fireStoneSword",
  },
  {
    id: "azureStreamSword",
    slot: "weapon",
    name: "蒼流の剣",
    effectLabel: "通常攻撃 +14",
    element: "water",
    cost: {
      coin: 0,
      materials: {},
    },
    effect: {
      attackBonus: 14,
    },
    canCraft: false,
    rebirthFrom: "waterMirrorSword",
  },
  {
    id: "travelerBandana",
    slot: "head",
    name: "旅人のバンダナ",
    effectLabel: "最大HP+10",
    cost: {
      coin: 80,
      materials: {
        oldCloth: 3,
      },
    },
    effect: {
      maxHpBonus: 10,
    },
  },
  {
    id: "adventurerClothes",
    slot: "body",
    name: "冒険者の服",
    effectLabel: "最大HP+20",
    cost: {
      coin: 100,
      materials: {
        oldCloth: 5,
      },
    },
    effect: {
      maxHpBonus: 20,
    },
  },
  {
    id: "lightBoots",
    slot: "feet",
    name: "軽いブーツ",
    effectLabel: "移動速度+5%",
    cost: {
      coin: 80,
      materials: {
        oldCloth: 2,
        beastClaw: 2,
      },
    },
    effect: {
      moveSpeedPercentBonus: 5,
    },
  },
];

export const REBIRTH_CHAIN: Record<EquipmentId, EquipmentId | null> = {
  fireStoneSword: "waterMirrorSword",
  waterMirrorSword: "azureStreamSword",
  azureStreamSword: null,
  travelerBandana: null,
  adventurerClothes: null,
  lightBoots: null,
};

const WEAPON_REBIRTH_COSTS: Partial<
  Record<WeaponId, { coin: number; materials: Partial<Record<MaterialId, number>> }>
> = {
  fireStoneSword: {
    coin: 250,
    materials: {
      beastClaw: 4,
      stonePiece: 3,
      magicShard: 2,
    },
  },
  waterMirrorSword: {
    coin: 500,
    materials: {
      beastClaw: 6,
      stonePiece: 6,
      magicShard: 5,
    },
  },
};

export type WeaponId =
  | "fireStoneSword"
  | "waterMirrorSword"
  | "azureStreamSword";

export interface WeaponRebirthCost {
  coin: number;
  materials: Partial<Record<MaterialId, number>>;
}

export interface WeaponRebirthResult {
  success: boolean;
  nextWeaponId?: WeaponId;
}

export const WEAPON_REBIRTH_ORDER: WeaponId[] = ["fireStoneSword", "waterMirrorSword"];

function isWeaponId(value: EquipmentId | null): value is WeaponId {
  return (
    value === "fireStoneSword" ||
    value === "waterMirrorSword" ||
    value === "azureStreamSword"
  );
}

export function getNextRebirthWeapon(equipmentId: EquipmentId): WeaponId | null {
  const nextId = REBIRTH_CHAIN[equipmentId];
  return isWeaponId(nextId) ? nextId : null;
}

export function getWeaponRebirthCost(equipmentId: WeaponId): WeaponRebirthCost | null {
  return WEAPON_REBIRTH_COSTS[equipmentId] ?? null;
}

export function canAffordRebirthCost(
  inventory: PlayerInventory,
  cost: WeaponRebirthCost,
): boolean {
  if (inventory.coin < cost.coin) {
    return false;
  }

  return MATERIAL_IDS.every(
    (materialId) => inventory[materialId] >= (cost.materials[materialId] ?? 0),
  );
}

export function applyRebirthCost(
  inventory: PlayerInventory,
  cost: WeaponRebirthCost,
): PlayerInventory {
  return MATERIAL_IDS.reduce(
    (nextInventory, materialId) => ({
      ...nextInventory,
      [materialId]: nextInventory[materialId] - (cost.materials[materialId] ?? 0),
    }),
    {
      ...inventory,
      coin: inventory.coin - cost.coin,
    },
  );
}

export function canRebirthWeapon(
  inventory: PlayerInventory,
  ownedEquipment: OwnedEquipment,
  equipmentId: WeaponId,
): boolean {
  if (!ownedEquipment[equipmentId]) {
    return false;
  }

  const nextWeaponId = getNextRebirthWeapon(equipmentId);
  const cost = getWeaponRebirthCost(equipmentId);

  if (!nextWeaponId || !cost || ownedEquipment[nextWeaponId]) {
    return false;
  }

  return canAffordRebirthCost(inventory, cost);
}

export function getRebirthableWeaponIds(
  inventory: PlayerInventory,
  ownedEquipment: OwnedEquipment,
): WeaponId[] {
  return WEAPON_REBIRTH_ORDER.filter((weaponId) =>
    canRebirthWeapon(inventory, ownedEquipment, weaponId),
  );
}

export function hasRebirthableWeapon(
  inventory: PlayerInventory,
  ownedEquipment: OwnedEquipment,
): boolean {
  return getRebirthableWeaponIds(inventory, ownedEquipment).length > 0;
}

export function rebirthWeapon(
  inventory: PlayerInventory,
  ownedEquipment: OwnedEquipment,
  equipmentLevels: EquipmentLevelMap,
  weaponId: WeaponId,
): {
  result: WeaponRebirthResult;
  inventory: PlayerInventory;
  ownedEquipment: OwnedEquipment;
  equipmentLevels: EquipmentLevelMap;
} {
  if (!canRebirthWeapon(inventory, ownedEquipment, weaponId)) {
    return {
      result: { success: false },
      inventory,
      ownedEquipment,
      equipmentLevels,
    };
  }

  const nextWeaponId = getNextRebirthWeapon(weaponId);
  const cost = getWeaponRebirthCost(weaponId);

  if (!nextWeaponId || !cost) {
    return {
      result: { success: false },
      inventory,
      ownedEquipment,
      equipmentLevels,
    };
  }

  const nextEquipmentLevels = {
    ...equipmentLevels,
    [weaponId]: 1,
    [nextWeaponId]: getEquipmentLevel(equipmentLevels, weaponId),
  };

  return {
    result: {
      success: true,
      nextWeaponId,
    },
    inventory: applyRebirthCost(inventory, cost),
    ownedEquipment: {
      ...ownedEquipment,
      [weaponId]: false,
      [nextWeaponId]: true,
    },
    equipmentLevels: nextEquipmentLevels,
  };
}

export const EQUIPMENT_BY_ID: Record<EquipmentId, EquipmentDefinition> =
  EQUIPMENT_DEFINITIONS.reduce(
    (map, equipment) => ({
      ...map,
      [equipment.id]: equipment,
    }),
    {} as Record<EquipmentId, EquipmentDefinition>,
  );

const EQUIPMENT_IDS = EQUIPMENT_DEFINITIONS.map((equipment) => equipment.id);
const EQUIPMENT_SLOTS: EquipmentSlot[] = ["weapon", "head", "body", "feet"];

function getBrowserStorage(): InventoryStorage | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function readJson(storage: InventoryStorage | null, key: string): unknown {
  if (!storage) {
    return null;
  }

  try {
    const rawValue = storage.getItem(key);
    return rawValue ? JSON.parse(rawValue) : null;
  } catch {
    return null;
  }
}

function writeJson(storage: InventoryStorage | null, key: string, value: unknown): void {
  if (!storage) {
    return;
  }

  try {
    storage.setItem(key, JSON.stringify(value));
  } catch {
    // localStorage can be unavailable in private browsing or quota-limited environments.
  }
}

export function createEmptyOwnedEquipment(): OwnedEquipment {
  return EQUIPMENT_IDS.reduce(
    (owned, equipmentId) => ({
      ...owned,
      [equipmentId]: false,
    }),
    {} as OwnedEquipment,
  );
}

export function createEmptyEquippedEquipment(): EquippedEquipment {
  return {
    weapon: null,
    head: null,
    body: null,
    feet: null,
  };
}

export function createEmptyEquipmentLevels(): EquipmentLevelMap {
  return EQUIPMENT_IDS.reduce(
    (levels, equipmentId) => ({
      ...levels,
      [equipmentId]: 1,
    }),
    {} as EquipmentLevelMap,
  );
}

function normalizeEquipmentLevelValue(value: unknown): EquipmentLevel {
  const numericValue = typeof value === "number" ? Math.round(value) : 1;

  if (numericValue <= 1) {
    return 1;
  }

  if (numericValue >= EQUIPMENT_MAX_LEVEL) {
    return EQUIPMENT_MAX_LEVEL;
  }

  return numericValue as EquipmentLevel;
}

export function normalizeOwnedEquipment(value: unknown): OwnedEquipment {
  const source = isRecord(value) ? value : {};

  return EQUIPMENT_IDS.reduce(
    (owned, equipmentId) => ({
      ...owned,
      [equipmentId]: source[equipmentId] === true,
    }),
    {} as OwnedEquipment,
  );
}

export function normalizeEquippedEquipment(value: unknown): EquippedEquipment {
  const source = isRecord(value) ? value : {};

  return EQUIPMENT_SLOTS.reduce((equipped, slot) => {
    const equipmentId = source[slot];
    const definition =
      typeof equipmentId === "string"
        ? EQUIPMENT_BY_ID[equipmentId as EquipmentId]
        : undefined;

    return {
      ...equipped,
      [slot]: definition?.slot === slot ? definition.id : null,
    };
  }, createEmptyEquippedEquipment());
}

export function normalizeEquipmentLevels(value: unknown): EquipmentLevelMap {
  const source = isRecord(value) ? value : {};

  return EQUIPMENT_IDS.reduce(
    (levels, equipmentId) => ({
      ...levels,
      [equipmentId]: normalizeEquipmentLevelValue(source[equipmentId]),
    }),
    createEmptyEquipmentLevels(),
  );
}

export function loadOwnedEquipment(
  storage: InventoryStorage | null = getBrowserStorage(),
): OwnedEquipment {
  return normalizeOwnedEquipment(readJson(storage, OWNED_EQUIPMENT_STORAGE_KEY));
}

export function loadEquippedEquipment(
  storage: InventoryStorage | null = getBrowserStorage(),
): EquippedEquipment {
  return normalizeEquippedEquipment(readJson(storage, EQUIPPED_STORAGE_KEY));
}

export function loadEquipmentLevels(
  storage: InventoryStorage | null = getBrowserStorage(),
): EquipmentLevelMap {
  return normalizeEquipmentLevels(readJson(storage, EQUIPMENT_LEVEL_STORAGE_KEY));
}

export function saveOwnedEquipment(
  ownedEquipment: OwnedEquipment,
  storage: InventoryStorage | null = getBrowserStorage(),
): void {
  writeJson(storage, OWNED_EQUIPMENT_STORAGE_KEY, normalizeOwnedEquipment(ownedEquipment));
}

export function saveEquippedEquipment(
  equippedEquipment: EquippedEquipment,
  storage: InventoryStorage | null = getBrowserStorage(),
): void {
  writeJson(storage, EQUIPPED_STORAGE_KEY, normalizeEquippedEquipment(equippedEquipment));
}

export function saveEquipmentLevels(
  equipmentLevels: EquipmentLevelMap,
  storage: InventoryStorage | null = getBrowserStorage(),
): void {
  writeJson(storage, EQUIPMENT_LEVEL_STORAGE_KEY, normalizeEquipmentLevels(equipmentLevels));
}

export function canCraftEquipment(
  inventory: PlayerInventory,
  equipment: EquipmentDefinition,
): boolean {
  if (equipment.canCraft === false) {
    return false;
  }

  if (inventory.coin < equipment.cost.coin) {
    return false;
  }

  return MATERIAL_IDS.every((materialId) => {
    const required = equipment.cost.materials[materialId] ?? 0;
    return inventory[materialId] >= required;
  });
}

export function getCraftableEquipmentIds(
  inventory: PlayerInventory,
  ownedEquipment: OwnedEquipment,
): EquipmentId[] {
  return EQUIPMENT_DEFINITIONS.filter(
    (equipment) => !ownedEquipment[equipment.id] && canCraftEquipment(inventory, equipment),
  ).map((equipment) => equipment.id);
}

export function getEquipmentLevel(
  equipmentLevels: EquipmentLevelMap,
  equipmentId: EquipmentId,
): EquipmentLevel {
  return normalizeEquipmentLevelValue(equipmentLevels[equipmentId]);
}

export function getNextEquipmentLevel(level: EquipmentLevel): EquipmentLevel | null {
  if (level >= EQUIPMENT_MAX_LEVEL) {
    return null;
  }

  return (level + 1) as EquipmentLevel;
}

export function getEquipmentUpgradeCost(level: EquipmentLevel): EquipmentUpgradeCost | null {
  return EQUIPMENT_UPGRADE_COSTS[level] ?? null;
}

export function getScaledEquipmentEffect(
  equipment: EquipmentDefinition,
  level: EquipmentLevel,
) {
  const multiplier = EQUIPMENT_LEVEL_MULTIPLIERS[level];

  return {
    attackBonus:
      equipment.effect.attackBonus === undefined
        ? undefined
        : Math.round(equipment.effect.attackBonus * multiplier),
    maxHpBonus:
      equipment.effect.maxHpBonus === undefined
        ? undefined
        : Math.round(equipment.effect.maxHpBonus * multiplier),
    moveSpeedPercentBonus:
      equipment.effect.moveSpeedPercentBonus === undefined
        ? undefined
        : Math.round(equipment.effect.moveSpeedPercentBonus * multiplier),
  };
}

export function canUpgradeEquipment(
  inventory: PlayerInventory,
  ownedEquipment: OwnedEquipment,
  equipmentLevels: EquipmentLevelMap,
  equipment: EquipmentDefinition,
): boolean {
  if (!ownedEquipment[equipment.id]) {
    return false;
  }

  const cost = getEquipmentUpgradeCost(getEquipmentLevel(equipmentLevels, equipment.id));

  if (!cost) {
    return false;
  }

  return inventory.coin >= cost.coin && inventory.magicShard >= cost.magicShard;
}

export function getUpgradeableEquipmentIds(
  inventory: PlayerInventory,
  ownedEquipment: OwnedEquipment,
  equipmentLevels: EquipmentLevelMap,
): EquipmentId[] {
  return EQUIPMENT_DEFINITIONS.filter((equipment) =>
    canUpgradeEquipment(inventory, ownedEquipment, equipmentLevels, equipment),
  ).map((equipment) => equipment.id);
}

export function consumeEquipmentCost(
  inventory: PlayerInventory,
  equipment: EquipmentDefinition,
): PlayerInventory {
  return MATERIAL_IDS.reduce(
    (nextInventory, materialId) => ({
      ...nextInventory,
      [materialId]: nextInventory[materialId] - (equipment.cost.materials[materialId] ?? 0),
    }),
    {
      ...inventory,
      coin: inventory.coin - equipment.cost.coin,
    },
  );
}

export function consumeEquipmentUpgradeCost(
  inventory: PlayerInventory,
  level: EquipmentLevel,
): PlayerInventory {
  const cost = getEquipmentUpgradeCost(level);

  if (!cost) {
    return inventory;
  }

  return {
    ...inventory,
    coin: inventory.coin - cost.coin,
    magicShard: inventory.magicShard - cost.magicShard,
  };
}

export function equipEquipment(
  equippedEquipment: EquippedEquipment,
  equipmentId: EquipmentId,
): EquippedEquipment {
  const equipment = EQUIPMENT_BY_ID[equipmentId];

  return {
    ...equippedEquipment,
    [equipment.slot]: equipment.id,
  };
}

export function upgradeEquipmentLevel(
  equipmentLevels: EquipmentLevelMap,
  equipmentId: EquipmentId,
): EquipmentLevelMap {
  const currentLevel = getEquipmentLevel(equipmentLevels, equipmentId);
  const nextLevel = getNextEquipmentLevel(currentLevel);

  if (!nextLevel) {
    return normalizeEquipmentLevels(equipmentLevels);
  }

  return {
    ...normalizeEquipmentLevels(equipmentLevels),
    [equipmentId]: nextLevel,
  };
}

export function calculateEquipmentBonus(
  equippedEquipment: EquippedEquipment,
  equipmentLevels: EquipmentLevelMap = createEmptyEquipmentLevels(),
): BattleEquipmentBonus {
  return Object.values(equippedEquipment).reduce<BattleEquipmentBonus>(
    (bonus, equipmentId) => {
      if (!equipmentId) {
        return bonus;
      }

      const equipment = EQUIPMENT_BY_ID[equipmentId];
      const effect = getScaledEquipmentEffect(
        equipment,
        getEquipmentLevel(equipmentLevels, equipmentId),
      );

      return {
        attackBonus: bonus.attackBonus + (effect.attackBonus ?? 0),
        maxHpBonus: bonus.maxHpBonus + (effect.maxHpBonus ?? 0),
        moveSpeedMultiplier:
          bonus.moveSpeedMultiplier + (effect.moveSpeedPercentBonus ?? 0) / 100,
      };
    },
    {
      attackBonus: 0,
      maxHpBonus: 0,
      moveSpeedMultiplier: 1,
    },
  );
}
