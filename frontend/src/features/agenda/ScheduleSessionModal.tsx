import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import type { OpenPackage } from "./api";
import { useScheduleSession } from "./hooks";

const schema = z.object({
  scheduled_at: z.string().min(1, "Data e horário são obrigatórios"),
  notes: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

type Props = {
  pkg: OpenPackage;
  onClose: () => void;
};

export function ScheduleSessionModal({ pkg, onClose }: Props) {
  const scheduleSession = useScheduleSession();
  const [serverError, setServerError] = useState<string | null>(null);

  // Data/hora padrão: amanhã às 10:00
  const defaultDate = new Date();
  defaultDate.setDate(defaultDate.getDate() + 1);
  defaultDate.setHours(10, 0, 0, 0);
  const defaultIso = defaultDate.toISOString().slice(0, 16);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      scheduled_at: defaultIso,
      notes: "",
    },
  });

  const submit = handleSubmit(async (values) => {
    if (!pkg.next_pending_session_id) {
      setServerError("Nenhuma sessão pendente encontrada neste pacote.");
      return;
    }

    setServerError(null);
    try {
      await scheduleSession.mutateAsync({
        id: pkg.next_pending_session_id,
        payload: {
          scheduled_at: new Date(values.scheduled_at).toISOString(),
          status: "SCHEDULED",
          notes: values.notes || null,
        },
      });
      onClose();
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Erro ao agendar sessão.");
    }
  });

  return (
    <div className="modal-backdrop">
      <div className="modal-card">
        <header className="modal-header">
          <h3>Agendar Sessão de Pacote</h3>
          <button type="button" className="modal-close" onClick={onClose}>
            ✕
          </button>
        </header>

        <div className="modal-info">
          <p>
            <strong>Paciente:</strong> {pkg.patient_name}
          </p>
          <p>
            <strong>Procedimento:</strong> {pkg.procedure_name} (Sessão {pkg.used_sessions + 1} de {pkg.total_sessions})
          </p>
        </div>

        <form onSubmit={submit} className="form">
          <label className="form__field">
            <span>Data e Horário do Atendimento *</span>
            <input {...register("scheduled_at")} type="datetime-local" />
            {errors.scheduled_at && (
              <span role="alert" className="form__error">
                {errors.scheduled_at.message}
              </span>
            )}
          </label>

          <label className="form__field">
            <span>Observações da sessão</span>
            <textarea {...register("notes")} rows={2} placeholder="ex: Aplicar na região frontal" />
          </label>

          {serverError && (
            <p role="alert" className="form__error">
              {serverError}
            </p>
          )}

          <div className="form__actions">
            <button type="submit" disabled={isSubmitting} className="tap-target">
              {isSubmitting ? "Agendando…" : "Confirmar Agendamento"}
            </button>
            <button type="button" onClick={onClose} className="tap-target button--ghost">
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
