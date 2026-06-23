from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from traffic_data import NODE_LOOKUP


def route_request_defaults(payload: dict[str, Any]) -> tuple[str, str, str, str, bool]:
    return (
        payload.get("sourceNodeId") or payload.get("source_id") or payload.get("sourceNode") or "n1",
        payload.get("targetNodeId") or payload.get("target_id") or payload.get("targetNode") or "n6",
        payload.get("algorithm", "astar"),
        payload.get("optimizeFor", "time"),
        bool(payload.get("avoidIncidents", True)),
    )


def _osrm_route_request(source: dict[str, Any], target: dict[str, Any], alternatives: bool = False):
    coords = f"{source['lng']},{source['lat']};{target['lng']},{target['lat']}"
    params = {"overview": "full", "geometries": "geojson", "alternatives": "true" if alternatives else "false"}
    candidates = []
    osrm_url = os.environ.get("OSRM_URL")
    if osrm_url:
        candidates.append(osrm_url)
    candidates.extend([
        "https://router.project-osrm.org",
        "https://routing.openstreetmap.de/routed-car",
    ])

    for base in candidates:
        url = f"{base.rstrip('/')}/route/v1/driving/{coords}?{urlencode(params)}"
        try:
            with urlopen(url, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, ValueError):
            continue
        routes = []
        for route in payload.get("routes", []):
            geometry = route.get("geometry", {}).get("coordinates", [])
            routes.append(
                {
                    "distance": route.get("distance", 0.0) / 1000.0,
                    "duration": route.get("duration", 0.0) / 60.0,
                    "geometry": [[lat, lng] for lng, lat in geometry],
                    "routeSource": "osrm",
                }
            )
        if routes:
            return routes
    raise RuntimeError("OSRM routing service is unavailable")


def _route_payload(
    *,
    source_id: str,
    target_id: str,
    algorithm: str,
    optimize_for: str,
    path_nodes: list[str],
    path_edges: list[dict[str, Any]],
    is_primary: bool,
    label: str,
    route_source: str,
):
    distance = sum(float(edge.get("distance_km") or 0.0) for edge in path_edges)
    duration = sum((float(edge.get("distance_km") or 0.0) / max(1.0, float(edge.get("currentSpeed") or edge.get("speedLimit") or 30.0))) * 60 for edge in path_edges)
    congestion_score = sum(float(edge.get("congestionLevel") or 0.0) for edge in path_edges) / max(1, len(path_edges))
    geometry = []
    for edge in path_edges:
        if edge.get("geometry"):
            geometry.extend(edge["geometry"] if not geometry else edge["geometry"][1:])
    return {
        "sourceId": source_id,
        "targetId": target_id,
        "algorithm": algorithm,
        "optimizeFor": optimize_for,
        "isPrimary": is_primary,
        "label": label,
        "distance": round(distance, 2),
        "duration": round(duration, 1),
        "congestionScore": round(congestion_score, 3),
        "nodeIds": path_nodes,
        "edgeIds": [edge["id"] for edge in path_edges],
        "geometry": geometry,
        "routeSource": route_source,
    }


def compute_route(
    source_node_id: str,
    target_node_id: str,
    algorithm: str = "astar",
    optimize_for: str = "time",
    avoid_incidents: bool = True,
):
    source = NODE_LOOKUP[source_node_id]
    target = NODE_LOOKUP[target_node_id]
    osrm_routes = _osrm_route_request(source, target, alternatives=False)
    selected = min(osrm_routes, key=lambda route: route["distance"] if optimize_for == "distance" else route["duration"])
    return {
        **selected,
        "sourceId": source_node_id,
        "targetId": target_node_id,
        "algorithm": algorithm,
        "optimizeFor": optimize_for,
        "isPrimary": True,
        "label": f"Primary {algorithm.upper()} Route",
        "nodeIds": [source_node_id, target_node_id],
        "edgeIds": [],
    }


def compute_alternative_routes(
    source_node_id: str,
    target_node_id: str,
    algorithm: str = "astar",
    optimize_for: str = "time",
    avoid_incidents: bool = True,
):
    primary = compute_route(
        source_node_id,
        target_node_id,
        algorithm=algorithm,
        optimize_for=optimize_for,
        avoid_incidents=avoid_incidents,
    )
    if not primary:
        return []
    if primary.get("routeSource") == "osrm":
        return [primary]
    return [primary]
