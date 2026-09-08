async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
    });
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        const message = typeof payload === "object" && payload.error
            ? payload.error
            : "The request could not be completed.";
        throw new Error(message);
    }

    return payload;
}

function notifyUser(message) {
    if (typeof showMessage === "function") {
        showMessage(message);
    } else {
        window.alert(message);
    }
}
