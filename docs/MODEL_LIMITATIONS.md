# Precision AquaDSS — Model Limitations & Scientific Boundaries

**Date:** 2026-11-26

---

## 1. Ammonia Soft-Sensor (Experiment 1)

**Model:** Random Forest pipeline  
**Purpose:** Estimate un-ionized ammonia (NH₃) concentration from DO, pH, temperature  
**Label:** Experimental ammonia soft-sensor estimate  

### Limitations
- Soft-sensor proxy — does NOT replace direct chemical measurement of TAN
- Trained on historical morning observations only (06:00–08:30 AM)
- Cannot capture diurnal ammonia cycles or post-feeding spikes
- Accuracy depends on input quality; missing or out-of-range values degrade estimates
- Not validated against independent laboratory reference standards

---

## 2. Fish Mortality Diagnostic (Experiment 2)

**Model:** Balanced logistic regression pipeline (`class_weight='balanced'`)  
**Purpose:** Screening diagnostic for mortality risk based on water quality  
**Label:** Experimental mortality diagnostic  

### Limitations
- Screening tool, NOT a clinical diagnostic instrument
- Trained with `class_weight='balanced'` to address severe class imbalance → elevated false positive rate
- Cannot distinguish mortality causes (disease, water quality, handling, predation)
- Binary output (risk/no-risk) with probability score; no severity grading
- 91.00% false discovery rate on historical test data

---

## 3. Next-Visit Ammonia Risk (Experiment 3)

**Model:** Random Forest pipeline  
**Purpose:** Screen whether next scheduled visit may show elevated ammonia risk  
**Label:** Experimental next-visit ammonia-risk screening  

### Limitations
- Screening classifier, NOT a confirmed toxicity forecast
- Assumes regular revisit intervals (3–45 days); irregular schedules reduce reliability
- Cannot account for unrecorded events between visits (rain, feed changes, water exchange)
- Risk classification is binary; does not estimate ammonia concentration magnitude
- Performance degrades for revisit intervals outside the training distribution

---

## 4. DO & Hypoxia Screening (Experiment 5)

**DO Benchmark Model:** Constant historical training mean (3.4984 mg/L)  
**Hypoxia Classifier:** GBDT moderate hypoxia screener  
**Labels:** Constant historical mean DO benchmark / Moderate hypoxia screening  

### Limitations
- **DO benchmark is a constant** — returns the same value (3.50 mg/L) regardless of inputs
- This constant statistically outperforms ML regressors on irregular multi-week revisits (MAE = 0.3963 mg/L) but provides zero predictive discrimination
- Not a dynamic biological prediction; it is a statistical benchmark
- **Severe hypoxia classifier is disabled** — rejected due to insufficient positive training examples
- GBDT moderate hypoxia screener has high false alarm rate
- Cannot model overnight DO minima, diurnal cycling, or algal bloom events
- Morning-only observations systematically miss the lowest DO values (typically pre-dawn)

---

## 5. Fish Growth (Experiment 4)

**Model:** Chronological persistence baseline (W_{t+1} = W_t)  
**Purpose:** Next-visit cohort average fish weight benchmark  
**Label:** Persistence fish-weight benchmark  

### Limitations
- **Persistence baseline, NOT an AI prediction** — returns the most recent weight observation as the forecast
- MAE = 93.38 g/fish on unfiltered commercial test pairs
- Cannot predict growth trajectories, only repeats last known weight
- Outperforms ML regressors because unrecorded partial harvests and cycle terminations create discontinuities that ML cannot learn
- Target is strictly next-visit pond-cohort average fish body weight (g/fish)
- **NOT** individual fish growth, **NOT** total pond biomass, **NOT** commercial harvest yield (kg/ha)
- 0% total harvest yield labels in the dataset

---

## 6. Feeding Advisory

**Model:** Rule-based decision engine  
**Purpose:** Provisional feeding recommendations based on water quality  
**Label:** Provisional feeding heuristic  

### Limitations
- Rule-based heuristic, NOT a machine learning model
- Applies biochemical throttling factors to reduce organic waste loading and post-prandial BOD
- Rules derived from aquaculture literature, NOT empirically optimized on this dataset
- Does not account for fish species, age, stocking density, or feed composition
- All recommendations are provisional and require qualified human verification
- Zero automated control actuation — does not control feeding equipment

---

## 7. Emerson Ammonia Chemistry

**Model:** Emerson et al. (1975) thermodynamic dissociation equation  
**Purpose:** Calculate un-ionized ammonia fraction from pH and temperature  
**Label:** Emerson chemistry calculation  

### Limitations
- Pure chemistry calculation, NOT a machine learning model
- Requires Total Ammonia Nitrogen (TAN-N) input; cannot estimate TAN from other parameters
- Assumes freshwater ionic strength; not validated for brackish or marine conditions
- Does not account for dissolved organic matter or other ions that affect dissociation
- Accuracy limited by input measurement precision

---

## 8. System-Level Limitations

| Limitation | Detail |
|---|---|
| **No real-time monitoring** | Morning observations only (06:00–08:30 AM), 3–45 day revisit intervals |
| **No automated control** | Decision-support only; `is_automatic_control = False` |
| **No runtime retraining** | Models are immutable read-only .joblib artifacts |
| **No SHAP/LIME explanations** | Neither library is installed; deterministic input-factor summaries used instead |
| **No harvest yield prediction** | 0% harvest yield labels in training data |
| **No individual fish tracking** | Cohort-level pond averages only |
| **No multi-species support** | Trained on single-species freshwater aquaculture |
| **Simulation data quarantined** | Synthetic benchmark data (`iot_water_model_v2.csv`) never mixed with field records |
| **Excel upload unsupported** | `.xlsx` requires `openpyxl` (not installed); CSV only |
| **Batch row cap** | Upload page caps batch execution at 500 rows per run |

---

## 9. What Precision AquaDSS Does NOT Claim

- ❌ Real-time IoT telemetry streaming
- ❌ Autonomous control of aerators, feeding gates, or water pumps
- ❌ Validated biological safety thresholds
- ❌ Overnight minimum DO forecasting
- ❌ Diurnal water quality cycle modeling
- ❌ Disease diagnosis or pathology classification
- ❌ Commercial harvest yield prediction (kg/ha)
- ❌ Multi-pond optimization or farm-wide scheduling
- ❌ Financial return-on-investment analysis
