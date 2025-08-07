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
> "Design a professional Python project structure for a data pipeline that fetches data from two APIs, processes it, and serves it to a Streamlit dashboard. Include directories for source code, tests, configuration, data, logs, and notebooks. Also, suggest a good `.gitignore` file and a `pyproject.toml` with common data science libraries."

**AI's Contribution:**
*   The AI generated a directory tree that was nearly identical to the final project structure.
*   It provided a standard `.gitignore` file that included entries for `.venv`, `.env`, `__pycache__/`, `*.log`, and data directories, which was crucial for keeping the repository clean and secure.
*   It generated a `pyproject.toml` file with `[project.dependencies]` listing `pandas`, `requests`, `streamlit`, `plotly`, `python-dotenv`, `pyyaml`, and `tenacity`.

**My Refinements & Learnings:**
*   I adopted the AI's proposed structure almost entirely, as it aligned with industry best practices.
*   I manually added `AI_USAGE.md` and `video_link.md` to the root directory as project-specific documentation requirements. This was a good reminder that while AI provides excellent templates, the developer must tailor them to specific project needs.

---

## Phase 2: Core Logic - Data Fetching

**Goal:** Write robust functions to fetch data from the NOAA and EIA APIs, complete with error handling and automatic retries.

**My Prompt to AI (Example):**
> "Write a Python function using the `requests` library to fetch data from the NOAA CDO v2 API. The function should accept an API token, station ID, and start/end dates. It must include error handling for HTTP errors and use the `tenacity` library for automatic retries with exponential backoff if the request fails. The token should be in the header."

**AI's Contribution:**
*   The AI generated a complete Python function for the NOAA API, including the `@retry` decorator from `tenacity` with `wait_exponential` and `stop_after_attempt`.
*   It correctly placed the NOAA token in the request `headers`.
*   It provided a `try...except` block to catch `requests.exceptions.HTTPError` and log failures.

**AI Mistake & My Fix:**
*   **The Mistake:** The AI-generated code for processing the NOAA response was too generic. It didn't know that the temperature values were returned in "tenths of degrees Celsius" or that the actual data was nested inside a `['results']` key in the JSON response. Running the code as-is would have resulted in incorrect temperature values (e.g., 250°C instead of 25.0°C) and a `KeyError`.
*   **How I Discovered It:** I first noticed the `KeyError` when running the script. After fixing that by adding `['results']`, I printed the DataFrame and saw nonsensical temperature values.
*   **The Fix:** I consulted the NOAA API documentation, which confirmed the unit format. I then modified the data processing logic to divide the raw temperature values by 10 before any conversion to Fahrenheit.

**What I Learned:**
AI is excellent at generating syntactically correct code for standard tasks like API calls. However, it lacks the domain-specific knowledge of a particular API's response schema or data conventions. The developer's role is to bridge this gap by reading documentation and providing the final, context-aware logic.

---

## Phase 3: Data Processing and Quality Checks

**Goal:** Clean the raw data, merge the two sources, perform unit conversions, and implement data quality checks.

**My Prompt to AI:**
> "I have two pandas DataFrames: `weather_df` and `energy_df`, both with a 'date' column. Write a Python function that merges them on 'date'. Then, add a data quality check to flag any rows where 'energy_mwh' is negative or 'TMAX_F' is greater than 130."

**AI's Contribution:**
*   It correctly generated the `pd.merge(weather_df, energy_df, on='date', how='outer')` call. I later changed `outer` to `inner` based on project needs, but the initial structure was correct.
*   It generated boolean masks to identify outlier data points (e.g., `df['temp_f'] < -50`).

**AI Mistake & My Fix:**
*   **The Mistake:** The AI's code assumed the `date` columns in both DataFrames were already in a compatible `datetime` format. In reality, they were strings after being loaded from JSON. Attempting to merge on string dates can fail silently or produce incorrect results if the formats differ.
*   **How I Discovered It:** During testing, I noticed that some days were not merging correctly. I inspected the `dtypes` of my DataFrames and confirmed the `date` columns were `object` (strings), not `datetime64[ns]`.
*   **The Fix:** I added `pd.to_datetime(df['date'])` to my processing logic for both the weather and energy data *before* the merge step to standardize the key.

**What I Learned:**
Data type consistency is paramount. This was a classic data processing bug that the AI's high-level logic missed. It reinforced the importance of always validating data types at each step of a pipeline, a crucial habit for any data engineer.

---

## Phase 4: Pipeline Orchestration

**Goal:** Create a master script (`pipeline.py`) to run the entire process, controlled by command-line arguments for different run modes (historical vs. daily).

**My Prompt to AI:**
> "Create a main Python script using the `argparse` library. It needs two mutually exclusive arguments: `--fetch-historical` which takes an integer for the number of days, and `--fetch-daily` which is a flag. Based on the argument, it should calculate the correct start and end dates. Also, set up basic file logging."

**AI's Contribution:**
*   The AI generated the complete `argparse` setup, including creating a mutually exclusive group, which is a non-trivial part of the library.
*   It correctly used `datetime` and `timedelta` to calculate the date ranges based on the user's input.
*   It provided the standard `logging.basicConfig` configuration to set up logging to `logs/pipeline.log`.

**What I Learned:**
For well-defined problems with standard libraries like `argparse` and `logging`, the AI is incredibly efficient and produces code that is often production-ready. My role shifted from "writer" to "integrator," connecting the AI-generated modules into a cohesive whole.

---

## Phase 5: Dashboard Development with Streamlit

**Goal:** Build the interactive visualizations for the dashboard. This was done one chart at a time.

**My Prompt to AI (Example for the Scatter Plot):**
> "Using Streamlit and Plotly Express, create a scatter plot from a pandas DataFrame. The x-axis should be 'TMAX_F', and the y-axis 'energy_mwh'. Color the points by 'city'. Add an OLS trendline. Also, show me how to calculate the R-squared value and display it using `st.metric`."

**AI's Contribution:**
*   Provided the correct Plotly Express call: `px.scatter(df, x='TMAX_F', y='energy_mwh', color='city', trendline='ols')`.
*   Showed how to calculate correlation with `df['col1'].corr(df['col2'])`.
*   For R-squared, it correctly suggested using the `statsmodels.api` library, which was necessary because Plotly's built-in trendline does not expose the R-squared value directly.
*   It demonstrated using `st.plotly_chart` to render the plot and `st.metric` or `st.write` to display the calculated stats.

**AI Mistake & My Fix:**
*   **The Mistake:** For the dual-axis time series chart, the AI's first attempt was overly complex and didn't use the recommended `make_subplots` function from Plotly, leading to code that was hard to read and modify.
*   **How I Discovered It:** The code was difficult to understand, and I knew from prior experience that there was a more elegant way to create dual-axis charts.
*   **The Fix:** I refined my prompt to be more specific: "Show me how to create a dual-axis time series chart in Plotly using `make_subplots`". The AI then returned a much cleaner, more idiomatic solution which I adopted.

**What I Learned:**
Prompt engineering is a skill. Being more specific in my requests and including key library functions (`make_subplots`) led to significantly better and more maintainable code from the AI. My main role in this phase was that of an architect, wiring together the individual components (widgets and charts) into a cohesive and interactive user interface.

---

## Phase 6: Documentation and Finalization

**Goal:** Generate a high-quality, comprehensive `README.md` file to explain the project to other developers and stakeholders.

**My Prompt to AI:**
> "Generate a professional `README.md` for my 'US Weather + Energy Analysis' Python project. Include these sections: Project Overview, Business Value, Repository Structure, Setup Instructions, How to Run, a description of the Dashboard Visualizations, and a Troubleshooting section."

**AI's Contribution:**
*   The AI generated a nearly complete `README.md` file with well-written prose for each section.
*   It created a markdown code block for the directory tree.
*   It provided clear, numbered steps for the setup and execution processes.

**What I Learned:**
For documentation, the AI is an incredible time-saver. It produces an excellent, well-structured first draft. My role was to act as an editor: fact-checking all commands, personalizing the content, and ensuring the tone matched the project's professional standard.

---

## Overall Learnings and Conclusion

Collaborating with an AI assistant was like having a very fast junior developer and a powerful search engine rolled into one.

*   **Strengths:** The AI excelled at generating boilerplate code (API functions, `argparse` setup, file I/O), writing documentation drafts, and providing examples for new libraries (`tenacity`, `plotly`). This dramatically reduced development time.
*   **Weaknesses:** The AI lacked project-specific context. It didn't know the exact format of an API response or the specific business logic I wanted to implement. It sometimes hallucinated library functions or parameters that didn't exist, requiring verification.
*   **Synergy:** The most effective workflow was a tight loop of **Prompt -> Generate -> Verify -> Refine**. The AI provided the initial code, and I used my expertise to debug, integrate, and add the nuanced logic required to make it work perfectly for this specific project.

In conclusion, AI did not "write the project for me." Rather, it acted as a powerful force multiplier, handling the repetitive and standard tasks, which freed me up to focus on the more creative and challenging aspects of data engineering: ensuring data quality, designing meaningful analysis, and building a polished, user-friendly end product.