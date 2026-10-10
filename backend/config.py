"""
config.py
---------
Configuration de l'application. Conformément au choix du projet, la base de
données cible est EXCLUSIVEMENT Microsoft SQL Server (aucun repli SQLite).

Toutes les valeurs sensibles viennent des variables d'environnement (voir
.env.example) — ne jamais committer de vrais identifiants.
"""
import os
import urllib.parse


class ConfigurationError(RuntimeError):
    """Levée si une variable d'environnement obligatoire est absente."""


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigurationError(
            f"Variable d'environnement manquante : {name}. "
            f"Copiez .env.example vers .env et renseignez vos identifiants SQL Server."
        )
    return value


def build_sqlserver_uri() -> str:
    """
    Construit l'URI SQLAlchemy pour SQL Server via pyodbc.

    Variables attendues (.env) :
      DB_SERVER   ex: localhost\\SQLEXPRESS  ou  monserveur.database.windows.net
      DB_NAME     ex: EmpreintePointage
      DB_USER     ex: sa
      DB_PASSWORD
      DB_DRIVER   ex: "ODBC Driver 18 for SQL Server"  (par défaut)
      DB_ENCRYPT  "yes"/"no" (par défaut "yes" — requis par le driver 18+)
      DB_TRUST_CERT "yes"/"no" (par défaut "yes", pratique en développement local)
    """
    server = _require("DB_SERVER")
    database = _require("DB_NAME")
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    driver = os.environ.get("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    encrypt = os.environ.get("DB_ENCRYPT", "yes")
    trust_cert = os.environ.get("DB_TRUST_CERT", "yes")

    if user and password:
        auth_params = f"UID={user};PWD={password};"
    else:
        auth_params = "Trusted_Connection=yes;"

    odbc_params = urllib.parse.quote_plus(
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"{auth_params}"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={trust_cert};"
    )
    return f"mssql+pyodbc:///?odbc_connect={odbc_params}"


class Config:
    # Ne PAS appeler build_sqlserver_uri() au chargement du module : ça lèverait
    # une exception dès `import config` même pour des commandes qui n'ont pas besoin
    # de la DB (ex: `flask --help`). On la résout au moment de create_app().
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-moi-en-production")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("JWT_EXPIRES_SECONDS", 8 * 3600))

    # Reconnaissance faciale (classe Configuration du diagramme — valeurs de
    # secours utilisées uniquement si la table `configuration` est vide au 1er démarrage)
    SEUIL_MIN_DEFAUT = float(os.environ.get("SEUIL_MIN_DEFAUT", 0.45))
    SEUIL_MAX_DEFAUT = float(os.environ.get("SEUIL_MAX_DEFAUT", 0.75))
    MODELE_RECONNAISSANCE = os.environ.get("MODELE_RECONNAISSANCE", "Facenet")
    DETECTOR_BACKEND = os.environ.get("DETECTOR_BACKEND", "opencv")

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
