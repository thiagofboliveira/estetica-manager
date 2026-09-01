import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import type { Patient } from "./api";

import { toast } from "@/ui/ToastContext";
import { IconWhatsApp } from "@/ui/icons";

const schema = z.object({
  name: z.string().min(1, "Nome é obrigatório"),
  phone: z.string().optional(),
  email: z.union([z.literal(""), z.string().email("E-mail inválido")]).optional(),
  birth_date: z.string().optional(),
  notes: z.string().optional(),
  consent_whatsapp: z.boolean(),
});

export type PatientFormValues = z.infer<typeof schema>;

type Props = {
  initial?: Patient;
  onSubmit: (values: PatientFormValues) => Promise<unknown>;
  submitLabel: string;
};

export function PatientForm({ initial, onSubmit, submitLabel }: Props) {
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<PatientFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initial?.name ?? "",
      phone: initial?.phone ?? "",
      email: initial?.email ?? "",
      birth_date: initial?.birth_date ?? "",
      notes: initial?.notes ?? "",
      consent_whatsapp: initial?.consent_whatsapp ?? false,
    },
  });

  // Qualquer edição após salvar invalida o "Salvo com sucesso" —
  // senão a mensagem fica presa mesmo depois de mudar campos sem reenviar.
  useEffect(() => {
    const sub = watch(() => setSaved(false));
    return () => sub.unsubscribe();
  }, [watch]);

  const submit = handleSubmit(async (values) => {
    setServerError(null);
    setSaved(false);
    try {
      await onSubmit(values);
      setSaved(true);
      toast.success("Paciente salva com sucesso!");
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Não consegui salvar. Tenta de novo?");
    }
  });

  return (
    <form onSubmit={submit} noValidate className="form">
      <label className="form__field">
        <span>Nome *</span>
        <input {...register("name")} autoComplete="name" />
        {errors.name && <span role="alert">{errors.name.message}</span>}
      </label>

      <label className="form__field">
        <span>Telefone (WhatsApp)</span>
        <input {...register("phone")} inputMode="tel" placeholder="(11) 91234-5678" />
      </label>

      <label className="form__field">
        <span>E-mail</span>
        <input {...register("email")} type="email" autoComplete="email" />
        {errors.email && <span role="alert">{errors.email.message}</span>}
      </label>

      <label className="form__field">
        <span>Data de nascimento</span>
        <input {...register("birth_date")} type="date" />
      </label>

      <label className="form__field">
        <span>Observações</span>
        <textarea {...register("notes")} rows={3} />
      </label>

      {/* Gate explícito de consentimento para contato WhatsApp */}
      <label className="whatsapp-consent-toggle">
        <input type="checkbox" {...register("consent_whatsapp")} />
        <div className="whatsapp-consent-content">
          <span className="whatsapp-consent-icon">
            <IconWhatsApp width="16" height="16" />
          </span>
          <span>Autorizou receber lembretes e mensagens no WhatsApp</span>
        </div>
      </label>

      {serverError && (
        <p role="alert" className="form__error">
          {serverError}
        </p>
      )}

      {saved && !serverError && (
        <p role="status" className="form__success">
          Salvo com sucesso.
        </p>
      )}

      <button type="submit" disabled={isSubmitting} className="tap-target">
        {isSubmitting ? "Salvando…" : submitLabel}
      </button>
    </form>
  );
}
