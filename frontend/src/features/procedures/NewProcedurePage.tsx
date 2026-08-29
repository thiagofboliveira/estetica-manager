import { useNavigate } from "react-router-dom";
import { ProcedureForm, type ProcedureFormValues } from "./ProcedureForm";
import { toProcedurePayload } from "./mapper";
import { useCreateProcedure } from "./hooks";

export function NewProcedurePage() {
  const navigate = useNavigate();
  const create = useCreateProcedure();

  async function handleSubmit(values: ProcedureFormValues) {
    const procedure = await create.mutateAsync(toProcedurePayload(values));
    navigate(`/procedimentos/${procedure.id}`);
  }

  return (
    <div className="page">
      <header className="page__header">
        <h1>Novo procedimento</h1>
      </header>
      <ProcedureForm onSubmit={handleSubmit} submitLabel="Cadastrar" />
    </div>
  );
}
