# Sensor-Ablation Experiment Report: Model A (8 Features) vs. Model B (6 Features)

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment Identifier:** `experiment_1_sensor_ablation_v1`  
**Execution Date:** 2026-11-03  
**Status:** **TRAINED, EVALUATED, AND FULLY AUDITED**  
**Serialized Models Directory:** [`experiment_1_sensor_ablation_v1/models/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/models/)  
**Evaluation Metrics CSV:** [`experiment_1_sensor_ablation_v1/metrics/sensor_ablation_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/metrics/sensor_ablation_metrics.csv)  
**Feature Importances Comparison CSV:** [`experiment_1_sensor_ablation_v1/metrics/feature_importances_comparison.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/metrics/feature_importances_comparison.csv)  
**Original Experiment 1 Preserved:** All files in [`baseline_toxicity_v1/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/) remain completely unmodified.  

---

## 1. Executive Summary & Objective

In our initial Experiment 1 evaluation, the 8-feature `RandomForestRegressor` achieved strong spatial performance across unseen ponds ($R^2 = 0.5007$, $\text{MAE} = 0.01396\text{ mg/L}$), but collapsed under chronological holdout testing ($R^2 = -0.2983$). The forensic audit revealed that this collapse coincided with a field protocol shift: **Secchi depth turbidity and handheld TDS were permanently discontinued in 2025–2026 ($100\%$ missing)**, despite `tds_ppt` accounting for $20.64\%$ of the model's predictive weight.

The core objective of this controlled follow-up experiment is to answer a fundamental operational question:  
**Does completely removing TDS and Turbidity from the feature space improve chronological generalization, and what spatial accuracy is sacrificed across unseen ponds?**

### Key Findings Summary:
1. **Chronological Error Reduced by 14.0% in Model B:**  
   Completely excluding TDS and Turbidity (Model B) improves chronological holdout MAE from **$0.01970\text{ mg/L}$ (Model A) down to $0.01694\text{ mg/L}$ (Model B)**—a **$14.0\%$ reduction in prediction error**, while improving $R^2$ by **$+0.1186$** (from $-0.2983$ to $-0.1797$).
2. **Minimal Spatial Sacrifice (Only 3.2% Variance Lost):**  
   Under 5-fold `GroupKFold` cross-validation across 317 unseen ponds ($N = 6,945$), Model B retains an out-of-fold **$R^2 = 0.4690$** (vs. $0.5007$ for Model A), with MAE increasing only marginally from $0.01396$ to $0.01454\text{ mg/L}$ ($+4.1\%$).
3. **Honest Scientific Reality (Temporal Drift Persists):**  
   Although Model B is substantially more robust than Model A under sensor omission, **sensor ablation alone does not yield a positive chronological $R^2$** ($R^2 = -0.1797$). Both models underperform the naive historical mean ($R^2 = -0.0252$) on the 2025–2026 test set. This proves that sensor deprecation was a major contributing factor, but not the sole driver of temporal concept drift; target distribution compression ($38.9\%$ lower target variance in 2025–2026) and field assay reagent transitions also contribute to the temporal shift.

---

## 2. Experimental Design & Model Configurations

Both models were trained using identical random seeds (`42`) and matching `RandomForestRegressor` hyperparameters (`n_estimators=100`, `min_samples_leaf=2`, `random_state=42`, `n_jobs=-1`). Preprocessing pipelines were fitted strictly on training data within each fold and split.

```mermaid
flowchart TD
    subgraph Input Data
        A["toxicity_analysis_v2.csv (N = 6,945)"]
    end

    subgraph Model A: Full Telemetry Configuration
        A --> B1["8 Features + 2 Indicators"]
        B1 --> B2["cont: DO, pH, Temp, Turbidity, TDS (median imputer)"]
        B1 --> B3["ind: TDS missing, Turbidity missing (constant 0.0)"]
        B1 --> B4["cat: Weather, Color, Region (OHE)"]
        B2 --> B5["RandomForestRegressor"]
        B3 --> B5
        B4 --> B5
    end

    subgraph Model B: Sensor-Ablated Configuration
        A --> C1["6 Features Strictly"]
        C1 --> C2["cont: DO, pH, Temp (median imputer)"]
        C1 --> C3["EXCLUDED: TDS, Turbidity & Indicators"]
        C1 --> C4["cat: Weather, Color, Region (OHE)"]
        C2 --> C5["RandomForestRegressor"]
        C4 --> C5
    end

    subgraph Dual Validation Protocols
        B5 --> D1["Protocol 1: 5-Fold GroupKFold (Spatial)"]
        B5 --> D2["Protocol 2: Chronological Split (Temporal)"]
        C5 --> D1
        C5 --> D2
    end
```

### Configuration Summary:
- **Model A (8-Feature System + Missingness Indicators):**  
  Features: `dissolved_oxygen_mg_l`, `ph`, `temp_c`, `turbidity_cm`, `tds_ppt`, `tds_ppt_is_missing`, `turbidity_cm_is_missing`, `Weather`, `water_color`, `region`. When evaluated on post-2024 test data, missing TDS and Turbidity receive training-set median constants ($1.17\text{ ppt}$ and $29.0\text{ cm}$).
- **Model B (6-Feature System Strictly):**  
  Features: `dissolved_oxygen_mg_l`, `ph`, `temp_c`, `Weather`, `water_color`, `region`. `tds_ppt`, `turbidity_cm`, and their missingness indicators are completely barred from the pipeline. No median constants are ever generated.
- **Reference Baselines:**
  - `Dummy_Mean`: Always predicts the training set mean.
  - `Dummy_Median`: Always predicts the training set median.
  - `Ablation_pH_Temp`: `RandomForestRegressor` trained strictly on `['ph', 'temp_c']`.

---

## 3. Protocol 1: 5-Fold GroupKFold Cross-Validation (Spatial Generalization)

Evaluates performance across 317 independent ponds ($N = 6,945$). Validation ponds are strictly withheld from training in each fold.

### 3.1 GroupKFold Per-Fold Metrics

| Model Configuration | Fold 1 $R^2$ | Fold 2 $R^2$ | Fold 3 $R^2$ | Fold 4 $R^2$ | Fold 5 $R^2$ | Mean $R^2 \pm \text{Std}$ | Mean MAE ($\text{mg/L}$) | Mean RMSE ($\text{mg/L}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Dummy_Mean` | -0.010 | -0.012 | -0.007 | -0.026 | +0.007 | $-0.009 \pm 0.010$ | $0.02013 \pm 0.0016$ | $0.04160 \pm 0.0091$ |
| `Dummy_Median` | -0.054 | -0.058 | -0.052 | -0.093 | -0.010 | $-0.053 \pm 0.025$ | $0.01837 \pm 0.0023$ | $0.04255 \pm 0.0097$ |
| `Ablation_pH_Temp` | +0.134 | -0.347 | +0.278 | +0.219 | -0.002 | $+0.057 \pm 0.281$ | $0.01835 \pm 0.0012$ | $0.03896 \pm 0.0046$ |
| **Model A (8 Features)** | **+0.559** | **+0.329** | **+0.537** | **+0.602** | **+0.442** | **$+0.494 \pm 0.105$** | **$0.01396 \pm 0.0019$** | **$0.02932 \pm 0.0066$** |
| **Model B (6 Features)** | **+0.505** | **+0.334** | **+0.528** | **+0.506** | **+0.373** | **$+0.449 \pm 0.078$** | **$0.01454 \pm 0.0018$** | **$0.03043 \pm 0.0057$** |

### 3.2 Global Out-of-Fold (OOF) Comparison ($N = 6,945$)

| Model Configuration | Global OOF MAE ($\text{mg/L}$) | Global OOF RMSE ($\text{mg/L}$) | Global OOF $R^2$ | Relative Lift vs. Dummy Median MAE | Relative Lift vs. pH+Temp Ablation $R^2$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `Dummy_Mean` | 0.02013 | 0.04239 | -0.0027 | Baseline | Baseline |
| `Dummy_Median` | 0.01837 | 0.04343 | -0.0523 | Reference (0.0%) | — |
| `Ablation_pH_Temp` | 0.01835 | 0.03918 | +0.1436 | +0.1% | Reference ($0.1436$) |
| **Model B (6 Features)** | **0.01454** | **0.03085** | **+0.4690** | **+20.9%** | **+0.3254 ($3.3\times$ lift)** |
| **Model A (8 Features)** | **0.01396** | **0.02991** | **+0.5007** | **+24.0%** | **+0.3571 ($3.5\times$ lift)** |

### Spatial Trade-Off Analysis:
- **Cost of Sensor Removal:** Model B loses **$0.0317$ in $R^2$** ($0.4690$ vs. $0.5007$) and experiences a modest **$4.1\%$ increase in MAE** (from $0.01396$ to $0.01454\text{ mg/L}$).
- **Higher Cross-Fold Stability:** The standard deviation across folds for Model B ($0.078$) is lower than Model A ($0.105$), indicating that Model B is less sensitive to pond-specific salinity variations.
- **Strong Soft-Sensing Preserved:** Even without TDS or Turbidity, Model B explains **$46.90\%$ of ammonia variance**, vastly exceeding the $14.36\%$ explained by temperature and pH alone.

---

## 4. Protocol 2: Chronological Holdout Evaluation (Temporal Generalization)

Trained on historical seasons (2021–2024, $N = 4,345$, 239 ponds) and evaluated out-of-sample on future seasons (2025–2026, $N = 2,600$, 176 ponds). In 2025–2026, TDS and Turbidity are $100\%$ unrecorded.

### 4.1 Chronological Test Performance Benchmarks ($N = 2,600$)

| Model Configuration | Test MAE ($\text{mg/L}$) | Test RMSE ($\text{mg/L}$) | Test $R^2$ | MAE Comparison vs. Model A | $R^2$ Comparison vs. Model A |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `Dummy_Mean` | 0.01574 | 0.02784 | -0.0252 | -20.1% | +0.2731 |
| `Dummy_Median` | 0.01517 | 0.02896 | -0.1094 | -23.0% | +0.1889 |
| `Ablation_pH_Temp` | 0.01591 | 0.02817 | -0.0499 | -19.2% | +0.2484 |
| **Model A (8 Features)** | **0.01970** | **0.03133** | **-0.2983** | **Reference** | **Reference** |
| **Model B (6 Features)** | **0.01694** | **0.02986** | **-0.1797** | **-14.0% (Improved)** | **+0.1186 (Improved)** |

### 4.2 Detailed Forensic Analysis of the Results

#### Q1: Did removing TDS and turbidity improve chronological generalization?
- **Relative Answer: YES.**  
  Model B achieved a **$14.0\%$ reduction in absolute error** (MAE dropped from $0.01970$ to $0.01694\text{ mg/L}$) and an **$R^2$ improvement of $+0.1186$** (from $-0.2983$ to $-0.1797$). Model B eliminated the harmful variance caused by Model A trying to evaluate decision splits on static median imputation values.
- **Absolute / Global Answer: NO.**  
  Model B’s $R^2$ remains **negative ($-0.1797$)**, and its MAE ($0.01694$) remains worse than the historical mean ($0.01574$) and historical median ($0.01517$).

#### Q2: Why does Model B still produce a negative $R^2$?
Removing the deprecated sensors isolated one major failure mode (sensor imputation mismatch), but exposed two remaining underlying temporal drift mechanisms:
1. **Target Distribution Compression:**  
   In 2021–2024, the target mean was $0.0223\text{ mg/L}$ with a standard deviation of $0.0450\text{ mg/L}$. In 2025–2026, the target mean was $0.0191\text{ mg/L}$ with a standard deviation of $0.0275\text{ mg/L}$ ($38.9\%$ lower target variance). Because the sum-of-squares denominator in $R^2$ is small, slight over-predictions on low-toxicity days result in a mathematically negative $R^2$.
2. **Shift in Chemical Assay Methodology:**  
   As audited in the scientific consistency report, 2021–2024 relied exclusively on nitrogen-basis TAN kits (Source 1), whereas 2026 switched entirely to molecular TAN kits (Source 2). The model trained on Source 1 was evaluated on Source 2, introducing calibration bias.

---

## 5. Feature Importances: How the Model Rebalanced Its Decisions

When TDS ($20.64\%$ importance) and Turbidity ($3.46\%$ importance) were removed, Model B redistributed its split decisions across the remaining 6 features:

| Feature Identifier | Importance in Model A (8 Features) | Importance in Model B (6 Features) | Absolute Change | Relative Rebalancing |
| :--- | :---: | :---: | :---: | :--- |
| `ph` | 40.03% | **41.90%** | +1.87% | Retains primary thermodynamic role. |
| `temp_c` | 14.35% | **20.57%** | **+6.22%** | Takes over a large share of the lost signal. |
| `dissolved_oxygen_mg_l` | 6.31% | **9.00%** | **+2.69%** | Becomes primary proxy for algal photosynthesis. |
| `region_Nellore` | 2.97% | **8.40%** | **+5.43%** | Captures coastal geographical baseline differences. |
| `water_color_Light green` | 1.84% | **6.96%** | **+5.12%** | Absorbs the visual algal density signal previously provided by Secchi clarity. |
| `region_Eluru` | 4.63% | **5.67%** | +1.04% | Inland cluster baseline. |
| `Weather_Sunny` | 1.34% | **1.41%** | +0.07% | Solar radiation signal. |
| `tds_ppt` | 20.64% | **EXCLUDED** | -20.64% | Successfully eliminated. |
| `turbidity_cm` | 3.46% | **EXCLUDED** | -3.46% | Successfully eliminated. |
| `tds_ppt_is_missing` | 0.85% | **EXCLUDED** | -0.85% | Successfully eliminated. |

**Key Feature Rebalancing Insight:**  
In Model B, `water_color_Light green` surged from $1.84\%$ to **$6.96\%$** ($3.8\times$ increase), and `dissolved_oxygen_mg_l` rose to **$9.00\%$**. The random forest organically compensated for the loss of physical Secchi depth by placing greater weight on visual water hue and oxygen levels!

---

## 6. Diagnostic Visualizations

All diagnostic figures were generated at 300 DPI and saved in [`experiment_1_sensor_ablation_v1/plots/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/plots/):

1. **[`actual_vs_predicted_groupkfold.png`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/plots/actual_vs_predicted_groupkfold.png):**  
   Shows out-of-fold predictions for Model A ($R^2 = 0.501$) vs. Model B ($R^2 = 0.469$). Both models closely track the 1:1 diagonal across $0.00 - 0.20\text{ mg/L}$, with Model A showing marginally tighter clustering on high spikes.
2. **[`residuals_groupkfold.png`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/plots/residuals_groupkfold.png):**  
   Side-by-side residual plots demonstrating comparable, well-centered error profiles for both models.
3. **[`actual_vs_predicted_chronological.png`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/plots/actual_vs_predicted_chronological.png):**  
   Illustrates predictions on the 2025–2026 test set. Shows that Model B’s predictions are noticeably tighter and less noisy than Model A’s, reflecting its $14.0\%$ lower MAE.
4. **[`residuals_chronological.png`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/plots/residuals_chronological.png):**  
   Highlights the residual distribution on recent production cycles, confirming that Model B reduces extreme residual spread compared to Model A.
5. **[`feature_importances_comparison.png`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/plots/feature_importances_comparison.png):**  
   Grouped horizontal bar chart visualizing the rebalancing of predictive weight from TDS and Turbidity into water color, DO, temperature, and region.

---

## 7. Operational Trade-Off & Final Recommendations

### 7.1 Direct Answer to the Research Question
> **Does Model B sacrifice unseen-pond performance to gain better chronological robustness?**  
> **YES.** Model B makes a **favorable trade-off**:
> - It sacrifices only **$3.2\%$ in explained variance on unseen ponds** ($R^2$ decreases from $0.5007$ to $0.4690$, with MAE increasing by only $0.00058\text{ mg/L}$).
> - In exchange, it achieves a **$14.0\%$ reduction in chronological forecasting error** ($0.01694$ vs. $0.01970\text{ mg/L}$) when deployed in operations where TDS and Secchi clarity are unavailable.

### 7.2 Engineering & Operational Recommendation
1. **Deploy Model B for Modern Field Operations:** Because commercial aquaculture operations post-2024 do not collect Secchi turbidity or handheld TDS, **Model B is the operationally superior model**. Deploying Model A with synthetic median imputations creates artificial variance and degrades performance.
2. **Do Not Claim Sensor Removal Solves Temporal Drift:** Sensor removal prevents the model from relying on phantom inputs, but does not eliminate temporal drift caused by chemical assay shifts or multi-year climate variability.
3. **Mandatory Reporting Boundary:** Both models must be reported honestly. Good spatial proxy performance ($R^2 \approx 0.47 - 0.50$) validates the physical soft-sensor concept across unseen farms, but chronological extrapolation without regular recalibration remains an open challenge.

---

## 8. Repository Manifest & Preservation Check

All deliverables are organized in [`experiment_1_sensor_ablation_v1/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/):
- **Models:** [`model_a_rf_pipeline.joblib`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/models/model_a_rf_pipeline.joblib), [`model_b_rf_pipeline.joblib`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/models/model_b_rf_pipeline.joblib)
- **Metrics:** [`sensor_ablation_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/metrics/sensor_ablation_metrics.csv), [`feature_importances_comparison.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/metrics/feature_importances_comparison.csv)
- **Plots:** All 5 diagnostic figures saved in [`experiment_1_sensor_ablation_v1/plots/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_sensor_ablation_v1/plots/)
- **Original Experiment 1 Integrity:** Unmodified and preserved in [`baseline_toxicity_v1/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/).
- **Source Datasets:** Completely unmodified in `dataset/` and `processed_data_v2/`.

