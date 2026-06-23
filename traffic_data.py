from __future__ import annotations

import math
NODES = [
    {"id": "n1", "name": "Coimbatore Junction", "lat": 10.9950, "lng": 76.9629, "type": "major_hub", "congestionLevel": 0.78},
    {"id": "n2", "name": "Gandhipuram", "lat": 11.0168, "lng": 76.9558, "type": "commercial", "congestionLevel": 0.85},
    {"id": "n3", "name": "Ukkadam", "lat": 10.9997, "lng": 76.9670, "type": "intersection", "congestionLevel": 0.62},
    {"id": "n4", "name": "Singanallur", "lat": 11.0070, "lng": 77.0184, "type": "residential", "congestionLevel": 0.45},
    {"id": "n5", "name": "Peelamedu", "lat": 11.0266, "lng": 77.0178, "type": "commercial", "congestionLevel": 0.55},
    {"id": "n6", "name": "Coimbatore Airport", "lat": 11.0301, "lng": 77.0440, "type": "airport", "congestionLevel": 0.38},
    {"id": "n7", "name": "RS Puram", "lat": 10.9933, "lng": 76.9487, "type": "residential", "congestionLevel": 0.52},
    {"id": "n8", "name": "Ganapathy", "lat": 11.0393, "lng": 76.9787, "type": "residential", "congestionLevel": 0.40},
    {"id": "n9", "name": "Saibaba Colony", "lat": 11.0220, "lng": 76.9487, "type": "residential", "congestionLevel": 0.47},
    {"id": "n10", "name": "Race Course", "lat": 10.9993, "lng": 76.9543, "type": "landmark", "congestionLevel": 0.60},
    {"id": "n11", "name": "Sulur", "lat": 11.0254, "lng": 77.1246, "type": "intersection", "congestionLevel": 0.27},
    {"id": "n12", "name": "Ondiputhur", "lat": 11.0062, "lng": 77.0527, "type": "intersection", "congestionLevel": 0.34},
]

NODE_LOOKUP = {node["id"]: node for node in NODES}


def _geo_line(a, b, bend=0.0, steps=10):
    ax, ay = a["lng"], a["lat"]
    bx, by = b["lng"], b["lat"]
    dx = bx - ax
    dy = by - ay
    length = math.hypot(dx, dy) or 1.0
    ox = -dy / length * bend
    oy = dx / length * bend
    points = []
    for i in range(steps + 1):
        t = i / steps
        curve = math.sin(t * math.pi) * bend
        x = ax + dx * t + ox * curve * 0.02
        y = ay + dy * t + oy * curve * 0.02
        points.append([round(y, 6), round(x, 6)])
    return points


def _geo_distance(a, b):
    return math.hypot((a["lat"] - b["lat"]) * 111.0, (a["lng"] - b["lng"]) * 111.0 * math.cos(math.radians((a["lat"] + b["lat"]) / 2)))


EDGE_DEFINITIONS = [
    {"id": "e1", "sourceId": "n1", "targetId": "n3", "roadName": "Avinashi Road", "speedLimit": 60, "currentSpeed": 30, "congestionLevel": 0.72, "weight": 1.4, "laneCount": 4, "roadType": "arterial", "geometry": _geo_line(NODE_LOOKUP["n1"], NODE_LOOKUP["n3"], 0.3)},
    {"id": "e2", "sourceId": "n3", "targetId": "n4", "roadName": "Trichy Road", "speedLimit": 60, "currentSpeed": 41, "congestionLevel": 0.45, "weight": 8.4, "laneCount": 4, "roadType": "arterial", "geometry": _geo_line(NODE_LOOKUP["n3"], NODE_LOOKUP["n4"], 0.6)},
    {"id": "e3", "sourceId": "n4", "targetId": "n5", "roadName": "Sathyamangalam Road", "speedLimit": 50, "currentSpeed": 35, "congestionLevel": 0.42, "weight": 3.7, "laneCount": 2, "roadType": "arterial", "geometry": _geo_line(NODE_LOOKUP["n4"], NODE_LOOKUP["n5"], 0.35)},
    {"id": "e4", "sourceId": "n5", "targetId": "n6", "roadName": "Airport Road", "speedLimit": 60, "currentSpeed": 45, "congestionLevel": 0.35, "weight": 3.9, "laneCount": 4, "roadType": "arterial", "geometry": _geo_line(NODE_LOOKUP["n5"], NODE_LOOKUP["n6"], 0.3)},
    {"id": "e5", "sourceId": "n6", "targetId": "n11", "roadName": "Avinashi - Sulur Road", "speedLimit": 70, "currentSpeed": 58, "congestionLevel": 0.25, "weight": 9.3, "laneCount": 2, "roadType": "highway", "geometry": _geo_line(NODE_LOOKUP["n6"], NODE_LOOKUP["n11"], 1.0)},
    {"id": "e6", "sourceId": "n1", "targetId": "n7", "roadName": "Town Hall Link Road", "speedLimit": 40, "currentSpeed": 24, "congestionLevel": 0.58, "weight": 2.6, "laneCount": 2, "roadType": "local", "geometry": _geo_line(NODE_LOOKUP["n1"], NODE_LOOKUP["n7"], 0.2)},
    {"id": "e7", "sourceId": "n7", "targetId": "n9", "roadName": "DB Road", "speedLimit": 40, "currentSpeed": 25, "congestionLevel": 0.55, "weight": 2.8, "laneCount": 2, "roadType": "local", "geometry": _geo_line(NODE_LOOKUP["n7"], NODE_LOOKUP["n9"], 0.2)},
    {"id": "e8", "sourceId": "n9", "targetId": "n2", "roadName": "Nehru Street", "speedLimit": 40, "currentSpeed": 17, "congestionLevel": 0.82, "weight": 2.2, "laneCount": 2, "roadType": "local", "geometry": _geo_line(NODE_LOOKUP["n9"], NODE_LOOKUP["n2"], 0.2)},
    {"id": "e9", "sourceId": "n2", "targetId": "n8", "roadName": "Gandhipuram-Ganapathy Road", "speedLimit": 50, "currentSpeed": 33, "congestionLevel": 0.50, "weight": 3.5, "laneCount": 2, "roadType": "arterial", "geometry": _geo_line(NODE_LOOKUP["n2"], NODE_LOOKUP["n8"], 0.35)},
    {"id": "e10", "sourceId": "n7", "targetId": "n10", "roadName": "Lakshmipuram Road", "speedLimit": 40, "currentSpeed": 24, "congestionLevel": 0.58, "weight": 2.3, "laneCount": 2, "roadType": "local", "geometry": _geo_line(NODE_LOOKUP["n7"], NODE_LOOKUP["n10"], 0.22)},
    {"id": "e11", "sourceId": "n3", "targetId": "n10", "roadName": "Oppanakara Street", "speedLimit": 30, "currentSpeed": 15, "congestionLevel": 0.70, "weight": 5.5, "laneCount": 2, "roadType": "local", "geometry": _geo_line(NODE_LOOKUP["n3"], NODE_LOOKUP["n10"], 0.12)},
    {"id": "e12", "sourceId": "n4", "targetId": "n12", "roadName": "Singanallur-Ondiputhur Road", "speedLimit": 50, "currentSpeed": 38, "congestionLevel": 0.33, "weight": 5.9, "laneCount": 2, "roadType": "arterial", "geometry": _geo_line(NODE_LOOKUP["n4"], NODE_LOOKUP["n12"], 0.35)},
    {"id": "e13", "sourceId": "n12", "targetId": "n6", "roadName": "Ondiputhur-Airport Link", "speedLimit": 50, "currentSpeed": 40, "congestionLevel": 0.30, "weight": 4.3, "laneCount": 2, "roadType": "arterial", "geometry": _geo_line(NODE_LOOKUP["n12"], NODE_LOOKUP["n6"], 0.3)},
    {"id": "e14", "sourceId": "n5", "targetId": "n12", "roadName": "Peelamedu-Ondiputhur Road", "speedLimit": 50, "currentSpeed": 37, "congestionLevel": 0.36, "weight": 7.2, "laneCount": 2, "roadType": "local", "geometry": _geo_line(NODE_LOOKUP["n5"], NODE_LOOKUP["n12"], 0.4)},
    {"id": "e15", "sourceId": "n8", "targetId": "n5", "roadName": "Ganapathy-Peelamedu Road", "speedLimit": 50, "currentSpeed": 35, "congestionLevel": 0.44, "weight": 7.9, "laneCount": 2, "roadType": "arterial", "geometry": _geo_line(NODE_LOOKUP["n8"], NODE_LOOKUP["n5"], 0.35)},
    {"id": "e16", "sourceId": "n2", "targetId": "n5", "roadName": "NSR Road", "speedLimit": 50, "currentSpeed": 29, "congestionLevel": 0.60, "weight": 14.4, "laneCount": 4, "roadType": "arterial", "geometry": _geo_line(NODE_LOOKUP["n2"], NODE_LOOKUP["n5"], 0.45)},
    {"id": "e17", "sourceId": "n8", "targetId": "n12", "roadName": "Ganapathy-Ondiputhur Road", "speedLimit": 45, "currentSpeed": 31, "congestionLevel": 0.41, "weight": 6.8, "laneCount": 2, "roadType": "arterial", "geometry": _geo_line(NODE_LOOKUP["n8"], NODE_LOOKUP["n12"], 0.25)},
    {"id": "e18", "sourceId": "n7", "targetId": "n2", "roadName": "Cross Cut Road", "speedLimit": 40, "currentSpeed": 21, "congestionLevel": 0.67, "weight": 2.7, "laneCount": 2, "roadType": "local", "geometry": _geo_line(NODE_LOOKUP["n7"], NODE_LOOKUP["n2"], 0.18)},
]

for edge in EDGE_DEFINITIONS:
    a = NODE_LOOKUP[edge["sourceId"]]
    b = NODE_LOOKUP[edge["targetId"]]
    edge["distance_km"] = round(_geo_distance(a, b), 2)


INCIDENTS = [
    {"id": "i1", "type": "accident", "severity": "high", "description": "Two-vehicle collision on Avinashi Road near Ukkadam junction", "edgeId": "e1", "location": "Avinashi Road, near Ukkadam", "lat": 10.9973, "lng": 76.9649, "reportedAt": "2026-06-20T13:48:34.796Z", "active": True},
    {"id": "i2", "type": "roadwork", "severity": "medium", "description": "Road resurfacing work on Nehru Street, single lane operation", "edgeId": "e8", "location": "Nehru Street, Coimbatore", "lat": 11.0059, "lng": 76.9593, "reportedAt": "2026-06-20T11:33:34.809Z", "active": True},
    {"id": "i3", "type": "weather", "severity": "low", "description": "Reduced visibility due to light rain on Trichy Road", "edgeId": "e2", "location": "Trichy Road, Singanallur", "lat": 11.0033, "lng": 76.9927, "reportedAt": "2026-06-20T14:03:34.809Z", "active": True},
    {"id": "i4", "type": "breakdown", "severity": "medium", "description": "Heavy vehicle breakdown blocking outer lane on Airport Road", "edgeId": "e4", "location": "Airport Road, Peelamedu", "lat": 11.0284, "lng": 77.0309, "reportedAt": "2026-06-20T14:13:34.809Z", "active": True},
    {"id": "i5", "type": "accident", "severity": "low", "description": "Minor fender-bender on DB Road, cleared to shoulder", "edgeId": "e7", "location": "DB Road, RS Puram", "lat": 10.9963, "lng": 76.9515, "reportedAt": "2026-06-20T13:03:34.809Z", "active": False},
]


PEAK_HOURS = [
    {"hour": 0, "label": "12am", "congestionIndex": 0.05, "vehicleCount": 120},
    {"hour": 1, "label": "1am", "congestionIndex": 0.04, "vehicleCount": 80},
    {"hour": 2, "label": "2am", "congestionIndex": 0.03, "vehicleCount": 60},
    {"hour": 3, "label": "3am", "congestionIndex": 0.03, "vehicleCount": 50},
    {"hour": 4, "label": "4am", "congestionIndex": 0.05, "vehicleCount": 100},
    {"hour": 5, "label": "5am", "congestionIndex": 0.12, "vehicleCount": 250},
    {"hour": 6, "label": "6am", "congestionIndex": 0.35, "vehicleCount": 820},
    {"hour": 7, "label": "7am", "congestionIndex": 0.72, "vehicleCount": 2100},
    {"hour": 8, "label": "8am", "congestionIndex": 0.88, "vehicleCount": 3200},
    {"hour": 9, "label": "9am", "congestionIndex": 0.75, "vehicleCount": 2600},
    {"hour": 10, "label": "10am", "congestionIndex": 0.55, "vehicleCount": 1800},
    {"hour": 11, "label": "11am", "congestionIndex": 0.50, "vehicleCount": 1600},
    {"hour": 12, "label": "12pm", "congestionIndex": 0.62, "vehicleCount": 2000},
    {"hour": 13, "label": "1pm", "congestionIndex": 0.58, "vehicleCount": 1900},
    {"hour": 14, "label": "2pm", "congestionIndex": 0.45, "vehicleCount": 1400},
    {"hour": 15, "label": "3pm", "congestionIndex": 0.50, "vehicleCount": 1600},
    {"hour": 16, "label": "4pm", "congestionIndex": 0.68, "vehicleCount": 2200},
    {"hour": 17, "label": "5pm", "congestionIndex": 0.85, "vehicleCount": 3100},
    {"hour": 18, "label": "6pm", "congestionIndex": 0.92, "vehicleCount": 3800},
    {"hour": 19, "label": "7pm", "congestionIndex": 0.80, "vehicleCount": 2900},
    {"hour": 20, "label": "8pm", "congestionIndex": 0.60, "vehicleCount": 2000},
    {"hour": 21, "label": "9pm", "congestionIndex": 0.45, "vehicleCount": 1400},
    {"hour": 22, "label": "10pm", "congestionIndex": 0.28, "vehicleCount": 800},
    {"hour": 23, "label": "11pm", "congestionIndex": 0.14, "vehicleCount": 380},
]


MODEL_ACCURACY = {
    "overallAccuracy": 0.87,
    "maeScore": 0.063,
    "rmseScore": 0.082,
    "lastUpdated": "2026-06-20T14:56:19.743Z",
    "segments": [
        {"edgeId": "e1", "roadName": "Avinashi Road", "accuracy": 0.83},
        {"edgeId": "e2", "roadName": "Trichy Road", "accuracy": 0.83},
        {"edgeId": "e3", "roadName": "Sathyamangalam Road", "accuracy": 0.81},
        {"edgeId": "e4", "roadName": "Airport Road", "accuracy": 0.92},
        {"edgeId": "e5", "roadName": "Avinashi - Sulur Road", "accuracy": 0.88},
        {"edgeId": "e6", "roadName": "Town Hall Link Road", "accuracy": 0.80},
        {"edgeId": "e7", "roadName": "DB Road", "accuracy": 0.86},
        {"edgeId": "e8", "roadName": "Nehru Street", "accuracy": 0.90},
    ],
}


def _status(congestion: float) -> str:
    if congestion > 0.65:
        return "heavy"
    if congestion > 0.4:
        return "moderate"
    return "free"


def full_graph():
    return {"nodes": NODES, "edges": EDGE_DEFINITIONS}


def current_traffic_snapshot():
    return [
        {
            "edgeId": edge["id"],
            "roadName": edge["roadName"],
            "currentSpeed": edge["currentSpeed"],
            "speedLimit": edge["speedLimit"],
            "congestionLevel": edge["congestionLevel"],
            "vehicleCount": int(round(120 + edge["congestionLevel"] * 400)),
            "status": _status(edge["congestionLevel"]),
        }
        for edge in EDGE_DEFINITIONS
    ]


def active_incidents(include_resolved: bool = False):
    return [incident for incident in INCIDENTS if include_resolved or incident.get("active")]


def analytics_summary():
    current = current_traffic_snapshot()
    avg_congestion = sum(item["congestionLevel"] for item in current) / len(current)
    total_vehicles = sum(item["vehicleCount"] for item in current)
    avg_speed = round(sum(item["currentSpeed"] for item in current) / len(current))
    active_count = len(active_incidents())
    status = "Heavy" if avg_congestion > 0.65 else "Moderate" if avg_congestion > 0.4 else "Normal"
    trend = "stable" if avg_congestion < 0.55 else "rising"
    return {
        "avgCongestion": round(avg_congestion, 2),
        "totalVehicles": total_vehicles,
        "activeIncidents": active_count,
        "affectedRoutes": active_count,
        "avgSpeed": avg_speed,
        "networkStatus": status,
        "congestionTrend": trend,
    }


def peak_hours():
    return PEAK_HOURS


def model_accuracy():
    return MODEL_ACCURACY


def prediction_series(edge_id: str, hours_ahead: int = 12):
    edge = next((item for item in EDGE_DEFINITIONS if item["id"] == edge_id), EDGE_DEFINITIONS[0])
    start_hour = 15
    pattern = [0.0, 0.19, 0.38, 0.42, 0.31, 0.15, 0.0, -0.12, -0.25, -0.33, -0.34, -0.34]
    out = []
    for i in range(hours_ahead):
        hour = (start_hour + i) % 24
        label = f"{hour % 12 or 12}{'am' if hour < 12 else 'pm'}"
        congestion = max(0.05, min(1.0, round(edge["congestionLevel"] + pattern[i % len(pattern)] - 0.05, 2)))
        estimated_speed = max(10, round(edge["speedLimit"] * (1 - congestion * 0.55)))
        out.append(
            {
                "hour": hour,
                "label": label,
                "congestionLevel": congestion,
                "estimatedSpeed": estimated_speed,
                "confidence": round(max(0.78, 1.06 - i * 0.02), 2),
            }
        )
    return out
