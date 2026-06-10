let data;
try {
  data = JSON.parse(localStorage.getItem("aura"));
} catch {
  data = null;
}

if (!data) {
  window.location.href = "/";
}

if (data.score == null) {
  document.getElementById("score").textContent = "—";
  document.getElementById("tier-title").textContent = "ANALYSIS FAILED";
  document.getElementById("tagline").textContent =
    "Slaylist dropped the ball. Try again.";
} else {
  populate();
}

function populate() {
  document.getElementById("score").textContent =
    data.score?.toLocaleString() ?? "—";
  document.getElementById("max-score").textContent =
    "/ " + (data.max_score?.toLocaleString() ?? "100");
  document.getElementById("tier-title").textContent =
    data.tier_title ?? "UNKNOWN";
  document.getElementById("tagline").textContent = data.tagline ?? "";

  const roastEl = document.getElementById("roast");
  if (roastEl) roastEl.textContent = data.specific_roast ?? "";
}

document.getElementById("try-another").addEventListener("click", () => {
  localStorage.removeItem("aura");
  window.location.href = "/";
});
