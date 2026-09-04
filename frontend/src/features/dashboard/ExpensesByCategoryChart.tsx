import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { formatBRL, formatBRLCompact } from "@/lib/money/format";
import { money, type Money } from "@/lib/money/money";
import { useExpensesByCategory } from "./hooks";
import { IconBuilding } from "@/ui/icons";
import styles from "./charts.module.css";

const BAR_COLORS = ["var(--accent)", "var(--accent-rose)", "var(--warning)", "var(--success)", "var(--text-muted)"];

/**
 * Despesas fixas correntes agrupadas por categoria (texto livre —
 * ver backend/app/models/fixed_expense.py: sem taxonomia fechada de
 * propósito). "Sem categoria" é um balde legítimo, não um erro.
 */
export function ExpensesByCategoryChart() {
  const query = useExpensesByCategory();

  return (
    <section className={styles.card} aria-label="Despesas correntes por tipo">
      <div className={styles.header}>
        <div className={styles.iconBadge}>
          <IconBuilding width="16" height="16" />
        </div>
        <h3 className={styles.title}>Despesas correntes por tipo</h3>
      </div>
      <p className={styles.subtitle}>
        Despesas fixas vigentes, valor mensal (anual dividido por 12).
      </p>

      <AsyncBoundary
        query={query}
        skeleton={<div className={styles.emptyChart}>Carregando despesas…</div>}
        empty={
          <div className={styles.emptyChart}>
            Nenhuma despesa fixa cadastrada. Configure em Configurações → Despesas fixas.
          </div>
        }
        isEmpty={(data) => data.rows.length === 0}
      >
        {(data) => {
          const chartData = data.rows.map((row) => ({
            category: row.category,
            // Só para a altura da barra (SVG exige número) — o valor
            // exibido em texto/tooltip vem sempre de formatBRL(money(...))
            // sobre a string original, nunca deste número.
            value: Number(row.monthly_amount),
            monthlyAmountRaw: row.monthly_amount,
          }));

          return (
            <div className={styles.chartWrap}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                  <XAxis
                    type="number"
                    tickFormatter={(v: number) => formatBRLCompact(money(String(v)) as Money)}
                    tick={{ fill: "var(--text-muted)", fontSize: 11 }}
                    stroke="var(--border)"
                  />
                  <YAxis
                    type="category"
                    dataKey="category"
                    width={110}
                    tick={{ fill: "var(--text)", fontSize: 12.5 }}
                    stroke="var(--border)"
                  />
                  <Tooltip
                    cursor={{ fill: "var(--bg-subtle)" }}
                    contentStyle={{
                      background: "var(--bg-card)",
                      border: "1px solid var(--border)",
                      borderRadius: 8,
                      fontSize: 13,
                      color: "var(--text-h)",
                    }}
                    formatter={(_value, _name, item) => [
                      formatBRL(money(item.payload.monthlyAmountRaw)),
                      "Valor mensal",
                    ]}
                  />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={entry.category} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          );
        }}
      </AsyncBoundary>
    </section>
  );
}
