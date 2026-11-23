import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, renderHook } from "@testing-library/react";

// A rejeição vem de uma função comum: o spy do vitest reporta rejeição de vi.fn como não tratada.
const { reportDraftSent, failing } = vi.hoisted(() => ({
  reportDraftSent: vi.fn(),
  failing: { on: false },
}));

vi.mock("./api", () => ({
  retentionApi: {
    reportDraftSent: (edited: boolean) =>
      failing.on ? Promise.reject(new Error("offline")) : reportDraftSent(edited),
  },
}));

import { useDraftComposer } from "./useDraftComposer";
import type { DraftMessage } from "./api";

const aiDraft: DraftMessage = {
  text: "Oi, Bia! Que tal voltar?",
  source: "ai",
  fallback_reason: null,
  remaining_drafts: 9,
};

beforeEach(() => {
  reportDraftSent.mockReset().mockResolvedValue(undefined);
  failing.on = false;
});
afterEach(cleanup);

describe("useDraftComposer", () => {
  it("gera, avisa que é sugestão e reporta envio sem edição", async () => {
    const { result } = renderHook(() => useDraftComposer(async () => aiDraft, {}));
    await act(() => result.current.generate());
    expect(result.current.message).toBe(aiDraft.text);
    expect(result.current.notice).toMatch(/sugestão pronta/i);

    act(() => result.current.reportSent());
    expect(reportDraftSent).toHaveBeenCalledWith(false);
  });

  it("reporta envio editado quando a profissional mudou o texto", async () => {
    const { result } = renderHook(() => useDraftComposer(async () => aiDraft, {}));
    await act(() => result.current.generate());
    act(() => result.current.setMessage("Oi, Bia! Vamos marcar?"));
    act(() => result.current.reportSent());
    expect(reportDraftSent).toHaveBeenCalledWith(true);
  });

  it("não conta o texto padrão como rascunho da IA", async () => {
    const fallback: DraftMessage = {
      ...aiDraft,
      source: "fallback",
      fallback_reason: "limit_reached",
    };
    const { result } = renderHook(() => useDraftComposer(async () => fallback, {}));
    await act(() => result.current.generate());
    expect(result.current.notice).toMatch(/todas as sugestões do mês/i);
    act(() => result.current.reportSent());
    expect(reportDraftSent).not.toHaveBeenCalled();
  });

  it("não reporta nada se nunca gerou rascunho", () => {
    const { result } = renderHook(() => useDraftComposer(async () => aiDraft, {}));
    act(() => result.current.reportSent());
    expect(reportDraftSent).not.toHaveBeenCalled();
  });

  it("falha da medição não atrapalha o envio", async () => {
    failing.on = true;
    const { result } = renderHook(() => useDraftComposer(async () => aiDraft, {}));
    await act(() => result.current.generate());
    expect(() => act(() => result.current.reportSent())).not.toThrow();
  });
});
