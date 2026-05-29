const API_BASE = "https://ruling-studies-speaking-opponents.trycloudflare.com";

export async function scanUser(username: string) {
  const res = await fetch(`${API_BASE}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ github_username: username }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getRepos(username: string) {
  const res = await fetch(`${API_BASE}/repos/${username}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function appraiseRepo(username: string, repo: string) {
  const res = await fetch(`${API_BASE}/appraise/${username}/${repo}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getEvidence(username: string, repo: string) {
  const res = await fetch(`${API_BASE}/evidence/${username}/${repo}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function getReportPdfUrl(username: string, repo: string) {
  return `${API_BASE}/report/pdf/${username}/${repo}`;
}

// Phase 2: Asset management
export async function createAsset(username: string) {
  const res = await fetch(`${API_BASE}/assets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ github_username: username }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listAssets() {
  const res = await fetch(`${API_BASE}/assets`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAsset(assetId: string) {
  const res = await fetch(`${API_BASE}/assets/${assetId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function verifyGitHubOwner(username: string, repo: string, token?: string) {
  const res = await fetch(`${API_BASE}/verify/github-owner`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ github_username: username, repo_full_name: repo, github_token: token, verification_method: token ? "token" : "none" }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getOwnership(assetId: string) {
  const res = await fetch(`${API_BASE}/assets/${assetId}/ownership`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function buildEvidenceV2(assetId: string) {
  const res = await fetch(`${API_BASE}/evidence/${assetId}`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getEvidenceByAsset(assetId: string) {
  const res = await fetch(`${API_BASE}/evidence/${assetId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function getPacketJsonUrl(assetId: string) {
  return `${API_BASE}/evidence/${assetId}/packet.json`;
}

export async function verifyPacket(assetId: string) {
  const res = await fetch(`${API_BASE}/evidence/${assetId}/verify`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createEpoch(assetId: string, trigger: string, notes?: string) {
  const res = await fetch(`${API_BASE}/evidence/${assetId}/epoch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ asset_id: assetId, trigger, notes }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listEpochs(assetId: string) {
  const res = await fetch(`${API_BASE}/assets/${assetId}/epochs`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Portfolio Layer
export async function getProfile(username: string, sources: string = "github") {
  const res = await fetch(`${API_BASE}/profile/${username}?sources=${sources}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listPortfolios() {
  const res = await fetch(`${API_BASE}/portfolios`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPortfolio(portfolioId: string) {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Phase 2.5 — Multi-source Software Asset Intelligence
export async function getProfileV2(username: string, sources: string = "github") {
  const res = await fetch(`${API_BASE}/profile-v2/${username}?sources=${sources}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getQualityScore(username: string, repo: string) {
  const res = await fetch(`${API_BASE}/quality/${username}/${repo}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getRegistryPackages(username: string) {
  const res = await fetch(`${API_BASE}/registry/${username}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDeployments(repoFullName: string) {
  const res = await fetch(`${API_BASE}/deployments/${repoFullName}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function exportEvidence(assetId: string) {
  const res = await fetch(`${API_BASE}/evidence/${assetId}/export`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
