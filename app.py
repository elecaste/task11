import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Global CO2 Analysis",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CARICAMENTO DATI ---
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
    df = pd.read_csv(url)
    
    # Selezioniamo colonne utili
    keep_cols = ['country', 'year', 'iso_code', 'population', 'gdp', 'co2_per_capita', 'co2']
    df = df[keep_cols]
    
    # Pulizia
    df = df[df['iso_code'].notna()]
    df = df.dropna(subset=['co2_per_capita'])
    
    return df

df = load_data()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("📊 Control Panel")
    
    # Filtro Anno
    st.subheader("1. Time Dimension")
    min_year = 1950
    max_year = int(df['year'].max())
    
    selected_year = st.slider(
        "Select Year:",
        min_value=min_year,
        max_value=max_year,
        value=2022
    )
    
    st.markdown("---")

    # Filtro Paesi
    st.subheader("2. Comparative Analysis")
    all_countries = sorted(df['country'].unique())
    default_countries = ["United States", "China", "United Kingdom", "Italy", "India"]
    # Verifica che i default esistano
    valid_defaults = [c for c in default_countries if c in all_countries]
    
    selected_countries = st.multiselect(
        "Select countries for Trend Chart:",
        all_countries,
        default=valid_defaults
    )
    
    st.markdown("---")
    
    # Informazioni
    st.info("ℹ️ **About**")
    st.markdown("""
    **Data Source:** [Our World in Data](https://ourworldindata.org/co2-and-greenhouse-gas-emissions)
    
    **Student Project:** Eleonora Castellani  
    *USI Master in Finance (Minor in Digital)*
    """)

# --- 4. PAGINA PRINCIPALE ---
st.title("Global CO2 emissions and analysis")
st.markdown(f"### Analysis for year **{selected_year}**")

df_year = df[df['year'] == selected_year]

if not df_year.empty:
    
    # KPI
    col1, col2, col3, col4 = st.columns(4)
    global_avg = df_year['co2_per_capita'].mean()
    max_emitter = df_year.loc[df_year['co2_per_capita'].idxmax()] if not df_year.empty else None
    
    with col1:
        st.metric("📅 Selected Year", selected_year)
    with col2:
        st.metric("🌍 Global Avg (Per Capita)", f"{global_avg:.2f} t")
    with col3:
        st.markdown("**🏭 Top 5 Ranking**")
        # Creiamo una mini tabella pulita per la visualizzazione
        top5_display = top_5_emitters[['country', 'co2_per_capita']].copy()
        top5_display.columns = ['Country', 'Tons']
        # Resettiamo l'indice per farlo partire da 1
        top5_display.reset_index(drop=True, inplace=True)
        top5_display.index += 1
        
        # Mostriamo la tabella senza indici fastidiosi
        st.dataframe(top5_display, height=180, use_container_width=True)
    with col4:
        st.metric("👥 Tracked Population", f"{df_year['population'].sum()/1e9:.2f} B")

    st.markdown("---")

    # --- TAB SYSTEM ---
    tab1, tab2, tab3 = st.tabs(["🗺️ Global Map", "📈 Historical Trends", "💰 GDP vs CO₂ (Finance Insight)"])

    # TAB 1: MAPPA
    with tab1:
        fig_map = px.choropleth(
            df_year,
            locations="iso_code",
            color="co2_per_capita",
            hover_name="country",
            hover_data={'iso_code': False, 'population': ':,.0f', 'gdp': ':,.0f'},
            color_continuous_scale="RdYlBu_r",
            range_color=(0, 20),
            title=f"<b>Global CO₂ Intensity ({selected_year})</b>",
        )
        fig_map.update_geos(showframe=False, projection_type="natural earth", showocean=True, oceancolor="#f0f8ff")
        fig_map.update_layout(height=600, margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)

    # TAB 2: LINE CHART
    with tab2:
        st.subheader("Historical Evolution")
        df_trend = df[df['country'].isin(selected_countries)]
        
        if not df_trend.empty:
            fig_line = px.line(
                df_trend,
                x="year",
                y="co2_per_capita",
                color="country",
                title="<b>Emission Trajectories (1950-2022)</b>",
                markers=False
            )
            fig_line.add_vline(x=selected_year, line_dash="dash", line_color="red", opacity=0.5)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("Select countries in the sidebar to visualize trends.")

    # TAB 3: SCATTER PLOT (VERSIONE STABILE CORRETTA)
    with tab3:
        st.subheader("Economic Growth vs. Environmental Impact")
        st.markdown("""
        *Does being richer mean polluting more?* This chart correlates **GDP per Capita** (Wealth) with **CO₂ Emissions**.
        The size of each bubble represents the country's population.
        """)
        
        # Calcolo GDP e pulizia
        df_year_fin = df_year.copy()
        df_year_fin['gdp_per_capita'] = df_year_fin['gdp'] / df_year_fin['population']
        df_year_fin = df_year_fin.dropna(subset=['gdp_per_capita', 'co2_per_capita', 'population'])

        if not df_year_fin.empty:
            fig_scatter = px.scatter(
                df_year_fin,
                x="gdp_per_capita",
                y="co2_per_capita",
                size="population",      
                color="country",        
                hover_name="country",
                log_x=True,             
                title=f"<b>Correlation: GDP per Capita vs CO₂ ({selected_year})</b>",
                labels={'gdp_per_capita': 'GDP per Capita ($)', 'co2_per_capita': 'CO₂ per Capita (t)'},
                size_max=60  # Dimensione massima corretta
            )
            
            # Impostiamo dimensione minima per non perdere i paesi piccoli
            fig_scatter.update_traces(marker=dict(sizemin=5))

            fig_scatter.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.caption("Note: X-axis is logarithmic. Bubble size represents population.")
        else:
            st.warning(f"Not enough economic data available for the year {selected_year}.")

else:
    st.error("No data available. Please adjust filters.")
