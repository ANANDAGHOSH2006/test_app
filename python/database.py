from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
from uuid import uuid4


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "ndrf.db"
OPERATIONS_FILE = DATA_DIR / "operations.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "switches": [True, True, True, True, True, True, True, False, False],
    "refreshInterval": "30 Seconds",
    "sensorUpdateMode": "Real-time",
    "defaultMapLayer": "Satellite + Terrain",
    "defaultRiskLevel": "All Risk Levels",
}

DEFAULT_DATA = {
    "sensors": [
        {"id": "SEN-001", "location": "Dehradun Valley", "type": "Rainfall", "value": "86 mm", "status": "High", "updated": "2 min ago"},
        {"id": "SEN-002", "location": "Chamoli District", "type": "Slope Stability", "value": "0.72", "status": "Normal", "updated": "4 min ago"},
        {"id": "SEN-003", "location": "Kedarnath Route", "type": "Water Level", "value": "4.8 m", "status": "Normal", "updated": "6 min ago"},
        {"id": "SEN-004", "location": "Rishikesh Zone", "type": "River Flow", "value": "2,840 m3/s", "status": "Normal", "updated": "8 min ago"},
    ],
    "alerts": [
        {"id": "ALT-001", "location": "Chamoli District", "risk": "High", "type": "Landslide", "status": "Active", "created": "2026-09-08T08:30:00Z"},
        {"id": "ALT-002", "location": "Rudraprayag", "risk": "High", "type": "Flash Flood", "status": "Active", "created": "2026-09-08T08:12:00Z"},
        {"id": "ALT-003", "location": "Pithoragarh", "risk": "Medium", "type": "Heavy Rainfall", "status": "Monitoring", "created": "2026-09-07T16:40:00Z"},
    ],
    "history": [
        {"id": "HIS-001", "date": "2026-08-18", "location": "Chamoli", "disaster": "Landslide", "severity": "High", "status": "Resolved"},
        {"id": "HIS-002", "date": "2026-07-29", "location": "Rudraprayag", "disaster": "Flash Flood", "severity": "High", "status": "Resolved"},
        {"id": "HIS-003", "date": "2026-06-14", "location": "Pithoragarh", "disaster": "Heavy Rainfall", "severity": "Medium", "status": "Closed"},
    ],
    "resources": [
        {"id": "RES-001", "name": "Rescue Team Alpha", "category": "Teams", "location": "Dehradun Base", "status": "Deployed", "updated": "12 min ago"},
        {"id": "RES-002", "name": "Inflatable Rescue Boats", "category": "Equipment", "location": "Rishikesh", "status": "In Transit", "updated": "18 min ago"},
        {"id": "RES-003", "name": "Emergency Medical Kits", "category": "Relief Materials", "location": "Chamoli", "status": "On Site", "updated": "25 min ago"},
    ],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS sensors (
    id TEXT PRIMARY KEY, location TEXT NOT NULL, type TEXT NOT NULL,
    value TEXT NOT NULL, status TEXT NOT NULL, updated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY, location TEXT NOT NULL, risk TEXT NOT NULL,
    type TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY, date TEXT NOT NULL, location TEXT NOT NULL,
    disaster TEXT NOT NULL, severity TEXT NOT NULL, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS resources (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
    location TEXT NOT NULL, status TEXT NOT NULL, updated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY, value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS risk_points (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, risk TEXT NOT NULL,
    latitude REAL NOT NULL, longitude REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL,
    entity TEXT NOT NULL, entity_id TEXT, created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS locations (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, district TEXT NOT NULL,
    state TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL,
    population INTEGER NOT NULL, evacuation_time_minutes INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_id TEXT NOT NULL,
    location_id TEXT NOT NULL, source TEXT NOT NULL, metric TEXT NOT NULL,
    value REAL NOT NULL, unit TEXT NOT NULL, observed_at TEXT NOT NULL,
    FOREIGN KEY(location_id) REFERENCES locations(id)
);
CREATE TABLE IF NOT EXISTS weather_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT, location_id TEXT NOT NULL,
    rainfall_1h REAL NOT NULL, rainfall_24h REAL NOT NULL,
    forecast_3h REAL NOT NULL, observed_at TEXT NOT NULL,
    FOREIGN KEY(location_id) REFERENCES locations(id)
);
CREATE TABLE IF NOT EXISTS soil_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT, location_id TEXT NOT NULL,
    moisture_pct REAL NOT NULL, observed_at TEXT NOT NULL,
    FOREIGN KEY(location_id) REFERENCES locations(id)
);
CREATE TABLE IF NOT EXISTS slope_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT, location_id TEXT NOT NULL,
    instability_index REAL NOT NULL, observed_at TEXT NOT NULL,
    FOREIGN KEY(location_id) REFERENCES locations(id)
);
CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY, location_id TEXT NOT NULL, hazard TEXT NOT NULL,
    score REAL NOT NULL, risk_level TEXT NOT NULL, lead_time_minutes INTEGER NOT NULL,
    factors TEXT NOT NULL, created_at TEXT NOT NULL,
    FOREIGN KEY(location_id) REFERENCES locations(id)
);
CREATE TABLE IF NOT EXISTS warnings (
    id TEXT PRIMARY KEY, prediction_id TEXT NOT NULL, location_id TEXT NOT NULL,
    severity TEXT NOT NULL, message TEXT NOT NULL, status TEXT NOT NULL,
    issued_at TEXT NOT NULL, expires_at TEXT NOT NULL,
    FOREIGN KEY(prediction_id) REFERENCES predictions(id),
    FOREIGN KEY(location_id) REFERENCES locations(id)
);
CREATE TABLE IF NOT EXISTS evacuation_nodes (
    id TEXT PRIMARY KEY, location_id TEXT NOT NULL, name TEXT NOT NULL,
    capacity INTEGER NOT NULL, status TEXT NOT NULL,
    FOREIGN KEY(location_id) REFERENCES locations(id)
);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_history_date ON history(date);
CREATE INDEX IF NOT EXISTS idx_resources_category ON resources(category);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_location ON sensor_readings(location_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_predictions_location ON predictions(location_id, created_at);
CREATE INDEX IF NOT EXISTS idx_warnings_status ON warnings(status, issued_at);
"""


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def connect():
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_FILE, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def rows_as_dicts(rows):
    return [dict(row) for row in rows]


def seed_from_json(connection):
    operations = DEFAULT_DATA
    try:
        if OPERATIONS_FILE.exists():
            operations = json.loads(OPERATIONS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass

    tables = {"sensors": ("id", "location", "type", "value", "status", "updated"), "alerts": ("id", "location", "risk", "type", "status", "created"), "history": ("id", "date", "location", "disaster", "severity", "status"), "resources": ("id", "name", "category", "location", "status", "updated")}
    for table, columns in tables.items():
        if connection.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone():
            continue
        placeholders = ", ".join("?" for _ in columns)
        connection.executemany(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})", [[item[column] for column in columns] for item in operations[table]])

    if not connection.execute("SELECT 1 FROM risk_points LIMIT 1").fetchone():
        connection.executemany("INSERT INTO risk_points (id, name, risk, latitude, longitude) VALUES (?, ?, ?, ?, ?)", [("R-1", "Chamoli", "High", 30.40, 79.32), ("R-2", "Rudraprayag", "Medium", 30.28, 78.98)])

    if not connection.execute("SELECT 1 FROM locations LIMIT 1").fetchone():
        locations = [
            ("LOC-CHM-001", "Chamoli Ward 4", "Chamoli", "Uttarakhand", 30.4042, 79.3227, 1840, 35),
            ("LOC-RDP-001", "Rudraprayag Ward 2", "Rudraprayag", "Uttarakhand", 30.2841, 78.9811, 2120, 45),
            ("LOC-PTH-001", "Pithoragarh Ward 7", "Pithoragarh", "Uttarakhand", 29.5829, 80.2182, 1560, 50),
            ("LOC-DDN-001", "Dehradun Valley Ward 1", "Dehradun", "Uttarakhand", 30.3165, 78.0322, 3250, 25),
        ]
        connection.executemany("INSERT INTO locations (id, name, district, state, latitude, longitude, population, evacuation_time_minutes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", locations)
        now = utc_now()
        connection.executemany("INSERT INTO weather_observations (location_id, rainfall_1h, rainfall_24h, forecast_3h, observed_at) VALUES (?, ?, ?, ?, ?)", [
            ("LOC-CHM-001", 42.0, 168.0, 86.0, now),
            ("LOC-RDP-001", 31.0, 124.0, 65.0, now),
            ("LOC-PTH-001", 18.0, 72.0, 40.0, now),
            ("LOC-DDN-001", 8.0, 34.0, 18.0, now),
        ])
        connection.executemany("INSERT INTO soil_observations (location_id, moisture_pct, observed_at) VALUES (?, ?, ?)", [
            ("LOC-CHM-001", 88.0, now), ("LOC-RDP-001", 79.0, now),
            ("LOC-PTH-001", 67.0, now), ("LOC-DDN-001", 48.0, now),
        ])
        connection.executemany("INSERT INTO slope_observations (location_id, instability_index, observed_at) VALUES (?, ?, ?)", [
            ("LOC-CHM-001", 0.83, now), ("LOC-RDP-001", 0.64, now),
            ("LOC-PTH-001", 0.48, now), ("LOC-DDN-001", 0.22, now),
        ])
        connection.executemany("INSERT INTO evacuation_nodes (id, location_id, name, capacity, status) VALUES (?, ?, ?, ?, ?)", [
            ("EVA-CHM-001", "LOC-CHM-001", "Chamoli Community School", 900, "Ready"),
            ("EVA-RDP-001", "LOC-RDP-001", "Rudraprayag Relief Center", 1100, "Ready"),
            ("EVA-PTH-001", "LOC-PTH-001", "Pithoragarh Sports Hall", 750, "Standby"),
            ("EVA-DDN-001", "LOC-DDN-001", "Dehradun Base Camp", 1800, "Ready"),
        ])

    if not connection.execute("SELECT 1 FROM settings LIMIT 1").fetchone():
        settings = DEFAULT_SETTINGS.copy()
        try:
            if SETTINGS_FILE.exists():
                settings.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            pass
        connection.executemany("INSERT INTO settings (key, value) VALUES (?, ?)", [(key, json.dumps(value)) for key, value in settings.items()])


def initialize_database():
    with connect() as connection:
        connection.executescript(SCHEMA)
        seed_from_json(connection)
        connection.commit()


def get_settings():
    initialize_database()
    with connect() as connection:
        values = {row["key"]: json.loads(row["value"]) for row in connection.execute("SELECT key, value FROM settings")}
    return {**DEFAULT_SETTINGS, **values}


def save_settings(settings):
    initialize_database()
    with connect() as connection:
        connection.executemany("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", [(key, json.dumps(value)) for key, value in settings.items()])
        connection.execute("INSERT INTO audit_events (action, entity, created) VALUES (?, ?, ?)", ("update", "settings", utc_now()))
        connection.commit()


def get_sensors():
    initialize_database()
    with connect() as connection:
        return rows_as_dicts(connection.execute("SELECT * FROM sensors ORDER BY id"))


def refresh_sensors():
    initialize_database()
    with connect() as connection:
        connection.execute("UPDATE sensors SET updated = ?", ("Just now",))
        connection.execute("INSERT INTO audit_events (action, entity, created) VALUES (?, ?, ?)", ("refresh", "sensors", utc_now()))
        connection.commit()
    return get_sensors()


def get_alerts():
    initialize_database()
    with connect() as connection:
        return rows_as_dicts(connection.execute("SELECT * FROM alerts ORDER BY created DESC"))


def create_alert():
    initialize_database()
    alert = {"id": f"ALT-{uuid4().hex[:6].upper()}", "location": "Dehradun Valley", "risk": "Medium", "type": "Forecast Risk Zone", "status": "Monitoring", "created": utc_now()}
    with connect() as connection:
        connection.execute("INSERT INTO alerts (id, location, risk, type, status, created) VALUES (:id, :location, :risk, :type, :status, :created)", alert)
        connection.execute("INSERT INTO audit_events (action, entity, entity_id, created) VALUES (?, ?, ?, ?)", ("create", "alert", alert["id"], utc_now()))
        connection.commit()
    return alert


def get_history(query="", severity=""):
    initialize_database()
    clauses, params = [], []
    if query:
        clauses.append("(location LIKE ? OR disaster LIKE ? OR status LIKE ?)")
        term = f"%{query}%"
        params.extend([term, term, term])
    if severity and severity != "all severity levels":
        clauses.append("severity = ?")
        params.append(severity.title())
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect() as connection:
        return rows_as_dicts(connection.execute(f"SELECT * FROM history{where} ORDER BY date DESC", params))


def get_resources(category="All"):
    initialize_database()
    params = []
    where = ""
    if category and category.lower() != "all":
        where = " WHERE category = ?"
        params.append(category)
    with connect() as connection:
        return rows_as_dicts(connection.execute(f"SELECT * FROM resources{where} ORDER BY id", params))


def create_resource(name, category, location):
    initialize_database()
    resource = {"id": f"RES-{uuid4().hex[:6].upper()}", "name": name, "category": category, "location": location, "status": "Planned", "updated": "Just now"}
    with connect() as connection:
        connection.execute("INSERT INTO resources (id, name, category, location, status, updated) VALUES (:id, :name, :category, :location, :status, :updated)", resource)
        connection.execute("INSERT INTO audit_events (action, entity, entity_id, created) VALUES (?, ?, ?, ?)", ("create", "resource", resource["id"], utc_now()))
        connection.commit()
    return resource


def get_resource(resource_id):
    initialize_database()
    with connect() as connection:
        row = connection.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
    return dict(row) if row else None


def get_risk_points():
    initialize_database()
    with connect() as connection:
        rows = connection.execute("SELECT id, name, risk, latitude AS lat, longitude AS lng FROM risk_points ORDER BY id")
        return rows_as_dicts(rows)


def get_dashboard_metrics():
    initialize_database()
    with connect() as connection:
        active_alerts = connection.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Active'").fetchone()[0]
        sensors = connection.execute("SELECT COUNT(*) FROM sensors").fetchone()[0]
        deployed = connection.execute("SELECT COUNT(*) FROM resources WHERE status IN ('Deployed', 'On Site')").fetchone()[0]
        incidents = connection.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    return {"activeAlerts": active_alerts, "monitoredSensors": sensors, "deployedResources": deployed, "openIncidents": incidents}


def get_locations():
    initialize_database()
    with connect() as connection:
        return rows_as_dicts(connection.execute("SELECT * FROM locations ORDER BY district, name"))


def get_latest_observations(location_id=None):
    initialize_database()
    params = [location_id] if location_id else []
    where = "WHERE l.id = ?" if location_id else ""
    query = f"""
        SELECT l.id AS location_id, l.name, l.district, l.state, l.latitude, l.longitude,
            l.population, l.evacuation_time_minutes,
            COALESCE(w.rainfall_1h, 0) AS rainfall_1h,
            COALESCE(w.rainfall_24h, 0) AS rainfall_24h,
            COALESCE(w.forecast_3h, 0) AS forecast_3h,
            COALESCE(s.moisture_pct, 0) AS moisture_pct,
            COALESCE(sl.instability_index, 0) AS instability_index,
            (SELECT COUNT(*) FROM history h WHERE h.location LIKE '%' || l.district || '%') AS historical_incidents,
            w.observed_at AS weather_observed_at,
            s.observed_at AS soil_observed_at,
            sl.observed_at AS slope_observed_at
        FROM locations l
        LEFT JOIN weather_observations w ON w.id = (
            SELECT id FROM weather_observations WHERE location_id = l.id ORDER BY observed_at DESC, id DESC LIMIT 1
        )
        LEFT JOIN soil_observations s ON s.id = (
            SELECT id FROM soil_observations WHERE location_id = l.id ORDER BY observed_at DESC, id DESC LIMIT 1
        )
        LEFT JOIN slope_observations sl ON sl.id = (
            SELECT id FROM slope_observations WHERE location_id = l.id ORDER BY observed_at DESC, id DESC LIMIT 1
        )
        {where}
        ORDER BY l.district, l.name
    """
    with connect() as connection:
        rows = rows_as_dicts(connection.execute(query, params))
    return rows


def _risk_result(observation):
    rainfall_score = min(100.0, observation["rainfall_24h"] / 180 * 45 + observation["forecast_3h"] / 100 * 25 + observation["rainfall_1h"] / 50 * 10)
    soil_score = min(100.0, max(0.0, (observation["moisture_pct"] - 40) / 60 * 100))
    slope_score = min(100.0, observation["instability_index"] * 100)
    historical_score = min(100.0, observation["historical_incidents"] * 35.0)
    score = round(rainfall_score * 0.45 + soil_score * 0.2 + slope_score * 0.3 + historical_score * 0.05, 2)
    if score >= 80:
        risk_level, lead_time = "Critical", 15
    elif score >= 60:
        risk_level, lead_time = "High", 30
    elif score >= 35:
        risk_level, lead_time = "Medium", 60
    else:
        risk_level, lead_time = "Low", 120
    hazard = "Flash Flood" if rainfall_score >= slope_score else "Landslide"
    factors = {
        "rainfallScore": round(rainfall_score, 2),
        "soilMoistureScore": round(soil_score, 2),
        "slopeInstabilityScore": round(slope_score, 2),
        "historicalSeverityScore": historical_score,
        "rainfall24hMm": observation["rainfall_24h"],
        "forecast3hMm": observation["forecast_3h"],
        "soilMoisturePct": observation["moisture_pct"],
        "slopeInstabilityIndex": observation["instability_index"],
    }
    return {"score": score, "risk_level": risk_level, "lead_time_minutes": lead_time, "hazard": hazard, "factors": factors}


def run_predictions(location_id=None):
    observations = get_latest_observations(location_id)
    now = utc_now()
    results = []
    with connect() as connection:
        for observation in observations:
            result = _risk_result(observation)
            prediction = {
                "id": f"PRED-{uuid4().hex[:8].upper()}",
                "location_id": observation["location_id"],
                "hazard": result["hazard"],
                "score": result["score"],
                "risk_level": result["risk_level"],
                "lead_time_minutes": result["lead_time_minutes"],
                "factors": json.dumps(result["factors"]),
                "created_at": now,
            }
            connection.execute("INSERT INTO predictions (id, location_id, hazard, score, risk_level, lead_time_minutes, factors, created_at) VALUES (:id, :location_id, :hazard, :score, :risk_level, :lead_time_minutes, :factors, :created_at)", prediction)
            warning = {
                "id": f"WARN-{uuid4().hex[:8].upper()}",
                "prediction_id": prediction["id"],
                "location_id": observation["location_id"],
                "severity": result["risk_level"],
                "message": f"{result['risk_level']} {result['hazard']} risk at {observation['name']}. Move residents to the nearest ready evacuation node.",
                "status": "Active" if result["risk_level"] in {"Critical", "High"} else "Monitoring",
                "issued_at": now,
                "expires_at": now,
            }
            connection.execute("INSERT INTO warnings (id, prediction_id, location_id, severity, message, status, issued_at, expires_at) VALUES (:id, :prediction_id, :location_id, :severity, :message, :status, :issued_at, :expires_at)", warning)
            results.append({**prediction, "factors": result["factors"], "location": observation["name"], "district": observation["district"], "warning": warning})
        connection.execute("INSERT INTO audit_events (action, entity, created) VALUES (?, ?, ?)", ("run", "predictions", now))
        connection.commit()
    return results


def get_predictions(location_id=None):
    initialize_database()
    params = [location_id] if location_id else []
    where = "WHERE p.location_id = ?" if location_id else ""
    query = f"""
        SELECT p.id, p.location_id, l.name AS location, l.district, p.hazard,
            p.score, p.risk_level, p.lead_time_minutes, p.factors, p.created_at
        FROM predictions p JOIN locations l ON l.id = p.location_id
        {where} ORDER BY p.created_at DESC
    """
    with connect() as connection:
        rows = rows_as_dicts(connection.execute(query, params))
    for row in rows:
        row["factors"] = json.loads(row["factors"])
    return rows


def get_warnings(status=""):
    initialize_database()
    params = []
    where = ""
    if status:
        where = "WHERE w.status = ?"
        params.append(status)
    query = f"""
        SELECT w.*, l.name AS location, l.district, p.hazard,
            p.score, p.lead_time_minutes
        FROM warnings w JOIN locations l ON l.id = w.location_id
        JOIN predictions p ON p.id = w.prediction_id
        {where} ORDER BY w.issued_at DESC
    """
    with connect() as connection:
        return rows_as_dicts(connection.execute(query, params))


def update_warning_status(warning_id, status):
    if status not in {"Active", "Monitoring", "Acknowledged", "Resolved"}:
        raise ValueError("Unsupported warning status")
    initialize_database()
    with connect() as connection:
        cursor = connection.execute("UPDATE warnings SET status = ? WHERE id = ?", (status, warning_id))
        if cursor.rowcount == 0:
            return None
        connection.execute("INSERT INTO audit_events (action, entity, entity_id, created) VALUES (?, ?, ?, ?)", ("update", "warning", warning_id, utc_now()))
        connection.commit()
    return next((warning for warning in get_warnings() if warning["id"] == warning_id), None)


def ingest_observation(payload):
    location_id = str(payload.get("locationId", "")).strip()
    metric = str(payload.get("metric", "")).strip().lower()
    source = str(payload.get("source", "IoT")).strip()
    if not location_id or not metric:
        raise ValueError("locationId and metric are required")
    if not get_latest_observations(location_id):
        raise ValueError("Unknown locationId")
    try:
        value = float(payload["value"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("value must be numeric") from error
    ranges = {"rainfall_1h": (0, 1000), "rainfall_24h": (0, 3000), "forecast_3h": (0, 2000), "soil_moisture": (0, 100), "slope_instability": (0, 1)}
    if metric not in ranges or not ranges[metric][0] <= value <= ranges[metric][1]:
        raise ValueError("metric or value is outside the supported range")
    now = utc_now()
    unit = payload.get("unit", "%" if metric == "soil_moisture" else "index" if metric == "slope_instability" else "mm")
    with connect() as connection:
        connection.execute("INSERT INTO sensor_readings (sensor_id, location_id, source, metric, value, unit, observed_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (payload.get("sensorId", f"IOT-{uuid4().hex[:6].upper()}"), location_id, source, metric, value, unit, now))
        if metric in {"rainfall_1h", "rainfall_24h", "forecast_3h"}:
            latest = connection.execute("SELECT rainfall_1h, rainfall_24h, forecast_3h FROM weather_observations WHERE location_id = ? ORDER BY observed_at DESC, id DESC LIMIT 1", (location_id,)).fetchone()
            values = dict(latest) if latest else {"rainfall_1h": 0, "rainfall_24h": 0, "forecast_3h": 0}
            values[metric] = value
            connection.execute("INSERT INTO weather_observations (location_id, rainfall_1h, rainfall_24h, forecast_3h, observed_at) VALUES (?, ?, ?, ?, ?)", (location_id, values["rainfall_1h"], values["rainfall_24h"], values["forecast_3h"], now))
        elif metric == "soil_moisture":
            connection.execute("INSERT INTO soil_observations (location_id, moisture_pct, observed_at) VALUES (?, ?, ?)", (location_id, value, now))
        else:
            connection.execute("INSERT INTO slope_observations (location_id, instability_index, observed_at) VALUES (?, ?, ?)", (location_id, value, now))
        connection.commit()
    return {"locationId": location_id, "metric": metric, "value": value, "source": source, "observedAt": now}


def get_evacuation_nodes(location_id=None):
    initialize_database()
    params = [location_id] if location_id else []
    where = "WHERE e.location_id = ?" if location_id else ""
    query = f"SELECT e.*, l.name AS location, l.district FROM evacuation_nodes e JOIN locations l ON l.id = e.location_id {where} ORDER BY l.district, e.name"
    with connect() as connection:
        return rows_as_dicts(connection.execute(query, params))
