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

BASE_DIR = 'experiment_3_next_visit_risk_v1'
METRICS_DIR = os.path.join(BASE_DIR, 'metrics')
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

os.makedirs(METRICS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

print("=" * 80)
print("EXPERIMENT 3: NEXT-VISIT AMMONIA TOXICITY RISK PREDICTION")
print("Task: Forecast provisional ammonia-risk status at next routine farm visit (t+1)")
print("Source Dataset: processed_data_v2/toxicity_analysis_v2.csv")
print("=" * 80)

# =========================================================================
# STEP 1: CONSTRUCT VALID TEMPORAL PAIRS (3 to 45 DAYS GAP)
# =========================================================================
print("\n[Step 1] Constructing Temporal Observation Pairs (3 <= Delta t <= 45 days)...")
DATA_PATH = 'processed_data_v2/toxicity_analysis_v2.csv'
df_raw = pd.read_csv(DATA_PATH)
df_raw['datetime'] = pd.to_datetime(df_raw['datetime'])
df_raw = df_raw.sort_values(['pond_id', 'datetime']).reset_index(drop=True)

pairs = []
total_evaluated_raw = len(df_raw)

for pond, group in df_raw.groupby('pond_id'):
    group = group.sort_values('datetime').reset_index(drop=True)
    for i in range(len(group) - 1):
        curr = group.iloc[i]
        nxt = group.iloc[i+1]
        
        # Calculate interval in fractional days
        gap_days = (nxt['datetime'] - curr['datetime']).total_seconds() / (24 * 3600)
        
        # Enforce temporal pairing constraint: 3 to 45 days
        if 3.0 <= gap_days <= 45.0:
            # Current visit features at t
            pairs.append({
                'pond_id': pond,
                'curr_datetime': curr['datetime'],
                'next_datetime': nxt['datetime'],
                'gap_days': gap_days,
                'curr_risk': int(curr['provisional_ammonia_risk_heuristic']),
                'next_risk': int(nxt['provisional_ammonia_risk_heuristic']),
                'curr_nh3': float(curr['primary_calculated_nh3_mg_l']),
                'next_nh3': float(nxt['primary_calculated_nh3_mg_l']),
                'curr_do': float(curr['dissolved_oxygen_mg_l']),
                'curr_ph': float(curr['ph']),
                'curr_temp': float(curr['temp_c']),
                'curr_turbidity': curr['turbidity_cm'],
                'curr_tds': curr['tds_ppt'],
                'curr_weather': str(curr['Weather']),
                'curr_color': str(curr['water_color']),
                'region': str(curr['region']),
                'tds_is_missing': float(np.isnan(curr['tds_ppt'])),
                'turbidity_is_missing': float(np.isnan(curr['turbidity_cm']))
            })

df_pairs = pd.DataFrame(pairs)
total_pairs = len(df_pairs)
unique_ponds = df_pairs['pond_id'].nunique()
pos_target_count = int(df_pairs['next_risk'].sum())
neg_target_count = int((df_pairs['next_risk'] == 0).sum())

print(f"Total raw observations in dataset: {total_evaluated_raw}")
print(f"Total valid temporal pairs constructed: {total_pairs}")
print(f"Unique ponds represented: {unique_ponds} (out of {df_raw['pond_id'].nunique()} total ponds)")
print(f"Target distribution at visit t+1 (next_risk):")
print(f"  Safe (0, NH3 < 0.05 mg/L): {neg_target_count} ({neg_target_count / total_pairs * 100:.2f}%)")
print(f"  High Risk (1, NH3 >= 0.05 mg/L): {pos_target_count} ({pos_target_count / total_pairs * 100:.2f}%)")
print(f"Class imbalance ratio: {neg_target_count / pos_target_count:.2f} : 1")

# State Transition Matrix
ct_trans = pd.crosstab(df_pairs['curr_risk'], df_pairs['next_risk'])
ct_trans.index = ['Current_Safe (0)', 'Current_Risk (1)']
ct_trans.columns = ['Next_Safe (0)', 'Next_Risk (1)']
ct_trans_pct = round(ct_trans / total_pairs * 100, 2)

print("\nState Transition Matrix (Counts):")
print(ct_trans)
print("\nState Transition Matrix (Percentages):")
print(ct_trans_pct)

# Save pair construction summary
pair_summary_records = [{
    'total_raw_rows': total_evaluated_raw,
    'valid_pairs_count': total_pairs,
    'unique_ponds_in_pairs': unique_ponds,
    'min_gap_days': round(df_pairs['gap_days'].min(), 2),
    'mean_gap_days': round(df_pairs['gap_days'].mean(), 2),
    'median_gap_days': round(df_pairs['gap_days'].median(), 2),
    'max_gap_days': round(df_pairs['gap_days'].max(), 2),
    'next_risk_positives': pos_target_count,
    'next_risk_negatives': neg_target_count,
    'positive_prevalence_pct': round(pos_target_count / total_pairs * 100, 2),
    'stable_safe_0_to_0': int(ct_trans.loc['Current_Safe (0)', 'Next_Safe (0)']),
    'new_onset_spikes_0_to_1': int(ct_trans.loc['Current_Safe (0)', 'Next_Risk (1)']),
    'recovery_events_1_to_0': int(ct_trans.loc['Current_Risk (1)', 'Next_Safe (0)']),
    'persistent_risk_1_to_1': int(ct_trans.loc['Current_Risk (1)', 'Next_Risk (1)'])
}]
df_pair_summary = pd.DataFrame(pair_summary_records)
csv_pair_summary = os.path.join(METRICS_DIR, 'temporal_pair_construction_summary.csv')
df_pair_summary.to_csv(csv_pair_summary, index=False)

ct_trans.to_csv(os.path.join(METRICS_DIR, 'state_transition_matrix.csv'))

# Gap Days Distribution Stats
gap_stats = df_pairs['gap_days'].describe().reset_index()
gap_stats.columns = ['statistic', 'value_days']
gap_stats.to_csv(os.path.join(METRICS_DIR, 'gap_days_distribution.csv'), index=False)

# =========================================================================
# STEP 2: FEATURE SELECTION & LEAKAGE PREVENTION
# =========================================================================
print("\n[Step 2] Feature Selection and Anti-Leakage Audit...")

# Selected features strictly at visit t + scheduled revisit interval
features_selected = [
    'gap_days',
    'curr_do', 'curr_ph', 'curr_temp',
    'curr_turbidity', 'curr_tds',
    'tds_is_missing', 'turbidity_is_missing',
    'curr_weather', 'curr_color', 'region',
    'curr_nh3'
]

num_features = ['gap_days', 'curr_do', 'curr_ph', 'curr_temp', 'curr_turbidity', 'curr_tds', 'curr_nh3']
ind_features = ['tds_is_missing', 'turbidity_is_missing']
cat_features = ['curr_weather', 'curr_color', 'region']

# Document feature inventory
inv_records = [
    {'feature_name': 'gap_days', 'source_time': 'Known at visit t', 'type': 'Continuous (days)', 'status': 'SELECTED', 'rationale': 'Scheduled revisit interval (3-45 days) modulating biogeochemical decay and accumulation time.'},
    {'feature_name': 'curr_do', 'source_time': 'Visit t', 'type': 'Continuous (mg/L)', 'status': 'SELECTED', 'rationale': 'Current dissolved oxygen reflecting photosynthetic stability and microbial oxygen debt.'},
    {'feature_name': 'curr_ph', 'source_time': 'Visit t', 'type': 'Continuous (pH scale)', 'status': 'SELECTED', 'rationale': 'Current pH driving carbonate buffer and chemical un-ionized ammonia fraction.'},
    {'feature_name': 'curr_temp', 'source_time': 'Visit t', 'type': 'Continuous (C)', 'status': 'SELECTED', 'rationale': 'Current water temperature driving biological metabolic and nitrification rates.'},
    {'feature_name': 'curr_turbidity', 'source_time': 'Visit t', 'type': 'Continuous (cm)', 'status': 'SELECTED', 'rationale': 'Current Secchi depth clarity reflecting phytoplankton bloom density.'},
    {'feature_name': 'curr_tds', 'source_time': 'Visit t', 'type': 'Continuous (ppt)', 'status': 'SELECTED', 'rationale': 'Current total dissolved solids reflecting salinity and ionic strength.'},
    {'feature_name': 'tds_is_missing', 'source_time': 'Visit t', 'type': 'Binary indicator', 'status': 'SELECTED', 'rationale': 'Missingness flag for TDS probe testing.'},
    {'feature_name': 'turbidity_is_missing', 'source_time': 'Visit t', 'type': 'Binary indicator', 'status': 'SELECTED', 'rationale': 'Missingness flag for Secchi clarity testing.'},
    {'feature_name': 'curr_weather', 'source_time': 'Visit t', 'type': 'Categorical', 'status': 'SELECTED', 'rationale': 'Current meteorological condition (Sunny, Cloudy, Rainy, Foggy).'},
    {'feature_name': 'curr_color', 'source_time': 'Visit t', 'type': 'Categorical', 'status': 'SELECTED', 'rationale': 'Current predominant algal community visual appearance.'},
    {'feature_name': 'region', 'source_time': 'Metadata', 'type': 'Categorical', 'status': 'SELECTED', 'rationale': 'Farming district baseline (Eluru vs Nellore).'},
    {'feature_name': 'curr_nh3', 'source_time': 'Visit t', 'type': 'Continuous (mg/L)', 'status': 'SELECTED', 'rationale': 'Current calculated un-ionized ammonia level serving as continuous initial condition.'},
    {'feature_name': 'curr_risk', 'source_time': 'Visit t', 'type': 'Binary', 'status': 'EXCLUDED FROM ML (USED IN PERSISTENCE)', 'rationale': 'Current binary risk label barred from ML feature matrix to prevent circularity; used strictly as the Persistence Baseline input.'},
    {'feature_name': 'next_risk', 'source_time': 'Visit t+1', 'type': 'Binary', 'status': 'TARGET (EXCLUDED FROM FEATURES)', 'rationale': 'Future risk status to be predicted (target variable).'},
    {'feature_name': 'next_nh3', 'source_time': 'Visit t+1', 'type': 'Continuous', 'status': 'EXCLUDED (FUTURE MEASUREMENT)', 'rationale': 'Future un-ionized ammonia reading at t+1; direct target leakage.'},
    {'feature_name': 'next_datetime', 'source_time': 'Visit t+1', 'type': 'Timestamp', 'status': 'EXCLUDED (FUTURE METADATA)', 'rationale': 'Next sampling timestamp; barred from features.'},
    {'feature_name': 'curr_datetime', 'source_time': 'Visit t', 'type': 'Timestamp', 'status': 'EXCLUDED (CHRONO SPLIT ONLY)', 'rationale': 'Sampling timestamp used strictly for chronological train/test partitioning.'},
    {'feature_name': 'pond_id', 'source_time': 'Metadata', 'type': 'Identifier', 'status': 'EXCLUDED (GROUP KEY ONLY)', 'rationale': 'Pond ID used strictly for GroupKFold cross-validation.'}
]
df_inv = pd.DataFrame(inv_records)
csv_inv = os.path.join(METRICS_DIR, 'feature_inventory.csv')
df_inv.to_csv(csv_inv, index=False)
print(f"Saved feature inventory with {len(df_inv)} variables to {csv_inv}")

# =========================================================================
# STEP 3 & 4: VALIDATION PROTOCOLS, BASELINES & MODEL TRAINING
# =========================================================================
print("\n[Step 3 & 4] Constructing Pipelines & Executing Validations...")

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

# Persistence Baseline Evaluator Function
def evaluate_persistence(curr_labels, next_labels):
    cm = confusion_matrix(next_labels, curr_labels)
    tn, fp, fn, tp = cm.ravel()
    rec = recall_score(next_labels, curr_labels, zero_division=0)
    prec = precision_score(next_labels, curr_labels, zero_division=0)
    f1 = f1_score(next_labels, curr_labels, zero_division=0)
    # New onset spike recall (curr = 0 and next = 1)
    new_spike_mask = (curr_labels == 0)
    new_spikes_total = int(((curr_labels == 0) & (next_labels == 1)).sum())
    new_spikes_detected = int((curr_labels[new_spike_mask & (next_labels == 1)] == 1).sum())
    
    return {
        'cm': cm, 'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp),
        'recall': round(rec, 4), 'precision': round(prec, 4), 'f1': round(f1, 4),
        'new_spikes_total': new_spikes_total, 'new_spikes_detected': new_spikes_detected
    }

# -------------------------------------------------------------------------
# PROTOCOL 1: 5-FOLD GROUPKFOLD BY POND_ID
# -------------------------------------------------------------------------
print("\n--- Executing Protocol 1: 5-Fold GroupKFold by pond_id ---")
gkf = GroupKFold(n_splits=5)
ponds = df_pairs['pond_id'].values
y_all = df_pairs['next_risk'].values
curr_risk_all = df_pairs['curr_risk'].values

models = build_models()
oof_probs = {m: np.zeros(total_pairs) for m in models}
oof_preds = {m: np.zeros(total_pairs) for m in models}

fold_records = []
for fold, (train_idx, val_idx) in enumerate(gkf.split(df_pairs, groups=ponds)):
    train_ponds = set(ponds[train_idx])
    val_ponds = set(ponds[val_idx])
    assert len(train_ponds.intersection(val_ponds)) == 0, f"Error: Pond overlap in fold {fold+1}!"
    
    y_tr, y_va = y_all[train_idx], y_all[val_idx]
    
    fold_records.append({
        'fold': fold + 1,
        'train_samples': len(train_idx),
        'val_samples': len(val_idx),
        'train_positives': int(y_tr.sum()),
        'val_positives': int(y_va.sum()),
        'train_ponds': len(train_ponds),
        'val_ponds': len(val_ponds),
        'val_prevalence_pct': round(y_va.sum() / len(y_va) * 100, 2)
    })
    
    for m_name, model in build_models().items():
        model.fit(df_pairs.iloc[train_idx][features_selected], y_tr)
        oof_probs[m_name][val_idx] = model.predict_proba(df_pairs.iloc[val_idx][features_selected])[:, 1]
        oof_preds[m_name][val_idx] = model.predict(df_pairs.iloc[val_idx][features_selected])

print("GroupKFold Partitioning Summary across 5 Folds:")
print(pd.DataFrame(fold_records).to_string(index=False))

# Evaluate GroupKFold OOF Metrics
conf_matrices = {}
gkf_metric_records = []
no_skill_gkf = round(y_all.sum() / total_pairs, 4)

# 1. Persistence Baseline
res_pers_gkf = evaluate_persistence(curr_risk_all, y_all)
conf_matrices['GroupKFold_Persistence'] = res_pers_gkf['cm']
gkf_metric_records.append({
    'protocol': 'GroupKFold_OOF',
    'model_name': 'Persistence_Baseline',
    'pr_auc': np.nan,
    'roc_auc': np.nan,
    'recall': res_pers_gkf['recall'],
    'precision': res_pers_gkf['precision'],
    'f1_score': res_pers_gkf['f1'],
    'tp': res_pers_gkf['tp'], 'fn': res_pers_gkf['fn'], 'fp': res_pers_gkf['fp'], 'tn': res_pers_gkf['tn'],
    'new_spikes_detected': res_pers_gkf['new_spikes_detected'],
    'new_spikes_total': res_pers_gkf['new_spikes_total'],
    'no_skill_pr_baseline': no_skill_gkf
})

# 2. ML Models
for m_name in models:
    probs = oof_probs[m_name]
    preds = oof_preds[m_name]
    cm = confusion_matrix(y_all, preds)
    conf_matrices[f'GroupKFold_{m_name}'] = cm
    tn, fp, fn, tp = cm.ravel()
    
    # Calculate new spike detection
    new_spike_mask = (curr_risk_all == 0) & (y_all == 1)
    new_spikes_det = int((preds[new_spike_mask] == 1).sum())
    
    gkf_metric_records.append({
        'protocol': 'GroupKFold_OOF',
        'model_name': m_name,
        'pr_auc': round(average_precision_score(y_all, probs), 4),
        'roc_auc': round(roc_auc_score(y_all, probs), 4),
        'recall': round(recall_score(y_all, preds, zero_division=0), 4),
        'precision': round(precision_score(y_all, preds, zero_division=0), 4),
        'f1_score': round(f1_score(y_all, preds, zero_division=0), 4),
        'tp': int(tp), 'fn': int(fn), 'fp': int(fp), 'tn': int(tn),
        'new_spikes_detected': new_spikes_det,
        'new_spikes_total': int(new_spike_mask.sum()),
        'no_skill_pr_baseline': no_skill_gkf
    })

df_gkf_metrics = pd.DataFrame(gkf_metric_records)
csv_gkf = os.path.join(METRICS_DIR, 'groupkfold_metrics.csv')
df_gkf_metrics.to_csv(csv_gkf, index=False)
print("\nGroupKFold Out-of-Fold Performance:")
print(df_gkf_metrics[['model_name', 'pr_auc', 'roc_auc', 'recall', 'precision', 'f1_score', 'tp', 'fn', 'fp', 'new_spikes_detected']].to_string(index=False))

# -------------------------------------------------------------------------
# PROTOCOL 2: STRICT CHRONOLOGICAL VALIDATION
# -------------------------------------------------------------------------
print("\n--- Executing Protocol 2: Strict Chronological Validation ---")
cutoff = pd.to_datetime('2025-01-01 00:00:00')

# Partition definitions ensuring no temporal crossing:
# Train: both curr_datetime and next_datetime < 2025-01-01
# Cross-cutoff: curr_datetime < 2025-01-01 and next_datetime >= 2025-01-01 (EXCLUDED from train to prevent future outcome leakage)
# Test: curr_datetime >= 2025-01-01
train_mask = (df_pairs['curr_datetime'] < cutoff) & (df_pairs['next_datetime'] < cutoff)
cross_mask = (df_pairs['curr_datetime'] < cutoff) & (df_pairs['next_datetime'] >= cutoff)
test_mask = df_pairs['curr_datetime'] >= cutoff

df_train = df_pairs[train_mask].copy().reset_index(drop=True)
df_cross = df_pairs[cross_mask].copy().reset_index(drop=True)
df_test = df_pairs[test_mask].copy().reset_index(drop=True)

y_train = df_train['next_risk'].values
y_test = df_test['next_risk'].values
curr_risk_test = df_test['curr_risk'].values

print(f"Chronological Cutoff Date: {cutoff}")
print(f"Training Pairs (both visits < 2025-01-01): N={len(df_train)}, Positives={int(y_train.sum())} ({y_train.sum()/len(df_train)*100:.2f}%)")
print(f"Cross-Cutoff Pairs (straddling 2025-01-01, EXCLUDED): N={len(df_cross)}")
print(f"Test Pairs (current visit >= 2025-01-01): N={len(df_test)}, Positives={int(y_test.sum())} ({y_test.sum()/len(df_test)*100:.2f}%)")

chrono_metric_records = []
chrono_probs = {}
chrono_preds = {}
no_skill_chrono = round(y_test.sum() / len(y_test), 4)

# 1. Persistence Baseline on Test
res_pers_test = evaluate_persistence(curr_risk_test, y_test)
conf_matrices['Chronological_Persistence'] = res_pers_test['cm']
chrono_metric_records.append({
    'protocol': 'Chronological_Test',
    'model_name': 'Persistence_Baseline',
    'pr_auc': np.nan,
    'roc_auc': np.nan,
    'recall': res_pers_test['recall'],
    'precision': res_pers_test['precision'],
    'f1_score': res_pers_test['f1'],
    'tp': res_pers_test['tp'], 'fn': res_pers_test['fn'], 'fp': res_pers_test['fp'], 'tn': res_pers_test['tn'],
    'new_spikes_detected': res_pers_test['new_spikes_detected'],
    'new_spikes_total': res_pers_test['new_spikes_total'],
    'no_skill_pr_baseline': no_skill_chrono
})

# 2. Fit ML models strictly on training partition
for m_name, model in build_models().items():
    model.fit(df_train[features_selected], y_train)
    
    # Save serialized pipeline
    model_path = os.path.join(MODELS_DIR, f"{m_name.lower()}_pipeline.joblib")
    joblib.dump(model, model_path)
    print(f"Saved serialized model pipeline to {model_path}")
    
    probs = model.predict_proba(df_test[features_selected])[:, 1]
    preds = model.predict(df_test[features_selected])
    
    chrono_probs[m_name] = probs
    chrono_preds[m_name] = preds
    
    cm = confusion_matrix(y_test, preds)
    conf_matrices[f'Chronological_{m_name}'] = cm
    tn, fp, fn, tp = cm.ravel()
    
    new_spike_mask = (curr_risk_test == 0) & (y_test == 1)
    new_spikes_det = int((preds[new_spike_mask] == 1).sum())
    
    chrono_metric_records.append({
        'protocol': 'Chronological_Test',
        'model_name': m_name,
        'pr_auc': round(average_precision_score(y_test, probs), 4),
        'roc_auc': round(roc_auc_score(y_test, probs), 4),
        'recall': round(recall_score(y_test, preds, zero_division=0), 4),
        'precision': round(precision_score(y_test, preds, zero_division=0), 4),
        'f1_score': round(f1_score(y_test, preds, zero_division=0), 4),
        'tp': int(tp), 'fn': int(fn), 'fp': int(fp), 'tn': int(tn),
        'new_spikes_detected': new_spikes_det,
        'new_spikes_total': int(new_spike_mask.sum()),
        'no_skill_pr_baseline': no_skill_chrono
    })

df_chrono_metrics = pd.DataFrame(chrono_metric_records)
csv_chrono = os.path.join(METRICS_DIR, 'chronological_test_metrics.csv')
df_chrono_metrics.to_csv(csv_chrono, index=False)
print("\nChronological Test Holdout Performance:")
print(df_chrono_metrics[['model_name', 'pr_auc', 'roc_auc', 'recall', 'precision', 'f1_score', 'tp', 'fn', 'fp', 'new_spikes_detected']].to_string(index=False))

# Save all Confusion Matrices
cm_records = []
for k, cm in conf_matrices.items():
    tn, fp, fn, tp = cm.ravel()
    cm_records.append({
        'setting': k,
        'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)
    })
pd.DataFrame(cm_records).to_csv(os.path.join(METRICS_DIR, 'confusion_matrices.csv'), index=False)

# Extract and Save Random Forest Feature Importances
rf_chrono = joblib.load(os.path.join(MODELS_DIR, 'random_forest_pipeline.joblib'))
prep_rf = rf_chrono.named_steps['prep']
clf_rf = rf_chrono.named_steps['clf']
cat_names = list(prep_rf.named_transformers_['cat'].named_steps['ohe'].get_feature_names_out(cat_features))
all_feat_names = num_features + ind_features + cat_names
imp_vals = clf_rf.feature_importances_

df_imp = pd.DataFrame({'feature': all_feat_names, 'importance': imp_vals}).sort_values('importance', ascending=False)
csv_imp = os.path.join(METRICS_DIR, 'feature_importances.csv')
df_imp.to_csv(csv_imp, index=False)
print(f"\nTop 10 Feature Importances (Saved to {csv_imp}):")
print(df_imp.head(10).to_string(index=False))

# =========================================================================
# STEP 5: GENERATE DIAGNOSTIC PLOTS
# =========================================================================
print("\n[Step 5] Generating Publication-Quality Plots...")

# 1. Temporal Gap Distribution Plot
fig, ax = plt.subplots(figsize=(9, 5))
ax.hist(df_pairs['gap_days'], bins=42, color='#1f77b4', edgecolor='black', alpha=0.8)
ax.axvline(df_pairs['gap_days'].median(), color='red', linestyle='--', lw=2, label=f"Median Gap: {df_pairs['gap_days'].median():.1f} days")
ax.axvline(df_pairs['gap_days'].mean(), color='orange', linestyle=':', lw=2, label=f"Mean Gap: {df_pairs['gap_days'].mean():.1f} days")
ax.set_title('Distribution of Revisit Intervals Between Consecutive Pond Observations\n(N=4,900 pairs, 3 to 45 days)', fontsize=12, fontweight='bold')
ax.set_xlabel('Sampling Interval (Days)', fontsize=11)
ax.set_ylabel('Number of Observation Pairs', fontsize=11)
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(fontsize=10)
plt.tight_layout()
p1_path = os.path.join(PLOTS_DIR, 'temporal_pair_gap_distribution.png')
plt.savefig(p1_path, dpi=300)
plt.close()
print(f"Saved Plot 1: {p1_path}")

# 2. State Transition Breakdown Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
trans_labels = ['Safe -> Safe\n(Stable)', 'Safe -> Risk\n(New Spike)', 'Risk -> Safe\n(Recovery)', 'Risk -> Risk\n(Persistent)']
trans_counts = [
    int(ct_trans.loc['Current_Safe (0)', 'Next_Safe (0)']),
    int(ct_trans.loc['Current_Safe (0)', 'Next_Risk (1)']),
    int(ct_trans.loc['Current_Risk (1)', 'Next_Safe (0)']),
    int(ct_trans.loc['Current_Risk (1)', 'Next_Risk (1)'])
]
colors = ['#2ca02c', '#d62728', '#1f77b4', '#ff7f0e']

bars = ax1.bar(trans_labels, trans_counts, color=colors, edgecolor='black', alpha=0.85, width=0.55)
ax1.set_title('Next-Visit Ammonia Risk State Transitions (Total N=4,900)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Pair Count', fontsize=11)
ax1.grid(True, linestyle=':', alpha=0.6)
for bar in bars:
    yval = bar.get_height()
    pct = yval / total_pairs * 100
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 50, f"{yval}\n({pct:.1f}%)", ha='center', va='bottom', fontsize=9, fontweight='bold')

# Panel 2: Persistence Baseline Failure on New Spikes
categories = ['All Positive Events (N=314)', 'New Onset Spikes (N=204)']
pers_detected = [res_pers_gkf['tp'], res_pers_gkf['new_spikes_detected']]
pers_missed = [res_pers_gkf['fn'], res_pers_gkf['new_spikes_total'] - res_pers_gkf['new_spikes_detected']]

x = np.arange(len(categories))
w = 0.35
ax2.bar(x - w/2, pers_detected, width=w, label='Detected by Persistence', color='#2ca02c', alpha=0.85, edgecolor='black')
ax2.bar(x + w/2, pers_missed, width=w, label='Missed by Persistence (Blind)', color='#d62728', alpha=0.85, edgecolor='black')
ax2.set_xticks(x)
ax2.set_xticklabels(categories, fontsize=10, fontweight='bold')
ax2.set_title('Persistence Baseline: Complete Blindness to New Risk Spikes', fontsize=12, fontweight='bold')
ax2.set_ylabel('Event Count', fontsize=11)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(fontsize=10)
for i in range(len(categories)):
    ax2.text(x[i] - w/2, pers_detected[i] + 5, str(pers_detected[i]), ha='center', fontweight='bold')
    ax2.text(x[i] + w/2, pers_missed[i] + 5, str(pers_missed[i]), ha='center', fontweight='bold')

plt.tight_layout()
p2_path = os.path.join(PLOTS_DIR, 'state_transitions.png')
plt.savefig(p2_path, dpi=300)
plt.close()
print(f"Saved Plot 2: {p2_path}")

# 3. Precision-Recall Curves
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
plot_colors = {'Dummy_Prior': '#7f7f7f', 'Logistic_Regression': '#1f77b4', 'Random_Forest': '#2ca02c'}

# Panel 1: GroupKFold PR Curves
ax1.axhline(no_skill_gkf, color='red', linestyle='--', label=f'No-Skill Baseline ({no_skill_gkf*100:.2f}%)')
# Plot persistence point
ax1.scatter(res_pers_gkf['recall'], res_pers_gkf['precision'], color='#ff7f0e', s=90, zorder=5, marker='D',
            label=f"Persistence Baseline (R={res_pers_gkf['recall']:.2f}, P={res_pers_gkf['precision']:.2f})")

for m_name in ['Random_Forest', 'Logistic_Regression', 'Dummy_Prior']:
    p, r, _ = precision_recall_curve(y_all, oof_probs[m_name])
    ap = average_precision_score(y_all, oof_probs[m_name])
    ax1.plot(r, p, label=f"{m_name} (PR-AUC = {ap:.4f})", color=plot_colors[m_name], lw=2)

ax1.set_title('Precision-Recall Curves: 5-Fold GroupKFold OOF\n(Spatial Generalization Across Unseen Ponds)', fontsize=12, fontweight='bold')
ax1.set_xlabel('Recall (Sensitivity)', fontsize=11)
ax1.set_ylabel('Precision (Positive Predictive Value)', fontsize=11)
ax1.set_ylim(-0.02, 0.65)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='upper right', fontsize=9)

# Panel 2: Chronological Test PR Curves
ax2.axhline(no_skill_chrono, color='red', linestyle='--', label=f'No-Skill Baseline ({no_skill_chrono*100:.2f}%)')
ax2.scatter(res_pers_test['recall'], res_pers_test['precision'], color='#ff7f0e', s=90, zorder=5, marker='D',
            label=f"Persistence Baseline (R={res_pers_test['recall']:.2f}, P={res_pers_test['precision']:.2f})")

for m_name in ['Random_Forest', 'Logistic_Regression', 'Dummy_Prior']:
    p, r, _ = precision_recall_curve(y_test, chrono_probs[m_name])
    ap = average_precision_score(y_test, chrono_probs[m_name])
    ax2.plot(r, p, label=f"{m_name} (PR-AUC = {ap:.4f})", color=plot_colors[m_name], lw=2)

ax2.set_title('Precision-Recall Curves: Chronological Holdout (2025-2026)\n(Temporal Generalization Across Later Dates)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Recall (Sensitivity)', fontsize=11)
ax2.set_ylabel('Precision (Positive Predictive Value)', fontsize=11)
ax2.set_ylim(-0.02, 0.65)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='upper right', fontsize=9)

plt.tight_layout()
p3_path = os.path.join(PLOTS_DIR, 'precision_recall_curves.png')
plt.savefig(p3_path, dpi=300)
plt.close()
print(f"Saved Plot 3: {p3_path}")

# 4. ROC Curves
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

ax1.plot([0, 1], [0, 1], 'k--', label='Random Chance (AUC = 0.5000)')
for m_name in ['Random_Forest', 'Logistic_Regression', 'Dummy_Prior']:
    fpr, tpr, _ = roc_curve(y_all, oof_probs[m_name])
    ra = roc_auc_score(y_all, oof_probs[m_name])
    ax1.plot(fpr, tpr, label=f"{m_name} (ROC-AUC = {ra:.4f})", color=plot_colors[m_name], lw=2)

ax1.set_title('ROC Curves: 5-Fold GroupKFold OOF\n(Spatial Generalization Across Unseen Ponds)', fontsize=12, fontweight='bold')
ax1.set_xlabel('False Positive Rate (1 - Specificity)', fontsize=11)
ax1.set_ylabel('True Positive Rate (Recall)', fontsize=11)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='lower right', fontsize=10)

ax2.plot([0, 1], [0, 1], 'k--', label='Random Chance (AUC = 0.5000)')
for m_name in ['Random_Forest', 'Logistic_Regression', 'Dummy_Prior']:
    fpr, tpr, _ = roc_curve(y_test, chrono_probs[m_name])
    ra = roc_auc_score(y_test, chrono_probs[m_name])
    ax2.plot(fpr, tpr, label=f"{m_name} (ROC-AUC = {ra:.4f})", color=plot_colors[m_name], lw=2)

ax2.set_title('ROC Curves: Chronological Holdout (2025-2026)\n(Temporal Generalization Across Later Dates)', fontsize=12, fontweight='bold')
ax2.set_xlabel('False Positive Rate (1 - Specificity)', fontsize=11)
ax2.set_ylabel('True Positive Rate (Recall)', fontsize=11)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='lower right', fontsize=10)

plt.tight_layout()
p4_path = os.path.join(PLOTS_DIR, 'roc_curves.png')
plt.savefig(p4_path, dpi=300)
plt.close()
print(f"Saved Plot 4: {p4_path}")

# 5. Confusion Matrices
fig, axes = plt.subplots(2, 4, figsize=(18, 9))

def plot_cm(ax, cm, title):
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.set_title(title, fontsize=10, fontweight='bold')
    tick_marks = np.arange(2)
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(['Safe (0)', 'Risk (1)'])
    ax.set_yticklabels(['Safe (0)', 'Risk (1)'])
    
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                    fontsize=11, fontweight='bold')
    ax.set_ylabel('True Next-Visit Label', fontsize=9)
    ax.set_xlabel('Predicted Label', fontsize=9)

# Row 1: GroupKFold
plot_cm(axes[0, 0], conf_matrices['GroupKFold_Dummy_Prior'], 'GKF: Dummy Prior')
plot_cm(axes[0, 1], conf_matrices['GroupKFold_Persistence'], 'GKF: Persistence Baseline')
plot_cm(axes[0, 2], conf_matrices['GroupKFold_Logistic_Regression'], 'GKF: Logistic Regression')
plot_cm(axes[0, 3], conf_matrices['GroupKFold_Random_Forest'], 'GKF: Random Forest')

# Row 2: Chronological Test
plot_cm(axes[1, 0], conf_matrices['Chronological_Dummy_Prior'], 'Chrono: Dummy Prior')
plot_cm(axes[1, 1], conf_matrices['Chronological_Persistence'], 'Chrono: Persistence Baseline')
plot_cm(axes[1, 2], conf_matrices['Chronological_Logistic_Regression'], 'Chrono: Logistic Regression')
plot_cm(axes[1, 3], conf_matrices['Chronological_Random_Forest'], 'Chrono: Random Forest')

plt.tight_layout()
p5_path = os.path.join(PLOTS_DIR, 'confusion_matrices.png')
plt.savefig(p5_path, dpi=300)
plt.close()
print(f"Saved Plot 5: {p5_path}")

print("\n" + "=" * 80)
print("EXPERIMENT 3 TRAINING & EVALUATION COMPLETED SUCCESSFULLY!")
print("=" * 80)

