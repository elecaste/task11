import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURAZIONE PAGINA (Layout Wide & Icona) ---
st.set_page_config(
    page_title="CO₂ Emissions Portfolio",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CARICAMENTO DATI OTTIMIZZATO ---
@st.cache_data
def load_data():
    # Dataset ufficiale OWID
    url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
    df = pd.read_csv(url)
    
    # Selezioniamo solo le colonne utili (incluso il 'continent' se presente, altrimenti lo simuliamo o usiamo iso_code)
    # OWID dataset ha colonne specifiche. Filtriamo per avere dataset pulito.
    keep_cols = ['country', 'year', 'iso_code', 'population', 'gdp', 'co2_per_capita', 'co2']
    df = df[keep_cols]
    
    # Pulizia: Rimuoviamo righe che non sono paesi (es. 'World', 'High-income countries')
    # I paesi veri hanno un ISO code.
    df = df[df['iso_code'].notna()]
    
    # Aggiungiamo una colonna Continente mappando i codici (o usiamo i dati raw se disponibili)
    # Per semplicità in questo esame, usiamo un dizionario base o lasciamo i dati raw. 
    # Nota: OWID ha già raggruppamenti, ma qui teniamo i paesi.
    return df

df = load_data()

# --- 3. SIDEBAR: FILTRI AVANZATI E TESTI ---
with st.sidebar:
    st.title("📊 Control Panel")
    
    # A. FILTRO ANNO
    st.subheader("1. Time Dimension")
    min_year = 1850 # Partiamo dal 1850 per mostrare meglio l'era industriale
    max_year = int(df['year'].max())
    
    selected_year = st.slider(
        "Select Year:",
        min_value=min_year,
        max_value=max_year,
        value=2022,
        help="Drag to see how emissions evolved over time."
    )
    
    st.markdown("---")

    # B. FILTRO PAESI (NUOVO!)
    st.subheader("2. Focus Area")
    # Creiamo una lista di paesi per permettere il confronto
    all_countries = sorted(df['country'].unique())
    selected_countries = st.multiselect(
        "Compare specific countries (Trend Chart):",
        all_countries,
        default=["United States", "China", "United Kingdom", "Italy", "India"]
    )
    
    st.markdown("---")
    
    # C. INFORMAZIONI DI LETTURA (RICHIESTA UTENTE)
    st.info("ℹ️ **How to read this dashboard**")
    st.markdown("""
    **The Metric:**
    We visualize **CO₂ per capita** (tonnes).
    * **High (Red/Dark):** The average person in this country has a high carbon footprint.
    * **Low (Yellow/Light):** Lower emissions per person.
    
    **Why is data missing before 1900?**
    In the 1800s, the **Industrial Revolution** was limited to a few nations (mostly UK & Europe). 
    Most of the world relied on biomass (wood) for energy, which was not recorded in historical fossil fuel datasets. 
    Additionally, modern statistical agencies did not exist globally.
    
    **Source:** [Our World in Data](https://github.com/owid/co2-data)
    """)
    st.caption("Student Project - Data Visualization Exam")

# --- 4. PAGINA PRINCIPALE ---
st.title("🌍 Global CO₂ Analysis: An Interactive Portfolio")
st.markdown(f"### Snapshot of the year **{selected_year}**")

# Filtro i dati per l'anno scelto
df_year = df[df['year'] == selected_year]

if not df_year.empty:
    
    # --- A. KPI CARDS (Indicatori Chiave) ---
    # Calcoliamo i KPI dinamici
    global_avg = df_year['co2_per_capita'].mean()
    max_country = df_year.loc[df_year['co2_per_capita'].idxmax()]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 Selected Year", selected_year)
    with col2:
        st.metric("🌍 Global Avg (Per Capita)", f"{global_avg:.2f} t")
    with col3:
        st.metric("🏭 Highest Emitter", max_country['country'], f"{max_country['co2_per_capita']:.1f} t")
    with col4:
        st.metric("📉 Lowest Emitter (Non-Zero)", 
                  df_year[df_year['co2_per_capita']>0].nsmallest(1, 'co2_per_capita')['country'].iloc[0],
                  f"{df_year[df_year['co2_per_capita']>0]['co2_per_capita'].min():.3f} t")

    # --- B. MAPPA INTERATTIVA (Choropleth) ---
    fig_map = px.choropleth(
        df_year,
        locations="iso_code",
        color="co2_per_capita",
        hover_name="country",
        hover_data={'iso_code': False, 'population': ':,.0f', 'gdp': ':,.0f'},
        color_continuous_scale="RdYlBu_r", # Scala Rosso-Giallo-Blu invertita (Rosso = Male)
        range_color=(0, 20),
        title=f"<b>Global Distribution of CO₂ Emissions ({selected_year})</b>",
        labels={'co2_per_capita': 'Tons/Person'}
    )
    
    fig_map.update_geos(
        showframe=False, showcoastlines=True, projection_type="natural earth",
        showocean=True, oceancolor="#f0f8ff", # Oceano leggero
        showlakes=True, lakecolor="#f0f8ff"
    )
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=550)
    
    st.plotly_chart(fig_map, use_container_width=True)

    # --- C. GRAFICO DI TENDENZA (TREND CHART) - IL "WOW" FACTOR ---
    st.markdown("---")
    st.subheader("📈 Historical Trend Analysis")
    st.markdown("While the map shows a snapshot, this chart shows **how emissions evolved over the last century** for the selected countries.")
    
    # Filtriamo il dataset COMPLETO (tutti gli anni) per i paesi selezionati nella sidebar
    df_trend = df[df['country'].isin(selected_countries)]
    
    if not df_trend.empty:
        fig_line = px.line(
            df_trend,
            x="year",
            y="co2_per_capita",
            color="country",
            title="<b>Evolution of CO₂ Emissions per Capita (1850-2022)</b>",
            labels={'co2_per_capita': 'CO₂ (Tonnes/Person)', 'year': 'Year'},
            markers=False
        )
        
        # Evidenziamo l'anno selezionato con una linea verticale
        fig_line.add_vline(x=selected_year, line_width=1, line_dash="dash", line_color="red")
        fig_line.add_annotation(x=selected_year, y=20, text="Selected Year", showarrow=False, yshift=10)
        
        fig_line.update_layout(
            hovermode="x unified", # Tooltip unificato (molto professionale)
            height=500,
            xaxis=dict(range=[1850, 2024]) # Fissiamo l'asse X per stabilità
        )
        
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("Please select at least one country in the sidebar to see the trend.")

else:
    st.error("Data not available. Please try reloading.")
