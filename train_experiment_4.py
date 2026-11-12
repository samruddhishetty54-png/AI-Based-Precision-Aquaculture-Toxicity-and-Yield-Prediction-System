import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Set random seed
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

OUTPUT_DIR = 'experiment_4_next_visit_weight_v1'
os.makedirs(OUTPUT_DIR, exist_ok=True)
METRICS_DIR = os.path.join(OUTPUT_DIR, 'metrics')
os.makedirs(METRICS_DIR, exist_ok=True)
PLOTS_DIR = os.path.join(OUTPUT_DIR, 'plots')
os.makedirs(PLOTS_DIR, exist_ok=True)

print("=" * 80)
print("EXPERIMENT 4: NEXT-VISIT AVERAGE FISH WEIGHT PREDICTION")
print("Task: Forecast average fish body weight (grams) at next routine farm visit (t+1)")
print("Output Directory:", OUTPUT_DIR)
print("=" * 80)

# =========================================================================
# PHASE 1: BUILD TEMPORAL PAIR DATASET
# =========================================================================
print("\n[Phase 1] Loading raw tables and constructing temporal observation pairs...")

df_wq = pd.read_csv('dataset/water_quality.csv', encoding='utf-8')
df_en = pd.read_csv('processed_data_v2/enrolled_ponds_v2.csv', encoding='utf-8')

# Ensure datetimes are parsed
df_wq['datetime'] = pd.to_datetime(df_wq['Date of data collection'] + ' ' + df_wq['Time of data collection'], errors='coerce')
df_wq['date'] = df_wq['datetime'].dt.date

# Filter to records where Weight is measured
df_w = df_wq[df_wq['Weight'].notna()].copy()
df_w = df_w.sort_values(['pond_id', 'datetime']).reset_index(drop=True)

# Prepare enrolled pond mapping (point-in-time latest profile)
df_en_sorted = df_en.sort_values(by=['pond_id', 'profile_date']).groupby('pond_id').last().reset_index()
en_dict = df_en_sorted.set_index('pond_id')[['Pond area in acres', 'Depth in meters', 'Feed type', 'profile_date']].to_dict('index')

# Daily consolidation: for each pond and visit date, consolidate morning nadir water quality, feed, and weight
daily_records = []
for (pond, v_date), grp in df_w.groupby(['pond_id', 'date']):
    morn = grp[grp['Type'] == 'Morning']
    rec = morn.iloc[0] if len(morn) > 0 else grp.iloc[0]
    
    feed_val = grp['Feed amount (kg)'].max() # preserves morning feeding
    p_info = en_dict.get(pond, {})
    
    pond_area = p_info.get('Pond area in acres', np.nan)
    feed_per_acre = feed_val / pond_area if (pd.notna(feed_val) and pd.notna(pond_area) and pond_area > 0) else np.nan
    
    # Check Temp column name
    temp_val = rec.get('Temp (in \ufffdC)', rec.get('Temp (in °C)', np.nan))
    
    daily_records.append({
        'pond_id': pond,
        'date': v_date,
        'datetime': rec['datetime'],
        'weight_g': float(rec['Weight']),
        'feed_amount_kg': float(feed_val) if pd.notna(feed_val) else np.nan,
        'feed_per_acre_kg': float(feed_per_acre) if pd.notna(feed_per_acre) else np.nan,
        'do_mg_l': float(rec['DO (mg/L)']) if pd.notna(rec['DO (mg/L)']) else np.nan,
        'ph': float(rec['pH']) if pd.notna(rec['pH']) else np.nan,
        'temp_c': float(temp_val) if pd.notna(temp_val) else np.nan,
        'stocking_density_per_acre': float(rec['Stocking density (per acre)']) if pd.notna(rec['Stocking density (per acre)']) else np.nan,
        'species': str(rec['Species']) if pd.notna(rec['Species']) else 'Missing',
        'weather': str(rec['Weather']) if pd.notna(rec['Weather']) else 'Missing',
        'region': str(rec['region']) if pd.notna(rec['region']) else 'Missing',
        'dead_fish_count': float(grp['Dead fish'].sum()) if grp['Dead fish'].notna().any() else 0.0,
        'air_gulping_count': float(grp['Individuals air gulping'].max()) if grp['Individuals air gulping'].notna().any() else 0.0,
        'tail_splashing_count': float(grp['Individuals tail splashing'].max()) if grp['Individuals tail splashing'].notna().any() else 0.0,
        'pond_area_acres': float(pond_area) if pd.notna(pond_area) else np.nan,
        'depth_meters': float(p_info.get('Depth in meters', np.nan)),
        'feed_type': str(p_info.get('Feed type', 'Missing'))
    })

df_daily = pd.DataFrame(daily_records).sort_values(['pond_id', 'datetime']).reset_index(drop=True)

# Build consecutive pairs with 3 <= gap_days <= 45
pairs = []
exclusion_counts = {
    'total_consecutive_transitions': 0,
    'excluded_gap_too_short_under_3d': 0,
    'excluded_gap_too_long_over_45d': 0,
    'valid_pairs_kept': 0
}

for pond, grp in df_daily.groupby('pond_id'):
    grp = grp.sort_values('datetime').reset_index(drop=True)
    for i in range(len(grp) - 1):
        c = grp.iloc[i]
        n = grp.iloc[i+1]
        gap_days = (n['datetime'] - c['datetime']).total_seconds() / (24 * 3600)
        exclusion_counts['total_consecutive_transitions'] += 1
        
        if gap_days < 3.0:
            exclusion_counts['excluded_gap_too_short_under_3d'] += 1
            continue
        elif gap_days > 45.0:
            exclusion_counts['excluded_gap_too_long_over_45d'] += 1
            continue
            
        dw = n['weight_g'] - c['weight_g']
        adg = dw / gap_days
        
        pairs.append({
            'pond_id': pond,
            'curr_datetime': c['datetime'],
            'next_datetime': n['datetime'],
            'gap_days': round(gap_days, 4),
            'curr_weight': c['weight_g'],
            'next_weight': n['weight_g'],
            'weight_change_g': round(dw, 2),
            'average_daily_gain_g': round(adg, 4),
            'curr_feed_amount_kg': c['feed_amount_kg'],
            'curr_feed_per_acre_kg': c['feed_per_acre_kg'],
            'curr_do_mg_l': c['do_mg_l'],
            'curr_ph': c['ph'],
            'curr_temp_c': c['temp_c'],
            'stocking_density_per_acre': c['stocking_density_per_acre'],
            'species': c['species'],
            'weather': c['weather'],
            'region': c['region'],
            'dead_fish_count': c['dead_fish_count'],
            'air_gulping_count': c['air_gulping_count'],
            'tail_splashing_count': c['tail_splashing_count'],
            'pond_area_acres': c['pond_area_acres'],
            'depth_meters': c['depth_meters'],
            'feed_type': c['feed_type'],
            'feed_is_missing': float(np.isnan(c['feed_amount_kg'])),
            'area_is_missing': float(np.isnan(c['pond_area_acres'])),
            'density_is_missing': float(np.isnan(c['stocking_density_per_acre']))
        })
        exclusion_counts['valid_pairs_kept'] += 1

df_pairs = pd.DataFrame(pairs)
print(f"Total transitions evaluated: {exclusion_counts['total_consecutive_transitions']}")
print(f"Excluded gap < 3 days: {exclusion_counts['excluded_gap_too_short_under_3d']}")
print(f"Excluded gap > 45 days: {exclusion_counts['excluded_gap_too_long_over_45d']}")
print(f"Valid pairs constructed: {len(df_pairs)} across {df_pairs['pond_id'].nunique()} unique ponds")

# =========================================================================
# PHASE 2: SUSPICIOUS WEIGHT CHANGES & DATA QUALITY FLAGS
# =========================================================================
print("\n[Phase 2] Flagging suspicious weight changes...")

df_pairs['flag_negative_growth'] = (df_pairs['weight_change_g'] < 0).astype(int)
df_pairs['flag_major_weight_loss'] = ((df_pairs['weight_change_g'] <= -100) | (df_pairs['average_daily_gain_g'] < -5.0)).astype(int)
df_pairs['flag_minor_weight_loss'] = ((df_pairs['weight_change_g'] < 0) & (df_pairs['flag_major_weight_loss'] == 0)).astype(int)
df_pairs['flag_zero_growth'] = (df_pairs['weight_change_g'] == 0).astype(int)
df_pairs['flag_normal_positive_growth'] = ((df_pairs['weight_change_g'] > 0) & (df_pairs['average_daily_gain_g'] <= 10.0)).astype(int)
df_pairs['flag_high_positive_growth'] = ((df_pairs['average_daily_gain_g'] > 10.0) & (df_pairs['average_daily_gain_g'] <= 20.0)).astype(int)
df_pairs['flag_extreme_positive_growth'] = ((df_pairs['average_daily_gain_g'] > 20.0) | (df_pairs['weight_change_g'] > 800)).astype(int)

# Composite suspicious flag: major weight loss (partial harvest/restock) OR extreme biologically impossible positive growth
df_pairs['is_suspicious_growth'] = (
    (df_pairs['flag_major_weight_loss'] == 1) | 
    (df_pairs['flag_extreme_positive_growth'] == 1)
).astype(int)

print("Quality breakdown across all 2,497 pairs:")
print(f"  Normal Positive Growth (ADG <= 10 g/day): {df_pairs['flag_normal_positive_growth'].sum()} ({df_pairs['flag_normal_positive_growth'].mean()*100:.2f}%)")
print(f"  Zero Growth (coarse rounding bins): {df_pairs['flag_zero_growth'].sum()} ({df_pairs['flag_zero_growth'].mean()*100:.2f}%)")
print(f"  Minor Weight Loss (-100g < delta < 0g): {df_pairs['flag_minor_weight_loss'].sum()} ({df_pairs['flag_minor_weight_loss'].mean()*100:.2f}%)")
print(f"  High Positive Growth (10 < ADG <= 20 g/day): {df_pairs['flag_high_positive_growth'].sum()} ({df_pairs['flag_high_positive_growth'].mean()*100:.2f}%)")
print(f"  Major Weight Loss (delta <= -100g, harvest/restock): {df_pairs['flag_major_weight_loss'].sum()} ({df_pairs['flag_major_weight_loss'].mean()*100:.2f}%)")
print(f"  Extreme Positive Growth (ADG > 20 g/day or delta > 800g): {df_pairs['flag_extreme_positive_growth'].sum()} ({df_pairs['flag_extreme_positive_growth'].mean()*100:.2f}%)")
print(f"  Total Flagged as Suspicious: {df_pairs['is_suspicious_growth'].sum()} ({df_pairs['is_suspicious_growth'].mean()*100:.2f}%)")
print(f"  Total Plausible / Clean: {(df_pairs['is_suspicious_growth'] == 0).sum()} ({(df_pairs['is_suspicious_growth'] == 0).mean()*100:.2f}%)")

# Save Deliverable 1: temporal_growth_dataset.csv
csv_dataset_path = os.path.join(OUTPUT_DIR, 'temporal_growth_dataset.csv')
df_pairs.to_csv(csv_dataset_path, index=False)
print(f"Saved {csv_dataset_path}")

# Save Deliverable 2: growth_data_quality_report.csv
quality_summary_records = [
    {'metric_name': 'Total Evaluated Consecutive Transitions', 'value': exclusion_counts['total_consecutive_transitions'], 'unit': 'count', 'interpretation': 'Total adjacent pond observations in daily consolidated dataset'},
    {'metric_name': 'Excluded Gap Under 3 Days', 'value': exclusion_counts['excluded_gap_too_short_under_3d'], 'unit': 'count', 'interpretation': 'Revisits within < 72h; excluded to prevent sub-revisit noise'},
    {'metric_name': 'Excluded Gap Over 45 Days', 'value': exclusion_counts['excluded_gap_too_long_over_45d'], 'unit': 'count', 'interpretation': 'Gaps > 45 days; excluded as broken production cycles'},
    {'metric_name': 'Total Valid Temporal Pairs', 'value': len(df_pairs), 'unit': 'count', 'interpretation': 'Full modeling pair dataset (3 <= gap <= 45 days)'},
    {'metric_name': 'Unique Ponds Represented', 'value': df_pairs['pond_id'].nunique(), 'unit': 'count', 'interpretation': 'Unique farming ponds with valid revisit pairs'},
    {'metric_name': 'Mean Revisit Gap', 'value': round(df_pairs['gap_days'].mean(), 2), 'unit': 'days', 'interpretation': 'Average scheduled farm inspection interval'},
    {'metric_name': 'Median Revisit Gap', 'value': round(df_pairs['gap_days'].median(), 2), 'unit': 'days', 'interpretation': 'Median scheduled farm inspection interval'},
    {'metric_name': 'Mean Current Body Weight', 'value': round(df_pairs['curr_weight'].mean(), 2), 'unit': 'grams', 'interpretation': 'Average initial fish body weight at visit t'},
    {'metric_name': 'Mean Next Body Weight', 'value': round(df_pairs['next_weight'].mean(), 2), 'unit': 'grams', 'interpretation': 'Average subsequent fish body weight at visit t+1 (target)'},
    {'metric_name': 'Mean Observed Weight Change', 'value': round(df_pairs['weight_change_g'].mean(), 2), 'unit': 'grams', 'interpretation': 'Average somatic growth over revisit interval'},
    {'metric_name': 'Mean Average Daily Gain (ADG)', 'value': round(df_pairs['average_daily_gain_g'].mean(), 2), 'unit': 'g/day', 'interpretation': 'Empirical daily growth rate matching commercial carp bioenergetics'},
    {'metric_name': 'Normal Positive Growth Pairs (ADG <= 10)', 'value': int(df_pairs['flag_normal_positive_growth'].sum()), 'unit': 'count', 'interpretation': 'Biologically standard growth events (55.19%)'},
    {'metric_name': 'Zero Weight Change Pairs (Delta = 0)', 'value': int(df_pairs['flag_zero_growth'].sum()), 'unit': 'count', 'interpretation': 'Coarse rounding to 25/50/100g bins by field officers (34.40%)'},
    {'metric_name': 'Minor Weight Loss Pairs (-100 < Delta < 0)', 'value': int(df_pairs['flag_minor_weight_loss'].sum()), 'unit': 'count', 'interpretation': 'Cast-net sampling variation across heterogeneous pond cohorts (0.88%)'},
    {'metric_name': 'High Positive Growth (10 < ADG <= 20)', 'value': int(df_pairs['flag_high_positive_growth'].sum()), 'unit': 'count', 'interpretation': 'Accelerated juvenile growth or warm-water metabolic surges (4.21%)'},
    {'metric_name': 'Major Weight Loss Pairs (Delta <= -100)', 'value': int(df_pairs['flag_major_weight_loss'].sum()), 'unit': 'count', 'interpretation': 'Partial harvest thinning or cycle turnaround restocking (4.77%)'},
    {'metric_name': 'Extreme Positive Growth (ADG > 20 or Delta > 800)', 'value': int(df_pairs['flag_extreme_positive_growth'].sum()), 'unit': 'count', 'interpretation': 'Biologically impossible single-cohort jumps; measurement/species error (0.56%)'},
    {'metric_name': 'Total Suspicious Pairs Flagged', 'value': int(df_pairs['is_suspicious_growth'].sum()), 'unit': 'count', 'interpretation': 'Combined major weight loss and extreme positive growth anomalies (5.33%)'},
    {'metric_name': 'Plausible / Clean Pairs', 'value': int((df_pairs['is_suspicious_growth'] == 0).sum()), 'unit': 'count', 'interpretation': 'Clean biological growth trajectory subset for sensitivity benchmarking (94.67%)'}
]
df_quality_summary = pd.DataFrame(quality_summary_records)
csv_qual_summary_path = os.path.join(OUTPUT_DIR, 'growth_data_quality_report.csv')
df_quality_summary.to_csv(csv_qual_summary_path, index=False)
print(f"Saved {csv_qual_summary_path}")

# =========================================================================
# PHASE 3: FEATURE ENGINEERING & INVENTORY
# =========================================================================
print("\n[Phase 3] Configuring feature pipelines and anti-leakage audit...")

feature_cols = [
    'curr_weight', 'gap_days',
    'curr_feed_amount_kg', 'curr_feed_per_acre_kg',
    'stocking_density_per_acre', 'pond_area_acres', 'depth_meters',
    'curr_do_mg_l', 'curr_ph', 'curr_temp_c',
    'dead_fish_count', 'air_gulping_count', 'tail_splashing_count',
    'feed_is_missing', 'area_is_missing', 'density_is_missing',
    'species', 'weather', 'region', 'feed_type'
]

num_features = [
    'curr_weight', 'gap_days',
    'curr_feed_amount_kg', 'curr_feed_per_acre_kg',
    'stocking_density_per_acre', 'pond_area_acres', 'depth_meters',
    'curr_do_mg_l', 'curr_ph', 'curr_temp_c',
    'dead_fish_count', 'air_gulping_count', 'tail_splashing_count'
]
ind_features = ['feed_is_missing', 'area_is_missing', 'density_is_missing']
cat_features = ['species', 'weather', 'region', 'feed_type']

# Save Deliverable 3: feature_availability_audit.csv
feat_audit_records = [
    {'feature_name': 'curr_weight', 'timing': 'Visit t', 'type': 'Continuous (grams)', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Mandatory initial biological state variable; anchors the somatic growth curve.'},
    {'feature_name': 'gap_days', 'timing': 'Known at visit t', 'type': 'Continuous (days)', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Elapsed duration (3-45 days) over which biomass accumulation occurs.'},
    {'feature_name': 'curr_feed_amount_kg', 'timing': 'Visit t', 'type': 'Continuous (kg)', 'missing_pct': round(df_pairs['curr_feed_amount_kg'].isna().mean()*100, 2), 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Daily supplementary feed applied at visit t; primary somatic energy driver.'},
    {'feature_name': 'curr_feed_per_acre_kg', 'timing': 'Visit t', 'type': 'Continuous (kg/acre)', 'missing_pct': round(df_pairs['curr_feed_per_acre_kg'].isna().mean()*100, 2), 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Nutritional density normalized by pond water surface area.'},
    {'feature_name': 'stocking_density_per_acre', 'timing': 'Profile / Visit t', 'type': 'Continuous (count/acre)', 'missing_pct': round(df_pairs['stocking_density_per_acre'].isna().mean()*100, 2), 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Biological crowding covariate governing competition and carrying capacity.'},
    {'feature_name': 'pond_area_acres', 'timing': 'Pond Profile', 'type': 'Continuous (acres)', 'missing_pct': round(df_pairs['pond_area_acres'].isna().mean()*100, 2), 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Total water surface area governing pond ecosystem scale.'},
    {'feature_name': 'depth_meters', 'timing': 'Pond Profile', 'type': 'Continuous (m)', 'missing_pct': round(df_pairs['depth_meters'].isna().mean()*100, 2), 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Operating water column depth modulating thermal stability and benthic stratification.'},
    {'feature_name': 'curr_do_mg_l', 'timing': 'Visit t', 'type': 'Continuous (mg/L)', 'missing_pct': round(df_pairs['curr_do_mg_l'].isna().mean()*100, 2), 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Morning nadir dissolved oxygen driving metabolic assimilation and feed conversion.'},
    {'feature_name': 'curr_ph', 'timing': 'Visit t', 'type': 'Continuous (pH)', 'missing_pct': round(df_pairs['curr_ph'].isna().mean()*100, 2), 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Water pH reflecting carbonate buffer and physiological stress.'},
    {'feature_name': 'curr_temp_c', 'timing': 'Visit t', 'type': 'Continuous (C)', 'missing_pct': round(df_pairs['curr_temp_c'].isna().mean()*100, 2), 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Water temperature directly governing ectothermic metabolic kinetics.'},
    {'feature_name': 'dead_fish_count', 'timing': 'Visit t', 'type': 'Continuous (count)', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Acute mortality indicator at visit t reflecting health crisis.'},
    {'feature_name': 'air_gulping_count', 'timing': 'Visit t', 'type': 'Continuous (count)', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Hypoxic behavioral distress indicator at visit t.'},
    {'feature_name': 'tail_splashing_count', 'timing': 'Visit t', 'type': 'Continuous (count)', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Agitation and parasitic/water stress indicator at visit t.'},
    {'feature_name': 'feed_is_missing', 'timing': 'Visit t', 'type': 'Binary flag', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Missingness indicator preserving pattern of missing feed records.'},
    {'feature_name': 'area_is_missing', 'timing': 'Pond Profile', 'type': 'Binary flag', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Missingness indicator for unrecorded pond acreage.'},
    {'feature_name': 'density_is_missing', 'timing': 'Profile / Visit t', 'type': 'Binary flag', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Missingness indicator for unrecorded stocking density.'},
    {'feature_name': 'species', 'timing': 'Pond Profile', 'type': 'Categorical', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Cultured species mix (Catla, Rohu, Roopchand polyculture).'},
    {'feature_name': 'weather', 'timing': 'Visit t', 'type': 'Categorical', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Meteorological condition (Sunny, Cloudy, Rainy, Foggy).'},
    {'feature_name': 'region', 'timing': 'Metadata', 'type': 'Categorical', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Farming district baseline (Eluru vs Nellore).'},
    {'feature_name': 'feed_type', 'timing': 'Pond Profile', 'type': 'Categorical', 'missing_pct': 0.0, 'status': 'SELECTED', 'leakage_risk': 'NONE', 'rationale': 'Physical feed type (floating pelleted feed, mash, etc.).'},
    {'feature_name': 'next_weight', 'timing': 'Visit t+1', 'type': 'Continuous (grams)', 'missing_pct': 0.0, 'status': 'TARGET (EXCLUDED FROM FEATURES)', 'leakage_risk': 'TARGET VARIABLE', 'rationale': 'Future average fish weight to be predicted; strictly excluded from feature matrix.'},
    {'feature_name': 'weight_change_g', 'timing': 'Derived t+1', 'type': 'Continuous (grams)', 'missing_pct': 0.0, 'status': 'EXCLUDED (FUTURE TARGET DERIVATIVE)', 'leakage_risk': 'DIRECT TARGET LEAKAGE', 'rationale': 'Target derivative (next_weight - curr_weight); barred from features.'},
    {'feature_name': 'average_daily_gain_g', 'timing': 'Derived t+1', 'type': 'Continuous (g/day)', 'missing_pct': 0.0, 'status': 'EXCLUDED (FUTURE TARGET DERIVATIVE)', 'leakage_risk': 'DIRECT TARGET LEAKAGE', 'rationale': 'Target derivative; barred from features.'},
    {'feature_name': 'next_datetime', 'timing': 'Visit t+1', 'type': 'Timestamp', 'missing_pct': 0.0, 'status': 'EXCLUDED (FUTURE METADATA)', 'leakage_risk': 'FUTURE LEAKAGE', 'rationale': 'Future visit timestamp; barred from features.'},
    {'feature_name': 'curr_datetime', 'timing': 'Visit t', 'type': 'Timestamp', 'missing_pct': 0.0, 'status': 'EXCLUDED (CHRONO SPLIT ONLY)', 'leakage_risk': 'TEMPORAL PARTITION KEY', 'rationale': 'Visit timestamp used solely for chronological train/test partitioning.'},
    {'feature_name': 'pond_id', 'timing': 'Metadata', 'type': 'Identifier', 'missing_pct': 0.0, 'status': 'EXCLUDED (GROUP KEY ONLY)', 'leakage_risk': 'SPATIAL LEAKAGE IF USED AS PREDICTOR', 'rationale': 'Pond identifier used strictly for GroupKFold cross-validation grouping; barred from feature matrix.'}
]
df_feat_audit = pd.DataFrame(feat_audit_records)
csv_feat_audit_path = os.path.join(OUTPUT_DIR, 'feature_availability_audit.csv')
df_feat_audit.to_csv(csv_feat_audit_path, index=False)
print(f"Saved {csv_feat_audit_path}")

# Pipeline builder
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
    return {
        'Linear_Regression': Pipeline([('prep', build_preprocessor()), ('reg', Ridge(alpha=1.0, random_state=RANDOM_SEED))]),
        'Random_Forest': Pipeline([('prep', build_preprocessor()), ('reg', RandomForestRegressor(n_estimators=100, min_samples_leaf=5, random_state=RANDOM_SEED, n_jobs=-1))]),
        'Gradient_Boosting': Pipeline([('prep', build_preprocessor()), ('reg', GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=RANDOM_SEED))])
    }

# =========================================================================
# PHASE 4 & 5: VALIDATION PROTOCOLS & MODEL BENCHMARKING
# =========================================================================
print("\n[Phase 4 & 5] Executing Validation Protocols across Regimes...")

# We benchmark under two data regimes:
# Regime 1: All Pairs (N = 2,497)
# Regime 2: Clean / Plausible Pairs (N = 2,364; excluding is_suspicious_growth == 1)

regimes = [
    ('All_Pairs', df_pairs),
    ('Clean_Plausible_Pairs', df_pairs[df_pairs['is_suspicious_growth'] == 0].reset_index(drop=True))
]

all_gkf_records = []
all_chrono_records = []
all_baseline_records = []

for reg_name, df_subset in regimes:
    print(f"\n=======================================================")
    print(f"EVALUATING REGIME: {reg_name} (N = {len(df_subset)})")
    print(f"=======================================================")
    
    X = df_subset[feature_cols]
    y = df_subset['next_weight'].values
    curr_w = df_subset['curr_weight'].values
    ponds = df_subset['pond_id'].values
    
    # ---------------------------------------------------------------------
    # PROTOCOL A: 5-FOLD GROUPKFOLD BY POND_ID
    # ---------------------------------------------------------------------
    gkf = GroupKFold(n_splits=5)
    
    # Track out-of-fold predictions
    oof_preds = {
        'Persistence': curr_w.copy(),
        'Mean_Predictor': np.zeros(len(df_subset)),
        'Linear_Regression': np.zeros(len(df_subset)),
        'Random_Forest': np.zeros(len(df_subset)),
        'Gradient_Boosting': np.zeros(len(df_subset))
    }
    
    fold_metrics = {m: [] for m in oof_preds.keys()}
    
    for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=ponds)):
        X_train, y_train = X.iloc[train_idx], y[train_idx]
        X_val, y_val = X.iloc[val_idx], y[val_idx]
        curr_val = curr_w[val_idx]
        
        # 1. Persistence
        mae_pers = mean_absolute_error(y_val, curr_val)
        rmse_pers = np.sqrt(mean_squared_error(y_val, curr_val))
        r2_pers = r2_score(y_val, curr_val)
        fold_metrics['Persistence'].append((mae_pers, rmse_pers, r2_pers))
        
        # 2. Mean Predictor
        mean_pred_val = np.mean(y_train)
        oof_preds['Mean_Predictor'][val_idx] = mean_pred_val
        mae_mean = mean_absolute_error(y_val, np.full_like(y_val, mean_pred_val))
        rmse_mean = np.sqrt(mean_squared_error(y_val, np.full_like(y_val, mean_pred_val)))
        r2_mean = r2_score(y_val, np.full_like(y_val, mean_pred_val))
        fold_metrics['Mean_Predictor'].append((mae_mean, rmse_mean, r2_mean))
        
        # 3, 4, 5. ML Models
        models = build_models()
        for m_name, pipe in models.items():
            pipe.fit(X_train, y_train)
            pred_val = pipe.predict(X_val)
            oof_preds[m_name][val_idx] = pred_val
            
            mae_m = mean_absolute_error(y_val, pred_val)
            rmse_m = np.sqrt(mean_squared_error(y_val, pred_val))
            r2_m = r2_score(y_val, pred_val)
            fold_metrics[m_name].append((mae_m, rmse_m, r2_m))
            
    # Calculate pooled OOF metrics
    pers_mae = mean_absolute_error(y, oof_preds['Persistence'])
    pers_rmse = np.sqrt(mean_squared_error(y, oof_preds['Persistence']))
    pers_r2 = r2_score(y, oof_preds['Persistence'])
    
    for m_name, preds_arr in oof_preds.items():
        mae = mean_absolute_error(y, preds_arr)
        rmse = np.sqrt(mean_squared_error(y, preds_arr))
        r2 = r2_score(y, preds_arr)
        
        delta_mae = mae - pers_mae
        pct_imp = (pers_mae - mae) / pers_mae * 100
        
        f_maes = [f[0] for f in fold_metrics[m_name]]
        f_rmses = [f[1] for f in fold_metrics[m_name]]
        f_r2s = [f[2] for f in fold_metrics[m_name]]
        
        all_gkf_records.append({
            'regime': reg_name,
            'model_name': m_name,
            'pooled_oof_mae_g': round(mae, 2),
            'pooled_oof_rmse_g': round(rmse, 2),
            'pooled_oof_r2': round(r2, 4),
            'delta_mae_vs_persistence_g': round(delta_mae, 2),
            'pct_improvement_vs_persistence': round(pct_imp, 2),
            'fold_mean_mae_g': round(float(np.mean(f_maes)), 2),
            'fold_std_mae_g': round(float(np.std(f_maes)), 2),
            'fold_mean_rmse_g': round(float(np.mean(f_rmses)), 2),
            'fold_std_rmse_g': round(float(np.std(f_rmses)), 2),
            'fold_mean_r2': round(float(np.mean(f_r2s)), 4),
            'fold_std_r2': round(float(np.std(f_r2s)), 4)
        })

    # ---------------------------------------------------------------------
    # PROTOCOL B: STRICT CHRONOLOGICAL VALIDATION
    # ---------------------------------------------------------------------
    cutoff = pd.to_datetime('2025-01-01 00:00:00')
    train_mask = (df_subset['curr_datetime'] < cutoff) & (df_subset['next_datetime'] < cutoff)
    cross_mask = (df_subset['curr_datetime'] < cutoff) & (df_subset['next_datetime'] >= cutoff)
    test_mask = (df_subset['curr_datetime'] >= cutoff) & (df_subset['next_datetime'] >= cutoff)
    
    df_train = df_subset[train_mask].copy().reset_index(drop=True)
    df_cross = df_subset[cross_mask].copy().reset_index(drop=True)
    df_test = df_subset[test_mask].copy().reset_index(drop=True)
    
    print(f"\nChronological Split for {reg_name}:")
    print(f"  Training pairs (both < 2025-01-01): N={len(df_train)}")
    print(f"  Cross-cutoff pairs (excluded): N={len(df_cross)}")
    print(f"  Testing pairs (both >= 2025-01-01): N={len(df_test)}")
    
    X_train_c = df_train[feature_cols]
    y_train_c = df_train['next_weight'].values
    
    X_test_c = df_test[feature_cols]
    y_test_c = df_test['next_weight'].values
    curr_test_c = df_test['curr_weight'].values
    
    # 1. Persistence on Test
    test_pers_mae = mean_absolute_error(y_test_c, curr_test_c)
    test_pers_rmse = np.sqrt(mean_squared_error(y_test_c, curr_test_c))
    test_pers_r2 = r2_score(y_test_c, curr_test_c)
    
    chrono_preds = {'Persistence': curr_test_c}
    
    # 2. Mean Predictor on Test
    train_mean_val = np.mean(y_train_c)
    mean_preds = np.full_like(y_test_c, train_mean_val)
    chrono_preds['Mean_Predictor'] = mean_preds
    
    # 3, 4, 5. ML Models fitted strictly on train
    models_c = build_models()
    for m_name, pipe in models_c.items():
        pipe.fit(X_train_c, y_train_c)
        pred_test = pipe.predict(X_test_c)
        chrono_preds[m_name] = pred_test
        
    for m_name, p_arr in chrono_preds.items():
        mae_c = mean_absolute_error(y_test_c, p_arr)
        rmse_c = np.sqrt(mean_squared_error(y_test_c, p_arr))
        r2_c = r2_score(y_test_c, p_arr)
        
        delta_c = mae_c - test_pers_mae
        pct_imp_c = (test_pers_mae - mae_c) / test_pers_mae * 100
        
        all_chrono_records.append({
            'regime': reg_name,
            'model_name': m_name,
            'train_pairs_count': len(df_train),
            'cross_pairs_excluded': len(df_cross),
            'test_pairs_count': len(df_test),
            'test_mae_g': round(mae_c, 2),
            'test_rmse_g': round(rmse_c, 2),
            'test_r2': round(r2_c, 4),
            'delta_mae_vs_persistence_g': round(delta_c, 2),
            'pct_improvement_vs_persistence': round(pct_imp_c, 2),
            'persistence_test_mae_g': round(test_pers_mae, 2),
            'persistence_test_rmse_g': round(test_pers_rmse, 2),
            'persistence_test_r2': round(test_pers_r2, 4)
        })
        
    # Baseline comparison summary
    for m_name in ['Persistence', 'Mean_Predictor', 'Linear_Regression', 'Random_Forest', 'Gradient_Boosting']:
        gkf_rec = [r for r in all_gkf_records if r['regime'] == reg_name and r['model_name'] == m_name][0]
        chr_rec = [r for r in all_chrono_records if r['regime'] == reg_name and r['model_name'] == m_name][0]
        all_baseline_records.append({
            'regime': reg_name,
            'model_name': m_name,
            'gkf_pooled_mae_g': gkf_rec['pooled_oof_mae_g'],
            'gkf_pooled_rmse_g': gkf_rec['pooled_oof_rmse_g'],
            'gkf_pooled_r2': gkf_rec['pooled_oof_r2'],
            'gkf_imp_vs_persistence_pct': gkf_rec['pct_improvement_vs_persistence'],
            'chrono_test_mae_g': chr_rec['test_mae_g'],
            'chrono_test_rmse_g': chr_rec['test_rmse_g'],
            'chrono_test_r2': chr_rec['test_r2'],
            'chrono_imp_vs_persistence_pct': chr_rec['pct_improvement_vs_persistence'],
            'improves_on_persistence_in_chrono': bool(chr_rec['pct_improvement_vs_persistence'] > 0)
        })

# Save Deliverables 4, 5, 6
df_gkf = pd.DataFrame(all_gkf_records)
csv_gkf_path = os.path.join(OUTPUT_DIR, 'groupkfold_metrics.csv')
df_gkf.to_csv(csv_gkf_path, index=False)
print(f"\nSaved {csv_gkf_path}")

df_chrono = pd.DataFrame(all_chrono_records)
csv_chrono_path = os.path.join(OUTPUT_DIR, 'chronological_metrics.csv')
df_chrono.to_csv(csv_chrono_path, index=False)
print(f"Saved {csv_chrono_path}")

df_base_comp = pd.DataFrame(all_baseline_records)
csv_base_path = os.path.join(OUTPUT_DIR, 'baseline_comparison.csv')
df_base_comp.to_csv(csv_base_path, index=False)
print(f"Saved {csv_base_path}")

# =========================================================================
# ERROR SLICING: BY WEIGHT RANGE AND REVISIT INTERVAL
# =========================================================================
print("\n[Phase 5.2] Analyzing Error Distributions by Subgroups on Chronological Test Set...")

# Evaluate subgroup errors on Chronological Test Set under Clean Plausible Regime
df_clean = df_pairs[df_pairs['is_suspicious_growth'] == 0].reset_index(drop=True)
clean_train = df_clean[(df_clean['curr_datetime'] < cutoff) & (df_clean['next_datetime'] < cutoff)].reset_index(drop=True)
clean_test = df_clean[(df_clean['curr_datetime'] >= cutoff) & (df_clean['next_datetime'] >= cutoff)].reset_index(drop=True)

# Train RF on clean train
rf_pipe = build_models()['Random_Forest']
rf_pipe.fit(clean_train[feature_cols], clean_train['next_weight'].values)
clean_test['rf_pred'] = rf_pipe.predict(clean_test[feature_cols])
clean_test['pers_pred'] = clean_test['curr_weight']
clean_test['rf_abs_error'] = np.abs(clean_test['next_weight'] - clean_test['rf_pred'])
clean_test['pers_abs_error'] = np.abs(clean_test['next_weight'] - clean_test['pers_pred'])

# Slices by Current Weight Range
weight_bins = [0, 300, 600, 1000, 3000]
weight_labels = ['< 300g (Juvenile)', '300-600g (Grow-out)', '600-1000g (Advanced)', '> 1000g (Market)']
clean_test['weight_group'] = pd.cut(clean_test['curr_weight'], bins=weight_bins, labels=weight_labels)

# Slices by Revisit Gap
gap_bins = [0, 14, 28, 50]
gap_labels = ['3-14 days (Short)', '15-28 days (Standard)', '29-45 days (Extended)']
clean_test['gap_group'] = pd.cut(clean_test['gap_days'], bins=gap_bins, labels=gap_labels)

slice_records = []
for grp_col, grp_name in [('weight_group', 'Current Weight Range'), ('gap_group', 'Revisit Interval')]:
    for val, sub in clean_test.groupby(grp_col, observed=True):
        n_sub = len(sub)
        p_mae = sub['pers_abs_error'].mean()
        rf_mae = sub['rf_abs_error'].mean()
        delta = rf_mae - p_mae
        pct_imp = (p_mae - rf_mae) / p_mae * 100
        slice_records.append({
            'grouping_category': grp_name,
            'subgroup_name': str(val),
            'sample_count': n_sub,
            'sample_pct': round(n_sub / len(clean_test) * 100, 2),
            'persistence_mae_g': round(p_mae, 2),
            'random_forest_mae_g': round(rf_mae, 2),
            'delta_mae_g': round(delta, 2),
            'pct_improvement_vs_persistence': round(pct_imp, 2),
            'rf_better_than_persistence': bool(rf_mae < p_mae)
        })

df_slices = pd.DataFrame(slice_records)
csv_slices_path = os.path.join(METRICS_DIR, 'test_subgroup_error_analysis.csv')
df_slices.to_csv(csv_slices_path, index=False)
print(f"Saved {csv_slices_path}")

print("\n--- Summary of Baseline Comparison ---")
print(df_base_comp[['regime', 'model_name', 'gkf_pooled_mae_g', 'gkf_imp_vs_persistence_pct', 'chrono_test_mae_g', 'chrono_imp_vs_persistence_pct', 'improves_on_persistence_in_chrono']].to_string(index=False))

print("\n--- Subgroup Error Breakdown on Chronological Test Set (Clean Regime) ---")
print(df_slices[['grouping_category', 'subgroup_name', 'sample_count', 'persistence_mae_g', 'random_forest_mae_g', 'delta_mae_g', 'pct_improvement_vs_persistence']].to_string(index=False))

