"""Serviço de Anamnese Digital (AN-04)."""

from datetime import UTC, datetime
from uuid import UUID

from app.models.anamnesis import (
    AnamnesisQuestion,
    AnamnesisSubmission,
    AnamnesisTemplate,
    QuestionFieldType,
)
from app.repositories.anamnesis import (
    AnamnesisQuestionRepository,
    AnamnesisSubmissionRepository,
    AnamnesisTemplateRepository,
)
from app.schemas.anamnesis import (
    AnamnesisQuestionCreate,
    AnamnesisQuestionUpdate,
    AnamnesisReorderQuestionsInput,
    AnamnesisTemplateUpdate,
    PublicAnamnesisSubmitInput,
)


class AnamnesisNotFoundError(Exception):
    pass


class AnamnesisQuestionNotFoundError(Exception):
    pass


class AnamnesisService:
    def __init__(
        self,
        template_repo: AnamnesisTemplateRepository,
        question_repo: AnamnesisQuestionRepository,
        submission_repo: AnamnesisSubmissionRepository,
    ) -> None:
        self.template_repo = template_repo
        self.question_repo = question_repo
        self.submission_repo = submission_repo

    def get_or_create_default_template(self) -> AnamnesisTemplate:
        template = self.template_repo.get_default_with_questions()
        if template is not None:
            return template

        # Cria template padrão caso não exista
        template = AnamnesisTemplate(
            title="Ficha de Anamnese Facial e Corporal",
            description="Questionário prévio de saúde e histórico estético para segurança do procedimento.",
            is_default=True,
            is_active=True,
            auto_request_on_booking=True,
        )
        self.template_repo.add(template)
        self.template_repo._session.flush()

        default_questions = [
            (
                "Está gestante ou em período de amamentação?",
                None,
                QuestionFieldType.YES_NO.value,
                None,
                True,
                True,
                "yes",
                1,
            ),
            (
                "Possui alguma alergia conhecida (medicamentos, cosméticos, látex)?",
                "Se sim, especifique no atendimento",
                QuestionFieldType.YES_NO.value,
                None,
                True,
                True,
                "yes",
                2,
            ),
            (
                "Faz uso de medicamentos contínuos (ex: Roacutan, anticoagulantes)?",
                "Importante para avaliar sensibilidade ou contraindicação",
                QuestionFieldType.YES_NO.value,
                None,
                True,
                True,
                "yes",
                3,
            ),
            (
                "Possui marcapasso ou implantes metálicos na área a ser tratada?",
                None,
                QuestionFieldType.YES_NO.value,
                None,
                True,
                True,
                "yes",
                4,
            ),
            (
                "Histórico de cicatrização com queloide ou manchas na pele?",
                None,
                QuestionFieldType.YES_NO.value,
                None,
                True,
                False,
                None,
                5,
            ),
            (
                "Realizou procedimentos estéticos recentes (Botox, preenchimento, peelings)?",
                "Informe se realizou algum procedimento nos últimos 3 meses",
                QuestionFieldType.TEXT.value,
                None,
                False,
                False,
                None,
                6,
            ),
            (
                "Qual sua queixa principal e objetivo com o tratamento?",
                "Conte o que você gostaria de melhorar",
                QuestionFieldType.LONG_TEXT.value,
                None,
                True,
                False,
                None,
                7,
            ),
        ]

        for (
            title,
            desc,
            f_type,
            opts,
            is_req,
            is_risk,
            trigger_val,
            order,
        ) in default_questions:
            q = AnamnesisQuestion(
                template_id=template.id,
                title=title,
                description=desc,
                field_type=f_type,
                options=opts,
                is_required=is_req,
                is_risk_alert=is_risk,
                risk_trigger_value=trigger_val,
                order_index=order,
                is_active=True,
            )
            self.question_repo.add(q)

        self.template_repo._session.flush()
        return self.template_repo.get_by_id(template.id) or template

    def update_template(
        self, template_id: UUID, payload: AnamnesisTemplateUpdate
    ) -> AnamnesisTemplate:
        template = self.template_repo.get_by_id(template_id)
        if template is None:
            raise AnamnesisNotFoundError("Template de anamnese não encontrado")

        if payload.title is not None:
            template.title = payload.title
        if payload.description is not None:
            template.description = payload.description
        if payload.auto_request_on_booking is not None:
            template.auto_request_on_booking = payload.auto_request_on_booking

        self.template_repo._session.flush()
        return template

    def create_question(
        self, template_id: UUID, payload: AnamnesisQuestionCreate
    ) -> AnamnesisQuestion:
        template = self.template_repo.get_by_id(template_id)
        if template is None:
            raise AnamnesisNotFoundError("Template de anamnese não encontrado")

        # Se order_index não veio ou for 0, coloca no final
        order_index = payload.order_index
        if order_index <= 0:
            existing = self.question_repo.list_by_template(
                template_id, active_only=False
            )
            order_index = (
                max([q.order_index for q in existing], default=0) + 1 if existing else 1
            )

        question = AnamnesisQuestion(
            template_id=template_id,
            title=payload.title,
            description=payload.description,
            field_type=payload.field_type,
            options=payload.options,
            is_required=payload.is_required,
            is_risk_alert=payload.is_risk_alert,
            risk_trigger_value=payload.risk_trigger_value,
            order_index=order_index,
            is_active=True,
        )
        self.question_repo.add(question)
        self.question_repo._session.flush()
        return question

    def update_question(
        self, question_id: UUID, payload: AnamnesisQuestionUpdate
    ) -> AnamnesisQuestion:
        question = self.question_repo.get_by_id(question_id)
        if question is None:
            raise AnamnesisQuestionNotFoundError("Pergunta de anamnese não encontrada")

        if payload.title is not None:
            question.title = payload.title
        if payload.description is not None:
            question.description = payload.description
        if payload.field_type is not None:
            question.field_type = payload.field_type
        if payload.options is not None:
            question.options = payload.options
        if payload.is_required is not None:
            question.is_required = payload.is_required
        if payload.is_risk_alert is not None:
            question.is_risk_alert = payload.is_risk_alert
        if payload.risk_trigger_value is not None:
            question.risk_trigger_value = payload.risk_trigger_value
        if payload.order_index is not None:
            question.order_index = payload.order_index
        if payload.is_active is not None:
            question.is_active = payload.is_active

        self.question_repo._session.flush()
        return question

    def delete_question(self, question_id: UUID) -> None:
        question = self.question_repo.get_by_id(question_id)
        if question is None:
            raise AnamnesisQuestionNotFoundError("Pergunta de anamnese não encontrada")
        self.question_repo._session.delete(question)
        self.question_repo._session.flush()

    def reorder_questions(
        self, template_id: UUID, payload: AnamnesisReorderQuestionsInput
    ) -> list[AnamnesisQuestion]:
        template = self.template_repo.get_by_id(template_id)
        if template is None:
            raise AnamnesisNotFoundError("Template de anamnese não encontrado")

        items = [(item.question_id, item.order_index) for item in payload.questions]
        self.question_repo.reorder(template_id, items)
        self.question_repo._session.flush()
        return self.question_repo.list_by_template(template_id, active_only=True)

    def list_submissions(
        self, limit: int = 50, offset: int = 0
    ) -> list[AnamnesisSubmission]:
        return self.submission_repo.list_recent(limit=limit, offset=offset)

    def get_patient_submissions(
        self, patient_id: UUID
    ) -> list[AnamnesisSubmission]:
        return self.submission_repo.list_by_patient(patient_id)

    def get_submission_by_token(self, token: str) -> AnamnesisSubmission | None:
        return self.submission_repo.get_by_token(token)

    def create_or_get_submission(
        self,
        template_id: UUID,
        patient_id: UUID | None = None,
        booking_id: UUID | None = None,
        patient_name: str = "",
        patient_phone: str | None = None,
    ) -> AnamnesisSubmission:
        # Se já existir uma submission para este booking, retorna ela
        if booking_id:
            existing = self.submission_repo.list_by_booking(booking_id)
            if existing:
                return existing[0]

        submission = AnamnesisSubmission(
            template_id=template_id,
            patient_id=patient_id,
            booking_id=booking_id,
            patient_name=patient_name or "Paciente",
            patient_phone=patient_phone,
            answers={},
            has_risk_alerts=False,
            risk_alerts_summary=[],
        )
        self.submission_repo.add(submission)
        self.submission_repo._session.flush()
        return submission

    def submit_answers(
        self,
        submission: AnamnesisSubmission,
        payload: PublicAnamnesisSubmitInput,
        questions: list[AnamnesisQuestion],
    ) -> AnamnesisSubmission:
        submission.patient_name = payload.patient_name
        if payload.patient_phone:
            submission.patient_phone = payload.patient_phone
        submission.answers = payload.answers
        submission.signature_name = payload.signature_name
        submission.submitted_at = datetime.now(UTC)

        # Cálculo automático de alertas de risco
        risk_alerts: list[str] = []
        for q in questions:
            if not q.is_risk_alert:
                continue

            ans = payload.answers.get(str(q.id))
            if ans is None:
                continue

            # Avalia gatilho
            trigger = (q.risk_trigger_value or "yes").lower().strip()
            ans_str = str(ans).lower().strip()

            is_triggered = False
            if trigger in ("yes", "true", "sim") and ans_str in (
                "yes",
                "true",
                "sim",
                "1",
            ) or trigger in ("no", "false", "não", "nao") and ans_str in (
                "no",
                "false",
                "não",
                "nao",
                "0",
            ) or trigger and trigger == ans_str:
                is_triggered = True

            if is_triggered:
                risk_alerts.append(q.title)

        submission.has_risk_alerts = len(risk_alerts) > 0
        submission.risk_alerts_summary = risk_alerts

        self.submission_repo._session.flush()
        return submission
