import pandas as pd
import json
import os

def _convert_temp_to_fahrenheit(temp_in_c):
    """Converts temperature from Celsius to Fahrenheit."""
    # The NOAA API with units=metric returns values in degrees Celsius.
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
        pd.DataFrame: A DataFrame with daily weather data, or None if processing fails.
    """
    try:
        with open(raw_file_path, 'r') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Pivot the table to get TMAX and TMIN as columns
        weather_df = df.pivot(index='date', columns='datatype', values='value').reset_index()
        
        # Convert temperatures to Fahrenheit
        weather_df['TMAX_F'] = weather_df['TMAX'].apply(_convert_temp_to_fahrenheit)
        weather_df['TMIN_F'] = weather_df['TMIN'].apply(_convert_temp_to_fahrenheit)
        
        return weather_df[['date', 'TMAX_F', 'TMIN_F']]
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error processing NOAA file {raw_file_path}: {e}")
        return None

def process_eia_data(raw_file_path):
    """
    Processes raw EIA JSON data into a clean DataFrame.

    Args:
        raw_file_path (str): The path to the raw EIA JSON file.

    Returns:
        pd.DataFrame: A DataFrame with daily energy data, or None if processing fails.
    """
    try:
        with open(raw_file_path, 'r') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        # Convert period to datetime and extract only the date part
        df['date'] = pd.to_datetime(df['period']).dt.date
        df.rename(columns={'value': 'energy_mwh'}, inplace=True)
        
        # Ensure the energy column is numeric before aggregation. Coerce errors to NaN.
        df['energy_mwh'] = pd.to_numeric(df['energy_mwh'], errors='coerce')
        
        # Group by the new date column and sum the energy values for each day
        daily_energy_df = df.groupby('date')['energy_mwh'].sum().reset_index()
        # Round the summed energy value to two decimal places
        daily_energy_df['energy_mwh'] = daily_energy_df['energy_mwh'].round(2)
        return daily_energy_df
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error processing EIA file {raw_file_path}: {e}")
        return None

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

    if weather_df is not None and energy_df is not None:
        # Both are available: merge them
        merged_df = pd.merge(weather_df, energy_df, on='date', how='inner')
        merged_df['city'] = city_name
        merged_df.to_csv(output_path, index=False)
        print(f"Successfully merged and saved processed data for {city_name} to {output_path}")
    elif weather_df is not None:
        # Only weather data is available
        weather_df['city'] = city_name
        weather_df.to_csv(output_path, index=False)
        print(f"Successfully saved processed weather-only data for {city_name} to {output_path}")
    elif energy_df is not None:
        # Only energy data is available
        energy_df['city'] = city_name
        energy_df.to_csv(output_path, index=False)
        print(f"Successfully saved processed energy-only data for {city_name} to {output_path}")
    else:
        # Neither is available
        print(f"Skipping save for {city_name} as no data was successfully processed.")
        return

def combine_processed_data(processed_dir, output_dir):
    """
    Finds all processed CSV files in a directory, combines them into a single
    master DataFrame, and saves it to a new CSV file in a specified output directory.

    Args:
        processed_dir (str): The directory containing the processed city CSV files.
        output_dir (str): The directory to save the final master file.
    """
    print("\n--- Combining All Processed Data ---")
    # Find all individual processed CSV files
    all_files = [os.path.join(processed_dir, f) for f in os.listdir(processed_dir) if f.endswith('_processed_data.csv')]
    
    if not all_files:
        print("No processed data files found to combine.")
        return

    df_list = []
    for file in all_files:
        try:
            df = pd.read_csv(file)
            df_list.append(df)
        except Exception as e:
            print(f"Could not read or process file {file}: {e}")

    if not df_list:
        print("No dataframes were created from the files. Aborting combination.")
        return

    combined_df = pd.concat(df_list, ignore_index=True)
    combined_df.sort_values(by=['city', 'date'], inplace=True)

    master_file_path = os.path.join(output_dir, 'master_energy_weather_data.csv')
    combined_df.to_csv(master_file_path, index=False)
    
    print(f"Successfully combined {len(df_list)} files into {master_file_path}")
