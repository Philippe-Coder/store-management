import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from db_config import connect_db, init_db
from crud_operations import *
from ml_forecasting import forecast_sales
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import numpy as np
from fpdf import FPDF
import io
from PIL import Image
import base64
from io import BytesIO
# Initialisation de la base de données
init_db()

# Variable de session pour suivre le dernier traitement
if 'last_processed' not in st.session_state:
    st.session_state.last_processed = None

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Ventes",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Thème clair/sombre
def set_theme():
    if "theme" not in st.session_state:
        st.session_state.theme = "light"

    with st.sidebar:
        st.write("## Paramètres d'affichage")
        if st.button("Changer de thème"):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()


# Authentification
def login():
    st.sidebar.subheader("Connexion Admin")
    user = st.sidebar.text_input("Nom d'utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")
    if st.sidebar.button("Se connecter"):
        if user == "admin" and password == "admin123":
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.sidebar.error("Identifiants invalides")


# --- Tableau de bord ---
def show_dashboard():
    st.header("Tableau de bord avancé des ventes")

    try:
        df_ventes = get_ventes()

        # Conversion et nettoyage des dates
        df_ventes['date_vente'] = pd.to_datetime(df_ventes['date_vente'], errors='coerce')
        df_ventes = df_ventes.dropna(subset=['date_vente'])

        if df_ventes.empty:
            st.warning("Aucune donnée de vente valide disponible")
            return

        # Détermination des dates min/max
        min_date = df_ventes['date_vente'].min().to_pydatetime()
        max_date = df_ventes['date_vente'].max().to_pydatetime()

        # Filtres
        with st.expander("🔍 Filtres", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                date_debut = st.date_input("Date début", min_date)
            with col2:
                date_fin = st.date_input("Date fin", max_date)
            with col3:
                categories = st.multiselect("Catégories", df_ventes['categorie'].unique())
            with col4:
                period = st.selectbox("Période d'analyse", ["Journalier", "Mensuel", "Trimestriel", "Annuel"])

        # Application des filtres
        mask = (
                (df_ventes['date_vente'].dt.date >= date_debut) &
                (df_ventes['date_vente'].dt.date <= date_fin)
        )
        filtered_df = df_ventes[mask]

        if categories:
            filtered_df = filtered_df[filtered_df['categorie'].isin(categories)]

        # KPI
        st.subheader("Indicateurs clés")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total = filtered_df['montant'].sum()
            st.metric("Total ventes", f"{total:,.2f}CFA")
        with col2:
            count = len(filtered_df)
            st.metric("Nombre de ventes", count)
        with col3:
            avg = filtered_df['montant'].mean() if not filtered_df.empty else 0
            st.metric("Panier moyen", f"{avg:,.2f}CFA")
        with col4:
            top_product = filtered_df.groupby('produit')['quantite'].sum().idxmax() if not filtered_df.empty else "N/A"
            st.metric("Produit phare", top_product)

        # Graphiques
        st.subheader("Analyse des ventes")
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Évolution", "Répartition", "Performance Produits", "Détails", "Exporter"])

        with tab1:  # Évolution
            if not filtered_df.empty:
                # Déterminer la fréquence en fonction de la période sélectionnée
                freq_map = {
                    "Journalier": 'D',
                    "Mensuel": 'M',
                    "Trimestriel": 'Q',
                    "Annuel": 'Y'
                }
                freq = freq_map.get(period, 'M')  # Par défaut mensuel

                period_sales = filtered_df.groupby(pd.Grouper(key='date_vente', freq=freq)).agg({
                    'montant': 'sum',
                    'quantite': 'sum'
                }).reset_index()

                fig = px.line(
                    period_sales,
                    x='date_vente',
                    y='montant',
                    title=f'Évolution des ventes ({period.lower()})',
                    labels={'date_vente': 'Date', 'montant': 'Montant (CFA)'},
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)

                # Ajout d'une courbe de tendance
                if len(period_sales) > 1:
                    fig.add_scatter(
                        x=period_sales['date_vente'],
                        y=np.polyval(np.polyfit(
                            range(len(period_sales)),
                            period_sales['montant'],
                            1
                        ), range(len(period_sales))),
                        mode='lines',
                        name='Tendance',
                        line=dict(color='red', dash='dash')
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Aucune donnée à afficher pour la période sélectionnée")

        with tab2:  # Répartition
            if not filtered_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.pie(
                        filtered_df.groupby('categorie')['montant'].sum().reset_index(),
                        names='categorie',
                        values='montant',
                        title='Répartition par catégorie',
                        hole=0.3
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig = px.bar(
                        filtered_df.groupby('categorie')['quantite'].sum().reset_index(),
                        x='categorie',
                        y='quantite',
                        title='Quantité vendue par catégorie',
                        color='categorie'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Aucune donnée à afficher pour la période sélectionnée")

        with tab3:  # Performance Produits
            if not filtered_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    top_produits = filtered_df.groupby('produit')['quantite'].sum().nlargest(5).reset_index()
                    fig = px.bar(
                        top_produits,
                        x='produit',
                        y='quantite',
                        title='Top 5 produits (quantité)',
                        color='produit',
                        text_auto=True
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    bottom_produits = filtered_df.groupby('produit')['quantite'].sum().nsmallest(5).reset_index()
                    fig = px.bar(
                        bottom_produits,
                        x='produit',
                        y='quantite',
                        title='Bottom 5 produits (quantité)',
                        color='produit',
                        text_auto=True
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Analyse de l'évolution des produits
                st.subheader("Évolution des produits")
                selected_products = st.multiselect(
                    "Sélectionnez les produits à comparer",
                    options=filtered_df['produit'].unique(),
                    default=top_produits['produit'].head(3).tolist()
                )

                if selected_products:
                    product_evolution = filtered_df[filtered_df['produit'].isin(selected_products)]
                    product_evolution = product_evolution.groupby(['date_vente', 'produit'])[
                        'quantite'].sum().unstack().fillna(0)

                    fig = px.line(
                        product_evolution.reset_index().melt(id_vars='date_vente'),
                        x='date_vente',
                        y='value',
                        color='produit',
                        title='Évolution comparative des produits',
                        labels={'value': 'Quantité vendue', 'date_vente': 'Date'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Aucune donnée à afficher pour la période sélectionnée")

        with tab4:  # Détails
            st.dataframe(
                filtered_df.sort_values('date_vente', ascending=False),
                column_config={
                    "date_vente": st.column_config.DateColumn("Date"),
                    "produit": "Produit",
                    "categorie": "Catégorie",
                    "quantite": "Quantité",
                    "montant": st.column_config.NumberColumn("Montant", format="%.2f CFA")
                },
                hide_index=True,
                use_container_width=True
            )

        with tab5:  # Exportation
            st.subheader("Exporter les données")

            # Export Excel
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, sheet_name='Ventes', index=False)

                # Ajout d'onglets supplémentaires avec des analyses
                summary_cat = filtered_df.groupby('categorie').agg({
                    'montant': ['sum', 'mean', 'count'],
                    'quantite': 'sum'
                })
                summary_cat.to_excel(writer, sheet_name='Par catégorie')

                summary_prod = filtered_df.groupby('produit').agg({
                    'montant': ['sum', 'mean'],
                    'quantite': 'sum'
                })
                summary_prod.to_excel(writer, sheet_name='Par produit')

            excel_buffer.seek(0)

            st.download_button(
                label="Télécharger Excel complet",
                data=excel_buffer,
                file_name=f"ventes_{date_debut}_{date_fin}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Contient les données brutes et des analyses par catégorie/produit"
            )

            # Export PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            # Titre
            pdf.cell(200, 10, txt=f"Rapport des ventes du {date_debut} au {date_fin}", ln=1, align='C')
            pdf.ln(10)

            # KPI
            pdf.set_font("Arial", 'B', size=11)
            pdf.cell(200, 10, txt="Indicateurs clés:", ln=1)
            pdf.set_font("Arial", size=10)
            pdf.cell(200, 10, txt=f"Total des ventes: {total:,.2f}CFA", ln=1)
            pdf.cell(200, 10, txt=f"Nombre de transactions: {count}", ln=1)
            pdf.cell(200, 10, txt=f"Panier moyen: {avg:,.2f}CFA", ln=1)
            pdf.cell(200, 10, txt=f"Produit le plus vendu: {top_product}", ln=1)
            pdf.ln(10)

            # Tableau des données
            pdf.set_font("Arial", 'B', size=10)
            cols = ["Date", "Produit", "Catégorie", "Quantité", "Montant (CFA)"]
            widths = [30, 50, 40, 25, 25]

            for col, width in zip(cols, widths):
                pdf.cell(width, 10, col, border=1)
            pdf.ln()

            pdf.set_font("Arial", size=8)
            for _, row in filtered_df.iterrows():
                pdf.cell(widths[0], 10, str(row['date_vente'].date()), border=1)
                pdf.cell(widths[1], 10, row['produit'], border=1)
                pdf.cell(widths[2], 10, row['categorie'], border=1)
                pdf.cell(widths[3], 10, str(row['quantite']), border=1)
                pdf.cell(widths[4], 10, f"{row['montant']:.2f}", border=1)
                pdf.ln()

            pdf_buffer = BytesIO()
            pdf.output(pdf_buffer)  # Écrit directement dans le buffer
            pdf_bytes = pdf_buffer.getvalue()

            st.download_button(
                label="Télécharger PDF",
                data=pdf_bytes,
                file_name="rapport.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")

def create_sales_pdf(filtered_df, period):
    """Crée un rapport PDF des analyses de ventes"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Titre
    pdf.cell(200, 10, txt=f"Rapport des Ventes ({period})", ln=1, align='C')
    pdf.ln(10)

    # KPI
    pdf.set_font("Arial", 'B', size=11)
    pdf.cell(200, 10, txt="Indicateurs Clés:", ln=1)
    pdf.set_font("Arial", size=10)

    total = filtered_df['montant'].sum()
    count = len(filtered_df)
    avg = filtered_df['montant'].mean() if not filtered_df.empty else 0

    pdf.cell(200, 10, txt=f"Total des ventes: {total:,.2f}CFA", ln=1)
    pdf.cell(200, 10, txt=f"Nombre de transactions: {count}", ln=1)
    pdf.cell(200, 10, txt=f"Panier moyen: {avg:,.2f}€", ln=1)
    pdf.ln(10)

    # Tableau des données
    pdf.set_font("Arial", 'B', size=9)
    cols = ["Date", "Produit", "Catégorie", "Quantité", "Montant"]
    widths = [30, 50, 40, 25, 25]

    for col, width in zip(cols, widths):
        pdf.cell(width, 10, col, border=1)
    pdf.ln()

    pdf.set_font("Arial", size=8)
    for _, row in filtered_df.iterrows():
        pdf.cell(widths[0], 10, str(row['date_vente'].date()), border=1)
        pdf.cell(widths[1], 10, row['produit'], border=1)
        pdf.cell(widths[2], 10, row['categorie'], border=1)
        pdf.cell(widths[3], 10, str(row['quantite']), border=1)
        pdf.cell(widths[4], 10, f"{row['montant']:.2f}CFA", border=1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin1', errors='replace')


def create_sales_excel(filtered_df, period):
    """Crée un fichier Excel des analyses de ventes"""
    output = io.BytesIO()

    # Création du fichier Excel avec plusieurs onglets
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Données brutes
        filtered_df.to_excel(writer, sheet_name='Ventes détaillées', index=False)

        # Synthèse par catégorie
        summary_cat = filtered_df.groupby('categorie').agg({
            'montant': ['sum', 'count'],
            'quantite': 'sum'
        })
        summary_cat.to_excel(writer, sheet_name='Par catégorie')

        # Synthèse par produit
        summary_prod = filtered_df.groupby('produit').agg({
            'montant': ['sum', 'mean'],
            'quantite': 'sum'
        })
        summary_prod.to_excel(writer, sheet_name='Par produit')

    output.seek(0)
    return output

# --- Gestion des ventes ---
def gestion_ventes():
    st.header("Gestion des Ventes")

    # Vérification du timestamp pour éviter les exécutions multiples
    current_time = datetime.now()

    try:
        # Onglets pour différentes opérations
        tab1, tab2, tab3 = st.tabs(["Voir les ventes", "Ajouter une vente", "Modifier/Supprimer"])

        with tab1:
            df_ventes = get_ventes()
            gb = GridOptionsBuilder.from_dataframe(df_ventes)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_side_bar()
            gb.configure_selection('single', use_checkbox=True)
            grid_options = gb.build()

            grid_response = AgGrid(
                df_ventes,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                theme='streamlit' if st.session_state.get("theme", "light") == "light" else 'dark',
                height=400,
                reload_data=True
            )

        with tab2:
            form_ajout = st.form(key='form_ajout_vente')
            with form_ajout:
                col1, col2 = st.columns(2)
                with col1:
                    date = st.date_input("Date de vente", value=datetime.now())
                    df_produits = get_produits()
                    # Conversion des IDs en int natif
                    produit_id_map = {row['nom']: int(row['id']) for _, row in df_produits.iterrows()}
                    produit = st.selectbox("Produit", list(produit_id_map.keys()))
                    produit_id = produit_id_map[produit]
                with col2:
                    df_clients = get_clients()
                    # Conversion des IDs en int natif
                    client_id_map = {row['nom']: int(row['id']) for _, row in df_clients.iterrows()}
                    client = st.selectbox("Client", list(client_id_map.keys()))
                    client_id = client_id_map[client]
                    quantite = st.number_input("Quantité", min_value=1, step=1, value=1)
                    montant = st.number_input("Montant", min_value=0.0, value=0.0)

                # Bouton de soumission correctement placé
                submit = form_ajout.form_submit_button("Ajouter la vente")
                if submit:
                    try:
                        insert_vente(date, produit_id, client_id, quantite, montant)
                        st.success("✅ Vente ajoutée avec succès !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de l'ajout: {str(e)}")

        with tab3:
            st.subheader("Modifier ou supprimer une vente")
            df_ventes = get_ventes()
            if len(df_ventes) == 0:
                st.warning("Aucune vente à afficher")
            else:
                # Conversion des IDs en int natif
                df_ventes['id'] = df_ventes['id'].astype(int)
                selected = st.selectbox(
                    "Sélectionner une vente à modifier",
                    df_ventes.apply(
                        lambda x: f"{x['date_vente']} - {x['produit']} - {x['client']} - {x['montant']}CFA",
                        axis=1
                    )
                )

                selected_id = int(df_ventes.iloc[
                                      df_ventes.apply(
                                          lambda
                                              x: f"{x['date_vente']} - {x['produit']} - {x['client']} - {x['montant']}CFA",
                                          axis=1
                                      ).tolist().index(selected)
                                  ]['id'])

                form_modif = st.form(key='form_modif_vente')
                with form_modif:
                    vente_data = df_ventes[df_ventes['id'] == selected_id].iloc[0]
                    col1, col2 = st.columns(2)
                    with col1:
                        new_date = st.date_input(
                            "Date",
                            value=datetime.strptime(str(vente_data['date_vente']), '%Y-%m-%d')
                        )
                        df_produits = get_produits()
                        # Conversion des IDs en int natif
                        produit_id_map = {row['nom']: int(row['id']) for _, row in df_produits.iterrows()}
                        current_produit = df_produits[df_produits['id'] == int(vente_data['produit_id'])]['nom'].values[
                            0]
                        new_produit = st.selectbox(
                            "Produit",
                            list(produit_id_map.keys()),
                            index=list(produit_id_map.keys()).index(current_produit)
                        )
                        new_produit_id = produit_id_map[new_produit]
                    with col2:
                        df_clients = get_clients()
                        # Conversion des IDs en int natif
                        client_id_map = {row['nom']: int(row['id']) for _, row in df_clients.iterrows()}
                        current_client = df_clients[df_clients['id'] == int(vente_data['client_id'])]['nom'].values[0]
                        new_client = st.selectbox(
                            "Client",
                            list(client_id_map.keys()),
                            index=list(client_id_map.keys()).index(current_client)
                        )
                        new_client_id = client_id_map[new_client]
                        new_quantite = st.number_input(
                            "Quantité",
                            min_value=1,
                            step=1,
                            value=int(vente_data['quantite'])
                        )
                        new_montant = st.number_input(
                            "Montant",
                            min_value=0.0,
                            value=float(vente_data['montant'])
                        )

                    col1, col2 = st.columns(2)
                    with col1:
                        if form_modif.form_submit_button("Modifier"):
                            try:
                                update_vente(selected_id, new_date, new_produit_id, new_client_id, new_quantite,
                                             new_montant)
                                st.success("✅ Vente modifiée avec succès !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur lors de la modification: {str(e)}")
                    with col2:
                        if form_modif.form_submit_button("Supprimer"):
                            try:
                                delete_vente(selected_id)
                                st.success("✅ Vente supprimée avec succès !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur lors de la suppression: {str(e)}")

    except Exception as e:
        st.error(f"Erreur dans la gestion des ventes: {str(e)}")

# --- Gestion des produits ---
def gestion_produits():
    st.header("Gestion des Produits")

    # Vérification du timestamp pour éviter les exécutions multiples
    current_time = datetime.now()

    try:
        tab1, tab2, tab3 = st.tabs(["Voir les produits", "Ajouter un produit", "Modifier/Supprimer"])

        with tab1:
            df_produits = get_produits()
            st.dataframe(df_produits, height=400)

        with tab2:
            with st.form("form_ajout_produit"):
                nom = st.text_input("Nom du produit")
                categorie = st.text_input("Catégorie")
                prix_unitaire = st.number_input("Prix unitaire", min_value=0.0)

                submit = st.form_submit_button("Ajouter le produit")
                if submit:
                    try:
                        insert_produit(nom, categorie, prix_unitaire)
                        st.success("✅ Produit ajouté avec succès !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de l'ajout: {str(e)}")

        with tab3:
            st.subheader("Modifier ou supprimer un produit")
            df_produits = get_produits()
            if len(df_produits) == 0:
                st.warning("Aucun produit à afficher")
            else:
                selected = st.selectbox("Sélectionner un produit à modifier", df_produits['nom'])

                selected_id = df_produits[df_produits['nom'] == selected]['id'].values[0]
                produit_data = df_produits[df_produits['id'] == selected_id].iloc[0]

                with st.form("form_modif_produit"):
                    new_nom = st.text_input("Nom", value=produit_data['nom'])
                    new_categorie = st.text_input("Catégorie", value=produit_data['categorie'])
                    new_prix = st.number_input(
                        "Prix unitaire",
                        min_value=0.0,
                        value=produit_data['prix_unitaire']
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Modifier"):
                            try:
                                update_produit(selected_id, new_nom, new_categorie, new_prix)
                                st.success("✅ Produit modifié avec succès !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur lors de la modification: {str(e)}")
                    with col2:
                        if st.form_submit_button("Supprimer"):
                            try:
                                delete_produit(selected_id)
                                st.success("✅ Produit supprimé avec succès !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur lors de la suppression: {str(e)}")

    except Exception as e:
        st.error(f"Erreur dans la gestion des produits: {str(e)}")


# --- Gestion des clients ---
def gestion_clients():
    st.header("Gestion des Clients")

    try:
        tab1, tab2, tab3 = st.tabs(["Voir les clients", "Ajouter un client", "Modifier/Supprimer"])

        with tab1:
            df_clients = get_clients()
            st.dataframe(df_clients, height=400)

        with tab2:
            with st.form("form_ajout_client"):
                nom = st.text_input("Nom complet")
                email = st.text_input("Email")
                ville = st.text_input("Ville")

                submit = st.form_submit_button("Ajouter le client")
                if submit:
                    try:
                        insert_client(nom, email, ville)
                        st.success("✅ Client ajouté avec succès !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de l'ajout: {str(e)}")

        with tab3:
            st.subheader("Modifier ou supprimer un client")
            df_clients = get_clients()
            if len(df_clients) == 0:
                st.warning("Aucun client à afficher")
            else:
                selected = st.selectbox("Sélectionner un client à modifier", df_clients['nom'])

                selected_id = df_clients[df_clients['nom'] == selected]['id'].values[0]
                client_data = df_clients[df_clients['id'] == selected_id].iloc[0]

                with st.form("form_modif_client"):
                    new_nom = st.text_input("Nom", value=client_data['nom'])
                    new_email = st.text_input("Email", value=client_data['email'])
                    new_ville = st.text_input("Ville", value=client_data['ville'])

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Modifier"):
                            try:
                                update_client(selected_id, new_nom, new_email, new_ville)
                                st.success("✅ Client modifié avec succès !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur lors de la modification: {str(e)}")
                    with col2:
                        if st.form_submit_button("Supprimer"):
                            try:
                                delete_client(selected_id)
                                st.success("✅ Client supprimé avec succès !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur lors de la suppression: {str(e)}")

    except Exception as e:
        st.error(f"Erreur dans la gestion des clients: {str(e)}")

# --- Prévisions ---
def show_forecasts():
    st.header("Prévisions des ventes")
    df_ventes = get_ventes()

    if len(df_ventes) < 30:
        st.warning("Pas assez de données historiques pour faire des prévisions (minimum 30 jours)")
        return

    with st.spinner("Calcul des prévisions..."):
        forecast, mae = forecast_sales(df_ventes)

    if forecast is not None:
        st.success(f"Prévisions calculées (MAE: {mae:.2f})")

        fig = px.line(
            forecast,
            x='date_vente',
            y='prediction',
            title='Prévisions des ventes pour les 6 prochains jours'
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(forecast)
    else:
        st.error("Erreur lors du calcul des prévisions")


def main():
    set_theme()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login()
        return

    st.title("Dashboard Analyse des Ventes")

    # Menu principal
    menu = ["Tableau de bord", "Gestion des Ventes", "Gestion des Produits", "Gestion des Clients", "Prévisions"]
    choice = st.sidebar.selectbox("Navigation", menu)

    if choice == "Tableau de bord":
        show_dashboard()
    elif choice == "Gestion des Ventes":
        gestion_ventes()
    elif choice == "Gestion des Produits":
        gestion_produits()
    elif choice == "Gestion des Clients":
        gestion_clients()
    elif choice == "Prévisions":
        show_forecasts()


if __name__ == "__main__":
    main()