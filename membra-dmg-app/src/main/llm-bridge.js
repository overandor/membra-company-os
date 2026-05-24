const https = require("https");
const http = require("http");

const DEFAULT_CONFIG = {
  provider: "groq",
  model: "llama-3.3-70b-versatile",
  apiKey: "",
  baseUrl: "",
  temperature: 0.3,
  maxTokens: 4096,
  ollamaUrl: "http://localhost:11434",
  ollamaModel: "codellama",
};

const PROVIDER_DEFAULTS = {
  groq: { baseUrl: "https://api.groq.com/openai/v1", model: "llama-3.3-70b-versatile" },
  openrouter: { baseUrl: "https://openrouter.ai/api/v1", model: "meta-llama/llama-3.3-70b-instruct" },
  openai: { baseUrl: "https://api.openai.com/v1", model: "gpt-4o" },
  gemini: { baseUrl: "https://generativelanguage.googleapis.com/v1beta", model: "gemini-2.0-flash" },
  ollama: { baseUrl: "http://localhost:11434", model: "codellama" },
};

class LLMBridge {
  constructor() {
    this.config = { ...DEFAULT_CONFIG };
    this.config.apiKey = process.env.GROQ_API_KEY || process.env.OPENROUTER_API_KEY || process.env.OPENAI_API_KEY || "";
    if (!this.config.apiKey && process.env.OPENROUTER_API_KEY) {
      this.config.provider = "openrouter";
      this.config.apiKey = process.env.OPENROUTER_API_KEY;
    }
  }

  getConfig() {
    return { ...this.config, apiKey: this.config.apiKey ? "***" : "" };
  }

  setConfig(newConfig) {
    Object.assign(this.config, newConfig);
    if (newConfig.provider && PROVIDER_DEFAULTS[newConfig.provider]) {
      const defaults = PROVIDER_DEFAULTS[newConfig.provider];
      if (!newConfig.baseUrl) this.config.baseUrl = defaults.baseUrl;
      if (!newConfig.model) this.config.model = defaults.model;
    }
  }

  async chat(messages, options = {}) {
    if (this.config.provider === "ollama") {
      return this._ollamaChat(messages, options);
    }
    if (this.config.provider === "gemini") {
      return this._geminiChat(messages, options);
    }
    return this._openaiCompatibleChat(messages, options);
  }

  async generateCode(prompt, language, context = "") {
    const systemPrompt = `You are an expert ${language} software developer working inside MEMBRA LLM Developer IDE.
Generate clean, production-ready code. Follow best practices for ${language}.
Return ONLY the code inside a single code block. No explanations unless asked.`;

    const userPrompt = context
      ? `Context:\n\`\`\`${language}\n${context}\n\`\`\`\n\nTask: ${prompt}`
      : prompt;

    const messages = [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt },
    ];

    return this.chat(messages, { temperature: 0.2 });
  }

  async reviewCode(code, language) {
    const messages = [
      {
        role: "system",
        content: `You are a senior code reviewer. Analyze the following ${language} code for:
1. Bugs and potential errors
2. Security vulnerabilities
3. Performance issues
4. Code style and best practices
5. Suggested improvements

Format your review with clear sections and severity levels (CRITICAL, WARNING, INFO).`,
      },
      { role: "user", content: `Review this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\`` },
    ];

    return this.chat(messages, { temperature: 0.1 });
  }

  async explainCode(code, language) {
    const messages = [
      {
        role: "system",
        content: `You are a patient teacher explaining ${language} code. Provide a clear, structured explanation covering:
1. What the code does (high-level summary)
2. Key components and their roles
3. Data flow and control flow
4. Any notable patterns or techniques used`,
      },
      { role: "user", content: `Explain this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\`` },
    ];

    return this.chat(messages, { temperature: 0.3 });
  }

  async refactorCode(code, language, instructions) {
    const messages = [
      {
        role: "system",
        content: `You are an expert ${language} developer performing code refactoring.
Apply the requested changes while maintaining functionality.
Return the complete refactored code in a code block, followed by a brief summary of changes.`,
      },
      {
        role: "user",
        content: `Refactor this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\`\n\nInstructions: ${instructions}`,
      },
    ];

    return this.chat(messages, { temperature: 0.2 });
  }

  async debugCode(code, error, language) {
    const messages = [
      {
        role: "system",
        content: `You are a debugging expert for ${language}. Analyze the code and error, then:
1. Identify the root cause
2. Explain why the error occurs
3. Provide the fixed code in a code block
4. Suggest how to prevent similar issues`,
      },
      {
        role: "user",
        content: `Debug this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\`\n\nError:\n\`\`\`\n${error}\n\`\`\``,
      },
    ];

    return this.chat(messages, { temperature: 0.1 });
  }

  async _openaiCompatibleChat(messages, options) {
    const baseUrl = this.config.baseUrl || PROVIDER_DEFAULTS[this.config.provider]?.baseUrl;
    const url = new URL(`${baseUrl}/chat/completions`);

    const body = JSON.stringify({
      model: options.model || this.config.model,
      messages,
      temperature: options.temperature ?? this.config.temperature,
      max_tokens: options.maxTokens ?? this.config.maxTokens,
      stream: false,
    });

    const headers = {
      "Content-Type": "application/json",
      Authorization: `Bearer ${this.config.apiKey}`,
    };

    const data = await this._request(url, "POST", headers, body);
    const parsed = JSON.parse(data);

    if (parsed.error) {
      return { error: parsed.error.message || JSON.stringify(parsed.error), content: null };
    }

    return {
      content: parsed.choices?.[0]?.message?.content || "",
      usage: parsed.usage || null,
      model: parsed.model || this.config.model,
    };
  }

  async _ollamaChat(messages, options) {
    const url = new URL(`${this.config.ollamaUrl}/api/chat`);

    const body = JSON.stringify({
      model: options.model || this.config.ollamaModel,
      messages,
      stream: false,
      options: {
        temperature: options.temperature ?? this.config.temperature,
        num_predict: options.maxTokens ?? this.config.maxTokens,
      },
    });

    const headers = { "Content-Type": "application/json" };

    try {
      const data = await this._request(url, "POST", headers, body);
      const parsed = JSON.parse(data);
      return { content: parsed.message?.content || "", model: parsed.model || this.config.ollamaModel };
    } catch (err) {
      return { error: `Ollama unreachable: ${err.message}`, content: null };
    }
  }

  async _geminiChat(messages, options) {
    const model = options.model || this.config.model;
    const url = new URL(
      `${PROVIDER_DEFAULTS.gemini.baseUrl}/models/${model}:generateContent?key=${this.config.apiKey}`
    );

    const contents = messages
      .filter((m) => m.role !== "system")
      .map((m) => ({
        role: m.role === "assistant" ? "model" : "user",
        parts: [{ text: m.content }],
      }));

    const systemInstruction = messages.find((m) => m.role === "system");
    const body = JSON.stringify({
      contents,
      ...(systemInstruction && { systemInstruction: { parts: [{ text: systemInstruction.content }] } }),
      generationConfig: {
        temperature: options.temperature ?? this.config.temperature,
        maxOutputTokens: options.maxTokens ?? this.config.maxTokens,
      },
    });

    const headers = { "Content-Type": "application/json" };

    const data = await this._request(url, "POST", headers, body);
    const parsed = JSON.parse(data);

    if (parsed.error) {
      return { error: parsed.error.message, content: null };
    }

    return {
      content: parsed.candidates?.[0]?.content?.parts?.[0]?.text || "",
      model,
    };
  }

  _request(url, method, headers, body) {
    return new Promise((resolve, reject) => {
      const transport = url.protocol === "https:" ? https : http;
      const req = transport.request(url, { method, headers }, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          if (res.statusCode >= 400) {
            reject(new Error(`HTTP ${res.statusCode}: ${data.slice(0, 500)}`));
          } else {
            resolve(data);
          }
        });
      });
      req.on("error", reject);
      req.setTimeout(60000, () => {
        req.destroy();
        reject(new Error("Request timed out"));
      });
      if (body) req.write(body);
      req.end();
    });
  }
}

module.exports = { LLMBridge };
