"""
Mexico Vacation Destination Suitability — MCDA Engine
Multi-Criteria Decision Analysis using min-max normalization + weighted overlay
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Criterion definitions
# ---------------------------------------------------------------------------

# (raw_column, display_name, benefit=True means higher raw = better)
CRITERIA = {
    "accessibility": {
        "label": "Accessibility",
        "components": [
            ("airport_dist_km",      "Airport Distance",    False, 0.5),
            ("intl_flight_routes",   "Int'l Flight Routes", True,  0.5),
        ],
    },
    "climate": {
        "label": "Climate Comfort",
        "components": [
            ("avg_temp_c",      "Avg Temperature",   True,  0.5),   # scored via comfort curve
            ("annual_precip_mm","Annual Precip",     False, 0.5),
        ],
    },
    "safety": {
        "label": "Safety",
        "components": [
            ("homicide_rate_per100k", "Homicide Rate",      False, 0.6),
            ("travel_advisory_level", "Travel Advisory",    False, 0.4),
        ],
    },
    "cost": {
        "label": "Affordability",
        "components": [
            ("avg_hotel_rate_usd",         "Hotel Rate",         False, 0.5),
            ("avg_daily_tourist_spend_usd","Daily Spend",        False, 0.5),
        ],
    },
    "attractions": {
        "label": "Attraction Density",
        "components": [
            ("attraction_score",  "Overall Attractions", True, 0.35),
            ("beach_quality",     "Beach Quality",       True, 0.2),
            ("cultural_score",    "Cultural Score",      True, 0.25),
            ("nature_score",      "Nature Score",        True, 0.2),
        ],
    },
    "hazard": {
        "label": "Low Hazard Exposure",
        "components": [
            ("hurricane_risk", "Hurricane Risk", False, 0.4),
            ("seismic_risk",   "Seismic Risk",   False, 0.3),
            ("flood_risk",     "Flood Risk",     False, 0.3),
        ],
    },
}

# Default scenario weights (must sum to 1.0)
DEFAULT_WEIGHTS = {
    "accessibility": 0.20,
    "climate":       0.15,
    "safety":        0.25,
    "cost":          0.15,
    "attractions":   0.15,
    "hazard":        0.10,
}

TRAVELER_PROFILES = {
    "Balanced": {
        "accessibility": 0.20, "climate": 0.15, "safety": 0.25,
        "cost": 0.15, "attractions": 0.15, "hazard": 0.10,
    },
    "Budget Traveler": {
        "accessibility": 0.15, "climate": 0.15, "safety": 0.20,
        "cost": 0.35, "attractions": 0.10, "hazard": 0.05,
    },
    "Luxury Traveler": {
        "accessibility": 0.25, "climate": 0.20, "safety": 0.20,
        "cost": 0.05, "attractions": 0.20, "hazard": 0.10,
    },
    "Eco-Adventure": {
        "accessibility": 0.10, "climate": 0.15, "safety": 0.15,
        "cost": 0.10, "attractions": 0.25, "hazard": 0.25,
    },
    "Culture & History": {
        "accessibility": 0.20, "climate": 0.10, "safety": 0.25,
        "cost": 0.15, "attractions": 0.25, "hazard": 0.05,
    },
    "Beach & Relaxation": {
        "accessibility": 0.20, "climate": 0.25, "safety": 0.20,
        "cost": 0.10, "attractions": 0.15, "hazard": 0.10,
    },
}


def _minmax(series: pd.Series, benefit: bool) -> pd.Series:
    """Min-max normalize a series. If benefit=False, invert so higher = better."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    normalized = (series - mn) / (mx - mn)
    return normalized if benefit else (1 - normalized)


def _temperature_comfort(avg_temp: pd.Series) -> pd.Series:
    """
    Bell-curve comfort: optimal ~24°C, discomfort increases toward extremes.
    Returns 0-1 score where 1 = most comfortable.
    """
    optimal = 24.0
    sigma = 6.0
    score = np.exp(-0.5 * ((avg_temp - optimal) / sigma) ** 2)
    return pd.Series(score, index=avg_temp.index)


def compute_criterion_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a 0-1 score for each of the six criteria.
    Returns a DataFrame with columns = criterion keys, index = destination.
    """
    scores = pd.DataFrame(index=df.index)

    for key, crit in CRITERIA.items():
        weighted_sum = pd.Series(0.0, index=df.index)
        for col, _, benefit, w in crit["components"]:
            if col == "avg_temp_c":
                norm = _temperature_comfort(df[col])
            else:
                norm = _minmax(df[col], benefit)
            weighted_sum += w * norm
        scores[key] = weighted_sum

    return scores


def compute_suitability(df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    """
    Full MCDA pipeline.
    Returns enriched DataFrame with criterion scores and composite suitability index.
    """
    assert abs(sum(weights.values()) - 1.0) < 1e-6, "Weights must sum to 1.0"

    criterion_scores = compute_criterion_scores(df)

    composite = pd.Series(0.0, index=df.index)
    for key, w in weights.items():
        composite += w * criterion_scores[key]

    result = df.copy()
    for key in CRITERIA:
        result[f"score_{key}"] = criterion_scores[key]
    result["suitability_index"] = composite
    result["rank"] = result["suitability_index"].rank(ascending=False).astype(int)

    return result.sort_values("suitability_index", ascending=False)


def load_data(path: str = "data/destinations.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.set_index("destination")
    return df


def run_all_profiles(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        name: compute_suitability(df, weights)
        for name, weights in TRAVELER_PROFILES.items()
    }


if __name__ == "__main__":
    df = load_data()
    results = compute_suitability(df, DEFAULT_WEIGHTS)
    print("\n=== Balanced Scenario Rankings ===")
    cols = ["rank", "suitability_index"] + [f"score_{k}" for k in CRITERIA]
    print(results[cols].round(3).to_string())
