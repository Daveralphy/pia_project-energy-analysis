import requests
import time
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
    handling pagination automatically.

    Args:
        base_url (str): The base URL for the NOAA API endpoint.
        token (str): Your NOAA API token.
        station_id (str): The ID of the weather station.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
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
    offset = 1  # NOAA API offset is 1-based
    api_limit_per_request = 1000  # NOAA's max limit per request

    while True:
        params = {
            'datasetid': 'GHCND',
            'stationid': station_id,
            'startdate': start_date,
            'enddate': end_date,
            'limit': api_limit_per_request,
            'offset': offset,
            'datatypeid': datatypes.split(','),
            'units': 'metric'  # Processor expects Celsius to convert to Fahrenheit
        }
 
        try:
            print(f"Requesting data for {log_identifier} with offset {offset}...")
            response = _make_noaa_api_request(endpoint_url, headers, params, log_identifier)
 
            if response.status_code != 200:
                # This will catch non-retriable client errors (4xx)
                print(f"Client error fetching NOAA data for {log_identifier}. Status: {response.status_code}, Response: {response.text}")
                return None
 
            data = response.json()
            results = data.get('results', [])
            all_results.extend(results)
 
        except Exception as e:
            # This catches the exception from tenacity if all retries fail
            print(f"An unrecoverable error occurred for {log_identifier} after multiple attempts: {e}")
            return None
 
        # Check if we've fetched all the data
        if not results or len(results) < api_limit_per_request:
            break
        
        offset += len(results)
        time.sleep(0.2) # Small delay to be a good API citizen between pagination requests

    return {'results': all_results}
