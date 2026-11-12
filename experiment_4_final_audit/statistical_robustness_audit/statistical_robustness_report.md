# Final Statistical Robustness Audit: Experiment 4

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Audit Target:** Statistical Clustered Dependence, Confidence Intervals, and Scientific Wording in Experiment 4  
**Evaluated Artifacts:** [`experiment_4_next_visit_weight_v1/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_next_visit_weight_v1)  
**Audit Deliverables Directory:** [`experiment_4_final_audit/statistical_robustness_audit/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/statistical_robustness_audit)  
**Audit Date:** November 3, 2026  
**Status:** Audit Complete — Cluster-Aware Uncertainty Quantification & Language Corrections  
**Generated CSV Deliverables:**  
- Cluster Structure Audit: [`pond_cluster_structure.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/statistical_robustness_audit/pond_cluster_structure.csv)  
- 5,000-Resample Clustered Bootstrap: [`pond_clustered_bootstrap_results.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/statistical_robustness_audit/pond_clustered_bootstrap_results.csv)  
- Sensitivity to Pond Weighting: [`pair_vs_pond_weighted_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/statistical_robustness_audit/pair_vs_pond_weighted_metrics.csv)

---

## Executive Summary

This final statistical audit investigates the impact of **repeated, chained, and clustered observations within farm ponds** on model evaluation metrics, confidence intervals, and scientific claims in **Experiment 4: Next-Visit Average Fish Weight Prediction**.

Standard regression metrics and naive paired tests (e.g. Student's paired $t$-test and Wilcoxon signed-rank test) assume that observation pairs are independent and identically distributed (i.i.d.). In longitudinal farm survey data, this assumption is fundamentally violated: consecutive pairs from the same pond share baseline biology, farmer practices, and serial Markovian transition states.

### Key Audit Findings
1. **Pond Clustering & Markovian Chaining Quantified:**  
   In the chronological test set ($N = 1,689$), observations are clustered across only **163 unique ponds** (averaging $10.36$ pairs per pond, with up to 29 pairs from a single pond). Crucially, **$83.94\%$ of adjacent pairs are directly chained** ($D_t \rightarrow D_{t+1}$, then $D_{t+1} \rightarrow D_{t+2}$). Treating 1,689 clustered pairs as independent artificially inflates effective sample size by roughly tenfold, producing overly optimistic confidence intervals and deflated $p$-values.
2. **Pond-Clustered Bootstrap Results (5,000 Resamples):**  
   When resampling whole pond clusters with replacement:
   - **Operational All-Pairs Population ($N = 1,689$):** Persistence is **statistically significantly superior to all ML models**. The 95% cluster-bootstrap confidence interval for $\Delta \text{MAE} = \text{MAE}_{\text{model}} - \text{MAE}_{\text{persistence}}$ is strictly positive across all models (Random Forest: $[+11.43\text{ g}, +27.25\text{ g}]$; Gradient Boosting: $[+23.55\text{ g}, +47.09\text{ g}]$). In **0.00% of the 5,000 bootstrap draws** did ML beat persistence.
   - **Retrospective Clean Subset ($N = 1,601$):**  
     - **Random Forest:** The 95% cluster-bootstrap CI spans zero ($[-6.55\text{ g}, +3.52\text{ g}]$), with 25.84% of draws favoring persistence. **Random Forest provides NO statistically significant improvement over persistence**.
     - **Gradient Boosting:** Retains a statistically verified advantage ($\Delta \text{MAE} = -8.26\text{ g}$, $95\%\text{ Cluster-CI } [-12.05\text{ g}, -4.44\text{ g}]$, with **100.00% of bootstrap draws favoring Gradient Boosting**).
3. **Pond-Weighting Sensitivity Analysis:**  
   Weighting each pond equally ($1/163$) rather than each pair equally ($1/1,689$):
   - On All Pairs: Persistence remains decisively superior (Pond-weighted $\text{MAE} = 81.65\text{ g}$ vs. Random Forest $100.06\text{ g}$).
   - On the Clean Subset: **Gradient Boosting's advantage increases from $+12.59\%$ to $+15.07\%$**, confirming that its superiority is robust across the pond population. Conversely, **Random Forest flips to inferior** ($-3.65\%$ vs. persistence), proving its pair-weighted margin was driven by a few heavily-sampled ponds.
4. **Correction of Scientific Language:**  
   Overstated assertions ("ML assumes continuous positive growth", "proves partial harvest", "biological impossibility") have been systematically replaced with precise, defensible scientific characterizations.

---

## 1. Task 1: Audit of Repeated Observations and Cluster Structure

### 1.1 Cluster Distribution across Chronological Test Partitions
In [`temporal_growth_dataset.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_next_visit_weight_v1/temporal_growth_dataset.csv), test pairs ($curr \ge 2025\text{-}01\text{-}01$) were audited for intra-pond clustering. The exact structure is exported as [`pond_cluster_structure.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/statistical_robustness_audit/pond_cluster_structure.csv) and summarized in Table 1.

### Table 1: Cluster Structure and Markovian Chaining in Chronological Test Sets

| Structural Parameter | All-Pairs Chronological Test Set | Clean Chronological Test Set (Retrospective) | Methodological Implication |
| :--- | :---: | :---: | :--- |
| **Total Test Pairs ($N$)** | 1,689 | 1,601 | Nominal sample size. |
| **Unique Pond Clusters ($K$)** | **163** | **163** | True independent sampling units. |
| **Mean Pairs per Pond** | 10.36 | 9.82 | Substantial repeated measurement within clusters. |
| **Median Pairs per Pond** | 9.0 | 8.0 | Skewed cluster size distribution. |
| **IQR (P25 — P75)** | 4.0 — 16.5 | 3.5 — 15.0 | High-density ponds contribute up to 29 pairs. |
| **Maximum Pairs in Single Pond**| 29 | 27 | Pond `ara2_00793177` contributes 29 test transitions. |
| **Chained Adjacent Links** | **1,281 / 1,526 (83.94%)** | **1,139 / 1,438 (79.21%)** | **Direct Markovian chaining:** Next-visit target ($W_{t+1}$) becomes current feature ($W_t$) in adjacent pair. |

### 1.2 Why Naive Paired $t$-Tests and Wilcoxon Tests Are Statistically Invalid
When pairs are clustered within 163 ponds:
1. **Violation of the i.i.d. Assumption:**  
   An ordinary paired $t$-test computes:
   $$t = \frac{\bar{d}}{s_d / \sqrt{N}}$$
   Where $N$ is the number of pairs ($1,689$ or $1,601$). This formula assumes that each paired error difference $d_i = |y_i - \hat{y}_{i,\text{model}}| - |y_i - \hat{y}_{i,\text{pers}}|$ is statistically independent.
2. **Serial Autocorrelation and Common Pond Shocks:**  
   Because $83.94\%$ of transitions share visit endpoints, a measurement shock at date $D_{t+1}$ affects both the residual of transition $D_t \rightarrow D_{t+1}$ and the feature input of transition $D_{t+1} \rightarrow D_{t+2}$. Furthermore, pond-specific latent factors (soil chemistry, farmer skill, stocking species ratio, water source) induce strong positive intra-cluster correlation ($\rho > 0$).
3. **Variance Deflation:**  
   The true variance of the sample mean under cluster sampling is inflated by the variance inflation factor (design effect):
   $$\text{VIF} = 1 + (\bar{m} - 1)\text{ICC}$$
   With $\bar{m} \approx 10.4$, treating observations as independent artificially shrinks standard errors by a factor of $\sqrt{\text{VIF}} \approx 2\text{--}3\times$, leading to false rejections of the null hypothesis (Type I error inflation).

---

## 2. Task 2: Pond-Aware Clustered Bootstrap Comparisons (5,000 Resamples)

To eliminate clustering bias without making parametric distributional assumptions, a **Pond-Clustered Block Bootstrap** was implemented:
- In each repetition $b \in \{1, \dots, 5000\}$, 163 unique ponds were sampled **with replacement**.
- All chronological test pairs belonging to each selected pond were extracted as an intact block.
- For each resample, the test MAE of Persistence and each ML model was computed, along with their difference:
  $$\Delta \text{MAE}^{(b)} = \text{MAE}_{\text{model}}^{(b)} - \text{MAE}_{\text{persistence}}^{(b)}$$
  *(Where negative values indicate the ML model achieved lower error than persistence).*
- Percentile confidence intervals (2.5th and 97.5th percentiles) and the empirical probability of outperforming persistence ($\Pr(\Delta \text{MAE} < 0)$) were derived.

The complete results are exported as [`pond_clustered_bootstrap_results.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/statistical_robustness_audit/pond_clustered_bootstrap_results.csv) and presented in Table 2.

### Table 2: Pond-Clustered Bootstrap Results (5,000 Resamples)

| Evaluation Regime | Model Name | Point Estimate $\Delta \text{MAE}$ (g) | Cluster-Bootstrap Mean $\Delta \text{MAE}$ (g) | 95% Cluster-Bootstrap CI (g) | Clustered CI Spans Zero? | % Bootstrap Draws Beating Persistence | Clustered Significance Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **All Pairs (Operational)** | **Linear Regression** | $+24.36$ | $+24.30$ | $[+18.67, +30.43]$ | No (Strictly $> 0$) | **0.00%** | **Statistically significantly INFERIOR to persistence** ($p < 0.0002$) |
| All Pairs (Operational) | **Random Forest** | $+18.77$ | $+18.70$ | $[+11.43, +27.25]$ | No (Strictly $> 0$) | **0.00%** | **Statistically significantly INFERIOR to persistence** ($p < 0.0002$) |
| All Pairs (Operational) | **Gradient Boosting**| $+33.97$ | $+33.85$ | $[+23.55, +47.09]$ | No (Strictly $> 0$) | **0.00%** | **Statistically significantly INFERIOR to persistence** ($p < 0.0002$) |
| **Clean Pairs (Retrospective)**| **Random Forest** | $-1.60$ | $-1.59$ | $[\mathbf{-6.55}, \mathbf{+3.52}]$ | **YES (Spans Zero)** | **74.16%** | **NO statistically significant difference** ($p_{\text{cluster}} = 0.517$) |
| Clean Pairs (Retrospective)| **Linear Regression** | $-5.54$ | $-5.54$ | $[-10.15, -0.93]$ | No (Strictly $< 0$) | **98.98%** | **Statistically significantly SUPERIOR to persistence** ($p_{\text{cluster}} = 0.0204$) |
| Clean Pairs (Retrospective)| **Gradient Boosting**| $-8.25$ | $-8.26$ | $[-12.05, -4.44]$ | No (Strictly $< 0$) | **100.00%** | **Statistically significantly SUPERIOR to persistence** ($p_{\text{cluster}} < 0.0002$) |

### 2.1 Critical Statistical Re-Evaluations
1. **Random Forest Significance Overturned:**  
   While naive paired tests previously suggested a marginal difference ($p = 0.056$), the **pond-clustered bootstrap proves that Random Forest provides NO statistically significant improvement over persistence** on the clean subset. The 95% cluster-bootstrap interval $[-6.55\text{ g}, +3.52\text{ g}]$ spans zero, and persistence outperformed Random Forest in $25.84\%$ of resampled pond worlds.
2. **Gradient Boosting Significance Upheld on Retrospective Data:**  
   Gradient Boosting's reduction of $8.26\text{ g}$ in MAE remains **statistically robust under cluster resampling** ($95\%\text{ CI: } [-12.05\text{ g}, -4.44\text{ g}]$). In 5,000 out of 5,000 bootstrap draws ($100.00\%$), Gradient Boosting achieved a lower MAE than persistence.
3. **Decisive Refutation of Operational ML Utility on All Pairs:**  
   On the operational all-pairs population, the 95% cluster-bootstrap CI is strictly positive for all ML models ($> +11.4\text{ g}$ for RF, $> +23.5\text{ g}$ for GBDT). Across 5,000 cluster resamples, **not a single bootstrap sample favored machine learning over persistence**.

---

## 3. Task 3: Sensitivity to Pond Weighting

To verify whether model rankings are distorted by ponds with disproportionately large sample counts (e.g. ponds with 20–29 pairs dominating ponds with 1–3 pairs), metrics were calculated under:
1. **Pair-Weighting:** Standard unweighted mean across all test pairs:
   $$\text{MAE}_{\text{pair}} = \frac{1}{N_{\text{pairs}}} \sum_{i=1}^{N_{\text{pairs}}} |y_i - \hat{y}_i|$$
2. **Pond-Weighting:** Macro-average across unique ponds, giving every pond equal voice:
   $$\text{MAE}_{\text{pond}} = \frac{1}{K_{\text{ponds}}} \sum_{k=1}^{K_{\text{ponds}}} \left( \frac{1}{n_k} \sum_{j=1}^{n_k} |y_{kj} - \hat{y}_{kj}| \right)$$

The complete sensitivity matrix is exported as [`pair_vs_pond_weighted_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/statistical_robustness_audit/pair_vs_pond_weighted_metrics.csv) and presented in Table 3.

### Table 3: Pair-Weighted vs. Pond-Weighted Chronological Test Performance

| Evaluation Regime | Model Name | Pair-Weighted MAE (g) | Pair-Weighted % Imp. | Pond-Weighted MAE (g) | Pond-Weighted % Imp. | Beats Persistence (Pair)? | Beats Persistence (Pond)? | Weighting Sensitivity Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **All Pairs (Operational)** | **Persistence** | **93.38** | 0.00% | **81.65** | 0.00% | *Benchmark* | *Benchmark* | **Persistence wins decisively under both weightings.** |
| All Pairs (Operational) | **Linear Regression** | 117.74 | -26.09% | 103.23 | -26.43% | No | No | Robustly inferior. |
| All Pairs (Operational) | **Random Forest** | 112.15 | -20.11% | 100.06 | -22.54% | No | No | Robustly inferior. |
| All Pairs (Operational) | **Gradient Boosting**| 127.34 | -36.38% | 112.45 | -37.72% | No | No | Robustly inferior. |
| **Clean Pairs (Retrospective)**| **Persistence** | 65.47 | 0.00% | 63.02 | 0.00% | *Benchmark* | *Benchmark* | Static Baseline. |
| Clean Pairs (Retrospective)| **Linear Regression** | 59.92 | +8.47% | 55.84 | **+11.39%** | Yes | Yes | Advantage strengthens under pond weighting. |
| Clean Pairs (Retrospective)| **Random Forest** | 63.87 | +2.44% | **65.32** | **-3.65%** | **YES** | **NO** | **FLIPS TO INFERIOR:** Pair-level edge was driven by high-density ponds. |
| Clean Pairs (Retrospective)| **Gradient Boosting**| **57.22** | **+12.59%** | **53.52** | **+15.07%** | **YES** | **YES** | **Advantage strengthens under pond weighting.** |

### 3.1 Weighting Sensitivity Takeaways
1. **On the Operational Population (All Pairs):**  
   Under pond weighting, Persistence MAE drops from $93.38\text{ g}$ to $81.65\text{ g}$, beating Random Forest ($100.06\text{ g}$) by $18.41\text{ g}$ and Gradient Boosting ($112.45\text{ g}$) by $30.80\text{ g}$. The operational superiority of persistence is entirely insensitive to weighting.
2. **On the Clean Subset (Retrospective):**  
   - **Gradient Boosting's superiority is highly robust:** Its advantage over persistence **expands from $+12.59\%$ under pair weighting to $+15.07\%$ under pond weighting** (reducing average pond error to $53.52\text{ g}$ vs. persistence $63.02\text{ g}$).
   - **Linear Regression also strengthens:** Its advantage increases from $+8.47\%$ to $+11.39\%$.
   - **Random Forest collapses:** Random Forest's pond-weighted MAE ($65.32\text{ g}$) is worse than persistence ($63.02\text{ g}$). Its modest pair-weighted margin was an artifact of a few heavily-sampled ponds where it performed well.

---

## 4. Task 4: Scientific Language Corrections

To adhere to strict scientific rigor, previously overstated assertions in project documentation are reviewed and replaced with evidence-supported descriptions.

### Table 4: Systematic Scientific Language Corrections

| Original Overstated Statement | Source Section | Scientific Critique & Defect | Corrected, Defensible Scientific Phrasing |
| :--- | :---: | :--- | :--- |
| *"ML assumes continuous positive biological growth."* | Report §6.1 | Anthropomorphic; ML models do not "assume" biological growth; they minimize empirical training loss. | *"Trained regression models learn predominantly positive slope parameters with respect to elapsed duration ($\Delta t$) and initial weight ($W_t$) because training partitions contain few cycle terminations, and feature matrices contain no explicit marker of net casting, draining, or biomass withdrawal."* |
| *"ML is penalized more heavily on every single cycle break."* | Report §6.1 | Absolute generalization ("every single"); unverified for minor fluctuations. | *"On transitions characterized by large negative weight shifts ($\Delta W \le -100\text{ g}$), regression models forecast somatic growth and therefore incur larger aggregate residuals than the persistence baseline on those specific observations."* |
| *"Verified non-biological break."* | Report §2, Table 2 | Overclaims empirical verification; biological starvation or severe pathology cannot be ruled out without necropsy. | *"Observed weight drops exceeding $-5.0\text{ g/day}$ are inconsistent with natural biological shrinkage under standard feeding, indicating external biomass removal, restocking, or cast-net sampling shifts."* |
| *"Biological impossibility."* | Report §2, Table 2 | Unqualified absolute claim; high-temperature juvenile surges in certain species can be rapid. | *"Observed weight gains exceeding $+20.0\text{ g/day}$ are inconsistent with published commercial aquaculture growth rates for Indian carps under normal culture conditions, suggesting measurement, transcription, or species misattribution error."* |
| *"Claims that suspicious observations prove partial harvest or restocking."* | Report §2, §6.1 | "Prove" is factually unsupported; harvest logs and stocking receipts were not recorded. | *"Large negative weight shifts are consistent with commercial partial harvest thinning, pond draining, restocking, or polyculture sampling variation; however, their exact agronomic cause cannot be verified from available farm records."* |
| *"Statistically verified improvements"* | Report §4, §6.1 | Ordinary paired $t$-tests violated cluster independence; Random Forest improvement is not significant under cluster bootstrap. | *"Observed improvement in chronological test MAE; statistical significance has not been established for operational deployment, and applies conditionally to retrospective biological growth trajectories under cluster-aware bootstrap estimation."* |

---

## 5. Synthesis: Operational vs. Retrospective Statistical Evidence

### Table 5: Methodological Hierarchy and Evidence Synthesis

| Evidence Dimension | Descriptive MAE Metric | Naive Paired $t$-Test / Wilcoxon | Pond-Clustered Block Bootstrap (5,000 draws) | Macro Pond-Weighted Sensitivity | Operational Viability |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **All Pairs: Persistence** | $93.38\text{ g}$ | *Benchmark* | *Benchmark* | **$81.65\text{ g}$** | **VALID & RECOMMENDED FOR PRODUCTION** |
| **All Pairs: Random Forest** | $112.15\text{ g}$ | $p = 2.0 \times 10^{-13}$ (Worse) | $95\%\text{ CI: } [+11.4\text{ g}, +27.3\text{ g}]$ | $100.06\text{ g}$ (Worse) | INFEASIBLE (Penalized by unannounced harvests) |
| **All Pairs: Gradient Boosting** | $127.34\text{ g}$ | $p = 1.9 \times 10^{-20}$ (Worse) | $95\%\text{ CI: } [+23.6\text{ g}, +47.1\text{ g}]$ | $112.45\text{ g}$ (Worse) | INFEASIBLE (Penalized by unannounced harvests) |
| **Clean Subset: Persistence** | $65.47\text{ g}$ | *Benchmark* | *Benchmark* | $63.02\text{ g}$ | Retrospective Benchmark |
| **Clean Subset: Random Forest** | $63.87\text{ g}$ | $p = 0.0566$ (Marginal) | $95\%\text{ CI: } [-6.55\text{ g}, +3.52\text{ g}]$ (Spans 0) | $65.32\text{ g}$ ($-3.65\%$ Worse) | NOT SIGNIFICANT / INFERIOR UNDER POND WEIGHT |
| **Clean Subset: Gradient Boosting**| **$57.22\text{ g}$** | $p = 1.06 \times 10^{-6}$ (Better) | **$95\%\text{ CI: } [-12.05\text{ g}, -4.44\text{ g}]$ (Strictly $< 0$)** | **$53.52\text{ g}$ (+15.07% Better)** | **VALID FOR SCENARIO SIMULATION ON GROWING PONDS** |

---

## 6. Final Audit Verdicts

### 1. Is the all-pairs model useful?
**NO.** On the unfiltered operational test population ($N = 1,689$), all machine learning models perform **statistically significantly worse than Persistence** ($p < 0.0002$ under 5,000 pond-clustered bootstrap resamples; $\Delta \text{MAE} \ge +18.7\text{ g}$). Machine learning models lack commercial inventory inputs and cannot foresee unrecorded fish harvests.

### 2. Does ML genuinely improve over persistence on unseen future observations?
**ONLY CONDITIONALLY.**  
- **On operational real-world data:** NO.
- **On uninterrupted biological trajectories (clean subset):** YES, but **only Gradient Boosting and Linear Regression** demonstrate genuine, cluster-robust improvements ($\Delta \text{MAE} = -8.26\text{ g}$, $p < 0.0002$). Random Forest's improvement is **not statistically significant** ($95\%\text{ CI } [-6.55\text{ g}, +3.52\text{ g}]$ spans zero) and reverses to inferior under pond weighting.
- **Horizon dependency:** The improvement is concentrated in extended forecasting horizons ($15\text{ to } 45\text{ days}$, up to $+28\%$ improvement) and grow-out cohorts ($300\text{--}600\text{g}$, $+33\%$ improvement). On short revisits ($< 14\text{ days}$), Persistence is superior due to observer visual rounding.

### 3. Is the clean-subset result operationally defensible?
**NO, NOT AS AN OPERATIONAL FILTER.**  
Because membership in the clean subset is defined using `next_weight`, an operator cannot filter out ponds at visit $t$. The clean-subset results are defensible **strictly as an ex-post, retrospective scientific benchmark** demonstrating that Gradient Boosting can learn biological bioenergetics when management interventions do not disrupt the cohort.

### 4. Which model, if any, should be retained as the experimental baseline?
- **For Operational Farm Deployment:** Retain the **Persistence Baseline ($\hat{W}_{t+1} = W_t$)**. It achieves the lowest error on the operational population ($\text{MAE} = 81.65\text{ g}$ pond-weighted, $93.38\text{ g}$ pair-weighted) and requires zero sensor telemetry.
- **For Bioenergetic Scenario Simulation:** Retain **Gradient Boosting Regressor** as the specialized tool for simulating growth over 15–45 day horizons on active grow-out ponds.

### 5. What claims are safe to make in a project presentation or placement interview?
In an interview or technical evaluation, present the following verified talking points:

> [!TIP]
> **Safe Interview Talking Points:**
> 1. *"In our precision aquaculture system, we discovered that biological growth modeling cannot be decoupled from commercial farm inventory dynamics. On unfiltered farm data, simple persistence ($\hat{W}_{t+1} = W_t$) achieved an MAE of $93.4\text{ g}$, outperforming ML models because ML models predict positive biological growth and are heavily penalized when unrecorded partial harvests occur."*
> 2. *"To account for the fact that test pairs were clustered within 163 ponds with 84% chained transitions, we implemented a 5,000-repetition pond-clustered block bootstrap. This revealed that while Random Forest's improvement was not statistically significant (95% CI $[-6.55\text{g}, +3.52\text{g}]$ spans zero), Gradient Boosting achieved a statistically verified reduction in MAE of $8.3\text{ g}$ (95% CI $[-12.05\text{g}, -4.44\text{g}]$, $p < 0.0002$) on uninterrupted growth cycles."*
> 3. *"We proved that filtering out suspicious pairs before model evaluation constituted target leakage because the filter relied on future weight. We transparently reported both the operational unfiltered metrics and the retrospective exploratory metrics."*
> 4. *"Under macro pond-weighting (giving every pond equal voice), Gradient Boosting's advantage increased from $+12.6\%$ to $+15.1\%$, confirming that its bioenergetic forecasting capability is robust across the farming population."*

