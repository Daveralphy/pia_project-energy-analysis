import requests
import time
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_result

def _is_server_error(response):
    """Return True if the response status code is a 5xx server error, indicating a retriable issue."""
    return response.status_code >= 500

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=(retry_if_exception_type(requests.exceptions.RequestException) | retry_if_result(_is_server_error)),
    reraise=True  # Reraise the last exception if all retries fail
)
def _make_noaa_api_request(url, headers, params, log_identifier):
    """
    Makes a single, robust request to the NOAA API, decorated to handle retries.
    """
    response = requests.get(url, headers=headers, params=params, timeout=20)
    # If it's a client error (4xx), we don't want to retry. The main function will handle it.
    # If it's a server error (5xx), tenacity's `retry_if_result` will trigger a retry.
    return response
 
def fetch_noaa_data(base_url, token, station_id, start_date, end_date, datatypes='TMAX,TMIN', city_name=None):
    """
    Fetches all weather data from the NOAA API for a given station and date range,
    handling pagination and the API's one-year limit automatically by chunking requests.

    Args:
        base_url (str): The base URL for the NOAA API endpoint.
        token (str): Your NOAA API token.
        station_id (str): The ID of the weather station.
        start_date (str): The start date string in YYYY-MM-DD format.
        end_date (str): The end date string in YYYY-MM-DD format.
        datatypes (str): Comma-separated string of data types to fetch (e.g., 'TMAX,TMIN').
        city_name (str, optional): The name of the city for better logging. Defaults to None.

    Returns:
        dict: A dictionary containing all results, or None if the request fails.
    """
    log_identifier = city_name if city_name else station_id
    headers = {
        'token': token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    endpoint_url = f"{base_url.rstrip('/')}/data"
    all_results = []
    api_limit_per_request = 1000  # NOAA's max limit per request

    # Convert string dates to datetime objects for calculations
    start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
    current_start_dt = start_date_dt

    # Loop through the date range in year-long (or smaller) chunks
    while current_start_dt <= end_date_dt:
        # Calculate the end of the current chunk (max 1 year)
        chunk_end_dt = current_start_dt + timedelta(days=364)
        if chunk_end_dt > end_date_dt:
            chunk_end_dt = end_date_dt

        chunk_start_str = current_start_dt.strftime('%Y-%m-%d')
        chunk_end_str = chunk_end_dt.strftime('%Y-%m-%d')

        print(f"\nFetching NOAA data chunk for {log_identifier} from {chunk_start_str} to {chunk_end_str}...")

        # --- Pagination logic for the current chunk ---
        offset = 1
        while True:
            params = {
                'datasetid': 'GHCND',
                'stationid': station_id,
                'startdate': chunk_start_str,
                'enddate': chunk_end_str,
                'limit': api_limit_per_request,
                'offset': offset,
                'datatypeid': datatypes.split(','),
                'units': 'metric'
            }
 
            try:
                print(f"Requesting data for {log_identifier} with offset {offset}...")
                response = _make_noaa_api_request(endpoint_url, headers, params, log_identifier)
 
                if response.status_code != 200:
                    print(f"Client error fetching NOAA data for {log_identifier}. Status: {response.status_code}, Response: {response.text}")
                    return None
 
                data = response.json()
                results_this_page = data.get('results', [])
                all_results.extend(results_this_page)
 
            except Exception as e:
                print(f"An unrecoverable error occurred for {log_identifier} after multiple attempts: {e}")
                return None
 
            if not results_this_page or len(results_this_page) < api_limit_per_request:
                break
            
            offset += len(results_this_page)
            time.sleep(0.2)

        # Move to the next chunk
        current_start_dt = chunk_end_dt + timedelta(days=1)

    return {'results': all_results}
