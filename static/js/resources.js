async function addDeployment() {
    const name = window.prompt("Resource name:");
    if (!name) return;
    try {
        const result = await apiRequest("/api/resources", {
            method: "POST",
            body: JSON.stringify({ name, category: "Teams", location: "Dehradun Base" }),
        });
        notifyUser(result.message);
    } catch (error) {
        notifyUser(error.message);
    }
}

document.querySelectorAll(".track").forEach(button => {
    button.addEventListener("click", function () {
        const rowIndex = Array.from(this.closest("tbody").children).indexOf(this.closest("tr"));
        apiRequest("/api/resources")
            .then((result) => result.items[rowIndex])
            .then((item) => notifyUser(item ? `${item.name} is ${item.status} at ${item.location}.` : "Resource details are unavailable."))
            .catch((error) => notifyUser(error.message));
    });
});

document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", function () {

        document.querySelectorAll(".tab")
            .forEach(t => t.classList.remove("active"));

        this.classList.add("active");
    });
});