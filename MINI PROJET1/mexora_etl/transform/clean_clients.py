"""
============================================================
Mexora Analytics — Nettoyage des Clients
============================================================
Applique les règles de transformation sur les clients :
  R1 - Déduplication sur email normalisé
  R2 - Standardisation du sexe (m/f/inconnu)
  R3 - Validation des dates de naissance (16-100 ans)
  R4 - Validation du format email
  R5 - Harmonisation des villes
============================================================
"""

import pandas as pd
import numpy as np
import re
import logging
from datetime import date

from config.settings import MAPPING_SEXE, MAPPING_VILLES

logger = logging.getLogger('mexora_etl')

# Pattern de validation email
PATTERN_EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


def transform_clients(df: pd.DataFrame, regions_filepath: str) -> pd.DataFrame:
    """
    Applique l'ensemble des règles de nettoyage sur les clients Mexora.
    
    Args:
        df: DataFrame brut des clients
        regions_filepath: Chemin vers regions_maroc.csv
    
    Returns:
        DataFrame clients nettoyé
    """
    initial = len(df)
    logger.info(f"[TRANSFORM] === Début nettoyage clients ({initial} lignes) ===")
    
    # --------------------------------------------------------
    # R1 — Déduplication sur email normalisé
    # Règle : même email (normalisé) = même client → garder l'inscription la plus récente
    # --------------------------------------------------------
    df['email_norm'] = df['email'].str.lower().str.strip()
    df['date_inscription'] = pd.to_datetime(df['date_inscription'], errors='coerce')
    avant_r1 = len(df)
    df = df.sort_values('date_inscription').drop_duplicates(subset=['email_norm'], keep='last')
    logger.info(f"[TRANSFORM] R1 Déduplication clients : {avant_r1 - len(df)} doublons supprimés")
    
    # --------------------------------------------------------
    # R2 — Standardisation du sexe
    # Sources multiples : m/f, 1/0, Homme/Femme, male/female, H
    # Cible : 'm', 'f', 'inconnu'
    # --------------------------------------------------------
    df['sexe'] = df['sexe'].str.lower().str.strip()
    avant_r2 = df['sexe'].value_counts().to_dict()
    df['sexe'] = df['sexe'].map(MAPPING_SEXE).fillna('inconnu')
    nb_inconnu = (df['sexe'] == 'inconnu').sum()
    logger.info(f"[TRANSFORM] R2 Sexe : standardisé (valeurs avant: {avant_r2}), "
                f"{nb_inconnu} non reconnus → 'inconnu'")
    
    # --------------------------------------------------------
    # R3 — Validation des dates de naissance
    # Règle : âge doit être entre 16 et 100 ans, sinon → NaT
    # --------------------------------------------------------
    df['date_naissance'] = pd.to_datetime(df['date_naissance'], errors='coerce')
    today = pd.Timestamp(date.today())
    age_days = (today - df['date_naissance']).dt.days
    df['age'] = pd.to_numeric(age_days / 365.25, errors='coerce').astype('float64')
    df['age'] = df['age'].where(df['age'].notna(), other=None)
    
    # Invalider les âges aberrants
    masque_invalide = (df['age'] < 16) | (df['age'] > 100)
    nb_age_invalide = masque_invalide.sum()
    df.loc[masque_invalide, 'date_naissance'] = pd.NaT
    df.loc[masque_invalide, 'age'] = pd.NA
    logger.info(f"[TRANSFORM] R3 Âges : {nb_age_invalide} dates de naissance invalidées "
                f"(âge < 16 ou > 100 ans)")
    
    # Calcul des tranches d'âge
    age_filled = df['age'].fillna(0).astype(float)
    tranche = pd.cut(
        age_filled,
        bins=[0, 18, 25, 35, 45, 55, 65, 200],
        labels=['<18', '18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
        right=False
    )
    df['tranche_age'] = tranche.astype(str)
    df.loc[df['age'].isna(), 'tranche_age'] = 'Non renseigné'
    
    # --------------------------------------------------------
    # R4 — Validation du format email
    # Pattern : xxx@xxx.xx — sinon → None
    # --------------------------------------------------------
    masque_email_invalide = ~df['email'].str.match(PATTERN_EMAIL, na=False)
    nb_email_invalide = masque_email_invalide.sum()
    df.loc[masque_email_invalide, 'email'] = None
    logger.info(f"[TRANSFORM] R4 Emails : {nb_email_invalide} emails invalides → None")
    
    # --------------------------------------------------------
    # R5 — Harmonisation des villes
    # --------------------------------------------------------
    df_regions = pd.read_csv(regions_filepath, encoding='utf-8')
    mapping = {row['nom_ville_standard'].lower(): row['nom_ville_standard']
               for _, row in df_regions.iterrows()}
    mapping.update({row['code_ville'].lower(): row['nom_ville_standard']
                    for _, row in df_regions.iterrows()})
    mapping.update({k.lower(): v for k, v in MAPPING_VILLES.items()})
    
    df['ville'] = df['ville'].str.strip().str.lower().map(mapping).fillna('Non renseignée')
    
    # --------------------------------------------------------
    # Construction du nom complet
    # --------------------------------------------------------
    df['nom_complet'] = df['prenom'].str.strip() + ' ' + df['nom'].str.strip()
    
    # Nettoyage des colonnes temporaires
    df = df.drop(columns=['email_norm'], errors='ignore')
    
    final = len(df)
    logger.info(f"[TRANSFORM] === Fin nettoyage clients : {initial} → {final} lignes ===")
    
    return df
