"""
ETL - Loader
Charge les données transformées dans le Data Warehouse (iuainsight_dw).
Stratégie : UPSERT (insert ou mise à jour si déjà existant)
"""

from datetime import datetime
from IUAInsight import db
from IUAInsight.Warehouse.models import (
    DimEtudiant, DimFiliere, DimNiveau, DimAnnee,
    DimMatiere, DimTemps,
    FaitResultatEtudiant
)


class Loader:
    """Charge les données dans le DW avec stratégie UPSERT."""

    # ══════════════════════════════════════════
    #  CHARGEMENT DES DIMENSIONS
    # ══════════════════════════════════════════

    def load_dim_etudiants(self, records):
        """Charge DimEtudiant — UPSERT sur id_etudiant."""
        count_new, count_upd = 0, 0
        for r in records:
            existing = DimEtudiant.query.filter_by(id_etudiant=r['id_etudiant']).first()
            if existing:
                existing.matricule       = r['matricule']
                existing.nom             = r['nom']
                existing.prenom          = r['prenom']
                existing.genre           = r['genre']
                existing.annee_naissance = r['annee_naissance']
                existing.nationalite     = r['nationalite']
                count_upd += 1
            else:
                db.session.add(DimEtudiant(**{k: v for k, v in r.items()}))
                count_new += 1
        db.session.commit()
        print(f"[Loader] DimEtudiant → {count_new} insérés, {count_upd} mis à jour")
        return count_new, count_upd

    def load_dim_filieres(self, records):
        """Charge DimFiliere — UPSERT sur (id_filiere, nom_specialite)."""
        count_new, count_upd = 0, 0
        for r in records:
            existing = DimFiliere.query.filter_by(
                id_filiere=r['id_filiere'],
                nom_specialite=r['nom_specialite']
            ).first()
            if existing:
                existing.nom_filiere    = r['nom_filiere']
                existing.nom_specialite = r['nom_specialite']
                count_upd += 1
            else:
                db.session.add(DimFiliere(**{k: v for k, v in r.items()}))
                count_new += 1
        db.session.commit()
        print(f"[Loader] DimFiliere → {count_new} insérés, {count_upd} mis à jour")
        return count_new, count_upd

    def load_dim_niveaux(self, records):
        """Charge DimNiveau — UPSERT sur id_niveau."""
        count_new, count_upd = 0, 0
        for r in records:
            existing = DimNiveau.query.filter_by(id_niveau=r['id_niveau']).first()
            if existing:
                existing.libelle           = r['libelle']
                existing.credits_requis    = r['credits_requis']
                existing.credits_admission = r['credits_admission']
                existing.ordre             = r['ordre']
                count_upd += 1
            else:
                db.session.add(DimNiveau(**{k: v for k, v in r.items()}))
                count_new += 1
        db.session.commit()
        print(f"[Loader] DimNiveau → {count_new} insérés, {count_upd} mis à jour")
        return count_new, count_upd

    def load_dim_annees(self, records):
        """Charge DimAnnee — UPSERT sur id_annee."""
        count_new, count_upd = 0, 0
        for r in records:
            existing = DimAnnee.query.filter_by(id_annee=r['id_annee']).first()
            if existing:
                existing.libelle    = r['libelle']
                existing.date_debut = r['date_debut']
                existing.date_fin   = r['date_fin']
                count_upd += 1
            else:
                db.session.add(DimAnnee(**{k: v for k, v in r.items()}))
                count_new += 1
        db.session.commit()
        print(f"[Loader] DimAnnee → {count_new} insérés, {count_upd} mis à jour")
        return count_new, count_upd

    def load_dim_matieres(self, records):
        """Charge DimMatiere — UPSERT sur id_matiere."""
        count_new, count_upd = 0, 0
        for r in records:
            existing = DimMatiere.query.filter_by(id_matiere=r['id_matiere']).first()
            if existing:
                existing.nom_matiere  = r['nom_matiere']
                existing.code_matiere = r['code_matiere']
                existing.credit       = r['credit']
                existing.coefficient  = r['coefficient']
                existing.nom_ue       = r['nom_ue']
                existing.nom_semestre = r['nom_semestre']
                count_upd += 1
            else:
                db.session.add(DimMatiere(**{k: v for k, v in r.items()}))
                count_new += 1
        db.session.commit()
        print(f"[Loader] DimMatiere → {count_new} insérés, {count_upd} mis à jour")
        return count_new, count_upd

    def load_dim_temps(self, records):
        """Charge DimTemps — UPSERT sur date."""
        count_new, count_upd = 0, 0
        for r in records:
            existing = DimTemps.query.filter_by(date=r['date']).first()
            if not existing:
                db.session.add(DimTemps(**{k: v for k, v in r.items()}))
                count_new += 1
        db.session.commit()
        print(f"[Loader] DimTemps → {count_new} insérés, {count_upd} mis à jour")
        return count_new, count_upd

    # ══════════════════════════════════════════
    #  RÉSOLUTION DES IDs DE DIMENSIONS
    # ══════════════════════════════════════════

    def _build_lookup_etudiants(self):
        return {e.id_etudiant: e.id for e in DimEtudiant.query.all()}

    def _build_lookup_filieres(self):
        lookup = {}
        for f in DimFiliere.query.all():
            if f.id_filiere not in lookup:
                lookup[f.id_filiere] = f.id
        return lookup

    def _build_lookup_niveaux(self):
        return {n.id_niveau: n.id for n in DimNiveau.query.all()}

    def _build_lookup_annees(self):
        return {a.id_annee: a.id for a in DimAnnee.query.all()}

    def _build_lookup_matieres(self):
        return {m.id_matiere: m.id for m in DimMatiere.query.all()}

    def _build_lookup_temps(self):
        return {t.date: t.id for t in DimTemps.query.all()}

    # ══════════════════════════════════════════
    #  CHARGEMENT DES FAITS
    # ══════════════════════════════════════════

    def load_faits_resultats(self, records):
        """
        Charge FaitResultatEtudiant — UPSERT sur id_inscription.
        Résout les FK vers les dimensions avant insertion.
        """
        lk_etu = self._build_lookup_etudiants()
        lk_fil = self._build_lookup_filieres()
        lk_niv = self._build_lookup_niveaux()
        lk_ann = self._build_lookup_annees()

        count_new, count_upd, count_skip = 0, 0, 0

        for r in records:
            id_dim_etu = lk_etu.get(r['_id_etudiant'])
            id_dim_fil = lk_fil.get(r['_id_filiere'])
            id_dim_niv = lk_niv.get(r['_id_niveau'])
            id_dim_ann = lk_ann.get(r['_id_annee'])

            if not id_dim_etu or not id_dim_niv or not id_dim_ann:
                count_skip += 1
                continue

            existing = FaitResultatEtudiant.query.filter_by(
                id_inscription=r['id_inscription']
            ).first()

            if existing:
                existing.moyenne_s1            = r['moyenne_s1']
                existing.moyenne_s2            = r['moyenne_s2']
                existing.moyenne_annuelle      = r['moyenne_annuelle']
                existing.credits_valides_s1    = r['credits_valides_s1']
                existing.credits_valides_s2    = r['credits_valides_s2']
                existing.credits_valides       = r['credits_valides']
                existing.credits_requis        = r['credits_requis']
                existing.taux_reussite_credits = r['taux_reussite_credits']
                existing.mention               = r['mention']
                existing.statut                = r['statut']
                existing.est_redoublant        = r['est_redoublant']
                existing.est_admis             = r['est_admis']
                existing.est_ajourne           = r['est_ajourne']
                existing.est_en_dette          = r['est_en_dette']   # corrigé
                existing.credits_dus           = r['credits_dus']    # corrigé
                existing.maj_at                = datetime.utcnow()
                count_upd += 1
            else:
                db.session.add(FaitResultatEtudiant(
                    id_inscription         = r['id_inscription'],
                    id_dim_etudiant        = id_dim_etu,
                    id_dim_filiere         = id_dim_fil,
                    id_dim_niveau          = id_dim_niv,
                    id_dim_annee           = id_dim_ann,
                    moyenne_s1             = r['moyenne_s1'],
                    moyenne_s2             = r['moyenne_s2'],
                    moyenne_annuelle       = r['moyenne_annuelle'],
                    credits_valides_s1     = r['credits_valides_s1'],
                    credits_valides_s2     = r['credits_valides_s2'],
                    credits_valides        = r['credits_valides'],
                    credits_requis         = r['credits_requis'],
                    taux_reussite_credits  = r['taux_reussite_credits'],
                    mention                = r['mention'],
                    statut                 = r['statut'],
                    est_redoublant         = r['est_redoublant'],
                    est_admis              = r['est_admis'],
                    est_ajourne            = r['est_ajourne'],
                    est_en_dette           = r['est_en_dette'],      # corrigé
                    credits_dus            = r['credits_dus'],       # corrigé
                    charge_at              = r['charge_at'],
                    maj_at                 = r['maj_at'],
                ))
                count_new += 1

        db.session.commit()
        print(f"[Loader] FaitResultatEtudiant → {count_new} insérés, {count_upd} mis à jour, {count_skip} ignorés")
        return count_new, count_upd

 

    # ══════════════════════════════════════════
    #  POINT D'ENTRÉE PRINCIPAL
    # ══════════════════════════════════════════

    def load_all(self, transformed):
        """
        Charge toutes les données dans le DW dans le bon ordre.
        (Dimensions d'abord, faits ensuite)
        """
        print(f"\n{'='*50}")
        print(f"[Loader] Début du chargement dans le DW")
        print(f"{'='*50}")

        # 1. Dimensions (ordre important pour les FK)
        self.load_dim_etudiants(transformed['dim_etudiants'])
        self.load_dim_filieres( transformed['dim_filieres'])
        self.load_dim_niveaux(  transformed['dim_niveaux'])
        self.load_dim_annees(   transformed['dim_annees'])
        self.load_dim_matieres( transformed['dim_matieres'])
        self.load_dim_temps(    transformed['dim_temps'])

        # 2. Faits (après toutes les dimensions)
        self.load_faits_resultats(transformed['faits_resultats'])


        print(f"[Loader] ✅ Chargement terminé dans iuadecis_dw")