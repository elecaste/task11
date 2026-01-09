import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configurazione Pagina
st.set_page_config(page_title="Mappa CO2", layout="wide")

# 2. Caricamento Dati
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
    df = pd.read_csv(url)
    # Pulizia dati
    df = df[['iso_code', 'country', 'year', 'co2_per_capita']]
    df = df[df['iso_code'].notna()]
    return df

df = load_data()

# 3. Interfaccia Utente
st.title("🌍 Mappa Interattiva Emissioni CO₂")
st.markdown("Visualizzazione dei dati globali *Our World in Data*.")

# Slider Anno
min_year = int(df['year'].min())
max_year = int(df['year'].max())
year = st.slider("Seleziona Anno:", min_year, max_year, 2022)

# Filtro dati
df_year = df[df['year'] == year]

# 4. Grafico
if not df_year.empty:
    fig = px.choropleth(
        df_year,
        locations="iso_code",
        color="co2_per_capita",
        hover_name="country",
        color_continuous_scale="Plasma",
        range_color=(0, 20),
        labels={'co2_per_capita': 'Tonnellate/Persona'},
        title=f"Emissioni Pro Capite ({year})"
    )
    fig.update_geos(showframe=False, projection_type="natural earth")
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=600)
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Nessun dato disponibile per questo anno.")
