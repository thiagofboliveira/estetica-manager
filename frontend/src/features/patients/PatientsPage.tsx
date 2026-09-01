import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { useDebouncedValue } from "@/lib/hooks/useDebouncedValue";
import { usePatientsSearch } from "./hooks";

export function PatientsPage() {
  const [search, setSearch] = useState("");
  const debounced = useDebouncedValue(search, 300);
  const query = usePatientsSearch(debounced);
  const navigate = useNavigate();

  return (
    <div className="page">
      <header className="page__header">
        <h1>Pacientes</h1>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="tap-target button--ghost" onClick={() => navigate("importar")}>
            📥 Importar
          </button>
          <button className="tap-target" onClick={() => navigate("novo")}>
            + Nova
          </button>
        </div>
      </header>

      <input
        type="search"
        placeholder="Buscar por nome ou telefone…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        aria-label="Buscar paciente"
        className="page__search"
      />

      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando…</p>}
        empty={
          <EmptyState
            tone={search ? "filtered" : "first-run"}
            title={search ? "Nenhuma paciente encontrada" : "Nenhuma paciente cadastrada ainda"}
            body={search ? "Tenta outro nome ou telefone." : "Cadastre a primeira paciente para começar."}
          />
        }
      >
        {(patients) => (
          <ul className="list">
            {patients.map((p) => (
              <li key={p.id} className="list__item">
                <button className="list__item-btn tap-target" onClick={() => navigate(p.id)}>
                  <span className="list__item-title">{p.name}</span>
                  {p.phone && <span className="list__item-sub">{p.phone}</span>}
                </button>
              </li>
            ))}
          </ul>
        )}
      </AsyncBoundary>
    </div>
  );
}
