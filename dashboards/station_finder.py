import streamlit as st
import requests
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

# A curated dictionary mapping major US cities to their known EIA Balancing Authority.
# This provides fast and accurate lookups for common cities.
CITY_TO_BA_MAPPING = {
    "new york": "NYIS", "los angeles": "CISO", "chicago": "PJM", "houston": "ERCO",
    "phoenix": "AZPS", "philadelphia": "PJM", "san antonio": "ERCO", "san diego": "CISO",
    "dallas": "ERCO", "san jose": "CISO", "austin": "ERCO", "jacksonville": "JEA",
    "fort worth": "ERCO", "columbus": "PJM", "charlotte": "DUK", "san francisco": "CISO",
    "indianapolis": "MISO", "seattle": "SCL", "denver": "PSCO", "washington": "PJM",
    "boston": "ISNE", "el paso": "EPE", "detroit": "MISO", "nashville": "TVA",
    "portland": "PGE", "memphis": "TVA", "oklahoma city": "SWPP", "las vegas": "NEVP",
    "louisville": "LGEE", "baltimore": "PJM", "milwaukee": "MISO", "albuquerque": "PNM",
    "tucson": "TEPC", "fresno": "CISO", "sacramento": "CISO", "kansas city": "SWPP",
    "long beach": "CISO", "mesa": "SRP", "atlanta": "SOCO", "colorado springs": "PSCO",
    "miami": "FPL", "raleigh": "CPLE", "omaha": "MISO", "minneapolis": "MISO",
    "tulsa": "SWPP", "cleveland": "PJM", "wichita": "SWPP", "arlington": "ERCO",
    "new orleans": "MISO", "bakersfield": "CISO", "tampa": "TEC", "honolulu": "HECO",
    "aurora": "PSCO", "anaheim": "CISO", "santa ana": "CISO", "st. louis": "MISO",
    "pittsburgh": "PJM", "corpus christi": "ERCO", "riverside": "CISO", "cincinnati": "PJM",
    "lexington": "LGEE", "anchorage": "MEA", "stockton": "CISO", "toledo": "MISO",
    "saint paul": "MISO", "newark": "PJM", "greensboro": "DUK", "plano": "ERCO",
    "henderson": "NEVP", "lincoln": "MISO", "orlando": "FPC", "jersey city": "PJM",
    "chula vista": "CISO", "buffalo": "NYIS", "fort wayne": "MISO", "chandler": "SRP",
    "laredo": "ERCO", "madison": "MISO", "durham": "CPLE", "lubbock": "ERCO",
    "winston-salem": "DUK", "garland": "ERCO", "glendale": "SRP", "reno": "NEVP",
    "hialeah": "FPL", "boise": "IPCO", "scottsdale": "SRP", "irving": "ERCO",
    "chesapeake": "PJM", "north las vegas": "NEVP", "fremont": "CISO", "baton rouge": "MISO",
    "richmond": "PJM", "san bernardino": "CISO", "spokane": "AVA", "des moines": "MISO",
    "tacoma": "TPWR", "montgomery": "SOCO", "little rock": "MISO", "salt lake city": "PACE"
}

# A fallback mapping for states to their most dominant Balancing Authority.
STATE_TO_PRIMARY_BA = {
    'alabama': 'SOCO', 'alaska': 'None', 'arizona': 'AZPS', 'arkansas': 'MISO',
    'california': 'CISO', 'colorado': 'PSCO', 'connecticut': 'ISNE', 'delaware': 'PJM',
    'district of columbia': 'PJM', 'florida': 'FPL', 'georgia': 'SOCO', 'hawaii': 'HECO',
    'idaho': 'IPCO', 'illinois': 'PJM', 'indiana': 'MISO', 'iowa': 'MISO',
    'kansas': 'SWPP', 'kentucky': 'LGEE', 'louisiana': 'MISO', 'maine': 'ISNE',
    'maryland': 'PJM', 'massachusetts': 'ISNE', 'michigan': 'MISO', 'minnesota': 'MISO',
    'mississippi': 'MISO', 'missouri': 'MISO', 'montana': 'NWMT', 'nebraska': 'MISO',
    'nevada': 'NEVP', 'new hampshire': 'ISNE', 'new jersey': 'PJM', 'new mexico': 'PNM',
    'new york': 'NYIS', 'north carolina': 'DUK', 'north dakota': 'MISO', 'ohio': 'PJM',
    'oklahoma': 'SWPP', 'oregon': 'PGE', 'pennsylvania': 'PJM', 'rhode island': 'ISNE',
    'south carolina': 'SCEG', 'south dakota': 'MISO', 'tennessee': 'TVA', 'texas': 'ERCO',
    'utah': 'PACE', 'vermont': 'ISNE', 'virginia': 'PJM', 'washington': 'SCL',
    'west virginia': 'PJM', 'wisconsin': 'MISO', 'wyoming': 'PACE'
}

# A mapping of US states to their FIPS codes, used for the NOAA API.
STATE_FIPS = {
    'Alabama': '01', 'Alaska': '02', 'Arizona': '04', 'Arkansas': '05', 'California': '06', 
    'Colorado': '08', 'Connecticut': '09', 'Delaware': '10', 'District of Columbia': '11', 
    'Florida': '12', 'Georgia': '13', 'Hawaii': '15', 'Idaho': '16', 'Illinois': '17', 
    'Indiana': '18', 'Iowa': '19', 'Kansas': '20', 'Kentucky': '21', 'Louisiana': '22', 
    'Maine': '23', 'Maryland': '24', 'Massachusetts': '25', 'Michigan': '26', 'Minnesota': '27', 
    'Mississippi': '28', 'Missouri': '29', 'Montana': '30', 'Nebraska': '31', 'Nevada': '32', 
    'New Hampshire': '33', 'New Jersey': '34', 'New Mexico': '35', 'New York': '36', 
    'North Carolina': '37', 'North Dakota': '38', 'Ohio': '39', 'Oklahoma': '40', 
    'Oregon': '41', 'Pennsylvania': '42', 'Rhode Island': '44', 'South Carolina': '45', 
    'South Dakota': '46', 'Tennessee': '47', 'Texas': '48', 'Utah': '49', 'Vermont': '50', 
    'Virginia': '51', 'Washington': '52', 'West Virginia': '54', 'Wisconsin': '55', 'Wyoming': '56'
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
    """Makes a request to the NOAA stations endpoint with retry logic."""
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
    response = requests.get(url, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()

def find_noaa_stations(state_name, noaa_token):
    """
    Finds NOAA GHCND stations for a given state, automatically determines their
    EIA Balancing Authority code, and displays them in a unified table.

    Args:
        state_name (str): The name of the US state.
        noaa_token (str): The NOAA API token.
    """
    if not noaa_token:
        st.error("NOAA API token not found. Cannot search for stations. Please check your `.env` file.")
        return

    fips_code = STATE_FIPS.get(state_name)
    if not fips_code:
        st.warning(f"State '{state_name}' not found.")
        return

    headers = {'token': noaa_token}
    params = {
        'datasetid': 'GHCND',
        'locationid': f'FIPS:{fips_code}',
        'limit': 1000  # Max limit per request
    }

    try:
        with st.spinner(f"Searching for weather stations in {state_name}..."):
            data = _make_station_request(params, headers)
        results = data.get('results', [])
        if results:
            mapper = CityToBaMapper()
            
            # Select and rename columns for clarity
            df = pd.DataFrame(results)[['id', 'name', 'latitude', 'longitude']]
            df.rename(columns={'id': 'noaa_station_id'}, inplace=True)
            
            # Automatically find the EIA BA code for each station using the new mapping logic.
            # This is much faster and doesn't require a spinner.
            mapping_results = df.apply(
                lambda row: mapper.find_ba_for_station(row['name'], state_name),
                axis=1
            )
            df[['eia_ba_code', 'match_type']] = pd.DataFrame(mapping_results.tolist(), index=df.index)
            
            # Reorder columns for the final display
            display_cols = ['name', 'noaa_station_id', 'eia_ba_code', 'match_type', 'latitude', 'longitude']
            st.info("The table below shows NOAA stations for the selected state with their estimated EIA region code.")
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.info(f"No stations found for {state_name}.")
    except Exception as e:
        st.error(f"Failed to fetch stations from NOAA API: {e}")