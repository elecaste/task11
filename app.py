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
    
    keep_cols = ['country', 'year', 'iso_code', 'population', 'gdp', 'co2_per_capita', 'co2']
    df = df[keep_cols]
    
    df = df[df['iso_code'].notna()]
    
    # FIX GDP 2023/24 e dati mancanti
    df = df.sort_values(['country', 'year'])
    df['gdp'] = df.groupby('country')['gdp'].ffill()
    df['population'] = df.groupby('country')['population'].ffill()
    
    df = df.dropna(subset=['co2_per_capita'])
    
    # Filtro Micro-stati (> 1 Milione abitanti)
    df = df[df['population'] > 1000000]
    
    return df

df = load_data()
max_year_available = int(df['year'].max())

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("📊 Control Panel")
    
    st.subheader("1. Time Dimension")
    min_year = 1950
    max_year = max_year_available
    
    selected_year = st.slider(
        "Select Year:",
        min_value=min_year,
        max_value=max_year,
        value=2022
    )
    
    st.markdown("---")

    st.subheader("🔍 Find a Country")
    all_countries = sorted(df['country'].unique())
    search_list = ["All Countries (Global View)"] + all_countries
    
    country_zoom = st.selectbox(
        "Search and Zoom to:",
        search_list,
        help="Select a country to highlight it."
    )

    st.markdown("---")

    st.subheader("2. Comparative Analysis")
    default_countries = ["United States", "China", "United Kingdom", "Italy", "India"]
    valid_defaults = [c for c in default_countries if c in all_countries]
    
    selected_countries = st.multiselect(
        "Select countries for Trend Chart:",
        all_countries,
        default=valid_defaults
    )
    
    st.markdown("---")
    
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
    
    # --- KPI SECTION ---
    col1, col2, col3, col4, col5 = st.columns(5)
    
    global_avg = df_year['co2_per_capita'].mean()
    top_per_capita = df_year.sort_values(by="co2_per_capita", ascending=False).iloc[0]
    top_absolute = df_year.sort_values(by="co2", ascending=False).iloc[0]
    
    with col1:
        st.metric("📅 Year", selected_year)
    with col2:
        st.metric("🌍 Global Avg", f"{global_avg:.2f} t")
    with col3:
        st.metric("👤 Top Per Capita", top_per_capita['country'], f"{top_per_capita['co2_per_capita']:.1f} t")
    with col4:
        abs_val = top_absolute['co2']
        abs_str = f"{abs_val/1e9:.2f} B tons" if abs_val > 1e9 else f"{abs_val/1e6:.0f} M tons"
        st.metric("🏭 Top Absolute", top_absolute['country'], abs_str)
    with col5:
        st.metric("👥 Population", f"{df_year['population'].sum()/1e9:.2f} B")

    st.markdown("---")

    # --- TAB SYSTEM ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Per Capita Map",       
        "🏭 Absolute Emissions Map", 
        "📈 Historical Trends", 
        "💰 GDP vs CO₂"
    ])

    geo_settings = dict(showframe=False, projection_type="natural earth", showocean=True, oceancolor="#f0f8ff")
    
    # ==========================
    # TAB 1: MAPPA PRO CAPITE
    # ==========================
    with tab1:
        st.subheader("👤 Per Capita CO₂ Emissions (Intensity)")
        
        fig_map = px.choropleth(
            df_year,
            locations="iso_code",
            color="co2_per_capita",
            hover_name="country",
            hover_data={'iso_code': False, 'population': ':,.0f', 'gdp': ':,.0f'},
            color_continuous_scale="YlOrRd", 
            range_color=(0, 40), 
        )
        
        if country_zoom != "All Countries (Global View)":
            selected_data = df_year[df_year['country'] == country_zoom]
            if not selected_data.empty:
                fig_map.add_trace(px.choropleth(selected_data, locations="iso_code", color_discrete_sequence=["rgba(0,0,0,0)"]).update_traces(marker_line_color="Cyan", marker_line_width=4).data[0])

        fig_map.update_geos(**geo_settings)
        fig_map.update_layout(height=550, margin={"r":0,"t":0,"l":0,"b":0})
        fig_map.update_coloraxes(colorbar_title="Tons/Person")
        st.plotly_chart(fig_map, use_container_width=True)

        # --- LISTA TOP 5 SOTTO LA MAPPA (NUOVO!) ---
        st.markdown("#### 🏆 Top 5 Countries (Per Capita Intensity)")
        top5_pc = df_year.sort_values(by="co2_per_capita", ascending=False).head(5)[['country', 'co2_per_capita']].copy()
        top5_pc.columns = ['Country', 'Tons per Person']
        top5_pc.reset_index(drop=True, inplace=True)
        top5_pc.index += 1
        st.dataframe(top5_pc, use_container_width=True)
        
        # --- INSIGHTS DETTAGLIATI (RIPRISTINATI CORRETTAMENTE) ---
        st.markdown("---")
        st.subheader(f"🔍 Deep Dive (Per Capita): Why is {top_per_capita['country']} ranked #1?")
        
        tp_name = top_per_capita['country']
        tp_pop = top_per_capita['population']
        tp_co2 = top_per_capita['co2']
        tp_val = top_per_capita['co2_per_capita']

        custom_insights = {
            "Qatar": {
                "icon": "⚡", "title": "The LNG Superpower",
                "text": """
                **Specific Driver:** Qatar is the world's leading exporter of **Liquefied Natural Gas (LNG)**. The process of cooling gas to -162°C is incredibly energy-intensive.
                
                **Lifestyle Factor:** Extremely subsidized electricity and water lead to some of the highest domestic consumption rates (AC and desalination)."""
            },
            "United Arab Emirates": {
                "icon": "🏗️", "title": "Construction & Water",
                "text": """
                **Specific Driver:** Emissions driven by rapid **urban construction** (Dubai) and aluminum smelting.
                
                **Water Stress:** Relies almost entirely on **desalination plants**, which are extremely carbon-heavy."""
            },
            "Kuwait": {
                "icon": "🛢️", "title": "Oil-Fired Power",
                "text": """
                **Specific Driver:** Kuwait burns significant amounts of **heavy crude oil** directly to generate electricity.
                
                **Climate Control:** Extreme summer heat drives massive cooling demand per square meter."""
            },
            "Bahrain": {
                "icon": "🏭", "title": "Aluminum Smelting",
                "text": """
                **Specific Driver:** Home to **Alba**, one of the world's largest aluminum smelters. Aluminum production acts as "solid electricity" export."""
            },
            "United States": {
                "icon": "🚗", "title": "Suburban Sprawl",
                "text": """
                **Specific Driver:** Car-centric infrastructure and low fuel taxes.
                
                **Lifestyle:** Large suburban homes with high heating/cooling needs lead to high individual consumption."""
            }
        }
        
        if tp_name in custom_insights:
            insight = custom_insights[tp_name]
            final_icon, final_title, final_text = insight["icon"], insight["title"], insight["text"]
        else:
            final_icon, final_title = "📊", "High Industrial Output / Small Population"
            final_text = f"""
            **The Reason:** {tp_name} combines significant industrial activity with a relatively small population base ({tp_pop:,.0f} people).
            
            **Statistical Effect:** When a country has a small denominator (population), even moderate industrial emissions result in a very high per-capita ranking."""

        with st.expander(f"📖 Read Analysis for {tp_name}", expanded=True):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"### {final_icon} {final_title}")
                st.markdown(final_text)
            with c2:
                st.markdown("#### 🧮 The Evidence (Math)")
                st.markdown(f"How we get **{tp_val:.1f} tons**:")
                st.markdown(f"$$\\frac{{{tp_co2:,.0f} \\text{{ Total Tons}}}}{{{tp_pop:,.0f} \\text{{ People}}}} = \\mathbf{{{tp_val:.1f}}}$$")
                st.markdown("*A small population (Denominator) amplifies the result.*")

    # ==========================
    # TAB 2: MAPPA ASSOLUTA
    # ==========================
    with tab2:
        st.subheader("🏭 Total Absolute Emissions (Global Impact)")
        
        max_abs_co2 = df_year['co2'].max()

        fig_abs = px.choropleth(
            df_year,
            locations="iso_code",
            color="co2", 
            hover_name="country",
            hover_data={'iso_code': False, 'co2': ':,.0f', 'population': ':,.0f'},
            color_continuous_scale="Reds", 
            range_color=(0, max_abs_co2), 
        )

        if country_zoom != "All Countries (Global View)":
             selected_data_abs = df_year[df_year['country'] == country_zoom]
             if not selected_data_abs.empty:
                fig_abs.add_trace(px.choropleth(selected_data_abs, locations="iso_code", color_discrete_sequence=["rgba(0,0,0,0)"]).update_traces(marker_line_color="Cyan", marker_line_width=4).data[0])

        fig_abs.update_geos(**geo_settings)
        fig_abs.update_layout(height=600, margin={"r":0,"t":0,"l":0,"b":0})
        fig_abs.update_coloraxes(colorbar_title="Total Tonnes")
        st.plotly_chart(fig_abs, use_container_width=True)

        # --- LISTA TOP 5 SOTTO LA MAPPA (NUOVO!) ---
        st.markdown("#### 🏆 Top 5 Countries (Total Volume)")
        top5_abs = df_year.sort_values(by="co2", ascending=False).head(5)[['country', 'co2']].copy()
        top5_abs['co2'] = top5_abs['co2'].apply(lambda x: f"{x/1e9:.2f} Billion" if x > 1e9 else f"{x/1e6:.0f} Million")
        top5_abs.columns = ['Country', 'Total Tonnes']
        top5_abs.reset_index(drop=True, inplace=True)
        top5_abs.index += 1
        st.dataframe(top5_abs, use_container_width=True)

    # ==========================
    # TAB 3: LINE CHART
    # ==========================
    with tab3:
        st.subheader("Historical Evolution")
        chart_mode = st.radio("Select Metric:", ["Per Capita (Intensity)", "Total Absolute (Volume)"], horizontal=True)
        
        df_trend = df[df['country'].isin(selected_countries)]
        
        if not df_trend.empty:
            if chart_mode == "Per Capita (Intensity)":
                y_col, title_text, y_label = "co2_per_capita", f"<b>Per Capita Emission Trajectories (1950-{max_year_available})</b>", "Tons per Person"
            else:
                y_col, title_text, y_label = "co2", f"<b>Total Absolute Emission Trajectories (1950-{max_year_available})</b>", "Total Tons"
            
            fig_line = px.line(df_trend, x="year", y=y_col, color="country", title=title_text, markers=False, labels={y_col: y_label})
            fig_line.add_vline(x=selected_year, line_dash="dash", line_color="red", opacity=0.5)
            st.plotly_chart(fig_line, use_container_width=True)
            
            if chart_mode == "Total Absolute (Volume)":
                 st.info("💡 **Observation:** Notice how China's total emissions (Red Line) surpassed the US around **2006**.")
        else:
            st.warning("Select countries in the sidebar.")

    # ==========================
    # TAB 4: SCATTER PLOT
    # ==========================
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
