from decimal import Decimal
from urllib.parse import quote
from uuid import UUID

from app.domain.loyalty.rules import (
    VIP_TIER_CONFIG,
    VipTier,
    calculate_earned_points,
    determine_vip_tier,
    generate_referral_code,
)
from app.models.financial_settings import FinancialSettings
from app.models.loyalty import LoyaltyTransaction, LoyaltyTransactionType
from app.models.patient import Patient
from app.models.sale import Sale
from app.repositories.financial_settings import FinancialSettingsRepository
from app.repositories.loyalty_repository import LoyaltyRepository
from app.repositories.patient import PatientRepository
from app.repositories.professional import ProfessionalRepository
from app.schemas.loyalty import (
    LoyaltyAdjustRequest,
    LoyaltyOverviewOut,
    LoyaltyPatientOut,
    LoyaltyTransactionOut,
    ReferralFriendOut,
    ReferralInfoOut,
)


class InsufficientPointsError(Exception):
    pass


class LoyaltyService:
    def __init__(
        self,
        loyalty_repo: LoyaltyRepository,
        patient_repo: PatientRepository,
        settings_repo: FinancialSettingsRepository,
        professional_repo: ProfessionalRepository | None = None,
    ) -> None:
        self._loyalty_repo = loyalty_repo
        self._patient_repo = patient_repo
        self._settings_repo = settings_repo
        self._professional_repo = professional_repo

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
