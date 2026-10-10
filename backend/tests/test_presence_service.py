"""Tests unitaires pour la logique de présence/absence (presence_service)."""
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from services.feries_service import est_jour_ferie
from services.presence_service import (
    STATUT_ABSENT,
    STATUT_CONGE,
    STATUT_FERIE,
    STATUT_PRESENT,
    agregats_jour,
    calculer_taux_ponctualite,
    est_en_retard,
    jours_conge_decomptables,
    statut_jour,
)


def _employe(employe_id=1, date_embauche=None):
    return SimpleNamespace(id=employe_id, date_embauche=date_embauche)


def _pointage(statut="VALIDE", mode=False):
    return SimpleNamespace(
        type="ENTREE",
        statut=statut,
        mode=mode,
        date_heure=datetime(2025, 3, 10, 8, 0),
    )


def _conge(debut, fin, statut="APPROUVE", employe_id=1):
    return SimpleNamespace(
        utilisateur_id=employe_id,
        date_debut=debut,
        date_fin=fin,
        statut=statut,
    )


class TestJoursFeries:
    def test_jour_an(self):
        assert est_jour_ferie(date(2025, 1, 1))

    def test_fete_travail(self):
        assert est_jour_ferie(date(2025, 5, 1))

    def test_jour_ouvrable_normal(self):
        assert not est_jour_ferie(date(2025, 3, 10))  # lundi


class TestStatutJour:
    JOUR = date(2025, 3, 10)  # lundi ouvré

    def test_ferie_prioritaire(self):
        jour_ferie = date(2025, 1, 1)
        resultat = statut_jour(1, jour_ferie, utilisateur=_employe())
        assert resultat["statut"] == STATUT_FERIE

    def test_conge_approuve(self):
        conges = {1: [_conge(self.JOUR, self.JOUR)]}
        resultat = statut_jour(
            1, self.JOUR, utilisateur=_employe(), conges_par_utilisateur=conges
        )
        assert resultat["statut"] == STATUT_CONGE

    def test_conge_soumis_sans_effet(self):
        conges = {1: [_conge(self.JOUR, self.JOUR, statut="SOUMISE")]}
        resultat = statut_jour(
            1, self.JOUR, utilisateur=_employe(), conges_par_utilisateur=conges
        )
        assert resultat["statut"] == STATUT_ABSENT

    def test_pointage_en_attente_compte_present(self):
        pointages = {1: [_pointage(statut="EN_ATTENTE")]}
        resultat = statut_jour(
            1, self.JOUR, utilisateur=_employe(), pointages_par_utilisateur=pointages
        )
        assert resultat["statut"] == STATUT_PRESENT
        assert resultat["a_valider"] is True

    def test_teletravail_approuve_compte_teletravail(self):
        teletravails = {
            1: [SimpleNamespace(utilisateur_id=1, date_debut=self.JOUR, date_fin=self.JOUR, statut="APPROUVE")]
        }
        resultat = statut_jour(
            1,
            self.JOUR,
            utilisateur=_employe(),
            teletravails_par_utilisateur=teletravails,
        )
        assert resultat["statut"] == STATUT_PRESENT
        assert resultat["teletravail"] is True

    def test_pointage_rejete_ne_compte_pas(self):
        pointages = {1: [_pointage(statut="REJETE")]}
        resultat = statut_jour(
            1, self.JOUR, utilisateur=_employe(), pointages_par_utilisateur=pointages
        )
        assert resultat["statut"] == STATUT_ABSENT

    def test_absence_standard(self):
        resultat = statut_jour(1, self.JOUR, utilisateur=_employe())
        assert resultat["statut"] == STATUT_ABSENT

    def test_weekend_exclu(self):
        samedi = date(2025, 3, 8)
        resultat = statut_jour(1, samedi, utilisateur=_employe())
        assert resultat["statut"] is None
        assert resultat.get("weekend") is True

    def test_embauche_future_exclue(self):
        resultat = statut_jour(
            1, self.JOUR, utilisateur=_employe(date_embauche=date(2025, 3, 15))
        )
        assert resultat["hors_effectif"] is True


class TestAgregatsJour:
    JOUR = date(2025, 3, 10)

    def test_coherence_agregats(self):
        employes = [_employe(i) for i in range(1, 4)]
        ag = agregats_jour(employes, self.JOUR)
        total = ag.presents + ag.absents + ag.conges + ag.feries
        assert total == ag.effectif

    def test_jour_ferie_tous_feries(self):
        employes = [_employe(i) for i in range(1, 4)]
        ag = agregats_jour(employes, date(2025, 1, 1))
        assert ag.feries == 3
        assert ag.absents == 0

    def test_compte_un_retard_apres_08h30(self):
        pointage = _pointage()
        pointage.date_heure = datetime(2025, 3, 10, 8, 31)
        ag = agregats_jour(
            [_employe()],
            self.JOUR,
            pointages_cache={1: {self.JOUR: pointage}},
            conges_cache={1: []},
            teletravails_cache={1: []},
        )
        assert ag.presents == 1
        assert ag.retards == 1


class TestCongeDecompte:
    def test_exclut_jours_feries(self):
        conge = _conge(date(2024, 12, 30), date(2025, 1, 2))
        # 30 déc (lun), 31 déc (mar), 1er jan (mer férié), 2 jan (jeu)
        jours = jours_conge_decomptables(conge)
        assert jours == 3  # sans le 1er janvier


class TestPonctualite:
    def test_08h30_n_est_pas_un_retard(self):
        assert est_en_retard("2025-03-10T08:30:00+00:00") is False

    def test_08h31_est_un_retard(self):
        assert est_en_retard("2025-03-10T08:31:00+00:00") is True

    def test_08h30_et_une_seconde_est_un_retard(self):
        assert est_en_retard("2025-03-10T08:30:01+00:00") is True

    def test_heure_anterieure_n_est_pas_un_retard(self):
        assert est_en_retard("2025-03-10T08:29:00+00:00") is False

    def test_08h30_et_59_secondes_est_exclu_de_la_ponctualite(self):
        pointages = [SimpleNamespace(date_heure=datetime(2025, 3, 10, 8, 30, 59))]
        assert calculer_taux_ponctualite(pointages) == 0.0

    def test_calcul_taux_ponctualite_preserve_precision(self):
        pointages = [
            SimpleNamespace(date_heure=datetime(2025, 3, 10, 8, 0)),
            SimpleNamespace(date_heure=datetime(2025, 3, 11, 9, 30)),
        ]
        taux = calculer_taux_ponctualite(pointages)
        assert taux == 50.0
