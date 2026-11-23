import { afterEach, describe, expect, it } from "vitest";
import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { confirmDialog } from "./confirmDialog";

afterEach(() => {
  cleanup();
  document.body.innerHTML = "";
});

describe("confirmDialog (substitui window.confirm)", () => {
  it("abre um alertdialog acessível com a mensagem e foco em Cancelar", async () => {
    void confirmDialog("Deseja excluir a regra?");
    const dialog = await screen.findByRole("alertdialog");
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect(dialog.textContent).toContain("Deseja excluir a regra?");
    // Foco em "Cancelar": Enter por engano nunca confirma ação destrutiva.
    expect(document.activeElement?.textContent).toBe("Cancelar");
  });

  it("resolve true ao confirmar e remove o diálogo", async () => {
    const user = userEvent.setup();
    const result = confirmDialog("Confirmar?");
    await user.click(await screen.findByRole("button", { name: "Confirmar" }));
    expect(await result).toBe(true);
    await waitFor(() => expect(screen.queryByRole("alertdialog")).toBeNull());
  });

  it("resolve false ao cancelar", async () => {
    const user = userEvent.setup();
    const result = confirmDialog("Confirmar?");
    await user.click(await screen.findByRole("button", { name: "Cancelar" }));
    expect(await result).toBe(false);
  });

  it("resolve false com Esc", async () => {
    const user = userEvent.setup();
    const result = confirmDialog("Confirmar?");
    await screen.findByRole("alertdialog");
    await user.keyboard("{Escape}");
    expect(await result).toBe(false);
  });

  it("aceita rótulos personalizados", async () => {
    const result = confirmDialog("Apagar?", { confirmLabel: "Apagar", title: "Atenção" });
    expect(await screen.findByRole("button", { name: "Apagar" })).toBeTruthy();
    expect(screen.getByText("Atenção")).toBeTruthy();
    void result;
  });

  it("Tab não escapa do diálogo", async () => {
    const user = userEvent.setup();
    void confirmDialog("Confirmar?");
    await screen.findByRole("alertdialog");
    await user.tab(); // Cancelar -> Confirmar
    expect(document.activeElement?.textContent).toBe("Confirmar");
    await user.tab(); // volta para Cancelar
    expect(document.activeElement?.textContent).toBe("Cancelar");
  });
});
