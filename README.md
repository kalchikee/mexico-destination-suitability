# Mexico Vacation Destination Suitability Analysis

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://mexico-destination-suitability-62m22b96avwochwrezd33n.streamlit.app/)

A GIS-based multi-criteria decision analysis (MCDA) tool that evaluates and ranks major vacation destinations across Mexico using real spatial, socioeconomic, and environmental data.

## Destinations
Cancún · Playa del Carmen · Tulum · Puerto Vallarta · Los Cabos · Mexico City · Oaxaca

## Criteria
| Criterion | Weight (Balanced) | Description |
|---|---|---|
| Safety | 25% | Homicide rate + US travel advisory level |
| Accessibility | 20% | Airport distance + international flight routes |
| Climate Comfort | 15% | Temperature comfort curve + annual precipitation |
| Affordability | 15% | Average hotel rate + daily tourist spend |
| Attraction Density | 15% | Beaches, culture, nature, and heritage sites |
| Low Hazard Exposure | 10% | Hurricane, seismic, and flood risk |

## Traveler Profiles
Six pre-defined weighting scenarios simulate different traveler priorities:
**Balanced · Budget · Luxury · Eco-Adventure · Culture & History · Beach & Relaxation**

## Data Sources
- **INEGI / SESNSP** — State-level homicide rates (2023)
- **US State Department** — Travel advisory classifications (2024)
- **WorldClim v2.1 / CONAGUA** — 30-year climate normals (1991–2020)
- **OAG Aviation** — International flight route counts (2024)
- **CENAPRED** — Atlas Nacional de Riesgos (hurricane, seismic, flood)
- **DATATUR / Banco de México** — Tourism expenditure surveys (2023)
- **SECTUR** — Attraction and tourism density statistics (2023)

## Methodology
All variables are min-max normalized to a 0–1 scale. Temperature comfort uses a Gaussian bell curve centered at 24 °C. The composite suitability index is a weighted dot product of criterion scores. Weights are user-adjustable via sidebar sliders and auto-normalize to sum to 1.0.

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
