const themeButton = document.getElementById("themeButton");

function setNavigationTheme(isLight) {
    document.body.classList.toggle("light-theme", isLight);
    document.body.classList.toggle("dark-theme", !isLight);
    document.body.classList.toggle("dark", !isLight);
    themeButton.textContent = isLight ? "☾ Dark mode" : "☀ Bright mode";
    themeButton.setAttribute("aria-label", isLight ? "Switch to dark mode" : "Switch to bright mode");
    themeButton.setAttribute("title", isLight ? "Switch to dark mode" : "Switch to bright mode");
    localStorage.setItem("ndrf-theme", isLight ? "light" : "dark");
}

if (themeButton) {
    setNavigationTheme(localStorage.getItem("ndrf-theme") === "light");
    themeButton.addEventListener("click", () => {
        setNavigationTheme(!document.body.classList.contains("light-theme"));
    });
}
