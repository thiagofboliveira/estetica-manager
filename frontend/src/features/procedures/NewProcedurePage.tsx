import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ProcedureForm, type ProcedureFormValues } from "./ProcedureForm";
import { toProcedurePayload } from "./mapper";
import { useCreateProcedure } from "./hooks";
import { ProcedureTemplateSelector } from "./ProcedureTemplateSelector";
import type { ProcedureTemplate, ProcedureType, Modality } from "./api";
import type { Money } from "@/lib/money/money";

export function NewProcedurePage() {
  const navigate = useNavigate();
  const create = useCreateProcedure();
  const [showSelector, setShowSelector] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<ProcedureTemplate | null>(null);

  async function handleSubmit(values: ProcedureFormValues) {
    const procedure = await create.mutateAsync(toProcedurePayload(values));
    navigate(`/procedimentos/${procedure.id}`);
  }

  function handleSelectTemplate(template: ProcedureTemplate) {
    setSelectedTemplate(template);
    setShowSelector(false);
  }

  // Mapear o template selecionado para o formato initial que o ProcedureForm espera
  const initialValues = selectedTemplate ? {
    name: selectedTemplate.name,
    type: selectedTemplate.type as ProcedureType,
    price: selectedTemplate.suggested_price as Money,
    estimated_cost: selectedTemplate.suggested_cost as Money,
    return_interval_days: selectedTemplate.suggested_return_interval_days,
    default_modality: "IN_PERSON" as Modality,
    // campos obrigatórios do mock initial
    id: "",
    is_active: true,
    is_invasive: false,
    session_plan: "SINGLE" as const,
    created_at: "",
    updated_at: "",
  } : undefined;

  return (
    <div className="page">
      <header className="page__header">
        <h1>Novo procedimento</h1>
      </header>
      
      {showSelector ? (
        <ProcedureTemplateSelector 
          onSelect={handleSelectTemplate} 
          onSkip={() => setShowSelector(false)} 
        />
      ) : (
        <ProcedureForm 
          key={selectedTemplate ? selectedTemplate.template_id : "empty"} 
          initial={initialValues} 
          onSubmit={handleSubmit} 
          submitLabel="Cadastrar" 
        />
      )}
    </div>
  );
}
