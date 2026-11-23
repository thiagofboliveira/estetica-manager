import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("./api", () => ({
  proceduresApi: { getTemplates: () => Promise.reject(new Error("offline")) },
}));

import { ProcedureTemplateSelector } from "./ProcedureTemplateSelector";

afterEach(cleanup);

describe("ProcedureTemplateSelector — teclado", () => {
  it("os cartões são botões focáveis e respondem a Enter e Espaço", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<ProcedureTemplateSelector onSelect={onSelect} onSkip={() => {}} />);

    const cards = await screen.findAllByRole("button", { name: /sugerido/i });
    expect(cards.length).toBeGreaterThan(0);

    cards[0].focus();
    await user.keyboard("{Enter}");
    expect(onSelect).toHaveBeenCalledTimes(1);

    await user.keyboard(" ");
    expect(onSelect).toHaveBeenCalledTimes(2);

    await user.click(cards[0]);
    expect(onSelect).toHaveBeenCalledTimes(3);
  });
});
