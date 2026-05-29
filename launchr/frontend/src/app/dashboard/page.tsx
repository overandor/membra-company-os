"use client";

import { useState, useEffect } from "react";
import AppraisalForm from "@/components/AppraisalForm";
import AppraisalResults from "@/components/AppraisalResults";
import AssetDetail from "@/components/AssetDetail";
import PortfolioPage from "@/components/PortfolioPage";
import { createAsset, getProfileV2, getRegistryPackages } from "@/lib/api";

type ViewMode = "scan" | "portfolio" | "asset" | "intelligence";

const API_BASE = "https://ruling-studies-speaking-opponents.trycloudflare.com";

export default function Dashboard() {
  const [result, setResult] = useState<any>(null);
  const [assetId, setAssetId] = useState<string | null>(null);
  const [view, setView] = useState<ViewMode>("scan");
  const [creatingAsset, setCreatingAsset] = useState(false);
  const [assetError, setAssetError] = useState("");
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [profileV2, setProfileV2] = useState<any>(null);
  const [loadingIntel, setLoadingIntel] = useState(false);
  const [intelError, setIntelError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/health`, { method: "GET", mode: "cors" })
      .then((r) => setBackendOk(r.ok))
      .catch(() => setBackendOk(false));
  }, []);

  async function handleCreateAsset() {
    if (!result?.github_username) return;
    setCreatingAsset(true);
    setAssetError("");
    try {
      const asset = await createAsset(result.github_username);
      setAssetId(asset.asset_id);
      setView("asset");
    } catch (err: any) {
      const msg = err.message || "";
      if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
        setAssetError("Backend unavailable. Deploy the backend first (see README).");
      } else if (msg.includes("403") || msg.includes("rate limit")) {
        setAssetError("GitHub API rate limit exceeded. Set GITHUB_TOKEN on the backend or wait before retrying.");
      } else {
        setAssetError(msg);
      }
    } finally {
      setCreatingAsset(false);
    }
  }

  async function loadIntelligence() {
    if (!result?.github_username) return;
    setLoadingIntel(true);
    setIntelError("");
    try {
      const intel = await getProfileV2(result.github_username, "github,hf,registry");
      setProfileV2(intel);
      setView("intelligence");
    } catch (err: any) {
      setIntelError(err.message || "Failed to load intelligence");
    } finally {
      setLoadingIntel(false);
    }
  }

  function handleBack() {
    setView("scan");
    setAssetId(null);
  }

  return (
    <div className="min-h-screen pb-20">
      {/* Backend status banner */}
      {backendOk === false && (
        <div className="neu-card mx-4 mt-4 p-4 border-l-4 border-neumorph-warning bg-neumorph-warning/10">
          <p className="text-sm font-semibold text-neumorph-warning">
            ⚠ Backend not connected ({API_BASE})
          </p>
          <p className="text-xs text-neumorph-textLight mt-1">
            The frontend is deployed but the backend API is not reachable. Run the backend locally
            or deploy it to Render/Railway/Fly.io. See the backend README for instructions.
          </p>
        </div>
      )}

      {/* Rate limit warning */}
      {result?.metadata?.rate_limited && (
        <div className="neu-card mx-4 mt-4 p-4 border-l-4 border-neumorph-accent bg-neumorph-accent/10">
          <p className="text-sm font-semibold text-neumorph-accent">
            ℹ GitHub API Rate Limited — Showing Demo Data
          </p>
          <p className="text-xs text-neumorph-textLight mt-1">
            {result.metadata.warning} For real data, set GITHUB_TOKEN on the backend.
          </p>
        </div>
      )}

      {/* Header */}
      <section className="py-12 px-4 text-center">
        <h1 className="text-3xl font-bold text-neumorph-text">Developer Dashboard</h1>
        <p className="text-neumorph-textLight mt-2">Scan, appraise, and capitalize software assets</p>
      </section>

      {/* Scan + Results */}
      {view === "scan" && (
        <>
          <section className="py-6 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto">
            <div className="neu-card p-8">
              <AppraisalForm onResult={setResult} />
            </div>
          </section>

          {result && (
            <section className="pb-6 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
              <div className="neu-card p-6">
                <AppraisalResults data={result} />
              </div>

              <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-6">
                <div className="neu-card p-6 text-center">
                  <p className="text-sm text-neumorph-textLight mb-4">
                    See full Developer Capitalization
                  </p>
                  <button
                    onClick={() => setView("portfolio")}
                    className="neu-btn"
                  >
                    View Portfolio
                  </button>
                </div>

                <div className="neu-card p-6 text-center">
                  <p className="text-sm text-neumorph-textLight mb-4">
                    Multi-source Software Asset Intelligence
                  </p>
                  {intelError && (
                    <p className="mb-4 text-sm text-neumorph-danger">{intelError}</p>
                  )}
                  <button
                    onClick={loadIntelligence}
                    disabled={loadingIntel}
                    className="neu-btn disabled:opacity-50"
                  >
                    {loadingIntel ? "Loading..." : "Asset Intelligence"}
                  </button>
                </div>

                <div className="neu-card p-6 text-center">
                  <p className="text-sm text-neumorph-textLight mb-4">
                    Generate persistent asset + evidence
                  </p>
                  {assetError && (
                    <p className="mb-4 text-sm text-neumorph-danger">{assetError}</p>
                  )}
                  <button
                    onClick={handleCreateAsset}
                    disabled={creatingAsset}
                    className="neu-btn disabled:opacity-50"
                  >
                    {creatingAsset ? "Creating..." : "Create Asset & Evidence"}
                  </button>
                </div>
              </div>
            </section>
          )}
        </>
      )}

      {/* Portfolio View */}
      {view === "portfolio" && result?.github_username && (
        <section className="pb-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto">
          <PortfolioPage
            username={result.github_username}
            onBack={handleBack}
            onSelectAsset={(asset) => {
              console.log("Selected asset:", asset);
            }}
          />
        </section>
      )}

      {/* Asset Detail */}
      {view === "asset" && assetId && (
        <section className="pb-20 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
          <div className="mb-4">
            <button onClick={handleBack} className="neu-btn text-sm">
              ← Back to scan
            </button>
          </div>
          <div className="neu-card p-6">
            <AssetDetail assetId={assetId} />
          </div>
        </section>
      )}

      {/* Multi-source Intelligence View */}
      {view === "intelligence" && profileV2 && (
        <section className="pb-20 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
          <div className="mb-4 flex items-center justify-between">
            <button onClick={handleBack} className="neu-btn text-sm">
              ← Back to scan
            </button>
            <span className="text-xs text-neumorph-accent font-semibold px-3 py-1 rounded-full bg-neumorph-accent/10">
              Phase 2.5 — Multi-source Intelligence
            </span>
          </div>

          {/* Gated notice */}
          <div className="neu-card p-4 mb-6 border-l-4 border-neumorph-accent bg-neumorph-accent/5">
            <p className="text-sm font-semibold text-neumorph-accent">🔒 Token Launch Gated</p>
            <p className="text-xs text-neumorph-textLight mt-1">
              {profileV2.gated_reason} Token launch features are disabled until compliance gates pass.
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="neu-card p-4 text-center">
              <p className="text-2xl font-bold text-neumorph-text">{profileV2.total_assets}</p>
              <p className="text-xs text-neumorph-textLight">Total Assets</p>
            </div>
            <div className="neu-card p-4 text-center">
              <p className="text-2xl font-bold text-neumorph-text">{profileV2.total_downloads.toLocaleString()}</p>
              <p className="text-xs text-neumorph-textLight">Downloads</p>
            </div>
            <div className="neu-card p-4 text-center">
              <p className="text-2xl font-bold text-neumorph-text">{profileV2.total_stars_or_likes.toLocaleString()}</p>
              <p className="text-xs text-neumorph-textLight">Stars / Likes</p>
            </div>
            <div className="neu-card p-4 text-center">
              <p className="text-2xl font-bold text-neumorph-text">{profileV2.quality_summary?.overall_quality?.toFixed(0) ?? "—"}</p>
              <p className="text-xs text-neumorph-textLight">Top Quality Score</p>
            </div>
          </div>

          {/* Sources */}
          <div className="neu-card p-4 mb-6">
            <p className="text-sm font-semibold text-neumorph-text mb-2">Sources Scanned</p>
            <div className="flex flex-wrap gap-2">
              {profileV2.sources_scanned.map((s: string) => (
                <span key={s} className="text-xs px-2 py-1 rounded-full bg-neumorph-bg text-neumorph-text border border-neumorph-shadow">
                  {s}
                </span>
              ))}
            </div>
          </div>

          {/* Asset List */}
          <h2 className="text-xl font-bold text-neumorph-text mb-4">Discovered Assets</h2>
          <div className="space-y-4">
            {profileV2.assets.map((asset: any, idx: number) => (
              <div key={idx} className="neu-card p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold uppercase px-2 py-0.5 rounded bg-neumorph-accent/20 text-neumorph-accent">
                        {asset.source}
                      </span>
                      <a href={asset.url} target="_blank" rel="noreferrer" className="font-semibold text-neumorph-text hover:text-neumorph-accent transition-colors">
                        {asset.name}
                      </a>
                    </div>
                    <p className="text-sm text-neumorph-textLight mt-1">{asset.description || "No description"}</p>
                    <div className="flex gap-4 mt-2 text-xs text-neumorph-textLight">
                      {asset.language && <span>🛠 {asset.language}</span>}
                      {asset.stars_or_likes > 0 && <span>⭐ {asset.stars_or_likes.toLocaleString()}</span>}
                      {asset.downloads > 0 && <span>⬇️ {asset.downloads.toLocaleString()}</span>}
                      {asset.license && <span>📄 {asset.license}</span>}
                      {asset.quality_score && <span>📊 {asset.quality_score.toFixed(0)}</span>}
                    </div>
                  </div>
                </div>
                {asset.deployments && asset.deployments.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-neumorph-shadow">
                    <p className="text-xs font-semibold text-neumorph-text mb-1">Deployments</p>
                    <div className="flex flex-wrap gap-2">
                      {asset.deployments.map((d: any, i: number) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded bg-green-500/10 text-green-400 border border-green-500/20">
                          {d.platform} {d.detected_framework ? `(${d.detected_framework})` : ""}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
