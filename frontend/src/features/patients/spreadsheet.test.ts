import { describe, expect, it } from "vitest";
import { parseSheet, toImportText } from "./spreadsheet";

describe("parseSheet", () => {
  it("lê CSV com ponto e vírgula, aspas e BOM", () => {
    const s = parseSheet('﻿Nome;Telefone\n"Silva, Maria";(31) 99999-0000\n\nAna;\n');
    expect(s.headers).toEqual(["Nome", "Telefone"]);
    expect(s.rows).toEqual([["Silva, Maria", "(31) 99999-0000"], ["Ana", ""]]);
  });

  it("detecta tabulação (colado do Excel)", () => {
    expect(parseSheet("Nome\tCelular\nJoana\t3199").rows[0]).toEqual(["Joana", "3199"]);
  });

  it("arquivo vazio não quebra", () => {
    expect(parseSheet("").headers).toEqual([]);
  });
});

describe("toImportText", () => {
  const sheet = { headers: ["a", "b"], rows: [["Maria", "3199"], ["", "1"], ["Ana", ""]] };
  it("gera linhas nome, telefone e ignora linhas sem nome", () => {
    expect(toImportText(sheet, { name: 0, phone: 1 })).toBe("Maria, 3199\nAna");
  });
  it("sem coluna de nome não importa nada", () => {
    expect(toImportText(sheet, { name: null, phone: 1 })).toBe("");
  });
});
