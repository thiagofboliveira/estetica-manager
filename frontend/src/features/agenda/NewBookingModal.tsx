import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import type { Modality } from "./api";
import { formatDateToLocalInput } from "@/lib/format/date";
import { useCreateBooking } from "./hooks";

const schema = z.object({
  patient_name_hint: z.string().min(1, "Nome do paciente ou contato é obrigatório"),
  scheduled_at: z.string().min(1, "Data e horário são obrigatórios"),
  modality: z.enum(["IN_PERSON", "REMOTE"]),
  note: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

type Props = {
  onClose: () => void;
};

export function NewBookingModal({ onClose }: Props) {
  const createBooking = useCreateBooking();
  const [serverError, setServerError] = useState<string | null>(null);

  // Data padrão: hoje na próxima hora cheia (hora local)
  const now = new Date();
  now.setHours(now.getHours() + 1, 0, 0, 0);
  
  const localISOTime = formatDateToLocalInput(now);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      patient_name_hint: "",
      scheduled_at: localISOTime,
      modality: "IN_PERSON",
      note: "",
    },
  });

  const submit = handleSubmit(async (values) => {
    setServerError(null);
    try {
      await createBooking.mutateAsync({
        patient_name_hint: values.patient_name_hint,
        scheduled_at: new Date(values.scheduled_at).toISOString(),
        modality: values.modality as Modality,
        note: values.note || null,
      });
      onClose();
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Erro ao criar agendamento provisório.");
    }
  });

  return (
    <div className="modal-backdrop">
      <div className="modal-card">
        <header className="modal-header">
          <h3>Novo Agendamento Provisório</h3>
          <button type="button" className="modal-close" onClick={onClose}>
            ✕
          </button>
        </header>

        <p className="form__hint">
          Reserve um horário na agenda para um contato novo mesmo antes de registrar o pagamento ou a venda.
        </p>

        <form onSubmit={submit} className="form">
          <label className="form__field">
            <span>Nome do Paciente ou Contato *</span>
            <input {...register("patient_name_hint")} placeholder="ex: Juliana Silva (WhatsApp)" />
            {errors.patient_name_hint && (
              <span role="alert" className="form__error">
                {errors.patient_name_hint.message}
              </span>
            )}
          </label>

          <label className="form__field">
            <span>Data e Horário *</span>
            <input {...register("scheduled_at")} type="datetime-local" />
            {errors.scheduled_at && (
              <span role="alert" className="form__error">
                {errors.scheduled_at.message}
              </span>
            )}
          </label>

          <fieldset className="form__field">
            <legend>Modalidade do Atendimento</legend>
            <label className="radio-label">
              <input type="radio" value="IN_PERSON" {...register("modality")} />
              <span>📍 Presencial (consultório)</span>
            </label>
            <label className="radio-label">
              <input type="radio" value="REMOTE" {...register("modality")} />
              <span>💻 Remoto / Videochamada</span>
            </label>
          </fieldset>

          <label className="form__field">
            <span>Observações / Procedimento previsto</span>
            <textarea {...register("note")} rows={2} placeholder="ex: Avaliação Botox / Dúvidas" />
          </label>

          {serverError && (
            <p role="alert" className="form__error">
              {serverError}
            </p>
          )}

          <div className="form__actions">
            <button type="submit" disabled={isSubmitting} className="tap-target">
              {isSubmitting ? "Salvando…" : "Reservar Horário"}
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
