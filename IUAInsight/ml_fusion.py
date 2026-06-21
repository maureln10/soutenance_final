"""
expert_ml_fusion.py — Fusion SystemeExpert + MLEngine
======================================================
Branche ml_models.py sur systeme_expert.py sans modifier aucun des deux.

Résultat unifié retourné par evaluer() :
{
    # ── Bloc Expert (LMD) ──────────────────────────────────────────
    "niveau_academique"    : "critique"|"modere"|"surveillance"|"ok",
    "regles_declenchees"   : ["Moyenne entre 6 et 10/20", ...],

    # ── Bloc ML ────────────────────────────────────────────────────
    "niveau_risque"        : "critique"|"modere"|"surveillance"|"ok",
    "confiance_risque"     : 0.87 | None,
    "probabilite_abandon"  : 0.34,
    "niveau_abandon"       : "pas_de_risque"|"risque_modere"|"abandon_probable",

    # ── Bloc fusion ────────────────────────────────────────────────
    "niveau_final"         : "critique"|"modere"|"surveillance"|"ok",
    "accord_expert_ml"     : True | False,
    "alerte_desaccord"     : None | "⚠️ Désaccord ...",

    # ── Recommandations fusionnées (dédupliquées, triées) ──────────
    "recommandations"      : [...],

    "source"               : "expert+ml" | "expert+heuristic",
}

Usage
-----
    from expert_ml_fusion import FusionEngine, fusion_engine

    # 1 étudiant
    result = fusion_engine.evaluer(inscription)

    # N étudiants (batch — rapide)
    results = fusion_engine.evaluer_batch(inscriptions)
    # → dict { id_inscription: result }

    # Entraîner le ML (à appeler au démarrage ou à la demande)
    fusion_engine.entrainer(inscriptions)
    fusion_engine.auto_entrainer_si_besoin(lambda: Inscription.objects.all())
"""

import logging
from expert_engine import expert_engine          # SystemeExpert singleton
from ml_models     import ml_engine              # MLEngine singleton

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# LOGIQUE DE FUSION
# ══════════════════════════════════════════════

# Ordre de sévérité (plus petit = plus grave)
_SEVERITE = {"critique": 0, "modere": 1, "surveillance": 2, "ok": 3}

# Correspondance niveau expert → niveau risque ML
_EXPERT_TO_ML = {
    "critique":    "critique",
    "modere":      "modere",
    "surveillance":"surveillance",
    "ok":          "ok",
}


def _niveau_max(n1: str, n2: str) -> str:
    """Retourne le niveau le plus sévère des deux."""
    return n1 if _SEVERITE.get(n1, 3) <= _SEVERITE.get(n2, 3) else n2


def _deduplication(recommandations: list) -> list:
    """Supprime les recommandations dont le titre est identique."""
    seen   = set()
    unique = []
    for r in recommandations:
        titre = r.get("titre", "")
        if titre not in seen:
            seen.add(titre)
            unique.append(r)
    return unique


def _trier_recos(recommandations: list) -> list:
    ordre = {"critique": 0, "moderee": 1, "info": 2}
    return sorted(recommandations, key=lambda r: ordre.get(r.get("priorite", "info"), 3))


def _fusionner(expert_result: dict, ml_result: dict) -> dict:
    """
    Fusionne les deux résultats en un dict unifié.
    · niveau_final = le plus sévère entre expert et ML
    · recommandations = union dédupliquée (expert en premier, ML en complément)
    · alerte si désaccord et confiance ML > 70 %
    """
    niveau_expert = expert_result.get("niveau_academique", "ok")
    niveau_ml     = ml_result.get("niveau_risque", "ok")
    confiance_ml  = ml_result.get("confiance_risque")

    niveau_final = _niveau_max(niveau_expert, niveau_ml)
    accord       = (_EXPERT_TO_ML.get(niveau_expert) == niveau_ml)

    alerte = None
    if not accord and confiance_ml and confiance_ml > 0.70:
        alerte = (
            f"⚠️ Désaccord expert/ML : "
            f"l'expert indique '{niveau_expert}' "
            f"mais le ML prédit '{niveau_ml}' "
            f"avec une confiance de {confiance_ml:.0%}. "
            f"Vérification manuelle recommandée."
        )
        logger.info("Désaccord expert/ML : %s vs %s (conf %.2f)", niveau_expert, niveau_ml, confiance_ml)

    # Union des recommandations : expert d'abord, ML en complément
    recos_expert = expert_result.get("recommandations", [])
    recos_ml     = ml_result.get("recommandations", [])
    recos_fusion = _trier_recos(_deduplication(recos_expert + recos_ml))

    source_ml = ml_result.get("source", "heuristic")
    source    = f"expert+{source_ml}"

    return {
        # Bloc expert
        "niveau_academique":   niveau_expert,
        "regles_declenchees":  expert_result.get("regles_declenchees", []),

        # Bloc ML
        "niveau_risque":       niveau_ml,
        "confiance_risque":    confiance_ml,
        "probabilite_abandon": ml_result.get("probabilite_abandon", 0.0),
        "niveau_abandon":      ml_result.get("niveau_abandon", "pas_de_risque"),
        "probas_risque":       ml_result.get("probas_risque", {}),

        # Bloc fusion
        "niveau_final":        niveau_final,
        "accord_expert_ml":    accord,
        "alerte_desaccord":    alerte,

        # Recommandations fusionnées
        "recommandations":     recos_fusion,

        "source":              source,
    }


# ══════════════════════════════════════════════
# MOTEUR DE FUSION
# ══════════════════════════════════════════════

class FusionEngine:
    """
    Orchestre SystemeExpert + MLEngine et retourne un résultat unifié.
    Ne modifie ni systeme_expert.py ni ml_models.py.
    """

    def __init__(self, expert=None, ml=None):
        self.expert = expert or expert_engine
        self.ml     = ml     or ml_engine

    # ── 1 étudiant ────────────────────────────────────────────────

    def evaluer(self, inscription) -> dict:
        """
        Évalue une inscription avec l'expert LMD + le ML.
        Retourne un dict unifié.
        """
        expert_result = self.expert.evaluer_statut(inscription)

        try:
            ml_result = self.ml.predict(inscription)
        except Exception as e:
            logger.warning("ML indisponible pour predict() : %s — fallback heuristique", e)
            ml_result = self.ml._fallback(inscription)

        return _fusionner(expert_result, ml_result)

    # ── N étudiants (batch) ───────────────────────────────────────

    def evaluer_batch(self, inscriptions: list) -> dict:
        """
        Évalue une liste d'inscriptions.
        Retourne un dict { id_inscription: result } — une seule passe ML (rapide).

        Usage dans les vues Django :
            ml_results = fusion_engine.evaluer_batch(inscriptions)
            for ins in inscriptions:
                r = ml_results.get(ins.id_inscription)
        """
        if not inscriptions:
            return {}

        # Expert : appel individuel (léger, règles Python)
        expert_results = {}
        for ins in inscriptions:
            try:
                expert_results[ins.id_inscription] = self.expert.evaluer_statut(ins)
            except Exception as e:
                logger.warning("Expert échoué pour %s : %s", ins.id_inscription, e)
                expert_results[ins.id_inscription] = {
                    "niveau_academique": "ok",
                    "recommandations":   [],
                    "regles_declenchees": [],
                    "source": "expert",
                }

        # ML : UN seul appel batch (rapide — RF vectorisé)
        try:
            ml_list    = self.ml.predict_batch(inscriptions)
            ml_results = {
                ins.id_inscription: r
                for ins, r in zip(inscriptions, ml_list)
            }
        except Exception as e:
            logger.warning("ML batch échoué : %s — fallback heuristique individuel", e)
            ml_results = {
                ins.id_inscription: self.ml._fallback(ins)
                for ins in inscriptions
            }

        # Fusion
        return {
            ins.id_inscription: _fusionner(
                expert_results.get(ins.id_inscription, {}),
                ml_results.get(ins.id_inscription, {}),
            )
            for ins in inscriptions
        }

    # ── Entraînement ──────────────────────────────────────────────

    def entrainer(self, inscriptions: list) -> dict:
        """Entraîne le ML et sauvegarde le modèle."""
        return self.ml.train(inscriptions)

    def auto_entrainer_si_besoin(self, inscriptions_fn, force: bool = False) -> dict:
        """
        Entraîne automatiquement si aucun modèle n'est chargé.
        À appeler dans apps.py → ready().

        Exemple dans app.py (Flask) :
            from expert_ml_fusion import fusion_engine
            from models import Inscription

            with app.app_context():
                fusion_engine.auto_entrainer_si_besoin(
                    lambda: Inscription.query
                        .options(
                            joinedload(Inscription.niveau),
                            joinedload(Inscription.annee),
                            joinedload(Inscription.resultats).joinedload(Resultat.matiere),
                        ).all()
                )
        """
        return self.ml.auto_train_if_needed(inscriptions_fn, force=force)

    # ── Statut ────────────────────────────────────────────────────

    def statut(self) -> dict:
        return self.ml.status()


# ══════════════════════════════════════════════
# SINGLETON
# ══════════════════════════════════════════════

fusion_engine = FusionEngine()