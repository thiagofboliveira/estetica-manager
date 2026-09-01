/**
 * Formata um objeto Date para o formato aceito por input[type="datetime-local"] (YYYY-MM-DDTHH:mm)
 * preservando exatamente o fuso horário local do usuário (sem conversões indevidas via toISOString).
 */
export function formatDateToLocalInput(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, "0");
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * Formata um objeto Date para o formato YYYY-MM-DD usando a data local (sem avançar o dia em fusos negativos à noite).
 */
export function formatLocalDate(date: Date = new Date()): string {
  const pad = (n: number) => n.toString().padStart(2, "0");
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  return `${year}-${month}-${day}`;
}
