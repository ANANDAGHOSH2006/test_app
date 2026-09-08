function runPageSearch(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const query = form.querySelector("input").value.trim().toLowerCase();
    const content = document.querySelector("main");
    const searchableItems = content.querySelectorAll("h1, h2, h3, h4, p, strong, b, td, label, .card, .panel");

    searchableItems.forEach((item) => {
        item.hidden = Boolean(query) && !item.textContent.toLowerCase().includes(query);
    });

    if (query && ![...searchableItems].some((item) => !item.hidden)) {
        window.alert(`No results found for "${query}".`);
    }

    return false;
}