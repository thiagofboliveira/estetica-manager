import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { ApiError } from "@/lib/http/client";
import { useSale, useSaleAudit, useCorrectSale } from "./hooks";
import type { Sale } from "./api";

type CorrectionFormValues = {
  paymentMethod: "PIX" | "DEBIT" | "CREDIT" | "CASH" | "TRANSFER";
  installments: string;
  reason: string;
};

/**
 * F-014d/T-017. "Editar" uma venda não é um UPDATE — o backend estorna
 * a original (`status` vira `REFUNDED`) e cria uma venda NOVA com id
 * diferente. `GET /sales/{id}/audit` (adicionado depois, mesma task)
 * expõe o vínculo original→substituta, usado abaixo para mostrar "esta
 * venda foi corrigida, veja a nova".
 * ⚠️ Achado real: a nota antiga do backlog dizia "recalcula com a
 * config do momento original (I3)" — o backend faz o OPOSTO, usa a
 * config de HOJE (sem versionamento de config). O aviso abaixo reflete
 * o comportamento real, não o que a nota desatualizada dizia.
 */
export function SaleDetailPage() {
  const { id = "" } = useParams();
  const query = useSale(id);

  return (
    <div className="page">
      <header className="page__header">
        <h1>Venda</h1>
      </header>
      <AsyncBoundary query={query} skeleton={<p>Carregando…</p>} empty={<p>Venda não encontrada.</p>} isEmpty={(s) => s == null}>
        {(sale) => <SaleDetail sale={sale} />}
      </AsyncBoundary>
    </div>
  );
}

function SaleDetail({ sale }: { sale: Sale }) {
  const [correcting, setCorrecting] = useState(false);
  const auditQuery = useSaleAudit(sale.id);
  // Se esta venda já foi corrigida, existe no máximo 1 entrada com
  // original_sale_id === sale.id (não dá pra corrigir 2x a mesma —
  // a segunda tentativa cai em 409, ver CorrectionForm).
  const correction = auditQuery.data?.[0];

  if (sale.status === "REFUNDED") {
    return (
      <div>
        <p className="form__error">
          Esta venda foi estornada — já foi substituída por uma correção.
          {correction && (
            <>
              {" "}
              Motivo: "{correction.reason}".{" "}
              <Link to={`/vendas/${correction.replacement_sale_id}`}>Ver venda corrigida</Link>
            </>
          )}
        </p>
        <SaleSummary sale={sale} />
      </div>
    );
  }

  return (
    <div>
      <SaleSummary sale={sale} />
      {correcting ? (
        <CorrectionForm sale={sale} onCancel={() => setCorrecting(false)} />
      ) : (
        <button type="button" className="tap-target" onClick={() => setCorrecting(true)}>
          Corrigir venda
        </button>
      )}
    </div>
  );
}

function SaleSummary({ sale }: { sale: Sale }) {
  return (
    <dl className="dashboard__metrics">
      <div className="dashboard__metric">
        <dt>Valor</dt>
        <dd>{formatBRL(money(sale.gross_amount))}</dd>
      </div>
      <div className="dashboard__metric">
        <dt>Lucro</dt>
        <dd>{formatBRL(money(sale.net_profit))}</dd>
      </div>
      <div className="dashboard__metric dashboard__metric--wide">
        <dt>Itens</dt>
        <dd>
          {sale.items.map((item) => (
            <p key={item.id}>
              {item.quantity}× — {formatBRL(money(item.unit_price))}/un.
            </p>
          ))}
        </dd>
      </div>
    </dl>
  );
}

function CorrectionForm({ sale, onCancel }: { sale: Sale; onCancel: () => void }) {
  const navigate = useNavigate();
  const correct = useCorrectSale(sale.id);
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    watch,
    formState: { isSubmitting },
  } = useForm<CorrectionFormValues>({
    defaultValues: {
      paymentMethod: sale.payment_method,
      installments: String(sale.installments),
      reason: "",
    },
  });
  const paymentMethod = watch("paymentMethod");

  const submit = handleSubmit(async (values) => {
    setServerError(null);
    try {
      const corrected = await correct.mutateAsync({
        patient_id: sale.patient_id,
        type: sale.type,
        items: sale.items.map((i) => ({ procedure_id: i.procedure_id, quantity: i.quantity })),
        discount_amount: sale.discount_amount,
        payment_method: values.paymentMethod,
        installments: values.paymentMethod === "CREDIT" ? Number(values.installments) : 1,
        reason: values.reason,
      });
      // Venda corrigida tem ID NOVO — navegar para a nova, não recarregar a antiga.
      navigate(`/vendas/${corrected.id}`);
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Não consegui corrigir a venda. Tenta de novo?");
    }
  });

  return (
    <form onSubmit={submit} noValidate className="form">
      <p className="form__error" role="alert">
        A correção usa a configuração financeira de <strong>hoje</strong> (taxas, split), não a de quando a
        venda foi feita — se algo mudou desde então, o lucro pode sair diferente do original.
      </p>

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

      <label className="form__field">
        <span>O que estava errado? *</span>
        <input {...register("reason", { required: true })} placeholder="ex: forma de pagamento errada" />
      </label>

      {serverError && (
        <p role="alert" className="form__error">
          {serverError}
        </p>
      )}

      <button type="submit" disabled={isSubmitting || correct.isPending} className="tap-target">
        {correct.isPending ? "Corrigindo…" : "Confirmar correção"}
      </button>
      <button type="button" className="tap-target" onClick={onCancel}>
        Cancelar
      </button>
    </form>
  );
}
