from decimal import Decimal
from urllib.parse import quote
from uuid import UUID

from sqlalchemy import select

from app.db.session import unsafe_session_without_tenant
from app.domain.loyalty.rules import (
    VIP_TIER_CONFIG,
    VipTier,
    calculate_earned_points,
    determine_vip_tier,
    generate_referral_code,
)
from app.models.clinic import Clinic
from app.models.financial_settings import FinancialSettings
from app.models.loyalty import LoyaltyReward, LoyaltyTransaction, LoyaltyTransactionType
from app.models.patient import Patient
from app.models.professional import Professional
from app.models.sale import Sale
from app.repositories.financial_settings import FinancialSettingsRepository
from app.repositories.loyalty_repository import LoyaltyRepository, LoyaltyRewardRepository
from app.repositories.patient import PatientRepository
from app.repositories.professional import ProfessionalRepository
from app.schemas.loyalty import (
    LoyaltyAdjustRequest,
    LoyaltyOverviewOut,
    LoyaltyPatientOut,
    LoyaltyRewardCreate,
    LoyaltyRewardOut,
    LoyaltyRewardUpdate,
    LoyaltyTransactionOut,
    PublicLoyaltyRewardOut,
    PublicVipCardOut,
    ReferralFriendOut,
    ReferralInfoOut,
    SendVipEmailResponse,
)
from app.services.email_service import EmailService


class InsufficientPointsError(Exception):
    pass


class LoyaltyService:
    def __init__(
        self,
        loyalty_repo: LoyaltyRepository,
        patient_repo: PatientRepository,
        settings_repo: FinancialSettingsRepository,
        professional_repo: ProfessionalRepository | None = None,
        reward_repo: LoyaltyRewardRepository | None = None,
    ) -> None:
        self._loyalty_repo = loyalty_repo
        self._patient_repo = patient_repo
        self._settings_repo = settings_repo
        self._professional_repo = professional_repo
        self._reward_repo = reward_repo


    def _get_settings(self) -> FinancialSettings:
        settings = self._settings_repo.get_singleton()
        if not settings:
            settings = FinancialSettings(
                loyalty_enabled=True,
                loyalty_points_per_currency=Decimal("0.10"),
                loyalty_redemption_rate=Decimal("1.00"),
                referral_reward_points=50,
            )
        return settings

    def get_patient_loyalty(self, patient_id: UUID) -> LoyaltyPatientOut:
        patient = self._patient_repo.get(patient_id)
        if not patient:
            raise ValueError("Paciente não encontrada")

        if not patient.referral_code:
            patient.referral_code = generate_referral_code(patient.name)
            self._patient_repo.flush()

        settings = self._get_settings()
        redemption_rate = settings.loyalty_redemption_rate or Decimal("1.00")
        monetary_value = Decimal(patient.loyalty_points) * redemption_rate

        tier = patient.vip_tier or VipTier.BRONZE
        tier_cfg = VIP_TIER_CONFIG.get(tier, VIP_TIER_CONFIG[VipTier.BRONZE])

        referred_by_name = None
        if patient.referred_by_id:
            referrer = self._patient_repo.get(patient.referred_by_id)
            if referrer:
                referred_by_name = referrer.name

        txs = self._loyalty_repo.list_for_patient(patient_id, limit=50)

        return LoyaltyPatientOut(
            patient_id=patient.id,
            patient_name=patient.name,
            loyalty_points=patient.loyalty_points,
            vip_tier=tier,
            vip_badge=tier_cfg["badge"],
            monetary_value=monetary_value,
            referral_code=patient.referral_code,
            referred_by_name=referred_by_name,
            transactions=[LoyaltyTransactionOut.model_validate(t) for t in txs],
        )

    def adjust_points(self, patient_id: UUID, req: LoyaltyAdjustRequest) -> LoyaltyTransactionOut:
        patient = self._patient_repo.get(patient_id)
        if not patient:
            raise ValueError("Paciente não encontrada")

        new_balance = patient.loyalty_points + req.points
        if new_balance < 0:
            raise InsufficientPointsError("Saldo de pontos insuficiente para este resgate")

        patient.loyalty_points = new_balance
        # Atualiza o nível VIP se subir
        computed_tier = determine_vip_tier(new_balance)
        patient.vip_tier = computed_tier

        tx = self._loyalty_repo.add_transaction(
            patient_id=patient.id,
            points=req.points,
            balance_after=new_balance,
            transaction_type=req.transaction_type,
            description=req.description,
        )
        self._loyalty_repo.flush()
        return LoyaltyTransactionOut.model_validate(tx)

    def process_sale_points(self, sale: Sale, patient: Patient) -> int:
        """Chamado pelo SaleService após registrar venda para creditar pontos ao comprador
        e recompensar quem indicou se for a 1ª compra."""
        settings = self._get_settings()
        if not settings.loyalty_enabled:
            return 0

        # 1. Pontos ganhos pelo paciente na compra
        earned = calculate_earned_points(sale.gross_amount, settings.loyalty_points_per_currency)
        if earned > 0:
            patient.loyalty_points += earned
            patient.vip_tier = determine_vip_tier(patient.loyalty_points)
            self._loyalty_repo.add_transaction(
                patient_id=patient.id,
                sale_id=sale.id,
                points=earned,
                balance_after=patient.loyalty_points,
                transaction_type=LoyaltyTransactionType.EARNED,
                description=f"Pontos acumulados na venda de R$ {sale.gross_amount:.2f}",
            )

        # 2. Bônus para quem indicou (se houver e for a primeira venda desta paciente)
        if patient.referred_by_id and settings.referral_reward_points > 0:
            referrer = self._patient_repo.get(patient.referred_by_id)
            if referrer:
                # Checa se é a primeira transação de venda da paciente indicada
                bonus_points = settings.referral_reward_points
                referrer.loyalty_points += bonus_points
                referrer.vip_tier = determine_vip_tier(referrer.loyalty_points)
                self._loyalty_repo.add_transaction(
                    patient_id=referrer.id,
                    sale_id=sale.id,
                    points=bonus_points,
                    balance_after=referrer.loyalty_points,
                    transaction_type=LoyaltyTransactionType.BONUS,
                    description=f"Bônus de indicação: {patient.name} realizou seu primeiro procedimento!",
                )

        self._loyalty_repo.flush()
        return earned

    def get_referral_info(self, patient_id: UUID) -> ReferralInfoOut:
        patient = self._patient_repo.get(patient_id)
        if not patient:
            raise ValueError("Paciente não encontrada")

        if not patient.referral_code:
            patient.referral_code = generate_referral_code(patient.name)
            self._patient_repo.flush()

        settings = self._get_settings()
        reward_points = settings.referral_reward_points or 50

        # Amigas indicadas por esta paciente
        friends = self._patient_repo.list_referred_by(patient_id)

        converted_count = 0
        friends_out = []
        for f in friends:
            # Checa se f já realizou alguma venda
            has_completed = f.loyalty_points > 0 or f.vip_tier != VipTier.BRONZE
            if has_completed:
                converted_count += 1
            friends_out.append(
                ReferralFriendOut(
                    patient_id=f.id,
                    patient_name=f.name,
                    joined_at=f.created_at,
                    has_completed_sale=has_completed,
                )
            )

        professional_name = "minha clínica favorita"
        if self._professional_repo:
            prof = self._professional_repo.get_current()
            if prof and prof.name:
                professional_name = prof.name

        msg = (
            f"Oi amiga! Tenho um mimo especial para você na {professional_name} ✨ "
            f"Use meu código de indicação *{patient.referral_code}* no seu primeiro agendamento "
            f"para ganhar um benefício exclusivo!"
        )
        whatsapp_url = f"https://wa.me/?text={quote(msg)}"

        return ReferralInfoOut(
            referral_code=patient.referral_code,
            whatsapp_share_text=msg,
            whatsapp_share_url=whatsapp_url,
            reward_points_per_friend=reward_points,
            total_friends_referred=len(friends),
            friends_converted_count=converted_count,
            total_points_earned_from_referrals=converted_count * reward_points,
            friends=friends_out,
        )

    def get_overview(self) -> LoyaltyOverviewOut:
        settings = self._get_settings()
        patients = self._patient_repo.list(limit=5000)

        total_points = sum(p.loyalty_points for p in patients)
        redemption_rate = settings.loyalty_redemption_rate or Decimal("1.00")
        total_value = Decimal(total_points) * redemption_rate

        tier_counts = {
            VipTier.BRONZE: 0,
            VipTier.SILVER: 0,
            VipTier.GOLD: 0,
            VipTier.DIAMOND: 0,
        }
        total_referrals = 0
        total_converted = 0

        for p in patients:
            tier = p.vip_tier or VipTier.BRONZE
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            if p.referred_by_id:
                total_referrals += 1
                if p.loyalty_points > 0 or p.vip_tier != VipTier.BRONZE:
                    total_converted += 1

        return LoyaltyOverviewOut(
            total_active_points=total_points,
            total_value_in_currency=total_value,
            tier_counts=tier_counts,
            total_referrals_count=total_referrals,
            total_converted_referrals=total_converted,
        )

    @classmethod
    def get_public_vip_card(cls, referral_code: str) -> PublicVipCardOut:
        """Retorna os dados do Cartão VIP público da paciente para acesso seguro sem senha."""
        with unsafe_session_without_tenant("public vip card") as session:
            patient = PatientRepository.get_by_referral_code_unscoped(session, referral_code)
            if not patient:
                raise ValueError("Cartão VIP não encontrado com o código informado.")

            # Resolve clínica e profissional
            clinic_name = "Clínica Lumina"
            booking_slug = None
            if patient.professional_id:
                prof = session.get(Professional, patient.professional_id)
                if prof:
                    booking_slug = prof.slug
                    if prof.clinic_id:
                        clinic = session.get(Clinic, prof.clinic_id)
                        if clinic and clinic.name:
                            clinic_name = clinic.name
                        elif prof.name:
                            clinic_name = f"Espaço {prof.name}"
                    elif prof.name:
                        clinic_name = f"Espaço {prof.name}"


            # Regras de próximo tier
            tier = patient.vip_tier or VipTier.BRONZE
            tier_cfg = VIP_TIER_CONFIG.get(tier, VIP_TIER_CONFIG[VipTier.BRONZE])
            next_tier = None
            points_to_next = 0
            next_tier_target = None

            if tier == VipTier.BRONZE:
                next_tier = "PRATA"
                next_tier_target = 100
                points_to_next = max(0, 100 - patient.loyalty_points)
            elif tier == VipTier.SILVER:
                next_tier = "OURO"
                next_tier_target = 300
                points_to_next = max(0, 300 - patient.loyalty_points)
            elif tier == VipTier.GOLD:
                next_tier = "DIAMANTE"
                next_tier_target = 700
                points_to_next = max(0, 700 - patient.loyalty_points)

            # Crédito em reais (R$ 0,50 por ponto padrão)
            credit_value = Decimal(patient.loyalty_points) * Decimal("0.50")


            first_name = patient.name.split()[0] if patient.name else "Cliente"
            wa_text = (
                f"Oi amiga! Ganhei um benefício especial para você na {clinic_name}! ✨ "
                f"Use meu código exclusivo *{patient.referral_code}* no seu primeiro agendamento "
                f"para ganhar um presente de boas-vindas!"
            )

            # Catálogo de Recompensas: busca customizado da profissional ou cai no padrão
            custom_rewards: list[LoyaltyReward] = []
            if patient.professional_id:
                custom_rewards = LoyaltyRewardRepository.list_active_by_professional_unscoped(
                    session, patient.professional_id
                )

            if custom_rewards:
                rewards = [
                    PublicLoyaltyRewardOut(
                        points_cost=r.points_cost,
                        title=r.title,
                        description=r.description or "",
                        discount_value=r.discount_value,
                    )
                    for r in custom_rewards
                ]
            else:
                rewards = [
                    PublicLoyaltyRewardOut(
                        points_cost=50,
                        title="R$ 25 de Desconto",
                        description="Abata R$ 25,00 direto na sua próxima sessão de qualquer procedimento.",
                        discount_value=Decimal("25.00"),
                    ),
                    PublicLoyaltyRewardOut(
                        points_cost=100,
                        title="R$ 50 de Desconto",
                        description="Crédito de R$ 50,00 ou aplicação de Máscara Revitalizante.",
                        discount_value=Decimal("50.00"),
                    ),
                    PublicLoyaltyRewardOut(
                        points_cost=200,
                        title="Drenagem Facial Revitalizante",
                        description="Sessão cortesia de Drenagem e Massagem Lifting Facial.",
                        discount_value=Decimal("120.00"),
                    ),
                    PublicLoyaltyRewardOut(
                        points_cost=300,
                        title="Peeling de Diamante Completo",
                        description="Higienização profunda, esfoliação com ponteira de diamante e fototerapia.",
                        discount_value=Decimal("180.00"),
                    ),
                ]

            return PublicVipCardOut(
                patient_first_name=first_name,
                patient_full_name=patient.name,
                clinic_name=clinic_name,
                vip_tier=tier,
                vip_badge=tier_cfg["badge"],
                loyalty_points=patient.loyalty_points,
                monetary_credit_value=credit_value,
                next_tier=next_tier,
                points_to_next_tier=points_to_next,
                next_tier_threshold=next_tier_target,
                referral_code=patient.referral_code,
                referral_whatsapp_message=wa_text,
                public_booking_slug=booking_slug,
                catalog_rewards=rewards,
            )

    def send_vip_card_email(self, patient_id: UUID, app_base_url: str = "") -> SendVipEmailResponse:
        """Gera e envia o Cartão VIP por e-mail para a paciente."""
        patient = self._patient_repo.get(patient_id)
        if not patient:
            raise ValueError("Paciente não encontrada.")

        if not patient.email or "@" not in patient.email:
            raise ValueError("Paciente não possui e-mail válido cadastrado.")

        if not patient.referral_code:
            patient.referral_code = generate_referral_code(patient.name)
            self._patient_repo.flush()

        clinic_name = "Clínica Lumina"
        booking_slug = None
        if self._professional_repo:
            prof = self._professional_repo.get_current()
            if prof:
                booking_slug = prof.slug
                if prof.name:
                    clinic_name = f"Espaço {prof.name}"

        card_url = f"{app_base_url}/clube-vip/{patient.referral_code}" if app_base_url else f"/clube-vip/{patient.referral_code}"
        booking_url = f"{app_base_url}/agendar/{booking_slug}" if booking_slug and app_base_url else None
        credit_val = Decimal(patient.loyalty_points) * Decimal("0.50")

        email_svc = EmailService()
        email_svc.send_vip_card_email(
            recipient_email=patient.email,
            patient_name=patient.name,
            clinic_name=clinic_name,
            vip_tier=patient.vip_tier or VipTier.BRONZE,
            loyalty_points=patient.loyalty_points,
            credit_value=credit_val,
            referral_code=patient.referral_code,
            vip_card_url=card_url,
            booking_url=booking_url,
        )

        return SendVipEmailResponse(
            success=True,
            message=f"Cartão VIP enviado com sucesso para {patient.email}",
            recipient_email=patient.email,
        )

    def list_rewards(self, active_only: bool = False) -> list[LoyaltyRewardOut]:
        if not self._reward_repo:
            return []
        rewards = self._reward_repo.list_active() if active_only else self._reward_repo.list_all()
        return [LoyaltyRewardOut.model_validate(r) for r in rewards]

    def create_reward(self, payload: LoyaltyRewardCreate) -> LoyaltyRewardOut:
        if not self._reward_repo:
            raise ValueError("Repositório de recompensas não configurado.")
        reward = LoyaltyReward(
            points_cost=payload.points_cost,
            title=payload.title,
            description=payload.description,
            discount_value=payload.discount_value,
            is_active=payload.is_active,
            order_index=payload.order_index,
        )
        saved = self._reward_repo.add(reward)
        return LoyaltyRewardOut.model_validate(saved)

    def update_reward(self, reward_id: UUID, payload: LoyaltyRewardUpdate) -> LoyaltyRewardOut:
        if not self._reward_repo:
            raise ValueError("Repositório de recompensas não configurado.")
        reward = self._reward_repo.get(reward_id)
        if not reward:
            raise ValueError("Recompensa não encontrada.")

        if payload.points_cost is not None:
            reward.points_cost = payload.points_cost
        if payload.title is not None:
            reward.title = payload.title
        if payload.description is not None:
            reward.description = payload.description
        if payload.discount_value is not None:
            reward.discount_value = payload.discount_value
        if payload.is_active is not None:
            reward.is_active = payload.is_active
        if payload.order_index is not None:
            reward.order_index = payload.order_index

        self._reward_repo.flush()
        return LoyaltyRewardOut.model_validate(reward)

    def delete_reward(self, reward_id: UUID) -> None:
        if not self._reward_repo:
            raise ValueError("Repositório de recompensas não configurado.")
        reward = self._reward_repo.get(reward_id)
        if not reward:
            raise ValueError("Recompensa não encontrada.")
        self._reward_repo.delete(reward)
        self._reward_repo.flush()


