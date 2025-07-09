import requests
import time

def fetch_eia_data(base_url, api_key, ba_code, start_date, end_date, city_name=None):
    """
    Fetches daily electricity demand data from the EIA API for a given region.

    Args:
        base_url (str): The base URL for the EIA API endpoint.
        api_key (str): Your EIA API key.
        ba_code (str): The EIA Balancing Authority code (e.g., 'NYIS', 'ERCO').
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
        city_name (str, optional): The name of the city for better logging. Defaults to None.

    Returns:
        list: A list of data records from the API, or an empty list if the request fails.
    """
    log_identifier = city_name if city_name else ba_code
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    params = {
        'api_key': api_key,
        'frequency': 'daily',
        'data[0]': 'value', # Per API docs for this endpoint, 'value' is the required data field
        'facets[respondent][]': ba_code,
        'start': start_date,
        'end': end_date,
        'sort[0][column]': 'period',
        'sort[0][direction]': 'asc',
        'offset': 0,
        'length': 50 # Max length, reduced for testing
    }

    for attempt in range(3): # Retry up to 3 times
        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data.get('response', {}).get('data', [])
            elif response.status_code >= 500:
                print(f"Server error ({response.status_code}) for {log_identifier}. Retrying in {2**attempt}s...")
                time.sleep(2 ** attempt)
            else:
                print(f"Client error fetching EIA data for {log_identifier}. Status: {response.status_code}, Response: {response.text}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"A network error occurred for {log_identifier}: {e}. Retrying in {2**attempt}s...")
            time.sleep(2 ** attempt)

    print(f"Failed to fetch EIA data for {log_identifier} after multiple attempts.")
    return []
