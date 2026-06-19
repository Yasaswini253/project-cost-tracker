# PROJECT REPORT

## AI-Powered Predictive Project Cost Intelligence System

---

| **Project Title** | AI-Powered Predictive Project Cost Intelligence System |
|-------------------|--------------------------------------------------------|
| **Project Type** | Web-Based Cost Performance & Predictive Analytics Dashboard |
| **Technology** | Python, Streamlit, Pandas, Scikit-learn, Statsmodels, Plotly |
| **GitHub Repository** | https://github.com/Yasaswini253/project-cost-tracker |
| **Deployment** | Localhost (`http://localhost:8501`) / Streamlit Cloud (optional) |

---

## 1. Introduction

Project cost performance tracking in engineering and manufacturing organizations is traditionally performed manually. Engineers combine data from multiple sources such as **ETC (Estimate to Complete)** and **ACWP (Actual Cost of Work Performed)** using spreadsheets. This process is:

- Time-consuming  
- Error-prone  
- Difficult to scale  
- Dependent on individual judgment instead of consistent, data-driven logic  

As a result, Project Engineers spend significant time on weekly cost reconciliation instead of proactive decision-making.

This project delivers an **AI-Powered Predictive Project Cost Intelligence System** — a web application that automatically reads cost files, consolidates data, calculates performance metrics, detects anomalies, predicts budget overruns, and presents insights through an interactive executive dashboard.

---

## 2. Problem Statement

Organizations struggle with:

1. Manual consolidation of ETC and actual cost files from different departments  
2. Delayed identification of budget overruns (discovered only after money is lost)  
3. Lack of predictive analytics for future cost performance  
4. No centralized view of project health, vendor performance, or fraud risks  
5. Repetitive weekly report preparation by project engineers  

---

## 3. Objectives

| # | Objective | Status |
|---|-----------|--------|
| 1 | Automatically read and consolidate ETC + Actual cost files | ✅ Achieved |
| 2 | Calculate Cost Variance and CPI | ✅ Achieved |
| 3 | Detect unusual patterns using AI (Isolation Forest) | ✅ Achieved |
| 4 | Predict cost overruns before they occur | ✅ Achieved |
| 5 | Provide Project Health Score and executive summary | ✅ Achieved |
| 6 | Generate smart recommendations and root cause analysis | ✅ Achieved |
| 7 | Display insights through interactive dashboard and charts | ✅ Achieved |
| 8 | Support multiple file uploads and flexible column names | ✅ Achieved |
| 9 | Enable AI chat assistant for project cost queries | ✅ Achieved |
| 10 | Export consolidated reports as CSV | ✅ Achieved |

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER (Web Browser)                          │
│              Upload ETC Files + Actual Cost Files               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STREAMLIT DASHBOARD (app.py)                  │
│  Executive Summary │ KPIs │ Charts │ AI Intelligence │ Chat    │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐  ┌─────────────────┐  ┌──────────────────┐
│  Data Layer   │  │  Analytics Layer │  │   AI/ML Layer    │
│ data_loader   │  │ metrics, risk    │  │ anomaly_detector │
│ column_mapper │  │ timeline         │  │ intelligence     │
│               │  │ fraud_analysis   │  │ forecasting      │
└───────────────┘  └─────────────────┘  └──────────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                   Consolidated CSV Report Export
```

---

## 5. Technology Stack

| Module | Technology | Purpose |
|--------|------------|---------|
| Frontend / Dashboard | **Streamlit** | Interactive web UI |
| Data Processing | **Pandas, NumPy** | Read, clean, merge cost data |
| Charts | **Plotly** | Bar, line, pie, gauge, Gantt charts |
| Anomaly Detection | **Isolation Forest (Scikit-learn)** | Multivariate outlier detection |
| Overrun Prediction | **Random Forest Classifier** | Budget overrun probability |
| Health Score | **Random Forest Regressor** | Project health scoring |
| Cost Forecasting | **ARIMA / Exponential Smoothing (Statsmodels)** | Weekly cost trend prediction |
| File Support | **openpyxl** | Excel (.xlsx, .xls) file reading |
| Version Control | **Git / GitHub** | Source code hosting |

---

## 6. Project Structure

```
project-cost-tracker/
├── app.py                    # Main Streamlit application entry point
├── run.bat                   # One-click Windows launcher
├── requirements.txt          # Python dependencies
├── README.md                 # Quick start guide
├── PROJECT_REPORT.md         # This report
├── sample_data/
│   ├── etc_tasks.csv         # Sample ETC (Task_ID format)
│   ├── actual_tasks.csv      # Sample Actual cost file
│   ├── etc_sample.csv        # Sample project-level ETC
│   └── actuals_sample.csv      # Sample project-level actuals
└── src/
    ├── data_loader.py        # File reading, merging, multi-file support
    ├── column_mapper.py      # Manual column mapping for custom headers
    ├── metrics.py            # CPI, variance, budget status
    ├── anomaly_detector.py   # Isolation Forest anomaly detection
    ├── intelligence.py       # ML predictions, health score, recommendations
    ├── forecasting.py        # ARIMA weekly cost forecast charts
    ├── fraud_analysis.py     # Duplicate invoices, vendor analysis
    ├── risk.py               # Risk badges, ranking, savings analysis
    ├── timeline.py           # Gantt timeline and task status
    ├── notifications.py      # Real-time dynamic alerts
    ├── chat_assistant.py     # AI Q&A assistant
    └── dashboard.py          # All UI rendering components
```

---

## 7. Complete Feature List

### 7.1 Data Ingestion Features

| Feature | Description |
|---------|-------------|
| Multi-file upload | Upload multiple ETC and multiple Actual files at once |
| Supported formats | CSV, TSV, Excel (.xlsx, .xls) |
| Auto column detection | Reads Task_ID, Task_Nam, ETC_Cost, Actual_Cost, etc. automatically |
| Manual column mapping | Map custom column names when auto-detection fails |
| Flexible headers | Spaces, underscores, and case do not matter |
| Period merging | Handles files with/without Week/Period columns |

### 7.2 Cost Performance Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Cost Variance** | Earned Value − Actual Cost | Positive = under budget |
| **CPI** | Earned Value / Actual Cost | > 1.0 = good, < 1.0 = over budget |
| **Budget Status** | Based on CPI | Under Budget / On Budget / Over Budget |
| **Expected Loss** | Predicted Final Cost − Budget | Financial impact if trend continues |
| **Burn Rate** | Week-over-week spend change | Detects accelerating spend |

### 7.3 Risk Classification

| CPI Value | Risk Badge | Meaning |
|-----------|------------|---------|
| > 1.0 | 🟢 Low | Under budget |
| 0.9 – 1.0 | 🟡 Medium | Slight overspend risk |
| < 0.9 | 🔴 High | Over budget – action needed |

### 7.4 Health Score Classification

| Health Score | Status |
|--------------|--------|
| > 80 | 🟢 Healthy |
| 60 – 80 | 🟡 Needs Attention |
| 40 – 60 | 🟠 At Risk |
| < 40 | 🔴 Critical |

### 7.5 AI & Machine Learning Features

| # | Feature | ML Method | Output |
|---|---------|-----------|--------|
| 1 | **Anomaly Detection** | Isolation Forest (scaled features) | Flags unusual cost patterns with explanations |
| 2 | **Cost Overrun Prediction** | Random Forest Classifier | Overrun probability % + model confidence % |
| 3 | **Root Cause Analysis** | Random Forest feature importance | Data-driven causes per project |
| 4 | **Health Score** | Random Forest Regressor | 0–100 score with risk breakdown |
| 5 | **Cost Forecast** | ARIMA / Exponential Smoothing | Weekly cost trend (not cumulative) |
| 6 | **Recommendations** | Feature-weighted action engine | Unique actions per project |
| 7 | **Fraud Detection** | Statistical threshold (2σ) | Suspicious spending flags |
| 8 | **Duplicate Invoice Detection** | Duplicate row / invoice ID matching | Potential financial loss amount |

### 7.6 Dashboard & Visualization Features

| Section | Charts / Components |
|---------|---------------------|
| Executive Summary | Projects analysed, budget utilization, overspend, critical count |
| KPI Cards | Total ETC, Actual, Variance, CPI, Project count |
| Health Gauge | Portfolio health 0–100% |
| Potential Savings | Overtime, supplier, duplicate invoice savings |
| Real-Time Alerts | 🔴🟠🟡🟢 dynamic alerts from uploaded data |
| Project Risk Cards | Risk badge, CPI, budget health, expected loss |
| Project Ranking | Best to worst projects by CPI |
| Project Timeline | Gantt view with Completed/Running/Delayed/Pending |
| Trend Analysis | Weekly actual vs budget (numeric week ordering) |
| Cost Forecast | Weekly ARIMA prediction line |
| Cost Distribution | Pie chart by department/phase |
| Department Costs | Budget vs Actual vs Variance bar chart |
| CPI & Risk | Bar chart with budget status colors |
| Burn Rate | Week-over-week spend acceleration |
| AI Intelligence Tabs | Overrun, Health, Root Cause, Recommendations, Fraud, Vendor, Weekly Report |
| AI Chat Assistant | Natural language project cost queries |
| Export | Download full CSV report |

### 7.7 Vendor Performance Dashboard

| Column | Description |
|--------|-------------|
| Vendor | Supplier name |
| Delivery % | On-time delivery performance |
| Cost Increase | Extra cost vs median vendor |
| Star Rating | ⭐⭐⭐⭐⭐ to ⭐☆☆☆☆ |
| Assessment | Good performance / delays / high impact |
| Worst Vendor | Automatically identified with consistent reasons |

---

## 8. System Workflow (Technical Steps)

```
Step 1:  User uploads ETC file(s) and Actual cost file(s)
           ↓
Step 2:  data_loader.py reads CSV/Excel and normalizes columns
           ↓
Step 3:  column_mapper.py (optional) maps custom column names
           ↓
Step 4:  consolidate_cost_data() merges ETC + Actual by Project/Task/Period
           ↓
Step 5:  metrics.py calculates Variance, CPI, Budget Status
           ↓
Step 6:  anomaly_detector.py runs Isolation Forest on cost features
           ↓
Step 7:  intelligence.py runs Random Forest for overrun prediction,
         health score, root cause, and recommendations
           ↓
Step 8:  forecasting.py generates ARIMA weekly cost forecast
           ↓
Step 9:  fraud_analysis.py checks duplicates, vendors, suspicious spend
           ↓
Step 10: risk.py adds risk badges, ranking, expected loss, savings
           ↓
Step 11: timeline.py builds Gantt chart and task status
           ↓
Step 12: notifications.py generates dynamic alerts
           ↓
Step 13: dashboard.py renders all UI sections
           ↓
Step 14: User downloads consolidated CSV report
```

---

## 9. User Interface Guide (Step-by-Step)

### Step 1: Launch the Application

**Option A – One click (Windows):**
```
Double-click run.bat
```

**Option B – Manual:**
```powershell
cd project-cost-tracker
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

**Browser opens at:** `http://localhost:8501`

---

### Step 2: Sidebar – Upload Data

| UI Element | Action |
|------------|--------|
| **ETC Files** | Click "Browse files" → select one or more ETC files |
| **Actual Cost Files** | Click "Browse files" → select one or more Actual files |
| **Use sample Task_ID data** | Check this to demo without uploading files |
| **Manual Column Mapping** | Enable if your column names are non-standard |
| **Sample Templates** | Download etc_tasks.csv / actual_tasks.csv as reference |

**Supported file formats:** `.csv`, `.tsv`, `.xlsx`, `.xls`

**Example ETC file columns:**
```
Task_ID, Task_Nam, ETC_Cost
T001, Task_1, 164918
T002, Task_2, 89234
```

**Example Actual file columns:**
```
Task_ID, Task_Nam, Actual_Cost, Vendor, Week
T001, Task_1, 172000, ABC Supplies, Week-1
```

---

### Step 3: Main Dashboard – Review Executive Summary

After upload, the dashboard automatically displays:

1. **Executive Summary table** – total projects, budget utilization, overspend, critical projects  
2. **KPI Cards** – Total ETC, Actual, Variance, CPI  
3. **Budget Status badges** – Under Budget / On Budget / Over Budget counts  
4. **Health Gauge** – portfolio health score  
5. **Potential Savings** – estimated recoverable savings  

---

### Step 4: Review Alerts and Risk

| Section | What to look for |
|---------|-----------------|
| **Real-Time Alerts** | 🔴 Critical, 🟠 Warning, 🟡 CPI drop, 🟢 duplicate detected |
| **Project Risk Overview** | Each task shows Risk badge, CPI, Budget Health %, Expected Loss |
| **Project Ranking** | Projects sorted best → worst by CPI |

---

### Step 5: Explore Charts (Tab Navigation)

| Tab | Purpose |
|-----|---------|
| **Trend Analysis** | Weekly spending trend – is cost accelerating? |
| **Planned vs Actual** | Bar chart comparing planned, actual, ETC |
| **Cost Distribution** | Pie chart – where money is spent |
| **Department Costs** | Budget vs Actual vs Variance by department |
| **CPI & Risk** | CPI bar chart with color-coded budget status |
| **Forecast** | ARIMA weekly cost prediction line |
| **Anomalies** | AI-flagged unusual cost rows |
| **Burn Rate** | Week-over-week spend change |

---

### Step 6: Project Timeline

- **Table view:** Task, Phase, Status (Completed/Running/Delayed/Pending)  
- **Gantt chart:** Tasks spanning ordered weeks with color-coded status  

---

### Step 7: AI Intelligence Section

| Tab | Content |
|-----|---------|
| **Overrun Prediction** | Probability %, Model Confidence %, AI explanation |
| **Health Score** | Per-project health with budget/schedule/resource risk |
| **Root Cause** | Feature-importance based root causes |
| **Recommendations** | ✔ Prioritized action checklist per project |
| **Fraud & Duplicates** | Duplicate invoices and suspicious spending |
| **Vendor Dashboard** | Vendor ratings, worst vendor callout |
| **Weekly Report** | Auto-generated management summary |
| **Completion Forecast** | Expected final cost with variable confidence % |

---

### Step 8: AI Chat Assistant

Type questions such as:

- *Which project has the highest risk?*  
- *Why is Task_11 over budget?*  
- *Which vendor causes maximum loss?*  
- *Show all anomalies*  
- *Which project should management review first?*  

---

### Step 9: Export Report

Click **"Download Full Report (CSV)"** at the bottom to save all consolidated analysis data.

---

## 10. Advantages of This Project

### 10.1 Over Manual Spreadsheet Process

| Manual Process | This System |
|----------------|-------------|
| Hours of copy-paste weekly | Upload files → instant analysis |
| Human calculation errors | Automated CPI, variance, forecast |
| Reactive (after overrun) | Predictive (before overrun) |
| No anomaly detection | AI Isolation Forest detection |
| Static reports | Interactive live dashboard |
| Single file limitation | Multiple file upload supported |
| Fixed column names required | Auto-read + manual mapping |

### 10.2 Business Advantages

1. **Faster decision-making** – Executive summary in seconds  
2. **Early warning system** – Overrun prediction before budget is exceeded  
3. **Reduced financial loss** – Duplicate invoice and fraud detection  
4. **Better vendor management** – Vendor rating and worst vendor identification  
5. **Improved accountability** – Project ranking and health score  
6. **Automated reporting** – Weekly management report generated automatically  
7. **Scalable** – Handles multiple projects and multiple files  
8. **Accessible** – Web UI, no special software needed beyond a browser  

### 10.3 Technical Advantages

1. **Modular architecture** – 13 separate Python modules, easy to maintain  
2. **ML-powered** – Not just formulas; uses Random Forest and Isolation Forest  
3. **Flexible data input** – Supports Task_ID, Project_ID, and custom column names  
4. **Open source stack** – Python, free libraries, deployable on Streamlit Cloud  
5. **Exportable** – CSV download for audit and record keeping  
6. **Version controlled** – Full source on GitHub for collaboration  

---

## 11. Sample Input File Formats

### Format A – Task Level (Primary)

**ETC File:**
| Task_ID | Task_Nam | ETC_Cost |
|---------|----------|----------|
| T001 | Task_1 | 164918 |
| T011 | Task_11 | 193910 |

**Actual File:**
| Task_ID | Task_Nam | Actual_Cost | Vendor | Week |
|---------|----------|-------------|--------|------|
| T001 | Task_1 | 172000 | ABC Supplies | Week-1 |
| T011 | Task_11 | 950000 | XYZ Corp | Week-3 |

### Format B – Project Level

**ETC File:**
| Project_ID | Project_Name | Cost_Element | Period | ETC |
|------------|--------------|--------------|--------|-----|
| P001 | Alpha Plant | Engineering | Week-01 | 45000 |

**Actual File:**
| Project_ID | Project_Name | Cost_Element | Period | ACWP |
|------------|--------------|--------------|--------|------|
| P001 | Alpha Plant | Engineering | Week-01 | 98000 |

---

## 12. Installation & Execution Steps

| Step | Command / Action |
|------|-----------------|
| 1 | Install Python 3.10 or higher |
| 2 | Clone repo: `git clone https://github.com/Yasaswini253/project-cost-tracker.git` |
| 3 | Open folder: `cd project-cost-tracker` |
| 4 | Run: `.\run.bat` (Windows) |
| 5 | Open browser: `http://localhost:8501` |
| 6 | Upload files or use sample data |
| 7 | Review dashboard and export CSV |

---

## 13. Deployment as Public Website

The application can be deployed online using **Streamlit Community Cloud**:

1. Go to [https://share.streamlit.io](https://share.streamlit.io)  
2. Connect GitHub account  
3. Select repository: `Yasaswini253/project-cost-tracker`  
4. Main file: `app.py`  
5. Deploy → receive public URL like `https://project-cost-tracker.streamlit.app`  

---

## 14. Future Enhancements

| Enhancement | Description |
|-------------|-------------|
| Database integration | Store historical cost data in SQLite/PostgreSQL |
| Email/SMS alerts | Send real notifications on budget threshold breach |
| User authentication | Login system for multi-user access |
| Custom domain | Deploy with company domain name |
| SPI (Schedule Performance Index) | Add schedule performance alongside CPI |
| PDF report export | Generate formatted PDF management reports |
| Mobile responsive UI | Optimize layout for tablet/mobile |

---

## 15. Conclusion

The **AI-Powered Predictive Project Cost Intelligence System** successfully transforms manual, error-prone project cost reconciliation into an automated, intelligent, and visual decision-support platform.

The system:

- Consolidates ETC and actual cost data from multiple files automatically  
- Calculates industry-standard metrics (CPI, Cost Variance, Burn Rate)  
- Applies machine learning for anomaly detection, overrun prediction, and health scoring  
- Presents actionable insights through a professional executive dashboard  
- Reduces engineer time spent on weekly cost reconciliation  
- Enables management to act **before** budget overruns become severe  

This project demonstrates practical application of **Data Science, Machine Learning, and Web Development** to solve a real-world engineering project management problem.

---

## 16. References

| Resource | Link |
|----------|------|
| GitHub Repository | https://github.com/Yasaswini253/project-cost-tracker |
| Streamlit Documentation | https://docs.streamlit.io |
| Scikit-learn Documentation | https://scikit-learn.org |
| Statsmodels (ARIMA) | https://www.statsmodels.org |
| Earned Value Management (CPI) | PMI / ANSI EIA-748 Standard |

---

*Report generated for: AI-Powered Predictive Project Cost Intelligence System*  
*Author: Yasaswini253*  
*Repository: https://github.com/Yasaswini253/project-cost-tracker*
