const { useState, useEffect, useRef } = React;

// ============== UTILS ==============
const shorten = (addr, n = 6) => addr ? `${addr.slice(0, n)}...${addr.slice(-n)}` : '';
const generateClaimId = () => {
  const arr = new Uint8Array(32);
  crypto.getRandomValues(arr);
  return Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join('');
};

// ============== WALLET HOOK ==============
function useWallet() {
  const [connected, setConnected] = useState(false);
  const [publicKey, setPublicKey] = useState(null);
  const [provider, setProvider] = useState(null);

  useEffect(() => {
    const getProvider = () => {
      if ('phantom' in window) {
        const p = window.phantom?.solana;
        if (p?.isPhantom) return p;
      }
      if ('solflare' in window) {
        const p = window.solflare;
        if (p?.isSolflare) return p;
      }
      return null;
    };
    setProvider(getProvider());
  }, []);

  const connect = async () => {
    if (!provider) { alert('Install Phantom or Solflare wallet'); return; }
    try {
      const resp = await provider.connect();
      setPublicKey(resp.publicKey.toString());
      setConnected(true);
    } catch (e) { console.error(e); }
  };

  const disconnect = async () => {
    if (provider) { await provider.disconnect(); }
    setPublicKey(null);
    setConnected(false);
  };

  useEffect(() => {
    if (provider) {
      provider.on('connect', (pk) => { setPublicKey(pk.toString()); setConnected(true); });
      provider.on('disconnect', () => { setPublicKey(null); setConnected(false); });
      if (provider.isConnected && provider.publicKey) {
        setPublicKey(provider.publicKey.toString());
        setConnected(true);
      }
    }
  }, [provider]);

  return { connected, publicKey, connect, disconnect, provider };
}

// ============== MOCK API (replace with real Anchor calls) ==============
const MOCK_NOTES = [
  { serial: 1, denom: 1000000000, holder: 'sender123...', redeemed: false, created_at: Date.now() - 86400000 },
  { serial: 2, denom: 5000000000, holder: 'sender123...', redeemed: false, created_at: Date.now() - 172800000 },
  { serial: 3, denom: 10000000000, holder: 'other456...', redeemed: true, created_at: Date.now() - 259200000 },
];

const MOCK_CLAIMS = [
  { id: 'abc123def456', assets: [{type:'BTC',amount:0.0001},{type:'USDC',amount:5.00}], claimed: false, expires_at: Date.now() + 86400000 },
];

function formatDenom(sats) {
  const btc = sats / 1e8;
  if (btc < 0.001) return `${sats} sats`;
  return `${btc.toFixed(6)} BTC`;
}

function formatUsd(sats, btcPrice = 65000) {
  const usd = (sats / 1e8) * btcPrice;
  return `$${usd.toFixed(2)}`;
}

// ============== COMPONENTS ==============

function RiskBanner() {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;
  return (
    <div className="bg-red-900/30 border-b border-red-500/30 px-4 py-2 text-center">
      <p className="text-xs text-red-200">
        <strong>Risk Warning:</strong> Membra Money is experimental. BTC-backed notes are custodial claims, not native Bitcoin.
        Loss of claim links, reserve insolvency, or smart contract bugs may result in loss of funds.
        <button onClick={() => setDismissed(true)} className="ml-2 underline text-red-300">Dismiss</button>
      </p>
    </div>
  );
}

function ReserveView() {
  const [proof, setProof] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/reserves/proof')
      .then(r => r.ok ? r.json() : null)
      .then(data => setProof(data))
      .catch(() => setProof({ degraded_source: true, disclaimer: 'Reserve data unavailable in demo mode.' }))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="card rounded-xl p-6 text-center text-gray-400">Loading reserve data...</div>;

  return (
    <div className="space-y-4">
      <div className="card rounded-xl p-6">
        <h3 className="text-lg font-bold mb-2">Reserve Status</h3>
        {proof && (
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-400">Reserve Ratio</span><span className={proof.reserve_ratio_bps >= 10000 ? 'text-green-400' : 'text-red-400'}>{(proof.reserve_ratio_bps / 100).toFixed(2)}%</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Fully Backed</span><span>{proof.fully_backed ? 'Yes' : 'No'}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Can Mint</span><span>{proof.can_mint_new_notes ? 'Yes' : 'No'}</span></div>
            {proof.degraded_source && <div className="text-amber-400 text-xs">Warning: reserve source is degraded or unavailable.</div>}
            <div className="text-xs text-gray-500 mt-2">{proof.disclaimer}</div>
          </div>
        )}
      </div>
      {proof && proof.snapshots && proof.snapshots.map((s, i) => (
        <div key={i} className="card rounded-xl p-4 text-sm">
          <div className="flex justify-between"><span className="text-gray-400">Address</span><span className="mono">{shorten(s.address, 8)}</span></div>
          <div className="flex justify-between"><span className="text-gray-400">Observed</span><span>{s.observed_sats} sats</span></div>
          <div className="flex justify-between"><span className="text-gray-400">Type</span><span>{s.wallet_type}</span></div>
          <div className="flex justify-between"><span className="text-gray-400">Proof Hash</span><span className="mono">{shorten(s.proof_hash, 8)}</span></div>
        </div>
      ))}
    </div>
  );
}

function AuditLogView() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/audit/events?limit=50')
      .then(r => r.ok ? r.json() : null)
      .then(data => setEvents(data?.events || []))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="card rounded-xl p-6 text-center text-gray-400">Loading audit logs...</div>;

  return (
    <div className="card rounded-xl p-6">
      <h3 className="text-lg font-bold mb-4">Audit Log</h3>
      {events.length === 0 ? (
        <p className="text-sm text-gray-500">No audit events available.</p>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {events.map(e => (
            <div key={e.id} className="bg-black/30 rounded-lg p-3 text-sm">
              <div className="flex justify-between"><span className="text-amber-400 font-semibold">{e.event_type}</span><span className="text-gray-500 text-xs">{e.created_at}</span></div>
              {e.wallet_address && <div className="text-gray-400 text-xs mono">{shorten(e.wallet_address)}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Header({ wallet }) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-md border-b border-white/10">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg btn-primary flex items-center justify-center">
            <span className="text-black font-bold text-sm">₿</span>
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight">Membra Money</h1>
            <p className="text-xs text-gray-400">Bitcoin Bearer Notes</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {wallet.connected ? (
            <div className="flex items-center gap-3">
              <span className="text-sm text-green-400 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                {shorten(wallet.publicKey)}
              </span>
              <button onClick={wallet.disconnect} className="px-3 py-1.5 text-sm bg-white/10 rounded-lg hover:bg-white/20 transition">
                Disconnect
              </button>
            </div>
          ) : (
            <button onClick={wallet.connect} className="px-4 py-2 btn-primary text-black font-semibold rounded-lg text-sm transition">
              Connect Wallet
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

function NoteCard({ note, onTransfer, onRedeem }) {
  const [showQR, setShowQR] = useState(false);
  const qrRef = useRef(null);

  useEffect(() => {
    if (showQR && qrRef.current) {
      qrRef.current.innerHTML = '';
      new QRCode(qrRef.current, {
        text: `coinpack://note/${note.serial}`,
        width: 160,
        height: 160,
        colorDark: '#f59e0b',
        colorLight: '#0a0e1a',
        correctLevel: QRCode.CorrectLevel.M,
      });
    }
  }, [showQR]);

  return (
    <div className="note-card rounded-xl p-5 slide-in">
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Note #{note.serial}</div>
          <div className="text-2xl font-bold gradient-text mono">{formatDenom(note.denom)}</div>
          <div className="text-sm text-gray-400">{formatUsd(note.denom)}</div>
        </div>
        <div className={`px-2 py-1 rounded text-xs font-semibold ${note.redeemed ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
          {note.redeemed ? 'REDEEMED' : 'ACTIVE'}
        </div>
      </div>
      <div className="flex gap-2 mb-3">
        <span className="text-xs bg-white/5 px-2 py-1 rounded text-gray-400 mono">Holder: {shorten(note.holder)}</span>
      </div>
      {!note.redeemed && (
        <div className="flex gap-2">
          <button onClick={() => setShowQR(!showQR)} className="flex-1 px-3 py-2 bg-white/10 rounded-lg text-sm font-medium hover:bg-white/20 transition flex items-center justify-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4h2v-4zM6 20h2v-4H6v4zm6-6h2v-4h-2v4zm-6 0h2v-4H6v4zm12-6h2V4h-2v4zM6 10h2V6H6v4zm6-6h2V4h-2v4z"/></svg>
            Show QR
          </button>
          <button onClick={onTransfer} className="flex-1 px-3 py-2 bg-white/10 rounded-lg text-sm font-medium hover:bg-white/20 transition">
            Transfer
          </button>
          <button onClick={onRedeem} className="flex-1 px-3 py-2 btn-primary text-black font-semibold rounded-lg text-sm transition">
            Redeem
          </button>
        </div>
      )}
      {showQR && (
        <div className="mt-4 flex flex-col items-center p-4 bg-black/50 rounded-lg">
          <div ref={qrRef} className="mb-2"></div>
          <p className="text-xs text-gray-500 mono">coinpack://note/{note.serial}</p>
        </div>
      )}
    </div>
  );
}

function MintNoteForm({ wallet, onMint }) {
  const [denom, setDenom] = useState('1000000000');
  const [loading, setLoading] = useState(false);

  const denoms = [
    { label: '$10', value: '1000000000', usd: '$10' },
    { label: '$50', value: '5000000000', usd: '$50' },
    { label: '$100', value: '10000000000', usd: '$100' },
    { label: '$500', value: '50000000000', usd: '$500' },
  ];

  const handleMint = async () => {
    setLoading(true);
    setTimeout(() => {
      onMint({ serial: Math.floor(Math.random()*100000), denom: parseInt(denom), holder: wallet.publicKey });
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="card rounded-xl p-6">
      <h3 className="text-lg font-bold mb-4">Mint New Note</h3>
      <div className="grid grid-cols-2 gap-3 mb-6">
        {denoms.map(d => (
          <button
            key={d.value}
            onClick={() => setDenom(d.value)}
            className={`p-4 rounded-xl border transition ${denom === d.value ? 'border-amber-500 bg-amber-500/10' : 'border-white/10 bg-white/5 hover:bg-white/10'}`}
          >
            <div className="text-lg font-bold">{d.label}</div>
            <div className="text-xs text-gray-400">{formatDenom(parseInt(d.value))}</div>
          </button>
        ))}
      </div>
      <button
        onClick={handleMint}
        disabled={loading || !wallet.connected}
        className="w-full py-3 btn-primary text-black font-bold rounded-xl transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Minting...' : wallet.connected ? 'Mint Note' : 'Connect Wallet to Mint'}
      </button>
    </div>
  );
}

function CreateCoinPack({ wallet }) {
  const [assets, setAssets] = useState([{ type: 'BTC', amount: '' }, { type: 'USDC', amount: '' }]);
  const [pin, setPin] = useState('');
  const [expires, setExpires] = useState('24');
  const [claimLink, setClaimLink] = useState(null);
  const [qrData, setQrData] = useState(null);
  const qrRef = useRef(null);

  const addAsset = () => {
    if (assets.length < 5) setAssets([...assets, { type: 'SOL', amount: '' }]);
  };
  const removeAsset = (i) => setAssets(assets.filter((_, idx) => idx !== i));
  const updateAsset = (i, field, value) => {
    const a = [...assets];
    a[i][field] = value;
    setAssets(a);
  };

  const create = () => {
    const validAssets = assets.filter(a => a.amount && parseFloat(a.amount) > 0);
    if (!pin || pin.length < 4) { alert('PIN must be at least 4 digits'); return; }
    if (validAssets.length === 0) { alert('Add at least one asset'); return; }

    const claimId = generateClaimId();
    const link = `${window.location.origin}/claim/${claimId}`;
    setClaimLink({ id: claimId, url: link, assets: validAssets, pin, expires });
    // SECURITY: Never include PIN in QR or URL. QR contains only claim ID.
    setQrData(`coinpack://claim/${claimId}`);
  };

  useEffect(() => {
    if (qrData && qrRef.current) {
      qrRef.current.innerHTML = '';
      new QRCode(qrRef.current, {
        text: qrData,
        width: 200,
        height: 200,
        colorDark: '#f59e0b',
        colorLight: '#0a0e1a',
      });
    }
  }, [qrData]);

  if (claimLink) {
    return (
      <div className="card rounded-xl p-6 text-center">
        <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg>
        </div>
        <h3 className="text-xl font-bold mb-2">CoinPack Created!</h3>
        <div className="flex justify-center mb-4"><div ref={qrRef}></div></div>
        <div className="bg-black/50 rounded-lg p-3 mb-4">
          <p className="text-xs text-gray-400 mb-1">Claim Link</p>
          <p className="text-sm mono text-amber-400 break-all">{claimLink.url}</p>
        </div>
        <div className="text-left space-y-2 mb-4">
          {claimLink.assets.map((a, i) => (
            <div key={i} className="flex justify-between text-sm">
              <span className="text-gray-400">{a.type}</span>
              <span className="font-mono font-bold">{a.amount}</span>
            </div>
          ))}
          <div className="flex justify-between text-sm border-t border-white/10 pt-2">
            <span className="text-gray-400">PIN</span>
            <span className="font-mono">{claimLink.pin}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Expires</span>
            <span className="font-mono">{claimLink.expires}h</span>
          </div>
        </div>
        <button onClick={() => { setClaimLink(null); setQrData(null); }} className="px-4 py-2 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition">
          Create Another
        </button>
      </div>
    );
  }

  return (
    <div className="card rounded-xl p-6">
      <h3 className="text-lg font-bold mb-1">Create CoinPack</h3>
      <p className="text-sm text-gray-400 mb-4">Multi-asset claim link</p>
      <div className="space-y-3 mb-4">
        {assets.map((a, i) => (
          <div key={i} className="flex gap-2">
            <select value={a.type} onChange={e => updateAsset(i, 'type', e.target.value)} className="bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm w-28">
              <option>BTC</option><option>USDC</option><option>SOL</option><option>ETH</option>
            </select>
            <input
              type="number"
              placeholder="Amount"
              value={a.amount}
              onChange={e => updateAsset(i, 'amount', e.target.value)}
              className="flex-1 bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm"
            />
            {assets.length > 1 && (
              <button onClick={() => removeAsset(i)} className="px-2 text-red-400 hover:text-red-300">×</button>
            )}
          </div>
        ))}
        {assets.length < 5 && (
          <button onClick={addAsset} className="text-sm text-amber-400 hover:text-amber-300 flex items-center gap-1">
            + Add Asset
          </button>
        )}
      </div>
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label className="text-xs text-gray-400 block mb-1">PIN (min 4 digits)</label>
          <input type="password" value={pin} onChange={e => setPin(e.target.value)} maxLength={8} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm mono" placeholder="****" />
        </div>
        <div>
          <label className="text-xs text-gray-400 block mb-1">Expires (hours)</label>
          <select value={expires} onChange={e => setExpires(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm">
            <option value="1">1 hour</option>
            <option value="24">24 hours</option>
            <option value="72">3 days</option>
            <option value="168">7 days</option>
          </select>
        </div>
      </div>
      <button
        onClick={create}
        disabled={!wallet.connected}
        className="w-full py-3 btn-primary text-black font-bold rounded-xl transition disabled:opacity-50"
      >
        {wallet.connected ? 'Generate CoinPack' : 'Connect Wallet'}
      </button>
    </div>
  );
}

function ClaimCoinPack() {
  const [claimId, setClaimId] = useState('');
  const [pin, setPin] = useState('');
  const [claimed, setClaimed] = useState(null);
  const [loading, setLoading] = useState(false);
  const [riskAccepted, setRiskAccepted] = useState(false);
  const [claimable, setClaimable] = useState(null);
  const [error, setError] = useState(null);

  const handleVerify = async () => {
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/coinpacks/${claimId}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin, device_fingerprint: navigator.userAgent }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail?.message || 'Verify failed');
      setClaimable(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClaim = async () => {
    if (!riskAccepted) { alert('You must accept the risk disclosure to claim.'); return; }
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/coinpacks/${claimId}/claim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin, device_fingerprint: navigator.userAgent, accepted_risk_disclosure: true }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail?.message || 'Claim failed');
      setClaimed(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (claimed) {
    return (
      <div className="card rounded-xl p-6 text-center">
        <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg>
        </div>
        <h3 className="text-xl font-bold mb-2">Claimed!</h3>
        <div className="space-y-2 mb-4">
          {claimed.assets && claimed.assets.map((a, i) => (
            <div key={i} className="flex justify-between bg-black/50 rounded-lg p-3">
              <span className="text-gray-400">{a.type}</span>
              <span className="font-mono font-bold">{a.amount}</span>
            </div>
          ))}
        </div>
        {claimed.proof_hash && <p className="text-xs text-gray-500 mono">Proof: {shorten(claimed.proof_hash, 8)}</p>}
      </div>
    );
  }

  return (
    <div className="card rounded-xl p-6">
      <h3 className="text-lg font-bold mb-1">Claim CoinPack</h3>
      <p className="text-sm text-gray-400 mb-4">Enter your claim ID and PIN</p>
      <input
        placeholder="Claim ID (or scan QR)"
        value={claimId}
        onChange={e => setClaimId(e.target.value)}
        className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm mb-3 mono"
      />
      <input
        type="password"
        placeholder="PIN"
        value={pin}
        onChange={e => setPin(e.target.value)}
        className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm mb-4 mono"
      />

      {error && <div className="mb-3 text-sm text-red-400 bg-red-900/20 rounded-lg p-2">{error}</div>}

      {claimable && (
        <div className="mb-4 bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
          <p className="text-sm font-semibold text-amber-300 mb-1">Risk Disclosure</p>
          <p className="text-xs text-gray-300 mb-2">
            Claim links can expire. Reserve/custody risk exists. SMS/email may be intercepted.
            This is experimental software. Only use funds you can afford to lose.
          </p>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={riskAccepted} onChange={e => setRiskAccepted(e.target.checked)} />
            <span>I accept the risk disclosure</span>
          </label>
        </div>
      )}

      {!claimable ? (
        <button
          onClick={handleVerify}
          disabled={!claimId || !pin || loading}
          className="w-full py-3 btn-primary text-black font-bold rounded-xl transition disabled:opacity-50"
        >
          {loading ? 'Verifying...' : 'Verify Claim'}
        </button>
      ) : (
        <button
          onClick={handleClaim}
          disabled={!riskAccepted || loading}
          className="w-full py-3 btn-primary text-black font-bold rounded-xl transition disabled:opacity-50"
        >
          {loading ? 'Claiming...' : 'Confirm Claim'}
        </button>
      )}
    </div>
  );
}

function RedemptionModal({ note, onClose, onConfirm }) {
  const [btcAddress, setBtcAddress] = useState('');
  const [confirming, setConfirming] = useState(false);

  const confirm = () => {
    if (!btcAddress || btcAddress.length < 26) { alert('Enter a valid BTC address'); return; }
    setConfirming(true);
    setTimeout(() => { onConfirm(btcAddress); }, 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="card rounded-2xl p-6 max-w-md w-full">
        <h3 className="text-xl font-bold mb-2">Redeem Note</h3>
        <p className="text-sm text-gray-400 mb-4">Burn note #{note.serial} and receive BTC on-chain.</p>
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4 mb-4">
          <div className="text-sm text-gray-400">Amount</div>
          <div className="text-2xl font-bold gradient-text mono">{formatDenom(note.denom)}</div>
          <div className="text-sm text-gray-400">{formatUsd(note.denom)}</div>
        </div>
        <label className="text-xs text-gray-400 block mb-1">BTC Receiving Address</label>
        <input
          value={btcAddress}
          onChange={e => setBtcAddress(e.target.value)}
          placeholder="bc1q... or 1..."
          className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm mb-4 mono"
        />
        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 py-3 bg-white/10 rounded-xl font-semibold hover:bg-white/20 transition">Cancel</button>
          <button onClick={confirm} disabled={confirming} className="flex-1 py-3 bg-red-500 text-white rounded-xl font-semibold hover:bg-red-600 transition disabled:opacity-50">
            {confirming ? 'Processing...' : 'Burn & Redeem'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ============== MAIN APP ==============
function App() {
  const wallet = useWallet();
  const [tab, setTab] = useState('notes');
  const [notes, setNotes] = useState([]);
  const [redeemNote, setRedeemNote] = useState(null);
  const [vaultStats, setVaultStats] = useState({ reserved: 0, minted: 0, redeemed: 0 });

  const handleMint = (note) => {
    setNotes([note, ...notes]);
  };

  const handleRedeem = (note, btcAddress) => {
    setNotes(notes.map(n => n.serial === note.serial ? { ...n, redeemed: true, btc_address: btcAddress } : n));
    setRedeemNote(null);
  };

  return (
    <div className="min-h-screen pb-20">
      <Header wallet={wallet} />

      <main className="max-w-6xl mx-auto px-4 pt-24">
        {/* Hero Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="card rounded-xl p-4">
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">BTC Reserved</div>
            <div className="text-xl font-bold mono">{(vaultStats.reserved / 1e8).toFixed(4)} BTC</div>
          </div>
          <div className="card rounded-xl p-4">
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Notes Minted</div>
            <div className="text-xl font-bold mono">{vaultStats.minted.toLocaleString()}</div>
          </div>
          <div className="card rounded-xl p-4">
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Notes Redeemed</div>
            <div className="text-xl font-bold mono">{vaultStats.redeemed.toLocaleString()}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {[
            { id: 'notes', label: 'My Notes' },
            { id: 'mint', label: 'Mint' },
            { id: 'create', label: 'Create CoinPack' },
            { id: 'claim', label: 'Claim' },
            { id: 'reserves', label: 'Reserves' },
            { id: 'audit', label: 'Audit' },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition ${tab === t.id ? 'btn-primary text-black' : 'bg-white/5 hover:bg-white/10'}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        {tab === 'notes' && (
          <div className="space-y-4">
            {notes.filter(n => n.holder && wallet.publicKey && n.holder.includes(wallet.publicKey.slice(-6))).map(note => (
              <NoteCard
                key={note.serial}
                note={note}
                onTransfer={() => alert('Transfer initiated via QR/NFC')}
                onRedeem={() => setRedeemNote(note)}
              />
            ))}
            {notes.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <p>No notes yet. Connect your wallet and mint your first bearer note.</p>
              </div>
            )}
          </div>
        )}

        {tab === 'mint' && <MintNoteForm wallet={wallet} onMint={handleMint} />}
        {tab === 'create' && <CreateCoinPack wallet={wallet} />}
        {tab === 'claim' && <ClaimCoinPack />}
        {tab === 'reserves' && <ReserveView />}
        {tab === 'audit' && <AuditLogView />}
      </main>

      {redeemNote && (
        <RedemptionModal
          note={redeemNote}
          onClose={() => setRedeemNote(null)}
          onConfirm={(addr) => handleRedeem(redeemNote, addr)}
        />
      )}

      <RiskBanner />
      <div className="fixed bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-amber-500 to-transparent opacity-30"></div>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
