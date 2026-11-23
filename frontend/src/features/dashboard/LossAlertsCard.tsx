import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CACHE } from "@/lib/query/client";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { IconAlertTriangle } from "@/ui/icons";
import { toast } from "@/ui/ToastContext";
import { lossAlertsApi, type LossAlertExplanation } from "./api";

/**
 * AI-04: procedimentos com prejuízo ou margem baixa no mês. A lista vem de
 * uma regra do backend (nunca depende de IA); a IA só explica em texto, a
 * pedido, usando os mesmos números mostrados aqui.
 */
export function LossAlertsCard() {
  const query = useQuery({
    queryKey: ["financial", "loss-alerts", "this_month"],
    queryFn: () => lossAlertsApi.get("this_month"),
    ...CACHE.MONEY,
  });
  const [explanation, setExplanation] = useState<LossAlertExplanation | null>(null);
  const [explaining, setExplaining] = useState(false);

  const alerts = query.data?.alerts ?? [];
  if (alerts.length === 0) return null;

  async function handleExplain() {
    setExplaining(true);
    try {
      setExplanation(await lossAlertsApi.explain("this_month"));
    } catch {
      toast.error("Não foi possível gerar a explicação agora.");
    } finally {
      setExplaining(false);
    }
  }

  return (
    <section aria-label="Procedimentos para revisar" style={{ marginTop: "16px" }}>
      <h3 style={{ fontSize: "1rem", margin: "0 0 8px", display: "flex", gap: "8px", alignItems: "center" }}>
        <IconAlertTriangle width="16" height="16" />
        <span>Procedimentos para revisar</span>
      </h3>
      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "8px" }}>
        {alerts.map((a) => (
          <li
            key={a.procedure_id}
            style={{ border: "1px solid #e2e8f0", borderRadius: "8px", padding: "10px 12px", background: "#fff" }}
          >
            <strong>{a.procedure_name}</strong>
            <span style={{ marginLeft: "8px", fontSize: "0.8rem", fontWeight: 600 }}>
              {a.kind === "loss" ? "⚠ Prejuízo" : "↓ Margem baixa"}
            </span>
            <div style={{ fontSize: "0.85rem", color: "#475569", marginTop: "2px" }}>
              Lucro {formatBRL(money(a.net_profit))} sobre {formatBRL(money(a.gross_revenue))} faturados
              {a.margin_percent !== null ? ` (margem ${a.margin_percent}%)` : ""} · {a.session_count}{" "}
              {a.session_count === 1 ? "atendimento" : "atendimentos"}
            </div>
          </li>
        ))}
      </ul>
      <p style={{ fontSize: "0.75rem", color: "#64748b", margin: "6px 0 0" }}>
        Os valores podem incluir custos estimados.
      </p>
      <button
        type="button"
        className="button button--secondary tap-target"
        style={{ marginTop: "8px" }}
        onClick={handleExplain}
        disabled={explaining}
      >
        {explaining ? "Gerando…" : "Explicar com IA"}
      </button>
      {explanation && (
        <div style={{ marginTop: "10px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "12px" }}>
          <p style={{ margin: 0, fontSize: "0.9rem" }}>{explanation.text}</p>
          <span style={{ display: "block", marginTop: "6px", fontSize: "0.72rem", color: "#64748b" }}>
            {explanation.source === "ai"
              ? "Texto sugerido automaticamente a partir dos números acima."
              : "Texto padrão com os números acima."}
          </span>
        </div>
      )}
    </section>
  );
}
