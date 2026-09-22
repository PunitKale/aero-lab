# Deploy Aero Lab

The dashboard and API must be hosted together on a Python-capable service. Browser requests use same-origin `/api/circuits`, `/api/simulate` and `/api/verify`. The production entry point `src.realtrack.web:app` reuses the solver and Python dashboard without changing the model or layout.

## Render configuration

Connect the GitHub repository and create a Blueprint using its root `render.yaml`, or create a Python Web Service with these values:

| Setting | Value |
|---|---|
| Root directory | `motorsport_aero_project` |
| Build | `pip install -r requirements-web.txt` |
| Start | `gunicorn src.realtrack.web:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 90 --access-logfile -` |
| Health path | `/healthz` |
| Python | `3.12.10` |
| Environment | `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1` |
| Instance | Free |

After deployment open the generated HTTPS URL and check all five circuits, Run Simulation, Verify prediction, exports and replay. GitHub Pages alone cannot execute the Python API.

Official references: [Flask deployment](https://render.com/docs/deploy-flask), [free service limitations](https://render.com/docs/free). Free instances may sleep when idle, so the first request may need a cold start.

## Operating assumptions

- One worker preserves bounded in-memory caches and a single active simulation. Concurrent calculations return HTTP 429 with Retry-After; users can retry.
- JSON requests are limited to 1 MB. Unexpected errors do not expose stack traces to visitors. TLS is provided by the hosting platform.
- Static serving is restricted to `reports/`; never place private files in that public directory. Credentials and Python files remain outside it.
- The app has no authentication and serves public geometry and synthetic project outputs only.
- MySQL belongs to the separate research pipeline. Live runs are ephemeral and are not inserted into the saved database. Saved setups remain in the visitor's browser.
- A finer-mesh check is numerical sensitivity only, not real-world validation.
- Keep `.env`, tokens, virtual environments and database/runtime files out of commits. `.env.example` contains placeholders only.

## Local production-server test

From the project folder, install `requirements-web.txt` and pytest, then run:

```powershell
python -m pytest tests/test_web.py tests/test_efficiency.py tests/test_dynamic_api.py tests/test_comparison.py -q
waitress-serve --host=127.0.0.1 --port=8765 src.realtrack.web:app
```
