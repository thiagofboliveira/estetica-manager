export const MESSAGES = {
  RETENTION: {
    WHATSAPP_DEFAULT: "Olá, {{patient_name}}! Tudo bem? Passando para lembrar que já está no período ideal para o seu retorno de {{procedure_name}}. Gostaria de agendar um horário esta semana?",
  }
};

export function fillTemplate(template: string, variables: Record<string, string>) {
  return Object.entries(variables).reduce((acc, [key, value]) => {
    return acc.replace(new RegExp(`{{${key}}}`, "g"), value);
  }, template);
}
