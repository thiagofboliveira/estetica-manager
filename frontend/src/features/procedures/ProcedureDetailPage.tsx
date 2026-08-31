import { useParams } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { ProcedureForm, type ProcedureFormValues } from "./ProcedureForm";
import { toProcedurePayload } from "./mapper";
import { useProcedure, useUpdateProcedure } from "./hooks";

export function ProcedureDetailPage() {
  const { id = "" } = useParams();
  const query = useProcedure(id);
  const update = useUpdateProcedure(id);

  async function handleSubmit(values: ProcedureFormValues) {
    const payload = toProcedurePayload(values);
    await update.mutateAsync(payload);
  }

  return (
    <div className="page">
      <header className="page__header">
        <h1>Procedimento</h1>
      </header>
      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando…</p>}
        empty={<p>Procedimento não encontrado.</p>}
        isEmpty={(p) => p == null}
      >
        {(procedure) => (
          <ProcedureForm initial={procedure} onSubmit={handleSubmit} submitLabel="Salvar" />
        )}
      </AsyncBoundary>
    </div>
  );
}
