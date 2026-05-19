from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf import CSRFProtect

app = Flask(__name__)

app.config['SECRET_KEY'] = 'f8b3cf545102730455c6d4a267c73d2f52f2ff80da9f9bc9b280691d03710c2d'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Base applicative Flask (admin, respo, rapports, alertes, sauvegardes)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/iua_app_db"

# ── Binds : OLTP source (lmd1) + Data Warehouse
app.config['SQLALCHEMY_BINDS'] = {
    "oltp": "mysql+pymysql://root:@localhost/lmd1",
    "dw":   "mysql+pymysql://root:@localhost/iuadecis_dw",
}

db       = SQLAlchemy(app)
bcrypt   = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect(app)

# ── Initialisation du Data Warehouse ───────────────────────
from IUAInsight.Warehouse import init_dw, create_dw_tables
init_dw(app)
create_dw_tables(app)

# ── Routes & modèles app ────────────────────────────────────
from IUAInsight import routes
from IUAInsight import models_app  # Administrateur, Respo, Rapport, Alerte, Sauvegarde

# ── Entraînement ML automatique au démarrage ───────────────
from IUAInsight.ml_models import ml_engine
from IUAInsight.models import Inscription

with app.app_context():
    ml_engine.auto_train_if_needed(
        lambda: Inscription.query.all()
    )

    # ── Premier chargement ETL au démarrage ────────────────
    from IUAInsight.Warehouse.models import FaitResultatEtudiant   # ← renommé
    from IUAInsight.Warehouse.etl_pipeline import ETLPipeline
    from IUAInsight.models import AnneeScolaire

    try:
        if FaitResultatEtudiant.query.count() == 0:
            annee = AnneeScolaire.query.filter_by(active=True).first()
            ETLPipeline().run(
                annee_id=annee.id_annee if annee else None
            )
    except Exception as e:
        app.logger.warning(f"[ETL boot] ignoré : {e}")

# ── Scheduler en dernier (après app, db, routes) ───────────
from IUAInsight.routes import init_scheduler
init_scheduler(app)