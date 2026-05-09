-- ============================================================
-- MEXORA ANALYTICS — Vérification de l'Intégrité Référentielle
-- ============================================================
-- Script : check_integrity.sql
-- Description : Vérifie la cohérence du Data Warehouse après chargement ETL
-- Usage : psql -U postgres -d mexora_dwh -f check_integrity.sql
-- ============================================================

-- ============================================================
-- 1. VÉRIFICATION DU NOMBRE DE LIGNES
-- ============================================================
SELECT '=== COMPTAGE DES TABLES ===' AS section;

SELECT 'dim_temps'    AS table_name, COUNT(*) AS nb_lignes FROM dwh_mexora.dim_temps
UNION ALL
SELECT 'dim_produit',  COUNT(*) FROM dwh_mexora.dim_produit
UNION ALL
SELECT 'dim_client',   COUNT(*) FROM dwh_mexora.dim_client
UNION ALL
SELECT 'dim_region',   COUNT(*) FROM dwh_mexora.dim_region
UNION ALL
SELECT 'dim_livreur',  COUNT(*) FROM dwh_mexora.dim_livreur
UNION ALL
SELECT 'fait_ventes',  COUNT(*) FROM dwh_mexora.fait_ventes
ORDER BY table_name;

-- ============================================================
-- 2. INTÉGRITÉ RÉFÉRENTIELLE — Orphelins dans fait_ventes
-- ============================================================
SELECT '=== VÉRIFICATION DES ORPHELINS ===' AS section;

-- Ventes sans date correspondante
SELECT 'Orphelins id_date' AS test,
       COUNT(*) AS nb_orphelins
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
WHERE t.id_date IS NULL;

-- Ventes sans produit correspondant
SELECT 'Orphelins id_produit' AS test,
       COUNT(*) AS nb_orphelins
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
WHERE p.id_produit_sk IS NULL;

-- Ventes sans client correspondant
SELECT 'Orphelins id_client' AS test,
       COUNT(*) AS nb_orphelins
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_client c ON f.id_client = c.id_client_sk
WHERE c.id_client_sk IS NULL;

-- Ventes sans région correspondante
SELECT 'Orphelins id_region' AS test,
       COUNT(*) AS nb_orphelins
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
WHERE r.id_region IS NULL AND f.id_region != 0;

-- ============================================================
-- 3. VÉRIFICATION DES CONTRAINTES MÉTIER
-- ============================================================
SELECT '=== VÉRIFICATION DES CONTRAINTES MÉTIER ===' AS section;

-- Quantités invalides (doit être 0)
SELECT 'Quantités <= 0' AS test,
       COUNT(*) AS nb_violations
FROM dwh_mexora.fait_ventes
WHERE quantite_vendue <= 0;

-- Montants négatifs (doit être 0)
SELECT 'Montants TTC négatifs' AS test,
       COUNT(*) AS nb_violations
FROM dwh_mexora.fait_ventes
WHERE montant_ttc < 0;

-- Statuts invalides (doit être 0)
SELECT 'Statuts non reconnus' AS test,
       COUNT(*) AS nb_violations
FROM dwh_mexora.fait_ventes
WHERE statut_commande NOT IN ('livré', 'annulé', 'en_cours', 'retourné', 'inconnu');

-- Segments clients invalides (doit être 0)
SELECT 'Segments invalides' AS test,
       COUNT(*) AS nb_violations
FROM dwh_mexora.dim_client
WHERE segment_client NOT IN ('Gold', 'Silver', 'Bronze');

-- ============================================================
-- 4. STATISTIQUES MÉTIER
-- ============================================================
SELECT '=== STATISTIQUES MÉTIER ===' AS section;

-- CA total par statut
SELECT statut_commande,
       COUNT(*) AS nb_commandes,
       ROUND(SUM(montant_ttc), 2) AS ca_ttc_total
FROM dwh_mexora.fait_ventes
GROUP BY statut_commande
ORDER BY ca_ttc_total DESC;

-- Répartition des segments clients
SELECT segment_client,
       COUNT(*) AS nb_clients
FROM dwh_mexora.dim_client
GROUP BY segment_client
ORDER BY nb_clients DESC;

-- Top 5 régions par CA
SELECT r.region_admin,
       ROUND(SUM(f.montant_ttc), 2) AS ca_total
FROM dwh_mexora.fait_ventes f
JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
WHERE f.statut_commande = 'livré'
GROUP BY r.region_admin
ORDER BY ca_total DESC
LIMIT 5;

-- ============================================================
-- 5. VÉRIFICATION DES VUES MATÉRIALISÉES
-- ============================================================
SELECT '=== VÉRIFICATION DES VUES MATÉRIALISÉES ===' AS section;

SELECT 'mv_ca_mensuel' AS vue,
       COUNT(*) AS nb_lignes
FROM reporting_mexora.mv_ca_mensuel
UNION ALL
SELECT 'mv_top_produits', COUNT(*)
FROM reporting_mexora.mv_top_produits
UNION ALL
SELECT 'mv_performance_livreurs', COUNT(*)
FROM reporting_mexora.mv_performance_livreurs;

SELECT '=== TOUTES LES VÉRIFICATIONS TERMINÉES ===' AS section;
