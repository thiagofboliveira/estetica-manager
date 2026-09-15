import { describe, expect, it } from "vitest";
import { normalizeWhatsAppPhone, toWhatsAppUrl } from "./whatsapp";

describe("normalizeWhatsAppPhone", () => {
  it("retorna null para valores nulos, indefinidos ou vazios", () => {
    expect(normalizeWhatsAppPhone(null)).toBeNull();
    expect(normalizeWhatsAppPhone(undefined)).toBeNull();
    expect(normalizeWhatsAppPhone("")).toBeNull();
    expect(normalizeWhatsAppPhone("   ")).toBeNull();
    expect(normalizeWhatsAppPhone("abc-()")).toBeNull();
  });

  it("não duplica 55 quando o telefone vem em E.164 (+55...)", () => {
    // Celular com DDD 11 vindo do backend
    expect(normalizeWhatsAppPhone("+5511987654321")).toBe("5511987654321");
    // Fixo com DDD 21 vindo do backend
    expect(normalizeWhatsAppPhone("+552133445566")).toBe("552133445566");
  });

  it("não duplica 55 quando o telefone já tem 55 com máscara ou sem", () => {
    expect(normalizeWhatsAppPhone("+55 (11) 98765-4321")).toBe("5511987654321");
    expect(normalizeWhatsAppPhone("5511987654321")).toBe("5511987654321");
  });

  it("adiciona 55 para números locais de 10 ou 11 dígitos", () => {
    // Celular 11 dígitos (DDD + 9 dígitos)
    expect(normalizeWhatsAppPhone("(11) 98765-4321")).toBe("5511987654321");
    expect(normalizeWhatsAppPhone("11987654321")).toBe("5511987654321");
    // Fixo 10 dígitos (DDD + 8 dígitos)
    expect(normalizeWhatsAppPhone("(11) 3344-5566")).toBe("551133445566");
    expect(normalizeWhatsAppPhone("1133445566")).toBe("551133445566");
  });

  it("remove zero à esquerda e adiciona 55 se restar 10 ou 11 dígitos", () => {
    expect(normalizeWhatsAppPhone("011987654321")).toBe("5511987654321");
    expect(normalizeWhatsAppPhone("01133445566")).toBe("551133445566");
  });

  it("trata corretamente DDD 55 (Santa Maria / RS)", () => {
    // E.164 de DDD 55: +55 55 99999-8888 -> 13 dígitos
    expect(normalizeWhatsAppPhone("+5555999998888")).toBe("5555999998888");
    // Sem DDI: (55) 99999-8888 -> 11 dígitos -> adiciona DDI 55 na frente
    expect(normalizeWhatsAppPhone("(55) 99999-8888")).toBe("5555999998888");
  });
});

describe("toWhatsAppUrl", () => {
  it("retorna null se não houver telefone válido", () => {
    expect(toWhatsAppUrl(null)).toBeNull();
    expect(toWhatsAppUrl("")).toBeNull();
    expect(toWhatsAppUrl(undefined, "Olá")).toBeNull();
  });

  it("gera url wa.me sem mensagem", () => {
    expect(toWhatsAppUrl("+5511987654321")).toBe("https://wa.me/5511987654321");
    expect(toWhatsAppUrl("(11) 98765-4321")).toBe("https://wa.me/5511987654321");
  });

  it("gera url wa.me com mensagem encodada corretamente", () => {
    const url = toWhatsAppUrl("+5511987654321", "Olá Maria! Tudo bem?");
    expect(url).toBe("https://wa.me/5511987654321?text=Ol%C3%A1%20Maria!%20Tudo%20bem%3F");
  });

  it("ignora mensagem vazia ou só com espaços", () => {
    expect(toWhatsAppUrl("+5511987654321", "   ")).toBe("https://wa.me/5511987654321");
  });
});
