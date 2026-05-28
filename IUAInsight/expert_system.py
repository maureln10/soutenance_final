"""
IUAInsight — Système Expert Académique (LMD)
============================================
Règles métier 100% alignées sur models.py :

  Colonnes utilisées directement :
    · inscription.credits_valides        (S1+S2 après rattrapage)
    · inscription.credits_valides_s1/s2  (par semestre)
    · inscription.moyenne_s1/s2/annuelle
    · inscription.est_redoublant
    · inscription.statut_simple          (propriété calculée)
    · niveau.credits_requis              (défaut 60)
    · niveau.credits_admission           (défaut 47)
    · resultat.moyenne_rattrapage        (session rattrapage)
    · resultat.credit_valide
    · resultat.credit_valide_rattrapage

  Logique LMD :
    · 60 crédits/an (30 S1 + 30 S2)
    · Admis        : credits_valides >= 60
    · Admis dettes : 47 <= credits_valides < 60
    · Éliminé      : credits_valides < 47
    · Pas de compensation inter-semestrielle
    · Deux sessions : Normale + Rattrapage
"""

import logging

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# MODÈLE D'UNE RÈGLE
# ══════════════════════════════════════════════

class Regle:
    """
    Paramètres
    ----------
    nom            : identifiant court
    condition      : callable(inscription) -> bool
    niveau         : "critique" | "modere" | "surveillance" | "ok"
    priorite       : int — plus petit = plus prioritaire
    message        : texte affiché dans regles_declenchees
    recommandation : dict affiché dans recommandations
    """
    def __init__(self, nom, condition, niveau, priorite, message, recommandation):
        self.nom            = nom
        self.condition      = condition
        self.niveau         = niveau
        self.priorite       = priorite
        self.message        = message
        self.recommandation = recommandation


# ══════════════════════════════════════════════
# HELPERS — colonnes/méthodes de models.py
# ══════════════════════════════════════════════

def _cv(i):
    """credits_valides total (S1+S2 après rattrapage) — colonne Inscription."""
    return i.credits_valides or 0

def _cv_s1(i):
    """credits_valides_s1 — colonne Inscription."""
    return i.credits_valides_s1 or 0

def _cv_s2(i):
    """credits_valides_s2 — colonne Inscription."""
    return i.credits_valides_s2 or 0

def _cr(i):
    """credits_requis — Niveau.credits_requis (défaut 60)."""
    return i.niveau.credits_requis if i.niveau else 60

def _ca(i):
    """credits_admission — Niveau.credits_admission (défaut 47)."""
    return i.niveau.credits_admission if i.niveau else 47

def _cps(i):
    """credits par semestre = credits_requis // 2 = 30."""
    return _cr(i) // 2

def _moy(i):
    """Meilleure moyenne disponible : annuelle > S1 > S2."""
    return i.moyenne_annuelle or i.moyenne_s1 or i.moyenne_s2

def _statut(i):
    """Utilise la propriété statut_simple de Inscription."""
    return i.statut_simple

def _a_rattrapage(i):
    """
    True si l'étudiant a au moins un Resultat avec moyenne_rattrapage
    renseignée (champ Resultat.moyenne_rattrapage de models.py).
    """
    return any(r.moyenne_rattrapage is not None for r in i.resultats)

def _nb_echecs(i):
    """Nombre de matières avec moyenne < 10 (session normale ou rattrapage)."""
    return sum(
        1 for r in i.resultats
        if r.matiere and r.moyenne is not None and r.moyenne < 10
    )

def _noms_echecs(i):
    """Liste des noms de matières en échec."""
    return [
        r.matiere.nom_matiere
        for r in i.resultats
        if r.matiere and r.moyenne is not None and r.moyenne < 10
    ]

def _s1_insuffisant(i):
    """S1 présent mais crédits S1 < seuil semestre (30)."""
    return i.moyenne_s1 is not None and _cv_s1(i) < _cps(i)

def _s2_insuffisant(i):
    """S2 présent mais crédits S2 < seuil semestre (30)."""
    return i.moyenne_s2 is not None and _cv_s2(i) < _cps(i)


# ══════════════════════════════════════════════
# RÈGLES MÉTIER LMD
# ══════════════════════════════════════════════

def construire_regles() -> list:
    regles = []

    # ── R01 : ABANDON ────────────────────────────────────────────────
    # statut_simple == "Abandon" si _a_notes_s1==False et _a_notes_s2==False
    regles.append(Regle(
        nom       = "abandon",
        condition = lambda i: _statut(i) == "Abandon",
        niveau    = "critique",
        priorite  = 1,
        message   = "Aucune note enregistrée au S1 ni au S2 — abandon probable.",
        recommandation = {
            "priorite":  "critique",
            "titre":     "Abandon probable — contact urgent",
            "action": (
                "Aucune présence ni note détectée. "
                "Contacter l'étudiant immédiatement pour confirmer sa situation "
                "et prévenir un abandon définitif."
            ),
            "categorie": "Abandon",
        },
    ))

    # ── R02 : ÉLIMINATION — credits_valides < credits_admission (47) ─
    regles.append(Regle(
        nom       = "elimination",
        condition = lambda i: (
            _statut(i) not in ("Abandon", "En cours")
            and _cv(i) < _ca(i)
            and i.moyenne_s1 is not None
            and i.moyenne_s2 is not None
        ),
        niveau    = "critique",
        priorite  = 2,
        message   = (
            "Crédits insuffisants pour le passage : "
            "moins de 47 crédits validés sur 60 requis — règle LMD."
        ),
        recommandation = {
            "priorite":  "critique",
            "titre":     "Risque d'élimination LMD",
            "action": (
                "L'étudiant n'a pas atteint le seuil de passage (47 crédits). "
                "Convoquer immédiatement pour examiner les options : "
                "redoublement, réorientation ou dossier de dérogation."
            ),
            "categorie": "Statut LMD",
        },
    ))

    # ── R03 : REDOUBLANT EN ÉCHEC ─────────────────────────────────────
    # statut_simple == "Redoublant" : est_redoublant + credits < 47
    regles.append(Regle(
        nom       = "redoublant_echec",
        condition = lambda i: _statut(i) == "Redoublant",
        niveau    = "critique",
        priorite  = 3,
        message   = "Redoublant avec crédits insuffisants — risque d'élimination définitive.",
        recommandation = {
            "priorite":  "critique",
            "titre":     "Redoublant en échec — situation critique",
            "action": (
                "Étudiant redoublant avec des résultats insuffisants. "
                "Analyser les causes d'échec du cycle précédent, proposer "
                "un accompagnement individuel renforcé et évaluer "
                "la nécessité d'une réorientation."
            ),
            "categorie": "Redoublement",
        },
    ))

    # ── R04 : AJOURNÉ S1 ET S2 ────────────────────────────────────────
    regles.append(Regle(
        nom       = "ajourn_s1_s2",
        condition = lambda i: _statut(i) == "Ajourné S1 & S2",
        niveau    = "critique",
        priorite  = 4,
        message   = "Ajourné aux deux semestres — crédits insuffisants au S1 et au S2.",
        recommandation = {
            "priorite":  "critique",
            "titre":     "Ajourné S1 & S2 — plan de remédiation urgent",
            "action": (
                "L'étudiant n'a pas validé suffisamment de crédits "
                "ni au S1 ni au S2. Mettre en place un plan de remédiation "
                "couvrant les deux semestres et inscrire aux sessions "
                "de rattrapage disponibles."
            ),
            "categorie": "Statut LMD",
        },
    ))

    # ── R05 : AJOURNÉ S1 UNIQUEMENT ───────────────────────────────────
    regles.append(Regle(
        nom       = "ajourn_s1",
        condition = lambda i: _statut(i) == "Ajourné S1",
        niveau    = "modere",
        priorite  = 5,
        message   = "Ajourné au S1 — crédits S1 insuffisants (< 30).",
        recommandation = {
            "priorite":  "moderee",
            "titre":     "Ajourné S1 — rattrapage S1",
            "action": (
                "Crédits insuffisants au S1. "
                "Préparer l'étudiant à la session de rattrapage S1 "
                "et identifier les matières à consolider en priorité."
            ),
            "categorie": "Semestre 1",
        },
    ))

    # ── R06 : AJOURNÉ S2 UNIQUEMENT ───────────────────────────────────
    regles.append(Regle(
        nom       = "ajourn_s2",
        condition = lambda i: _statut(i) == "Ajourné S2",
        niveau    = "modere",
        priorite  = 6,
        message   = "Ajourné au S2 — crédits S2 insuffisants (< 30).",
        recommandation = {
            "priorite":  "moderee",
            "titre":     "Ajourné S2 — rattrapage S2",
            "action": (
                "Crédits insuffisants au S2. "
                "Préparer l'étudiant à la session de rattrapage S2 "
                "et organiser un bilan de fin d'année."
            ),
            "categorie": "Semestre 2",
        },
    ))

    # ── R07 : ADMIS AVEC DETTES ───────────────────────────────────────
    # 47 <= credits_valides < 60 — propriété statut_simple == "Admis (dettes)"
    regles.append(Regle(
        nom       = "admis_dettes",
        condition = lambda i: _statut(i) == "Admis (dettes)",
        niveau    = "surveillance",
        priorite  = 7,
        message   = (
            "Admis avec dettes : passage au niveau suivant autorisé "
            "mais des crédits restent à valider."
        ),
        recommandation = {
            "priorite":  "moderee",
            "titre":     "Admis avec dettes — suivi obligatoire",
            "action": (
                "L'étudiant passe au niveau suivant mais conserve des dettes de crédits. "
                "Planifier un suivi semestriel pour s'assurer de la validation "
                "des crédits manquants et mettre à jour la table DetteCreditNiveau."
            ),
            "categorie": "Statut LMD",
        },
    ))

    # ── R08 : PASSAGE PAR RATTRAPAGE ─────────────────────────────────
    # Resultat.moyenne_rattrapage renseignée sur au moins un résultat
    regles.append(Regle(
        nom       = "rattrapage",
        condition = lambda i: _a_rattrapage(i),
        niveau    = "surveillance",
        priorite  = 8,
        message   = "L'étudiant a eu recours à la session de rattrapage.",
        recommandation = {
            "priorite":  "moderee",
            "titre":     "Passage par session de rattrapage",
            "action": (
                "L'étudiant a dû passer par le rattrapage. "
                "Mettre en place un suivi préventif pour éviter "
                "le recours systématique au rattrapage les semestres suivants."
            ),
            "categorie": "Sessions",
        },
    ))

    # ── R09 : MOYENNE TRÈS FAIBLE (< 6) ──────────────────────────────
    regles.append(Regle(
        nom       = "moyenne_tres_faible",
        condition = lambda i: _moy(i) is not None and _moy(i) < 6,
        niveau    = "critique",
        priorite  = 9,
        message   = "Moyenne inférieure à 6/20 — niveau très insuffisant.",
        recommandation = {
            "priorite":  "critique",
            "titre":     "Moyenne très insuffisante (< 6/20)",
            "action": (
                "Niveau académique critique. Déclencher le protocole d'urgence : "
                "entretien pédagogique sous 48 h, orientation vers la cellule d'aide "
                "et évaluation d'une possible réorientation."
            ),
            "categorie": "Académique",
        },
    ))

    # ── R10 : MOYENNE FAIBLE (6–10) ──────────────────────────────────
    regles.append(Regle(
        nom       = "moyenne_faible",
        condition = lambda i: _moy(i) is not None and 6 <= _moy(i) < 10,
        niveau    = "modere",
        priorite  = 10,
        message   = "Moyenne entre 6 et 10/20 — en dessous du seuil de validation.",
        recommandation = {
            "priorite":  "moderee",
            "titre":     "Moyenne insuffisante (6–10/20)",
            "action": (
                "Planifier un entretien pédagogique et mettre en place "
                "un tutorat hebdomadaire. Identifier les matières les plus "
                "problématiques et proposer des groupes de révision."
            ),
            "categorie": "Académique",
        },
    ))

    # ── R11 : DÉCROCHAGE EN COURS D'ANNÉE ────────────────────────────
    # S1 présent, S2 absent — statut_simple == "En cours" avec moyenne_s2 None
    regles.append(Regle(
        nom       = "decrochage_s2",
        condition = lambda i: (
            i.moyenne_s1 is not None and i.moyenne_s2 is None
            and _statut(i) != "Abandon"
        ),
        niveau    = "modere",
        priorite  = 11,
        message   = "Notes présentes au S1 mais absentes au S2 — décrochage possible.",
        recommandation = {
            "priorite":  "moderee",
            "titre":     "Décrochage en cours d'année",
            "action": (
                "S1 enregistré mais aucune note au S2. "
                "Contacter l'étudiant pour comprendre cette absence "
                "et l'accompagner avant la clôture de l'année."
            ),
            "categorie": "Abandon",
        },
    ))

    # ── R12 : MULTIPLES ÉCHECS (>= 4 matières) ───────────────────────
    # Résultats avec credit_valide == False
    regles.append(Regle(
        nom       = "multi_echecs",
        condition = lambda i: _nb_echecs(i) >= 4,
        niveau    = "modere",
        priorite  = 12,
        message   = "4 matières ou plus en échec — difficultés généralisées.",
        recommandation = {
            "priorite":  "moderee",
            "titre":     "Échecs multiples (≥ 4 matières)",
            "action": (
                "L'étudiant est en échec dans 4 matières ou plus. "
                "Organiser des séances de rattrapage ciblées et "
                "établir un plan de travail personnalisé."
            ),
            "categorie": "Académique",
        },
    ))

    # ── R13 : CRÉDITS FRAGILES (ca <= cv < ca+6) ─────────────────────
    # Juste au-dessus du seuil d'élimination — surveiller
    regles.append(Regle(
        nom       = "credits_fragiles",
        condition = lambda i: (
            _statut(i) == "Admis (dettes)"
            and _cv(i) < _ca(i) + 6          # entre 47 et 52
        ),
        niveau    = "surveillance",
        priorite  = 13,
        message   = "Crédits juste au-dessus du seuil d'élimination (47–52) — situation fragile.",
        recommandation = {
            "priorite":  "moderee",
            "titre":     "Crédits proches du seuil d'élimination",
            "action": (
                "L'étudiant est juste au-dessus du seuil de 47 crédits. "
                "Instaurer un suivi trimestriel et l'encourager à "
                "consolider ses acquis pour sécuriser son passage."
            ),
            "categorie": "Statut LMD",
        },
    ))

    # ── R14 : REDOUBLANT EN SURVEILLANCE ─────────────────────────────
    # est_redoublant mais pas encore en échec final
    regles.append(Regle(
        nom       = "redoublant_surveillance",
        condition = lambda i: (
            i.est_redoublant
            and _statut(i) not in ("Redoublant", "Abandon")
            and (_moy(i) is None or _moy(i) < 12)
        ),
        niveau    = "surveillance",
        priorite  = 14,
        message   = "Étudiant redoublant — nécessite un suivi renforcé.",
        recommandation = {
            "priorite":  "moderee",
            "titre":     "Redoublant — accompagnement renforcé",
            "action": (
                "Étudiant en situation de redoublement. "
                "Analyser les causes d'échec du cycle précédent et proposer "
                "un tutorat individuel adapté pour éviter un nouvel échec."
            ),
            "categorie": "Redoublement",
        },
    ))

    return regles


# ══════════════════════════════════════════════
# SYSTÈME EXPERT
# ══════════════════════════════════════════════

class SystemeExpert:

    def __init__(self, regles: list = None):
        self.regles = regles or []

    def evaluer_statut(self, inscription) -> dict:
        """
        Évalue le statut académique LMD d'une inscription.

        Retourne
        --------
        {
            "niveau_academique"  : "critique"|"modere"|"surveillance"|"ok",
            "recommandations"    : [...],
            "regles_declenchees" : [...],
            "source"             : "expert",
        }
        """
        regles_declenchees = []

        for regle in self.regles:
            try:
                if regle.condition(inscription):
                    regles_declenchees.append(regle)
            except Exception as e:
                logger.debug("Règle '%s' ignorée : %s", regle.nom, e)
                continue

        regles_declenchees.sort(key=lambda r: r.priorite)

        niveau_academique = regles_declenchees[0].niveau if regles_declenchees else "ok"

        recommandations = [r.recommandation for r in regles_declenchees]
        if not recommandations:
            recommandations = [{
                "priorite":  "info",
                "titre":     "Situation académique satisfaisante",
                "action": (
                    "L'étudiant a validé ses 60 crédits et respecte "
                    "les normes LMD. Encourager la régularité et "
                    "la participation aux activités d'enrichissement."
                ),
                "categorie": "Académique",
            }]

        return {
            "niveau_academique":  niveau_academique,
            "recommandations":    recommandations,
            "regles_declenchees": [r.message for r in regles_declenchees],
            "source":             "expert",
        }


# ══════════════════════════════════════════════
# SINGLETON
# ══════════════════════════════════════════════
expert_engine = SystemeExpert(regles=construire_regles())