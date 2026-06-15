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

document.getElementById("download-btn").addEventListener("click", downloadAuraScore);

async function downloadAuraScore() {
  const btn = document.getElementById("download-btn");
  const card = document.getElementById("story-card");

  document.getElementById("story-score").textContent =
    data.score?.toLocaleString() ?? "—";
  document.getElementById("story-max-score").textContent =
    "/ " + (data.max_score?.toLocaleString() ?? "100");
  document.getElementById("story-tier").textContent =
    data.tier_title ?? "UNKNOWN";
  const roastEl = document.getElementById("story-roast");
  if (roastEl) {
    roastEl.textContent = data.specific_roast ?? "";
  }

  card.style.opacity = "1";

  const original = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML =
    '<span class="material-symbols-outlined">downloading</span> GENERATING...';

  try {
    const dataUrl = await htmlToImage.toPng(card, {
      quality: 1,
      pixelRatio: 3,
    });
    const link = document.createElement("a");
    link.download = "slaylist-aura.png";
    link.href = dataUrl;
    link.click();

    btn.innerHTML =
      '<span class="material-symbols-outlined">check</span> DOWNLOADED!';
    btn.classList.remove("bg-primary");
    btn.classList.add("bg-tertiary");
  } catch {
    btn.innerHTML =
      '<span class="material-symbols-outlined">error</span> FAILED';
  } finally {
    card.style.opacity = "0";
    setTimeout(() => {
      btn.innerHTML = original;
      btn.classList.add("bg-primary");
      btn.classList.remove("bg-tertiary");
      btn.disabled = false;
    }, 2000);
  }
}
