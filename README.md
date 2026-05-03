# Cyclone Risk Baseline Stress Test

This project tests whether tropical cyclone behaviour from 1988–2023 is still consistent with the historical baselines a reinsurer might use for pricing and capital decisions.

The analysis uses TropiCycloneNet Data1D and focuses on five basins: Western Pacific (WP), Eastern Pacific (EP), North Atlantic (NA), South Indian (SI), and South Pacific (SP). The project examines three risk channels: severity, rapid intensification, and movement-related exposure.

## Findings

- **Severity**: the high-intensity storm share shows statistically meaningful upward trends in WP and SI. SP is treated as a sensitivity case. EP and NA are broadly flat.
- **Rapid intensification**: meaningful upward trends appear in SP, WP, and SI. EP is broadly flat. NA shows a borderline downward tendency.
- **Movement**: only SP shows a meaningful slowdown in translation speed, at around -2.1 km/h per decade.
- **Cross-channel view**: SP is the only basin showing change across all three risk channels.

A single global cyclone baseline would miss these regional differences. The recommendation is to use basin-specific monitoring before renewal pricing or capital decisions.

## How to run

```bash
pip install -r requirements.txt
jupyter lab
