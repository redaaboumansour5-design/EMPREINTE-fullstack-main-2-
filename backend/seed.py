"""
seed.py
---------
Peuple la base SQL Server avec des données de démonstration cohérentes :
départements, permissions, comptes (administrateur + employés/managers/RH),
configuration des seuils, et quelques pointages/demandes de télétravail.

Usage :
    flask --app app shell   # puis, dans le shell :  exec(open('seed.py').read())
ou directement :
    python seed.py

ATTENTION : ce script est idempotent-safe pour les tables de référence
(départements/permissions) mais NE DOIT être lancé qu'une fois sur une base
vierge pour les comptes (les emails/matricules sont uniques).
"""
from datetime import date, datetime, timedelta

from app import create_app
from extensions import db
from models import (
    Administrateur, Departement, Utilisateur, Permission,
    Configuration, Pointage, ReconnaissanceFaciale, Teletravail, Conge,
)

DEPARTEMENTS = ["Direction", "Ressources Humaines", "Finance", "IT", "Commercial", "Production"]

POSTES = {
    "Direction": ["Directeur Général", "Directrice Adjointe"],
    "Ressources Humaines": ["Chargée RH", "Responsable Recrutement", "Gestionnaire Paie"],
    "Finance": ["Comptable", "Contrôleur de Gestion", "Analyste Financier"],
    "IT": ["Développeur", "Administrateur Systèmes", "Support Technique"],
    "Commercial": ["Chargé de Clientèle", "Responsable Commercial", "Business Developer"],
    "Production": ["Chef d'Équipe", "Technicien", "Opérateur"],
}

EMPLOYES_DEMO = [
    # (prenom, nom, departement, poste, role)
    ("Sofia", "Lahlou", "Commercial", "Responsable Commercial", "manager"),
    ("Yasmine", "Mansouri", "Production", "Technicien", "employe"),
    ("Amine", "Ziani", "Ressources Humaines", "Responsable Recrutement", "employe"),
    ("Nadia", "Berrada", "Finance", "Comptable", "employe"),
    ("Nour", "Naciri", "Direction", "Directrice Adjointe", "manager"),
    ("Ilyas", "Bouzid", "Direction", "Directrice Adjointe", "manager"),
    ("Rania", "El Ouazzani", "Finance", "Comptable", "employe"),
    ("Omar", "Lahlou", "IT", "Administrateur Systèmes", "employe"),
    ("Asmaa", "Benali", "Finance", "Contrôleur de Gestion", "employe"),
    ("Yassine", "El Ouazzani", "Production", "Technicien", "manager"),
    ("Amine", "El Amrani", "Ressources Humaines", "Chargée RH", "rh"),
    ("Hind", "Alaoui", "Finance", "Comptable", "employe"),
    ("Sara", "Cherkaoui", "Finance", "Contrôleur de Gestion", "manager"),
    ("Ghita", "Idrissi", "IT", "Administrateur Systèmes", "employe"),
    ("Rania", "Benali", "Ressources Humaines", "Gestionnaire Paie", "rh"),
    ("Bilal", "Alaoui", "IT", "Développeur", "employe"),
    ("Adam", "Ait Ali", "Ressources Humaines", "Responsable Recrutement", "employe"),
    ("Salma", "El Amrani", "Ressources Humaines", "Chargée RH", "employe"),
]


def creer_departements():
    depts = {}
    for nom in DEPARTEMENTS:
        d = Departement.query.filter_by(nom=nom).first()
        if d is None:
            d = Departement(nom=nom)
            db.session.add(d)
        depts[nom] = d
    db.session.commit()
    return depts


def creer_permissions():
    """Table plate (rôle, action) — reflète les use-cases par espace."""
    regles = {
        "employe": ["pointer", "declarer_teletravail", "declarer_conge", "consulter_ses_pointages", "consulter_dashboard"],
        "manager": ["consulter_equipe", "valider_teletravail", "valider_conge", "consulter_dashboard", "valider_pointage"],
        "rh": ["gerer_employes", "consulter_dashboard", "generer_rapports", "exporter", "valider_pointage", "valider_teletravail", "valider_conge"],
    }
    for role, actions in regles.items():
        for action in actions:
            if not Permission.query.filter_by(nom_role=role, action_autorisee=action).first():
                db.session.add(Permission(nom_role=role, action_autorisee=action))
    db.session.commit()


def creer_administrateur():
    if Administrateur.query.filter_by(identifiant_admin="admin").first():
        return
    admin = Administrateur(identifiant_admin="admin", nom_complet="Administrateur Système")
    admin.set_password("admin")
    db.session.add(admin)
    db.session.commit()
    print("Administrateur créé -> identifiant: admin / mot de passe: admin")


def creer_employes(depts):
    utilisateurs = []
    for i, (prenom, nom, dept_nom, poste, role) in enumerate(EMPLOYES_DEMO):
        email = f"{prenom.lower()}.{nom.lower().replace(' ', '')}@empreinte-demo.local"
        if Utilisateur.query.filter_by(email=email).first():
            continue
        u = Utilisateur(
            matricule=f"EMP-{1000 + i * 7}",
            nom=nom, prenom=prenom, email=email,
            telephone=f"06{10000000 + i * 37 % 89999999:08d}",
            role=role, poste=poste,
            # pour la démo : autoriser le télétravail sur une partie des employés
            teletravail_autorise=(i % 3 == 0),
            date_embauche=date(2021, 1, 1) + timedelta(days=i * 47),
            departement_id=depts[dept_nom].id,
        )

        u.set_password("Employe123!")
        db.session.add(u)
        utilisateurs.append(u)
    db.session.commit()

    # désigne un responsable par département (premier manager trouvé)
    for dept_nom, dept in depts.items():
        manager = next((u for u in utilisateurs if u.departement_id == dept.id and u.role == "manager"), None)
        if manager:
            dept.responsable_id = manager.id
    db.session.commit()
    return utilisateurs


def creer_configuration():
    Configuration.instance({
        "SEUIL_MIN_DEFAUT": 0.45,
        "SEUIL_MAX_DEFAUT": 0.75,
        "SEUIL_DISTANCE_DEFAUT": 1.0,
        "MODELE_RECONNAISSANCE": "Facenet",
    })


def creer_donnees_demo(utilisateurs):
    """Quelques pointages et demandes de télétravail pour visualiser le dashboard."""
    aujourd_hui = datetime.utcnow().replace(hour=8, minute=30, second=0, microsecond=0)
    for i, u in enumerate(utilisateurs[:12]):
        if u.pointages:
            continue
        score = 0.6 + (i % 5) * 0.08
        statut = "VALIDE" if score >= 0.75 else ("EN_ATTENTE" if score >= 0.45 else "REJETE")
        db.session.add(Pointage(
            utilisateur_id=u.id,
            date_heure=aujourd_hui + timedelta(minutes=i * 6),
            type="ENTREE",
            mode=(i % 4 == 0),
            methode_validation="AUTOMATIQUE" if statut == "VALIDE" else "MANUELLE_RH",
            statut=statut,
            score_confiance=score,
        ))

    if utilisateurs:
        db.session.add(Teletravail(
            utilisateur_id=utilisateurs[1].id,
            date_debut=date.today() + timedelta(days=3),
            date_fin=date.today() + timedelta(days=5),
            motif="Garde d'enfant",
            statut="SOUMISE",
        ))
        db.session.add(Conge(
            utilisateur_id=utilisateurs[2].id,
            date_debut=date.today() + timedelta(days=1),
            date_fin=date.today() + timedelta(days=2),
            motif="Congé personnel",
            statut="APPROUVE",
        ))
    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        depts = creer_departements()
        creer_permissions()
        creer_administrateur()
        utilisateurs = creer_employes(depts)
        creer_configuration()
        creer_donnees_demo(Utilisateur.query.all())
        print(f"Seed terminé : {Utilisateur.query.count()} utilisateurs, "
              f"{Departement.query.count()} départements, "
              f"{Pointage.query.count()} pointages.")
        print("NOTE : aucune empreinte faciale n'est enrôlée par ce script — "
              "utilisez POST /api/employes/<id>/empreinte avec une vraie photo "
              "avant de tester /api/pointage/scan.")


if __name__ == "__main__":
    main()
