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
    
    # Selezioniamo colonne utili (co2 è il totale assoluto)
    keep_cols = ['country', 'year', 'iso_code', 'population', 'gdp', 'co2_per_capita', 'co2']
    df = df[keep_cols]
    
    # Pulizia base
    df = df[df['iso_code'].notna()]
    
    # FIX GDP MANCANTE
    df = df.sort_values(['country', 'year'])
    df['gdp'] = df.groupby('country')['gdp'].ffill()
    df['population'] = df.groupby('country')['population'].ffill()
    
    # Rimuoviamo righe solo se manca il dato fondamentale pro capite
    df = df.dropna(subset=['co2_per_capita'])
    
    # Filtro Micro-stati
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
        help="Select a country to highlight it."
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
    
    **Metodologia:**
    * **Per Capita:** Emissioni totali divise per la popolazione. Indica lo stile di vita.
    * **Absolute:** Tonnellate totali emesse. Indica l'impatto globale del paese.
    
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
    top_country_row = top_5_emitters.iloc[0]
    top_country_name = top_country_row['country']
    
    with col1:
        st.metric("📅 Selected Year", selected_year)
    with col2:
        st.metric("🌍 Global Avg (Per Capita)", f"{global_avg:.2f} t")
    with col3:
        # Calcoliamo anche il top Absolute Emitter per completezza
        top_abs = df_year.sort_values(by="co2", ascending=False).iloc[0]
        st.metric("🏭 Top Absolute Emitter", top_abs['country'], help="Country with highest total emissions.")
    with col4:
        st.metric("👥 Tracked Population", f"{df_year['population'].sum()/1e9:.2f} B")

    st.markdown("---")

    # --- TAB SYSTEM AGGIORNATO (4 TABS) ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Map (Per Capita)", 
        "🗺️ Map (Absolute Giants)", # NUOVO TAB
        "📈 Historical Trends", 
        "💰 GDP vs CO₂"
    ])

    # ==========================
    # TAB 1: MAPPA PRO CAPITE
    # ==========================
    with tab1:
        fig_map = px.choropleth(
            df_year,
            locations="iso_code",
            color="co2_per_capita",
            hover_name="country",
            hover_data={'iso_code': False, 'population': ':,.0f', 'gdp': ':,.0f'},
            color_continuous_scale="YlOrRd", 
            range_color=(0, 40), 
            title=f"<b>CO₂ Per Capita Intensity ({selected_year})</b>",
        )
        
        # Zoom Logic (Condivisa)
        geo_settings = dict(showframe=False, projection_type="natural earth", showocean=True, oceancolor="#f0f8ff")
        if country_zoom != "All Countries (Global View)":
            country_iso_series = df_year[df_year['country'] == country_zoom]['iso_code']
            if not country_iso_series.empty:
                selected_data = df_year[df_year['country'] == country_zoom]
                fig_map.add_trace(px.choropleth(selected_data, locations="iso_code", color_discrete_sequence=["rgba(0,0,0,0)"]).update_traces(marker_line_color="Cyan", marker_line_width=4).data[0])
                fig_map.update_layout(title_text=f"<b>Per Capita View - Highlighted: {country_zoom}</b>")

        fig_map.update_geos(**geo_settings)
        fig_map.update_layout(height=550, margin={"r":0,"t":40,"l":0,"b":0})
        fig_map.update_coloraxes(colorbar_title="Tons/Person")
        st.plotly_chart(fig_map, use_container_width=True)
        
        # --- SPIEGAZIONE PRO CAPITE (QATAR ecc.) ---
        # (Manteniamo la tua logica esistente qui)
        st.markdown("---")
        st.subheader(f"🔍 Deep Dive (Per Capita): Why is {top_country_name} ranked #1?")
        # Dati per la formula
        total_co2_val_pc = top_country_row['co2'] 
        pop_val_pc = top_country_row['population']
        per_capita_val_pc = top_country_row['co2_per_capita']

        custom_insights = {
            "Qatar": {"icon": "⚡", "title": "The LNG Superpower", "text": "Massive energy required for LNG cooling and desalination, divided by a small population."},
            "United Arab Emirates": {"icon": "🏗️", "title": "Construction & Water", "text": "Driven by rapid urban construction (Dubai) and energy-intensive water desalination."},
            "Kuwait": {"icon": "🛢️", "title": "Oil-Fired Power", "text": "Relies heavily on burning crude oil directly for electricity and extreme cooling needs."},
            "United States": {"icon": "🚗", "title": "High Consumption Lifestyle", "text": "Historical development based on car-centric infrastructure, large homes, and high consumption."},
        }
        if top_country_name in custom_insights:
            insight = custom_insights[top_country_name]
            final_icon, final_title, final_text = insight["icon"], insight["title"], insight["text"]
        else:
            final_icon, final_title = "📊", "High Industrial Output / Small Population"
            final_text = f"{top_country_name} combines significant industrial activity with a relatively small population base."

        with st.expander(f"📖 Read Analysis for {top_country_name}", expanded=True):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.markdown(f"### {final_icon} {final_title}")
                st.markdown(final_text)
            with col_b:
                st.markdown("#### 🧮 The Math (Denominator Effect)")
                st.markdown(f"$$\\frac{{{total_co2_val_pc:,.0f} \\text{{ Total}}}}{{{pop_val_pc:,.0f} \\text{{ People}}}} = \\mathbf{{{per_capita_val_pc:.1f}}}$$")

    # ==========================
    # TAB 2: NUOVA MAPPA ASSOLUTA
    # ==========================
    with tab2:
        st.subheader("🏭 Who are the total biggest emitters?")
        st.markdown("This map shows the **total absolute emissions** in tonnes. It highlights the world's industrial and demographic giants, regardless of their population size.")

        # Calcoliamo il massimo assoluto dell'anno per settare la scala dinamicamente
        max_abs_co2 = df_year['co2'].max()

        fig_abs = px.choropleth(
            df_year,
            locations="iso_code",
            # USIAMO LA COLONNA DEL TOTALE ASSOLUTO
            color="co2", 
            hover_name="country",
            # Formattiamo il numero grande con le virgole
            hover_data={'iso_code': False, 'co2': ':,.0f', 'population': ':,.0f'},
            
            # NUOVA PALETTE: "Plasma" (Viola -> Giallo acceso) per un look diverso e "pesante"
            color_continuous_scale="Plasma", 
            
            # RANGE DINAMICO: Da 0 al massimo emettitore di quell'anno (es. Cina)
            # Questo assicura che i giganti siano sempre evidenziati al massimo.
            range_color=(0, max_abs_co2), 
            
            title=f"<b>Total Absolute CO₂ Emissions ({selected_year})</b>",
        )

        # Applichiamo lo stesso zoom se attivo
        if country_zoom != "All Countries (Global View)":
             if not country_iso_series.empty: # riusiamo la serie calcolata nel tab1
                selected_data_abs = df_year[df_year['country'] == country_zoom]
                fig_abs.add_trace(px.choropleth(selected_data_abs, locations="iso_code", color_discrete_sequence=["rgba(0,0,0,0)"]).update_traces(marker_line_color="Cyan", marker_line_width=4).data[0])
                fig_abs.update_layout(title_text=f"<b>Absolute View - Highlighted: {country_zoom}</b>")

        fig_abs.update_geos(**geo_settings)
        fig_abs.update_layout(height=600, margin={"r":0,"t":40,"l":0,"b":0})
        # Titolo della barra colori specifico
        fig_abs.update_coloraxes(colorbar_title="Total Tonnes")
        
        st.plotly_chart(fig_abs, use_container_width=True)
        
        # Mini-classifica assoluta sotto la mappa
        st.markdown("#### 🏆 Top 5 Absolute Giants")
        top_5_abs = df_year.sort_values(by="co2", ascending=False).head(5).copy()
        top_5_abs = top_5_abs[['country', 'co2']]
        top_5_abs.columns = ['Country', 'Total Tonnes']
        # Formattiamo i numeri grandi in miliardi/milioni per leggibilità nella tabella
        top_5_abs['Total Tonnes'] = top_5_abs['Total Tonnes'].apply(lambda x: f"{x/1e9:.2f} Billion" if x > 1e9 else f"{x/1e6:.0f} Million")
        top_5_abs.reset_index(drop=True, inplace=True)
        top_5_abs.index += 1
        st.table(top_5_abs)

    # TAB 3: LINE CHART (Invariato)
    with tab3:
        st.subheader("Historical Evolution (Per Capita)")
        df_trend = df[df['country'].isin(selected_countries)]
        if not df_trend.empty:
            fig_line = px.line(df_trend, x="year", y="co2_per_capita", color="country", title="<b>Emission Trajectories (1950-2022)</b>", markers=False)
            fig_line.add_vline(x=selected_year, line_dash="dash", line_color="red", opacity=0.5)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("Select countries in the sidebar.")

    # TAB 4: SCATTER PLOT (Invariato)
    with tab4:
        st.subheader("Economic Growth vs. Environmental Impact")
        st.markdown("*Does being richer mean polluting more?* (GDP vs CO₂ Per Capita)")
        df_year_fin = df_year.copy()
        df_year_fin['gdp_per_capita'] = df_year_fin['gdp'] / df_year_fin['population']
        df_year_fin = df_year_fin.dropna(subset=['gdp_per_capita', 'co2_per_capita', 'population'])

        if not df_year_fin.empty:
            fig_scatter = px.scatter(
                df_year_fin, x="gdp_per_capita", y="co2_per_capita", size="population", color="country", hover_name="country",
                log_x=True, title=f"<b>Correlation: GDP per Capita vs CO₂ ({selected_year})</b>",
                labels={'gdp_per_capita': 'GDP per Capita ($)', 'co2_per_capita': 'CO₂ per Capita (t)'}, size_max=60
            )
            fig_scatter.update_traces(marker=dict(sizemin=5))
            fig_scatter.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.caption("Note: X-axis is logarithmic. Bubble size represents population. Most recent GDP used for current year.")
        else:
            st.warning(f"Not enough economic data available for the year {selected_year}.")

else:
    st.error("No data available. Please adjust filters.")
