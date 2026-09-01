import { useState } from "react";
import { Link } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { useDebouncedValue } from "@/lib/hooks/useDebouncedValue";
import { usePatients } from "@/features/patients/hooks";
import type { Patient } from "@/features/patients/api";

/**
 * Busca + seleção de paciente via dropdown nativo com busca dinâmica
 * e suporte a criação rápida de novas pacientes.
 */
export function PatientPicker({
  selected,
  onSelect,
  onClear,
}: {
  selected: Patient | null;
  onSelect: (patient: Patient) => void;
  onClear: () => void;
}) {
  const [search, setSearch] = useState("");
  const debounced = useDebouncedValue(search, 300);
  const query = usePatients(debounced);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <AsyncBoundary
        query={query}
        skeleton={<p style={{ fontSize: "13px", color: "#64748b" }}>Carregando pacientes…</p>}
        empty={
          <div style={{ padding: "8px 0", fontSize: "13px", color: "#64748b" }}>
            Nenhuma paciente cadastrada.{" "}
            <Link to="/pacientes/novo" style={{ color: "var(--accent)", fontWeight: "600" }}>
              + Cadastrar nova paciente
            </Link>
          </div>
        }
      >
        {(patients) => {
          if (!patients || patients.length === 0) {
            return (
              <div style={{ padding: "8px 0", fontSize: "13px", color: "#64748b" }}>
                Nenhuma paciente encontrada.{" "}
                <Link to="/pacientes/novo" style={{ color: "var(--accent)", fontWeight: "600" }}>
                  + Cadastrar nova paciente
                </Link>
              </div>
            );
          }

          return (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <select
                value={selected?.id || ""}
                onChange={(e) => {
                  const pid = e.target.value;
                  if (!pid) {
                    onClear();
                  } else {
                    const found = patients.find((p) => p.id === pid);
                    if (found) onSelect(found);
                  }
                }}
              >
                <option value="">Selecione uma paciente…</option>
                {patients.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} {p.phone ? `(${p.phone})` : ""}
                  </option>
                ))}
              </select>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <input
                  type="search"
                  placeholder="🔍 Digite para filtrar a lista…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  style={{
                    fontSize: "13px",
                    padding: "6px 12px",
                    minHeight: "36px",
                    flex: 1,
                  }}
                />
                <Link
                  to="/pacientes/novo"
                  className="button button--secondary tap-target"
                  style={{
                    fontSize: "12.5px",
                    padding: "6px 12px",
                    minHeight: "36px",
                    whiteSpace: "nowrap",
                  }}
                >
                  + Nova Paciente
                </Link>
              </div>
            </div>
          );
        }}
      </AsyncBoundary>
    </div>
  );
}
