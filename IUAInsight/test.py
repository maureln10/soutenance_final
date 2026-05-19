print("=== DEBUG tableau_m ===")
print("annee_active:", annee_active)
print("filiere_selected:", filiere_selected)
print("niveau_selected:", niveau_selected)
print("semestre_selected:", semestre_selected)

# Vérifie que la base_query remonte des résultats
resultats_count = base_query.count()
print("Nombre de résultats dans base_query:", resultats_count)

# Vérifie echec_agg
print("echec_agg rows:", len(echec_agg))
for row in echec_agg:
    print(f"  matiere_id={row.id_matiere}, nom={row.nom_matiere}, total={row.total}, echecs={row.echecs}")

# Vérifie matieres_map
print("matieres_map keys:", list(matieres_map.keys()))

# Vérifie stats avant filtre
print("stats (avant filtre 50%):", len(stats))
for s in stats:
    print(f"  {s['matiere']} → taux={s['taux_echec']}%")
def apply_db_config(uri: str):
    """Applique une nouvelle URI de BD sans redémarrage."""
    from sqlalchemy import create_engine, text

    new_engine = create_engine(uri, pool_pre_ping=True, pool_recycle=3600)

    # Valider la connexion
    with new_engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    db.engine.dispose()
    db.session.remove()

    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    db.engine = new_engine
    db.session.bind = new_engine