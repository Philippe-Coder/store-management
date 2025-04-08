import pandas as pd
from datetime import timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error


def forecast_sales(df_ventes, periods=6):
    try:
        # Préparation des données
        df = df_ventes.copy()
        df['date_vente'] = pd.to_datetime(df['date_vente'])
        df = df.set_index('date_vente').resample('D').sum(numeric_only=True).reset_index()
        df['jour'] = df['date_vente'].dt.day
        df['mois'] = df['date_vente'].dt.month
        df['annee'] = df['date_vente'].dt.year
        df['jour_semaine'] = df['date_vente'].dt.dayofweek

        # Entraînement du modèle
        X = df[['jour', 'mois', 'annee', 'jour_semaine']]
        y = df['montant']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Prédiction
        last_date = df['date_vente'].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, periods + 1)]
        future_df = pd.DataFrame({
            'date_vente': future_dates,
            'jour': [d.day for d in future_dates],
            'mois': [d.month for d in future_dates],
            'annee': [d.year for d in future_dates],
            'jour_semaine': [d.weekday() for d in future_dates]
        })
        future_df['prediction'] = model.predict(future_df[['jour', 'mois', 'annee', 'jour_semaine']])

        mae = mean_absolute_error(y_test, model.predict(X_test))
        return future_df[['date_vente', 'prediction']], mae
    except Exception as e:
        return None, str(e)