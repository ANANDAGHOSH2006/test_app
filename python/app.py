import csv
import io

from flask import Flask, jsonify, make_response, render_template, request

from database import (
    create_resource,
    get_alerts,
    get_dashboard_metrics,
    get_history,
    get_evacuation_nodes,
    get_latest_observations,
    get_locations,
    get_predictions,
    get_resource,
    get_resources,
    get_risk_points,
    get_sensors,
    get_settings,
    get_warnings,
    ingest_observation,
    initialize_database,
    refresh_sensors,
    run_predictions,
    save_settings,
    update_warning_status,
    utc_now,
)


app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
PAGE_NAMES = ("index", "monitors", "alerts", "geospatial", "history", "resources", "settings")
DEFAULT_SETTINGS_KEYS = {"switches", "refreshInterval", "sensorUpdateMode", "defaultMapLayer", "defaultRiskLevel"}


def json_error(message, status=400, details=None):
    payload = {"error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status


def request_json():
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else None


@app.before_request
def ensure_database():
    initialize_database()


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return json_error("The requested API resource was not found.", 404)
    return error


@app.errorhandler(500)
def server_error(error):
    return json_error("An unexpected server error occurred.", 500)


@app.route("/")
def dashboard():
    return render_template("index.html")


def render_page(page_name):
    return render_template(f"{page_name}.html")


for page_name in PAGE_NAMES[1:]:
    app.add_url_rule(f"/{page_name}", endpoint=page_name, view_func=lambda page_name=page_name: render_page(page_name))


@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok", "service": "ndrf-disaster-intelligence", "database": "sqlite", "timestamp": utc_now()})


@app.get("/api/dashboard")
def dashboard_data():
    return jsonify({"metrics": get_dashboard_metrics(), "alerts": get_alerts()[:5], "updatedAt": utc_now()})


@app.get("/api/monitors")
def api_monitors():
    return jsonify({"items": get_sensors(), "updatedAt": utc_now()})


@app.post("/api/monitors/refresh")
def refresh_monitors():
    return jsonify({"message": "Sensor data refreshed.", "items": refresh_sensors(), "updatedAt": utc_now()})


@app.get("/api/alerts")
def api_alerts():
    return jsonify({"items": get_alerts(), "updatedAt": utc_now()})


@app.post("/api/alerts/predict")
def predict_alerts():
    payload = request_json() or {}
    predictions = run_predictions(payload.get("locationId"))
    return jsonify({"message": "Multi-source prediction completed.", "newZones": len([item for item in predictions if item["risk_level"] in {"Critical", "High"}]), "predictions": predictions}), 201


@app.get("/api/locations")
def locations():
    items = get_locations()
    return jsonify({"items": items, "total": len(items)})


@app.get("/api/observations/latest")
def latest_observations():
    items = get_latest_observations(request.args.get("locationId"))
    return jsonify({"items": items, "total": len(items), "updatedAt": utc_now()})


@app.post("/api/observations")
def create_observation():
    payload = request_json()
    if payload is None:
        return json_error("Expected a JSON observation object.")
    try:
        return jsonify({"message": "Observation ingested.", "observation": ingest_observation(payload)}), 201
    except ValueError as error:
        return json_error(str(error))


@app.post("/api/predictions/run")
def run_prediction_model():
    payload = request_json() or {}
    predictions = run_predictions(payload.get("locationId"))
    return jsonify({"message": "Prediction model executed.", "count": len(predictions), "predictions": predictions, "generatedAt": utc_now()})


@app.get("/api/predictions")
def predictions():
    return jsonify({"items": get_predictions(request.args.get("locationId")), "generatedAt": utc_now()})


@app.get("/api/warnings")
def warnings():
    items = get_warnings(request.args.get("status", ""))
    return jsonify({"items": items, "total": len(items)})


@app.patch("/api/warnings/<warning_id>")
def update_warning(warning_id):
    payload = request_json() or {}
    try:
        warning = update_warning_status(warning_id, payload.get("status", ""))
    except ValueError as error:
        return json_error(str(error))
    return jsonify(warning) if warning else json_error("Warning was not found.", 404)


@app.get("/api/evacuation/nodes")
def evacuation_nodes():
    items = get_evacuation_nodes(request.args.get("locationId"))
    return jsonify({"items": items, "total": len(items)})


@app.get("/api/geospatial")
def api_geospatial():
    return jsonify({"riskPoints": get_risk_points(), "updatedAt": utc_now()})


@app.post("/api/geospatial/analyze")
def analyze_geospatial():
    payload = request_json() or {}
    return jsonify({"message": "Geo-spatial analysis completed.", "state": payload.get("state", "Uttarakhand"), "district": payload.get("district", "All districts"), "riskLevel": "Elevated", "layersUpdated": 3, "updatedAt": utc_now()})


@app.get("/api/history")
def api_history():
    items = get_history(request.args.get("q", "").strip(), request.args.get("severity", "").strip())
    return jsonify({"items": items, "total": len(items)})


@app.get("/api/history/export")
def export_history():
    rows = get_history()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys() if rows else ["id"])
    writer.writeheader()
    writer.writerows(rows)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=ndrf-history.csv"
    return response


@app.get("/api/resources")
def api_resources():
    items = get_resources(request.args.get("category", "All").strip())
    return jsonify({"items": items, "total": len(items)})


@app.post("/api/resources")
def api_create_resource():
    payload = request_json()
    if not payload:
        return json_error("Expected a JSON object with name, category, and location.")
    missing = [field for field in ("name", "category", "location") if not str(payload.get(field, "")).strip()]
    if missing:
        return json_error("Required deployment fields are missing.", details=missing)
    item = create_resource(payload["name"].strip(), payload["category"].strip(), payload["location"].strip())
    return jsonify({"message": "Deployment created.", "item": item}), 201


@app.get("/api/resources/<resource_id>")
def resource_details(resource_id):
    item = get_resource(resource_id)
    return jsonify(item) if item else json_error("Resource was not found.", 404)


@app.get("/api/settings")
def api_get_settings():
    return jsonify(get_settings())


@app.post("/api/settings")
def api_update_settings():
    settings = request_json()
    if settings is None:
        return json_error("Expected a JSON object.")
    unknown = sorted(set(settings) - DEFAULT_SETTINGS_KEYS)
    if unknown:
        return json_error("Unsupported settings were provided.", details=unknown)
    merged = {**get_settings(), **settings}
    if not isinstance(merged["switches"], list) or len(merged["switches"]) != 9:
        return json_error("The switches setting must contain 9 boolean values.")
    if not all(isinstance(value, bool) for value in merged["switches"]):
        return json_error("Every switch value must be boolean.")
    save_settings(merged)
    return jsonify({"message": "Settings saved successfully.", "settings": merged})


initialize_database()


if __name__ == "__main__":
    app.run(debug=True)