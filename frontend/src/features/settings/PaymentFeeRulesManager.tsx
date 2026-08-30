import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import type { PaymentFeeRule } from "./api";
import {
  useCreatePaymentFeeRule,
  useDeletePaymentFeeRule,
  usePaymentFeeRules,
  useUpdatePaymentFeeRule,
} from "./hooks";

const ruleSchema = z
  .object({
    installments_min: z.string().min(1, "Obrigatório").refine((v) => Number(v) >= 1, "Mínimo 1 parcela"),
    installments_max: z.string().min(1, "Obrigatório").refine((v) => Number(v) >= 1, "Mínimo 1 parcela"),
    fee_percentage: z.string().refine((v) => {
      const n = Number(v);
      return !isNaN(n) && n >= 0 && n <= 100;
    }, "Taxa deve ser entre 0% e 100%"),
    fixed_fee: z.string().optional(),
  })
  .refine((data) => Number(data.installments_max) >= Number(data.installments_min), {
    message: "Parcela máxima deve ser maior ou igual à mínima",
    path: ["installments_max"],
  });

type RuleFormValues = z.infer<typeof ruleSchema>;

export function PaymentFeeRulesManager() {
  const query = usePaymentFeeRules();
  const createRule = useCreatePaymentFeeRule();
  const updateRule = useUpdatePaymentFeeRule();
  const deleteRule = useDeletePaymentFeeRule();

  const [editingRule, setEditingRule] = useState<PaymentFeeRule | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<RuleFormValues>({
    resolver: zodResolver(ruleSchema),
    defaultValues: {
      installments_min: "1",
      installments_max: "1",
      fee_percentage: "3.20",
      fixed_fee: "0.00",
    },
  });

  function startEdit(rule: PaymentFeeRule) {
    setEditingRule(rule);
    setIsAdding(true);
    setErrorMsg(null);
    reset({
      installments_min: rule.installments_min.toString(),
      installments_max: rule.installments_max.toString(),
      fee_percentage: rule.fee_percentage,
      fixed_fee: rule.fixed_fee || "0.00",
    });
  }

  function startAdd() {
    setEditingRule(null);
    setIsAdding(true);
    setErrorMsg(null);
    reset({
      installments_min: "1",
      installments_max: "1",
      fee_percentage: "3.20",
      fixed_fee: "0.00",
    });
  }

  function cancel() {
    setIsAdding(false);
    setEditingRule(null);
    setErrorMsg(null);
  }

  const submit = handleSubmit(async (values) => {
    setErrorMsg(null);
    try {
      if (editingRule) {
        await updateRule.mutateAsync({
          id: editingRule.id,
          payload: {
            installments_min: Number(values.installments_min),
            installments_max: Number(values.installments_max),
            fee_percentage: values.fee_percentage,
            fixed_fee: values.fixed_fee || "0.00",
          },
        });
      } else {
        await createRule.mutateAsync({
          payment_method: "CREDIT",
          installments_min: Number(values.installments_min),
          installments_max: Number(values.installments_max),
          fee_percentage: values.fee_percentage,
          fixed_fee: values.fixed_fee || "0.00",
        });
      }
      cancel();
    } catch (e) {
      setErrorMsg(e instanceof ApiError ? e.message : "Não foi possível salvar a regra de taxa.");
    }
  });

  async function handleDelete(rule: PaymentFeeRule) {
    if (!window.confirm(`Deseja excluir a regra de ${rule.installments_min}x a ${rule.installments_max}x?`)) {
      return;
    }
    try {
      await deleteRule.mutateAsync(rule.id);
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "Erro ao excluir regra.");
    }
  }

  return (
    <div className="payment-rules">
      <div className="payment-rules__header">
        <div>
          <h3>Taxas de Cartão de Crédito por Parcela</h3>
          <p className="form__hint">
            Configure as taxas cobradas pela sua maquininha conforme a quantidade de parcelas.
          </p>
        </div>
        {!isAdding && (
          <button type="button" onClick={startAdd} className="tap-target button--secondary">
            + Nova faixa
          </button>
        )}
      </div>

      {isAdding && (
        <form onSubmit={submit} className="form form--nested">
          <h4>{editingRule ? "Editar faixa de parcelas" : "Nova faixa de parcelas"}</h4>

          <div className="form__row">
            <label className="form__field">
              <span>De (parcela)</span>
              <input {...register("installments_min")} type="number" min={1} max={36} />
              {errors.installments_min && (
                <span role="alert" className="form__error">
                  {errors.installments_min.message}
                </span>
              )}
            </label>

            <label className="form__field">
              <span>Até (parcela)</span>
              <input {...register("installments_max")} type="number" min={1} max={36} />
              {errors.installments_max && (
                <span role="alert" className="form__error">
                  {errors.installments_max.message}
                </span>
              )}
            </label>
          </div>

          <div className="form__row">
            <label className="form__field">
              <span>Taxa (%) *</span>
              <input {...register("fee_percentage")} type="text" inputMode="decimal" placeholder="ex: 4.50" />
              {errors.fee_percentage && (
                <span role="alert" className="form__error">
                  {errors.fee_percentage.message}
                </span>
              )}
            </label>

            <label className="form__field">
              <span>Taxa fixa por venda (R$)</span>
              <input {...register("fixed_fee")} type="text" inputMode="decimal" placeholder="ex: 0.00" />
            </label>
          </div>

          {errorMsg && (
            <p role="alert" className="form__error">
              {errorMsg}
            </p>
          )}

          <div className="form__actions">
            <button type="submit" disabled={isSubmitting} className="tap-target">
              {isSubmitting ? "Salvando…" : "Salvar faixa"}
            </button>
            <button type="button" onClick={cancel} className="tap-target button--ghost">
              Cancelar
            </button>
          </div>
        </form>
      )}

      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando taxas…</p>}
        empty={<p>Nenhuma taxa de cartão configurada.</p>}
      >
        {(rules) => (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Parcelas</th>
                  <th>Taxa (%)</th>
                  <th>Taxa fixa</th>
                  <th className="text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {rules
                  .slice()
                  .sort((a, b) => a.installments_min - b.installments_min)
                  .map((r) => (
                    <tr key={r.id}>
                      <td>
                        {r.installments_min === r.installments_max
                          ? `${r.installments_min}x (à vista)`
                          : `${r.installments_min}x a ${r.installments_max}x`}
                      </td>
                      <td>{r.fee_percentage}%</td>
                      <td>{Number(r.fixed_fee) > 0 ? `R$ ${r.fixed_fee}` : "—"}</td>
                      <td className="text-right">
                        <button
                          type="button"
                          className="button--text"
                          onClick={() => startEdit(r)}
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          className="button--text button--danger"
                          onClick={() => handleDelete(r)}
                        >
                          Excluir
                        </button>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </AsyncBoundary>
    </div>
  );
}
