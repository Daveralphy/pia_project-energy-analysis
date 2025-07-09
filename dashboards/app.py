import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
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
    st.title("U.S. Weather and Energy Consumption Analysis")

    df = load_data()

    # Create tabs for different analysis views
    tab1, tab2, tab3 = st.tabs(["Geographic Overview", "Time Series Analysis", "Correlation Analysis"])

    with tab1:
        display_geographic_overview(df)
    
    with tab2:
        display_time_series(df)

    with tab3:
        display_correlation_analysis(df)

def display_geographic_overview(df):
    """Displays an interactive map of the latest data for each city."""
    st.header("Geographic Overview")
    latest_data = df.loc[df.groupby('city')['date'].idxmax()]

    if 'latitude' not in latest_data.columns or latest_data['latitude'].isnull().any():
        st.warning("City coordinates are missing. Cannot display map. Please check `config.yaml`.")
        return

    fig = px.scatter_map(
        latest_data,
        lat="latitude",
        lon="longitude",
        size="energy_mwh",
        color="TMAX_F",
        hover_name="city",
        hover_data={"TMAX_F": ":.1f°F", "energy_mwh": ":, MWh", "latitude": False, "longitude": False},
        color_continuous_scale=px.colors.sequential.Plasma,
        size_max=50,
        zoom=3,
        map_style="carto-positron"
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

def display_time_series(df):
    """Displays the time series analysis chart."""
    st.header("Time Series Analysis: Temperature vs. Energy Demand")
    city_list = ['All Cities'] + sorted(df['city'].unique())
    selected_city = st.selectbox("Select a City to Analyze", city_list, key="time_series_city")

    if selected_city == 'All Cities':
        plot_df = df.groupby('date').agg({'TMAX_F': 'mean', 'energy_mwh': 'sum'}).reset_index()
    else:
        plot_df = df[df['city'] == selected_city].copy()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['TMAX_F'], name='Max Temperature (°F)', line=dict(color='orange')), secondary_y=False)
    fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['energy_mwh'], name='Energy (MWh)', line=dict(color='skyblue', dash='dot')), secondary_y=True)
    fig.update_layout(title_text=f"Temperature and Energy Demand for {selected_city}", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Max Temperature (°F)", secondary_y=False)
    fig.update_yaxes(title_text="Energy Demand (MWh)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

def display_correlation_analysis(df):
    """Displays a scatter plot to show correlation between temp and energy."""
    st.header("Correlation Analysis")
    
    # Calculate overall correlation
    correlation = df['TMAX_F'].corr(df['energy_mwh'])
    
    col1, col2 = st.columns([3, 1])

    with col1:
        fig = px.scatter(
            df,
            x="TMAX_F",
            y="energy_mwh",
            color="city",
            trendline="ols", # Add Ordinary Least Squares regression line
            title="Temperature vs. Energy Consumption"
        )
        fig.update_layout(xaxis_title="Max Temperature (°F)", yaxis_title="Energy Demand (MWh)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric(label="Overall Correlation Coefficient", value=f"{correlation:.2f}")
        st.info("""
        **Correlation Coefficient:**
        - **+1:** Perfect positive correlation
        - **0:** No correlation
        - **-1:** Perfect negative correlation
        
        This value measures the strength and direction of the linear relationship between daily max temperature and energy demand.
        """)

if __name__ == "__main__":
    main()