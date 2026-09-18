import { describe, expect, it } from "vitest";

import { lossAnalysisCsv, lossAnalysisQuery } from "./p1Operations";

describe("P1 loss analytics helpers", () => {
  it("preserves date, seller and previous-stage filters in the API query", () => {
    const query = new URLSearchParams(lossAnalysisQuery({
      from: "2026-09-01",
      to: "2026-09-30",
      sellerId: "  seller-42  ",
      previousStage: "NEGOTIATION",
    }));
    expect(query.get("from")).toBe("2026-09-01");
    expect(query.get("to")).toBe("2026-09-30");
    expect(query.get("sellerId")).toBe("seller-42");
    expect(query.get("previousStage")).toBe("NEGOTIATION");
  });

  it("exports filtered loss-analysis rows as escaped CSV", () => {
    const csv = lossAnalysisCsv([{
      reasonCode: "PRICE",
      reasonLabel: 'Price, "too high"',
      sellerId: "seller-1",
      previousStage: "EVALUATION",
      count: 3,
    }]);
    expect(csv).toContain('"reasonCode","reasonLabel","sellerId","previousStage","count"');
    expect(csv).toContain('"Price, ""too high"""');
    expect(csv).toContain('"3"');
  });
});
