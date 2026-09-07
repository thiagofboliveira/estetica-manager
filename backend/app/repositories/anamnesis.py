"""Repository para Anamnese Digital (AN-04)."""

from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import joinedload

from app.models.anamnesis import (
    AnamnesisQuestion,
    AnamnesisSubmission,
    AnamnesisTemplate,
)
from app.repositories.base import TenantRepository


class AnamnesisTemplateRepository(TenantRepository[AnamnesisTemplate]):
    model = AnamnesisTemplate

    def get_default_with_questions(self) -> AnamnesisTemplate | None:
        stmt = (
            self._scoped()
            .where(
                AnamnesisTemplate.is_default == True,  # noqa: E712
                AnamnesisTemplate.is_active == True,  # noqa: E712
            )
            .options(joinedload(AnamnesisTemplate.questions))
        )
        return self._session.scalars(stmt).unique().first()

    def get_by_id(self, template_id: UUID) -> AnamnesisTemplate | None:
        stmt = (
            self._scoped()
            .where(AnamnesisTemplate.id == template_id)
            .options(joinedload(AnamnesisTemplate.questions))
        )
        return self._session.scalars(stmt).unique().first()


class AnamnesisQuestionRepository(TenantRepository[AnamnesisQuestion]):
    model = AnamnesisQuestion

    def list_by_template(
        self, template_id: UUID, active_only: bool = True
    ) -> list[AnamnesisQuestion]:
        stmt = self._scoped().where(AnamnesisQuestion.template_id == template_id)
        if active_only:
            stmt = stmt.where(AnamnesisQuestion.is_active == True)  # noqa: E712
        stmt = stmt.order_by(
            AnamnesisQuestion.order_index.asc(), AnamnesisQuestion.created_at.asc()
        )
        return list(self._session.scalars(stmt))

    def get_by_id(self, question_id: UUID) -> AnamnesisQuestion | None:
        stmt = self._scoped().where(AnamnesisQuestion.id == question_id)
        return self._session.scalar(stmt)

    def reorder(self, template_id: UUID, items: list[tuple[UUID, int]]) -> None:
        for q_id, order_idx in items:
            self._session.execute(
                update(AnamnesisQuestion)
                .where(
                    AnamnesisQuestion.id == q_id,
                    AnamnesisQuestion.template_id == template_id,
                    AnamnesisQuestion.professional_id == self._professional_id,
                )
                .values(order_index=order_idx)
            )


class AnamnesisSubmissionRepository(TenantRepository[AnamnesisSubmission]):
    model = AnamnesisSubmission

    def get_by_token(self, token: str) -> AnamnesisSubmission | None:
        stmt = self._scoped().where(AnamnesisSubmission.public_token == token)
        return self._session.scalar(stmt)

    def list_by_patient(self, patient_id: UUID) -> list[AnamnesisSubmission]:
        stmt = (
            self._scoped()
            .where(AnamnesisSubmission.patient_id == patient_id)
            .order_by(
                AnamnesisSubmission.submitted_at.desc().nullslast(),
                AnamnesisSubmission.created_at.desc(),
            )
        )
        return list(self._session.scalars(stmt))

    def list_by_booking(self, booking_id: UUID) -> list[AnamnesisSubmission]:
        stmt = (
            self._scoped()
            .where(AnamnesisSubmission.booking_id == booking_id)
            .order_by(AnamnesisSubmission.created_at.desc())
        )
        return list(self._session.scalars(stmt))

    def list_recent(
        self, limit: int = 50, offset: int = 0
    ) -> list[AnamnesisSubmission]:
        stmt = (
            self._scoped()
            .order_by(
                AnamnesisSubmission.submitted_at.desc().nullslast(),
                AnamnesisSubmission.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt))
