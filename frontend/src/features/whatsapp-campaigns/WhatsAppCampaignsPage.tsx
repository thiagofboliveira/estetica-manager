import { useState, useMemo } from "react";
import { useBirthdays } from "./useBirthdays";
import type { PatientBirthday } from "./campaignsApi";
import { useRetentionCards, useReengagement } from "@/features/retention/hooks";
import type { PatientRetentionCard, ReengagementPatient } from "@/features/retention/api";
import {
  IconWhatsApp,
  IconSparkles,
  IconTarget,
  IconInfo,
} from "@/ui/icons";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { MESSAGES, fillTemplate } from "@/lib/constants/messages";
import styles from "./WhatsAppCampaignsPage.module.css";

const MONTH_NAMES = [
  "Todos os Meses",
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

const PROMO_TEMPLATES = [
  {
    id: "botox_day",
    title: "💉 Botox Day Especial",
    desc: "Campanha para preencher a agenda em um dia dedicado à aplicação de toxina botulínica.",
    text: "Oi {nome}! ✨ Passando com uma super novidade: nesta semana teremos nosso Botox Day exclusivo na clínica! Reservamos condições muito especiais para você garantir seu rejuvenescimento e prevenção de linhas de expressão com segurança médica. Temos poucas vagas para esse dia, posso reservar seu horário com a gente?",
  },
  {
    id: "glow_station",
    title: "🌸 Protocolo Glow & Renovação Facial",
    desc: "Oferta especial de limpeza de pele profunda associada a peeling iluminador.",
    text: "Olá {nome}! 🌸 Como está sua rotina de cuidados com a pele? Preparamos um protocolo exclusivo de Limpeza de Pele Profunda + Hidratação com LED neste mês para devolver o viço e o glow natural do seu rosto. Vamos marcar seu momento de autocuidado?",
  },
  {
    id: "reactivation_vip",
    title: "✨ Sentimos sua Falta (Condição VIP)",
    desc: "Mensagem calorosa para pacientes que não visitam a clínica há mais de 60 dias.",
    text: "Oi {nome}, tudo bem com você? Sentimos sua falta aqui na clínica! Pensando em você, separamos um mimo exclusivo de 15% de desconto no seu próximo procedimento neste mês. Que tal tirar uma horinha essa semana para relaxar e se cuidar?",
  },
  {
    id: "friend_referral",
    title: "🎁 Traga uma Amiga & Ganhe Mimo",
    desc: "Campanha de indicação onde a paciente e a amiga ganham benefícios.",
    text: "Oi {nome}! Sabia que se cuidar acompanhada é ainda melhor? Durante este mês, se você vier fazer um procedimento e trouxer uma amiga, ambas ganham uma Revitalização Facial de presente! Qual dia fica melhor para virem juntas?",
  },
];

export function WhatsAppCampaignsPage() {
  const currentMonth = new Date().getMonth() + 1;
  const [selectedMonth, setSelectedMonth] = useState<number>(currentMonth);
  const [activeTab, setActiveTab] = useState<"birthdays" | "returns" | "reengagement" | "promos">("birthdays");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Queries
  const birthdaysQuery = useBirthdays(selectedMonth === 0 ? undefined : selectedMonth);
  const retentionQuery = useRetentionCards();
  const reengagementQuery = useReengagement(60, 1, 50);

  const birthdays = birthdaysQuery.data ?? [];
  const retentionCards = retentionQuery.data ?? [];
  const reengagementData = reengagementQuery.data;

  // Cálculos de KPIs
  const totalPotentialReturns = useMemo(() => {
    return retentionCards.reduce(
      (sum, c) => sum + Number(c.total_potential_value || 0),
      0
    );
  }, [retentionCards]);

  const totalColdPatients = useMemo(() => {
    if (!reengagementData) return 0;
    return (
      (reengagementData.inactive_total_count || 0) +
      (reengagementData.never_treated_total_count || 0)
    );
  }, [reengagementData]);

  const handleCopyText = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  return (
    <div className={styles.page}>
      {/* Header Superior */}
      <header className={styles.header}>
        <div className={styles.titleArea}>
          <h1 className={styles.title}>Central de Disparos WhatsApp</h1>
          <p className={styles.subtitle}>
            Aumente o faturamento e a fidelização com mensagens personalizadas em 1 clique para aniversariantes, retornos e reativação.
          </p>
        </div>
      </header>

      {/* Top Metrics Grid */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <span className={styles.metricLabel}>Aniversariantes do Mês</span>
          <span className={styles.metricValue} style={{ color: "var(--accent)" }}>
            {birthdays.length}
          </span>
          <span className={styles.metricNote}>
            {selectedMonth === 0 ? "Em todo o ano" : `No mês de ${MONTH_NAMES[selectedMonth]}`}
          </span>
        </div>

        <div className={`${styles.metricCard} ${retentionCards.length > 0 ? styles.metricCardAlert : ""}`}>
          <span className={styles.metricLabel}>Retornos a Chamar</span>
          <span className={styles.metricValue} style={{ color: retentionCards.length > 0 ? "#b45309" : undefined }}>
            {retentionCards.length}
          </span>
          <span className={styles.metricNote}>
            {formatBRL(money(totalPotentialReturns.toFixed(2)))} em receita prevista
          </span>
        </div>

        <div className={styles.metricCard}>
          <span className={styles.metricLabel}>Clientes Inativas</span>
          <span className={styles.metricValue}>{totalColdPatients}</span>
          <span className={styles.metricNote}>Sem procedimentos há mais de 60 dias</span>
        </div>

        <div className={styles.metricCard}>
          <span className={styles.metricLabel}>Campanhas Prontas</span>
          <span className={styles.metricValue}>{PROMO_TEMPLATES.length}</span>
          <span className={styles.metricNote}>Modelos de copywriting validados</span>
        </div>
      </div>

      {/* Navegação de Abas */}
      <div className={styles.tabGroup}>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === "birthdays" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("birthdays")}
        >
          🎂 Aniversariantes ({birthdays.length})
        </button>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === "returns" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("returns")}
        >
          🎯 Retornos Pendentes ({retentionCards.length})
        </button>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === "reengagement" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("reengagement")}
        >
          💤 Clientes Inativas ({totalColdPatients})
        </button>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === "promos" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("promos")}
        >
          📢 Campanhas & Promoções
        </button>
      </div>

      {/* ABA 1: ANIVERSARIANTES */}
      {activeTab === "birthdays" && (
        <section style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div className={styles.toolbar}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text)" }}>Filtrar por Mês:</span>
              <select
                className={styles.selectInput}
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(Number(e.target.value))}
              >
                {MONTH_NAMES.map((name, idx) => (
                  <option key={idx} value={idx}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
            <span style={{ fontSize: "12.5px", color: "var(--text-muted)" }}>
              {birthdays.length} {birthdays.length === 1 ? "paciente encontrada" : "pacientes encontradas"}
            </span>
          </div>

          {birthdays.length === 0 ? (
            <div className={styles.emptyState}>
              <IconSparkles width="36" height="36" color="var(--accent)" />
              <h3 className={styles.emptyTitle}>Nenhum aniversariante neste mês</h3>
              <p className={styles.emptyDesc}>
                Conforme você cadastrar as datas de nascimento no prontuário das clientes, elas aparecerão aqui automaticamente para envio de parabéns e mimos.
              </p>
            </div>
          ) : (
            <div className={styles.cardsGrid}>
              {birthdays.map((item) => (
                <BirthdayCard key={item.patient_id} item={item} />
              ))}
            </div>
          )}
        </section>
      )}

      {/* ABA 2: RETORNOS PENDENTES */}
      {activeTab === "returns" && (
        <section style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {retentionCards.length === 0 ? (
            <div className={styles.emptyState}>
              <IconTarget width="36" height="36" color="var(--accent)" />
              <h3 className={styles.emptyTitle}>Todos os retornos em dia! 🎉</h3>
              <p className={styles.emptyDesc}>
                Não há pacientes na janela de retoque ou manutenção pendentes no momento.
              </p>
            </div>
          ) : (
            <div className={styles.cardsGrid}>
              {retentionCards.map((card) => (
                <ReturnOpportunityCard key={card.patient_id} card={card} />
              ))}
            </div>
          )}
        </section>
      )}

      {/* ABA 3: REATIVAÇÃO DE INATIVAS */}
      {activeTab === "reengagement" && (
        <section style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {totalColdPatients === 0 ? (
            <div className={styles.emptyState}>
              <h3 className={styles.emptyTitle}>Nenhuma cliente inativa no momento</h3>
              <p className={styles.emptyDesc}>
                Sua base está engajada e ativa com atendimentos recentes!
              </p>
            </div>
          ) : (
            <div className={styles.cardsGrid}>
              {reengagementData?.inactive.map((patient) => (
                <InactivePatientCard key={patient.patient_id} patient={patient} />
              ))}
              {reengagementData?.never_treated.map((patient) => (
                <InactivePatientCard key={patient.patient_id} patient={patient} isNeverTreated />
              ))}
            </div>
          )}
        </section>
      )}

      {/* ABA 4: CAMPANHAS & PROMOÇÕES */}
      {activeTab === "promos" && (
        <section style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ background: "rgba(99, 102, 241, 0.08)", padding: "12px 16px", borderRadius: "10px", fontSize: "13px", color: "var(--text)" }}>
            <IconInfo width="14" height="14" style={{ verticalAlign: "-2px", marginRight: "6px", color: "var(--accent)" }} />
            Estes são modelos de copywriting de alta conversão para estética. Copie o texto e dispare no WhatsApp ou publique nos Stories/Status para atrair novos agendamentos!
          </div>

          <div className={styles.cardsGrid}>
            {PROMO_TEMPLATES.map((promo) => (
              <div key={promo.id} className={styles.promoCard}>
                <div>
                  <h3 className={styles.promoTitle}>{promo.title}</h3>
                  <p className={styles.promoText}>{promo.desc}</p>
                </div>

                <div className={styles.messagePreview} style={{ fontStyle: "italic" }}>
                  "{promo.text}"
                </div>

                <button
                  type="button"
                  className={styles.wppButton}
                  style={{ background: copiedId === promo.id ? "#15803d" : undefined }}
                  onClick={() => handleCopyText(promo.id, promo.text)}
                >
                  <IconSparkles width="15" height="15" />
                  <span>{copiedId === promo.id ? "Copiado com Sucesso! ✨" : "Copiar Texto da Campanha"}</span>
                </button>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function BirthdayCard({ item }: { item: PatientBirthday }) {
  return (
    <div className={styles.campaignCard}>
      <div className={styles.cardHeader}>
        <div className={styles.cardPatientInfo}>
          <h3 className={styles.patientName}>{item.patient_name}</h3>
          <span className={styles.patientMeta}>
            🎂 {item.formatted_date}
            {item.patient_phone ? ` • ${item.patient_phone}` : " • Sem telefone"}
          </span>
        </div>

        <span className={`${styles.badge} ${item.is_today ? styles.badgeToday : styles.badgeUpcoming}`}>
          {item.is_today ? "🎉 É HOJE!" : `Em ${item.days_until} dia(s)`}
        </span>
      </div>

      <div className={styles.messagePreview}>
        <span className={styles.messageTag}>Mensagem de Aniversário com Mimo:</span>
        "Oi {item.patient_name.split(" ")[0]}! 🎉 Passando para desejar um Feliz Aniversário! Preparamos um presente especial para você: um mimo exclusivo no seu próximo procedimento este mês..."
      </div>

      {item.whatsapp_url ? (
        <a
          href={item.whatsapp_url}
          target="_blank"
          rel="noreferrer"
          className={styles.wppButton}
        >
          <IconWhatsApp width="16" height="16" />
          <span>Enviar Parabéns no WhatsApp</span>
        </a>
      ) : (
        <button
          type="button"
          disabled
          className={styles.wppButtonDisabled}
          title="Cadastre o telefone no prontuário para habilitar o WhatsApp"
        >
          <IconWhatsApp width="16" height="16" />
          <span>Telefone não cadastrado</span>
        </button>
      )}
    </div>
  );
}

function ReturnOpportunityCard({ card }: { card: PatientRetentionCard }) {
  const cleanPhone = card.patient_phone ? card.patient_phone.replace(/\D/g, "") : null;
  const firstName = card.patient_name.split(" ")[0];
  const procName = card.primary_opportunity?.procedure_name || "seu procedimento";
  const defaultMessage = `Oi ${firstName}! ✨ Lembrei de você hoje. Já está na hora de fazermos a manutenção do seu ${procName} para garantir o melhor resultado duradouro. Como está sua agenda essa semana?`;

  const whatsappUrl = cleanPhone
    ? `https://wa.me/55${cleanPhone}?text=${encodeURIComponent(defaultMessage)}`
    : null;

  return (
    <div className={styles.campaignCard}>
      <div className={styles.cardHeader}>
        <div className={styles.cardPatientInfo}>
          <h3 className={styles.patientName}>{card.patient_name}</h3>
          <span className={styles.patientMeta}>
            {card.primary_opportunity?.procedure_name} • Previsão de retorno
          </span>
        </div>

        <span className={`${styles.badge} ${styles.badgeReturn}`}>
          {card.primary_opportunity?.timing === "OVERDUE"
            ? "Vencido"
            : card.primary_opportunity?.timing === "DUE"
            ? "Na Janela Ideal"
            : "Em breve"}
        </span>
      </div>

      <div className={styles.messagePreview}>
        <span className={styles.messageTag}>Mensagem de Retoque / Manutenção:</span>
        "{defaultMessage}"
      </div>

      {whatsappUrl ? (
        <a
          href={whatsappUrl}
          target="_blank"
          rel="noreferrer"
          className={styles.wppButton}
        >
          <IconWhatsApp width="16" height="16" />
          <span>Chamar para Retorno</span>
        </a>
      ) : (
        <button type="button" disabled className={styles.wppButtonDisabled}>
          <IconWhatsApp width="16" height="16" />
          <span>Sem telefone</span>
        </button>
      )}
    </div>
  );
}

function InactivePatientCard({
  patient,
  isNeverTreated,
}: {
  patient: ReengagementPatient;
  isNeverTreated?: boolean;
}) {
  const cleanPhone = patient.patient_phone ? patient.patient_phone.replace(/\D/g, "") : null;
  const message = fillTemplate(MESSAGES.RETENTION.WHATSAPP_REENGAGEMENT, {
    patient_name: patient.patient_name,
  });

  const whatsappUrl = cleanPhone
    ? `https://wa.me/55${cleanPhone}?text=${encodeURIComponent(message)}`
    : null;

  return (
    <div className={styles.campaignCard}>
      <div className={styles.cardHeader}>
        <div className={styles.cardPatientInfo}>
          <h3 className={styles.patientName}>{patient.patient_name}</h3>
          <span className={styles.patientMeta}>
            {isNeverTreated ? "Nunca realizou procedimento" : "Parada há mais de 60 dias"}
          </span>
        </div>

        <span className={`${styles.badge} ${styles.badgeInactive}`}>
          {isNeverTreated ? "Novo Contato" : "Inativa"}
        </span>
      </div>

      <div className={styles.messagePreview}>
        <span className={styles.messageTag}>Mensagem de Reativação:</span>
        "{message}"
      </div>

      {whatsappUrl ? (
        <a
          href={whatsappUrl}
          target="_blank"
          rel="noreferrer"
          className={styles.wppButton}
        >
          <IconWhatsApp width="16" height="16" />
          <span>Reativar no WhatsApp</span>
        </a>
      ) : (
        <button type="button" disabled className={styles.wppButtonDisabled}>
          <IconWhatsApp width="16" height="16" />
          <span>Sem telefone</span>
        </button>
      )}
    </div>
  );
}
