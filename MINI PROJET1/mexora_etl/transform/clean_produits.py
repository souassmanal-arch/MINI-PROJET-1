"""
============================================================
Mexora Analytics — Nettoyage des Produits
============================================================
Applique les règles de transformation sur les produits :
  R1 - Standardisation de la casse des catégories
  R2 - Gestion des prix catalogue null
  R3 - Gestion des produits inactifs (SCD)
============================================================
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger('mexora_etl')


def transform_produits(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique les règles de nettoyage sur les produits Mexora.
    
    Args:
        df: DataFrame brut des produits (extrait du JSON)
    
    Returns:
        DataFrame produits nettoyé et standardisé
    """
    initial = len(df)
    logger.info(f"[TRANSFORM] === Début nettoyage produits ({initial} lignes) ===")
    
    # --------------------------------------------------------
    # R1 — Standardisation de la casse des catégories
    # Problème : "electronique", "Electronique", "ELECTRONIQUE"
    # Cible : casse titre (première lettre majuscule)
    # --------------------------------------------------------
    categories_avant = df['categorie'].unique().tolist()
    df['categorie'] = df['categorie'].str.strip().str.title()
    df['sous_categorie'] = df['sous_categorie'].str.strip().str.title()
    categories_apres = df['categorie'].unique().tolist()
    logger.info(f"[TRANSFORM] R1 Catégories : {len(categories_avant)} variantes "
                f"→ {len(categories_apres)} catégories standards")
    logger.info(f"[TRANSFORM] R1 Détail : {categories_avant} → {categories_apres}")
    
    # --------------------------------------------------------
    # R2 — Gestion des prix catalogue null
    # Règle : remplacer par la médiane de la même catégorie
    # --------------------------------------------------------
    df['prix_catalogue'] = pd.to_numeric(df['prix_catalogue'], errors='coerce')
    nb_prix_null = df['prix_catalogue'].isna().sum()
    
    if nb_prix_null > 0:
        # Imputation par la médiane de la catégorie
        mediane_par_cat = df.groupby('categorie')['prix_catalogue'].transform('median')
        df['prix_catalogue'] = df['prix_catalogue'].fillna(mediane_par_cat)
        # Si toujours null (catégorie entière sans prix), utiliser la médiane globale
        df['prix_catalogue'] = df['prix_catalogue'].fillna(df['prix_catalogue'].median())
    
    logger.info(f"[TRANSFORM] R2 Prix null : {nb_prix_null} prix catalogue imputés par médiane")
    
    # --------------------------------------------------------
    # R3 — Gestion des produits inactifs (préparation SCD Type 2)
    # Les produits inactifs sont conservés avec un flag pour le suivi historique
    # --------------------------------------------------------
    nb_inactifs = (~df['actif']).sum() if 'actif' in df.columns else 0
    logger.info(f"[TRANSFORM] R3 Produits inactifs : {nb_inactifs} produits marqués inactifs "
                f"(conservés pour SCD Type 2)")
    
    # --------------------------------------------------------
    # Standardisation des autres champs
    # --------------------------------------------------------
    df['marque'] = df['marque'].str.strip()
    df['fournisseur'] = df['fournisseur'].str.strip()
    df['nom'] = df['nom'].str.strip()
    df['origine_pays'] = df['origine_pays'].str.strip()
    
    # Conversion de la date de création
    df['date_creation'] = pd.to_datetime(df['date_creation'], errors='coerce')
    
    logger.info(f"[TRANSFORM] === Fin nettoyage produits : {initial} → {len(df)} lignes ===")
    
    return df
