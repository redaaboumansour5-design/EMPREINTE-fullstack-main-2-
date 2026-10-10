"""
services/feries_service.py
----------------------------
Service de détection des jours fériés marocains.

Jours fériés fixes (grégoriens) :
  - 1er janvier    → Jour de l'An
  - 1er mai        → Fête du Travail
  - 30 juillet     → Fête du Trône
  - 6 novembre     → Anniversaire de la Marche Verte
  - 18 novembre    → Fête de l'Indépendance

Jours fériés mobiles (calendrier hégirien) :
  - 1er Moharram (1 Muharram)           → Nouvel An hégirien
  - 12 Rabi' al-awwal                    → Aid Al Mawlid Annabaoui
  - 1er & 2 Shawwal                      → Aïd al-Fitr (2 jours)
  - 10 & 11 Dhu al-Hijjah                → Aïd al-Adha (2 jours)

Utilisation :
    from services.feries_service import est_jour_ferie, JOURS_FERIES_FIXES
    if est_jour_ferie(date.today()):
        # Ne pas marquer d'absence
"""
from datetime import date

from hijridate import Gregorian as HijriGregorian, Hijri

# =============================================================================
# Jours fériés fixes (grégoriens)
# =============================================================================

JOURS_FERIES_FIXES = [
    (1, 1),     # 1er janvier    → Jour de l'An
    (1, 5),     # 1er mai        → Fête du Travail
    (30, 7),    # 30 juillet     → Fête du Trône
    (6, 11),    # 6 novembre     → Anniversaire de la Marche Verte
    (18, 11),   # 18 novembre    → Fête de l'Indépendance
]

# =============================================================================
# Jours fériés mobiles (hégiriens) — définition par (mois_hijri, jour_hijri)
# =============================================================================

# Mois hégiriens (1-indexed) :
#   1  = Muharram
#   3  = Rabi' al-awwal
#   10 = Shawwal
#   12 = Dhu al-Hijjah

JOURS_FERIES_MOBILES = [
    (1, 1),     # 1er Moharram → Nouvel An hégirien
    (3, 12),    # 12 Rabi' al-awwal → Aid Al Mawlid Annabaoui
    (10, 1),    # 1 Shawwal → Aïd al-Fitr (jour 1)
    (10, 2),    # 2 Shawwal → Aïd al-Fitr (jour 2)
    (12, 10),   # 10 Dhu al-Hijjah → Aïd al-Adha (jour 1)
    (12, 11),   # 11 Dhu al-Hijjah → Aïd al-Adha (jour 2)
]


def est_jour_ferie(jour: date) -> bool:
    """Retourne True si *jour* est un jour férié marocain (fixe ou mobile).

    Args:
        jour: date grégorienne à tester.

    Returns:
        bool: True si la date correspond à un jour férié marocain.
    """
    # 1) Vérifier les jours fixes grégoriens
    for mois, jour_mois in JOURS_FERIES_FIXES:
        if jour.month == jour_mois and jour.day == mois:
            return True

    # 2) Convertir la date grégorienne → date hégirienne
    try:
        hijri = HijriGregorian(jour.year, jour.month, jour.day).to_hijri()
    except (ValueError, OverflowError):
        # En cas de date hors limites (ex: année < 1880), on skip
        return False

    for mois_hijri, jour_hijri in JOURS_FERIES_MOBILES:
        if hijri.month == mois_hijri and hijri.day == jour_hijri:
            return True

    return False


def lister_jours_feries(annee: int) -> list[date]:
    """Génère la liste de tous les jours fériés marocains pour une année donnée.

    Args:
        annee: Année grégorienne (ex: 2024).

    Returns:
        Liste des dates fériées (``datetime.date``) pour cette année.
    """
    jours = []

    # Jours fixes
    for mois, jour_mois in JOURS_FERIES_FIXES:
        jours.append(date(annee, jour_mois, mois))

    # Jours mobiles : on convertit chaque jour hégirien en grégorien
    # L'année hégirienne n'est pas alignée sur l'année grégorienne, donc on
    # doit scanner l'année grégorienne À L'ENVERS : pour chaque (mois_h, jour_h)
    # on cherche s'il existe une date grégorienne dans l'année *annee* qui
    # corresponde. La méthode la plus fiable est de parcourir Hijri → Gregorian
    # en se basant sur l'estimation du mois hégirien correspondant.
    #
    # On utilise une heuristique : l'année hégirienne décale d'environ 11 jours/an.
    # On calcule une année hégirienne approximative, puis on balaie autour.
    # Approximation : annee_hijri ≈ (annee_gregorienne - 622) * 33/32
    annee_hijri_approx = int((annee - 622) * 33 / 32)

    for offset in range(-2, 3):  # ±2 ans pour couvrir le décalage
        hy = annee_hijri_approx + offset
        for mois_h, jour_h in JOURS_FERIES_MOBILES:
            try:
                h = Hijri(hy, mois_h, jour_h)
                greg = h.to_gregorian()
                if greg.year == annee:
                    jours.append(greg)
            except (ValueError, OverflowError):
                continue

    # Dédupliquer et trier
    jours = sorted(set(jours))
    return jours
