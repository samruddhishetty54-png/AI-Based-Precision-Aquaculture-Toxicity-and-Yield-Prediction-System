import os
import tempfile
os.environ['MPLCONFIGDIR'] = os.path.join(tempfile.gettempdir(), 'mpl_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import GroupKFold
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

BASE_DIR = 'experiment_1_sensor_ablation_v1'
MODELS_DIR = os.path.join(BASE_DIR, 'models')
METRICS_DIR = os.path.join(BASE_DIR, 'metrics')
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

# 1. Load data
DATA_PATH = 'processed_data_v2/toxicity_analysis_v2.csv'
print(f"Loading data from {DATA_PATH}...")
df = pd.read_csv(DATA_PATH)
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values(['pond_id', 'datetime']).reset_index(drop=True)

target_col = 'primary_calculated_nh3_mg_l'
y = df[target_col].values
ponds = df['pond_id'].values

# Feature sets definition
# Model A: 8 features + 2 missingness indicators
cont_features_a = ['dissolved_oxygen_mg_l', 'ph', 'temp_c', 'turbidity_cm', 'tds_ppt']
df['tds_ppt_is_missing'] = df['tds_ppt'].isna().astype(float)
df['turbidity_cm_is_missing'] = df['turbidity_cm'].isna().astype(float)
ind_features_a = ['tds_ppt_is_missing', 'turbidity_cm_is_missing']
cat_features_common = ['Weather', 'water_color', 'region']

features_model_a = cont_features_a + ind_features_a + cat_features_common

# Model B: 6 features ONLY (Strictly exclude tds_ppt, turbidity_cm and their indicators)
cont_features_b = ['dissolved_oxygen_mg_l', 'ph', 'temp_c']
features_model_b = cont_features_b + cat_features_common

print(f"Dataset rows: {len(df)}")
print(f"Model A features ({len(features_model_a)}): {features_model_a}")
print(f"Model B features ({len(features_model_b)}): {features_model_b}")

# 2. Pipeline Factories
def build_pipeline_model_a():
    num_pipe = Pipeline([('imputer', SimpleImputer(strategy='median'))])
    ind_pipe = Pipeline([('imputer', SimpleImputer(strategy='constant', fill_value=0.0))])
    cat_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
        ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    preprocessor = ColumnTransformer([
        ('num', num_pipe, cont_features_a),
        ('ind', ind_pipe, ind_features_a),
        ('cat', cat_pipe, cat_features_common)
    ], remainder='drop')
    
    rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1)
    return Pipeline([('preprocessor', preprocessor), ('regressor', rf)])

def build_pipeline_model_b():
    num_pipe = Pipeline([('imputer', SimpleImputer(strategy='median'))])
    cat_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
        ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    preprocessor = ColumnTransformer([
        ('num', num_pipe, cont_features_b),
        ('cat', cat_pipe, cat_features_common)
    ], remainder='drop')
    
    rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1)
    return Pipeline([('preprocessor', preprocessor), ('regressor', rf)])

# 3. Protocol 1: 5-Fold GroupKFold Cross-Validation
print("\n=========================================================================")
print("=== PROTOCOL 1: 5-FOLD GROUPKFOLD BY POND_ID ===")
print("=========================================================================")

gkf = GroupKFold(n_splits=5)
fold_metrics = []

oof_preds = {
    'Dummy_Mean': np.zeros(len(df)),
    'Dummy_Median': np.zeros(len(df)),
    'Ablation_pH_Temp': np.zeros(len(df)),
    'Model_A_8Features': np.zeros(len(df)),
    'Model_B_6Features': np.zeros(len(df))
}

for fold, (train_idx, val_idx) in enumerate(gkf.split(df, groups=ponds)):
    df_train, y_train = df.iloc[train_idx], y[train_idx]
    df_val, y_val = df.iloc[val_idx], y[val_idx]
    
    # 1. Dummy Mean
    dm = DummyRegressor(strategy='mean')
    dm.fit(df_train, y_train)
    p_dm = dm.predict(df_val)
    oof_preds['Dummy_Mean'][val_idx] = p_dm
    
    # 2. Dummy Median
    dmed = DummyRegressor(strategy='median')
    dmed.fit(df_train, y_train)
    p_dmed = dmed.predict(df_val)
    oof_preds['Dummy_Median'][val_idx] = p_dmed
    
    # 3. Ablation pH + Temp
    ab_imp = SimpleImputer(strategy='median')
    X_tr_ab = ab_imp.fit_transform(df_train[['ph', 'temp_c']])
    X_va_ab = ab_imp.transform(df_val[['ph', 'temp_c']])
    rf_ab = RandomForestRegressor(n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1)
    rf_ab.fit(X_tr_ab, y_train)
    p_ab = rf_ab.predict(X_va_ab)
    oof_preds['Ablation_pH_Temp'][val_idx] = p_ab
    
    # 4. Model A (8 features + indicators)
    pipe_a = build_pipeline_model_a()
    pipe_a.fit(df_train[features_model_a], y_train)
    p_a = pipe_a.predict(df_val[features_model_a])
    oof_preds['Model_A_8Features'][val_idx] = p_a
    
    # 5. Model B (6 features strictly)
    pipe_b = build_pipeline_model_b()
    pipe_b.fit(df_train[features_model_b], y_train)
    p_b = pipe_b.predict(df_val[features_model_b])
    oof_preds['Model_B_6Features'][val_idx] = p_b
    
    for m_name, preds in [('Dummy_Mean', p_dm), ('Dummy_Median', p_dmed), 
                          ('Ablation_pH_Temp', p_ab), ('Model_A_8Features', p_a), 
                          ('Model_B_6Features', p_b)]:
        mae = mean_absolute_error(y_val, preds)
        rmse = root_mean_squared_error(y_val, preds)
        r2 = r2_score(y_val, preds)
        fold_metrics.append({
            'protocol': 'GroupKFold',
            'fold': fold + 1,
            'model': m_name,
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'n_train': len(train_idx),
            'n_val': len(val_idx)
        })

df_fold_metrics = pd.DataFrame(fold_metrics)
print("\n--- GroupKFold Mean ± Std across Folds ---")
gkf_summary = df_fold_metrics.groupby('model').agg(
    mae_mean=('mae', 'mean'), mae_std=('mae', 'std'),
    rmse_mean=('rmse', 'mean'), rmse_std=('rmse', 'std'),
    r2_mean=('r2', 'mean'), r2_std=('r2', 'std')
).reset_index()
print(gkf_summary.to_string(index=False))

print("\n--- Global Out-of-Fold (OOF) Metrics (N = 6,945) ---")
oof_summary = []
for m_name, preds in oof_preds.items():
    mae = mean_absolute_error(y, preds)
    rmse = root_mean_squared_error(y, preds)
    r2 = r2_score(y, preds)
    oof_summary.append({
        'protocol': 'GroupKFold_OOF_Global',
        'fold': 'Overall',
        'model': m_name,
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'n_train': 5556,
        'n_val': 6945
    })
df_oof_summary = pd.DataFrame(oof_summary)
print(df_oof_summary[['model', 'mae', 'rmse', 'r2']].to_string(index=False))

# 4. Protocol 2: Chronological Split (2021-2024 vs 2025-2026)
print("\n=========================================================================")
print("=== PROTOCOL 2: CHRONOLOGICAL HOLDOUT (2021-2024 vs 2025-2026) ===")
print("=========================================================================")

cutoff = pd.to_datetime('2025-01-01 00:00:00')
train_mask = df['datetime'] < cutoff
test_mask = df['datetime'] >= cutoff

df_train_c = df[train_mask].copy()
y_train_c = y[train_mask]
df_test_c = df[test_mask].copy()
y_test_c = y[test_mask]

print(f"Train (2021-2024): N = {len(df_train_c)}, Ponds = {df_train_c['pond_id'].nunique()}")
print(f"Test  (2025-2026): N = {len(df_test_c)}, Ponds = {df_test_c['pond_id'].nunique()}")

chrono_metrics = []
chrono_preds = {}

# 1. Dummy Mean
dm_c = DummyRegressor(strategy='mean')
dm_c.fit(df_train_c, y_train_c)
p_dm_c = dm_c.predict(df_test_c)
chrono_preds['Dummy_Mean'] = p_dm_c

# 2. Dummy Median
dmed_c = DummyRegressor(strategy='median')
dmed_c.fit(df_train_c, y_train_c)
p_dmed_c = dmed_c.predict(df_test_c)
chrono_preds['Dummy_Median'] = p_dmed_c

# 3. Ablation pH + Temp
ab_imp_c = SimpleImputer(strategy='median')
X_tr_ab_c = ab_imp_c.fit_transform(df_train_c[['ph', 'temp_c']])
X_te_ab_c = ab_imp_c.transform(df_test_c[['ph', 'temp_c']])
rf_ab_c = RandomForestRegressor(n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1)
rf_ab_c.fit(X_tr_ab_c, y_train_c)
p_ab_c = rf_ab_c.predict(X_te_ab_c)
chrono_preds['Ablation_pH_Temp'] = p_ab_c

# 4. Model A (8 features)
pipe_a_c = build_pipeline_model_a()
pipe_a_c.fit(df_train_c[features_model_a], y_train_c)
p_a_c = pipe_a_c.predict(df_test_c[features_model_a])
chrono_preds['Model_A_8Features'] = p_a_c

joblib_a_path = os.path.join(MODELS_DIR, 'model_a_rf_pipeline.joblib')
joblib.dump(pipe_a_c, joblib_a_path)
print(f"Saved Model A pipeline to {joblib_a_path}")

# 5. Model B (6 features strictly)
pipe_b_c = build_pipeline_model_b()
pipe_b_c.fit(df_train_c[features_model_b], y_train_c)
p_b_c = pipe_b_c.predict(df_test_c[features_model_b])
chrono_preds['Model_B_6Features'] = p_b_c

joblib_b_path = os.path.join(MODELS_DIR, 'model_b_rf_pipeline.joblib')
joblib.dump(pipe_b_c, joblib_b_path)
print(f"Saved Model B pipeline to {joblib_b_path}")

for m_name, preds in chrono_preds.items():
    mae = mean_absolute_error(y_test_c, preds)
    rmse = root_mean_squared_error(y_test_c, preds)
    r2 = r2_score(y_test_c, preds)
    chrono_metrics.append({
        'protocol': 'Chronological_Holdout',
        'fold': 'Test_2025_2026',
        'model': m_name,
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'n_train': len(df_train_c),
        'n_val': len(df_test_c)
    })

df_chrono_metrics = pd.DataFrame(chrono_metrics)
print("\n--- Chronological Holdout Test Performance (2025-2026, N = 2,600) ---")
print(df_chrono_metrics[['model', 'mae', 'rmse', 'r2']].to_string(index=False))

# Combine and save all metrics
all_metrics_df = pd.concat([df_fold_metrics, df_oof_summary, df_chrono_metrics], ignore_index=True)
metrics_csv = os.path.join(METRICS_DIR, 'sensor_ablation_metrics.csv')
all_metrics_df.to_csv(metrics_csv, index=False)
print(f"\nSaved all sensor ablation metrics to {metrics_csv}")

# 5. Feature Importances Comparison
print("\n=========================================================================")
print("=== FEATURE IMPORTANCES COMPARISON ===")
print("=========================================================================")

# Model A Feature Importances
cat_ohe_a = pipe_a_c.named_steps['preprocessor'].named_transformers_['cat'].named_steps['ohe']
cat_names_a = list(cat_ohe_a.get_feature_names_out(cat_features_common))
names_a = cont_features_a + ind_features_a + cat_names_a
imp_a = pipe_a_c.named_steps['regressor'].feature_importances_

df_imp_a = pd.DataFrame({'feature': names_a, 'importance_model_a': imp_a})

# Model B Feature Importances
cat_ohe_b = pipe_b_c.named_steps['preprocessor'].named_transformers_['cat'].named_steps['ohe']
cat_names_b = list(cat_ohe_b.get_feature_names_out(cat_features_common))
names_b = cont_features_b + cat_names_b
imp_b = pipe_b_c.named_steps['regressor'].feature_importances_

df_imp_b = pd.DataFrame({'feature': names_b, 'importance_model_b': imp_b})

df_imp_merged = pd.merge(df_imp_a, df_imp_b, on='feature', how='outer').fillna(0.0)
df_imp_merged = df_imp_merged.sort_values('importance_model_b', ascending=False)

imp_csv = os.path.join(METRICS_DIR, 'feature_importances_comparison.csv')
df_imp_merged.to_csv(imp_csv, index=False)
print(f"Saved feature importances comparison to {imp_csv}")
print(df_imp_merged.head(15).to_string(index=False))

# 6. Evaluation Plots
print("\n=========================================================================")
print("=== GENERATING DIAGNOSTIC PLOTS ===")
print("=========================================================================")

# Plot 1: Actual vs Predicted (GroupKFold OOF) - Model A vs Model B
plt.figure(figsize=(10, 8))
plt.scatter(y, oof_preds['Model_A_8Features'], alpha=0.30, color='#1f77b4', s=20, label=f"Model A (8 Features) - OOF R²={r2_score(y, oof_preds['Model_A_8Features']):.3f}")
plt.scatter(y, oof_preds['Model_B_6Features'], alpha=0.30, color='#2ca02c', s=20, label=f"Model B (6 Features) - OOF R²={r2_score(y, oof_preds['Model_B_6Features']):.3f}")
max_v = max(y.max(), oof_preds['Model_A_8Features'].max(), oof_preds['Model_B_6Features'].max()) * 1.05
plt.plot([0, max_v], [0, max_v], 'k--', lw=1.5, label='1:1 Ideal Line')
plt.xlabel('Actual Calculated NH3 (mg/L)', fontsize=12)
plt.ylabel('Predicted NH3 (mg/L)', fontsize=12)
plt.title('GroupKFold OOF: Model A (8 Features) vs. Model B (6 Features)', fontsize=13, fontweight='bold')
plt.xlim(0, max_v)
plt.ylim(0, max_v)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper left', fontsize=11)
plt.tight_layout()
p1_path = os.path.join(PLOTS_DIR, 'actual_vs_predicted_groupkfold.png')
plt.savefig(p1_path, dpi=300)
plt.close()
print(f"Saved Plot 1 to {p1_path}")

# Plot 2: Residuals (GroupKFold OOF) - Model A vs Model B
res_a_gkf = y - oof_preds['Model_A_8Features']
res_b_gkf = y - oof_preds['Model_B_6Features']
mae_a_gkf = mean_absolute_error(y, oof_preds['Model_A_8Features'])
mae_b_gkf = mean_absolute_error(y, oof_preds['Model_B_6Features'])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
ax1.scatter(oof_preds['Model_A_8Features'], res_a_gkf, alpha=0.30, color='#1f77b4', s=20)
ax1.axhline(0, color='red', linestyle='--', lw=1.5)
ax1.set_xlabel('Predicted Calculated NH3 (mg/L)', fontsize=11)
ax1.set_ylabel('Residual: Actual - Predicted (mg/L)', fontsize=11)
ax1.set_title(f'Model A (8 Features) Residuals (MAE={mae_a_gkf:.4f})', fontsize=12, fontweight='bold')
ax1.grid(True, linestyle=':', alpha=0.6)

ax2.scatter(oof_preds['Model_B_6Features'], res_b_gkf, alpha=0.30, color='#2ca02c', s=20)
ax2.axhline(0, color='red', linestyle='--', lw=1.5)
ax2.set_xlabel('Predicted Calculated NH3 (mg/L)', fontsize=11)
ax2.set_title(f'Model B (6 Features) Residuals (MAE={mae_b_gkf:.4f})', fontsize=12, fontweight='bold')
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
p2_path = os.path.join(PLOTS_DIR, 'residuals_groupkfold.png')
plt.savefig(p2_path, dpi=300)
plt.close()
print(f"Saved Plot 2 to {p2_path}")

# Plot 3: Actual vs Predicted (Chronological Holdout 2025-2026) - Model A vs Model B
plt.figure(figsize=(10, 8))
plt.scatter(y_test_c, chrono_preds['Model_A_8Features'], alpha=0.30, color='#1f77b4', s=20, label=f"Model A (8 Features) - Test R²={r2_score(y_test_c, chrono_preds['Model_A_8Features']):.3f}")
plt.scatter(y_test_c, chrono_preds['Model_B_6Features'], alpha=0.30, color='#2ca02c', s=20, label=f"Model B (6 Features) - Test R²={r2_score(y_test_c, chrono_preds['Model_B_6Features']):.3f}")
plt.scatter(y_test_c, chrono_preds['Ablation_pH_Temp'], alpha=0.20, color='#ff7f0e', s=15, label=f"pH+Temp Baseline - Test R²={r2_score(y_test_c, chrono_preds['Ablation_pH_Temp']):.3f}")
max_vc = max(y_test_c.max(), chrono_preds['Model_A_8Features'].max(), chrono_preds['Model_B_6Features'].max()) * 1.05
plt.plot([0, max_vc], [0, max_vc], 'k--', lw=1.5, label='1:1 Ideal Line')
plt.xlabel('Actual Calculated NH3 (mg/L)', fontsize=12)
plt.ylabel('Predicted NH3 (mg/L)', fontsize=12)
plt.title('Chronological Holdout (2025-2026): Model A vs. Model B vs. Baseline', fontsize=13, fontweight='bold')
plt.xlim(0, max_vc)
plt.ylim(0, max_vc)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper left', fontsize=11)
plt.tight_layout()
p3_path = os.path.join(PLOTS_DIR, 'actual_vs_predicted_chronological.png')
plt.savefig(p3_path, dpi=300)
plt.close()
print(f"Saved Plot 3 to {p3_path}")

# Plot 4: Residuals (Chronological Holdout) - Model A vs Model B
res_a_chr = y_test_c - chrono_preds['Model_A_8Features']
res_b_chr = y_test_c - chrono_preds['Model_B_6Features']
mae_a_chr = mean_absolute_error(y_test_c, chrono_preds['Model_A_8Features'])
r2_a_chr = r2_score(y_test_c, chrono_preds['Model_A_8Features'])
mae_b_chr = mean_absolute_error(y_test_c, chrono_preds['Model_B_6Features'])
r2_b_chr = r2_score(y_test_c, chrono_preds['Model_B_6Features'])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
ax1.scatter(chrono_preds['Model_A_8Features'], res_a_chr, alpha=0.30, color='#1f77b4', s=20)
ax1.axhline(0, color='red', linestyle='--', lw=1.5)
ax1.set_xlabel('Predicted Calculated NH3 (mg/L)', fontsize=11)
ax1.set_ylabel('Residual: Actual - Predicted (mg/L)', fontsize=11)
ax1.set_title(f'Model A (8 Feats, Test 2025-2026)\nMAE={mae_a_chr:.4f}, R²={r2_a_chr:.3f}', fontsize=12, fontweight='bold')
ax1.grid(True, linestyle=':', alpha=0.6)

ax2.scatter(chrono_preds['Model_B_6Features'], res_b_chr, alpha=0.30, color='#2ca02c', s=20)
ax2.axhline(0, color='red', linestyle='--', lw=1.5)
ax2.set_xlabel('Predicted Calculated NH3 (mg/L)', fontsize=11)
ax2.set_title(f'Model B (6 Feats, Test 2025-2026)\nMAE={mae_b_chr:.4f}, R²={r2_b_chr:.3f}', fontsize=12, fontweight='bold')
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
p4_path = os.path.join(PLOTS_DIR, 'residuals_chronological.png')
plt.savefig(p4_path, dpi=300)
plt.close()
print(f"Saved Plot 4 to {p4_path}")

# Plot 5: Feature Importances Comparison (Top 10 features for Model B vs Model A)
top_b = df_imp_merged.head(10).sort_values('importance_model_b', ascending=True)

plt.figure(figsize=(11, 7))
y_pos = np.arange(len(top_b))
width = 0.38

plt.barh(y_pos + width/2, top_b['importance_model_a'], width, label='Model A (8 Features + Ind)', color='#1f77b4')
plt.barh(y_pos - width/2, top_b['importance_model_b'], width, label='Model B (6 Features Strictly)', color='#2ca02c')

plt.yticks(y_pos, top_b['feature'], fontsize=10)
plt.xlabel('Gini Feature Importance', fontsize=12)
plt.title('Feature Importances: Model A vs. Model B (Top 10 Model B Features)', fontsize=13, fontweight='bold')
plt.grid(True, linestyle=':', alpha=0.6, axis='x')
plt.legend(loc='lower right', fontsize=11)
plt.tight_layout()
p5_path = os.path.join(PLOTS_DIR, 'feature_importances_comparison.png')
plt.savefig(p5_path, dpi=300)
plt.close()
print(f"Saved Plot 5 to {p5_path}")

print("\n=== SENSOR ABLATION TRAINING SCRIPT COMPLETED ===")
