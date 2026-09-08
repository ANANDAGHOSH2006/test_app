/* ==========================================
   NDRF DISASTER INTELLIGENCE DASHBOARD
========================================== */


/* ==========================================
   STARTUP LOADER
========================================== */

const introLoader = document.getElementById("introLoader");


if (introLoader) {

    window.setTimeout(() => {

        introLoader.classList.add("is-complete");

        window.setTimeout(() => introLoader.remove(), 900);

    }, 3000);

}


document.querySelectorAll(".stat").forEach((stat) => {

    const trend = stat.querySelector("em");
    const icon = stat.querySelector(".stat-icon");

    if (trend && icon) {

        icon.classList.toggle(
            "negative",
            /^\s*-/.test(trend.textContent)
        );

    }

});


/* ==========================================
   DISPLAY MODE TOGGLE
========================================== */

const themeButton =
    document.getElementById("themeButton");


function getSavedTheme() {

    try {

        return localStorage.getItem("ndrf-theme");

    } catch (error) {

        return null;

    }

}


function saveTheme(theme) {

    try {

        localStorage.setItem("ndrf-theme", theme);

    } catch (error) {

        /* Theme still works when browser storage is unavailable. */

    }

}


function setTheme(isLight) {

    document.body.classList.toggle("light-theme", isLight);

    document.body.classList.toggle("dark-theme", !isLight);

    themeButton.textContent =
        isLight ? "☾ Dark mode" : "☀ Bright mode";

    themeButton.dataset.mode =
        isLight ? "light" : "dark";

    themeButton.setAttribute(
        "aria-label",
        isLight ? "Switch to dark mode" : "Switch to bright mode"
    );

    themeButton.setAttribute(
        "title",
        isLight ? "Switch to dark mode" : "Switch to bright mode"
    );

    saveTheme(isLight ? "light" : "dark");

}


const savedTheme =
    getSavedTheme();


setTheme(savedTheme === "light");


themeButton.addEventListener(
    "click",
    () => setTheme(!document.body.classList.contains("light-theme"))
);


/* ==========================================
   SIDEBAR NAVIGATION
========================================== */

const navigationButtons =
    document.querySelectorAll(".nav-btn:not(.theme-toggle)");


navigationButtons.forEach(button => {

    button.addEventListener("click", function () {

        navigationButtons.forEach(btn => {

            btn.classList.remove("active");

        });

        this.classList.add("active");

        showMessage(
            this.innerText.trim() +
            " module selected"
        );

    });

});


/* ==========================================
   LEAFLET MAP
========================================== */

const map =
    L.map("map", {

        zoomControl: true,

        attributionControl: false

    }).setView(
        [31.70, 77.25],
        7
    );


/* OpenStreetMap */

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 18
    }
).addTo(map);


/* ==========================================
   HIGH RISK ZONES
========================================== */

const riskLayer =
    L.layerGroup();


const riskZones = [

    [32.10, 77.20],

    [31.85, 77.35],

    [31.60, 77.10],

    [31.45, 77.55],

    [31.95, 76.90],

    [32.25, 76.80],

    [31.25, 77.15]

];


riskZones.forEach(
    (location, index) => {

        const zone =
            L.circle(
                location,
                {
                    radius:
                        9000 +
                        index * 1500,

                    color: "#f04444",

                    weight: 1,

                    fillColor: "#ff443d",

                    fillOpacity: 0.18
                }
            );


        zone.bindPopup(

            `
            <b>High Risk Zone ${index + 1}</b>
            <br>
            Rainfall and slope instability detected.
            `

        );


        zone.addTo(riskLayer);

    }
);


/* ==========================================
   EVACUATION NODES
========================================== */

const evacuationLayer =
    L.layerGroup();


const evacuationNodes = [

    [31.72, 77.15],

    [31.89, 77.18],

    [31.48, 77.30],

    [32.02, 77.45]

];


evacuationNodes.forEach(
    (location, index) => {

        L.circleMarker(
            location,
            {

                radius: 6,

                color: "#48e1bf",

                weight: 2,

                fillColor: "#0c554d",

                fillOpacity: 0.9

            }
        )

        .bindPopup(

            `
            <b>Evacuation Node ${index + 1}</b>
            <br>
            All systems operational.
            `

        )

        .addTo(evacuationLayer);

    }
);


/* ==========================================
   RAINFALL LAYER
========================================== */

const rainfallLayer =
    L.layerGroup();


function rainfallStyle(rainfall24h) {
    if (rainfall24h >= 150) {
        return { color: "#ef4949", fillColor: "#ff5252" };
    }
    if (rainfall24h >= 80) {
        return { color: "#e8a735", fillColor: "#f5c14b" };
    }
    return { color: "#42d9b0", fillColor: "#2f9e7c" };
}


async function loadLiveRainfall() {
    try {
        const result = await apiRequest("/api/observations/latest");
        const highRiskZones = result.items.filter(item => item.rainfall_24h >= 150).length;
        const status = document.querySelector(".map-status span");

        rainfallLayer.clearLayers();
        result.items.forEach(item => {
            const style = rainfallStyle(item.rainfall_24h);
            L.circle(
                [item.latitude, item.longitude],
                {
                    radius: Math.max(2500, Math.min(9000, item.rainfall_24h * 35)),
                    color: style.color,
                    weight: 2,
                    fillColor: style.fillColor,
                    fillOpacity: 0.3
                }
            )
                .bindPopup(`<b>${item.name}</b><br>Rainfall: ${item.rainfall_24h} mm / 24h<br>Next 3h forecast: ${item.forecast_3h} mm<br>Source status: Live`)
                .addTo(rainfallLayer);
        });

        if (status) {
            status.textContent = `${highRiskZones} high-risk rainfall zones detected`;
        }
    } catch (error) {
        if (typeof showMessage === "function") {
            showMessage("Live rainfall data is temporarily unavailable.");
        }
    }
}


loadLiveRainfall();
window.setInterval(loadLiveRainfall, 30000);


/* Show all layers */

riskLayer.addTo(map);

evacuationLayer.addTo(map);

rainfallLayer.addTo(map);


/* ==========================================
   MAP FILTER BUTTONS
========================================== */

const mapButtons =
    document.querySelectorAll(".map-btn");


mapButtons.forEach(button => {

    button.addEventListener("click", function () {

        mapButtons.forEach(btn => {

            btn.classList.remove("active");

        });

        this.classList.add("active");


        map.removeLayer(riskLayer);

        map.removeLayer(evacuationLayer);

        map.removeLayer(rainfallLayer);


        const layer =
            this.dataset.layer;


        if (layer === "all") {

            riskLayer.addTo(map);

            evacuationLayer.addTo(map);

            rainfallLayer.addTo(map);

        }


        if (layer === "rain") {

            rainfallLayer.addTo(map);

        }


        if (layer === "slope") {

            riskLayer.addTo(map);

            evacuationLayer.addTo(map);

        }

    });

});


/* ==========================================
   RAINFALL CHART
========================================== */

const chartCanvas =
    document.getElementById("rainChart");


new Chart(
    chartCanvas,
    {

        type: "line",

        data: {

            labels: [

                "12:00",

                "13:00",

                "14:00",

                "15:00",

                "16:00",

                "17:00",

                "18:00",

                "19:00"

            ],

            datasets: [

                {

                    label: "Rainfall",

                    data: [

                        42,

                        67,

                        55,

                        92,

                        82,

                        131,

                        119,

                        165

                    ],

                    borderWidth: 2,

                    tension: .35,

                    fill: true,

                    pointRadius: 2

                },


                {

                    label: "Threshold",

                    data: [

                        100,

                        100,

                        100,

                        100,

                        100,

                        100,

                        100,

                        100

                    ],

                    borderWidth: 1,

                    borderDash: [

                        5,

                        5

                    ],

                    pointRadius: 0,

                    fill: false

                }

            ]

        },


        options: {

            responsive: true,

            maintainAspectRatio: false,


            plugins: {

                legend: {

                    display: false

                }

            },


            scales: {

                x: {

                    grid: {

                        display: false

                    },

                    ticks: {

                        color: "#688193",

                        font: {

                            size: 7

                        }

                    }

                },


                y: {

                    beginAtZero: true,

                    max: 200,

                    ticks: {

                        color: "#688193",

                        font: {

                            size: 7

                        }

                    },

                    grid: {

                        color:
                            "rgba(140,170,190,.09)"

                    }

                }

            }

        }

    }
);


/* ==========================================
   SIMULATED SENSOR DATA
========================================== */

setInterval(
    () => {

        /* Sensor */

        const sensorValue =
            1284 +
            Math.floor(
                Math.random() * 10
            );


        document.getElementById(
            "sensor"
        ).textContent =
            sensorValue.toLocaleString();


        /* Soil Moisture */

        const moistureValue =
            72 +
            Math.floor(
                Math.random() * 8
            );


        document.getElementById(
            "moisture"
        ).textContent =
            moistureValue;


        /* Synchronization */

        document.getElementById(
            "sync"
        ).textContent =
            "just now";


    },
    4000
);


/* ==========================================
   VIEW ALERTS
========================================== */

document
    .getElementById("viewAlerts")
    .addEventListener(
        "click",
        function () {

            showMessage(
                "Opening complete alert matrix..."
            );

        }
    );


/* ==========================================
   TOAST MESSAGE
========================================== */

function showMessage(message) {

    let toast =
        document.querySelector(".toast");


    if (!toast) {

        toast =
            document.createElement("div");

        toast.className =
            "toast";


        toast.style.position =
            "fixed";

        toast.style.right =
            "20px";

        toast.style.bottom =
            "20px";

        toast.style.zIndex =
            "9999";

        toast.style.background =
            "#10283b";

        toast.style.color =
            "#ffffff";

        toast.style.border =
            "1px solid rgba(70,216,176,.3)";

        toast.style.padding =
            "10px 14px";

        toast.style.borderRadius =
            "6px";

        toast.style.fontSize =
            "10px";

        toast.style.boxShadow =
            "0 10px 30px rgba(0,0,0,.4)";

        document.body.appendChild(toast);

    }


    toast.textContent =
        message;


    toast.style.opacity =
        "1";


    setTimeout(
        () => {

            toast.style.opacity =
                "0";

        },
        1800
    );

}

if (typeof apiRequest === "function") {
    apiRequest("/api/dashboard")
        .then((result) => {
            const sensor = document.getElementById("sensor");
            const wardNumber = document.getElementById("wardNumber");
            const sync = document.getElementById("sync");
            if (sensor) sensor.textContent = result.metrics.monitoredSensors;
            if (wardNumber) wardNumber.textContent = result.metrics.activeAlerts;
            if (sync) sync.textContent = "just now";
        })
        .catch(() => {
            if (typeof showMessage === "function") showMessage("Dashboard data is temporarily unavailable.");
        });
}