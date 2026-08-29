import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import { CurrencyInput } from "@/ui/CurrencyInput";
import { ZERO, type Money } from "@/lib/money/money";
import type { FixedExpense } from "./api";

const schema = z.object({
  label: z.string().min(1, "Nome é obrigatório"),
  category: z.string().optional(),
  amount: z.string().refine((v) => Number(v) > 0, "Valor deve ser maior que zero"),
  periodicity: z.enum(["MONTHLY", "YEARLY"]),
});

export type ExpenseFormValues = z.infer<typeof schema>;

type Props = {
  initial?: FixedExpense;
  onSubmit: (values: ExpenseFormValues) => Promise<unknown>;
  submitLabel: string;
};

export function ExpenseForm({ initial, onSubmit, submitLabel }: Props) {
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const {
    register,
    control,
    watch,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ExpenseFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      label: initial?.label ?? "",
      category: initial?.category ?? "",
      amount: initial?.amount ?? ZERO,
      periodicity: initial?.periodicity ?? "MONTHLY",
    },
  });

  // Mesmo padrão de ProcedureForm: qualquer edição depois de salvar
  // invalida o "Salvo com sucesso" preso na tela.
  useEffect(() => {
    const sub = watch(() => setSaved(false));
    return () => sub.unsubscribe();
  }, [watch]);

  const submit = handleSubmit(async (values) => {
    setServerError(null);
    setSaved(false);
    try {
      await onSubmit(values);
      setSaved(true);
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Não consegui salvar. Tenta de novo?");
    }
  });

  return (
    <form onSubmit={submit} noValidate className="form">
      <label className="form__field">
        <span>Nome da despesa *</span>
        <input {...register("label")} placeholder="ex: Aluguel da sala" />
        {errors.label && <span role="alert">{errors.label.message}</span>}
      </label>

      <label className="form__field">
        <span>Categoria</span>
        <input {...register("category")} placeholder="ex: Estrutura (opcional)" />
      </label>

      <label className="form__field">
        <span>Valor do ciclo *</span>
        <Controller
          control={control}
          name="amount"
          render={({ field }) => (
            <CurrencyInput
              value={field.value as Money}
              onChange={(v) => field.onChange(v)}
              aria-label="Valor do ciclo"
            />
          )}
        />
        {errors.amount && <span role="alert">{errors.amount.message}</span>}
      </label>

      <fieldset className="form__field">
        <legend>Repete a cada</legend>
        <label>
          <input type="radio" value="MONTHLY" {...register("periodicity")} /> Mês
        </label>
        <label>
          <input type="radio" value="YEARLY" {...register("periodicity")} /> Ano
        </label>
      </fieldset>

      {serverError && (
        <p role="alert" className="form__error">
          {serverError}
        </p>
      )}

      {saved && !serverError && (
        <p role="status" className="form__success">
          Salvo com sucesso.
        </p>
      )}

      <button type="submit" disabled={isSubmitting} className="tap-target">
        {isSubmitting ? "Salvando…" : submitLabel}
      </button>
    </form>
  );
}
