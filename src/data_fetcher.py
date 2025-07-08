# test_config.py (or at the top of your data_fetcher.py)

import os
from dotenv import load_dotenv
import yaml

# 1. Load environment variables from .env file
load_dotenv()

# 2. Access API keys
noaa_token = os.getenv("NOAA_TOKEN")
eia_api_key = os.getenv("EIA_API_KEY")

if noaa_token:
    print(f"NOAA Token loaded: {noaa_token[:5]}...") # Print first 5 chars for verification
else:
    print("NOAA Token not found. Check your .env file.")

if eia_api_key:
    print(f"EIA API Key loaded: {eia_api_key[:5]}...") # Print first 5 chars
else:
    print("EIA API Key not found. Check your .env file.")

# 3. Load config.yaml
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
# If you are running this from the project root directly:
# config_path = os.path.join('config', 'config.yaml')

config = None
try:
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    print(f"Error: config.yaml not found at {config_path}")
except yaml.YAMLError as e:
    print(f"Error parsing config.yaml: {e}")

# Example of accessing data
if config:
    print("\nConfig loaded successfully:")
    print(f"Number of cities in config: {len(config.get('cities', []))}")
    print(f"NOAA Base URL: {config.get('api_endpoints', {}).get('noaa_base_url')}")
    # You can print more config items to verify
    if config.get('cities'):
        first_city = config['cities'][0]
        print(f"First city name: {first_city['name']}")
        print(f"First city NOAA ID: {first_city['noaa_station_id']}")
else:
    print("\nCould not load config or config is empty.")