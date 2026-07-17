const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function badge(status, risk) {
  const value = status || risk || "unknown";
  const cls = value === "blocked" || risk === "critical" || risk === "high" ? "danger" : value === "needs_approval" || risk === "medium" ? "warn" : "";
  return `<span class="badge ${cls}">${value}</span>`;
}

async function loadStatus() {
  const status = await api("/api/status");
  $("modeBadge").textContent = status.mode;
  $("auditCount").textContent = status.audit_events;
}

async function loadActions() {
  const data = await api("/api/actions");
  $("actionSelect").innerHTML = data.actions.filter((a) => a.allowed).map((a) => `<option value="${a.name}">${a.name}</option>`).join("");
  $("actionsList").innerHTML = data.actions.map((a) => `
    <div class="action-item">
      <div class="action-top"><strong>${a.name}</strong>${badge(null, a.risk)}</div>
      <p>${a.description}</p>
      <p>Allowed: <b>${a.allowed}</b> · Approval: <b>${a.requires_approval}</b> · Simulator-only: <b>${a.simulator_only}</b></p>
    </div>`).join("");
}

function renderAuditItem(event) {
  const status = event.status || "unknown";
  const cls = status === "blocked" ? "blocked" : status === "needs_approval" ? "pending" : status.includes("executed") || status === "approved" ? "executed" : "";
  const approval = status === "needs_approval" ? `<button data-approve="${event.id}">Approve</button>` : "";
  const reason = event.decision?.reason || "No decision reason recorded.";
  return `<div class="audit-item ${cls}"><div class="audit-top"><strong>${event.action || "event"}</strong>${badge(status)}</div><p><code>${event.id}</code></p><p>${reason}</p><p>Source: ${event.source || "system"}</p>${approval}</div>`;
}

async function loadAudit() {
  const data = await api("/api/audit");
  const events = data.events || [];
  $("auditList").innerHTML = events.length ? events.map(renderAuditItem).join("") : `<p>No audit events yet.</p>`;
  const pending = events.filter((e) => e.status === "needs_approval");
  $("pendingList").innerHTML = pending.length ? pending.map(renderAuditItem).join("") : `<p>No pending approvals.</p>`;
  document.querySelectorAll("[data-approve]").forEach((button) => button.addEventListener("click", async () => { await api(`/api/approve/${button.dataset.approve}`, { method: "POST" }); await refreshAll(); }));
}

async function submitProposal() {
  let parameters = {};
  try { parameters = JSON.parse($("paramsInput").value || "{}"); } catch { alert("Parameters must be valid JSON."); return; }
  await api("/api/propose", { method: "POST", body: JSON.stringify({ source: "dashboard", goal: $("goalInput").value, action: $("actionSelect").value, parameters }) });
  await refreshAll();
}

async function refreshAll() { await loadStatus(); await loadActions(); await loadAudit(); }

$("loadDemo").addEventListener("click", async () => { await api("/api/demo/load", { method: "POST" }); await refreshAll(); });
$("refreshAudit").addEventListener("click", refreshAll);
$("submitProposal").addEventListener("click", submitProposal);
$("clearAudit").addEventListener("click", async () => { if (confirm("Clear the local audit log?")) { await api("/api/audit", { method: "DELETE" }); await refreshAll(); }});
$("exportAudit").addEventListener("click", () => { window.open("/api/export/audit.json", "_blank"); });
refreshAll().catch((error) => console.error(error));
