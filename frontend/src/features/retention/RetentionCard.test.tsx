import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";

const { draftMessage, testClient, failing } = vi.hoisted(() => ({
  draftMessage: vi.fn(),
  failing: { on: false },
  testClient: { current: null as unknown },
}));

// O módulo real importa o cliente HTTP, que exige VITE_API_URL.
vi.mock("@/lib/query/client", async () => {
  const { QueryClient } = await import("@tanstack/react-query");
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: 0, throwOnError: false } } });
  testClient.current = client;
  return { queryClient: client, CACHE: { MONEY: {} } };
});

vi.mock("./api", () => ({
  retentionApi: {
    draftMessage: (id: string) =>
      failing.on ? Promise.reject(new Error("offline")) : draftMessage(id),
    updateOpportunity: () => Promise.resolve(),
    reportDraftSent: () => Promise.resolve(),
  },
}));

import { RetentionCard } from "./RetentionCard";
import type { PatientRetentionCard } from "./api";

const card: PatientRetentionCard = {
  patient_id: "p1",
  patient_name: "Ana Souza",
  patient_phone: "31999990000",
  consent_whatsapp: true,
  opted_out: false,
  is_suppressed: false,
  last_contacted_at: null,
  total_potential_value: "200.00",
  primary_opportunity: {
    id: "o1",
    procedure_id: "pr1",
    procedure_name: "Limpeza de pele",
    due_date: "2026-11-01",
    timing: "OVERDUE",
    status: "OPEN",
    potential_value: "200.00",
    days_diff: -10,
  },
  secondary_opportunities: [],
  whatsapp_enabled: true,
  disabled_reason: null,
};

function renderCard(c: PatientRetentionCard = card) {
  return render(
    <QueryClientProvider client={testClient.current as QueryClient}>
      <RetentionCard card={c} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  draftMessage.mockReset();
  failing.on = false;
});
afterEach(cleanup);

describe("RetentionCard — sugerir mensagem", () => {
  it("mostra o rascunho editável e usa o texto no link do WhatsApp", async () => {
    draftMessage.mockResolvedValue({
      text: "Oi, Ana! Vamos retomar?",
      source: "ai",
      fallback_reason: null,
      remaining_drafts: 99,
    });
    const user = userEvent.setup();
    renderCard();

    await user.click(screen.getByRole("button", { name: /sugerir mensagem/i }));

    const box = await screen.findByRole("textbox", { name: /mensagem para ana souza/i });
    expect((box as HTMLTextAreaElement).value).toBe("Oi, Ana! Vamos retomar?");
    expect(draftMessage).toHaveBeenCalledWith("o1");

    const link = screen.getByRole("link", { name: /chamar no whatsapp/i });
    expect(link.getAttribute("href")).toContain(encodeURIComponent("Oi, Ana! Vamos retomar?"));
  });

  it("avisa quando o teto do mês acabou e mantém o texto padrão", async () => {
    draftMessage.mockResolvedValue({
      text: "Oi, Ana! Já está na época.",
      source: "fallback",
      fallback_reason: "limit_reached",
      remaining_drafts: 0,
    });
    const user = userEvent.setup();
    renderCard();
    await user.click(screen.getByRole("button", { name: /sugerir mensagem/i }));
    expect(await screen.findByText(/usou todas as sugestões do mês/i)).toBeTruthy();
  });

  it("se a API falhar, mostra aviso e não quebra", async () => {
    failing.on = true;
    const user = userEvent.setup();
    renderCard();
    await user.click(screen.getByRole("button", { name: /sugerir mensagem/i }));
    expect(await screen.findByText(/não foi possível gerar a sugestão/i)).toBeTruthy();
  });

  it("não oferece sugestão quando o WhatsApp está indisponível", () => {
    renderCard({ ...card, whatsapp_enabled: false, disabled_reason: "Sem consentimento" });
    expect(screen.queryByRole("button", { name: /sugerir mensagem/i })).toBeNull();
  });
});
