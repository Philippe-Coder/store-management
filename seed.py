from db_config import connect_db

def seed_data():
    conn = connect_db()
    cursor = conn.cursor()

    # Insérer des produits
    produits = [
        ("Stylo bleu", "Papeterie", 1.50),
        ("Carnet A5", "Papeterie", 3.00),
        ("Calculatrice", "Électronique", 15.00),
        ("Clé USB 16GB", "Informatique", 8.00),
        ("Ramette de papier", "Papeterie", 5.50),
        ("Souris sans fil", "Électronique", 12.00),
        ("Agrafeuse", "Bureau", 4.00),
        ("Enveloppes x50", "Papeterie", 2.50),
        ("Tapis de souris", "Bureau", 6.00),
        ("Tableau blanc", "Bureau", 25.00),
    ]
    cursor.executemany("INSERT INTO produits (nom, categorie, prix_unitaire) VALUES (?, ?, ?)", produits)

    # Insérer des clients
    clients = [
        ("Alice Dupont", "alice@example.com", "Paris"),
        ("Bob Martin", "bob@example.com", "Lyon"),
        ("Claire Morel", "claire@example.com", "Marseille"),
        ("David Leroy", "david@example.com", "Toulouse"),
        ("Emma Dubois", "emma@example.com", "Nice"),
        ("François Petit", "francois@example.com", "Nantes"),
        ("Gabrielle Chevalier", "gabrielle@example.com", "Strasbourg"),
        ("Hugo Bernard", "hugo@example.com", "Montpellier"),
        ("Isabelle Fontaine", "isabelle@example.com", "Bordeaux"),
        ("Julien Lefevre", "julien@example.com", "Lille"),
    ]
    cursor.executemany("INSERT INTO clients (nom, email, ville) VALUES (?, ?, ?)", clients)

    # Insérer des ventes avec des dates variées
    ventes = [
        ("2025-02-03", 1, 1, 5, 7.50),
        ("2025-02-05", 2, 2, 2, 6.00),
        ("2025-02-10", 3, 3, 1, 15.00),
        ("2025-02-15", 4, 4, 3, 24.00),
        ("2025-02-20", 5, 5, 1, 5.50),
        ("2025-02-25", 6, 6, 1, 12.00),
        ("2025-03-01", 7, 7, 2, 8.00),
        ("2025-03-05", 8, 8, 1, 2.50),
        ("2025-03-09", 9, 9, 1, 6.00),
        ("2025-03-12", 10, 10, 1, 25.00),
        ("2025-03-15", 3, 1, 1, 15.00),
        ("2025-03-20", 2, 4, 3, 9.00),
        ("2025-03-22", 5, 6, 2, 11.00),
        ("2025-03-27", 6, 7, 1, 12.00),
        ("2025-04-01", 1, 2, 10, 15.00),
        ("2025-04-04", 4, 5, 1, 8.00),
        ("2025-04-07", 7, 6, 1, 4.00),
        ("2025-04-08", 8, 3, 2, 5.00),
        ("2025-04-08", 9, 8, 1, 6.00),
        ("2025-04-08", 10, 9, 1, 25.00),
    ]
    cursor.executemany("INSERT INTO ventes (date_vente, produit_id, client_id, quantite, montant) VALUES (?, ?, ?, ?, ?)", ventes)

    conn.commit()
    conn.close()
    print("✅ Données insérées avec succès avec des dates variées !")

if __name__ == "__main__":
    seed_data()
