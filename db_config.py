import sqlite3
from sqlite3 import Error
import os

DB_PATH = 'ventes.db'


def connect_db():
    """Établit une connexion à la base SQLite"""
    try:
        if os.path.dirname(DB_PATH):
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Error as e:
        print(f"Erreur de connexion SQLite: {e}")
        raise


def init_db():
    """Initialise la structure de la base avec mise à jour de la table ventes"""
    conn = connect_db()
    try:
        cursor = conn.cursor()

        # Table clients
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT,
            ville TEXT
        )""")

        # Table produits
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            categorie TEXT,
            prix_unitaire REAL
        )""")

        # Vérifie si la table ventes existe déjà
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ventes'")
        if cursor.fetchone():
            # Renomme l’ancienne table
            cursor.execute("ALTER TABLE ventes RENAME TO ventes_old")

        # Crée la nouvelle table ventes avec date_vente en TEXT
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_vente TEXT NOT NULL,
            produit_id INTEGER,
            client_id INTEGER,
            quantite INTEGER,
            montant REAL,
            FOREIGN KEY (produit_id) REFERENCES produits(id),
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )""")

        # Si l’ancienne table existe, on récupère les données
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ventes_old'")
        if cursor.fetchone():
            cursor.execute("""
            INSERT INTO ventes (id, date_vente, produit_id, client_id, quantite, montant)
            SELECT id, date_vente, produit_id, client_id, quantite, montant FROM ventes_old
            """)
            cursor.execute("DROP TABLE ventes_old")
            print("Migration des données réussie.")

        conn.commit()
        print("Base de données initialisée avec succès.")
    except Error as e:
        print(f"Erreur d'initialisation: {e}")
        raise
    finally:
        conn.close()
