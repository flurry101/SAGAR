# M4 Marine and Weather Integration

This directory contains the M4 integration for marine and weather data.  The
implementation follows a small, layered path:

```text
graph node -> tool wrapper -> adapter -> live source or local fallback data
```

The graph nodes only collect data and return state updates.  They do not own
routing, API endpoints, or risk calculations.

## Implemented components

### Adapters

- `app/adapters/open_meteo_adapter.py` combines Open-Meteo marine and weather
  observations for a location and time.
- `app/adapters/open_meteo_client.py` provides shared, in-process Open-Meteo
  caching so weather and SST requests reuse a marine response.
- `app/adapters/sst_adapter.py` supplies sea-surface temperature.
- `app/adapters/static_hazard_adapter.py` supplies hazard alerts.
- `app/adapters/static_pfz_adapter.py` supplies Potential Fishing Zones (PFZs)
  through NOAA live-front detection with a local GeoJSON fallback.
- `app/adapters/amfitrite_hab_adapter.py` supports Sentinel-2/RDNet HAB
  detection when imagery and model dependencies are available.  When a tile
  has a usable ROI but no loaded RDNet model, it returns an honest unresolved
  result with Sentinel-2 provenance rather than requiring inference bands.

### Tools

- `app/tools/weather_tools.py`
  - wave, wind, swell, hazard, and batch weather tools.
- `app/tools/marine_tools.py`
  - PFZ, SST, HAB, and batch marine tools.

The wrappers are plain Python functions intended for direct use or later
LangGraph/LangChain tool binding.

### Graph nodes

- `app/graph/nodes/weather.py` returns `weather_observations` and optional
  `hazard_alerts`.
- `app/graph/nodes/marine.py` returns `pfz_data` and
  `marine_observations`.

### Fallback data

Local data is kept in `data/fallback/`:

- `marine_forecast_sample.json` for Open-Meteo fallback forecasts.
- `hazard_sample.json` and `hazard_demo.json` for hazard fallback data.
- `pfz.geojson` for PFZ fallback data.

Open-Meteo and PFZ adapters try their live sources first and fall back to the
local data when network retrieval is unavailable.  Fallback provenance is
reported as tier 3.  The HAB adapter returns an unresolved result when usable
imagery or model inference is unavailable; `DEMO_HAB_MOCK=1` enables its
explicit demo-only HAB response.

## Dependencies

`httpx` is already declared in `requirements.txt` for live API requests.

The core M4 weather, PFZ, hazard, and SST paths use the existing backend
dependencies.  Optional HAB real-imagery validation additionally needs:

- `numpy`
- `rasterio`
- `torch` and `timm` for RDNet inference
- Sentinel-2/STAC network access and RDNet model weights for live inference

`numpy` is installed in the local virtual environment for the HAB image tests;
add it to project dependency management before relying on those tests in a
fresh environment.

## Running M4 tests

From `SAGAR/`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
..\.venv\Scripts\python.exe -m pytest backend\tests\orca_m4 -q -p no:cacheprovider
```

The tests mock network calls where appropriate and exercise fallback paths.
For a narrow HAB real-imagery check:

```powershell
..\.venv\Scripts\python.exe -m pytest `
  backend\tests\orca_m4\test_adapters.py::TestAmfitriteHABRealImageryPipeline -q
```

## Known limitations

- Two source-inspection HAB tests still use ORCA's old relative path.  From
  `backend/tests/orca_m4/` they look for `../../backend/app/...`; SAGAR's
  correct path is `../../app/adapters/amfitrite_hab_adapter.py`.  These are
  test-path compatibility failures, not adapter failures.
- Real HAB inference needs optional imagery dependencies, model weights, and
  external STAC access.  Without them the adapter deliberately returns an
  unresolved result or uses the explicit demo mode.
- Starting the full FastAPI application currently requires PostgreSQL at the
  configured database URL; this is separate from the M4 fallback tests.
