import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const { narrative, failing } = vi.hoisted(() => ({
  narrative: vi.fn(),
  failing: { on: false },
}));

vi.mock("./api", () => ({
  weeklySummaryApi: {
    get: () =>
      Promise.resolve({
        professional_name: "Ana",
        period_start: "2026-11-16",
        period_end: "2026-11-22",
        gross_revenue: "1234.50",
        net_profit: "800.00",
        sales_count: 7,
        pending_opportunities_count: 3,
        weekly_summary_enabled: true,
        whatsapp_message: "msg",
        whatsapp_url: null,
        unsubscribe_url: "u",
      }),
    narrative: () =>
      failing.on ? Promise.reject(new Error("offline")) : narrative(),
    updateSettings: () => Promise.resolve({ weekly_summary_enabled: true }),
  },
}));
vi.mock("@/ui/ToastContext", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

import { WeeklySummarySection } from "./WeeklySummarySection";

beforeEach(() => {
  narrative.mockReset();
  failing.on = false;
});
afterEach(cleanup);

describe("WeeklySummarySection — resumo em texto", () => {
  it("mostra o texto sugerido pela IA com o aviso de origem", async () => {
    narrative.mockResolvedValue({
      text: "Boa semana: 7 atendimentos.",
      source: "ai",
      fallback_reason: null,
      remaining_drafts: 9,
    });
    const user = userEvent.setup();
    render(<WeeklySummarySection />);
    await user.click(await screen.findByRole("button", { name: /resumir minha semana/i }));
    expect(await screen.findByText("Boa semana: 7 atendimentos.")).toBeTruthy();
    expect(screen.getByText(/sugerido automaticamente/i)).toBeTruthy();
  });

  it("identifica o texto padrão quando a IA não responde", async () => {
    narrative.mockResolvedValue({
      text: "Na semana você faturou R$ 1.234,50.",
      source: "fallback",
      fallback_reason: "no_provider",
      remaining_drafts: 9,
    });
    const user = userEvent.setup();
    render(<WeeklySummarySection />);
    await user.click(await screen.findByRole("button", { name: /resumir minha semana/i }));
    expect(await screen.findByText(/texto padrão com os números/i)).toBeTruthy();
  });

  it("falha da API não quebra a tela", async () => {
    failing.on = true;
    const user = userEvent.setup();
    render(<WeeklySummarySection />);
    await user.click(await screen.findByRole("button", { name: /resumir minha semana/i }));
    expect(await screen.findByRole("button", { name: /resumir minha semana/i })).toBeTruthy();
  });
});
