# US Weather + Energy Analysis Pipeline

## Project Overview

Energy companies face significant financial losses due to inaccurate demand forecasting. This project aims to demonstrate how combining weather data with energy consumption patterns can significantly improve these forecasts, helping utilities optimize power generation, reduce waste, and lower operational costs. This solution provides a production-ready data pipeline, robust data quality checks, and an interactive dashboard for insightful analysis.

**Business Value:**
* **Cost Optimization:** Better forecasting reduces the need for expensive peak-time power generation and minimizes energy waste.
* **Operational Efficiency:** Utilities can more effectively manage resources and generation capacity.
* **Enhanced Reliability:** Proactive insights help maintain grid stability and prevent outages.

## Table of Contents

1.  [Project Deliverables](#project-deliverables)
2.  [Repository Structure](#repository-structure)
3.  [Setup Instructions](#setup-instructions)
    * [1. Prerequisites](#1-prerequisites)
    * [2. API Key Registration](#2-api-key-registration)
    * [3. Clone the Repository](#3-clone-the-repository)
    * [4. Virtual Environment & Dependencies](#4-virtual-environment--dependencies)
    * [5. Configuration Files](#5-configuration-files)
4.  [How to Run the Pipeline](#how-to-run-the-pipeline)
    * [Fetch Historical Data (One-Time)](#fetch-historical-data-one-time)
    * [Run Daily Data Fetch](#run-daily-data-fetch)
    * [Scheduling with Cron (Linux/macOS)](#scheduling-with-cron-linuxmacos)
    * [Scheduling with Task Scheduler (Windows)](#scheduling-with-task-scheduler-windows)
5.  [How to Run the Dashboard](#how-to-run-the-dashboard)
6.  [Data Quality Checks](#data-quality-checks)
    * [Missing Values](#missing-values)
    * [Outlier Detection](#outlier-detection)
    * [Data Freshness](#data-freshness)
7.  [Analysis and Visualizations](#analysis-and-visualizations)
8.  [AI Collaboration & Learning (`AI_USAGE.md`)](#ai-collaboration--learning-ai_usagemd)
9.  [Video Presentation](#video-presentation)
10. [Peer Review](#peer-review)
11. [Troubleshooting](#troubleshooting)
12. [Contact](#contact)

---

## Project Deliverables

This project delivers the following key components:

1.  **Automated Data Pipeline:** A Python script designed to run daily, fetching fresh weather and energy consumption data for 5 key US cities (New York, Chicago, Houston, Phoenix, Seattle) from NOAA and EIA APIs. It includes robust error handling, logging, and a separate script for initial historical data pull (90 days).
2.  **Data Quality Report:** Automated checks for missing values, outliers (e.g., extreme temperatures, negative energy usage), and data freshness. A basic report/dashboard component will show these metrics over time.
3.  **Analysis Dashboard with Specific Visualizations (Streamlit):**
    * **Geographic Overview:** Interactive US map showing current city data (temp, usage, % change from yesterday) with color-coding.
    * **Time Series Analysis:** Dual-axis line chart of temperature vs. energy consumption over 90 days, with city selection and weekend highlighting.
    * **Correlation Analysis:** Scatter plot of temperature vs. energy consumption, color-coded by city, with regression line, R-squared, and correlation coefficient.
    * **Usage Patterns Heatmap:** Heatmap of average energy usage by temperature range and day of week, with city filtering and value annotations.
4.  **Production-Ready Code:** Modular, well-organized Python code with a clear configuration file, comprehensive logging, and thorough documentation (comments, README).

---

## Repository Structure

```
pia_project-energy-analysis/
├── README.md                 # This file: Business-focused project summary and setup guide
├── AI_USAGE.md               # Documentation of AI assistance, prompts, and lessons learned
├── pyproject.toml            # Project dependencies and metadata (managed by pip)
├── .env                      # Environment variables (e.g., API keys - DO NOT COMMIT!)
├── .gitignore                # Specifies files/directories to be ignored by Git
├── config/
│   └── config.yaml           # API keys (placeholders), cities list, API endpoints, data paths
├── pia_project_energy_analysis/ # Source code package
│   ├── __init__.py
│   ├── config_loader.py      # Loads .env and config.yaml
│   ├── noaa_fetcher.py       # Fetches weather data from NOAA API
│   ├── eia_fetcher.py        # Fetches energy data from EIA API
│   ├── data_processor.py     # Cleans, transforms, and merges data
│   └── pipeline.py           # Orchestrates the data fetching and processing steps
├── dashboards/
│   └── app.py                # Streamlit application for the interactive dashboard
├── data/
│   ├── raw/                  # Stores original, un-processed API responses (e.g., JSON, CSV)
│   └── processed/            # Stores clean, analysis-ready data (e.g., CSV)
├── notebooks/
│   └── exploration.ipynb     # Optional: For initial data exploration and prototyping
├── tests/
│   └── test_pipeline.py      # Basic unit tests for critical functions
└── video_link.md             # Contains the link to your video presentation
```

---

## Setup Instructions

Follow these steps to get the project up and running on your local machine.

### 1. Prerequisites

* **Python 3.9+**: Ensure you have Python installed. You can download it from [python.org](https://www.python.org/downloads/).
* **Git**: For cloning the repository.
* **Internet Connection**: To fetch data from APIs.

### 2. API Key Registration

You need API keys from both NOAA and EIA. These are free for personal/research use.

* **NOAA Climate Data Online API Token:**
    1.  Visit: [https://www.ncdc.noaa.gov/cdo-web/token](https://www.ncdc.noaa.gov/cdo-web/token)
    2.  Enter your email and click "Submit".
    3.  Your token will be sent to your email address.

* **EIA Energy API Key:**
    1.  Visit: [https://www.eia.gov/opendata/register.php](https://www.eia.gov/opendata/register.php)
    2.  Fill out the registration form and click "Register".
    3.  Your API key will be sent to your email address.

### 3. Clone the Repository

Open your terminal (or Git Bash on Windows) and clone the repository:

```bash
git clone [https://github.com/](https://github.com/)[YourUsername]/pia_project-energy-analysis.git
cd pia_project-energy-analysis
```
(Replace `[YourUsername]` with your actual GitHub username.)

### 4. Virtual Environment & Dependencies

It's highly recommended to use a virtual environment to manage project dependencies.

1.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    ```

2.  **Activate the virtual environment:**
    * **On macOS/Linux (and Git Bash):**
        ```bash
        source .venv/bin/activate
        ```
    * **On Windows (Command Prompt):**
        ```bash
        .venv\Scripts\activate.bat
        ```
    * **On Windows (PowerShell):**
        ```powershell
        .venv\Scripts\Activate.ps1
        ```
    Your terminal prompt should now show `(.venv)` indicating the environment is active.

3.  **Install project dependencies:**
    ```bash
    pip install .
    ```
    This command reads `pyproject.toml` and installs all necessary libraries (e.g., `requests`, `pandas`, `streamlit`, `plotly`, `scipy`, `python-dotenv`, `pyyaml`, `tenacity`).

### 5. Configuration Files

1.  **Populate `.env`:**
    * Open the `.env` file in the root of your project.
    * Add your API keys obtained in Step 2:
        ```
        # .env
        NOAA_TOKEN="YOUR_ACTUAL_NOAA_API_TOKEN_HERE"
        EIA_API_KEY="YOUR_ACTUAL_EIA_API_KEY_HERE"
        ```
    * Save the file. **Do not commit this file to GitHub!** (`.gitignore` should prevent this).

2.  **Verify `config/config.yaml`:**
    * The `config/config.yaml` file is pre-populated with city information, API endpoints, and data paths.
    * Review its content to ensure it matches the project requirements (NOAA station IDs, EIA region codes, city coordinates). You may add custom thresholds for data quality checks here if desired.

---

## How to Run the Pipeline

Ensure your virtual environment is activated before running any pipeline scripts.

### Fetch Historical Data (One-Time)

For initial setup and analysis, you'll need 90 days of historical data.

```bash
python run.py --fetch-historical 90
```
This command will fetch 90 days of data, process it, and store it in `data/processed/`. Logs will be written to `logs/pipeline.log`.

### Run Daily Data Fetch

To fetch the latest day's data, run:

```bash
python src/pipeline.py --fetch-daily
```
This command is intended to be run daily to update your dataset.

### Scheduling with Cron (Linux/macOS)

To automate daily data fetches on Linux or macOS, you can use `cron`.

1.  Open your crontab for editing:
    ```bash
    crontab -e
    ```
2.  Add a line like the following to run the pipeline daily (e.g., at 3:00 AM UTC). Replace `/path/to/your/project` with the absolute path to your `pia_project-energy-analysis` directory.

    ```cron
    0 3 * * * /path/to/your/project/.venv/bin/python /path/to/your/project/run.py --fetch-daily --pipeline-only >> /path/to/your/project/logs/cron.log 2>&1
    ```
    * `0 3 * * *`: Runs at 03:00 every day.
    * `/path/to/your/project/.venv/bin/python`: Absolute path to your virtual environment's Python interpreter.
    * `--pipeline-only`: Ensures that only the data pipeline runs, without attempting to launch the dashboard.
    * `>> ...`: Redirects all output (stdout and stderr) to a cron-specific log file for debugging.

### Scheduling with Task Scheduler (Windows)

For Windows, use the Task Scheduler.

1.  Search for "Task Scheduler" in the Start Menu and open it.
2.  Click "Create Basic Task..."
3.  **Name:** e.g., "Energy Data Daily Fetch"
4.  **Trigger:** Daily, specify a time (e.g., 3:00 AM).
5.  **Action:** "Start a program"
6.  **Program/script:** `C:\path\to\your\pia_project-energy-analysis\.venv\Scripts\python.exe` (Replace with your actual path)
7.  **Add arguments (optional):** `run.py --fetch-daily --pipeline-only`
8.  **Start in (optional):** `C:\path\to\your\pia_project-energy-analysis` (This is important! Set it to your project's root directory)
9.  Finish the wizard. You might need to adjust user permissions in the task's properties to "Run with highest privileges".


## How to Run the Dashboard

The interactive dashboard is built with Streamlit. The recommended way to launch it is via the main `run.py` script, which ensures the data is up-to-date before launching the UI.

1.  **Ensure your virtual environment is activated.**
2.  **Navigate to the project root directory.**
3.  **Run the application:**
    ```bash
    python run.py
    ```
    This will first run the pipeline (using the default 365-day historical fetch if no arguments are given) and then automatically launch the dashboard in your web browser.

    **To launch the dashboard directly without running the pipeline first:**
    ```bash
    streamlit run dashboards/app.py
    ```

---

## Data Quality Checks

The `data_processor.py` module includes automated data quality checks that are performed as part of the pipeline. These checks ensure the reliability and integrity of the data used for analysis.

### Missing Values
* **What it does:** Identifies and quantifies any missing entries (`NaN` or `None`) within the fetched temperature and energy consumption datasets.
* **Why it matters:** Missing data can lead to skewed analyses, incorrect visualizations, and unreliable forecasts. Understanding where and how much data is missing informs imputation strategies or flags unreliable data sources.

### Outlier Detection
* **What it does:** Flags data points that fall outside expected ranges:
    * Temperatures: Values outside -50°F to 130°F are marked as outliers.
    * Energy Consumption: Negative energy consumption values are flagged.
* **Why it matters:** Extreme or illogical values are often data entry errors, sensor malfunctions, or API glitches. Identifying and handling them prevents these erroneous points from distorting statistical models and visualizations.

### Data Freshness
* **What it does:** Compares the timestamp of the latest fetched data with the current date.
* **Why it matters:** Ensures the pipeline is actively pulling recent data. Stale data can lead to outdated and irrelevant insights, particularly for demand forecasting where current conditions are paramount.

A simple report showing these metrics will be generated, and can be viewed in the logs or eventually integrated into the dashboard for historical quality tracking.

## Analysis and Visualizations

The Streamlit dashboard provides four key visualizations to explore the relationship between weather and energy consumption:

1.  **Geographic Overview:** An interactive map displaying current temperature, daily energy usage, and percentage change from the previous day for each of the five selected cities. Color-coding (red for high usage, green for low) provides an immediate visual summary.
2.  **Time Series Analysis:** A dual-axis line chart showing the trend of temperature (solid line) and energy consumption (dotted line) over the last 90 days. Users can select individual cities or view an aggregate, with weekends highlighted to identify weekly patterns.
3.  **Correlation Analysis:** A scatter plot illustrating the relationship between temperature and energy consumption across all cities. Each city's data points are color-coded. A regression line, its equation, R-squared value, and the correlation coefficient are displayed to quantify the strength and direction of the relationship. Hover tooltips provide exact values and dates.
4.  **Usage Patterns Heatmap:** A heatmap visualizing average energy usage based on temperature ranges (Y-axis) and day of the week (X-axis). A color scale from blue (low usage) to red (high usage) quickly reveals consumption patterns. Filtering by city allows for regional pattern comparison, and text annotations on cells show exact average values.

---

## AI Collaboration & Learning (`AI_USAGE.md`)

This project was developed with significant assistance from AI tools. A detailed breakdown of the AI tools used, effective prompts, identified AI mistakes and their fixes, and an estimate of time saved is documented in the `AI_USAGE.md` file. Reviewing this file provides insight into the problem-solving process and the effective integration of AI in development workflows.

---

## Video Presentation

A 3-minute video presentation is available, covering:
* The business problem and its impact.
* A technical walkthrough of the pipeline architecture and a live demo.
* Key results and insights from the dashboard.
* Reflections on AI collaboration and lessons learned.

**Watch the video here:** [https://youtu.be/aUgApbzkrUI](https://youtu.be/aUgApbzkrUI)

---

## Peer Review

This project was peer-reviewed by:
* **Reviewer Name:** Dallan Quass
* **Feedback Received:** None yet.
* **Actions Taken:** Pending

---

## Troubleshooting

* **`Permission denied` errors:**
    * On Windows, ensure your terminal (Git Bash, VS Code integrated terminal) is run **as administrator**. Close and reopen it with elevated privileges.
    * Check if any other process is holding a lock on the `.venv` directory. A system restart can often resolve this.
* **API `403 Forbidden` / `401 Unauthorized`:**
    * Verify your API keys in the `.env` file are correct and accurately copied from NOAA/EIA.
    * Ensure no extra spaces or characters are around the keys.
    * Double-check that you're using the correct key type (token for NOAA, key for EIA) in the correct part of the request (header for NOAA, query parameter for EIA).
* **`ModuleNotFoundError`:**
    * Ensure your virtual environment is **activated** (`(.venv)` in your terminal prompt).
    * Make sure you ran `pip install .` within the activated environment.
* **No data returned from API:**
    * Verify API parameters (`datasetid`, `stationid`, `startdate`, `enddate`, `datatypeid` for NOAA; `region` for EIA) match the documentation and `config.yaml`.
    * Check for correct date formats (`YYYY-MM-DD`).
    * Be aware of API rate limits. Implement `tenacity` for retries with backoff.
* **Temperature values seem off:**
    * Remember NOAA temperature values are in **tenths of degrees Celsius**. You need to convert them to Fahrenheit (multiply by 0.1, then C to F formula: `(C * 9/5) + 32`).

---

## Contact

For any questions or feedback, please reach out:

* **Name:** Raphael Daveal Eferire
* **Email:** raphaeldaveal@gmail.com
* **GitHub:** https://github.com/Daveralphy
