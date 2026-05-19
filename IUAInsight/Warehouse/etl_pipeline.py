"""
ETL Pipeline — Orchestrateur
Lance l'extraction, la transformation et le chargement en séquence.
"""

from datetime import datetime
from IUAInsight.etl.extractor   import Extractor
from IUAInsight.etl.transformer import Transformer
from IUAInsight.etl.loader      import Loader


class ETLPipeline:
    """
    Orchestre le pipeline ETL complet :
      OLTP (lmd1)  →  Extraction  →  Transformation  →  Chargement  →  DW (iuainsight_dw)
    """

    def __init__(self):
        self.extractor   = Extractor()
        self.transformer = Transformer()
        self.loader      = Loader()

    def run(self, annee_id=None):
        """
        Lance le pipeline complet.
        annee_id : filtre sur une année scolaire précise (None = tout)
        """
        debut = datetime.utcnow()
        print(f"\n{'#'*55}")
        print(f"#  ETL PIPELINE — Démarrage : {debut.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*55}")

        try:
            # ── Étape 1 : Extraction ──────────────────────────────
            raw_data = self.extractor.extract_all(annee_id=annee_id)

            # ── Étape 2 : Transformation ──────────────────────────
            transformed = self.transformer.transform_all(raw_data)

            # ── Étape 3 : Chargement ──────────────────────────────
            self.loader.load_all(transformed)

            fin = datetime.utcnow()
            duree = (fin - debut).seconds
            print(f"\n{'#'*55}")
            print(f"#  ETL PIPELINE ✅ Terminé en {duree}s")
            print(f"{'#'*55}\n")
            return True

        except Exception as e:
            print(f"\n[ETL Pipeline] ❌ Erreur : {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_incremental(self, annee_id):
        """
        Variante incrémentale : recharge uniquement une année donnée.
        Utile pour les mises à jour quotidiennes.
        """
        print(f"[ETL Pipeline] Mode incrémental — annee_id={annee_id}")
        return self.run(annee_id=annee_id)