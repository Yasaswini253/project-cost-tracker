# Project Cost Performance Tracker

AI-assisted dashboard for consolidating ETC and actual cost (ACWP) data, calculating cost variance and CPI, detecting anomalies, and visualizing project cost performance.

## Features

- **Automatic data consolidation** from ETC and Actual cost files (CSV or Excel)
- **Cost variance** calculation: `Cost Variance = Earned Value - Actual Cost`
- **CPI** calculation: `CPI = Earned Value / Actual Cost`
- **Anomaly detection** using rule-based checks + Isolation Forest (AI)
- **Interactive dashboard** with charts and exportable reports

## Quick Start (Windows)

1. Open PowerShell in this folder:
   ```
   cd project-cost-tracker
   ```

2. Run the setup and launch script:
   ```
   .\run.bat
   ```

   Or manually:
   ```
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```

3. Your browser will open at `http://localhost:8501`

## How to Use

1. Open the app in your browser
2. In the sidebar, upload:
   - **ETC file** (Estimate to Complete – planned remaining cost)
   - **Actual cost file** (ACWP – actual cost incurred)
3. Or check **Use sample data** to see a demo immediately
4. Review KPIs, charts, anomaly alerts, and detailed tables
5. Download the consolidated CSV report if needed

## Expected File Format

### ETC File (CSV or Excel)

| Column | Required | Description |
|--------|----------|-------------|
| Project_ID | Yes* | Project identifier |
| Project_Name | Yes* | Project name (* at least one of ID or Name) |
| Cost_Element | Optional | Engineering, Procurement, Construction, etc. |
| Period | Optional | Week-01, Month-03, etc. |
| ETC | Yes | Estimate to Complete amount |
| Planned_Cost | Optional | Total planned/budget cost |
| Earned_Value | Optional | Earned value (EV); used for CPI if provided |

### Actual Cost File (CSV or Excel)

| Column | Required | Description |
|--------|----------|-------------|
| Project_ID | Yes* | Must match ETC file |
| Project_Name | Yes* | Must match ETC file |
| Cost_Element | Optional | Must match ETC for line-level comparison |
| Period | Optional | Must match ETC for period-level comparison |
| ACWP | Yes | Actual Cost of Work Performed |

Sample files are in the `sample_data/` folder.

## Metrics Explained

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Cost Variance | EV − AC | Positive = under budget |
| CPI | EV / AC | > 1.0 = good, < 1.0 = over budget |
| Performance Status | Based on CPI | Under Budget / On Track / At Risk / Over Budget |

## Project Structure

```
project-cost-tracker/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── run.bat                 # One-click run script (Windows)
├── sample_data/
│   ├── etc_sample.csv
│   └── actuals_sample.csv
└── src/
    ├── data_loader.py      # File reading & consolidation
    ├── metrics.py          # Variance & CPI calculations
    ├── anomaly_detector.py # AI anomaly detection
    └── dashboard.py        # Charts & UI components
```

## Deploy on Streamlit Cloud (Public URL)

Your app code is on GitHub. To get a **public link** anyone can open:

1. Go to **[https://share.streamlit.io](https://share.streamlit.io)**
2. Sign in with your **GitHub** account (`Yasaswini253`)
3. Click **New app**
4. Fill in:
   - **Repository:** `Yasaswini253/project-cost-tracker`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Click **Deploy**

After 2–5 minutes you will get a URL like:

`https://project-cost-tracker-yasaswini253.streamlit.app`

Anyone with that link can use your dashboard without running it on localhost.

**Live demo tip:** On first load, check **Use sample Task_ID data** in the sidebar to show the dashboard instantly.

## Requirements

- Python 3.10 or higher
- Internet connection (first run only, to install packages)
