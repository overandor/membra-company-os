const crypto = require("crypto");

const AGENT_REGISTRY = [
  {
    id: "strategy",
    name: "Strategy Agent",
    role: "Decides what to build next based on project goals and market analysis",
    icon: "chess-knight",
    capabilities: ["project-planning", "prioritization", "roadmap-generation"],
  },
  {
    id: "product",
    name: "Product Agent",
    role: "Converts strategy into product requirements, user stories, and specs",
    icon: "clipboard-list",
    capabilities: ["requirements-analysis", "user-stories", "spec-generation"],
  },
  {
    id: "engineering",
    name: "Engineering Agent",
    role: "Builds software: generates code, APIs, services, and infrastructure",
    icon: "code",
    capabilities: ["code-generation", "api-design", "architecture", "testing"],
  },
  {
    id: "reviewer",
    name: "Code Review Agent",
    role: "Reviews code for bugs, security, performance, and best practices",
    icon: "search",
    capabilities: ["code-review", "security-audit", "performance-analysis"],
  },
  {
    id: "testing",
    name: "Testing Agent",
    role: "Generates test cases, writes test suites, and validates functionality",
    icon: "check-circle",
    capabilities: ["test-generation", "test-execution", "coverage-analysis"],
  },
  {
    id: "devops",
    name: "DevOps Agent",
    role: "Creates CI/CD pipelines, Dockerfiles, deployment configs",
    icon: "server",
    capabilities: ["ci-cd", "containerization", "deployment", "monitoring"],
  },
  {
    id: "docs",
    name: "Documentation Agent",
    role: "Writes README files, API docs, inline comments, and guides",
    icon: "book",
    capabilities: ["readme-generation", "api-docs", "tutorials"],
  },
  {
    id: "security",
    name: "Security Agent",
    role: "Scans for vulnerabilities, suggests fixes, enforces security policies",
    icon: "shield",
    capabilities: ["vulnerability-scan", "dependency-audit", "security-policy"],
  },
  {
    id: "refactor",
    name: "Refactoring Agent",
    role: "Identifies code smells, suggests and applies refactoring patterns",
    icon: "recycle",
    capabilities: ["code-smell-detection", "pattern-application", "optimization"],
  },
  {
    id: "governance",
    name: "Governance Agent",
    role: "Enforces approval gates, compliance checks, and proof-of-work hashing",
    icon: "gavel",
    capabilities: ["approval-gates", "compliance", "proof-generation"],
  },
];

class AgentOrchestrator {
  constructor(llmBridge, projectManager) {
    this.llmBridge = llmBridge;
    this.projectManager = projectManager;
    this.pipelineHistory = [];
    this.activePipeline = null;
  }

  listAgents() {
    return AGENT_REGISTRY;
  }

  getStatus() {
    return {
      active: this.activePipeline,
      history: this.pipelineHistory.slice(-20),
      agentCount: AGENT_REGISTRY.length,
    };
  }

  async runPipeline(task, agentIds = null) {
    const agents = agentIds
      ? AGENT_REGISTRY.filter((a) => agentIds.includes(a.id))
      : this._selectAgentsForTask(task);

    const pipelineId = crypto.randomUUID();
    const pipeline = {
      id: pipelineId,
      task,
      agents: agents.map((a) => a.id),
      status: "running",
      startedAt: Date.now(),
      steps: [],
    };

    this.activePipeline = pipeline;

    try {
      for (const agent of agents) {
        const step = await this._runAgent(agent, task, pipeline.steps);
        pipeline.steps.push(step);

        if (step.error) {
          pipeline.status = "failed";
          pipeline.error = `Agent ${agent.id} failed: ${step.error}`;
          break;
        }
      }

      if (pipeline.status === "running") {
        pipeline.status = "completed";
      }
    } catch (err) {
      pipeline.status = "error";
      pipeline.error = err.message;
    }

    pipeline.completedAt = Date.now();
    pipeline.durationMs = pipeline.completedAt - pipeline.startedAt;
    this.activePipeline = null;
    this.pipelineHistory.push(pipeline);

    return pipeline;
  }

  async _runAgent(agent, task, previousSteps) {
    const contextFromPreviousSteps = previousSteps
      .map((s) => `[${s.agentId}]: ${s.summary || s.output?.slice(0, 200) || "no output"}`)
      .join("\n");

    const systemPrompt = `You are the ${agent.name} in the MEMBRA LLM Developer pipeline.
Your role: ${agent.role}
Your capabilities: ${agent.capabilities.join(", ")}

You are part of an autonomous software development pipeline. Previous agents in this pipeline have produced:
${contextFromPreviousSteps || "(You are the first agent in this pipeline)"}

Provide actionable, concrete output for your role. Be specific and thorough.`;

    const messages = [
      { role: "system", content: systemPrompt },
      { role: "user", content: `Task: ${task}\n\nProvide your analysis/output for this task based on your role.` },
    ];

    const startTime = Date.now();

    try {
      const result = await this.llmBridge.chat(messages, { temperature: 0.3 });

      const proofHash = crypto
        .createHash("sha256")
        .update(JSON.stringify({ agent: agent.id, task, output: result.content, ts: startTime }))
        .digest("hex");

      return {
        agentId: agent.id,
        agentName: agent.name,
        output: result.content,
        summary: result.content?.slice(0, 200),
        error: result.error || null,
        durationMs: Date.now() - startTime,
        proofHash,
      };
    } catch (err) {
      return {
        agentId: agent.id,
        agentName: agent.name,
        output: null,
        error: err.message,
        durationMs: Date.now() - startTime,
        proofHash: null,
      };
    }
  }

  _selectAgentsForTask(task) {
    const lower = task.toLowerCase();
    const selected = [];

    if (lower.includes("plan") || lower.includes("what to build") || lower.includes("roadmap")) {
      selected.push("strategy", "product");
    }
    if (lower.includes("build") || lower.includes("create") || lower.includes("implement") || lower.includes("code") || lower.includes("develop")) {
      selected.push("engineering");
    }
    if (lower.includes("review") || lower.includes("check") || lower.includes("audit")) {
      selected.push("reviewer");
    }
    if (lower.includes("test") || lower.includes("verify") || lower.includes("validate")) {
      selected.push("testing");
    }
    if (lower.includes("deploy") || lower.includes("ci") || lower.includes("docker") || lower.includes("pipeline")) {
      selected.push("devops");
    }
    if (lower.includes("doc") || lower.includes("readme") || lower.includes("guide")) {
      selected.push("docs");
    }
    if (lower.includes("secur") || lower.includes("vulnerab") || lower.includes("scan")) {
      selected.push("security");
    }
    if (lower.includes("refactor") || lower.includes("clean") || lower.includes("optimize")) {
      selected.push("refactor");
    }

    if (selected.length === 0) {
      selected.push("strategy", "engineering", "reviewer");
    }

    selected.push("governance");

    const unique = [...new Set(selected)];
    return unique.map((id) => AGENT_REGISTRY.find((a) => a.id === id)).filter(Boolean);
  }
}

module.exports = { AgentOrchestrator };
