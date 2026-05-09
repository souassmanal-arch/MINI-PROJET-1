"""
============================================================
Mexora Analytics — Module d'Extraction (Extract)
============================================================
Fonctions d'extraction des données depuis les sources brutes :
  - commandes_mexora.csv   (CSV, 50 000+ lignes)
  - produits_mexora.json   (JSON)
  - clients_mexora.csv     (CSV)
  - regions_maroc.csv      (CSV — référentiel)

Principe : lire les données SANS transformation.
Tout est importé en type string pour éviter les conversions implicites.
============================================================
"""

import pandas as pd
import json
import logging
import os

logger = logging.getLogger('mexora_etl')


def extract_commandes(filepath: str) -> pd.DataFrame:
    """
    Extrait les commandes depuis le fichier CSV source.
    
    Args:
        filepath: Chemin vers commandes_mexora.csv
    
    Returns:
        DataFrame brut sans aucune modification
    
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier introuvable : {filepath}")
    
    df = pd.read_csv(filepath, encoding='utf-8', dtype=str)
    # Nettoyer les noms de colonnes (espaces éventuels)
    df.columns = df.columns.str.strip()
    
    logger.info(f"[EXTRACT] Commandes : {len(df)} lignes extraites depuis {filepath}")
    logger.info(f"[EXTRACT] Colonnes : {list(df.columns)}")
    
    return df


def extract_produits(filepath: str) -> pd.DataFrame:
    """
    Extrait les produits depuis le fichier JSON source.
    
    Args:
        filepath: Chemin vers produits_mexora.json
    
    Returns:
        DataFrame brut des produits
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier introuvable : {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data['produits'])
    
    logger.info(f"[EXTRACT] Produits : {len(df)} lignes extraites depuis {filepath}")
    logger.info(f"[EXTRACT] Colonnes : {list(df.columns)}")
    
    return df


def extract_clients(filepath: str) -> pd.DataFrame:
    """
    Extrait les clients depuis le fichier CSV source.
    
    Args:
        filepath: Chemin vers clients_mexora.csv
    
    Returns:
        DataFrame brut des clients
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier introuvable : {filepath}")
    
    df = pd.read_csv(filepath, encoding='utf-8', dtype=str)
    df.columns = df.columns.str.strip()
    
    logger.info(f"[EXTRACT] Clients : {len(df)} lignes extraites depuis {filepath}")
    logger.info(f"[EXTRACT] Colonnes : {list(df.columns)}")
    
    return df


def extract_regions(filepath: str) -> pd.DataFrame:
    """
    Extrait le référentiel géographique officiel.
    Ce fichier est propre et sert de table de correspondance.
    
    Args:
        filepath: Chemin vers regions_maroc.csv
    
    Returns:
        DataFrame du référentiel régions
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier introuvable : {filepath}")
    
    df = pd.read_csv(filepath, encoding='utf-8')
    
    logger.info(f"[EXTRACT] Régions : {len(df)} lignes extraites depuis {filepath}")
    
    return df
