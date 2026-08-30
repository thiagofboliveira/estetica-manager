import { queryClient } from "./client";
import { qk } from "./keys";

/**
 * Uma venda muda: dashboard, retenção (o paciente saiu da lista de
 * "sumidos"), pacotes em aberto, histórico do paciente, agenda.
 * refetchType: "active" refaz já o que está na tela; sem isso ela
 * navega para Retornos e vê dado velho.
 */
export async function invalidateAfterSale(patientId: string) {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: qk.financial(), refetchType: "active" }),
    queryClient.invalidateQueries({ queryKey: qk.patientDetail(patientId) }),
  ]);
}

/** Mudar taxa/comissão recalcula TODO lucro histórico exibido. */
export async function invalidateAfterSettingsChange() {
  await queryClient.invalidateQueries({ queryKey: qk.financial() });
  await queryClient.invalidateQueries({ queryKey: qk.settings() });
}

/** Agendar sessão de pacote: PENDING -> SCHEDULED. Dashboard NÃO muda
 * (agendar não gera receita) — não invalide o que não mudou. */
export async function invalidateAfterScheduling() {
  await queryClient.invalidateQueries({ queryKey: qk.packages() });
  await queryClient.invalidateQueries({ queryKey: qk.sessions() });
}

/** Despesa fixa só muda a lista/detalhe dela e o dashboard (fixed_expenses_total
 * / net_profit_after_fixed_expenses) — retenção, pacotes, sessões e vendas
 * não têm relação com isso. */
export async function invalidateAfterFixedExpenseChange() {
  await queryClient.invalidateQueries({ queryKey: qk.expenses() });
  await queryClient.invalidateQueries({ queryKey: [...qk.financial(), "dashboard"] });
}
