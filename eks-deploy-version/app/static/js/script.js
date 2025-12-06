function toggleTheme() {
  const body = document.getElementById("themeBody");
  body.classList.toggle("dark");
  localStorage.setItem("theme", body.classList.contains("dark") ? "dark" : "light");
}
window.onload = function () {
  if (localStorage.getItem("theme") === "dark") {
    document.getElementById("themeBody").classList.add("dark");
  }
};
