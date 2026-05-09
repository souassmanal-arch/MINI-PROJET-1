-- ============================================================
-- MEXORA ANALYTICS — Création du Data Warehouse PostgreSQL
-- ============================================================
-- Script : create_dwh.sql
-- Description : Crée les schémas, tables, index et vues matérialisées
-- Usage : psql -U postgres -d mexora_dwh -f create_dwh.sql
-- ============================================================

-- ============================================================
-- 1. CRÉATION DES SCHÉMAS
-- ============================================================
-- staging_mexora  : données brutes importées (zone d'atterrissage)
-- dwh_mexora      : dimensions et faits (Data Warehouse final)
-- reporting_mexora: vues matérialisées pour le reporting BI

CREATE SCHEMA IF NOT EXISTS staging_mexora;
CREATE SCHEMA IF NOT EXISTS dwh_mexora;
CREATE SCHEMA IF NOT EXISTS reporting_mexora;

-- ============================================================
-- 2. TABLES DE DIMENSIONS
-- ============================================================

-- --------------------------------------------------------
-- DIM_TEMPS — Dimension Temporelle
-- Granularité : 1 ligne = 1 jour calendaire
-- --------------------------------------------------------
DROP TABLE IF EXISTS dwh_mexora.dim_temps CASCADE;
CREATE TABLE dwh_mexora.dim_temps (
    id_date           INTEGER PRIMARY KEY,          -- format YYYYMMDD (ex: 20240315)
    jour              SMALLINT NOT NULL CHECK (jour BETWEEN 1 AND 31),
    mois              SMALLINT NOT NULL CHECK (mois BETWEEN 1 AND 12),
    trimestre         SMALLINT NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    annee             SMALLINT NOT NULL,
    semaine           SMALLINT,
    libelle_jour      VARCHAR(20),                  -- Lundi, Mardi, ...
    libelle_mois      VARCHAR(20),                  -- Janvier, Février, ...
    est_weekend       BOOLEAN DEFAULT FALSE,
    est_ferie_maroc   BOOLEAN DEFAULT FALSE,
    periode_ramadan   BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE dwh_mexora.dim_temps IS 'Dimension temporelle — 1 ligne par jour calendaire';
COMMENT ON COLUMN dwh_mexora.dim_temps.id_date IS 'Clé primaire au format YYYYMMDD';
COMMENT ON COLUMN dwh_mexora.dim_temps.periode_ramadan IS 'True si le jour tombe pendant le Ramadan';

-- --------------------------------------------------------
-- DIM_PRODUIT — Dimension Produit (SCD Type 2)
-- --------------------------------------------------------
DROP TABLE IF EXISTS dwh_mexora.dim_produit CASCADE;
CREATE TABLE dwh_mexora.dim_produit (
    id_produit_sk     SERIAL PRIMARY KEY,           -- Surrogate Key (auto-incrémentée)
    id_produit_nk     VARCHAR(20) NOT NULL,          -- Natural Key (source : P001, P002...)
    nom_produit       VARCHAR(200) NOT NULL,
    categorie         VARCHAR(100),                  -- Electronique, Mode, Alimentation
    sous_categorie    VARCHAR(100),
    marque            VARCHAR(100),
    fournisseur       VARCHAR(100),
    prix_standard     DECIMAL(10,2),
    origine_pays      VARCHAR(50),
    -- Colonnes SCD Type 2
    date_debut        DATE NOT NULL DEFAULT CURRENT_DATE,
    date_fin          DATE NOT NULL DEFAULT '9999-12-31',
    est_actif         BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE dwh_mexora.dim_produit IS 'Dimension produit avec SCD Type 2 — historique des changements';
COMMENT ON COLUMN dwh_mexora.dim_produit.id_produit_sk IS 'Surrogate Key — clé technique auto-générée';
COMMENT ON COLUMN dwh_mexora.dim_produit.id_produit_nk IS 'Natural Key — identifiant source (ex: P001)';

-- --------------------------------------------------------
-- DIM_CLIENT — Dimension Client (avec segmentation)
-- --------------------------------------------------------
DROP TABLE IF EXISTS dwh_mexora.dim_client CASCADE;
CREATE TABLE dwh_mexora.dim_client (
    id_client_sk      SERIAL PRIMARY KEY,
    id_client_nk      VARCHAR(20) NOT NULL,
    nom_complet       VARCHAR(200),
    tranche_age       VARCHAR(20),                   -- <18, 18-24, 25-34, 35-44, 45-54, 55-64, 65+
    sexe              VARCHAR(10),                   -- m, f, inconnu
    ville             VARCHAR(100),
    region_admin      VARCHAR(100),
    segment_client    VARCHAR(20) CHECK (segment_client IN ('Gold', 'Silver', 'Bronze')),
    canal_acquisition VARCHAR(50),                   -- web, mobile, marketplace, social_media, referral
    -- SCD Type 1 : segment_client mis à jour directement
    date_debut        DATE NOT NULL DEFAULT CURRENT_DATE,
    date_fin          DATE NOT NULL DEFAULT '9999-12-31',
    est_actif         BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE dwh_mexora.dim_client IS 'Dimension client — segmentation Gold/Silver/Bronze basée sur CA 12 mois';

-- --------------------------------------------------------
-- DIM_REGION — Dimension Géographique
-- --------------------------------------------------------
DROP TABLE IF EXISTS dwh_mexora.dim_region CASCADE;
CREATE TABLE dwh_mexora.dim_region (
    id_region         SERIAL PRIMARY KEY,
    ville             VARCHAR(100) NOT NULL,
    province          VARCHAR(100),
    region_admin      VARCHAR(100),
    zone_geo          VARCHAR(50),                   -- Nord, Centre, Sud, Est
    pays              VARCHAR(50) DEFAULT 'Maroc'
);

COMMENT ON TABLE dwh_mexora.dim_region IS 'Dimension géographique — référentiel des villes et régions du Maroc';

-- --------------------------------------------------------
-- DIM_LIVREUR — Dimension Livreur
-- --------------------------------------------------------
DROP TABLE IF EXISTS dwh_mexora.dim_livreur CASCADE;
CREATE TABLE dwh_mexora.dim_livreur (
    id_livreur        SERIAL PRIMARY KEY,
    id_livreur_nk     VARCHAR(20),
    nom_livreur       VARCHAR(100),
    type_transport    VARCHAR(50),                   -- Moto, Voiture, Camionnette, Vélo
    zone_couverture   VARCHAR(100)                   -- Nord, Centre, Sud, Est, National
);

COMMENT ON TABLE dwh_mexora.dim_livreur IS 'Dimension livreur — profil et zone de couverture';

-- ============================================================
-- 3. TABLE DE FAITS
-- ============================================================

DROP TABLE IF EXISTS dwh_mexora.fait_ventes CASCADE;
CREATE TABLE dwh_mexora.fait_ventes (
    id_vente              BIGSERIAL PRIMARY KEY,
    -- Clés étrangères vers les dimensions
    id_date               INTEGER     NOT NULL REFERENCES dwh_mexora.dim_temps(id_date),
    id_produit            INTEGER     NOT NULL REFERENCES dwh_mexora.dim_produit(id_produit_sk),
    id_client             INTEGER     NOT NULL REFERENCES dwh_mexora.dim_client(id_client_sk),
    id_region             INTEGER     NOT NULL REFERENCES dwh_mexora.dim_region(id_region),
    id_livreur            INTEGER     REFERENCES dwh_mexora.dim_livreur(id_livreur),
    -- Mesures ADDITIVES (sommables sur toutes les dimensions)
    quantite_vendue       INTEGER     NOT NULL CHECK (quantite_vendue > 0),
    montant_ht            DECIMAL(12,2) NOT NULL,
    montant_ttc           DECIMAL(12,2) NOT NULL,
    cout_livraison        DECIMAL(8,2),
    -- Mesures SEMI-ADDITIVES (non sommables sur la dimension temps)
    delai_livraison_jours SMALLINT,
    -- Mesures NON-ADDITIVES (taux/pourcentages — à recalculer, pas à sommer)
    remise_pct            DECIMAL(5,2) DEFAULT 0,
    -- Métadonnées ETL
    date_chargement       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut_commande       VARCHAR(20) CHECK (statut_commande IN ('livré','annulé','en_cours','retourné','inconnu'))
);

COMMENT ON TABLE dwh_mexora.fait_ventes IS 'Table de faits — 1 ligne = 1 ligne de commande (1 produit dans 1 commande)';

-- ============================================================
-- 4. INDEX
-- ============================================================

-- Index simples sur les clés étrangères (accélèrent les jointures)
CREATE INDEX idx_fv_date     ON dwh_mexora.fait_ventes(id_date);
CREATE INDEX idx_fv_produit  ON dwh_mexora.fait_ventes(id_produit);
CREATE INDEX idx_fv_client   ON dwh_mexora.fait_ventes(id_client);
CREATE INDEX idx_fv_region   ON dwh_mexora.fait_ventes(id_region);
CREATE INDEX idx_fv_livreur  ON dwh_mexora.fait_ventes(id_livreur);

-- Index composites pour les requêtes analytiques fréquentes
CREATE INDEX idx_fv_date_region ON dwh_mexora.fait_ventes(id_date, id_region)
    INCLUDE (montant_ttc, quantite_vendue);

-- Index partiel : seules les commandes livrées (les plus requêtées)
CREATE INDEX idx_fv_statut_livre ON dwh_mexora.fait_ventes(statut_commande)
    WHERE statut_commande = 'livré';

-- Index sur dim_produit pour recherche par catégorie
CREATE INDEX idx_dp_categorie ON dwh_mexora.dim_produit(categorie);
CREATE INDEX idx_dp_nk        ON dwh_mexora.dim_produit(id_produit_nk);

-- Index sur dim_client pour recherche par segment
CREATE INDEX idx_dc_segment ON dwh_mexora.dim_client(segment_client);
CREATE INDEX idx_dc_ville   ON dwh_mexora.dim_client(ville);

-- ============================================================
-- 5. VUES MATÉRIALISÉES (Reporting)
-- ============================================================

-- --------------------------------------------------------
-- VUE 1 — CA mensuel par région et catégorie
-- Usage : analyse de l'évolution du CA, comparaison N-1, effet Ramadan
-- --------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS reporting_mexora.mv_ca_mensuel;
CREATE MATERIALIZED VIEW reporting_mexora.mv_ca_mensuel AS
SELECT
    t.annee,
    t.mois,
    t.libelle_mois,
    BOOL_OR(t.periode_ramadan)               AS inclut_ramadan,
    r.region_admin,
    r.zone_geo,
    r.ville,
    p.categorie,
    SUM(f.montant_ttc)                       AS ca_ttc,
    SUM(f.montant_ht)                        AS ca_ht,
    COUNT(DISTINCT f.id_client)              AS nb_clients_actifs,
    SUM(f.quantite_vendue)                   AS volume_vendu,
    AVG(f.montant_ttc)                       AS panier_moyen,
    COUNT(DISTINCT f.id_vente)               AS nb_commandes
FROM dwh_mexora.fait_ventes f
JOIN dwh_mexora.dim_temps   t ON f.id_date    = t.id_date
JOIN dwh_mexora.dim_region  r ON f.id_region  = r.id_region
JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
WHERE f.statut_commande = 'livré'
GROUP BY t.annee, t.mois, t.libelle_mois,
         r.region_admin, r.zone_geo, r.ville, p.categorie
WITH DATA;

CREATE INDEX ON reporting_mexora.mv_ca_mensuel(annee, mois);
CREATE INDEX ON reporting_mexora.mv_ca_mensuel(region_admin);
CREATE INDEX ON reporting_mexora.mv_ca_mensuel(categorie);

-- --------------------------------------------------------
-- VUE 2 — Top produits par trimestre
-- Usage : classement des produits par CA dans chaque catégorie
-- --------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS reporting_mexora.mv_top_produits;
CREATE MATERIALIZED VIEW reporting_mexora.mv_top_produits AS
SELECT
    t.annee,
    t.trimestre,
    r.ville,
    p.nom_produit,
    p.categorie,
    p.marque,
    SUM(f.quantite_vendue)                   AS qte_totale,
    SUM(f.montant_ttc)                       AS ca_total,
    COUNT(DISTINCT f.id_client)              AS nb_clients_distincts,
    RANK() OVER (
        PARTITION BY t.annee, t.trimestre, p.categorie
        ORDER BY SUM(f.montant_ttc) DESC
    )                                         AS rang_dans_categorie
FROM dwh_mexora.fait_ventes f
JOIN dwh_mexora.dim_temps   t ON f.id_date    = t.id_date
JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
JOIN dwh_mexora.dim_region  r ON f.id_region  = r.id_region
WHERE f.statut_commande = 'livré'
GROUP BY t.annee, t.trimestre, r.ville,
         p.nom_produit, p.categorie, p.marque
WITH DATA;

CREATE INDEX ON reporting_mexora.mv_top_produits(annee, trimestre);
CREATE INDEX ON reporting_mexora.mv_top_produits(ville);

-- --------------------------------------------------------
-- VUE 3 — Performance livreurs (taux de retard)
-- Usage : suivi qualité de service des livreurs
-- --------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS reporting_mexora.mv_performance_livreurs;
CREATE MATERIALIZED VIEW reporting_mexora.mv_performance_livreurs AS
SELECT
    l.nom_livreur,
    l.type_transport,
    l.zone_couverture,
    t.annee,
    t.mois,
    COUNT(*)                                                   AS nb_livraisons,
    AVG(f.delai_livraison_jours)                               AS delai_moyen_jours,
    COUNT(*) FILTER (WHERE f.delai_livraison_jours > 3)        AS nb_livraisons_retard,
    ROUND(
        COUNT(*) FILTER (WHERE f.delai_livraison_jours > 3) * 100.0
        / NULLIF(COUNT(*), 0), 2
    )                                                          AS taux_retard_pct
FROM dwh_mexora.fait_ventes f
JOIN dwh_mexora.dim_livreur l ON f.id_livreur = l.id_livreur
JOIN dwh_mexora.dim_temps   t ON f.id_date    = t.id_date
WHERE f.statut_commande IN ('livré', 'retourné')
  AND f.delai_livraison_jours IS NOT NULL
GROUP BY l.nom_livreur, l.type_transport, l.zone_couverture, t.annee, t.mois
WITH DATA;

CREATE INDEX ON reporting_mexora.mv_performance_livreurs(annee, mois);
CREATE INDEX ON reporting_mexora.mv_performance_livreurs(nom_livreur);

-- ============================================================
-- 6. RAFRAÎCHISSEMENT DES VUES
-- ============================================================
-- À exécuter après chaque chargement ETL :
-- REFRESH MATERIALIZED VIEW CONCURRENTLY reporting_mexora.mv_ca_mensuel;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY reporting_mexora.mv_top_produits;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY reporting_mexora.mv_performance_livreurs;

-- ============================================================
-- FIN DU SCRIPT
-- ============================================================
SELECT 'Data Warehouse Mexora créé avec succès !' AS message;
