import pandas as pd
from db_config import connect_db
from datetime import datetime
import numpy as np


# ==================== UTILITAIRES ====================

def _convert_types(df):
    """Convertit les types numpy en types Python natifs"""
    for col in df.columns:
        if pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].astype(int)
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].astype(float)
        elif pd.api.types.is_object_dtype(df[col]):
            df[col] = df[col].astype(str)
    return df


# ==================== FONCTIONS VENTES ====================

def get_ventes():
    """Récupère toutes les ventes avec jointures"""
    conn = connect_db()
    try:
        query = """
        SELECT 
            v.id,
            v.date_vente,
            v.produit_id,
            v.client_id,
            p.nom as produit, 
            p.categorie,
            c.nom as client,
            v.quantite,
            v.montant
        FROM ventes v
        LEFT JOIN produits p ON v.produit_id = p.id
        LEFT JOIN clients c ON v.client_id = c.id
        ORDER BY v.date_vente DESC
        """
        df = pd.read_sql(query, conn, parse_dates=['date_vente'])
        return _convert_types(df)
    except Exception as e:
        raise ValueError(f"Erreur lors de la récupération des ventes: {str(e)}")
    finally:
        conn.close()


def insert_vente(date, produit_id, client_id, quantite, montant):
    """Insère une nouvelle vente avec validation"""
    conn = connect_db()
    try:
        # Si la date a une heure, on la convertit au format 'YYYY-MM-DD HH:MM:SS'
        if date:
            # Assurer que la date est au format correct 'YYYY-MM-DD HH:MM:SS'
            date_str = date.strftime('%Y-%m-%d %H:%M:%S')  # Format complet avec l'heure
        else:
            date_str = None

        print(f"Insertion de la vente avec la date : {date_str}")  # Debug print

        # Paramètres pour l'insertion
        params = (
            date_str,
            int(produit_id),
            int(client_id),
            int(quantite),
            float(montant)
        )

        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO ventes 
        (date_vente, produit_id, client_id, quantite, montant) 
        VALUES (?, ?, ?, ?, ?)
        """, params)
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Erreur insertion vente: {str(e)}")
    finally:
        conn.close()

def update_vente(vente_id, date, produit_id, client_id, quantite, montant):
    """Met à jour une vente existante"""
    conn = connect_db()
    try:
        date_str = date.strftime('%Y-%m-%d %H:%M:%S') if date else None
        params = (
            date_str,
            int(produit_id),
            int(client_id),
            int(quantite),
            float(montant),
            int(vente_id)
        )

        cursor = conn.cursor()
        cursor.execute("""
        UPDATE ventes SET 
            date_vente=?, 
            produit_id=?, 
            client_id=?, 
            quantite=?, 
            montant=? 
        WHERE id=?
        """, params)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Erreur mise à jour vente: {str(e)}")
    finally:
        conn.close()

def delete_vente(vente_id):
    """Supprime une vente"""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ventes WHERE id=?", (int(vente_id),))
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Erreur suppression vente: {str(e)}")
    finally:
        conn.close()


# ==================== FONCTIONS PRODUITS ====================

def get_produits():
    """Récupère tous les produits"""
    conn = connect_db()
    try:
        df = pd.read_sql("SELECT * FROM produits ORDER BY nom", conn)
        return _convert_types(df)
    except Exception as e:
        raise ValueError(f"Erreur récupération produits: {str(e)}")
    finally:
        conn.close()


def insert_produit(nom, categorie, prix_unitaire):
    """Ajoute un nouveau produit"""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO produits (nom, categorie, prix_unitaire)
        VALUES (?, ?, ?)
        """, (str(nom), str(categorie), float(prix_unitaire)))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Erreur insertion produit: {str(e)}")
    finally:
        conn.close()


def update_produit(produit_id, nom, categorie, prix_unitaire):
    """Met à jour un produit"""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE produits SET 
            nom=?, 
            categorie=?, 
            prix_unitaire=? 
        WHERE id=?
        """, (str(nom), str(categorie), float(prix_unitaire), int(produit_id)))
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Erreur mise à jour produit: {str(e)}")
    finally:
        conn.close()


def delete_produit(produit_id):
    """Supprime un produit"""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM produits WHERE id=?", (int(produit_id),))
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Erreur suppression produit: {str(e)}")
    finally:
        conn.close()


# ==================== FONCTIONS CLIENTS ====================

def get_clients():
    """Récupère tous les clients"""
    conn = connect_db()
    try:
        df = pd.read_sql("SELECT * FROM clients ORDER BY nom", conn)
        return _convert_types(df)
    except Exception as e:
        raise ValueError(f"Erreur récupération clients: {str(e)}")
    finally:
        conn.close()


def insert_client(nom, email, ville):
    """Ajoute un nouveau client"""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO clients (nom, email, ville)
        VALUES (?, ?, ?)
        """, (str(nom), str(email), str(ville)))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Erreur insertion client: {str(e)}")
    finally:
        conn.close()


def update_client(client_id, nom, email, ville):
    """Met à jour un client"""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE clients SET 
            nom=?, 
            email=?, 
            ville=? 
        WHERE id=?
        """, (str(nom), str(email), str(ville), int(client_id)))
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Erreur mise à jour client: {str(e)}")
    finally:
        conn.close()


def delete_client(client_id):
    """Supprime un client"""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clients WHERE id=?", (int(client_id),))
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Erreur suppression client: {str(e)}")
    finally:
        conn.close()


# ==================== FONCTIONS UTILITAIRES ====================

def get_produit_by_id(produit_id):
    """Récupère un produit par son ID"""
    conn = connect_db()
    try:
        df = pd.read_sql("SELECT * FROM produits WHERE id=?", conn, params=(int(produit_id),))
        return _convert_types(df).iloc[0] if not df.empty else None
    except Exception as e:
        raise ValueError(f"Erreur récupération produit: {str(e)}")
    finally:
        conn.close()


def get_client_by_id(client_id):
    """Récupère un client par son ID"""
    conn = connect_db()
    try:
        df = pd.read_sql("SELECT * FROM clients WHERE id=?", conn, params=(int(client_id),))
        return _convert_types(df).iloc[0] if not df.empty else None
    except Exception as e:
        raise ValueError(f"Erreur récupération client: {str(e)}")
    finally:
        conn.close()