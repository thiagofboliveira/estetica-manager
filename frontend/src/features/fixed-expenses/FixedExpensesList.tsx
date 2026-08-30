import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import { formatBRL } from "@/lib/money/format";
import { money, ZERO, type Money } from "@/lib/money/money";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { CurrencyInput } from "@/ui/CurrencyInput";
import { EmptyState } from "@/ui/EmptyState";
import type { ExpensePeriodicity, FixedExpense } from "./api";
import {
  useArchiveFixedExpense,
  useCreateFixedExpense,
  useFixedExpenses,
  useUpdateFixedExpense,
} from "./hooks";

const schema = z.object({
  label: z.string().min(1, "Descrição é obrigatória"),
  category: z.string().optional(),
  amount: z.string().refine((v) => Number(v) > 0, "Valor deve ser maior que zero"),
  periodicity: z.enum(["MONTHLY", "YEARLY"]),
  active_from: z.string().min(1, "Data de início é obrigatória"),
});

type FormValues = z.infer<typeof schema>;

export function FixedExpensesList() {
  const query = useFixedExpenses(true);
  const createExpense = useCreateFixedExpense();
  const updateExpense = useUpdateFixedExpense();
  const archiveExpense = useArchiveFixedExpense();

  const [editingExpense, setEditingExpense] = useState<FixedExpense | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const todayStr = new Date().toISOString().slice(0, 10);

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      label: "",
      category: "",
      amount: ZERO,
      periodicity: "MONTHLY",
      active_from: todayStr,
    },
  });

  function startAdd() {
    setEditingExpense(null);
    setIsAdding(true);
    setServerError(null);
    reset({
      label: "",
      category: "",
      amount: ZERO,
      periodicity: "MONTHLY",
      active_from: todayStr,
    });
  }

  function startEdit(item: FixedExpense) {
    setEditingExpense(item);
    setIsAdding(true);
    setServerError(null);
    reset({
      label: item.label,
      category: item.category ?? "",
      amount: item.amount,
      periodicity: item.periodicity,
      active_from: item.active_from,
    });
  }

  function cancel() {
    setIsAdding(false);
    setEditingExpense(null);
    setServerError(null);
  }

  const submit = handleSubmit(async (values) => {
    setServerError(null);
    try {
      if (editingExpense) {
        await updateExpense.mutateAsync({
          id: editingExpense.id,
          payload: {
            label: values.label,
            category: values.category || null,
            amount: values.amount,
            periodicity: values.periodicity as ExpensePeriodicity,
          },
        });
      } else {
        await createExpense.mutateAsync({
          label: values.label,
          category: values.category || null,
          amount: values.amount,
          periodicity: values.periodicity as ExpensePeriodicity,
          active_from: values.active_from,
        });
      }
      cancel();
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Não foi possível salvar a despesa.");
    }
  });

  async function handleArchive(item: FixedExpense) {
    if (!window.confirm(`Deseja encerrar a despesa fixa "${item.label}"? Ela deixará de contar a partir de hoje.`)) {
      return;
    }
    try {
      await archiveExpense.mutateAsync(item.id);
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "Erro ao encerrar despesa.");
    }
  }

  return (
    <div className="fixed-expenses">
      <div className="fixed-expenses__header">
        <div>
          <h2>Despesas Fixas e Custos Operacionais</h2>
          <p className="form__hint">
            Custos recorrentes que compõem o cálculo do seu <strong>Lucro Real do Mês</strong> (ex: aluguel, luz, vigilância sanitária, contador).
          </p>
        </div>
        {!isAdding && (
          <button type="button" onClick={startAdd} className="tap-target button--secondary">
            + Nova despesa fixa
          </button>
        )}
      </div>

      {isAdding && (
        <form onSubmit={submit} className="form form--nested">
          <h3>{editingExpense ? "Editar despesa fixa" : "Cadastrar nova despesa fixa"}</h3>

          <label className="form__field">
            <span>Descrição / Nome do Custo *</span>
            <input {...register("label")} placeholder="ex: Aluguel da sala, Vigilância Sanitária" />
            {errors.label && (
              <span role="alert" className="form__error">
                {errors.label.message}
              </span>
            )}
          </label>

          <div className="form__row">
            <label className="form__field">
              <span>Valor *</span>
              <Controller
                control={control}
                name="amount"
                render={({ field }) => (
                  <CurrencyInput
                    value={field.value as Money}
                    onChange={(v) => field.onChange(v)}
                    aria-label="Valor da despesa"
                  />
                )}
              />
              {errors.amount && (
                <span role="alert" className="form__error">
                  {errors.amount.message}
                </span>
              )}
            </label>

            <label className="form__field">
              <span>Frequência / Periodicidade</span>
              <select {...register("periodicity")}>
                <option value="MONTHLY">Mensal (todo mês)</option>
                <option value="YEARLY">Anual (rateado em 12x)</option>
              </select>
            </label>
          </div>

          <div className="form__row">
            <label className="form__field">
              <span>Categoria (opcional)</span>
              <input {...register("category")} placeholder="ex: Estrutura, Taxas, Serviços" />
            </label>

            {!editingExpense && (
              <label className="form__field">
                <span>Válido a partir de</span>
                <input {...register("active_from")} type="date" />
                {errors.active_from && (
                  <span role="alert" className="form__error">
                    {errors.active_from.message}
                  </span>
                )}
              </label>
            )}
          </div>

          {serverError && (
            <p role="alert" className="form__error">
              {serverError}
            </p>
          )}

          <div className="form__actions">
            <button type="submit" disabled={isSubmitting} className="tap-target">
              {isSubmitting ? "Salvando…" : "Salvar despesa"}
            </button>
            <button type="button" onClick={cancel} className="tap-target button--ghost">
              Cancelar
            </button>
          </div>
        </form>
      )}

      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando despesas…</p>}
        empty={
          <EmptyState
            tone="first-run"
            title="Nenhuma despesa fixa cadastrada"
            body="Cadastre despesas como aluguel e custos fixos para ver o cálculo do seu lucro real líquido do mês."
          />
        }
      >
        {(expenses) => (
          <ul className="list">
            {expenses.map((item) => (
              <li key={item.id} className="list__item">
                <div className="list__item-main">
                  <div className="list__item-row">
                    <span className="list__item-title">{item.label}</span>
                    {item.category && <span className="list__item-badge">{item.category}</span>}
                  </div>
                  <span className="list__item-note">
                    {item.periodicity === "MONTHLY"
                      ? "Mensal"
                      : "Anual (rateado em 12 parcelas no fechamento)"}
                  </span>
                </div>
                <div className="list__item-aside">
                  <span className="list__item-amount">{formatBRL(money(item.amount))}</span>
                  <div className="list__item-actions">
                    <button type="button" className="button--text" onClick={() => startEdit(item)}>
                      Editar
                    </button>
                    <button
                      type="button"
                      className="button--text button--danger"
                      onClick={() => handleArchive(item)}
                    >
                      Encerrar
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </AsyncBoundary>
    </div>
  );
}
