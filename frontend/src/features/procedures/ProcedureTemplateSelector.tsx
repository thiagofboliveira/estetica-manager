import { useState, useEffect } from "react";
import { proceduresApi, type ProcedureTemplate } from "./api";
import { formatBRL } from "@/lib/money/format";
import type { Money } from "@/lib/money/money";
import { IconSparkles, IconArrowRight } from "@/ui/icons";
import styles from "./ProcedureTemplateSelector.module.css";

type Props = {
  onSelect: (template: ProcedureTemplate) => void;
  onSkip: () => void;
};

// MOCK para testes antes do backend estar pronto
const MOCK_TEMPLATES: ProcedureTemplate[] = [
  { template_id: "1", name: "Limpeza de Pele Profunda", type: "SERVICE", suggested_price: "180", suggested_cost: "30", suggested_return_interval_days: 30, category: "Facial" },
  { template_id: "2", name: "Peeling Químico", type: "SERVICE", suggested_price: "250", suggested_cost: "50", suggested_return_interval_days: 21, category: "Facial" },
  { template_id: "3", name: "Botox (Terço Superior)", type: "SERVICE", suggested_price: "850", suggested_cost: "350", suggested_return_interval_days: 120, category: "Injetáveis" },
  { template_id: "4", name: "Preenchimento Labial", type: "SERVICE", suggested_price: "1100", suggested_cost: "450", suggested_return_interval_days: 365, category: "Injetáveis" },
  { template_id: "5", name: "Drenagem Linfática", type: "SERVICE", suggested_price: "120", suggested_cost: "10", suggested_return_interval_days: 7, category: "Corporal" },
];

export function ProcedureTemplateSelector({ onSelect, onSkip }: Props) {
  const [templates, setTemplates] = useState<ProcedureTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Tenta buscar da API, mas se falhar (pois backend pode não estar pronto), usa mock
    proceduresApi.getTemplates()
      .then(data => setTemplates(data.length ? data : MOCK_TEMPLATES))
      .catch(() => setTemplates(MOCK_TEMPLATES))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <div className={styles.container}>Carregando templates pré-configurados...</div>;
  }

  // Agrupar por categoria
  const grouped = templates.reduce((acc, curr) => {
    if (!acc[curr.category]) acc[curr.category] = [];
    acc[curr.category].push(curr);
    return acc;
  }, {} as Record<string, ProcedureTemplate[]>);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.titleRow}>
          <div className={styles.iconBadge}>
            <IconSparkles width="18" height="18" />
          </div>
          <div>
            <h2 className={styles.title}>Comece com um template de mercado</h2>
            <p className={styles.subtitle}>Valores médios recomendados pela curadoria estética. Você pode personalizar todos os campos.</p>
          </div>
        </div>
      </header>

      {Object.entries(grouped).map(([category, items]) => (
        <div key={category} className={styles.categoryGroup}>
          <h3 className={styles.categoryTitle}>{category}</h3>
          <div className={styles.grid}>
            {items.map(t => (
              <div key={t.template_id} className={styles.card} onClick={() => onSelect(t)}>
                <div className={styles.cardName}>{t.name}</div>
                <div className={styles.cardPrice}>
                  <span>~{formatBRL(t.suggested_price as Money)}</span>
                  <span className={styles.badge}>sugerido</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className={styles.footer}>
        <button type="button" className={styles.btnSkip} onClick={onSkip}>
          <span>Cadastrar procedimento do zero</span>
          <IconArrowRight width="14" height="14" />
        </button>
      </div>
    </div>
  );
}
