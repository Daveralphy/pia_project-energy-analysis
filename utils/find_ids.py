import requests
import os
from dotenv import load_dotenv
import json

def find_noaa_stations():
    """Helper function to find NOAA station IDs for a given state."""
    load_dotenv()
    noaa_token = os.getenv("NOAA_TOKEN")
    if not noaa_token:
        print("Error: NOAA_TOKEN not found in .env file.")
        return

    print("\n--- NOAA Station ID Finder ---")
    print("This tool helps find NOAA station IDs from the GHCND (Daily Summaries) dataset.")
    
    state_fips = {
        'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08', 'CT': '09', 'DE': '10', 'FL': '12', 'GA': '13',
        'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18', 'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23', 'MD': '24',
        'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33', 'NJ': '34',
        'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39', 'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45',
        'SD': '46', 'TN': '47', 'TX': '48', 'UT': '49', 'VT': '50', 'VA': '51', 'WA': '52', 'WV': '54', 'WI': '55', 'WY': '56'
    }

    state_abbr = input("Enter the 2-letter state abbreviation (e.g., CA, NY, TX): ").upper()
    if state_abbr not in state_fips:
        print("Invalid state abbreviation.")
        return

    location_id = f"FIPS:{state_fips[state_abbr]}"
    url = f"https://www.ncei.noaa.gov/cdo-web/api/v2/stations?locationid={location_id}&datasetid=GHCND&limit=1000"
    headers = {'token': noaa_token}

    print(f"Searching for stations in {state_abbr}...")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        stations = response.json().get('results', [])
        
        if not stations:
            print("No stations found for this state and dataset.")
            return

        search_term = input("Enter a city name or keyword to filter results (e.g., 'International Airport', 'Chicago'): ").lower()
        
        found_stations = []
        for station in stations:
            if search_term in station.get('name', '').lower():
                found_stations.append(station)
        
        if not found_stations:
            print(f"No stations matched the keyword '{search_term}'. Try a broader search.")
        else:
            print("\n--- Found Matching Stations ---")
            for station in found_stations:
                print(f"  Name: {station.get('name')}, ID: {station.get('id')}")
            print("\nCopy the desired ID (e.g., 'GHCND:USW00094728') into your config.yaml file.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def find_eia_ba_codes():
    """Helper function to find EIA Balancing Authority codes."""
    print("\n--- EIA Balancing Authority (BA) Code Finder ---")
    print("Fetching a list of all available BAs from the EIA API. This may take a moment...")

    # We can discover BAs by making a generic call and extracting the 'respondent' facet
    url = "https://api.eia.gov/v2/electricity/rto/daily-region-data/data/"
    load_dotenv()
    eia_api_key = os.getenv("EIA_API_KEY")
    if not eia_api_key:
        print("Error: EIA_API_KEY not found in .env file.")
        return

    params = {'api_key': eia_api_key, 'frequency': 'daily', 'data[0]': 'value', 'facets[respondent][]': 'ALL'}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        facets = response.json().get('response', {}).get('facets', {})
        respondents = facets.get('respondent', [])

        if not respondents:
            print("Could not retrieve the list of Balancing Authorities from EIA.")
            return

        search_term = input("Enter a state, company, or region to search for (e.g., 'California', 'PJM', 'England'): ").lower()
        
        found_bas = []
        for ba in respondents:
            if search_term in ba.get('name', '').lower():
                found_bas.append(ba)

        if not found_bas:
            print(f"No BAs matched the keyword '{search_term}'.")
        else:
            print("\n--- Found Matching Balancing Authorities ---")
            for ba in found_bas:
                print(f"  Name: {ba.get('name')}, Code: {ba.get('id')}")
            print("\nCopy the desired Code (e.g., 'CISO', 'NYIS') into your config.yaml file.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def main():
    """Main menu for the ID finder utility."""
    while True:
        print("\n--- City ID Finder Utility ---")
        print("1. Find NOAA Station ID")
        print("2. Find EIA Balancing Authority (BA) Code")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ")

        if choice == '1':
            find_noaa_stations()
        elif choice == '2':
            find_eia_ba_codes()
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
