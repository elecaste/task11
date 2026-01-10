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
    
    # Selezioniamo colonne utili (Aggiunto 'co2' totale per i calcoli esplicativi)
    keep_cols = ['country', 'year', 'iso_code', 'population', 'gdp', 'co2_per_capita', 'co2']
    df = df[keep_cols]
    
    # Pulizia base
    df = df[df['iso_code'].notna()]
    df = df.dropna(subset=['co2_per_capita', 'population', 'co2']) 
    
    # --- FILTRO MICRO-STATI ---
    # Teniamo solo paesi con più di 1 milione di abitanti per evitare distorsioni
    df = df[df['population'] > 1000000]
    
    return df

df = load_data()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("📊 Control Panel")
    
    # A. Filtro Anno
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

    # TAB 1: MAPPA + SPIEGAZIONE AVANZATA
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
        
        # 2. SEZIONE SPIEGAZIONE (NUOVA!)
        st.markdown("---")
        st.subheader(f"🔍 Deep Dive: Why is {top_country_name} ranked #1?")
        
        # Logica per generare la spiegazione basata sul tipo di paese
        gulf_states = ['Qatar', 'United Arab Emirates', 'Kuwait', 'Bahrain', 'Saudi Arabia']
        western_industrial = ['United States', 'Luxembourg', 'United Kingdom', 'Canada']
        
        # Calcoliamo i numeri per l'evidenza
        total_co2_val = top_country_row['co2'] 
        pop_val = top_country_row['population']
        per_capita_val = top_country_row['co2_per_capita']
        
        explanation_text = ""
        
        if top_country_name in gulf_states:
            explanation_type = "🛢️ **Energy-Intensive Economy (Oil & Gas)**"
            explanation_text = f"""
            **The Context:** {top_country_name} is a major producer of fossil fuels. The economy relies heavily on energy-intensive processes like **oil refining** and **desalination** (converting seawater to drinking water), which require massive amounts of energy.
            
            **The Denominator Effect:** With a relatively small population ({pop_val:,.0f} people), the massive industrial emissions are divided by few inhabitants, resulting in a very high per capita figure.
            """
        elif top_country_name in western_industrial:
            explanation_type = "🏭 **Industrial Manufacturing & Consumption**"
            explanation_text = f"""
            **The Context:** {top_country_name} has a highly developed industrial base (Steel, Manufacturing, Automotive) and high levels of domestic consumption. 
            
            **Historical Note:** In the mid-20th century, these economies relied heavily on coal and heavy industry before transitioning to service-based economies.
            """
        else:
            explanation_type = "📊 **High Industrial Output / Small Population**"
            explanation_text = f"""
            **The Reason:** This country combines significant industrial or mining activity with a relatively small population base. This creates a statistical spike in per-capita metrics compared to larger, more diversified economies.
            """

        # Mostriamo l'insight in un box pulito
        with st.expander(f"📖 Read Analysis for {top_country_name}", expanded=True):
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                st.markdown(f"### {explanation_type}")
                st.markdown(explanation_text)
                
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
                size_max=60 
            )
            
            fig_scatter.update_traces(marker=dict(sizemin=5))
            fig_scatter.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.caption("Note: X-axis is logarithmic. Bubble size represents population.")
        else:
            st.warning(f"Not enough economic data available for the year {selected_year}.")

else:
    st.error("No data available. Please adjust filters.")
