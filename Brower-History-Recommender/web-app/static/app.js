const form = document.getElementById("reco-form");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const sourcesEl = document.getElementById("sources");
const resetBtn = document.getElementById("reset-btn");

function readFormData() {
  const data = new FormData(form);
  return {
    history: data.get("history") || "",
    profile: data.get("profile") || "",
    recent_days: Number(data.get("recent_days") || 14),
    since: data.get("since") || "",
    limit: Number(data.get("limit") || 15),
    min_visits: Number(data.get("min_visits") || 1),
    exclude_hosts: data.get("exclude_hosts") || "",
    exclude_url_pattern: data.get("exclude_url_pattern") || "",
    no_reading_filter: Boolean(data.get("no_reading_filter")),
    use_arxiv: Boolean(data.get("use_arxiv")),
    use_crossref: Boolean(data.get("use_crossref")),
    use_semantic_scholar: Boolean(data.get("use_semantic_scholar")),
  };
}

function renderError(message) {
  resultsEl.innerHTML = `<div class="cluster"><h3>Problem</h3><p>${message}</p></div>`;
  sourcesEl.innerHTML = "";
}

function renderSources(payload) {
  sourcesEl.innerHTML = "";
  const interest = (payload.interest_tokens || []).join(", ");
  const topics = (payload.topics || []).join(", ");
  const queries = (payload.queries || []).join(" | ");

  const wrapper = document.createElement("div");
  wrapper.className = "cluster sources-block";

  const heading = document.createElement("h3");
  heading.textContent = "New Reading Recommendations";

  const sub = document.createElement("p");
  sub.textContent = interest
    ? `Based on your recent topics: ${interest}`
    : "Based on your recent topics.";

  const meta = document.createElement("p");
  meta.className = "muted";
  meta.textContent = topics
    ? `AI topics: ${topics}`
    : "AI topics are inferred from your recent browsing.";

  const query = document.createElement("p");
  query.className = "muted";
  query.textContent = queries ? `arXiv queries: ${queries}` : "";

  wrapper.appendChild(heading);
  wrapper.appendChild(sub);
  wrapper.appendChild(meta);
  if (queries) wrapper.appendChild(query);

  const warnings = payload.warnings || [];
  if (warnings.length) {
    const warn = document.createElement("p");
    warn.className = "muted";
    warn.textContent = `Warnings: ${warnings.join(" | ")}`;
    wrapper.appendChild(warn);
  }

  sourcesEl.appendChild(wrapper);
}

function renderClusters(payload) {
  resultsEl.innerHTML = "";
  const sources = payload.new_recommendations || {};
  const sections = [
    { key: "arxiv", title: "arXiv Recommendations" },
    { key: "crossref", title: "Crossref Recommendations" },
    { key: "semantic_scholar", title: "Semantic Scholar Recommendations" },
  ];

  const hasAny = sections.some((section) => (sources[section.key] || []).length);
  if (!hasAny) {
    renderError("No new recommendations returned.");
    return;
  }

  sections.forEach((section) => {
    const items = sources[section.key] || [];
    if (!items.length) return;

    const wrapper = document.createElement("div");
    wrapper.className = "cluster";

    const title = document.createElement("h3");
    title.textContent = section.title;
    wrapper.appendChild(title);

    items.forEach((item) => {
      const card = document.createElement("div");
      card.className = "item";

      const cardTitle = document.createElement("div");
      cardTitle.className = "item-title";
      cardTitle.textContent = item.title || item.url;

      const meta = document.createElement("div");
      meta.className = "item-meta";
      const authors = (item.authors || []).slice(0, 3).join(", ");
      meta.textContent = `Score: ${item.score} | Published: ${item.published || "n/a"} | Authors: ${authors}`;

      const why = document.createElement("div");
      why.className = "item-meta";
      why.textContent = `Why: ${item.why || ""}`;

      const summary = document.createElement("div");
      summary.className = "item-meta";
      summary.textContent = item.summary ? item.summary.slice(0, 260) + "..." : "";

      const link = document.createElement("a");
      link.href = item.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = "View source";

      card.appendChild(cardTitle);
      card.appendChild(meta);
      card.appendChild(why);
      if (item.summary) card.appendChild(summary);
      if (item.url) card.appendChild(link);
      if (item.pdf_url) {
        const pdf = document.createElement("a");
        pdf.href = item.pdf_url;
        pdf.target = "_blank";
        pdf.rel = "noreferrer";
        pdf.textContent = "PDF";
        pdf.style.marginLeft = "12px";
        card.appendChild(pdf);
      }
      wrapper.appendChild(card);
    });

    resultsEl.appendChild(wrapper);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusEl.textContent = "Working...";
  resultsEl.innerHTML = "";
  sourcesEl.innerHTML = "";

  try {
    const response = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(readFormData()),
    });
    const payload = await response.json();
    if (!response.ok) {
      renderError(payload.error || "Something went wrong.");
      statusEl.textContent = "Try adjusting filters and run again.";
      return;
    }
    renderSources(payload);
    renderClusters(payload);
    statusEl.textContent = "Done.";
  } catch (error) {
    renderError("Failed to reach the server. Is it running on port 8000?");
    statusEl.textContent = "Connection failed.";
  }
});

resetBtn.addEventListener("click", () => {
  form.reset();
  resultsEl.innerHTML = "";
  sourcesEl.innerHTML = "";
  statusEl.textContent = "Ready when you are.";
});
