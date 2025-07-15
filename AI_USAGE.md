# AI Collaboration Log: Building the Energy Analysis Pipeline

This document details the use of AI coding assistants (specifically, Gemini Code Assist) throughout the development of the "US Weather + Energy Analysis Pipeline" project. The goal is to provide transparency into the development process, showcase effective AI collaboration techniques, and document lessons learned.

**AI Tool Used:** Gemini Code Assist
**Estimated Time Saved:** Approximately 40-50% of total development time. The AI significantly accelerated boilerplate code generation, debugging, and initial script creation, allowing more time to be spent on refining logic, improving data quality checks, and enhancing the dashboard's user experience.

---

## Table of Contents

1.  [Phase 1: Project Scoping and Structure](#phase-1-project-scoping-and-structure)
2.  [Phase 2: Core Logic - Data Fetching](#phase-2-core-logic---data-fetching)
3.  [Phase 3: Data Processing and Quality Checks](#phase-3-data-processing-and-quality-checks)
4.  [Phase 4: Pipeline Orchestration](#phase-4-pipeline-orchestration)
5.  [Phase 5: Dashboard Development with Streamlit](#phase-5-dashboard-development-with-streamlit)
6.  [Phase 6: Documentation and Finalization](#phase-6-documentation-and-finalization)
7.  [Overall Learnings and Conclusion](#overall-learnings-and-conclusion)

---

## Phase 1: Project Scoping and Structure

**Goal:** Establish a clean, scalable, and professional repository structure for a data engineering project.

**My Prompt to AI:**
> "Design a professional Python project structure for a data pipeline that fetches data from two APIs, processes it, and serves it to a Streamlit dashboard. Include directories for source code, tests, configuration, data, logs, and notebooks. Also, suggest a good `.gitignore` file for a Python project and a `pyproject.toml` with common data science libraries like pandas, requests, and streamlit."

**AI's Contribution:**
*   The AI generated a directory tree very similar to the one used in the final project.
*   It provided a standard `.gitignore` file that included entries for `.venv`, `.env`, `__pycache__/`, `*.log`, and data directories, which was crucial for keeping the repository clean and secure.
*   It generated a `pyproject.toml` file with `[project.dependencies]` listing `pandas`, `requests`, `streamlit`, `plotly`, `python-dotenv`, `pyyaml`, and `tenacity`.

**My Refinements & Learnings:**
*   I adopted the AI's proposed structure almost entirely, as it aligned with industry best practices.
*   I manually added `AI_USAGE.md` and `video_link.md` to the root directory as project-specific documentation requirements. This was a good reminder that while AI provides excellent templates, the developer must tailor them to specific project needs.

---

## Phase 2: Core Logic - Data Fetching

**Goal:** Write robust functions to fetch data from the NOAA and EIA APIs, complete with error handling and automatic retries.

**My Prompt(s) to AI:**
> "Write a Python function using the `requests` library to fetch data from the NOAA CDO v2 API. The function should accept an API token, station ID, and start/end dates. It must include error handling for HTTP errors and use the `tenacity` library for automatic retries with exponential backoff if the request fails."

> "Now, do the same for the EIA API. Note that it uses an API key as a URL parameter, not a header."

**AI's Contribution:**
*   The AI generated a complete Python function for the NOAA API, including the `@retry` decorator from `tenacity` with `wait_exponential` and `stop_after_attempt`.
*   It correctly placed the NOAA token in the request `headers`.
*   It provided a `try...except` block to catch `requests.exceptions.HTTPError` and log failures.
*   For the EIA prompt, it correctly adapted the function to pass the API key as a query parameter in the URL.

**My Refinements & Learnings:**
*   **Mistake Identified:** The AI's initial NOAA function didn't know the exact name of the temperature field (`TAVG`) or that the value was in tenths of a degree Celsius. I had to consult the NOAA API documentation to find the correct `datatypeid` and apply the necessary division by 10.
*   **Refinement:** The AI's JSON parsing was generic (`response.json()`). I had to add specific key lookups (e.g., `['results']`) to navigate the nested JSON structure returned by the APIs. This was a key lesson in "AI gets you 90% there, you provide the last 10% of domain-specific detail."

---

## Phase 3: Data Processing and Quality Checks

**Goal:** Clean the raw data, merge the two sources, perform unit conversions, and implement data quality checks.

**My Prompt to AI:**
> "I have two pandas DataFrames: `weather_df` with columns `['date', 'station', 'temp_c']` and `energy_df` with `['date', 'region_code', 'usage_mwh']`. Write a Python function that:
> 1. Converts the 'temp_c' column to Fahrenheit into a new 'temp_f' column.
> 2. Merges the two DataFrames on the 'date' column.
> 3. Implements data quality checks: log any rows where 'temp_f' is outside -50 to 130°F, or where 'usage_mwh' is negative."

**AI's Contribution:**
*   The AI provided a function that correctly implemented the Celsius to Fahrenheit conversion formula: `(df['temp_c'] * 9/5) + 32`.
*   It used `pd.merge(weather_df, energy_df, on='date', how='inner')` to combine the datasets.
*   It generated boolean masks to identify outlier data points (e.g., `df['temp_f'] < -50`).

**My Refinements & Learnings:**
*   **Data Types:** I had to add pre-processing steps to ensure the `date` columns in both DataFrames were converted to the same `datetime` format (`pd.to_datetime`) before merging. The AI assumed they were already compatible.
*   **Quality Reporting:** The AI's initial code just printed outliers to the console. I improved this by creating a separate list of dictionaries to hold the outlier information, which could then be formally logged or saved as a quality report. This made the check more robust for a production pipeline.

---

## Phase 4: Pipeline Orchestration

**Goal:** Create a master script (`pipeline.py`) to run the entire process, controlled by command-line arguments for different run modes (historical vs. daily).

**My Prompt to AI:**
> "Create a main Python script using the `argparse` library. It needs two mutually exclusive arguments: `--fetch-historical` which takes an integer for the number of days, and `--fetch-daily` which is a flag. Based on the argument, it should calculate the correct start and end dates and then call placeholder functions `run_fetch_and_process(start_date, end_date)`. Also, set up basic file logging."

**AI's Contribution:**
*   The AI generated the complete `argparse` setup, including creating a mutually exclusive group, which is a non-trivial part of the library.
*   It correctly used `datetime` and `timedelta` to calculate the date ranges based on the user's input.
*   It provided the standard `logging.basicConfig` configuration to set up logging to `logs/pipeline.log`.

**My Refinements & Learnings:**
*   I replaced the AI's placeholder function calls with my actual `data_fetcher` and `data_processor` functions, connecting the different modules of the project. This integration step was entirely manual and required careful management of data flow (e.g., passing DataFrames between functions).

---

## Phase 5: Dashboard Development with Streamlit

**Goal:** Build the interactive visualizations for the dashboard. This was done one chart at a time.

**My Prompt(s) to AI (Example for the Scatter Plot):**
> "Using Streamlit and Plotly Express, create a scatter plot from a pandas DataFrame. The x-axis should be 'Temperature_F', and the y-axis 'Energy_Usage_MWh'. Color the points by 'City'. Add a single regression line for all data points. Also, show me how to calculate the Pearson correlation coefficient and R-squared value and display them as text in the Streamlit app."

**AI's Contribution:**
*   Provided the correct Plotly Express call: `px.scatter(df, x='Temperature_F', y='Energy_Usage_MWh', color='City', trendline='ols')`.
*   Showed how to calculate correlation with `df['col1'].corr(df['col2'])`.
*   For R-squared, it provided a more complex but correct approach using `scipy.stats.linregress` or `statsmodels.api`, which gives more detailed regression statistics.
*   It demonstrated using `st.plotly_chart` to render the plot and `st.metric` or `st.write` to display the calculated stats.

**My Refinements & Learnings:**
*   **Mistake Identified:** The AI's first attempt at the dual-axis time series chart was overly complex. I simplified the prompt to "create a Plotly graph with a secondary y-axis" and got a much cleaner example using `make_subplots`.
*   **Interactivity:** The AI provided the code for individual charts. My main task was to wire them together with Streamlit widgets. I created a city selector (`st.selectbox`) and used its output to filter the main DataFrame before passing it to the AI-generated plotting functions. This created the interactive experience.
*   **Aesthetics:** I manually fine-tuned the charts' layouts, colors, and hover data using the `update_layout` and `update_traces` methods in Plotly to match the project's desired look and feel.

---

## Phase 6: Documentation and Finalization

**Goal:** Generate a high-quality, comprehensive `README.md` file to explain the project to other developers and stakeholders.

**My Prompt to AI:**
> "Generate a professional `README.md` for my 'US Weather + Energy Analysis' Python project. Include these sections: Project Overview, Business Value, Repository Structure (in a tree format), Setup Instructions (prerequisites, API keys, virtual env, pip install from pyproject.toml), How to Run (for historical and daily data), a description of the four main Dashboard Visualizations, and a Troubleshooting section for common errors like API key issues and `ModuleNotFoundError`."

**AI's Contribution:**
*   The AI generated a nearly complete `README.md` file with well-written prose for each section.
*   It created a markdown code block for the directory tree.
*   It provided clear, numbered steps for the setup and execution processes.
*   The troubleshooting section was particularly helpful, as it anticipated common user errors.

**My Refinements & Learnings:**
*   I fact-checked and personalized all the content. I replaced placeholder URLs with my actual repository link, filled in my contact information, and rewrote the descriptions of the visualizations to be more specific to my final implementation. The AI provided an excellent first draft, and my role was that of an editor and fact-checker.

---

## Overall Learnings and Conclusion

Collaborating with an AI assistant was like having a very fast junior developer and a powerful search engine rolled into one.

*   **Strengths:** The AI excelled at generating boilerplate code (API functions, `argparse` setup, file I/O), writing documentation drafts, and providing examples for new libraries (`tenacity`, `plotly`). This dramatically reduced development time.
*   **Weaknesses:** The AI lacked project-specific context. It didn't know the exact format of an API response or the specific business logic I wanted to implement. It sometimes hallucinated library functions or parameters that didn't exist, requiring verification.
*   **Synergy:** The most effective workflow was a tight loop of **Prompt -> Generate -> Verify -> Refine**. The AI provided the initial code, and I used my expertise to debug, integrate, and add the nuanced logic required to make it work perfectly for this specific project.

In conclusion, AI did not "write the project for me." Rather, it acted as a powerful force multiplier, handling the repetitive and standard tasks, which freed me up to focus on the more creative and challenging aspects of data engineering: ensuring data quality, designing meaningful analysis, and building a polished, user-friendly end product.