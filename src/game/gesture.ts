import { GESTURE_THRESHOLDS } from "./constants";

export type GestureKind = "tap" | "swipe" | "flick" | "none";

export interface GestureInput {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  durationMs: number;
}

export interface GestureResult {
  kind: GestureKind;
  distancePx: number;
  velocityPxPerMs: number;
  dx: number;
  dy: number;
}

export function classifyGesture(input: GestureInput): GestureResult {
  const dx = input.endX - input.startX;
  const dy = input.endY - input.startY;
  const distancePx = Math.hypot(dx, dy);
  const safeDuration = Math.max(input.durationMs, 1);
  const velocityPxPerMs = distancePx / safeDuration;

  if (
    input.durationMs <= GESTURE_THRESHOLDS.flickMaxDurationMs &&
    distancePx >= GESTURE_THRESHOLDS.flickMinDistancePx &&
    velocityPxPerMs >= GESTURE_THRESHOLDS.flickMinVelocityPxPerMs
  ) {
    return { kind: "flick", distancePx, velocityPxPerMs, dx, dy };
  }

  if (
    input.durationMs <= GESTURE_THRESHOLDS.tapMaxDurationMs &&
    distancePx <= GESTURE_THRESHOLDS.tapMaxDistancePx
  ) {
    return { kind: "tap", distancePx, velocityPxPerMs, dx, dy };
  }

  if (distancePx >= GESTURE_THRESHOLDS.swipeStartDistancePx) {
    return { kind: "swipe", distancePx, velocityPxPerMs, dx, dy };
  }

  return { kind: "none", distancePx, velocityPxPerMs, dx, dy };
}

export function hasSwipeMovement(startX: number, startY: number, x: number, y: number): boolean {
  return Math.hypot(x - startX, y - startY) >= GESTURE_THRESHOLDS.swipeStartDistancePx;
}

export function shouldHandleCanvasPointer(isUiControl: boolean): boolean {
  return !isUiControl;
}
