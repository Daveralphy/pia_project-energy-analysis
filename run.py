import subprocess
import sys
import os
import logging
import argparse

# Configure logging to output to console and a file as per project structure
LOG_FILE = os.path.join('logs', 'runner.log')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)]
)

def run_pipeline(args):
    """
    Imports and runs the main data pipeline function.
    Accepts parsed arguments and returns True on success, False on failure.
    """
    logging.info("--- Starting Data Pipeline ---")
    try:
        # Explicitly add the project root to the Python path.
        # This makes the script runnable from anywhere and resolves import issues.
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)

        # Import the main function from the pipeline script
        from pia_project_energy_analysis.pipeline import main as pipeline_main
        pipeline_main(args)
        logging.info("--- Data Pipeline Finished Successfully ---")
        return True
    except Exception as e:
        # exc_info=True automatically includes exception traceback in the log
        logging.error("An error occurred during the pipeline execution.", exc_info=True)
        return False

def run_dashboard():
    """Launches the Streamlit dashboard using a subprocess."""
    logging.info("--- Launching Streamlit Dashboard ---")
    dashboard_path = os.path.join('dashboards', 'app.py')
    try:
        # Use sys.executable to ensure we use the python from the current venv
        subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path], check=True)
    except FileNotFoundError:
        logging.error(f"Could not find streamlit. Is it installed in your environment '{sys.executable}'?")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error launching dashboard: {e}")

def main():
    """Main function to parse arguments and orchestrate the application."""
    parser = argparse.ArgumentParser(description="Run the data pipeline and/or launch the dashboard.")
    parser.add_argument(
        '--pipeline-only',
        action='store_true',
        help='If set, only runs the data pipeline and then exits.'
    )
    # Add pipeline-specific arguments for data fetching
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--fetch-historical", type=int, metavar='DAYS', help="Fetch historical data for the specified number of past days.")
    group.add_argument("--fetch-daily", action="store_true", help="Fetch data for the last full day (yesterday).")
    group.add_argument("--fetch-range", nargs=2, metavar=('START_DATE', 'END_DATE'), help="Fetch data for a specific date range (YYYY-MM-DD).")

    args = parser.parse_args()

    pipeline_success = run_pipeline(args)

    if not args.pipeline_only:
        if pipeline_success:
            run_dashboard()
        else:
            logging.warning("Dashboard will not be launched due to a failure in the data pipeline.")

if __name__ == "__main__":
    main()