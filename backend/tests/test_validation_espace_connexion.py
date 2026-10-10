import pytest


# Petite "classe fake" pour éviter toute dépendance ORM/DB
class FakeUtilisateur:
    def __init__(self, teletravail_autorise: bool):
        self.teletravail_autorise = teletravail_autorise


# Import en local : la fonction vit dans backend/routes/auth.py
# (on ajoute le dossier backend au sys.path pour éviter les problèmes de packaging)
import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from routes.auth import valider_espace_connexion



def test_autorise_teletravail_ok():
    u = FakeUtilisateur(teletravail_autorise=True)
    # teletravail_autorise=1 => OK en Télétravail
    valider_espace_connexion(u, "teletravail", teletravail_approuve_active=False)


def test_demande_approuvee_prime_pour_teletravail():
    u = FakeUtilisateur(teletravail_autorise=False)
    # demande approuvée couvrant aujourd'hui => OK en Télétravail
    valider_espace_connexion(u, "teletravail", teletravail_approuve_active=True)


def test_non_autorise_presentiel_ok():
    u = FakeUtilisateur(teletravail_autorise=False)
    # pas d'autorisation télétravail et pas de demande => OK en Présentiel
    valider_espace_connexion(u, "presentiel", teletravail_approuve_active=False)


def test_non_autorise_presentiel_refuse_si_demande_approuvee():
    u = FakeUtilisateur(teletravail_autorise=False)
    # demande approuvée => doit être en Télétravail, donc refus en Présentiel
    with pytest.raises(PermissionError) as excinfo:
        valider_espace_connexion(u, "presentiel", teletravail_approuve_active=True)
    assert "télétravail" in str(excinfo.value).lower()





def test_autorise_presentiel_refuse():
    u = FakeUtilisateur(teletravail_autorise=True)
    with pytest.raises(PermissionError) as excinfo:
        valider_espace_connexion(u, "presentiel", teletravail_approuve_active=False)
    assert "télétravail" in str(excinfo.value).lower()




def test_non_autorise_teletravail_refuse():
    u = FakeUtilisateur(teletravail_autorise=False)
    with pytest.raises(PermissionError) as excinfo:
        valider_espace_connexion(u, "teletravail", teletravail_approuve_active=False)
    assert "présentiel" in str(excinfo.value).lower()



def test_non_autorise_presentiel_ok():
    u = FakeUtilisateur(teletravail_autorise=False)
    valider_espace_connexion(u, "presentiel", teletravail_approuve_active=False)

