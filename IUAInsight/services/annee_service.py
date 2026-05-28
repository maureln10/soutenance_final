import logging
from IUAInsight import db
from IUAInsight.models import AnneeScolaire, Inscription

logger = logging.getLogger(__name__)


def cloture_annee(id_annee):
    """
    Clôture une année scolaire et calcule le bilan académique
    en se basant sur statut_simple du modèle Inscription.
    """
    try:
        annee = db.session.get(AnneeScolaire, id_annee)
        if not annee:
            return {"success": False, "erreur": f"Année {id_annee} introuvable"}

        from sqlalchemy.orm import joinedload, selectinload
        inscriptions = (
            Inscription.query
            .filter_by(id_annee=id_annee)
            .options(
                joinedload(Inscription.niveau),
                selectinload(Inscription.resultats),
            )
            .all()
        )

        # Recalcul préalable pour s'assurer que credits_valides est à jour
        for ins in inscriptions:
            ins.recalculer_tout()

        admis        = 0
        admis_dettes = 0
        redoublants  = 0
        abandons     = 0

        for ins in inscriptions:
            statut = ins.statut_simple
            if statut == "Abandon":
                abandons += 1
            elif statut == "Admis":
                admis += 1
            elif statut == "Admis (dettes)":
                admis_dettes += 1
            elif statut in ("Redoublant", "Ajourné S1", "Ajourné S2", "Ajourné S1 & S2"):
                redoublants += 1
            # "En cours" ignoré — année pas encore terminée pour eux

        annee.active = False
        db.session.commit()

        logger.info(
            "Clôture %s — admis:%d dettes:%d redoublants:%d abandons:%d",
            annee.libelle, admis, admis_dettes, redoublants, abandons
        )

        return {
            "success":      True,
            "admis":        admis,
            "admis_dettes": admis_dettes,
            "redoublants":  redoublants,
            "abandons":     abandons,
        }

    except Exception as e:
        db.session.rollback()
        logger.error("Erreur clôture année %s : %s", id_annee, e)
        return {"success": False, "erreur": str(e)}