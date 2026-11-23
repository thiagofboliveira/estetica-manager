import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { QueryClient } from "@tanstack/react-query";
import { QueryClientProvider } from "@tanstack/react-query";

const { getAlerts, explain, client } = vi.hoisted(() => ({
  getAlerts: vi.fn(),
  explain: vi.fn(),
  client: { current: null as unknown },
}));

vi.mock("@/lib/query/client", async () => {
  const { QueryClient } = await import("@tanstack/react-query");
  const c = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  client.current = c;
  return { queryClient: c, CACHE: { MONEY: {} } };
});
vi.mock("@/ui/ToastContext", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));
vi.mock("./api", () => ({
  lossAlertsApi: { get: () => getAlerts(), explain: () => explain() },
}));

import { LossAlertsCard } from "./LossAlertsCard";

const alert = {
  procedure_id: "p1",
  procedure_name: "Peeling",
  kind: "loss" as const,
  gross_revenue: "1000.00",
  net_profit: "-80.00",
  margin_percent: -8,
  session_count: 4,
};

function renderCard() {
  (client.current as QueryClient).clear();
  return render(
    <QueryClientProvider client={client.current as QueryClient}>
      <LossAlertsCard />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getAlerts.mockReset();
  explain.mockReset();
});
afterEach(cleanup);

describe("LossAlertsCard", () => {
  it("lista o procedimento com ícone e texto (não só cor) e o aviso de estimativa", async () => {
    getAlerts.mockResolvedValue({ period: "this_month", date_from: "", date_to: "", alerts: [alert] });
    renderCard();
    expect(await screen.findByText("Peeling")).toBeTruthy();
    expect(screen.getByText(/prejuízo/i)).toBeTruthy();
    expect(screen.getByText(/margem -8%/i)).toBeTruthy();
    expect(screen.getByText(/podem incluir custos estimados/i)).toBeTruthy();
  });

  it("não mostra nada quando não há alertas", async () => {
    getAlerts.mockResolvedValue({ period: "this_month", date_from: "", date_to: "", alerts: [] });
    const { container } = renderCard();
    await vi.waitFor(() => expect(getAlerts).toHaveBeenCalled());
    expect(container.textContent).toBe("");
  });

  it("explica com IA e identifica a origem do texto", async () => {
    getAlerts.mockResolvedValue({ period: "this_month", date_from: "", date_to: "", alerts: [alert] });
    explain.mockResolvedValue({
      text: "Revise o custo dos insumos do Peeling.",
      source: "ai",
      fallback_reason: null,
      remaining_drafts: 9,
    });
    const user = userEvent.setup();
    renderCard();
    await user.click(await screen.findByRole("button", { name: /explicar com ia/i }));
    expect(await screen.findByText(/revise o custo dos insumos/i)).toBeTruthy();
    expect(screen.getByText(/sugerido automaticamente/i)).toBeTruthy();
  });
});
