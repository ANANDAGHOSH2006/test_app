async function searchHistory() {
    const inputs = document.querySelectorAll(".filter input");
    const eventType = document.querySelector(".filter select")?.value || "";
    const query = eventType === "All Events" ? "" : eventType;
    const params = new URLSearchParams({ q: query });
    try {
        const result = await apiRequest(`/api/history?${params}`);
        const body = document.querySelector("#historyTable tbody");
        if (body) {
            body.innerHTML = result.items.map((item) => `
                <tr><td>${item.date}</td><td>${item.disaster}</td><td>${item.location}</td>
                <td>${item.severity} severity</td><td><button class="view" type="button">View</button></td></tr>`).join("");
            bindHistoryButtons();
        }
        notifyUser(`${result.total} historical records found.`);
    } catch (error) {
        notifyUser(error.message);
    }
}

function exportReport() {
    window.location.href = "/api/history/export";
}

function bindHistoryButtons() {
    document.querySelectorAll(".view").forEach(button => {
        button.addEventListener("click", function () {
            notifyUser("Historical disaster report opened.");
        });
    });
}

bindHistoryButtons();