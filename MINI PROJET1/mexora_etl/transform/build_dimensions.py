"""
============================================================
Mexora Analytics — Construction des Dimensions
============================================================
Construit les 5 tables de dimensions du schéma en étoile :
  - DIM_TEMPS    : dimension temporelle (jours fériés, Ramadan)
  - DIM_PRODUIT  : dimension produit (SCD Type 2)
  - DIM_CLIENT   : dimension client (segmentation Gold/Silver/Bronze)
  - DIM_REGION   : dimension géographique
  - DIM_LIVREUR  : dimension livreur

Et la table de faits :
  - FAIT_VENTES  : transactions avec mesures additives/semi-additives/non-additives
============================================================
"""

import pandas as pd
import numpy as np
import logging
from datetime import date, timedelta

from config.settings import (
    FERIES_MAROC, RAMADAN_PERIODES,
    DIM_TEMPS_DATE_DEBUT, DIM_TEMPS_DATE_FIN,
    SEUIL_GOLD, SEUIL_SILVER
)

logger = logging.getLogger('mexora_etl')


# ============================================================
# DIM_TEMPS — Dimension Temporelle
# ============================================================
def build_dim_temps(date_debut: str = None, date_fin: str = None) -> pd.DataFrame:
    """
    Génère la dimension temporelle complète entre deux dates.
    Inclut les jours fériés marocains et les périodes Ramadan.
    
    Granularité : 1 ligne = 1 jour calendaire
    """
    debut = date_debut or DIM_TEMPS_DATE_DEBUT
    fin = date_fin or DIM_TEMPS_DATE_FIN
    
    dates = pd.date_range(start=debut, end=fin, freq='D')
    
    df = pd.DataFrame({
        'id_date':         dates.strftime('%Y%m%d').astype(int),
        'date_complete':   dates,
        'jour':            dates.day,
        'mois':            dates.month,
        'trimestre':       dates.quarter,
        'annee':           dates.year,
        'semaine':         dates.isocalendar().week.astype(int),
        'libelle_jour':    dates.strftime('%A'),
        'libelle_mois':    dates.strftime('%B'),
        'est_weekend':     dates.dayofweek >= 5,
        'est_ferie_maroc': dates.strftime('%Y-%m-%d').isin(FERIES_MAROC),
    })
    
    # Calcul période Ramadan
    df['periode_ramadan'] = False
    for debut_r, fin_r in RAMADAN_PERIODES:
        masque = (df['date_complete'] >= debut_r) & (df['date_complete'] <= fin_r)
        df.loc[masque, 'periode_ramadan'] = True
    
    # Colonnes finales
    result = df[['id_date', 'jour', 'mois', 'trimestre', 'annee', 'semaine',
                 'libelle_jour', 'libelle_mois', 'est_weekend',
                 'est_ferie_maroc', 'periode_ramadan']]
    
    logger.info(f"[DIMENSION] dim_temps : {len(result)} jours générés "
                f"({debut} → {fin})")
    
    return result


# ============================================================
# DIM_PRODUIT — Dimension Produit (SCD Type 2)
# ============================================================
def build_dim_produit(df_produits: pd.DataFrame) -> pd.DataFrame:
    """
    Construit la dimension produit avec support SCD Type 2.
    
    SCD Type 2 : historisation des changements de catégorie/prix.
    Chaque version d'un produit est une ligne distincte avec
    date_debut, date_fin et flag est_actif.
    """
    dim = pd.DataFrame({
        'id_produit_nk':  df_produits['id_produit'],
        'nom_produit':    df_produits['nom'],
        'categorie':      df_produits['categorie'],
        'sous_categorie': df_produits['sous_categorie'],
        'marque':         df_produits['marque'],
        'fournisseur':    df_produits['fournisseur'],
        'prix_standard':  df_produits['prix_catalogue'],
        'origine_pays':   df_produits['origine_pays'],
        'date_debut':     df_produits['date_creation'].fillna(pd.Timestamp('2023-01-01')),
        'date_fin':       pd.Timestamp('9999-12-31'),
        'est_actif':      df_produits.get('actif', True),
    })
    
    # Surrogate key
    dim.insert(0, 'id_produit_sk', range(1, len(dim) + 1))
    
    # Marquer les produits inactifs
    if 'actif' in df_produits.columns:
        masque_inactif = ~df_produits['actif'].astype(bool)
        dim.loc[masque_inactif, 'date_fin'] = pd.Timestamp('today').normalize()
        dim.loc[masque_inactif, 'est_actif'] = False
    
    logger.info(f"[DIMENSION] dim_produit : {len(dim)} produits "
                f"({dim['est_actif'].sum()} actifs, "
                f"{(~dim['est_actif']).sum()} inactifs)")
    
    return dim


# ============================================================
# DIM_CLIENT — Dimension Client (avec Segmentation)
# ============================================================
def calculer_segments_clients(df_commandes: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule le segment client (Gold/Silver/Bronze) basé sur le CA cumulé
    des 12 derniers mois pour chaque client.
    
    Règles métier Mexora :
      Gold   : CA 12 mois >= 15 000 MAD
      Silver : CA 12 mois >= 5 000 MAD
      Bronze : CA 12 mois < 5 000 MAD
    """
    date_limite = pd.Timestamp(date.today() - timedelta(days=365))
    
    df_recents = df_commandes[
        (df_commandes['date_commande'] >= date_limite) &
        (df_commandes['statut'] == 'livré')
    ].copy()
    
    if 'montant_ttc' not in df_recents.columns:
        df_recents['montant_ttc'] = (
            df_recents['quantite'].astype(float) * df_recents['prix_unitaire'].astype(float) * 1.20
        )
    
    ca_par_client = df_recents.groupby('id_client')['montant_ttc'].sum().reset_index()
    ca_par_client.columns = ['id_client', 'ca_12m']
    
    def segmenter(ca):
        if ca >= SEUIL_GOLD:
            return 'Gold'
        elif ca >= SEUIL_SILVER:
            return 'Silver'
        else:
            return 'Bronze'
    
    ca_par_client['segment_client'] = ca_par_client['ca_12m'].apply(segmenter)
    
    logger.info(f"[DIMENSION] Segmentation clients : "
                f"Gold={len(ca_par_client[ca_par_client['segment_client']=='Gold'])}, "
                f"Silver={len(ca_par_client[ca_par_client['segment_client']=='Silver'])}, "
                f"Bronze={len(ca_par_client[ca_par_client['segment_client']=='Bronze'])}")
    
    return ca_par_client[['id_client', 'segment_client', 'ca_12m']]


def build_dim_client(df_clients: pd.DataFrame, df_commandes: pd.DataFrame) -> pd.DataFrame:
    """
    Construit la dimension client enrichie avec la segmentation.
    """
    # Calculer les segments
    segments = calculer_segments_clients(df_commandes)
    
    dim = pd.DataFrame({
        'id_client_nk':     df_clients['id_client'],
        'nom_complet':      df_clients['nom_complet'],
        'tranche_age':      df_clients['tranche_age'].astype(str),
        'sexe':             df_clients['sexe'],
        'ville':            df_clients['ville'],
        'canal_acquisition': df_clients['canal_acquisition'],
        'date_debut':       pd.Timestamp('today').normalize(),
        'date_fin':         pd.Timestamp('9999-12-31'),
        'est_actif':        True,
    })
    
    # Joindre les segments
    dim = dim.merge(segments[['id_client', 'segment_client']],
                    left_on='id_client_nk', right_on='id_client', how='left')
    dim['segment_client'] = dim['segment_client'].fillna('Bronze')
    dim = dim.drop(columns=['id_client'], errors='ignore')
    
    # Joindre la région administrative
    dim['region_admin'] = ''  # Sera enrichi par la dim_region
    
    # Surrogate key
    dim.insert(0, 'id_client_sk', range(1, len(dim) + 1))
    
    logger.info(f"[DIMENSION] dim_client : {len(dim)} clients")
    
    return dim


# ============================================================
# DIM_REGION — Dimension Géographique
# ============================================================
def build_dim_region(df_regions: pd.DataFrame) -> pd.DataFrame:
    """
    Construit la dimension région depuis le référentiel officiel.
    """
    dim = pd.DataFrame({
        'ville':        df_regions['nom_ville_standard'],
        'province':     df_regions['province'],
        'region_admin': df_regions['region_admin'],
        'zone_geo':     df_regions['zone_geo'],
        'pays':         'Maroc',
    })
    
    dim.insert(0, 'id_region', range(1, len(dim) + 1))
    
    logger.info(f"[DIMENSION] dim_region : {len(dim)} villes/régions")
    
    return dim


# ============================================================
# DIM_LIVREUR — Dimension Livreur
# ============================================================
def build_dim_livreur(df_commandes: pd.DataFrame) -> pd.DataFrame:
    """
    Construit la dimension livreur à partir des commandes.
    Génère des attributs descriptifs pour chaque livreur unique.
    """
    import random
    random.seed(42)
    
    livreurs_uniques = df_commandes['id_livreur'].unique()
    livreurs_uniques = [l for l in livreurs_uniques if l != '-1']
    
    types_transport = ['Moto', 'Voiture', 'Camionnette', 'Vélo']
    zones = ['Nord', 'Centre', 'Sud', 'Est', 'National']
    prenoms = ['Youssef', 'Ahmed', 'Mohamed', 'Karim', 'Hamza', 'Omar',
               'Rachid', 'Said', 'Driss', 'Mustapha', 'Ali', 'Hassan',
               'Amine', 'Mehdi', 'Zakaria', 'Reda', 'Adil', 'Nabil',
               'Brahim', 'Imad', 'Soufiane', 'Khalid', 'Samir', 'Abdellatif']
    noms_fam = ['Alaoui', 'Bennani', 'Tazi', 'Amrani', 'Berrada', 'Haddad',
                'Ziani', 'Bouazza', 'Naciri', 'Tahiri', 'Filali', 'Ouahbi']
    
    records = []
    for lid in sorted(livreurs_uniques):
        records.append({
            'id_livreur_nk':   lid,
            'nom_livreur':     f"{random.choice(prenoms)} {random.choice(noms_fam)}",
            'type_transport':  random.choice(types_transport),
            'zone_couverture': random.choice(zones),
        })
    
    # Ajouter le livreur inconnu (-1)
    records.append({
        'id_livreur_nk':   '-1',
        'nom_livreur':     'Livreur Inconnu',
        'type_transport':  'Non renseigné',
        'zone_couverture': 'Non renseigné',
    })
    
    dim = pd.DataFrame(records)
    dim.insert(0, 'id_livreur', range(1, len(dim) + 1))
    
    logger.info(f"[DIMENSION] dim_livreur : {len(dim)} livreurs "
                f"(dont 1 'Livreur Inconnu')")
    
    return dim


# ============================================================
# FAIT_VENTES — Table de Faits
# ============================================================
def build_fait_ventes(df_commandes: pd.DataFrame,
                      dim_temps: pd.DataFrame,
                      dim_client: pd.DataFrame,
                      dim_produit: pd.DataFrame,
                      dim_region: pd.DataFrame,
                      dim_livreur: pd.DataFrame) -> pd.DataFrame:
    """
    Construit la table de faits FAIT_VENTES.
    
    Granularité : 1 ligne = 1 ligne de commande (1 produit dans 1 commande)
    
    Mesures :
      - Additives    : quantite_vendue, montant_ht, montant_ttc, cout_livraison
      - Semi-additive: delai_livraison_jours
      - Non-additive : remise_pct
    """
    import random
    random.seed(42)
    
    fait = df_commandes.copy()
    
    # Mapping vers les surrogate keys des dimensions
    # --- DIM_TEMPS ---
    fait['id_date'] = fait['date_commande'].dt.strftime('%Y%m%d').astype(int)
    
    # --- DIM_PRODUIT ---
    produit_map = dim_produit.set_index('id_produit_nk')['id_produit_sk'].to_dict()
    fait['id_produit'] = fait['id_produit'].map(produit_map)
    
    # --- DIM_CLIENT ---
    client_map = dim_client.set_index('id_client_nk')['id_client_sk'].to_dict()
    fait['id_client'] = fait['id_client'].map(client_map)
    
    # --- DIM_REGION ---
    region_map = dim_region.set_index('ville')['id_region'].to_dict()
    fait['id_region'] = fait['ville_livraison'].map(region_map)
    
    # --- DIM_LIVREUR ---
    livreur_map = dim_livreur.set_index('id_livreur_nk')['id_livreur'].to_dict()
    fait['id_livreur'] = fait['id_livreur'].map(livreur_map)
    
    # Supprimer les lignes dont les FK n'ont pas pu être résolues
    avant = len(fait)
    fait = fait.dropna(subset=['id_date', 'id_produit', 'id_client'])
    logger.info(f"[FAIT] Jointures FK : {avant - len(fait)} lignes sans correspondance supprimées")
    
    # Remplir les FK région/livreur manquantes
    fait['id_region'] = fait['id_region'].fillna(0).astype(int)
    fait['id_livreur'] = fait['id_livreur'].fillna(0).astype(int)
    
    # Construction de la table finale
    fait_final = pd.DataFrame({
        'id_date':                fait['id_date'].astype(int),
        'id_produit':             fait['id_produit'].astype(int),
        'id_client':              fait['id_client'].astype(int),
        'id_region':              fait['id_region'].astype(int),
        'id_livreur':             fait['id_livreur'].astype(int),
        'quantite_vendue':        fait['quantite'].astype(int),
        'montant_ht':             fait['montant_ht'].round(2),
        'montant_ttc':            fait['montant_ttc'].round(2),
        'cout_livraison':         np.random.uniform(15, 80, size=len(fait)).round(2),
        'delai_livraison_jours':  fait['delai_livraison_jours'],
        'remise_pct':             np.random.choice([0, 0, 0, 5, 10, 15, 20], size=len(fait)).astype(float),
        'statut_commande':        fait['statut'],
    })
    
    logger.info(f"[FAIT] fait_ventes : {len(fait_final)} lignes construites")
    logger.info(f"[FAIT] CA total TTC : {fait_final['montant_ttc'].sum():,.2f} MAD")
    logger.info(f"[FAIT] Répartition statuts : {fait_final['statut_commande'].value_counts().to_dict()}")
    
    return fait_final
