import pandas as pd
import json
import os

def _convert_temp_to_fahrenheit(temp_in_c):
    """Converts temperature from Celsius to Fahrenheit."""
    if pd.isna(temp_in_c):
        return None
    fahrenheit = (temp_in_c * 9/5) + 32
    return round(fahrenheit, 2)

def process_noaa_data(raw_file_path):
    """
    Processes raw NOAA JSON data into a clean DataFrame.

    Args:
        raw_file_path (str): The path to the raw NOAA JSON file.

    Returns:
        tuple: A tuple containing (pd.DataFrame, list of warnings), or (None, []) on failure.
    """
    warnings = []
    try:
        with open(raw_file_path, 'r') as f:
            data = json.load(f)
        
        if not data:
            print(f"  - No data found in NOAA file {os.path.basename(raw_file_path)}. Returning empty dataframe.")
            return pd.DataFrame(columns=['date', 'TMAX_F', 'TMIN_F']), []
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        if df.duplicated(subset=['date', 'datatype']).any():
            duplicates = df[df.duplicated(subset=['date', 'datatype'], keep=False)].sort_values(by=['date', 'datatype'])
            issue = f"Duplicate weather data points found. This can cause processing errors. Taking first entry."
            warnings.append({
                "file": os.path.basename(raw_file_path),
                "check": "Duplicate Raw Data",
                "level": "WARNING",
                "message": issue,
                "details": duplicates.to_dict('records')
            })
            print(f"  [!] DATA QUALITY WARNING for {os.path.basename(raw_file_path)}: {issue}")
            df.drop_duplicates(subset=['date', 'datatype'], keep='first', inplace=True)

        weather_df = df.pivot(index='date', columns='datatype', values='value').reset_index()
        
        if 'TMAX' not in weather_df.columns:
            weather_df['TMAX'] = pd.NA
        if 'TMIN' not in weather_df.columns:
            weather_df['TMIN'] = pd.NA

        weather_df['TMAX_F'] = weather_df['TMAX'].apply(_convert_temp_to_fahrenheit)
        weather_df['TMIN_F'] = weather_df['TMIN'].apply(_convert_temp_to_fahrenheit)
        
        valid_temps_df = weather_df.dropna(subset=['TMIN_F', 'TMAX_F'])
        invalid_temp_rows = valid_temps_df[valid_temps_df['TMIN_F'] > valid_temps_df['TMAX_F']]
        if not invalid_temp_rows.empty:
            warning_msg = f"DATA QUALITY WARNING for {os.path.basename(raw_file_path)}:"
            print(f"  [!] {warning_msg}")
            for _, row in invalid_temp_rows.iterrows():
                issue = f"Date {row.get('date')}: TMIN ({row.get('TMIN_F')}°F) > TMAX ({row.get('TMAX_F')}°F)."
                print(f"      - {issue}")
                warnings.append({
                    "file": os.path.basename(raw_file_path),
                    "check": "Temperature Logic",
                    "level": "WARNING",
                    "message": issue,
                    "details": { "date": str(row.get('date')), "tmin_f": row.get('TMIN_F'), "tmax_f": row.get('TMAX_F') }
                })

        return weather_df[['date', 'TMAX_F', 'TMIN_F']], warnings
    except ValueError as e:
        error_message = f"ValueError during processing of NOAA file {os.path.basename(raw_file_path)}: {e}"
        print(f"  [!] {error_message}")
        warnings.append({
            "file": os.path.basename(raw_file_path),
            "check": "Data Pivoting",
            "level": "ERROR",
            "message": f"Could not pivot data, likely due to duplicate TMAX/TMIN values for a single day. Error: {e}",
            "details": {}
        })
        return None, warnings 
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error processing NOAA file {raw_file_path}: {e}")
        return None, []
    except Exception as e:
        print(f"An unexpected error occurred while processing {raw_file_path}: {e}")
        return None, []

def process_eia_data(raw_file_path):
    """
    Processes raw EIA JSON data into a clean DataFrame.

    Args:
        raw_file_path (str): The path to the raw EIA JSON file.

    Returns:
        tuple: A tuple containing (pd.DataFrame, list of warnings), or (None, []) on failure.
    """
    warnings = []
    try:
        with open(raw_file_path, 'r') as f:
            data = json.load(f)
        
        if not data:
            print(f"  - No data found in EIA file {os.path.basename(raw_file_path)}. Returning empty dataframe.")
            return pd.DataFrame(columns=['date', 'energy_mwh']), []

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['period']).dt.date
        df.rename(columns={'value': 'energy_mwh'}, inplace=True)
        
        df['energy_mwh'] = pd.to_numeric(df['energy_mwh'], errors='coerce')
        
        daily_energy_df = df.groupby('date')['energy_mwh'].sum().reset_index()
        daily_energy_df['energy_mwh'] = daily_energy_df['energy_mwh'].round(2)

        negative_energy_rows = daily_energy_df[daily_energy_df['energy_mwh'] < 0]
        if not negative_energy_rows.empty:
            warning_msg = f"DATA QUALITY WARNING for {os.path.basename(raw_file_path)}:"
            print(f"  [!] {warning_msg}")
            for _, row in negative_energy_rows.iterrows():
                issue = f"Date {row.get('date')}: Negative energy consumption detected ({row.get('energy_mwh')} MWh)."
                print(f"      - {issue}")
                warnings.append({
                    "file": os.path.basename(raw_file_path),
                    "check": "Negative Energy",
                    "level": "WARNING",
                    "message": issue,
                    "details": { "date": str(row.get('date')), "energy_mwh": row.get('energy_mwh') }
                })

        return daily_energy_df, warnings
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error processing EIA file {raw_file_path}: {e}")
        return None, []
    except Exception as e:
        print(f"An unexpected error occurred while processing {raw_file_path}: {e}")
        return None, []

def merge_and_save_data(weather_df, energy_df, city_name, processed_dir):
    """
    Merges weather and/or energy data and saves it to a CSV file.
    If only one dataframe is provided, it saves that one. If neither is
    provided, it does nothing.

    Args:
        weather_df (pd.DataFrame or None): The processed weather data.
        energy_df (pd.DataFrame or None): The processed energy data.
        city_name (str): The name of the city.
        processed_dir (str): The directory to save the processed file.
    """
    output_path = os.path.join(processed_dir, f"{city_name.lower().replace(' ', '_')}_processed_data.csv")

    final_df = None

    has_weather_data = weather_df is not None and not weather_df.empty
    has_energy_data = energy_df is not None and not energy_df.empty

    if has_weather_data and has_energy_data:
        merged_df = pd.merge(weather_df, energy_df, on='date', how='outer')
        final_df = merged_df
        print(f"Successfully merged weather and energy data for {city_name}.")
    elif has_weather_data:
        final_df = weather_df.copy()
        print(f"Successfully saved processed weather-only data for {city_name} to {output_path}")
    elif has_energy_data:
        final_df = energy_df.copy()
        print(f"Successfully saved processed energy-only data for {city_name} to {output_path}")

    if final_df is None:
        final_df = pd.DataFrame()

    expected_cols = ['date', 'TMAX_F', 'TMIN_F', 'energy_mwh']
    for col in expected_cols:
        if col not in final_df.columns:
            final_df[col] = pd.NA

    final_df['city'] = city_name
    final_df.to_csv(output_path, index=False)
    if final_df.empty:
        print(f"No data processed for {city_name}. Saved an empty placeholder file.")

def combine_processed_data(processed_dir, output_dir, configured_cities):
    """
    Combines all processed data files from the current run into a single, new
    master data file, ensuring all configured cities are represented. This
    process overwrites any existing master file.

    Args:
        processed_dir (str): The directory containing the processed city CSV files.
        output_dir (str): The directory to save the final master file.
        configured_cities (list): The list of city dictionaries from the config file.
    """
    print("\n--- Combining All Processed Data into a New Master File ---")
    configured_city_names = {city['name'] for city in configured_cities}
    
    processed_files = [os.path.join(processed_dir, f) for f in os.listdir(processed_dir) if f.endswith('_processed_data.csv')]
    
    if not processed_files:
        print("No processed data files found to combine. Creating a master file with placeholders.")
        master_df = pd.DataFrame([{'city': city['name']} for city in configured_cities])
    else:
        df_list = []
        for file in processed_files:
            try:
                df = pd.read_csv(file)
                df_list.append(df)
            except pd.errors.EmptyDataError:
                print(f"  - Skipping empty file: {os.path.basename(file)}")
            except Exception as e:
                print(f"  - Could not read or process file {os.path.basename(file)}: {e}")

        if not df_list:
            print("Could not create any dataframes from processed files. Creating a master file with placeholders.")
            master_df = pd.DataFrame([{'city': city['name']} for city in configured_cities])
        else:
            master_df = pd.concat(df_list, ignore_index=True)

    cities_in_master = set(master_df['city'].unique()) if 'city' in master_df.columns else set()
    
    missing_cities = configured_city_names - cities_in_master
    
    if missing_cities:
        print(f"Adding placeholder records for configured cities not found in data: {', '.join(missing_cities)}")
        missing_cities_df = pd.DataFrame([{'city': name} for name in missing_cities])
        master_df = pd.concat([master_df, missing_cities_df], ignore_index=True)

    expected_cols = ['date', 'TMAX_F', 'TMIN_F', 'energy_mwh']
    for col in expected_cols:
        if col not in master_df.columns:
            master_df[col] = pd.NA

    if not master_df.empty:
        master_df.sort_values(by=['city', 'date'], inplace=True, na_position='first')
        master_file_path = os.path.join(output_dir, 'master_energy_weather_data.csv')
        master_df.to_csv(master_file_path, index=False)
        print(f"Successfully created new master data file at {master_file_path}")
    else:
        print("Master dataframe is empty. Nothing to save.")
