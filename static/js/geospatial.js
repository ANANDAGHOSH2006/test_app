function toggleRisk() {
    const pins = document.querySelectorAll(".pin");

    pins.forEach(pin => {
        pin.style.display =
            pin.style.display === "none" ? "block" : "none";
    });
}

async function analyze() {
    const selects = document.querySelectorAll(".filter select");
    try {
        const result = await apiRequest("/api/geospatial/analyze", {
            method: "POST",
            body: JSON.stringify({
                state: selects[0]?.value,
                district: selects[1]?.value,
                riskLayer: selects[2]?.value,
                mapMode: selects[3]?.value,
            }),
        });
        notifyUser(`${result.message} ${result.layersUpdated} layers updated.`);
    } catch (error) {
        notifyUser(error.message);
    }
}