"""
ETL - Extracteur
Lit les données brutes depuis la BD OLTP (lmd1)
"""

from IUAInsight import db
from IUAInsight.models import (
    Inscription, Etudiant, Filiere, Specialite,
    Niveau, AnneeScolaire, Matiere, Resultat,
    Absence, Nationalite, Semestre, UE
)


class Extractor:
    """Extrait toutes les données nécessaires depuis l'OLTP."""

    def extract_inscriptions(self, annee_id=None):
        """
        Retourne toutes les inscriptions avec leurs relations.
        Si annee_id est fourni, filtre sur cette année scolaire.
        """
        query = Inscription.query \
            .join(Etudiant,      Inscription.id_etudiant == Etudiant.id_etudiant) \
            .join(Niveau,        Inscription.id_niveau   == Niveau.id_niveau) \
            .join(AnneeScolaire, Inscription.id_annee    == AnneeScolaire.id_annee) \
            .outerjoin(Filiere,    Inscription.id_filiere   == Filiere.id_filiere) \
            .outerjoin(Specialite, Inscription.id_specialite == Specialite.id_specialite)

        if annee_id:
            query = query.filter(Inscription.id_annee == annee_id)

        inscriptions = query.all()
        print(f"[Extractor] {len(inscriptions)} inscriptions extraites.")
        return inscriptions

    def extract_etudiants(self):
        """Retourne tous les étudiants avec leur nationalité."""
        etudiants = Etudiant.query \
            .outerjoin(Nationalite, Etudiant.id_nationalite == Nationalite.id_nationalite) \
            .all()
        print(f"[Extractor] {len(etudiants)} étudiants extraits.")
        return etudiants

    def extract_filieres(self):
        """Retourne toutes les filières."""
        filieres = Filiere.query.all()
        print(f"[Extractor] {len(filieres)} filières extraites.")
        return filieres

    def extract_specialites(self):
        """Retourne toutes les spécialités."""
        specialites = Specialite.query.all()
        print(f"[Extractor] {len(specialites)} spécialités extraites.")
        return specialites

    def extract_niveaux(self):
        """Retourne tous les niveaux."""
        niveaux = Niveau.query.all()
        print(f"[Extractor] {len(niveaux)} niveaux extraits.")
        return niveaux

    def extract_annees(self):
        """Retourne toutes les années scolaires."""
        annees = AnneeScolaire.query.all()
        print(f"[Extractor] {len(annees)} années scolaires extraites.")
        return annees

    def extract_matieres(self):
        """Retourne toutes les matières avec UE et semestre."""
        matieres = Matiere.query \
            .outerjoin(UE,       Matiere.id_ue      == UE.id_ue) \
            .outerjoin(Semestre, Matiere.id_semestre == Semestre.id_semestre) \
            .all()
        print(f"[Extractor] {len(matieres)} matières extraites.")
        return matieres

    def extract_absences(self, annee_id=None):
        """
        Retourne toutes les absences.
        Filtre optionnel par année (via inscription).
        """
        query = Absence.query \
            .join(Etudiant, Absence.id_etudiant == Etudiant.id_etudiant) \
            .join(Matiere,  Absence.id_matiere  == Matiere.id_matiere)

        absences = query.all()
        print(f"[Extractor] {len(absences)} absences extraites.")
        return absences

    def extract_all(self, annee_id=None):
        """
        Point d'entrée principal : extrait tout en une fois.
        Retourne un dictionnaire avec toutes les données.
        """
        print(f"\n{'='*50}")
        print(f"[Extractor] Début de l'extraction (annee_id={annee_id})")
        print(f"{'='*50}")

        data = {
            'inscriptions': self.extract_inscriptions(annee_id),
            'etudiants':    self.extract_etudiants(),
            'filieres':     self.extract_filieres(),
            'specialites':  self.extract_specialites(),
            'niveaux':      self.extract_niveaux(),
            'annees':       self.extract_annees(),
            'matieres':     self.extract_matieres(),
            'absences':     self.extract_absences(annee_id),
        }

        total = sum(len(v) for v in data.values())
        print(f"[Extractor] ✅ Extraction terminée — {total} enregistrements au total.")
        return data