# Precision AquaDSS — Presentation Demo Guide

**Date:** 2026-11-26  
**Duration:** ~10–15 minutes

---

## Setup

```powershell
cd AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System
.\.venv\Scripts\Activate.ps1
streamlit run dashboard.py --server.headless=true
```

Open **http://localhost:8501** in Chrome or Edge.

---

## Demo Script

### Step 1: Organization Overview (Landing Page)

> _"This is Precision AquaDSS, our aquaculture decision-support platform."_

1. The landing page shows the **Organization Overview** with farm-level KPIs
2. Point out the 4 summary cards (ponds monitored, total observations, avg DO, avg temperature)
3. Scroll to show the **5 interactive charts**: DO trends, temperature/pH, ammonia, pond comparison, fish weights
4. Note the sidebar branding and system safeguards footer

**📸 Screenshot 1:** Organization Overview with KPI cards and charts

---

### Step 2: Upload New Dataset

> _"Let's upload new pond observations and run our models."_

1. Click **Upload New Dataset** in the sidebar
2. Click **Browse files** and select `processed_data_v2/toxicity_analysis_v2.csv`
3. The system shows a **data preview** with row/column counts
4. **Column Mapping** — the canonical fields are automatically matched to CSV columns
5. **Validation** — the system checks for missing values and data types
6. **Compatibility Assessment** — shows which models can run on this data:
   - ✅ Emerson NH₃, Ammonia Soft-Sensor, Mortality Diagnostic, Next-Visit Risk, DO/Hypoxia
   - ❌ Fish Growth (no weight data), Feeding Advisor (no feed data)
7. **Select Analyses** — check the compatible models
8. Click **Run Analysis**
9. Show the **Execution Summary** table: processed vs skipped vs rejected per model
10. Show the **Pond-Wise Summary** and **row-level results**
11. Click **Download Results CSV**

**📸 Screenshot 2:** Upload page with file loaded and column mapping  
**📸 Screenshot 3:** Compatibility assessment showing eligible/rejected models  
**📸 Screenshot 4:** Execution summary with per-model counts  
**📸 Screenshot 5:** Row-level results table

---

### Step 3: Water Quality & Toxicity Risk

> _"Now let's analyze a specific pond's water quality."_

1. Click **Water Quality & Toxicity Risk** in the sidebar
2. Select a pond from the dropdown (e.g., `ara2_000384fb`)
3. Select an observation date
4. The page shows:
   - **Emerson NH₃ result** — calculated un-ionized ammonia
   - **Ammonia soft-sensor estimate** — ML-based proxy
   - **Mortality diagnostic** — risk probability
   - **Next-visit ammonia risk** — screening result
5. Point out the **risk bar chart** and **historical ammonia trend**
6. Open the **Explainable Input-Factor Breakdown** expander

**📸 Screenshot 6:** Water quality page with risk cards and charts

---

### Step 4: DO & Hypoxia Screening

> _"The DO screening uses a statistical benchmark rather than a complex model."_

1. Click **DO & Hypoxia Screening**
2. Select a pond and observation
3. Show the 4 KPI cards:
   - DO benchmark (constant 3.50 mg/L historical mean)
   - Hypoxia risk score
   - Hypoxia flag
   - Severe classifier (disabled)
4. Show the **DO trend chart** over time
5. Explain: _"The constant mean outperforms ML regressors on irregular multi-week revisits."_

**📸 Screenshot 7:** DO & Hypoxia page with KPIs and trend chart

---

### Step 5: Fish Growth & Feeding Advisor

> _"The feeding advisor uses rule-based biochemical throttling."_

1. Click **Fish Growth & Feeding Advisor**
2. Select a pond with available weight data
3. Show the **weight benchmark** (persistence baseline)
4. Show the **feeding recommendation** with adjustment factors
5. Explain: _"These are provisional recommendations requiring human verification."_

**📸 Screenshot 8:** Feeding advisor with recommendation cards

---

### Step 6: Simulation Mode

> _"The simulation sandbox lets us explore what-if scenarios safely."_

1. Click **Simulation Mode**
2. Point out the **quarantine notice** — synthetic data only, never mixed with real records
3. Adjust parameters in the What-If form (temperature, pH, DO)
4. Show the simulated KPI results
5. Show the synthetic time-series chart

**📸 Screenshot 9:** Simulation sandbox with What-If form and results

---

### Step 7: Model Information

> _"The system provides full transparency about model capabilities and limitations."_

1. Click **Model Information**
2. Show the compact status display:
   - Model availability table
   - Analysis modules available
   - Dataset status
3. Point out the **operational limitations** section
4. Open a collapsed technical reference to show benchmark details

**📸 Screenshot 10:** Model information page with status and limitations

---

### Step 8: Pond Monitoring

> _"The monitoring view shows per-pond inspection priorities."_

1. Click **Pond Monitoring**
2. Show the multi-pond KPI summary
3. Point out the inspection priority queue
4. Show the model registry health bar

**📸 Screenshot 11:** Pond monitoring with priority queue

---

### Closing

> _"Precision AquaDSS provides aquaculture organizations with AI-driven decision support: ammonia risk screening, feeding recommendations, and water quality analysis — all from routine pond observations, with full scientific transparency and no real-time claims."_

---

## Key Talking Points

1. **Working prediction platform** — not just dashboards; upload data → run models → get results
2. **Scientific integrity** — every model has documented limitations, no overclaims
3. **6 analysis modules** — Emerson chemistry, ammonia soft-sensor, mortality diagnostic, next-visit risk, DO/hypoxia, feeding advisory
4. **Professional UI** — SaaS-style design suitable for organization use
5. **150 automated tests** — comprehensive test coverage, 100% pass rate
6. **Decision-support only** — no automated control, human verification required

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `PermissionError` on startup | Add `--server.headless=true` flag |
| Port already in use | Use `--server.port=8502` |
| Charts not rendering | Ensure `plotly` is installed (`pip install plotly`) |
| Upload rejects file | Ensure CSV format with standard column names (see column mapping step) |
