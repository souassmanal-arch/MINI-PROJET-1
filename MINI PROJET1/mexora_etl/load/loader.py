"""
============================================================
Mexora Analytics — Module de Chargement (Load)
============================================================
Charge les dimensions et la table de faits dans PostgreSQL.
  - Stratégie dimensions : TRUNCATE + RELOAD (replace)
  - Stratégie faits : UPSERT (ON CONFLICT DO UPDATE)
  - Chargement par lots (chunks) pour la performance
============================================================
"""

import pandas as pd
import logging
from sqlalchemy import create_engine, text

from config.settings import DB_URL, SCHEMA_DWH, SCHEMA_STAGING, SCHEMA_REPORTING, CHUNK_SIZE

logger = logging.getLogger('mexora_etl')


def get_engine():
    """
    Crée et retourne un moteur SQLAlchemy connecté à PostgreSQL.
    """
    try:
        engine = create_engine(DB_URL, echo=False)
        # Test de connexion
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"[LOAD] Connexion PostgreSQL établie : {DB_URL.split('@')[1]}")
        return engine
    except Exception as e:
        logger.error(f"[LOAD] Erreur de connexion PostgreSQL : {e}")
        raise


def creer_schemas(engine):
    """
    Crée les 3 schémas PostgreSQL s'ils n'existent pas :
      - staging_mexora  : données brutes importées
      - dwh_mexora      : dimensions et faits (Data Warehouse)
      - reporting_mexora: vues matérialisées pour le reporting
    """
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_STAGING}"))
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_DWH}"))
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_REPORTING}"))
        conn.commit()
    logger.info(f"[LOAD] Schémas créés/vérifiés : {SCHEMA_STAGING}, {SCHEMA_DWH}, {SCHEMA_REPORTING}")


def charger_dimension(df: pd.DataFrame, table_name: str, engine, schema: str = None):
    """
    Charge une table de dimension dans PostgreSQL.
    
    Stratégie : TRUNCATE + RELOAD (replace) pour les dimensions.
    Les dimensions sont entièrement rechargées à chaque exécution du pipeline
    pour garantir la cohérence.
    
    Args:
        df: DataFrame de la dimension à charger
        table_name: Nom de la table cible
        engine: Moteur SQLAlchemy
        schema: Schéma PostgreSQL (défaut: dwh_mexora)
    """
    schema = schema or SCHEMA_DWH
    
    try:
        df.to_sql(
            name=table_name,
            con=engine,
            schema=schema,
            if_exists='replace',
            index=False,
            method='multi',
            chunksize=CHUNK_SIZE
        )
        logger.info(f"[LOAD] {schema}.{table_name} : {len(df)} lignes chargées ✅")
    except Exception as e:
        logger.error(f"[LOAD] Erreur chargement {table_name} : {e}")
        raise


def charger_faits(df: pd.DataFrame, engine, schema: str = None):
    """
    Charge la table de faits dans PostgreSQL.
    
    Stratégie : REPLACE (truncate + reload) pour simplifier.
    En production, on utiliserait un UPSERT avec ON CONFLICT.
    
    Args:
        df: DataFrame de la table de faits
        engine: Moteur SQLAlchemy
        schema: Schéma PostgreSQL
    """
    schema = schema or SCHEMA_DWH
    table_name = 'fait_ventes'
    
    try:
        df.to_sql(
            name=table_name,
            con=engine,
            schema=schema,
            if_exists='replace',
            index=False,
            method='multi',
            chunksize=CHUNK_SIZE
        )
        logger.info(f"[LOAD] {schema}.{table_name} : {len(df)} lignes chargées ✅")
        logger.info(f"[LOAD] CA total chargé : {df['montant_ttc'].sum():,.2f} MAD")
    except Exception as e:
        logger.error(f"[LOAD] Erreur chargement fait_ventes : {e}")
        raise


def charger_staging(df: pd.DataFrame, table_name: str, engine):
    """
    Charge les données brutes dans le schéma staging pour audit.
    """
    charger_dimension(df, table_name, engine, schema=SCHEMA_STAGING)


def exporter_csv(df: pd.DataFrame, filepath: str):
    """
    Exporte un DataFrame en CSV (alternative au chargement PostgreSQL).
    Utile pour le debug ou si PostgreSQL n'est pas disponible.
    """
    df.to_csv(filepath, index=False, encoding='utf-8')
    logger.info(f"[EXPORT] {filepath} : {len(df)} lignes exportées")
