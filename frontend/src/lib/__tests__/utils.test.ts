import { describe, it, expect } from "vitest";
import { cn } from "../utils";

describe("cn", () => {
  it("merges multiple class strings", () => {
    expect(cn("foo", "bar", "baz")).toBe("foo bar baz");
  });

  it("filters out falsy values", () => {
    expect(cn("foo", false, null, undefined, "", "bar")).toBe("foo bar");
  });

  it("handles array inputs", () => {
    expect(cn(["foo", "bar"], "baz")).toBe("foo bar baz");
  });

  it("handles clsx-style object inputs", () => {
    expect(cn({ foo: true, bar: false, baz: true })).toBe("foo baz");
  });

  it("merges conflicting Tailwind padding classes, keeping the last", () => {
    expect(cn("p-4", "p-2")).toBe("p-2");
  });

  it("merges conflicting Tailwind text color classes, keeping the last", () => {
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });

  it("returns empty string when called with no arguments", () => {
    expect(cn()).toBe("");
  });

  it("combines conditional objects with plain strings", () => {
    const isActive = true;
    const isDisabled = false;
    expect(cn("base", { active: isActive, disabled: isDisabled })).toBe(
      "base active"
    );
  });
});
