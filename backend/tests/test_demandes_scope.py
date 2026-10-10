from types import SimpleNamespace

from routes.demandes import _determiner_perimetre


def test_scope_employe_est_limite_a_ses_demandes():
    principal = SimpleNamespace(id=7, departement_id=3)
    assert _determiner_perimetre("employe", principal) == "mine"


def test_scope_manager_sans_departement_reste_global():
    principal = SimpleNamespace(id=12, departement_id=None)
    assert _determiner_perimetre("manager", principal) == "all"


def test_scope_rh_avec_departement_utilise_le_departement():
    principal = SimpleNamespace(id=13, departement_id=4)
    assert _determiner_perimetre("rh", principal) == "departement"
