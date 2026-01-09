import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAZIONE PAGINA (Titolo e Layout Wide)
st.set_page_config(
    page_title="Dashboard CO₂ Globale",
    page_icon="🌍",
    layout="wide"
)

# 2. CARICAMENTO E PULIZIA DATI
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
    df = pd.read_csv(url)
    # Prendiamo più colonne per rendere il tooltip più interessante
    cols = ['iso_code', 'country', 'year', 'co2_per_capita', 'population', 'gdp']
    df = df[cols]
    df = df[df['iso_code'].notna()] # Rimuove continenti e aggregati
    return df

df = load_data()

# 3. SIDEBAR (Barra Laterale per i Controlli)
with st.sidebar:
    st.title("⚙️ Filtri")
    
    # Slider Anno
    min_year = int(df['year'].min())
    max_year = int(df['year'].max())
    
    selected_year = st.slider(
        "Seleziona Anno",
        min_year, max_year, 2022
    )
    
    st.markdown("---")
    st.markdown("""
    **Informazioni:**
    Questa dashboard mostra le emissioni di CO₂ pro capite (tonnellate per persona).
    
    *Fonte dati: Our World in Data*
    """)

# Filtriamo i dati
df_year = df[df['year'] == selected_year]

# 4. INTERFACCIA PRINCIPALE
st.title(f"🌍 Emissioni di CO₂ nel {selected_year}")

# --- SEZIONE KPI (Indicatori Chiave in alto) ---
if not df_year.empty:
    # Calcoli per le statistiche
    max_emitter = df_year.loc[df_year['co2_per_capita'].idxmax()]
    avg_co2 = df_year['co2_per_capita'].mean()
    
    # Creiamo 3 colonne per i numeri
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🌍 Media Globale (Tons/Persona)",
            value=f"{avg_co2:.2f}"
        )
    
    with col2:
        st.metric(
            label="🏭 Paese più inquinante (Pro Capite)",
            value=max_emitter['country'],
            delta=f"{max_emitter['co2_per_capita']:.1f} Tons"
        )
        
    with col3:
        st.metric(
            label="👥 Popolazione Mondiale Monitorata",
            value=f"{df_year['population'].sum() / 1e9:.2f} Miliardi"
        )

    st.markdown("---") # Linea separatrice

    # --- MAPPA INTERATTIVA AVANZATA ---
    fig = px.choropleth(
        df_year,
        locations="iso_code",
        color="co2_per_capita",
        hover_name="country",
        # Aggiungiamo dati extra al passaggio del mouse
        hover_data={
            'iso_code': False,
            'population': ':,.0f', # Formattazione numeri
            'gdp': ':,.0f'
        },
        # Cambiamo scala colori: 'Reds', 'Spectral_r', 'Plasma'
        color_continuous_scale="YlOrRd", 
        range_color=(0, 20),
        title="Mappa Globale Emissioni",
        labels={'co2_per_capita': 'Tons CO₂/capita'}
    )

    # Miglioramenti grafici della mappa
    fig.update_geos(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="Gray",
        projection_type="natural earth",
        showocean=True,
        oceancolor="#eefaff", # Colore azzurrino per l'oceano
        showlakes=True,
        lakecolor="#eefaff"
    )
    
    fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        height=600,
        # Legenda orizzontale in basso
        coloraxis_colorbar=dict(
            title="Tonnellate/Persona",
            orientation="h",
            y=-0.1
        )
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Nessun dato disponibile per l'anno selezionato.")
