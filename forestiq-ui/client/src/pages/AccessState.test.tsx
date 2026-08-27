import { renderToStaticMarkup } from "react-dom/server";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

import { AccessDenied, AuthenticationRequired } from "./AccessState";

describe("access state components", () => {
  beforeAll(() => {
    vi.stubGlobal("location", new URL("http://localhost/"));
    vi.stubGlobal("history", { pushState: vi.fn(), replaceState: vi.fn() });
  });

  afterAll(() => {
    vi.unstubAllGlobals();
  });
  it("renders a distinct authentication-required state", () => {
    const html = renderToStaticMarkup(<AuthenticationRequired />);

    expect(html).toContain("Sisselogimine on vajalik");
    expect(html).toContain("Ava sisselogimine");
    expect(html).not.toContain("403");
  });

  it("renders a distinct forbidden state and confirms protected data was not loaded", () => {
    const html = renderToStaticMarkup(<AccessDenied />);

    expect(html).toContain("403 — puudub ligipääsuõigus");
    expect(html).toContain("Keelatud lehe andmeid ei ole laaditud.");
    expect(html).toContain("Tagasi töölauale");
  });
});
