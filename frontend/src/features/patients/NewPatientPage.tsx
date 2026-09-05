import { useNavigate } from "react-router-dom";
import { PatientForm, type PatientFormValues } from "./PatientForm";
import { useCreatePatient } from "./hooks";

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
      consent_whatsapp: values.consent_whatsapp,
      gender: values.gender || null,
    });
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
