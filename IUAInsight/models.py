from datetime import date
from IUAInsight import db


# ==========================
# NATIONALITE
# ==========================
class Nationalite(db.Model):
    __tablename__  = 'nationalite'
    __bind_key__   = 'oltp'

    id_nationalite = db.Column(db.Integer, primary_key=True)
    pays           = db.Column(db.String(100), unique=True, nullable=False)
    code_iso       = db.Column(db.String(3))

    etudiants = db.relationship('Etudiant', backref='nationalite', lazy='select')

    def __repr__(self):
        return f"<Nationalite {self.pays}>"


# ==========================
# ETUDIANT
# ==========================
class Etudiant(db.Model):
    __tablename__ = 'etudiant'
    __bind_key__  = 'oltp'

    id_etudiant     = db.Column(db.Integer, primary_key=True)
    matricule       = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nom             = db.Column(db.String(50), nullable=False)
    prenom          = db.Column(db.String(50), nullable=False)
    annee_naissance = db.Column(db.Integer)
    genre           = db.Column(db.String(10))
    id_nationalite  = db.Column(db.Integer, db.ForeignKey('nationalite.id_nationalite', ondelete='SET NULL'), nullable=True)

    inscriptions = db.relationship('Inscription', backref='etudiant', lazy='select', cascade='all, delete-orphan')

    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}"

    @property
    def initiales(self):
        return f"{self.nom[0]}{self.prenom[0]}".upper() if self.nom and self.prenom else "?"

    def calculer_age(self):
        if self.annee_naissance:
            return date.today().year - self.annee_naissance
        return None

    def __repr__(self):
        return f"<Etudiant {self.matricule} - {self.nom_complet}>"


# ==========================
# FILIERE
# ==========================
class Filiere(db.Model):
    __tablename__ = 'filiere'
    __bind_key__  = 'oltp'

    id_filiere  = db.Column(db.Integer, primary_key=True)
    nom_filiere = db.Column(db.String(100), nullable=False, unique=True)

    specialites = db.relationship('Specialite',    backref='filiere', lazy='select')
    matieres    = db.relationship('Matiere',       backref='filiere', lazy='select')
    professeurs = db.relationship('Professeur',    backref='filiere', lazy='select')
    niveaux     = db.relationship('NiveauFiliere', backref='filiere', lazy='select')

    def __repr__(self):
        return f"<Filiere {self.nom_filiere}>"


# ==========================
# SPECIALITE
# ==========================
class Specialite(db.Model):
    __tablename__ = 'specialite'
    __bind_key__  = 'oltp'

    id_specialite  = db.Column(db.Integer, primary_key=True)
    nom_specialite = db.Column(db.String(100), nullable=False)
    id_filiere     = db.Column(db.Integer, db.ForeignKey('filiere.id_filiere', ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f"<Specialite {self.nom_specialite}>"


# ==========================
# NIVEAU
# ==========================
class Niveau(db.Model):
    __tablename__ = 'niveau'
    __bind_key__  = 'oltp'

    id_niveau         = db.Column(db.Integer, primary_key=True)
    libelle           = db.Column(db.String(10), nullable=False, unique=True)
    credits_requis    = db.Column(db.Integer, default=60, nullable=False)
    credits_admission = db.Column(db.Integer, default=47, nullable=False)
    ordre             = db.Column(db.Integer, default=0,  nullable=False)

    niveau_suivant_id = db.Column(db.Integer, db.ForeignKey('niveau.id_niveau', ondelete='SET NULL'), nullable=True)
    niveau_suivant    = db.relationship('Niveau', remote_side=[id_niveau], lazy='select')

    semestres    = db.relationship('Semestre',    backref='niveau', lazy='select')
    inscriptions = db.relationship('Inscription', back_populates='niveau', lazy='select')

    @property
    def libelle_suivant(self):
        return self.niveau_suivant.libelle if self.niveau_suivant else None

    def __repr__(self):
        return f"<Niveau {self.libelle}>"


# ==========================
# NIVEAU FILIERE
# ==========================
class NiveauFiliere(db.Model):
    __tablename__ = 'niveau_filiere'
    __bind_key__  = 'oltp'
    __table_args__ = (
        db.UniqueConstraint('id_niveau', 'id_filiere', name='uq_niveau_filiere'),
    )

    id                        = db.Column(db.Integer, primary_key=True)
    id_niveau                 = db.Column(db.Integer, db.ForeignKey('niveau.id_niveau',   ondelete='CASCADE'), nullable=False)
    id_filiere                = db.Column(db.Integer, db.ForeignKey('filiere.id_filiere', ondelete='CASCADE'), nullable=False)
    credits_requis_filiere    = db.Column(db.Integer, nullable=True)
    credits_admission_filiere = db.Column(db.Integer, nullable=True)

    niveau = db.relationship('Niveau', lazy='joined')

    def __repr__(self):
        return f"<NiveauFiliere {self.id_niveau}-{self.id_filiere}>"


# ==========================
# SEMESTRE
# ==========================
class Semestre(db.Model):
    __tablename__ = 'semestre'
    __bind_key__  = 'oltp'

    id_semestre = db.Column(db.Integer, primary_key=True)
    libelle     = db.Column(db.String(10), nullable=False, unique=True)
    ordre       = db.Column(db.Integer, default=0, nullable=False)
    id_niveau   = db.Column(db.Integer, db.ForeignKey('niveau.id_niveau', ondelete='CASCADE'), nullable=False)

    ues      = db.relationship('UE',      backref='semestre', lazy='select')
    matieres = db.relationship('Matiere', backref='semestre', lazy='select')

    def __repr__(self):
        return f"<Semestre {self.libelle}>"


# ==========================
# UE
# ==========================
class UE(db.Model):
    __tablename__ = 'ue'
    __bind_key__  = 'oltp'

    id_ue        = db.Column(db.Integer, primary_key=True)
    nom          = db.Column(db.String(100), nullable=False)
    code_ue      = db.Column(db.String(20), nullable=True)
    credit_total = db.Column(db.Integer, nullable=False)
    coefficient  = db.Column(db.Float, default=1.0, nullable=False)
    id_semestre  = db.Column(db.Integer, db.ForeignKey('semestre.id_semestre', ondelete='CASCADE'), nullable=False)
    compensable  = db.Column(db.Boolean, default=True, nullable=False)

    matieres = db.relationship('Matiere', backref='ue', lazy='select')

    def __repr__(self):
        return f"<UE {self.nom} ({self.credit_total} cr.)>"


# ==========================
# ANNEE SCOLAIRE
# ==========================
class AnneeScolaire(db.Model):
    __tablename__ = 'annee_scolaire'
    __bind_key__  = 'oltp'

    id_annee   = db.Column(db.Integer, primary_key=True)
    libelle    = db.Column(db.String(20), unique=True, nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin   = db.Column(db.Date, nullable=False)
    active     = db.Column(db.Boolean, default=False, nullable=False)

    @staticmethod
    def get_active():
        return AnneeScolaire.query.filter_by(active=True).first()

    def __repr__(self):
        return f"<AnneeScolaire {self.libelle}>"


# ==========================
# PROFESSEUR
# ==========================
class Professeur(db.Model):
    __tablename__ = 'professeur'
    __bind_key__  = 'oltp'

    id_professeur = db.Column(db.Integer, primary_key=True)
    nom           = db.Column(db.String(100), nullable=False)
    prenom        = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    telephone     = db.Column(db.String(20))
    specialite    = db.Column(db.String(100))
    id_filiere    = db.Column(db.Integer, db.ForeignKey('filiere.id_filiere', ondelete='SET NULL'), nullable=True)

    matieres = db.relationship('Matiere', backref='professeur', lazy='select')

    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}"

    def __repr__(self):
        return f"<Professeur {self.nom_complet}>"


# ==========================
# MATIERE
# ==========================
class Matiere(db.Model):
    __tablename__ = 'matiere'
    __bind_key__  = 'oltp'

    id_matiere    = db.Column(db.Integer, primary_key=True)
    nom_matiere   = db.Column(db.String(100), nullable=False)
    code_matiere  = db.Column(db.String(20), nullable=True)
    credit        = db.Column(db.Integer, nullable=False, default=1)
    coefficient   = db.Column(db.Float, nullable=False, default=1.0)
    coef_cc       = db.Column(db.Float, default=0.4, nullable=False)
    coef_exam     = db.Column(db.Float, default=0.6, nullable=False)
    id_filiere    = db.Column(db.Integer, db.ForeignKey('filiere.id_filiere',       ondelete='SET NULL'), nullable=True)
    id_professeur = db.Column(db.Integer, db.ForeignKey('professeur.id_professeur', ondelete='SET NULL'), nullable=True)
    id_semestre   = db.Column(db.Integer, db.ForeignKey('semestre.id_semestre',     ondelete='SET NULL'), nullable=True)
    id_ue         = db.Column(db.Integer, db.ForeignKey('ue.id_ue',                 ondelete='SET NULL'), nullable=True)

    resultats = db.relationship('Resultat', backref='matiere', lazy='select')
    notes     = db.relationship('Note',     backref='matiere', lazy='select')

    def __repr__(self):
        return f"<Matiere {self.nom_matiere}>"


# ==========================
# SESSION
# ==========================
class Session(db.Model):
    __tablename__ = 'session'
    __bind_key__  = 'oltp'

    id_session     = db.Column(db.Integer, primary_key=True)
    libelle        = db.Column(db.String(20), nullable=False, unique=True)
    est_rattrapage = db.Column(db.Boolean, default=False, nullable=False)

    notes = db.relationship('Note', backref='session', lazy='select')

    def __repr__(self):
        return f"<Session {self.libelle}>"


# ==========================
# INSCRIPTION
# ==========================
class Inscription(db.Model):
    __tablename__ = 'inscription'
    __bind_key__  = 'oltp'
    __table_args__ = (
        db.UniqueConstraint('id_etudiant', 'id_niveau', 'id_annee', name='uq_inscription_etudiant_niveau_annee'),
    )

    id_inscription   = db.Column(db.Integer, primary_key=True)
    id_etudiant      = db.Column(db.Integer, db.ForeignKey('etudiant.id_etudiant',     ondelete='CASCADE'),  nullable=False)
    id_filiere       = db.Column(db.Integer, db.ForeignKey('filiere.id_filiere',       ondelete='SET NULL'), nullable=True)
    id_specialite    = db.Column(db.Integer, db.ForeignKey('specialite.id_specialite', ondelete='SET NULL'), nullable=True)
    id_niveau        = db.Column(db.Integer, db.ForeignKey('niveau.id_niveau',         ondelete='RESTRICT'), nullable=False)
    id_annee         = db.Column(db.Integer, db.ForeignKey('annee_scolaire.id_annee',  ondelete='RESTRICT'), nullable=False)

    moyenne_s1       = db.Column(db.Float, nullable=True)
    moyenne_s2       = db.Column(db.Float, nullable=True)
    moyenne_annuelle = db.Column(db.Float, nullable=True)

    credits_valides_s1 = db.Column(db.Integer, default=0, nullable=False)
    credits_valides_s2 = db.Column(db.Integer, default=0, nullable=False)
    credits_valides    = db.Column(db.Integer, default=0, nullable=False)

    mention        = db.Column(db.String(30), nullable=True)
    est_redoublant = db.Column(db.Boolean, default=False, nullable=False)

    filiere    = db.relationship('Filiere',       foreign_keys=[id_filiere],    lazy='select')
    specialite = db.relationship('Specialite',    foreign_keys=[id_specialite], lazy='select')
    niveau     = db.relationship('Niveau',        foreign_keys=[id_niveau],     back_populates='inscriptions', lazy='joined')
    annee      = db.relationship('AnneeScolaire', foreign_keys=[id_annee],      lazy='select')
    resultats  = db.relationship('Resultat', backref='inscription', lazy='select', cascade='all, delete-orphan')
    notes      = db.relationship('Note',     backref='inscription', lazy='select', cascade='all, delete-orphan')

    # ── Helpers ──────────────────────────────────────────────────

    def _credits_requis(self):       return self.niveau.credits_requis    if self.niveau else 60
    def _credits_admission(self):    return self.niveau.credits_admission  if self.niveau else 47
    def _credits_par_semestre(self): return self._credits_requis() // 2

    def _semestres_du_niveau(self):
        # ── CACHE (perf) ─────────────────────────────────────────────
        # Le tri de niveau.semestres ne change jamais au cours d'une
        # requête HTTP : on ne le fait qu'une seule fois par instance.
        # ────────────────────────────────────────────────────────────
        if not hasattr(self, "_cache_semestres"):
            if not self.niveau or not self.niveau.semestres:
                self._cache_semestres = []
            else:
                self._cache_semestres = sorted(self.niveau.semestres, key=lambda s: s.ordre)
        return self._cache_semestres

    def _id_semestre_1(self):
        s = self._semestres_du_niveau()
        return s[0].id_semestre if s else None

    def _id_semestre_2(self):
        s = self._semestres_du_niveau()
        return s[1].id_semestre if len(s) >= 2 else None

    def _resultats_par_semestre(self, id_semestre):
        # ── CACHE (perf) ─────────────────────────────────────────────
        # statut_simple boucle plusieurs fois sur self.resultats pour un
        # même id_semestre (a_notes, credits_apres_rattrapage, rat_s1/s2).
        # On ne filtre qu'une fois par (instance, id_semestre).
        # ────────────────────────────────────────────────────────────
        if not hasattr(self, "_cache_res_par_sem"):
            self._cache_res_par_sem = {}
        if id_semestre not in self._cache_res_par_sem:
            self._cache_res_par_sem[id_semestre] = [
                r for r in self.resultats if r.id_semestre == id_semestre
            ]
        return self._cache_res_par_sem[id_semestre]

    def _a_notes_s1(self):
        id_s1 = self._id_semestre_1()
        return id_s1 is not None and any(
            r.moyenne is not None for r in self._resultats_par_semestre(id_s1)
        )

    def _a_notes_s2(self):
        id_s2 = self._id_semestre_2()
        return id_s2 is not None and any(
            r.moyenne is not None for r in self._resultats_par_semestre(id_s2)
        )

    def _credits_s1_apres_rattrapage(self):
        id_s1 = self._id_semestre_1()
        if id_s1 is None: return 0
        res = self._resultats_par_semestre(id_s1)
        credits = sum(r.matiere.credit for r in res if r.credit_valide and r.matiere)
        seuil = self._credits_par_semestre()
        rat = any(r.moyenne_rattrapage is not None for r in res)
        return seuil if rat and credits >= seuil else credits

    def _credits_s2_apres_rattrapage(self):
        id_s2 = self._id_semestre_2()
        if id_s2 is None: return 0
        res = self._resultats_par_semestre(id_s2)
        credits = sum(r.matiere.credit for r in res if r.credit_valide and r.matiere)
        seuil = self._credits_par_semestre()
        rat = any(r.moyenne_rattrapage is not None for r in res)
        return seuil if rat and credits >= seuil else credits

    # ── Statut ───────────────────────────────────────────────────

    @property
    def statut_simple(self):
        # ── CACHE (perf) ─────────────────────────────────────────────
        # statut_simple était appelée jusqu'à 4-5 fois par inscription
        # dans certaines routes (/student, /tableau_sp), chaque appel
        # refaisant ~6 tris + ~8 boucles sur resultats. On calcule une
        # seule fois par instance et on réutilise le résultat.
        # Invalidé automatiquement via invalider_cache_statut() après
        # toute modification des résultats (voir recalculer_tout()).
        # ────────────────────────────────────────────────────────────
        if hasattr(self, "_cache_statut"):
            return self._cache_statut

        a_s1 = self._a_notes_s1()
        a_s2 = self._a_notes_s2()

        # Abandon : aucune note
        if not a_s1 and not a_s2:
            self._cache_statut = "Abandon"
            return self._cache_statut

        seuil_sem   = self._credits_par_semestre()  # 30
        seuil_total = self._credits_requis()         # 60
        seuil_admis = self._credits_admission()      # 47

        credits_s1 = self._credits_s1_apres_rattrapage() if a_s1 else 0
        credits_s2 = self._credits_s2_apres_rattrapage() if a_s2 else 0

        id_s1 = self._id_semestre_1()
        id_s2 = self._id_semestre_2()

        # Vérifie si rattrapage a eu lieu
        rat_s1 = a_s1 and any(
            r.moyenne_rattrapage is not None
            for r in self._resultats_par_semestre(id_s1)
        )
        rat_s2 = a_s2 and any(
            r.moyenne_rattrapage is not None
            for r in self._resultats_par_semestre(id_s2)
        )

        # Ajourné = crédits insuffisants
        # Si rattrapage passé et toujours insuffisant → reste Ajourné
        s1_insuf = a_s1 and credits_s1 < seuil_sem
        s2_insuf = a_s2 and credits_s2 < seuil_sem

        # ── Bilan annuel complet (S1 + S2) ───────────────────────────
        if a_s1 and a_s2 and self.moyenne_s1 is not None and self.moyenne_s2 is not None:
            total = credits_s1 + credits_s2

            # Admis : crédits complets
            if total >= seuil_total:
                resultat = "Admis"

            # Admis avec dettes : passe au niveau suivant mais doit rattraper
            elif total >= seuil_admis:
                resultat = "Admis (dettes)"

            # Crédits < 47
            elif self.est_redoublant:
                resultat = "Redoublant"

            # Ajourné selon semestre insuffisant
            elif s1_insuf and s2_insuf:
                resultat = "Ajourné S1 & S2"
            elif s1_insuf:
                resultat = "Ajourné S1"
            elif s2_insuf:
                resultat = "Ajourné S2"
            else:
                resultat = "Ajourné S1 & S2"

        # ── S1 seulement (année en cours) ────────────────────────────
        elif a_s1 and self.moyenne_s1 is not None:
            # Rattrapage S1 passé et toujours insuffisant
            if rat_s1 and s1_insuf:
                resultat = "Ajourné S1"
            elif s1_insuf:
                resultat = "Ajourné S1"
            else:
                resultat = "En cours"

        # ── S2 seulement ─────────────────────────────────────────────
        elif a_s2 and self.moyenne_s2 is not None:
            # Rattrapage S2 passé et toujours insuffisant
            if rat_s2 and s2_insuf:
                resultat = "Ajourné S2"
            elif s2_insuf:
                resultat = "Ajourné S2"
            else:
                resultat = "En cours"

        else:
            resultat = "En cours"

        self._cache_statut = resultat
        return self._cache_statut

    def invalider_cache_statut(self):
        """
        À appeler après toute modification des résultats/notes de cette
        inscription (import de notes, saisie manuelle, rattrapage, etc.)
        si statut_simple doit être relu dans la MÊME requête HTTP après
        la modification. Entre deux requêtes HTTP, le cache est de toute
        façon repartis à zéro (nouvelle instance ORM à chaque requête).
        """
        for attr in ("_cache_statut", "_cache_semestres", "_cache_res_par_sem"):
            if hasattr(self, attr):
                delattr(self, attr)

    @property
    def statut_passage(self):
        statut = self.statut_simple
        if statut in ("Abandon", "En cours", "Ajourné S1", "Ajourné S2", "Ajourné S1 & S2"):
            return statut
        if statut == "Redoublant":
            return f"Redoublant en {self.niveau.libelle}" if self.niveau else "Redoublant"
        niv_suiv = self.niveau.niveau_suivant if self.niveau else None
        if statut == "Admis":
            return f"Admis en {niv_suiv.libelle}" if niv_suiv else "Diplômé"
        if statut == "Admis (dettes)":
            return f"Admis en {niv_suiv.libelle} avec dettes" if niv_suiv else "Diplômé (dettes)"
        return statut

    # ── Recalculs ─────────────────────────────────────────────────

    def recalculer_credits(self):
        self.credits_valides_s1 = self._credits_s1_apres_rattrapage()
        self.credits_valides_s2 = self._credits_s2_apres_rattrapage()
        self.credits_valides    = self.credits_valides_s1 + self.credits_valides_s2

    def recalculer_moyenne_semestrielle(self, id_semestre):
        res = [r for r in self.resultats if r.id_semestre == id_semestre and r.moyenne is not None]
        if not res: return None
        total_pts  = sum(r.moyenne * (r.matiere.coefficient if r.matiere else 1) for r in res)
        total_coef = sum(r.matiere.coefficient if r.matiere else 1 for r in res)
        return round(total_pts / total_coef, 2) if total_coef else None

    def recalculer_moyenne_annuelle(self):
        if self.moyenne_s1 is not None and self.moyenne_s2 is not None:
            self.moyenne_annuelle = round((self.moyenne_s1 + self.moyenne_s2) / 2, 2)
        elif self.moyenne_s1 is not None:
            self.moyenne_annuelle = self.moyenne_s1
        elif self.moyenne_s2 is not None:
            self.moyenne_annuelle = self.moyenne_s2
        else:
            self.moyenne_annuelle = None

    def _calculer_mention(self):
        m = self.moyenne_annuelle
        if m is None:  self.mention = None
        elif m >= 16:  self.mention = "Très Bien"
        elif m >= 14:  self.mention = "Bien"
        elif m >= 12:  self.mention = "Assez Bien"
        elif m >= 10:  self.mention = "Passable"
        else:          self.mention = None

    def recalculer_tout(self):
        id_s1 = self._id_semestre_1()
        id_s2 = self._id_semestre_2()
        if id_s1:
            self.moyenne_s1 = self.recalculer_moyenne_semestrielle(id_s1)
        if id_s2:
            self.moyenne_s2 = self.recalculer_moyenne_semestrielle(id_s2)
        self.recalculer_credits()
        self.recalculer_moyenne_annuelle()
        self._calculer_mention()
        # ── Important : les résultats viennent de changer, on invalide
        #    le cache de statut_simple pour que la suite de la requête
        #    (ex: creer_ou_maj_dette juste après) voie le bon statut.
        self.invalider_cache_statut()

    def __repr__(self):
        return f"<Inscription {self.id_inscription} - {self.statut_simple}>"


# ==========================
# RESULTAT
# ==========================
class Resultat(db.Model):
    __tablename__ = 'resultat'
    __bind_key__  = 'oltp'
    __table_args__ = (
        db.UniqueConstraint('id_inscription', 'id_matiere', 'id_semestre', name='uq_resultat_inscription_matiere_semestre'),
    )

    id_resultat    = db.Column(db.Integer, primary_key=True)
    id_inscription = db.Column(db.Integer, db.ForeignKey('inscription.id_inscription', ondelete='CASCADE'),  nullable=False)
    id_matiere     = db.Column(db.Integer, db.ForeignKey('matiere.id_matiere',         ondelete='CASCADE'),  nullable=False)
    id_semestre    = db.Column(db.Integer, db.ForeignKey('semestre.id_semestre',       ondelete='RESTRICT'), nullable=False)

    moyenne                  = db.Column(db.Float, nullable=True)
    credit_valide            = db.Column(db.Boolean, default=False, nullable=False)
    moyenne_rattrapage       = db.Column(db.Float, nullable=True)
    credit_valide_rattrapage = db.Column(db.Boolean, default=False, nullable=False)

    semestre = db.relationship('Semestre', foreign_keys=[id_semestre], lazy='joined')

    def valider_credit(self, seuil=10.0):
        self.credit_valide = (self.moyenne is not None and self.moyenne >= seuil)

    def appliquer_rattrapage(self, note_rattrapage, seuil=10.0):
        self.moyenne_rattrapage = note_rattrapage
        candidates = [v for v in [self.moyenne, note_rattrapage] if v is not None]
        meilleure  = max(candidates) if candidates else None
        if meilleure is not None:
            self.moyenne                  = round(meilleure, 2)
            self.credit_valide            = self.moyenne >= seuil
            self.credit_valide_rattrapage = self.credit_valide

    def __repr__(self):
        return f"<Resultat {self.id_resultat} - Moy: {self.moyenne}>"


# ==========================
# NOTE
# ==========================
class Note(db.Model):
    __tablename__ = 'note'
    __bind_key__  = 'oltp'
    __table_args__ = (
        db.UniqueConstraint('id_inscription', 'id_matiere', 'id_session', 'type_evaluation',
                            name='uq_note_inscription_matiere_session_type'),
    )

    TYPE_CC   = 'CC'
    TYPE_EXAM = 'EXAM'

    id_note         = db.Column(db.Integer, primary_key=True)
    id_inscription  = db.Column(db.Integer, db.ForeignKey('inscription.id_inscription', ondelete='CASCADE'),  nullable=False)
    id_matiere      = db.Column(db.Integer, db.ForeignKey('matiere.id_matiere',         ondelete='CASCADE'),  nullable=False)
    id_session      = db.Column(db.Integer, db.ForeignKey('session.id_session',         ondelete='RESTRICT'), nullable=False)
    type_evaluation = db.Column(db.String(10), nullable=False, default=TYPE_EXAM)
    valeur          = db.Column(db.Float, nullable=False)
    date_eval       = db.Column(db.Date, default=date.today, nullable=False)

    def __repr__(self):
        return f"<Note {self.id_note} [{self.type_evaluation}] - {self.valeur}/20>"


# ==========================
# RESULTAT UE
# ==========================
class ResultatUE(db.Model):
    __tablename__ = 'resultat_ue'
    __bind_key__  = 'oltp'
    __table_args__ = (
        db.UniqueConstraint('id_inscription', 'id_ue', name='uq_resultat_ue_inscription'),
    )

    id_resultat_ue     = db.Column(db.Integer, primary_key=True)
    id_inscription     = db.Column(db.Integer, db.ForeignKey('inscription.id_inscription', ondelete='CASCADE'), nullable=False)
    id_ue              = db.Column(db.Integer, db.ForeignKey('ue.id_ue',                   ondelete='CASCADE'), nullable=False)
    moyenne_ue         = db.Column(db.Float, nullable=True)
    ue_validee         = db.Column(db.Boolean, default=False, nullable=False)
    compensee          = db.Column(db.Boolean, default=False, nullable=False)
    credits_ue_valides = db.Column(db.Integer, default=0, nullable=False)

    inscription = db.relationship('Inscription', lazy='select')
    ue          = db.relationship('UE',          lazy='joined')

    def appliquer_compensation(self, moyenne_semestre, seuil_ue=8.0):
        if self.moyenne_ue is None: return
        if self.moyenne_ue >= 10.0:
            self.ue_validee = True
        elif self.ue and self.ue.compensable and self.moyenne_ue >= seuil_ue and moyenne_semestre >= 10.0:
            self.ue_validee = True
            self.compensee  = True
        else:
            self.ue_validee = False
        self.credits_ue_valides = (self.ue.credit_total if self.ue else 0) if self.ue_validee else 0

    def __repr__(self):
        return f"<ResultatUE UE={self.id_ue} Moy={self.moyenne_ue}>"


# ==========================
# DETTE DE CREDITS
# ==========================
class DetteCreditNiveau(db.Model):
    __tablename__ = 'dette_credit_niveau'
    __bind_key__  = 'oltp'
    __table_args__ = (
        db.UniqueConstraint('id_etudiant', 'id_niveau', name='uq_dette_etudiant_niveau'),
    )

    id                 = db.Column(db.Integer, primary_key=True)
    id_etudiant        = db.Column(db.Integer, db.ForeignKey('etudiant.id_etudiant', ondelete='CASCADE'), nullable=False)
    id_niveau          = db.Column(db.Integer, db.ForeignKey('niveau.id_niveau',     ondelete='CASCADE'), nullable=False)
    credits_dus        = db.Column(db.Integer, nullable=False, default=0)
    credits_rembourses = db.Column(db.Integer, nullable=False, default=0)
    soldee             = db.Column(db.Boolean, default=False, nullable=False)

    etudiant = db.relationship('Etudiant', lazy='select')
    niveau   = db.relationship('Niveau',   lazy='joined')

    @property
    def credits_restants(self):
        return max(0, self.credits_dus - self.credits_rembourses)

    def rembourser(self, credits):
        self.credits_rembourses = min(self.credits_dus, self.credits_rembourses + credits)
        self.soldee             = self.credits_rembourses >= self.credits_dus

    def __repr__(self):
        return f"<Dette {self.id_etudiant}·{self.niveau.libelle if self.niveau else '?'}>"


# ==========================
# ABSENCE
# ==========================
class Absence(db.Model):
    __tablename__ = 'absence'
    __bind_key__  = 'oltp'

    id          = db.Column(db.Integer, primary_key=True)
    id_etudiant = db.Column(db.Integer, db.ForeignKey('etudiant.id_etudiant', ondelete='CASCADE'), nullable=False)
    id_matiere  = db.Column(db.Integer, db.ForeignKey('matiere.id_matiere',   ondelete='CASCADE'), nullable=False)
    date        = db.Column(db.Date, nullable=False, default=date.today)
    justifie    = db.Column(db.Boolean, default=False, nullable=False)

    etudiant = db.relationship('Etudiant', foreign_keys=[id_etudiant], lazy='select')
    matiere  = db.relationship('Matiere',  foreign_keys=[id_matiere],  lazy='select')

    def __repr__(self):
        return f"<Absence {self.id} - Etudiant {self.id_etudiant}>"


# ==========================
# HELPERS
# ==========================

def etudiant_peut_avancer(etudiant_id, niveau_actuel_id):
    dettes = DetteCreditNiveau.query.filter_by(id_etudiant=etudiant_id, soldee=False).filter(
        DetteCreditNiveau.id_niveau != niveau_actuel_id
    ).all()
    return (False, dettes) if dettes else (True, [])


def creer_ou_maj_dette(inscription):
    if inscription.statut_simple != "Admis (dettes)":
        return
    credits_manquants = inscription._credits_requis() - (
        inscription._credits_s1_apres_rattrapage() + inscription._credits_s2_apres_rattrapage()
    )
    if credits_manquants <= 0:
        return
    dette = DetteCreditNiveau.query.filter_by(
        id_etudiant=inscription.id_etudiant,
        id_niveau=inscription.id_niveau
    ).first()
    if dette:
        dette.credits_dus        = credits_manquants
        dette.credits_rembourses = 0
        dette.soldee             = False
    else:
        from IUAInsight import db as _db
        _db.session.add(DetteCreditNiveau(
            id_etudiant=inscription.id_etudiant,
            id_niveau=inscription.id_niveau,
            credits_dus=credits_manquants,
        ))