from sqlalchemy import func, or_

from app.models.patient import Patient
from app.repositories.base import TenantRepository


class PatientRepository(TenantRepository[Patient]):
    model = Patient

    def list(
        self, *, limit: int = 50, offset: int = 0, search: str | None = None
    ) -> list[Patient]:
        """Lista ativos, com busca opcional por nome (case/acento-insensível
        via unaccent — requer a extensão habilitada na migration)."""
        stmt = self._scoped().where(Patient.is_active.is_(True))
        if search:
            needle = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    func.unaccent(Patient.name).ilike(func.unaccent(needle)),
                    Patient.phone.ilike(needle),
                )
            )
        return list(
            self._session.scalars(
                stmt.order_by(Patient.name).limit(limit).offset(offset)
            )
        )
