import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { useDebouncedValue } from "@/lib/hooks/useDebouncedValue";
import type { Gender } from "./api";
import { usePatientsPage } from "./hooks";

const PAGE_SIZE = 20;

const GENDER_OPTIONS: { value: Gender; label: string }[] = [
  { value: "FEMALE", label: "Feminino" },
  { value: "MALE", label: "Masculino" },
  { value: "OTHER", label: "Outro" },
  { value: "UNDISCLOSED", label: "Prefere não dizer" },
];

// Três estados por filtro: indefinido (sem filtro), true, false.
type TriState = boolean | undefined;

function nextTriState(current: TriState): TriState {
  if (current === undefined) return true;
  if (current === true) return false;
  return undefined;
}

export function PatientsPage() {
  const [search, setSearch] = useState("");
  const debounced = useDebouncedValue(search, 300);
  const [gender, setGender] = useState<Gender | "">("");
  const [hasUpcomingBooking, setHasUpcomingBooking] = useState<TriState>(undefined);
  const [hasCompletedTreatment, setHasCompletedTreatment] = useState<TriState>(undefined);
  const [page, setPage] = useState(1);

  // Trocar qualquer filtro com a página > 1 deixaria a tela presa numa
  // página que pode nem existir mais no novo recorte filtrado.
  useEffect(
    () => setPage(1),
    [debounced, gender, hasUpcomingBooking, hasCompletedTreatment],
  );

  const hasActiveFilters =
    Boolean(search) || Boolean(gender) || hasUpcomingBooking !== undefined || hasCompletedTreatment !== undefined;

  const query = usePatientsPage(
    {
      search: debounced || undefined,
      gender: gender || undefined,
      has_upcoming_booking: hasUpcomingBooking,
      has_completed_treatment: hasCompletedTreatment,
    },
    page,
    PAGE_SIZE,
  );
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

      <div className="filters-bar">
        <select
          value={gender}
          onChange={(e) => setGender(e.target.value as Gender | "")}
          aria-label="Filtrar por sexo"
        >
          <option value="">Sexo: todos</option>
          {GENDER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <button
          type="button"
          className={
            hasUpcomingBooking !== undefined
              ? "filters-bar__toggle filters-bar__toggle--active"
              : "filters-bar__toggle"
          }
          onClick={() => setHasUpcomingBooking((v) => nextTriState(v))}
          aria-pressed={hasUpcomingBooking !== undefined}
        >
          📅 Tem agendamento{hasUpcomingBooking === true ? ": sim" : hasUpcomingBooking === false ? ": não" : ""}
        </button>

        <button
          type="button"
          className={
            hasCompletedTreatment !== undefined
              ? "filters-bar__toggle filters-bar__toggle--active"
              : "filters-bar__toggle"
          }
          onClick={() => setHasCompletedTreatment((v) => nextTriState(v))}
          aria-pressed={hasCompletedTreatment !== undefined}
        >
          ✓ Já tratou{hasCompletedTreatment === true ? ": sim" : hasCompletedTreatment === false ? ": não" : ""}
        </button>
      </div>

      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando…</p>}
        empty={
          <EmptyState
            tone={hasActiveFilters ? "filtered" : "first-run"}
            title={hasActiveFilters ? "Nenhuma paciente encontrada" : "Nenhuma paciente cadastrada ainda"}
            body={
              hasActiveFilters
                ? "Tenta outro nome, telefone ou ajuste os filtros."
                : "Cadastre a primeira paciente para começar."
            }
          />
        }
        isEmpty={(data) => data.items.length === 0}
      >
        {(result) => {
          const totalPages = Math.max(1, Math.ceil(result.total_count / result.page_size));

          return (
            <>
              <ul className="list">
                {result.items.map((p) => (
                  <li key={p.id} className="list__item">
                    <button className="list__item-btn tap-target" onClick={() => navigate(p.id)}>
                      <span className="list__item-title">{p.name}</span>
                      {p.phone && <span className="list__item-sub">{p.phone}</span>}
                    </button>
                  </li>
                ))}
              </ul>

              {totalPages > 1 && (
                <nav className="pagination" aria-label="Páginas de pacientes">
                  <button
                    type="button"
                    className="tap-target"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                  >
                    ← Anterior
                  </button>
                  <span className="pagination__status">
                    Página {page} de {totalPages} · {result.total_count}{" "}
                    {result.total_count === 1 ? "paciente" : "pacientes"}
                  </span>
                  <button
                    type="button"
                    className="tap-target"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                  >
                    Próxima →
                  </button>
                </nav>
              )}
            </>
          );
        }}
      </AsyncBoundary>
    </div>
  );
}
