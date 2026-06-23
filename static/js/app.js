(function () {
  const page = document.body.dataset.page;
  const api = (path) => fetch(path).then((r) => {
    if (!r.ok) throw new Error(`${path} failed`);
    return r.json();
  });

  function colorForCongestion(v) {
    if (v > 0.65) return "#ef4444";
    if (v > 0.4) return "#f59e0b";
    return "#22c55e";
  }

  function labelForCongestion(v) {
    if (v > 0.65) return "Heavy";
    if (v > 0.4) return "Moderate";
    return "Free";
  }

  function incidentBadge(type) {
    return ({ accident: "red", roadwork: "orange", weather: "blue", breakdown: "yellow" }[type] || "red");
  }

  function incidentColor(severity) {
    return ({ high: "#ef4444", medium: "#f59e0b", low: "#22c55e" }[severity] || "#94a3b8");
  }

  function kpi(label, value, sub = "", tone = "") {
    return `<div class="card kpi"><div class="label">${label}</div><div class="value ${tone}">${value}</div>${sub ? `<div class="sub">${sub}</div>` : ""}</div>`;
  }

  function incidentCard(incident) {
    const age = Math.max(0, Math.floor((Date.now() - new Date(incident.reportedAt).getTime()) / 60000));
    return `<div class="incident">
      <div class="incident-head">
        <span class="pill ${incidentBadge(incident.type)}">${incident.type.toUpperCase()}</span>
        <span class="status ${incident.severity === "high" ? "red" : incident.severity === "medium" ? "orange" : "green"}">${incident.severity.toUpperCase()} SEVERITY</span>
      </div>
      <div style="font-size:14px;line-height:1.45">${incident.description}</div>
      <div class="muted" style="margin-top:8px;font-size:12px">${incident.location} - ${age}m ago - ${incident.active ? "Active" : "Resolved"}</div>
    </div>`;
  }

  function trafficRow(edge) {
    const pct = Math.round(edge.congestionLevel * 100);
    return `<div class="incident" style="display:grid;gap:6px">
      <div style="display:flex;justify-content:space-between;gap:10px;align-items:center">
        <strong>${edge.roadName}</strong>
        <span class="status ${pct > 65 ? "red" : pct > 40 ? "orange" : "green"}">${pct}%</span>
      </div>
      <div class="bar"><div style="width:${pct}%;background:${colorForCongestion(edge.congestionLevel)}"></div></div>
      <div class="muted" style="font-size:12px">${edge.currentSpeed} km/h - ${edge.speedLimit} km/h limit - ${edge.vehicleCount} vehicles</div>
    </div>`;
  }

  function chartSvg(points, width, height, opts = {}) {
    const pad = 28;
    const yMax = opts.yMax || 1;
    const plotW = width - pad * 2;
    const plotH = height - pad * 2;
    const step = points.length > 1 ? plotW / (points.length - 1) : plotW;
    const xs = points.map((_, i) => pad + i * step);
    const ys = points.map((p) => pad + (1 - Math.max(0, Math.min(yMax, p.y)) / yMax) * plotH);
    const poly = xs.map((x, i) => `${x},${ys[i]}`).join(" ");
    const bars = opts.bar
      ? points.map((p, i) => {
          const h = (Math.max(0, Math.min(yMax, p.y)) / yMax) * plotH;
          const x = pad + i * step + 1;
          const y = pad + (plotH - h);
          const w = Math.max(4, step - 2);
          return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="3" fill="${p.fill || opts.stroke || "#38bdf8"}"></rect>`;
        }).join("")
      : "";
    const tLines = (opts.thresholds || []).map((t) => {
      const y = pad + (1 - t.value / yMax) * plotH;
      return `<line x1="${pad}" y1="${y}" x2="${width - pad}" y2="${y}" stroke="${t.stroke}" stroke-dasharray="5 4"></line><text x="${width - pad - 4}" y="${y - 4}" text-anchor="end" font-size="10" fill="${t.stroke}">${t.label}</text>`;
    }).join("");
    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="chart">
      <rect x="0" y="0" width="${width}" height="${height}" rx="14" fill="rgba(255,255,255,0.01)"></rect>
      <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="rgba(255,255,255,0.12)"></line>
      <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="rgba(255,255,255,0.12)"></line>
      ${tLines}
      ${opts.bar ? bars : `<polyline points="${poly}" fill="none" stroke="${opts.stroke || "#38bdf8"}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"></polyline>`}
      ${!opts.bar ? points.map((p, i) => `<circle cx="${xs[i]}" cy="${ys[i]}" r="3.5" fill="${p.fill || opts.stroke || "#38bdf8"}"></circle>`).join("") : ""}
      ${points.map((p, i) => `<text x="${xs[i]}" y="${height - 10}" text-anchor="middle" font-size="10" fill="rgba(148,163,184,0.95)">${p.label}</text>`).join("")}
    </svg>`;
  }

  function initMap(el, graph, options = {}) {
    if (!el || !graph || !window.L) return null;
    const map = L.map(el, { scrollWheelZoom: false }).setView([11.015, 76.99], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    const nodesById = new Map(graph.nodes.map((n) => [n.id, n]));
    const activeIds = new Set((options.incidents || []).map((i) => i.edgeId).filter(Boolean));
    const routeEdges = new Set((options.route?.edgeIds || []));
    const bounds = [];
    const routeOnly = !!options.routeOnly;

    if (!routeOnly) {
      graph.edges.forEach((edge) => {
        const pts = edge.geometry && edge.geometry.length
          ? edge.geometry.map(([lat, lng]) => [lat, lng])
          : [
            [nodesById.get(edge.sourceId).lat, nodesById.get(edge.sourceId).lng],
            [nodesById.get(edge.targetId).lat, nodesById.get(edge.targetId).lng],
          ];
        pts.forEach((p) => bounds.push(p));
        L.polyline(pts, {
          color: routeEdges.has(edge.id) ? "#38bdf8" : activeIds.has(edge.id) ? "#fb7185" : (edge.congestionLevel > 0.65 ? "#f97316" : edge.congestionLevel > 0.4 ? "#f59e0b" : "#22c55e"),
          weight: routeEdges.has(edge.id) ? 5 : activeIds.has(edge.id) ? 4.5 : 3,
          opacity: routeEdges.has(edge.id) ? 0.98 : activeIds.has(edge.id) ? 0.95 : 0.7,
          dashArray: routeEdges.has(edge.id) ? null : edge.congestionLevel > 0.65 ? "6 4" : null,
        }).addTo(map).bindPopup(`${edge.roadName}<br>${Math.round(edge.congestionLevel * 100)}% congestion`);
      });
    }

    graph.nodes.forEach((node) => {
      bounds.push([node.lat, node.lng]);
      const color = node.congestionLevel > 0.65 ? "#ef4444" : node.congestionLevel > 0.4 ? "#f59e0b" : "#22c55e";
      L.circleMarker([node.lat, node.lng], {
        radius: 7 + node.congestionLevel * 3,
        color: "rgba(255,255,255,0.9)",
        weight: 1,
        fillColor: color,
        fillOpacity: 0.9,
      }).addTo(map).bindPopup(`<strong>${node.name}</strong><br>${node.type}`);
    });

    if (options.incidents) {
      options.incidents.forEach((incident) => {
        L.circleMarker([incident.lat, incident.lng], {
          radius: 8,
          color: "#fff",
          weight: 1,
          fillColor: incidentColor(incident.severity),
          fillOpacity: 0.85,
        }).addTo(map).bindPopup(`<strong>${incident.type.toUpperCase()}</strong><br>${incident.description}`);
      });
    }

    if (options.route && options.route.geometry && options.route.geometry.length) {
      const routePoints = options.route.geometry.map(([lat, lng]) => [lat, lng]);
      L.polyline(routePoints, { color: "#38bdf8", weight: 7, opacity: 0.98, lineJoin: "round", lineCap: "round" }).addTo(map);
      bounds.push(...routePoints);
    }

    if (bounds.length) map.fitBounds(bounds, { padding: [30, 30] });
    return map;
  }

  async function loadGraph() {
    return api("/api/graph/full");
  }

  async function loadTraffic() {
    return api("/api/traffic/current");
  }

  async function loadIncidents() {
    return api("/api/traffic/incidents");
  }

  async function loadSummary() {
    return api("/api/analytics/summary");
  }

  async function loadPeaks() {
    return api("/api/analytics/peak-hours");
  }

  async function loadAccuracy() {
    return api("/api/analytics/model-accuracy");
  }

  async function loadPredictions(edgeId) {
    return api(`/api/traffic/predict?edgeId=${encodeURIComponent(edgeId)}&hoursAhead=12`);
  }

  function fillSelect(select, items, selectedId, labelFn) {
    select.innerHTML = items.map((item) => `<option value="${item.id}" ${item.id === selectedId ? "selected" : ""}>${labelFn(item)}</option>`).join("");
  }

  async function homePage() {
    const [graph, traffic, incidents, summary] = await Promise.all([loadGraph(), loadTraffic(), loadIncidents(), loadSummary()]);
    const activeIncidents = incidents.filter((i) => i.active);
    document.getElementById("home-kpis").innerHTML = [
      kpi("Avg Congestion", `${Math.round(summary.avgCongestion * 100)}%`, summary.congestionTrend || ""),
      kpi("Total Vehicles", summary.totalVehicles.toLocaleString(), "on network"),
      kpi("Active Incidents", String(summary.activeIncidents), "", summary.activeIncidents > 0 ? "red" : "green"),
      kpi("Network Status", summary.networkStatus, `Avg speed ${summary.avgSpeed} km/h`, summary.networkStatus === "Heavy" ? "red" : summary.networkStatus === "Moderate" ? "amber" : "green"),
    ].join("");
    document.getElementById("home-incidents").innerHTML = activeIncidents.map(incidentCard).join("") || `<div class="muted">No active incidents.</div>`;
    document.getElementById("home-traffic").innerHTML = traffic.slice().sort((a, b) => b.congestionLevel - a.congestionLevel).slice(0, 4).map(trafficRow).join("");
    initMap(document.getElementById("home-map"), graph, { incidents: activeIncidents });
  }

  async function routingPage() {
    const graph = await loadGraph();
    const incidents = await loadIncidents();
    const form = document.getElementById("route-form");
    const routeSummary = document.getElementById("route-summary");
    const alternativesEl = document.getElementById("route-alternatives");
    const sourceSelect = document.getElementById("source-node");
    const targetSelect = document.getElementById("target-node");
    const algorithmSelect = document.getElementById("route-algorithm");
    const optimizeSelect = document.getElementById("route-optimize");
    const avoidEl = document.getElementById("avoid-incidents");
    const mapEl = document.getElementById("routing-map");
    let routeMap = null;
    let currentRoute = null;
    let altRoutes = [];

    fillSelect(sourceSelect, graph.nodes, "n1", (n) => n.name);
    fillSelect(targetSelect, graph.nodes, "n6", (n) => n.name);

    function renderRoute(route) {
      if (!route) {
        routeSummary.innerHTML = `<div class="muted">No route yet.</div>`;
        return;
      }
      const routeName = graph.nodes.find((n) => n.id === route.sourceId)?.name || route.sourceId;
      const targetName = graph.nodes.find((n) => n.id === route.targetId)?.name || route.targetId;
      routeSummary.innerHTML = `
        <div class="route-meta">
          <div class="route-box">
            <h3>${route.label}</h3>
            <p>${routeName} to ${targetName}</p>
          </div>
          <div class="stats-2">
            <div class="mini"><div class="m-label">Distance</div><div class="m-value">${route.distance.toFixed(1)} km</div></div>
            <div class="mini"><div class="m-label">Duration</div><div class="m-value">${route.duration.toFixed(0)} min</div></div>
            <div class="mini"><div class="m-label">Congestion</div><div class="m-value" style="color:${colorForCongestion(route.congestionScore)}">${Math.round(route.congestionScore * 100)}%</div></div>
            <div class="mini"><div class="m-label">Via nodes</div><div class="m-value">${route.nodeIds.length}</div></div>
          </div>
          <div class="footer-note">Source: ${route.routeSource.toUpperCase()} routing</div>
        </div>`;
    }

    function renderAlts(routes) {
      alternativesEl.innerHTML = routes.map((route, idx) => `<div class="incident"><strong>${idx === 0 ? "Primary Route" : `Alternative ${idx}`}</strong><div class="muted" style="margin-top:4px;font-size:12px">${route.distance.toFixed(1)} km - ${route.duration.toFixed(0)} min - Cong: ${Math.round(route.congestionScore * 100)}%</div></div>`).join("") || `<div class="muted">No alternatives yet.</div>`;
    }

    async function compute(alternative = false) {
      const payload = {
        sourceNodeId: sourceSelect.value,
        targetNodeId: targetSelect.value,
        algorithm: algorithmSelect.value,
        optimizeFor: optimizeSelect.value,
        avoidIncidents: avoidEl.checked,
      };
      const endpoint = alternative ? "/api/routing/alternatives" : "/api/routing/optimal";
      const result = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).then((r) => r.json());
      if (alternative) {
        altRoutes = result;
        renderAlts(altRoutes);
        currentRoute = altRoutes[0] || currentRoute;
      } else {
        currentRoute = result;
        renderRoute(currentRoute);
      }
      if (routeMap) routeMap.remove();
      routeMap = initMap(mapEl, graph, {
        route: currentRoute,
        incidents: incidents.filter((i) => i.active),
        routeOnly: true,
      });
      document.getElementById("selected-origin").textContent = graph.nodes.find((n) => n.id === sourceSelect.value)?.name || sourceSelect.value;
      document.getElementById("selected-target").textContent = graph.nodes.find((n) => n.id === targetSelect.value)?.name || targetSelect.value;
    }

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      compute(false);
    });
    document.getElementById("show-alternatives").addEventListener("click", () => compute(true));
    renderAlts([]);
    compute(false);
  }

  async function predictionsPage() {
    const graph = await loadGraph();
    const select = document.getElementById("prediction-segment");
    const roadName = document.getElementById("prediction-road-name");
    const roadMeta = document.getElementById("prediction-road-meta");
    const speed = document.getElementById("prediction-speed");
    const limit = document.getElementById("prediction-limit");
    const peak = document.getElementById("prediction-peak");
    const peakTime = document.getElementById("prediction-peak-time");
    const horizon = document.getElementById("prediction-horizon");
    const chart = document.getElementById("prediction-chart");
    const breakdown = document.getElementById("prediction-breakdown");

    const edges = graph.edges;
    fillSelect(select, edges, "e1", (e) => e.roadName);

    async function render(edgeId) {
      const edge = edges.find((e) => e.id === edgeId) || edges[0];
      const data = await loadPredictions(edge.id);
      roadName.textContent = edge.roadName;
      roadMeta.textContent = `${edge.currentSpeed} km/h current speed - ${edge.speedLimit} km/h limit - ${Math.round(edge.congestionLevel * 100)}% congestion`;
      speed.textContent = `${edge.currentSpeed} km/h`;
      limit.textContent = `${edge.speedLimit} km/h`;
      const top = data.reduce((best, item) => (item.congestionLevel > best.congestionLevel ? item : best), data[0]);
      peak.textContent = `${Math.round(top.congestionLevel * 100)}%`;
      peak.style.color = colorForCongestion(top.congestionLevel);
      peakTime.textContent = `at ${top.label}`;
      horizon.innerHTML = `<div class="forecast-grid">${data.map((p) => `<div class="forecast"><div class="t1">${p.label}</div><div class="t2" style="color:${colorForCongestion(p.congestionLevel)}">${Math.round(p.congestionLevel * 100)}%</div><div class="t3">${p.estimatedSpeed} km/h</div></div>`).join("")}</div>`;
      chart.innerHTML = chartSvg(data.map((p) => ({ label: p.label, y: p.congestionLevel, fill: colorForCongestion(p.congestionLevel) })), 1000, 320, {
        yMax: 1,
        stroke: "#38bdf8",
        thresholds: [
          { value: 0.65, label: "Heavy", stroke: "#ef4444" },
          { value: 0.4, label: "Moderate", stroke: "#f59e0b" },
        ],
      });
      breakdown.innerHTML = data.map((p) => `<div class="forecast"><div class="t1">${p.label}</div><div class="t2" style="color:${colorForCongestion(p.congestionLevel)}">${Math.round(p.congestionLevel * 100)}%</div><div class="t3">${p.estimatedSpeed} km/h</div></div>`).join("");
    }

    select.addEventListener("change", () => render(select.value));
    await render(select.value);
  }

  async function incidentsPage() {
    const [graph, traffic, incidents, summary] = await Promise.all([loadGraph(), loadTraffic(), loadIncidents(), loadSummary()]);
    const active = incidents.filter((i) => i.active);
    const resolved = incidents.filter((i) => !i.active);
    document.getElementById("incident-kpis").innerHTML = [
      kpi("Avg Congestion", `${Math.round(summary.avgCongestion * 100)}%`, summary.congestionTrend || ""),
      kpi("Total Vehicles", summary.totalVehicles.toLocaleString(), "on network"),
      kpi("Active Incidents", String(active.length), "", active.length ? "red" : "green"),
      kpi("Network Status", summary.networkStatus, `Avg speed ${summary.avgSpeed} km/h`, summary.networkStatus === "Heavy" ? "red" : summary.networkStatus === "Moderate" ? "amber" : "green"),
    ].join("");
    document.getElementById("active-incidents").innerHTML = active.map(incidentCard).join("") || `<div class="muted">No active incidents.</div>`;
    document.getElementById("resolved-incidents").innerHTML = resolved.map(incidentCard).join("") || `<div class="muted">No resolved incidents.</div>`;
    initMap(document.getElementById("incident-map"), graph, { incidents: active });
  }

  async function analyticsPage() {
    const [summary, peaks, accuracy] = await Promise.all([loadSummary(), loadPeaks(), loadAccuracy()]);
    document.getElementById("analytics-kpis").innerHTML = [
      kpi("Avg Congestion", `${Math.round(summary.avgCongestion * 100)}`, "across all segments"),
      kpi("Total Vehicles", summary.totalVehicles.toLocaleString(), "on network now"),
      kpi("Avg Speed", String(summary.avgSpeed), "network average"),
      kpi("Network Status", summary.networkStatus, summary.congestionTrend || ""),
    ].join("");
    document.getElementById("analytics-peak-chart").innerHTML = chartSvg(peaks.map((p) => ({ label: p.label, y: p.congestionIndex, fill: colorForCongestion(p.congestionIndex) })), 1000, 280, {
      yMax: 1,
      bar: true,
      stroke: "#38bdf8",
      thresholds: [
        { value: 0.65, label: "Heavy", stroke: "#ef4444" },
        { value: 0.4, label: "Moderate", stroke: "#f59e0b" },
      ],
    });
    document.getElementById("analytics-overall").textContent = `${Math.round(accuracy.overallAccuracy * 100)}%`;
    document.getElementById("analytics-mae").textContent = accuracy.maeScore.toFixed(3);
    document.getElementById("analytics-rmse").textContent = accuracy.rmseScore.toFixed(3);
    document.getElementById("analytics-updated").textContent = `Updated: ${new Date(accuracy.lastUpdated).toLocaleTimeString()}`;
    document.getElementById("analytics-accuracy").innerHTML = accuracy.segments.map((s) => `<div class="accuracy-row"><div class="muted" title="${s.roadName}">${s.roadName}</div><div class="bar"><div style="width:${Math.round(s.accuracy * 100)}%"></div></div><div style="text-align:right;font-weight:800">${Math.round(s.accuracy * 100)}%</div></div>`).join("");
  }

  async function main() {
    try {
      if (page === "home") await homePage();
      if (page === "routing") await routingPage();
      if (page === "predictions") await predictionsPage();
      if (page === "incidents") await incidentsPage();
      if (page === "analytics") await analyticsPage();
    } catch (err) {
      document.body.innerHTML = `<div style="padding:24px;color:#fecaca">Failed to load app: ${err.message}</div>`;
    }
  }

  main();
})();
