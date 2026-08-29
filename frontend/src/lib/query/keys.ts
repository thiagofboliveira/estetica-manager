/**
 * Hierarquia desenhada para a INVALIDAÇÃO, não para organização. Tudo
 * que uma venda afeta fica sob o mesmo prefixo (qk.financial()) — um
 * invalidate resolve dashboard + retenção + pacotes + sessões de uma vez.
 */
export const qk = {
  all: ["app"] as const,

  financial: () => [...qk.all, "financial"] as const,
  dashboard: (range: { from: string; to: string }) =>
    [...qk.financial(), "dashboard", range] as const,
  retention: () => [...qk.financial(), "retention"] as const,
  retentionList: (filters?: { minValue?: string }) =>
    [...qk.retention(), "list", filters ?? {}] as const,
  packages: () => [...qk.financial(), "packages"] as const,
  packagesOpen: () => [...qk.packages(), "open"] as const,
  sessions: () => [...qk.financial(), "sessions"] as const,
  sessionsRange: (from: string, to: string) => [...qk.sessions(), { from, to }] as const,
  sales: () => [...qk.financial(), "sales"] as const,

  // Cadastros ficam FORA de financial: venda não invalida catálogo.
  patients: () => [...qk.all, "patients"] as const,
  patientsSearch: (q: string) => [...qk.patients(), "search", q] as const,
  patientDetail: (id: string) => [...qk.patients(), "detail", id] as const,

  procedures: () => [...qk.all, "procedures"] as const,
  settings: () => [...qk.all, "settings"] as const,
} as const;
