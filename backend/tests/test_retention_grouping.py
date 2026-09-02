from datetime import date, datetime

from app.domain.retention.grouping import OpportunityForGrouping, group_by_patient


def _opp(**overrides):
    defaults = dict(
        id="opp-1",
        patient_id="pat-1",
        patient_name="Maria",
        patient_phone="+5511999999999",
        consent_whatsapp=True,
        opted_out_at=None,
        last_contacted_at=None,
        procedure_name="Botox",
        due_date=date(2026, 9, 1),
        status="OPEN",
        potential_value="1000.00",
    )
    defaults.update(overrides)
    return OpportunityForGrouping(**defaults)


def test_agrupa_por_paciente_um_card_por_paciente():
    opportunities = [
        _opp(id="a", patient_id="pat-1", potential_value="1000.00"),
        _opp(id="b", patient_id="pat-1", procedure_name="Skinbooster", potential_value="300.00"),
        _opp(id="c", patient_id="pat-2", potential_value="200.00"),
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert len(groups) == 2
    maria = next(g for g in groups if g.patient_id == "pat-1")
    assert len(maria.opportunities) == 2
    assert maria.total_potential_value == "1300.00"


def test_ordena_por_atraso_mais_atrasado_primeiro():
    opportunities = [
        _opp(id="a", patient_id="pat-1", due_date=date(2026, 9, 10)),
        _opp(id="b", patient_id="pat-1", procedure_name="Skinbooster", due_date=date(2026, 8, 1)),
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups[0].opportunities[0].procedure == "Skinbooster"


def test_ordena_pacientes_por_valor_potencial_total_decrescente():
    opportunities = [
        _opp(id="a", patient_id="pat-1", potential_value="100.00"),
        _opp(id="b", patient_id="pat-2", potential_value="900.00"),
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups[0].patient_id == "pat-2"


def test_suprime_paciente_contatada_ha_menos_de_14_dias():
    opportunities = [
        _opp(
            patient_id="pat-1",
            last_contacted_at=datetime(2026, 8, 30, 12, 0),
        )
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups == []


def test_nao_suprime_paciente_contatada_ha_mais_de_14_dias():
    opportunities = [
        _opp(
            patient_id="pat-1",
            last_contacted_at=datetime(2026, 8, 10, 12, 0),
        )
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert len(groups) == 1


def test_can_contact_falso_sem_consentimento():
    opportunities = [_opp(patient_id="pat-1", consent_whatsapp=False)]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups[0].can_contact is False
    assert groups[0].cannot_contact_reason is not None


def test_can_contact_falso_sem_telefone():
    opportunities = [_opp(patient_id="pat-1", patient_phone=None)]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups[0].can_contact is False


def test_can_contact_falso_com_opt_out():
    opportunities = [
        _opp(patient_id="pat-1", opted_out_at=datetime(2026, 1, 1))
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups[0].can_contact is False
