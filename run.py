import subprocess
import sys
import os

def run_pipeline():
    """
    Imports and runs the main data pipeline function.
    Returns True on success, False on failure.
    """
    print("--- 🚀 Starting Data Pipeline ---")
    try:
        # Import the main function from the pipeline script
        from src.pipeline import main as run_pipeline_main
        run_pipeline_main()
        print("--- ✅ Data Pipeline Finished Successfully ---")
        return True
    except Exception as e:
        print(f"--- ❌ An error occurred during the pipeline execution: {e} ---")
        # For more detailed debugging, you might want to log the full traceback
        # import traceback
        # traceback.print_exc()
        return False

def run_dashboard():
    """Launches the Streamlit dashboard using a subprocess."""
    print("\n--- 📊 Launching Streamlit Dashboard ---")
    dashboard_path = os.path.join('dashboards', 'app.py')
    try:
        # Use sys.executable to ensure we use the python from the current venv
        subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path], check=True)
    except FileNotFoundError:
        print(f"Error: Could not find streamlit. Is it installed in your environment '{sys.executable}'?")
    except subprocess.CalledProcessError as e:
        print(f"Error launching dashboard: {e}")

if __name__ == "__main__":
    if run_pipeline():
        run_dashboard()
    else:
        print("\nDashboard will not be launched due to a failure in the data pipeline.")