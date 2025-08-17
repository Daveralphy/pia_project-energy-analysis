# US Weather + Energy Analysis Pipeline

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://daveralphy-energy-analysis.streamlit.app/)

A comprehensive, production-ready data pipeline and interactive dashboard designed to analyze the relationship between weather patterns and energy consumption in the United States.

---
## 🚀 Live Demo

**Explore the live, self-sufficient dashboard here:**
[**https://daveralphy-energy-analysis.streamlit.app/**](https://daveralphy-energy-analysis.streamlit.app/)

---
## Table of Contents

1.  [Project Overview](#project-overview)
2.  [Key Features](#key-features)
3.  [Video Presentation](#video-presentation)
4.  [Repository Structure](#repository-structure)
5.  [Setup Instructions](#setup-instructions)
6.  [Usage](#usage)
7.  [Scheduling Automation](#scheduling-automation)
8.  [Dashboard Visualizations](#dashboard-visualizations)
9.  [Data Quality](#data-quality)
10. [AI Collaboration](#ai-collaboration)
11. [Troubleshooting](#troubleshooting)
12. [Contact](#contact)

---
## Project Overview

Energy companies face significant financial and operational challenges due to inaccurate demand forecasting. This project provides a robust solution by demonstrating the strong correlation between weather data and energy consumption. It features an automated data pipeline that fetches, processes, and validates data from NOAA and EIA APIs, and a powerful, self-sufficient Streamlit dashboard for in-depth analysis.

**Business Value:**
* **Cost Optimization:** Improve forecasting to reduce reliance on expensive peak-time power generation and minimize energy waste.
* **Operational Efficiency:** Enable utilities to manage generation capacity and resources more effectively.
* **Data-Driven Decisions:** Provide analysts and stakeholders with a tool to explore complex data relationships without needing to write code.

---
## Key Features

* **Automated Data Pipeline:** Scripts to fetch historical or daily data with robust error handling, logging, and retries.
* **Self-Sufficient Dashboard:** The Streamlit dashboard is not just for viewing data. Users can **add new cities**, **find the required API IDs**, and **trigger a full data pipeline refresh** directly from the user interface.
* **Interactive Visualizations:** A suite of Plotly charts including a geographic map, dual-axis time series, correlation scatter plot, and a usage pattern heatmap.
* **Configuration as Code:** A central `config.yaml` file to manage cities, API endpoints, and data paths, which can also be edited and validated through the dashboard.
* **Data Quality Assurance:** The pipeline automatically checks for missing values, outliers, and data freshness, generating a report for transparency.
* **Production-Ready Code:** Modular, well-organized Python code with a clear project structure, dependency management via `pyproject.toml`, and comprehensive documentation.

---
## Video Presentation

A 3-minute video presentation is available, covering the business problem, a technical walkthrough of the pipeline, a live demo of the self-sufficient dashboard, and key insights.

**Watch the video on YouTube**

[![Project Video Presentation](http://img.youtube.com/vi/aUgApbzkrUI/0.jpg)](https://www.youtube.com/watch?v=aUgApbzkrUI "Project Video Presentation")

---
## Repository Structure

```
pia_project-energy-analysis/
├── README.md                 # This file: Project summary and setup guide
├── AI_USAGE.md               # Detailed log of AI collaboration and learnings
├── pyproject.toml            # Project dependencies and metadata for pip
├── .env                      # Securely stores API keys (not committed to Git)
├── .gitignore                # Specifies files/directories to be ignored by Git
├── run.py                    # Main entry point to run the pipeline and/or dashboard
├── config/
│   └── config.yaml           # Main configuration for cities, APIs, and paths
├── pia_project_energy_analysis/ # Core source code package
│   ├── __init__.py
│   ├── config_loader.py      # Loads .env and config.yaml
│   ├── noaa_fetcher.py       # Fetches weather data from NOAA API
│   ├── eia_fetcher.py        # Fetches energy data from EIA API
│   ├── data_processor.py     # Cleans, transforms, merges, and validates data
│   └── pipeline.py           # Orchestrates the data fetching and processing steps
├── dashboards/
│   └── app.py                # Streamlit application for the interactive dashboard
├── data/
│   ├── output/               # Final, analysis-ready data and quality reports
│   ├── processed/            # Intermediate, per-city processed data
│   └── raw/                  # Original, unprocessed API responses
└── logs/
    └── runner.log            # Log file for pipeline and runner execution
```

---
## Setup Instructions

### 1. Prerequisites
* Python 3.9+
* Git

### 2. Get API Keys
You need free API keys from both NOAA and EIA.
* **NOAA Token:** Request one at [www.ncdc.noaa.gov/cdo-web/token](http://www.ncdc.noaa.gov/cdo-web/token).
* **EIA Key:** Register for one at [www.eia.gov/opendata/register.php](http://www.eia.gov/opendata/register.php).

### 3. Clone the Repository
```bash
git clone https://github.com/Daveralphy/pia_project-energy-analysis.git
cd pia_project-energy-analysis
```

### 4. Set Up Environment and Install Dependencies
1.  **Create and activate a virtual environment:**
    ```bash
    # Create the environment
    python -m venv venv

    # Activate it (use the command for your OS)
    # Windows (PowerShell):
    .\venv\Scripts\Activate.ps1
    # Windows (Command Prompt):
    .\venv\Scripts\activate.bat
    # macOS / Linux:
    source venv/bin/activate
    ```
    Your terminal prompt should now be prefixed with `(venv)`.

2.  **Install dependencies in editable mode:**
    ```bash
    pip install -e .
    ```
    This command reads `pyproject.toml` and installs all required libraries. The `-e` (editable) flag is recommended for development, as it allows your code changes to take effect immediately without reinstalling.

### 5. Configure API Keys for Local Development
1.  In the project root, create a file named `.env`.
2.  Add your API keys to this file:
    ```
    # .env
    NOAA_TOKEN="YOUR_NOAA_TOKEN_HERE"
    EIA_API_KEY="YOUR_EIA_KEY_HERE"
    ```
3.  Save the file. It is already listed in `.gitignore` and will not be committed.

---
## Deployment

To deploy this application to a service like Streamlit Community Cloud, you must provide your API keys as environment variables (or "secrets") in the platform's settings. **Do not commit your `.env` file to your repository.**

### Deploying to Streamlit Community Cloud

1.  **Push your code to a public GitHub repository.** Ensure your `.gitignore` is correctly excluding your local `.env` file and data directories.
2.  **Log in to share.streamlit.io** and click "New app".
3.  **Select your repository** and the correct branch.
4.  The "Main file path" should be `dashboards/app.py`.
5.  **Add your secrets:**
    *   Click on the "Advanced settings..." dropdown.
    *   In the "Secrets" section, add your API keys exactly as they appear in your `.env` file:
        ```toml
        # Streamlit Secrets (secrets.toml format)
        NOAA_TOKEN = "YOUR_NOAA_TOKEN_HERE"
        EIA_API_KEY = "YOUR_EIA_KEY_HERE"
        ```
    *   Click "Save".
6.  **Click "Deploy!".**

Streamlit will securely inject these secrets as environment variables, and your application's `config_loader.py` will automatically pick them up using `os.getenv()`.

---
## Usage

The `run.py` script is the main entry point for the application. Ensure your virtual environment is active before running commands.

### Running the Pipeline
You can run the data pipeline in several modes:

*   **Fetch a specific historical range (e.g., 90 days):**
    ```bash
    python run.py --pipeline-only --fetch-historical 90
    ```
*   **Fetch data for a custom date range:**
    ```bash
    python run.py --pipeline-only --fetch-range 2023-01-01 2023-03-31
    ```
*   **Fetch only yesterday's data (for daily updates):**
    ```bash
    python run.py --pipeline-only --fetch-daily
    ```

### Launching the Dashboard
There are two ways to launch the dashboard:

1.  **Run Pipeline then Launch Dashboard (Recommended):**
    This command runs the pipeline with its default settings (fetching the last year of data) and then automatically opens the dashboard.
    ```bash
    python run.py
    ```

2.  **Launch Dashboard Directly:**
    If you have already generated the data and just want to view the dashboard, you can launch it directly:
    ```bash
    streamlit run dashboards/app.py
    ```

---
## Scheduling Automation

To keep the data fresh automatically, schedule the daily fetch script.

### Cron (Linux/macOS)
1.  Open your crontab: `crontab -e`
2.  Add the following line, replacing `/path/to/your/project` with the absolute path to the `pia_project-energy-analysis` directory. This example runs the script at 3:00 AM daily.
    ```cron
    0 3 * * * /path/to/your/project/venv/bin/python /path/to/your/project/run.py --fetch-daily --pipeline-only >> /path/to/your/project/logs/cron.log 2>&1
    ```

### Task Scheduler (Windows)
1.  Open **Task Scheduler**.
2.  Click **Create Basic Task...**
3.  **Name:** `Energy Data Daily Fetch`
4.  **Trigger:** `Daily`, set a time (e.g., 3:00 AM).
5.  **Action:** `Start a program`.
6.  **Program/script:** `C:\path\to\your\project\venv\Scripts\python.exe` (use your absolute path).
7.  **Add arguments:** `run.py --fetch-daily --pipeline-only`
8.  **Start in:** `C:\path\to\your\project\` (use your absolute path to the project root).
9.  Finish the wizard.

---
## Dashboard Visualizations

1.  **📍 Geographic Overview:** An interactive map displaying the latest temperature, daily energy usage, and percentage change from the previous day for each city.
2.  **📈 Time Series Analysis:** A dual-axis line chart showing the trend of temperature and energy consumption over time. Users can select individual cities or view an aggregate, with weekends highlighted.
3.  **🔗 Correlation Analysis:** A scatter plot illustrating the relationship between temperature and energy consumption. A regression line, its equation, R-squared value, and the correlation coefficient quantify the relationship.
4.  **🗓️ Usage Patterns Heatmap:** A heatmap visualizing average energy usage based on temperature ranges and the day of the week, revealing clear consumption patterns.

---
## Data Quality

The pipeline automatically performs data quality checks and generates a report (`data/output/data_quality_report.json`) which is viewable in the dashboard.
*   **Missing Values:** Identifies and quantifies any missing entries in the raw data.
*   **Outlier Detection:** Flags data points outside of logical ranges (e.g., temperatures > 130°F, negative energy usage).
*   **Data Freshness:** Compares the latest data timestamp against the current date to ensure the pipeline is running correctly.

---
## AI Collaboration

This project was developed with significant assistance from AI tools. A detailed breakdown of the AI tools used, effective prompts, identified AI mistakes and their fixes, and an estimate of time saved is documented in the **`AI_USAGE.md`** file.

---
## Troubleshooting

*   **`ModuleNotFoundError`:** Ensure your virtual environment is **activated**. The `(venv)` prefix should be visible in your terminal.
*   **API Errors (`401`, `403`):** Double-check that your API keys in the `.env` file are correct and have no extra spaces.
*   **Permission Errors on Windows:** If you have trouble creating the virtual environment or installing packages, try running your terminal (PowerShell/CMD) as an Administrator.
*   **No Data from API:** Verify the `noaa_station_id` and `eia_ba_code` in `config/yaml` are correct. You can use the ID finder tool in the dashboard to verify them.

---
## Contact

For any questions or feedback, please reach out:
*   **Name:** Raphael Daveal Eferire
*   **Email:** raphaeldaveal@gmail.com
*   **GitHub:** Daveralphy