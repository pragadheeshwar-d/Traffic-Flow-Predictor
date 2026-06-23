from flask import Flask, jsonify, render_template, request

from algorithms import compute_alternative_routes, compute_route, route_request_defaults
from traffic_data import (
    active_incidents,
    analytics_summary,
    current_traffic_snapshot,
    full_graph,
    model_accuracy,
    peak_hours,
    prediction_series,
)


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("home.html", active_page="home")


@app.route("/routing")
def routing_page():
    return render_template("routing.html", active_page="routing")


@app.route("/predictions")
def predictions_page():
    return render_template("predictions.html", active_page="predictions")


@app.route("/incidents")
def incidents_page():
    return render_template("incidents.html", active_page="incidents")


@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html", active_page="analytics")


@app.get("/api/graph/nodes")
def api_graph_nodes():
    return jsonify(full_graph()["nodes"])


@app.get("/api/graph/edges")
def api_graph_edges():
    return jsonify(full_graph()["edges"])


@app.get("/api/graph/full")
def api_graph_full():
    return jsonify(full_graph())


@app.get("/api/traffic/current")
def api_traffic_current():
    return jsonify(current_traffic_snapshot())


@app.get("/api/traffic/incidents")
def api_traffic_incidents():
    return jsonify(active_incidents(include_resolved=True))


@app.get("/api/traffic/predict")
def api_traffic_predict():
    edge_id = request.args.get("edgeId", "e1")
    hours_ahead = int(request.args.get("hoursAhead", 12))
    return jsonify(prediction_series(edge_id=edge_id, hours_ahead=hours_ahead))


@app.post("/api/routing/optimal")
def api_routing_optimal():
    payload = request.get_json(force=True, silent=True) or {}
    source_id, target_id, algorithm, optimize_for, avoid_incidents = route_request_defaults(payload)
    return jsonify(
        compute_route(
            source_id,
            target_id,
            algorithm=algorithm,
            optimize_for=optimize_for,
            avoid_incidents=avoid_incidents,
        )
    )


@app.post("/api/routing/alternatives")
def api_routing_alternatives():
    payload = request.get_json(force=True, silent=True) or {}
    source_id, target_id, algorithm, optimize_for, avoid_incidents = route_request_defaults(payload)
    return jsonify(
        compute_alternative_routes(
            source_id,
            target_id,
            algorithm=algorithm,
            optimize_for=optimize_for,
            avoid_incidents=avoid_incidents,
        )
    )


@app.get("/api/analytics/summary")
def api_analytics_summary():
    return jsonify(analytics_summary())


@app.get("/api/analytics/peak-hours")
def api_analytics_peak_hours():
    return jsonify(peak_hours())


@app.get("/api/analytics/model-accuracy")
def api_analytics_model_accuracy():
    return jsonify(model_accuracy())


if __name__ == "__main__":
    app.run(debug=True)
