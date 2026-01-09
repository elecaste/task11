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
    
    # Selezioniamo colonne utili inclusi PIL (gdp) e popolazione
    keep_cols = ['country', 'year', 'iso_code', 'population', 'gdp', 'co2_per_capita', 'co2']
    df = df[keep_cols]
    
    # Pulizia: Rimuoviamo righe che non sono paesi
    df = df[df['iso_code'].notna()]
    
    # Rimuoviamo righe con CO2 nullo per evitare errori grafici
    df = df.dropna(subset=['co2_per_capita'])
    
    return df

df = load_data()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("📊 Control Panel")
    
    # Filtro Anno
    st.subheader("1. Time Dimension")
    min_year = 1950 # Partiamo dal 1950 per avere dati GDP più solidi
    max_year = int(df['year'].max())
    
    selected_year = st.slider(
        "Select Year:",
        min_value=min_year,
        max_value=max_year,
        value=2022
    )
    
    st.markdown("---")

    # Filtro Paesi per il grafico Trend
    st.subheader("2. Comparative Analysis")
    all_countries = sorted(df['country'].unique())
    default_countries = ["United States", "China", "United Kingdom", "Italy", "India"]
    # Controlliamo che i default esistano nel dataset filtrato
    valid_defaults = [c for c in default_countries if c in all_countries]
    
    selected_countries = st.multiselect(
        "Select countries for Trend Chart:",
        all_countries,
        default=valid_defaults
    )
    
    st.markdown("---")
    
    # Informazioni Studente e Fonte
    st.info("ℹ️ **About**")
    st.markdown("""
    **Data Source:** [Our World in Data: CO₂ and Greenhouse Gas Emissions](https://ourworldindata.org/co2-and-greenhouse-gas-emissions)
    
    **Student Project:** Eleonora Castellani  
    *USI Master in Finance (Minor in Digital)*
    """)

# --- 4. PAGINA PRINCIPALE ---
st.title("Global CO2 emissions and analysis")
st.markdown(f"### Analysis for year **{selected_year}**")

# Filtro dati anno
df_year = df[df['year'] == selected_year]

if not df_year.empty:
    
    # KPI (Top metrics)
    col1, col2, col3, col4 = st.columns(4)
    global_avg = df_year['co2_per_capita'].mean()
    
    # Gestione caso dati mancanti per KPI
    max_emitter = df_year.loc[df_year['co2_per_capita'].idxmax()] if not df_year.empty else None
    
    with col1:
        st.metric("📅 Selected Year", selected_year)
    with col2:
        st.metric("🌍 Global Avg (Per Capita)", f"{global_avg:.2f} t")
    with col3:
        if max_emitter is not None:
            st.metric("🏭 Highest Emitter", max_emitter['country'], f"{max_emitter['co2_per_capita']:.1f} t")
    with col4:
        st.metric("👥 Tracked Population", f"{df_year['population'].sum()/1e9:.2f} B")

    st.markdown("---")

    # --- TAB SYSTEM (Per organizzare le visualizzazioni) ---
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

   # --- TAB SYSTEM ---
    tab1, tab2, tab3 = st.tabs(["🗺️ Global Map", "📈 Trend Analysis (Deep Dive)", "💰 Motion Chart (GDP vs CO₂)"])

    # TAB 1: MAPPA (Resta uguale, è perfetta)
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

    # TAB 2: LINE CHART CON OPZIONE FINANCE (CARBON INTENSITY)
    with tab2:
        st.subheader("Historical Evolution & Efficiency")
        
        # --- NOVITÀ: Radio button per scegliere la metrica ---
        metric_choice = st.radio(
            "Select Metric to Analyze:",
            ["Emission per Capita (Impact)", "Carbon Intensity (Efficiency)"],
            horizontal=True,
            help="Per Capita = How much people pollute. Intensity = How dirty the production of wealth is (CO2 / GDP)."
        )
        
        df_trend = df[df['country'].isin(selected_countries)].copy()
        
        if not df_trend.empty:
            if metric_choice == "Emission per Capita (Impact)":
                y_val = "co2_per_capita"
                title_txt = "Emission Trajectories (Tonnes per Person)"
                y_label = "CO₂ (t/person)"
            else:
                # Calcolo Carbon Intensity: CO2 (kg) per Dollaro di PIL
                # Moltiplichiamo per 1000 per avere grammi/chili leggibili se i dati sono in tonnellate
                df_trend['carbon_intensity'] = df_trend['co2'] / df_trend['gdp']
                y_val = "carbon_intensity"
                title_txt = "Economic Efficiency: CO₂ emitted per $ of GDP"
                y_label = "CO₂ Intensity (kg/$)"

            fig_line = px.line(
                df_trend,
                x="year",
                y=y_val,
                color="country",
                title=f"<b>{title_txt}</b>",
                markers=False
            )
            fig_line.add_vline(x=selected_year, line_dash="dash", line_color="red", opacity=0.5)
            # Scala logaritmica opzionale se le differenze sono enormi
            # fig_line.update_yaxes(type="log") 
            st.plotly_chart(fig_line, use_container_width=True)
            
            if metric_choice == "Carbon Intensity (Efficiency)":
                st.info("💡 **Finance Note:** A downward trend in Carbon Intensity means the country is becoming more efficient at generating wealth with less pollution (Decoupling).")
        else:
            st.warning("Select countries in the sidebar to visualize trends.")

    # TAB 3: ANIMATED SCATTER PLOT (IL WOW FACTOR)
    with tab3:
        st.subheader("The Evolution of Wealth and Pollution (1950-2022)")
        st.markdown("Press **Play ▶️** below to watch how the world has changed over the last 70 years.")
        
        # Prepariamo i dati per l'animazione (tutti gli anni, non solo quello selezionato)
        # Filtriamo per ridurre il carico (anni > 1950 e rimuoviamo dati nulli)
        df_anim = df[(df['year'] >= 1950) & (df['year'] <= 2022)].copy()
        df_anim['gdp_per_capita'] = df_anim['gdp'] / df_anim['population']
        df_anim = df_anim.dropna(subset=['gdp_per_capita', 'co2_per_capita', 'population', 'country'])
        
        # Ordiniamo per anno per garantire l'animazione fluida
        df_anim = df_anim.sort_values("year")

        if not df_anim.empty:
            fig_anim = px.scatter(
                df_anim,
                x="gdp_per_capita",
                y="co2_per_capita",
                animation_frame="year", # <--- QUESTA È LA MAGIA
                animation_group="country",
                size="population",
                color="country", # O 'continent' se lo avessimo
                hover_name="country",
                log_x=True,
                size_max=60,
                range_x=[df_anim['gdp_per_capita'].min(), df_anim['gdp_per_capita'].max()], # Assi fissi
                range_y=[0, 30], # Assi fissi per evitare saltelli
                title="<b>Motion Chart: GDP vs CO₂ Evolution</b>",
                labels={'gdp_per_capita': 'GDP per Capita ($)', 'co2_per_capita': 'CO₂ per Capita (t)'}
            )
            
            fig_anim.update_traces(marker=dict(sizemin=4))
            fig_anim.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 100 # Velocità animazione
            fig_anim.update_layout(height=650, showlegend=False)
            
            st.plotly_chart(fig_anim, use_container_width=True)
        else:
            st.warning("Data loading for animation...")
