from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, SelectField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from flask_login import current_user
from IUAInsight.models_app import Administrateur_sy, Respo_peda
from flask import abort


# ─────────────────────────────────────────────
# Utilitaire : contrainte domaine @iuaci.ci
# ─────────────────────────────────────────────
def check_iua_domain(email_data):
    """Lève une ValidationError si l'email n'appartient pas au domaine @iuaci.ci"""
    if not email_data.strip().lower().endswith('@iua.ci'):
        raise ValidationError("L'adresse email doit être du domaine @iua.ci")


# ─────────────────────────────────────────────
# Créer un compte admin
# ─────────────────────────────────────────────
class AdminForm(FlaskForm):
    first_name       = StringField('Nom :',    validators=[DataRequired(), Length(min=2, max=50)])
    last_name        = StringField('Prénoms :', validators=[DataRequired(), Length(min=2, max=100)])
    email            = StringField('Email :',  validators=[DataRequired(), Email()],
                                   render_kw={"placeholder": "prenom.nom@iua.ci"})
    password         = PasswordField('Mot de passe :', validators=[DataRequired(), Length(min=6, max=12)])
    confirm_password = PasswordField('Confirmer le mot de passe :', validators=[DataRequired(), EqualTo('password')])
    genre            = RadioField('Genre :', choices=[('Homme', 'Homme'), ('Femme', 'Femme')], validators=[DataRequired()])
    submit           = SubmitField('Créer')

    def validate_email(self, email):
        # ✅ Contrainte domaine IUA
        check_iua_domain(email.data)
        # Unicité
        admin = Administrateur_sy.query.filter_by(email=email.data).first()
        if admin:
            raise ValidationError('Cette adresse e-mail est déjà utilisée. Veuillez en choisir une autre !')


# ─────────────────────────────────────────────
# Connexion
# ─────────────────────────────────────────────
class Login_adminForm(FlaskForm):
    email    = StringField('Email :', validators=[DataRequired(), Email()],
               render_kw={"placeholder": "prenom.nom@iua.ci"})
    password = PasswordField('Mot de passe :', validators=[DataRequired()])
    submit   = SubmitField('Se connecter')
    # ❌ Pas de contrainte domaine ici (connexion uniquement)


# ─────────────────────────────────────────────
# Modifier compte
# ─────────────────────────────────────────────
class UpdateAccountForm(FlaskForm):
    first_name       = StringField('Nom :',    validators=[Length(min=2, max=50)])
    last_name        = StringField('Prénoms :', validators=[Length(min=2, max=100)])
    email            = StringField('Email :',  validators=[Email()],
                       render_kw={"placeholder": "prenom.nom@iua.ci"})
    password         = PasswordField('Nouveau mot de passe :')
    confirm_password = PasswordField(
        'Confirmer le mot de passe :',
        validators=[EqualTo('password', message="Les mots de passe ne correspondent pas")]
    )
    genre   = RadioField('Genre :', choices=[('Homme', 'Homme'), ('Femme', 'Femme')], validators=[DataRequired()])
    picture = FileField('Modifier la photo de profil :', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit  = SubmitField('Enregistrer les changements')

    def validate_email(self, email):
        # ✅ Contrainte domaine IUA
        check_iua_domain(email.data)
        # Pas besoin de vérifier l'unicité si l'email n'a pas changé
        if email.data == current_user.email:
            return
        # Unicité selon le type d'utilisateur connecté
        if isinstance(current_user, Administrateur_sy):
            if Administrateur_sy.query.filter_by(email=email.data).first():
                raise ValidationError('Cette adresse e-mail est déjà utilisée !')
        elif isinstance(current_user, Respo_peda):
            if Respo_peda.query.filter_by(email=email.data).first():
                raise ValidationError('Cette adresse e-mail est déjà utilisée !')


# ─────────────────────────────────────────────
# Rapport
# ─────────────────────────────────────────────
class RapportForm(FlaskForm):
    type_rapport = SelectField(
        "Type de Rapport",
        choices=[
            ("Rapport de résultats", "Rapport de résultats"),
            ("Étudiants admis",      "Étudiants admis"),
            ("Admis endettés",       "Admis endettés"),
            ("Étudiants en échec",   "Étudiants en échec"),
            ("Abandon étudiants",    "Abandon étudiants"),
        ],
        validators=[DataRequired()]
    )
    periode        = SelectField("Période",  validators=[DataRequired()])
    filiere        = SelectField("Filière",  validators=[DataRequired()])
    niveau         = SelectField("Niveau",   validators=[DataRequired()])
    format_fichier = RadioField(
        "Format",
        choices=[("PDF", "PDF"), ("Excel", "Excel")],
        default="PDF",
        validators=[DataRequired()]
    )
    submit = SubmitField("Générer & Télécharger")


# ─────────────────────────────────────────────
# Création compte responsable pédagogique
# ─────────────────────────────────────────────
class RespoForm(FlaskForm):
    nom          = StringField("Nom",    validators=[DataRequired(), Length(max=50)])
    prenom       = StringField("Prénom", validators=[DataRequired(), Length(max=50)])
    email        = StringField("Email",  validators=[DataRequired(), Email(), Length(max=100)],
                 render_kw={"placeholder": "prenom.nom@iua.ci"})
    mot_de_passe = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=6, max=12)])
    role         = SelectField(
        "Rôle",
        choices=[("responsable pédagogique", "Responsable pédagogique")],
        default="responsable pédagogique",
        validators=[DataRequired()]
    )
    genre  = RadioField("Genre", choices=[("Homme", "Homme"), ("Femme", "Femme")], validators=[DataRequired()])
    submit = SubmitField("Créer")

    def validate_email(self, email):
        # ✅ Contrainte domaine IUA
        check_iua_domain(email.data)
        # Unicité
        if Respo_peda.query.filter_by(email=email.data).first():
            raise ValidationError('Cette adresse e-mail est déjà utilisée !')