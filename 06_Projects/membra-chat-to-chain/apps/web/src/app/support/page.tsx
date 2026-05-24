"use client";
import { GlassCard, StatusChip } from "@/components/ui";

export default function SupportPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gradient">Support</h1>
      <GlassCard>
        <h2 className="font-semibold mb-2">Artifact Support QR</h2>
        <p className="text-sm text-text-muted mb-4">
          Support an artifact on devnet. This prepares a QR payload that can be scanned to open the support page.
        </p>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-text-muted block mb-1">Artifact ID</label>
            <input className="w-full bg-background border border-white/10 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary-orange/50" placeholder="MEMBRA-ART-..." />
          </div>
          <button className="bg-primary-orange text-background font-medium px-4 py-2 rounded-md text-sm hover:bg-primary-orange/90 transition-colors">
            Generate QR Campaign
          </button>
        </div>
      </GlassCard>
      <GlassCard>
        <h2 className="font-semibold mb-2">Terms</h2>
        <div className="space-y-2 text-xs text-text-muted">
          <p>- No profit guarantee. Appraisal is directional, not a cash valuation.</p>
          <p>- No private keys or seed phrases are stored.</p>
          <p>- Mainnet execution requires explicit human / multisig approval.</p>
          <p>- This is a proof-of-concept on Solana devnet.</p>
        </div>
        <div className="mt-4 flex gap-2">
          <StatusChip status="active">Devnet Only</StatusChip>
          <StatusChip status="locked">No Auto-Sign</StatusChip>
        </div>
      </GlassCard>
    </div>
  );
}
