// MEMBRA CompanyOS — Dashboard Frontend
function resolveApiBase() {
  const meta = document.querySelector('meta[name="membra-api-base"]');
  if (meta?.content) {
    return meta.content.replace(/\/$/, '');
  }
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000/v1';
  }
  return '/v1';
}
const API_BASE = resolveApiBase();

const TABS = {
  orchestration: renderOrchestration,
  agents: renderAgents,
  tasks: renderTasks,
  jobs: renderJobs,
  company: renderCompany,
  governance: renderGovernance,
  proofbook: renderProofBook,
  worldbridge: renderWorldBridge,
  concierge: renderConcierge,
  workforce: renderWorkforce,
};

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  loadTab('orchestration');
});

function initTabs() {
  document.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      loadTab(btn.dataset.tab);
    });
  });
}

function loadTab(name) {
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">Loading ' + name + '...</div>';
  if (TABS[name]) TABS[name](content);
}

// ===== ORCHESTRATION TAB =====
function renderOrchestration(container) {
  container.innerHTML = `
    <div class="grid">
      <div class="card wide">
        <h3>Orchestrate Intent</h3>
        <div class="chat-input-row">
          <input type="text" id="intentInput" class="chat-input" placeholder="I have a window, a car, two hours free, a drill...">
          <button class="chat-send" onclick="submitIntent()">Orchestrate</button>
        </div>
        <div id="intentResult" style="margin-top:16px;"></div>
      </div>
      <div class="card">
        <div class="label">Pipeline</div>
        <div class="value">Intent → Objective → Task → Agent → Job → Proof → Governance → Settlement</div>
      </div>
      <div class="card">
        <div class="label">Active Orchestrations</div>
        <div class="value gold" id="orchCount">--</div>
      </div>
    </div>
  `;
  loadStats();
}

async function submitIntent() {
  const input = document.getElementById('intentInput');
  const result = document.getElementById('intentResult');
  const text = input.value.trim();
  if (!text) return;
  result.innerHTML = '<div class="loading">Orchestrating...</div>';
  try {
    const res = await fetch(`${API_BASE}/orchestrate/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ intent_text: text }),
    });
    const data = await res.json();
    const r = data.data || {};
    result.innerHTML = formatOrchestration(r, text);
    loadStats();
  } catch (e) {
    result.innerHTML = `<div class="terminal"><div class="cmd">Error:</div>${e.message}</div>`;
  }
}

function formatOrchestration(r, text) {
  const objectives = (r.objectives || []).map(o => `<li>${o.title}</li>`).join('') || '<li>None</li>';
  const tasks = (r.tasks || []).map(t => `<li>${t.title} <span class="badge badge-${t.status === 'completed' ? 'active' : 'pending'}">${t.status}</span></li>`).join('') || '<li>None</li>';
  const jobs = (r.jobs || []).map(j => `<li>${j.title} <span class="badge badge-pending">${j.type}</span></li>`).join('') || '<li>None</li>';
  const gates = (r.gates || []).map(g => `<li>${g.type} <span class="badge badge-${g.status === 'approved' ? 'active' : 'pending'}">${g.status}</span></li>`).join('') || '<li>None</li>';
  return `
<div class="terminal">
  <div class="cmd">> orchestrate("${escapeHtml(text.slice(0,60))}...")</div>
  <div style="margin-top:8px;"><b>Intent ID:</b> ${r.intent_id || '--'}</div>
  <div><b>Proof Hash:</b> <code>${r.proof_hash ? r.proof_hash.slice(0,24)+'...' : '--'}</code></div>
  <div style="margin-top:12px;"><b>Objectives (${r.objectives?.length || 0})</b></div>
  <ul>${objectives}</ul>
  <div style="margin-top:8px;"><b>Tasks (${r.tasks?.length || 0})</b></div>
  <ul>${tasks}</ul>
  <div style="margin-top:8px;"><b>Jobs (${r.jobs?.length || 0})</b></div>
  <ul>${jobs}</ul>
  <div style="margin-top:8px;"><b>Governance Gates (${r.gates?.length || 0})</b></div>
  <ul>${gates}</ul>
  <div class="disclaimer">AI recommendation only. Human confirmation required for real-world execution.</div>
</div>`;
}

// ===== AGENTS TAB =====
async function renderAgents(container) {
  container.innerHTML = '<div class="loading">Loading agents...</div>';
  try {
    const res = await fetch(`${API_BASE}/agents/?limit=50`);
    const data = await res.json();
    const items = data.items || [];
    container.innerHTML = `
      <div class="card wide">
        <h3>Agent Registry (${items.length})</h3>
        <table class="data-table">
          <thead><tr><th>Type</th><th>Name</th><th>Status</th><th>Executions</th><th>Success</th><th>LLM</th></tr></thead>
          <tbody>
            ${items.map(a => `<tr>
              <td><span class="badge badge-pending">${a.agent_type}</span></td>
              <td>${a.name}</td>
              <td><span class="badge badge-active">${a.status}</span></td>
              <td>${a.execution_count}</td>
              <td>${a.success_count}</td>
              <td>${a.llm_provider || '--'}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<div class="card">Error loading agents: ${e.message}</div>`;
  }
}

// ===== TASKS TAB =====
async function renderTasks(container) {
  container.innerHTML = '<div class="loading">Loading tasks...</div>';
  try {
    const res = await fetch(`${API_BASE}/tasks/?limit=50`);
    const data = await res.json();
    const items = data.items || [];
    container.innerHTML = `
      <div class="card wide">
        <h3>Task Board (${items.length})</h3>
        <table class="data-table">
          <thead><tr><th>Title</th><th>Type</th><th>Status</th><th>Priority</th><th>Deadline</th></tr></thead>
          <tbody>
            ${items.map(t => `<tr>
              <td>${t.title}</td>
              <td><span class="badge badge-pending">${t.task_type}</span></td>
              <td><span class="badge badge-${t.status === 'completed' ? 'active' : t.status === 'blocked' ? 'rejected' : 'pending'}">${t.status}</span></td>
              <td>${t.priority}</td>
              <td>${t.deadline ? new Date(t.deadline).toLocaleDateString() : '--'}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<div class="card">Error loading tasks: ${e.message}</div>`;
  }
}

// ===== JOBS TAB =====
async function renderJobs(container) {
  container.innerHTML = '<div class="loading">Loading jobs...</div>';
  try {
    const res = await fetch(`${API_BASE}/jobs/?limit=50`);
    const data = await res.json();
    const items = data.items || [];
    container.innerHTML = `
      <div class="card wide">
        <h3>Job Marketplace (${items.length})</h3>
        <table class="data-table">
          <thead><tr><th>Title</th><th>Type</th><th>Status</th><th>Budget</th><th>Payout Eligible</th></tr></thead>
          <tbody>
            ${items.map(j => `<tr>
              <td>${j.title}</td>
              <td><span class="badge badge-pending">${j.job_type}</span></td>
              <td><span class="badge badge-${j.status === 'completed' ? 'active' : j.status === 'cancelled' ? 'rejected' : 'pending'}">${j.status}</span></td>
              <td>${j.budget ? j.budget + ' ' + j.currency : '--'}</td>
              <td>${j.payout_eligible ? 'Yes' : 'No'}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<div class="card">Error loading jobs: ${e.message}</div>`;
  }
}

// ===== COMPANY TAB =====
async function renderCompany(container) {
  container.innerHTML = `
    <div class="grid">
      <div class="card">
        <div class="label">Companies</div>
        <div class="value gold" id="compCount">--</div>
      </div>
      <div class="card">
        <div class="label">Departments</div>
        <div class="value" id="deptCount">--</div>
      </div>
      <div class="card">
        <div class="label">Initiatives</div>
        <div class="value" id="initCount">--</div>
      </div>
      <div class="card">
        <div class="label">KPI Records</div>
        <div class="value accent" id="kpiCount">--</div>
      </div>
      <div class="card wide">
        <button class="chat-send" onclick="seedDemoData()">Seed Default Agents &amp; Data</button>
        <div id="seedResult" style="margin-top:8px;"></div>
      </div>
    </div>
  `;
  loadStats();
}

async function seedDemoData() {
  const result = document.getElementById('seedResult');
  result.innerHTML = '<div class="loading">Seeding...</div>';
  try {
    const res = await fetch(`${API_BASE}/agents/registry/seed`, { method: 'POST' });
    const data = await res.json();
    result.innerHTML = `<div class="terminal">Seeded ${data.data?.created || 0} agents. Skipped ${data.data?.skipped || 0}.</div>`;
    loadStats();
  } catch (e) {
    result.innerHTML = `<div class="terminal">Error: ${e.message}</div>`;
  }
}

// ===== GOVERNANCE TAB =====
async function renderGovernance(container) {
  container.innerHTML = '<div class="loading">Loading governance...</div>';
  try {
    const res = await fetch(`${API_BASE}/governance/approval-gates?limit=50`);
    const data = await res.json();
    const items = data.items || [];
    container.innerHTML = `
      <div class="card wide">
        <h3>Approval Gates (${items.length})</h3>
        <table class="data-table">
          <thead><tr><th>Type</th><th>Resource</th><th>Status</th><th>Risk</th><th>Approvals</th></tr></thead>
          <tbody>
            ${items.map(g => `<tr>
              <td>${g.type}</td>
              <td>${g.resource_type}</td>
              <td><span class="badge badge-${g.status === 'approved' ? 'active' : g.status === 'rejected' ? 'rejected' : 'pending'}">${g.status}</span></td>
              <td>${g.risk_level || 'low'}</td>
              <td>${g.current_approvals || 0}/${g.required_approvals || 1}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<div class="card">Error loading governance: ${e.message}</div>`;
  }
}

// ===== PROOFBOOK TAB =====
async function renderProofBook(container) {
  container.innerHTML = '<div class="loading">Loading proofbook...</div>';
  try {
    const res = await fetch(`${API_BASE}/proofbook/entries?limit=50`);
    const data = await res.json();
    const items = data.items || [];
    container.innerHTML = `
      <div class="card wide">
        <h3>ProofBook Entries (${items.length})</h3>
        <table class="data-table">
          <thead><tr><th>Type</th><th>Resource</th><th>Actor</th><th>Hash</th><th>Time</th></tr></thead>
          <tbody>
            ${items.map(e => `<tr>
              <td><span class="badge badge-pending">${e.type}</span></td>
              <td>${e.resource_type}</td>
              <td>${e.actor_type}</td>
              <td><code>${e.hash ? e.hash.slice(0,16)+'...' : '--'}</code></td>
              <td>${new Date(e.created_at).toLocaleString()}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<div class="card">Error loading proofbook: ${e.message}</div>`;
  }
}

// ===== WORLDBRIDGE TAB =====
async function renderWorldBridge(container) {
  container.innerHTML = '<div class="loading">Loading worldbridge...</div>';
  try {
    const res = await fetch(`${API_BASE}/worldbridge/assets?limit=50`);
    const data = await res.json();
    const items = data.items || [];
    container.innerHTML = `
      <div class="card wide">
        <h3>World Assets (${items.length})</h3>
        <table class="data-table">
          <thead><tr><th>Name</th><th>Type</th><th>Status</th><th>Owner</th><th>Listings</th></tr></thead>
          <tbody>
            ${items.map(a => `<tr>
              <td>${a.name}</td>
              <td><span class="badge badge-pending">${a.asset_type}</span></td>
              <td><span class="badge badge-${a.status === 'available' ? 'active' : 'pending'}">${a.status}</span></td>
              <td><code>${a.owner_wallet ? a.owner_wallet.slice(0,8)+'...' : '--'}</code></td>
              <td>${a.listings ? a.listings.length : 0}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<div class="card">Error loading worldbridge: ${e.message}</div>`;
  }
}

// ===== CONCIERGE TAB =====
function renderConcierge(container) {
  container.innerHTML = `
    <div class="grid">
      <div class="card wide">
        <h3>LLM Concierge</h3>
        <div class="chat-container">
          <div class="chat-messages" id="chatMessages">
            <div class="chat-bubble ai">
              Welcome to MEMBRA CompanyOS. I am the Concierge.
              <br><br>
              Tell me what you have (window, car, tool, time, skills) and what you want to turn it into.
              <div class="disclaimer">
                <b>Production Boundaries:</b><br>
                MEMBRA does not guarantee income.<br>
                MEMBRA does not custody funds.<br>
                Settlement happens through external rails.<br>
                Owner confirmation is required before marketplace visibility.<br>
                Governance approval is required for high-risk actions.<br>
                AI agents recommend and prepare; they do not bypass human/policy gates.
              </div>
            </div>
          </div>
          <div class="chat-input-row">
            <input type="text" id="chatInput" class="chat-input" placeholder="Describe your intent...">
            <button class="chat-send" onclick="sendChat()">Send</button>
          </div>
        </div>
      </div>
    </div>
  `;
  document.getElementById('chatInput').addEventListener('keypress', e => { if (e.key === 'Enter') sendChat(); });
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const messages = document.getElementById('chatMessages');
  const text = input.value.trim();
  if (!text) return;

  messages.innerHTML += `<div class="chat-bubble user">${escapeHtml(text)}</div>`;
  input.value = '';
  messages.scrollTop = messages.scrollHeight;

  const loadingId = 'loading-' + Date.now();
  messages.innerHTML += `<div class="chat-bubble ai" id="${loadingId}"><div class="loading">Thinking...</div></div>`;
  messages.scrollTop = messages.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/concierge/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    const reply = data.data?.reply || 'No response from Concierge.';
    const provider = data.data?.provider || 'unknown';
    const actions = data.data?.actions_taken?.join(', ') || 'none';
    document.getElementById(loadingId).innerHTML = `
      ${escapeHtml(reply)}
      <div class="disclaimer">Provider: ${provider} | Actions: ${actions}</div>
    `;
  } catch (e) {
    document.getElementById(loadingId).innerHTML = `<div class="terminal"><div class="cmd">Error:</div>${e.message}<div class="disclaimer">No LLM provider configured? Set GROQ_API_KEY or OPENAI_API_KEY.</div></div>`;
  }
  messages.scrollTop = messages.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function loadStats() {
  try {
    const health = await fetch(`${API_BASE}/health/`).then(r => r.json());
    document.querySelectorAll('.status-pill').forEach(el => el.textContent = `SYSTEM: ${health.status.toUpperCase()}`);
  } catch (e) {
    console.error('Health check failed', e);
  }
  try {
    const dash = await fetch(`${API_BASE}/dashboard/`).then(r => r.json());
    const counts = dash.data?.counts || {};
    document.getElementById('orchCount').textContent = counts.intents || 0;
    const compCount = document.getElementById('compCount');
    if (compCount) compCount.textContent = counts.companies || 0;
    const deptCount = document.getElementById('deptCount');
    if (deptCount) deptCount.textContent = '--';
    const initCount = document.getElementById('initCount');
    if (initCount) initCount.textContent = '--';
    const kpiCount = document.getElementById('kpiCount');
    if (kpiCount) kpiCount.textContent = '--';
    const wfCount = document.getElementById('wfCount');
    if (wfCount) wfCount.textContent = counts.workforce_employees || 0;
  } catch (e) {
    console.error('Dashboard load failed', e);
  }
}

// ===== WORKFORCE TAB =====
async function renderWorkforce(container) {
  container.innerHTML = `
    <div class="grid">
      <div class="card"><div class="label">Workforce Size</div><div class="value gold" id="wfCount">--</div></div>
      <div class="card"><div class="label">Running</div><div class="value" id="wfRunning">--</div></div>
      <div class="card"><div class="label">Contributions</div><div class="value accent" id="wfContrib">--</div></div>
      <div class="card"><div class="label">Departments</div><div class="value">12</div></div>
      <div class="card wide">
        <button class="chat-send" onclick="seedWorkforce()">Seed 60-Employee Workforce</button>
        <button class="chat-send" onclick="runAllWorkforce()">Run All Employees</button>
        <div id="wfSeedResult" style="margin-top:8px;"></div>
      </div>
    </div>
    <div id="wfDepartments"></div>
    <div id="wfEmployees" style="margin-top:16px;"></div>
  `;
  await loadWorkforceStats();
  await loadDepartments();
  await loadWorkforceEmployees();
}

async function loadWorkforceStats() {
  try {
    const res = await fetch(`${API_BASE}/workforce/stats`);
    const data = await res.json();
    const s = data;
    const wfCount = document.getElementById('wfCount');
    if (wfCount) wfCount.textContent = s.total_employees || 0;
    const wfRunning = document.getElementById('wfRunning');
    if (wfRunning) wfRunning.textContent = s.running || 0;
    const wfContrib = document.getElementById('wfContrib');
    if (wfContrib) wfContrib.textContent = s.total_contributions || 0;
  } catch (e) {
    console.error('Workforce stats failed', e);
  }
}

async function seedWorkforce() {
  const result = document.getElementById('wfSeedResult');
  result.innerHTML = '<div class="loading">Seeding workforce...</div>';
  try {
    const res = await fetch(`${API_BASE}/workforce/seed`, { method: 'POST' });
    const data = await res.json();
    result.innerHTML = `<div class="terminal">Seeded ${data.data?.created || 0} employees. Skipped ${data.data?.skipped || 0}.</div>`;
    await loadWorkforceStats();
    await loadWorkforceEmployees();
  } catch (e) {
    result.innerHTML = `<div class="terminal">Error: ${e.message}</div>`;
  }
}

async function runAllWorkforce() {
  const result = document.getElementById('wfSeedResult');
  result.innerHTML = '<div class="loading">Triggering all 60 employees via Ollama...</div>';
  try {
    const listRes = await fetch(`${API_BASE}/workforce/employees?limit=200`);
    const listData = await listRes.json();
    const employees = listData || [];
    let completed = 0;
    for (const emp of employees) {
      try {
        await fetch(`${API_BASE}/workforce/employees/${emp.employee_id}/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
        completed++;
      } catch (e) {
        console.error('Failed to run ' + emp.employee_id + ':', e);
      }
    }
    result.innerHTML = `<div class="terminal">Triggered ${completed}/${employees.length} employees. Check contributions below.</div>`;
    await loadWorkforceStats();
    await loadWorkforceEmployees();
  } catch (e) {
    result.innerHTML = `<div class="terminal">Error: ${e.message}</div>`;
  }
}

async function loadDepartments() {
  const container = document.getElementById('wfDepartments');
  if (!container) return;
  try {
    const res = await fetch(`${API_BASE}/workforce/departments`);
    const data = await res.json();
    const depts = data || [];
    container.innerHTML = '<div class="grid" style="margin-top:16px;">' + depts.map(d => `
      <div class="card">
        <div class="label">${escapeHtml(d.name)}</div>
        <div class="value">${d.employee_count || 0} employees</div>
        <div class="disclaimer">${escapeHtml(d.mission || '')}</div>
      </div>
    `).join('') + '</div>';
  } catch (e) {
    container.innerHTML = `<div class="terminal">Error: ${e.message}</div>`;
  }
}

async function loadWorkforceEmployees() {
  const container = document.getElementById('wfEmployees');
  if (!container) return;
  try {
    const res = await fetch(`${API_BASE}/workforce/employees?limit=200`);
    const data = await res.json();
    const employees = data || [];
    container.innerHTML = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;">' + employees.map(e => `
      <div class="card" style="flex:1 1 280px;min-width:260px;">
        <div style="font-weight:700;color:#fbbf24;">${escapeHtml(e.name)}</div>
        <div class="label">${escapeHtml(e.title)} | ${escapeHtml(e.department)}</div>
        <div class="disclaimer">Status: <strong>${e.status}</strong> | Runs: ${e.total_runs} | Contributions: ${e.total_contributions}</div>
        <div class="disclaimer">Model: ${e.model}</div>
        <div class="disclaimer">Resp: ${(e.responsibilities || []).slice(0,2).join(', ')}${(e.responsibilities || []).length > 2 ? '...' : ''}</div>
        <button class="chat-send" style="margin-top:8px;" onclick="runEmployee('${e.employee_id}')">Run Employee</button>
        ${e.last_error ? `<div class="terminal" style="margin-top:6px;">Last error: ${escapeHtml(e.last_error.substring(0,120))}</div>` : ''}
        ${e.last_output ? `<div class="disclaimer" style="margin-top:6px;">Last output: ${escapeHtml(e.last_output.substring(0,120))}...</div>` : ''}
      </div>
    `).join('') + '</div>';
  } catch (e) {
    container.innerHTML = `<div class="terminal">Error: ${e.message}</div>`;
  }
}

async function runEmployee(employeeId) {
  try {
    await fetch(`${API_BASE}/workforce/employees/${employeeId}/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
    await loadWorkforceStats();
    await loadWorkforceEmployees();
  } catch (e) {
    alert('Error running employee: ' + e.message);
  }
}
