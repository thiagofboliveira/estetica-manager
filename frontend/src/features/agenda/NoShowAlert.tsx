import { useUnconfirmedSessions, useConfirmSession } from "./hooks";
import { IconAlertTriangle, IconCheck, IconWhatsApp } from "@/ui/icons";
import styles from "./NoShowAlert.module.css";

export function NoShowAlert() {
  const { data: sessions, isLoading } = useUnconfirmedSessions();
  const confirmMutation = useConfirmSession();

  if (isLoading || !sessions || sessions.length === 0) {
    return null;
  }

  const allConfirmed = sessions.every(s => s.confirmed_at !== null);
  if (allConfirmed) {
    return null;
  }

  const pendingCount = sessions.filter(s => s.confirmed_at === null).length;

  const handleSendAll = () => {
    const unconfirmed = sessions.filter(
      s => s.confirmed_at === null && s.consent_whatsapp && s.patient_phone && s.whatsapp_link
    );
    unconfirmed.forEach((session, index) => {
      setTimeout(() => {
        if (session.whatsapp_link) {
          window.open(session.whatsapp_link, '_blank');
        }
      }, index * 500);
    });
  };

  const handleConfirm = (id: string) => {
    confirmMutation.mutate(id);
  };

  return (
    <div className={styles.container} role="alert">
      <header className={styles.header}>
        <div className={styles.alertBadge}>
          <IconAlertTriangle width="16" height="16" />
        </div>
        <div className={styles.headerContent}>
          <h3 className={styles.title}>
            {pendingCount} {pendingCount === 1 ? 'sessão de amanhã pendente de confirmação' : 'sessões de amanhã pendentes de confirmação'}
          </h3>
          <span className={styles.subtitle}>Envie lembrete prévio para evitar no-show e blindar o faturamento da clínica</span>
        </div>
      </header>

      <div className={styles.list}>
        {sessions.map(session => {
          const time = new Date(session.scheduled_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
          const isConfirmed = session.confirmed_at !== null;

          return (
            <div key={session.session_id} className={styles.item}>
              <div className={styles.itemInfo}>
                <span className={styles.modalityBadge}>
                  {session.modality === "IN_PERSON" ? "Presencial" : "Remoto"}
                </span>
                <span className={styles.patientName}>{session.patient_name}</span>
                <span className={styles.procedure}>• {session.procedure_name}</span>
                <span className={styles.time}>• {time}</span>
              </div>

              <div className={styles.actions}>
                {isConfirmed ? (
                  <div className={styles.confirmedBadge}>
                    <IconCheck width="13" height="13" />
                    <span>Confirmada às {new Date(session.confirmed_at!).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                ) : (
                  <>
                    <button 
                      className={styles.btnConfirm} 
                      onClick={() => handleConfirm(session.session_id)}
                      title="Marcar como confirmada"
                      disabled={confirmMutation.isPending}
                    >
                      <IconCheck width="14" height="14" />
                      <span>Confirmar</span>
                    </button>
                    {!session.patient_phone ? (
                      <span className={styles.noPhone}>Sem telefone</span>
                    ) : (
                      <a 
                        href={session.whatsapp_link ?? "#"} 
                        target="_blank" 
                        rel="noreferrer"
                        className={styles.btnWhatsapp}
                        aria-disabled={!session.consent_whatsapp || !session.whatsapp_link}
                        title={!session.consent_whatsapp ? "Paciente sem consentimento WhatsApp" : "Enviar lembrete via WhatsApp"}
                        onClick={e => {
                          if (!session.consent_whatsapp || !session.whatsapp_link) e.preventDefault();
                        }}
                      >
                        <IconWhatsApp width="15" height="15" />
                        <span>Lembrar no WhatsApp</span>
                      </a>
                    )}
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className={styles.footer}>
        <button className={styles.btnSendAll} onClick={handleSendAll} type="button">
          <IconWhatsApp width="16" height="16" />
          <span>Enviar lembrete para todas</span>
        </button>
      </div>
    </div>
  );
}
