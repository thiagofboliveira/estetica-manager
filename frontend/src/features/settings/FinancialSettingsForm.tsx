import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import { PercentInput } from "@/ui/PercentInput";
import { ZERO, type Money } from "@/lib/money/money";
import type { FinancialSettings } from "./api";

const schema = z.object({
  fee_payer: z.enum(["PROFESSIONAL", "CLINIC", "SPLIT_PRO_RATA"]),
  split_base: z.enum(["GROSS", "NET_OF_FEE"]),
  split_clinic_percentage: z.string(),
  pix_fee_percentage: z.string(),
  debit_card_fee_percentage: z.string(),
  default_payment_method: z.enum(["PIX", "DEBIT", "CREDIT", "CASH", "TRANSFER"]),
});

export type FinancialSettingsFormValues = z.infer<typeof schema>;

type Props = {
  initial: FinancialSettings;
  onSubmit: (values: FinancialSettingsFormValues) => Promise<unknown>;
};

function toDefaults(initial: FinancialSettings): FinancialSettingsFormValues {
  return {
    fee_payer: initial.fee_payer,
    split_base: initial.split_base,
    split_clinic_percentage: initial.split_clinic_percentage || ZERO,
    pix_fee_percentage: initial.pix_fee_percentage || ZERO,
    debit_card_fee_percentage: initial.debit_card_fee_percentage || ZERO,
    default_payment_method: initial.default_payment_method,
  };
}

/**
 * F-012a. Linguagem natural nas perguntas de decisão (F-021a, MVP §16.2
 * E1/E2) — nunca enum cru: "A taxa sai do seu bolso ou a clínica cobre?"
 * em vez de um <select> com PROFESSIONAL/CLINIC/SPLIT_PRO_RATA.
 */
export function FinancialSettingsForm({ initial, onSubmit }: Props) {
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const {
    register,
    control,
    watch,
    reset,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<FinancialSettingsFormValues>({
    resolver: zodResolver(schema),
    defaultValues: toDefaults(initial),
  });

  useEffect(() => {
    reset(toDefaults(initial));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initial.id]);

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
      <fieldset className="form__field">
        <legend>A taxa da máquina de cartão sai do seu bolso ou a clínica cobre?</legend>
        <label>
          <input type="radio" value="PROFESSIONAL" {...register("fee_payer")} /> Sai do meu bolso
        </label>
        <label>
          <input type="radio" value="CLINIC" {...register("fee_payer")} /> A clínica cobre
        </label>
        <label>
          <input type="radio" value="SPLIT_PRO_RATA" {...register("fee_payer")} /> Dividimos a taxa
        </label>
      </fieldset>

      <fieldset className="form__field">
        <legend>O repasse da clínica é calculado sobre o valor total ou depois de descontar a taxa do cartão?</legend>
        <label>
          <input type="radio" value="GROSS" {...register("split_base")} /> Sobre o valor total
        </label>
        <label>
          <input type="radio" value="NET_OF_FEE" {...register("split_base")} /> Depois de descontar a taxa
        </label>
      </fieldset>

      <label className="form__field">
        <span>Percentual que fica com a clínica</span>
        <Controller
          control={control}
          name="split_clinic_percentage"
          render={({ field }) => (
            <PercentInput
              value={field.value as Money}
              onChange={(v) => field.onChange(v)}
              aria-label="Percentual que fica com a clínica"
            />
          )}
        />
      </label>

      <label className="form__field">
        <span>Taxa do Pix</span>
        <Controller
          control={control}
          name="pix_fee_percentage"
          render={({ field }) => (
            <PercentInput value={field.value as Money} onChange={(v) => field.onChange(v)} aria-label="Taxa do Pix" />
          )}
        />
      </label>

      <label className="form__field">
        <span>Taxa do cartão de débito</span>
        <Controller
          control={control}
          name="debit_card_fee_percentage"
          render={({ field }) => (
            <PercentInput
              value={field.value as Money}
              onChange={(v) => field.onChange(v)}
              aria-label="Taxa do cartão de débito"
            />
          )}
        />
      </label>

      <fieldset className="form__field">
        <legend>Forma de pagamento mais usada (vem pré-selecionada numa venda nova)</legend>
        <label>
          <input type="radio" value="PIX" {...register("default_payment_method")} /> Pix
        </label>
        <label>
          <input type="radio" value="DEBIT" {...register("default_payment_method")} /> Débito
        </label>
        <label>
          <input type="radio" value="CREDIT" {...register("default_payment_method")} /> Crédito
        </label>
        <label>
          <input type="radio" value="CASH" {...register("default_payment_method")} /> Dinheiro
        </label>
        <label>
          <input type="radio" value="TRANSFER" {...register("default_payment_method")} /> Transferência
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
        {isSubmitting ? "Salvando…" : "Salvar"}
      </button>
    </form>
  );
}
