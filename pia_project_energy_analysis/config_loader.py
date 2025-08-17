import os
from dotenv import load_dotenv
import yaml

def load_configuration(config_path='config/config.yaml'):
    """
    Loads API keys from .env and configuration from a YAML file.

    Args:
        config_path (str): Relative path to the YAML configuration file.

    Returns:
        tuple: A tuple containing the config dictionary, NOAA token, and EIA key.
               Returns (None, None, None) on failure.
    """
    load_dotenv(override=True) 
    noaa_token = os.getenv("NOAA_TOKEN")
    eia_api_key = os.getenv("EIA_API_KEY")

    if noaa_token:
        noaa_token = noaa_token.strip()
    if eia_api_key:
        eia_api_key = eia_api_key.strip()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_config_path = os.path.join(project_root, config_path)

    try:
        with open(full_config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config, noaa_token, eia_api_key
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error processing configuration: {e}")
        return None, None, None

