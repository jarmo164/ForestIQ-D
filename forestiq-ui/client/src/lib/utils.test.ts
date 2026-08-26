import { describe, expect, it } from "vitest";

import { cn } from "./utils";

describe("cn", () => {
  it("ühendab klassid ja eelistab Tailwindi konfliktis viimast väärtust", () => {
    expect(cn("px-2", "px-4", "font-semibold")).toBe("px-4 font-semibold");
  });
});
