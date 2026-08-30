import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { useProcedures } from "@/features/procedures/hooks";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { ApiError } from "@/lib/http/client";
import { PatientPicker } from "./PatientPicker";
import { useCreateSale } from "./hooks";
import type { Patient } from "@/features/patients/api";
import type { Sale } from "./api";

const schema = z.object({
  patientId: z.string().min(1, "Selecione a paciente"),
  procedureId: z.string().min(1, "Selecione o procedimento"),
  paymentMethod: z.enum(["PIX", "DEBIT", "CREDIT", "CASH", "TRANSFER"]),
  installments: z.string(),
});

type FormValues = z.infer<typeof schema>;

/**
 * F-014, venda avulsa. Integrado com POST /sales real (T-015) — o
 * lucro exibido na confirmação vem da resposta da API, nunca é
 * recalculado no cliente (ENGENHARIA.md invariante). Idempotency-Key
 * nasce ao montar o form (useCreateSale) e cobre F-014a.
 * F-019a: suporte à conversão de booking via booking_id.
 */
export function SaleForm() {
  const [searchParams] = useSearchParams();
  const bookingId = searchParams.get("booking_id");
  const proceduresQuery = useProcedures();
  const createSale = useCreateSale();
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [confirmedSale, setConfirmedSale] = useState<Sale | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    watch,
    setValue,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      patientId: "",
      procedureId: "",
      paymentMethod: "PIX",
      installments: "1",
    },
  });

  const procedureId = watch("procedureId");
  const paymentMethod = watch("paymentMethod");

  const submit = handleSubmit(async (values) => {
    setServerError(null);
    try {
      const sale = await createSale.mutateAsync({
        patient_id: values.patientId,
        type: "SINGLE",
        items: [{ procedure_id: values.procedureId, quantity: 1 }],
        discount_amount: "0.00",
        payment_method: values.paymentMethod,
        installments: values.paymentMethod === "CREDIT" ? Number(values.installments) : 1,
        booking_id: bookingId || null,
      });
      setConfirmedSale(sale);
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Não consegui registrar a venda. Tenta de novo?");
    }
  });

  if (confirmedSale) {
    return (
      <div className="sale-confirm" role="status">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Venda registrada</h2>
          <span className="badge badge--success">🟢 Lucro Realizado</span>
        </div>
        {selectedPatient && <p>{selectedPatient.name}</p>}
        <p>Valor: {formatBRL(money(confirmedSale.gross_amount))}</p>
        <p>
          Lucro: <strong>{formatBRL(money(confirmedSale.net_profit))}</strong>
        </p>
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
          {(procedures) => {
            const selectedProcedure = procedures.find((p) => p.id === procedureId);
            return (
              <>
                <select value={procedureId} onChange={(e) => setValue("procedureId", e.target.value)}>
                  <option value="">Selecione…</option>
                  {procedures.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
                {selectedProcedure && (
                  <p className="sale-form__procedure-price">
                    Valor: {formatBRL(money(selectedProcedure.price))}
                  </p>
                )}
              </>
            );
          }}
        </AsyncBoundary>
        {errors.procedureId && <span role="alert">{errors.procedureId.message}</span>}
      </label>

      <fieldset className="form__field">
        <legend>Forma de pagamento</legend>
        <label>
          <input type="radio" value="PIX" {...register("paymentMethod")} /> Pix
        </label>
        <label>
          <input type="radio" value="DEBIT" {...register("paymentMethod")} /> Débito
        </label>
        <label>
          <input type="radio" value="CREDIT" {...register("paymentMethod")} /> Crédito
        </label>
        <label>
          <input type="radio" value="CASH" {...register("paymentMethod")} /> Dinheiro
        </label>
        <label>
          <input type="radio" value="TRANSFER" {...register("paymentMethod")} /> Transferência
        </label>
      </fieldset>

      {paymentMethod === "CREDIT" && (
        <label className="form__field">
          <span>Parcelas</span>
          <input {...register("installments")} type="number" min={1} max={12} />
        </label>
      )}

      {serverError && (
        <p role="alert" className="form__error">
          {serverError}
        </p>
      )}

      <button type="submit" disabled={isSubmitting || createSale.isPending} className="tap-target">
        {createSale.isPending ? "Confirmando…" : "Confirmar venda"}
      </button>

      <p className="sale-form__package-link">
        Vendendo um pacote (várias sessões)? <Link to="/vendas/nova-pacote">Ir para venda de pacote</Link>
      </p>
    </form>
  );
}
