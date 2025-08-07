import os
import json
from datetime import datetime, timedelta
import time
import argparse
import logging
from .config_loader import load_configuration
from .noaa_fetcher import fetch_noaa_data
from .eia_fetcher import fetch_eia_data
from .data_processor import process_noaa_data, process_eia_data, merge_and_save_data, combine_processed_data
 
def fetch_and_save_noaa_data(city, noaa_base_url, noaa_token, full_raw_data_path, start_date, end_date):
    """Fetches and saves NOAA weather data for a given city."""
    city_name = city['name']
    station_id = city['noaa_station_id']
    logging.info(f"Fetching NOAA data for {city_name} (Station: {station_id})...")

    weather_data = fetch_noaa_data(noaa_base_url, noaa_token, station_id, start_date, end_date, city_name=city_name)

    filename = os.path.join(full_raw_data_path, f"noaa_{city_name.lower().replace(' ', '_')}_{start_date}_to_{end_date}.json")
    
    # Always save a file to ensure the city is processed, even if the fetch fails.
    if weather_data and 'results' in weather_data and weather_data['results']:
        with open(filename, 'w') as f:
            json.dump(weather_data['results'], f, indent=4)
        logging.info(f"Successfully fetched and saved {len(weather_data['results'])} records to {filename}")
    else:
        logging.warning(f"Failed to fetch or no NOAA data returned for {city_name}. Saving empty file.")
        with open(filename, 'w') as f:
            json.dump([], f) # Save an empty JSON array
    return filename

def fetch_and_save_eia_data(city, eia_base_url, eia_api_key, full_raw_data_path, start_date, end_date):
    """Fetches and saves EIA energy data for a given city."""
    city_name = city['name']
    eia_ba_code = city.get('eia_ba_code')
    
    # More robust check for invalid BA codes, including the string 'None' or 'N/A'
    if not eia_ba_code or str(eia_ba_code).strip().upper() in ['NONE', 'N/A']:
        logging.warning(f"Skipping EIA data for {city_name}: no valid 'eia_ba_code' in config (found: {eia_ba_code}).")
        # Create an empty file to ensure the city is processed correctly downstream.
        filename = os.path.join(full_raw_data_path, f"eia_{city_name.lower().replace(' ', '_')}_{start_date}_to_{end_date}.json")
        with open(filename, 'w') as f:
            json.dump([], f)
        return filename

    logging.info(f"Fetching EIA data for {city_name} (Balancing Authority: {eia_ba_code})...")
    energy_data = fetch_eia_data(eia_base_url, eia_api_key, eia_ba_code, start_date, end_date, city_name=city_name)

    filename = os.path.join(full_raw_data_path, f"eia_{city_name.lower().replace(' ', '_')}_{start_date}_to_{end_date}.json")

    # Always save a file to ensure the city is processed, even if the fetch fails.
    if energy_data:
        with open(filename, 'w') as f:
            json.dump(energy_data, f, indent=4)
        logging.info(f"Successfully fetched and saved {len(energy_data)} records to {filename}")
    else:
        logging.warning(f"Failed to fetch or no EIA data returned for {city_name}. Saving empty file.")
        with open(filename, 'w') as f:
            json.dump([], f) # Save an empty JSON array
    return filename

def _setup_pipeline_parameters(config, args):
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
        logging.error("One or more API base URLs are missing in config.yaml. Exiting.")
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

    # Define a date range for the data fetch based on command-line arguments
    if args.fetch_range:
        logging.info(f"Mode: Custom range fetch from {args.fetch_range[0]} to {args.fetch_range[1]}.")
        try:
            start_date = datetime.strptime(args.fetch_range[0], '%Y-%m-%d')
            end_date = datetime.strptime(args.fetch_range[1], '%Y-%m-%d')
        except ValueError:
            logging.error("Invalid date format for --fetch-range. Please use YYYY-MM-DD. Exiting.")
            return None
    elif args.fetch_historical:
        logging.info(f"Mode: Historical fetch for the last {args.fetch_historical} days.")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.fetch_historical)
    elif args.fetch_daily:
        logging.info("Mode: Daily fetch for yesterday's data (yesterday).")
        # Set both start and end date to yesterday to fetch a single day's data
        yesterday = datetime.now() - timedelta(days=1)
        start_date = yesterday
        end_date = yesterday
    else:  # Default case: no arguments provided
        default_days = 365
        logging.info(f"Mode: No argument provided, defaulting to historical fetch for the last {default_days} days (one year).")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=default_days)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    return {
        "noaa_base_url": noaa_base_url, "eia_base_url": eia_base_url, "cities": cities,
        "full_raw_data_path": full_raw_data_path, "full_processed_data_path": full_processed_data_path, "full_output_data_path": full_output_data_path,
        "start_date": start_date_str, "end_date": end_date_str
    }

def _clear_intermediate_data(raw_dir, processed_dir):
    """
    Clears out the raw and processed data directories to ensure a clean pipeline run.
    This prevents stale data from a previous run from contaminating the current one.
    """
    logging.info("--- Clearing Intermediate Data Directories for a Clean Run ---")
    for directory in [raw_dir, processed_dir]:
        if os.path.exists(directory):
            logging.info(f"Clearing contents of {directory}...")
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logging.error(f"Failed to delete {file_path}. Reason: {e}")

def main(args):
    """
    Main function to orchestrate the data fetching process.
    Accepts parsed command-line arguments.
    """
    logging.info("--- Starting Data Fetching Process ---")

    # 1. Load Configuration
    config, noaa_token, eia_api_key = load_configuration()

    if not config:
        logging.error("Could not load configuration file. Exiting.")
        return
    
    if not all([noaa_token, eia_api_key]):
        logging.error("Could not load configuration or API keys. Exiting.")
        return

    logging.info("Configuration and API keys loaded successfully.")

    # 2. Setup pipeline parameters from config
    params = _setup_pipeline_parameters(config, args)
    if not params:
        return

    # Clear intermediate directories for a clean run
    _clear_intermediate_data(params["full_raw_data_path"], params["full_processed_data_path"])

    # Initialize a list to hold all data quality warnings
    all_warnings = []

    # 3. Fetch Data for Each City
    for city in params["cities"]:
        try:
            # Validate that the city entry has all the required keys before processing
            # eia_ba_code is optional as it's handled gracefully if missing.
            required_keys = ['name', 'noaa_station_id']
            if not all(key in city for key in required_keys):
                logging.warning(f"Skipping an entry due to missing keys. Found: {list(city.keys())}. Required: {required_keys}")
                continue

            # Step 1: Fetch raw data
            noaa_file = fetch_and_save_noaa_data(city, params["noaa_base_url"], noaa_token, params["full_raw_data_path"], params["start_date"], params["end_date"])
            eia_file = fetch_and_save_eia_data(city, params["eia_base_url"], eia_api_key, params["full_raw_data_path"], params["start_date"], params["end_date"])

            # Step 2: Process any available data
            logging.info(f"Processing available data for {city['name']}...")

            # Process each file if it exists, otherwise the result is None
            weather_df, noaa_warnings = process_noaa_data(noaa_file)
            energy_df, eia_warnings = process_eia_data(eia_file)

            # Collect warnings from both processors
            all_warnings.extend(noaa_warnings)
            all_warnings.extend(eia_warnings)

            # Step 3: Merge and/or save the processed data
            merge_and_save_data(weather_df, energy_df, city['name'], params["full_processed_data_path"])

            # Be a good API citizen: wait 1 second between requests to avoid rate-limiting.
            time.sleep(1)
        except Exception as e:
            logging.critical(f"An unrecoverable error occurred while processing city: {city.get('name', 'Unknown')}. Skipping.", exc_info=True)
            all_warnings.append({
                "file": city.get('name', 'Unknown'),
                "check": "City Processing Loop",
                "level": "CRITICAL",
                "message": "The pipeline failed to process this city due to an unhandled exception.",
                "details": str(e)
            })
            continue # Ensure the loop continues to the next city

    # Step 4: Combine all processed files into a master file
    combine_processed_data(params["full_processed_data_path"], params["full_output_data_path"], params["cities"])

    # Step 5: Save the data quality report
    report_path = os.path.join(params["full_output_data_path"], "data_quality_report.json")
    if all_warnings:
        logging.info(f"Saving {len(all_warnings)} data quality warnings to {report_path}...")
    else:
        logging.info("No data quality issues found. Creating an empty report file.")
    with open(report_path, 'w') as f:
        json.dump(all_warnings, f, indent=4)

    logging.info("--- All Processes Finished ---")

if __name__ == "__main__":
    main()
