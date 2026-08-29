import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CurrencyInput } from "@/ui/CurrencyInput";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { useProcedures } from "@/features/procedures/hooks";
import { formatBRL } from "@/lib/money/format";
import { ZERO, money, type Money } from "@/lib/money/money";
import { estimateProfit, type PaymentMethod } from "./prototypeMath";
import { PatientPicker } from "./PatientPicker";
import type { Patient } from "@/features/patients/api";
import type { Procedure } from "@/features/procedures/api";

const schema = z.object({
  patientId: z.string().min(1, "Selecione a paciente"),
  procedureId: z.string().min(1, "Selecione o procedimento"),
  price: z.string().refine((v) => Number(v) > 0, "Valor deve ser maior que zero"),
  cost: z.string(),
  paymentMethod: z.enum(["PIX", "CARD"]),
  installments: z.string(),
});

type FormValues = z.infer<typeof schema>;

/**
 * PROTÓTIPO — F-014. Sem chamada de API: `onConfirm` só simula o
 * submit para testar a sensação do fluxo. Ver frontend/BACKLOG.md F-014.
 */
export function SaleForm({ onConfirm }: { onConfirm: () => Promise<void> }) {
  const proceduresQuery = useProcedures();
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const {
    register,
    control,
    watch,
    setValue,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      patientId: "",
      procedureId: "",
      price: ZERO,
      cost: ZERO,
      paymentMethod: "PIX",
      installments: "1",
    },
  });

  const procedureId = watch("procedureId");
  const price = watch("price");
  const cost = watch("cost");
  const paymentMethod = watch("paymentMethod");

  function handlePickProcedure(procedure: Procedure) {
    setValue("procedureId", procedure.id);
    setValue("price", procedure.price as Money);
    setValue("cost", procedure.estimated_cost as Money);
  }

  const preview = useMemo(() => {
    try {
      return estimateProfit({
        unitPrice: money(price || ZERO),
        unitCost: money(cost || ZERO),
        paymentMethod: paymentMethod as PaymentMethod,
      });
    } catch {
      return null;
    }
  }, [price, cost, paymentMethod]);

  const submit = handleSubmit(async () => {
    setConfirming(true);
    try {
      await onConfirm();
      setConfirmed(true);
    } finally {
      setConfirming(false);
    }
  });

  if (confirmed) {
    return (
      <div className="sale-confirm" role="status">
        <h2>Venda registrada</h2>
        {selectedPatient && <p>{selectedPatient.name}</p>}
        {preview && (
          <>
            <p>Valor: {formatBRL(preview.total)}</p>
            <p>
              Lucro estimado: <strong>{formatBRL(preview.profit)}</strong>
            </p>
            <p className="sale-confirm__disclaimer">
              Estimativa de protótipo — o lucro real vem do backend quando a venda estiver
              integrada (T-015/T-018).
            </p>
          </>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={submit} noValidate className="form">
      <label className="form__field">
        <span>Paciente *</span>
        <PatientPicker
          selected={selectedPatient}
          onSelect={(p) => {
            setSelectedPatient(p);
            setValue("patientId", p.id);
          }}
          onClear={() => {
            setSelectedPatient(null);
            setValue("patientId", "");
          }}
        />
        {errors.patientId && <span role="alert">{errors.patientId.message}</span>}
      </label>

      <label className="form__field">
        <span>Procedimento *</span>
        <AsyncBoundary
          query={proceduresQuery}
          skeleton={<p>Carregando…</p>}
          empty={<p>Nenhum procedimento cadastrado.</p>}
        >
          {(procedures) => (
            <select
              value={procedureId}
              onChange={(e) => {
                const proc = procedures.find((p) => p.id === e.target.value);
                if (proc) handlePickProcedure(proc);
              }}
            >
              <option value="">Selecione…</option>
              {procedures.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}
        </AsyncBoundary>
        {errors.procedureId && <span role="alert">{errors.procedureId.message}</span>}
      </label>

      <label className="form__field">
        <span>Valor *</span>
        <Controller
          control={control}
          name="price"
          render={({ field }) => (
            <CurrencyInput
              value={field.value as Money}
              onChange={field.onChange}
              aria-label="Valor"
            />
          )}
        />
        {errors.price && <span role="alert">{errors.price.message}</span>}
      </label>

      <label className="form__field">
        <span>Custo estimado</span>
        <Controller
          control={control}
          name="cost"
          render={({ field }) => (
            <CurrencyInput
              value={field.value as Money}
              onChange={field.onChange}
              aria-label="Custo estimado"
            />
          )}
        />
      </label>

      <fieldset className="form__field">
        <legend>Forma de pagamento</legend>
        <label>
          <input type="radio" value="PIX" {...register("paymentMethod")} /> Pix
        </label>
        <label>
          <input type="radio" value="CARD" {...register("paymentMethod")} /> Cartão
        </label>
      </fieldset>

      {paymentMethod === "CARD" && (
        <label className="form__field">
          <span>Parcelas</span>
          <input {...register("installments")} type="number" min={1} max={12} />
        </label>
      )}

      {preview && (
        <p className="sale-form__preview">
          Lucro estimado: <strong>{formatBRL(preview.profit)}</strong>
        </p>
      )}

      <button type="submit" disabled={isSubmitting || confirming} className="tap-target">
        {confirming ? "Confirmando…" : "Confirmar venda"}
      </button>

      <p className="sale-form__package-link">
        Vendendo um pacote (várias sessões)? <Link to="/vendas/nova-pacote">Ir para venda de pacote</Link>
      </p>
    </form>
  );
}
