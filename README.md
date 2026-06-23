# Traffic Flow Predictor and Route Optimizer

A Flask mini project for visualizing a Coimbatore traffic network, computing routes, showing incidents, forecasting congestion, and displaying analytics.

## Features

- Live traffic network dashboard
- Route planner with A* and Dijkstra-style graph routing
- Optional OSRM road-following route geometry
- Incident monitoring
- 12-hour congestion predictions
- Analytics dashboard with peak-hour and model accuracy charts

## Project Structure

- `app.py` - Flask app, page routes, and API endpoints
- `algorithms.py` - route computation and OSRM fallback logic
- `traffic_data.py` - nodes, edges, incidents, predictions, and analytics data
- `templates/` - HTML pages
- `static/css/style.css` - styling
- `static/js/app.js` - map rendering and frontend behavior
- `render.yaml` - Render deployment configuration

## Run Locally

```powershell
cd D:\Traffic
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

If `python` is not available in PATH:

```powershell
& "C:\Users\praga\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" app.py
```

## Deploy On Render

1. Create a new GitHub repository.
2. Push this folder to that repository.
3. Go to Render and choose `New` -> `Blueprint`.
4. Select the GitHub repository.
5. Render will read `render.yaml` automatically.
6. Click `Apply` to deploy.

The Render build uses:

```text
pip install -r requirements.txt
```

The Render start command uses:

```text
gunicorn app:app
```

## Optional OSRM

The app can use a custom OSRM server by setting:

```text
OSRM_URL=https://your-osrm-server
```

If this variable is not set, the app tries public OSRM endpoints and then falls back to graph routing.
"# Traffic-Flow-Predictor" 
