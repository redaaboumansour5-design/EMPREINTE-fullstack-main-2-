"""
services/reconnaissance_service.py
------------------------------------
Implémentation RÉELLE de la reconnaissance faciale avec DeepFace / FaceNet
(conforme à stack.jpeg : "DeepFace (FaceNet) — Exécution locale de la
reconnaissance faciale, calcul des vecteurs (embeddings) et comparaison
biométrique").

Correspond aux méthodes de la classe `ReconnaissanceFaciale` :
    +capturerVisage(img) : void      -> generer_embedding()
    +comparerVisage(img) : float     -> comparer()  (similarité cosinus)

Toute l'exécution est LOCALE (aucun appel à une API cloud tierce) : le
premier appel télécharge une seule fois les poids pré-entraînés du modèle
(~90 Mo, hébergés par le projet DeepFace sur GitHub) puis les met en cache
dans ~/.deepface/weights — comportement standard de la librairie.
"""
from __future__ import annotations

import base64
import io
import logging
import re
from dataclasses import dataclass

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# L'import de `deepface` (qui initialise TensorFlow) est VOLONTAIREMENT différé
# jusqu'au premier appel réel de generer_embedding() — pas fait au chargement
# du module. Ainsi, le démarrage de l'API et les endpoints qui n'ont pas besoin
# de reconnaissance faciale (santé, auth, dashboard...) restent rapides ; le
# coût (quelques secondes) n'est payé qu'à la première capture caméra.
_DeepFace = None
DEEPFACE_DISPONIBLE = None  # None = pas encore testé ; True/False une fois résolu
_import_error = None


def _charger_deepface():
    global _DeepFace, DEEPFACE_DISPONIBLE, _import_error
    if DEEPFACE_DISPONIBLE is not None:
        return
    try:
        from deepface import DeepFace as DF
        _DeepFace = DF
        DEEPFACE_DISPONIBLE = True
    except Exception as exc:  # pragma: no cover - environnement sans DeepFace installé
        DEEPFACE_DISPONIBLE = False
        _import_error = exc


class VisageNonDetecteError(Exception):
    """Aucun visage n'a été détecté dans l'image transmise par la caméra (WebRTC)."""


class ServiceReconnaissanceIndisponibleError(Exception):
    """DeepFace/TensorFlow n'est pas installé dans cet environnement."""


@dataclass
class ResultatEmbedding:
    embedding: list[float]
    modele: str
    zone_visage: dict


def _decode_data_url(image_data: str) -> Image.Image:
    """
    Décode une image envoyée par le front-end React (capture WebRTC -> canvas
    -> toDataURL()), typiquement au format 'data:image/jpeg;base64,/9j/4AAQ...'.
    Accepte aussi du base64 brut sans préfixe, par souplesse.
    """
    match = re.match(r"^data:image/\w+;base64,(.*)$", image_data)
    raw_b64 = match.group(1) if match else image_data
    try:
        image_bytes = base64.b64decode(raw_b64)
    except Exception as exc:
        raise ValueError("Image base64 invalide.") from exc
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def _ensure_deepface():
    _charger_deepface()
    if not DEEPFACE_DISPONIBLE:
        raise ServiceReconnaissanceIndisponibleError(
            "DeepFace n'est pas installé. Exécutez : pip install deepface tf-keras"
        ) from _import_error


def generer_embedding(image_data: str, model_name: str = "Facenet", detector_backend: str = "opencv") -> ResultatEmbedding:
    """
    +capturerVisage(img) — détecte le visage et calcule son embedding FaceNet.
    Utilisé (a) à l'inscription d'un employé pour enregistrer son empreinte de
    référence, et (b) à chaque pointage pour obtenir l'embedding "candidat".
    """
    _ensure_deepface()
    pil_image = _decode_data_url(image_data)
    img_array = np.array(pil_image)

    try:
        resultats = _DeepFace.represent(
            img_path=img_array,
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=True,
        )
    except ValueError as exc:
        message = str(exc)
        # DeepFace lève un ValueError explicite quand aucun visage n'est trouvé
        if "face could not be detected" in message.lower():
            raise VisageNonDetecteError(
                "Aucun visage détecté dans l'image. Rapprochez-vous de la caméra "
                "et assurez un bon éclairage."
            ) from exc
        # DeepFace lève aussi un ValueError si le téléchargement des poids du
        # modèle a échoué/été interrompu (1er lancement sans connexion stable,
        # ou fichier de poids corrompu) — à distinguer clairement d'un 500 brut.
        if "pre-trained weights" in message.lower() or "weight" in message.lower():
            raise ServiceReconnaissanceIndisponibleError(
                "Impossible de charger le modèle de reconnaissance faciale (téléchargement "
                "des poids interrompu ou absent). Vérifiez la connexion internet du serveur "
                "puis réessayez ; supprimez ~/.deepface/weights en cas de fichier corrompu."
            ) from exc
        raise

    if len(resultats) > 1:
        logger.warning("Plusieurs visages détectés (%d) — le premier est utilisé.", len(resultats))

    principal = resultats[0]
    return ResultatEmbedding(
        embedding=principal["embedding"],
        modele=model_name,
        zone_visage=principal.get("facial_area", {}),
    )


def comparer(embedding_reference: list[float], embedding_candidat: list[float]) -> float:
    """
    +comparerVisage(img) : float — similarité cosinus entre l'empreinte de
    référence (enregistrée en base) et l'embedding du visage capturé au
    pointage. Retourne un score dans [0, 1] (1 = identique).
    """
    a = np.asarray(embedding_reference, dtype=np.float64)
    b = np.asarray(embedding_candidat, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError(
            f"Dimensions d'embeddings incompatibles ({a.shape} vs {b.shape}) — "
            "les deux images doivent utiliser le même modèle (ex: Facenet)."
        )
    norme_a, norme_b = np.linalg.norm(a), np.linalg.norm(b)
    if norme_a == 0 or norme_b == 0:
        return 0.0
    similarite_cosinus = float(np.dot(a, b) / (norme_a * norme_b))
    # ramène [-1, 1] -> [0, 1] pour un score de confiance plus intuitif côté UI
    score = (similarite_cosinus + 1) / 2
    return max(0.0, min(1.0, score))
