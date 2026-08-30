import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import { CurrencyInput } from "@/ui/CurrencyInput";
import { ZERO, type Money } from "@/lib/money/money";
import type { Procedure, ProcedureType } from "./api";

const schema = z.object({
  name: z.string().min(1, "Nome é obrigatório"),
  type: z.enum(["SERVICE", "PRODUCT"]),
  price: z.string().refine((v) => Number(v) > 0, "Preço deve ser maior que zero"),
  estimated_cost: z.string(),
  return_interval_days: z.string().optional(),
  default_modality: z.enum(["IN_PERSON", "REMOTE"]),
});

export type ProcedureFormValues = z.infer<typeof schema>;

type Props = {
  initial?: Procedure;
  onSubmit: (values: ProcedureFormValues) => Promise<unknown>;
  submitLabel: string;
};

export function ProcedureForm({ initial, onSubmit, submitLabel }: Props) {
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const {
    register,
    control,
    watch,
    reset,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProcedureFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initial?.name ?? "",
      type: (initial?.type ?? "SERVICE") as ProcedureType,
      price: initial?.price ?? ZERO,
      estimated_cost: initial?.estimated_cost ?? ZERO,
      return_interval_days: initial?.return_interval_days?.toString() ?? "",
      default_modality: initial?.default_modality ?? "IN_PERSON",
    },
  });

  const type = watch("type");

  // Se o id trocar sem remontar o componente, o form precisa refletir o
  // procedimento novo, não o antigo.
  useEffect(() => {
    reset({
      name: initial?.name ?? "",
      type: (initial?.type ?? "SERVICE") as ProcedureType,
      price: initial?.price ?? ZERO,
      estimated_cost: initial?.estimated_cost ?? ZERO,
      return_interval_days: initial?.return_interval_days?.toString() ?? "",
      default_modality: initial?.default_modality ?? "IN_PERSON",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initial?.id]);

  // Qualquer edição após salvar invalida o "Salvo com sucesso" —
  // senão a mensagem fica presa mesmo depois de mudar campos sem reenviar.
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
        <span>Nome *</span>
        <input {...register("name")} />
        {errors.name && <span role="alert">{errors.name.message}</span>}
      </label>

      <fieldset className="form__field">
        <legend>Tipo</legend>
        <label>
          <input type="radio" value="SERVICE" {...register("type")} /> Serviço (procedimento)
        </label>
        <label>
          <input type="radio" value="PRODUCT" {...register("type")} /> Produto
        </label>
      </fieldset>

      <label className="form__field">
        <span>Preço *</span>
        <Controller
          control={control}
          name="price"
          render={({ field }) => (
            <CurrencyInput
              value={field.value as Money}
              onChange={(v) => field.onChange(v)}
              aria-label="Preço"
            />
          )}
        />
        {errors.price && <span role="alert">{errors.price.message}</span>}
      </label>

      <label className="form__field">
        <span>Custo estimado</span>
        <Controller
          control={control}
          name="estimated_cost"
          render={({ field }) => (
            <CurrencyInput
              value={field.value as Money}
              onChange={(v) => field.onChange(v)}
              aria-label="Custo estimado"
            />
          )}
        />
      </label>

      {type === "SERVICE" && (
        <label className="form__field">
          <span>Retorno recomendado (dias)</span>
          <input
            {...register("return_interval_days")}
            type="number"
            min={0}
            placeholder="ex: 30"
          />
        </label>
      )}

      <fieldset className="form__field">
        <legend>Modalidade padrão</legend>
        {/* Default do procedimento — copiado para a sessão na criação (F-017a
            lê isto para o ícone presencial/remoto na agenda). */}
        <label>
          <input type="radio" value="IN_PERSON" {...register("default_modality")} /> Presencial
        </label>
        <label>
          <input type="radio" value="REMOTE" {...register("default_modality")} /> Videochamada
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
