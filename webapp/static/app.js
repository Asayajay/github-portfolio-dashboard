/*
 * Fetches /api/scan and renders the result: stat tiles, the health chart,
 * and a per-repo table. Runs once on page load, and again on demand
 * whenever the form is submitted -- every call is a fresh GitHub API scan
 * server-side, nothing is cached client-side between runs.
 */

const form = document.getElementById("scan-form");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const refreshBtn = document.getElementById("refresh-btn");

function markCell(passed) {
  return passed ? "✓" : "✗";
}

function recencyLabel(days) {
  if (days === null || days === undefined) return "no commits";
  if (days === 0) return "today";
  if (days === 1) return "1 day ago";
  return `${days} days ago`;
}

async function runScan() {
  statusEl.textContent = "Scanning...";
  statusEl.classList.remove("error");
  resultsEl.classList.add("hidden");
  refreshBtn.disabled = true;

  const params = new URLSearchParams();
  const owner = form.owner.value.trim();
  if (owner) params.set("owner", owner);
  params.set("include_forks", form.include_forks.checked);
  params.set("include_archived", form.include_archived.checked);

  try {
    const response = await fetch(`/api/scan?${params.toString()}`);
    const body = await response.json();

    if (!response.ok) {
      statusEl.textContent = `Error: ${body.error}`;
      statusEl.classList.add("error");
      return;
    }

    render(body);
    statusEl.textContent = `Last scanned ${new Date().toLocaleTimeString()}`;
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
    statusEl.classList.add("error");
  } finally {
    refreshBtn.disabled = false;
  }
}

function render(body) {
  const { summary, repos } = body;

  document.getElementById("stat-repo-count").textContent = summary.repo_count;
  document.getElementById("stat-healthy").textContent = summary.fully_healthy_count;
  document.getElementById("stat-avg").textContent = `${summary.average_hygiene_percent}%`;
  document.getElementById("stat-issues").textContent = summary.total_open_issues;
  document.getElementById("stat-stale").textContent = summary.stale_count;

  const canvas = document.getElementById("health-chart");
  drawHealthChart(
    canvas,
    repos.map((r) => ({ label: r.full_name, value: r.hygiene_percent }))
  );

  const tbody = document.querySelector("#repo-table tbody");
  tbody.innerHTML = "";
  repos
    .slice()
    .sort((a, b) => a.full_name.localeCompare(b.full_name))
    .forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.full_name}</td>
        <td>${markCell(r.license_ok)}</td>
        <td>${markCell(r.readme_ok)}</td>
        <td>${markCell(r.gitignore_ok)}</td>
        <td>${recencyLabel(r.days_since_last_commit)}${r.is_stale ? " (stale)" : ""}</td>
        <td>${r.open_issue_count}</td>
      `;
      tbody.appendChild(tr);
    });

  resultsEl.classList.remove("hidden");
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runScan();
});

runScan();
