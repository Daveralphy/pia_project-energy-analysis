import requests
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
def _make_eia_api_request(url, headers, params, log_identifier):
    """Makes a single, robust request to the EIA API, decorated to handle retries."""
    response = requests.get(url, headers=headers, params=params, timeout=15)
    return response

def fetch_eia_data(base_url, api_key, ba_code, start_date, end_date, city_name=None):
    """
    Fetches all hourly electricity demand data from the EIA API for a given region,
    handling pagination automatically.

    Args:
        base_url (str): The base URL for the EIA API endpoint.
        api_key (str): Your EIA API key.
        ba_code (str): The EIA Balancing Authority code (e.g., 'NYIS', 'ERCO').
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
        city_name (str, optional): The name of the city for better logging. Defaults to None.

    Returns:
        list: A list of all data records from the API, or an empty list if the request fails.
    """
    log_identifier = city_name if city_name else ba_code
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    all_data = []
    offset = 0
    api_length_per_request = 5000  # EIA's max length per request

    while True:
        params = {
            'api_key': api_key,
            'frequency': 'daily',  # Reverted to daily frequency for stability
            'data[0]': 'value',
            'facets[respondent][]': ba_code,
            'start': start_date,  # Use YYYY-MM-DD format for daily
            'end': end_date,
            'sort[0][column]': 'period',
            'sort[0][direction]': 'asc',
            'offset': offset,
            'length': api_length_per_request
        }

        try:
            response = _make_eia_api_request(base_url, headers, params, log_identifier)

            if response.status_code != 200:
                # This will catch non-retriable client errors (4xx)
                print(f"Client error fetching EIA data for {log_identifier}. Status: {response.status_code}, Response: {response.text}")
                return []

            response_data = response.json()
            data = response_data.get('response', {}).get('data', [])
            all_data.extend(data)

        except Exception as e:
            # This catches the exception from tenacity if all retries fail
            print(f"An unrecoverable error occurred for {log_identifier} after multiple attempts: {e}")
            return []

        if not data or len(data) < api_length_per_request:
            break

        offset += len(data)

    return all_data
