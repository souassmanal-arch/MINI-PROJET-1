"""
============================================================
Mexora Analytics — Module de Logging
============================================================
Configure le système de logging pour l'ensemble du pipeline ETL.
  - Fichier de log horodaté dans le dossier logs/
  - Sortie console simultanée
  - Format professionnel avec timestamp, niveau et module
============================================================
"""

import logging
import os
from datetime import datetime
from config.settings import LOGS_DIR, LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL


def setup_logger(name: str = 'mexora_etl') -> logging.Logger:
    """
    Configure et retourne un logger professionnel pour le pipeline ETL.
    
    Args:
        name: Nom du logger (défaut: 'mexora_etl')
    
    Returns:
        logging.Logger: Logger configuré avec handlers fichier et console
    """
    # Créer le dossier logs s'il n'existe pas
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Nom du fichier de log avec horodatage
    log_filename = f"etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_filepath = os.path.join(LOGS_DIR, log_filename)
    
    # Création du logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Éviter les handlers dupliqués en cas d'appels multiples
    if logger.handlers:
        return logger
    
    # Formatter commun
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    
    # Handler fichier — enregistre tout dans le fichier log
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler console — affiche les messages en temps réel
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Ajout des handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"Logger initialisé — Fichier: {log_filepath}")
    
    return logger


def get_logger(name: str = 'mexora_etl') -> logging.Logger:
    """
    Récupère un logger existant ou en crée un nouveau.
    Fonction utilitaire pour les sous-modules.
    
    Args:
        name: Nom du logger
    
    Returns:
        logging.Logger: Logger configuré
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
