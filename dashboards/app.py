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
from tenacity import retry, stop_after_attempt, wait_exponential
import requests

# --- Path Setup ---
# This must be at the top to ensure all project-level imports work correctly.
project_root_for_imports = os.path.join(os.path.dirname(__file__), '..')
if project_root_for_imports not in sys.path:
    sys.path.insert(0, project_root_for_imports)

# --- Project-specific Imports ---
from pia_project_energy_analysis.config_loader import load_configuration

# --- START: Consolidated Helper Logic ---
# This logic is moved from station_finder.py and city_to_ba_mapper.py to resolve import errors.

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
    """Finds NOAA stations and returns them as a DataFrame, or None on failure."""
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
            
            # Filter for major stations (typically at airports, ID starts with 'USW')
            # These are more reliable for TMAX/TMIN data.
            major_stations_df = df[df['id'].str.startswith('GHCND:USW')].copy()

            if not major_stations_df.empty:
                st.success(f"Found {len(major_stations_df)} major weather stations. These are recommended for analysis.")
                # Process and return only the major stations
                major_stations_df = major_stations_df[['id', 'name', 'latitude', 'longitude']]
                major_stations_df.rename(columns={'id': 'noaa_station_id'}, inplace=True)
                return major_stations_df
            else:
                # If no major stations, warn the user and show all available stations
                st.warning(f"No major weather stations found for {state_name}. The smaller stations listed below may not have the required temperature data.", icon="⚠️")
                all_stations_df = df[['id', 'name', 'latitude', 'longitude']]
                all_stations_df.rename(columns={'id': 'noaa_station_id'}, inplace=True)
                return all_stations_df
        else:
            st.info(f"No stations found for {state_name}.")
            return None
    except Exception as e:
        st.error(f"Failed to fetch stations from NOAA API: {e}")
        return None

# --- END: Consolidated Helper Logic ---

@st.cache_data
def load_data():
    """Loads the master data file from the output directory."""
    # Construct the path relative to the script's location
    # This makes it runnable from the project root (streamlit run dashboards/app.py)
    project_root = os.path.join(os.path.dirname(__file__), '..')
    data_path = os.path.join(project_root, 'data', 'output', 'master_energy_weather_data.csv')
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    
    if not os.path.exists(data_path):
        st.error(f"Master data file not found at `{data_path}`.")
        st.warning("The master data file is missing. Please run the main application to generate it. From your project root, execute:")
        st.code("python run.py")
        st.stop() # Halt execution and display the messages

    # Load master data
    try:
        df = pd.read_csv(data_path)
        df['date'] = pd.to_datetime(df['date'])
    except Exception as e:
        st.error(f"An error occurred while loading or parsing the data file: {e}")
        st.stop()

    # Load city coordinates from config.yaml to merge into the dataframe
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        cities_info = {city['name']: {'latitude': city['latitude'], 'longitude': city['longitude']} for city in config.get('cities', [])}
        
        # Map the coordinates to the dataframe
        df['latitude'] = df['city'].map(lambda x: cities_info.get(x, {}).get('latitude'))
        df['longitude'] = df['city'].map(lambda x: cities_info.get(x, {}).get('longitude'))
        
        return df

    except (FileNotFoundError, yaml.YAMLError) as e:
        st.warning(f"Could not load city coordinates from config file: {e}")
        return df # Return dataframe without coordinates

def convert_df_to_csv(df):
    """Converts a DataFrame to a CSV string for download."""
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    # In a more complex app, you might use @st.cache_data here.
    return df.to_csv(index=False).encode('utf-8')

def apply_compact_style():
    """Applies custom CSS to make the dashboard more compact."""
    st.markdown("""
        <style>
            /* Reduce padding of the main page to make it more compact */
            .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            /* Reduce padding in the sidebar */
            [data-testid="stSidebar"] > div:first-child {
                padding-top: 1.5rem;
            }
            /* Reduce the gap between streamlit elements */
            [data-testid="stVerticalBlock"] > [style*="gap"] {
                gap: 0.1rem; /* Drastically reduce vertical spacing */
            }
            /* Increase font size for tab labels */
            button[data-testid="stTab"] {
                font-size: 1.2rem; /* Increased font size for tabs */
                font-weight: 600;
            }
            /* Reduce font size for titles and headers */
            h1 { font-size: 2.2rem !important; margin-bottom: 0rem !important; }
            h2 { font-size: 1.6rem !important; }
            h3 { font-size: 1.3rem !important; }
            /* Standardize font size for KPI Metric Labels for consistency */
            [data-testid="stMetricLabel"] {
                font-size: 1rem !important;
                font-weight: 600 !important;
            }
        </style>
    """, unsafe_allow_html=True)

def run_pipeline_from_dashboard():
    """Executes the main data pipeline and streams its output to the dashboard."""
    log_area = st.empty()
    log_content = "--- Starting Data Pipeline ---\n"
    log_area.code(log_content, language='log')

    # Construct the path to run.py and the project root
    project_root = os.path.join(os.path.dirname(__file__), '..')
    run_script_path = os.path.join(project_root, 'run.py')

    # Use Popen to capture output in real-time
    # We run the script from the project_root directory to ensure all paths inside it resolve correctly
    process = subprocess.Popen(
        [sys.executable, run_script_path, '--pipeline-only'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=project_root,
        encoding='utf-8',
        errors='replace'
    )

    # Read and display output line by line
    for line in iter(process.stdout.readline, ''):
        log_content += line
        log_area.code(log_content, language='log')
    
    process.stdout.close()
    process.wait()
    log_area.code(log_content, language='log') # Display final content

def save_configuration(new_cities_list):
    """Reads the existing config, replaces the cities list, and writes it back."""
    project_root = os.path.join(os.path.dirname(__file__), '..')
    config_path = os.path.join(project_root, 'config', 'config.yaml')

    try:
        with open(config_path, 'r') as f:
            full_config = yaml.safe_load(f)

        # Validate and sanitize the list of cities from the user input
        if not isinstance(new_cities_list, list):
            st.error("Configuration must be a list of cities in valid YAML format.")
            return False

        for city in new_cities_list:
            # Ensure latitude and longitude are correctly typed as floats
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
    """Main function to run the Streamlit dashboard."""
    st.set_page_config(page_title="Energy & Weather Analysis", layout="wide")
    apply_compact_style()
    
    master_df = load_data()

    # --- Sidebar for Global Controls ---
    with st.sidebar:
        st.title("Analysis Options")
        
        temp_metric = st.radio(
            "Select Temperature Metric",
            ('Max Temperature (TMAX)', 'Min Temperature (TMIN)', 'Average Temperature'),
            key='temp_metric_selector'
        )

        # Add date input dropdowns for start and end dates
        if not master_df.empty:
            min_date = master_df['date'].min().date()
            max_date = master_df['date'].max().date()

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date, key='start_date')
            with col2:
                end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date, key='end_date')
            
            # Validate that the start date is not after the end date
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
        
        # Placeholder for the download button. It will be populated after the data is filtered.
        download_button_placeholder = st.empty()

        # --- Data Management Section ---
        st.markdown("---")
        st.header("Manage Data")

        with st.expander("Refresh Data", expanded=False):
            st.info("This will re-run the entire data pipeline to fetch the latest data for all configured cities. This may take several minutes.")
            if st.button("🔄 Refresh All Data"):
                with st.spinner("Pipeline is running... see logs below."):
                    run_pipeline_from_dashboard()
                st.success("Pipeline finished! Reloading dashboard with new data...")
                st.cache_data.clear() # Clear the data cache to force reload
                time.sleep(3)
                st.rerun()

        # Replace the button/dialog with a popover for better compatibility and UI
        with st.popover("⚙️ Edit Configuration", use_container_width=True):
            st.header("Configuration & Data Management")
            st.write("Here you can manage the list of cities for analysis and find the necessary IDs.")

            # --- Section 1: Find IDs ---
            with st.expander("🔎 Find City IDs"):
                st.subheader("Find Required IDs for a City")
                st.info("To add a new city, you need its **NOAA Station ID** and its **EIA Balancing Authority Code**. Use this tool to find them.")

                selected_state = st.selectbox("Select a U.S. State to find its stations and energy regions:", options=sorted(STATE_FIPS.keys()), key="modal_state_select", index=None, placeholder="Choose a state...")
                
                if selected_state:
                    if st.button(f"Find Available IDs for {selected_state}", key="modal_find_stations"):
                        # Store search results in session state to persist them across reruns
                        _, noaa_token, _ = load_configuration()
                        st.session_state.station_results = find_noaa_stations(selected_state, noaa_token)

                # If search results exist in the session state, display the interactive editor
                if 'station_results' in st.session_state and st.session_state.station_results is not None:
                    st.markdown("---")
                    st.markdown("##### Step 2: Select Stations to Add")
                    st.info("Check the 'Add' box for stations you want to include. You can edit the city name for clarity.")
                    
                    results_df = st.session_state.station_results.copy()
                    mapper = CityToBaMapper()
                    
                    # Automatically find the BA code and add it to the dataframe
                    mapping_results = results_df.apply(lambda row: mapper.find_ba_for_station(row['name'], selected_state), axis=1)
                    results_df[['eia_ba_code', 'match_type']] = pd.DataFrame(mapping_results.tolist(), index=results_df.index)
                    
                    # Add the 'Add' column for user selection
                    results_df.insert(0, 'Add', False)

                    # Display the interactive data editor
                    edited_stations_df = st.data_editor(
                        results_df[['Add', 'name', 'noaa_station_id', 'eia_ba_code', 'latitude', 'longitude']],
                        column_config={"name": st.column_config.TextColumn("City Name (Editable)")},
                        use_container_width=True,
                        key="station_selector_editor"
                    )

                    if st.button("Add Selected to Configuration"):
                        selected_rows = edited_stations_df[edited_stations_df['Add']]
                        if not selected_rows.empty:
                            # Prepare the selected data for YAML conversion
                            rows_to_add = selected_rows.drop(columns=['Add']).to_dict('records')
                            for row in rows_to_add:
                                row['state'] = selected_state
                            
                            # Append to the current YAML in the text area
                            current_yaml_list = yaml.safe_load(st.session_state.get('cities_yaml_string', '[]')) or []
                            current_yaml_list.extend(rows_to_add)
                            st.session_state.cities_yaml_string = yaml.dump(current_yaml_list, default_flow_style=False, sort_keys=False, indent=2)
                            
                            # Clear the search results and rerun to update the UI
                            del st.session_state.station_results
                            st.rerun()

            # --- Section 2: Manage Cities ---
            st.subheader("Manage Monitored Cities")
            st.info("Edit the city configurations below in YAML format. You can add, remove, or modify cities.")
            config, _, _ = load_configuration()
            if config:
                # Initialize session state for the YAML editor if it doesn't exist
                if 'cities_yaml_string' not in st.session_state:
                    current_cities_list = config.get('cities', [])
                    st.session_state.cities_yaml_string = yaml.dump(current_cities_list, default_flow_style=False, sort_keys=False, indent=2)

                edited_yaml = st.text_area(
                    "City Configuration (YAML)",
                    value=st.session_state.cities_yaml_string,
                    height=400,
                    key="city_yaml_editor"
                )

                if st.button("💾 Save Changes & Refresh All Data", key="modal_save_refresh"):
                    try:
                        # Parse the user's edited YAML string
                        new_cities_list = yaml.safe_load(edited_yaml)
                        if save_configuration(new_cities_list):
                            st.success("Configuration saved successfully! Now running the data pipeline...")
                            with st.spinner("Pipeline is running... see logs below."):
                                run_pipeline_from_dashboard()
                            st.success("Pipeline finished! Reloading dashboard with new data...")
                            st.cache_data.clear()
                            time.sleep(3)
                            st.rerun()
                    except yaml.YAMLError as e:
                        st.error(f"Error parsing YAML. Please check your formatting.\nDetails: {e}")
            else:
                st.error("Could not load config.yaml. Cannot display city management tool.")

    # --- Data Filtering ---
    # This section is placed after the sidebar to ensure all filter values are available.

    # 1. Filter by date
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date)
    df_date_filtered = master_df[(master_df['date'] >= start_datetime) & (master_df['date'] <= end_datetime)].copy()

    # 2. Create the temperature column for analysis
    if temp_metric == 'Max Temperature (TMAX)':
        df_date_filtered['temp_for_analysis'] = df_date_filtered['TMAX_F']
        temp_axis_label = "Max Temperature (°F)"
    elif temp_metric == 'Min Temperature (TMIN)':
        df_date_filtered['temp_for_analysis'] = df_date_filtered['TMIN_F']
        temp_axis_label = "Min Temperature (°F)"
    else:  # Average Temperature
        df_date_filtered['temp_for_analysis'] = (df_date_filtered['TMAX_F'] + df_date_filtered['TMIN_F']) / 2
        temp_axis_label = "Average Temperature (°F)"
    
    # 3. Drop rows where the analysis temp is NaN to avoid issues in plots
    df_date_filtered.dropna(subset=['temp_for_analysis'], inplace=True)

    # 4. Filter by city to create the final dataframe for display in most charts
    if selected_city == 'All Cities':
        display_df = df_date_filtered.copy()
    else:
        display_df = df_date_filtered[df_date_filtered['city'] == selected_city].copy()

    # --- Add Download Button to Sidebar (now that data is filtered) ---
    with download_button_placeholder.container():
        st.markdown("---")
        st.header("Export Data")
        
        csv = convert_df_to_csv(display_df)
        
        st.download_button(
           label="Download Filtered Data",
           data=csv,
           file_name=f"filtered_data_{start_date}_to_{end_date}_{selected_city.replace(' ', '_')}.csv",
           mime="text/csv",
        )

    # --- Main Dashboard Layout ---
    st.title("U.S. Weather and Energy Consumption Analysis")

    # --- KPI Metrics Section ---

    if not display_df.empty:
        # Calculate metrics
        num_cities = display_df['city'].nunique()

        # Duration
        duration_days = (end_date - start_date).days + 1
        duration_text = f"{duration_days} day" if duration_days == 1 else f"{duration_days} days"

        # Calculate static Avg Max and Avg Min Temp, regardless of radio button selection
        avg_max_temp = display_df['TMAX_F'].mean()
        avg_min_temp = display_df['TMIN_F'].mean()

        # Average Energy
        avg_energy = display_df['energy_mwh'].mean()

        # Location
        if selected_city == 'All Cities':
            location_label = "Locations Analyzed"
            location_value = f"{num_cities} Cities"
        else:
            location_label = "Location Analyzed"
            location_value = selected_city

        # Display metrics in 5 columns
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(label=location_label, value=location_value)
        col2.metric(label="Analysis Duration", value=duration_text)
        col3.metric(label="Avg. Max Temp", value=f"{avg_max_temp:.1f} °F" if pd.notna(avg_max_temp) else "N/A")
        col4.metric(label="Avg. Min Temp", value=f"{avg_min_temp:.1f} °F" if pd.notna(avg_min_temp) else "N/A")
        col5.metric(label="Avg. Daily Energy", value=f"{avg_energy:,.0f} MWh" if pd.notna(avg_energy) else "N/A")
    else:
        st.warning("No data available for the selected filters to display key metrics.")
    
    # Create tabs for different analysis views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📍 Geographic Overview", "📈 Time Series Analysis", "🔗 Correlation Analysis", "🗓️ Usage Patterns", "⚠️ Data Quality Report"])

    with tab1:
        # Pass the date-filtered dataframe to the map to ensure all cities are available for scaling,
        # while respecting the date filter. The function itself will handle showing only the selected city.
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
    """Displays an interactive map of the latest data for each city."""
    st.header("Geographic Overview")
    if df.empty:
        st.info("Select one or more cities to display the geographic overview.")
        return
        
    # This now operates on the FULL dataframe, ensuring consistent ranges for size and color.
    latest_data = df.loc[df.groupby('city')['date'].idxmax()]

    if 'latitude' not in latest_data.columns or latest_data['latitude'].isnull().any():
        st.warning("City coordinates are missing. Cannot display map. Please check `config.yaml`.")
        return

    # Prepare data for map, handling missing energy values gracefully
    map_data = latest_data.dropna(subset=['latitude', 'longitude', temp_col]).copy()

    if map_data.empty:
        st.warning("No data with coordinates and temperature available to display.")
        return

    # Use a small, constant size for cities with missing energy data to ensure they are still plotted.
    # Create a new column for hover text that is more informative.
    map_data['size_for_map'] = map_data['energy_mwh'].fillna(1000) # Use a small default size
    map_data['hover_energy_text'] = map_data['energy_mwh'].apply(
        lambda x: f"{x:,.0f} MWh" if pd.notna(x) else "Energy data not available"
    )

    fig = px.scatter_map( # The figure is now always created with data for ALL cities.
        map_data,
        lat="latitude",
        lon="longitude",
        size="size_for_map",
        color="city", # Use city for distinct colors instead of temperature
        hover_name="city",
        # Use explicit custom_data for a more robust hover template
        custom_data=[temp_col, 'hover_energy_text'],
        color_discrete_sequence=px.colors.qualitative.Vivid, # Use a color scale with distinct colors
        size_max=50,
        zoom=3,
        map_style="carto-positron"
    )
    # Customize the hover label for clarity
    fig.update_traces(hovertemplate=
        f'<b>%{{hovertext}}</b><br>' +
        f'{temp_label}: %{{customdata[0]:.1f}}°F<br>' +
        'Energy: %{customdata[1]}<extra></extra>'
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # If a specific city is selected, hide all other traces.
    if selected_city != 'All Cities':
        fig.update_traces(visible=False) # First, hide all traces
        fig.update_traces(visible=True, selector=dict(name=selected_city)) # Then, make only the selected one visible

    st.plotly_chart(fig, use_container_width=True)

def display_time_series(df, temp_col, temp_label, selected_city):
    """Displays the time series analysis chart."""
    st.header("Time Series Analysis")
    if df.empty:
        st.info("Select one or more cities to see the time series analysis.")
        return

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if selected_city == 'All Cities':
        title = "Temperature and Energy Demand Comparison"
        # Plot temperature for each city on the primary axis
        for city_name in df['city'].unique():
            city_df = df[df['city'] == city_name]
            fig.add_trace(
                go.Scatter(x=city_df['date'], y=city_df[temp_col], name=f"{city_name} ({temp_label.split(' ')[0]})", mode='lines'),
                secondary_y=False,
            )
        
        # Plot total aggregated energy on the secondary axis
        total_energy_df = df.groupby('date')['energy_mwh'].sum().reset_index()
        fig.add_trace(
            go.Scatter(x=total_energy_df['date'], y=total_energy_df['energy_mwh'], name='Total Energy (MWh)', line=dict(color='rgba(135, 206, 250, 0.6)', dash='dot', width=3)),
            secondary_y=True,
        )
    else:
        title = f"Temperature and Energy Demand for {selected_city}"
        plot_df = df.copy()
        # Add the selected temperature trace for the single city
        fig.add_trace(
            go.Scatter(
                x=plot_df['date'], y=plot_df[temp_col], name=temp_label,
                mode='lines', line=dict(color='rgba(255, 165, 0, 0.8)')
            ),
            secondary_y=False
        )
        # Add the energy demand trace for the single city
        fig.add_trace(
            go.Scatter(x=plot_df['date'], y=plot_df['energy_mwh'], name='Energy (MWh)', line=dict(color='skyblue', dash='dot')),
            secondary_y=True
        )

    fig.update_layout(
        title_text=title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=50, b=40) # Add compact margins
    )
    fig.update_yaxes(title_text=temp_label, secondary_y=False)
    fig.update_yaxes(title_text="Energy Demand (MWh)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

def display_correlation_analysis(df, temp_col, temp_label):
    """Displays a scatter plot to show correlation between temp and energy."""
    st.header("Correlation Analysis")
    if df.empty:
        st.info("Select one or more cities to see the correlation analysis.")
        return
    
    # Calculate overall correlation
    correlation = df[temp_col].corr(df['energy_mwh'])
    
    col1, col2 = st.columns([3, 1])

    with col1:
        fig = px.scatter(
            df,
            x=temp_col,
            y="energy_mwh",
            color="city",
            trendline="ols",
            title="Temperature vs. Energy Consumption"
        )
        fig.update_layout(
            xaxis_title=temp_label,
            yaxis_title="Energy Demand (MWh)",
            margin=dict(l=40, r=10, t=40, b=40) # Add compact margins
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric(label="Overall Correlation Coefficient", value=f"{correlation:.2f}")
        st.info("""
        **Correlation Coefficient:**
        - **+1:** Perfect positive correlation
        - **0:** No correlation
        - **-1:** Perfect negative correlation
        
        This value measures the strength and direction of the linear relationship between the selected temperature metric and energy demand.
        """)

def display_usage_patterns_heatmap(df, temp_col, temp_label, selected_city):
    """Displays a heatmap of average energy usage by day of week and temperature."""
    st.header("Usage Patterns Heatmap")
    if df.empty:
        st.info("Select one or more cities to see the usage patterns heatmap.")
        return

    if selected_city == 'All Cities':
        title = "Average Daily Energy Demand for All Cities (Aggregated)"
    else:
        title = f"Average Daily Energy Demand for {selected_city}"
    plot_df = df.copy()

    # Feature Engineering: Create day of week and temperature bins
    plot_df['day_of_week'] = plot_df['date'].dt.day_name()
    
    # Define temperature bins from -20F to 130F in 10-degree increments
    bins = list(range(-20, 131, 10))
    labels = [f"{i} to {i+9}°F" for i in bins[:-1]]
    plot_df['temp_bin'] = pd.cut(plot_df[temp_col], bins=bins, labels=labels, right=False)

    # Create pivot table for the heatmap
    heatmap_data = plot_df.pivot_table(
        values='energy_mwh',
        index='temp_bin',
        columns='day_of_week',
        aggfunc='mean',
        observed=False # Explicitly set to silence FutureWarning and maintain behavior
    ).round(0)

    # Order the columns by day of week
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(columns=days_order)

    fig = px.imshow(
        heatmap_data,
        text_auto=True, # Automatically display the values on the heatmap
        aspect="auto",
        labels=dict(x="Day of Week", y="Temperature Range", color="Avg. Energy (MWh)"),
        title=title
    )
    fig.update_layout(margin=dict(t=50, b=0, l=0, r=0)) # Add top margin for title
    st.plotly_chart(fig, use_container_width=True)

def display_data_quality_report():
    """Reads and displays the data quality report from the pipeline run."""
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
        
        # Convert to DataFrame for better display
        warnings_df = pd.DataFrame(warnings)
        
        # Reorder columns for clarity and display
        display_cols = ['level', 'check', 'message', 'file']
        st.dataframe(warnings_df[display_cols], use_container_width=True)

        with st.expander("View Detailed Report (JSON)"):
            st.json(warnings)

    except (json.JSONDecodeError, FileNotFoundError):
        st.error("Could not parse the data quality report. The JSON file may be corrupted or missing.")

if __name__ == "__main__":
    main()