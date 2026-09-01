from uuid import UUID, uuid4

from app.models.clinic import Clinic
from app.repositories.clinic import ClinicRepository


class ClinicService:
    def __init__(self, clinic_repo: ClinicRepository) -> None:
        self._clinic_repo = clinic_repo

    def list_clinics(self) -> list[dict]:
        clinics = self._clinic_repo.list_all()
        result = []
        for c in clinics:
            users_count = self._clinic_repo.count_users(c.id)
            result.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "document": c.document,
                    "phone": c.phone,
                    "email": c.email,
                    "plan": c.plan,
                    "is_active": c.is_active,
                    "users_count": users_count,
                    "created_at": c.created_at,
                    "updated_at": c.updated_at,
                }
            )
        return result

    def get_clinic(self, clinic_id: UUID) -> Clinic:
        clinic = self._clinic_repo.get_by_id(clinic_id)
        if clinic is None:
            raise LookupError(f"Clínica {clinic_id} não encontrada")
        return clinic

    def create_clinic(
        self,
        name: str,
        document: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        plan: str = "standard",
    ) -> Clinic:
        clinic = Clinic(
            id=uuid4(),
            name=name.strip(),
            document=document.strip() if document else None,
            phone=phone.strip() if phone else None,
            email=email.strip().lower() if email else None,
            plan=plan.strip(),
            is_active=True,
        )
        return self._clinic_repo.add(clinic)

    def update_clinic(
        self,
        clinic_id: UUID,
        name: str | None = None,
        document: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        plan: str | None = None,
        is_active: bool | None = None,
    ) -> Clinic:
        clinic = self.get_clinic(clinic_id)

        if name is not None:
            clinic.name = name.strip()
        if document is not None:
            clinic.document = document.strip() if document else None
        if phone is not None:
            clinic.phone = phone.strip() if phone else None
        if email is not None:
            clinic.email = email.strip().lower() if email else None
        if plan is not None:
            clinic.plan = plan.strip()
        if is_active is not None:
            clinic.is_active = is_active

        self._clinic_repo.flush()
        return clinic

    def deactivate_clinic(self, clinic_id: UUID) -> Clinic:
        return self.update_clinic(clinic_id, is_active=False)
