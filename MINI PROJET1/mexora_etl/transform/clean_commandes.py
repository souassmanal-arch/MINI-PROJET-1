"""
============================================================
Mexora Analytics — Nettoyage des Commandes
============================================================
Applique les 7 règles de transformation obligatoires :
  R1 - Suppression des doublons sur id_commande
  R2 - Standardisation des dates (format YYYY-MM-DD)
  R3 - Harmonisation des noms de villes via référentiel
  R4 - Standardisation des statuts de commande
  R5 - Suppression des quantités <= 0
  R6 - Suppression des prix = 0 (commandes test)
  R7 - Remplacement des id_livreur manquants par -1
============================================================
"""

import pandas as pd
import numpy as np
import logging

from config.settings import MAPPING_VILLES, MAPPING_STATUTS, STATUTS_VALIDES

logger = logging.getLogger('mexora_etl')


def charger_referentiel_villes(filepath: str) -> dict:
    """
    Charge le référentiel géographique et construit un dictionnaire
    de correspondance ville_brute → ville_standard.
    
    Le mapping combine :
      1. Le référentiel officiel regions_maroc.csv
      2. Les correspondances manuelles de settings.py
    """
    df = pd.read_csv(filepath, encoding='utf-8')
    
    # Construire le mapping depuis le référentiel
    mapping = {}
    for _, row in df.iterrows():
        ville_std = row['nom_ville_standard']
        code = row['code_ville'].lower()
        nom_lower = ville_std.lower()
        mapping[nom_lower] = ville_std
        mapping[code] = ville_std
    
    # Ajouter les mappings manuels de settings.py
    mapping.update({k.lower(): v for k, v in MAPPING_VILLES.items()})
    
    logger.info(f"[TRANSFORM] Référentiel villes chargé : {len(mapping)} correspondances")
    return mapping


def transform_commandes(df: pd.DataFrame, regions_filepath: str) -> pd.DataFrame:
    """
    Applique l'ensemble des règles de nettoyage sur les commandes Mexora.
    
    Args:
        df: DataFrame brut des commandes
        regions_filepath: Chemin vers le fichier regions_maroc.csv
    
    Returns:
        DataFrame nettoyé et standardisé
    """
    initial = len(df)
    logger.info(f"[TRANSFORM] === Début nettoyage commandes ({initial} lignes) ===")
    
    # --------------------------------------------------------
    # R1 — Suppression des doublons sur id_commande
    # Règle métier : conserver la dernière occurrence (mise à jour la plus récente)
    # --------------------------------------------------------
    avant_r1 = len(df)
    df = df.drop_duplicates(subset=['id_commande'], keep='last')
    nb_doublons = avant_r1 - len(df)
    logger.info(f"[TRANSFORM] R1 Doublons : {nb_doublons} lignes supprimées "
                f"({nb_doublons/avant_r1*100:.1f}%)")
    
    # --------------------------------------------------------
    # R2 — Standardisation des dates
    # Les dates arrivent en formats mixtes : 15/11/2024, 2024-11-15, Nov 15 2024
    # Format cible : YYYY-MM-DD (datetime)
    # --------------------------------------------------------
    df['date_commande'] = pd.to_datetime(
        df['date_commande'], format='mixed', dayfirst=True, errors='coerce'
    )
    dates_invalides = df['date_commande'].isna().sum()
    df = df.dropna(subset=['date_commande'])
    logger.info(f"[TRANSFORM] R2 Dates : {dates_invalides} dates invalides supprimées")
    
    # Standardisation de date_livraison également
    df['date_livraison'] = pd.to_datetime(
        df['date_livraison'], format='mixed', dayfirst=True, errors='coerce'
    )
    
    # --------------------------------------------------------
    # R3 — Harmonisation des villes via le référentiel
    # Exemples : "tanger" → "Tanger", "TNG" → "Tanger", "Tnja" → "Tanger"
    # --------------------------------------------------------
    mapping_villes = charger_referentiel_villes(regions_filepath)
    df['ville_livraison'] = df['ville_livraison'].str.strip().str.lower()
    villes_avant = df['ville_livraison'].nunique()
    df['ville_livraison'] = df['ville_livraison'].map(mapping_villes).fillna('Non renseignée')
    villes_apres = df['ville_livraison'].nunique()
    non_renseignees = (df['ville_livraison'] == 'Non renseignée').sum()
    logger.info(f"[TRANSFORM] R3 Villes : {villes_avant} variantes → {villes_apres} villes standards "
                f"({non_renseignees} non mappées)")
    
    # --------------------------------------------------------
    # R4 — Standardisation des statuts
    # Mapping : "OK" → "en_cours", "KO" → "annulé", "DONE" → "livré", etc.
    # --------------------------------------------------------
    df['statut'] = df['statut'].str.strip()
    df['statut'] = df['statut'].replace(MAPPING_STATUTS)
    invalides_mask = ~df['statut'].isin(STATUTS_VALIDES)
    nb_invalides_statut = invalides_mask.sum()
    df.loc[invalides_mask, 'statut'] = 'inconnu'
    logger.warning(f"[TRANSFORM] R4 Statuts : {nb_invalides_statut} valeurs non reconnues → 'inconnu'")
    
    # --------------------------------------------------------
    # R5 — Suppression des quantités invalides (<=0)
    # Règle métier : une quantité négative est une erreur de saisie
    # --------------------------------------------------------
    df['quantite'] = pd.to_numeric(df['quantite'], errors='coerce')
    avant_r5 = len(df)
    df = df[df['quantite'] > 0]
    logger.info(f"[TRANSFORM] R5 Quantités : {avant_r5 - len(df)} lignes supprimées (quantité <= 0)")
    
    # --------------------------------------------------------
    # R6 — Suppression des prix nuls (commandes test)
    # Règle métier : un prix_unitaire = 0 indique une commande de test
    # --------------------------------------------------------
    df['prix_unitaire'] = pd.to_numeric(df['prix_unitaire'], errors='coerce')
    avant_r6 = len(df)
    df = df[df['prix_unitaire'] > 0]
    logger.info(f"[TRANSFORM] R6 Prix : {avant_r6 - len(df)} commandes test supprimées (prix = 0)")
    
    # --------------------------------------------------------
    # R7 — Gestion des livreurs manquants
    # Règle métier : remplacer par "-1" (livreur inconnu) pour intégrité référentielle
    # --------------------------------------------------------
    df['id_livreur'] = df['id_livreur'].replace('', np.nan)
    nb_manquants = df['id_livreur'].isna().sum()
    df['id_livreur'] = df['id_livreur'].fillna('-1')
    logger.info(f"[TRANSFORM] R7 Livreurs : {nb_manquants} valeurs manquantes → '-1'")
    
    # --------------------------------------------------------
    # Calcul du montant TTC (mesure dérivée)
    # --------------------------------------------------------
    df['quantite'] = df['quantite'].astype(int)
    df['montant_ht'] = (df['quantite'] * df['prix_unitaire']).round(2)
    df['montant_ttc'] = (df['montant_ht'] * 1.20).round(2)  # TVA 20%
    
    # --------------------------------------------------------
    # Calcul du délai de livraison
    # --------------------------------------------------------
    df['delai_livraison_jours'] = (df['date_livraison'] - df['date_commande']).dt.days
    df.loc[df['delai_livraison_jours'] < 0, 'delai_livraison_jours'] = np.nan
    
    # --------------------------------------------------------
    # Résumé final
    # --------------------------------------------------------
    final = len(df)
    logger.info(f"[TRANSFORM] === Fin nettoyage commandes : {initial} → {final} lignes "
                f"({initial - final} supprimées, soit {(initial-final)/initial*100:.1f}%) ===")
    
    return df
