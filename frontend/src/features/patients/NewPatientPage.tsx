import { useNavigate } from "react-router-dom";
import { PatientForm, type PatientFormValues } from "./PatientForm";
import { useCreatePatient } from "./hooks";
import { patientsApi } from "./api";

export function NewPatientPage() {
  const navigate = useNavigate();
  const create = useCreatePatient();

  async function handleSubmit(values: PatientFormValues) {
    const patient = await create.mutateAsync({
      name: values.name,
      phone: values.phone || null,
      email: values.email || null,
      birth_date: values.birth_date || null,
      notes: values.notes || null,
    });
    // POST /patients (PatientCreate) não aceita consent_whatsapp — só
    // PATCH aceita. Marcar o checkbox na criação exige um PATCH logo
    // em seguida, senão o campo fica visível no form mas não persiste
    // (achado real: bug silencioso do F-011b/F-015b).
    if (values.consent_whatsapp) {
      await patientsApi.update(patient.id, { consent_whatsapp: true });
    }
    navigate(`/pacientes/${patient.id}`);
  }

  return (
    <div className="page">
      <header className="page__header">
        <h1>Nova paciente</h1>
      </header>
      <PatientForm onSubmit={handleSubmit} submitLabel="Cadastrar" />
    </div>
  );
}
