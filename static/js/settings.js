function toggleSwitch(element) {
    element.classList.toggle("on");
}

function toggleDark(element) {
    element.classList.toggle("on");
    const isLight = !element.classList.contains("on");

    if (typeof setNavigationTheme === "function") {
        setNavigationTheme(isLight);
    } else {
        document.body.classList.toggle("dark", !isLight);
    }
}

async function saveSettings() {
    const switches = Array.from(document.querySelectorAll(".switch"));
    const selects = Array.from(document.querySelectorAll("select"));
    const settings = {
        switches: switches.map((element) => element.classList.contains("on")),
        refreshInterval: selects[0]?.value || "30 Seconds",
        sensorUpdateMode: selects[1]?.value || "Real-time",
        defaultMapLayer: selects[2]?.value || "Satellite + Terrain",
        defaultRiskLevel: selects[3]?.value || "All Risk Levels",
    };

    try {
        const response = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(settings),
        });

        if (!response.ok) {
            throw new Error("Unable to save settings.");
        }

        alert("Application settings saved successfully.");
    } catch (error) {
        alert(error.message);
    }
}

document.querySelectorAll(".menu").forEach(item => {

    item.addEventListener("click", function () {

        document.querySelectorAll(".menu")
            .forEach(menu => menu.classList.remove("active"));

        this.classList.add("active");
    });

});