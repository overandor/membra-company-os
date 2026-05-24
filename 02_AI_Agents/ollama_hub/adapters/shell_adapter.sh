#!/usr/bin/env bash
# Shell LLM Adapter — source this into any shell project.
# Provides LLM calls via local Ollama.

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
DEFAULT_MODEL="${OLLAMA_DEFAULT_MODEL:-llama3.2:1b}"

# llm_generate <prompt> [model] [system] [temperature] [max_tokens]
llm_generate() {
    local prompt="$1"
    local model="${2:-$DEFAULT_MODEL}"
    local system="${3:-}"
    local temp="${4:-0.7}"
    local max_tokens="${5:-400}"

    local json_body
    json_body=$(jq -n \
        --arg model "$model" \
        --arg prompt "$prompt" \
        --arg system "$system" \
        --argjson temperature "$temp" \
        --argjson num_predict "$max_tokens" \
        '{model: $model, prompt: $prompt, system: $system, stream: false, options: {temperature: $temperature, num_predict: $num_predict}}')

    curl -s -X POST "${OLLAMA_HOST}/api/generate" \
        -H "Content-Type: application/json" \
        -d "$json_body" | jq -r '.response'
}

# llm_chat <json_messages> [model]
llm_chat() {
    local messages="$1"
    local model="${2:-$DEFAULT_MODEL}"
    local json_body
    json_body=$(jq -n \
        --arg model "$model" \
        --argjson messages "$messages" \
        '{model: $model, messages: $messages, stream: false}')
    curl -s -X POST "${OLLAMA_HOST}/api/chat" \
        -H "Content-Type: application/json" \
        -d "$json_body" | jq -r '.message.content'
}

# llm_code_review <file> [language]
llm_code_review() {
    local file="$1"
    local lang="${2:-bash}"
    local code
    code=$(cat "$file")
    local system="You are a senior ${lang} engineer. Review for bugs, style, performance, security."
    local prompt="Review this ${lang} code:\n\n\`\`\`\n${code}\n\`\`\`\n\nGive concise bullet points."
    llm_generate "$prompt" "" "$system" 0.3 600
}

# llm_explain <file>
llm_explain() {
    local file="$1"
    local code
    code=$(cat "$file")
    local prompt="Explain this code step by step:\n\n\`\`\`\n${code}\n\`\`\`"
    llm_generate "$prompt" "" "You explain code clearly." 0.3 500
}
