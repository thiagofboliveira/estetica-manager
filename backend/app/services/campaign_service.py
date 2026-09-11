"""CampaignService: Gerenciamento de modelos de campanhas e disparos."""

from datetime import datetime
from uuid import UUID

from app.models.campaign import CampaignTemplate
from app.repositories.campaign import CampaignTemplateRepository
from app.schemas.campaign import (
    CampaignTemplateCreate,
    CampaignTemplateOut,
    CampaignTemplateUpdate,
)


class CampaignTemplateNotFoundError(Exception):
    pass


SYSTEM_TEMPLATES: list[dict] = [
    {
        "id": "sys_botox_day",
        "title": "💉 Botox Day Especial",
        "category": "promos",
        "description": "Campanha para preencher a agenda em um dia dedicado à aplicação de toxina botulínica.",
        "message_text": "Oi {nome}! ✨ Passando com uma super novidade: nesta semana teremos nosso Botox Day exclusivo na clínica! Reservamos condições muito especiais para você garantir seu rejuvenescimento e prevenção de linhas de expressão com segurança médica. Temos poucas vagas para esse dia, posso reservar seu horário com a gente?",
        "is_system": True,
        "is_active": True,
    },
    {
        "id": "sys_glow_station",
        "title": "🌸 Protocolo Glow & Renovação Facial",
        "category": "promos",
        "description": "Oferta especial de limpeza de pele profunda associada a peeling iluminador.",
        "message_text": "Olá {nome}! 🌸 Como está sua rotina de cuidados com a pele? Preparamos um protocolo exclusivo de Limpeza de Pele Profunda + Hidratação com LED neste mês para devolver o viço e o glow natural do seu rosto. Vamos marcar seu momento de autocuidado?",
        "is_system": True,
        "is_active": True,
    },
    {
        "id": "sys_reactivation_vip",
        "title": "✨ Sentimos sua Falta (Condição VIP)",
        "category": "reativacao",
        "description": "Mensagem calorosa para pacientes que não visitam a clínica há mais de 60 dias.",
        "message_text": "Oi {nome}, tudo bem com você? Sentimos sua falta aqui na clínica! Pensando em você, separamos um mimo exclusivo de 15% de desconto no seu próximo procedimento neste mês. Que tal tirar uma horinha essa semana para relaxar e se cuidar?",
        "is_system": True,
        "is_active": True,
    },
    {
        "id": "sys_friend_referral",
        "title": "🎁 Traga uma Amiga & Ganhe Mimo",
        "category": "promos",
        "description": "Campanha de indicação onde a paciente e a amiga ganham benefícios.",
        "message_text": "Oi {nome}! Sabia que se cuidar acompanhada é ainda melhor? Durante este mês, se você vier fazer um procedimento e trouxer uma amiga, ambas ganham uma Revitalização Facial de presente! Qual dia fica melhor para virem juntas?",
        "is_system": True,
        "is_active": True,
    },
    {
        "id": "sys_birthday_gift",
        "title": "🎂 Mimo de Aniversário Especial",
        "category": "aniversario",
        "description": "Parabéns especial para aniversariantes do mês com presente exclusivo.",
        "message_text": "Oi {nome}! 🎉 Passando para desejar um Feliz Aniversário! Preparamos um presente especial para você: um mimo exclusivo no seu próximo procedimento este mês. Quando podemos agendar seu momento de cuidado?",
        "is_system": True,
        "is_active": True,
    },
    {
        "id": "sys_maintenance_alert",
        "title": "🎯 Lembrete de Manutenção Preventiva",
        "category": "retencao",
        "description": "Convite para retoque ou manutenção periódica de procedimentos faciais/corporais.",
        "message_text": "Oi {nome}! ✨ Lembrei de você hoje. Já está na hora de fazermos a manutenção do seu procedimento para garantir o melhor resultado e longevidade. Como está sua agenda essa semana?",
        "is_system": True,
        "is_active": True,
    },
]


class CampaignService:
    def __init__(self, repo: CampaignTemplateRepository) -> None:
        self._repo = repo

    def list_templates(self, category: str | None = None) -> list[CampaignTemplateOut]:
        db_templates = self._repo.list_templates(category=category)
        results: list[CampaignTemplateOut] = [
            CampaignTemplateOut(
                id=t.id,
                professional_id=t.professional_id,
                clinic_id=t.clinic_id,
                title=t.title,
                category=t.category,
                description=t.description,
                message_text=t.message_text,
                is_system=False,
                is_active=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in db_templates
        ]

        # Inclui templates de sistema padronizados
        for sys in SYSTEM_TEMPLATES:
            if not category or category == "all" or sys["category"] == category:
                results.append(
                    CampaignTemplateOut(
                        id=sys["id"],
                        professional_id=None,
                        clinic_id=None,
                        title=sys["title"],
                        category=sys["category"],
                        description=sys["description"],
                        message_text=sys["message_text"],
                        is_system=True,
                        is_active=True,
                        created_at=None,
                        updated_at=None,
                    )
                )

        return results

    def create_template(
        self, data: CampaignTemplateCreate, clinic_id: UUID | None = None
    ) -> CampaignTemplateOut:
        template = CampaignTemplate(
            title=data.title.strip(),
            category=data.category.strip() or "promos",
            description=data.description.strip() if data.description else None,
            message_text=data.message_text.strip(),
            clinic_id=clinic_id,
            is_active=True,
        )
        saved = self._repo.add(template)
        return CampaignTemplateOut(
            id=saved.id,
            professional_id=saved.professional_id,
            clinic_id=saved.clinic_id,
            title=saved.title,
            category=saved.category,
            description=saved.description,
            message_text=saved.message_text,
            is_system=False,
            is_active=bool(saved.is_active if saved.is_active is not None else True),
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )

    def update_template(
        self, template_id: UUID, data: CampaignTemplateUpdate
    ) -> CampaignTemplateOut:
        template = self._repo.get(template_id)
        if not template:
            raise CampaignTemplateNotFoundError("Modelo de campanha não encontrado")

        if data.title is not None:
            template.title = data.title.strip()
        if data.category is not None:
            template.category = data.category.strip()
        if data.description is not None:
            template.description = data.description.strip() if data.description else None
        if data.message_text is not None:
            template.message_text = data.message_text.strip()
        if data.is_active is not None:
            template.is_active = data.is_active

        self._repo.flush()

        return CampaignTemplateOut(
            id=template.id,
            professional_id=template.professional_id,
            clinic_id=template.clinic_id,
            title=template.title,
            category=template.category,
            description=template.description,
            message_text=template.message_text,
            is_system=False,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    def delete_template(self, template_id: UUID) -> None:
        template = self._repo.get(template_id)
        if not template:
            raise CampaignTemplateNotFoundError("Modelo de campanha não encontrado")
        self._repo.delete(template)
        self._repo.flush()
