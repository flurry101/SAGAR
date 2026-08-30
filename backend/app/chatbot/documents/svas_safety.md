# SVAS Safety Rules — Vessel Safety Assessment System

## What is SVAS?

SVAS (Safety and Vulnerability Assessment System) is a vessel safety assessment framework developed by INCOIS for evaluating whether sea conditions are safe for a specific vessel type. Unlike generic weather warnings that apply to everyone, SVAS evaluates conditions relative to a vessel's specific physical characteristics.

## The Core SVAS Formula

The primary safety threshold in SVAS is the wave height limit relative to a vessel's beam width:

```
Maximum Safe Wave Height = Beam Width (m) / 4.0
```

### Example

- A vessel with a beam width of 4.5 meters has a safe wave limit of **1.125 meters**.
- If the forecast wave height at the vessel's location and time is **2.8 meters**, this exceeds the limit by 149%.
- Result: **WAVE_HEIGHT_EXCEEDED** → **SEVERE hazard flag**.

## Why This Formula Matters

The beam width / 4.0 rule is a simplified capsizing risk metric:
- Waves higher than 25% of a vessel's beam width create significant rolling forces.
- For small artisanal vessels (beam width 2-5m), this means waves of just 0.5-1.25m can be dangerous.
- This is why generic "3m wave warning" broadcasts are insufficient — they don't account for vessel size.

## Additional Safety Checks in ORCA

Beyond the SVAS wave formula, ORCA's deterministic Risk Engine also checks:

### Wind Speed
- Wind speed thresholds vary by vessel type and Beaufort scale.
- Motorized trawlers can tolerate higher winds than non-motorized craft.

### Visibility
- Reduced visibility (fog, heavy rain) increases collision and navigation risk.
- Threshold: typically < 2 km visibility triggers a warning.

### Geofence Violations
- Marine Protected Areas (MPAs) that vessels should not enter.
- International maritime boundaries (EEZ limits).

### Active Hazard Advisories
- Cyclone warnings from IMD.
- Tsunami warnings from INCOIS.
- High wave alerts.

## Risk Levels in ORCA

| Level | Meaning |
|:---|:---|
| **FAVORABLE** | All conditions within vessel safety limits |
| **MODERATE_RISK** | Some conditions approaching limits |
| **ELEVATED_RISK** | One or more conditions near threshold |
| **SEVERE_HAZARD** | Critical thresholds exceeded — trip not recommended |
| **INSUFFICIENT_INFORMATION** | Cannot assess — critical data missing |

## Sources

- INCOIS SVAS Documentation: https://incois.gov.in
- ORCA Risk Engine: Deterministic Python module (no LLM involved)
