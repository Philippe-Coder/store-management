import sqlite3

def check_table_structure():
    conn = sqlite3.connect('ventes.db')  # Remplace par le chemin de ta base de données
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(ventes);")
        columns = cursor.fetchall()
        for column in columns:
            print(column)  # Affiche les informations sur les colonnes
    except Exception as e:
        print(f"Erreur lors de la récupération des informations de la table : {str(e)}")
    finally:
        conn.close()

# Appel de la fonction
check_table_structure()
