import requests
import time

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

        for attempt in range(3):  # Retry up to 3 times
            try:
                response = requests.get(endpoint_url, headers=headers, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    all_results.extend(results)
                    break  # Break the retry loop on success
                elif response.status_code >= 500:
                    print(f"Server error ({response.status_code}) for {log_identifier}. Retrying in {2**attempt}s...")
                    time.sleep(2 ** attempt)
                else:
                    print(f"Client error fetching NOAA data for {log_identifier}. Status: {response.status_code}, Response: {response.text}")
                    return None  # Non-retriable client error
            except requests.exceptions.RequestException as e:
                print(f"A network error occurred for {log_identifier}: {e}. Retrying in {2**attempt}s...")
                time.sleep(2 ** attempt)
        else:  # This 'else' belongs to the 'for' loop, runs if it completes without break
            print(f"Failed to fetch data for {log_identifier} after multiple attempts.")
            return None

        # Check if we've fetched all the data
        if not results or len(results) < api_limit_per_request:
            break
        
        offset += len(results)

    return {'results': all_results}
