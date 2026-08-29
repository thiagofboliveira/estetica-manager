import { useState } from "react";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { useDebouncedValue } from "@/lib/hooks/useDebouncedValue";
import { usePatientsSearch } from "@/features/patients/hooks";
import type { Patient } from "@/features/patients/api";

/**
 * Busca + seleção de paciente, compartilhada entre venda avulsa (F-014)
 * e venda de pacote (F-014b) — mesmo padrão de `PatientsPage`, mas
 * inline em vez de navegar para outra tela.
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
  const query = usePatientsSearch(debounced);

  if (selected) {
    return (
      <div className="sale-form__selected">
        <span>{selected.name}</span>
        <button type="button" className="tap-target" onClick={onClear}>
          Trocar
        </button>
      </div>
    );
  }

  return (
    <>
      <input
        type="search"
        placeholder="Buscar por nome ou telefone…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        aria-label="Buscar paciente"
      />
      {debounced && (
        <AsyncBoundary query={query} skeleton={<p>Buscando…</p>} empty={<p>Nenhuma paciente encontrada.</p>}>
          {(patients) => (
            <ul className="list">
              {patients.map((p) => (
                <li key={p.id} className="list__item">
                  <button
                    type="button"
                    className="list__item-btn tap-target"
                    onClick={() => onSelect(p)}
                  >
                    <span className="list__item-title">{p.name}</span>
                    {p.phone && <span className="list__item-sub">{p.phone}</span>}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </AsyncBoundary>
      )}
    </>
  );
}
