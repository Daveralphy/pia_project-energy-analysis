import streamlit as st
import requests
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential
import json
import os

# This function implements the Ray-Casting algorithm to determine if a point is inside a polygon.
def _point_in_polygon(x, y, polygon_ring):
    """
    Determines if a point (x, y) is inside a polygon ring.

    Args:
        x (float): The longitude of the point.
        y (float): The latitude of the point.
        polygon_ring (list): A list of [lon, lat] pairs defining the polygon.

    Returns:
        bool: True if the point is inside the polygon, False otherwise.
    """
    n = len(polygon_ring)
    inside = False
    p1x, p1y = polygon_ring[0]
    for i in range(n + 1):
        p2x, p2y = polygon_ring[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        xinters = x # Assign a value to xinters if points are horizontal
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

class EiaRegionMapper:
    """
    A class to find the EIA Balancing Authority (BA) for a given geographic coordinate.
    It loads pre-processed GeoJSON data of BA regions and uses a point-in-polygon
    algorithm to perform the mapping.
    """
    _instance = None
    _regions_data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EiaRegionMapper, cls).__new__(cls)
            cls._instance._load_regions()
        return cls._instance

    def _load_regions(self):
        """Loads the BA regions from the bundled JSON file with robust error handling."""
        if self._regions_data is None:
            file_path = os.path.join(os.path.dirname(__file__), 'eia_ba_regions.json')
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._regions_data = json.load(f)
            except FileNotFoundError:
                st.error(
                    "**Critical Error:** The `eia_ba_regions.json` file is missing from the `dashboards/` directory. "
                    "Please see the instructions to download this required file.", icon="🚨"
                )
                self._regions_data = {"features": []}
            except json.JSONDecodeError as e:
                st.error(f"Error decoding `eia_ba_regions.json`. The file may be corrupt. Error: {e}", icon="🚨")
                self._regions_data = {"features": []}

    def find_ba_for_location(self, latitude, longitude):
        """
        Finds the BA code for a given latitude and longitude.
        """
        if not self._regions_data or not self._regions_data.get("features"):
            return 'N/A'

        if pd.isna(latitude) or pd.isna(longitude):
            return 'N/A'

        for feature in self._regions_data['features']:
            geom = feature.get('geometry', {})
            props = feature.get('properties', {})
            if geom.get('type') == 'Polygon':
                for ring in geom.get('coordinates', []):
                    if _point_in_polygon(longitude, latitude, ring):
                        return props.get('ba_code', 'N/A')
            elif geom.get('type') == 'MultiPolygon':
                for polygon in geom.get('coordinates', []):
                    for ring in polygon:
                        if _point_in_polygon(longitude, latitude, ring):
                            return props.get('ba_code', 'N/A')
        return 'N/A'

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
            mapper = EiaRegionMapper()
            
            # Select and rename columns for clarity
            df = pd.DataFrame(results)[['id', 'name', 'latitude', 'longitude']]
            df.rename(columns={'id': 'noaa_station_id'}, inplace=True)
            
            # Automatically find the EIA BA code for each station using its coordinates.
            # This can take a moment, so the spinner is helpful.
            with st.spinner("Mapping stations to energy regions..."):
                df['eia_ba_code'] = df.apply(
                    lambda row: mapper.find_ba_for_location(row['latitude'], row['longitude']),
                    axis=1
                )
            
            # Reorder columns for the final display
            display_cols = ['name', 'noaa_station_id', 'eia_ba_code', 'latitude', 'longitude']
            st.info("The table below shows NOAA stations for the selected state with their automatically-detected EIA region code. Stations with 'N/A' may be outside a defined energy region.")
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.info(f"No stations found for {state_name}.")
    except Exception as e:
        st.error(f"Failed to fetch stations from NOAA API: {e}")