import { useParams } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { PatientForm, type PatientFormValues } from "./PatientForm";
import { usePatient, useUpdatePatient } from "./hooks";

export function PatientDetailPage() {
  const { id = "" } = useParams();
  const query = usePatient(id);
  const update = useUpdatePatient(id);

  async function handleSubmit(values: PatientFormValues) {
    await update.mutateAsync({
      name: values.name,
      phone: values.phone || null,
      email: values.email || null,
      birth_date: values.birth_date || null,
      notes: values.notes || null,
      consent_whatsapp: values.consent_whatsapp,
    });
  }

  return (
    <div className="page">
      <header className="page__header">
        <h1>Paciente</h1>
      </header>
      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando…</p>}
        empty={<p>Paciente não encontrada.</p>}
        isEmpty={(p) => p == null}
      >
        {(patient) => (
          <PatientForm initial={patient} onSubmit={handleSubmit} submitLabel="Salvar" />
        )}
      </AsyncBoundary>
    </div>
  );
}
