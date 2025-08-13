document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const toggleBtn = document.getElementById("toggle-sidebar");

    toggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed");
    });
});
