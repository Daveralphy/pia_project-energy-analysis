import streamlit as st
import requests
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential
from dashboards.city_to_ba_mapper import CityToBaMapper, STATE_FIPS

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