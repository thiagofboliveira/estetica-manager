/**
 * Hierarquia desenhada para a INVALIDAÇÃO, não para organização. Tudo
 * que uma venda afeta fica sob o mesmo prefixo (qk.financial()) — um
 * invalidate resolve dashboard + retenção + pacotes + sessões de uma vez.
 */
export const qk = {
  all: ["app"] as const,

  financial: () => [...qk.all, "financial"] as const,
  dashboard: (params: { period: string; date_from?: string; date_to?: string }) =>
    [...qk.financial(), "dashboard", params] as const,
  retention: () => [...qk.financial(), "retention"] as const,
  retentionList: (filters?: { minValue?: string }) =>
    [...qk.retention(), "list", filters ?? {}] as const,
  packages: () => [...qk.financial(), "packages"] as const,
  packagesOpen: () => [...qk.packages(), "open"] as const,
  sessions: () => [...qk.financial(), "sessions"] as const,
  sessionsRange: (from: string, to: string) => [...qk.sessions(), { from, to }] as const,
  freeSlots: (date: string) => [...qk.sessions(), "free-slots", date] as const,
  sales: () => [...qk.financial(), "sales"] as const,

  // Cadastros ficam FORA de financial: venda não invalida catálogo.
  patients: () => [...qk.all, "patients"] as const,
  patientsSearch: (q: string) => [...qk.patients(), "search", q] as const,
  patientDetail: (id: string) => [...qk.patients(), "detail", id] as const,

  procedures: () => [...qk.all, "procedures"] as const,
  settings: () => [...qk.all, "settings"] as const,
  financialSettings: () => [...qk.settings(), "financial"] as const,
  paymentFeeRules: () => [...qk.settings(), "payment-fee-rules"] as const,
  fixedExpenses: () => [...qk.financial(), "fixed-expenses"] as const,
  procedureRanking: (params: { period: string; date_from?: string; date_to?: string }) =>
    [...qk.financial(), "procedure-ranking", params] as const,
  roi: (params: { period: string; date_from?: string; date_to?: string }) =>
    [...qk.financial(), "roi", params] as const,
} as const;
