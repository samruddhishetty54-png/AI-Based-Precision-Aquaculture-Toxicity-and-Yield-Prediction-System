# FINAL UI CORRECTION — PRECISION AquaDSS

I have inspected the current Precision AquaDSS application. The functionality and existing pages should be preserved, but the current user interface does not look polished enough for our final mini-project presentation.

Your task is to perform a complete UI/UX improvement across the existing application.

## 1. Preserve the existing application

- Do not create a new project.
- Do not replace the existing application with a static dashboard.
- Preserve all 9 existing pages and their functionality.
- Preserve trained AI models, preprocessing pipelines, datasets and prediction logic.
- Do not modify scientific calculations or model results.
- Do not remove existing working features.

## 2. Fix the sidebar

The current sidebar has clipped navigation labels and branding.

Fix:
- Sidebar width and alignment.
- Left and right padding.
- Navigation label visibility.
- Icon alignment.
- Consistent spacing between navigation groups.
- Project branding at the bottom.
- Sidebar collapse and expand behaviour.

Every navigation label must be completely visible.

## 3. Redesign the organization overview

The current overview contains too much explanatory text.

Create a professional organization dashboard with:

- A clean page heading: Organization Overview.
- A short subtitle.
- Compact organization summary.
- Four or five attractive KPI cards.
- Water-quality trend charts.
- Toxicity risk overview.
- Pond comparison.
- Fish growth trends.
- Recent observations table.
- Recent prediction activity.

Convert Quick Actions into attractive clickable cards with icons.

The most important information must be visible without excessive scrolling.

Move lengthy scientific explanations and technical disclaimers into expandable sections.

## 4. Improve all six main modules

Apply a consistent professional design to:

1. Organization Overview
2. Dataset Upload
3. AI Predictions and Toxicity Risk
4. Feeding Advisor
5. Growth Analytics
6. Simulation Mode

Also improve Pond Monitoring, Prediction History and Reports, DO and Hypoxia Screening, and Model Information.

Each page should have:
- Clear page title.
- Short description.
- Consistent card design.
- Properly aligned inputs.
- Readable graphs.
- Clear result indicators.
- Proper spacing.
- Consistent navigation.

## 5. Dataset Upload page

Make the upload workflow visually attractive and easy to understand.

Display:
- CSV upload area.
- Uploaded filename.
- Dataset preview.
- Column mapping.
- Missing-value validation.
- Model compatibility.
- Analysis selection.
- Run Analysis button.
- Prediction results.
- CSV download.

Keep all existing validation and model compatibility logic.

## 6. AI Prediction page

Present prediction results using professional result cards.

Show actual available:
- Ammonia predictions.
- Toxicity screening.
- Mortality diagnostic.
- Dissolved oxygen screening.
- Pond-wise comparisons.

Use readable charts and risk indicators.

Never invent prediction values, accuracy scores or risk percentages.

## 7. Feeding and Growth pages

Create visually clear feeding recommendation cards and fish-weight analytics.

Separate actual model outputs from rule-based recommendations.

Clearly label provisional recommendations.

Do not claim unsupported harvest-yield predictions or automatic feeding control.

## 8. Design system

Use this visual theme throughout the application:

- Navy blue: primary navigation and headings.
- Aquatic blue: primary actions.
- Teal: secondary highlights.
- White: cards and content areas.
- Very light blue-grey: page background.
- Green, amber and red: meaningful status indicators only.

Use:
- Modern professional typography.
- Consistent card heights.
- Rounded corners.
- Subtle shadows.
- Clean icons.
- Proper chart sizing.
- Consistent margins and padding.

Avoid:
- Excessive paragraphs.
- Huge empty spaces.
- Tiny text.
- Clipped labels.
- Unnecessary borders.
- Inconsistent colours.
- Unstyled buttons.
- Horizontal scrolling.

## 9. Responsive layout

Test the interface at 1366px, 1440px and 1920px desktop widths.

Ensure:
- Sidebar is not clipped.
- Main content uses available screen space.
- Cards align properly.
- Graphs resize correctly.
- Navigation works.
- No horizontal overflow.
- All page content is readable.

## 10. Final testing

After completing the redesign:

- Inspect all 9 pages.
- Test sidebar navigation.
- Test CSV upload.
- Test model execution.
- Test prediction displays.
- Test graphs and filters.
- Test CSV downloads.
- Test simulation isolation.
- Verify that existing functionality remains intact.
- Run the existing test suite.

Do not stop after redesigning only the home page.

IMPORTANT: First inspect the existing CSS, Streamlit configuration, dashboard.py, styles.py and all page files. Identify the reason for the sidebar clipping before changing styles.

Implement the improvements directly in the existing codebase.

Do not change the project name: Precision AquaDSS.

The final result should look like a professional commercial aquaculture AI analytics SaaS platform, suitable for a college mini-project demonstration.# Precision AquaDSS

**AI-Based Precision Aquaculture Toxicity and Yield Prediction System**

An AI-driven aquaculture prediction and decision-support platform that analyses pond water-quality observations, identifies potential toxicity risks, provides adaptive feeding recommendations and supports sustainable fish-farm management.

---

## Quick Start

```powershell
# 1. Clone and enter the repository
git clone <repository-url>
cd AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System

# 2. Create virtual environment and install dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Launch the application
streamlit run dashboard.py --server.headless=true

# 4. Open in browser
# http://localhost:8501
```

### Run Tests
```powershell
.\.venv\Scripts\python.exe -m pytest app/tests/ -q
# Result: 150 passed, 4 subtests passed
```

---

## Application Modules

Precision AquaDSS provides **9 pages** organized into 5 navigation groups:

### Farm & Monitoring
| Page | Purpose |
|---|---|
| **Organization Overview** | Executive farm-level KPIs, region/pond summaries, DO trends, temperature/pH charts, ammonia trends, pond-to-pond comparisons, fish weight observations |
| **Pond Monitoring** | Per-pond inspection priority queue, model registry health status, operational boundary cards |

### Data Management
| Page | Purpose |
|---|---|
| **Upload New Dataset** | 6-step CSV import workflow: upload → column mapping → validation → compatibility check → analysis selection → batch execution with per-row results and CSV export |

### Water Quality & Risk
| Page | Purpose |
|---|---|
| **Water Quality & Toxicity Risk** | Emerson ammonia chemistry calculator, ammonia soft-sensor estimate, mortality diagnostic, next-visit ammonia risk screening, risk visualization charts |
| **DO & Hypoxia Screening** | Morning DO benchmark (3.50 mg/L historical mean), GBDT moderate hypoxia screening, historical DO trend chart |

### Growth & Feeding
| Page | Purpose |
|---|---|
| **Fish Growth & Feeding Advisor** | Next-visit fish weight persistence benchmark, provisional rule-based feeding advisory with biochemical throttling factors |

### Analytics
| Page | Purpose |
|---|---|
| **Prediction History & Reports** | Interactive historical data explorer with trajectory charts, session prediction history, CSV download |
| **Simulation Mode** | Non-operational What-If sandbox using synthetic time-series data, parameter stress testing |

### System
| Page | Purpose |
|---|---|
| **Model Information** | Model availability status, analysis module inventory, dataset status, operational limitations, technical reference documentation |

---

## Key Features

- **CSV Upload → Model Execution → Results**: Upload new pond observations, validate columns, select compatible analyses, run models, view and export results
- **Ammonia Risk Assessment**: Emerson NH₃ chemistry + ML-based ammonia soft-sensor + mortality diagnostic + next-visit risk screening
- **DO & Hypoxia Screening**: Historical mean DO benchmark + GBDT moderate hypoxia classifier
- **Feeding Advisory**: Rule-based provisional feeding recommendations with biochemical throttling factors
- **Water Quality Visualization**: DO trends, pH/temperature trends, ammonia concentration trends, pond-to-pond comparisons
- **Simulation Sandbox**: Quarantined What-If parameter exploration using synthetic data

---

## Project Structure

```
AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/
├── README.md                           # This file
├── dashboard.py                        # Streamlit main application launcher
├── requirements.txt                    # Python dependency specifications
├── clean_datasets_v2.py                # Dataset cleaning and standardization script
│
├── app/                                # Application source code
│   ├── core/                           # Chemical calculators and data manager
│   │   ├── chemistry.py                # Emerson dissociation equations
│   │   └── data_manager.py             # Cached dataset loader
│   ├── models/                         # Pre-trained model wrappers & registry
│   │   ├── registry.py                 # Central ModelRegistry coordinator
│   │   ├── exp1_soft_sensor.py         # RF ammonia soft-sensor
│   │   ├── exp2_mortality.py           # Balanced logistic regression mortality diagnostic
│   │   ├── exp3_ammonia_risk.py        # RF next-visit ammonia risk classifier
│   │   ├── do_hypoxia.py              # Historical mean DO + GBDT hypoxia screener
│   │   ├── fish_growth.py             # Persistence cohort weight baseline
│   │   └── feeding_advisor.py         # Rule-based feeding advisory engine
│   ├── dashboard/                      # UI presentation layer
│   │   ├── components/                 # Reusable UI components
│   │   │   ├── header.py              # Page header with category badges
│   │   │   ├── metric_card.py         # KPI card containers
│   │   │   ├── banners.py            # Alert and governance banners
│   │   │   └── registry_status.py    # Model registry health display
│   │   ├── pages/                      # 9 Streamlit pages (01-09)
│   │   └── utils/                      # Styles and upload processor
│   │       ├── styles.py              # Professional SaaS CSS theme
│   │       └── upload_processor.py    # CSV parsing, validation, batch analysis
│   └── tests/                          # 150 automated tests
│
├── baseline_toxicity_v1/models/        # Experiment 1 RF pipeline (.joblib)
├── experiment_2_mortality_v1/models/   # Experiment 2 LR pipeline (.joblib)
├── experiment_3_next_visit_risk_v1/    # Experiment 3 RF pipeline (.joblib)
├── processed_data_v2/                  # Cleaned datasets (read-only)
├── dataset/                            # Raw field logs (read-only)
│
└── docs/                               # Implementation documentation
    ├── FINAL_IMPLEMENTATION_REPORT.md
    ├── MODEL_LIMITATIONS.md
    ├── DEMO_GUIDE.md
    └── implementation_reports/         # Phase-by-phase development reports
```

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.14 |
| Web Framework | Streamlit 1.67 |
| Visualization | Plotly 7.1 |
| ML Models | scikit-learn 1.9 (pre-trained .joblib pipelines) |
| Scientific Computation | NumPy, SciPy, Pandas |
| Testing | pytest (150 tests, 100% pass rate) |

---

## Operational Safeguards

- **Decision-support only** — zero automated control actuation (`is_automatic_control = False`)
- **No real-time monitoring claims** — morning observations (06:00–08:30 AM), 3–45 day revisit intervals
- **Immutable read-only models** — no runtime retraining or parameter updates
- **Strict simulation quarantine** — synthetic data never mixed with field records
- **Negative harvest yield scope** — target is next-visit pond-cohort average fish weight (g/fish), NOT total harvest yield

---

## Academic Information

**Project:** BAI507P Mini Project (AIML)  
**Department:** Department of Computer Science & Engineering (AI and ML)  
**Institution:** Sahyadri College of Engineering & Management, Mangaluru  
**Academic Year:** 2026

---

## Cryptographic Artifact Integrity

All processed datasets and pre-trained model artifacts are SHA-256 hashed to guarantee reproducibility. See the Model Information page in the application for the full hash audit table.
