import { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { escapeToClose, focusModal } from "./modalA11y";

afterEach(cleanup);

function Demo() {
  const [open, setOpen] = useState(true);
  if (!open) return <p>fechado</p>;
  return (
    <div
      data-testid="overlay"
      ref={focusModal}
      tabIndex={-1}
      onKeyDown={escapeToClose(() => setOpen(false))}
    >
      <div role="dialog" aria-modal="true" aria-label="Exemplo">
        <input aria-label="nome" autoFocus />
      </div>
    </div>
  );
}

describe("modalA11y", () => {
  it("não rouba o foco de um campo já focado dentro do modal", () => {
    render(<Demo />);
    expect(document.activeElement).toBe(screen.getByLabelText("nome"));
  });

  it("Esc fecha o modal", async () => {
    const user = userEvent.setup();
    render(<Demo />);
    await user.keyboard("{Escape}");
    expect(screen.getByText("fechado")).toBeTruthy();
  });

  it("expõe role=dialog com aria-modal", () => {
    render(<Demo />);
    expect(screen.getByRole("dialog").getAttribute("aria-modal")).toBe("true");
  });
});
