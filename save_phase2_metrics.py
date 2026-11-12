import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    roc_auc_score, average_precision_score, precision_score, recall_score,
    f1_score, accuracy_score, balanced_accuracy_score, confusion_matrix, brier_score_loss
)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

METRICS_DIR = 'experiment_5_do_hypoxia_v1/metrics'
os.makedirs(METRICS_DIR, exist_ok=True)

df_train = pd.read_csv('experiment_5_do_hypoxia_v1/data/train_pairs.csv')
df_test = pd.read_csv('experiment_5_do_hypoxia_v1/data/test_pairs.csv')

num_features = [
    'curr_do', 'curr_ph', 'curr_temp_c', 'curr_turbidity_cm', 'curr_tds_ppt',
    'curr_feed_amount_kg', 'curr_feed_per_acre_kg',
    'curr_stocking_density', 'curr_weight',
    'curr_dead_fish', 'curr_air_gulping', 'curr_tail_splashing',
    'pond_area_acres', 'depth_meters',
    'gap_days', 'curr_time_hour', 'day_of_year', 'month'
]
ind_features = [
    'turbidity_is_missing', 'tds_is_missing', 'feed_is_missing',
    'density_is_missing', 'species_is_missing', 'weight_is_missing',
    'area_is_missing'
]
cat_features = [
    'curr_water_color', 'curr_weather', 'curr_species', 'farm_equipment',
    'feed_type', 'region'
]
feature_cols = num_features + ind_features + cat_features

y_reg_train = df_train['next_do'].values
y_clf_train = df_train['next_hypoxia_3'].values
y_clf2_train = df_train['next_hypoxia_2'].values
curr_do_train = df_train['curr_do'].values
ponds_train = df_train['pond_id'].values

y_reg_test = df_test['next_do'].values
y_clf_test = df_test['next_hypoxia_3'].values
y_clf2_test = df_test['next_hypoxia_2'].values
curr_do_test = df_test['curr_do'].values
ponds_test = df_test['pond_id'].values

def build_preprocessor():
    return ColumnTransformer([
        ('num', Pipeline([('imp', SimpleImputer(strategy='median')), ('scl', StandardScaler())]), num_features),
        ('ind', Pipeline([('imp', SimpleImputer(strategy='constant', fill_value=0.0))]), ind_features),
        ('cat', Pipeline([('imp', SimpleImputer(strategy='constant', fill_value='Missing')), ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), cat_features)
    ])

# 1. TASK A: REGRESSION METRICS TABLE
print("Computing Regression Metrics...")
gkf = GroupKFold(n_splits=5)
reg_models = {
    'Ridge_Regression': Pipeline([('prep', build_preprocessor()), ('reg', Ridge(alpha=10.0, random_state=RANDOM_SEED))]),
    'Random_Forest_Regressor': Pipeline([('prep', build_preprocessor()), ('reg', RandomForestRegressor(n_estimators=100, min_samples_leaf=5, random_state=RANDOM_SEED, n_jobs=-1))]),
    'Gradient_Boosting_Regressor': Pipeline([('prep', build_preprocessor()), ('reg', GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=RANDOM_SEED))])
}

oof_reg = {m: np.zeros(len(df_train)) for m in reg_models.keys()}
oof_reg['Persistence'] = curr_do_train.copy()
oof_reg['Historical_Mean'] = np.zeros(len(df_train))

for t_idx, v_idx in gkf.split(df_train[feature_cols], y_reg_train, groups=ponds_train):
    X_tr, y_tr = df_train[feature_cols].iloc[t_idx], y_reg_train[t_idx]
    X_va, y_va = df_train[feature_cols].iloc[v_idx], y_reg_train[v_idx]
    oof_reg['Historical_Mean'][v_idx] = np.mean(y_tr)
    for m_name, pipe in reg_models.items():
        pipe.fit(X_tr, y_tr)
        oof_reg[m_name][v_idx] = pipe.predict(X_va)

chrono_reg = {
    'Persistence': curr_do_test.copy(),
    'Historical_Mean': np.full_like(y_reg_test, np.mean(y_reg_train))
}
for m_name, pipe in reg_models.items():
    pipe.fit(df_train[feature_cols], y_reg_train)
    chrono_reg[m_name] = pipe.predict(df_test[feature_cols])

pers_gkf_mae = mean_absolute_error(y_reg_train, oof_reg['Persistence'])
pers_test_mae = mean_absolute_error(y_reg_test, chrono_reg['Persistence'])

reg_rows = []
for m_name in ['Persistence', 'Historical_Mean', 'Ridge_Regression', 'Random_Forest_Regressor', 'Gradient_Boosting_Regressor']:
    # GroupKFold
    p_gkf = oof_reg[m_name]
    mae_gkf = mean_absolute_error(y_reg_train, p_gkf)
    rmse_gkf = np.sqrt(mean_squared_error(y_reg_train, p_gkf))
    r2_gkf = r2_score(y_reg_train, p_gkf)
    imp_gkf = (pers_gkf_mae - mae_gkf) / pers_gkf_mae * 100
    
    # Chrono Test
    p_test = chrono_reg[m_name]
    mae_t = mean_absolute_error(y_reg_test, p_test)
    rmse_t = np.sqrt(mean_squared_error(y_reg_test, p_test))
    r2_t = r2_score(y_reg_test, p_test)
    imp_t = (pers_test_mae - mae_t) / pers_test_mae * 100
    
    reg_rows.append({
        'model_name': m_name,
        'gkf_train_mae_mg_l': round(mae_gkf, 4),
        'gkf_train_rmse_mg_l': round(rmse_gkf, 4),
        'gkf_train_r2': round(r2_gkf, 4),
        'gkf_pct_imp_vs_persistence': round(imp_gkf, 2),
        'chrono_test_mae_mg_l': round(mae_t, 4),
        'chrono_test_rmse_mg_l': round(rmse_t, 4),
        'chrono_test_r2': round(r2_t, 4),
        'chrono_test_pct_imp_vs_persistence': round(imp_t, 2),
        'beats_persistence_in_test': bool(imp_t > 0)
    })

df_reg = pd.DataFrame(reg_rows)
df_reg.to_csv(os.path.join(METRICS_DIR, 'phase2_regression_metrics.csv'), index=False)

# 2. TASK B: CLASSIFICATION THRESHOLDS & TEST EVALUATION
print("Computing Classification Metrics & Threshold Tuning...")
clf_models = {
    'Logistic_Regression': Pipeline([('prep', build_preprocessor()), ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=RANDOM_SEED))]),
    'Random_Forest_Classifier': Pipeline([('prep', build_preprocessor()), ('clf', RandomForestClassifier(n_estimators=100, min_samples_leaf=5, class_weight='balanced', random_state=RANDOM_SEED, n_jobs=-1))]),
    'Gradient_Boosting_Classifier': Pipeline([('prep', build_preprocessor()), ('clf', GradientBoostingClassifier(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=RANDOM_SEED))])
}

oof_clf = {m: np.zeros(len(df_train)) for m in clf_models.keys()}
for t_idx, v_idx in gkf.split(df_train[feature_cols], y_clf_train, groups=ponds_train):
    X_tr, y_tr = df_train[feature_cols].iloc[t_idx], y_clf_train[t_idx]
    X_va, y_va = df_train[feature_cols].iloc[v_idx], y_clf_train[v_idx]
    for m_name, pipe in clf_models.items():
        pipe.fit(X_tr, y_tr)
        oof_clf[m_name][v_idx] = pipe.predict_proba(X_va)[:, 1]

# Threshold search on Train OOF
thresh_rows = []
frozen_thresholds = {}
for m_name, probs in oof_clf.items():
    p_grid = np.linspace(0.05, 0.95, 91)
    best_f1 = -1
    best_p_f1 = 0.50
    best_bal = -1
    best_p_bal = 0.50
    rec80_p = 0.50
    
    for p in p_grid:
        preds = (probs >= p).astype(int)
        f = f1_score(y_clf_train, preds, zero_division=0)
        ba = balanced_accuracy_score(y_clf_train, preds)
        rec = recall_score(y_clf_train, preds, zero_division=0)
        prec = precision_score(y_clf_train, preds, zero_division=0)
        
        if f > best_f1:
            best_f1 = f
            best_p_f1 = p
        if ba > best_bal:
            best_bal = ba
            best_p_bal = p
        if rec >= 0.80:
            rec80_p = p
            
    frozen_thresholds[m_name] = {
        'optimal_f1': best_p_f1,
        'balanced_acc': best_p_bal,
        'high_recall': rec80_p
    }
    
    # Evaluate at key points on train OOF
    for p_val, label in [(0.50, 'Default (p=0.50)'), (best_p_f1, f'Max-F1 (p*={best_p_f1:.2f})'), (rec80_p, f'High-Recall>=80% (p*={rec80_p:.2f})')]:
        preds = (probs >= p_val).astype(int)
        cm = confusion_matrix(y_clf_train, preds)
        thresh_rows.append({
            'model_name': m_name,
            'threshold_type': label,
            'threshold_value': round(p_val, 3),
            'train_precision': round(precision_score(y_clf_train, preds, zero_division=0), 4),
            'train_recall': round(recall_score(y_clf_train, preds, zero_division=0), 4),
            'train_f1': round(f1_score(y_clf_train, preds, zero_division=0), 4),
            'train_balanced_accuracy': round(balanced_accuracy_score(y_clf_train, preds), 4),
            'train_tp': int(cm[1,1]),
            'train_fp': int(cm[0,1]),
            'train_fn': int(cm[1,0]),
            'train_tn': int(cm[0,0])
        })

df_thresh = pd.DataFrame(thresh_rows)
df_thresh.to_csv(os.path.join(METRICS_DIR, 'threshold_selection_audit.csv'), index=False)

# Prospective Test Evaluation
chrono_clf_prob = {}
for m_name, pipe in clf_models.items():
    pipe.fit(df_train[feature_cols], y_clf_train)
    chrono_clf_prob[m_name] = pipe.predict_proba(df_test[feature_cols])[:, 1]

test_prev = y_clf_test.mean()
clf_eval_rows = []

# Baselines
pers_prob = (curr_do_test < 3.0).astype(float)
pers_pred = (curr_do_test < 3.0).astype(int)
cm_p = confusion_matrix(y_clf_test, pers_pred)
clf_eval_rows.append({
    'model_name': 'Persistence_Classifier',
    'threshold_used': 'curr_do < 3.0',
    'pr_auc': round(average_precision_score(y_clf_test, pers_prob), 4),
    'no_skill_baseline': round(test_prev, 4),
    'roc_auc': round(roc_auc_score(y_clf_test, pers_prob), 4),
    'precision': round(precision_score(y_clf_test, pers_pred, zero_division=0), 4),
    'recall': round(recall_score(y_clf_test, pers_pred, zero_division=0), 4),
    'f1_score': round(f1_score(y_clf_test, pers_pred, zero_division=0), 4),
    'accuracy': round(accuracy_score(y_clf_test, pers_pred), 4),
    'balanced_accuracy': round(balanced_accuracy_score(y_clf_test, pers_pred), 4),
    'brier_score': round(brier_score_loss(y_clf_test, pers_prob), 4),
    'confusion_matrix': f"TP={cm_p[1,1]},FP={cm_p[0,1]},FN={cm_p[1,0]},TN={cm_p[0,0]}"
})

dummy_pred = np.zeros_like(y_clf_test)
cm_d = confusion_matrix(y_clf_test, dummy_pred)
clf_eval_rows.append({
    'model_name': 'Prior_Prevalence_Dummy',
    'threshold_used': 'N/A (All Zero)',
    'pr_auc': round(test_prev, 4),
    'no_skill_baseline': round(test_prev, 4),
    'roc_auc': 0.5000,
    'precision': 0.0000,
    'recall': 0.0000,
    'f1_score': 0.0000,
    'accuracy': round(accuracy_score(y_clf_test, dummy_pred), 4),
    'balanced_accuracy': 0.5000,
    'brier_score': round(brier_score_loss(y_clf_test, np.full(len(y_clf_test), test_prev)), 4),
    'confusion_matrix': f"TP={cm_d[1,1]},FP={cm_d[0,1]},FN={cm_d[1,0]},TN={cm_d[0,0]}"
})

for m_name in ['Logistic_Regression', 'Random_Forest_Classifier', 'Gradient_Boosting_Classifier']:
    probs = chrono_clf_prob[m_name]
    pr = average_precision_score(y_clf_test, probs)
    roc = roc_auc_score(y_clf_test, probs)
    brier = brier_score_loss(y_clf_test, probs)
    
    # 1. Default threshold (0.50)
    p_def = 0.50
    preds_def = (probs >= p_def).astype(int)
    cm_def = confusion_matrix(y_clf_test, preds_def)
    clf_eval_rows.append({
        'model_name': m_name,
        'threshold_used': 'Default (p=0.50)',
        'pr_auc': round(pr, 4),
        'no_skill_baseline': round(test_prev, 4),
        'roc_auc': round(roc, 4),
        'precision': round(precision_score(y_clf_test, preds_def, zero_division=0), 4),
        'recall': round(recall_score(y_clf_test, preds_def, zero_division=0), 4),
        'f1_score': round(f1_score(y_clf_test, preds_def, zero_division=0), 4),
        'accuracy': round(accuracy_score(y_clf_test, preds_def), 4),
        'balanced_accuracy': round(balanced_accuracy_score(y_clf_test, preds_def), 4),
        'brier_score': round(brier, 4),
        'confusion_matrix': f"TP={cm_def[1,1]},FP={cm_def[0,1]},FN={cm_def[1,0]},TN={cm_def[0,0]}"
    })
    
    # 2. Frozen OOF Max-F1 threshold
    p_opt = frozen_thresholds[m_name]['optimal_f1']
    preds_opt = (probs >= p_opt).astype(int)
    cm_opt = confusion_matrix(y_clf_test, preds_opt)
    clf_eval_rows.append({
        'model_name': m_name,
        'threshold_used': f'Frozen Max-F1 (p*={p_opt:.3f})',
        'pr_auc': round(pr, 4),
        'no_skill_baseline': round(test_prev, 4),
        'roc_auc': round(roc, 4),
        'precision': round(precision_score(y_clf_test, preds_opt, zero_division=0), 4),
        'recall': round(recall_score(y_clf_test, preds_opt, zero_division=0), 4),
        'f1_score': round(f1_score(y_clf_test, preds_opt, zero_division=0), 4),
        'accuracy': round(accuracy_score(y_clf_test, preds_opt), 4),
        'balanced_accuracy': round(balanced_accuracy_score(y_clf_test, preds_opt), 4),
        'brier_score': round(brier, 4),
        'confusion_matrix': f"TP={cm_opt[1,1]},FP={cm_opt[0,1]},FN={cm_opt[1,0]},TN={cm_opt[0,0]}"
    })
    
    # 3. Frozen High-Recall threshold
    p_rec = frozen_thresholds[m_name]['high_recall']
    preds_rec = (probs >= p_rec).astype(int)
    cm_rec = confusion_matrix(y_clf_test, preds_rec)
    clf_eval_rows.append({
        'model_name': m_name,
        'threshold_used': f'Frozen High-Recall (p*={p_rec:.3f})',
        'pr_auc': round(pr, 4),
        'no_skill_baseline': round(test_prev, 4),
        'roc_auc': round(roc, 4),
        'precision': round(precision_score(y_clf_test, preds_rec, zero_division=0), 4),
        'recall': round(recall_score(y_clf_test, preds_rec, zero_division=0), 4),
        'f1_score': round(f1_score(y_clf_test, preds_rec, zero_division=0), 4),
        'accuracy': round(accuracy_score(y_clf_test, preds_rec), 4),
        'balanced_accuracy': round(balanced_accuracy_score(y_clf_test, preds_rec), 4),
        'brier_score': round(brier, 4),
        'confusion_matrix': f"TP={cm_rec[1,1]},FP={cm_rec[0,1]},FN={cm_rec[1,0]},TN={cm_rec[0,0]}"
    })

df_clf_eval = pd.DataFrame(clf_eval_rows)
df_clf_eval.to_csv(os.path.join(METRICS_DIR, 'phase2_classification_metrics.csv'), index=False)

# 3. POND-CLUSTERED BOOTSTRAP ROBUSTNESS TABLE
print("Computing 5,000 Pond-Clustered Bootstrap Metrics...")
unique_test_ponds = np.unique(ponds_test)
n_test_ponds = len(unique_test_ponds)
pond_to_indices = {p: np.where(ponds_test == p)[0] for p in unique_test_ponds}

N_BOOT = 5000
boot_reg = {m: [] for m in ['Historical_Mean', 'Ridge_Regression', 'Random_Forest_Regressor', 'Gradient_Boosting_Regressor']}
boot_prauc = {m: [] for m in ['Logistic_Regression', 'Random_Forest_Classifier', 'Gradient_Boosting_Classifier']}

pers_errs = np.abs(y_reg_test - chrono_reg['Persistence'])
reg_errs = {m: np.abs(y_reg_test - chrono_reg[m]) for m in boot_reg.keys()}

for b in range(N_BOOT):
    boot_ponds = np.random.choice(unique_test_ponds, size=n_test_ponds, replace=True)
    boot_idx = np.concatenate([pond_to_indices[p] for p in boot_ponds])
    
    p_mae_b = np.mean(pers_errs[boot_idx])
    for m in boot_reg.keys():
        m_mae_b = np.mean(reg_errs[m][boot_idx])
        boot_reg[m].append(m_mae_b - p_mae_b)
        
    y_b = y_clf_test[boot_idx]
    if np.sum(y_b) > 0:
        no_skill_b = np.mean(y_b)
        for m in boot_prauc.keys():
            prauc_b = average_precision_score(y_b, chrono_clf_prob[m][boot_idx])
            boot_prauc[m].append(prauc_b - no_skill_b)

boot_rows = []
for m, diffs in boot_reg.items():
    diffs = np.array(diffs)
    ci_l = np.percentile(diffs, 2.5)
    ci_u = np.percentile(diffs, 97.5)
    boot_rows.append({
        'task_type': 'Regression (Delta MAE vs Persistence)',
        'model_name': m,
        'mean_difference': round(float(np.mean(diffs)), 4),
        'median_difference': round(float(np.median(diffs)), 4),
        'ci_lower_95': round(float(ci_l), 4),
        'ci_upper_95': round(float(ci_u), 4),
        'pct_draws_improving_over_baseline': round(float(np.mean(diffs < 0) * 100), 2),
        'ci_spans_zero': bool((ci_l <= 0) and (ci_u >= 0)),
        'statistical_verdict': 'Statistically significantly superior to persistence (95% CI strictly negative)' if ci_u < 0 else ('No significant difference (95% CI spans zero)' if (ci_l <= 0 <= ci_u) else 'Inferior')
    })

for m, diffs in boot_prauc.items():
    diffs = np.array(diffs)
    ci_l = np.percentile(diffs, 2.5)
    ci_u = np.percentile(diffs, 97.5)
    boot_rows.append({
        'task_type': 'Classification (Delta PR-AUC vs No-Skill)',
        'model_name': m,
        'mean_difference': round(float(np.mean(diffs)), 4),
        'median_difference': round(float(np.median(diffs)), 4),
        'ci_lower_95': round(float(ci_l), 4),
        'ci_upper_95': round(float(ci_u), 4),
        'pct_draws_improving_over_baseline': round(float(np.mean(diffs > 0) * 100), 2),
        'ci_spans_zero': bool((ci_l <= 0) and (ci_u >= 0)),
        'statistical_verdict': 'Statistically significantly superior to no-skill (95% CI strictly positive)' if ci_l > 0 else ('No statistically significant difference under cluster-bootstrap (95% CI spans zero)' if (ci_l <= 0 <= ci_u) else 'Inferior')
    })

df_boot = pd.DataFrame(boot_rows)
df_boot.to_csv(os.path.join(METRICS_DIR, 'pond_clustered_bootstrap_results.csv'), index=False)

# 4. SECONDARY SEVERE HYPOXIA (< 2.0 mg/L)
print("Computing Secondary Severe Hypoxia Metrics...")
sec_rows = []
models_sec = {
    'Logistic_Regression': Pipeline([('prep', build_preprocessor()), ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=RANDOM_SEED))]),
    'Random_Forest_Classifier': Pipeline([('prep', build_preprocessor()), ('clf', RandomForestClassifier(n_estimators=100, min_samples_leaf=5, class_weight='balanced', random_state=RANDOM_SEED, n_jobs=-1))]),
    'Gradient_Boosting_Classifier': Pipeline([('prep', build_preprocessor()), ('clf', GradientBoostingClassifier(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=RANDOM_SEED))])
}

pers2_prob = (curr_do_test < 2.0).astype(float)
pers2_pred = (curr_do_test < 2.0).astype(int)
cm_p2 = confusion_matrix(y_clf2_test, pers2_pred)
sec_rows.append({
    'model_name': 'Persistence_Classifier',
    'threshold_used': 'curr_do < 2.0',
    'test_pr_auc': round(average_precision_score(y_clf2_test, pers2_prob), 4),
    'no_skill_baseline': round(y_clf2_test.mean(), 4),
    'test_roc_auc': round(roc_auc_score(y_clf2_test, pers2_prob), 4),
    'test_precision': round(precision_score(y_clf2_test, pers2_pred, zero_division=0), 4),
    'test_recall': round(recall_score(y_clf2_test, pers2_pred, zero_division=0), 4),
    'test_f1': round(f1_score(y_clf2_test, pers2_pred, zero_division=0), 4),
    'confusion_matrix': f"TP={cm_p2[1,1]},FP={cm_p2[0,1]},FN={cm_p2[1,0]},TN={cm_p2[0,0]}"
})

for m_name, pipe in models_sec.items():
    pipe.fit(df_train[feature_cols], y_clf2_train)
    probs = pipe.predict_proba(df_test[feature_cols])[:, 1]
    pr = average_precision_score(y_clf2_test, probs)
    roc = roc_auc_score(y_clf2_test, probs)
    
    # Rare event cutoff (p=0.10)
    preds = (probs >= 0.10).astype(int)
    cm = confusion_matrix(y_clf2_test, preds)
    sec_rows.append({
        'model_name': m_name,
        'threshold_used': 'Risk Threshold (p=0.10)',
        'test_pr_auc': round(pr, 4),
        'no_skill_baseline': round(y_clf2_test.mean(), 4),
        'test_roc_auc': round(roc, 4),
        'test_precision': round(precision_score(y_clf2_test, preds, zero_division=0), 4),
        'test_recall': round(recall_score(y_clf2_test, preds, zero_division=0), 4),
        'test_f1': round(f1_score(y_clf2_test, preds, zero_division=0), 4),
        'confusion_matrix': f"TP={cm[1,1]},FP={cm[0,1]},FN={cm[1,0]},TN={cm[0,0]}"
    })

df_sec = pd.DataFrame(sec_rows)
df_sec.to_csv(os.path.join(METRICS_DIR, 'secondary_severe_hypoxia_metrics.csv'), index=False)

print("\nAll Phase 2 metrics successfully generated and saved to experiment_5_do_hypoxia_v1/metrics/")

