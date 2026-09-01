from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Clinic(Base, TimestampMixin):
    """Clínica — entidade de Tenant organizacional no SaaS Multi-Tenant.
    
    Representa a empresa/clínica contratante do SaaS, agrupando profissionais,
    usuários e configurações de atendimento.
    """

    __tablename__ = "clinics"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(nullable=False)
    document: Mapped[str | None] = mapped_column(nullable=True)  # CNPJ / CPF
    phone: Mapped[str | None] = mapped_column(nullable=True)
    email: Mapped[str | None] = mapped_column(nullable=True)
    plan: Mapped[str] = mapped_column(default="standard", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
