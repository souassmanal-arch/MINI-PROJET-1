"""
============================================================
Mexora Analytics — Pipeline ETL Principal
============================================================
Point d'entrée du pipeline ETL complet.
Orchestre les 3 phases : EXTRACT → TRANSFORM → LOAD

Usage :
    python main.py                  # Pipeline complet avec PostgreSQL
    python main.py --csv-only       # Export CSV sans PostgreSQL
    python main.py --generate-data  # Générer les données d'abord

Auteur : Data Engineer Junior — Mexora
Date   : 2024-2025
============================================================
"""

import sys
import os
import logging
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import (
    COMMANDES_CSV, PRODUITS_JSON, CLIENTS_CSV, REGIONS_CSV,
    DATA_DIR, LOGS_DIR
)
from utils.logger import setup_logger
from extract.extractor import extract_commandes, extract_produits, extract_clients, extract_regions
from transform.clean_commandes import transform_commandes
from transform.clean_clients import transform_clients
from transform.clean_produits import transform_produits
from transform.build_dimensions import (
    build_dim_temps, build_dim_produit, build_dim_client,
    build_dim_region, build_dim_livreur, build_fait_ventes
)
from load.loader import (
    get_engine, creer_schemas, charger_dimension, charger_faits, exporter_csv
)


def run_pipeline(csv_only: bool = False):
    """
    Exécute le pipeline ETL complet en 3 phases.
    
    Args:
        csv_only: Si True, exporte en CSV au lieu de charger dans PostgreSQL
    """
    # Initialisation du logger
    logger = setup_logger()
    
    start = datetime.now()
    logger.info("=" * 70)
    logger.info("       MEXORA ANALYTICS — PIPELINE ETL")
    logger.info(f"       Démarrage : {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"       Mode : {'CSV Export' if csv_only else 'PostgreSQL Load'}")
    logger.info("=" * 70)
    
    try:
        # ====================================================
        # PHASE 1 — EXTRACT
        # ====================================================
        logger.info("")
        logger.info("━" * 50)
        logger.info("  📥 PHASE 1 — EXTRACTION DES DONNÉES")
        logger.info("━" * 50)
        
        df_commandes_raw = extract_commandes(COMMANDES_CSV)
        df_produits_raw  = extract_produits(PRODUITS_JSON)
        df_clients_raw   = extract_clients(CLIENTS_CSV)
        df_regions       = extract_regions(REGIONS_CSV)
        
        logger.info(f"[EXTRACT] Total : {len(df_commandes_raw) + len(df_produits_raw) + len(df_clients_raw)} "
                     f"lignes extraites depuis 4 sources")
        
        # ====================================================
        # PHASE 2 — TRANSFORM
        # ====================================================
        logger.info("")
        logger.info("━" * 50)
        logger.info("  🔄 PHASE 2 — TRANSFORMATION DES DONNÉES")
        logger.info("━" * 50)
        
        # 2.1 — Nettoyage des données sources
        logger.info("\n--- 2.1 Nettoyage des commandes ---")
        df_commandes = transform_commandes(df_commandes_raw, REGIONS_CSV)
        
        logger.info("\n--- 2.2 Nettoyage des clients ---")
        df_clients = transform_clients(df_clients_raw, REGIONS_CSV)
        
        logger.info("\n--- 2.3 Nettoyage des produits ---")
        df_produits = transform_produits(df_produits_raw)
        
        # 2.2 — Construction des dimensions
        logger.info("\n--- 2.4 Construction des dimensions ---")
        dim_temps    = build_dim_temps()
        dim_produit  = build_dim_produit(df_produits)
        dim_client   = build_dim_client(df_clients, df_commandes)
        dim_region   = build_dim_region(df_regions)
        dim_livreur  = build_dim_livreur(df_commandes)
        
        # 2.3 — Construction de la table de faits
        logger.info("\n--- 2.5 Construction de la table de faits ---")
        fait_ventes = build_fait_ventes(
            df_commandes, dim_temps, dim_client,
            dim_produit, dim_region, dim_livreur
        )
        
        # ====================================================
        # PHASE 3 — LOAD
        # ====================================================
        logger.info("")
        logger.info("━" * 50)
        logger.info("  📤 PHASE 3 — CHARGEMENT DES DONNÉES")
        logger.info("━" * 50)
        
        if csv_only:
            # Export CSV (sans PostgreSQL)
            output_dir = os.path.join(DATA_DIR, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            exporter_csv(dim_temps,    os.path.join(output_dir, 'dim_temps.csv'))
            exporter_csv(dim_produit,  os.path.join(output_dir, 'dim_produit.csv'))
            exporter_csv(dim_client,   os.path.join(output_dir, 'dim_client.csv'))
            exporter_csv(dim_region,   os.path.join(output_dir, 'dim_region.csv'))
            exporter_csv(dim_livreur,  os.path.join(output_dir, 'dim_livreur.csv'))
            exporter_csv(fait_ventes,  os.path.join(output_dir, 'fait_ventes.csv'))
            
            logger.info(f"[LOAD] Toutes les tables exportées en CSV dans {output_dir}")
        else:
            # Chargement PostgreSQL
            engine = get_engine()
            creer_schemas(engine)
            
            charger_dimension(dim_temps,    'dim_temps',    engine)
            charger_dimension(dim_produit,  'dim_produit',  engine)
            charger_dimension(dim_client,   'dim_client',   engine)
            charger_dimension(dim_region,   'dim_region',   engine)
            charger_dimension(dim_livreur,  'dim_livreur',  engine)
            charger_faits(fait_ventes, engine)
            
            logger.info("[LOAD] Toutes les tables chargées dans PostgreSQL ✅")
        
        # ====================================================
        # RÉSUMÉ FINAL
        # ====================================================
        duree = (datetime.now() - start).total_seconds()
        logger.info("")
        logger.info("=" * 70)
        logger.info("  ✅ PIPELINE ETL TERMINÉ AVEC SUCCÈS")
        logger.info(f"  ⏱️  Durée totale : {duree:.1f} secondes")
        logger.info(f"  📊 Résumé :")
        logger.info(f"      • dim_temps    : {len(dim_temps):>8} lignes")
        logger.info(f"      • dim_produit  : {len(dim_produit):>8} lignes")
        logger.info(f"      • dim_client   : {len(dim_client):>8} lignes")
        logger.info(f"      • dim_region   : {len(dim_region):>8} lignes")
        logger.info(f"      • dim_livreur  : {len(dim_livreur):>8} lignes")
        logger.info(f"      • fait_ventes  : {len(fait_ventes):>8} lignes")
        logger.info(f"  💰 CA Total TTC : {fait_ventes['montant_ttc'].sum():>15,.2f} MAD")
        logger.info("=" * 70)
        
    except FileNotFoundError as e:
        logger.error(f"❌ Fichier source introuvable : {e}")
        logger.error("💡 Exécutez d'abord : python data/generate_data.py")
        raise
    except Exception as e:
        logger.error(f"❌ ERREUR PIPELINE : {e}", exc_info=True)
        raise


if __name__ == '__main__':
    # Détection des arguments
    csv_only = '--csv-only' in sys.argv
    
    if '--generate-data' in sys.argv:
        print("🔄 Génération des données...")
        os.system(f'python "{os.path.join(DATA_DIR, "generate_data.py")}"')
        print()
    
    run_pipeline(csv_only=csv_only)
