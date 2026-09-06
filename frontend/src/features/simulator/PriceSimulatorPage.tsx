import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useProcedures } from "@/features/procedures/hooks";
import { salesApi, type PaymentMethod, type SaleSimulationOut } from "@/features/sales/api";
import { CurrencyInput } from "@/ui/CurrencyInput";
import { formatBRL, formatRate } from "@/lib/money/format";
import { money, rate, ZERO, type Money } from "@/lib/money/money";
import styles from "./PriceSimulatorPage.module.css";


export function PriceSimulatorPage() {
  const [searchParams] = useSearchParams();
  const initialProcId = searchParams.get("procedure_id") || "";

  const proceduresQuery = useProcedures();
  const procedures = proceduresQuery.data || [];

  const [selectedProcId, setSelectedProcId] = useState<string>(initialProcId);
  const [price, setPrice] = useState<Money>("150.00" as Money);
  const [cost, setCost] = useState<Money>("30.00" as Money);
  const [discount, setDiscount] = useState<Money>(ZERO);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("PIX");
  const [installments, setInstallments] = useState<number>(1);

  const [simulation, setSimulation] = useState<SaleSimulationOut | null>(null);

  // Quando seleciona um procedimento existente, pré-carrega os dados
  useEffect(() => {
    if (selectedProcId) {
      const p = procedures.find((item) => item.id === selectedProcId);
      if (p) {
        setPrice(p.price as Money);
        setCost((p.estimated_cost || ZERO) as Money);
      }
    }
  }, [selectedProcId, procedures]);

  // Executa simulação sempre que um parâmetro mudar
  useEffect(() => {
    let active = true;

    const timer = setTimeout(async () => {
      try {
        const res = await salesApi.simulate({
          procedure_id: selectedProcId || undefined,
          price: price.toString(),
          estimated_cost: cost.toString(),
          discount_amount: discount.toString(),
          payment_method: paymentMethod,
          installments: paymentMethod === "CREDIT" ? installments : 1,
        });
        if (active) {
          setSimulation(res);
        }
      } catch {
        // Silencioso ou fallback
      }
    }, 150);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [selectedProcId, price, cost, discount, paymentMethod, installments]);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.badge}>Inteligência Financeira</div>
        <h1 className={styles.title}>Simulador de Preço & Margem de Lucro</h1>
        <p className={styles.subtitle}>
          Descubra o lucro líquido real de cada procedimento antes de fechar com a paciente. 
          O cálculo considera suas taxas reais de maquininha, regras de repasse e custo de insumos.
        </p>
      </header>

      <div className={styles.grid}>
        {/* Painel de Configuração */}
        <section className={`card ${styles.formCard}`}>
          <h2 className={styles.sectionTitle}>Parâmetros da Sessão</h2>

          <div className="form__field">
            <label htmlFor="proc-select">Procedimento cadastrado (opcional)</label>
            <select
              id="proc-select"
              value={selectedProcId}
              onChange={(e) => setSelectedProcId(e.target.value)}
              className="select"
            >
              <option value="">Simular procedimento avulso / novo</option>
              {procedures.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} (R$ {Number(p.price).toFixed(2)})
                </option>
              ))}
            </select>
          </div>

          <div className="form__field">
            <label>Preço cobrado da paciente (R$) *</label>
            <CurrencyInput
              value={price}
              onChange={(v) => {
                setSelectedProcId("");
                setPrice(v);
              }}
              aria-label="Preço cobrado"
            />
          </div>

          <div className="form__field">
            <label>Custo estimado de insumos por sessão (R$)</label>
            <CurrencyInput
              value={cost}
              onChange={(v) => {
                setSelectedProcId("");
                setCost(v);
              }}
              aria-label="Custo de insumos"
            />
            <span className={styles.hintText}>
              Ex: ampolas, toxina, descartáveis, agulhas, cremes usados no atendimento.
            </span>
          </div>

          <div className="form__field">
            <label>Desconto concedido (R$)</label>
            <CurrencyInput
              value={discount}
              onChange={(v) => setDiscount(v)}
              aria-label="Desconto concedido"
            />
          </div>

          <div className="form__field">
            <label>Forma de pagamento</label>
            <div className={styles.paymentMethods}>
              {(["PIX", "DEBIT", "CREDIT", "CASH"] as PaymentMethod[]).map((method) => (
                <button
                  key={method}
                  type="button"
                  onClick={() => setPaymentMethod(method)}
                  className={`${styles.paymentBtn} ${paymentMethod === method ? styles.paymentBtnActive : ""}`}
                >
                  {method === "PIX" && "⚡ PIX"}
                  {method === "DEBIT" && "💳 Débito"}
                  {method === "CREDIT" && "💳 Crédito"}
                  {method === "CASH" && "💵 Dinheiro"}
                </button>
              ))}
            </div>
          </div>

          {paymentMethod === "CREDIT" && (
            <div className="form__field">
              <label htmlFor="installments-select">Parcelamento no cartão</label>
              <select
                id="installments-select"
                value={installments}
                onChange={(e) => setInstallments(Number(e.target.value))}
                className="select"
              >
                {[1, 2, 3, 4, 5, 6, 10, 12].map((n) => (
                  <option key={n} value={n}>
                    {n}x {n === 1 ? "(À vista no crédito)" : `vezes de ${formatBRL(money((Number(price) / n).toFixed(2)))}`}
                  </option>

                ))}
              </select>
            </div>
          )}
        </section>

        {/* Painel de Resultados */}
        <section className={styles.resultsWrapper}>
          {simulation?.is_negative_margin && (
            <div className={styles.alertNegative} role="alert">
              <div className={styles.alertIcon}>⚠️</div>
              <div>
                <strong>Alerta de Margem Negativa:</strong>
                <p>{simulation.negative_margin_alert}</p>
                <span className={styles.alertAdvice}>
                  💡 Para não pagar para trabalhar, ajuste o preço cobrado ou renegocie o custo do produto com fornecedores.
                </span>
              </div>
            </div>
          )}

          <div className={`card ${styles.resultCard}`}>
            <h2 className={styles.sectionTitle}>Lucro Real por Atendimento</h2>

            <div className={styles.profitHighlight}>
              <span className={styles.profitLabel}>Você coloca no bolso (Lucro Líquido):</span>
              <div className={styles.profitValueRow}>
                <span
                  className={`${styles.profitAmount} ${
                    simulation?.is_negative_margin ? styles.profitAmountNegative : styles.profitAmountPositive
                  }`}
                >
                  {simulation ? formatBRL(money(simulation.net_profit)) : "—"}
                </span>
                {simulation?.margin && (
                  <span
                    className={`${styles.marginBadge} ${
                      simulation.is_negative_margin ? styles.marginBadgeNegative : styles.marginBadgePositive
                    }`}
                  >
                    {formatRate(rate(simulation.margin))} de margem
                  </span>
                )}
              </div>
            </div>

            <hr className={styles.divider} />

            <h3 className={styles.breakdownTitle}>Detalhamento do Lucro Líquido:</h3>
            <dl className={styles.breakdownList}>
              <div className={styles.breakdownItem}>
                <dt>Preço Bruto:</dt>
                <dd>{simulation ? formatBRL(money(simulation.gross_amount)) : "—"}</dd>
              </div>
              <div className={styles.breakdownItem}>
                <dt>Taxa da Maquininha ({simulation?.fee_rate}%):</dt>
                <dd className={styles.textRed}>
                  - {simulation ? formatBRL(money(simulation.fee_amount)) : "—"}
                </dd>
              </div>
              <div className={styles.breakdownItem}>
                <dt>Custo de Insumos:</dt>
                <dd className={styles.textRed}>
                  - {simulation ? formatBRL(money(simulation.cost_provisioned)) : "—"}
                </dd>
              </div>
            </dl>

            <div className={styles.auditFooter}>
              <span>🔒 Cálculo de precisão contábil considerando taxas, comissões e custos cadastrados.</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
