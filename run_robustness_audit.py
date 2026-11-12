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

BASE_DIR = 'experiment_1_robustness_audit_v1'
METRICS_DIR = os.path.join(BASE_DIR, 'metrics')
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')

os.makedirs(METRICS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

# 1. Load data
DATA_PATH = 'processed_data_v2/toxicity_analysis_v2.csv'
print(f"Loading data from {DATA_PATH}...")
df = pd.read_csv(DATA_PATH)
df['datetime'] = pd.to_datetime(df['datetime'])
df['year'] = df['datetime'].dt.year
df = df.sort_values(['pond_id', 'datetime']).reset_index(drop=True)

target_col = 'primary_calculated_nh3_mg_l'
y = df[target_col].values
ponds = df['pond_id'].values

# Feature sets
cont_features_a = ['dissolved_oxygen_mg_l', 'ph', 'temp_c', 'turbidity_cm', 'tds_ppt']
df['tds_ppt_is_missing'] = df['tds_ppt'].isna().astype(float)
df['turbidity_cm_is_missing'] = df['turbidity_cm'].isna().astype(float)
ind_features_a = ['tds_ppt_is_missing', 'turbidity_cm_is_missing']
cat_features_common = ['Weather', 'water_color', 'region']

features_model_a = cont_features_a + ind_features_a + cat_features_common
cont_features_b = ['dissolved_oxygen_mg_l', 'ph', 'temp_c']
features_model_b = cont_features_b + cat_features_common

# Pipeline builders
def build_pipe_a():
    num_pipe = Pipeline([('imputer', SimpleImputer(strategy='median'))])
    ind_pipe = Pipeline([('imputer', SimpleImputer(strategy='constant', fill_value=0.0))])
    cat_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
        ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    prep = ColumnTransformer([
        ('num', num_pipe, cont_features_a),
        ('ind', ind_pipe, ind_features_a),
        ('cat', cat_pipe, cat_features_common)
    ])
    rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1)
    return Pipeline([('preprocessor', prep), ('regressor', rf)])

def build_pipe_b():
    num_pipe = Pipeline([('imputer', SimpleImputer(strategy='median'))])
    cat_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
        ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    prep = ColumnTransformer([
        ('num', num_pipe, cont_features_b),
        ('cat', cat_pipe, cat_features_common)
    ])
    rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1)
    return Pipeline([('preprocessor', prep), ('regressor', rf)])

print("\n=========================================================================")
print("=== VERIFICATION 1: IDENTICAL EVALUATION ROWS AND TARGET VALUES ===")
print("=========================================================================")
print(f"Total dataset rows: {len(df)}")
print(f"Target non-null count: {pd.Series(y).notna().sum()} / {len(df)}")
print(f"Target physical range: min={y.min():.5f}, max={y.max():.5f}, mean={y.mean():.5f}, std={y.std():.5f}")

# Re-run 5-fold GroupKFold to extract exact OOF predictions and verify fold independence
gkf = GroupKFold(n_splits=5)
oof_preds_a = np.zeros(len(df))
oof_preds_b = np.zeros(len(df))

fold_verification = []

for fold, (train_idx, val_idx) in enumerate(gkf.split(df, groups=ponds)):
    train_ponds = set(ponds[train_idx])
    val_ponds = set(ponds[val_idx])
    overlap = train_ponds.intersection(val_ponds)
    
    # Assert zero pond overlap
    assert len(overlap) == 0, f"Error: Pond overlap detected in fold {fold+1}!"
    fold_verification.append({
        'fold': fold + 1,
        'n_train': len(train_idx),
        'n_val': len(val_idx),
        'ponds_train': len(train_ponds),
        'ponds_val': len(val_ponds),
        'overlap_count': len(overlap)
    })
    
    # Train Model A
    pipe_a = build_pipe_a()
    pipe_a.fit(df.iloc[train_idx][features_model_a], y[train_idx])
    oof_preds_a[val_idx] = pipe_a.predict(df.iloc[val_idx][features_model_a])
    
    # Train Model B
    pipe_b = build_pipe_b()
    pipe_b.fit(df.iloc[train_idx][features_model_b], y[train_idx])
    oof_preds_b[val_idx] = pipe_b.predict(df.iloc[val_idx][features_model_b])

print("GroupKFold integrity verification (Zero overlap across all folds):")
print(pd.DataFrame(fold_verification).to_string(index=False))

# Load or evaluate Chronological split models
cutoff = pd.to_datetime('2025-01-01 00:00:00')
train_mask = df['datetime'] < cutoff
test_mask = df['datetime'] >= cutoff

# Check existing serialized models from sensor ablation experiment
model_b_joblib_path = 'experiment_1_sensor_ablation_v1/models/model_b_rf_pipeline.joblib'
model_a_joblib_path = 'experiment_1_sensor_ablation_v1/models/model_a_rf_pipeline.joblib'

if os.path.exists(model_b_joblib_path) and os.path.exists(model_a_joblib_path):
    print(f"\nLoading existing chronological models from {model_b_joblib_path} and {model_a_joblib_path}...")
    pipe_a_chrono = joblib.load(model_a_joblib_path)
    pipe_b_chrono = joblib.load(model_b_joblib_path)
else:
    print("\nFitting chronological models on 2021-2024...")
    pipe_a_chrono = build_pipe_a()
    pipe_a_chrono.fit(df.loc[train_mask, features_model_a], y[train_mask])
    pipe_b_chrono = build_pipe_b()
    pipe_b_chrono.fit(df.loc[train_mask, features_model_b], y[train_mask])

chrono_preds_a = pipe_a_chrono.predict(df.loc[test_mask, features_model_a])
chrono_preds_b = pipe_b_chrono.predict(df.loc[test_mask, features_model_b])

df['oof_pred_model_a'] = oof_preds_a
df['oof_pred_model_b'] = oof_preds_b
df['oof_res_model_b'] = y - oof_preds_b
df['oof_abs_err_model_b'] = np.abs(df['oof_res_model_b'])

df_test = df[test_mask].copy()
df_test['chrono_pred_model_a'] = chrono_preds_a
df_test['chrono_pred_model_b'] = chrono_preds_b
df_test['chrono_res_model_b'] = df_test[target_col] - chrono_preds_b
df_test['chrono_abs_err_model_b'] = np.abs(df_test['chrono_res_model_b'])

print("\n=========================================================================")
print("=== ANALYSIS 1: YEARLY ERROR AND BIAS ANALYSIS ===")
print("=========================================================================")
yearly_records = []

for yr in sorted(df['year'].unique()):
    mask_yr = df['year'] == yr
    y_yr = y[mask_yr]
    pred_b_yr = oof_preds_b[mask_yr]
    pred_a_yr = oof_preds_a[mask_yr]
    
    # Signed error / bias = pred - actual
    bias_b = np.mean(pred_b_yr - y_yr)
    bias_a = np.mean(pred_a_yr - y_yr)
    
    mae_b = mean_absolute_error(y_yr, pred_b_yr)
    rmse_b = root_mean_squared_error(y_yr, pred_b_yr)
    r2_b = r2_score(y_yr, pred_b_yr)
    
    mae_a = mean_absolute_error(y_yr, pred_a_yr)
    rmse_a = root_mean_squared_error(y_yr, pred_a_yr)
    r2_a = r2_score(y_yr, pred_a_yr)
    
    yearly_records.append({
        'year': yr,
        'protocol': 'GroupKFold_OOF',
        'n_samples': int(mask_yr.sum()),
        'target_mean': float(y_yr.mean()),
        'target_std': float(y_yr.std()),
        'target_median': float(np.median(y_yr)),
        'model_b_pred_mean': float(pred_b_yr.mean()),
        'model_b_bias': float(bias_b),
        'model_b_mae': float(mae_b),
        'model_b_rmse': float(rmse_b),
        'model_b_r2': float(r2_b),
        'model_a_bias': float(bias_a),
        'model_a_mae': float(mae_a),
        'model_a_rmse': float(rmse_a),
        'model_a_r2': float(r2_a)
    })

# Add Chronological Test years (2025, 2026, and Overall)
for yr in [2025, 2026]:
    mask_c_yr = df_test['year'] == yr
    y_cyr = df_test.loc[mask_c_yr, target_col].values
    pred_b_cyr = df_test.loc[mask_c_yr, 'chrono_pred_model_b'].values
    pred_a_cyr = df_test.loc[mask_c_yr, 'chrono_pred_model_a'].values
    
    yearly_records.append({
        'year': yr,
        'protocol': 'Chronological_Test',
        'n_samples': int(mask_c_yr.sum()),
        'target_mean': float(y_cyr.mean()),
        'target_std': float(y_cyr.std()),
        'target_median': float(np.median(y_cyr)),
        'model_b_pred_mean': float(pred_b_cyr.mean()),
        'model_b_bias': float(np.mean(pred_b_cyr - y_cyr)),
        'model_b_mae': float(mean_absolute_error(y_cyr, pred_b_cyr)),
        'model_b_rmse': float(root_mean_squared_error(y_cyr, pred_b_cyr)),
        'model_b_r2': float(r2_score(y_cyr, pred_b_cyr)),
        'model_a_bias': float(np.mean(pred_a_cyr - y_cyr)),
        'model_a_mae': float(mean_absolute_error(y_cyr, pred_a_cyr)),
        'model_a_rmse': float(root_mean_squared_error(y_cyr, pred_a_cyr)),
        'model_a_r2': float(r2_score(y_cyr, pred_a_cyr))
    })

df_yearly = pd.DataFrame(yearly_records)
yearly_csv = os.path.join(METRICS_DIR, 'yearly_metrics.csv')
df_yearly.to_csv(yearly_csv, index=False)
print(f"Saved yearly metrics to {yearly_csv}")
print(df_yearly[['year', 'protocol', 'n_samples', 'target_mean', 'model_b_bias', 'model_b_mae', 'model_b_r2']].to_string(index=False))

print("\n=========================================================================")
print("=== ANALYSIS 2: REGIONAL ERROR AND BIAS ANALYSIS ===")
print("=========================================================================")
regional_records = []

for reg in sorted(df['region'].unique()):
    # OOF
    mask_reg = df['region'] == reg
    y_reg = y[mask_reg]
    p_b_reg = oof_preds_b[mask_reg]
    p_a_reg = oof_preds_a[mask_reg]
    
    regional_records.append({
        'region': reg,
        'protocol': 'GroupKFold_OOF',
        'n_samples': int(mask_reg.sum()),
        'target_mean': float(y_reg.mean()),
        'target_std': float(y_reg.std()),
        'model_b_pred_mean': float(p_b_reg.mean()),
        'model_b_bias': float(np.mean(p_b_reg - y_reg)),
        'model_b_mae': float(mean_absolute_error(y_reg, p_b_reg)),
        'model_b_rmse': float(root_mean_squared_error(y_reg, p_b_reg)),
        'model_b_r2': float(r2_score(y_reg, p_b_reg)),
        'model_a_mae': float(mean_absolute_error(y_reg, p_a_reg)),
        'model_a_rmse': float(root_mean_squared_error(y_reg, p_a_reg)),
        'model_a_r2': float(r2_score(y_reg, p_a_reg))
    })
    
    # Chrono Test
    mask_c_reg = df_test['region'] == reg
    n_c_reg = mask_c_reg.sum()
    if n_c_reg > 0:
        y_c_reg = df_test.loc[mask_c_reg, target_col].values
        p_b_c_reg = df_test.loc[mask_c_reg, 'chrono_pred_model_b'].values
        p_a_c_reg = df_test.loc[mask_c_reg, 'chrono_pred_model_a'].values
        
        regional_records.append({
            'region': reg,
            'protocol': 'Chronological_Test',
            'n_samples': int(n_c_reg),
            'target_mean': float(y_c_reg.mean()),
            'target_std': float(y_c_reg.std()),
            'model_b_pred_mean': float(p_b_c_reg.mean()),
            'model_b_bias': float(np.mean(p_b_c_reg - y_c_reg)),
            'model_b_mae': float(mean_absolute_error(y_c_reg, p_b_c_reg)),
            'model_b_rmse': float(root_mean_squared_error(y_c_reg, p_b_c_reg)),
            'model_b_r2': float(r2_score(y_c_reg, p_b_c_reg)),
            'model_a_mae': float(mean_absolute_error(y_c_reg, p_a_c_reg)),
            'model_a_rmse': float(root_mean_squared_error(y_c_reg, p_a_c_reg)),
            'model_a_r2': float(r2_score(y_c_reg, p_a_c_reg))
        })
    else:
        regional_records.append({
            'region': reg,
            'protocol': 'Chronological_Test',
            'n_samples': 0,
            'target_mean': np.nan,
            'target_std': np.nan,
            'model_b_pred_mean': np.nan,
            'model_b_bias': np.nan,
            'model_b_mae': np.nan,
            'model_b_rmse': np.nan,
            'model_b_r2': np.nan,
            'model_a_mae': np.nan,
            'model_a_rmse': np.nan,
            'model_a_r2': np.nan
        })

df_regional = pd.DataFrame(regional_records)
regional_csv = os.path.join(METRICS_DIR, 'regional_metrics.csv')
df_regional.to_csv(regional_csv, index=False)
print(f"Saved regional metrics to {regional_csv}")
print(df_regional[['region', 'protocol', 'n_samples', 'target_mean', 'model_b_bias', 'model_b_mae', 'model_b_r2']].to_string(index=False))

print("\n=========================================================================")
print("=== ANALYSIS 3: POND-LEVEL ERROR AND HIGH-ERROR IDENTIFICATION ===")
print("=========================================================================")
# Pond-level aggregation for Model B OOF
pond_stats = df.groupby('pond_id').agg(
    region=('region', 'first'),
    n_visits=('primary_calculated_nh3_mg_l', 'count'),
    target_mean=('primary_calculated_nh3_mg_l', 'mean'),
    target_max=('primary_calculated_nh3_mg_l', 'max'),
    model_b_pred_mean=('oof_pred_model_b', 'mean'),
    model_b_bias=('oof_pred_model_b', lambda p: np.mean(p - df.loc[p.index, 'primary_calculated_nh3_mg_l'])),
    model_b_mae=('oof_abs_err_model_b', 'mean'),
    model_b_rmse=('oof_res_model_b', lambda r: np.sqrt(np.mean(r**2))),
    model_b_max_err=('oof_abs_err_model_b', 'max'),
    model_a_mae=('oof_pred_model_a', lambda p: mean_absolute_error(df.loc[p.index, 'primary_calculated_nh3_mg_l'], p))
).reset_index()

pond_stats = pond_stats.sort_values('model_b_mae', ascending=False)
pond_csv = os.path.join(METRICS_DIR, 'pond_error_analysis.csv')
pond_stats.to_csv(pond_csv, index=False)
print(f"Saved pond error analysis to {pond_csv}")
print("\nTop 15 Highest Error Ponds (by Model B MAE):")
print(pond_stats.head(15)[['pond_id', 'region', 'n_visits', 'target_mean', 'target_max', 'model_b_bias', 'model_b_mae', 'model_b_rmse']].to_string(index=False))

print(f"\nOverall Ponds: {len(pond_stats)}")
print(f"Ponds with MAE > 0.030 mg/L: {(pond_stats['model_b_mae'] > 0.030).sum()} ({(pond_stats['model_b_mae'] > 0.030).mean()*100:.1f}%)")
print(f"Ponds with MAE <= 0.015 mg/L: {(pond_stats['model_b_mae'] <= 0.015).sum()} ({(pond_stats['model_b_mae'] <= 0.015).mean()*100:.1f}%)")

print("\n=========================================================================")
print("=== ANALYSIS 4: RESIDUAL DISTRIBUTION & PREDICTION BIAS ===")
print("=========================================================================")
res_oof = df['oof_res_model_b'].values
bias_oof = np.mean(df['oof_pred_model_b'] - y)
print(f"Global OOF Mean Signed Error (Bias = Pred - Actual): {bias_oof:+.6f} mg/L")
print(f"Global OOF Residuals (Actual - Pred): Mean={res_oof.mean():+.6f}, Std={res_oof.std():.6f}, Skew={pd.Series(res_oof).skew():.4f}")
print(f"  % Over-estimated (Pred > Actual) : {(df['oof_pred_model_b'] > y).mean()*100:.2f}%")
print(f"  % Under-estimated (Pred < Actual): {(df['oof_pred_model_b'] < y).mean()*100:.2f}%")
print(f"  % Exactly equal (0 residual)     : {(df['oof_pred_model_b'] == y).mean()*100:.2f}%")

res_chr = df_test['chrono_res_model_b'].values
bias_chr = np.mean(df_test['chrono_pred_model_b'] - df_test[target_col])
print(f"\nChronological Test Mean Signed Error (Bias = Pred - Actual): {bias_chr:+.6f} mg/L")
print(f"Chronological Test Residuals (Actual - Pred): Mean={res_chr.mean():+.6f}, Std={res_chr.std():.6f}, Skew={pd.Series(res_chr).skew():.4f}")
print(f"  % Over-estimated in 2025-2026: {(df_test['chrono_pred_model_b'] > df_test[target_col]).mean()*100:.2f}%")
print(f"  % Under-estimated in 2025-2026: {(df_test['chrono_pred_model_b'] < df_test[target_col]).mean()*100:.2f}%")

print("\n=========================================================================")
print("=== ANALYSIS 5: TARGET DISTRIBUTION & PROTOCOL SHIFT INVESTIGATION ===")
print("=========================================================================")
target_by_year = df.groupby('year')['primary_calculated_nh3_mg_l'].agg(
    n_records='count',
    mean='mean',
    std='std',
    median='median',
    p25=lambda s: s.quantile(0.25),
    p75=lambda s: s.quantile(0.75),
    max='max',
    skew='skew'
).reset_index()
print("Target Distribution across Monitoring Years:")
print(target_by_year.to_string(index=False))

ct_protocol = pd.crosstab(df['year'], df['nh3_calculation_source'])
print("\nAmmonia Calculation Protocol Shift by Year:")
print(ct_protocol)

print("\n=========================================================================")
print("=== GENERATING AUDIT PLOTS ===")
print("=========================================================================")

# Plot 1: Yearly Performance (MAE, RMSE, R2, Bias)
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
years = [2021, 2022, 2023, 2024, 2025, 2026]
oof_yr = df_yearly[df_yearly['protocol'] == 'GroupKFold_OOF']

# 1. MAE by year
ax1.plot(oof_yr['year'], oof_yr['model_b_mae'], 'o-', color='#2ca02c', lw=2, label='Model B (6 Feats) - OOF')
ax1.plot(oof_yr['year'], oof_yr['model_a_mae'], 's--', color='#1f77b4', lw=2, label='Model A (8 Feats) - OOF')
chr_yr = df_yearly[df_yearly['protocol'] == 'Chronological_Test']
ax1.plot(chr_yr['year'], chr_yr['model_b_mae'], '^:', color='#d62728', lw=2.5, markersize=8, label='Model B - Chrono Test')
ax1.set_title('Mean Absolute Error (MAE) by Year', fontsize=12, fontweight='bold')
ax1.set_ylabel('MAE (mg/L)', fontsize=11)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(fontsize=9)

# 2. R2 by year
ax2.plot(oof_yr['year'], oof_yr['model_b_r2'], 'o-', color='#2ca02c', lw=2, label='Model B - OOF R²')
ax2.plot(oof_yr['year'], oof_yr['model_a_r2'], 's--', color='#1f77b4', lw=2, label='Model A - OOF R²')
ax2.plot(chr_yr['year'], chr_yr['model_b_r2'], '^:', color='#d62728', lw=2.5, markersize=8, label='Model B - Chrono Test R²')
ax2.axhline(0, color='black', linestyle='--', lw=1)
ax2.set_title('Coefficient of Determination (R²) by Year', fontsize=12, fontweight='bold')
ax2.set_ylabel('R² Score', fontsize=11)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(fontsize=9)

# 3. Prediction Bias by year
ax3.plot(oof_yr['year'], oof_yr['model_b_bias'], 'o-', color='#2ca02c', lw=2, label='Model B - OOF Bias')
ax3.plot(oof_yr['year'], oof_yr['model_a_bias'], 's--', color='#1f77b4', lw=2, label='Model A - OOF Bias')
ax3.plot(chr_yr['year'], chr_yr['model_b_bias'], '^:', color='#d62728', lw=2.5, markersize=8, label='Model B - Chrono Test Bias')
ax3.axhline(0, color='red', linestyle='--', lw=1.2, label='Zero Bias')
ax3.set_title('Prediction Bias (Mean Signed Error: Pred - Actual)', fontsize=12, fontweight='bold')
ax3.set_xlabel('Monitoring Year', fontsize=11)
ax3.set_ylabel('Bias (mg/L)', fontsize=11)
ax3.grid(True, linestyle=':', alpha=0.6)
ax3.legend(fontsize=9)

# 4. Target Mean vs Predicted Mean
ax4.plot(oof_yr['year'], oof_yr['target_mean'], 'k-o', lw=2.5, label='Actual Target Mean')
ax4.plot(oof_yr['year'], oof_yr['model_b_pred_mean'], 'o--', color='#2ca02c', lw=2, label='Model B Pred Mean (OOF)')
ax4.plot(chr_yr['year'], chr_yr['model_b_pred_mean'], '^:', color='#d62728', lw=2.5, markersize=8, label='Model B Pred Mean (Chrono)')
ax4.set_title('Target Mean vs. Predicted Mean by Year', fontsize=12, fontweight='bold')
ax4.set_xlabel('Monitoring Year', fontsize=11)
ax4.set_ylabel('NH3 Concentration (mg/L)', fontsize=11)
ax4.grid(True, linestyle=':', alpha=0.6)
ax4.legend(fontsize=9)

plt.tight_layout()
p1_path = os.path.join(PLOTS_DIR, 'yearly_performance.png')
plt.savefig(p1_path, dpi=300)
plt.close()
print(f"Saved Plot 1 to {p1_path}")

# Plot 2: Residual Analysis (Histogram & Spread)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Histogram of Residuals
ax1.hist(res_oof, bins=60, color='#2ca02c', alpha=0.65, edgecolor='black', label=f'OOF Residuals (Mean={res_oof.mean():+.4f}, Std={res_oof.std():.4f})')
ax1.hist(res_chr, bins=40, color='#d62728', alpha=0.55, edgecolor='black', label=f'Chrono Test Residuals (Mean={res_chr.mean():+.4f}, Std={res_chr.std():.4f})')
ax1.axvline(0, color='black', linestyle='--', lw=1.5, label='Zero Residual')
ax1.set_title('Residual Error Distribution (Actual - Predicted)', fontsize=12, fontweight='bold')
ax1.set_xlabel('Residual Error (mg/L)', fontsize=11)
ax1.set_ylabel('Frequency', fontsize=11)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(fontsize=9)

# Residuals vs Fitted
ax2.scatter(df['oof_pred_model_b'], res_oof, alpha=0.25, color='#2ca02c', s=18, label='OOF Residuals (N=6,945)')
ax2.scatter(df_test['chrono_pred_model_b'], res_chr, alpha=0.35, color='#d62728', s=20, label='Chrono Test Residuals (N=2,600)')
ax2.axhline(0, color='black', linestyle='--', lw=1.5)
ax2.set_title('Residuals vs. Fitted Values (Model B)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Predicted Calculated NH3 (mg/L)', fontsize=11)
ax2.set_ylabel('Residual: Actual - Predicted (mg/L)', fontsize=11)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(fontsize=9)

plt.tight_layout()
p2_path = os.path.join(PLOTS_DIR, 'residual_analysis.png')
plt.savefig(p2_path, dpi=300)
plt.close()
print(f"Saved Plot 2 to {p2_path}")

# Plot 3: Actual vs Predicted (Model B OOF by Region + Chrono Test)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

# Panel 1: OOF by Region
eluru_mask = df['region'] == 'Eluru'
nellore_mask = df['region'] == 'Nellore'
max_val = max(y.max(), df['oof_pred_model_b'].max()) * 1.05

ax1.scatter(y[eluru_mask], df.loc[eluru_mask, 'oof_pred_model_b'], alpha=0.25, color='#1f77b4', s=16, label=f"Eluru (N={eluru_mask.sum()}, MAE={mean_absolute_error(y[eluru_mask], df.loc[eluru_mask, 'oof_pred_model_b']):.4f})")
ax1.scatter(y[nellore_mask], df.loc[nellore_mask, 'oof_pred_model_b'], alpha=0.35, color='#ff7f0e', s=20, label=f"Nellore (N={nellore_mask.sum()}, MAE={mean_absolute_error(y[nellore_mask], df.loc[nellore_mask, 'oof_pred_model_b']):.4f})")
ax1.plot([0, max_val], [0, max_val], 'k--', lw=1.5, label='1:1 Line')
ax1.set_title('Model B OOF: Actual vs. Predicted by Region', fontsize=12, fontweight='bold')
ax1.set_xlabel('Actual Calculated NH3 (mg/L)', fontsize=11)
ax1.set_ylabel('Predicted NH3 (mg/L)', fontsize=11)
ax1.set_xlim(0, max_val)
ax1.set_ylim(0, max_val)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='upper left', fontsize=10)

# Panel 2: Chrono Test Actual vs Predicted
max_c = max(df_test[target_col].max(), df_test['chrono_pred_model_b'].max()) * 1.05
ax2.scatter(df_test[target_col], df_test['chrono_pred_model_b'], alpha=0.35, color='#2ca02c', s=22, label=f"Chrono Test 2025-2026 (N=2,600, MAE={mean_absolute_error(df_test[target_col], df_test['chrono_pred_model_b']):.4f})")
ax2.plot([0, max_c], [0, max_c], 'k--', lw=1.5, label='1:1 Line')
ax2.set_title('Model B Chronological Test: Actual vs. Predicted (2025-2026)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Actual Calculated NH3 (mg/L)', fontsize=11)
ax2.set_ylabel('Predicted NH3 (mg/L)', fontsize=11)
ax2.set_xlim(0, max_c)
ax2.set_ylim(0, max_c)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='upper left', fontsize=10)

plt.tight_layout()
p3_path = os.path.join(PLOTS_DIR, 'actual_vs_predicted.png')
plt.savefig(p3_path, dpi=300)
plt.close()
print(f"Saved Plot 3 to {p3_path}")

print("\n=== AUDIT COMPUTATIONS COMPLETED SUCCESSFULLY ===")
