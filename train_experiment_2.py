import os
import sys
import tempfile

os.environ['MPLCONFIGDIR'] = os.path.join(tempfile.gettempdir(), 'mpl_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import GroupKFold
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix, precision_recall_curve, roc_curve
)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Setup directories
BASE_DIR = 'experiment_2_mortality_v1'
METRICS_DIR = os.path.join(BASE_DIR, 'metrics')
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

os.makedirs(METRICS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

print("=" * 80)
print("EXPERIMENT 2: FISH MORTALITY CLASSIFICATION")
print("Target: dead_fish_count > 0 (Binary)")
print("Source Dataset: processed_data_v2/toxicity_analysis_v2.csv")
print("=" * 80)

# =========================================================================
# STEP 1: DATA AUDIT & TARGET VALIDATION
# =========================================================================
print("\n[Step 1] Executing Data Audit and Target Verification...")
DATA_PATH = 'processed_data_v2/toxicity_analysis_v2.csv'
df_raw = pd.read_csv(DATA_PATH)
df_raw['datetime'] = pd.to_datetime(df_raw['datetime'])
df_raw['year'] = df_raw['datetime'].dt.year

total_raw_rows = len(df_raw)
missing_mortality_count = int(df_raw['dead_fish_count'].isna().sum())
evaluated_rows_count = int(df_raw['dead_fish_count'].notna().sum())

print(f"Total raw records in toxicity dataset: {total_raw_rows}")
print(f"Missing dead_fish_count records: {missing_mortality_count} ({missing_mortality_count / total_raw_rows * 100:.2f}%)")
print(f"Evaluated records with recorded mortality: {evaluated_rows_count} ({evaluated_rows_count / total_raw_rows * 100:.2f}%)")

# Filter out missing mortality records - DO NOT ZERO-FILL
df = df_raw[df_raw['dead_fish_count'].notna()].copy().reset_index(drop=True)
df['target'] = (df['dead_fish_count'] > 0).astype(int)

pos_count = int(df['target'].sum())
neg_count = int((df['target'] == 0).sum())
pos_pct = pos_count / len(df) * 100
neg_pct = neg_count / len(df) * 100
imbalance_ratio = neg_count / pos_count if pos_count > 0 else 0

print(f"\nTarget Class Distribution (N={len(df)}):")
print(f"  Negative Class (0: No Dead Fish): {neg_count} ({neg_pct:.2f}%)")
print(f"  Positive Class (1: Dead Fish > 0): {pos_count} ({pos_pct:.2f}%)")
print(f"  Class Imbalance Ratio: {imbalance_ratio:.2f} : 1")

# Class Distribution by Year
yearly_records = []
for yr in sorted(df_raw['year'].unique()):
    sub_raw = df_raw[df_raw['year'] == yr]
    sub_eval = df[df['year'] == yr]
    n_raw = len(sub_raw)
    n_miss = int(sub_raw['dead_fish_count'].isna().sum())
    n_eval = len(sub_eval)
    n_pos = int(sub_eval['target'].sum()) if n_eval > 0 else 0
    n_neg = int((sub_eval['target'] == 0).sum()) if n_eval > 0 else 0
    
    yearly_records.append({
        'year': yr,
        'total_raw_records': n_raw,
        'missing_records': n_miss,
        'evaluated_records': n_eval,
        'negative_count_0': n_neg,
        'positive_count_1': n_pos,
        'positive_prevalence_pct': round(n_pos / n_eval * 100, 2) if n_eval > 0 else 0.0
    })

df_yearly_audit = pd.DataFrame(yearly_records)
csv_yearly_audit = os.path.join(METRICS_DIR, 'class_distribution_by_year.csv')
df_yearly_audit.to_csv(csv_yearly_audit, index=False)
print(f"\nYearly Target Audit Table (Saved to {csv_yearly_audit}):")
print(df_yearly_audit.to_string(index=False))

# Distribution by Pond
pond_summary = df.groupby('pond_id').agg(
    total_visits=('target', 'count'),
    positive_events=('target', 'sum'),
    negative_events=('target', lambda s: (s == 0).sum()),
    region=('region', 'first')
).reset_index()
pond_summary['has_mortality'] = (pond_summary['positive_events'] > 0).astype(int)
pond_summary['mortality_rate_pct'] = round(pond_summary['positive_events'] / pond_summary['total_visits'] * 100, 2)

ponds_with_mort = int(pond_summary['has_mortality'].sum())
total_eval_ponds = len(pond_summary)
print(f"\nPond-Level Mortality Audit:")
print(f"  Total unique ponds evaluated: {total_eval_ponds}")
print(f"  Ponds with >= 1 mortality event: {ponds_with_mort} ({ponds_with_mort / total_eval_ponds * 100:.2f}%)")
print(f"  Ponds with 0 mortality events: {total_eval_ponds - ponds_with_mort} ({(total_eval_ponds - ponds_with_mort) / total_eval_ponds * 100:.2f}%)")

csv_pond_audit = os.path.join(METRICS_DIR, 'class_distribution_by_pond.csv')
pond_summary.to_csv(csv_pond_audit, index=False)

# =========================================================================
# STEP 2: FEATURE SELECTION & LEAKAGE PREVENTION
# =========================================================================
print("\n[Step 2] Feature Selection and Itemized Leakage Elimination...")

# Indicators for missing values
df['tds_ppt_is_missing'] = df['tds_ppt'].isna().astype(float)
df['turbidity_cm_is_missing'] = df['turbidity_cm'].isna().astype(float)

# Selected features: Physical/physicochemical water quality + contextual + missingness indicators + calculated NH3
# Note: primary_calculated_nh3_mg_l is an environmental stressor (un-ionized ammonia), available at sampling time.
features_selected = [
    'dissolved_oxygen_mg_l', 'ph', 'temp_c',
    'turbidity_cm', 'tds_ppt',
    'tds_ppt_is_missing', 'turbidity_cm_is_missing',
    'Weather', 'water_color', 'region',
    'primary_calculated_nh3_mg_l'
]

num_features = ['dissolved_oxygen_mg_l', 'ph', 'temp_c', 'turbidity_cm', 'tds_ppt', 'primary_calculated_nh3_mg_l']
ind_features = ['tds_ppt_is_missing', 'turbidity_cm_is_missing']
cat_features = ['Weather', 'water_color', 'region']

# Document all 27 columns from toxicity_analysis_v2.csv
feature_inventory_records = []
for col in df_raw.columns:
    dtype_str = str(df_raw[col].dtype)
    miss_count = int(df_raw[col].isna().sum())
    miss_pct = round(miss_count / total_raw_rows * 100, 2)
    
    if col in features_selected:
        status = "SELECTED"
        reason = "Permitted environmental water quality / contextual predictor available at prediction time."
    elif col == 'dead_fish_count':
        status = "TARGET (EXCLUDED)"
        reason = "Direct mathematical source of the classification target (target leakage)."
    elif col in ['air_gulping_count', 'tail_splashing_count', 'provisional_behavioral_distress_observed']:
        status = "EXCLUDED (CLINICAL SYMPTOM)"
        reason = "Behavioral distress symptom occurring concurrently with mortality. Excluded to avoid outcome leakage."
    elif col.startswith('provisional_') or col in ['is_wq_in_range', 'parameters_out_of_range']:
        status = "EXCLUDED (HEURISTIC LABEL)"
        reason = "Post-hoc heuristic rule label; provisional_severity_heuristic directly incorporates dead fish count."
    elif col in ['pond_id', 'datetime']:
        status = "EXCLUDED (METADATA / GROUP KEY)"
        reason = "Identifier used strictly for GroupKFold splitting and chronological ordering; barred from feature matrix."
    elif col in ['raw_ammonia_tan_nh3_n_mg_l', 'raw_ammonia_tan_nh3_mg_l', 'reported_ammonia_nh3_unverified_mg_l', 'calculated_nh3_from_tan_n_mg_l', 'calculated_nh3_from_tan_nh3_mg_l', 'nh3_calculation_source']:
        status = "EXCLUDED (REDUNDANT / INTERMEDIATE AMMONIA)"
        reason = "Redundant raw TAN or intermediate pathway; consolidated into primary_calculated_nh3_mg_l."
    else:
        status = "EXCLUDED"
        reason = "Excluded to maintain strict experimental validity."
        
    feature_inventory_records.append({
        'column_name': col,
        'data_type': dtype_str,
        'missing_count_raw': miss_count,
        'missing_pct_raw': miss_pct,
        'status': status,
        'technical_rationale': reason
    })

df_feature_inventory = pd.DataFrame(feature_inventory_records)
csv_feature_inv = os.path.join(METRICS_DIR, 'feature_inventory.csv')
df_feature_inventory.to_csv(csv_feature_inv, index=False)
print(f"Documented {len(df_feature_inventory)} columns in feature inventory (Saved to {csv_feature_inv}).")
print(f"Selected features count: {len(features_selected)} (6 continuous, 2 indicators, 3 categorical)")

# =========================================================================
# STEP 3 & 4: MODEL PIPELINES & VALIDATION PROTOCOLS
# =========================================================================
print("\n[Step 3 & 4] Constructing Model Pipelines & Executing Validations...")

def build_preprocessor():
    num_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    ind_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value=0.0))
    ])
    cat_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
        ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    return ColumnTransformer([
        ('num', num_pipe, num_features),
        ('ind', ind_pipe, ind_features),
        ('cat', cat_pipe, cat_features)
    ])

def build_models():
    dummy = DummyClassifier(strategy='prior')
    lr = LogisticRegression(class_weight='balanced', random_state=RANDOM_SEED, max_iter=1000)
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', min_samples_leaf=5, random_state=RANDOM_SEED, n_jobs=-1)
    
    return {
        'Dummy_Prior': Pipeline([('prep', build_preprocessor()), ('clf', dummy)]),
        'Logistic_Regression': Pipeline([('prep', build_preprocessor()), ('clf', lr)]),
        'Random_Forest': Pipeline([('prep', build_preprocessor()), ('clf', rf)])
    }

# -------------------------------------------------------------------------
# PROTOCOL 1: 5-FOLD GROUPKFOLD BY POND_ID
# -------------------------------------------------------------------------
print("\n--- Executing Protocol 1: 5-Fold GroupKFold by pond_id ---")
gkf = GroupKFold(n_splits=5)
ponds = df['pond_id'].values
y = df['target'].values
X = df[features_selected]

models = build_models()
oof_probs = {m_name: np.zeros(len(df)) for m_name in models}
oof_preds = {m_name: np.zeros(len(df)) for m_name in models}

fold_records = []

for fold, (train_idx, val_idx) in enumerate(gkf.split(df, groups=ponds)):
    train_ponds = set(ponds[train_idx])
    val_ponds = set(ponds[val_idx])
    overlap = train_ponds.intersection(val_ponds)
    assert len(overlap) == 0, f"Error: Pond overlap in fold {fold+1}!"
    
    y_tr, y_va = y[train_idx], y[val_idx]
    
    fold_info = {
        'fold': fold + 1,
        'train_samples': len(train_idx),
        'val_samples': len(val_idx),
        'train_positives': int(y_tr.sum()),
        'val_positives': int(y_va.sum()),
        'train_ponds': len(train_ponds),
        'val_ponds': len(val_ponds)
    }
    fold_records.append(fold_info)
    
    # Fit each model on training fold only
    for m_name, model in build_models().items():
        model.fit(df.iloc[train_idx][features_selected], y_tr)
        probs = model.predict_proba(df.iloc[val_idx][features_selected])[:, 1]
        preds = model.predict(df.iloc[val_idx][features_selected])
        oof_probs[m_name][val_idx] = probs
        oof_preds[m_name][val_idx] = preds

print("GroupKFold Distribution Summary across 5 Folds:")
print(pd.DataFrame(fold_records).to_string(index=False))

# Compute GroupKFold OOF Metrics
gkf_metric_records = []
conf_matrices = {}

for m_name in models:
    probs = oof_probs[m_name]
    preds = oof_preds[m_name]
    
    cm = confusion_matrix(y, preds)
    conf_matrices[f"GroupKFold_{m_name}"] = cm
    tn, fp, fn, tp = cm.ravel()
    
    prec = precision_score(y, preds, zero_division=0)
    rec = recall_score(y, preds, zero_division=0)
    f1 = f1_score(y, preds, zero_division=0)
    pr_auc = average_precision_score(y, probs)
    roc_auc = roc_auc_score(y, probs)
    
    gkf_metric_records.append({
        'protocol': 'GroupKFold_OOF',
        'model_name': m_name,
        'precision': round(prec, 4),
        'recall': round(rec, 4),
        'f1_score': round(f1, 4),
        'pr_auc': round(pr_auc, 4),
        'roc_auc': round(roc_auc, 4),
        'tp': int(tp),
        'fp': int(fp),
        'fn': int(fn),
        'tn': int(tn)
    })

df_gkf_metrics = pd.DataFrame(gkf_metric_records)
csv_gkf = os.path.join(METRICS_DIR, 'groupkfold_metrics.csv')
df_gkf_metrics.to_csv(csv_gkf, index=False)
print("\nGroupKFold Out-of-Fold Performance:")
print(df_gkf_metrics[['model_name', 'pr_auc', 'roc_auc', 'recall', 'precision', 'f1_score', 'tp', 'fn', 'fp']].to_string(index=False))

# -------------------------------------------------------------------------
# PROTOCOL 2: CHRONOLOGICAL VALIDATION (TRAIN 2021-2024, TEST 2025-2026)
# -------------------------------------------------------------------------
print("\n--- Executing Protocol 2: Chronological Validation ---")
cutoff = pd.to_datetime('2025-01-01 00:00:00')
train_mask = df['datetime'] < cutoff
test_mask = df['datetime'] >= cutoff

df_train = df[train_mask].copy().reset_index(drop=True)
df_test = df[test_mask].copy().reset_index(drop=True)

y_train = df_train['target'].values
y_test = df_test['target'].values

print(f"Chronological Train (2021-2024 evaluated): N={len(df_train)}, Positives={int(y_train.sum())} ({y_train.sum()/len(df_train)*100:.2f}%)")
print(f"Chronological Test (2025-2026 evaluated): N={len(df_test)}, Positives={int(y_test.sum())} ({y_test.sum()/len(df_test)*100:.2f}%)")

chrono_metric_records = []
chrono_probs = {}
chrono_preds = {}

# Fit and evaluate Chronological Models
for m_name, model in build_models().items():
    # Fit strictly on training partition
    model.fit(df_train[features_selected], y_train)
    
    # Save serialized model pipeline
    model_save_path = os.path.join(MODELS_DIR, f"{m_name.lower()}_pipeline.joblib")
    joblib.dump(model, model_save_path)
    print(f"Saved {m_name} serialized pipeline to {model_save_path}")
    
    probs = model.predict_proba(df_test[features_selected])[:, 1]
    preds = model.predict(df_test[features_selected])
    
    chrono_probs[m_name] = probs
    chrono_preds[m_name] = preds
    
    cm = confusion_matrix(y_test, preds)
    conf_matrices[f"Chronological_{m_name}"] = cm
    tn, fp, fn, tp = cm.ravel()
    
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    pr_auc = average_precision_score(y_test, probs)
    roc_auc = roc_auc_score(y_test, probs)
    
    chrono_metric_records.append({
        'protocol': 'Chronological_Test',
        'model_name': m_name,
        'precision': round(prec, 4),
        'recall': round(rec, 4),
        'f1_score': round(f1, 4),
        'pr_auc': round(pr_auc, 4),
        'roc_auc': round(roc_auc, 4),
        'tp': int(tp),
        'fp': int(fp),
        'fn': int(fn),
        'tn': int(tn)
    })

df_chrono_metrics = pd.DataFrame(chrono_metric_records)
csv_chrono = os.path.join(METRICS_DIR, 'chronological_test_metrics.csv')
df_chrono_metrics.to_csv(csv_chrono, index=False)
print("\nChronological Test Holdout Performance:")
print(df_chrono_metrics[['model_name', 'pr_auc', 'roc_auc', 'recall', 'precision', 'f1_score', 'tp', 'fn', 'fp']].to_string(index=False))

# Save all Confusion Matrices to CSV
cm_records = []
for k, cm in conf_matrices.items():
    tn, fp, fn, tp = cm.ravel()
    cm_records.append({
        'evaluation_setting': k,
        'true_negatives_tn': int(tn),
        'false_positives_fp': int(fp),
        'false_negatives_fn': int(fn),
        'true_positives_tp': int(tp)
    })
df_cm = pd.DataFrame(cm_records)
csv_cm = os.path.join(METRICS_DIR, 'confusion_matrices.csv')
df_cm.to_csv(csv_cm, index=False)
print(f"\nSaved confusion matrices to {csv_cm}")

# =========================================================================
# GENERATE DIAGNOSTIC PLOTS
# =========================================================================
print("\n[Step 5] Generating Publication-Quality Plots...")

# 1. Class Distribution by Year Plot
fig, ax1 = plt.subplots(figsize=(10, 5))
years = df_yearly_audit['year'].values
eval_recs = df_yearly_audit['evaluated_records'].values
pos_recs = df_yearly_audit['positive_count_1'].values

ax1.bar(years - 0.15, eval_recs, width=0.3, label='Total Evaluated Records', color='#1f77b4', alpha=0.85)
ax1.set_ylabel('Total Evaluated Records', fontsize=11, color='#1f77b4')
ax1.set_xlabel('Monitoring Year', fontsize=11)
ax1.set_title('Mortality Audit: Evaluated Records & Positive Cases by Year', fontsize=12, fontweight='bold')
ax1.grid(True, linestyle=':', alpha=0.6)

ax2 = ax1.twinx()
ax2.bar(years + 0.15, pos_recs, width=0.3, label='Positive Cases (Dead Fish > 0)', color='#d62728', alpha=0.85)
ax2.set_ylabel('Positive Mortality Cases (Count)', fontsize=11, color='#d62728')

# Value annotations
for y_val, e_val, p_val in zip(years, eval_recs, pos_recs):
    if e_val > 0:
        ax1.text(y_val - 0.15, e_val + 30, str(e_val), ha='center', fontsize=9)
        ax2.text(y_val + 0.15, p_val + 0.8, str(p_val), ha='center', fontsize=9, fontweight='bold', color='#d62728')

plt.tight_layout()
p1_path = os.path.join(PLOTS_DIR, 'class_distribution_by_year.png')
plt.savefig(p1_path, dpi=300)
plt.close()
print(f"Saved Plot 1: {p1_path}")

# 2. Precision-Recall Curves
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

colors = {'Dummy_Prior': '#7f7f7f', 'Logistic_Regression': '#1f77b4', 'Random_Forest': '#2ca02c'}

# Panel 1: GroupKFold PR Curves
base_pr_gkf = y.sum() / len(y)
ax1.axhline(base_pr_gkf, color='red', linestyle='--', label=f'No-Skill Baseline ({base_pr_gkf*100:.2f}%)')
for m_name in ['Logistic_Regression', 'Random_Forest', 'Dummy_Prior']:
    p, r, _ = precision_recall_curve(y, oof_probs[m_name])
    pr_auc = average_precision_score(y, oof_probs[m_name])
    ax1.plot(r, p, label=f'{m_name} (PR-AUC = {pr_auc:.4f})', color=colors[m_name], lw=2)

ax1.set_title('Precision-Recall Curve: 5-Fold GroupKFold OOF\n(Unseen Ponds)', fontsize=12, fontweight='bold')
ax1.set_xlabel('Recall (Sensitivity)', fontsize=11)
ax1.set_ylabel('Precision (Positive Predictive Value)', fontsize=11)
ax1.set_ylim(-0.02, 0.40)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='upper right', fontsize=10)

# Panel 2: Chronological Test PR Curves
base_pr_chr = y_test.sum() / len(y_test)
ax2.axhline(base_pr_chr, color='red', linestyle='--', label=f'No-Skill Baseline ({base_pr_chr*100:.2f}%)')
for m_name in ['Logistic_Regression', 'Random_Forest', 'Dummy_Prior']:
    p, r, _ = precision_recall_curve(y_test, chrono_probs[m_name])
    pr_auc = average_precision_score(y_test, chrono_probs[m_name])
    ax2.plot(r, p, label=f'{m_name} (PR-AUC = {pr_auc:.4f})', color=colors[m_name], lw=2)

ax2.set_title('Precision-Recall Curve: Chronological Holdout (2025-2026)\n(Temporal Generalization)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Recall (Sensitivity)', fontsize=11)
ax2.set_ylabel('Precision (Positive Predictive Value)', fontsize=11)
ax2.set_ylim(-0.02, 0.40)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='upper right', fontsize=10)

plt.tight_layout()
p2_path = os.path.join(PLOTS_DIR, 'precision_recall_curves.png')
plt.savefig(p2_path, dpi=300)
plt.close()
print(f"Saved Plot 2: {p2_path}")

# 3. ROC Curves
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

ax1.plot([0, 1], [0, 1], 'k--', label='Random Chance (AUC = 0.5000)')
for m_name in ['Logistic_Regression', 'Random_Forest', 'Dummy_Prior']:
    fpr, tpr, _ = roc_curve(y, oof_probs[m_name])
    roc_auc = roc_auc_score(y, oof_probs[m_name])
    ax1.plot(fpr, tpr, label=f'{m_name} (ROC-AUC = {roc_auc:.4f})', color=colors[m_name], lw=2)

ax1.set_title('ROC Curves: 5-Fold GroupKFold OOF\n(Unseen Ponds)', fontsize=12, fontweight='bold')
ax1.set_xlabel('False Positive Rate (1 - Specificity)', fontsize=11)
ax1.set_ylabel('True Positive Rate (Recall)', fontsize=11)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='lower right', fontsize=10)

ax2.plot([0, 1], [0, 1], 'k--', label='Random Chance (AUC = 0.5000)')
for m_name in ['Logistic_Regression', 'Random_Forest', 'Dummy_Prior']:
    fpr, tpr, _ = roc_curve(y_test, chrono_probs[m_name])
    roc_auc = roc_auc_score(y_test, chrono_probs[m_name])
    ax2.plot(fpr, tpr, label=f'{m_name} (ROC-AUC = {roc_auc:.4f})', color=colors[m_name], lw=2)

ax2.set_title('ROC Curves: Chronological Holdout (2025-2026)\n(Temporal Generalization)', fontsize=12, fontweight='bold')
ax2.set_xlabel('False Positive Rate (1 - Specificity)', fontsize=11)
ax2.set_ylabel('True Positive Rate (Recall)', fontsize=11)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='lower right', fontsize=10)

plt.tight_layout()
p3_path = os.path.join(PLOTS_DIR, 'roc_curves.png')
plt.savefig(p3_path, dpi=300)
plt.close()
print(f"Saved Plot 3: {p3_path}")

# 4. Confusion Matrices Plot
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

def plot_cm(ax, cm, title):
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.set_title(title, fontsize=11, fontweight='bold')
    tick_marks = np.arange(2)
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(['No Mortality (0)', 'Mortality (1)'])
    ax.set_yticklabels(['No Mortality (0)', 'Mortality (1)'])
    
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                    fontsize=12, fontweight='bold')
    ax.set_ylabel('True Label', fontsize=10)
    ax.set_xlabel('Predicted Label', fontsize=10)

# Top row: GroupKFold
plot_cm(axes[0, 0], conf_matrices['GroupKFold_Dummy_Prior'], 'GroupKFold: Dummy Prior')
plot_cm(axes[0, 1], conf_matrices['GroupKFold_Logistic_Regression'], 'GroupKFold: Logistic Regression')
plot_cm(axes[0, 2], conf_matrices['GroupKFold_Random_Forest'], 'GroupKFold: Random Forest')

# Bottom row: Chronological Test
plot_cm(axes[1, 0], conf_matrices['Chronological_Dummy_Prior'], 'Chrono Test: Dummy Prior')
plot_cm(axes[1, 1], conf_matrices['Chronological_Logistic_Regression'], 'Chrono Test: Logistic Regression')
plot_cm(axes[1, 2], conf_matrices['Chronological_Random_Forest'], 'Chrono Test: Random Forest')

plt.tight_layout()
p4_path = os.path.join(PLOTS_DIR, 'confusion_matrices.png')
plt.savefig(p4_path, dpi=300)
plt.close()
print(f"Saved Plot 4: {p4_path}")

print("\n" + "=" * 80)
print("EXPERIMENT 2 TRAINING & EVALUATION COMPLETED SUCCESSFULLY!")
print("=" * 80)

