import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { formatBRL, formatBRLCompact } from "@/lib/money/format";
import { cmp, money, type Money } from "@/lib/money/money";
import { IconCalendar, IconTrendingUp } from "@/ui/icons";
import type { DashboardParams, ProcedureRankingRow } from "./api";
import { useProcedureRanking } from "./hooks";
import styles from "./charts.module.css";

const TOP_N = 10;
// Cobre o catálogo de procedimentos de qualquer profissional autônoma
// real; se algum dia isso não bastar, os gráficos passam a refletir só
// os 100 primeiros por faturamento — a tabela paginada abaixo continua
// mostrando todos, então o dado nunca fica escondido, só o gráfico.
const CHART_SAMPLE_SIZE = 100;

type Props = {
  params: DashboardParams;
};

// F5-03: extraídos como componentes de topo para virarem slides
// independentes no carrossel de gráficos (cada um pede seus próprios
// dados via useProcedureRanking, que já cacheia por query key idêntica
// — não duplica a requisição entre os dois).

export function ProfitByServiceChart({ params }: Props) {
  const query = useProcedureRanking({ ...params, page: 1, page_size: CHART_SAMPLE_SIZE });

  const topByProfit = useMemo(() => {
    if (!query.data) return [];
    return [...query.data.rows]
      .sort((a, b) => cmp(money(b.net_profit), money(a.net_profit)))
      .slice(0, TOP_N);
  }, [query.data]);

  return (
    <section className={styles.card} aria-label="Lucro por serviço">
      <div className={styles.header}>
        <div className={styles.iconBadge}>
          <IconTrendingUp width="16" height="16" />
        </div>
        <h3 className={styles.title}>Lucro por serviço</h3>
      </div>
      <p className={styles.subtitle}>Top {TOP_N} procedimentos por lucro real no período.</p>

      <AsyncBoundary
        query={query}
        skeleton={<div className={styles.emptyChart}>Carregando…</div>}
        empty={<div className={styles.emptyChart}>Nenhuma venda no período.</div>}
        isEmpty={() => topByProfit.length === 0}
      >
        {() => <ProcedureBarChart rows={topByProfit} valueField="net_profit" barColor="var(--accent)" valueLabel="Lucro real" />}
      </AsyncBoundary>
    </section>
  );
}

export function AppointmentsByServiceChart({ params }: Props) {
  const query = useProcedureRanking({ ...params, page: 1, page_size: CHART_SAMPLE_SIZE });

  const topByAppointments = useMemo(() => {
    if (!query.data) return [];
    return [...query.data.rows]
      .filter((row) => row.session_count > 0)
      .sort((a, b) => b.session_count - a.session_count)
      .slice(0, TOP_N);
  }, [query.data]);

  const mostOffered = topByAppointments[0];

  return (
    <section className={styles.card} aria-label="Atendimentos por serviço">
      <div className={styles.header}>
        <div className={styles.iconBadge}>
          <IconCalendar width="16" height="16" />
        </div>
        <h3 className={styles.title}>Atendimentos por serviço</h3>
      </div>
      <p className={styles.subtitle}>Sessões concluídas por procedimento no período.</p>

      <AsyncBoundary
        query={query}
        skeleton={<div className={styles.emptyChart}>Carregando…</div>}
        empty={
          <div className={styles.emptyChart}>
            Nenhum atendimento concluído no período — sessões agendadas ainda não contam.
          </div>
        }
        isEmpty={() => topByAppointments.length === 0}
      >
        {() => (
          <>
            {mostOffered && (
              <p className={styles.highlight}>
                🏆 Serviço mais oferecido: <strong>{mostOffered.procedure_name}</strong> (
                {mostOffered.session_count}{" "}
                {mostOffered.session_count === 1 ? "atendimento" : "atendimentos"})
              </p>
            )}
            <AppointmentsBarChart rows={topByAppointments} />
          </>
        )}
      </AsyncBoundary>
    </section>
  );
}

function ProcedureBarChart({
  rows,
  valueField,
  barColor,
  valueLabel,
}: {
  rows: ProcedureRankingRow[];
  valueField: "net_profit" | "gross_revenue";
  barColor: string;
  valueLabel: string;
}) {
  const chartData = rows.map((row) => ({
    name: row.procedure_name,
    // Só para a altura da barra — o rótulo/tooltip sempre lê o texto
    // original de moneyRaw via formatBRL(money(...)), nunca este número.
    value: Number(row[valueField]),
    moneyRaw: row[valueField],
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
            dataKey="name"
            width={130}
            tick={{ fill: "var(--text)", fontSize: 12 }}
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
            formatter={(_value, _name, item) => [formatBRL(money(item.payload.moneyRaw)), valueLabel]}
          />
          <Bar dataKey="value" fill={barColor} radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function AppointmentsBarChart({ rows }: { rows: ProcedureRankingRow[] }) {
  const chartData = rows.map((row) => ({
    name: row.procedure_name,
    value: row.session_count,
  }));

  return (
    <div className={styles.chartWrap}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
          <XAxis
            type="number"
            allowDecimals={false}
            tick={{ fill: "var(--text-muted)", fontSize: 11 }}
            stroke="var(--border)"
          />
          <YAxis
            type="category"
            dataKey="name"
            width={130}
            tick={{ fill: "var(--text)", fontSize: 12 }}
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
            formatter={(value) => {
              const n = Number(value ?? 0);
              return [`${n} ${n === 1 ? "atendimento" : "atendimentos"}`, "Atendimentos"];
            }}
          />
          <Bar dataKey="value" fill="var(--accent-rose)" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
