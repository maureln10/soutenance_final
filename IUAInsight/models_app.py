from datetime import datetime, timezone
from IUAInsight import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# ==========================
# LOGIN MANAGER
# ==========================
@login_manager.user_loader
def load_user(user_id):
    if str(user_id).startswith("Respo"):
        return Respo_peda.query.get(int(user_id[5:]))
    return Administrateur_sy.query.get(int(user_id))


# ==========================
# ADMINISTRATEUR
# ==========================
class Administrateur_sy(db.Model, UserMixin):
    __tablename__ = 'administrateur_sy'
    # Pas de __bind_key__ → va dans la BD par défaut : iua_app_db

    id_admin     = db.Column(db.Integer, primary_key=True)
    nom          = db.Column(db.String(50), nullable=False)
    prenom       = db.Column(db.String(50), nullable=False)
    email        = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    genre        = db.Column(db.String(10))
    image_file   = db.Column(db.String(50), default='default.jpg')
    role         = db.Column(db.String(50), default='admin système', nullable=False)

    def set_password(self, password):
        self.mot_de_passe = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe, password)

    def get_id(self):
        return str(self.id_admin)

    def __repr__(self):
        return f"<Administrateur {self.role} {self.nom} {self.prenom}>"


# ==========================
# RESPONSABLE PÉDAGOGIQUE
# ==========================
class Respo_peda(db.Model, UserMixin):
    __tablename__ = 'respo_peda'
    # Pas de __bind_key__ → va dans iua_app_db

    id_respo     = db.Column(db.Integer, primary_key=True)
    nom          = db.Column(db.String(50), nullable=False)
    prenom       = db.Column(db.String(50), nullable=False)
    email        = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    genre        = db.Column(db.String(10))
    image_file   = db.Column(db.String(50), default='default.jpg')
    role         = db.Column(db.String(50), default='responsable pédagogique')
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return f"Respo{self.id_respo}"

    def __repr__(self):
        return f"<Respo_peda {self.nom} {self.prenom}>"


# ==========================
# RAPPORT
# ==========================
class Rapport(db.Model):
    __tablename__ = 'rapport'

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), nullable=False)
    details = db.Column(db.String(250))
    date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    format = db.Column(db.String(20))
    path = db.Column(db.String(250))

    
    id_respo = db.Column(
        db.Integer,
        db.ForeignKey('respo_peda.id_respo'),
        nullable=True
    )

    respo = db.relationship(
        'Respo_peda',
        backref='rapports'
    )

    def __repr__(self):
        return f"<Rapport {self.titre}>"

# ==========================
# ALERTE
# ==========================
class Alerte(db.Model):
    __tablename__ = 'alerte'

    id_alerte = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    message = db.Column(db.String(255))
    type_alerte = db.Column(db.String(100), unique=True)
    date = db.Column(db.DateTime)
    vue = db.Column(db.Boolean, default=False)

    # RELATION
    id_respo = db.Column(
        db.Integer,
        db.ForeignKey('respo_peda.id_respo'),
        nullable=True
    )

    respo = db.relationship(
        'Respo_peda',
        backref='alertes'
    )

    def __repr__(self):
        return f"<Alerte {self.type_alerte}>"
# ==========================
# SAUVEGARDES
# ==========================
class Sauvegarde(db.Model):
    __tablename__ = 'sauvegardes'
    # Pas de __bind_key__ → va dans iua_app_db

    id_sauvegarde   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom_fichier     = db.Column(db.String(255), nullable=False)
    type_sauvegarde = db.Column(db.String(50), nullable=False)
    date_sauvegarde = db.Column(db.DateTime, default=datetime.utcnow)
    taille_fichier  = db.Column(db.String(100))
    statut          = db.Column(db.String(50), default='Succès')

    def __repr__(self):
        return f"<Sauvegarde {self.nom_fichier}>"