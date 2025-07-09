import os
import json
from datetime import datetime
import time
from config_loader import load_configuration
from noaa_fetcher import fetch_noaa_data
from eia_fetcher import fetch_eia_data
from data_processor import process_noaa_data, process_eia_data, merge_and_save_data, combine_processed_data

def fetch_and_save_noaa_data(city, noaa_base_url, noaa_token, full_raw_data_path, start_date, end_date):
    """Fetches and saves NOAA weather data for a given city."""
    city_name = city['name']
    station_id = city['noaa_station_id']
    print(f"\nFetching NOAA data for {city_name} (Station: {station_id})...")

    weather_data = fetch_noaa_data(noaa_base_url, noaa_token, station_id, start_date, end_date, city_name=city_name)

    if weather_data and 'results' in weather_data:
        filename = os.path.join(full_raw_data_path, f"noaa_{city_name.lower().replace(' ', '_')}_{start_date}_to_{end_date}.json")
        with open(filename, 'w') as f:
            json.dump(weather_data['results'], f, indent=4)
        print(f"Successfully fetched and saved {len(weather_data['results'])} records to {filename}")
        return filename
    else:
        print(f"Failed to fetch or no NOAA data returned for {city_name}.")
        return None

def fetch_and_save_eia_data(city, eia_base_url, eia_api_key, full_raw_data_path, start_date, end_date):
    """Fetches and saves EIA energy data for a given city."""
    city_name = city['name']
    eia_ba_code = city.get('eia_ba_code')
    
    if not eia_ba_code:
        print(f"Skipping EIA data for {city_name}: no 'eia_ba_code' in config.")
        return

    print(f"Fetching EIA data for {city_name} (Balancing Authority: {eia_ba_code})...")
    energy_data = fetch_eia_data(eia_base_url, eia_api_key, eia_ba_code, start_date, end_date, city_name=city_name)

    if energy_data:
        filename = os.path.join(full_raw_data_path, f"eia_{city_name.lower().replace(' ', '_')}_{start_date}_to_{end_date}.json")
        with open(filename, 'w') as f:
            json.dump(energy_data, f, indent=4)
        print(f"Successfully fetched and saved {len(energy_data)} records to {filename}")
        return filename
    else:
        print(f"Failed to fetch or no EIA data returned for {city_name}.")
        return None

def _setup_pipeline_parameters(config):
    """
    Validates and extracts necessary parameters from the configuration object.

    Args:
        config (dict): The configuration dictionary loaded from config.yaml.

    Returns:
        dict: A dictionary of validated parameters, or None if validation fails.
    """
    # 2. Define Parameters
    api_endpoints = config.get('api_endpoints', {})
    noaa_base_url = api_endpoints.get('noaa_base_url')
    eia_base_url = api_endpoints.get('eia_base_url')
    cities = config.get('cities', [])
    
    if not all([noaa_base_url, eia_base_url]):
        print("One or more API base URLs are missing in config.yaml. Exiting.")
        return None

    # Construct absolute path for the data directory
    project_root = os.path.dirname(os.path.dirname(__file__))
    raw_data_path = config.get('data_paths', {}).get('raw_data_dir', 'data/raw')
    processed_data_path = config.get('data_paths', {}).get('processed_data_dir', 'data/processed')
    output_data_path = config.get('data_paths', {}).get('output_data_dir', 'data/output')
    full_raw_data_path = os.path.join(project_root, raw_data_path)
    full_processed_data_path = os.path.join(project_root, processed_data_path)
    full_output_data_path = os.path.join(project_root, output_data_path)
    os.makedirs(full_raw_data_path, exist_ok=True)
    os.makedirs(full_processed_data_path, exist_ok=True)
    os.makedirs(full_output_data_path, exist_ok=True)

    # Define a date range for the data fetch
    date_config = config.get('date_range', {})
    start_date = date_config.get('start_date')
    end_date = date_config.get('end_date')

    if not all([start_date, end_date]):
        print("start_date or end_date is missing in config.yaml. Exiting.")
        return None
    
    return {
        "noaa_base_url": noaa_base_url, "eia_base_url": eia_base_url, "cities": cities,
        "full_raw_data_path": full_raw_data_path, "full_processed_data_path": full_processed_data_path,
        "full_output_data_path": full_output_data_path,
        "start_date": start_date, "end_date": end_date
    }

def main():
    """Main function to orchestrate the data fetching process."""
    print("--- Starting Data Fetching Process ---")

    # 1. Load Configuration
    config, noaa_token, eia_api_key = load_configuration()

    if not config:
        print("Could not load configuration file. Exiting.")
        return
    
    if not all([noaa_token, eia_api_key]):
        print("Could not load configuration or API keys. Exiting.")
        return

    print("Configuration and API keys loaded successfully.")

    # 2. Setup pipeline parameters from config
    params = _setup_pipeline_parameters(config)
    if not params:
        return

    # 3. Fetch Data for Each City
    for city in params["cities"]:
        # Validate that the city entry has all the required keys before processing
        required_keys = ['name', 'noaa_station_id', 'eia_ba_code']
        if not all(key in city for key in required_keys):
            print(f"\nSkipping an entry due to missing keys. Found: {list(city.keys())}. Required: {required_keys}")
            continue

        # Step 1: Fetch raw data
        noaa_file = fetch_and_save_noaa_data(city, params["noaa_base_url"], noaa_token, params["full_raw_data_path"], params["start_date"], params["end_date"])
        eia_file = fetch_and_save_eia_data(city, params["eia_base_url"], eia_api_key, params["full_raw_data_path"], params["start_date"], params["end_date"])

        # Step 2: Process any available data
        print(f"\nProcessing available data for {city['name']}...")

        # Process each file if it exists, otherwise the result is None
        weather_df = process_noaa_data(noaa_file) if noaa_file else None
        energy_df = process_eia_data(eia_file) if eia_file else None

        # Step 3: Merge and/or save the processed data
        merge_and_save_data(weather_df, energy_df, city['name'], params["full_processed_data_path"])

        # Be a good API citizen: wait 1 second between requests to avoid rate-limiting.
        time.sleep(1)

    # Step 4: Combine all processed files into a master file
    combine_processed_data(params["full_processed_data_path"], params["full_output_data_path"])

    print("\n--- All Processes Finished ---")

if __name__ == "__main__":
    main()
