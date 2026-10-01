// Light/dark toggle and the mobile sidebar menu.
(() => {
  const root = document.documentElement;
  const darkQuery = matchMedia("(prefers-color-scheme: dark)");
  const toggle = document.querySelector(".theme-toggle");
  const menuButton = document.querySelector(".menu-btn");
  const backdrop = document.querySelector(".nav-backdrop");

  const currentTheme = () => root.dataset.theme || (darkQuery.matches ? "dark" : "light");

  function updateToggleLabel() {
    if (!toggle) return;
    const next = currentTheme() === "dark" ? "light" : "dark";
    toggle.setAttribute("aria-label", `Switch to ${next} mode`);
    toggle.title = `Switch to ${next} mode`;
  }

  function setMenu(open) {
    document.body.classList.toggle("nav-open", open);
    if (menuButton) menuButton.setAttribute("aria-expanded", String(open));
    if (backdrop) backdrop.hidden = !open;
  }

  toggle?.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    root.classList.add("theme-switching");
    root.dataset.theme = next;
    requestAnimationFrame(() => requestAnimationFrame(() => root.classList.remove("theme-switching")));
    try {
      localStorage.setItem("theme", next);
    } catch (e) {}
    updateToggleLabel();
  });

  menuButton?.addEventListener("click", () => setMenu(!document.body.classList.contains("nav-open")));
  backdrop?.addEventListener("click", () => setMenu(false));
  document.querySelectorAll(".sidebar a").forEach((a) => a.addEventListener("click", () => setMenu(false)));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setMenu(false);
  });

  darkQuery.addEventListener("change", updateToggleLabel);
  updateToggleLabel();
})();
