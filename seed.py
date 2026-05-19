# seed.py - IUAInsight 2023-2024
# Dataset complet : 400 étudiants, 6 filières, ML-ready
# Corrigé : 30 crédits/semestre, notes entières ou x.5

from faker import Faker
import random
from datetime import date
from werkzeug.security import generate_password_hash

from IUAInsight import app, db
from IUAInsight.models import (
    Nationalite,
    Filiere,
    Specialite,
    Niveau,
    NiveauFiliere,
    Semestre,
    UE,
    AnneeScolaire,
    Professeur,
    Matiere,
    Etudiant,
    Inscription,
    Resultat,
    ResultatUE,
    Note,
    Session,
    Absence,
    Alerte,
    Administrateur_sy,
    Respo_peda,
    creer_ou_maj_dette,
)

fake = Faker('fr_FR')
random.seed(42)

NB_ETUDIANTS = 400

# ─────────────────────────────────────────────────────────────
# PROFILS DE PERFORMANCE (pour ML)
# ─────────────────────────────────────────────────────────────
PROFILS = {
    "excellent":  {"range": (14.0, 18.5), "prob": 0.15},
    "moyen":      {"range": (10.0, 13.5), "prob": 0.45},
    "faible":     {"range": (6.0,   9.5), "prob": 0.20},
    "critique":   {"range": (2.0,   5.5), "prob": 0.10},
    "abandon":    {"range": (0,      0),  "prob": 0.05},
    "redoublant": {"range": (4.0,   8.0), "prob": 0.05},
}


def choose_profile():
    r = random.random()
    cumulative = 0.0
    for profile, data in PROFILS.items():
        cumulative += data["prob"]
        if r <= cumulative:
            return profile
    return "moyen"


def random_note(profile):
    """Retourne une note entière ou avec .5 (multiples de 0.5)."""
    if profile == "abandon":
        return None
    lo, hi = PROFILS[profile]["range"]
    # Générer un multiple de 0.5 dans [lo, hi]
    lo_idx = int(lo * 2)
    hi_idx = int(hi * 2)
    val = random.randint(lo_idx, hi_idx) / 2.0
    return val


def round_note(val):
    """Arrondit une note au multiple de 0.5 le plus proche, clampé entre 0 et 20."""
    if val is None:
        return None
    val = max(0.0, min(val, 20.0))
    return round(val * 2) / 2.0


def mention_from_average(avg):
    if avg is None:
        return None
    if avg >= 16:
        return "Très Bien"
    if avg >= 14:
        return "Bien"
    if avg >= 12:
        return "Assez Bien"
    if avg >= 10:
        return "Passable"
    return None


# ─────────────────────────────────────────────────────────────
# RESET
# ─────────────────────────────────────────────────────────────
def reset_database():
    print("Suppression des anciennes données...")
    tables = [
        Absence, Note, ResultatUE, Resultat, Inscription, Etudiant,
        Matiere, Professeur, UE, Semestre, NiveauFiliere,
        Specialite, Filiere, Niveau, Nationalite,
        Session, Alerte, AnneeScolaire,
        Administrateur_sy, Respo_peda,
    ]
    for table in tables:
        table.query.delete()
    db.session.commit()
    print("Base réinitialisée.")


# ─────────────────────────────────────────────────────────────
# NATIONALITÉS
# ─────────────────────────────────────────────────────────────
def seed_nationalites():
    data = [
        ("Côte d'Ivoire", "CIV"),
        ("Sénégal",        "SEN"),
        ("Cameroun",       "CMR"),
        ("Mali",           "MLI"),
        ("Burkina Faso",   "BFA"),
        ("Guinée",         "GIN"),
        ("Bénin",          "BEN"),
        ("Togo",           "TGO"),
        ("Niger",          "NER"),
        ("Congo",          "COG"),
    ]
    objs = []
    for pays, code in data:
        obj = Nationalite(pays=pays, code_iso=code)
        db.session.add(obj)
        objs.append(obj)
    db.session.commit()
    print(f"  {len(objs)} nationalités générées")
    return objs


# ─────────────────────────────────────────────────────────────
# FILIÈRES
# ─────────────────────────────────────────────────────────────
def seed_filieres():
    noms = [
        "Informatique",
        "Gestion",
        "Finance Comptabilité",
        "Marketing",
        "DROIT",
        "Logistique",
    ]
    filieres = []
    for nom in noms:
        f = Filiere(nom_filiere=nom)
        db.session.add(f)
        filieres.append(f)
    db.session.commit()
    print(f"  {len(filieres)} filières générées")
    return filieres


# ─────────────────────────────────────────────────────────────
# SPÉCIALITÉS
# ─────────────────────────────────────────────────────────────
def seed_specialites(filieres):
    mapping = {
        "Informatique":         ["RIT", "MIAGE", "GI"],
        "Gestion":              ["GRH", "Management"],
        "Finance Comptabilité": ["Audit", "Finance"],
        "Marketing":            ["Marketing Digital", "Communication"],
        "DROIT":                ["Droit Public", "Droit Privé"],
        "Logistique":           ["Transport", "Supply Chain"],
    }
    all_specs = []
    for filiere in filieres:
        for nom in mapping.get(filiere.nom_filiere, []):
            obj = Specialite(nom_specialite=nom, id_filiere=filiere.id_filiere)
            db.session.add(obj)
            all_specs.append(obj)
    db.session.commit()
    print(f"  {len(all_specs)} spécialités générées")
    return all_specs


# ─────────────────────────────────────────────────────────────
# NIVEAUX
# ─────────────────────────────────────────────────────────────
def seed_niveaux():
    data = [("L1", 1), ("L2", 2), ("L3", 3)]
    niveaux = []
    for libelle, ordre in data:
        n = Niveau(
            libelle=libelle,
            ordre=ordre,
            credits_requis=60,
            credits_admission=47,
        )
        db.session.add(n)
        niveaux.append(n)
    db.session.commit()
    niveaux[0].niveau_suivant = niveaux[1]
    niveaux[1].niveau_suivant = niveaux[2]
    db.session.commit()
    print(f"  {len(niveaux)} niveaux générés")
    return niveaux


# ─────────────────────────────────────────────────────────────
# SEMESTRES
# ─────────────────────────────────────────────────────────────
def seed_semestres(niveaux):
    mapping = {
        "L1": [("S1", 1), ("S2", 2)],
        "L2": [("S3", 3), ("S4", 4)],
        "L3": [("S5", 5), ("S6", 6)],
    }
    semestres = []
    for niveau in niveaux:
        for lib, ordre in mapping[niveau.libelle]:
            s = Semestre(libelle=lib, ordre=ordre, id_niveau=niveau.id_niveau)
            db.session.add(s)
            semestres.append(s)
    db.session.commit()
    print(f"  {len(semestres)} semestres générés")
    return semestres


# ─────────────────────────────────────────────────────────────
# UNITÉS D'ENSEIGNEMENT (UE)
# CORRECTION : chaque semestre doit totaliser exactement 30 crédits
# → 2 UE par semestre : UE_a = 18 crédits, UE_b = 12 crédits
# Structure : (nom, code, credit_total, coeff, sem_libelle, compensable)
# ─────────────────────────────────────────────────────────────
_UES_PAR_FILIERE = {
    "Informatique": [
        ("Fondamentaux Informatique",  "UE-INFO-S1-1", 18, 1.5, "S1", True),
        ("Outils Transversaux S1",     "UE-INFO-S1-2", 12, 1.0, "S1", True),
        ("Programmation & Algo",       "UE-INFO-S2-1", 18, 2.0, "S2", True),
        ("Systèmes & Anglais",         "UE-INFO-S2-2", 12, 1.0, "S2", True),
        ("BDD & POO",                  "UE-INFO-S3-1", 18, 2.0, "S3", True),
        ("Réseaux & Méthodes",         "UE-INFO-S3-2", 12, 1.5, "S3", True),
        ("Infra & Sécurité",           "UE-INFO-S4-1", 18, 2.0, "S4", True),
        ("Dév. & Méthodes",            "UE-INFO-S4-2", 12, 1.5, "S4", True),
        ("IA & Data",                  "UE-INFO-S5-1", 18, 2.0, "S5", True),
        ("Cloud & Projet",             "UE-INFO-S5-2", 12, 1.0, "S5", True),
        ("Sécurité & Big Data",        "UE-INFO-S6-1", 18, 2.0, "S6", True),
        ("Projet & Entrepreneuriat",   "UE-INFO-S6-2", 12, 1.5, "S6", True),
    ],
    "Gestion": [
        ("Comptabilité & Éco S1",      "UE-GEST-S1-1", 18, 2.0, "S1", True),
        ("Droit & Outils S1",          "UE-GEST-S1-2", 12, 1.0, "S1", True),
        ("Comptabilité & Éco S2",      "UE-GEST-S2-1", 18, 2.0, "S2", True),
        ("RH & Outils S2",             "UE-GEST-S2-2", 12, 1.0, "S2", True),
        ("Management & Compta S3",     "UE-GEST-S3-1", 18, 2.0, "S3", True),
        ("Fiscalité & Droit S3",       "UE-GEST-S3-2", 12, 1.5, "S3", True),
        ("Management & Finance S4",    "UE-GEST-S4-1", 18, 2.0, "S4", True),
        ("Analyse & SIRH S4",          "UE-GEST-S4-2", 12, 1.0, "S4", True),
        ("Stratégie & Gestion S5",     "UE-GEST-S5-1", 18, 2.0, "S5", True),
        ("Entrepreneuriat S5",         "UE-GEST-S5-2", 12, 1.0, "S5", True),
        ("Stratégie & Contrôle S6",    "UE-GEST-S6-1", 18, 2.0, "S6", True),
        ("Stage & Innovation S6",      "UE-GEST-S6-2", 12, 1.5, "S6", True),
    ],
    "Finance Comptabilité": [
        ("Comptabilité & Math S1",     "UE-FICO-S1-1", 18, 2.0, "S1", True),
        ("Droit & Bureautique S1",     "UE-FICO-S1-2", 12, 1.0, "S1", True),
        ("Comptabilité & Math S2",     "UE-FICO-S2-1", 18, 2.0, "S2", True),
        ("Tréso & Fiscalité S2",       "UE-FICO-S2-2", 12, 1.0, "S2", True),
        ("Compta Sociétés & Analyse",  "UE-FICO-S3-1", 18, 2.0, "S3", True),
        ("Fiscalité & Contrôle S3",    "UE-FICO-S3-2", 12, 1.5, "S3", True),
        ("Compta & Analyse S4",        "UE-FICO-S4-1", 18, 2.0, "S4", True),
        ("Audit & Finance S4",         "UE-FICO-S4-2", 12, 1.5, "S4", True),
        ("Audit & Finance S5",         "UE-FICO-S5-1", 18, 2.0, "S5", True),
        ("Consolidation & IFRS S5",    "UE-FICO-S5-2", 12, 1.0, "S5", True),
        ("Stage & Planification S6",   "UE-FICO-S6-1", 18, 2.0, "S6", True),
        ("Risk & Contrôle S6",         "UE-FICO-S6-2", 12, 1.5, "S6", True),
    ],
    "Marketing": [
        ("Marketing Fondamental S1",   "UE-MKT-S1-1",  18, 2.0, "S1", True),
        ("Éco & Bureautique S1",       "UE-MKT-S1-2",  12, 1.0, "S1", True),
        ("Comportement & Mix S2",      "UE-MKT-S2-1",  18, 2.0, "S2", True),
        ("Vente & Statistiques S2",    "UE-MKT-S2-2",  12, 1.0, "S2", True),
        ("Marketing Stratégique S3",   "UE-MKT-S3-1",  18, 2.0, "S3", True),
        ("Digital & Droit S3",         "UE-MKT-S3-2",  12, 1.5, "S3", True),
        ("Stratégie & Digital S4",     "UE-MKT-S4-1",  18, 2.0, "S4", True),
        ("CRM & Etudes S4",            "UE-MKT-S4-2",  12, 1.5, "S4", True),
        ("Stratégie Commerciale S5",   "UE-MKT-S5-1",  18, 2.0, "S5", True),
        ("Stage & Commerce S5",        "UE-MKT-S5-2",  12, 1.5, "S5", True),
        ("Services & Plan S6",         "UE-MKT-S6-1",  18, 2.0, "S6", True),
        ("Innovation & Mémoire S6",    "UE-MKT-S6-2",  12, 1.0, "S6", True),
    ],
    "DROIT": [
        ("Fondamentaux Droit S1",      "UE-DRT-S1-1",  18, 2.0, "S1", True),
        ("Institutions & Méthodo S1",  "UE-DRT-S1-2",  12, 1.0, "S1", True),
        ("Droit Civil & Constit S2",   "UE-DRT-S2-1",  18, 2.0, "S2", True),
        ("Commerce & Éco S2",          "UE-DRT-S2-2",  12, 1.0, "S2", True),
        ("Obligations & Commerce S3",  "UE-DRT-S3-1",  18, 2.0, "S3", True),
        ("Administratif & Travail S3", "UE-DRT-S3-2",  12, 1.5, "S3", True),
        ("Obligations & Admin S4",     "UE-DRT-S4-1",  18, 2.0, "S4", True),
        ("Fiscal & OHADA S4",          "UE-DRT-S4-2",  12, 1.5, "S4", True),
        ("Droit des Affaires S5",      "UE-DRT-S5-1",  18, 2.0, "S5", True),
        ("Stage & International S5",   "UE-DRT-S5-2",  12, 1.5, "S5", True),
        ("Contrats & Arbitrage S6",    "UE-DRT-S6-1",  18, 2.0, "S6", True),
        ("Environnement & Mémoire S6", "UE-DRT-S6-2",  12, 1.0, "S6", True),
    ],
    "Logistique": [
        ("Fondamentaux Logistique S1", "UE-LOG-S1-1",  18, 2.0, "S1", True),
        ("Transport & Maths S1",       "UE-LOG-S1-2",  12, 1.0, "S1", True),
        ("Stocks & Transport S2",      "UE-LOG-S2-1",  18, 2.0, "S2", True),
        ("Droit & Informatique S2",    "UE-LOG-S2-2",  12, 1.0, "S2", True),
        ("Supply Chain S3",            "UE-LOG-S3-1",  18, 2.0, "S3", True),
        ("Douane & Achats S3",         "UE-LOG-S3-2",  12, 1.5, "S3", True),
        ("Supply Chain Int. S4",       "UE-LOG-S4-1",  18, 2.0, "S4", True),
        ("Lean & ERP S4",              "UE-LOG-S4-2",  12, 1.5, "S4", True),
        ("Optimisation S5",            "UE-LOG-S5-1",  18, 2.0, "S5", True),
        ("Stage & E-Logistique S5",    "UE-LOG-S5-2",  12, 1.5, "S5", True),
        ("Reverse & Transport S6",     "UE-LOG-S6-1",  18, 2.0, "S6", True),
        ("Innovation & Projet S6",     "UE-LOG-S6-2",  12, 1.0, "S6", True),
    ],
}

# Mapping position matière (0-29) → indice UE dans la liste de la filière
# 5 matières par semestre, 2 UE par semestre : 3 premières → UE_a, 2 suivantes → UE_b
_MAT_UE_MAPPING = {
    0: 0,  1: 0,  2: 0,  3: 1,  4: 1,    # S1
    5: 2,  6: 2,  7: 2,  8: 3,  9: 3,    # S2
    10: 4, 11: 4, 12: 4, 13: 5, 14: 5,   # S3
    15: 6, 16: 6, 17: 6, 18: 7, 19: 7,   # S4
    20: 8, 21: 8, 22: 8, 23: 9, 24: 9,   # S5
    25: 10, 26: 10, 27: 10, 28: 11, 29: 11,  # S6
}


def seed_ues(filieres, semestres):
    sem_by_lib = {s.libelle: s for s in semestres}
    fil_by_nom = {f.nom_filiere: f for f in filieres}
    all_ues = []
    ues_by_filiere = {}

    for fil_nom, ues_data in _UES_PAR_FILIERE.items():
        filiere    = fil_by_nom[fil_nom]
        ues_filiere = []
        for nom_ue, code_ue, credit_total, coeff, sem_lib, compensable in ues_data:
            sem = sem_by_lib[sem_lib]
            ue = UE(
                nom=nom_ue,
                code_ue=code_ue,
                credit_total=credit_total,
                coefficient=coeff,
                id_semestre=sem.id_semestre,
                compensable=compensable,
            )
            db.session.add(ue)
            ues_filiere.append(ue)
            all_ues.append(ue)
        ues_by_filiere[fil_nom] = ues_filiere

    db.session.commit()
    print(f"  {len(all_ues)} UE générées")
    return all_ues, ues_by_filiere


# ─────────────────────────────────────────────────────────────
# ANNÉE SCOLAIRE
# ─────────────────────────────────────────────────────────────
def seed_annee_scolaire():
    annee = AnneeScolaire(
        libelle="2023-2024",
        date_debut=date(2023, 9, 1),
        date_fin=date(2024, 7, 31),
        active=True,
    )
    db.session.add(annee)
    db.session.commit()
    print("  Année scolaire 2023-2024 créée")
    return annee


# ─────────────────────────────────────────────────────────────
# SESSIONS
# ─────────────────────────────────────────────────────────────
def seed_sessions():
    normale    = Session(libelle="Normale",    est_rattrapage=False)
    rattrapage = Session(libelle="Rattrapage", est_rattrapage=True)
    db.session.add(normale)
    db.session.add(rattrapage)
    db.session.commit()
    print("  2 sessions générées (Normale / Rattrapage)")
    return normale, rattrapage


# ─────────────────────────────────────────────────────────────
# PROFESSEURS (40)
# ─────────────────────────────────────────────────────────────
_PROFS_DATA = [
    ("Kouassi",    "Abdoulaye",   "Algorithmique & IA",          "Informatique"),
    ("Traoré",     "Ibrahim",     "Réseaux & Télécoms",           "Informatique"),
    ("Bamba",      "Souleymane",  "Base de Données",              "Informatique"),
    ("Diallo",     "Mamadou",     "Algorithmique",                "Informatique"),
    ("Coulibaly",  "Adama",       "Intelligence Artificielle",    "Informatique"),
    ("Koné",       "Yves",        "Génie Logiciel",               "Informatique"),
    ("Soro",       "Ladji",       "Sécurité Informatique",        "Informatique"),
    ("Ouattara",   "Drissa",      "Systèmes d'Information",      "Informatique"),
    ("Aké",        "Bertin",      "Mathématiques",                "Informatique"),
    ("N'Guessan",  "Bertrand",    "Statistiques",                 "Informatique"),
    ("Brou",       "Kouamé",      "Comptabilité Générale",        "Finance Comptabilité"),
    ("Gnangui",    "Adjoua",      "Finance",                      "Finance Comptabilité"),
    ("Touré",      "Bintou",      "Gestion Financière",           "Finance Comptabilité"),
    ("Sanogo",     "Korotoumou",  "Marketing",                    "Marketing"),
    ("Diabaté",    "Fatoumata",   "Marketing Stratégique",        "Marketing"),
    ("Konaté",     "Sékou",       "Droit des Affaires",           "DROIT"),
    ("Coulibaly",  "Mariam",      "Droit Public",                 "DROIT"),
    ("Fofana",     "Yacouba",     "Logistique",                   "Logistique"),
    ("Dosso",      "Tenin",       "Supply Chain",                 "Logistique"),
    ("Yao",        "Edmond",      "Économie",                     "Gestion"),
    ("Assoumou",   "Patricia",    "Gestion de Projet",            "Gestion"),
    ("Mensah",     "Kofi",        "Réseaux",                      "Informatique"),
    ("Atcho",      "Stéphane",    "Algorithmique Avancée",        "Informatique"),
    ("Kamagaté",   "Siaka",       "Systèmes Embarqués",           "Informatique"),
    ("Dembélé",    "Aminata",     "Audit",                        "Finance Comptabilité"),
    ("Keita",      "Moussa",      "Comptabilité Analytique",      "Finance Comptabilité"),
    ("Bagayoko",   "Awa",         "Finances Publiques",           "Finance Comptabilité"),
    ("Camara",     "Lamine",      "Droit Fiscal",                 "DROIT"),
    ("Sawadogo",   "Rasmané",     "Transport International",      "Logistique"),
    ("Zongo",      "Inoussa",     "Logistique Urbaine",           "Logistique"),
    ("Barry",      "Kadiatou",    "Commerce International",       "Gestion"),
    ("Sidibé",     "Boubacar",    "Management",                   "Gestion"),
    ("Touré",      "Abdramane",   "Entrepreneuriat",              "Gestion"),
    ("Coulibaly",  "Péné",        "Ressources Humaines",          "Gestion"),
    ("Silué",      "Moussa",      "Développement Web",            "Informatique"),
    ("Kourouma",   "Hawa",        "Business Intelligence",        "Informatique"),
    ("Kondé",      "Thierno",     "Machine Learning",             "Informatique"),
    ("Bah",        "Mamadou",     "Data Science",                 "Informatique"),
    ("Sow",        "Ibrahima",    "Cybersécurité",                "Informatique"),
    ("Ndiaye",     "Fatou",       "Communication",                "Marketing"),
]


def seed_professeurs(filieres):
    profs = []
    for nom, prenom, spec, fil_nom in _PROFS_DATA:
        email = (
            f"{prenom.lower().replace(' ', '.').replace('-', '.')}"
            f".{nom.lower().replace(' ', '')}@iua.ci"
        )
        tel = (
            f"+225 07 {random.randint(10, 99):02d} "
            f"{random.randint(10, 99):02d} "
            f"{random.randint(10, 99):02d}"
        )
        p = Professeur(
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=tel,
            specialite=spec,
        )
        db.session.add(p)
        profs.append(p)
    db.session.commit()
    print(f"  {len(profs)} professeurs générés")
    return profs


# ─────────────────────────────────────────────────────────────
# MATIÈRES (30 par filière = 180 total)
# CORRECTION : crédits par semestre = 30
# 5 matières par semestre, répartition :
#   UE_a (3 matières) : 8 + 8 + 8 = 24  → mais on vise UE_a=18 total
#   En pratique on répartit les crédits dans la matière directement :
#   UE_a : mat1=7, mat2=6, mat3=5  → total=18
#   UE_b : mat4=7, mat5=5          → total=12
#   Somme semestre = 18+12 = 30 ✓
#
# Structure : (nom, coeff, credit, sem_libelle)
# ─────────────────────────────────────────────────────────────
_MATIERES_PAR_FILIERE = {
    "Informatique": [
        # S1 — total 30 : UE_a (mat 0,1,2)=18 ; UE_b (mat 3,4)=12
        ("Introduction à l'Informatique",      1.5, 7, "S1"),   # idx 0
        ("Algorithmique I",                    2.0, 6, "S1"),   # idx 1
        ("Mathématiques I",                    2.0, 5, "S1"),   # idx 2  → UE_a=18
        ("Architecture des Ordinateurs",       1.5, 7, "S1"),   # idx 3
        ("Anglais Informatique I",             1.0, 5, "S1"),   # idx 4  → UE_b=12
        # S2 — total 30
        ("Algorithmique II",                   2.0, 7, "S2"),   # idx 5
        ("Programmation C",                    2.0, 6, "S2"),   # idx 6
        ("Mathématiques II",                   2.0, 5, "S2"),   # idx 7  → UE_a=18
        ("Systèmes d'Exploitation",            1.5, 7, "S2"),   # idx 8
        ("Anglais Informatique II",            1.0, 5, "S2"),   # idx 9  → UE_b=12
        # S3 — total 30
        ("Base de Données I",                  2.0, 7, "S3"),   # idx 10
        ("Programmation Orientée Objet",       2.0, 6, "S3"),   # idx 11
        ("Réseaux I",                          1.5, 5, "S3"),   # idx 12 → UE_a=18
        ("Statistiques Appliquées",            1.5, 7, "S3"),   # idx 13
        ("Gestion de Projet I",                1.0, 5, "S3"),   # idx 14 → UE_b=12
        # S4 — total 30
        ("Base de Données II",                 2.0, 7, "S4"),   # idx 15
        ("Réseaux II",                         2.0, 6, "S4"),   # idx 16
        ("Développement Web",                  1.5, 5, "S4"),   # idx 17 → UE_a=18
        ("Sécurité Informatique",              1.5, 7, "S4"),   # idx 18
        ("Méthodes Formelles",                 1.0, 5, "S4"),   # idx 19 → UE_b=12
        # S5 — total 30
        ("Intelligence Artificielle",          2.0, 7, "S5"),   # idx 20
        ("Machine Learning",                   2.0, 6, "S5"),   # idx 21
        ("Business Intelligence",              2.0, 5, "S5"),   # idx 22 → UE_a=18
        ("Cloud Computing",                    1.5, 7, "S5"),   # idx 23
        ("Gestion de Projet II",               1.0, 5, "S5"),   # idx 24 → UE_b=12
        # S6 — total 30
        ("Sécurité Avancée",                   2.0, 7, "S6"),   # idx 25
        ("Big Data",                           2.0, 6, "S6"),   # idx 26
        ("Systèmes Distribués",                1.5, 5, "S6"),   # idx 27 → UE_a=18
        ("Stage / Mémoire",                    3.0, 7, "S6"),   # idx 28
        ("Entrepreneuriat Tech",               1.0, 5, "S6"),   # idx 29 → UE_b=12
    ],
    "Gestion": [
        # S1 — total 30
        ("Comptabilité Générale I",            2.0, 7, "S1"),
        ("Microéconomie",                      2.0, 6, "S1"),
        ("Droit Commercial I",                 1.5, 5, "S1"),
        ("Mathématiques de Gestion",           1.5, 7, "S1"),
        ("Communication I",                    1.0, 5, "S1"),
        # S2 — total 30
        ("Comptabilité Générale II",           2.0, 7, "S2"),
        ("Macroéconomie",                      2.0, 6, "S2"),
        ("Gestion des Ressources Humaines I",  1.5, 5, "S2"),
        ("Statistiques de Gestion",            1.5, 7, "S2"),
        ("Informatique de Gestion",            1.0, 5, "S2"),
        # S3 — total 30
        ("Management des Organisations I",     2.0, 7, "S3"),
        ("Comptabilité Analytique I",          2.0, 6, "S3"),
        ("Fiscalité des Entreprises",          1.5, 5, "S3"),
        ("Marketing Fondamental",              1.5, 7, "S3"),
        ("Droit du Travail",                   1.0, 5, "S3"),
        # S4 — total 30
        ("Management des Organisations II",    2.0, 7, "S4"),
        ("Comptabilité Analytique II",         2.0, 6, "S4"),
        ("Gestion Financière I",               2.0, 5, "S4"),
        ("Analyse Financière",                 1.5, 7, "S4"),
        ("SIRH",                               1.0, 5, "S4"),
        # S5 — total 30
        ("Stratégie d'Entreprise I",          2.0, 7, "S5"),
        ("Gestion Financière II",              2.0, 6, "S5"),
        ("Entrepreneuriat",                    1.5, 5, "S5"),
        ("Contrôle de Gestion I",              2.0, 7, "S5"),
        ("Anglais des Affaires",               1.0, 5, "S5"),
        # S6 — total 30
        ("Stratégie d'Entreprise II",         2.0, 7, "S6"),
        ("Contrôle de Gestion II",             2.0, 6, "S6"),
        ("Stage Gestion",                      3.0, 5, "S6"),
        ("Développement Durable",              1.0, 7, "S6"),
        ("Management de l'Innovation",        1.5, 5, "S6"),
    ],
    "Finance Comptabilité": [
        # S1 — total 30
        ("Comptabilité Financière I",          2.0, 7, "S1"),
        ("Mathématiques Financières I",        2.0, 6, "S1"),
        ("Droit Comptable",                    1.5, 5, "S1"),
        ("Microéconomie Finance",              1.5, 7, "S1"),
        ("Bureautique",                        1.0, 5, "S1"),
        # S2 — total 30
        ("Comptabilité Financière II",         2.0, 7, "S2"),
        ("Mathématiques Financières II",       2.0, 6, "S2"),
        ("Gestion Trésorerie I",               1.5, 5, "S2"),
        ("Fiscalité I",                        1.5, 7, "S2"),
        ("Communication Financière",           1.0, 5, "S2"),
        # S3 — total 30
        ("Comptabilité des Sociétés I",        2.0, 7, "S3"),
        ("Analyse Financière I",               2.0, 6, "S3"),
        ("Fiscalité II",                       1.5, 5, "S3"),
        ("Contrôle Interne",                   1.5, 7, "S3"),
        ("Gestion Trésorerie II",              1.0, 5, "S3"),
        # S4 — total 30
        ("Comptabilité des Sociétés II",       2.0, 7, "S4"),
        ("Analyse Financière II",              2.0, 6, "S4"),
        ("Audit Comptable I",                  2.0, 5, "S4"),
        ("Finance de Marché I",                1.5, 7, "S4"),
        ("Droit Fiscal",                       1.0, 5, "S4"),
        # S5 — total 30
        ("Audit Comptable II",                 2.0, 7, "S5"),
        ("Finance de Marché II",               2.0, 6, "S5"),
        ("Evaluation d'Entreprise",           2.0, 5, "S5"),
        ("Consolidation des Comptes",          1.5, 7, "S5"),
        ("Normes IFRS",                        1.0, 5, "S5"),
        # S6 — total 30
        ("Stage Finance Comptabilité",         3.0, 7, "S6"),
        ("Planification Financière",           2.0, 6, "S6"),
        ("Risk Management",                    1.5, 5, "S6"),
        ("Contrôle de Gestion Avancé",         1.5, 7, "S6"),
        ("Mémoire Finance",                    1.0, 5, "S6"),
    ],
    "Marketing": [
        # S1 — total 30
        ("Introduction au Marketing",          2.0, 7, "S1"),
        ("Comportement du Consommateur I",     2.0, 6, "S1"),
        ("Microéconomie Marché",               1.5, 5, "S1"),
        ("Communication Commerciale I",        1.5, 7, "S1"),
        ("Bureautique MKT",                    1.0, 5, "S1"),
        # S2 — total 30
        ("Comportement du Consommateur II",    2.0, 7, "S2"),
        ("Marketing Mix",                      2.0, 6, "S2"),
        ("Techniques de Vente",                1.5, 5, "S2"),
        ("Statistiques Marketing",             1.5, 7, "S2"),
        ("Communication Commerciale II",       1.0, 5, "S2"),
        # S3 — total 30
        ("Marketing Stratégique I",            2.0, 7, "S3"),
        ("Marketing Digital I",                2.0, 6, "S3"),
        ("Etudes de Marché I",                 1.5, 5, "S3"),
        ("Droit de la Consommation",           1.5, 7, "S3"),
        ("E-Commerce",                         1.0, 5, "S3"),
        # S4 — total 30
        ("Marketing Stratégique II",           2.0, 7, "S4"),
        ("Marketing Digital II",               2.0, 6, "S4"),
        ("Gestion de la Relation Client",      2.0, 5, "S4"),
        ("Etudes de Marché II",                1.5, 7, "S4"),
        ("Branding",                           1.0, 5, "S4"),
        # S5 — total 30
        ("Stratégie Commerciale",              2.0, 7, "S5"),
        ("Social Media Marketing",             2.0, 6, "S5"),
        ("Commerce International MKT",        1.5, 5, "S5"),
        ("Marketing B2B",                      1.5, 7, "S5"),
        ("Stage Marketing",                    3.0, 5, "S5"),
        # S6 — total 30
        ("Marketing des Services",             2.0, 7, "S6"),
        ("Plan Marketing",                     2.0, 6, "S6"),
        ("Entrepreneuriat Commercial",         1.5, 5, "S6"),
        ("Innovation Marketing",               1.0, 7, "S6"),
        ("Mémoire Marketing",                  1.0, 5, "S6"),
    ],
    "DROIT": [
        # S1 — total 30
        ("Introduction au Droit",              2.0, 7, "S1"),
        ("Droit Civil I",                      2.0, 6, "S1"),
        ("Histoire du Droit",                  1.5, 5, "S1"),
        ("Institutions Politiques",            1.5, 7, "S1"),
        ("Méthodologie Juridique",             1.0, 5, "S1"),
        # S2 — total 30
        ("Droit Civil II",                     2.0, 7, "S2"),
        ("Droit Constitutionnel",              2.0, 6, "S2"),
        ("Droit Commercial I",                 1.5, 5, "S2"),
        ("Economie Générale",                  1.5, 7, "S2"),
        ("Langue Juridique",                   1.0, 5, "S2"),
        # S3 — total 30
        ("Droit des Obligations I",            2.0, 7, "S3"),
        ("Droit Commercial II",                2.0, 6, "S3"),
        ("Droit Administratif I",              1.5, 5, "S3"),
        ("Droit du Travail I",                 1.5, 7, "S3"),
        ("Procédure Civile",                   1.0, 5, "S3"),
        # S4 — total 30
        ("Droit des Obligations II",           2.0, 7, "S4"),
        ("Droit Administratif II",             2.0, 6, "S4"),
        ("Droit Fiscal",                       1.5, 5, "S4"),
        ("Droit du Travail II",                1.5, 7, "S4"),
        ("Droit OHADA",                        1.0, 5, "S4"),
        # S5 — total 30
        ("Droit des Sociétés",                 2.0, 7, "S5"),
        ("Droit Pénal des Affaires",           2.0, 6, "S5"),
        ("Droit International Privé",          1.5, 5, "S5"),
        ("Contentieux Administratif",          1.5, 7, "S5"),
        ("Stage Droit",                        3.0, 5, "S5"),
        # S6 — total 30
        ("Droit des Contrats Spéciaux",        2.0, 7, "S6"),
        ("Arbitrage Commercial",               2.0, 6, "S6"),
        ("Droit de l'Environnement",          1.5, 5, "S6"),
        ("Mémoire Droit",                      1.5, 7, "S6"),
        ("Clinique Juridique",                 1.0, 5, "S6"),
    ],
    "Logistique": [
        # S1 — total 30
        ("Introduction à la Logistique",       2.0, 7, "S1"),
        ("Gestion des Stocks I",               2.0, 6, "S1"),
        ("Transport Routier",                  1.5, 5, "S1"),
        ("Mathématiques Logistique",           1.5, 7, "S1"),
        ("Communication Logistique",           1.0, 5, "S1"),
        # S2 — total 30
        ("Gestion des Stocks II",              2.0, 7, "S2"),
        ("Transport Maritime",                 2.0, 6, "S2"),
        ("Entreposage et Manutention",         1.5, 5, "S2"),
        ("Droit des Transports",               1.5, 7, "S2"),
        ("Informatique Logistique",            1.0, 5, "S2"),
        # S3 — total 30
        ("Supply Chain Management I",          2.0, 7, "S3"),
        ("Transport Aérien",                   2.0, 6, "S3"),
        ("Douane et Commerce Ext.",            1.5, 5, "S3"),
        ("Gestion des Achats I",               1.5, 7, "S3"),
        ("Qualité et Certification",           1.0, 5, "S3"),
        # S4 — total 30
        ("Supply Chain Management II",         2.0, 7, "S4"),
        ("Logistique Internationale",          2.0, 6, "S4"),
        ("Gestion des Achats II",              1.5, 5, "S4"),
        ("Lean Management",                    1.5, 7, "S4"),
        ("ERP Logistique",                     1.0, 5, "S4"),
        # S5 — total 30
        ("Optimisation Logistique",            2.0, 7, "S5"),
        ("Logistique Urbaine",                 2.0, 6, "S5"),
        ("E-Logistique",                       1.5, 5, "S5"),
        ("Stratégie Achats",                   1.5, 7, "S5"),
        ("Stage Logistique",                   3.0, 5, "S5"),
        # S6 — total 30
        ("Reverse Logistique",                 2.0, 7, "S6"),
        ("Transport et Développement Durable", 2.0, 6, "S6"),
        ("Mémoire Logistique",                 2.0, 5, "S6"),
        ("Innovation Logistique",              1.0, 7, "S6"),
        ("Projet Logistique",                  1.0, 5, "S6"),
    ],
}

_PROF_IDX_BY_FILIERE = {
    "Informatique":         [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 22, 23, 34, 35, 36, 37, 38],
    "Gestion":              [19, 20, 31, 32, 33],
    "Finance Comptabilité": [10, 11, 12, 24, 25, 26],
    "Marketing":            [13, 14, 39],
    "DROIT":                [15, 16, 27],
    "Logistique":           [17, 18, 28, 29],
}


def seed_matieres(filieres, semestres, professeurs, ues_by_filiere):
    sem_by_lib = {s.libelle: s for s in semestres}
    fil_by_nom = {f.nom_filiere: f for f in filieres}
    all_matieres = []

    for fil_nom, mats in _MATIERES_PAR_FILIERE.items():
        filiere      = fil_by_nom[fil_nom]
        prof_indices = _PROF_IDX_BY_FILIERE.get(fil_nom, [0])
        ues_fil      = ues_by_filiere.get(fil_nom, [])

        for idx_mat, (nom_matiere, coeff, credit, sem_lib) in enumerate(mats):
            sem  = sem_by_lib[sem_lib]
            prof = professeurs[random.choice(prof_indices)]

            ue_idx = _MAT_UE_MAPPING.get(idx_mat)
            id_ue  = ues_fil[ue_idx].id_ue if (ue_idx is not None and ue_idx < len(ues_fil)) else None

            m = Matiere(
                nom_matiere=nom_matiere,
                coefficient=coeff,
                credit=credit,
                id_semestre=sem.id_semestre,
                id_filiere=filiere.id_filiere,
                id_professeur=prof.id_professeur,
                id_ue=id_ue,
            )
            db.session.add(m)
            all_matieres.append(m)

    db.session.commit()
    print(f"  {len(all_matieres)} matières générées (UE associées)")
    return all_matieres


# ─────────────────────────────────────────────────────────────
# ÉTUDIANTS (400)
# ─────────────────────────────────────────────────────────────
_NOMS = [
    "Kouassi","Traoré","Bamba","Diallo","Coulibaly","Koné","Soro","Ouattara",
    "Aké","N'Guessan","Brou","Touré","Sanogo","Diabaté","Konaté","Fofana",
    "Dosso","Yao","Mensah","Kamagaté","Dembélé","Keita","Bagayoko","Camara",
    "Sawadogo","Zongo","Barry","Sidibé","Silué","Kourouma","Kondé","Bah",
    "Sow","Ndiaye","Cissé","Dieng","Fall","Gueye","Sarr","Kaboré",
    "Ouédraogo","Compaoré","Tapsoba","Dao","Kiénou","Tall","Diop","Ndoye",
]
_PRENOMS_M = [
    "Abdoulaye","Ibrahim","Mamadou","Souleymane","Moussa","Kofi","Yves",
    "Bertin","Kouamé","Adama","Drissa","Ladji","Edmond","Stéphane","Siaka",
    "Boubacar","Lamine","Rasmané","Inoussa","Thierno","Ibrahima","Cheikh",
    "Modibo","Sékou","Alpha","Oumar","Daouda","Salif","Jean-Claude","Marc",
    "Boris","Franck","Dimitri","Roland","Cédric","Patrick","Olivier",
]
_PRENOMS_F = [
    "Adjoua","Fatoumata","Aminata","Mariam","Awa","Bintou","Hawa",
    "Korotoumou","Tenin","Patricia","Kadiatou","Fatou","Aïssatou","Rokia",
    "Djeneba","Safiatou","Néné","Oumou","Coumba","Nabintou","Rosine",
    "Clarisse","Joëlle","Estelle","Sandrine","Nathalie","Christelle","Vanessa",
]
_NAT_WEIGHTS = [55, 8, 6, 7, 6, 5, 3, 3, 3, 4]


def seed_etudiants(nationalites):
    etudiants = []
    for i in range(1, NB_ETUDIANTS + 1):
        genre  = random.choices(["M", "F"], weights=[60, 40])[0]
        prenom = random.choice(_PRENOMS_M) if genre == "M" else random.choice(_PRENOMS_F)
        nom    = random.choice(_NOMS)
        nat    = random.choices(nationalites, weights=_NAT_WEIGHTS)[0]
        annee  = random.randint(1997, 2005)

        e = Etudiant(
            matricule=f"IUA23{i:04d}",
            nom=nom,
            prenom=prenom,
            genre=genre,
            annee_naissance=annee,
            id_nationalite=nat.id_nationalite,
        )
        db.session.add(e)
        etudiants.append(e)
    db.session.commit()
    print(f"  {len(etudiants)} étudiants générés")
    return etudiants


# ─────────────────────────────────────────────────────────────
# INSCRIPTIONS + RÉSULTATS + NOTES + ABSENCES + RESULTAT_UE
# ─────────────────────────────────────────────────────────────
def seed_inscriptions(
    etudiants, filieres, specialites, niveaux,
    annee, matieres, session_normale, session_rattrapage,
):
    fil_by_nom = {f.nom_filiere: f for f in filieres}
    niv_by_lib = {n.libelle: n    for n in niveaux}

    spec_by_fil = {}
    for s in specialites:
        spec_by_fil.setdefault(s.id_filiere, []).append(s)

    mat_by_fil_sem = {}
    for m in matieres:
        key = (m.id_filiere, m.id_semestre)
        mat_by_fil_sem.setdefault(key, []).append(m)

    sem_by_niveau = {}
    for s in Semestre.query.all():
        sem_by_niveau.setdefault(s.id_niveau, []).append(s)

    fil_noms   = ["Informatique","Gestion","Finance Comptabilité","Marketing","DROIT","Logistique"]
    fil_poids  = [25, 20, 15, 15, 15, 10]
    niv_labels = ["L1", "L2", "L3"]
    niv_poids  = [50, 30, 20]

    inscriptions_data = []

    for etudiant in etudiants:
        profile   = choose_profile()
        fil_nom   = random.choices(fil_noms,   weights=fil_poids)[0]
        niv_label = random.choices(niv_labels, weights=niv_poids)[0]
        filiere   = fil_by_nom[fil_nom]
        niveau    = niv_by_lib[niv_label]
        specs_dispo = spec_by_fil.get(filiere.id_filiere, [None])
        specialite  = random.choice(specs_dispo)

        sems_du_niveau = sorted(
            sem_by_niveau.get(niveau.id_niveau, []),
            key=lambda s: s.ordre,
        )

        moy_s1 = moy_s2 = None
        credits_valides_s1 = credits_valides_s2 = 0
        resultats_par_sem = []

        for idx_sem, sem in enumerate(sems_du_niveau[:2]):
            mats_sem = mat_by_fil_sem.get((filiere.id_filiere, sem.id_semestre), [])
            if not mats_sem:
                resultats_par_sem.append([])
                continue

            sem_resultats = []
            moy_pond   = 0.0
            total_coef = 0.0

            for mat in mats_sem:
                note_val = random_note(profile)

                if note_val is None:
                    sem_resultats.append((mat, sem, None, None, None, False, session_normale))
                    continue

                # CC et examen : variation ±2 arrondie au 0.5
                delta_cc   = random.choice([x / 2.0 for x in range(-4, 5)])  # -2 à +2 par pas de 0.5
                delta_exam = random.choice([x / 2.0 for x in range(-4, 5)])
                note_cc   = round_note(note_val + delta_cc)
                note_exam = round_note(note_val + delta_exam)

                # Moyenne = 40% CC + 60% exam, arrondie au 0.5
                moy_mat_raw = note_cc * 0.4 + note_exam * 0.6
                moy_mat     = round_note(moy_mat_raw)
                sess_used   = session_normale

                if moy_mat < 10 and profile not in ("critique", "abandon") and random.random() < 0.65:
                    delta2     = random.choice([x / 2.0 for x in range(2, 9)])  # +1 à +4 par pas de 0.5
                    note_exam2 = round_note(note_exam + delta2)
                    moy_mat    = round_note(note_cc * 0.4 + note_exam2 * 0.6)
                    note_exam  = note_exam2
                    sess_used  = session_rattrapage

                credit_valide = moy_mat >= 10.0
                moy_pond   += moy_mat * mat.coefficient
                total_coef += mat.coefficient
                sem_resultats.append((mat, sem, note_cc, note_exam, moy_mat, credit_valide, sess_used))

            # Moyenne semestrielle arrondie au 0.5
            moy_sem     = round_note(moy_pond / total_coef) if total_coef else None
            credits_sem = sum(mat.credit for mat, _, cc, ex, moy, cv, _ in sem_resultats if cv)

            if idx_sem == 0:
                moy_s1             = moy_sem
                credits_valides_s1 = credits_sem
            else:
                moy_s2             = moy_sem
                credits_valides_s2 = credits_sem

            resultats_par_sem.append(sem_resultats)

        if profile == "abandon":
            moy_s1 = moy_s2 = None

        moy_ann = None
        if moy_s1 is not None and moy_s2 is not None:
            moy_ann = round_note((moy_s1 + moy_s2) / 2)
        elif moy_s1 is not None:
            moy_ann = moy_s1
        elif moy_s2 is not None:
            moy_ann = moy_s2

        credits_valides = credits_valides_s1 + credits_valides_s2
        men             = mention_from_average(moy_ann)
        est_redoublant  = (profile == "redoublant")

        insc = Inscription(
            id_etudiant        = etudiant.id_etudiant,
            id_filiere         = filiere.id_filiere,
            id_specialite      = specialite.id_specialite if specialite else None,
            id_niveau          = niveau.id_niveau,
            id_annee           = annee.id_annee,
            moyenne_s1         = moy_s1,
            moyenne_s2         = moy_s2,
            moyenne_annuelle   = moy_ann,
            credits_valides_s1 = credits_valides_s1,
            credits_valides_s2 = credits_valides_s2,
            credits_valides    = credits_valides,
            mention            = men,
            est_redoublant     = est_redoublant,
        )
        db.session.add(insc)
        db.session.flush()

        for sem_resultats in resultats_par_sem:
            for mat, sem, note_cc, note_exam, moy_mat, credit_valide, sess in sem_resultats:

                db.session.add(Resultat(
                    id_inscription = insc.id_inscription,
                    id_matiere     = mat.id_matiere,
                    id_semestre    = sem.id_semestre,
                    moyenne        = moy_mat,
                    credit_valide  = bool(credit_valide),
                ))

                if note_cc is None:
                    continue

                db.session.add(Note(
                    id_inscription  = insc.id_inscription,
                    id_matiere      = mat.id_matiere,
                    id_session      = session_normale.id_session,
                    type_evaluation = Note.TYPE_CC,
                    valeur          = note_cc,
                    date_eval       = date.today(),
                ))
                db.session.add(Note(
                    id_inscription  = insc.id_inscription,
                    id_matiere      = mat.id_matiere,
                    id_session      = sess.id_session,
                    type_evaluation = Note.TYPE_EXAM,
                    valeur          = note_exam,
                    date_eval       = date.today(),
                ))

                if profile in ("excellent", "moyen"):
                    nb_abs = random.randint(0, 4)
                elif profile == "faible":
                    nb_abs = random.randint(2, 10)
                elif profile == "critique":
                    nb_abs = random.randint(6, 18)
                elif profile == "abandon":
                    nb_abs = random.randint(12, 30)
                else:
                    nb_abs = random.randint(4, 14)

                for _ in range(nb_abs):
                    db.session.add(Absence(
                        id_etudiant = etudiant.id_etudiant,
                        id_matiere  = mat.id_matiere,
                        date        = date.today(),
                        justifie    = random.random() < 0.4,
                    ))

        try:
            creer_ou_maj_dette(insc)
        except Exception:
            pass

        inscriptions_data.append((insc.id_inscription, resultats_par_sem, moy_s1, moy_s2))

    db.session.commit()
    print("  Inscriptions, résultats, notes et absences générés")

    _seed_resultat_ue(inscriptions_data)


def _seed_resultat_ue(inscriptions_data):
    """
    Peuple resultat_ue depuis les données collectées pendant seed_inscriptions.
    """
    count = 0
    for id_inscription, resultats_par_sem, moy_s1, moy_s2 in inscriptions_data:
        ue_data = {}

        for idx_sem, sem_resultats in enumerate(resultats_par_sem):
            moy_sem = moy_s1 if idx_sem == 0 else moy_s2

            for mat, sem, note_cc, note_exam, moy_mat, credit_valide, sess in sem_resultats:
                if mat.id_ue is None:
                    continue
                id_ue = mat.id_ue
                if id_ue not in ue_data:
                    ue_data[id_ue] = {
                        "ue":         mat.ue,
                        "moy_pond":   0.0,
                        "total_coef": 0.0,
                        "moy_sem":    moy_sem,
                    }
                if moy_mat is not None:
                    coef = mat.coefficient or 1.0
                    ue_data[id_ue]["moy_pond"]   += moy_mat * coef
                    ue_data[id_ue]["total_coef"] += coef

        for id_ue, data in ue_data.items():
            ue      = data["ue"]
            moy_sem = data["moy_sem"]
            moy_ue  = (
                round_note(data["moy_pond"] / data["total_coef"])
                if data["total_coef"] > 0 else None
            )

            ue_validee = moy_ue is not None and moy_ue >= 10.0
            compensee  = False

            if (not ue_validee and moy_ue is not None
                    and ue is not None and ue.compensable
                    and moy_ue >= 8.0
                    and moy_sem is not None and moy_sem >= 10.0):
                ue_validee = True
                compensee  = True

            credits_ue_valides = (ue.credit_total if ue else 0) if ue_validee else 0

            db.session.add(ResultatUE(
                id_inscription     = id_inscription,
                id_ue              = id_ue,
                moyenne_ue         = moy_ue,
                ue_validee         = ue_validee,
                compensee          = compensee,
                credits_ue_valides = credits_ue_valides,
            ))
            count += 1

    db.session.commit()
    print(f"  {count} ResultatUE générés")


# ─────────────────────────────────────────────────────────────
# ADMINS
# ─────────────────────────────────────────────────────────────
def seed_admins():
    admin = Administrateur_sy(
        nom="Admin",
        prenom="Système",
        email="admin@iua.ci",
        genre="M",
    )
    admin.set_password("Admin@2024")
    db.session.add(admin)

    respo = Respo_peda(
        nom="Responsable",
        prenom="Pédagogique",
        email="respo@iua.ci",
        genre="F",
        mot_de_passe=generate_password_hash("Respo@2024"),
    )
    db.session.add(respo)

    db.session.commit()
    print("  Admins créés (admin@iua.ci / respo@iua.ci)")


# ─────────────────────────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────
def run_seed():
    reset_database()

    print("\n[1/11] Nationalités...")
    nationalites = seed_nationalites()

    print("[2/11] Filières...")
    filieres = seed_filieres()

    print("[3/11] Spécialités...")
    specialites = seed_specialites(filieres)

    print("[4/11] Niveaux...")
    niveaux = seed_niveaux()

    print("[5/11] Semestres...")
    semestres = seed_semestres(niveaux)

    print("[6/11] UE...")
    all_ues, ues_by_filiere = seed_ues(filieres, semestres)

    print("[7/11] Année scolaire...")
    annee = seed_annee_scolaire()

    print("[8/11] Sessions...")
    session_normale, session_rattrapage = seed_sessions()

    print("[9/11] Professeurs...")
    professeurs = seed_professeurs(filieres)

    print("[10/11] Matières (180)...")
    matieres = seed_matieres(filieres, semestres, professeurs, ues_by_filiere)

    print("[11/11] Étudiants + inscriptions + ResultatUE (400)...")
    etudiants = seed_etudiants(nationalites)
    seed_inscriptions(
        etudiants, filieres, specialites, niveaux,
        annee, matieres, session_normale, session_rattrapage,
    )

    seed_admins()

    print("\n" + "=" * 60)
    print("  SEED TERMINÉ AVEC SUCCÈS")
    print(f"  {NB_ETUDIANTS} étudiants  |  180 matières  |  6 filières")
    print("  30 crédits/semestre  |  Notes entières ou x.5")
    print("  ResultatUE peuplée  |  Dataset ML-ready")
    print("=" * 60)


if __name__ == "__main__":
    with app.app_context():
        run_seed()
