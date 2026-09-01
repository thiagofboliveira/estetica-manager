import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { useProcedures } from "@/features/procedures/hooks";
import { usePatient } from "@/features/patients/hooks";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { ApiError } from "@/lib/http/client";
import { toast } from "@/ui/ToastContext";
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
  const patientIdParam = searchParams.get("patient_id");
  const preloadedPatientQuery = usePatient(patientIdParam || "");

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

  useEffect(() => {
    if (preloadedPatientQuery.data && !selectedPatient) {
      setSelectedPatient(preloadedPatientQuery.data);
      setValue("patientId", preloadedPatientQuery.data.id);
    }
  }, [preloadedPatientQuery.data, selectedPatient, setValue]);

  const procedureId = watch("procedureId");
  const paymentMethod = watch("paymentMethod");

  const submit = handleSubmit(
    async (values) => {
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
        toast.success("Venda registrada com sucesso!");
      } catch (e) {
        setServerError(e instanceof ApiError ? e.message : "Não consegui registrar a venda. Tenta de novo?");
      }
    },
    () => {
      toast.show("Por favor, selecione a paciente e o procedimento antes de confirmar.", "error");
    }
  );

  if (confirmedSale) {
    return (
      <div className="sale-confirm" role="status" style={{ padding: "24px", backgroundColor: "#f8fafc", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h2 style={{ margin: 0, color: "#0f172a" }}>Venda registrada com sucesso!</h2>
          <span className="badge badge--success" style={{ backgroundColor: "#dcfce7", color: "#166534", padding: "6px 12px", borderRadius: "20px", fontWeight: "600" }}>
            🟢 Lucro Realizado
          </span>
        </div>
        {selectedPatient && (
          <p style={{ fontSize: "15px", color: "#334155", marginBottom: "8px" }}>
            <strong>Paciente:</strong> {selectedPatient.name}
          </p>
        )}
        <p style={{ fontSize: "15px", color: "#334155", marginBottom: "8px" }}>
          <strong>Valor Total:</strong> {formatBRL(money(confirmedSale.gross_amount))}
        </p>
        <p style={{ fontSize: "16px", color: "#15803d", marginBottom: "20px" }}>
          <strong>Lucro Líquido:</strong> {formatBRL(money(confirmedSale.net_profit))}
        </p>

        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginTop: "16px" }}>
          <button
            type="button"
            className="button tap-target"
            onClick={() => {
              setConfirmedSale(null);
              setSelectedPatient(null);
              setValue("patientId", "");
              setValue("procedureId", "");
            }}
          >
            + Registrar outra venda
          </button>
          <Link to="/agenda" className="button button--secondary tap-target">
            📅 Ver na Agenda
          </Link>
          <Link to="/dashboard" className="button button--secondary tap-target">
            📊 Ir para o Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={submit} noValidate className="form">
      <div className="form__field">
        <label htmlFor="patient-select" style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-h)", marginBottom: "4px", display: "block" }}>
          Paciente *
        </label>
        <PatientPicker
          selected={selectedPatient}
          onSelect={(p) => {
            setSelectedPatient(p);
            setValue("patientId", p.id, { shouldValidate: true });
          }}
          onClear={() => {
            setSelectedPatient(null);
            setValue("patientId", "", { shouldValidate: true });
          }}
        />
        {errors.patientId && (
          <span role="alert" className="form__error" style={{ color: "#dc2626", fontWeight: "600", fontSize: "13px", marginTop: "4px", display: "block" }}>
            {errors.patientId.message}
          </span>
        )}
      </div>

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
                <select
                  value={procedureId}
                  onChange={(e) => setValue("procedureId", e.target.value, { shouldValidate: true })}
                >
                  <option value="">Selecione um procedimento…</option>
                  {procedures.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} — {formatBRL(money(p.price))}
                    </option>
                  ))}
                </select>
                {selectedProcedure && (
                  <p className="sale-form__procedure-price" style={{ marginTop: "6px", fontWeight: "600", color: "#166534" }}>
                    Valor: {formatBRL(money(selectedProcedure.price))}
                  </p>
                )}
              </>
            );
          }}
        </AsyncBoundary>
        {errors.procedureId && (
          <span role="alert" className="form__error" style={{ color: "#dc2626", fontWeight: "600", fontSize: "13px", marginTop: "4px", display: "block" }}>
            {errors.procedureId.message}
          </span>
        )}
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
