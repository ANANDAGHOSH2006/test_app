async function runPrediction() {
    try {
        const result = await apiRequest("/api/alerts/predict", { method: "POST" });
        notifyUser(`${result.message} ${result.newZones} new risk zones identified.`);
    } catch (error) {
        notifyUser(error.message);
    }
}

async function viewAlert() {
    try {
        const result = await apiRequest("/api/alerts");
        const alertItem = result.items[0];
        notifyUser(alertItem ? `${alertItem.type} alert at ${alertItem.location}: ${alertItem.risk} risk.` : "No active alerts found.");
    } catch (error) {
        notifyUser(error.message);
    }
}