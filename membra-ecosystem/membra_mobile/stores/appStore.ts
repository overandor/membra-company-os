import { create } from 'zustand';
import type { Asset, CampaignOffer, MediaKit, ProofSubmission, QRScanEvent, Claim, RewardStatus } from '@/types';

interface AppState {
  assets: Asset[];
  offers: CampaignOffer[];
  mediaKits: MediaKit[];
  proofs: ProofSubmission[];
  scans: QRScanEvent[];
  claims: Claim[];
  rewardStatus: RewardStatus | null;
  isLoading: boolean;
  error: string | null;
  setAssets: (assets: Asset[]) => void;
  addAsset: (asset: Asset) => void;
  setOffers: (offers: CampaignOffer[]) => void;
  updateOffer: (offer: CampaignOffer) => void;
  setMediaKits: (kits: MediaKit[]) => void;
  updateMediaKit: (kit: MediaKit) => void;
  setProofs: (proofs: ProofSubmission[]) => void;
  addProof: (proof: ProofSubmission) => void;
  setScans: (scans: QRScanEvent[]) => void;
  addScan: (scan: QRScanEvent) => void;
  setClaims: (claims: Claim[]) => void;
  addClaim: (claim: Claim) => void;
  setRewardStatus: (status: RewardStatus | null) => void;
  setLoading: (value: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  assets: [],
  offers: [],
  mediaKits: [],
  proofs: [],
  scans: [],
  claims: [],
  rewardStatus: null,
  isLoading: false,
  error: null,
  setAssets: (assets) => set({ assets }),
  addAsset: (asset) => set((state) => ({ assets: [asset, ...state.assets] })),
  setOffers: (offers) => set({ offers }),
  updateOffer: (offer) => set((state) => ({
    offers: state.offers.map((o) =>
      o.campaign.id === offer.campaign.id ? offer : o
    ),
  })),
  setMediaKits: (mediaKits) => set({ mediaKits }),
  updateMediaKit: (kit) => set((state) => ({
    mediaKits: state.mediaKits.map((k) => (k.id === kit.id ? kit : k)),
  })),
  setProofs: (proofs) => set({ proofs }),
  addProof: (proof) => set((state) => ({ proofs: [proof, ...state.proofs] })),
  setScans: (scans) => set({ scans }),
  addScan: (scan) => set((state) => ({ scans: [scan, ...state.scans] })),
  setClaims: (claims) => set({ claims }),
  addClaim: (claim) => set((state) => ({ claims: [claim, ...state.claims] })),
  setRewardStatus: (rewardStatus) => set({ rewardStatus }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));
