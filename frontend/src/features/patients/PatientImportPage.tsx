import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { usePatientImport } from "./hooks";
import type { BatchImportResult } from "./api";
import { IconUsers, IconCheck, IconAlertTriangle, IconArrowRight, IconSparkles } from "@/ui/icons";
import styles from "./PatientImport.module.css";

type Step = 1 | 2 | 3 | 4;
type ParsedRow = { name: string; phone: string | null; status: "OK" | "WARN" };

export function PatientImportPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>(1);
  const [text, setText] = useState("");
  const [result, setResult] = useState<BatchImportResult | null>(null);
  
  const importMutation = usePatientImport();

  const parsedData = useMemo(() => {
    if (!text.trim()) return [];
    
    const lines = text.split('\n');
    const rows: ParsedRow[] = [];
    
    for (const line of lines) {
      if (!line.trim()) continue;
      
      const parts = line.split(/[\t,;]/);
      const name = parts[0]?.trim();
      const phone = parts.length > 1 ? parts.slice(1).join("").replace(/[^\d+()-\s]/g, "").trim() : null;
      
      if (name) {
        rows.push({
          name,
          phone: phone || null,
          status: phone ? "OK" : "WARN"
        });
      }
    }
    return rows;
  }, [text]);

  function handleGoToReview() {
    if (parsedData.length === 0) return;
    setStep(2);
  }

  async function handleConfirm() {
    if (parsedData.length === 0) return;
    
    setStep(3);
    try {
      const payload = {
        patients: parsedData.map(r => ({ name: r.name, phone: r.phone }))
      };
      const res = await importMutation.mutateAsync(payload);
      setResult(res);
      setStep(4);
    } catch (err) {
      alert("Erro ao importar pacientes. Verifique o console.");
      console.error(err);
      setStep(2);
    }
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.titleRow}>
          <div className={styles.iconBadge}>
            <IconUsers width="20" height="20" />
          </div>
          <div>
            <h1 className={styles.title}>Importação em Lote de Pacientes</h1>
            <p className={styles.subtitle}>Cole sua listagem do WhatsApp ou Excel (Nome e Telefone) para popular a base em segundos.</p>
          </div>
        </div>
      </header>

      <div className={styles.card}>
        {step === 1 && (
          <>
            <div className={styles.textareaWrapper}>
              <textarea 
                className={styles.textarea}
                placeholder="Cole aqui sua lista de contatos (uma por linha):&#10;Maria Silva, (11) 99999-1234&#10;Ana Costa, (21) 98765-4321&#10;Joana Martins"
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>
            
            {parsedData.length > 0 && (
              <div className={styles.previewSection}>
                <h3 className={styles.previewTitle}>Pré-visualização ({parsedData.length} pacientes identificados)</h3>
                <div className={styles.tableContainer}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>Nome</th>
                        <th>Telefone</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {parsedData.map((row, i) => (
                        <tr key={i}>
                          <td>{row.name}</td>
                          <td>{row.phone || "-"}</td>
                          <td>
                            {row.status === "OK" ? (
                              <span className={styles.statusOk}>
                                <IconCheck width="12" height="12" />
                                <span>Válido</span>
                              </span>
                            ) : (
                              <span className={styles.statusWarn}>
                                <IconAlertTriangle width="12" height="12" />
                                <span>Sem telefone</span>
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className={styles.actions}>
              <button 
                className={styles.btnConfirm} 
                disabled={parsedData.length === 0}
                onClick={handleGoToReview}
              >
                <span>Prosseguir para Revisão</span>
                <IconArrowRight width="15" height="15" />
              </button>
            </div>
          </>
        )}

        {step === 2 && (
          <div className={styles.resultBox}>
            <h2 className={styles.resultTitle}>Revisão de Importação</h2>
            <p className={styles.summaryText}>
              Você está prestes a cadastrar <strong>{parsedData.length}</strong> pacientes na clínica.
            </p>
            {parsedData.filter(r => r.status === "WARN").length > 0 && (
              <div className={styles.warningAlert}>
                <IconAlertTriangle width="16" height="16" />
                <span>{parsedData.filter(r => r.status === "WARN").length} pacientes não possuem telefone e não poderão receber lembretes automáticos de WhatsApp.</span>
              </div>
            )}
            <div className={styles.actionsRow}>
              <button 
                className={styles.btnBack} 
                onClick={() => setStep(1)}
              >
                ← Voltar e Editar
              </button>
              <button 
                className={styles.btnConfirm} 
                onClick={handleConfirm}
              >
                <span>Confirmar Importação</span>
                <IconCheck width="15" height="15" />
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className={styles.resultBox}>
            <div className={styles.loadingSpinner} />
            <h2 className={styles.resultTitle}>Processando cadastro...</h2>
            <p className={styles.summaryText}>Por favor, aguarde enquanto salvamos {parsedData.length} contatos.</p>
          </div>
        )}

        {step === 4 && result && (
          <div className={styles.resultBox}>
            <div className={styles.successIcon}>
              <IconSparkles width="24" height="24" />
            </div>
            <h2 className={styles.resultTitle}>Importação Concluída com Sucesso!</h2>
            
            <div className={styles.resultStats}>
              <div className={styles.statItem}>
                <span className={styles.statValue} style={{ color: "#059669" }}>{result.created_count}</span>
                <span className={styles.statLabel}>Cadastrados</span>
              </div>
              <div className={styles.statItem}>
                <span className={styles.statValue} style={{ color: "#d97706" }}>{result.skipped_count}</span>
                <span className={styles.statLabel}>Já existiam</span>
              </div>
              <div className={styles.statItem}>
                <span className={styles.statValue} style={{ color: "#dc2626" }}>{result.errors.length}</span>
                <span className={styles.statLabel}>Inconsistências</span>
              </div>
            </div>

            {result.errors.length > 0 && (
              <div className={styles.errorList}>
                <h4>Linhas não importadas:</h4>
                <ul>
                  {result.errors.map((err, i) => (
                    <li key={i}>Linha {err.line}: {err.reason}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className={styles.actionsRow} style={{ marginTop: "24px" }}>
              <button className={styles.btnConfirm} onClick={() => navigate("/pacientes")}>
                <span>Ver Lista de Pacientes</span>
                <IconArrowRight width="15" height="15" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
