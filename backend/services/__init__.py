"""
services package
------------------
Services métier pour l'application EMPREINTE.
"""
from services.feries_service import est_jour_ferie, lister_jours_feries, JOURS_FERIES_FIXES
from services.presence_service import (
    statut_jour,
    agregats_jour,
    agregats_periode,
    aujourd_hui_casablanca,
    est_jour_ouvre,
    STATUT_FERIE,
    STATUT_CONGE,
    STATUT_PRESENT,
    STATUT_ABSENT,
)

