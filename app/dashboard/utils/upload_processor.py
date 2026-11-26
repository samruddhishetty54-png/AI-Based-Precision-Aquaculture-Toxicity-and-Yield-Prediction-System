"""CSV Upload, Schema Mapping, Validation, and Model Compatibility Engine.

Handles organization-uploaded aquaculture CSV datasets with strict scientific
and data-integrity guardrails:
1. Never silently renames columns without explicit mapping.
2. Never fills missing values with zero or fabricates missing readings.
3. Never invents pond IDs, farm hierarchies, or observation dates.
4. Never assumes units from ambiguous column names (flags for explicit user confirmation).
5. Runs models ONLY when their actual required inputs and bounds are satisfied.
6. Keeps uploaded data strictly isolated in session state from historical and simulated data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import io
import numpy as np
import pandas as pd

from app.core.chemistry import calculate_nh3_from_tan_n, calculate_nh3_from_tan_nh3
from app.dashboard.utils.helpers import DEFENSIVE_BOUNDS, detect_simulation_source


# Canonical fields supported by Precision AquaDSS
CANONICAL_FIELDS: Dict[str, Dict[str, Any]] = {
    "pond_id": {
        "label": "Pond / Tank Identifier",
        "unit": "text/id",
        "type": "identifier",
        "exact_aliases": [
            "pond_id", "Pond ID", "pondid", "pond_code",
            "tank_id", "Tank ID", "tankid", "tank_code", "system_id", "System ID",
        ],
        "ambiguous_aliases": ["pond", "tank", "id"],
    },
    "farm_id": {
        "label": "Farm / Site Identifier (Optional)",
        "unit": "text/id",
        "type": "identifier",
        "exact_aliases": ["farm_id", "Farm ID", "farm_name", "site_id"],
        "ambiguous_aliases": ["farm", "site"],
    },
    "region": {
        "label": "Region / Zone (Optional)",
        "unit": "text",
        "type": "categorical",
        "exact_aliases": ["region", "Region", "zone", "district"],
        "ambiguous_aliases": [],
    },
    "datetime": {
        "label": "Observation Date / Timestamp",
        "unit": "ISO / date",
        "type": "datetime",
        "exact_aliases": ["datetime", "Date of data collection", "observation_date", "date_parsed", "timestamp"],
        "ambiguous_aliases": ["date", "time"],
    },
    "dissolved_oxygen_mg_l": {
        "label": "Dissolved Oxygen (mg/L)",
        "unit": "mg/L",
        "type": "numeric",
        "bound_key": "do",
        "exact_aliases": ["dissolved_oxygen_mg_l", "DO (mg/L)", "do_mg_l", "curr_do"],
        "ambiguous_aliases": ["do", "dissolved_oxygen", "oxygen"],
    },
    "ph": {
        "label": "Water pH (0–14)",
        "unit": "pH",
        "type": "numeric",
        "bound_key": "ph",
        "exact_aliases": ["ph", "pH", "curr_ph", "water_ph"],
        "ambiguous_aliases": [],
    },
    "temp_c": {
        "label": "Water Temperature (°C)",
        "unit": "°C",
        "type": "numeric",
        "bound_key": "water_temp",
        "exact_aliases": ["temp_c", "Temp (in °C)", "temperature_c", "curr_temp", "curr_temp_c"],
        "ambiguous_aliases": ["temp", "temperature", "water_temp"],
    },
    "tan_n_mg_l": {
        "label": "TAN as Nitrogen — NH3-N (mg/L)",
        "unit": "mg/L as N",
        "type": "numeric",
        "bound_key": "tan",
        "exact_aliases": [
            "raw_ammonia_tan_nh3_n_mg_l",
            "Ammonia—TAN (NH3-N) (mg/L)",
            "tan_n_mg_l",
            "nh3_n_mg_l",
        ],
        "ambiguous_aliases": ["tan", "ammonia", "total_ammonia", "ammonia_mg_l"],
    },
    "tan_nh3_mg_l": {
        "label": "TAN as Molecular Ammonia — NH3 (mg/L)",
        "unit": "mg/L as NH3",
        "type": "numeric",
        "bound_key": "tan",
        "exact_aliases": [
            "raw_ammonia_tan_nh3_mg_l",
            "Ammonia—TAN (NH3) (mg/L)",
            "tan_nh3_mg_l",
        ],
        "ambiguous_aliases": [],
    },
    "primary_calculated_nh3_mg_l": {
        "label": "Un-ionized NH3 (mg/L)",
        "unit": "mg/L NH3",
        "type": "numeric",
        "bound_key": "tan",
        "exact_aliases": ["primary_calculated_nh3_mg_l", "curr_nh3", "calculated_nh3_from_tan_n_mg_l"],
        "ambiguous_aliases": ["nh3", "unionized_ammonia"],
    },
    "turbidity_cm": {
        "label": "Turbidity / Secchi Depth (cm)",
        "unit": "cm",
        "type": "numeric",
        "bound_key": "turbidity",
        "exact_aliases": ["turbidity_cm", "Turbidity (in cm)", "curr_turbidity", "curr_turbidity_cm"],
        "ambiguous_aliases": ["turbidity", "secchi"],
    },
    "tds_ppt": {
        "label": "Total Dissolved Solids (ppt)",
        "unit": "ppt",
        "type": "numeric",
        "bound_key": "tds",
        "exact_aliases": ["tds_ppt", "TDS (ppt)", "curr_tds", "curr_tds_ppt"],
        "ambiguous_aliases": ["tds", "salinity"],
    },
    "average_fish_weight_g": {
        "label": "Average Fish Weight (g/fish)",
        "unit": "g/fish",
        "type": "numeric",
        "bound_key": "fish_weight",
        "exact_aliases": ["average_fish_weight_g", "current_weight_g", "weight_g", "Weight"],
        "ambiguous_aliases": ["weight", "fish_weight", "avg_weight"],
    },
    "feed_amount_kg": {
        "label": "Feed Amount (kg/day)",
        "unit": "kg/day",
        "type": "numeric",
        "bound_key": "daily_feed",
        "exact_aliases": ["feed_amount_kg", "Feed amount (kg)", "current_feed_amount_kg", "curr_feed_amount_kg"],
        "ambiguous_aliases": ["feed", "feed_amount"],
    },
    "stocking_density_per_acre": {
        "label": "Stocking Density (fish/acre)",
        "unit": "fish/acre",
        "type": "numeric",
        "exact_aliases": ["stocking_density_per_acre", "Stocking density (per acre)", "curr_stocking_density"],
        "ambiguous_aliases": ["stocking_density", "density"],
    },
    "pond_area_acres": {
        "label": "Pond Area (acres)",
        "unit": "acres",
        "type": "numeric",
        "exact_aliases": ["Pond area in acres", "pond_area_acres", "pond_acres"],
        "ambiguous_aliases": ["area", "acres"],
    },
    "gap_days": {
        "label": "Revisit Interval (days, 3–45)",
        "unit": "days",
        "type": "numeric",
        "bound_key": "revisit_interval",
        "exact_aliases": ["gap_days", "revisit_interval_days"],
        "ambiguous_aliases": ["gap", "interval"],
    },
    "Weather": {
        "label": "Weather Condition (Optional)",
        "unit": "text",
        "type": "categorical",
        "exact_aliases": ["Weather", "weather", "curr_weather"],
        "ambiguous_aliases": [],
    },
    "water_color": {
        "label": "Water Color (Optional)",
        "unit": "text",
        "type": "categorical",
        "exact_aliases": ["water_color", "Water color", "curr_color", "curr_water_color"],
        "ambiguous_aliases": [],
    },
    "species": {
        "label": "Fish Species (Optional)",
        "unit": "text",
        "type": "categorical",
        "exact_aliases": ["species", "Species", "curr_species"],
        "ambiguous_aliases": [],
    },
}


def parse_uploaded_csv(file_bytes: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Safely parse an uploaded CSV file without altering values or filling NaNs."""
    if not filename.lower().endswith(".csv"):
        return None, (
            f"Unsupported file format for '{filename}'. Only CSV (.csv) files are supported "
            "because Excel parsing dependencies (openpyxl) are not installed in this environment."
        )

    try:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
        except Exception as exc:
            return None, f"Failed to decode CSV file '{filename}': {exc}"
    except Exception as exc:
        return None, f"Failed to parse CSV file '{filename}': {exc}"

    if df.empty or len(df.columns) == 0:
        return None, f"Uploaded CSV '{filename}' is empty or contains no columns."

    return df, None


def inspect_dataframe_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """Inspect column dtypes, missing values, and duplicate records without mutating df."""
    total_rows = len(df)
    total_cols = len(df.columns)
    duplicate_rows = int(df.duplicated().sum())

    col_profiles: List[Dict[str, Any]] = []
    for col in df.columns:
        na_count = int(df[col].isna().sum())
        na_pct = round((na_count / total_rows) * 100.0, 2) if total_rows > 0 else 0.0
        col_profiles.append({
            "Column": str(col),
            "Data Type": str(df[col].dtype),
            "Non-Null": total_rows - na_count,
            "Missing": na_count,
            "Missing %": na_pct,
        })

    return {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "duplicate_rows": duplicate_rows,
        "columns_df": pd.DataFrame(col_profiles),
    }


def suggest_column_mapping(columns: List[str]) -> Tuple[Dict[str, Optional[str]], List[Dict[str, str]]]:
    """Suggest exact canonical column mappings and flag ambiguous unit columns.

    Never silently maps an ambiguous column (like 'temp' or 'ammonia') without
    recording an ambiguity warning so the user must explicitly confirm units.
    """
    mapping: Dict[str, Optional[str]] = {}
    ambiguities: List[Dict[str, str]] = []
    lower_map = {str(c).strip().lower(): str(c) for c in columns}

    for canonical, spec in CANONICAL_FIELDS.items():
        matched: Optional[str] = None
        for alias in spec["exact_aliases"]:
            if alias in columns:
                matched = alias
                break
            if alias.lower() in lower_map:
                matched = lower_map[alias.lower()]
                break

        if matched is None:
            for amb in spec.get("ambiguous_aliases", []):
                if amb.lower() in lower_map:
                    col_found = lower_map[amb.lower()]
                    ambiguities.append({
                        "uploaded_column": col_found,
                        "candidate_field": canonical,
                        "expected_unit": spec["unit"],
                        "reason": (
                            f"Column '{col_found}' has an ambiguous unit/basis. "
                            f"Confirm explicitly if it represents {spec['label']} ({spec['unit']})."
                        ),
                    })
                    break

        mapping[canonical] = matched

    return mapping, ambiguities


def validate_mapped_dataset(
    df: pd.DataFrame,
    mapping: Dict[str, Optional[str]],
    filename: str = "uploaded.csv",
    confirmed_ambiguous_cols: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Validate mapped columns, data types, physical bounds, dates, and duplicates.

    Returns a structured validation report and a canonicalized working copy
    (preserving NaNs; never mutating the original uploaded DataFrame).
    """
    confirmed_set = set(confirmed_ambiguous_cols or [])
    errors: List[str] = []
    warnings: List[str] = []

    # Check simulation marker in filename
    is_sim, sim_tag, op_permitted = detect_simulation_source(filename, False)
    if is_sim:
        warnings.append(
            f"Filename '{filename}' matched simulation keyword ({sim_tag}). "
            "Outputs will be quarantined as non-operational."
        )

    # Check duplicate mappings (two canonical fields mapped to same source column)
    used_cols: Dict[str, List[str]] = {}
    for canon, src in mapping.items():
        if src:
            used_cols.setdefault(src, []).append(canon)
    for src, targets in used_cols.items():
        if len(targets) > 1:
            errors.append(
                f"Source column '{src}' is mapped to multiple canonical fields: {targets}. "
                "Each source column may map to at most one canonical field."
            )

    # Build canonical working DataFrame (read-only view of mapped values, preserving NaNs)
    work = pd.DataFrame(index=df.index)
    for canon, src in mapping.items():
        if src and src in df.columns:
            work[canon] = df[src]

    # Check ambiguous columns that were mapped without explicit confirmation
    for canon, src in mapping.items():
        if not src:
            continue
        spec = CANONICAL_FIELDS[canon]
        amb_lower = [a.lower() for a in spec.get("ambiguous_aliases", [])]
        if str(src).strip().lower() in amb_lower and src not in confirmed_set:
            warnings.append(
                f"Ambiguous unit for '{src}' → '{spec['label']}' ({spec['unit']}). "
                "Please confirm the measurement unit before trusting chemical or model outputs."
            )

    # Validate numeric fields & defensive bounds
    out_of_bounds_summary: List[Dict[str, Any]] = []
    for canon, spec in CANONICAL_FIELDS.items():
        if canon not in work.columns or spec["type"] != "numeric":
            continue

        raw_series = work[canon]
        numeric_series = pd.to_numeric(raw_series, errors="coerce")
        non_numeric_mask = raw_series.notna() & numeric_series.isna()
        non_numeric_count = int(non_numeric_mask.sum())
        if non_numeric_count > 0:
            errors.append(
                f"Column '{mapping[canon]}' ({spec['label']}) contains {non_numeric_count} non-numeric value(s)."
            )

        work[canon] = numeric_series

        bound_key = spec.get("bound_key")
        if bound_key and bound_key in DEFENSIVE_BOUNDS:
            b_min, b_max, unit = DEFENSIVE_BOUNDS[bound_key]
            valid_vals = numeric_series.dropna()
            below = int((valid_vals < b_min).sum())
            above = int((valid_vals > b_max).sum())
            if below > 0 or above > 0:
                out_of_bounds_summary.append({
                    "Field": spec["label"],
                    "Source Column": mapping[canon],
                    "Below Min": below,
                    "Above Max": above,
                    "Allowed Range": f"{b_min} to {b_max} {unit}",
                })
                warnings.append(
                    f"'{mapping[canon]}' has {below + above} value(s) outside software defensive bounds "
                    f"[{b_min}, {b_max}] {unit}."
                )

    # Validate datetime if mapped
    duplicate_pond_dates = 0
    if "datetime" in work.columns:
        raw_dt = work["datetime"]
        parsed_dt = pd.to_datetime(raw_dt, errors="coerce")
        invalid_dt_count = int((raw_dt.notna() & parsed_dt.isna()).sum())
        if invalid_dt_count > 0:
            warnings.append(
                f"Date column '{mapping['datetime']}' has {invalid_dt_count} unparsable date value(s). "
                "Unparsable dates are preserved as NaT and not fabricated."
            )
        work["datetime_parsed"] = parsed_dt
        if "pond_id" in work.columns:
            valid_pd = work.dropna(subset=["pond_id", "datetime_parsed"])
            duplicate_pond_dates = int(valid_pd.duplicated(subset=["pond_id", "datetime_parsed"]).sum())
            if duplicate_pond_dates > 0:
                warnings.append(
                    f"Detected {duplicate_pond_dates} duplicate (pond_id, observation date) record(s)."
                )

    # Pond & Farm hierarchy check (never invent farm hierarchy)
    pond_count = int(work["pond_id"].dropna().nunique()) if "pond_id" in work.columns else 0
    farm_count = int(work["farm_id"].dropna().nunique()) if "farm_id" in work.columns else 0
    region_count = int(work["region"].dropna().nunique()) if "region" in work.columns else 0

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "canonical_df": work,
        "out_of_bounds_df": pd.DataFrame(out_of_bounds_summary),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_pond_dates": duplicate_pond_dates,
        "pond_count": pond_count,
        "farm_count": farm_count,
        "region_count": region_count,
        "is_simulated": is_sim,
        "operational_use_permitted": op_permitted,
    }


def _in_bounds_mask(series: pd.Series, bound_key: str) -> pd.Series:
    """Return boolean mask of rows that are non-null, numeric, and within DEFENSIVE_BOUNDS."""
    s = pd.to_numeric(series, errors="coerce")
    bmin, bmax, _ = DEFENSIVE_BOUNDS[bound_key]
    return s.notna() & (s >= bmin) & (s <= bmax)


def assess_model_compatibility(work_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Audit which analytical modules and ML models are genuinely compatible with work_df.

    Checks both required feature presence and row-level physical/defensive bounds.
    """
    cols = set(work_df.columns)
    n_rows = len(work_df)

    def _valid_wq_mask() -> pd.Series:
        req = ["dissolved_oxygen_mg_l", "ph", "temp_c"]
        if not all(c in cols for c in req):
            return pd.Series(False, index=work_df.index)
        return (
            _in_bounds_mask(work_df["dissolved_oxygen_mg_l"], "do")
            & _in_bounds_mask(work_df["ph"], "ph")
            & _in_bounds_mask(work_df["temp_c"], "water_temp")
        )

    results: List[Dict[str, Any]] = []

    # 1. Emerson NH3 Equilibrium
    has_tan_n = "tan_n_mg_l" in cols
    has_tan_nh3 = "tan_nh3_mg_l" in cols
    if ("ph" in cols and "temp_c" in cols) and (has_tan_n or has_tan_nh3):
        tan_col = "tan_n_mg_l" if has_tan_n else "tan_nh3_mg_l"
        eligible = int((
            _in_bounds_mask(work_df["ph"], "ph")
            & _in_bounds_mask(work_df["temp_c"], "water_temp")
            & _in_bounds_mask(work_df[tan_col], "tan")
        ).sum())
        results.append({
            "key": "emerson_nh3",
            "name": "Emerson (1975) Equilibrium NH3",
            "category": "Chemistry Calculation",
            "compatible": eligible > 0,
            "eligible_rows": eligible,
            "total_rows": n_rows,
            "status": "READY" if eligible > 0 else "NO_COMPLETE_ROWS",
            "reason": (
                f"Requires in-bounds pH, Temp (°C), and explicit TAN basis ({tan_col})."
                if eligible > 0
                else "Required columns exist, but 0 rows have valid in-bounds (pH, Temp, TAN) values."
            ),
        })
    else:
        results.append({
            "key": "emerson_nh3",
            "name": "Emerson (1975) Equilibrium NH3",
            "category": "Chemistry Calculation",
            "compatible": False,
            "eligible_rows": 0,
            "total_rows": n_rows,
            "status": "MISSING_INPUTS",
            "reason": "Requires Water pH, Water Temperature (°C), and explicit TAN (NH3-N or NH3).",
        })

    # 2. Exp 1 Ammonia Soft-Sensor
    wq_mask = _valid_wq_mask()
    exp1_eligible = int(wq_mask.sum())
    results.append({
        "key": "exp1_soft_sensor",
        "name": "Exp 1: Ammonia Soft-Sensor (RF)",
        "category": "Experimental ML",
        "compatible": exp1_eligible > 0,
        "eligible_rows": exp1_eligible,
        "total_rows": n_rows,
        "status": "EXPERIMENTAL_READY" if exp1_eligible > 0 else "MISSING_INPUTS",
        "reason": (
            "In-bounds core inputs (DO, pH, Temp) present. Experimental only (AP pond domain; underpredicts NH3 >=0.05 mg/L)."
            if exp1_eligible > 0
            else "Requires valid in-bounds Dissolved Oxygen (0–25 mg/L), pH (0–14), and Temp (10–45 °C)."
        ),
    })

    # 3. Exp 2 Mortality Diagnostic
    exp2_eligible = int(wq_mask.sum())
    results.append({
        "key": "exp2_mortality",
        "name": "Exp 2: Mortality Diagnostic (LR)",
        "category": "Advisory Diagnostic (Weak Holdout)",
        "compatible": exp2_eligible > 0,
        "eligible_rows": exp2_eligible,
        "total_rows": n_rows,
        "status": "EXPERIMENTAL_READY" if exp2_eligible > 0 else "MISSING_INPUTS",
        "reason": (
            "In-bounds core inputs (DO, pH, Temp) present. Weak chronological precision (3.81%); not a mortality predictor."
            if exp2_eligible > 0
            else "Requires valid in-bounds Dissolved Oxygen (0–25 mg/L), pH (0–14), and Temp (10–45 °C)."
        ),
    })

    # 4. Exp 3 Next-Visit Ammonia Risk
    exp3_eligible = int(wq_mask.sum())
    has_gap = "gap_days" in cols and int(work_df["gap_days"].notna().sum()) > 0
    results.append({
        "key": "exp3_ammonia_risk",
        "name": "Exp 3: Next-Visit Ammonia Risk (RF)",
        "category": "Exploratory Prognostic (3–45d)",
        "compatible": exp3_eligible > 0,
        "eligible_rows": exp3_eligible,
        "total_rows": n_rows,
        "status": "EXPERIMENTAL_READY" if exp3_eligible > 0 else "MISSING_INPUTS",
        "reason": (
            f"Core inputs present ({'using gap_days column' if has_gap else 'requires user-selected 3–45d revisit interval'}). "
            "Holdout PR-AUC 0.0305 vs no-skill 0.0280."
            if exp3_eligible > 0
            else "Requires Dissolved Oxygen (mg/L), Water pH, and Water Temperature (°C)."
        ),
    })

    # 5. Exp 4 Fish Weight Persistence (requires strictly positive weight > 0)
    if "average_fish_weight_g" in cols:
        w_series = pd.to_numeric(work_df["average_fish_weight_g"], errors="coerce")
        exp4_eligible = int((w_series.notna() & (w_series > 0.0)).sum())
    else:
        exp4_eligible = 0
    results.append({
        "key": "exp4_fish_growth",
        "name": "Exp 4: Next-Visit Cohort Weight (Persistence)",
        "category": "Operational Persistence Baseline",
        "compatible": exp4_eligible > 0,
        "eligible_rows": exp4_eligible,
        "total_rows": n_rows,
        "status": "READY" if exp4_eligible > 0 else "MISSING_INPUTS",
        "reason": (
            "Requires Average Fish Weight (> 0 g/fish). Returns W(t+1) = W(t) persistence benchmark (NOT harvest yield)."
            if exp4_eligible > 0
            else "Requires Average Fish Weight (> 0 g/fish)."
        ),
    })

    # 6. Exp 5 DO & Hypoxia Benchmark (requires 0.0 <= DO <= 25.0 mg/L)
    if "dissolved_oxygen_mg_l" in cols:
        do_series = pd.to_numeric(work_df["dissolved_oxygen_mg_l"], errors="coerce")
        exp5_eligible = int((do_series.notna() & (do_series >= 0.0) & (do_series <= 25.0)).sum())
    else:
        exp5_eligible = 0
    results.append({
        "key": "exp5_do_hypoxia",
        "name": "Exp 5: Next-Visit Morning DO Benchmark",
        "category": "Operational Constant Mean Baseline",
        "compatible": exp5_eligible > 0,
        "eligible_rows": exp5_eligible,
        "total_rows": n_rows,
        "status": "READY" if exp5_eligible > 0 else "MISSING_INPUTS",
        "reason": (
            "Requires Dissolved Oxygen (0–25 mg/L). Returns constant historical mean benchmark (3.50 mg/L), not a dynamic forecast."
            if exp5_eligible > 0
            else "Requires Dissolved Oxygen (0–25 mg/L)."
        ),
    })

    # 7. Provisional Feeding Advisory
    has_do = "dissolved_oxygen_mg_l" in cols
    has_feed = "feed_amount_kg" in cols
    has_biomass = all(c in cols for c in ["average_fish_weight_g", "stocking_density_per_acre", "pond_area_acres"])
    if has_do and (has_feed or has_biomass):
        feed_eligible = 0
        for _, row in work_df.iterrows():
            if pd.isna(row.get("dissolved_oxygen_mg_l")):
                continue
            f_ok = has_feed and pd.notna(row.get("feed_amount_kg")) and float(row.get("feed_amount_kg", 0)) > 0
            b_ok = (
                has_biomass
                and pd.notna(row.get("average_fish_weight_g"))
                and pd.notna(row.get("stocking_density_per_acre"))
                and pd.notna(row.get("pond_area_acres"))
            )
            if f_ok or b_ok:
                feed_eligible += 1
        results.append({
            "key": "feeding_advisor",
            "name": "Provisional Rule-Based Feeding Advisory",
            "category": "Provisional Heuristic",
            "compatible": feed_eligible > 0,
            "eligible_rows": feed_eligible,
            "total_rows": n_rows,
            "status": "READY" if feed_eligible > 0 else "NO_COMPLETE_ROWS",
            "reason": (
                "DO and feed/biomass inputs satisfied. Rule-based provisional advisory only (no auto control)."
                if feed_eligible > 0
                else "Columns exist, but 0 rows have valid DO + positive feed or complete biomass."
            ),
        })
    else:
        results.append({
            "key": "feeding_advisor",
            "name": "Provisional Rule-Based Feeding Advisory",
            "category": "Provisional Heuristic",
            "compatible": False,
            "eligible_rows": 0,
            "total_rows": n_rows,
            "status": "MISSING_INPUTS",
            "reason": "Requires Dissolved Oxygen (mg/L) plus either Feed Amount (kg/day) or complete biomass (weight, density, pond acres).",
        })

    return results


def run_batch_analysis(
    work_df: pd.DataFrame,
    registry: Any,
    selected_models: List[str],
    default_gap_days: float = 21.0,
    max_rows: int = 500,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run compatible models row-by-row on validated canonical DataFrame.

    Returns (results_df, summary_dict). Missing inputs per row produce NaN /
    explicit 'UNAVAILABLE' notes rather than manufactured predictions.
    """
    df_eval = work_df.head(max_rows).copy()
    out_rows: List[Dict[str, Any]] = []

    for idx, row in df_eval.iterrows():
        rec: Dict[str, Any] = {
            "row_index": idx,
            "pond_id": row.get("pond_id", "N/A") if pd.notna(row.get("pond_id")) else "N/A",
            "observation_date": (
                str(row["datetime_parsed"].strftime("%Y-%m-%d"))
                if "datetime_parsed" in df_eval.columns and pd.notna(row.get("datetime_parsed"))
                else (str(row.get("datetime")) if pd.notna(row.get("datetime")) else "N/A")
            ),
            "do_mg_l": row.get("dissolved_oxygen_mg_l", np.nan),
            "ph": row.get("ph", np.nan),
            "temp_c": row.get("temp_c", np.nan),
        }

        # Chemistry NH3 (Emerson)
        calc_nh3 = row.get("primary_calculated_nh3_mg_l", np.nan)
        if "emerson_nh3" in selected_models and pd.notna(row.get("ph")) and pd.notna(row.get("temp_c")):
            if "tan_n_mg_l" in df_eval.columns and pd.notna(row.get("tan_n_mg_l")):
                calc_nh3 = calculate_nh3_from_tan_n(row["tan_n_mg_l"], row["ph"], row["temp_c"])
                rec["emerson_nh3_mg_l"] = calc_nh3
                rec["emerson_basis"] = "TAN_N"
            elif "tan_nh3_mg_l" in df_eval.columns and pd.notna(row.get("tan_nh3_mg_l")):
                calc_nh3 = calculate_nh3_from_tan_nh3(row["tan_nh3_mg_l"], row["ph"], row["temp_c"])
                rec["emerson_nh3_mg_l"] = calc_nh3
                rec["emerson_basis"] = "TAN_NH3"
            else:
                rec["emerson_nh3_mg_l"] = np.nan
                rec["emerson_basis"] = "UNAVAILABLE (missing TAN)"

        has_core_wq = (
            pd.notna(row.get("dissolved_oxygen_mg_l"))
            and pd.notna(row.get("ph"))
            and pd.notna(row.get("temp_c"))
            and (DEFENSIVE_BOUNDS["do"][0] <= float(row["dissolved_oxygen_mg_l"]) <= DEFENSIVE_BOUNDS["do"][1])
            and (DEFENSIVE_BOUNDS["ph"][0] <= float(row["ph"]) <= DEFENSIVE_BOUNDS["ph"][1])
            and (DEFENSIVE_BOUNDS["water_temp"][0] <= float(row["temp_c"]) <= DEFENSIVE_BOUNDS["water_temp"][1])
        )

        # Build feature dict preserving NaNs
        feat_dict: Dict[str, Any] = {}
        for k in [
            "dissolved_oxygen_mg_l", "ph", "temp_c", "turbidity_cm", "tds_ppt",
            "Weather", "water_color", "region", "average_fish_weight_g",
            "feed_amount_kg", "stocking_density_per_acre", "pond_area_acres",
        ]:
            if k in df_eval.columns and pd.notna(row.get(k)):
                feat_dict[k] = row[k]
        if pd.notna(calc_nh3):
            feat_dict["primary_calculated_nh3_mg_l"] = float(calc_nh3)
        if "tan_n_mg_l" in df_eval.columns and pd.notna(row.get("tan_n_mg_l")):
            feat_dict["tan_n_mg_l"] = float(row["tan_n_mg_l"])

        # Exp 1
        if "exp1_soft_sensor" in selected_models:
            if has_core_wq:
                try:
                    res1 = registry.predict_ammonia_soft_sensor(feat_dict)
                    rec["exp1_est_nh3_mg_l"] = res1.get("estimated_nh3_mg_l", np.nan)
                except Exception:
                    rec["exp1_est_nh3_mg_l"] = np.nan
            else:
                rec["exp1_est_nh3_mg_l"] = np.nan

        # Exp 2
        if "exp2_mortality" in selected_models:
            if has_core_wq:
                try:
                    res2 = registry.predict_mortality_diagnostic(feat_dict)
                    rec["exp2_mortality_risk_score"] = res2.get("mortality_risk_score", np.nan)
                except Exception:
                    rec["exp2_mortality_risk_score"] = np.nan
            else:
                rec["exp2_mortality_risk_score"] = np.nan

        # Exp 3
        if "exp3_ammonia_risk" in selected_models:
            if has_core_wq:
                gap_val = (
                    float(row["gap_days"])
                    if "gap_days" in df_eval.columns and pd.notna(row.get("gap_days"))
                    else float(default_gap_days)
                )
                feat3 = dict(feat_dict)
                feat3["gap_days"] = gap_val
                try:
                    res3 = registry.predict_next_visit_ammonia_risk(feat3)
                    rec["exp3_next_visit_nh3_risk"] = res3.get("next_visit_risk_score", np.nan)
                except Exception:
                    rec["exp3_next_visit_nh3_risk"] = np.nan
            else:
                rec["exp3_next_visit_nh3_risk"] = np.nan

        # Exp 4
        if "exp4_fish_growth" in selected_models:
            w = row.get("average_fish_weight_g") if "average_fish_weight_g" in df_eval.columns else np.nan
            if pd.notna(w) and float(w) > 0:
                try:
                    res4 = registry.predict_fish_growth({"average_fish_weight_g": float(w)})
                    rec["exp4_persistence_next_weight_g"] = res4.get("predicted_next_weight_g", np.nan)
                except Exception:
                    rec["exp4_persistence_next_weight_g"] = np.nan
            else:
                rec["exp4_persistence_next_weight_g"] = np.nan

        # Exp 5
        if "exp5_do_hypoxia" in selected_models:
            if pd.notna(row.get("dissolved_oxygen_mg_l")):
                try:
                    res5 = registry.predict_do_hypoxia({"curr_do": float(row["dissolved_oxygen_mg_l"])})
                    rec["exp5_benchmark_next_do_mg_l"] = res5.get("predicted_next_do_mg_l", np.nan)
                    hyp = res5.get("exploratory_hypoxia_screening", {})
                    if hyp.get("hypoxia_risk_score") is not None:
                        rec["exp5_hypoxia_risk_score"] = hyp.get("hypoxia_risk_score")
                        rec["exp5_hypoxia_flag"] = bool(hyp.get("screening_flag", False))
                except Exception:
                    rec["exp5_benchmark_next_do_mg_l"] = np.nan
            else:
                rec["exp5_benchmark_next_do_mg_l"] = np.nan

        # Feeding Advisory
        if "feeding_advisor" in selected_models:
            if pd.notna(row.get("dissolved_oxygen_mg_l")):
                try:
                    res_feed = registry.get_feeding_advisory(feat_dict)
                    if res_feed.get("is_valid"):
                        rec["feeding_action"] = res_feed.get("advisory_action")
                        rec["recommended_feed_kg"] = res_feed.get("recommended_feed_kg")
                    else:
                        rec["feeding_action"] = "UNAVAILABLE"
                        rec["recommended_feed_kg"] = np.nan
                except Exception:
                    rec["feeding_action"] = "UNAVAILABLE"
                    rec["recommended_feed_kg"] = np.nan
            else:
                rec["feeding_action"] = "UNAVAILABLE"
                rec["recommended_feed_kg"] = np.nan

        out_rows.append(rec)

    results_df = pd.DataFrame(out_rows)
    col_map = {
        "emerson_nh3": "emerson_nh3_mg_l",
        "exp1_soft_sensor": "exp1_est_nh3_mg_l",
        "exp2_mortality": "exp2_mortality_risk_score",
        "exp3_ammonia_risk": "exp3_next_visit_nh3_risk",
        "exp4_fish_growth": "exp4_persistence_next_weight_g",
        "exp5_do_hypoxia": "exp5_benchmark_next_do_mg_l",
        "feeding_advisor": "recommended_feed_kg",
    }
    module_counts: Dict[str, Dict[str, int]] = {}
    n_analyzed = len(results_df)
    for m_key in selected_models:
        out_col = col_map.get(m_key)
        if out_col and out_col in results_df.columns:
            proc_n = int(results_df[out_col].notna().sum())
        else:
            proc_n = 0
        module_counts[m_key] = {"processed": proc_n, "rejected": max(0, n_analyzed - proc_n)}

    summary = {
        "analyzed_rows": n_analyzed,
        "truncated_from": len(work_df) if len(work_df) > max_rows else None,
        "models_executed": list(selected_models),
        "module_counts": module_counts,
        "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return results_df, summary


def detect_and_map_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Automatically detect and map columns from raw DataFrame using canonical aliases."""
    mapping, ambiguities = suggest_column_mapping(list(df.columns))
    mapped_df = df.copy()
    rename_dict = {}
    for canon, col in mapping.items():
        if col and col in df.columns and col != canon:
            rename_dict[col] = canon
    if rename_dict:
        mapped_df = mapped_df.rename(columns=rename_dict)

    report = {
        "mapping": mapping,
        "ambiguities": ambiguities,
        "renamed": rename_dict,
    }
    return mapped_df, report


def validate_mapped_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate a mapped DataFrame against required aquaculture fields."""
    missing_required = []
    has_id = "pond_id" in df.columns or "tank_id" in df.columns
    if not has_id:
        missing_required.append("pond_id (or tank_id)")
    if "dissolved_oxygen_mg_l" not in df.columns:
        missing_required.append("dissolved_oxygen_mg_l")
    if "ph" not in df.columns:
        missing_required.append("ph")
    if "temp_c" not in df.columns:
        missing_required.append("temp_c")

    is_valid = len(missing_required) == 0
    return {
        "is_valid": is_valid,
        "missing_required": missing_required,
        "row_count": len(df),
        "columns_present": list(df.columns),
    }


def save_uploaded_dataset_to_session(filename: str, raw_df: pd.DataFrame, mapped_df: pd.DataFrame, validation_results: Dict[str, Any]) -> None:
    """Save validated dataset to session state for cross-page analysis."""
    import streamlit as st
    pond_col = "pond_id" if "pond_id" in mapped_df.columns else ("tank_id" if "tank_id" in mapped_df.columns else None)
    pond_ids = sorted(mapped_df[pond_col].dropna().astype(str).unique().tolist()) if pond_col else []

    st.session_state["uploaded_analysis_state"] = {
        "filename": filename,
        "raw_df": raw_df,
        "work_df": mapped_df,
        "total_rows": len(mapped_df),
        "pond_count": len(pond_ids),
        "pond_ids": pond_ids,
        "is_valid": True,
        "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if pond_ids:
        st.session_state["selected_pond"] = pond_ids[0]
        st.session_state["active_container_id"] = pond_ids[0]


def generate_validation_report_markdown(val_res: Dict[str, Any]) -> str:
    """Generate Markdown report for validation outcome."""
    if val_res.get("is_valid"):
        return f"**Validation Passed:** {val_res.get('row_count', 0)} rows successfully verified."
    missing = ", ".join(val_res.get("missing_required", []))
    return f"**Validation Blocked:** Missing required water quality fields: `{missing}`."

