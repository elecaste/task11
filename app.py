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

# --- 2. CARICAMENTO DATI (FIX AVANZATO) ---
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
    df = pd.read_csv(url)
    
    # Selezioniamo colonne utili
    keep_cols = ['country', 'year', 'iso_code', 'population', 'gdp', 'co2_per_capita', 'co2']
    df = df[keep_cols]
    
    # Pulizia base
    df = df[df['iso_code'].notna()]
    
    # --- FIX CRITICO PER GDP MANCANTE (2023/2024) ---
    # Ordiniamo per paese e anno
    df = df.sort_values(['country', 'year'])
    
    # "Forward Fill": Se manca il GDP nel 2024, copiamo quello del 2023.
    # Questo permette al grafico a bolle di funzionare anche per gli anni recenti.
    df['gdp'] = df.groupby('country')['gdp'].ffill()
    df['population'] = df.groupby('country')['population'].ffill()
    
    # Rimuoviamo righe solo se manca la CO2 (il dato fondamentale)
    df = df.dropna(subset=['co2_per_capita'])
    
    # Filtro Micro-stati (popolazione > 1 milione) per pulire la mappa
    df = df[df['population'] > 1000000]
    
    return df

# --- QUESTA È LA RIGA CHE MANCAVA E CAUSAVA L'ERRORE ---
df = load_data()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("📊 Control Panel")
    
    # A. Filtro Anno
    st.subheader("1. Time Dimension")
    min_year = 1950
    # Ora df è definito, quindi questa riga funzionerà!
    max_year = int(df['year'].max())
    
    selected_year = st.slider(
        "Select Year:",
        min_value=min_year,
        max_value=max_year,
        value=2022
    )
    
    st.markdown("---")

    # B. Ricerca e Zoom
    st.subheader("🔍 Find a Country")
    all_countries = sorted(df['country'].unique())
    search_list = ["All Countries (Global View)"] + all_countries
    
    country_zoom = st.selectbox(
        "Search and Zoom to:",
        search_list,
        help="Select a country to highlight it. Micro-states (<1M pop) are excluded."
    )

    st.markdown("---")

    # C. Filtro Paesi per Grafico Trends
    st.subheader("2. Comparative Analysis")
    default_countries = ["United States", "China", "United Kingdom", "Italy", "India"]
    valid_defaults = [c for c in default_countries if c in all_countries]
    
    selected_countries = st.multiselect(
        "Select countries for Trend Chart:",
        all_countries,
        default=valid_defaults
    )
    
    st.markdown("---")
    
    # D. Informazioni
    st.info("ℹ️ **About**")
    st.markdown("""
    **Data Source:** [Our World in Data](https://ourworldindata.org/co2-and-greenhouse-gas-emissions)
    
    **Methodology:**
    Top Emitter is calculated as:
    $CO_2 \ Per \ Capita = \\frac{Total \ Emissions}{Population}$
    
    **Student Project:** Eleonora Castellani  
    *USI Master in Finance (Minor in Digital)*
    """)

# --- 4. PAGINA PRINCIPALE ---
st.title("Global CO2 emissions and analysis")
st.markdown(f"### Analysis for year **{selected_year}**")

df_year = df[df['year'] == selected_year]

if not df_year.empty:
    
    # --- KPI SECTION ---
    col1, col2, col3, col4 = st.columns(4)
    
    global_avg = df_year['co2_per_capita'].mean()
    top_5_emitters = df_year.sort_values(by="co2_per_capita", ascending=False).head(5)
    
    # Recuperiamo il PRIMO in classifica per l'analisi dettagliata
    top_country_row = top_5_emitters.iloc[0]
    top_country_name = top_country_row['country']
    
    with col1:
        st.metric("📅 Selected Year", selected_year)
        
    with col2:
        st.metric("🌍 Global Avg", f"{global_avg:.2f} t")
        
    with col3:
        st.markdown("**🏭 Top 5 Polluters (Per Capita)**")
        top5_display = top_5_emitters[['country', 'co2_per_capita']].copy()
        top5_display.columns = ['Country', 'Tons']
        top5_display.reset_index(drop=True, inplace=True)
        top5_display.index += 1
        st.dataframe(top5_display, height=180, use_container_width=True)
            
    with col4:
        st.metric("👥 Tracked Population", f"{df_year['population'].sum()/1e9:.2f} B")

    st.markdown("---")

    # --- TAB SYSTEM ---
    tab1, tab2, tab3 = st.tabs(["🗺️ Global Map & Analysis", "📈 Historical Trends", "💰 GDP vs CO₂ (Finance Insight)"])

    # TAB 1: MAPPA + SPIEGAZIONE PERSONALIZZATA
    with tab1:
        # 1. MAPPA
        fig_map = px.choropleth(
            df_year,
            locations="iso_code",
            color="co2_per_capita",
            hover_name="country",
            hover_data={'iso_code': False, 'population': ':,.0f', 'gdp': ':,.0f'},
            color_continuous_scale="YlOrRd", 
            range_color=(0, 40), 
            title=f"<b>Global CO₂ Intensity ({selected_year})</b>",
        )
        
        # Zoom Logic
        if country_zoom != "All Countries (Global View)":
            country_iso_series = df_year[df_year['country'] == country_zoom]['iso_code']
            if not country_iso_series.empty:
                selected_data = df_year[df_year['country'] == country_zoom]
                fig_map.add_trace(
                    px.choropleth(
                        selected_data, 
                        locations="iso_code", 
                        color_discrete_sequence=["rgba(0,0,0,0)"] 
                    ).update_traces(marker_line_color="Cyan", marker_line_width=4).data[0]
                )
                fig_map.update_layout(title_text=f"<b>Global View - Highlighted: {country_zoom}</b>")

        fig_map.update_geos(showframe=False, projection_type="natural earth", showocean=True, oceancolor="#f0f8ff")
        fig_map.update_layout(height=550, margin={"r":0,"t":40,"l":0,"b":0})
        fig_map.update_coloraxes(colorbar_title="Tons/Person")
        
        st.plotly_chart(fig_map, use_container_width=True)
        
        # 2. SEZIONE SPIEGAZIONE PERSONALIZZATA
        st.markdown("---")
        st.subheader(f"🔍 Deep Dive: Why is {top_country_name} ranked #1?")
        
        # Dati per la formula
        total_co2_val = top_country_row['co2'] 
        pop_val = top_country_row['population']
        per_capita_val = top_country_row['co2_per_capita']

        # Dizionario Insight
        custom_insights = {
            "Qatar": {
                "icon": "⚡",
                "title": "The LNG Superpower",
                "text": """
                **Specific Driver:** Qatar is the world's leading exporter of **Liquefied Natural Gas (LNG)**. The process of cooling gas to -162°C for export is incredibly energy-intensive.
                
                **Lifestyle Factor:** Extremely subsidized electricity and water lead to some of the highest domestic consumption rates in the world (air conditioning and water desalination).
                """
            },
            "United Arab Emirates": {
                "icon": "🏗️",
                "title": "Construction, Water & Aviation",
                "text": """
                **Specific Driver:** Unlike others, the UAE's emissions are driven heavily by rapid **urban construction** (Dubai/Abu Dhabi) and huge aluminum smelting industries.
                
                **Water Stress:** The UAE relies almost entirely on **desalination plants** (turning seawater into drinking water), which is one of the most carbon-heavy processes in existence.
                """
            },
            "Kuwait": {
                "icon": "🛢️",
                "title": "Oil-Fired Power Generation",
                "text": """
                **Specific Driver:** Kuwait has one of the oldest oil infrastructures in the region. Unlike modern economies shifting to gas, Kuwait still burns a significant amount of **heavy crude oil** directly to generate electricity.
                
                **Climate Control:** With summer temperatures exceeding 50°C, the energy demand for cooling per square meter is the highest on Earth.
                """
            },
            "Bahrain": {
                "icon": "🏭",
                "title": "Aluminum Smelting Giant",
                "text": """
                **Specific Driver:** Bahrain is home to **Alba**, one of the largest aluminum smelters in the world. Aluminum production is effectively "solid electricity" because it requires massive amounts of power.
                
                **Impact:** This single industry accounts for a huge percentage of the small island's national footprint.
                """
            },
            "Luxembourg": {
                "icon": "⛽",
                "title": "The 'Fuel Tourism' Paradox",
                "text": """
                **Specific Driver:** Luxembourg often ranks #1 in Europe not just because of its steel industry, but due to **Fuel Tourism**.
                
                **The Data Anomaly:** Truckers and commuters from France/Germany drive into Luxembourg to fill up on cheaper diesel. The emissions are counted against Luxembourg, but the fuel is burned elsewhere.
                """
            },
            "United States": {
                "icon": "🚗",
                "title": "The Age of Suburban Sprawl",
                "text": """
                **Specific Driver:** In the mid-20th century (1950s-70s), the USA developed a car-centric infrastructure. 
                
                **Lifestyle:** Large suburban homes (high heating/cooling needs) and low fuel taxes created a culture of high individual consumption compared to denser European cities.
                """
            }
        }

        if top_country_name in custom_insights:
            insight = custom_insights[top_country_name]
            final_icon = insight["icon"]
            final_title = insight["title"]
            final_text = insight["text"]
        else:
            final_icon = "📊"
            final_title = "High Industrial Output / Small Population"
            final_text = f"""
            **The Reason:** {top_country_name} combines significant industrial or mining activity with a relatively small population base ({pop_val:,.0f} people). 
            
            **Statistical Effect:** When a country has a small denominator (population), even moderate industrial emissions result in a very high per-capita ranking.
            """

        with st.expander(f"📖 Read Analysis for {top_country_name}", expanded=True):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.markdown(f"### {final_icon} {final_title}")
                st.markdown(final_text)
            with col_b:
                st.markdown("#### 🧮 The Evidence (Math)")
                st.markdown(f"""
                How we get **{per_capita_val:.1f} tons**:
                
                $$
                \\frac{{{total_co2_val:,.0f} \\text{{ Total Tons}}}}{{{pop_val:,.0f} \\text{{ People}}}} = \\mathbf{{{per_capita_val:.1f}}}
                $$
                
                *A small population (Denominator) amplifies the result.*
                """)

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

    # TAB 3: SCATTER PLOT
    with tab3:
        st.subheader("Economic Growth vs. Environmental Impact")
        st.markdown("""
        *Does being richer mean polluting more?* This chart correlates **GDP per Capita** (Wealth) with **CO₂ Emissions**.
        The size of each bubble represents the country's population.
        """)
        
        # Qui ora usiamo il DataFrame che ha già i dati GDP "riempiti" (ffill)
        df_year_fin = df_year.copy()
        
        # Calcoliamo il GDP pro capite
        # Poiché gdp e population sono stati 'puliti' nel caricamento, non avremo buchi
        df_year_fin['gdp_per_capita'] = df_year_fin['gdp'] / df_year_fin['population']
        
        # Pulizia finale di sicurezza
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
                size_max=60 
            )
            
            fig_scatter.update_traces(marker=dict(sizemin=5))
            fig_scatter.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Nota aggiornata
            st.caption("Note: X-axis is logarithmic. Bubble size represents population. *Most recent available GDP data is used for the current year.*")
        else:
            st.warning(f"Not enough economic data available for the year {selected_year}.")

else:
    st.error("No data available. Please adjust filters.")
