from csv import writer
from io import BytesIO, StringIO

from flask import Flask, jsonify, render_template, request, send_file

import database


app = Flask(__name__)


PAGE_TEMPLATES = {
	"dashboard": "index.html",
	"monitors": "monitors.html",
	"alerts": "alerts.html",
	"geospatial": "geospatial.html",
	"history": "history.html",
	"resources": "resources.html",
	"settings": "settings.html",
}


@app.before_request
def prepare_database():
	database.initialize_database()


@app.route("/")
def dashboard():
	return render_template("index.html", metrics=database.get_dashboard_metrics())


@app.route("/monitors")
def monitors():
	return render_template("monitors.html")


@app.route("/alerts")
def alerts():
	return render_template("alerts.html")


@app.route("/geospatial")
def geospatial():
	return render_template("geospatial.html")


@app.route("/history")
def history():
	return render_template("history.html")


@app.route("/resources")
def resources():
	return render_template("resources.html")


@app.route("/settings")
def settings():
	return render_template("settings.html", settings=database.get_settings())


@app.get("/api/dashboard")
def dashboard_api():
	return jsonify({"metrics": database.get_dashboard_metrics()})


@app.get("/api/monitors")
def monitors_api():
	items = database.get_sensors()
	return jsonify({"items": items, "total": len(items)})


@app.post("/api/monitors/refresh")
def refresh_monitors_api():
	items = database.refresh_sensors()
	return jsonify({"items": items, "message": "Sensor data refreshed."})


@app.get("/api/alerts")
def alerts_api():
	items = database.get_alerts()
	return jsonify({"items": items, "total": len(items)})


@app.post("/api/alerts/predict")
def predict_alerts_api():
	results = database.run_predictions()
	return jsonify({"message": "Prediction completed.", "newZones": len(results), "items": results})


@app.get("/api/history")
def history_api():
	items = database.get_history(request.args.get("q", ""), request.args.get("severity", ""))
	return jsonify({"items": items, "total": len(items)})


@app.get("/api/history/export")
def export_history_api():
	output = StringIO()
	csv_writer = writer(output)
	items = database.get_history()
	columns = ("id", "date", "location", "disaster", "severity", "status")
	csv_writer.writerow(columns)
	csv_writer.writerows([item.get(column, "") for column in columns] for item in items)
	return send_file(BytesIO(output.getvalue().encode("utf-8")), mimetype="text/csv", as_attachment=True, download_name="ndrf-history.csv")


@app.get("/api/resources")
def resources_api():
	items = database.get_resources(request.args.get("category", "All"))
	return jsonify({"items": items, "total": len(items)})


@app.post("/api/resources")
def create_resource_api():
	payload = request.get_json(silent=True) or {}
	name = str(payload.get("name", "")).strip()
	category = str(payload.get("category", "Teams")).strip()
	location = str(payload.get("location", "")).strip()
	if not name or not location:
		return jsonify({"error": "name and location are required"}), 400
	resource = database.create_resource(name, category, location)
	return jsonify({"item": resource, "message": "Resource deployment created."}), 201


@app.get("/api/risk-points")
def risk_points_api():
	return jsonify({"items": database.get_risk_points()})


@app.post("/api/geospatial/analyze")
def geospatial_analyze_api():
	payload = request.get_json(silent=True) or {}
	return jsonify(database.analyze_geospatial(
		payload.get("state", ""),
		payload.get("district", ""),
		payload.get("riskLayer", ""),
	))


@app.get("/api/locations")
def locations_api():
	return jsonify({"items": database.get_locations()})


@app.get("/api/observations")
def observations_api():
	return jsonify({"items": database.get_latest_observations(request.args.get("locationId"))})


@app.get("/api/predictions")
def predictions_api():
	return jsonify({"items": database.get_predictions(request.args.get("locationId"))})


@app.get("/api/warnings")
def warnings_api():
	return jsonify({"items": database.get_warnings(request.args.get("status", ""))})


@app.patch("/api/warnings/<warning_id>")
def update_warning_api(warning_id):
	payload = request.get_json(silent=True) or {}
	warning = database.update_warning_status(warning_id, str(payload.get("status", "")).strip())
	if warning is None:
		return jsonify({"error": "Warning not found"}), 404
	return jsonify({"item": warning, "message": "Warning status updated."})


@app.get("/api/evacuation-nodes")
def evacuation_nodes_api():
	return jsonify({"items": database.get_evacuation_nodes(request.args.get("locationId"))})


@app.post("/api/observations")
def ingest_observation_api():
	try:
		return jsonify(database.ingest_observation(request.get_json(silent=True) or {})), 201
	except ValueError as error:
		return jsonify({"error": str(error)}), 400


@app.post("/api/settings")
def save_settings_api():
	payload = request.get_json(silent=True) or {}
	database.save_settings(payload)
	return jsonify({"settings": database.get_settings(), "message": "Application settings saved successfully."})


@app.errorhandler(ValueError)
def handle_value_error(error):
	return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
	app.run(debug=True)
