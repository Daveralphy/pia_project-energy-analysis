import time
import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
import subprocess
import yaml

def load_data():
    """Loads the master data file from the output directory."""
    # Construct the path relative to the script's location
    # This makes it runnable from the project root (streamlit run dashboards/app.py)
    project_root = os.path.join(os.path.dirname(__file__), '..')
    data_path = os.path.join(project_root, 'data', 'output', 'master_energy_weather_data.csv')
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    
    if not os.path.exists(data_path):
        st.error(f"Master data file not found at `{data_path}`.")
        st.warning("Please run the main data pipeline first to generate the master data file. From your project root, execute:")
        st.code("python src/main.py")
        st.stop() # Halt execution and display the messages

    # Load master data
    try:
        df = pd.read_csv(data_path)
        df['date'] = pd.to_datetime(df['date'])
    except Exception as e:
        st.error(f"An error occurred while loading or parsing the data file: {e}")
        st.stop()

    # Load city coordinates from config.yaml to merge into the dataframe
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        cities_info = {city['name']: {'latitude': city['latitude'], 'longitude': city['longitude']} for city in config.get('cities', [])}
        
        # Map the coordinates to the dataframe
        df['latitude'] = df['city'].map(lambda x: cities_info.get(x, {}).get('latitude'))
        df['longitude'] = df['city'].map(lambda x: cities_info.get(x, {}).get('longitude'))
        
        return df

    except (FileNotFoundError, yaml.YAMLError) as e:
        st.warning(f"Could not load city coordinates from config file: {e}")
        return df # Return dataframe without coordinates

def main():
    """Main function to run the Streamlit dashboard."""
    st.set_page_config(page_title="Energy & Weather Analysis", layout="wide")

    with st.sidebar:
        st.header("Pipeline Controls")
        st.write("Click the button below to trigger a full data refresh from the APIs.")
        if st.button("Force Data Refresh"):
            run_pipeline()

        st.header("Analysis Options")
        temp_metric = st.radio(
            "Select Temperature Metric for Analysis",
            ('Max Temperature (TMAX)', 'Min Temperature (TMIN)', 'Average Temperature'),
            key='temp_metric_selector'
        )

    st.title("U.S. Weather and Energy Consumption Analysis")

    df = load_data()

    # Create a dynamic column for analysis based on user selection
    if temp_metric == 'Max Temperature (TMAX)':
        df['temp_for_analysis'] = df['TMAX_F']
        temp_axis_label = "Max Temperature (°F)"
    elif temp_metric == 'Min Temperature (TMIN)':
        df['temp_for_analysis'] = df['TMIN_F']
        temp_axis_label = "Min Temperature (°F)"
    else:  # Average Temperature
        df['temp_for_analysis'] = (df['TMAX_F'] + df['TMIN_F']) / 2
        temp_axis_label = "Average Temperature (°F)"
    
    # Drop rows where the analysis temp is NaN to avoid issues in plots
    df.dropna(subset=['temp_for_analysis'], inplace=True)

    # Create tabs for different analysis views
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📍 Geographic Overview", "📈 Time Series Analysis", "🔗 Correlation Analysis", "🗓️ Usage Patterns", "⚠️ Data Quality Report"])

    with tab1:
        display_geographic_overview(df, 'temp_for_analysis', temp_axis_label)
    
    with tab2:
        display_time_series(df)

    with tab3:
        display_correlation_analysis(df, 'temp_for_analysis', temp_axis_label)
    
    with tab4:
        display_usage_patterns_heatmap(df, 'temp_for_analysis', temp_axis_label)

    with tab5:
        display_data_quality_report()

def run_pipeline():
    """Triggers the main.py data pipeline as a background process and handles feedback."""
    st.info("Starting the data pipeline. This may take several minutes...")
    
    project_root = os.path.join(os.path.dirname(__file__), '..')
    main_script_path = os.path.join(project_root, 'src', 'main.py')
    
    with st.spinner("Fetching and processing data in the background... Please wait."):
        try:
            process = subprocess.run(
                [sys.executable, main_script_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=False # Do not raise exception on non-zero exit code, we'll check it manually
            )
        except Exception as e:
            st.error(f"An exception occurred while trying to run the pipeline: {e}")
            return

    if process.returncode == 0:
        st.success("Data pipeline finished successfully!")
        st.toast("Dashboard is reloading with new data...")
        time.sleep(2)
        st.rerun()
    else:
        st.error("The data pipeline encountered an error. See details below.")
        # Show both stdout and stderr for comprehensive debugging
        full_log = f"--- STDOUT ---\n{process.stdout}\n\n--- STDERR ---\n{process.stderr}"
        st.code(full_log, language='log')

def display_geographic_overview(df, temp_col, temp_label):
    """Displays an interactive map of the latest data for each city."""
    st.header("Geographic Overview")
    latest_data = df.loc[df.groupby('city')['date'].idxmax()]

    if 'latitude' not in latest_data.columns or latest_data['latitude'].isnull().any():
        st.warning("City coordinates are missing. Cannot display map. Please check `config.yaml`.")
        return

    # Prepare data for map, handling missing energy values gracefully
    map_data = latest_data.dropna(subset=['latitude', 'longitude', temp_col]).copy()

    if map_data.empty:
        st.warning("No data with coordinates and temperature available to display.")
        return

    # Use a small, constant size for cities with missing energy data to ensure they are still plotted.
    # Create a new column for hover text that is more informative.
    map_data['size_for_map'] = map_data['energy_mwh'].fillna(1000) # Use a small default size
    map_data['hover_energy_text'] = map_data['energy_mwh'].apply(
        lambda x: f"{x:,.0f} MWh" if pd.notna(x) else "Energy data not available"
    )

    fig = px.scatter_map(
        map_data,
        lat="latitude",
        lon="longitude",
        size="size_for_map",
        color=temp_col,
        hover_name="city",
        hover_data={temp_col: ":.1f°F", "hover_energy_text": True, "latitude": False, "longitude": False, "size_for_map": False},
        color_continuous_scale=px.colors.sequential.Plasma,
        size_max=50,
        zoom=3,
        map_style="carto-positron"
    )
    # Customize the hover label for clarity
    fig.update_traces(hovertemplate=f'<b>%{{hovertext}}</b><br>{temp_label}: %{{customdata[0]:.1f}}°F<br>Energy: %{{customdata[1]}}<extra></extra>')
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

def display_time_series(df):
    """Displays the time series analysis chart."""
    st.header("Time Series Analysis: Temperature vs. Energy Demand")
    city_list = ['All Cities'] + sorted(df['city'].unique())
    selected_city = st.selectbox("Select a City to Analyze", city_list, key="time_series_city")

    if selected_city == 'All Cities':
        # Aggregate both TMIN and TMAX for the shaded range
        plot_df = df.groupby('date').agg({
            'TMAX_F': 'mean',
            'TMIN_F': 'mean',
            'energy_mwh': 'sum'
        }).reset_index()
    else:
        plot_df = df[df['city'] == selected_city].copy()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add the lower bound of the temperature range (TMIN_F)
    # This trace is made invisible in the legend and has a transparent line.
    fig.add_trace(
        go.Scatter(x=plot_df['date'], y=plot_df['TMIN_F'], mode='lines', line=dict(width=0), showlegend=False),
        secondary_y=False
    )

    # Add the upper bound (TMAX_F) and fill the area down to the previous trace (TMIN_F)
    fig.add_trace(
        go.Scatter(
            x=plot_df['date'], y=plot_df['TMAX_F'], name='Temperature Range (°F)',
            fill='tonexty', fillcolor='rgba(255, 165, 0, 0.2)', # Fill area to the 'next y' trace
            mode='lines', line=dict(color='rgba(255, 165, 0, 0.5)')
        ),
        secondary_y=False
    )

    # Add the energy demand trace on the secondary y-axis
    fig.add_trace(
        go.Scatter(x=plot_df['date'], y=plot_df['energy_mwh'], name='Energy (MWh)', line=dict(color='skyblue', dash='dot')),
        secondary_y=True
    )

    fig.update_layout(title_text=f"Temperature and Energy Demand for {selected_city}", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_yaxes(title_text="Temperature (°F)", secondary_y=False)
    fig.update_yaxes(title_text="Energy Demand (MWh)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

def display_correlation_analysis(df, temp_col, temp_label):
    """Displays a scatter plot to show correlation between temp and energy."""
    st.header(f"Correlation Analysis: {temp_label} vs. Energy")
    
    # Calculate overall correlation
    correlation = df[temp_col].corr(df['energy_mwh'])
    
    col1, col2 = st.columns([3, 1])

    with col1:
        fig = px.scatter(
            df,
            x=temp_col,
            y="energy_mwh",
            color="city",
            trendline="ols", # Add Ordinary Least Squares regression line
            title="Temperature vs. Energy Consumption"
        )
        fig.update_layout(xaxis_title=temp_label, yaxis_title="Energy Demand (MWh)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric(label="Overall Correlation Coefficient", value=f"{correlation:.2f}")
        st.info("""
        **Correlation Coefficient:**
        - **+1:** Perfect positive correlation
        - **0:** No correlation
        - **-1:** Perfect negative correlation
        
        This value measures the strength and direction of the linear relationship between the selected temperature metric and energy demand.
        """)

def display_usage_patterns_heatmap(df, temp_col, temp_label):
    """Displays a heatmap of average energy usage by day of week and temperature."""
    st.header("Usage Patterns Heatmap")
    st.write(f"Analyze the average energy demand based on the day of the week and the selected temperature metric ({temp_label}).")

    city_list = ['All Cities'] + sorted(df['city'].unique())
    selected_city = st.selectbox("Select a City to Analyze", city_list, key="heatmap_city")

    if selected_city == 'All Cities':
        plot_df = df.copy()
    else:
        plot_df = df[df['city'] == selected_city].copy()

    # Feature Engineering: Create day of week and temperature bins
    plot_df['day_of_week'] = plot_df['date'].dt.day_name()
    
    # Define temperature bins from -20F to 130F in 10-degree increments
    bins = list(range(-20, 131, 10))
    labels = [f"{i} to {i+9}°F" for i in bins[:-1]]
    plot_df['temp_bin'] = pd.cut(plot_df[temp_col], bins=bins, labels=labels, right=False)

    # Create pivot table for the heatmap
    heatmap_data = plot_df.pivot_table(
        values='energy_mwh',
        index='temp_bin',
        columns='day_of_week',
        aggfunc='mean',
        observed=False # Explicitly set to silence FutureWarning and maintain behavior
    ).round(0)

    # Order the columns by day of week
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(columns=days_order)

    fig = px.imshow(
        heatmap_data,
        text_auto=True, # Automatically display the values on the heatmap
        aspect="auto",
        labels=dict(x="Day of Week", y="Temperature Range", color="Avg. Energy (MWh)"),
        title=f"Average Daily Energy Demand for {selected_city}"
    )
    st.plotly_chart(fig, use_container_width=True)

def display_data_quality_report():
    """Reads and displays the data quality report from the pipeline run."""
    st.header("Data Quality Report")
    st.write("This report shows any warnings or issues detected during the last data processing run.")

    project_root = os.path.join(os.path.dirname(__file__), '..')
    report_path = os.path.join(project_root, 'data', 'output', 'data_quality_report.json')

    if not os.path.exists(report_path):
        st.info("Data quality report not found. Please run the pipeline to generate it.")
        return

    try:
        with open(report_path, 'r') as f:
            warnings = json.load(f)
        
        if not warnings:
            st.success("✅ No data quality issues were found in the last pipeline run. Great job!")
            return

        st.warning(f"Found {len(warnings)} data quality issue(s).")
        
        # Convert to DataFrame for better display
        warnings_df = pd.DataFrame(warnings)
        
        # Reorder columns for clarity and display
        display_cols = ['level', 'check', 'message', 'file']
        st.dataframe(warnings_df[display_cols], use_container_width=True)

        with st.expander("View Detailed Report (JSON)"):
            st.json(warnings)

    except (json.JSONDecodeError, FileNotFoundError):
        st.error("Could not parse the data quality report. The JSON file may be corrupted or missing.")

if __name__ == "__main__":
    main()