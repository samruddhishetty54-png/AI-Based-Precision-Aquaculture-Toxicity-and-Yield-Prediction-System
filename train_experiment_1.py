import os
import tempfile
# Configure Matplotlib backend and temp directory before importing pyplot
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

# Set seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Create output directories inside baseline_toxicity_v1
BASE_DIR = 'baseline_toxicity_v1'
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
continuous_features = ['dissolved_oxygen_mg_l', 'ph', 'temp_c', 'turbidity_cm', 'tds_ppt']
categorical_features = ['Weather', 'water_color', 'region']

# Add explicit missingness indicators before column transformer to guarantee traceability
df['tds_ppt_is_missing'] = df['tds_ppt'].isna().astype(float)
df['turbidity_cm_is_missing'] = df['turbidity_cm'].isna().astype(float)
indicator_features = ['tds_ppt_is_missing', 'turbidity_cm_is_missing']

all_feature_cols = continuous_features + indicator_features + categorical_features
y = df[target_col].values
X = df[all_feature_cols].copy()
ponds = df['pond_id'].values

print(f"Dataset shape: {df.shape}")
print(f"Target distribution: Mean={y.mean():.5f}, Median={np.median(y):.5f}, Std={y.std():.5f}, Min={y.min():.5f}, Max={y.max():.5f}")

# 2. Build Pipeline Transformers
def build_preprocessor():
    num_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median'))
    ])
    
    ind_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value=0.0))
    ])
    
    cat_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
        ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer([
        ('num', num_pipe, continuous_features),
        ('ind', ind_pipe, indicator_features),
        ('cat', cat_pipe, categorical_features)
    ], remainder='drop')
    
    return preprocessor

# 3. Model Factories
def get_models():
    return {
        'Dummy_Mean': DummyRegressor(strategy='mean'),
        'Dummy_Median': DummyRegressor(strategy='median'),
        'Ablation_pH_Temp': RandomForestRegressor(
            n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1
        ),
        'Random_Forest': RandomForestRegressor(
            n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1
        )
    }

print("\n=========================================================================")
print("=== PROTOCOL A: 5-FOLD GROUPKFOLD BY POND_ID (SPATIAL EVALUATION) ===")
print("=========================================================================")

gkf = GroupKFold(n_splits=5)
fold_metrics = []

# Out-of-fold prediction arrays
oof_preds = {
    'Dummy_Mean': np.zeros(len(df)),
    'Dummy_Median': np.zeros(len(df)),
    'Ablation_pH_Temp': np.zeros(len(df)),
    'Random_Forest': np.zeros(len(df))
}

for fold, (train_idx, val_idx) in enumerate(gkf.split(df, groups=ponds)):
    X_train, y_train = X.iloc[train_idx], y[train_idx]
    X_val, y_val = X.iloc[val_idx], y[val_idx]
    
    # Verify no pond overlap
    train_ponds = set(ponds[train_idx])
    val_ponds = set(ponds[val_idx])
    assert len(train_ponds.intersection(val_ponds)) == 0, f"Pond overlap detected in fold {fold+1}!"
    
    # Train and evaluate each model on this fold
    # 1. Dummy Mean
    dm = DummyRegressor(strategy='mean')
    dm.fit(X_train, y_train)
    p_dm = dm.predict(X_val)
    oof_preds['Dummy_Mean'][val_idx] = p_dm
    
    # 2. Dummy Median
    dmed = DummyRegressor(strategy='median')
    dmed.fit(X_train, y_train)
    p_dmed = dmed.predict(X_val)
    oof_preds['Dummy_Median'][val_idx] = p_dmed
    
    # 3. Ablation pH + Temp
    # Impute median for pH and temp if needed, though they are complete
    ablation_imputer = SimpleImputer(strategy='median')
    X_train_ablation = ablation_imputer.fit_transform(X_train[['ph', 'temp_c']])
    X_val_ablation = ablation_imputer.transform(X_val[['ph', 'temp_c']])
    
    rf_ablation = RandomForestRegressor(
        n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1
    )
    rf_ablation.fit(X_train_ablation, y_train)
    p_ablation = rf_ablation.predict(X_val_ablation)
    oof_preds['Ablation_pH_Temp'][val_idx] = p_ablation
    
    # 4. Full Random Forest Pipeline
    preprocessor = build_preprocessor()
    rf_full = RandomForestRegressor(
        n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1
    )
    full_pipe = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', rf_full)
    ])
    full_pipe.fit(X_train, y_train)
    p_rf = full_pipe.predict(X_val)
    oof_preds['Random_Forest'][val_idx] = p_rf
    
    for m_name, preds in [('Dummy_Mean', p_dm), ('Dummy_Median', p_dmed), 
                          ('Ablation_pH_Temp', p_ablation), ('Random_Forest', p_rf)]:
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
            'n_val': len(val_idx),
            'n_ponds_train': len(train_ponds),
            'n_ponds_val': len(val_ponds)
        })

df_fold_metrics = pd.DataFrame(fold_metrics)
print("\n--- Summary of 5-Fold GroupKFold Cross-Validation ---")
gkf_summary = df_fold_metrics.groupby('model').agg(
    mae_mean=('mae', 'mean'), mae_std=('mae', 'std'),
    rmse_mean=('rmse', 'mean'), rmse_std=('rmse', 'std'),
    r2_mean=('r2', 'mean'), r2_std=('r2', 'std')
).reset_index()
print(gkf_summary.to_string(index=False))

# Calculate overall OOF metrics across the full dataset
print("\n--- Overall Out-of-Fold (OOF) Metrics (Global N = 6,945) ---")
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
        'n_train': 5556,  # approx 4/5
        'n_val': 6945,
        'n_ponds_train': 253,
        'n_ponds_val': 317
    })
df_oof_summary = pd.DataFrame(oof_summary)
print(df_oof_summary[['model', 'mae', 'rmse', 'r2']].to_string(index=False))

print("\n=========================================================================")
print("=== PROTOCOL B: CHRONOLOGICAL HOLDOUT (2021-2024 vs 2025-2026) ===")
print("=========================================================================")

cutoff = pd.to_datetime('2025-01-01 00:00:00')
train_mask = df['datetime'] < cutoff
test_mask = df['datetime'] >= cutoff

X_train_c = X[train_mask].copy()
y_train_c = y[train_mask]
X_test_c = X[test_mask].copy()
y_test_c = y[test_mask]

print(f"Chronological Train (2021-2024): N = {len(X_train_c)}, Ponds = {df.loc[train_mask, 'pond_id'].nunique()}")
print(f"Chronological Test  (2025-2026): N = {len(X_test_c)}, Ponds = {df.loc[test_mask, 'pond_id'].nunique()}")

chrono_metrics = []
chrono_preds = {}

# 1. Dummy Mean
dm_c = DummyRegressor(strategy='mean')
dm_c.fit(X_train_c, y_train_c)
p_dm_c = dm_c.predict(X_test_c)
chrono_preds['Dummy_Mean'] = p_dm_c

# 2. Dummy Median
dmed_c = DummyRegressor(strategy='median')
dmed_c.fit(X_train_c, y_train_c)
p_dmed_c = dmed_c.predict(X_test_c)
chrono_preds['Dummy_Median'] = p_dmed_c

# 3. Ablation pH + Temp
ablation_imputer_c = SimpleImputer(strategy='median')
X_tr_ab_c = ablation_imputer_c.fit_transform(X_train_c[['ph', 'temp_c']])
X_te_ab_c = ablation_imputer_c.transform(X_test_c[['ph', 'temp_c']])

rf_ablation_c = RandomForestRegressor(
    n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1
)
rf_ablation_c.fit(X_tr_ab_c, y_train_c)
p_ab_c = rf_ablation_c.predict(X_te_ab_c)
chrono_preds['Ablation_pH_Temp'] = p_ab_c

# 4. Full Random Forest Pipeline
preprocessor_c = build_preprocessor()
rf_full_c = RandomForestRegressor(
    n_estimators=100, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1
)
full_pipe_c = Pipeline([
    ('preprocessor', preprocessor_c),
    ('regressor', rf_full_c)
])
full_pipe_c.fit(X_train_c, y_train_c)
p_rf_c = full_pipe_c.predict(X_test_c)
chrono_preds['Random_Forest'] = p_rf_c

# Save trained final pipeline artifact
joblib_path = os.path.join(MODELS_DIR, 'experiment_1_rf_pipeline.joblib')
joblib.dump(full_pipe_c, joblib_path)
print(f"\nSaved trained Random Forest pipeline to {joblib_path}")

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
        'n_train': len(X_train_c),
        'n_val': len(X_test_c),
        'n_ponds_train': df.loc[train_mask, 'pond_id'].nunique(),
        'n_ponds_val': df.loc[test_mask, 'pond_id'].nunique()
    })

df_chrono_metrics = pd.DataFrame(chrono_metrics)
print("\n--- Chronological Holdout Test Performance (2025-2026, N = 2,600) ---")
print(df_chrono_metrics[['model', 'mae', 'rmse', 'r2']].to_string(index=False))

# Combine all metrics and save to CSV
all_metrics_df = pd.concat([df_fold_metrics, df_oof_summary, df_chrono_metrics], ignore_index=True)
metrics_csv_path = os.path.join(METRICS_DIR, 'experiment_1_metrics.csv')
all_metrics_df.to_csv(metrics_csv_path, index=False)
print(f"\nSaved all metrics to {metrics_csv_path}")

print("\n=========================================================================")
print("=== SUBGROUP PERFORMANCE AUDIT: MEASURED VS MISSING TDS/TURBIDITY ===")
print("=========================================================================")
# Evaluate OOF predictions on full dataset partitioned by missingness
subgroup_records = []

# Partition 1: Global OOF by TDS missingness
for tds_status, mask in [('TDS_Measured', df['tds_ppt_is_missing'] == 0), 
                         ('TDS_Missing', df['tds_ppt_is_missing'] == 1)]:
    y_sub = y[mask]
    for m_name in ['Dummy_Mean', 'Dummy_Median', 'Ablation_pH_Temp', 'Random_Forest']:
        p_sub = oof_preds[m_name][mask]
        subgroup_records.append({
            'dataset_split': 'Global_OOF',
            'subgroup': tds_status,
            'model': m_name,
            'n_samples': int(mask.sum()),
            'target_mean': float(y_sub.mean()),
            'mae': float(mean_absolute_error(y_sub, p_sub)),
            'rmse': float(root_mean_squared_error(y_sub, p_sub)),
            'r2': float(r2_score(y_sub, p_sub))
        })

# Partition 2: Global OOF by Turbidity missingness
for turb_status, mask in [('Turbidity_Measured', df['turbidity_cm_is_missing'] == 0), 
                          ('Turbidity_Missing', df['turbidity_cm_is_missing'] == 1)]:
    y_sub = y[mask]
    for m_name in ['Dummy_Mean', 'Dummy_Median', 'Ablation_pH_Temp', 'Random_Forest']:
        p_sub = oof_preds[m_name][mask]
        subgroup_records.append({
            'dataset_split': 'Global_OOF',
            'subgroup': turb_status,
            'model': m_name,
            'n_samples': int(mask.sum()),
            'target_mean': float(y_sub.mean()),
            'mae': float(mean_absolute_error(y_sub, p_sub)),
            'rmse': float(root_mean_squared_error(y_sub, p_sub)),
            'r2': float(r2_score(y_sub, p_sub))
        })

# Partition 3: Chronological Training partition (2021-2024) by TDS missingness
df_train_c = df[train_mask].copy()
y_train_c = df_train_c[target_col].values
preds_train_c = full_pipe_c.predict(df_train_c[all_feature_cols])

for tds_status, sub_mask in [('Train2021_2024_TDS_Measured', df_train_c['tds_ppt_is_missing'] == 0),
                             ('Train2021_2024_TDS_Missing', df_train_c['tds_ppt_is_missing'] == 1)]:
    y_sub = y_train_c[sub_mask]
    p_sub = preds_train_c[sub_mask]
    subgroup_records.append({
        'dataset_split': 'Chrono_Train_InSample',
        'subgroup': tds_status,
        'model': 'Random_Forest',
        'n_samples': int(sub_mask.sum()),
        'target_mean': float(y_sub.mean()),
        'mae': float(mean_absolute_error(y_sub, p_sub)),
        'rmse': float(root_mean_squared_error(y_sub, p_sub)),
        'r2': float(r2_score(y_sub, p_sub))
    })

df_subgroup = pd.DataFrame(subgroup_records)
subgroup_csv_path = os.path.join(METRICS_DIR, 'experiment_1_subgroup_metrics.csv')
df_subgroup.to_csv(subgroup_csv_path, index=False)
print(f"Saved subgroup metrics to {subgroup_csv_path}")
print(df_subgroup[df_subgroup['model'] == 'Random_Forest'][['dataset_split', 'subgroup', 'n_samples', 'mae', 'rmse', 'r2']].to_string(index=False))

print("\n=========================================================================")
print("=== GENERATING EVALUATION PLOTS ===")
print("=========================================================================")

# Plot 1: Actual vs Predicted (GroupKFold OOF)
plt.figure(figsize=(9, 7))
plt.scatter(y, oof_preds['Random_Forest'], alpha=0.35, color='#1f77b4', edgecolors='none', s=25, label='Random Forest (OOF)')
plt.scatter(y, oof_preds['Ablation_pH_Temp'], alpha=0.25, color='#ff7f0e', edgecolors='none', s=15, label='Ablation: pH+Temp Only (OOF)')
max_val = max(y.max(), oof_preds['Random_Forest'].max()) * 1.05
plt.plot([0, max_val], [0, max_val], 'k--', lw=1.5, label='Ideal 1:1 Identity Line')
plt.xlabel('Actual Calculated NH3 (mg/L)', fontsize=12)
plt.ylabel('Predicted NH3 (mg/L)', fontsize=12)
plt.title('Experiment 1: Actual vs. Predicted Un-ionized Ammonia (5-Fold GroupKFold OOF)', fontsize=13, fontweight='bold')
plt.xlim(0, max_val)
plt.ylim(0, max_val)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper left', fontsize=10)
plt.tight_layout()
p1_path = os.path.join(PLOTS_DIR, 'actual_vs_predicted_groupkfold.png')
plt.savefig(p1_path, dpi=300)
plt.close()
print(f"Saved Plot 1 to {p1_path}")

# Plot 2: Residuals Plot (GroupKFold OOF)
residuals_rf = y - oof_preds['Random_Forest']
residuals_ablation = y - oof_preds['Ablation_pH_Temp']

plt.figure(figsize=(9, 7))
plt.scatter(oof_preds['Random_Forest'], residuals_rf, alpha=0.35, color='#2ca02c', edgecolors='none', s=25, label='Random Forest Residuals')
plt.axhline(0, color='red', linestyle='--', lw=1.5, label='Zero Residual Baseline')
plt.xlabel('Predicted Calculated NH3 (mg/L)', fontsize=12)
plt.ylabel('Residual: Actual - Predicted (mg/L)', fontsize=12)
plt.title('Experiment 1: Residuals vs. Fitted Values (5-Fold GroupKFold OOF)', fontsize=13, fontweight='bold')
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper right', fontsize=10)
plt.tight_layout()
p2_path = os.path.join(PLOTS_DIR, 'residuals_groupkfold.png')
plt.savefig(p2_path, dpi=300)
plt.close()
print(f"Saved Plot 2 to {p2_path}")

# Plot 3: Actual vs Predicted (Chronological Test 2025-2026)
plt.figure(figsize=(9, 7))
plt.scatter(y_test_c, chrono_preds['Random_Forest'], alpha=0.35, color='#9467bd', edgecolors='none', s=25, label='Random Forest (Test 2025-2026)')
plt.scatter(y_test_c, chrono_preds['Ablation_pH_Temp'], alpha=0.25, color='#e377c2', edgecolors='none', s=15, label='Ablation: pH+Temp Only')
max_c = max(y_test_c.max(), chrono_preds['Random_Forest'].max()) * 1.05
plt.plot([0, max_c], [0, max_c], 'k--', lw=1.5, label='Ideal 1:1 Identity Line')
plt.xlabel('Actual Calculated NH3 (mg/L)', fontsize=12)
plt.ylabel('Predicted NH3 (mg/L)', fontsize=12)
plt.title('Experiment 1: Chronological Holdout (2025-2026 Test Set, N = 2,600)', fontsize=13, fontweight='bold')
plt.xlim(0, max_c)
plt.ylim(0, max_c)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper left', fontsize=10)
plt.tight_layout()
p3_path = os.path.join(PLOTS_DIR, 'actual_vs_predicted_chronological.png')
plt.savefig(p3_path, dpi=300)
plt.close()
print(f"Saved Plot 3 to {p3_path}")

# Plot 4: Residuals (Chronological Test 2025-2026)
residuals_chrono_rf = y_test_c - chrono_preds['Random_Forest']
plt.figure(figsize=(9, 7))
plt.scatter(chrono_preds['Random_Forest'], residuals_chrono_rf, alpha=0.35, color='#8c564b', edgecolors='none', s=25, label='RF Chrono Test Residuals')
plt.axhline(0, color='red', linestyle='--', lw=1.5, label='Zero Residual Baseline')
plt.xlabel('Predicted Calculated NH3 (mg/L)', fontsize=12)
plt.ylabel('Residual: Actual - Predicted (mg/L)', fontsize=12)
plt.title('Experiment 1: Chronological Test Residuals (2025-2026, N = 2,600)', fontsize=13, fontweight='bold')
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper right', fontsize=10)
plt.tight_layout()
p4_path = os.path.join(PLOTS_DIR, 'residuals_chronological.png')
plt.savefig(p4_path, dpi=300)
plt.close()
print(f"Saved Plot 4 to {p4_path}")

# Plot 5: Feature Importances
# Extract feature names from fitted pipeline
cat_ohe = full_pipe_c.named_steps['preprocessor'].named_transformers_['cat'].named_steps['ohe']
cat_feature_names = list(cat_ohe.get_feature_names_out(categorical_features))
all_transformed_names = continuous_features + indicator_features + cat_feature_names

importances = full_pipe_c.named_steps['regressor'].feature_importances_
fi_df = pd.DataFrame({
    'feature': all_transformed_names,
    'importance': importances
}).sort_values('importance', ascending=True)

# Save feature importances to CSV
fi_csv_path = os.path.join(METRICS_DIR, 'experiment_1_feature_importances.csv')
fi_df.sort_values('importance', ascending=False).to_csv(fi_csv_path, index=False)
print(f"Saved feature importances to {fi_csv_path}")

plt.figure(figsize=(10, 8))
top_fi = fi_df.tail(15)  # Top 15 features
plt.barh(range(len(top_fi)), top_fi['importance'], color='#1f77b4', align='center')
plt.yticks(range(len(top_fi)), top_fi['feature'], fontsize=10)
plt.xlabel('Gini Feature Importance', fontsize=12)
plt.title('Experiment 1: Random Forest Feature Importances (Top 15)', fontsize=13, fontweight='bold')
plt.grid(True, linestyle=':', alpha=0.6, axis='x')
plt.tight_layout()
p5_path = os.path.join(PLOTS_DIR, 'feature_importances.png')
plt.savefig(p5_path, dpi=300)
plt.close()
print(f"Saved Plot 5 to {p5_path}")

print("\n=========================================================================")
print("=== TRAINING SCRIPT COMPLETED SUCCESSFULLY ===")
print("=========================================================================")

