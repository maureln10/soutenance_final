# 🎓 IUADECIS

**Mise en place d'un outil décisionnel pour l'analyse de résultats universitaires**

Solution décisionnelle développée pour l'**Institut Universitaire d'Abidjan (IUA)**, basée sur les principes de la Business Intelligence et des Systèmes d'Aide à la Décision (SIAD).

![Python](https://img.shields.io/badge/Python-3.7+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-black?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1?logo=mysql&logoColor=white)
![License](https://img.shields.io/badge/license-Academic-lightgrey)

---

## 📖 Table des matières

- [À propos](#-à-propos)
- [Fonctionnalités](#-fonctionnalités)
- [Stack technologique](#️-stack-technologique)
- [Architecture](#-architecture)
- [Démarrage rapide](#-démarrage-rapide)
- [Configuration](#️-configuration)
- [Utilisation](#-utilisation)
- [Structure du projet](#-structure-du-projet)
- [Aperçus](#-aperçus)
- [Auteur](#-auteur)

---

## 📌 À propos

**IUADECIS** est une solution décisionnelle adaptée aux besoins de l'IUA, conçue dans le cadre d'un projet de fin d'études (Licence 3 MIAGE). Elle propose une interface simple et intuitive ainsi que des fonctionnalités avancées :

- Analyse des résultats académiques
- Génération de tableaux de bord dynamiques
- Système d'alertes et de recommandations
- Production d'indicateurs de performance (KPI)
- Génération de rapports exportables

L'objectif est d'aider les responsables académiques à prendre des décisions **rapides, pertinentes et fondées sur les données**, afin d'améliorer le pilotage académique et la réussite des étudiants.

---

## ✨ Fonctionnalités

### 🔐 Gestion des rôles
- Authentification sécurisée par rôle
- Deux profils d'accès :
  - **Administrateur** : gestion complète du système (utilisateurs, données, paramètres)
  - **Responsable Pédagogique** : consultation et analyse des résultats

### 📥 Gestion des données
- Import de données (Excel, CSV)
- Nettoyage et validation automatiques
- Pipeline ETL complet
- Data Warehouse centralisé (modèle en étoile)

### 📊 Tableaux de bord
- Vue globale des performances
- Analyse par filière et niveau
- Analyse par matière
- Filtrage multi-critères
- Comparaison inter-années

### 📈 Indicateurs clés (KPI)
- Moyenne générale par étudiant
- Taux de réussite / échec / redoublement
- Classement des filières
- Identification des matières critiques
- Tendances historiques

### 🤖 Aide à la décision
- Moteur de prédiction du risque académique (Machine Learning – RandomForest)
- Alertes automatiques sur les étudiants à risque
- Recommandations personnalisées

### 📄 Export et rapports
- Export PDF / Excel
- Impression des tableaux de bord
- Génération de rapports détaillés

---

## 🛠️ Stack technologique

| Couche | Technologies |
|---|---|
| **Backend** | Flask, Python |
| **Frontend** | HTML, CSS, JavaScript, Chart.js |
| **Base de données** | MySQL, SQLAlchemy |
| **Machine Learning** | scikit-learn (RandomForestClassifier) |
| **Rapports** | ReportLab (PDF), openpyxl (Excel) |
| **Tâches planifiées** | APScheduler |
| **Architecture** | Data Warehouse (modèle en étoile) |
| **Déploiement** | Render, Aiven (MySQL cloud) |

**Composition du code :**

`Python 57%` · `HTML 36.3%` · `CSS 3.8%` · `JavaScript 2.9%`

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌───────────────────┐
│  Sources de      │ --> │  Pipeline    │ --> │  Data Warehouse   │
│  données         │     │  ETL         │     │  (modèle étoile)  │
│  (Excel / CSV)   │     │              │     │                   │
└─────────────────┘     └──────────────┘     └─────────┬─────────┘
                                                          │
                                              ┌───────────▼───────────┐
                                              │  Moteur ML            │
                                              │  (prédiction risque)  │
                                              └───────────┬───────────┘
                                                          │
                          ┌───────────────────────────────▼──────────────────────┐
                          │        Application Flask (Dashboards, KPI, Alertes)   │
                          └───────────────────────────────────────────────────────┘
```

---

## 🚀 Démarrage rapide

### Prérequis

```bash
Python 3.7+
Pipenv (ou pip + venv)
MySQL 5.7+ / MariaDB
```

### Installation

```bash
# Cloner le dépôt
git clone https://github.com/<votre-utilisateur>/iuadecis.git
cd iuadecis

# Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### Configuration de la base de données

```bash
# Créer la base de données MySQL
mysql -u root -p -e "CREATE DATABASE iuadecis;"

# Appliquer les migrations
flask db upgrade
```

### Lancer l'application

```bash
flask run
```

L'application est accessible sur `http://127.0.0.1:5000`.

---

## ⚙️ Configuration

Créer un fichier `.env` à la racine du projet (ne jamais le committer) :

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=votre_cle_secrete
DATABASE_URL=mysql+pymysql://user:password@host:port/iuadecis
```

> ⚠️ **Important** : les identifiants de connexion ne doivent jamais être versionnés. Assurez-vous que `.env` figure dans `.gitignore`.

---

## 📘 Utilisation

1. Se connecter avec un compte **Administrateur** ou **Responsable Pédagogique**
2. Importer les données académiques (Excel/CSV)
3. Laisser le pipeline ETL alimenter le Data Warehouse
4. Consulter les tableaux de bord et indicateurs générés automatiquement
5. Exporter les rapports au format PDF ou Excel selon les besoins

---

## 📂 Structure du projet

```
iuadecis/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models/               # Modèles SQLAlchemy
│   ├── routes/                # Blueprints (routes Flask)
│   ├── ml_engine/             # Moteur de prédiction (RandomForest)
│   ├── etl/                   # Scripts d'import et transformation
│   ├── templates/             # Templates HTML (Jinja2)
│   └── static/                 # CSS, JS, images
├── migrations/                # Migrations Alembic
├── tests/                       # Tests unitaires
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🖼️ Aperçus

### 👨‍🏫 Espace Responsable Pédagogique

| | |
|---|---|
| **Tableau de bord** ![Tableau de bord](image.png) | **Analyse par matière** ![Analyse par matière](image-1.png) |
| **Comparaison par spécialité** ![Comparaison par spécialité](image-2.png) | **Rapport** ![Rapport](image-3.png) |
| **Comparaison par filière** ![Comparaison par filière](image-4.png) | **Analyse démographique** ![Analyse démographique](image-5.png) |
| **Tendances** ![Tendances](image-6.png) | **Alertes et risques** ![Alertes et risques](image-7.png) |
| **Recommandations** ![Recommandations](image-8.png) | |

### 🛠️ Espace Administrateur système

| | |
|---|---|
| **Vue administrative** ![Vue administrative](image-9.png) | **Gestion des utilisateurs** ![Gestion des utilisateurs](image-10.png) |
| **Connexion ETL** ![Connexion ETL](image-11.png) | **Paramétrage académique** ![Paramétrage académique](image-12.png) |
| **Import de données** ![Import de données](image-13.png) | |

---

## 👤 Auteur

**N'GUESSAN Marc Maurel**
Étudiant en Licence 3 MIAGE — Institut Universitaire d'Abidjan (IUA)
Projet réalisé sous la supervision du **Dr. ATTA Ferdinand**

---

## 📄 Licence

Projet académique réalisé dans le cadre d'un mémoire de fin d'études à l'IUA.