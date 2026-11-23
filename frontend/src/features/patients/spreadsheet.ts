/** AI-08: leitura de planilha CSV/TSV no navegador. O arquivo inteiro nunca
 * sai daqui: ao backend (e à IA) vão só os cabeçalhos e até 5 linhas de exemplo. */

export const MAX_IMPORT_ROWS = 100; // limite do lote em POST /patients/import
export const MAX_FILE_BYTES = 1_000_000;

export type Sheet = { headers: string[]; rows: string[][] };
export type ColumnMapping = { name: number | null; phone: number | null };

function detectDelimiter(firstLine: string): string {
  const counts = [";", "\t", ","].map((d) => [d, firstLine.split(d).length] as const);
  return counts.sort((a, b) => b[1] - a[1])[0][0];
}

export function parseSheet(raw: string): Sheet {
  const text = raw.replace(/^﻿/, "").replace(/\r\n?/g, "\n");
  const delimiter = detectDelimiter(text.split("\n", 1)[0] ?? "");
  const records: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') {
        cell += '"';
        i++;
      } else if (ch === '"') quoted = false;
      else cell += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === delimiter) {
      row.push(cell.trim());
      cell = "";
    } else if (ch === "\n") {
      row.push(cell.trim());
      cell = "";
      records.push(row);
      row = [];
    } else cell += ch;
  }
  row.push(cell.trim());
  records.push(row);
  const filled = records.filter((r) => r.some((c) => c !== ""));
  if (filled.length === 0) return { headers: [], rows: [] };
  return { headers: filled[0], rows: filled.slice(1) };
}

/** Converte a planilha no texto "nome, telefone" que a tela de importação já
 * entende (pré-visualização e envio seguem o fluxo existente). */
export function toImportText(sheet: Sheet, mapping: ColumnMapping): string {
  if (mapping.name === null) return "";
  return sheet.rows
    .map((r) => {
      const name = r[mapping.name as number]?.trim() ?? "";
      const phone = mapping.phone === null ? "" : (r[mapping.phone]?.trim() ?? "");
      return name ? (phone ? `${name}, ${phone}` : name) : "";
    })
    .filter(Boolean)
    .join("\n");
}
