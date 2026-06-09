import type { AttributeId } from "../types/game";
import type { EquipmentDefinition } from "../types/game";
import { ATTRIBUTE_BY_ID } from "./constants";

export type ElementRelation = "advantage" | "neutral" | "disadvantage";

const ELEMENT_ADVANTAGE: Readonly<Record<AttributeId, AttributeId>> = {
  water: "fire",
  fire: "wind",
  wind: "water",
  light: "dark",
  dark: "poison",
  poison: "light",
};

export const ELEMENT_MULTIPLIER = {
  advantage: 1.25,
  neutral: 1.0,
  disadvantage: 0.85,
} as const;

export function getElementRelation(attack: AttributeId, defense: AttributeId): ElementRelation {
  if (attack === defense) {
    return "neutral";
  }

  if (ELEMENT_ADVANTAGE[attack] === defense) {
    return "advantage";
  }

  if (ELEMENT_ADVANTAGE[defense] === attack) {
    return "disadvantage";
  }

  return "neutral";
}

export function getElementMultiplier(attack: AttributeId, defense: AttributeId): number {
  return ELEMENT_MULTIPLIER[getElementRelation(attack, defense)];
}

export function getAttackElement(
  weapon: EquipmentDefinition | null | undefined,
  selectedAttribute: AttributeId,
): AttributeId {
  return weapon?.element ?? selectedAttribute;
}

export function getDefenseElement(selectedAttribute: AttributeId): AttributeId {
  return selectedAttribute;
}

export function getElementRelationLabel(relation: ElementRelation): string {
  return relation === "advantage"
    ? "Advantage"
    : relation === "disadvantage"
      ? "Disadvantage"
      : "Neutral";
}

export function getAttributeLabel(attributeId: AttributeId): string {
  return ATTRIBUTE_BY_ID[attributeId].label;
}
