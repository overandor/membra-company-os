/* ============================================================
   MEMBRA LLM Developer — Application Controller
   ============================================================ */

const { membraAPI } = window;

const AGENT_ICONS = {
  strategy: "\u265E",
  product: "\u2630",
  engineering: "\u2328",
  reviewer: "\u2315",
  testing: "\u2714",
  devops: "\u2601",
  docs: "\u2709",
  security: "\u26E8",
  refactor: "\u267B",
  governance: "\u2696",
};

class App {
  constructor() {
    this.currentView = "chat";
    this.chatHistory = [];
    this.selectedAgents = new Set();
    this.currentFile = null;
    this.isProcessing = false;

    this.init();
  }

  async init() {
    this.bindNavigation();
    this.bindChatEvents();
    this.bindEditorEvents();
    this.bindAgentEvents();
    this.bindSettingsEvents();
    this.bindProjectEvents();
    this.bindIPCEvents();
    await this.loadAgents();
    await this.loadSettings();
  }

  /* ---- Navigation ---- */
  bindNavigation() {
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => {
        const view = btn.dataset.view;
        this.switchView(view);
      });
    });
  }

  switchView(view) {
    document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));

    const navBtn = document.querySelector(`.nav-item[data-view="${view}"]`);
    const viewEl = document.getElementById(`view-${view}`);
    if (navBtn) navBtn.classList.add("active");
    if (viewEl) viewEl.classList.add("active");
    this.currentView = view;
  }

  /* ---- IPC Events from main process ---- */
  bindIPCEvents() {
    membraAPI.on("navigate", (target) => this.switchView(target));
    membraAPI.on("action", (action) => this.handleAction(action));
    membraAPI.on("project-opened", (dirPath) => this.openProject(dirPath));
  }

  handleAction(action) {
    switch (action) {
      case "new-chat": this.resetChat(); break;
      case "generate-code":
        document.getElementById("chat-mode").value = "generate";
        this.handleModeChange();
        this.switchView("chat");
        break;
      case "review-code":
        document.getElementById("chat-mode").value = "review";
        this.handleModeChange();
        this.switchView("chat");
        break;
      case "toggle-sidebar":
        document.getElementById("sidebar").classList.toggle("collapsed");
        break;
      case "run-agents":
        this.switchView("agents");
        break;
      case "save":
        this.saveCurrentFile();
        break;
      case "new-project":
        this.openProjectDialog();
        break;
    }
  }

  /* ---- Chat ---- */
  bindChatEvents() {
    const input = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const modeSelect = document.getElementById("chat-mode");

    sendBtn.addEventListener("click", () => this.sendMessage());
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 150) + "px";
    });

    modeSelect.addEventListener("change", () => this.handleModeChange());

    document.getElementById("close-code-input").addEventListener("click", () => {
      document.getElementById("code-input-area").style.display = "none";
    });

    document.querySelectorAll(".quick-action").forEach((btn) => {
      btn.addEventListener("click", () => {
        input.value = btn.dataset.prompt;
        input.focus();
      });
    });
  }

  handleModeChange() {
    const mode = document.getElementById("chat-mode").value;
    const codeArea = document.getElementById("code-input-area");
    const errorArea = document.getElementById("error-input-area");
    const refactorArea = document.getElementById("refactor-input-area");

    const needsCode = ["review", "explain", "refactor", "debug"].includes(mode);
    codeArea.style.display = needsCode ? "block" : "none";
    errorArea.style.display = mode === "debug" ? "block" : "none";
    refactorArea.style.display = mode === "refactor" ? "block" : "none";
  }

  async sendMessage() {
    if (this.isProcessing) return;

    const input = document.getElementById("chat-input");
    const mode = document.getElementById("chat-mode").value;
    const language = document.getElementById("chat-language").value;
    const codeInput = document.getElementById("code-input");
    const errorInput = document.getElementById("error-input");
    const refactorInput = document.getElementById("refactor-input");

    const text = input.value.trim();
    if (!text && mode === "chat") return;

    const code = codeInput.value.trim();

    this.isProcessing = true;
    document.getElementById("send-btn").disabled = true;

    this.clearWelcome();
    if (text) this.appendMessage("user", text);

    const loadingEl = this.appendMessage("assistant", "Thinking...", true);

    try {
      let result;
      switch (mode) {
        case "chat":
          this.chatHistory.push({ role: "user", content: text });
          result = await membraAPI.llm.chat([
            { role: "system", content: "You are MEMBRA LLM Developer, an expert software development AI assistant. Help the user with code generation, debugging, architecture, and all aspects of software engineering." },
            ...this.chatHistory,
          ]);
          break;
        case "generate":
          result = await membraAPI.llm.generateCode(text, language, code);
          break;
        case "review":
          result = await membraAPI.llm.reviewCode(code || text, language);
          break;
        case "explain":
          result = await membraAPI.llm.explainCode(code || text, language);
          break;
        case "refactor":
          result = await membraAPI.llm.refactorCode(code || text, language, refactorInput.value || text);
          break;
        case "debug":
          result = await membraAPI.llm.debugCode(code || text, errorInput.value, language);
          break;
      }

      loadingEl.remove();

      if (result.error) {
        this.appendMessage("assistant", `Error: ${result.error}`);
      } else {
        const content = result.content || "No response received.";
        this.appendMessage("assistant", content);
        if (mode === "chat") {
          this.chatHistory.push({ role: "assistant", content });
        }
      }
    } catch (err) {
      loadingEl.remove();
      this.appendMessage("assistant", `Error: ${err.message}`);
    }

    input.value = "";
    input.style.height = "auto";
    this.isProcessing = false;
    document.getElementById("send-btn").disabled = false;
  }

  appendMessage(role, content, loading = false) {
    const container = document.getElementById("chat-messages");
    const msg = document.createElement("div");
    msg.className = `message ${role}${loading ? " loading" : ""}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "U" : "M";

    const body = document.createElement("div");
    body.className = "message-content";
    body.innerHTML = loading ? content : this.renderMarkdown(content);

    msg.appendChild(avatar);
    msg.appendChild(body);
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;

    return msg;
  }

  clearWelcome() {
    const welcome = document.querySelector(".welcome-message");
    if (welcome) welcome.remove();
  }

  resetChat() {
    this.chatHistory = [];
    const container = document.getElementById("chat-messages");
    container.innerHTML = `
      <div class="welcome-message">
        <div class="welcome-logo">M</div>
        <h3>MEMBRA LLM Software Developer</h3>
        <p>AI-powered software development with autonomous agent pipelines, code generation, review, debugging, and more.</p>
        <div class="quick-actions">
          <button class="quick-action" data-prompt="Generate a FastAPI REST endpoint with CRUD operations">Generate API</button>
          <button class="quick-action" data-prompt="Review my code for bugs and security issues">Review Code</button>
          <button class="quick-action" data-prompt="Explain this codebase architecture">Explain Code</button>
          <button class="quick-action" data-prompt="Create a CI/CD pipeline with Docker">Create Pipeline</button>
          <button class="quick-action" data-prompt="Build a React component with TypeScript">Build Component</button>
          <button class="quick-action" data-prompt="Write unit tests for this module">Write Tests</button>
        </div>
      </div>`;

    document.querySelectorAll(".quick-action").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.getElementById("chat-input").value = btn.dataset.prompt;
        document.getElementById("chat-input").focus();
      });
    });
  }

  renderMarkdown(text) {
    let html = this.escapeHtml(text);

    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_match, lang, code) => {
      return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    });

    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
    html = html.replace(/^### (.+)$/gm, "<h4>$1</h4>");
    html = html.replace(/^## (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^# (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>");
    html = html.replace(/^\d+\. (.+)$/gm, "<li>$1</li>");
    html = html.replace(/\n\n/g, "<br><br>");

    return html;
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  /* ---- Code Editor ---- */
  bindEditorEvents() {
    document.getElementById("editor-save-btn").addEventListener("click", () => this.saveCurrentFile());
    document.getElementById("btn-review-editor").addEventListener("click", () => this.editorAction("review"));
    document.getElementById("btn-explain-editor").addEventListener("click", () => this.editorAction("explain"));
    document.getElementById("btn-refactor-editor").addEventListener("click", () => this.editorAction("refactor"));
    document.getElementById("btn-debug-editor").addEventListener("click", () => this.editorAction("debug"));
    document.getElementById("btn-generate-editor").addEventListener("click", () => this.editorAction("generate"));
  }

  async editorAction(action) {
    const code = document.getElementById("code-editor").value;
    if (!code.trim()) return;

    this.switchView("chat");
    document.getElementById("chat-mode").value = action;
    document.getElementById("chat-language").value = this.currentFile
      ? this.detectLanguage(this.currentFile)
      : "javascript";
    this.handleModeChange();

    if (["review", "explain", "refactor", "debug"].includes(action)) {
      document.getElementById("code-input").value = code;
      document.getElementById("code-input-area").style.display = "block";
    }

    document.getElementById("chat-input").value =
      action === "generate" ? "Generate code based on the editor content" : `${action} the code from the editor`;
    document.getElementById("chat-input").focus();
  }

  async saveCurrentFile() {
    if (!this.currentFile) return;
    const content = document.getElementById("code-editor").value;
    await membraAPI.project.writeFile(this.currentFile, content);
  }

  async openFileInEditor(filePath) {
    const result = await membraAPI.project.readFile(filePath);
    if (result.error) return;

    this.currentFile = filePath;
    document.getElementById("code-editor").value = result.content;
    document.getElementById("editor-filename").textContent = filePath.split("/").pop();
    this.switchView("code");
  }

  detectLanguage(filePath) {
    const ext = filePath.split(".").pop().toLowerCase();
    const map = {
      js: "javascript", ts: "typescript", py: "python", rs: "rust",
      go: "go", rb: "ruby", java: "java", cpp: "cpp", c: "c",
      sol: "solidity", sh: "bash", sql: "sql",
    };
    return map[ext] || "plaintext";
  }

  /* ---- Agents ---- */
  bindAgentEvents() {
    document.getElementById("run-pipeline-btn").addEventListener("click", () => this.runAgentPipeline());
  }

  async loadAgents() {
    const agents = await membraAPI.agents.list();
    const grid = document.getElementById("agents-grid");
    grid.innerHTML = "";

    agents.forEach((agent) => {
      const card = document.createElement("div");
      card.className = "agent-card";
      card.dataset.agentId = agent.id;

      card.innerHTML = `
        <div class="agent-icon">${AGENT_ICONS[agent.id] || "\u2699"}</div>
        <div class="agent-name">${agent.name}</div>
        <div class="agent-role">${agent.role}</div>
        <div class="agent-check"></div>
      `;

      card.addEventListener("click", () => {
        card.classList.toggle("selected");
        if (card.classList.contains("selected")) {
          this.selectedAgents.add(agent.id);
          card.querySelector(".agent-check").textContent = "\u2713";
        } else {
          this.selectedAgents.delete(agent.id);
          card.querySelector(".agent-check").textContent = "";
        }
      });

      grid.appendChild(card);
    });
  }

  async runAgentPipeline() {
    const task = document.getElementById("pipeline-task").value.trim();
    if (!task) return;

    const btn = document.getElementById("run-pipeline-btn");
    btn.disabled = true;
    btn.textContent = "Running...";

    const outputEl = document.getElementById("pipeline-output");
    const stepsEl = document.getElementById("pipeline-steps");
    outputEl.style.display = "block";
    stepsEl.innerHTML = '<div class="pipeline-step"><div class="pipeline-step-output">Running agent pipeline...</div></div>';

    try {
      const agentIds = this.selectedAgents.size > 0 ? [...this.selectedAgents] : null;
      const result = await membraAPI.agents.runPipeline(task, agentIds);

      stepsEl.innerHTML = "";
      result.steps.forEach((step) => {
        const stepEl = document.createElement("div");
        stepEl.className = "pipeline-step";
        stepEl.innerHTML = `
          <div class="pipeline-step-header">
            <span class="pipeline-step-name">${AGENT_ICONS[step.agentId] || ""} ${step.agentName}</span>
            <span class="pipeline-step-time">${step.durationMs}ms</span>
          </div>
          <div class="pipeline-step-output">${step.error ? `ERROR: ${step.error}` : this.renderMarkdown(step.output || "No output")}</div>
        `;
        stepsEl.appendChild(stepEl);
      });

      const summary = document.createElement("div");
      summary.className = "pipeline-step";
      summary.innerHTML = `
        <div class="pipeline-step-header">
          <span class="pipeline-step-name">Pipeline ${result.status}</span>
          <span class="pipeline-step-time">${result.durationMs}ms total</span>
        </div>
      `;
      stepsEl.appendChild(summary);
    } catch (err) {
      stepsEl.innerHTML = `<div class="pipeline-step"><div class="pipeline-step-output">Error: ${err.message}</div></div>`;
    }

    btn.disabled = false;
    btn.textContent = "Run Pipeline";
  }

  /* ---- Settings ---- */
  bindSettingsEvents() {
    const providerSelect = document.getElementById("setting-provider");
    const tempRange = document.getElementById("setting-temperature");

    providerSelect.addEventListener("change", () => {
      document.getElementById("ollama-settings").style.display =
        providerSelect.value === "ollama" ? "block" : "none";
    });

    tempRange.addEventListener("input", () => {
      document.getElementById("temp-value").textContent = tempRange.value;
    });

    document.getElementById("save-settings-btn").addEventListener("click", () => this.saveSettings());
  }

  async loadSettings() {
    const config = await membraAPI.llm.getConfig();
    document.getElementById("setting-provider").value = config.provider || "groq";
    document.getElementById("setting-model").value = config.model || "";
    document.getElementById("setting-temperature").value = config.temperature || 0.3;
    document.getElementById("temp-value").textContent = config.temperature || 0.3;
    document.getElementById("setting-max-tokens").value = config.maxTokens || 4096;
    document.getElementById("setting-ollama-url").value = config.ollamaUrl || "http://localhost:11434";
    document.getElementById("setting-ollama-model").value = config.ollamaModel || "codellama";

    document.getElementById("ollama-settings").style.display =
      config.provider === "ollama" ? "block" : "none";
  }

  async saveSettings() {
    const config = {
      provider: document.getElementById("setting-provider").value,
      apiKey: document.getElementById("setting-api-key").value || undefined,
      model: document.getElementById("setting-model").value || undefined,
      temperature: parseFloat(document.getElementById("setting-temperature").value),
      maxTokens: parseInt(document.getElementById("setting-max-tokens").value, 10),
      ollamaUrl: document.getElementById("setting-ollama-url").value,
      ollamaModel: document.getElementById("setting-ollama-model").value,
    };

    await membraAPI.llm.setConfig(config);
    const btn = document.getElementById("save-settings-btn");
    btn.textContent = "Saved!";
    setTimeout(() => { btn.textContent = "Save Settings"; }, 1500);
  }

  /* ---- Project ---- */
  bindProjectEvents() {
    document.getElementById("open-project-btn").addEventListener("click", () => this.openProjectDialog());
  }

  async openProjectDialog() {
    const input = document.getElementById("chat-input");
    input.placeholder = "Enter project directory path and press Enter...";
    input.focus();
  }

  async openProject(dirPath) {
    const result = await membraAPI.project.open(dirPath);
    if (result.error) return;

    document.getElementById("project-tree-container").style.display = "block";
    this.renderTree(result.tree, document.getElementById("project-tree"), 0);

    const infoEl = document.getElementById("project-info");
    infoEl.innerHTML = `
      <p><strong>Project:</strong> ${dirPath}</p>
      <p><strong>Type:</strong> ${result.info.type} | <strong>Languages:</strong> ${result.info.languages.join(", ") || "unknown"}</p>
      ${result.info.frameworks.length ? `<p><strong>Frameworks:</strong> ${result.info.frameworks.join(", ")}</p>` : ""}
    `;

    this.renderTree(result.tree, document.getElementById("project-tree-full"), 0);
  }

  renderTree(nodes, container, depth) {
    if (!nodes) return;
    container.innerHTML = "";

    nodes.forEach((node) => {
      const item = document.createElement("div");
      item.className = `tree-item ${node.type}`;
      item.style.paddingLeft = `${depth * 16 + 8}px`;

      const icon = node.type === "directory" ? "\u{1F4C1}" : "\u{1F4C4}";
      item.textContent = `${icon} ${node.name}`;

      if (node.type === "file") {
        item.addEventListener("click", () => this.openFileInEditor(node.path));
      } else if (node.children) {
        const childContainer = document.createElement("div");
        childContainer.className = "tree-children";
        this.renderTree(node.children, childContainer, depth + 1);

        item.addEventListener("click", () => {
          childContainer.style.display = childContainer.style.display === "none" ? "block" : "none";
        });

        container.appendChild(item);
        container.appendChild(childContainer);
        return;
      }

      container.appendChild(item);
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.app = new App();
});
