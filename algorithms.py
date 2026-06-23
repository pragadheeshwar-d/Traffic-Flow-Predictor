from __future__ import annotations

import heapq
import json
import math
import os
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from traffic_data import INCIDENTS, NODES, NODE_LOOKUP, active_incidents, full_graph


def route_request_defaults(payload: dict[str, Any]) -> tuple[str, str, str, str, bool]:
    return (
        payload.get("sourceNodeId") or payload.get("source_id") or payload.get("sourceNode") or "n1",
        payload.get("targetNodeId") or payload.get("target_id") or payload.get("targetNode") or "n6",
        payload.get("algorithm", "astar"),
        payload.get("optimizeFor", "time"),
        bool(payload.get("avoidIncidents", True)),
    )


def _distance_km(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.hypot((a["lat"] - b["lat"]) * 111.0, (a["lng"] - b["lng"]) * 111.0 * math.cos(math.radians((a["lat"] + b["lat"]) / 2)))


def _route_cost(edge: dict[str, Any], optimize_for: str) -> float:
    distance = edge.get("distance_km") or 1.0
    speed = max(1.0, edge.get("currentSpeed") or edge.get("speedLimit") or 30.0)
    congestion = float(edge.get("congestionLevel") or 0.0)
    if optimize_for == "distance":
        return distance * (1 + congestion * 0.08)
    if optimize_for == "fuel":
        return distance * (1 + congestion * 0.45)
    return (distance / speed) * 60 * (1 + congestion * 0.25)


def _heuristic(node_a: dict[str, Any], node_b: dict[str, Any]) -> float:
    return _distance_km(node_a, node_b)


def _build_adj(block_edges: set[str] | None = None, avoid_incidents: bool = False):
    blocked = block_edges or set()
    active_edge_ids = {incident["edgeId"] for incident in INCIDENTS if incident.get("active") and incident.get("edgeId")}
    adjacency: dict[str, list[dict[str, Any]]] = {node["id"]: [] for node in NODES}
    for edge in full_graph()["edges"]:
        if edge["id"] in blocked:
            continue
        if avoid_incidents and edge["id"] in active_edge_ids:
            continue
        adjacency[edge["sourceId"]].append(edge)
        adjacency[edge["targetId"]].append(
            {
                **edge,
                "sourceId": edge["targetId"],
                "targetId": edge["sourceId"],
                "reversed": True,
            }
        )
    return adjacency


def _dijkstra_or_astar(
    source_id: str,
    target_id: str,
    *,
    algorithm: str,
    optimize_for: str,
    avoid_incidents: bool,
    block_edges: set[str] | None = None,
):
    source = NODE_LOOKUP[source_id]
    target = NODE_LOOKUP[target_id]
    adjacency = _build_adj(block_edges=block_edges, avoid_incidents=avoid_incidents)

    frontier: list[tuple[float, str]] = [(0.0, source_id)]
    came_from: dict[str, tuple[str, dict[str, Any]]] = {}
    cost_so_far: dict[str, float] = {source_id: 0.0}

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == target_id:
            break

        for edge in adjacency.get(current, []):
            next_id = edge["targetId"]
            new_cost = cost_so_far[current] + _route_cost(edge, optimize_for)
            new_cost *= 1 + float(edge.get("congestionLevel") or 0.0) * 0.15
            if next_id not in cost_so_far or new_cost < cost_so_far[next_id]:
                cost_so_far[next_id] = new_cost
                priority = new_cost
                if algorithm == "astar":
                    priority += _heuristic(NODE_LOOKUP[next_id], target)
                heapq.heappush(frontier, (priority, next_id))
                came_from[next_id] = (current, edge)

    if target_id not in came_from and source_id != target_id:
        return None

    path_nodes = [target_id]
    path_edges = []
    cursor = target_id
    while cursor != source_id:
        prev = came_from.get(cursor)
        if not prev:
            break
        prev_node, edge = prev
        path_nodes.append(prev_node)
        path_edges.append(edge)
        cursor = prev_node

    path_nodes.reverse()
    path_edges.reverse()
    return _route_payload(
        source_id=source_id,
        target_id=target_id,
        algorithm=algorithm,
        optimize_for=optimize_for,
        path_nodes=path_nodes,
        path_edges=path_edges,
        is_primary=True,
        label=f"Primary {algorithm.upper()} Route",
        route_source="graph",
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
    return None


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
    if osrm_routes:
        selected = min(osrm_routes, key=lambda route: route["distance"] if optimize_for == "distance" else route["duration"])
        fallback_edges = []
        for i in range(len(selected["geometry"]) - 1):
            fallback_edges.append(
                {
                    "id": f"osrm-{i}",
                    "distance_km": max(0.01, _distance_km(
                        {"lat": selected["geometry"][i][0], "lng": selected["geometry"][i][1]},
                        {"lat": selected["geometry"][i + 1][0], "lng": selected["geometry"][i + 1][1]},
                    )),
                    "currentSpeed": 30,
                    "speedLimit": 30,
                    "congestionLevel": 0.0,
                    "geometry": [selected["geometry"][i], selected["geometry"][i + 1]],
                }
            )
        return {
            **selected,
            "sourceId": source_node_id,
            "targetId": target_node_id,
            "algorithm": algorithm,
            "optimizeFor": optimize_for,
            "isPrimary": True,
            "label": f"Primary {algorithm.upper()} Route",
            "nodeIds": [source_node_id, target_node_id],
            "edgeIds": [edge["id"] for edge in fallback_edges],
        }
    return _dijkstra_or_astar(
        source_node_id,
        target_node_id,
        algorithm=algorithm,
        optimize_for=optimize_for,
        avoid_incidents=avoid_incidents,
    )


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
    edges = primary.get("edgeIds", [])
    alternatives = [primary]
    for edge_id in edges[:3]:
        route = _dijkstra_or_astar(
            source_node_id,
            target_node_id,
            algorithm=algorithm,
            optimize_for=optimize_for,
            avoid_incidents=avoid_incidents,
            block_edges={edge_id},
        )
        if route and route["nodeIds"] != primary["nodeIds"]:
            route["isPrimary"] = False
            route["label"] = f"Alternative via {route['nodeIds'][1] if len(route['nodeIds']) > 1 else route['targetId']}"
            alternatives.append(route)
    return alternatives
