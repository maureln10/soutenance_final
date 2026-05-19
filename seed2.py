# seed_2024_2025.py - IUAInsight 2024-2025
# Dataset complet : 400 étudiants, 6 filières, ML-ready
# Notes entières ou x.5 — sans création d'admins

from faker import Faker
import random
from datetime import date

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
    creer_ou_maj_dette,
)

fake = Faker('fr_FR')
random.seed(99)

NB_ETUDIANTS = 600

# ─────────────────────────────────────────────────────────────
# PROFILS DE PERFORMANCE
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
    if profile == "abandon":
        return None
    lo, hi = PROFILS[profile]["range"]
    lo_idx = int(lo * 2)
    hi_idx = int(hi * 2)
    return random.randint(lo_idx, hi_idx) / 2.0


def round_note(val):
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
# NOMS / PRÉNOMS
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

_MAT_UE_MAPPING = {
    0: 0,  1: 0,  2: 0,  3: 1,  4: 1,
    5: 2,  6: 2,  7: 2,  8: 3,  9: 3,
    10: 4, 11: 4, 12: 4, 13: 5, 14: 5,
    15: 6, 16: 6, 17: 6, 18: 7, 19: 7,
    20: 8, 21: 8, 22: 8, 23: 9, 24: 9,
    25: 10, 26: 10, 27: 10, 28: 11, 29: 11,
}


# ─────────────────────────────────────────────────────────────
# ANNÉE SCOLAIRE
# ─────────────────────────────────────────────────────────────
def seed_annee_scolaire():
    existing = AnneeScolaire.query.filter_by(libelle="2024-2025").first()
    if existing:
        print("  Année 2024-2025 déjà existante, réutilisée.")
        return existing

    # Désactiver l'année précédente
    AnneeScolaire.query.update({"active": False})

    annee = AnneeScolaire(
        libelle="2024-2025",
        date_debut=date(2024, 9, 1),
        date_fin=date(2025, 7, 31),
        active=True,
    )
    db.session.add(annee)
    db.session.commit()
    print("  Année scolaire 2024-2025 créée et activée.")
    return annee


# ─────────────────────────────────────────────────────────────
# SESSIONS — réutilise les existantes
# ─────────────────────────────────────────────────────────────
def get_or_create_sessions():
    normale    = Session.query.filter_by(libelle="Normale").first()
    rattrapage = Session.query.filter_by(libelle="Rattrapage").first()
    if not normale:
        normale = Session(libelle="Normale", est_rattrapage=False)
        db.session.add(normale)
    if not rattrapage:
        rattrapage = Session(libelle="Rattrapage", est_rattrapage=True)
        db.session.add(rattrapage)
    db.session.commit()
    return normale, rattrapage


# ─────────────────────────────────────────────────────────────
# ÉTUDIANTS (400 nouveaux avec matricules 2024xxxx)
# ─────────────────────────────────────────────────────────────
def seed_etudiants(nationalites):
    etudiants = []
    for i in range(1, NB_ETUDIANTS + 1):
        genre  = random.choices(["M", "F"], weights=[60, 40])[0]
        prenom = random.choice(_PRENOMS_M) if genre == "M" else random.choice(_PRENOMS_F)
        nom    = random.choice(_NOMS)
        nat    = random.choices(nationalites, weights=_NAT_WEIGHTS)[0]
        annee  = random.randint(1998, 2006)

        e = Etudiant(
            matricule=f"IUA24{i:04d}",
            nom=nom,
            prenom=prenom,
            genre=genre,
            annee_naissance=annee,
            id_nationalite=nat.id_nationalite,
        )
        db.session.add(e)
        etudiants.append(e)
    db.session.commit()
    print(f"  {len(etudiants)} étudiants générés (matricules IUA24xxxx)")
    return etudiants


# ─────────────────────────────────────────────────────────────
# INSCRIPTIONS + RÉSULTATS + NOTES + ABSENCES + RESULTAT_UE
# ─────────────────────────────────────────────────────────────
def seed_inscriptions(
    etudiants, filieres, specialites, niveaux,
    annee, matieres, semestres, ues_by_filiere,
    session_normale, session_rattrapage,
):
    fil_by_nom  = {f.nom_filiere: f for f in filieres}
    niv_by_lib  = {n.libelle: n     for n in niveaux}

    spec_by_fil = {}
    for s in specialites:
        spec_by_fil.setdefault(s.id_filiere, []).append(s)

    mat_by_fil_sem = {}
    for m in matieres:
        key = (m.id_filiere, m.id_semestre)
        mat_by_fil_sem.setdefault(key, []).append(m)

    sem_by_niveau = {}
    for s in semestres:
        sem_by_niveau.setdefault(s.id_niveau, []).append(s)

    fil_noms  = ["Informatique","Gestion","Finance Comptabilité","Marketing","DROIT","Logistique"]
    fil_poids = [25, 20, 15, 15, 15, 10]
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

                delta_cc   = random.choice([x / 2.0 for x in range(-4, 5)])
                delta_exam = random.choice([x / 2.0 for x in range(-4, 5)])
                note_cc    = round_note(note_val + delta_cc)
                note_exam  = round_note(note_val + delta_exam)

                moy_mat_raw = note_cc * 0.4 + note_exam * 0.6
                moy_mat     = round_note(moy_mat_raw)
                sess_used   = session_normale

                if moy_mat < 10 and profile not in ("critique", "abandon") and random.random() < 0.65:
                    delta2     = random.choice([x / 2.0 for x in range(2, 9)])
                    note_exam2 = round_note(note_exam + delta2)
                    moy_mat    = round_note(note_cc * 0.4 + note_exam2 * 0.6)
                    note_exam  = note_exam2
                    sess_used  = session_rattrapage

                credit_valide = moy_mat >= 10.0
                moy_pond   += moy_mat * mat.coefficient
                total_coef += mat.coefficient
                sem_resultats.append((mat, sem, note_cc, note_exam, moy_mat, credit_valide, sess_used))

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
# POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────
def run_seed():
    print("\n[1/5] Récupération des données existantes...")
    nationalites = Nationalite.query.all()
    filieres     = Filiere.query.order_by(Filiere.nom_filiere).all()
    specialites  = Specialite.query.all()
    niveaux      = Niveau.query.order_by(Niveau.libelle).all()
    semestres    = Semestre.query.all()
    matieres     = Matiere.query.all()

    ues_by_filiere = {}
    for ue in UE.query.all():
        sem = Semestre.query.get(ue.id_semestre)
        if not sem:
            continue
        niv = Niveau.query.get(sem.id_niveau)
        if not niv:
            continue
        # Trouver la filière via les matières liées à cette UE
        mat_ue = Matiere.query.filter_by(id_ue=ue.id_ue).first()
        if mat_ue:
            fil = Filiere.query.get(mat_ue.id_filiere)
            if fil:
                ues_by_filiere.setdefault(fil.nom_filiere, [])
                if ue not in ues_by_filiere[fil.nom_filiere]:
                    ues_by_filiere[fil.nom_filiere].append(ue)

    if not nationalites or not filieres or not matieres:
        print("ERREUR : données de base manquantes. Lance d'abord seed.py.")
        return

    print("[2/5] Année scolaire 2024-2025...")
    annee = seed_annee_scolaire()

    print("[3/5] Sessions...")
    session_normale, session_rattrapage = get_or_create_sessions()

    print("[4/5] Étudiants (400 nouveaux)...")
    etudiants = seed_etudiants(nationalites)

    print("[5/5] Inscriptions + résultats + notes...")
    seed_inscriptions(
        etudiants, filieres, specialites, niveaux,
        annee, matieres, semestres, ues_by_filiere,
        session_normale, session_rattrapage,
    )

    print("\n" + "=" * 60)
    print("  SEED 2024-2025 TERMINÉ AVEC SUCCÈS")
    print(f"  {NB_ETUDIANTS} nouveaux étudiants  |  Année 2024-2025 active")
    print("  Données de base (filières, matières) réutilisées")
    print("  Aucun admin créé")
    print("=" * 60)


if __name__ == "__main__":
    with app.app_context():
        run_seed()