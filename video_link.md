# Video Presentation

This 3-minute video presentation covers:
* An introduction to the business value of energy demand forecasting.
* A live demonstration of the interactive dashboard, showcasing its self-sufficient configuration and data refresh capabilities.
* A technical overview of the automated data pipeline architecture, from data fetching to processing.
* A walkthrough of the key analytical insights and visualizations available in the dashboard after the data is updated.

[![Project Video Presentation](http://img.youtube.com/vi/S03I_Vgl9Bs/0.jpg)](https://www.youtube.com/watch?v=S03I_Vgl9Bs "Project Video Presentation")

---

## Video Script

**(Intro Music Fades)**

**Daveal:**
"Hi everyone, my name is Raphael Daveal. Today, I'm walking you through my automated Weather and Energy Analysis Pipeline, a project designed to turn complex data into clear, actionable business intelligence."

**(Visual: Screen shows the GitHub repository structure, highlighting the `README.md` and the clean folder layout.)**

**Daveal:**
"It all starts here, with a production-ready repository. But the real power is in the dashboard it produces. Let's jump right in."

**(Visual: Transition to the Streamlit dashboard. It shows data for two cities: Utah and Connecticut.)**

**Daveal:**
"This dashboard is completely self-sufficient. Instead of running scripts in an IDE, all the controls are built right in. Right now, we're analyzing two locations, but let's add more."

**(Visual: Clicks on the 'Edit Configuration' expander. Clicks 'Find City IDs'.)**

**Daveal:**
"I can find reliable weather stations directly. Let's add Arkansas... and Maryland. The tool finds active stations for us. Now, let's try Alabama."

**(Visual: Selects Alabama. A warning message appears: "No reliable stations found with sufficient data.")**

**Daveal:**
"The system automatically flags that there are no reliable stations for Alabama, so we'll skip it. This built-in data validation is key. We'll add New Jersey instead."

**(Visual: Adds the selected cities to the YAML editor in the dashboard. Clicks 'Save Configuration'. Then, goes to the sidebar, selects a date range, and clicks 'Refresh All Data'.)**

**Daveal:**
"With our new cities added, I'll trigger a full data refresh directly from the UI. While that runs, let's look at how this was built."

**(Visual: Transition to a slide or diagram showing the project lifecycle: Plan -> API Keys -> Code.)**

**Daveal:**
"The project began with careful planning and obtaining API keys from NOAA for weather and EIA for energy data. The code is organized into distinct modules."

**(Visual: Show snippets or file icons for `data_fetcher.py`, `data_processor.py`, `app.py`, and `run.py`.)**

**Daveal:**
"'Fetcher' scripts are responsible for grabbing the raw data. The 'processor' then cleans, validates, and transforms it into an analysis-ready format. The `app.py` file contains all the Streamlit code for the dashboard you see. And the magic that connects them is `run.py`—a single script that allows the dashboard's 'refresh' button to execute the entire backend pipeline, making it truly interactive and self-contained."

**(Visual: Transition back to the live Streamlit dashboard. The KPIs at the top now reflect the new number of cities and the updated date range.)**

**Daveal:**
"And we're back. The pipeline has finished, and our dashboard is updated. You can see our key metrics now include the new cities we added."

**(Visual: Quickly click through each dashboard tab.)**

**Daveal:**
"We can now explore the new data. The **Geographic Overview** maps out the energy demand hotspots. The **Time Series** chart lets us compare consumption trends across all our new locations. The **Correlation Analysis** proves the strong link between temperature and energy use with hard numbers. The **Heatmap** reveals daily and weekly usage patterns. And finally, the **Data Quality Report** verifies that all the information we just pulled is clean and reliable."

**(Visual: Return to you on camera for the conclusion.)**

**Daveal:**
"So, in just a few clicks, we expanded our analysis and gained new insights, all without ever leaving the dashboard. This is the power of a well-architected data pipeline."

**Daveal:**
"A huge thank you to the Pioneer Artificial Intelligence Academy, Elder Quass, my team lead Promise, and all my teammates for their incredible support. Thank you for watching. If you found this interesting, please like, subscribe, and leave a comment below!"

**(Outro Music Fades In)**