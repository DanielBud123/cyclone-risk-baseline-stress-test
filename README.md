# Cyclone Risk Baseline Stress Test

This project tests whether tropical cyclone behaviour from 1988–2023 is still consistent with the historical baselines a reinsurer might use for pricing and capital decisions.

The analysis uses TropiCycloneNet Data1D and focuses on five basins: Western Pacific (WP), Eastern Pacific (EP), North Atlantic (NA), South Indian (SI), and South Pacific (SP). The project examines three risk channels: severity, rapid intensification, and movement-related exposure.

## Method

Each risk channel is reduced to a yearly basin-level series: high-intensity share (peak wind ≥ 58.1 m/s), rapid-intensification share (≥ 30 kt over any 24-hour window), and mean translation speed. The trend test is rank-based Kendall tau. The slope estimate is Theil-Sen, with OLS reported as a reference and 95% CIs from the Theil-Sen rank distribution. Broad-period summaries use bootstrap 95% CIs over storms. Basin-years with fewer than three storms are dropped so a single storm cannot dominate a yearly share. Findings are reported per basin; this is diagnostic of past change, not a forecast.

## Findings

- **Severity**: the high-intensity storm share shows statistically meaningful upward trends in WP and SI. SP is treated as a sensitivity case. EP and NA are broadly flat.
- **Rapid intensification**: meaningful upward trends appear in SP, WP, and SI. EP is broadly flat. NA shows a borderline downward tendency.
- **Movement**: only SP shows a meaningful slowdown in translation speed, at around -2.1 km/h per decade.
- **Cross-channel view**: SP is the only basin showing change across all three risk channels.

A single global cyclone baseline would miss these regional differences. The recommendation is to use basin-specific monitoring before renewal pricing or capital decisions.

## Repo structure

- `src/load_data1d.py` — TropiCycloneNet Data1D loader, denormalisation, per-storm metrics.
- `notebooks/01_data_loading.ipynb` — builds the storm-level summary from raw data.
- `notebooks/02_intensity_tail_shift.ipynb` — severity analysis.
- `notebooks/03_rapid_intensification.ipynb` — rapid-intensification analysis.
- `notebooks/04_exposure_duration_risk.ipynb` — translation-speed analysis with a persistence cross-check.
- `data/processed/` — storm-level and timestep-level parquet files used by notebooks 02–04.

## How to run

Notebooks 02–04 run standalone from the processed parquets already checked in under `data/processed/`. Notebook 01 rebuilds those parquets from the raw TropiCycloneNet Data1D files, which are not shipped in this repo, download them from the dataset's source and place under `data/raw/TCND_Data1D/Data1D/` if you want to re-run the loader.

```bash
pip install -r requirements.txt
jupyter lab
```
