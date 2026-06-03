import { describe, expect, it } from "vitest";
import { classifyGesture, shouldHandleCanvasPointer } from "../src/game/gesture";

describe("classifyGesture", () => {
  it("短時間かつ小距離ならtapになる", () => {
    const result = classifyGesture({
      startX: 100,
      startY: 100,
      endX: 106,
      endY: 104,
      durationMs: 120,
    });

    expect(result.kind).toBe("tap");
  });

  it("長押し移動ならswipeになる", () => {
    const result = classifyGesture({
      startX: 100,
      startY: 100,
      endX: 145,
      endY: 106,
      durationMs: 480,
    });

    expect(result.kind).toBe("swipe");
  });

  it("短時間かつ高速で一定距離以上ならflickになる", () => {
    const result = classifyGesture({
      startX: 100,
      startY: 100,
      endX: 182,
      endY: 106,
      durationMs: 130,
    });

    expect(result.kind).toBe("flick");
  });

  it("flick条件を満たす場合はtapよりflickが優先される", () => {
    const result = classifyGesture({
      startX: 100,
      startY: 100,
      endX: 174,
      endY: 100,
      durationMs: 160,
    });

    expect(result.kind).toBe("flick");
  });

  it("UIボタン操作はCanvas処理対象から外せる", () => {
    expect(shouldHandleCanvasPointer(true)).toBe(false);
    expect(shouldHandleCanvasPointer(false)).toBe(true);
  });
});
