import streamlit as st
import requests
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

# A mapping of US states to their FIPS codes, used for API filtering.
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

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def _make_station_request(params, headers):
    """Makes a request to the NOAA stations endpoint with retry logic."""
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
    response = requests.get(url, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()

def find_noaa_stations(state_name, noaa_token):
    """
    Finds NOAA GHCND stations for a given state and displays them.

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
            df = pd.DataFrame(results)[['id', 'name', 'latitude', 'longitude', 'mindate', 'maxdate']]
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"No stations found for {state_name}.")
    except Exception as e:
        st.error(f"Failed to fetch stations from NOAA API: {e}")