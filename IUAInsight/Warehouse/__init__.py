"""
IUAInsight — Data Warehouse
============================
Le bind 'dw' est géré par le db principal (SQLALCHEMY_BINDS).
"""

def init_dw(app):
    pass  # Rien à faire — db principal gère déjà le bind "dw"


def create_dw_tables(app):
    """Crée toutes les tables DW si elles n'existent pas."""
    from IUAInsight.Warehouse import models  # noqa — enregistre les modèles
    with app.app_context():
        from IUAInsight import db
        db.create_all(bind_key="dw")