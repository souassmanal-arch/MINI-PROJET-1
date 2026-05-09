"""
============================================================
Mexora Analytics — Générateur de Données Réalistes
============================================================
Génère les 4 fichiers de données brutes avec des problèmes
intentionnels à détecter et corriger dans le pipeline ETL.
============================================================
"""

import pandas as pd
import numpy as np
import json
import os
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 1. RÉFÉRENTIEL RÉGIONS (fichier propre)
# ============================================================
def generate_regions():
    regions = [
        ("TNG", "Tanger", "Tanger-Assilah", "Tanger-Tétouan-Al Hoceïma", "Nord", 1065601, "90000"),
        ("TET", "Tétouan", "Tétouan", "Tanger-Tétouan-Al Hoceïma", "Nord", 380787, "93000"),
        ("AHC", "Al Hoceïma", "Al Hoceïma", "Tanger-Tétouan-Al Hoceïma", "Nord", 395644, "32000"),
        ("CAS", "Casablanca", "Casablanca", "Casablanca-Settat", "Centre", 3359818, "20000"),
        ("MOH", "Mohammedia", "Mohammedia", "Casablanca-Settat", "Centre", 208612, "20800"),
        ("SET", "Settat", "Settat", "Casablanca-Settat", "Centre", 142250, "26000"),
        ("RBT", "Rabat", "Rabat", "Rabat-Salé-Kénitra", "Centre", 577827, "10000"),
        ("SLE", "Salé", "Salé", "Rabat-Salé-Kénitra", "Centre", 890403, "11000"),
        ("KNT", "Kénitra", "Kénitra", "Rabat-Salé-Kénitra", "Centre", 431282, "14000"),
        ("MRK", "Marrakech", "Marrakech", "Marrakech-Safi", "Sud", 928850, "40000"),
        ("SFI", "Safi", "Safi", "Marrakech-Safi", "Sud", 308508, "46000"),
        ("ESS", "Essaouira", "Essaouira", "Marrakech-Safi", "Sud", 77966, "44000"),
        ("FES", "Fès", "Fès", "Fès-Meknès", "Centre", 1150131, "30000"),
        ("MKN", "Meknès", "Meknès", "Fès-Meknès", "Centre", 632079, "50000"),
        ("AGD", "Agadir", "Agadir-Ida Ou Tanane", "Souss-Massa", "Sud", 421844, "80000"),
        ("OJD", "Oujda", "Oujda-Angad", "Oriental", "Est", 494252, "60000"),
        ("NDR", "Nador", "Nador", "Oriental", "Est", 161726, "62000"),
        ("EJD", "El Jadida", "El Jadida", "Casablanca-Settat", "Centre", 194934, "24000"),
        ("BML", "Béni Mellal", "Béni Mellal", "Béni Mellal-Khénifra", "Centre", 192676, "23000"),
        ("TZA", "Taza", "Taza", "Fès-Meknès", "Centre", 148456, "35000"),
        ("KHB", "Khouribga", "Khouribga", "Béni Mellal-Khénifra", "Centre", 196196, "25000"),
        ("LAY", "Laâyoune", "Laâyoune", "Laâyoune-Sakia El Hamra", "Sud", 217732, "70000"),
        ("DKL", "Dakhla", "Oued Ed-Dahab", "Dakhla-Oued Ed-Dahab", "Sud", 106277, "73000"),
        ("GLM", "Guelmim", "Guelmim", "Guelmim-Oued Noun", "Sud", 118318, "81000"),
        ("ERC", "Errachidia", "Errachidia", "Drâa-Tafilalet", "Sud", 92374, "52000"),
        ("TRD", "Taroudant", "Taroudant", "Souss-Massa", "Sud", 80149, "83000"),
    ]
    df = pd.DataFrame(regions, columns=[
        "code_ville", "nom_ville_standard", "province",
        "region_admin", "zone_geo", "population", "code_postal"
    ])
    path = os.path.join(OUTPUT_DIR, "regions_maroc.csv")
    df.to_csv(path, index=False, encoding='utf-8')
    print(f"✅ regions_maroc.csv : {len(df)} lignes")
    return df

# ============================================================
# 2. PRODUITS (JSON avec problèmes)
# ============================================================
def generate_produits():
    produits = []
    categories = {
        "Electronique": {
            "Smartphones": [
                ("iPhone 16 Pro 256Go", "Apple", "Apple MENA", 12999.00, "USA"),
                ("Samsung Galaxy S24 Ultra", "Samsung", "Samsung Maroc", 11499.00, "Corée du Sud"),
                ("Xiaomi 14 Ultra", "Xiaomi", "Xiaomi MENA", 7999.00, "Chine"),
                ("OPPO Find X7", "OPPO", "OPPO Maroc", 6499.00, "Chine"),
                ("Google Pixel 8 Pro", "Google", "Google EMEA", 9999.00, "USA"),
            ],
            "Laptops": [
                ("MacBook Air M3", "Apple", "Apple MENA", 14999.00, "USA"),
                ("Dell XPS 15", "Dell", "Dell Maroc", 13499.00, "USA"),
                ("Lenovo ThinkPad X1", "Lenovo", "Lenovo MENA", 12999.00, "Chine"),
                ("HP Spectre x360", "HP", "HP Maroc", 11999.00, "USA"),
                ("ASUS ZenBook 14", "ASUS", "ASUS MENA", 8999.00, "Taïwan"),
            ],
            "Accessoires": [
                ("AirPods Pro 2", "Apple", "Apple MENA", 2999.00, "USA"),
                ("Samsung Galaxy Buds3", "Samsung", "Samsung Maroc", 1499.00, "Corée du Sud"),
                ("Logitech MX Master 3S", "Logitech", "Logitech EMEA", 899.00, "Suisse"),
                ("Anker PowerBank 20000mAh", "Anker", "Anker MENA", 399.00, "Chine"),
            ],
            "Tablettes": [
                ("iPad Air M2", "Apple", "Apple MENA", 8999.00, "USA"),
                ("Samsung Galaxy Tab S9", "Samsung", "Samsung Maroc", 7499.00, "Corée du Sud"),
            ],
        },
        "Mode": {
            "Vêtements Homme": [
                ("Polo Ralph Lauren Classic", "Ralph Lauren", "Fashion Import MA", 899.00, "USA"),
                ("Jean Levi's 501 Original", "Levi's", "Levi's Maroc", 799.00, "USA"),
                ("T-shirt Nike Dri-FIT", "Nike", "Nike Maroc", 349.00, "Vietnam"),
                ("Chemise Zara Slim Fit", "Zara", "Inditex Maroc", 449.00, "Espagne"),
            ],
            "Vêtements Femme": [
                ("Robe Mango Midi", "Mango", "Mango Maroc", 599.00, "Espagne"),
                ("Sac Michael Kors Jet Set", "Michael Kors", "Fashion Import MA", 2499.00, "USA"),
                ("Abaya Moderne Brodée", "Caftan House", "Artisan Maroc", 1299.00, "Maroc"),
            ],
            "Chaussures": [
                ("Nike Air Max 90", "Nike", "Nike Maroc", 1299.00, "Vietnam"),
                ("Adidas Stan Smith", "Adidas", "Adidas Maroc", 999.00, "Vietnam"),
                ("Babouche Artisanale Fès", "Artisan Fès", "Artisan Maroc", 299.00, "Maroc"),
            ],
        },
        "Alimentation": {
            "Épicerie Fine": [
                ("Huile d'Argan Bio 500ml", "Argan du Souss", "Coopérative Souss", 249.00, "Maroc"),
                ("Miel de Thym Atlas 1kg", "Atlas Miel", "Coopérative Atlas", 399.00, "Maroc"),
                ("Safran de Taliouine 5g", "Safran Taliouine", "Coopérative Taliouine", 199.00, "Maroc"),
                ("Dattes Mejhoul Premium 1kg", "Oasis Errachidia", "Coopérative Draa", 149.00, "Maroc"),
            ],
            "Boissons": [
                ("Thé Vert Gunpowder 500g", "Sultan Tea", "Sultan Import", 89.00, "Chine"),
                ("Café Moulu Arabica 250g", "Café Najjar", "Café Najjar MENA", 79.00, "Brésil"),
            ],
            "Pâtisserie": [
                ("Cornes de Gazelle 500g", "Pâtisserie Bennis", "Pâtisserie Bennis", 129.00, "Maroc"),
                ("Chebakia Traditionnelle 1kg", "Pâtisserie Atlas", "Pâtisserie Atlas", 169.00, "Maroc"),
                ("Ghriba aux Amandes 500g", "Pâtisserie Fès", "Pâtisserie Fès", 119.00, "Maroc"),
            ],
        },
    }

    pid = 1
    for cat, sous_cats in categories.items():
        for sous_cat, items in sous_cats.items():
            for nom, marque, fournisseur, prix, pays in items:
                # Problème intentionnel : casse incohérente des catégories
                cat_display = random.choice([cat, cat.lower(), cat.upper()])
                # Problème intentionnel : certains produits inactifs
                actif = True if pid <= 35 else random.choice([True, False])
                # Problème intentionnel : prix null pour quelques anciens produits
                prix_final = prix if random.random() > 0.05 else None
                produits.append({
                    "id_produit": f"P{pid:03d}",
                    "nom": nom,
                    "categorie": cat_display,
                    "sous_categorie": sous_cat,
                    "marque": marque,
                    "fournisseur": fournisseur,
                    "prix_catalogue": prix_final,
                    "origine_pays": pays,
                    "date_creation": (datetime(2023, 1, 1) + timedelta(days=random.randint(0, 600))).strftime("%Y-%m-%d"),
                    "actif": actif,
                })
                pid += 1

    path = os.path.join(OUTPUT_DIR, "produits_mexora.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"produits": produits}, f, ensure_ascii=False, indent=2)
    print(f"✅ produits_mexora.json : {len(produits)} produits")
    return produits

# ============================================================
# 3. CLIENTS (CSV avec problèmes)
# ============================================================
def generate_clients():
    prenoms_h = ["Mohamed", "Youssef", "Ahmed", "Amine", "Omar", "Hamza", "Mehdi",
                 "Karim", "Rachid", "Hassan", "Said", "Ali", "Khalid", "Adil", "Nabil",
                 "Mustapha", "Zakaria", "Reda", "Brahim", "Driss", "Imad", "Soufiane"]
    prenoms_f = ["Fatima", "Khadija", "Meryem", "Salma", "Amina", "Houda", "Nadia",
                 "Sara", "Laila", "Zineb", "Samira", "Nawal", "Hind", "Asmae", "Rim",
                 "Hanane", "Loubna", "Sanae", "Wafae", "Ilham", "Ghita", "Dounia"]
    noms = ["Alaoui", "Bennani", "Tazi", "El Idrissi", "Berrada", "Fassi Fihri", "Cherkaoui",
            "Amrani", "Benjelloun", "El Mansouri", "Skalli", "Lahlou", "Bouzid", "Chraibi",
            "El Ouazzani", "Kettani", "Sefrioui", "Benkirane", "Ziani", "Haddad", "Bouazza",
            "El Amrani", "Naciri", "Tahiri", "Filali", "Rahmouni", "Benali", "Ouahbi"]
    villes_normales = ["Tanger", "Casablanca", "Rabat", "Marrakech", "Fès", "Agadir",
                       "Oujda", "Kénitra", "Tétouan", "Meknès", "Nador", "Safi",
                       "El Jadida", "Béni Mellal", "Mohammedia"]
    villes_problemes = ["tanger", "TNG", "TANGER", "Tnja", "casa", "CASA", "Casablanca",
                        "rbt", "RABAT", "mkch", "MARRAKECH", "fes", "FES", "Fès"]
    canaux = ["web", "mobile", "marketplace", "social_media", "referral"]
    sexe_values = ["m", "f", "1", "0", "Homme", "Femme", "male", "female", "H", "h"]

    clients = []
    emails_seen = set()

    for i in range(1, 8001):
        is_male = random.random() < 0.55
        prenom = random.choice(prenoms_h if is_male else prenoms_f)
        nom = random.choice(noms)
        
        # Problème : sexe codé différemment
        sexe = random.choice(sexe_values)
        
        # Email avec problèmes intentionnels
        email_base = f"{prenom.lower()}.{nom.lower().replace(' ', '')}".replace("é", "e").replace("è", "e").replace("î", "i").replace("ï", "i")
        domain = random.choice(["gmail.com", "hotmail.com", "yahoo.fr", "outlook.com", "live.fr"])
        email = f"{email_base}{random.randint(1,999)}@{domain}"
        
        # Problème : emails mal formatés (3%)
        if random.random() < 0.03:
            email = random.choice([
                email_base + str(random.randint(1,99)),  # sans @
                f"{email_base}@",                         # sans domaine
                f"@{domain}",                              # sans nom
                f"{email_base}@@{domain}",                 # double @
            ])

        # Problème : doublons clients (même email, id différent) ~5%
        if random.random() < 0.05 and emails_seen:
            email = random.choice(list(emails_seen))
        emails_seen.add(email)

        # Problème : villes incohérentes
        ville = random.choice(villes_normales + villes_problemes)
        
        # Problème : dates de naissance aberrantes (2%)
        if random.random() < 0.02:
            # Âge > 120 ou < 0
            dob = datetime(random.choice([1880, 1890, 2025, 2026]), random.randint(1,12), random.randint(1,28))
        else:
            dob = datetime(random.randint(1960, 2006), random.randint(1, 12), random.randint(1, 28))

        date_insc = datetime(random.randint(2021, 2025), random.randint(1, 12), random.randint(1, 28))
        tel = f"06{random.randint(10000000, 99999999)}"

        clients.append({
            "id_client": f"C{i:05d}",
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "date_naissance": dob.strftime("%Y-%m-%d"),
            "sexe": sexe,
            "ville": ville,
            "telephone": tel,
            "date_inscription": date_insc.strftime("%Y-%m-%d"),
            "canal_acquisition": random.choice(canaux),
        })

    df = pd.DataFrame(clients)
    path = os.path.join(OUTPUT_DIR, "clients_mexora.csv")
    df.to_csv(path, index=False, encoding='utf-8')
    print(f"✅ clients_mexora.csv : {len(df)} lignes")
    return df

# ============================================================
# 4. COMMANDES (CSV 50 000 lignes avec problèmes)
# ============================================================
def generate_commandes(produits_list, clients_df):
    villes_normales = ["Tanger", "Casablanca", "Rabat", "Marrakech", "Fès", "Agadir",
                       "Oujda", "Kénitra", "Tétouan", "Meknès"]
    villes_problemes = ["tanger", "TNG", "TANGER", "Tnja", "casa", "CASA",
                        "rbt", "RABAT", "mkch", "fes"]
    
    statuts_normaux = ["livré", "annulé", "en_cours", "retourné"]
    statuts_problemes = ["OK", "KO", "DONE", "livre", "LIVRE", "annule", "retourne"]
    
    modes_paiement = ["carte_bancaire", "virement", "cash_delivery", "mobile_payment"]
    
    product_ids = [p["id_produit"] for p in produits_list]
    product_prices = {p["id_produit"]: p["prix_catalogue"] or 500.0 for p in produits_list}
    client_ids = clients_df["id_client"].tolist()
    
    livreurs = [f"L{i:03d}" for i in range(1, 51)]
    
    date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%b %d %Y"]

    commandes = []
    for i in range(1, 50001):
        cid = f"CMD{i:06d}"
        id_client = random.choice(client_ids)
        id_produit = random.choice(product_ids)
        
        date_cmd = datetime(2022, 1, 1) + timedelta(days=random.randint(0, 1095))
        # Problème : dates en formats mixtes
        fmt = random.choice(date_formats)
        date_cmd_str = date_cmd.strftime(fmt)
        
        quantite = random.randint(1, 5)
        # Problème : quantités négatives (~1%)
        if random.random() < 0.01:
            quantite = -random.randint(1, 3)
        
        prix = product_prices.get(id_produit, 500.0)
        # Problème : prix = 0 (commandes test, ~1.5%)
        if random.random() < 0.015:
            prix = 0.0
        # Ajouter variation
        prix = round(prix * random.uniform(0.85, 1.15), 2)

        # Problème : statuts non standards
        statut = random.choice(statuts_normaux * 3 + statuts_problemes)
        
        ville = random.choice(villes_normales * 2 + villes_problemes)
        mode = random.choice(modes_paiement)
        
        # Problème : id_livreur manquant (~7%)
        id_livreur = random.choice(livreurs) if random.random() > 0.07 else ""
        
        # Date livraison
        if statut in ["livré", "livre", "LIVRE", "DONE"]:
            date_liv = date_cmd + timedelta(days=random.randint(1, 7))
            date_liv_str = date_liv.strftime("%Y-%m-%d")
        else:
            date_liv_str = ""

        commandes.append({
            "id_commande": cid,
            "id_client": id_client,
            "id_produit": id_produit,
            "date_commande": date_cmd_str,
            "quantite": quantite,
            "prix_unitaire": prix,
            "statut": statut,
            "ville_livraison": ville,
            "mode_paiement": mode,
            "id_livreur": id_livreur,
            "date_livraison": date_liv_str,
        })

    df = pd.DataFrame(commandes)
    
    # Problème : doublons (~3%)
    n_dup = int(len(df) * 0.03)
    duplicates = df.sample(n=n_dup).copy()
    # Modifier légèrement certaines valeurs pour simuler des doublons réalistes
    duplicates["quantite"] = duplicates["quantite"].apply(lambda x: x + random.choice([0, 0, 1]))
    df = pd.concat([df, duplicates], ignore_index=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    path = os.path.join(OUTPUT_DIR, "commandes_mexora.csv")
    df.to_csv(path, index=False, encoding='utf-8')
    print(f"✅ commandes_mexora.csv : {len(df)} lignes (dont ~{n_dup} doublons)")
    return df


# ============================================================
# MAIN — Génération complète
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("MEXORA ANALYTICS — Génération des données")
    print("=" * 60)
    
    df_regions = generate_regions()
    produits = generate_produits()
    df_clients = generate_clients()
    df_commandes = generate_commandes(produits, df_clients)
    
    print("\n" + "=" * 60)
    print("✅ Tous les fichiers ont été générés avec succès !")
    print("=" * 60)
