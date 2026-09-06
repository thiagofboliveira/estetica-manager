import { useEffect, useState } from "react";
import { weeklySummaryApi, type WeeklySummary } from "./api";
import { formatBRL } from "@/lib/money/format";
import type { Money } from "@/lib/money/money";
import { toast } from "@/ui/ToastContext";

export function WeeklySummarySection() {
  const [summary, setSummary] = useState<WeeklySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [useCurrentWeek, setUseCurrentWeek] = useState(false);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    weeklySummaryApi
      .get(useCurrentWeek)
      .then((data) => {
        if (isMounted) setSummary(data);
      })
      .catch(() => {
        // fail-safe
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [useCurrentWeek]);

  async function handleToggle(enabled: boolean) {
    if (!summary) return;
    setUpdating(true);
    try {
      await weeklySummaryApi.updateSettings(enabled);
      setSummary({ ...summary, weekly_summary_enabled: enabled });
      toast.success(
        enabled
          ? "Resumo semanal ativado! Você receberá atualizações toda semana."
          : "Resumo semanal pausado."
      );
    } catch {
      toast.error("Não foi possível atualizar a configuração do resumo semanal.");
    } finally {
      setUpdating(false);
    }
  }

  function handleCopyOrOpen() {
    if (!summary) return;
    if (summary.whatsapp_url) {
      window.open(summary.whatsapp_url, "_blank");
    } else {
      navigator.clipboard.writeText(summary.whatsapp_message);
      toast.success("Mensagem do resumo copiada! Cole no seu WhatsApp.");
    }
  }

  return (
    <section className="settings-section" style={{ marginTop: "24px" }}>
      <hr className="settings-divider" />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", marginBottom: "12px" }}>
        <div>
          <h2 style={{ fontSize: "1.1rem", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
            📊 Resumo Semanal no WhatsApp
            <span style={{ fontSize: "0.75rem", background: "#ecfdf5", color: "#065f46", padding: "2px 8px", borderRadius: "12px", fontWeight: 500 }}>
              Retenção Automática
            </span>
          </h2>
          <p style={{ margin: "4px 0 0", fontSize: "0.85rem", color: "#64748b" }}>
            Receba toda segunda-feira o fechamento da semana: faturamento, lucro real e quantas pacientes chamar.
          </p>
        </div>

        {summary && (
          <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "0.85rem", fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={summary.weekly_summary_enabled}
              disabled={updating}
              onChange={(e) => handleToggle(e.target.checked)}
              style={{ width: "18px", height: "18px" }}
            />
            <span>{summary.weekly_summary_enabled ? "Ativo" : "Pausado"}</span>
          </label>
        )}
      </div>

      {loading ? (
        <p style={{ fontSize: "0.85rem", color: "#64748b" }}>Carregando dados do resumo semanal…</p>
      ) : summary ? (
        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 600, color: "#334155" }}>
              Prévia do Resumo ({summary.period_start} a {summary.period_end})
            </span>
            <div style={{ display: "flex", gap: "6px" }}>
              <button
                type="button"
                className="button--text"
                style={{ fontSize: "0.75rem", padding: "2px 8px", background: !useCurrentWeek ? "#e2e8f0" : "transparent", borderRadius: "4px" }}
                onClick={() => setUseCurrentWeek(false)}
              >
                Semana Passada
              </button>
              <button
                type="button"
                className="button--text"
                style={{ fontSize: "0.75rem", padding: "2px 8px", background: useCurrentWeek ? "#e2e8f0" : "transparent", borderRadius: "4px" }}
                onClick={() => setUseCurrentWeek(true)}
              >
                Semana Atual (em andamento)
              </button>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "10px", marginBottom: "16px" }}>
            <div style={{ background: "#fff", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <span style={{ fontSize: "0.72rem", color: "#64748b", display: "block" }}>Faturamento</span>
              <strong style={{ fontSize: "0.95rem", color: "#0f172a" }}>{formatBRL(summary.gross_revenue as Money)}</strong>
            </div>
            <div style={{ background: "#fff", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <span style={{ fontSize: "0.72rem", color: "#64748b", display: "block" }}>Lucro Real (I1)</span>
              <strong style={{ fontSize: "0.95rem", color: "#16a34a" }}>{formatBRL(summary.net_profit as Money)}</strong>
            </div>
            <div style={{ background: "#fff", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <span style={{ fontSize: "0.72rem", color: "#64748b", display: "block" }}>Atendimentos</span>
              <strong style={{ fontSize: "0.95rem", color: "#0f172a" }}>{summary.sales_count}</strong>
            </div>
            <div style={{ background: "#fff", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <span style={{ fontSize: "0.72rem", color: "#64748b", display: "block" }}>Chamar esta semana</span>
              <strong style={{ fontSize: "0.95rem", color: "#d97706" }}>{summary.pending_opportunities_count}</strong>
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
            <button
              type="button"
              className="button button--primary"
              style={{ fontSize: "0.85rem", padding: "8px 16px" }}
              onClick={handleCopyOrOpen}
            >
              📲 {summary.whatsapp_url ? "Abrir prévia no WhatsApp" : "Copiar mensagem para WhatsApp"}
            </button>
            <span style={{ fontSize: "0.75rem", color: "#64748b" }}>
              🔒 Inclui link de descadastro em 1 clique (V5-02) no rodapé.
            </span>
          </div>
        </div>
      ) : null}
    </section>
  );
}
