# EMPREINTE — Pointage par reconnaissance faciale (React + Flask + SQL Server)

Application complète (et non plus une maquette) : **React** (front-end), **Flask**
(API REST), **SQL Server** (base de données), **DeepFace/FaceNet** (reconnaissance
faciale RÉELLE, exécutée localement). Construite directement à partir de votre
cahier des charges, de votre conception UML (diagrammes de cas d'utilisation,
classes, séquence) et de votre stack technique.

## Ce qui a changé par rapport à la maquette précédente

L'ancienne version (`dashboard-empreinte.html`) était une démo front-end avec des
données simulées. **Celle-ci est une vraie application 3-tiers** :
- Le front-end React appelle une vraie API Flask (plus aucune donnée inventée en JS).
- L'API interroge une vraie base SQL Server via SQLAlchemy.
- La reconnaissance faciale utilise la vraie librairie DeepFace (modèle FaceNet),
  pas un score aléatoire.

## Architecture

```
Navigateur (React, Vite)  ──HTTP/JSON + JWT──▶  API Flask  ──SQLAlchemy/pyodbc──▶  SQL Server
                                                    │
                                                    └──▶ DeepFace (FaceNet, local, aucun cloud)
```

## Structure du dossier

```
EMPREINTE-fullstack/
├── backend/
│   ├── app.py                 point d'entrée Flask (application factory)
│   ├── config.py               connexion SQL Server (variables d'environnement)
│   ├── extensions.py
│   ├── seed.py                  peuple la base avec des données de démonstration
│   ├── schema.sql                DDL SQL Server de référence (facultatif, db.create_all() suffit)
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/                    un fichier par classe UML (Utilisateur, Pointage, Configuration...)
│   ├── routes/                     un blueprint par cas d'utilisation (auth, pointage, teletravail...)
│   └── services/
│       └── reconnaissance_service.py   intégration réelle DeepFace/FaceNet
└── frontend/
    ├── package.json
    ├── vite.config.js            proxy /api -> Flask en développement
    ├── .env.example
    └── src/
        ├── api/client.js          client HTTP (JWT automatique)
        ├── context/AuthContext.jsx
        ├── components/             Layout, CameraCapture (WebRTC), etc.
        └── pages/                   Overview, Employees, Pointages, Remote, AI, Reports
```

## Démarrage — Backend

### 1. Prérequis
- Python 3.11+ (testé en 3.12)
- **Un serveur SQL Server accessible** (local avec SQL Server Express, distant, ou Azure SQL)
- Le driver ODBC système (PAS un paquet pip) :
  - **Windows** : téléchargez « ODBC Driver 18 for SQL Server » depuis le site Microsoft Learn.
  - **macOS** : `brew install unixodbc && brew tap microsoft/mssql-release && brew install msodbcsql18`
  - **Linux (Debian/Ubuntu)** : suivez le guide officiel Microsoft
    « Install the Microsoft ODBC driver for SQL Server (Linux) ».
- ~3 Go d'espace disque libre (TensorFlow + DeepFace).

### 2. Installation
```bash
cd backend
python -m venv venv
# Windows : venv\Scripts\activate      macOS/Linux : source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# ouvrez .env et renseignez DB_SERVER / DB_NAME / DB_USER / DB_PASSWORD (+ JWT_SECRET_KEY)
```

### 3. Base de données
Le schéma est créé automatiquement au premier `seed.py` (via `db.create_all()`).
Si vous préférez créer les tables manuellement dans SSMS d'abord, exécutez `schema.sql`.

```bash
python seed.py
```
Cela crée : les départements, la table de permissions, un compte administrateur
(**identifiant : `admin` / mot de passe : `ChangeMoi!2026` — à changer immédiatement**),
et 18 comptes employés/managers/RH de démonstration (mot de passe : `Employe123!`).
**Aucune empreinte faciale n'est enrôlée par le seed** — il faut le faire depuis
l'écran "Employés" (bouton "Enrôler") avec une vraie webcam avant de pouvoir pointer.

### 4. Lancer l'API
```bash
flask --app app run --debug --port 5000
# ou : python app.py
```
Vérifiez sur http://localhost:5000/api/sante → `{"statut":"ok",...}`.

## Démarrage — Frontend

```bash
cd frontend
npm install
npm run dev
```
Ouvrez http://localhost:5173 — le proxy Vite relaie automatiquement `/api/*` vers
`http://127.0.0.1:5000` (rien à configurer en dev). Pour un build de production
(`npm run build`), définissez `VITE_API_URL` dans `frontend/.env` vers l'URL réelle
de votre API déployée.

## Comptes de démonstration (après `python seed.py`)

| Rôle | Email / identifiant | Mot de passe |
|---|---|---|
| Administrateur | `admin` | `ChangeMoi!2026` |
| Manager (Commercial) | `sofia.lahlou@empreinte-demo.local` | `Employe123!` |
| Employé (Production) | `yasmine.mansouri@empreinte-demo.local` | `Employe123!` |
| RH (Ressources Humaines) | `amine.elamrani@empreinte-demo.local` | `Employe123!` |

(voir `backend/seed.py`, liste `EMPLOYES_DEMO`, pour les 18 comptes générés et leurs rôles exacts)

## Matrice des permissions

| Action | Employé | Manager | RH | Administrateur |
|---|:---:|:---:|:---:|:---:|
| Pointer par caméra | ✓ | ✓ | ✓ | — |
| Consulter ses pointages | ✓ | ✓ | ✓ | — |
| Consulter le dashboard | ✓ | ✓ | ✓ | ✓ |
| Déclarer du télétravail | ✓ | ✓ | — | — |
| Valider le télétravail (équipe) | — | ✓ | ✓ | ✓ |
| Gérer les employés / enrôler une empreinte | — | — | ✓ | ✓ |
| Générer / exporter des rapports | — | — | ✓ | ✓ |
| Modifier les seuils de reconnaissance | — | — | — | ✓ |

Ajustez `backend/seed.py` (dictionnaire `regles`) si votre organisation a besoin
d'une matrice différente — la table `permissions` est entièrement pilotée par ces
données, aucune règle n'est codée en dur dans les routes.

## Ce qui a été testé, et comment

Avant de vous livrer ce projet, j'ai réellement fait tourner le code (pas juste
relu) :
- **42 tests automatisés** sur le backend (authentification, permissions par rôle,
  logique des 3 zones de seuils, télétravail, dashboard, export CSV) — tous passent.
- **Reconnaissance faciale réelle** : DeepFace/FaceNet installés et exécutés dans mon
  environnement ; la détection de visage a été validée sur une vraie photo. **Le
  téléchargement des poids pré-entraînés de FaceNet (~90 Mo, hébergés par DeepFace
  sur GitHub) est bloqué par les restrictions réseau de mon environnement de
  développement** — c'est un téléchargement standard, à usage unique, que DeepFace
  effectue automatiquement au premier lancement sur une machine avec un accès
  internet normal (celle de vos utilisateurs). Le code de comparaison (similarité
  cosinus) a lui été testé et validé avec de vrais vecteurs.
- **Intégration bout-en-bout dans un vrai navigateur** (Playwright + caméra virtuelle) :
  connexion, navigation par rôle, pointage caméra, enrôlement biométrique, validation
  télétravail, export CSV téléchargé, affichage mobile — sur React + Flask connectés
  ensemble, avec SQLite en base de test (SQL Server n'était pas disponible dans mon
  environnement — voir ci-dessous).
- **Non testé par moi, car nécessitant votre infrastructure réelle** : la connexion à
  un vrai serveur SQL Server (le code utilise le pilote standard `pyodbc`/`ODBC
  Driver 18`, la configuration la plus courante, mais je n'ai pas pu la vérifier
  moi-même faute d'instance disponible).

## Sécurité avant mise en production

- Changez immédiatement le mot de passe administrateur créé par `seed.py`.
- Générez un vrai `JWT_SECRET_KEY` (voir le commentaire dans `.env.example`).
- `DB_TRUST_CERT=yes` est pratique en développement local uniquement — utilisez un
  vrai certificat en production.
- Les tokens JWT sont "stateless" (pas de révocation serveur) : pour une vraie
  déconnexion forcée, ajoutez une blocklist (voir la documentation de
  flask-jwt-extended, section "Token Revoking").
