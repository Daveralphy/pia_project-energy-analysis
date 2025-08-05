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
        tuple: A tuple containing (pd.DataFrame, list of warnings), or (None, []) on failure.
    """
    warnings = []
    try:
        with open(raw_file_path, 'r') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Data Quality Check: Look for duplicate datatype entries for the same date before pivoting.
        # This prevents the pivot operation from failing with a ValueError.
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

        # Pivot the table to get TMAX and TMIN as columns
        weather_df = df.pivot(index='date', columns='datatype', values='value').reset_index()
        
        # Ensure TMAX and TMIN columns exist, creating them with NaN if they don't.
        # This makes the function resilient to stations that only report one metric.
        if 'TMAX' not in weather_df.columns:
            weather_df['TMAX'] = pd.NA
        if 'TMIN' not in weather_df.columns:
            weather_df['TMIN'] = pd.NA

        # Convert temperatures to Fahrenheit
        weather_df['TMAX_F'] = weather_df['TMAX'].apply(_convert_temp_to_fahrenheit)
        weather_df['TMIN_F'] = weather_df['TMIN'].apply(_convert_temp_to_fahrenheit)
        
        # Data Quality Check: Flag days where TMIN > TMAX, a logical impossibility.
        # Corrected boolean indexing for safety
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
        # This can happen if pivot fails due to duplicate data from the API
        error_message = f"ValueError during processing of NOAA file {os.path.basename(raw_file_path)}: {e}"
        print(f"  [!] {error_message}")
        warnings.append({
            "file": os.path.basename(raw_file_path),
            "check": "Data Pivoting",
            "level": "ERROR",
            "message": f"Could not pivot data, likely due to duplicate TMAX/TMIN values for a single day. Error: {e}",
            "details": {}
        })
        return None, warnings # Return None for the dataframe, but include the critical warning
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error processing NOAA file {raw_file_path}: {e}")
        return None, []
    except Exception as e:
        # Catch-all for any other unexpected errors
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

        # Data Quality Check: Flag days with negative energy consumption.
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

    if weather_df is not None and energy_df is not None:
        # Both are available: merge them using an outer join to preserve all data points
        merged_df = pd.merge(weather_df, energy_df, on='date', how='outer')
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
    Finds all newly processed CSV files, reads the existing master data file (if any),
    and merges the new data into the master file, overwriting old data with new
    data for any overlapping city/date combinations.

    Args:
        processed_dir (str): The directory containing the processed city CSV files.
        output_dir (str): The directory to save the final master file.
    """
    print("\n--- Combining All Processed Data ---")
    newly_processed_files = [os.path.join(processed_dir, f) for f in os.listdir(processed_dir) if f.endswith('_processed_data.csv')]
    
    if not newly_processed_files:
        print("No new data was processed in this run. Master file remains unchanged.")
        return

    new_data_list = []
    for file in newly_processed_files:
        try:
            df = pd.read_csv(file)
            new_data_list.append(df)
        except Exception as e:
            print(f"Could not read or process file {file}: {e}")

    if not new_data_list:
        print("No new dataframes were created from the processed files. Aborting combination.")
        return

    newly_processed_df = pd.concat(new_data_list, ignore_index=True)
    master_file_path = os.path.join(output_dir, 'master_energy_weather_data.csv')

    if os.path.exists(master_file_path):
        print(f"Existing master file found at {master_file_path}. Merging new data...")
        existing_master_df = pd.read_csv(master_file_path)
        # Combine old and new data, then drop duplicates, keeping the new data for any overlaps
        combined_df = pd.concat([existing_master_df, newly_processed_df], ignore_index=True)
        combined_df.drop_duplicates(subset=['city', 'date'], keep='last', inplace=True)
    else:
        print("No existing master file found. Creating a new one.")
        combined_df = newly_processed_df

    combined_df.sort_values(by=['city', 'date'], inplace=True)
    combined_df.to_csv(master_file_path, index=False)
    
    print(f"Successfully updated master data file at {master_file_path}")
