"""
Data Warehouse - Schéma en étoile
BD : iuadecis_dw  (bind_key = 'dw')

Tables de dimensions :
  - DimEtudiant
  - DimFiliere
  - DimNiveau
  - DimAnnee
  - DimMatiere
  - DimTemps
  - DimSession       ← AJOUT : distingue session normale vs rattrapage

Table de faits :
  - FaitResultatEtudiant   (cœur des analyses)
  - FaitAbsence            (suivi des absences)
"""

from datetime import datetime
from IUAInsight import db


# ══════════════════════════════════════════════
#  DIMENSIONS
# ══════════════════════════════════════════════

class DimEtudiant(db.Model):
    """Dimension Étudiant — qui est l'étudiant ?"""
    __tablename__ = 'dim_etudiant'
    __bind_key__  = 'dw'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_etudiant     = db.Column(db.Integer, nullable=False, index=True)   # clé naturelle OLTP
    matricule       = db.Column(db.String(20), nullable=False)
    nom             = db.Column(db.String(50),  nullable=False)
    prenom          = db.Column(db.String(50),  nullable=False)
    genre           = db.Column(db.String(10))
    annee_naissance = db.Column(db.Integer)
    nationalite     = db.Column(db.String(100))
    # SCD type 1 — on écrase si changement
    charge_at = db.Column(db.DateTime, default=datetime.utcnow)

    faits = db.relationship('FaitResultatEtudiant', backref='etudiant', lazy='dynamic')

    def __repr__(self):
        return f"<DimEtudiant {self.matricule} - {self.nom} {self.prenom}>"


class DimFiliere(db.Model):
    """Dimension Filière"""
    __tablename__ = 'dim_filiere'
    __bind_key__  = 'dw'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_filiere     = db.Column(db.Integer, nullable=False, index=True)
    nom_filiere    = db.Column(db.String(100), nullable=False)
    nom_specialite = db.Column(db.String(100), nullable=True)
    charge_at      = db.Column(db.DateTime, default=datetime.utcnow)

    faits = db.relationship('FaitResultatEtudiant', backref='filiere', lazy='dynamic')

    def __repr__(self):
        return f"<DimFiliere {self.nom_filiere}>"


class DimNiveau(db.Model):
    """Dimension Niveau d'études"""
    __tablename__ = 'dim_niveau'
    __bind_key__  = 'dw'

    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_niveau         = db.Column(db.Integer, nullable=False, index=True)
    libelle           = db.Column(db.String(10),  nullable=False)
    credits_requis    = db.Column(db.Integer, default=60)
    credits_admission = db.Column(db.Integer, default=47)
    ordre             = db.Column(db.Integer, default=0)
    charge_at         = db.Column(db.DateTime, default=datetime.utcnow)

    faits = db.relationship('FaitResultatEtudiant', backref='niveau', lazy='dynamic')

    def __repr__(self):
        return f"<DimNiveau {self.libelle}>"


class DimAnnee(db.Model):
    """Dimension Année scolaire"""
    __tablename__ = 'dim_annee'
    __bind_key__  = 'dw'

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_annee   = db.Column(db.Integer, nullable=False, index=True)
    libelle    = db.Column(db.String(20), nullable=False)
    date_debut = db.Column(db.Date)
    date_fin   = db.Column(db.Date)
    charge_at  = db.Column(db.DateTime, default=datetime.utcnow)

    faits = db.relationship('FaitResultatEtudiant', backref='annee', lazy='dynamic')

    def __repr__(self):
        return f"<DimAnnee {self.libelle}>"


class DimMatiere(db.Model):
    """Dimension Matière"""
    __tablename__ = 'dim_matiere'
    __bind_key__  = 'dw'

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_matiere   = db.Column(db.Integer, nullable=False, index=True)
    nom_matiere  = db.Column(db.String(100), nullable=False)
    code_matiere = db.Column(db.String(20))
    credit       = db.Column(db.Integer, default=1)
    coefficient  = db.Column(db.Float, default=1.0)
    nom_ue       = db.Column(db.String(100))
    nom_semestre = db.Column(db.String(10))
    charge_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DimMatiere {self.nom_matiere}>"


class DimTemps(db.Model):
    """Dimension Temps (date du chargement ETL)"""
    __tablename__ = 'dim_temps'
    __bind_key__  = 'dw'

    id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date      = db.Column(db.Date, unique=True, nullable=False)
    jour      = db.Column(db.Integer)
    mois      = db.Column(db.Integer)
    annee     = db.Column(db.Integer)
    trimestre = db.Column(db.Integer)
    nom_mois  = db.Column(db.String(20))

    def __repr__(self):
        return f"<DimTemps {self.date}>"


# ══════════════════════════════════════════════
#  NOUVELLE DIMENSION : SESSION
# ══════════════════════════════════════════════

class DimSession(db.Model):
    """
    Dimension Session — distingue session normale et session de rattrapage.
    Nécessaire pour que les statuts 'Ajourné' et 'Admis (dettes)' soient
    correctement calculés dans le DW (les résultats après rattrapage changeant
    les crédits validés et donc le statut final de l'étudiant).
    """
    __tablename__ = 'dim_session'
    __bind_key__  = 'dw'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_session     = db.Column(db.Integer, nullable=False, index=True)  # clé naturelle OLTP
    libelle        = db.Column(db.String(20), nullable=False)           # ex: "Session 1", "Rattrapage"
    est_rattrapage = db.Column(db.Boolean, default=False, nullable=False)
    charge_at      = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DimSession {self.libelle} (rattrapage={self.est_rattrapage})>"


# ══════════════════════════════════════════════
#  TABLE DE FAITS PRINCIPALE
# ══════════════════════════════════════════════

class FaitResultatEtudiant(db.Model):
    """
    Table de faits — résultats académiques par étudiant / filière / niveau / année.
    Granularité : 1 ligne = 1 inscription (étudiant × niveau × année scolaire)
    """
    __tablename__ = 'fait_resultat_etudiant'
    __bind_key__  = 'dw'
    __table_args__ = (
        db.UniqueConstraint('id_inscription', name='uq_fait_inscription'),
    )

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_inscription = db.Column(db.Integer, nullable=False, index=True)  # clé naturelle OLTP

    # Clés étrangères vers les dimensions
    id_dim_etudiant = db.Column(db.Integer, db.ForeignKey('dim_etudiant.id'), nullable=False)
    id_dim_filiere  = db.Column(db.Integer, db.ForeignKey('dim_filiere.id'),  nullable=True)
    id_dim_niveau   = db.Column(db.Integer, db.ForeignKey('dim_niveau.id'),   nullable=False)
    id_dim_annee    = db.Column(db.Integer, db.ForeignKey('dim_annee.id'),    nullable=False)

    # ── Mesures session normale ──────────────────────────────────
    moyenne_s1       = db.Column(db.Float, nullable=True)
    moyenne_s2       = db.Column(db.Float, nullable=True)
    moyenne_annuelle = db.Column(db.Float, nullable=True)

    credits_valides_s1 = db.Column(db.Integer, default=0)
    credits_valides_s2 = db.Column(db.Integer, default=0)
    credits_valides    = db.Column(db.Integer, default=0)
    credits_requis     = db.Column(db.Integer, default=60)

    taux_reussite_credits = db.Column(db.Float, nullable=True)  # credits_valides / credits_requis * 100

    # ── Mesures session de rattrapage (AJOUT) ────────────────────
    # Permet de distinguer les ajournés vrais des ajournés rattrapés
    moyenne_s1_rattrapage  = db.Column(db.Float, nullable=True)   # moyenne S1 après rattrapage
    moyenne_s2_rattrapage  = db.Column(db.Float, nullable=True)   # moyenne S2 après rattrapage
    credits_valides_s1_rat = db.Column(db.Integer, default=0)     # crédits S1 après rattrapage
    credits_valides_s2_rat = db.Column(db.Integer, default=0)     # crédits S2 après rattrapage
    credits_valides_rat    = db.Column(db.Integer, default=0)     # total crédits après rattrapage
    a_rattrapage_s1        = db.Column(db.Boolean, default=False) # a passé le rattrapage S1
    a_rattrapage_s2        = db.Column(db.Boolean, default=False) # a passé le rattrapage S2

    # ── Attributs dégénérés (pas de dimension séparée) ──────────
    mention        = db.Column(db.String(30), nullable=True)
    statut         = db.Column(db.String(30), nullable=True)   # Admis / Ajourné / Admis (dettes)...
    est_redoublant = db.Column(db.Boolean, default=False)
    est_admis      = db.Column(db.Boolean, default=False)
    est_ajourne    = db.Column(db.Boolean, default=False)
    est_en_dette   = db.Column(db.Boolean, default=False)      # AJOUT : Admis (dettes)
    credits_dus    = db.Column(db.Integer, default=0)          # AJOUT : nb crédits manquants si dettes

    # ── Métadonnées ETL ─────────────────────────────────────────
    charge_at = db.Column(db.DateTime, default=datetime.utcnow)
    maj_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FaitResultat insc={self.id_inscription} moy={self.moyenne_annuelle} statut={self.statut}>"


# ══════════════════════════════════════════════
#  TABLE DE FAITS SECONDAIRE : ABSENCES
# ══════════════════════════════════════════════
'''
class FaitAbsence(db.Model):
    __tablename__ = 'fait_absence'
    __bind_key__  = 'dw'

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_absence = db.Column(db.Integer, nullable=False, index=True)  # clé naturelle OLTP

    id_dim_etudiant = db.Column(db.Integer, db.ForeignKey('dim_etudiant.id'), nullable=False)
    id_dim_matiere  = db.Column(db.Integer, db.ForeignKey('dim_matiere.id'),  nullable=False)
    id_dim_temps    = db.Column(db.Integer, db.ForeignKey('dim_temps.id'),    nullable=True)

    # Mesures
    nb_absences       = db.Column(db.Integer, default=1)
    nb_justifiees     = db.Column(db.Integer, default=0)
    nb_non_justifiees = db.Column(db.Integer, default=0)

    charge_at = db.Column(db.DateTime, default=datetime.utcnow)

    etudiant = db.relationship('DimEtudiant', lazy='joined')
    matiere  = db.relationship('DimMatiere',  lazy='joined')

    def __repr__(self):
        return f"<FaitAbsence etudiant={self.id_dim_etudiant} matiere={self.id_dim_matiere}>'''