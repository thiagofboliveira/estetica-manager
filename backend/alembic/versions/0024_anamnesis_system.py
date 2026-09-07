"""anamnesis_system: templates, questions and submissions (AN-01)

Revision ID: 0024
Revises: 0023
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. anamnesis_templates
    op.create_table(
        "anamnesis_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "title",
            sa.String(255),
            nullable=False,
            server_default="Ficha de Anamnese Facial e Corporal",
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "auto_request_on_booking",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
    )

    # 2. anamnesis_questions
    op.create_table(
        "anamnesis_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("anamnesis_templates.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "field_type",
            sa.String(50),
            nullable=False,
            server_default="yes_no",
        ),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "is_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "is_risk_alert",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("risk_trigger_value", sa.String(50), nullable=True),
        sa.Column(
            "order_index",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_anamnesis_questions_order",
        "anamnesis_questions",
        ["template_id", "order_index"],
    )

    # 3. anamnesis_submissions
    op.create_table(
        "anamnesis_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("anamnesis_templates.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "booking_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bookings.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("public_token", sa.String(64), nullable=False),
        sa.Column("patient_name", sa.String(255), nullable=False),
        sa.Column("patient_phone", sa.String(30), nullable=True),
        sa.Column(
            "answers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "has_risk_alerts",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "risk_alerts_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("signature_name", sa.String(255), nullable=True),
        sa.Column("submitted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_anamnesis_submissions_token",
        "anamnesis_submissions",
        ["public_token"],
        unique=True,
    )

    # 4. RLS e Grants para estetica_app
    for table_name in [
        "anamnesis_templates",
        "anamnesis_questions",
        "anamnesis_submissions",
    ]:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'estetica_app') THEN
                    GRANT SELECT, INSERT, UPDATE, DELETE ON {table_name} TO estetica_app;
                END IF;
            END $$;
            """
        )

    op.execute("ALTER TABLE anamnesis_templates ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE anamnesis_templates FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON anamnesis_templates
          FOR ALL TO estetica_app
          USING (
            current_setting('app.bypass_tenant', true) = 'true'
            OR professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
          )
          WITH CHECK (
            current_setting('app.bypass_tenant', true) = 'true'
            OR professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
          );
        """
    )

    op.execute("ALTER TABLE anamnesis_questions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE anamnesis_questions FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON anamnesis_questions
          FOR ALL TO estetica_app
          USING (
            current_setting('app.bypass_tenant', true) = 'true'
            OR professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
          )
          WITH CHECK (
            current_setting('app.bypass_tenant', true) = 'true'
            OR professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
          );
        """
    )

    op.execute("ALTER TABLE anamnesis_submissions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE anamnesis_submissions FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON anamnesis_submissions
          FOR ALL TO estetica_app
          USING (
            current_setting('app.bypass_tenant', true) = 'true'
            OR professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
          )
          WITH CHECK (
            current_setting('app.bypass_tenant', true) = 'true'
            OR professional_id = NULLIF(current_setting('app.professional_id', true), '')::uuid
          );
        """
    )

    # 5. Seed dos templates e perguntas iniciais para cada profissional existente
    op.execute(
        """
        DO $$
        DECLARE
            p RECORD;
            t_id UUID;
        BEGIN
            FOR p IN SELECT id, clinic_id FROM professionals LOOP
                -- Verifica se já tem template padrão
                IF NOT EXISTS (SELECT 1 FROM anamnesis_templates WHERE professional_id = p.id) THEN
                    t_id := gen_random_uuid();
                    INSERT INTO anamnesis_templates (
                        id, professional_id, clinic_id, title, description, is_default, is_active, auto_request_on_booking
                    ) VALUES (
                        t_id, p.id, p.clinic_id, 'Ficha de Anamnese Facial e Corporal',
                        'Questionário prévio de saúde e histórico estético para segurança do procedimento.',
                        true, true, true
                    );

                    -- Insere perguntas essenciais padrão
                    INSERT INTO anamnesis_questions (
                        id, template_id, professional_id, title, description, field_type, is_required, is_risk_alert, risk_trigger_value, order_index, is_active
                    ) VALUES
                    (gen_random_uuid(), t_id, p.id, 'Está gestante ou em período de amamentação?', NULL, 'yes_no', true, true, 'yes', 1, true),
                    (gen_random_uuid(), t_id, p.id, 'Possui alguma alergia conhecida (medicamentos, cosméticos, látex)?', 'Se sim, especifique no atendimento', 'yes_no', true, true, 'yes', 2, true),
                    (gen_random_uuid(), t_id, p.id, 'Faz uso de medicamentos contínuos (ex: Roacutan, anticoagulantes)?', 'Importante para avaliar sensibilidade ou contraindicação', 'yes_no', true, true, 'yes', 3, true),
                    (gen_random_uuid(), t_id, p.id, 'Possui marcapasso ou implantes metálicos na área a ser tratada?', NULL, 'yes_no', true, true, 'yes', 4, true),
                    (gen_random_uuid(), t_id, p.id, 'Histórico de cicatrização com queloide ou manchas na pele?', NULL, 'yes_no', true, false, NULL, 5, true),
                    (gen_random_uuid(), t_id, p.id, 'Realizou procedimentos estéticos recentes (Botox, preenchimento, peelings)?', 'Informe se realizou algum procedimento nos últimos 3 meses', 'text', false, false, NULL, 6, true),
                    (gen_random_uuid(), t_id, p.id, 'Qual sua queixa principal e objetivo com o tratamento?', 'Conte o que você gostaria de melhorar', 'long_text', true, false, NULL, 7, true);
                END IF;
            END LOOP;
        END $$;
        """
    )


def downgrade() -> None:
    op.drop_table("anamnesis_submissions")
    op.drop_table("anamnesis_questions")
    op.drop_table("anamnesis_templates")
