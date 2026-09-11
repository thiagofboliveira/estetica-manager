import { useState, useMemo, useRef } from "react";
import { useBirthdays } from "./useBirthdays";
import type { PatientBirthday, CampaignTemplate } from "./campaignsApi";
import {
  useCampaignTemplates,
  useCreateCampaignTemplate,
  useUpdateCampaignTemplate,
  useDeleteCampaignTemplate,
} from "./useCampaignTemplates";
import { useRetentionCards, useReengagement } from "@/features/retention/hooks";
import type { PatientRetentionCard, ReengagementPatient } from "@/features/retention/api";
import { usePatients } from "@/features/patients/hooks";
import type { Patient } from "@/features/patients/api";
import { toast } from "@/ui/ToastContext";
import {
  IconWhatsApp,
  IconSparkles,
  IconTarget,
  IconInfo,
  IconPlus,
  IconEdit,
  IconTrash,
  IconCopy,
  IconX,
  IconCheck,
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

const CAMPAIGN_CATEGORIES = [
  { id: "all", label: "Todas as Campanhas" },
  { id: "promos", label: "📢 Promoções" },
  { id: "retencao", label: "🎯 Retenção" },
  { id: "reativacao", label: "✨ Reativação VIP" },
  { id: "aniversario", label: "🎂 Aniversários" },
  { id: "outros", label: "💡 Outros" },
];

const CATEGORY_LABELS: Record<string, string> = {
  promos: "Promoção",
  retencao: "Retenção",
  reativacao: "Reativação",
  aniversario: "Aniversário",
  outros: "Outros",
};

const FALLBACK_TEMPLATES: CampaignTemplate[] = [
  {
    id: "sys_botox_day",
    title: "💉 Botox Day Especial",
    category: "promos",
    description: "Campanha para preencher a agenda em um dia dedicado à aplicação de toxina botulínica.",
    message_text: "Oi {nome}! ✨ Passando com uma super novidade: nesta semana teremos nosso Botox Day exclusivo na clínica! Reservamos condições muito especiais para você garantir seu rejuvenescimento e prevenção de linhas de expressão com segurança médica. Temos poucas vagas para esse dia, posso reservar seu horário com a gente?",
    is_system: true,
    is_active: true,
  },
  {
    id: "sys_glow_station",
    title: "🌸 Protocolo Glow & Renovação Facial",
    category: "promos",
    description: "Oferta especial de limpeza de pele profunda associada a peeling iluminador.",
    message_text: "Olá {nome}! 🌸 Como está sua rotina de cuidados com a pele? Preparamos um protocolo exclusivo de Limpeza de Pele Profunda + Hidratação com LED neste mês para devolver o viço e o glow natural do seu rosto. Vamos marcar seu momento de autocuidado?",
    is_system: true,
    is_active: true,
  },
  {
    id: "sys_reactivation_vip",
    title: "✨ Sentimos sua Falta (Condição VIP)",
    category: "reativacao",
    description: "Mensagem calorosa para pacientes que não visitam a clínica há mais de 60 dias.",
    message_text: "Oi {nome}, tudo bem com você? Sentimos sua falta aqui na clínica! Pensando em você, separamos um mimo exclusivo de 15% de desconto no seu próximo procedimento neste mês. Que tal tirar uma horinha essa semana para relaxar e se cuidar?",
    is_system: true,
    is_active: true,
  },
  {
    id: "sys_friend_referral",
    title: "🎁 Traga uma Amiga & Ganhe Mimo",
    category: "promos",
    description: "Campanha de indicação onde a paciente e a amiga ganham benefícios.",
    message_text: "Oi {nome}! Sabia que se cuidar acompanhada é ainda melhor? Durante este mês, se você vier fazer um procedimento e trouxer uma amiga, ambas ganham uma Revitalização Facial de presente! Qual dia fica melhor para virem juntas?",
    is_system: true,
    is_active: true,
  },
  {
    id: "sys_birthday_gift",
    title: "🎂 Mimo de Aniversário Especial",
    category: "aniversario",
    description: "Parabéns especial para aniversariantes do mês com presente exclusivo.",
    message_text: "Oi {nome}! 🎉 Passando para desejar um Feliz Aniversário! Preparamos um presente especial para você: um mimo exclusivo no seu próximo procedimento este mês. Quando podemos agendar seu momento de cuidado?",
    is_system: true,
    is_active: true,
  },
  {
    id: "sys_maintenance_alert",
    title: "🎯 Lembrete de Manutenção Preventiva",
    category: "retencao",
    description: "Convite para retoque ou manutenção periódica de procedimentos faciais/corporais.",
    message_text: "Oi {nome}! ✨ Lembrei de você hoje. Já está na hora de fazermos a manutenção do seu procedimento para garantir o melhor resultado e longevidade. Como está sua agenda essa semana?",
    is_system: true,
    is_active: true,
  },
];

export function WhatsAppCampaignsPage() {
  const currentMonth = new Date().getMonth() + 1;
  const [selectedMonth, setSelectedMonth] = useState<number>(currentMonth);
  const [activeTab, setActiveTab] = useState<"birthdays" | "returns" | "reengagement" | "promos">("birthdays");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Filtros de Campanhas
  const [campaignCategory, setCampaignCategory] = useState<string>("all");

  // Modais de Campanhas
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState<boolean>(false);
  const [editingTemplate, setEditingTemplate] = useState<CampaignTemplate | null>(null);
  const [dispatchingTemplate, setDispatchingTemplate] = useState<CampaignTemplate | null>(null);

  // Queries
  const birthdaysQuery = useBirthdays(selectedMonth === 0 ? undefined : selectedMonth);
  const retentionQuery = useRetentionCards();
  const reengagementQuery = useReengagement(60, 1, 50);
  const templatesQuery = useCampaignTemplates(campaignCategory === "all" ? undefined : campaignCategory);

  const birthdays = birthdaysQuery.data ?? [];
  const retentionCards = retentionQuery.data ?? [];
  const reengagementData = reengagementQuery.data;
  const templates = templatesQuery.data ?? FALLBACK_TEMPLATES;

  // Mutations
  const createTemplateMutation = useCreateCampaignTemplate();
  const updateTemplateMutation = useUpdateCampaignTemplate();
  const deleteTemplateMutation = useDeleteCampaignTemplate();

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
    toast.success("Mensagem copiada para a área de transferência!");
    setTimeout(() => setCopiedId(null), 2500);
  };

  const handleOpenCreateModal = () => {
    setEditingTemplate(null);
    setIsTemplateModalOpen(true);
  };

  const handleOpenEditModal = (tpl: CampaignTemplate) => {
    setEditingTemplate(tpl);
    setIsTemplateModalOpen(true);
  };

  const handleDuplicateTemplate = (tpl: CampaignTemplate) => {
    setEditingTemplate({
      ...tpl,
      id: "",
      title: `${tpl.title} (Cópia)`,
      is_system: false,
    });
    setIsTemplateModalOpen(true);
  };

  const handleDeleteTemplate = async (tpl: CampaignTemplate) => {
    if (tpl.is_system) return;
    if (confirm(`Tem certeza que deseja excluir o modelo "${tpl.title}"?`)) {
      try {
        await deleteTemplateMutation.mutateAsync(tpl.id);
        toast.success("Modelo excluído com sucesso.");
      } catch {
        toast.error("Não foi possível excluir o modelo.");
      }
    }
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
          <span className={styles.metricLabel}>Modelos de Campanha</span>
          <span className={styles.metricValue}>{templates.length}</span>
          <span className={styles.metricNote}>Padrões e personalizados da clínica</span>
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
          📢 Campanhas & Promoções ({templates.length})
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
        <section style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          <div className={styles.campaignsTopBar}>
            <div className={styles.categoryFilterGroup}>
              {CAMPAIGN_CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  className={`${styles.filterChip} ${
                    campaignCategory === cat.id ? styles.filterChipActive : ""
                  }`}
                  onClick={() => setCampaignCategory(cat.id)}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            <button
              type="button"
              className={styles.newCampaignBtn}
              onClick={handleOpenCreateModal}
            >
              <IconPlus width="16" height="16" />
              <span>Novo Modelo de Campanha</span>
            </button>
          </div>

          <div style={{ background: "rgba(99, 102, 241, 0.08)", padding: "12px 16px", borderRadius: "10px", fontSize: "13px", color: "var(--text)" }}>
            <IconInfo width="14" height="14" style={{ verticalAlign: "-2px", marginRight: "6px", color: "var(--accent)" }} />
            Modelos de copywriting com gatilhos mentais para estética. Você pode personalizar o texto, criar novos modelos exclusivos para sua clínica ou disparar diretamente para qualquer paciente cadastrada no WhatsApp.
          </div>

          {templates.length === 0 ? (
            <div className={styles.emptyState}>
              <IconSparkles width="36" height="36" color="var(--accent)" />
              <h3 className={styles.emptyTitle}>Nenhum modelo encontrado nesta categoria</h3>
              <p className={styles.emptyDesc}>
                Crie um modelo customizado para suas campanhas e ofertas promocionais.
              </p>
              <button
                type="button"
                className={styles.newCampaignBtn}
                style={{ marginTop: "10px" }}
                onClick={handleOpenCreateModal}
              >
                <IconPlus width="16" height="16" />
                <span>Criar Primeiro Modelo</span>
              </button>
            </div>
          ) : (
            <div className={styles.cardsGrid}>
              {templates.map((tpl) => (
                <div key={tpl.id} className={styles.promoCard}>
                  <div className={styles.promoCardTop}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className={styles.promoBadgesRow}>
                        <span className={styles.tagBadge}>
                          {CATEGORY_LABELS[tpl.category] || tpl.category}
                        </span>
                        <span
                          className={`${styles.tagBadge} ${
                            tpl.is_system ? styles.badgeSystem : styles.badgeCustom
                          }`}
                        >
                          {tpl.is_system ? "Modelo Padrão" : "Personalizado"}
                        </span>
                      </div>
                      <h3 className={styles.promoTitle}>{tpl.title}</h3>
                    </div>

                    <div className={styles.promoActionsRow}>
                      <button
                        type="button"
                        className={styles.iconBtn}
                        title="Duplicar como novo modelo"
                        onClick={() => handleDuplicateTemplate(tpl)}
                      >
                        <IconCopy width="15" height="15" />
                      </button>
                      {!tpl.is_system && (
                        <>
                          <button
                            type="button"
                            className={styles.iconBtn}
                            title="Editar modelo"
                            onClick={() => handleOpenEditModal(tpl)}
                          >
                            <IconEdit width="15" height="15" />
                          </button>
                          <button
                            type="button"
                            className={`${styles.iconBtn} ${styles.iconBtnDanger}`}
                            title="Excluir modelo"
                            onClick={() => handleDeleteTemplate(tpl)}
                          >
                            <IconTrash width="15" height="15" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {tpl.description && (
                    <p className={styles.promoText}>{tpl.description}</p>
                  )}

                  <div className={styles.messagePreview} style={{ fontStyle: "italic" }}>
                    "{tpl.message_text}"
                  </div>

                  <div className={styles.promoCardFooter}>
                    <button
                      type="button"
                      className={styles.wppButton}
                      style={{
                        background: copiedId === tpl.id ? "#15803d" : undefined,
                        flex: 1,
                      }}
                      onClick={() => handleCopyText(tpl.id, tpl.message_text)}
                    >
                      {copiedId === tpl.id ? (
                        <>
                          <IconCheck width="15" height="15" />
                          <span>Copiado! ✨</span>
                        </>
                      ) : (
                        <>
                          <IconCopy width="15" height="15" />
                          <span>Copiar Mensagem</span>
                        </>
                      )}
                    </button>

                    <button
                      type="button"
                      className={styles.secondaryCardBtn}
                      title="Disparar esta campanha para uma paciente selecionada"
                      onClick={() => setDispatchingTemplate(tpl)}
                    >
                      <IconWhatsApp width="15" height="15" style={{ color: "#25d366" }} />
                      <span>Disparar para Paciente</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* MODAL 1: CRIAR / EDITAR MODELO DE CAMPANHA */}
      {isTemplateModalOpen && (
        <TemplateFormModal
          template={editingTemplate}
          isOpen={isTemplateModalOpen}
          onClose={() => {
            setIsTemplateModalOpen(false);
            setEditingTemplate(null);
          }}
          onSave={async (formData) => {
            try {
              if (editingTemplate && editingTemplate.id) {
                await updateTemplateMutation.mutateAsync({
                  id: editingTemplate.id,
                  data: formData,
                });
                toast.success("Modelo atualizado com sucesso!");
              } else {
                await createTemplateMutation.mutateAsync(formData);
                toast.success("Modelo de campanha salvo com sucesso!");
              }
              setIsTemplateModalOpen(false);
              setEditingTemplate(null);
            } catch {
              toast.error("Erro ao salvar o modelo de campanha.");
            }
          }}
          isSaving={createTemplateMutation.isPending || updateTemplateMutation.isPending}
        />
      )}

      {/* MODAL 2: DISPARAR CAMPANHA PARA PACIENTE */}
      {dispatchingTemplate && (
        <DispatchCampaignModal
          template={dispatchingTemplate}
          onClose={() => setDispatchingTemplate(null)}
        />
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

function TemplateFormModal({
  template,
  isOpen,
  onClose,
  onSave,
  isSaving,
}: {
  template: CampaignTemplate | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: { title: string; category: string; description?: string; message_text: string }) => Promise<void>;
  isSaving: boolean;
}) {
  const [title, setTitle] = useState(template?.title || "");
  const [category, setCategory] = useState(template?.category || "promos");
  const [description, setDescription] = useState(template?.description || "");
  const [messageText, setMessageText] = useState(template?.message_text || "");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  if (!isOpen) return null;

  const insertVariable = (tag: string) => {
    if (!textareaRef.current) {
      setMessageText((prev) => prev + " " + tag);
      return;
    }
    const start = textareaRef.current.selectionStart;
    const end = textareaRef.current.selectionEnd;
    const newText = messageText.substring(0, start) + tag + messageText.substring(end);
    setMessageText(newText);
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.focus();
        textareaRef.current.setSelectionRange(start + tag.length, start + tag.length);
      }
    }, 0);
  };

  const previewSimulated = messageText
    .replace(/{nome}/gi, "Mariana")
    .replace(/{clinica}/gi, "nossa clínica")
    .replace(/{pontos}/gi, "150")
    .replace(/{nivel_vip}/gi, "💎 Diamante VIP");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !messageText.trim()) {
      toast.error("Por favor, preencha o título e o texto da mensagem.");
      return;
    }
    onSave({
      title: title.trim(),
      category,
      description: description.trim() || undefined,
      message_text: messageText.trim(),
    });
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>
            {template?.id ? "Editar Modelo de Campanha" : "Criar Novo Modelo de Campanha"}
          </h2>
          <button type="button" className={styles.iconBtn} onClick={onClose}>
            <IconX width="18" height="18" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.formContainer}>
          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Título do Modelo *</label>
            <input
              type="text"
              className={styles.formInput}
              placeholder="Ex: 💎 Exclusivo Clube VIP Diamante"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Categoria Estratégica *</label>
            <select
              className={styles.formSelect}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="promos">🔥 Promoção / Lançamento</option>
              <option value="retencao">🎯 Retenção / Manutenção</option>
              <option value="reengajamento">❄️ Reengajamento (Clientes Sumidas)</option>
              <option value="aniversario">🎂 Aniversariantes</option>
              <option value="indica">🎁 Indicação ("Traga uma Amiga")</option>
              <option value="fidelidade">🏆 Clube VIP & Fidelidade</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Descrição / Objetivo (Opcional)</label>
            <input
              type="text"
              className={styles.formInput}
              placeholder="Ex: Disparo exclusivo para clientes VIP com saldo de pontos alto"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className={styles.formGroup}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "6px" }}>
              <label className={styles.formLabel}>Texto da Mensagem no WhatsApp *</label>
              <div className={styles.variableChips}>
                <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Inserir:</span>
                <button
                  type="button"
                  className={styles.varChip}
                  onClick={() => insertVariable("{nome}")}
                  title="Será substituído pelo primeiro nome da paciente"
                >
                  + {"{nome}"}
                </button>
                <button
                  type="button"
                  className={styles.varChip}
                  onClick={() => insertVariable("{clinica}")}
                  title="Será substituído pelo nome da clínica"
                >
                  + {"{clinica}"}
                </button>
                <button
                  type="button"
                  className={styles.varChip}
                  onClick={() => insertVariable("{pontos}")}
                  title="Será substituído pelo saldo de pontos do Clube VIP da paciente"
                >
                  + {"{pontos}"}
                </button>
                <button
                  type="button"
                  className={styles.varChip}
                  onClick={() => insertVariable("{nivel_vip}")}
                  title="Será substituído pela Categoria VIP (Bronze, Prata, Ouro, Diamante)"
                >
                  + {"{nivel_vip}"}
                </button>
              </div>
            </div>

            <textarea
              ref={textareaRef}
              className={styles.formTextarea}
              placeholder="Oi {nome}! Preparamos uma condição especial na clínica este mês..."
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              required
            />
          </div>

          {/* Live Preview Simulated */}
          <div className={styles.livePreview}>
            <span className={styles.livePreviewTitle}>Prévia Realista no WhatsApp:</span>
            <div className={styles.livePreviewBubble}>
              {previewSimulated || "O texto da mensagem aparecerá aqui conforme você digita..."}
            </div>
          </div>

          <div className={styles.modalFooter}>
            <button
              type="button"
              className={styles.secondaryCardBtn}
              onClick={onClose}
              disabled={isSaving}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={styles.newCampaignBtn}
              disabled={isSaving}
            >
              <IconCheck width="16" height="16" />
              <span>{isSaving ? "Salvando..." : "Salvar Modelo"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DispatchCampaignModal({
  template,
  onClose,
}: {
  template: CampaignTemplate;
  onClose: () => void;
}) {
  const [search, setSearch] = useState("");
  const [selectedVipTier, setSelectedVipTier] = useState<string>("ALL");
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const patientsQuery = usePatients(search);
  const rawPatients = patientsQuery.data ?? [];

  const patients = useMemo(() => {
    if (selectedVipTier === "ALL") return rawPatients;
    if (selectedVipTier === "WITH_POINTS") {
      return rawPatients.filter((p) => (p.loyalty_points || 0) > 0);
    }
    return rawPatients.filter((p) => (p.vip_tier || "BRONZE") === selectedVipTier);
  }, [rawPatients, selectedVipTier]);

  const firstName = selectedPatient
    ? selectedPatient.name.trim().split(" ")[0]
    : "Mariana";

  const vipTierName =
    selectedPatient?.vip_tier === "DIAMOND"
      ? "Diamante VIP"
      : selectedPatient?.vip_tier === "GOLD"
      ? "Ouro"
      : selectedPatient?.vip_tier === "SILVER"
      ? "Prata"
      : "Bronze";

  const personalizedMessage = template.message_text
    .replace(/{nome}/gi, firstName)
    .replace(/{clinica}/gi, "nossa clínica")
    .replace(/{pontos}/gi, String(selectedPatient?.loyalty_points || 0))
    .replace(/{nivel_vip}/gi, vipTierName);

  const cleanPhone = selectedPatient?.phone
    ? selectedPatient.phone.replace(/\D/g, "")
    : null;

  const whatsappUrl = cleanPhone
    ? `https://wa.me/55${cleanPhone}?text=${encodeURIComponent(personalizedMessage)}`
    : null;

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div>
            <h2 className={styles.modalTitle}>Disparar Campanha para Paciente</h2>
            <span style={{ fontSize: "12.5px", color: "var(--text-muted)" }}>
              Modelo: {template.title}
            </span>
          </div>
          <button type="button" className={styles.iconBtn} onClick={onClose}>
            <IconX width="18" height="18" />
          </button>
        </div>

        {/* Filtro de Categoria VIP */}
        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "4px" }}>
          <button
            type="button"
            className={`${styles.categoryTab} ${selectedVipTier === "ALL" ? styles.categoryTabActive : ""}`}
            onClick={() => setSelectedVipTier("ALL")}
            style={{ fontSize: "11px", padding: "4px 8px" }}
          >
            Todas ({rawPatients.length})
          </button>
          <button
            type="button"
            className={`${styles.categoryTab} ${selectedVipTier === "DIAMOND" ? styles.categoryTabActive : ""}`}
            onClick={() => setSelectedVipTier("DIAMOND")}
            style={{ fontSize: "11px", padding: "4px 8px" }}
          >
            💎 Diamante
          </button>
          <button
            type="button"
            className={`${styles.categoryTab} ${selectedVipTier === "GOLD" ? styles.categoryTabActive : ""}`}
            onClick={() => setSelectedVipTier("GOLD")}
            style={{ fontSize: "11px", padding: "4px 8px" }}
          >
            🥇 Ouro
          </button>
          <button
            type="button"
            className={`${styles.categoryTab} ${selectedVipTier === "SILVER" ? styles.categoryTabActive : ""}`}
            onClick={() => setSelectedVipTier("SILVER")}
            style={{ fontSize: "11px", padding: "4px 8px" }}
          >
            🥈 Prata
          </button>
          <button
            type="button"
            className={`${styles.categoryTab} ${selectedVipTier === "WITH_POINTS" ? styles.categoryTabActive : ""}`}
            onClick={() => setSelectedVipTier("WITH_POINTS")}
            style={{ fontSize: "11px", padding: "4px 8px" }}
          >
            ⭐ Com Pontos &gt; 0
          </button>
        </div>

        <div className={styles.formGroup}>
          <label className={styles.formLabel}>Buscar Paciente:</label>
          <input
            type="text"
            className={styles.formInput}
            placeholder="Digite o nome ou telefone da paciente..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className={styles.patientSelectList}>
          {patients.length === 0 ? (
            <div style={{ padding: "16px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
              Nenhuma paciente encontrada com o filtro selecionado.
            </div>
          ) : (
            patients.map((p) => (
              <div
                key={p.id}
                className={`${styles.patientSelectItem} ${
                  selectedPatient?.id === p.id ? styles.patientSelectItemActive : ""
                }`}
                onClick={() => setSelectedPatient(p)}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: "13.5px", color: "var(--text-h)", display: "flex", alignItems: "center", gap: "8px" }}>
                    <span>{p.name}</span>
                    {p.vip_tier && (
                      <span
                        style={{
                          fontSize: "10.5px",
                          fontWeight: 700,
                          padding: "1px 6px",
                          borderRadius: "10px",
                          background:
                            p.vip_tier === "DIAMOND"
                              ? "#e0f2fe"
                              : p.vip_tier === "GOLD"
                              ? "#fef9c3"
                              : p.vip_tier === "SILVER"
                              ? "#f1f5f9"
                              : "#fef3c7",
                          color:
                            p.vip_tier === "DIAMOND"
                              ? "#0369a1"
                              : p.vip_tier === "GOLD"
                              ? "#854d0e"
                              : p.vip_tier === "SILVER"
                              ? "#334155"
                              : "#92400e",
                        }}
                      >
                        {p.vip_tier === "DIAMOND"
                          ? "💎 Diamante"
                          : p.vip_tier === "GOLD"
                          ? "🥇 Ouro"
                          : p.vip_tier === "SILVER"
                          ? "🥈 Prata"
                          : "🥉 Bronze"}
                      </span>
                    )}
                    {p.loyalty_points ? (
                      <span style={{ fontSize: "11px", color: "#16a34a", fontWeight: 700 }}>
                        {p.loyalty_points} pts
                      </span>
                    ) : null}
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                    {p.phone || "Sem telefone cadastrado"}
                  </div>
                </div>
                {selectedPatient?.id === p.id && (
                  <span style={{ color: "var(--accent)", fontSize: "12px", fontWeight: 700 }}>
                    ✓ Selecionada
                  </span>
                )}
              </div>
            ))
          )}
        </div>

        <div className={styles.livePreview}>
          <span className={styles.livePreviewTitle}>
            Mensagem Personalizada {selectedPatient ? `para ${selectedPatient.name}` : ""}:
          </span>
          <div className={styles.livePreviewBubble}>
            {personalizedMessage}
          </div>
        </div>

        <div className={styles.modalFooter}>
          <button type="button" className={styles.secondaryCardBtn} onClick={onClose}>
            Fechar
          </button>
          {whatsappUrl ? (
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noreferrer"
              className={styles.wppButton}
              style={{ width: "auto" }}
            >
              <IconWhatsApp width="16" height="16" />
              <span>Abrir WhatsApp com Mensagem</span>
            </a>
          ) : (
            <button
              type="button"
              disabled
              className={styles.wppButtonDisabled}
              style={{ width: "auto" }}
            >
              <IconWhatsApp width="16" height="16" />
              <span>
                {selectedPatient
                  ? "Paciente sem telefone válido"
                  : "Selecione uma paciente"}
              </span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
