# 📊 Mexora Analytics — Data Warehouse from Scratch

> **Système décisionnel complet** pour une marketplace e-commerce marocaine.

![Status](https://img.shields.io/badge/Status-Production-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791)
![License](https://img.shields.io/badge/License-Academic-orange)

---

## 🎯 Contexte

**Mexora** est une marketplace e-commerce basée à Tanger qui vend des produits électroniques, de mode et d'alimentation à travers tout le Maroc. Ce projet construit un **système décisionnel complet** depuis la modélisation jusqu'au dashboard final.

### Questions métier auxquelles le système répond :
1. Quelle région génère le plus de CA ? Évolution sur 12 mois ?
2. Quels sont les 10 produits les plus vendus par trimestre à Tanger ?
3. Quel segment client a le panier moyen le plus élevé ?
4. Quel est le taux de retour par catégorie de produit ?
5. Y a-t-il un effet Ramadan visible sur les ventes d'alimentation ?

---

## 🏗️ Architecture du Projet

```
MINI PROJET1/
├── mexora_etl/                     # Pipeline ETL Python
│   ├── config/
│   │   └── settings.py             # Configuration centralisée
│   ├── extract/
│   │   └── extractor.py            # Extraction CSV/JSON
│   ├── transform/
│   │   ├── clean_commandes.py      # Nettoyage commandes (7 règles)
│   │   ├── clean_clients.py        # Nettoyage clients (5 règles)
│   │   ├── clean_produits.py       # Nettoyage produits (3 règles)
│   │   └── build_dimensions.py     # Construction dimensions + faits
│   ├── load/
│   │   └── loader.py               # Chargement PostgreSQL
│   ├── utils/
│   │   └── logger.py               # Logging professionnel
│   ├── data/
│   │   ├── generate_data.py        # Générateur de données réalistes
│   │   ├── commandes_mexora.csv    # 50 000+ commandes (avec problèmes)
│   │   ├── produits_mexora.json    # ~40 produits
│   │   ├── clients_mexora.csv      # ~8 000 clients
│   │   └── regions_maroc.csv       # Référentiel géographique
│   ├── main.py                     # Orchestration du pipeline
│   └── requirements.txt            # Dépendances Python
├── sql/
│   ├── create_dwh.sql              # Création du DWH (DDL complet)
│   └── check_integrity.sql         # Vérification d'intégrité
├── dashboard/
│   ├── index.html                  # Dashboard BI interactif
│   ├── style.css                   # Design premium dark mode
│   └── app.js                      # Graphiques Chart.js

```

---

## 🚀 Installation et Exécution

### Prérequis
- Python 3.11+
- PostgreSQL 15+ (optionnel — mode CSV disponible)
- pip

### 1. Installation des dépendances
```bash
cd mexora_etl
pip install -r requirements.txt
```

### 2. Génération des données
```bash
cd mexora_etl/data
python generate_data.py
```
Ceci crée les 4 fichiers de données brutes avec des **problèmes intentionnels** :
- ~3% de doublons dans les commandes
- Dates en formats mixtes (15/11/2024, 2024-11-15, Nov 15 2024)
- Villes incohérentes (tanger, TNG, TANGER, Tnja)
- Quantités négatives, prix nuls, emails invalides

### 3. Exécution du pipeline ETL

**Mode CSV (sans PostgreSQL) :**
```bash
cd mexora_etl
python main.py --csv-only
```

**Mode PostgreSQL :**
```bash
# 1. Créer la base de données
createdb -U postgres mexora_dwh

# 2. Créer le schéma DWH
psql -U postgres -d mexora_dwh -f sql/create_dwh.sql

# 3. Lancer le pipeline
cd mexora_etl
python main.py
```

### 4. Vérification d'intégrité
```bash
psql -U postgres -d mexora_dwh -f sql/check_integrity.sql
```

### 5. Dashboard BI
Ouvrir `fancy-hummingbird-62722e.netlify.app ` dans un navigateur 
---

## 📐 Modélisation — Schéma en Étoile

### Table de Faits : `FAIT_VENTES`
**Granularité** : 1 ligne = 1 ligne de commande (1 produit dans 1 commande)

| Mesure | Type d'Additivité | Description |
|--------|-------------------|-------------|
| `quantite_vendue` | **Additive** | Sommable sur toutes les dimensions |
| `montant_ht` | **Additive** | CA hors taxes |
| `montant_ttc` | **Additive** | CA TTC (HT × 1.20) |
| `cout_livraison` | **Additive** | Coût de livraison |
| `delai_livraison_jours` | **Semi-additive** | Non sommable sur le temps (moyenne) |
| `remise_pct` | **Non-additive** | Pourcentage — doit être recalculé |
 

### Dimensions (5)

| Dimension | Clé | Attributs clés |
|-----------|-----|----------------|
| `DIM_TEMPS` | `id_date` (YYYYMMDD) | jour, mois, trimestre, Ramadan, fériés Maroc |
| `DIM_PRODUIT` | `id_produit_sk` (SCD2) | catégorie, marque, prix, origine |
| `DIM_CLIENT` | `id_client_sk` | segment Gold/Silver/Bronze, tranche âge |
| `DIM_REGION` | `id_region` | ville, province, région admin, zone géo |
| `DIM_LIVREUR` | `id_livreur` | type transport, zone couverture |

OUVRIR WIKI POUR PLUS DÉTAILLE
### Gestion des SCD
- **SCD Type 2** sur `DIM_PRODUIT` : historisation des changements de catégorie/prix
- **SCD Type 1** sur `DIM_CLIENT` : mise à jour directe du segment client

---

## 🔄 Transformations ETL

### Commandes (7 règles)
| # | Règle | Description |
|---|-------|-------------|
| R1 | Doublons | Suppression ~3% de doublons sur id_commande |
| R2 | Dates | Standardisation formats mixtes → YYYY-MM-DD |
| R3 | Villes | Harmonisation via référentiel (TNG → Tanger) |
| R4 | Statuts | OK → en_cours, KO → annulé, DONE → livré |
| R5 | Quantités | Suppression quantités ≤ 0 |
| R6 | Prix | Suppression prix = 0 (commandes test) |
| R7 | Livreurs | Valeurs manquantes → -1 (livreur inconnu) |

### Clients (5 règles)
| # | Règle | Description |
|---|-------|-------------|
| R1 | Déduplication | Email normalisé, garder inscription récente |
| R2 | Sexe | m/f/1/0/Homme/Femme → m/f/inconnu |
| R3 | Âge | Validation 16-100 ans, sinon invalidé |
| R4 | Email | Validation regex, sinon → NULL |
| R5 | Segmentation | Gold (≥15K) / Silver (≥5K) / Bronze |

---

## 📊 Dashboard BI

Le dashboard interactif répond aux **5 questions métier** :

| Page | Question | Visualisation |
|------|----------|---------------|
| Évolution CA | Quelle région génère le plus de CA ? | Courbe + barres régions |
| Top Produits | Top 10 produits à Tanger par trimestre | Barres horizontales |
| Segments | Quel segment a le meilleur panier moyen ? | Donut + tableau détaillé |
| Taux de Retour | Taux par catégorie (seuils 3%/5%) | Barres avec alertes couleur |
| Effet Ramadan | Impact sur ventes alimentation | Courbe avec zones Ramadan |

---

## 🛠️ Stack Technique

| Outil | Usage |
|-------|-------|
| Python 3.11+ | Pipeline ETL |
| pandas / numpy | Transformation de données |
| SQLAlchemy / psycopg2 | Connexion PostgreSQL |
| PostgreSQL 15+ | Data Warehouse |
| Chart.js | Visualisations dashboard |
| HTML/CSS/JS | Dashboard BI interactif |

---

## 👤 Auteur

Projet réalisé dans le cadre du miniprojet Data Engineering & Business Intelligence.
----
2025-2026
