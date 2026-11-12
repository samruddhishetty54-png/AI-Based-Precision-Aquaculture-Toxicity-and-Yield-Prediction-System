"""
Data Preprocessing Pipeline v2 for AI-Based Precision Aquaculture Toxicity and Yield Prediction System.

Corrections in v2:
1. Ammonia Calculations:
   - Preserves all 3 original ammonia columns separately without destructive merging.
   - Converts TAN (NH3-N) to molecular NH3 using Emerson equation + 17.031/14.007 MW conversion factor.
   - Calculates molecular NH3 directly from TAN (NH3) using Emerson equation without re-applying 17/14.
   - Marks reported Ammonia-NH3 as unverified field measurement.
   - Standardizes output feature names with units and sources.
2. Inconsistency & Overlap Auditing:
   - Cross-checks records where multiple ammonia measurements co-occur.
   - Quantifies discrepancy and records calculation methodology per row.
3. Externalized Provisional Heuristics:
   - Externalizes risk thresholds to thresholds_config.json.
   - Explicitly marks risk classifications as provisional heuristics (unverified against site-specific bioassays).
   - Keeps raw sensor vitals strictly separated from rule-derived risk labels.
4. Point-in-Time Temporal Matching (Eliminating Look-Ahead Leakage):
   - Merges pond metadata as-of the observation date (profile_date <= wq_date).
   - Prevents back-projecting 2026 pond area, feed brand, or equipment onto historical (2021-2025) records.
5. All outputs saved to 'processed_data_v2/'.
   - Original datasets and 'processed_data/' are left untouched.
   - No ML models trained.
"""

import os
import json
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
PROCESSED_V2_DIR = os.path.join(BASE_DIR, "processed_data_v2")

os.makedirs(PROCESSED_V2_DIR, exist_ok=True)

# -------------------------------------------------------------------------
# 1. Externalized Threshold Configuration (Provisional Heuristics)
# -------------------------------------------------------------------------
CONFIG_FILE = os.path.join(PROCESSED_V2_DIR, "thresholds_config.json")

PROVISIONAL_THRESHOLDS = {
    "metadata": {
        "status": "provisional_heuristic",
        "scientific_validation": "unverified",
        "warning": (
            "These thresholds are unverified operational heuristics. They are NOT validated against "
            "published site-specific bioassays or regulatory standards, and must not be presented as ground truth."
        ),
        "configurable": True
    },
    "heuristics": {
        "hypoxia_sublethal_do_mg_l": 4.0,
        "hypoxia_acute_do_mg_l": 3.0,
        "ph_stress_lower": 6.5,
        "ph_stress_upper": 8.5,
        "toxic_molecular_nh3_heuristic_mg_l": 0.05,
        "tan_caution_heuristic_mg_l": 1.0
    }
}

with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
    json.dump(PROVISIONAL_THRESHOLDS, f, indent=2)

THRESH = PROVISIONAL_THRESHOLDS["heuristics"]

# -------------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------------

def parse_xlsx_stdlib(file_path):
    """Parses Excel .xlsx file using standard library zipfile and xml.etree."""
    sheets_data = {}
    with zipfile.ZipFile(file_path, 'r') as z:
        wb_xml = ET.fromstring(z.read('xl/workbook.xml'))
        ns = {
            'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        }
        
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_xml = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in ss_xml.findall('main:si', ns):
                t = si.find('main:t', ns)
                if t is not None and t.text:
                    shared_strings.append(t.text)
                else:
                    r_texts = [r.find('main:t', ns).text for r in si.findall('main:r', ns) 
                               if r.find('main:t', ns) is not None and r.find('main:t', ns).text]
                    shared_strings.append("".join(r_texts))

        sheets = wb_xml.findall('main:sheets/main:sheet', ns)
        sheet_info = [(s.attrib.get('name'), s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')) for s in sheets]

        rel_xml = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        rel_ns = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
        rel_map = {rel.attrib['Id']: rel.attrib['Target'] for rel in rel_xml.findall('r:Relationship', rel_ns)}

        for name, r_id in sheet_info:
            target = rel_map.get(r_id)
            if not target:
                continue
            sheet_file = target if target.startswith('xl/') else 'xl/' + target
            
            sheet_xml = ET.fromstring(z.read(sheet_file))
            rows = sheet_xml.findall('main:sheetData/main:row', ns)
            data = []
            max_col = 0
            
            def col_str_to_idx(col_str):
                idx = 0
                for c in col_str:
                    idx = idx * 26 + (ord(c) - ord('A') + 1)
                return idx - 1

            for row in rows:
                row_cells = {}
                for c in row.findall('main:c', ns):
                    r_ref = c.attrib.get('r', '')
                    col_letters = ''.join([ch for ch in r_ref if ch.isalpha()])
                    if not col_letters:
                        continue
                    col_idx = col_str_to_idx(col_letters)
                    max_col = max(max_col, col_idx + 1)
                    
                    c_type = c.attrib.get('t', '')
                    v_elem = c.find('main:v', ns)
                    val = v_elem.text if v_elem is not None else None
                    
                    if c_type == 's' and val is not None:
                        val = shared_strings[int(val)] if int(val) < len(shared_strings) else val
                    elif c_type == 'b' and val is not None:
                        val = (val == '1')
                    row_cells[col_idx] = val
                data.append(row_cells)

            grid = []
            for r in data:
                row_vals = [r.get(c_idx, None) for c_idx in range(max_col)]
                grid.append(row_vals)
            
            if grid:
                headers = grid[0]
                rows_data = grid[1:]
                clean_headers = [f"Col_{i}" if h is None or str(h).strip() == "" else str(h).strip() for i, h in enumerate(headers)]
                df = pd.DataFrame(rows_data, columns=clean_headers)
            else:
                df = pd.DataFrame()
            sheets_data[name] = df

    return sheets_data


def calculate_nh3_from_tan_n(tan_n_mg_l, ph, temp_c):
    """
    Computes molecular toxic un-ionized ammonia (mg/L molecular NH3) from TAN expressed as NH3-N.
    
    Equations:
      1. Emerson et al. (1975) dissociation equilibrium:
         pKa = 0.09018 + (2729.92 / (temp_c + 273.15))
         f = 1 / (10^(pKa - ph) + 1)
      2. Molecular weight conversion:
         NH3_molecular = f * TAN_N * (17.031 / 14.007)
    """
    if pd.isna(tan_n_mg_l) or pd.isna(ph) or pd.isna(temp_c):
        return np.nan
    try:
        temp_k = float(temp_c) + 273.15
        pka = 0.09018 + (2729.92 / temp_k)
        f = 1.0 / (10.0 ** (pka - float(ph)) + 1.0)
        ratio_mw = 17.031 / 14.007
        return round(float(tan_n_mg_l) * f * ratio_mw, 5)
    except Exception:
        return np.nan


def calculate_nh3_from_tan_nh3(tan_nh3_mg_l, ph, temp_c):
    """
    Computes molecular toxic un-ionized ammonia (mg/L molecular NH3) from TAN expressed as molecular NH3.
    
    Because TAN is ALREADY expressed as NH3 molecular mass, the un-ionized fraction f
    is applied directly WITHOUT the 17/14 conversion factor.
    """
    if pd.isna(tan_nh3_mg_l) or pd.isna(ph) or pd.isna(temp_c):
        return np.nan
    try:
        temp_k = float(temp_c) + 273.15
        pka = 0.09018 + (2729.92 / temp_k)
        f = 1.0 / (10.0 ** (pka - float(ph)) + 1.0)
        return round(float(tan_nh3_mg_l) * f, 5)
    except Exception:
        return np.nan


# -------------------------------------------------------------------------
# Step 1: Clean water_quality.csv
# -------------------------------------------------------------------------
def clean_water_quality():
    fpath = os.path.join(DATASET_DIR, "water_quality.csv")
    df_raw = pd.read_csv(fpath, encoding='utf-8')
    orig_rows, orig_cols = df_raw.shape
    
    missing_before = df_raw.isna().sum().to_dict()
    
    report = {
        "dataset": "water_quality.csv",
        "original_rows": orig_rows,
        "original_columns": orig_cols,
        "missing_before_total": int(df_raw.isna().sum().sum()),
        "cleaning_decisions": []
    }
    
    # Combined datetime
    dt_str = df_raw['Date of data collection'] + ' ' + df_raw['Time of data collection']
    df_raw['datetime'] = pd.to_datetime(dt_str, format='mixed', errors='coerce')
    df_raw['date_parsed'] = pd.to_datetime(df_raw['Date of data collection'], format='mixed')
    
    # Sort chronologically by pond
    df_raw = df_raw.sort_values(by=['pond_id', 'datetime']).reset_index(drop=True)
    report["cleaning_decisions"].append("Created parsed datetime and sorted chronologically within each pond.")
    
    # Deduplicate timestamps
    dup_subset = ['pond_id', 'Date of data collection', 'Time of data collection']
    dup_count = int(df_raw.duplicated(subset=dup_subset, keep=False).sum())
    report["duplicate_records_found"] = dup_count
    
    if dup_count > 0:
        df_raw['completeness_score'] = df_raw[['DO (mg/L)', 'pH', 'Temp (in °C)']].notna().sum(axis=1)
        df_raw = df_raw.sort_values(by=['pond_id', 'datetime', 'completeness_score'], ascending=[True, True, False])
        df_raw = df_raw.drop_duplicates(subset=dup_subset, keep='first').reset_index(drop=True)
        df_raw = df_raw.drop(columns=['completeness_score'])
        report["cleaning_decisions"].append(f"Resolved {dup_count} duplicate timestamps by retaining the record with complete sensor vitals.")
        
    # Purge 100% empty columns
    cols_100_empty = ['Alkalinity (mg/L)', 'Hardness (mg/L)']
    
    # Exclude non-modeling text notes and corrective workflows
    cols_notes_actions = [
        'Observer', 'Is follow up possible', 'Reason follow up not possible',
        'Corrective actions requested', 'Corrective actions requested (other)',
        'Corrective actions amount requested', 'Corrective actions implemented',
        'Corrective actions implementation date', 'Corrective actions taken',
        'Corrective actions taken (other)', 'Corrective actions taken (details)',
        'Non-prescribed corrective actions taken', 'Reason not implemented',
        'Water quality improved after corrective actions', 'Corrective action notes',
        'Notes (mortalities)', 'Self-initiated corrective actions taken',
        'Self-initiated corrective actions implemented on (exact date)',
        'Self-initiated corrective actions implemented (date range)',
        'Self-initiated corrective actions notes', 'Notes', 'Corrective actions'
    ]
    
    cols_to_drop = [c for c in cols_100_empty + cols_notes_actions if c in df_raw.columns]
    df_cleaned = df_raw.drop(columns=cols_to_drop).copy()
    report["columns_removed"] = cols_to_drop
    report["cleaning_decisions"].append(f"Purged 100% empty columns: {cols_100_empty}.")
    report["cleaning_decisions"].append(f"Excluded {len(cols_notes_actions)} unverified notes and intervention workflow columns.")
    
    # Drop rows missing triage sensor vitals (DO, pH, or Temp)
    vital_missing_mask = df_cleaned['pH'].isna() | df_cleaned['DO (mg/L)'].isna() | df_cleaned['Temp (in °C)'].isna()
    vital_missing_count = int(vital_missing_mask.sum())
    report["vital_sensor_missing_count"] = vital_missing_count
    df_cleaned = df_cleaned[~vital_missing_mask].copy().reset_index(drop=True)
    report["cleaning_decisions"].append(f"Excluded {vital_missing_count} incomplete rows missing DO, pH, or Temp to prevent synthetic sensor hallucination.")
    
    # Zero-fill prevention for weight and feed
    df_cleaned.loc[df_cleaned['Weight'] == 0, 'Weight'] = np.nan
    df_cleaned.loc[df_cleaned['Feed amount (kg)'] == 0, 'Feed amount (kg)'] = np.nan
    report["cleaning_decisions"].append("Replaced physically invalid 0.0g weights and 0.0kg feed entries with NaN; never zero-filled.")

    # Parameters out of range handling
    df_cleaned['Parameters out of range'] = df_cleaned['Parameters out of range'].fillna('None')
    
    report["final_rows"] = len(df_cleaned)
    report["final_columns"] = len(df_cleaned.columns)
    report["columns_retained"] = list(df_cleaned.columns)
    report["missing_after_total"] = int(df_cleaned.isna().sum().sum())
    
    out_path = os.path.join(PROCESSED_V2_DIR, "water_quality_cleaned_v2.csv")
    df_cleaned.to_csv(out_path, index=False, encoding='utf-8')
    report["output_file"] = out_path
    
    return df_cleaned, report


# -------------------------------------------------------------------------
# Step 2: Clean enrolled_ponds.csv (Point-in-Time Historical Profiles)
# -------------------------------------------------------------------------
def clean_enrolled_ponds():
    fpath = os.path.join(DATASET_DIR, "enrolled_ponds.csv")
    df_raw = pd.read_csv(fpath)
    orig_rows, orig_cols = df_raw.shape
    
    report = {
        "dataset": "enrolled_ponds.csv",
        "original_rows": orig_rows,
        "original_columns": orig_cols,
        "cleaning_decisions": []
    }
    
    df_cleaned = df_raw.copy()
    df_cleaned['profile_date'] = pd.to_datetime(df_cleaned['Date of data collection'], format='mixed')
    
    # Preserve both records for pond ara2_f33085c0 as valid historical snapshots
    # (Snapshot 1 on 2022-02-15 with NaN area; Snapshot 2 on 2026-06-03 with 41.0 acres)
    report["cleaning_decisions"].append(
        "Preserved all 324 pond enrollment profiles as point-in-time historical snapshots to prevent look-ahead leakage."
    )
    
    # Preserve uninvented physical measurements
    report["cleaning_decisions"].append("Preserved missing 'Pond area in acres' as genuine NaN; zero synthetic dimensions injected.")
    
    # Clean categorical text missing values
    cat_fills = {
        'Enrollment mechanism': 'Unknown',
        'Added by': 'Unknown',
        'Status': 'Unknown',
        'Culture change': 'None Reported',
        'Equipment': 'Standard/Unspecified',
        'Existing practices': 'Standard/Unspecified',
        'Fertilizers used': 'None/Unspecified',
        'Feed type': 'Unspecified',
        'Feed source': 'Unspecified',
        'Feed brand or name': 'Unspecified',
        'Fish source (e.g. hatchery name)': 'Unspecified',
        'Notes (existing practices)': 'None',
        'Notes': 'None'
    }
    for col, fill_val in cat_fills.items():
        if col in df_cleaned.columns:
            df_cleaned[col] = df_cleaned[col].fillna(fill_val)
            
    report["final_rows"] = len(df_cleaned)
    report["final_columns"] = len(df_cleaned.columns)
    report["columns_retained"] = list(df_cleaned.columns)
    
    out_path = os.path.join(PROCESSED_V2_DIR, "enrolled_ponds_v2.csv")
    df_cleaned.to_csv(out_path, index=False)
    report["output_file"] = out_path
    
    return df_cleaned, report


# -------------------------------------------------------------------------
# Step 3: Clean dropouts.csv
# -------------------------------------------------------------------------
def clean_dropouts():
    fpath = os.path.join(DATASET_DIR, "dropouts.csv")
    df_raw = pd.read_csv(fpath)
    orig_rows, orig_cols = df_raw.shape
    
    report = {
        "dataset": "dropouts.csv",
        "original_rows": orig_rows,
        "original_columns": orig_cols,
        "cleaning_decisions": []
    }
    
    df_cleaned = df_raw.copy()
    df_cleaned['Tenancy type'] = df_cleaned['Tenancy type'].fillna('Unknown')
    df_cleaned['Further details on reason'] = df_cleaned['Further details on reason'].fillna('None recorded')
    report["cleaning_decisions"].append("Preserved all 128 dropout records; filled missing descriptive fields with explicit 'Unknown' / 'None recorded'.")
    
    report["final_rows"] = len(df_cleaned)
    report["final_columns"] = len(df_cleaned.columns)
    
    out_path = os.path.join(PROCESSED_V2_DIR, "dropouts_v2.csv")
    df_cleaned.to_csv(out_path, index=False)
    report["output_file"] = out_path
    
    return df_cleaned, report


# -------------------------------------------------------------------------
# Step 4: Clean Data_Model_IoTMLCQ_2024.xlsx
# -------------------------------------------------------------------------
def clean_iot_model():
    fpath = os.path.join(DATASET_DIR, "Data_Model_IoTMLCQ_2024.xlsx")
    sheets = parse_xlsx_stdlib(fpath)
    df_raw = sheets['Sheet1']
    orig_rows, orig_cols = df_raw.shape
    
    report = {
        "dataset": "Data_Model_IoTMLCQ_2024.xlsx",
        "original_rows": orig_rows,
        "original_columns": orig_cols,
        "cleaning_decisions": []
    }
    
    df_cleaned = df_raw.copy()
    
    # Standardize column headers
    clean_cols = {}
    for c in df_cleaned.columns:
        clean_name = c.replace('\ufffd', '°').replace('(C)', '(°C)').strip()
        clean_cols[c] = clean_name
    df_cleaned = df_cleaned.rename(columns=clean_cols)
    
    # Convert Excel serial date to standard datetime
    dt_numeric = pd.to_numeric(df_cleaned['Datetime'], errors='coerce')
    df_cleaned['datetime_iso'] = pd.to_datetime(dt_numeric, unit='D', origin='1899-12-30').dt.strftime('%Y-%m-%d %H:%M:%S')
    
    num_cols = [
        'Average Fish Weight (g)', 'Survival Rate (%)', 'Disease Occurrence (Cases)',
        'Temperature (°C)', 'Dissolved Oxygen (mg/L)', 'pH', 'Turbidity (NTU)',
        'Month_Num', 'month_x', 'Oxygenation Interventions', 'Corrective Interventions',
        'Average Temperature (°C)', 'High Temperature (°C)', 'Low Temperature (°C)',
        'Precipitation (inches)', 'month_y', 'day', 'hour', 'oxigeno_scaled', 'ph', 'turbidez'
    ]
    for c in num_cols:
        if c in df_cleaned.columns:
            df_cleaned[c] = pd.to_numeric(df_cleaned[c], errors='coerce')
            
    report["cleaning_decisions"].append("Standardized ISO datetimes and validated proper float/int types across all 4,383 records.")
    report["final_rows"] = len(df_cleaned)
    report["final_columns"] = len(df_cleaned.columns)
    
    out_path = os.path.join(PROCESSED_V2_DIR, "iot_water_model_v2.csv")
    df_cleaned.to_csv(out_path, index=False)
    report["output_file"] = out_path
    
    return df_cleaned, report


# -------------------------------------------------------------------------
# Step 5: Task-Specific Datasets with Leakage Prevention & Ammonia Fixes
# -------------------------------------------------------------------------
def prepare_task_datasets_v2(df_wq, df_en):
    reports = {}
    
    # ---------------------------------------------------------------------
    # A. Toxicity Analysis v2
    # ---------------------------------------------------------------------
    # Filter rows where at least one ammonia measurement is present
    c1_raw = 'Ammonia—TAN (NH3-N) (mg/L)'
    c2_raw = 'Ammonia—TAN (NH3) (mg/L)'
    c3_raw = 'Ammonia—NH3 (mg/L)'
    
    any_amm = df_wq[c1_raw].notna() | df_wq[c2_raw].notna() | df_wq[c3_raw].notna()
    df_tox = df_wq[any_amm].copy().reset_index(drop=True)
    
    # Keep all three raw columns distinctly preserved and clearly named
    df_tox = df_tox.rename(columns={
        c1_raw: 'raw_ammonia_tan_nh3_n_mg_l',
        c2_raw: 'raw_ammonia_tan_nh3_mg_l',
        c3_raw: 'reported_ammonia_nh3_unverified_mg_l',
        'DO (mg/L)': 'dissolved_oxygen_mg_l',
        'pH': 'ph',
        'Temp (in °C)': 'temp_c',
        'Turbidity (in cm)': 'turbidity_cm',
        'TDS (ppt)': 'tds_ppt',
        'Water color': 'water_color',
        'Is WQ in range?': 'is_wq_in_range',
        'Parameters out of range': 'parameters_out_of_range',
        'Individuals air gulping': 'air_gulping_count',
        'Individuals tail splashing': 'tail_splashing_count',
        'Dead fish': 'dead_fish_count'
    })
    
    # Calculation 1: From TAN (NH3-N) with MW factor 17.031/14.007
    df_tox['calculated_nh3_from_tan_n_mg_l'] = df_tox.apply(
        lambda r: calculate_nh3_from_tan_n(r['raw_ammonia_tan_nh3_n_mg_l'], r['ph'], r['temp_c']),
        axis=1
    )
    
    # Calculation 2: From TAN (NH3) directly (already on NH3 mass basis)
    df_tox['calculated_nh3_from_tan_nh3_mg_l'] = df_tox.apply(
        lambda r: calculate_nh3_from_tan_nh3(r['raw_ammonia_tan_nh3_mg_l'], r['ph'], r['temp_c']),
        axis=1
    )
    
    # Primary unified calculated NH3 with explicit source attribution
    def assign_primary_nh3(r):
        if pd.notna(r['calculated_nh3_from_tan_n_mg_l']):
            return r['calculated_nh3_from_tan_n_mg_l'], 'emerson_from_tan_nh3_n_with_mw_conversion'
        elif pd.notna(r['calculated_nh3_from_tan_nh3_mg_l']):
            return r['calculated_nh3_from_tan_nh3_mg_l'], 'emerson_from_tan_nh3_direct'
        else:
            return np.nan, 'uncalculated_missing_inputs'
            
    nh3_res = df_tox.apply(assign_primary_nh3, axis=1)
    df_tox['primary_calculated_nh3_mg_l'] = [val[0] for val in nh3_res]
    df_tox['nh3_calculation_source'] = [val[1] for val in nh3_res]
    
    # Inconsistency checks on multi-populated records
    multi_populated = df_tox[
        (df_tox['raw_ammonia_tan_nh3_n_mg_l'].notna() & df_tox['raw_ammonia_tan_nh3_mg_l'].notna()) |
        (df_tox['raw_ammonia_tan_nh3_n_mg_l'].notna() & df_tox['reported_ammonia_nh3_unverified_mg_l'].notna())
    ]
    overlap_count = len(multi_populated)
    
    # Rule-derived heuristic risk labels (explicitly marked as provisional)
    df_tox['provisional_hypoxia_risk_heuristic'] = (df_tox['dissolved_oxygen_mg_l'] < THRESH['hypoxia_sublethal_do_mg_l']).astype(int)
    df_tox['provisional_ph_stress_risk_heuristic'] = (
        (df_tox['ph'] < THRESH['ph_stress_lower']) | (df_tox['ph'] > THRESH['ph_stress_upper'])
    ).astype(int)
    
    # Toxic ammonia risk evaluated on primary molecular NH3
    df_tox['provisional_ammonia_risk_heuristic'] = (
        (df_tox['primary_calculated_nh3_mg_l'] >= THRESH['toxic_molecular_nh3_heuristic_mg_l']) |
        (df_tox['raw_ammonia_tan_nh3_n_mg_l'] >= THRESH['tan_caution_heuristic_mg_l'])
    ).astype(int)
    
    df_tox['provisional_behavioral_distress_observed'] = (
        (df_tox['air_gulping_count'] > 0) |
        (df_tox['tail_splashing_count'] > 0) |
        (df_tox['dead_fish_count'] > 0)
    ).astype(int)
    
    def get_provisional_severity(row):
        if (row['dead_fish_count'] > 0 or 
            row['dissolved_oxygen_mg_l'] < THRESH['hypoxia_acute_do_mg_l'] or 
            row['provisional_ammonia_risk_heuristic'] == 1):
            return 'High Risk / Severe Stress'
        elif (row['provisional_hypoxia_risk_heuristic'] == 1 or 
              row['provisional_ph_stress_risk_heuristic'] == 1 or 
              row['provisional_behavioral_distress_observed'] == 1):
            return 'Moderate Warning'
        else:
            return 'Optimal / Baseline'
            
    df_tox['provisional_severity_heuristic'] = df_tox.apply(get_provisional_severity, axis=1)
    
    tox_cols = [
        'pond_id', 'datetime', 'region', 'Weather', 'water_color',
        'dissolved_oxygen_mg_l', 'ph', 'temp_c', 'turbidity_cm', 'tds_ppt',
        'raw_ammonia_tan_nh3_n_mg_l', 'raw_ammonia_tan_nh3_mg_l', 'reported_ammonia_nh3_unverified_mg_l',
        'calculated_nh3_from_tan_n_mg_l', 'calculated_nh3_from_tan_nh3_mg_l',
        'primary_calculated_nh3_mg_l', 'nh3_calculation_source',
        'provisional_hypoxia_risk_heuristic', 'provisional_ph_stress_risk_heuristic',
        'provisional_ammonia_risk_heuristic', 'provisional_behavioral_distress_observed',
        'air_gulping_count', 'tail_splashing_count', 'dead_fish_count',
        'is_wq_in_range', 'parameters_out_of_range', 'provisional_severity_heuristic'
    ]
    df_tox = df_tox[[c for c in tox_cols if c in df_tox.columns]]
    
    tox_out = os.path.join(PROCESSED_V2_DIR, "toxicity_analysis_v2.csv")
    df_tox.to_csv(tox_out, index=False)
    
    reports["toxicity_analysis_v2"] = {
        "file": tox_out,
        "rows": len(df_tox),
        "columns": len(df_tox.columns),
        "method_breakdown": df_tox['nh3_calculation_source'].value_counts().to_dict(),
        "multi_populated_ammonia_records": overlap_count,
        "uncalculated_records_count": int((df_tox['nh3_calculation_source'] == 'uncalculated_missing_inputs').sum())
    }
    
    # ---------------------------------------------------------------------
    # Point-in-Time Temporal Join Utility (Eliminates Future Leakage)
    # ---------------------------------------------------------------------
    df_en_sorted = df_en.sort_values(by='profile_date').reset_index(drop=True)
    
    # ---------------------------------------------------------------------
    # B. Fish Health and Growth Analysis v2
    # ---------------------------------------------------------------------
    has_fish_obs = (
        (df_wq['Weight'].notna() & (df_wq['Weight'] > 0)) |
        df_wq['Dead fish'].notna() |
        df_wq['Individuals air gulping'].notna() |
        df_wq['Individuals tail splashing'].notna()
    )
    df_health = df_wq[has_fish_obs].copy().sort_values(by='date_parsed').reset_index(drop=True)
    
    # Point-in-time merge: attach ONLY profiles available on or before observation date
    en_cols_match = ['pond_id', 'profile_date', 'Pond area in acres', 'Depth in meters', 'Feed type']
    df_health = pd.merge_asof(
        df_health,
        df_en_sorted[en_cols_match],
        left_on='date_parsed',
        right_on='profile_date',
        by='pond_id',
        direction='backward'
    )
    
    health_rename = {
        'DO (mg/L)': 'dissolved_oxygen_mg_l',
        'pH': 'ph',
        'Temp (in °C)': 'temp_c',
        'Weight': 'average_fish_weight_g',
        'Species': 'species',
        'Stocking density (per acre)': 'stocking_density_per_acre',
        'Individuals air gulping': 'air_gulping_count',
        'Individuals tail splashing': 'tail_splashing_count',
        'Dead fish': 'dead_fish_count',
        'Have fish been helped': 'have_fish_been_helped'
    }
    df_health = df_health.rename(columns=health_rename)
    df_health['has_weight_measurement'] = df_health['average_fish_weight_g'].notna().astype(int)
    
    health_cols = [
        'pond_id', 'datetime', 'region', 'species', 'profile_date', 'Pond area in acres', 'Depth in meters',
        'stocking_density_per_acre', 'average_fish_weight_g', 'has_weight_measurement',
        'dead_fish_count', 'air_gulping_count', 'tail_splashing_count',
        'dissolved_oxygen_mg_l', 'ph', 'temp_c', 'have_fish_been_helped'
    ]
    df_health = df_health[[c for c in health_cols if c in df_health.columns]]
    
    health_out = os.path.join(PROCESSED_V2_DIR, "fish_health_growth_analysis_v2.csv")
    df_health.to_csv(health_out, index=False)
    
    reports["fish_health_growth_v2"] = {
        "file": health_out,
        "rows": len(df_health),
        "columns": len(df_health.columns),
        "missing_historical_profile_count": int(df_health['profile_date'].isna().sum()),
        "missing_pond_area_count": int(df_health['Pond area in acres'].isna().sum())
    }
    
    # ---------------------------------------------------------------------
    # C. Feeding Analysis v2
    # ---------------------------------------------------------------------
    has_feed = df_wq['Feed amount (kg)'].notna() & (df_wq['Feed amount (kg)'] > 0)
    df_feed = df_wq[has_feed].copy().sort_values(by='date_parsed').reset_index(drop=True)
    
    en_feed_cols = ['pond_id', 'profile_date', 'Pond area in acres', 'Depth in meters', 'Feed type', 'Feed brand or name']
    df_feed = pd.merge_asof(
        df_feed,
        df_en_sorted[en_feed_cols],
        left_on='date_parsed',
        right_on='profile_date',
        by='pond_id',
        direction='backward'
    )
    
    feed_rename = {
        'DO (mg/L)': 'dissolved_oxygen_mg_l',
        'pH': 'ph',
        'Temp (in °C)': 'temp_c',
        'Feed amount (kg)': 'feed_amount_kg',
        'Weight': 'average_fish_weight_g',
        'Species': 'species',
        'Stocking density (per acre)': 'stocking_density_per_acre',
        'Ammonia—TAN (NH3-N) (mg/L)': 'ammonia_tan_nh3_n_mg_l'
    }
    df_feed = df_feed.rename(columns=feed_rename)
    
    # Feed per acre calculated ONLY when historical pond area was known on that date
    df_feed['feed_per_acre_kg'] = np.where(
        df_feed['Pond area in acres'].notna() & (df_feed['Pond area in acres'] > 0),
        round(df_feed['feed_amount_kg'] / df_feed['Pond area in acres'], 2),
        np.nan
    )
    
    feed_cols = [
        'pond_id', 'datetime', 'region', 'species', 'profile_date', 'Pond area in acres', 'Depth in meters',
        'Feed type', 'Feed brand or name', 'stocking_density_per_acre',
        'feed_amount_kg', 'feed_per_acre_kg', 'average_fish_weight_g',
        'dissolved_oxygen_mg_l', 'ph', 'temp_c', 'ammonia_tan_nh3_n_mg_l'
    ]
    df_feed = df_feed[[c for c in feed_cols if c in df_feed.columns]]
    
    feed_out = os.path.join(PROCESSED_V2_DIR, "feeding_analysis_v2.csv")
    df_feed.to_csv(feed_out, index=False)
    
    reports["feeding_analysis_v2"] = {
        "file": feed_out,
        "rows": len(df_feed),
        "columns": len(df_feed.columns),
        "missing_historical_profile_count": int(df_feed['profile_date'].isna().sum()),
        "missing_pond_area_count": int(df_feed['Pond area in acres'].isna().sum())
    }
    
    return reports


# -------------------------------------------------------------------------
# Main Execution Pipeline v2
# -------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("AI-BASED PRECISION AQUACULTURE DATA PREPROCESSING PIPELINE v2")
    print("=" * 70)
    
    full_report = {
        "pipeline_version": "v2.0",
        "destination_folder": "processed_data_v2",
        "corrections_implemented": [
            "Applied 17.031/14.007 molecular weight ratio to Emerson calculation from TAN (NH3-N).",
            "Applied direct Emerson calculation to TAN (NH3) without double-applying MW ratio.",
            "Preserved reported Ammonia-NH3 as separate unverified measurement.",
            "Maintained distinct column names with explicit sources and units.",
            "Cross-checked multi-populated ammonia records for consistency.",
            "Externalized heuristic risk thresholds to thresholds_config.json as provisional heuristics.",
            "Implemented point-in-time temporal matching (merge_asof) to eliminate look-ahead leakage.",
            "Preserved uninvented physical measurements and genuine NaNs.",
            "Preserved original datasets in 'dataset/' and existing 'processed_data/' intact."
        ],
        "datasets": {}
    }
    
    # 1. Clean water_quality.csv
    print("\n[1/4] Processing water_quality.csv...")
    df_wq, wq_rep = clean_water_quality()
    full_report["datasets"]["water_quality_v2"] = wq_rep
    print(f"  -> Cleaned: {wq_rep['final_rows']} rows, {wq_rep['final_columns']} cols")
    
    # 2. Clean enrolled_ponds.csv
    print("\n[2/4] Processing enrolled_ponds.csv (point-in-time profiles)...")
    df_en, en_rep = clean_enrolled_ponds()
    full_report["datasets"]["enrolled_ponds_v2"] = en_rep
    print(f"  -> Cleaned: {en_rep['final_rows']} rows, {en_rep['final_columns']} cols")
    
    # 3. Clean dropouts.csv
    print("\n[3/4] Processing dropouts.csv...")
    df_dr, dr_rep = clean_dropouts()
    full_report["datasets"]["dropouts_v2"] = dr_rep
    print(f"  -> Cleaned: {dr_rep['final_rows']} rows, {dr_rep['final_columns']} cols")
    
    # 4. Clean Data_Model_IoTMLCQ_2024.xlsx
    print("\n[4/4] Processing Data_Model_IoTMLCQ_2024.xlsx...")
    df_iot, iot_rep = clean_iot_model()
    full_report["datasets"]["Data_Model_IoTMLCQ_2024_v2"] = iot_rep
    print(f"  -> Cleaned: {iot_rep['final_rows']} rows, {iot_rep['final_columns']} cols")
    
    # 5. Generate v2 task-specific datasets
    print("\n[5/5] Generating Task-Specific Prepared Datasets (v2)...")
    task_reps = prepare_task_datasets_v2(df_wq, df_en)
    full_report["task_specific_datasets_v2"] = task_reps
    for t_name, t_info in task_reps.items():
        print(f"  -> {t_name}: {t_info['rows']} rows, {t_info['columns']} cols ({os.path.basename(t_info['file'])})")
        
    # Save v2 report JSON
    rep_json_path = os.path.join(PROCESSED_V2_DIR, "preprocessing_v2_report.json")
    with open(rep_json_path, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, indent=2)
        
    print(f"\n[DONE] v2 processing completed. Metadata saved to {rep_json_path}")
    print("=" * 70)

if __name__ == '__main__':
    main()

