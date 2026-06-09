import type { BattleReward, MaterialId, MaterialRewardMap, PlayerInventory } from "../types/game";

export const INVENTORY_STORAGE_KEY = "gameapp_demo_inventory";

export const MATERIAL_IDS = [
  "beastClaw",
  "fireStone",
  "oldCloth",
  "stonePiece",
  "magicShard",
] as const satisfies readonly MaterialId[];

export const MATERIAL_LABELS: Record<MaterialId, string> = {
  beastClaw: "獣の爪",
  fireStone: "炎石",
  oldCloth: "古びた布",
  stonePiece: "石片",
  magicShard: "魔力の欠片",
};

export const DEMO_MATERIAL_GRANT: PlayerInventory = {
  coin: 2000,
  beastClaw: 30,
  fireStone: 30,
  oldCloth: 30,
  stonePiece: 30,
  magicShard: 30,
};

export type InventoryStorage = Pick<Storage, "getItem" | "setItem">;

export function createEmptyMaterialMap(): MaterialRewardMap {
  return MATERIAL_IDS.reduce(
    (materials, materialId) => ({
      ...materials,
      [materialId]: 0,
    }),
    {} as MaterialRewardMap,
  );
}

export function createEmptyInventory(): PlayerInventory {
  return {
    coin: 0,
    ...createEmptyMaterialMap(),
  };
}

export function addRewardToInventory(
  inventory: PlayerInventory,
  reward: BattleReward,
): PlayerInventory {
  return MATERIAL_IDS.reduce(
    (nextInventory, materialId) => ({
      ...nextInventory,
      [materialId]: nextInventory[materialId] + reward.materials[materialId],
    }),
    {
      ...inventory,
      coin: inventory.coin + reward.coin,
    },
  );
}

export function addDemoMaterialsToInventory(inventory: PlayerInventory): PlayerInventory {
  return MATERIAL_IDS.reduce(
    (nextInventory, materialId) => ({
      ...nextInventory,
      [materialId]: nextInventory[materialId] + DEMO_MATERIAL_GRANT[materialId],
    }),
    {
      ...inventory,
      coin: inventory.coin + DEMO_MATERIAL_GRANT.coin,
    },
  );
}

function getBrowserStorage(): InventoryStorage | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function toInventoryCount(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.max(0, Math.floor(value))
    : 0;
}

export function normalizeInventory(value: unknown): PlayerInventory {
  const source = isRecord(value) ? value : {};

  return {
    coin: toInventoryCount(source.coin),
    beastClaw: toInventoryCount(source.beastClaw),
    fireStone: toInventoryCount(source.fireStone),
    oldCloth: toInventoryCount(source.oldCloth),
    stonePiece: toInventoryCount(source.stonePiece),
    magicShard: toInventoryCount(source.magicShard),
  };
}

export function loadPlayerInventory(storage: InventoryStorage | null = getBrowserStorage()): PlayerInventory {
  if (!storage) {
    return createEmptyInventory();
  }

  try {
    const rawValue = storage.getItem(INVENTORY_STORAGE_KEY);

    if (!rawValue) {
      return createEmptyInventory();
    }

    return normalizeInventory(JSON.parse(rawValue));
  } catch {
    return createEmptyInventory();
  }
}

export function savePlayerInventory(
  inventory: PlayerInventory,
  storage: InventoryStorage | null = getBrowserStorage(),
): void {
  if (!storage) {
    return;
  }

  try {
    storage.setItem(INVENTORY_STORAGE_KEY, JSON.stringify(normalizeInventory(inventory)));
  } catch {
    // localStorage can be unavailable in private browsing or quota-limited environments.
  }
}
