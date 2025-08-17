import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import yaml
import subprocess
import sys
import time
import statsmodels.api as sm
from tenacity import retry, stop_after_attempt, wait_exponential
import requests

project_root_for_imports = os.path.join(os.path.dirname(__file__), '..')
if project_root_for_imports not in sys.path:
    sys.path.insert(0, project_root_for_imports)

from pia_project_energy_analysis.config_loader import load_configuration

CITY_TO_BA_MAPPING = {
    "new york": "NYIS", "los angeles": "CISO", "chicago": "PJM", "houston": "ERCO", "phoenix": "AZPS", 
    "philadelphia": "PJM", "san antonio": "ERCO", "san diego": "CISO", "dallas": "ERCO", "san jose": "CISO", 
    "austin": "ERCO", "jacksonville": "JEA", "fort worth": "ERCO", "columbus": "PJM", "charlotte": "DUK", 
    "san francisco": "CISO", "indianapolis": "MISO", "seattle": "SCL", "denver": "PSCO", "washington": "PJM", 
    "boston": "ISNE", "el paso": "EPE", "detroit": "MISO", "nashville": "TVA", "portland": "PGE", "memphis": "TVA", 
    "oklahoma city": "SWPP", "las vegas": "NEVP", "louisville": "LGEE", "baltimore": "PJM", "milwaukee": "MISO", 
    "albuquerque": "PNM", "tucson": "TEPC", "fresno": "CISO", "sacramento": "CISO", "kansas city": "SWPP", 
    "long beach": "CISO", "mesa": "SRP", "atlanta": "SOCO", "colorado springs": "PSCO", "miami": "FPL", 
    "raleigh": "CPLE", "omaha": "MISO", "minneapolis": "MISO", "tulsa": "SWPP", "cleveland": "PJM", 
    "wichita": "SWPP", "arlington": "ERCO", "new orleans": "MISO", "bakersfield": "CISO", "tampa": "TEC", 
    "honolulu": "HECO", "aurora": "PSCO", "anaheim": "CISO", "santa ana": "CISO", "st. louis": "MISO", 
    "pittsburgh": "PJM", "corpus christi": "ERCO", "riverside": "CISO", "cincinnati": "PJM", "lexington": "LGEE", 
    "anchorage": "MEA", "stockton": "CISO", "toledo": "MISO", "saint paul": "MISO", "newark": "PJM", 
    "greensboro": "DUK", "plano": "ERCO", "henderson": "NEVP", "lincoln": "MISO", "orlando": "FPC", 
    "jersey city": "PJM", "chula vista": "CISO", "buffalo": "NYIS", "fort wayne": "MISO", "chandler": "SRP", 
    "laredo": "ERCO", "madison": "MISO", "durham": "CPLE", "lubbock": "ERCO", "winston-salem": "DUK", 
    "garland": "ERCO", "glendale": "SRP", "reno": "NEVP", "hialeah": "FPL", "boise": "IPCO", "scottsdale": "SRP", 
    "irving": "ERCO", "chesapeake": "PJM", "north las vegas": "NEVP", "fremont": "CISO", "baton rouge": "MISO", 
    "richmond": "PJM", "san bernardino": "CISO", "spokane": "AVA", "des moines": "MISO", "tacoma": "TPWR", 
    "montgomery": "SOCO", "little rock": "MISO", "salt lake city": "PACE"
}
STATE_TO_PRIMARY_BA = {
    'alabama': 'SOCO', 'alaska': 'None', 'arizona': 'AZPS', 'arkansas': 'MISO', 'california': 'CISO', 
    'colorado': 'PSCO', 'connecticut': 'ISNE', 'delaware': 'PJM', 'district of columbia': 'PJM', 'florida': 'FPL', 
    'georgia': 'SOCO', 'hawaii': 'HECO', 'idaho': 'IPCO', 'illinois': 'PJM', 'indiana': 'MISO', 'iowa': 'MISO', 
    'kansas': 'SWPP', 'kentucky': 'LGEE', 'louisiana': 'MISO', 'maine': 'ISNE', 'maryland': 'PJM', 
    'massachusetts': 'ISNE', 'michigan': 'MISO', 'minnesota': 'MISO', 'mississippi': 'MISO', 'missouri': 'MISO', 
    'montana': 'NWMT', 'nebraska': 'MISO', 'nevada': 'NEVP', 'new hampshire': 'ISNE', 'new jersey': 'PJM', 
    'new mexico': 'PNM', 'new york': 'NYIS', 'north carolina': 'DUK', 'north dakota': 'MISO', 'ohio': 'PJM', 
    'oklahoma': 'SWPP', 'oregon': 'PGE', 'pennsylvania': 'PJM', 'rhode island': 'ISNE', 'south carolina': 'SCEG', 
    'south dakota': 'MISO', 'tennessee': 'TVA', 'texas': 'ERCO', 'utah': 'PACE', 'vermont': 'ISNE', 'virginia': 'PJM', 
    'washington': 'SCL', 'west virginia': 'PJM', 'wisconsin': 'MISO', 'wyoming': 'PACE'
}
STATE_FIPS = {
    'Alabama': '01', 'Alaska': '02', 'Arizona': '04', 'Arkansas': '05', 'California': '06', 'Colorado': '08', 
    'Connecticut': '09', 'Delaware': '10', 'District of Columbia': '11', 'Florida': '12', 'Georgia': '13', 
    'Hawaii': '15', 'Idaho': '16', 'Illinois': '17', 'Indiana': '18', 'Iowa': '19', 'Kansas': '20', 'Kentucky': '21', 
    'Louisiana': '22', 'Maine': '23', 'Maryland': '24', 'Massachusetts': '25', 'Michigan': '26', 'Minnesota': '27', 
    'Mississippi': '28', 'Missouri': '29', 'Montana': '30', 'Nebraska': '31', 'Nevada': '32', 'New Hampshire': '33', 
    'New Jersey': '34', 'New Mexico': '35', 'New York': '36', 'North Carolina': '37', 'North Dakota': '38', 'Ohio': '39', 
    'Oklahoma': '40', 'Oregon': '41', 'Pennsylvania': '42', 'Rhode Island': '44', 'South Carolina': '45', 
    'South Dakota': '46', 'Tennessee': '47', 'Texas': '48', 'Utah': '49', 'Vermont': '50', 'Virginia': '51', 
    'Washington': '52', 'West Virginia': '54', 'Wisconsin': '55', 'Wyoming': '56'
}

class CityToBaMapper:
    def find_ba_for_station(self, station_name, state_name):
        city_name_lower = station_name.lower().split(',')[0].split(' ')[0]
        if city_name_lower in CITY_TO_BA_MAPPING:
            return CITY_TO_BA_MAPPING[city_name_lower], "City Match"
        if state_name:
            state_name_lower = state_name.lower()
            if state_name_lower in STATE_TO_PRIMARY_BA:
                return STATE_TO_PRIMARY_BA[state_name_lower], "State Estimate"
        return 'N/A', "No Match"

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def _make_station_request(params, headers):
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
    response = requests.get(url, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()

def find_noaa_stations(state_name, noaa_token):
    if not noaa_token:
        st.error("NOAA API token not found. Cannot search for stations. Please check your `.env` file.")
        return None
    fips_code = STATE_FIPS.get(state_name)
    if not fips_code:
        st.warning(f"State '{state_name}' not found.")
        return None
    headers = {'token': noaa_token}
    params = {'datasetid': 'GHCND', 'locationid': f'FIPS:{fips_code}', 'limit': 1000}
    try:
        with st.spinner(f"Searching for weather stations in {state_name}..."):
            data = _make_station_request(params, headers)
        results = data.get('results', [])
        if results:
            df = pd.DataFrame(results)            
            df['maxdate'] = pd.to_datetime(df['maxdate'])
            one_year_ago = pd.to_datetime('today') - pd.DateOffset(years=1)
            active_stations_df = df[df['maxdate'] >= one_year_ago].copy()

            if active_stations_df.empty:
                st.warning(f"No recently active weather stations found for {state_name}. The pipeline may fail for stations that have not reported data in over a year.", icon="⚠️")
                all_stations_df = df[['id', 'name', 'latitude', 'longitude']].copy()
                all_stations_df.rename(columns={'id': 'noaa_station_id'}, inplace=True)
                return all_stations_df

            major_active_stations_df = active_stations_df[active_stations_df['id'].str.startswith('GHCND:USW')].copy()

            if not major_active_stations_df.empty:
                st.success(f"Found {len(major_active_stations_df)} major, recently active weather stations. These are highly recommended for analysis.")
                major_active_stations_df = major_active_stations_df[['id', 'name', 'latitude', 'longitude']]
                major_active_stations_df.rename(columns={'id': 'noaa_station_id'}, inplace=True)
                return major_active_stations_df
            else:
                st.warning(f"No major weather stations found for {state_name}. The smaller, active stations listed below may not have the required temperature data.", icon="⚠️")
                active_stations_df = active_stations_df[['id', 'name', 'latitude', 'longitude']]
                active_stations_df.rename(columns={'id': 'noaa_station_id'}, inplace=True)
                return active_stations_df
        else:
            st.info(f"No stations found for {state_name}.")
            return None
    except Exception as e:
        st.error(f"Failed to fetch stations from NOAA API: {e}")
        return None

@st.cache_data
def load_data():
    project_root = os.path.join(os.path.dirname(__file__), '..')
    data_path = os.path.join(project_root, 'data', 'output', 'master_energy_weather_data.csv')
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    
    if not os.path.exists(data_path):
        st.error(f"Master data file not found at `{data_path}`.")
        st.warning("The master data file is missing. Please run the main application to generate it. From your project root, execute:")
        st.code("python run.py")
        st.stop()

    try:
        df = pd.read_csv(data_path)
        df['date'] = pd.to_datetime(df['date'])
    except Exception as e:
        st.error(f"An error occurred while loading or parsing the data file: {e}")
        st.stop()

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        cities_info = {city['name']: {'latitude': city['latitude'], 'longitude': city['longitude']} for city in config.get('cities', [])}
        
        df['latitude'] = df['city'].map(lambda x: cities_info.get(x, {}).get('latitude'))
        df['longitude'] = df['city'].map(lambda x: cities_info.get(x, {}).get('longitude'))
        
        return df

    except (FileNotFoundError, yaml.YAMLError) as e:
        st.warning(f"Could not load city coordinates from config file: {e}")
        return df

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def apply_compact_style():
    st.markdown("""
        <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            [data-testid="stSidebar"] > div:first-child {
                padding-top: 0rem;
            }
            [data-testid="stVerticalBlock"] > [style*="gap"] {
                gap: 0.1rem;
            }
            [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [style*="gap"] {
                gap: 0.25rem;
            }
            button[data-testid="stTab"] {
                font-size: 1.2rem;
                font-weight: 600;
            }
            h1 { font-size: 2.2rem !important; margin-bottom: 0rem !important; }
            h2 { font-size: 1.6rem !important; }
            h3 { font-size: 1.3rem !important; }
            [data-testid="stMetricLabel"] {
                font-size: 1rem !important;
                font-weight: 600 !important;
            }
        </style>
    """, unsafe_allow_html=True)

def run_pipeline_from_dashboard(start_date=None, end_date=None):
    log_area = st.empty()
    log_content = "--- Starting Data Pipeline ---\n"
    log_area.code(log_content, language='log')

    project_root = os.path.join(os.path.dirname(__file__), '..')
    run_script_path = os.path.join(project_root, 'run.py')

    command = [sys.executable, run_script_path, '--pipeline-only']
    if start_date and end_date:
        command.extend(['--fetch-range', start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')])

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=project_root,
        encoding='utf-8',
        errors='replace'
    )

    for line in iter(process.stdout.readline, ''):
        log_content += line
        log_area.code(log_content, language='log')
    
    process.stdout.close()
    process.wait()
    log_area.code(log_content, language='log')

def save_configuration(new_cities_list):
    project_root = os.path.join(os.path.dirname(__file__), '..')
    config_path = os.path.join(project_root, 'config', 'config.yaml')

    try:
        with open(config_path, 'r') as f:
            full_config = yaml.safe_load(f)

        if not isinstance(new_cities_list, list):
            st.error("Configuration must be a list of cities in valid YAML format.")
            return False

        for city in new_cities_list:
            if 'latitude' in city and city['latitude'] is not None:
                city['latitude'] = float(city['latitude'])
            if 'longitude' in city and city['longitude'] is not None:
                city['longitude'] = float(city['longitude'])

        # Replace the cities list in the config
        full_config['cities'] = new_cities_list

        with open(config_path, 'w') as f:
            yaml.dump(full_config, f, default_flow_style=False, sort_keys=False, indent=2)
        
        return True
    except (ValueError, TypeError) as e:
        st.error(f"Invalid value for latitude/longitude. Please ensure they are numbers. Error: {e}")
        return False
    except Exception as e:
        st.error(f"Failed to save configuration: {e}")
        return False

def main():
    st.set_page_config(page_title="Energy & Weather Analysis", layout="wide")
    apply_compact_style()
    
    master_df = load_data()

    expected_cols = ['TMAX_F', 'TMIN_F', 'energy_mwh', 'date', 'city']
    for col in expected_cols:
        if col not in master_df.columns:
            master_df[col] = pd.NA
    
    if 'date' in master_df.columns:
        master_df['date'] = pd.to_datetime(master_df['date'])

    with st.sidebar:
        download_button_placeholder = st.empty()
        
        st.markdown("---")
        st.header("Manage Data")

        with st.expander("Refresh Data", expanded=False):
            st.info("This will re-run the data pipeline for the selected date range. This may take several minutes.")
            
            col1, col2 = st.columns(2)
            with col1:
                refresh_start_date = st.date_input("Fetch Start Date", value=pd.to_datetime('today') - pd.DateOffset(years=1), key="refresh_start")
            with col2:
                refresh_end_date = st.date_input("Fetch End Date", value=pd.to_datetime('today') - pd.DateOffset(days=1), key="refresh_end")

            if st.button("🔄 Refresh All Data"):
                with st.spinner("Pipeline is running... see logs below."):
                    run_pipeline_from_dashboard(start_date=refresh_start_date, end_date=refresh_end_date)
                st.success("Pipeline finished! Reloading dashboard with new data...")
                st.cache_data.clear()
                time.sleep(3)
                st.rerun()

        st.markdown("---")
        st.header("Analysis Options")
        
        temp_metric = st.radio(
            "Select Temperature Metric",
            ('Max Temperature (TMAX)', 'Min Temperature (TMIN)', 'Average Temperature'),
            key='temp_metric_selector'
        )
        if not master_df.empty and 'date' in master_df.columns and not master_df['date'].isna().all():
            min_date = master_df['date'].min().date()
            max_date = master_df['date'].max().date()

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date, key='start_date')
            with col2:
                end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date, key='end_date')
            
            if start_date > end_date:
                st.error("Error: End date must be on or after start date.")
                st.stop()

        else:
            st.warning("No data loaded to select a date range.")
            st.stop()

        city_list = ['All Cities'] + sorted(master_df['city'].unique())
        selected_city = st.selectbox(
            "Select a City",
            options=city_list,
            key="global_city_filter"
        )

    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date)
    df_date_filtered = master_df[(master_df['date'] >= start_datetime) & (master_df['date'] <= end_datetime)].copy()

    if temp_metric == 'Max Temperature (TMAX)':
        df_date_filtered['temp_for_analysis'] = df_date_filtered['TMAX_F']
        temp_axis_label = "Max Temperature (°F)"
    elif temp_metric == 'Min Temperature (TMIN)':
        df_date_filtered['temp_for_analysis'] = df_date_filtered['TMIN_F']
        temp_axis_label = "Min Temperature (°F)"
    else:
        df_date_filtered['temp_for_analysis'] = (df_date_filtered['TMAX_F'] + df_date_filtered['TMIN_F']) / 2
        temp_axis_label = "Average Temperature (°F)"
    
    df_date_filtered.dropna(subset=['temp_for_analysis'], inplace=True)

    if selected_city == 'All Cities':
        display_df = df_date_filtered.copy()
    else:
        display_df = df_date_filtered[df_date_filtered['city'] == selected_city].copy()

    with download_button_placeholder.container():
        st.header("Export Data")
        
        csv = convert_df_to_csv(display_df)
        
        st.download_button(
           label="Download Filtered Data",
           data=csv,
           file_name=f"filtered_data_{start_date}_to_{end_date}_{selected_city.replace(' ', '_')}.csv",
           mime="text/csv",
        )

    st.title("U.S. Weather and Energy Consumption Analysis")

    with st.expander("⚙️ Edit Configuration & Add Cities"):
        st.write("Here you can manage the list of cities for analysis and find the necessary IDs.")

        st.subheader("Find Required IDs for a City")
        st.info("To add a new city, you need its **NOAA Station ID** and its **EIA Balancing Authority Code**. Use this tool to find them.")

        selected_state = st.selectbox("Select a U.S. State to find its stations and energy regions:", options=sorted(STATE_FIPS.keys()), key="modal_state_select", index=None, placeholder="Choose a state...")
        
        if selected_state:
            if st.button(f"Find Available IDs for {selected_state}", key="modal_find_stations"):
                _, noaa_token, _ = load_configuration()
                st.session_state.station_results = find_noaa_stations(selected_state, noaa_token)

        if 'station_results' in st.session_state and st.session_state.station_results is not None:
            st.markdown("---")
            st.markdown("##### Step 2: Select Stations to Add")
            st.info("Check the 'Add' box for stations you want to include. You can edit the city name for clarity.")
            
            results_df = st.session_state.station_results.copy()
            mapper = CityToBaMapper()
            
            mapping_results = results_df.apply(lambda row: mapper.find_ba_for_station(row['name'], selected_state), axis=1)
            results_df[['eia_ba_code', 'match_type']] = pd.DataFrame(mapping_results.tolist(), index=results_df.index)
            
            results_df.insert(0, 'Add', False)

            edited_stations_df = st.data_editor(
                results_df[['Add', 'name', 'noaa_station_id', 'eia_ba_code', 'latitude', 'longitude']],
                column_config={"name": st.column_config.TextColumn("City Name (Editable)")},
                use_container_width=True,
                key="station_selector_editor"
            )

            if st.button("Add Selected to Configuration"):
                selected_rows = edited_stations_df[edited_stations_df['Add']]
                if not selected_rows.empty:
                    rows_to_add = selected_rows.drop(columns=['Add']).to_dict('records')
                    for row in rows_to_add:
                        row['state'] = selected_state
                    
                    current_yaml_text = st.session_state.city_yaml_editor
                    current_yaml_list = yaml.safe_load(current_yaml_text) or []
                    current_yaml_list.extend(rows_to_add)
                    st.session_state.cities_yaml_string = yaml.dump(current_yaml_list, default_flow_style=False, sort_keys=False, indent=2)
                    
                    del st.session_state.station_results
                    st.rerun()

        st.subheader("Manage Monitored Cities")
        st.info("Edit the city configurations below in YAML format. You can add, remove, or modify cities.")
        config, _, _ = load_configuration()
        if config:
            if 'cities_yaml_string' not in st.session_state:
                current_cities_list = config.get('cities', [])
                st.session_state.cities_yaml_string = yaml.dump(current_cities_list, default_flow_style=False, sort_keys=False, indent=2)

            edited_yaml = st.text_area(
                "City Configuration (YAML)",
                value=st.session_state.cities_yaml_string,
                height=400,
                key="city_yaml_editor"
            )

            if st.button("💾 Save Configuration", key="modal_save_refresh"):
                try:
                    new_cities_list = yaml.safe_load(edited_yaml)
                    if save_configuration(new_cities_list):
                        st.success("Configuration saved successfully! Use the 'Refresh Data' tool in the sidebar to fetch data for the new configuration.")
                        time.sleep(2)
                        st.rerun()
                except yaml.YAMLError as e:
                    st.error(f"Error parsing YAML. Please check your formatting.\nDetails: {e}")
        else:
            st.error("Could not load config.yaml. Cannot display city management tool.")


    if not display_df.empty:
        num_cities = display_df['city'].nunique()

        duration_days = (end_date - start_date).days + 1
        duration_text = f"{duration_days} day" if duration_days == 1 else f"{duration_days} days"

        avg_max_temp = display_df['TMAX_F'].mean()
        avg_min_temp = display_df['TMIN_F'].mean()

        avg_energy = display_df['energy_mwh'].mean()

        if selected_city == 'All Cities':
            location_label = "Locations Analyzed"
            location_value = f"{num_cities} Cities"
        else:
            location_label = "Location Analyzed"
            location_value = selected_city

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(label=location_label, value=location_value)
        col2.metric(label="Analysis Duration", value=duration_text)
        col3.metric(label="Avg. Max Temp", value=f"{avg_max_temp:.1f} °F" if pd.notna(avg_max_temp) else "N/A")
        col4.metric(label="Avg. Min Temp", value=f"{avg_min_temp:.1f} °F" if pd.notna(avg_min_temp) else "N/A")
        col5.metric(label="Avg. Daily Energy", value=f"{avg_energy:,.0f} MWh" if pd.notna(avg_energy) else "N/A")
    else:
        st.warning("No data available for the selected filters to display key metrics.")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📍 Geographic Overview", "📈 Time Series Analysis", "🔗 Correlation Analysis", "🗓️ Usage Patterns", "⚠️ Data Quality Report"])

    with tab1:
        display_geographic_overview(df_date_filtered, 'temp_for_analysis', temp_axis_label, selected_city)
    
    with tab2:
        display_time_series(display_df, 'temp_for_analysis', temp_axis_label, selected_city)

    with tab3:
        display_correlation_analysis(display_df, 'temp_for_analysis', temp_axis_label)
    
    with tab4:
        display_usage_patterns_heatmap(display_df, 'temp_for_analysis', temp_axis_label, selected_city)

    with tab5:
        display_data_quality_report()

def display_geographic_overview(df, temp_col, temp_label, selected_city):
    st.header("Geographic Overview")
    if df.empty:
        st.info("Select one or more cities to display the geographic overview.")
        return
        
    latest_data_all_cities = df.sort_values('date').loc[df.groupby('city')['date'].idxmax()].copy()

    previous_day_date = latest_data_all_cities['date'].min() - pd.Timedelta(days=1)
    previous_day_data = df[df['date'] == previous_day_date][['city', 'energy_mwh']].rename(columns={'energy_mwh': 'energy_prev_day'})

    if not previous_day_data.empty:
        map_data = pd.merge(latest_data_all_cities, previous_day_data, on='city', how='left')
        map_data['energy_pct_change'] = ((map_data['energy_mwh'] - map_data['energy_prev_day']) / map_data['energy_prev_day']) * 100
    else:
        map_data = latest_data_all_cities.copy()
        map_data['energy_pct_change'] = pd.NA


    color_range_min = map_data['energy_mwh'].min()
    color_range_max = map_data['energy_mwh'].max()

    if selected_city != 'All Cities':
        map_data = map_data[map_data['city'] == selected_city].copy()

    if 'latitude' not in map_data.columns or map_data['latitude'].isnull().all():
        st.warning("City coordinates are missing. Cannot display map. Please check `config.yaml`.")
        return

    map_data.dropna(subset=['latitude', 'longitude', temp_col], inplace=True)

    if map_data.empty:
        st.warning("No data with coordinates and temperature available to display for the selection.")
        return

    map_data['size_for_map'] = map_data['energy_mwh'].fillna(1000)
    map_data['hover_energy_text'] = map_data['energy_mwh'].apply(
        lambda x: f"{x:,.0f} MWh" if pd.notna(x) else "Energy data not available"
    )
    map_data['hover_pct_change_text'] = map_data['energy_pct_change'].apply(
        lambda x: f"{x:+.1f}% vs yesterday" if pd.notna(x) else "No prior day data"
    )

    fig = px.scatter_map(
        map_data,
        lat="latitude", lon="longitude", size="size_for_map", color="energy_mwh", hover_name="city",
        custom_data=[temp_col, 'hover_energy_text', 'hover_pct_change_text'],
        color_continuous_scale="RdYlGn_r", size_max=50, zoom=3, map_style="carto-positron",
        range_color=[color_range_min, color_range_max]
    )

    fig.update_traces(hovertemplate=
        f'<b>%{{hovertext}}</b><br>' +
        f'Latest {temp_label}: %{{customdata[0]:.1f}}°F<br>' +
        'Latest Energy Usage: %{customdata[1]}<br>' +
        '% Change: %{customdata[2]}<extra></extra>'
    )
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        coloraxis_colorbar_title_text='Energy (MWh)'
    )

    st.plotly_chart(fig, use_container_width=True)

def display_time_series(df, temp_col, temp_label, selected_city):
    st.header("Time Series Analysis")
    if df.empty:
        st.info("Select one or more cities to see the time series analysis.")
        return

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if selected_city == 'All Cities':
        title = "Temperature and Energy Demand Comparison"
        for city_name in df['city'].unique():
            city_df = df[df['city'] == city_name]
            fig.add_trace(
                go.Scatter(x=city_df['date'], y=city_df[temp_col], name=f"{city_name} ({temp_label.split(' ')[0]})", mode='lines'),
                secondary_y=False,
            )
        
        total_energy_df = df.groupby('date')['energy_mwh'].sum().reset_index()
        fig.add_trace(
            go.Scatter(x=total_energy_df['date'], y=total_energy_df['energy_mwh'], name='Total Energy (MWh)', line=dict(color='rgba(135, 206, 250, 0.6)', dash='dot', width=3)),
            secondary_y=True,
        )
    else:
        title = f"Temperature and Energy Demand for {selected_city}"
        plot_df = df.copy()
        fig.add_trace(
            go.Scatter(
                x=plot_df['date'], y=plot_df[temp_col], name=temp_label,
                mode='lines', line=dict(color='rgba(255, 165, 0, 0.8)')
            ),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=plot_df['date'], y=plot_df['energy_mwh'], name='Energy (MWh)', line=dict(color='skyblue', dash='dot')),
            secondary_y=True
        )

    weekends_df = df[df['date'].dt.weekday >= 5]
    for d in weekends_df['date'].unique():
        fig.add_vrect(
            x0=pd.to_datetime(d) - pd.Timedelta(hours=12),
            x1=pd.to_datetime(d) + pd.Timedelta(hours=12),
            fillcolor="rgba(211, 211, 211, 0.25)",
            layer="below",
            line_width=0,
        )

    fig.update_layout(
        title_text=title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    fig.update_yaxes(title_text=temp_label, secondary_y=False)
    fig.update_yaxes(title_text="Energy Demand (MWh)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

def display_correlation_analysis(df, temp_col, temp_label):
    st.header("Correlation Analysis")
    if df.empty:
        st.info("Select one or more cities to see the correlation analysis.")
        return
    
    plot_df = df.dropna(subset=[temp_col, 'energy_mwh']).copy()
    if plot_df.empty:
        st.warning("No overlapping temperature and energy data available for correlation analysis.")
        return

    X = sm.add_constant(plot_df[temp_col])
    y = plot_df['energy_mwh']
    model = sm.OLS(y, X).fit()
    r_squared = model.rsquared
    correlation = plot_df[temp_col].corr(plot_df['energy_mwh'])
    intercept, slope = model.params

    x_range = pd.Series([plot_df[temp_col].min(), plot_df[temp_col].max()])
    y_range = intercept + slope * x_range
    
    col1, col2 = st.columns([3, 1])

    with col1:
        fig = px.scatter(
            plot_df,
            x=temp_col,
            y="energy_mwh",
            color="city",
            title="Temperature vs. Energy Consumption"
        )
        fig.add_traces(go.Scatter(x=x_range, y=y_range, mode='lines', name='Regression Line', line=dict(color='black', dash='dash')))

        fig.update_layout(
            xaxis_title=temp_label,
            yaxis_title="Energy Demand (MWh)",
            margin=dict(l=40, r=10, t=40, b=40),
            legend_title_text='City'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric(label="R-squared", value=f"{r_squared:.3f}")
        st.metric(label="Correlation Coefficient (r)", value=f"{correlation:.3f}")
        st.markdown(f"**Regression Equation:**")
        st.latex(f"Energy = {intercept:,.0f} + ({slope:,.2f} \\times Temp)")
        st.info("""
        **R-squared:** The proportion of the variance in energy demand that is predictable from the temperature.
        **Correlation (r):** Measures the strength and direction of the linear relationship.
        """)

def display_usage_patterns_heatmap(df, temp_col, temp_label, selected_city):
    st.header("Usage Patterns Heatmap")
    if df.empty:
        st.info("Select one or more cities to see the usage patterns heatmap.")
        return

    if selected_city == 'All Cities':
        title = "Average Daily Energy Demand for All Cities (Aggregated)"
    else:
        title = f"Average Daily Energy Demand for {selected_city}"
    plot_df = df.copy()

    plot_df['day_of_week'] = plot_df['date'].dt.day_name()
    
    bins = [-float('inf'), 50, 60, 70, 80, 90, float('inf')]
    labels = [
        "<50°F",
        "50-60°F",
        "60-70°F",
        "70-80°F",
        "80-90°F",
        ">90°F"
    ]
    plot_df['temp_bin'] = pd.cut(plot_df[temp_col], bins=bins, labels=labels, right=False)

    heatmap_data = plot_df.pivot_table(
        values='energy_mwh',
        index='temp_bin',
        columns='day_of_week',
        aggfunc='mean',
        observed=False
    ).round(0)

    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(columns=days_order)
    heatmap_data = heatmap_data.reindex(index=labels)

    fig = px.imshow(
        heatmap_data,
        text_auto=True,
        aspect="auto",
        labels=dict(x="Day of Week", y="Temperature Range", color="Avg. Energy (MWh)"),
        title=title
    )
    fig.update_layout(margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

def display_data_quality_report():
    st.header("Data Quality Report")
    st.write("This report shows any warnings or issues detected during the last data processing run.")

    project_root = os.path.join(os.path.dirname(__file__), '..')
    report_path = os.path.join(project_root, 'data', 'output', 'data_quality_report.json')

    if not os.path.exists(report_path):
        st.info("Data quality report not found. Please run the pipeline to generate it.")
        return

    try:
        with open(report_path, 'r') as f:
            warnings = json.load(f)
        
        if not warnings:
            st.success("✅ No data quality issues were found in the last pipeline run. Great job!")
            return

        st.warning(f"Found {len(warnings)} data quality issue(s).")
        
        warnings_df = pd.DataFrame(warnings)
        
        display_cols = ['level', 'check', 'message', 'file']
        st.dataframe(warnings_df[display_cols], use_container_width=True)

        with st.expander("View Detailed Report (JSON)"):
            st.json(warnings)

    except (json.JSONDecodeError, FileNotFoundError):
        st.error("Could not parse the data quality report. The JSON file may be corrupted or missing.")

if __name__ == "__main__":
    main()