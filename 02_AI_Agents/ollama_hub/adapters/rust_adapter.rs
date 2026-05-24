//! Rust LLM Adapter — drop this module into any Rust project.
//! Provides async LLM calls via local Ollama.

use reqwest;
use serde::{Deserialize, Serialize};
use serde_json::json;

const OLLAMA_HOST: &str = option_env!("OLLAMA_HOST").unwrap_or("http://localhost:11434");
const DEFAULT_MODEL: &str = "llama3.2:1b";

#[derive(Serialize)]
struct GenerateRequest {
    model: String,
    prompt: String,
    #[serde(skip_serializing_if = "String::is_empty")]
    system: String,
    stream: bool,
    options: GenerateOptions,
}

#[derive(Serialize)]
struct GenerateOptions {
    temperature: f32,
    num_predict: i32,
}

#[derive(Deserialize)]
struct GenerateResponse {
    response: String,
}

pub struct LLMClient {
    host: String,
    default_model: String,
    client: reqwest::Client,
}

impl LLMClient {
    pub fn new() -> Self {
        Self {
            host: OLLAMA_HOST.to_string(),
            default_model: DEFAULT_MODEL.to_string(),
            client: reqwest::Client::new(),
        }
    }

    pub fn with_model(model: &str) -> Self {
        Self {
            host: OLLAMA_HOST.to_string(),
            default_model: model.to_string(),
            client: reqwest::Client::new(),
        }
    }

    pub async fn generate(
        &self,
        prompt: &str,
        model: Option<&str>,
        system: Option<&str>,
        temperature: f32,
        max_tokens: i32,
    ) -> Result<String, reqwest::Error> {
        let req = GenerateRequest {
            model: model.unwrap_or(&self.default_model).to_string(),
            prompt: prompt.to_string(),
            system: system.unwrap_or("").to_string(),
            stream: false,
            options: GenerateOptions { temperature, num_predict: max_tokens },
        };

        let resp = self
            .client
            .post(format!("{}/api/generate", self.host))
            .json(&req)
            .send()
            .await?
            .json::<GenerateResponse>()
            .await?;

        Ok(resp.response)
    }

    pub async fn code_review(&self, code: &str) -> Result<String, reqwest::Error> {
        let system = "You are a senior Rust engineer. Review code for bugs, style, performance, security.";
        let prompt = format!("Review this Rust code:\n\n```\n{}\n```\n\nGive concise bullet points.", code);
        self.generate(&prompt, None, Some(system), 0.3, 600).await
    }

    pub async fn explain_code(&self, code: &str) -> Result<String, reqwest::Error> {
        let prompt = format!("Explain this code step by step:\n\n```\n{}\n```", code);
        self.generate(&prompt, None, Some("You explain code clearly."), 0.3, 500).await
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_generate() {
        let llm = LLMClient::new();
        let resp = llm.generate("What is 2+2?", None, None, 0.7, 50).await;
        assert!(resp.is_ok());
        let text = resp.unwrap();
        assert!(!text.is_empty());
    }
}
