/**
 * MEMBRA L3 — JavaScript Frontend
 * Real-time dashboard showing proof-of-proof consensus,
 * transaction flow, and earnings from LLM inference.
 */

const WS_URL = 'ws://localhost:42425';
let ws = null;
let reconnectInterval = 1000;
let stats = {
    totalTx: 0,
    totalTokens: 0,
    totalValue: 0,
    finalizedBatches: 0,
    peers: 0,
    consensusRounds: 0,
};

function initDashboard() {
    const app = document.getElementById('app');
    if (!app) {
        console.error('App container not found');
        return;
    }

    app.innerHTML = `
        <header>
            <h1>MEMBRA L3</h1>
            <div class="status" id="connection-status">Connecting...</div>
        </header>
        <div class="grid">
            <div class="card" id="throughput-card">
                <h2>Throughput</h2>
                <div class="big-number" id="tps-display">0</div>
                <div class="label">tx/sec</div>
            </div>
            <div class="card" id="tokens-card">
                <h2>Tokens Generated</h2>
                <div class="big-number" id="tokens-display">0</div>
                <div class="label">inference tokens</div>
            </div>
            <div class="card" id="value-card">
                <h2>Value Minted</h2>
                <div class="big-number" id="value-display">0</div>
                <div class="label">base units</div>
            </div>
            <div class="card" id="consensus-card">
                <h2>Consensus</h2>
                <div class="metric-row">
                    <span class="label">Rounds:</span>
                    <span class="value" id="rounds-display">0</span>
                </div>
                <div class="metric-row">
                    <span class="label">Batches:</span>
                    <span class="value" id="batches-display">0</span>
                </div>
                <div class="metric-row">
                    <span class="label">Peers:</span>
                    <span class="value" id="peers-display">0</span>
                </div>
            </div>
            <div class="card wide" id="prompt-card">
                <h2>Submit Prompt</h2>
                <textarea id="prompt-input" placeholder="Enter prompt... Each word becomes a transaction. Each token earns money."></textarea>
                <button id="submit-btn" onclick="submitPrompt()">Submit & Earn</button>
                <div id="prompt-result"></div>
            </div>
            <div class="card wide" id="log-card">
                <h2>Live Transactions</h2>
                <div id="tx-log"></div>
            </div>
        </div>
    `;

    connectWebSocket();
    startThroughputCounter();
}

function connectWebSocket() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        console.log('Connected to Membra L3 runtime');
        document.getElementById('connection-status').textContent = '● LIVE';
        document.getElementById('connection-status').classList.add('live');
        reconnectInterval = 1000;
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleRuntimeMessage(data);
        } catch (e) {
            console.log('Raw:', event.data);
        }
    };

    ws.onclose = () => {
        document.getElementById('connection-status').textContent = '● DISCONNECTED';
        document.getElementById('connection-status').classList.remove('live');
        setTimeout(connectWebSocket, reconnectInterval);
        reconnectInterval = Math.min(reconnectInterval * 2, 30000);
    };

    ws.onerror = (err) => {
        console.error('WebSocket error:', err);
    };
}

function handleRuntimeMessage(data) {
    if (data.msg_type === 'tx_batch') {
        const txs = data.payload || [];
        stats.totalTx += txs.length;
        
        txs.forEach(tx => {
            if (tx.tx_type === 'Inference') {
                stats.totalTokens++;
                stats.totalValue += tx.amount || 0;
            }
            logTransaction(tx);
        });
        
        updateDisplays();
    }
    
    if (data.msg_type === 'consensus_proof') {
        stats.consensusRounds++;
        updateDisplays();
    }
    
    if (data.msg_type === 'gossip') {
        const payload = data.payload || {};
        if (payload.peers !== undefined) {
            stats.peers = payload.peers;
        }
        updateDisplays();
    }
}

function logTransaction(tx) {
    const log = document.getElementById('tx-log');
    if (!log) return;
    
    const entry = document.createElement('div');
    entry.className = 'tx-entry';
    const typeColor = {
        'Prompt': '#ffaa00',
        'Inference': '#00ff88',
        'Response': '#0088ff',
        'ConsensusVote': '#ff00ff',
    }[tx.tx_type] || '#888';
    
    entry.innerHTML = `
        <span class="tx-type" style="color:${typeColor}">${tx.tx_type}</span>
        <span class="tx-hash">${tx.tx_hash?.substring(0, 16) || '...'}...</span>
        <span class="tx-amount">${tx.amount || 0}</span>
    `;
    
    log.insertBefore(entry, log.firstChild);
    if (log.children.length > 50) {
        log.removeChild(log.lastChild);
    }
}

function updateDisplays() {
    document.getElementById('tokens-display').textContent = stats.totalTokens.toLocaleString();
    document.getElementById('value-display').textContent = stats.totalValue.toLocaleString();
    document.getElementById('rounds-display').textContent = stats.consensusRounds.toLocaleString();
    document.getElementById('batches-display').textContent = stats.finalizedBatches.toLocaleString();
    document.getElementById('peers-display').textContent = stats.peers.toLocaleString();
}

let lastTxCount = 0;
let tps = 0;

function startThroughputCounter() {
    setInterval(() => {
        const current = stats.totalTx;
        tps = current - lastTxCount;
        lastTxCount = current;
        const el = document.getElementById('tps-display');
        if (el) el.textContent = tps.toLocaleString();
    }, 1000);
}

async function submitPrompt() {
    const input = document.getElementById('prompt-input');
    const result = document.getElementById('prompt-result');
    const btn = document.getElementById('submit-btn');
    
    const prompt = input.value.trim();
    if (!prompt) return;
    
    btn.disabled = true;
    btn.textContent = 'Processing...';
    
    try {
        // Send to runtime via WebSocket
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                msg_type: 'prompt',
                sender: 'web-user',
                payload: { prompt, model: 'llama3.2' },
                timestamp: Date.now(),
            }));
        }
        
        // Also try HTTP API fallback
        const response = await fetch('http://localhost:8080/api/prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, user: 'web-user' }),
        });
        
        const data = await response.json();
        result.innerHTML = `
            <div class="success">
                <strong>Response:</strong> ${data.response?.substring(0, 200) || 'Processing...'}<br>
                <strong>Tokens:</strong> ${data.tokens || 0} | 
                <strong>Earned:</strong> ${data.value_minted || 0} units
            </div>
        `;
    } catch (e) {
        result.innerHTML = `<div class="error">Error: ${e.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Submit & Earn';
        input.value = '';
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initDashboard);
