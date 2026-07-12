from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from dotenv import load_dotenv
import os
import time  
import logging
import threading

# ── Chargement des variables d'environnement ───────────────
load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY']                  = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Base applicative Flask (admin, respo, rapports, alertes, sauvegardes)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_APP_URI')

# ── Binds : OLTP source (lmd1) + Data Warehouse
app.config['SQLALCHEMY_BINDS'] = {
    "oltp": os.getenv('DB_OLTP_URI'),
    "dw":   os.getenv('DB_DW_URI'),
}

# 🔍 DEBUG TEMPORAIRE — à retirer une fois le problème résolu
logging.basicConfig(level=logging.INFO)
_debug_logger = logging.getLogger("startup-debug")
_debug_logger.warning(f"DEBUG DB_APP_URI  = {os.getenv('DB_APP_URI')}")
_debug_logger.warning(f"DEBUG DB_OLTP_URI = {os.getenv('DB_OLTP_URI')}")
_debug_logger.warning(f"DEBUG DB_DW_URI   = {os.getenv('DB_DW_URI')}")
_debug_logger.warning(f"DEBUG SQLALCHEMY_DATABASE_URI (config) = {app.config.get('SQLALCHEMY_DATABASE_URI')}")
_debug_logger.warning(f"DEBUG SQLALCHEMY_BINDS (config) = {app.config.get('SQLALCHEMY_BINDS')}")

# ── Sécurité HTTPS + headers ───────────────────────────────
Talisman(app,
    force_https=False,
    strict_transport_security=True,
    session_cookie_secure=False,
    content_security_policy={
        'default-src': "'self'",
        'script-src':  ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
        'style-src':   ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com"],
        'img-src':     ["'self'", "data:"],
        'font-src':    ["'self'", "cdn.jsdelivr.net", "fonts.gstatic.com"],
        'connect-src': ["'self'", "cdn.jsdelivr.net"],
    }
)

db            = SQLAlchemy(app)
bcrypt        = Bcrypt(app)
login_manager = LoginManager(app)
csrf          = CSRFProtect(app)

login_manager.login_view             = 'login'
login_manager.login_message_category = 'info'

# ── Rate Limiting ──────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# ── Profiling des requêtes lentes ─────────────────────────
@app.before_request
def _start_timer():
    from flask import g, request
    if not request.path.startswith('/static'):
        g._req_start = time.perf_counter()

@app.after_request
def _log_response_time(response):
    from flask import g, request
    start = getattr(g, '_req_start', None)
    if start is not None:
        ms = (time.perf_counter() - start) * 1000
        level = logging.WARNING if ms > 500 else logging.INFO
        app.logger.log(level, f"[PERF] {request.method} {request.path} → {ms:.0f}ms")
    return response

# ── Initialisation du Data Warehouse ───────────────────────
# Cette étape reste synchrone : c'est rapide (juste un CREATE TABLE IF NOT EXISTS),
# contrairement à l'entraînement ML et l'ETL qui, eux, peuvent être longs.
from IUAInsight.Warehouse import init_dw, create_dw_tables
init_dw(app)
create_dw_tables(app)

# ── Routes & modèles app ────────────────────────────────────
from IUAInsight import routes
from IUAInsight import models_app

# ── Démarrage : ML + ETL — EXÉCUTÉS EN ARRIÈRE-PLAN ─────────
# ✅ FIX CRITIQUE : ce bloc était auparavant exécuté de manière SYNCHRONE au
#    niveau module, donc AVANT que Gunicorn ne puisse lier son port. Sur Render,
#    Gunicorn importe entièrement IUAInsight:app avant de bind le port — tant que
#    l'entraînement ML (RandomForest sur toute la table Inscription) et l'ETL
#    tournaient ici, le port ne s'ouvrait jamais, provoquant le timeout Render
#    "No open ports detected".
#
#    Solution : lancer ce travail dans un thread daemon séparé. L'import du
#    module se termine immédiatement, Gunicorn bind le port tout de suite,
#    et le modèle ML / l'ETL se mettent à jour en tâche de fond une fois
#    l'app déjà en train de répondre aux requêtes (avec le fallback
#    heuristique de ml_engine en attendant que l'entraînement se termine).
def _startup_background_tasks():
    with app.app_context():
        from IUAInsight.ml_models import ml_engine
        from IUAInsight.models import Inscription

        try:
            result = ml_engine.auto_train_if_needed(
                lambda: Inscription.query.all(),
                force=True
            )
            app.logger.info(f"[ML boot] Entraînement terminé : {result}")
        except Exception as e:
            app.logger.warning(f"[ML boot] Entraînement ignoré : {e}")

        try:
            from IUAInsight.Warehouse.models import FaitResultatEtudiant
            from IUAInsight.Warehouse.etl_pipeline import ETLPipeline
            from IUAInsight.models import AnneeScolaire

            if FaitResultatEtudiant.query.count() == 0:
                annee = AnneeScolaire.query.filter_by(active=True).first()
                ETLPipeline().run(
                    annee_id=annee.id_annee if annee else None
                )
                app.logger.info("[ETL boot] ETL initial terminé.")
        except Exception as e:
            app.logger.warning(f"[ETL boot] ignoré : {e}")


_startup_thread = threading.Thread(target=_startup_background_tasks, daemon=True)
_startup_thread.start()

# ── Scheduler en dernier (après app, db, routes) ───────────
from IUAInsight.routes import init_scheduler
init_scheduler(app)