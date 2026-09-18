export type LossAnalysisRow = { reasonCode: string; reasonLabel: string; sellerId: string | null; previousStage: string; count: number };
export type LossAnalysisFilters = { from?: string; to?: string; sellerId?: string; previousStage?: string };

export function lossAnalysisQuery(filters: LossAnalysisFilters) {
  const params = new URLSearchParams();
  if (filters.from) params.set("from", filters.from);
  if (filters.to) params.set("to", filters.to);
  if (filters.sellerId?.trim()) params.set("sellerId", filters.sellerId.trim());
  if (filters.previousStage) params.set("previousStage", filters.previousStage);
  return params.toString();
}

export function lossAnalysisCsv(rows: LossAnalysisRow[]) {
  const data: Array<Array<string | number>> = [
    ["reasonCode", "reasonLabel", "sellerId", "previousStage", "count"],
    ...rows.map((row) => [row.reasonCode, row.reasonLabel, row.sellerId || "", row.previousStage, row.count]),
  ];
  return data.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(",")).join("\n");
}
