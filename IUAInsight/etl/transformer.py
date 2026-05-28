"""
ETL - Transformateur
Convertit les données OLTP brutes en enregistrements
prêts à être chargés dans le Data Warehouse.
"""

from datetime import datetime, date


class Transformer:
    """Transforme les données extraites en dicts prêts pour le DW."""

    # ══════════════════════════════════════════
    #  DIMENSIONS
    # ══════════════════════════════════════════

    def transform_etudiants(self, etudiants):
        """Transforme les étudiants → DimEtudiant."""
        result = []
        for e in etudiants:
            result.append({
                'id_etudiant':    e.id_etudiant,
                'matricule':      e.matricule,
                'nom':            e.nom,
                'prenom':         e.prenom,
                'genre':          e.genre or 'Non renseigné',
                'annee_naissance':e.annee_naissance,
                'nationalite':    e.nationalite.pays if e.nationalite else 'Non renseigné',
                'charge_at':      datetime.utcnow(),
            })
        print(f"[Transformer] {len(result)} étudiants transformés → DimEtudiant")
        return result

    def transform_filieres(self, filieres, specialites):
        """Transforme filières + spécialités → DimFiliere."""
        result = []
        for f in filieres:
            specs_filiere = [s for s in specialites if s.id_filiere == f.id_filiere]
            if specs_filiere:
                for s in specs_filiere:
                    result.append({
                        'id_filiere':     f.id_filiere,
                        'nom_filiere':    f.nom_filiere,
                        'nom_specialite': s.nom_specialite,
                        'charge_at':      datetime.utcnow(),
                    })
            else:
                result.append({
                    'id_filiere':     f.id_filiere,
                    'nom_filiere':    f.nom_filiere,
                    'nom_specialite': None,
                    'charge_at':      datetime.utcnow(),
                })
        print(f"[Transformer] {len(result)} entrées transformées → DimFiliere")
        return result

    def transform_niveaux(self, niveaux):
        """Transforme les niveaux → DimNiveau."""
        result = []
        for n in niveaux:
            result.append({
                'id_niveau':          n.id_niveau,
                'libelle':            n.libelle,
                'credits_requis':     n.credits_requis,
                'credits_admission':  n.credits_admission,
                'ordre':              n.ordre,
                'charge_at':          datetime.utcnow(),
            })
        print(f"[Transformer] {len(result)} niveaux transformés → DimNiveau")
        return result

    def transform_annees(self, annees):
        """Transforme les années scolaires → DimAnnee."""
        result = []
        for a in annees:
            result.append({
                'id_annee':   a.id_annee,
                'libelle':    a.libelle,
                'date_debut': a.date_debut,
                'date_fin':   a.date_fin,
                'charge_at':  datetime.utcnow(),
            })
        print(f"[Transformer] {len(result)} années transformées → DimAnnee")
        return result

    def transform_matieres(self, matieres):
        """Transforme les matières → DimMatiere."""
        result = []
        for m in matieres:
            result.append({
                'id_matiere':   m.id_matiere,
                'nom_matiere':  m.nom_matiere,
                'code_matiere': m.code_matiere,
                'credit':       m.credit,
                'coefficient':  m.coefficient,
                'nom_ue':       m.ue.nom          if m.ue       else None,
                'nom_semestre': m.semestre.libelle if m.semestre else None,
                'charge_at':    datetime.utcnow(),
            })
        print(f"[Transformer] {len(result)} matières transformées → DimMatiere")
        return result

    def transform_temps(self, dates):
        """Génère les entrées DimTemps depuis une liste de dates."""
        MOIS_FR = {
            1: 'Janvier', 2: 'Février',  3: 'Mars',      4: 'Avril',
            5: 'Mai',     6: 'Juin',     7: 'Juillet',   8: 'Août',
            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
        }
        result = []
        seen   = set()
        for d in dates:
            if d and d not in seen:
                seen.add(d)
                result.append({
                    'date':      d,
                    'jour':      d.day,
                    'mois':      d.month,
                    'annee':     d.year,
                    'trimestre': (d.month - 1) // 3 + 1,
                    'nom_mois':  MOIS_FR.get(d.month, ''),
                })
        print(f"[Transformer] {len(result)} dates transformées → DimTemps")
        return result

    # ══════════════════════════════════════════
    #  TABLE DE FAITS PRINCIPALE
    # ══════════════════════════════════════════

    def transform_faits_resultats(self, inscriptions):
        """
        Transforme les inscriptions → FaitResultatEtudiant.
        Calcule les indicateurs analytiques clés.
        """
        result = []
        for insc in inscriptions:
            # Sécurisation : statut ne sera jamais None
            statut          = insc.statut_simple or ''
            credits_requis  = insc._credits_requis()
            credits_valides = insc.credits_valides or 0

            # Taux de réussite en crédits (0-100)
            taux_credits = round(
                (credits_valides / credits_requis * 100), 2
            ) if credits_requis > 0 else 0.0

            # Drapeaux statut — calculés une seule fois proprement
            est_admis    = statut in ('Admis', 'Admis (dettes)')
            est_ajourne  = 'Ajourné' in statut
            est_en_dette = statut == 'Admis (dettes)'
            credits_dus  = max(0, credits_requis - credits_valides) if est_en_dette else 0

            result.append({
                'id_inscription':        insc.id_inscription,
                # Clés naturelles (pour retrouver les dim IDs après insertion)
                '_id_etudiant':          insc.id_etudiant,
                '_id_filiere':           insc.id_filiere,
                '_id_niveau':            insc.id_niveau,
                '_id_annee':             insc.id_annee,
                # Mesures
                'moyenne_s1':            insc.moyenne_s1,
                'moyenne_s2':            insc.moyenne_s2,
                'moyenne_annuelle':      insc.moyenne_annuelle,
                'credits_valides_s1':    insc.credits_valides_s1,
                'credits_valides_s2':    insc.credits_valides_s2,
                'credits_valides':       credits_valides,
                'credits_requis':        credits_requis,
                'taux_reussite_credits': taux_credits,
                # Attributs dégénérés
                'mention':               insc.mention,
                'statut':                statut,
                'est_redoublant':        insc.est_redoublant,
                'est_admis':             est_admis,
                'est_ajourne':           est_ajourne,
                'est_en_dette':          est_en_dette,  # corrigé : manquait
                'credits_dus':           credits_dus,   # corrigé : manquait
                'charge_at':             datetime.utcnow(),
                'maj_at':                datetime.utcnow(),
            })

        print(f"[Transformer] {len(result)} faits résultats transformés → FaitResultatEtudiant")
        return result

    # ══════════════════════════════════════════
    #  TABLE DE FAITS SECONDAIRE : ABSENCES
    # ══════════════════════════════════════════

    def transform_faits_absences(self, absences):
        """Transforme les absences → FaitAbsence."""
        result = []
        for a in absences:
            result.append({
                'id_absence':         a.id,
                '_id_etudiant':       a.id_etudiant,
                '_id_matiere':        a.id_matiere,
                '_date':              a.date,
                'nb_absences':        1,
                'nb_justifiees':      1 if a.justifie else 0,
                'nb_non_justifiees':  0 if a.justifie else 1,
                'charge_at':          datetime.utcnow(),
            })
        print(f"[Transformer] {len(result)} absences transformées → FaitAbsence")
        return result

    # ══════════════════════════════════════════
    #  POINT D'ENTRÉE PRINCIPAL
    # ══════════════════════════════════════════

    def transform_all(self, data):
        """
        Transforme toutes les données extraites.
        Retourne un dict avec les données prêtes pour le loader.
        """
        print(f"\n{'='*50}")
        print(f"[Transformer] Début de la transformation")
        print(f"{'='*50}")

        # Collecte toutes les dates pour DimTemps
        dates_absences = [a.date for a in data['absences'] if a.date]
        dates_annees   = []
        for a in data['annees']:
            if a.date_debut: dates_annees.append(a.date_debut)
            if a.date_fin:   dates_annees.append(a.date_fin)

        transformed = {
            # Dimensions
            'dim_etudiants': self.transform_etudiants(data['etudiants']),
            'dim_filieres':  self.transform_filieres(data['filieres'], data['specialites']),
            'dim_niveaux':   self.transform_niveaux(data['niveaux']),
            'dim_annees':    self.transform_annees(data['annees']),
            'dim_matieres':  self.transform_matieres(data['matieres']),
            'dim_temps':     self.transform_temps(dates_absences + dates_annees),
            # Faits
            'faits_resultats': self.transform_faits_resultats(data['inscriptions']),
            'faits_absences':  self.transform_faits_absences(data['absences']),
        }

        print(f"[Transformer] ✅ Transformation terminée.")
        return transformed