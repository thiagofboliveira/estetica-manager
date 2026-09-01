"""ExportService — Gera arquivos CSV formatados para Excel e LGPD (EPIC-S3-02).

Formatado para padrão brasileiro:
- Delimitador: ';'
- Encoding: UTF-8 com BOM (\\ufeff) para correta abertura no Excel sem problemas de acentuação
- Formato numérico e monetário: 'R$ 1.500,00' ou '1500,00'
"""

import csv
import io

from app.repositories.patient import PatientRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.sale import SaleRepository
from app.repositories.session import SessionRepository


class ExportService:
    def __init__(
        self,
        patient_repo: PatientRepository,
        sale_repo: SaleRepository,
        session_repo: SessionRepository,
        procedure_repo: ProcedureRepository,
    ) -> None:
        self._patient_repo = patient_repo
        self._sale_repo = sale_repo
        self._session_repo = session_repo
        self._procedure_repo = procedure_repo

    def export_patients_csv(self) -> str:
        output = io.StringIO()
        output.write("\ufeff")  # UTF-8 BOM
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

        writer.writerow([
            "ID",
            "Nome",
            "Telefone",
            "Consentimento WhatsApp",
            "Data de Cadastro",
        ])

        patients = self._patient_repo.list(limit=10000)
        for p in patients:
            writer.writerow([
                str(p.id),
                p.name,
                p.phone or "",
                "Sim" if p.consent_whatsapp else "Não",
                p.created_at.strftime("%d/%m/%Y %H:%M") if p.created_at else "",
            ])

        return output.getvalue()

    def export_sales_csv(self) -> str:
        output = io.StringIO()
        output.write("\ufeff")
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

        writer.writerow([
            "ID Venda",
            "Data da Venda",
            "Paciente",
            "Tipo",
            "Forma de Pagamento",
            "Parcelas",
            "Valor Bruto (R$)",
            "Desconto (R$)",
            "Taxa Maquininha (R$)",
            "Split Clínica (R$)",
            "Custos (R$)",
            "Lucro Líquido (R$)",
            "Margem (%)",
            "Status",
        ])

        patients_map = {p.id: p.name for p in self._patient_repo.list(limit=10000)}
        sales = self._sale_repo.list(limit=10000)
        for s in sales:
            pat_name = patients_map.get(s.patient_id, "Não informado")
            margin_str = f"{(s.margin * 100):.1f}%" if s.margin is not None else "0.0%"
            writer.writerow([
                str(s.id),
                s.sold_at.strftime("%d/%m/%Y"),
                pat_name,
                s.type.value if hasattr(s.type, "value") else str(s.type),
                s.payment_method.value if hasattr(s.payment_method, "value") else str(s.payment_method),
                str(s.installments),
                f"{s.gross_amount:.2f}".replace(".", ","),
                f"{s.discount_amount:.2f}".replace(".", ","),
                f"{s.fee_amount_applied:.2f}".replace(".", ","),
                f"{s.split_amount_applied:.2f}".replace(".", ","),
                f"{s.cost_realized:.2f}".replace(".", ","),
                f"{s.net_profit:.2f}".replace(".", ","),
                margin_str,
                s.status.value if hasattr(s.status, "value") else str(s.status),
            ])

        return output.getvalue()

    def export_sessions_csv(self) -> str:
        output = io.StringIO()
        output.write("\ufeff")
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

        writer.writerow([
            "ID Sessão",
            "Data Agendada",
            "Paciente",
            "Procedimento",
            "Modalidade",
            "Status",
            "Confirmada Em",
            "Custo Realizado (R$)",
        ])

        sessions = self._session_repo.list(limit=10000)
        for sess in sessions:
            pat_name = (
                sess.sale_item.sale.patient.name
                if sess.sale_item and hasattr(sess.sale_item, "sale") and sess.sale_item.sale and hasattr(sess.sale_item.sale, "patient") and sess.sale_item.sale.patient
                else ""
            )
            proc_name = (
                sess.sale_item.procedure.name
                if sess.sale_item and hasattr(sess.sale_item, "procedure") and sess.sale_item.procedure
                else ""
            )
            sched_str = sess.scheduled_at.strftime("%d/%m/%Y %H:%M") if sess.scheduled_at else ""
            conf_str = sess.confirmed_at.strftime("%d/%m/%Y %H:%M") if sess.confirmed_at else "Não confirmada"
            cost_str = f"{sess.cost_realized:.2f}".replace(".", ",") if sess.cost_realized is not None else "0,00"

            writer.writerow([
                str(sess.id),
                sched_str,
                pat_name,
                proc_name,
                sess.modality.value if hasattr(sess.modality, "value") else str(sess.modality),
                sess.status.value if hasattr(sess.status, "value") else str(sess.status),
                conf_str,
                cost_str,
            ])

        return output.getvalue()
