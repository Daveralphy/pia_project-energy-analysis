import subprocess
import sys
import os
import argparse

def run_pipeline(args):
    """
    Imports and runs the main data pipeline function.
    Accepts parsed arguments and returns True on success, False on failure.
    """
    print("--- Starting Data Pipeline ---")
    try:
        # Explicitly add the project root to the Python path.
        # This makes the script runnable from anywhere and resolves import issues.
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)

        # Import the main function from the pipeline script
        from pia_project_energy_analysis.pipeline import main as run_pipeline_main
        run_pipeline_main(args)
        print("--- Data Pipeline Finished Successfully ---")
        return True
    except Exception as e:
        print(f"--- An error occurred during the pipeline execution: {e} ---")
        # For more detailed debugging, you might want to log the full traceback
        # import traceback
        # traceback.print_exc()
        return False

def run_dashboard():
    """Launches the Streamlit dashboard using a subprocess."""
    print("\n--- Launching Streamlit Dashboard ---")
    dashboard_path = os.path.join('dashboards', 'app.py')
    try:
        # Use sys.executable to ensure we use the python from the current venv
        subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path], check=True)
    except FileNotFoundError:
        print(f"Error: Could not find streamlit. Is it installed in your environment '{sys.executable}'?")
    except subprocess.CalledProcessError as e:
        print(f"Error launching dashboard: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the data pipeline and/or launch the dashboard.")
    parser.add_argument(
        '--pipeline-only',
        action='store_true',
        help='If set, only runs the data pipeline and then exits.'
    )
    # Add pipeline-specific arguments here
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--fetch-historical", type=int, metavar='DAYS', help="Fetch historical data for the specified number of past days.")
    group.add_argument("--fetch-daily", action="store_true", help="Fetch data for the last full day (yesterday).")
    group.add_argument("--fetch-range", nargs=2, metavar=('START_DATE', 'END_DATE'), help="Fetch data for a specific date range (YYYY-MM-DD).")

    args = parser.parse_args()

    # The pipeline is always run.
    pipeline_success = run_pipeline(args)

    # The dashboard is only launched if we are NOT in pipeline-only mode
    # and the pipeline was successful.
    if not args.pipeline_only:
        if pipeline_success:
            run_dashboard()
        else:
            print("\nDashboard will not be launched due to a failure in the data pipeline.")