async function refreshData() {
    try {
        const result = await apiRequest("/api/monitors/refresh", { method: "POST" });
        const body = document.querySelector("#sensorTable tbody");
        if (body) {
            body.innerHTML = result.items.map((item) => `
                <tr>
                    <td>${item.id}</td><td>${item.location}</td><td>${item.type}</td>
                    <td>${item.value}</td><td><span class="${item.status === "High" ? "danger" : "normal"}">${item.status}</span></td>
                    <td>${item.updated}</td>
                </tr>`).join("");
        }
        notifyUser(result.message);
    } catch (error) {
        notifyUser(error.message);
    }
}