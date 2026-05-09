"""
============================================================
Mexora Analytics — Configuration du Pipeline ETL
============================================================
Ce fichier centralise tous les paramètres de configuration :
  - Chemins des fichiers source
  - Paramètres de connexion PostgreSQL
  - Constantes métier (seuils segmentation, mapping villes, etc.)
  - Paramètres de logging
============================================================
"""

import os

# ============================================================
# CHEMINS DES FICHIERS SOURCE
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Fichiers d'entrée
COMMANDES_CSV    = os.path.join(DATA_DIR, 'commandes_mexora.csv')
PRODUITS_JSON    = os.path.join(DATA_DIR, 'produits_mexora.json')
CLIENTS_CSV      = os.path.join(DATA_DIR, 'clients_mexora.csv')
REGIONS_CSV      = os.path.join(DATA_DIR, 'regions_maroc.csv')

# ============================================================
# CONNEXION POSTGRESQL
# ============================================================
DB_CONFIG = {
    'host':     'localhost',
    'port':     5432,
    'database': 'mexora_dwh',
    'user':     'postgres',
    'password': 'postgres',   # À changer en production
}

# URL SQLAlchemy construite dynamiquement
DB_URL = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# ============================================================
# SCHÉMAS POSTGRESQL
# ============================================================
SCHEMA_STAGING   = 'staging_mexora'
SCHEMA_DWH       = 'dwh_mexora'
SCHEMA_REPORTING = 'reporting_mexora'

# ============================================================
# PARAMÈTRES DE TRANSFORMATION
# ============================================================

# Mapping des villes non-standards vers les noms officiels
# Ce mapping est enrichi par le référentiel regions_maroc.csv
MAPPING_VILLES = {
    'tanger':       'Tanger',
    'tng':          'Tanger',
    'tnja':         'Tanger',
    'tangier':      'Tanger',
    'casablanca':   'Casablanca',
    'casa':         'Casablanca',
    'dar el beida': 'Casablanca',
    'rabat':        'Rabat',
    'rbt':          'Rabat',
    'marrakech':    'Marrakech',
    'marrakesh':    'Marrakech',
    'mkch':         'Marrakech',
    'fes':          'Fès',
    'fès':          'Fès',
    'fez':          'Fès',
    'agadir':       'Agadir',
    'oujda':        'Oujda',
    'kenitra':      'Kénitra',
    'kénitra':      'Kénitra',
    'knitra':       'Kénitra',
    'tetouan':      'Tétouan',
    'tétouan':      'Tétouan',
    'meknes':       'Meknès',
    'meknès':       'Meknès',
    'nador':        'Nador',
    'safi':         'Safi',
    'el jadida':    'El Jadida',
    'beni mellal':  'Béni Mellal',
    'béni mellal':  'Béni Mellal',
    'taza':         'Taza',
    'settat':       'Settat',
    'khouribga':    'Khouribga',
    'mohammedia':   'Mohammedia',
    'laayoune':     'Laâyoune',
    'laâyoune':     'Laâyoune',
    'dakhla':       'Dakhla',
    'guelmim':      'Guelmim',
    'errachidia':   'Errachidia',
    'taroudant':    'Taroudant',
    'essaouira':    'Essaouira',
    'al hoceima':   'Al Hoceïma',
    'al hoceïma':   'Al Hoceïma',
}

# Mapping des statuts non-standards
MAPPING_STATUTS = {
    'livré':     'livré',
    'livre':     'livré',
    'LIVRE':     'livré',
    'DONE':      'livré',
    'delivered': 'livré',
    'annulé':    'annulé',
    'annule':    'annulé',
    'KO':        'annulé',
    'cancelled': 'annulé',
    'en_cours':  'en_cours',
    'en cours':  'en_cours',
    'OK':        'en_cours',
    'pending':   'en_cours',
    'retourné':  'retourné',
    'retourne':  'retourné',
    'returned':  'retourné',
}

# Statuts valides après standardisation
STATUTS_VALIDES = ['livré', 'annulé', 'en_cours', 'retourné']

# Mapping du sexe
MAPPING_SEXE = {
    'm':      'm',
    'f':      'f',
    '1':      'm',
    '0':      'f',
    'homme':  'm',
    'femme':  'f',
    'male':   'm',
    'female': 'f',
    'h':      'm',
    'masculin': 'm',
    'feminin':  'f',
    'féminin':  'f',
}

# ============================================================
# SEUILS DE SEGMENTATION CLIENT
# ============================================================
SEUIL_GOLD   = 15000   # CA 12 mois >= 15 000 MAD
SEUIL_SILVER = 5000    # CA 12 mois >= 5 000 MAD
# Bronze = tout client en dessous de SEUIL_SILVER

# ============================================================
# DIMENSION TEMPORELLE
# ============================================================
DIM_TEMPS_DATE_DEBUT = '2022-01-01'
DIM_TEMPS_DATE_FIN   = '2025-12-31'

# Jours fériés marocains (fixes — à compléter pour chaque année)
FERIES_MAROC = [
    # 2022
    '2022-01-01', '2022-01-11', '2022-05-01', '2022-07-30',
    '2022-08-14', '2022-08-20', '2022-08-21', '2022-11-06', '2022-11-18',
    # 2023
    '2023-01-01', '2023-01-11', '2023-05-01', '2023-07-30',
    '2023-08-14', '2023-08-20', '2023-08-21', '2023-11-06', '2023-11-18',
    # 2024
    '2024-01-01', '2024-01-11', '2024-05-01', '2024-07-30',
    '2024-08-14', '2024-08-20', '2024-08-21', '2024-11-06', '2024-11-18',
    # 2025
    '2025-01-01', '2025-01-11', '2025-05-01', '2025-07-30',
    '2025-08-14', '2025-08-20', '2025-08-21', '2025-11-06', '2025-11-18',
]

# Périodes Ramadan (approximatives — dates grégoriennes)
RAMADAN_PERIODES = [
    ('2022-04-02', '2022-05-01'),
    ('2023-03-22', '2023-04-20'),
    ('2024-03-10', '2024-04-09'),
    ('2025-02-28', '2025-03-29'),
]

# ============================================================
# PARAMÈTRES DE LOGGING
# ============================================================
LOG_FORMAT = '%(asctime)s — %(levelname)s — %(name)s — %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = 'INFO'

# ============================================================
# PARAMÈTRES DE CHARGEMENT
# ============================================================
CHUNK_SIZE = 5000   # Taille des lots pour l'insertion en base
