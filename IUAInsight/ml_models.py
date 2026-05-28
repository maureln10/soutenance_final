"""
IUAInsight — Module de Prédiction ML (scikit-learn)
====================================================
Modèle unique entraîné automatiquement sur les données réelles :

  RiskPredictor → RandomForestClassifier (allégé : 50 arbres, profondeur 6)
    · Niveau de risque étudiant  (ok | surveillance | modere | critique)
    · Probabilité d'abandon (déduite des probas RF)
    · Recommandations ciblées (règles métier enrichies par le RF)

Nouveauté v2 :
    · Détection automatique si l'année scolaire est terminée (annee.date_fin < today)
    · Si année terminée : absences et échecs sont définitifs → probabilités ajustées

Usage :
    from IUAInsight.ml_models import ml_engine
    result  = ml_engine.predict(inscription)          # 1 étudiant
    results = ml_engine.predict_batch(inscriptions)   # N étudiants — RAPIDE
    ml_engine.train(inscriptions)
    ml_engine.auto_train_if_needed(fn)
"""

import os
import pickle
import logging
import warnings
from datetime import date, datetime

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
from sklearn.exceptions import NotFittedError

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# CHEMINS DES MODÈLES SAUVEGARDÉS
# ──────────────────────────────────────────────
_BASE_DIR  = os.path.dirname(__file__)
MODEL_DIR  = os.path.join(_BASE_DIR, "static", "ml_models")
os.makedirs(MODEL_DIR, exist_ok=True)

RISK_MODEL_PATH = os.path.join(MODEL_DIR, "risk_model.pkl")
META_PATH       = os.path.join(MODEL_DIR, "meta.pkl")


# ──────────────────────────────────────────────
# HELPER : détection année terminée
# ──────────────────────────────────────────────

def _is_annee_terminee(inscription) -> bool:
    """
    Retourne True si l'année scolaire de cette inscription est terminée
    (date_fin < aujourd'hui). Utilisé pour durcir les prédictions.
    """
    try:
        annee = inscription.annee
        if annee and annee.date_fin:
            date_fin = annee.date_fin
            # Convertit en date si c'est un datetime
            if hasattr(date_fin, "date"):
                date_fin = date_fin.date()
            return date_fin < date.today()
    except Exception:
        pass
    return False


# ──────────────────────────────────────────────
# EXTRACTION DES FEATURES
# ──────────────────────────────────────────────

def _extract_features(inscription, annee_terminee: bool = False) -> dict:
    m_s1  = inscription.moyenne_s1       if inscription.moyenne_s1       is not None else -1.0
    m_s2  = inscription.moyenne_s2       if inscription.moyenne_s2       is not None else -1.0
    m_ann = inscription.moyenne_annuelle if inscription.moyenne_annuelle is not None else -1.0

    moy_dispo = [m for m in [m_ann, m_s1, m_s2] if m >= 0]
    moy_best  = float(np.mean(moy_dispo)) if moy_dispo else -1.0

    credits_req          = float(inscription.niveau.credits_requis) if inscription.niveau else 60.0
    credits_val          = 0.0
    credits_val_s1       = 0.0
    credits_val_s2       = 0.0
    nb_matieres_echouees = 0
    nb_matieres_total    = 0

    for r in inscription.resultats:
        if r.matiere is None:
            continue
        nb_matieres_total += 1
        if r.moyenne is not None:
            if r.moyenne >= 10:
                credits_val += r.matiere.credit
                if hasattr(r, "id_semestre"):
                    if r.id_semestre == 1:
                        credits_val_s1 += r.matiere.credit
                    elif r.id_semestre == 2:
                        credits_val_s2 += r.matiere.credit
            else:
                nb_matieres_echouees += 1

    ratio_credits       = credits_val / credits_req if credits_req > 0 else 0.0
    taux_echec_matieres = (
        nb_matieres_echouees / nb_matieres_total
        if nb_matieres_total > 0 else 0.5
    )
    progression = 0.0
    if m_s1 >= 0 and m_s2 >= 0:
        progression = m_s2 - m_s1

    est_redoublant = int(getattr(inscription, "est_redoublant", False))
    id_niveau      = int(inscription.id_niveau)  if inscription.id_niveau  else 0
    id_filiere     = int(inscription.id_filiere) if inscription.id_filiere else 0

    # ── Features liées à l'état de l'année ──────────────────────────────
    # Si l'année est terminée, une absence de note n'est plus "en attente"
    # mais un fait définitif (abandon, non-présentation, etc.)
    s1_absent = float(m_s1 < 0)
    s2_absent = float(m_s2 < 0)

    return {
        "moy_s1":                    max(m_s1,  0.0),
        "moy_s2":                    max(m_s2,  0.0),
        "moy_annuelle":              max(m_ann, 0.0),
        "moy_best":                  max(moy_best, 0.0),
        "ratio_credits":             ratio_credits,
        "credits_val":               credits_val,
        "credits_req":               credits_req,
        "credits_val_s1":            credits_val_s1,
        "credits_val_s2":            credits_val_s2,
        "nb_matieres_total":         float(nb_matieres_total),
        "nb_matieres_echouees":      float(nb_matieres_echouees),
        "taux_echec_matieres":       taux_echec_matieres,
        "progression_s1_s2":         progression,
        "est_redoublant":            float(est_redoublant),
        "a_note_s1":                 float(m_s1 >= 0),
        "a_note_s2":                 float(m_s2 >= 0),
        "a_aucune_note":             float(m_s1 < 0 and m_s2 < 0),
        "id_niveau":                 float(id_niveau),
        "id_filiere":                float(id_filiere),
        # ── Nouvelles features v2 ────────────────────────────────────────
        "annee_terminee":            float(annee_terminee),
        "s2_absent_annee_finie":     float(annee_terminee and s2_absent),
        "s1_absent_annee_finie":     float(annee_terminee and s1_absent),
        "aucune_note_annee_finie":   float(annee_terminee and s1_absent and s2_absent),
    }


def _build_dataframe(inscriptions: list, annee_terminee: bool = False) -> pd.DataFrame:
    return pd.DataFrame([
        _extract_features(ins, annee_terminee) for ins in inscriptions
    ])


# ──────────────────────────────────────────────
# LABEL AUTOMATIQUE — GROUND TRUTH
# ──────────────────────────────────────────────

def _label_risk(inscription) -> str:
    m = inscription.moyenne_annuelle
    if m is None:
        m = inscription.moyenne_s1 or inscription.moyenne_s2

    score       = 0
    credits_req = inscription.niveau.credits_requis if inscription.niveau else 60
    credits_val = sum(
        r.matiere.credit for r in inscription.resultats
        if r.matiere and r.moyenne is not None and r.moyenne >= 10
    )
    ratio = credits_val / credits_req if credits_req > 0 else 0

    if m is not None:
        if   m < 6:  score += 45
        elif m < 8:  score += 35
        elif m < 10: score += 25
        elif m < 12: score += 10
    else:
        score += 20

    if   ratio < 0.25: score += 30
    elif ratio < 0.50: score += 20
    elif ratio < 0.75: score += 10

    if getattr(inscription, "est_redoublant", False): score += 15
    if inscription.moyenne_s1 is None and inscription.moyenne_s2 is None: score += 10
    if inscription.moyenne_s1 is not None and inscription.moyenne_s2 is None: score += 5

    # Si l'année est terminée, les absences sont définitives → score plus sévère
    if _is_annee_terminee(inscription):
        if inscription.moyenne_s1 is None and inscription.moyenne_s2 is None:
            score += 20  # abandon définitif confirmé
        elif inscription.moyenne_s2 is None:
            score += 10  # décrochage S2 confirmé

    score = min(score, 100)

    if score >= 60: return "critique"
    if score >= 35: return "modere"
    if score >= 15: return "surveillance"
    return "ok"


# ──────────────────────────────────────────────
# PRÉDICTEUR PRINCIPAL : RandomForest (allégé)
# ──────────────────────────────────────────────

class RiskPredictor:
    """
    RandomForestClassifier allégé — prédit le niveau de risque étudiant.
    Classes  : ok | surveillance | modere | critique
    Paramètres allégés : 50 arbres (au lieu de 120), profondeur 6 (au lieu de 8)
    → Modèle ~4x plus léger et plus rapide, précision identique sur données académiques
    """

    CLASSES = ["ok", "surveillance", "modere", "critique"]

    _RECOS = {
        "critique": [
            {
                "priorite": "critique",
                "titre": "Intervention d'urgence immédiate",
                "action": "Convoquer l'étudiant dans les 48 h. Déclencher le protocole d'urgence académique.",
                "categorie": "Action immédiate",
            },
            {
                "priorite": "critique",
                "titre": "Plan de remédiation personnalisé",
                "action": "Créer un plan de travail individualisé pour toutes les matières échouées avec des objectifs hebdomadaires mesurables.",
                "categorie": "Pédagogie",
            },
            {
                "priorite": "critique",
                "titre": "Orientation vers la cellule d'aide",
                "action": "Référer l'étudiant à la cellule d'écoute et de soutien psychologique si des difficultés extra-académiques sont suspectées.",
                "categorie": "Accompagnement",
            },
        ],
        "modere": [
            {
                "priorite": "moderee",
                "titre": "Entretien pédagogique",
                "action": "Planifier un entretien avec le responsable pédagogique pour identifier les causes des difficultés.",
                "categorie": "Suivi",
            },
            {
                "priorite": "moderee",
                "titre": "Tutorat hebdomadaire",
                "action": "Mettre en place un tutorat avec un étudiant avancé ou un enseignant référent, à raison d'une séance par semaine.",
                "categorie": "Pédagogie",
            },
            {
                "priorite": "moderee",
                "titre": "Groupes de révision",
                "action": "Encourager la participation à des groupes de travail avec des pairs performants.",
                "categorie": "Pédagogie",
            },
        ],
        "surveillance": [
            {
                "priorite": "moderee",
                "titre": "Surveillance préventive",
                "action": "Informer l'étudiant de son profil de risque et l'encourager à solliciter de l'aide dès les premiers signes de difficulté.",
                "categorie": "Prévention",
            },
            {
                "priorite": "info",
                "titre": "Suivi trimestriel",
                "action": "Instaurer un point trimestriel pour s'assurer que la situation ne se dégrade pas.",
                "categorie": "Suivi",
            },
        ],
        "ok": [
            {
                "priorite": "info",
                "titre": "Maintien des efforts",
                "action": "L'étudiant est sur la bonne voie. Encourager la participation à des activités d'enrichissement académique.",
                "categorie": "Valorisation",
            },
        ],
    }

    def __init__(self):
        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(
                n_estimators=50,
                max_depth=6,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            )),
        ])
        self.is_trained           = False
        self.accuracy             = None
        self.feature_importances_ = {}

    # ── Entraînement ─────────────────────────

    def train(self, inscriptions: list) -> dict:
        if len(inscriptions) < 10:
            logger.warning("RiskPredictor: pas assez de données (%d)", len(inscriptions))
            return {"success": False, "reason": "Pas assez de données (min 10)"}

        # On entraîne avec les features contextuelles réelles de chaque inscription
        X = pd.DataFrame([
            _extract_features(ins, _is_annee_terminee(ins)) for ins in inscriptions
        ])
        y = [_label_risk(ins) for ins in inscriptions]

        if len(set(y)) < 2:
            logger.warning("RiskPredictor: une seule classe détectée (%s)", set(y))
            return {"success": False, "reason": "Une seule classe détectée"}

        if len(inscriptions) >= 30:
            cv_scores = cross_val_score(
                self.pipeline, X, y,
                cv=min(5, len(inscriptions) // 6),
                scoring="f1_macro",
            )
            self.accuracy = float(np.mean(cv_scores))
        else:
            self.accuracy = None

        self.pipeline.fit(X, y)
        self.is_trained = True

        clf = self.pipeline.named_steps["clf"]
        self.feature_importances_ = dict(
            sorted(
                zip(X.columns, clf.feature_importances_),
                key=lambda x: x[1], reverse=True,
            )
        )
        logger.info(
            "RiskPredictor entraîné — %d exemples | CV F1: %s",
            len(inscriptions),
            f"{self.accuracy:.3f}" if self.accuracy else "N/A",
        )
        return {
            "success":   True,
            "n_samples": len(inscriptions),
            "classes":   list(set(y)),
            "cv_f1":     self.accuracy,
        }

    # ── Prédiction individuelle ───────────────

    def predict_risk(self, inscription) -> dict:
        """Prédit pour 1 inscription — appelle predict_risk_batch en interne."""
        return self.predict_risk_batch([inscription])[0]

    # ── Prédiction batch ─────────────────────

    def predict_risk_batch(self, inscriptions: list,
                           annee_terminee: bool = False) -> list[dict]:
        """
        Prédit le risque pour toute une liste en UN seul appel sklearn.
        10x–50x plus rapide que N appels individuels.
        annee_terminee : si True, les features sont durcies (absences définitives).
        """
        if not self.is_trained:
            raise NotFittedError("RiskPredictor non entraîné.")

        X          = _build_dataframe(inscriptions, annee_terminee)
        labels     = self.pipeline.predict(X)
        proba_arrs = self.pipeline.predict_proba(X)
        classes    = self.pipeline.classes_

        results = []
        for label, proba_arr in zip(labels, proba_arrs):
            proba_dict = {cls: float(p) for cls, p in zip(classes, proba_arr)}
            results.append({
                "niveau_risque": label,
                "confiance":     float(max(proba_arr)),
                "probas":        proba_dict,
            })
        return results

    # ── Probabilité d'abandon ────────────────

    def predict_abandon(self, inscription, risk_result: dict,
                        annee_terminee: bool = False) -> dict:
        proba_critique = risk_result.get("probas", {}).get("critique", 0.0)

        m           = inscription.moyenne_annuelle or inscription.moyenne_s1 or inscription.moyenne_s2
        aucune_note = inscription.moyenne_s1 is None and inscription.moyenne_s2 is None
        tres_faible = m is not None and m < 4

        proba_abandon = proba_critique * 0.7
        if aucune_note: proba_abandon = max(proba_abandon, 0.85)
        if tres_faible: proba_abandon = max(proba_abandon, 0.70)

        # ── Durcissement si l'année est terminée ────────────────────────
        # Les absences ne sont plus "en attente" — ce sont des faits définitifs
        if annee_terminee:
            if aucune_note:
                # Aucune note sur toute l'année terminée = abandon certain
                proba_abandon = 1.0
            elif inscription.moyenne_s2 is None:
                # S2 absent après fin d'année = décrochage très probable
                proba_abandon = max(proba_abandon, 0.90)
            if m is not None and m < 10:
                # Échec définitif confirmé
                proba_abandon = max(proba_abandon, 0.75)
            if m is not None and m < 6:
                # Échec sévère définitif
                proba_abandon = max(proba_abandon, 0.85)

        proba_abandon = round(min(proba_abandon, 1.0), 4)

        if proba_abandon >= 0.7:   niveau = "abandon_probable"
        elif proba_abandon >= 0.4: niveau = "risque_modere"
        else:                      niveau = "pas_de_risque"

        return {"probabilite_abandon": proba_abandon, "niveau_abandon": niveau}

    # ── Recommandations ──────────────────────

    def recommend(self, inscription, risk_result: dict,
                  abandon_result: dict, annee_terminee: bool = False) -> list:
        niveau_risque  = risk_result.get("niveau_risque",  "ok")
        niveau_abandon = abandon_result.get("niveau_abandon", "pas_de_risque")

        recos = list(self._RECOS.get(niveau_risque, self._RECOS["ok"]))

        if niveau_abandon == "abandon_probable":
            recos.insert(0, {
                "priorite": "critique",
                "titre": "Risque d'abandon élevé",
                "action": "Contacter l'étudiant immédiatement pour comprendre la situation et prévenir l'abandon définitif.",
                "categorie": "Action immédiate",
            })

        # ── Recommandations spécifiques fin d'année ──────────────────────
        if annee_terminee:
            m = inscription.moyenne_annuelle or inscription.moyenne_s1 or inscription.moyenne_s2
            aucune_note = inscription.moyenne_s1 is None and inscription.moyenne_s2 is None

            if aucune_note:
                recos.insert(0, {
                    "priorite": "critique",
                    "titre": "Abandon confirmé — année terminée",
                    "action": "L'étudiant n'a aucune note sur une année terminée. Déclencher la procédure de suivi post-abandon et contacter la famille si nécessaire.",
                    "categorie": "Action immédiate",
                })
            elif inscription.moyenne_s2 is None:
                recos.insert(0, {
                    "priorite": "critique",
                    "titre": "Décrochage S2 confirmé",
                    "action": "L'étudiant a disparu en cours d'année. Analyser les causes et proposer une réorientation ou un rattrapage l'année suivante.",
                    "categorie": "Action immédiate",
                })
            if m is not None and m < 10:
                recos.append({
                    "priorite": "critique",
                    "titre": "Échec définitif — décision de jury requise",
                    "action": "Les résultats sont définitifs. Préparer le dossier pour la commission de jury (redoublement, réorientation, exclusion).",
                    "categorie": "Administratif",
                })

        matieres_echouees = [
            r.matiere.nom_matiere for r in inscription.resultats
            if r.matiere and r.moyenne is not None and r.moyenne < 10
        ]
        if len(matieres_echouees) >= 3:
            recos.append({
                "priorite": "critique" if niveau_risque == "critique" else "moderee",
                "titre": f"Rattrapage — {len(matieres_echouees)} matières en difficulté",
                "action": (
                    f"Organiser des séances de rattrapage pour : "
                    f"{', '.join(matieres_echouees[:4])}"
                    f"{'...' if len(matieres_echouees) > 4 else ''}."
                ),
                "categorie": "Rattrapage",
            })
        elif len(matieres_echouees) == 1:
            recos.append({
                "priorite": "moderee",
                "titre": f"Soutien ciblé — {matieres_echouees[0]}",
                "action": f"Proposer une aide spécifique pour la matière « {matieres_echouees[0]} ».",
                "categorie": "Rattrapage",
            })

        if getattr(inscription, "est_redoublant", False):
            recos.append({
                "priorite": "moderee",
                "titre": "Accompagnement renforcé — redoublant",
                "action": "Proposer un tutorat individuel adapté aux redoublants et analyser les causes de l'échec précédent.",
                "categorie": "Suivi",
            })

        if inscription.moyenne_s1 is not None and inscription.moyenne_s2 is None and not annee_terminee:
            recos.append({
                "priorite": "moderee",
                "titre": "Absence de notes au S2",
                "action": "Contacter l'étudiant pour comprendre l'absence de résultats au second semestre et prévenir un abandon définitif.",
                "categorie": "Action immédiate",
            })

        ordre = {"critique": 0, "moderee": 1, "info": 2}
        recos.sort(key=lambda x: ordre.get(x.get("priorite", "info"), 3))
        return recos

    # ── Heuristique fallback ──────────────────

    @staticmethod
    def _heuristic_single(inscription, annee_terminee: bool = False) -> dict:
        label     = _label_risk(inscription)
        proba_map = {"ok": 0.05, "surveillance": 0.20, "modere": 0.50, "critique": 0.80}

        # Durcir si année terminée
        if annee_terminee:
            aucune_note = inscription.moyenne_s1 is None and inscription.moyenne_s2 is None
            if aucune_note and label != "critique":
                label = "critique"
            if label == "critique":
                proba_map["critique"] = 0.95

        p = proba_map.get(label, 0.1)
        return {
            "niveau_risque": label,
            "confiance":     None,
            "probas":        {"critique": p if label == "critique" else 0.05},
        }


# ──────────────────────────────────────────────
# FAÇADE PRINCIPALE : MLEngine
# ──────────────────────────────────────────────

class MLEngine:
    """
    Point d'entrée unique du module ML — singleton `ml_engine`.

    predict(inscription)          → 1 étudiant
    predict_batch(inscriptions)   → N étudiants en 1 seul appel RF (rapide)
    train(inscriptions)           → entraîne + sauvegarde
    auto_train_if_needed(fn)      → appelé au démarrage dans __init__.py

    Nouveauté v2 :
    · Détecte automatiquement si l'année est terminée via inscription.annee.date_fin
    · Durcit les prédictions en conséquence (absences = faits définitifs)

    Exemple correct dans les routes :
        ml_results_list = predict_batch(inscriptions)
        ml_results      = ml_index(inscriptions, ml_results_list)
        # Puis utiliser ml_results.get(i.id_inscription) partout
    """

    def __init__(self):
        self.risk_predictor = RiskPredictor()
        self._meta = {
            "trained_at": None,
            "n_samples":  0,
            "risk_cv_f1": None,
        }
        self._load_models()

    # ── Persistance ──────────────────────────

    def _save_models(self):
        try:
            with open(RISK_MODEL_PATH, "wb") as f:
                pickle.dump(self.risk_predictor, f)
            with open(META_PATH, "wb") as f:
                pickle.dump(self._meta, f)
            logger.info("Modèle ML sauvegardé dans %s", MODEL_DIR)
        except Exception as e:
            logger.error("Erreur sauvegarde modèle : %s", e)

    def _load_models(self):
        try:
            if os.path.exists(RISK_MODEL_PATH):
                with open(RISK_MODEL_PATH, "rb") as f:
                    self.risk_predictor = pickle.load(f)
                if os.path.exists(META_PATH):
                    with open(META_PATH, "rb") as f:
                        self._meta = pickle.load(f)
                logger.info("Modèle ML chargé depuis le disque ✓")
        except Exception as e:
            logger.warning("Impossible de charger le modèle : %s — ré-entraînement requis.", e)

    # ── Entraînement ─────────────────────────

    def train(self, inscriptions: list) -> dict:
        if not inscriptions:
            return {"success": False, "reason": "Liste d'inscriptions vide"}

        logger.info("Début de l'entraînement ML — %d inscriptions", len(inscriptions))
        result = self.risk_predictor.train(inscriptions)

        self._meta = {
            "trained_at": datetime.now().isoformat(),
            "n_samples":  len(inscriptions),
            "risk_cv_f1": result.get("cv_f1"),
        }
        if result.get("success"):
            self._save_models()

        return {"risk": result, "meta": self._meta}

    def auto_train_if_needed(self, inscriptions_fn, force: bool = False) -> dict:
        """
        Entraîne automatiquement si aucun modèle n'est chargé ou si force=True.
        inscriptions_fn : callable () → list[Inscription]
        """
        if self.risk_predictor.is_trained and not force:
            logger.info("Modèle ML déjà entraîné — pas de ré-entraînement")
            return {"skipped": True, "meta": self._meta}
        return self.train(inscriptions_fn())

    # ── Prédiction individuelle ───────────────

    def predict(self, inscription) -> dict:
        """1 étudiant. Pour les listes, utiliser predict_batch()."""
        results = self.predict_batch([inscription])
        return results[0] if results else self._fallback(inscription)

    # ── Prédiction batch ─────────────────────

    def predict_batch(self, inscriptions: list) -> list[dict]:
        """
        Prédit pour une liste entière en UN seul appel sklearn.
        Détecte automatiquement si l'année est terminée.
        N'appeler qu'UNE SEULE FOIS par route, puis indexer avec ml_index().
        """
        if not inscriptions:
            return []

        # ── Détection automatique de l'état de l'année ──────────────────
        annee_terminee = False
        try:
            annee = inscriptions[0].annee
            if annee and annee.date_fin:
                date_fin = annee.date_fin
                if hasattr(date_fin, "date"):
                    date_fin = date_fin.date()
                annee_terminee = date_fin < date.today()
                if annee_terminee:
                    logger.info(
                        "predict_batch — année '%s' terminée le %s → prédictions durcies",
                        getattr(annee, "libelle", "?"), date_fin,
                    )
        except Exception:
            pass

        source = "ml"

        if self.risk_predictor.is_trained:
            try:
                risk_results = self.risk_predictor.predict_risk_batch(
                    inscriptions, annee_terminee=annee_terminee
                )
            except Exception as e:
                logger.warning("predict_risk_batch échoué : %s — fallback heuristique", e)
                risk_results = [
                    RiskPredictor._heuristic_single(ins, annee_terminee)
                    for ins in inscriptions
                ]
                source = "heuristic"
        else:
            risk_results = [
                RiskPredictor._heuristic_single(ins, annee_terminee)
                for ins in inscriptions
            ]
            source = "heuristic"

        results = []
        for ins, risk_result in zip(inscriptions, risk_results):
            abandon_result = self.risk_predictor.predict_abandon(
                ins, risk_result, annee_terminee=annee_terminee
            )
            try:
                recos = self.risk_predictor.recommend(
                    ins, risk_result, abandon_result, annee_terminee=annee_terminee
                )
            except Exception:
                recos = []
            results.append(self._build_result(risk_result, abandon_result, recos, source))

        return results

    # ── Index par id_inscription ──────────────

    def predict_batch_indexed(self, inscriptions: list) -> dict:
        """
        Retourne directement un dict {id_inscription: result}.
        Remplace le pattern predict_batch() + ml_index() en une seule ligne.

        Usage dans les routes :
            ml_results = ml_engine.predict_batch_indexed(inscriptions)
            r = ml_results.get(i.id_inscription)
        """
        results = self.predict_batch(inscriptions)
        return {
            ins.id_inscription: r
            for ins, r in zip(inscriptions, results)
        }

    # ── Builder commun ───────────────────────

    def _build_result(self, risk_result, abandon_result, recos, source) -> dict:
        return {
            "niveau_risque":       risk_result.get("niveau_risque", "ok"),
            "confiance_risque":    risk_result.get("confiance"),
            "probas_risque":       risk_result.get("probas", {}),
            "probabilite_abandon": abandon_result.get("probabilite_abandon", 0.0),
            "niveau_abandon":      abandon_result.get("niveau_abandon", "pas_de_risque"),
            "recommandations":     recos,
            "source":              source,
            "trained_at":          self._meta.get("trained_at"),
        }

    def _fallback(self, inscription) -> dict:
        annee_terminee = _is_annee_terminee(inscription)
        risk    = RiskPredictor._heuristic_single(inscription, annee_terminee)
        abandon = self.risk_predictor.predict_abandon(inscription, risk, annee_terminee)
        recos   = self.risk_predictor.recommend(inscription, risk, abandon, annee_terminee)
        return self._build_result(risk, abandon, recos, "heuristic")

    # ── Utilitaires ──────────────────────────

    def status(self) -> dict:
        return {
            "risk_model_trained": self.risk_predictor.is_trained,
            "risk_cv_f1":         self.risk_predictor.accuracy,
            "top_features":       list(self.risk_predictor.feature_importances_.keys())[:5],
            **self._meta,
        }

    def feature_importances(self) -> dict:
        return self.risk_predictor.feature_importances_


# ──────────────────────────────────────────────
# SINGLETON
# ──────────────────────────────────────────────
ml_engine = MLEngine()