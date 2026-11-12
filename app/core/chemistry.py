"""
Aqueous Ammonia Dissociation Chemistry Module - Phase 1 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Implements the audited v2 Emerson et al. (1975) equilibrium formulation for
calculating molecular toxic un-ionized ammonia (NH3) from Total Ammonia Nitrogen (TAN).

Scientific Background:
  In aqueous solutions, total ammonia exists in an equilibrium between ionized
  ammonium (NH4+, relatively non-toxic) and un-ionized ammonia (NH3, highly toxic):
      NH3 + H2O <===> NH4+ + OH-

  The dissociation constant (pKa) is temperature-dependent (Emerson et al., 1975):
      pKa = 0.09018 + (2729.92 / (Temp_C + 273.15))

  The fraction (f) of un-ionized ammonia is governed by pH and pKa:
      f = 1 / (10^(pKa - pH) + 1)

Molecular Weight Conversion Rule:
  - When TAN is reported as Nitrogen (TAN-N / NH3-N), the molecular weight ratio
    (MW_NH3 / MW_N = 17.031 / 14.007 ≈ 1.21589) MUST be applied exactly once to yield
    molecular NH3 in mg/L:
        NH3_molecular = f * TAN_N * (17.031 / 14.007)
  - When TAN is reported as molecular Ammonia (TAN-NH3), TAN is already expressed
    on an NH3 molecular mass basis, so the conversion factor MUST NOT be applied:
        NH3_molecular = f * TAN_NH3

Scientific Boundaries & Disclaimer:
  Calculated un-ionized ammonia is an equilibrium-derived theoretical estimate,
  NOT a direct analytical laboratory measurement. Unverified field test-kit
  readings must not be treated as certified laboratory bioassays.
"""

from typing import Union, Optional, Dict, Any
import numpy as np
import pandas as pd

from app.config import (
    EMERSON_PKA_INTERCEPT,
    EMERSON_PKA_SLOPE,
    ABSOLUTE_ZERO_CELSIUS,
    MW_RATIO_NH3_N,
)


def calculate_pka(temp_c: Union[float, int, None]) -> float:
    """
    Computes the temperature-dependent dissociation constant (pKa) for ammonia in water.

    Formula (Emerson et al., 1975):
        pKa = 0.09018 + 2729.92 / (temp_c + 273.15)

    Parameters:
        temp_c: Water temperature in degrees Celsius (°C).

    Returns:
        pKa as a float, or np.nan if input is missing or unphysical.
    """
    if temp_c is None:
        return np.nan
    try:
        val = float(temp_c)
        if np.isnan(val) or val <= ABSOLUTE_ZERO_CELSIUS or val > 100.0:
            return np.nan
        temp_k = val + 273.15
        return EMERSON_PKA_INTERCEPT + (EMERSON_PKA_SLOPE / temp_k)
    except (ValueError, TypeError, OverflowError):
        return np.nan


def calculate_unionized_fraction(ph: Union[float, int, None], temp_c: Union[float, int, None]) -> float:
    """
    Computes the fraction (f) of total ammonia present in toxic un-ionized (NH3) form.

    Formula:
        f = 1.0 / (10.0 ** (pKa - pH) + 1.0)

    Parameters:
        ph: Water pH (standard units, 0.0 to 14.0).
        temp_c: Water temperature in degrees Celsius (°C).

    Returns:
        Fraction f (between 0.0 and 1.0), or np.nan if inputs are invalid/missing.
    """
    if ph is None or temp_c is None:
        return np.nan
    try:
        ph_val = float(ph)
        if np.isnan(ph_val) or ph_val < 0.0 or ph_val > 14.0:
            return np.nan

        pka = calculate_pka(temp_c)
        if np.isnan(pka):
            return np.nan

        exponent = pka - ph_val
        # Prevent numerical overflow on extreme exponents
        if exponent > 50.0:
            return 0.0
        elif exponent < -50.0:
            return 1.0

        return 1.0 / (10.0 ** exponent + 1.0)
    except (ValueError, TypeError, OverflowError):
        return np.nan


def calculate_nh3_from_tan_n(
    tan_n_mg_l: Union[float, int, None],
    ph: Union[float, int, None],
    temp_c: Union[float, int, None],
    round_digits: Optional[int] = 5
) -> float:
    """
    Computes molecular toxic un-ionized ammonia (mg/L molecular NH3) from TAN
    expressed on a nitrogen basis (TAN-N / NH3-N).

    Applies the Emerson et al. (1975) equilibrium fraction AND the molecular-weight
    conversion factor (17.031 / 14.007) exactly once.

    Formula:
        NH3 = f * TAN_N * (17.031 / 14.007)

    Parameters:
        tan_n_mg_l: Total Ammonia Nitrogen in mg/L as N.
        ph: Water pH.
        temp_c: Water temperature in °C.
        round_digits: Number of decimal places to round to (default 5, matches v2 audit).
                      Pass None for full double-precision float.

    Returns:
        Molecular NH3 in mg/L, or np.nan if any input is missing/invalid.
        Never returns 0.0 for missing inputs.
    """
    if tan_n_mg_l is None or ph is None or temp_c is None:
        return np.nan

    try:
        tan_val = float(tan_n_mg_l)
        if np.isnan(tan_val) or tan_val < 0.0:
            return np.nan

        f = calculate_unionized_fraction(ph, temp_c)
        if np.isnan(f):
            return np.nan

        nh3_val = f * tan_val * MW_RATIO_NH3_N
        if round_digits is not None:
            return round(nh3_val, round_digits)
        return nh3_val
    except (ValueError, TypeError, OverflowError):
        return np.nan


def calculate_nh3_from_tan_nh3(
    tan_nh3_mg_l: Union[float, int, None],
    ph: Union[float, int, None],
    temp_c: Union[float, int, None],
    round_digits: Optional[int] = 5
) -> float:
    """
    Computes molecular toxic un-ionized ammonia (mg/L molecular NH3) from TAN
    expressed on a molecular ammonia basis (TAN-NH3).

    Because TAN is ALREADY expressed on an NH3 molecular mass basis, the un-ionized
    fraction f is applied directly WITHOUT the 17.031 / 14.007 conversion factor.

    Formula:
        NH3 = f * TAN_NH3

    Parameters:
        tan_nh3_mg_l: Total Ammonia Nitrogen in mg/L as molecular NH3.
        ph: Water pH.
        temp_c: Water temperature in °C.
        round_digits: Number of decimal places to round to (default 5, matches v2 audit).

    Returns:
        Molecular NH3 in mg/L, or np.nan if any input is missing/invalid.
        Never returns 0.0 for missing inputs.
    """
    if tan_nh3_mg_l is None or ph is None or temp_c is None:
        return np.nan

    try:
        tan_val = float(tan_nh3_mg_l)
        if np.isnan(tan_val) or tan_val < 0.0:
            return np.nan

        f = calculate_unionized_fraction(ph, temp_c)
        if np.isnan(f):
            return np.nan

        nh3_val = f * tan_val
        if round_digits is not None:
            return round(nh3_val, round_digits)
        return nh3_val
    except (ValueError, TypeError, OverflowError):
        return np.nan


def calculate_ammonia_toxicity(
    tan_mg_l: Union[float, int, None],
    ph: Union[float, int, None],
    temp_c: Union[float, int, None],
    basis: str = "TAN_N",
    round_digits: Optional[int] = 5
) -> Dict[str, Any]:
    """
    Unified, transparent ammonia toxicity calculation interface.

    Accepts the reporting basis explicitly ("TAN_N" or "TAN_NH3") and returns
    both the calculated un-ionized ammonia and complete calculation metadata.

    Parameters:
        tan_mg_l: Total ammonia concentration (mg/L).
        ph: Water pH.
        temp_c: Water temperature in °C.
        basis: Either "TAN_N" (default) or "TAN_NH3". Case-insensitive.
        round_digits: Decimal places for rounding (default 5).

    Returns:
        Dictionary with calculation results, methodology, and scientific disclaimers.

    Raises:
        ValueError: If basis is unrecognized.
    """
    norm_basis = basis.strip().upper().replace("-", "_")
    if norm_basis in ["TAN_N", "NH3_N", "N"]:
        nh3 = calculate_nh3_from_tan_n(tan_mg_l, ph, temp_c, round_digits=round_digits)
        mw_applied = True
        desc = "Emerson et al. (1975) equilibrium with (17.031 / 14.007) molecular weight conversion"
    elif norm_basis in ["TAN_NH3", "NH3", "MOLECULAR"]:
        nh3 = calculate_nh3_from_tan_nh3(tan_mg_l, ph, temp_c, round_digits=round_digits)
        mw_applied = False
        desc = "Emerson et al. (1975) equilibrium direct fraction (no MW conversion)"
    else:
        raise ValueError(
            f"Invalid ammonia reporting basis: '{basis}'. Must be 'TAN_N' (as Nitrogen) or 'TAN_NH3' (as molecular NH3)."
        )

    pka = calculate_pka(temp_c)
    f = calculate_unionized_fraction(ph, temp_c)

    return {
        "calculated_nh3_mg_l": nh3,
        "reporting_basis": norm_basis,
        "mw_conversion_applied": mw_applied,
        "fraction_unionized": None if np.isnan(f) else (round(f, 6) if round_digits else f),
        "pka": None if np.isnan(pka) else (round(pka, 4) if round_digits else pka),
        "is_valid": bool(not np.isnan(nh3)),
        "method": desc,
        "scientific_disclaimer": (
            "Calculated theoretical un-ionized ammonia based on aqueous equilibrium; "
            "not a direct analytical laboratory measurement. Unverified field readings "
            "are not certified laboratory bioassays."
        )
    }


def calculate_nh3_series(
    tan_series: pd.Series,
    ph_series: pd.Series,
    temp_series: pd.Series,
    basis: str = "TAN_N",
    round_digits: Optional[int] = 5
) -> pd.Series:
    """
    Vectorized calculation of molecular NH3 across pandas Series.

    Preserves missing values (NaN) without silent zero-replacement.
    """
    norm_basis = basis.strip().upper().replace("-", "_")
    if norm_basis in ["TAN_N", "NH3_N", "N"]:
        func = lambda row: calculate_nh3_from_tan_n(row[0], row[1], row[2], round_digits=round_digits)
    elif norm_basis in ["TAN_NH3", "NH3", "MOLECULAR"]:
        func = lambda row: calculate_nh3_from_tan_nh3(row[0], row[1], row[2], round_digits=round_digits)
    else:
        raise ValueError(f"Invalid reporting basis: '{basis}'.")

    df_temp = pd.concat([tan_series, ph_series, temp_series], axis=1)
    return df_temp.apply(func, axis=1)

