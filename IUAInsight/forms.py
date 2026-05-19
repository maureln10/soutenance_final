from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, SelectField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from flask_login import current_user
from IUAInsight.models_app import Administrateur_sy, Respo_peda
from functools import wraps
from flask import abort


# Créer un compte admin
class AdminForm(FlaskForm):
    first_name       = StringField('Nom :',    validators=[DataRequired(), Length(min=2, max=50)])
    last_name        = StringField('Prénoms :', validators=[DataRequired(), Length(min=2, max=100)])
    email            = StringField('Email :',  validators=[DataRequired(), Email()])
    password         = PasswordField('Mot de passe :', validators=[DataRequired(), Length(min=6, max=12)])
    confirm_password = PasswordField('Confirmer le mot de passe :', validators=[DataRequired(), EqualTo('password')])
    genre            = RadioField('Genre :', choices=[('Homme', 'Homme'), ('Femme', 'Femme')], validators=[DataRequired()])
    submit           = SubmitField('Créer')

    def validate_email(self, email):
        admin = Administrateur_sy.query.filter_by(email=email.data).first()
        if admin:
            raise ValidationError('Cette adresse e-mail est déjà utilisée. Veuillez en choisir une autre !')


# Connexion
class Login_adminForm(FlaskForm):
    email    = StringField('Email :', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe :', validators=[DataRequired()])
    submit   = SubmitField('Se connecter')


# Modifier compte
class UpdateAccountForm(FlaskForm):
    first_name       = StringField('Nom :',    validators=[Length(min=2, max=50)])
    last_name        = StringField('Prénoms :', validators=[Length(min=2, max=100)])
    email            = StringField('Email :',  validators=[Email()])
    password         = PasswordField('Nouveau mot de passe :')
    confirm_password = PasswordField(
        'Confirmer le mot de passe :',
        validators=[EqualTo('password', message="Les mots de passe ne correspondent pas")]
    )
    genre   = RadioField('Genre :', choices=[('Homme', 'Homme'), ('Femme', 'Femme')], validators=[DataRequired()])
    picture = FileField('Modifier la photo de profil :', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit  = SubmitField('Enregistrer les changements')

    def validate_email(self, email):
        if email.data == current_user.email:
            return
        # ✅ CORRIGÉ : Respo_acad → Respo_peda
        if isinstance(current_user, Administrateur_sy):
            if Administrateur_sy.query.filter_by(email=email.data).first():
                raise ValidationError('Cette adresse e-mail est déjà utilisée !')
        elif isinstance(current_user, Respo_peda):
            if Respo_peda.query.filter_by(email=email.data).first():
                raise ValidationError('Cette adresse e-mail est déjà utilisée !')


# Rapport
class RapportForm(FlaskForm):
    type_rapport = SelectField(
        "Type de Rapport",
        choices=[
            # ✅ CORRIGÉ : valeurs identiques à celles vérifiées dans routes.py
            ("Rapport de résultats", "Rapport de résultats"),
            ("Étudiants admis",      "Étudiants admis"),
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


# Création compte responsable pédagogique
class RespoForm(FlaskForm):
    nom          = StringField("Nom",    validators=[DataRequired(), Length(max=50)])
    prenom       = StringField("Prénom", validators=[DataRequired(), Length(max=50)])
    email        = StringField("Email",  validators=[DataRequired(), Email(), Length(max=100)])
    mot_de_passe = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=6, max=12)])
    role         = SelectField(
        "Rôle",
        # ✅ Une seule option : responsable pédagogique
        choices=[("responsable pédagogique", "Responsable pédagogique")],
        default="responsable pédagogique",
        validators=[DataRequired()]
    )
    genre  = RadioField("Genre", choices=[("Homme", "Homme"), ("Femme", "Femme")], validators=[DataRequired()])
    submit = SubmitField("Créer")