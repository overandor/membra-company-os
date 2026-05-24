/**
 * JavaScript/TypeScript LLM Adapter — drop into any JS/TS project.
 * Provides async LLM calls via local Ollama.
 */

const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://localhost:11434';
const DEFAULT_MODEL = 'llama3.2:1b';

class LLMClient {
    constructor(host = OLLAMA_HOST, defaultModel = DEFAULT_MODEL) {
        this.host = host.replace(/\/$/, '');
        this.defaultModel = defaultModel;
    }

    async generate(prompt, options = {}) {
        const model = options.model || this.defaultModel;
        const system = options.system || '';
        const temperature = options.temperature ?? 0.7;
        const maxTokens = options.maxTokens ?? 400;

        const res = await fetch(`${this.host}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model,
                prompt,
                system,
                stream: false,
                options: { temperature, num_predict: maxTokens },
            }),
        });
        const data = await res.json();
        return data.response || '';
    }

    async chat(messages, model) {
        const m = model || this.defaultModel;
        const res = await fetch(`${this.host}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: m, messages, stream: false }),
        });
        const data = await res.json();
        return data.message?.content || '';
    }

    async embed(text, model = 'nomic-embed-text') {
        const res = await fetch(`${this.host}/api/embed`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model, input: text }),
        });
        const data = await res.json();
        return data.embeddings?.[0] || [];
    }

    async codeReview(code, language = 'javascript') {
        const system = `You are a senior ${language} engineer. Review for bugs, style, performance, security.`;
        const prompt = `Review this ${language} code:\n\n\`\`\`\n${code}\n\`\`\`\n\nGive concise bullet points.`;
        return this.generate(prompt, { system, temperature: 0.3, maxTokens: 600 });
    }

    async generateTests(code, language = 'javascript') {
        const system = 'You are a test engineer. Generate comprehensive unit tests.';
        const prompt = `Generate unit tests for this ${language} code:\n\n\`\`\`\n${code}\n\`\`\``;
        return this.generate(prompt, { system, temperature: 0.2, maxTokens: 800 });
    }

    async explainCode(code) {
        const prompt = `Explain this code step by step:\n\n\`\`\`\n${code}\n\`\`\``;
        return this.generate(prompt, { system: 'You explain code clearly.', temperature: 0.3, maxTokens: 500 });
    }
}

// ESM + CommonJS compatibility
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LLMClient, llm: new LLMClient() };
}
if (typeof window !== 'undefined') {
    window.LLMClient = LLMClient;
}

// Quick test if run directly
if (typeof process !== 'undefined' && process.argv[1] === new URL(import.meta.url).pathname) {
    const llm = new LLMClient();
    llm.generate('What is 2+2?').then(console.log).catch(console.error);
}
