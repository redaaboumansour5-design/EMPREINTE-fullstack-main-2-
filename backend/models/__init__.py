"""
models package
----------------
Regroupe tous les modèles SQLAlchemy pour un import simple :
    from models import Utilisateur, Departement, Pointage, ...
et pour que `db.create_all()` / Alembic voient bien toutes les tables.
"""
from models.administrateur import Administrateur
from models.departement import Departement
from models.utilisateur import Utilisateur, ROLES_VALIDES
from models.permission import Permission
from models.reconnaissance_faciale import ReconnaissanceFaciale
from models.configuration import Configuration
from models.pointage import Pointage, STATUTS_VALIDES as POINTAGE_STATUTS
from models.teletravail import Teletravail, STATUTS_VALIDES as TELETRAVAIL_STATUTS
from models.conge import Conge, STATUTS_VALIDES as CONGE_STATUTS
from models.rapport import Rapport

__all__ = [
    "Administrateur",
    "Departement",
    "Utilisateur",
    "ROLES_VALIDES",
    "Permission",
    "ReconnaissanceFaciale",
    "Configuration",
    "Pointage",
    "POINTAGE_STATUTS",
    "Teletravail",
    "TELETRAVAIL_STATUTS",
    "Conge",
    "CONGE_STATUTS",
    "Rapport",
]
