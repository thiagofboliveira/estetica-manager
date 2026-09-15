/**
 * Utilitários para normalização de telefone e geração de links do WhatsApp (wa.me).
 *
 * Contrato:
 * - Telefones no backend são normalizados em formato E.164 (+5511987654321).
 * - O link wa.me/{número} espera o número internacional sem o prefixo '+' e sem pontuação.
 * - Números brasileiros têm DDI 55 + DDD (2 dígitos) + 8 ou 9 dígitos (total 12 ou 13 dígitos).
 * - Se o número vier sem DDI (10 ou 11 dígitos), o DDI 55 é adicionado automaticamente.
 * - NUNCA prefixe "55" cegamente: se o número já tiver 12 ou 13 dígitos começando com 55,
 *   adicionar "55" novamente gerava "5555...", tornando o link inválido.
 */

export function normalizeWhatsAppPhone(phone: string | null | undefined): string | null {
  if (!phone) return null;
  const digits = phone.replace(/\D/g, "");
  if (!digits) return null;

  // Remove zeros à esquerda (ex: 011987654321 -> 11987654321)
  const stripped = digits.replace(/^0+/, "");
  if (!stripped) return null;

  // Se tem 10 ou 11 dígitos, é um número brasileiro sem DDI (DDD + 8 ou 9 dígitos)
  if (stripped.length === 10 || stripped.length === 11) {
    return `55${stripped}`;
  }

  // Se já começa com 55 e tem 12 ou 13 dígitos (DDI 55 + DDD + 8 ou 9 dígitos), mantém
  if (stripped.startsWith("55") && (stripped.length === 12 || stripped.length === 13)) {
    return stripped;
  }

  // Outros formatos internacionais (ou casos fora do padrão BR), retorna os dígitos limpos
  return stripped;
}

export function toWhatsAppUrl(
  phone: string | null | undefined,
  message?: string | null
): string | null {
  const normalizedPhone = normalizeWhatsAppPhone(phone);
  if (!normalizedPhone) return null;

  const baseUrl = `https://wa.me/${normalizedPhone}`;
  if (message && message.trim()) {
    return `${baseUrl}?text=${encodeURIComponent(message.trim())}`;
  }
  return baseUrl;
}
