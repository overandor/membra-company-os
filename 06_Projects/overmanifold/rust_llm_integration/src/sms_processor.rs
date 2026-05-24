//! Rust LLM SMS Processing System
//! Custom SMS gateway without Twilio dependencies

use anyhow::{Context, Result};
use async_trait::async_trait;
use chrono::{DateTime, Utc};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::env;
use std::time::Duration;
use tracing::{debug, error, info, warn};
use uuid::Uuid;

/// SMS intent types
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum SmsIntent {
    Payment,
    Balance,
    Help,
    Register,
    Verify,
    Unknown,
}

/// SMS intent result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SmsIntentResult {
    pub intent: SmsIntent,
    pub confidence: f64,
    pub parameters: HashMap<String, String>,
    pub reasoning: String,
}

/// SMS payment request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SmsPaymentRequest {
    pub from_phone: String,
    pub to_phone: String,
    pub amount: f64,
    pub currency: String,
    pub message: String,
}

/// SMS message structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SmsMessage {
    pub id: String,
    pub from_phone: String,
    pub to_phone: String,
    pub content: String,
    pub timestamp: DateTime<Utc>,
    pub processed: bool,
    pub intent_result: Option<SmsIntentResult>,
}

impl SmsMessage {
    pub fn new(from_phone: String, to_phone: String, content: String) -> Self {
        let id = Self::generate_message_id(&from_phone, &to_phone, &content);
        Self {
            id,
            from_phone,
            to_phone,
            content,
            timestamp: Utc::now(),
            processed: false,
            intent_result: None,
        }
    }

    fn generate_message_id(from: &str, to: &str, content: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(format!("{}{}{}{}", from, to, content, Utc::now().timestamp()));
        hex::encode(hasher.finalize())
    }
}

/// LLM SMS processor
pub struct LlmSmsProcessor {
    openai_api_key: Option<String>,
    client: Client,
    sms_gateway: CustomSmsGateway,
}

impl LlmSmsProcessor {
    pub fn new(openai_api_key: Option<String>) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");

        Self {
            openai_api_key,
            client,
            sms_gateway: CustomSmsGateway::new(),
        }
    }

    pub fn from_env() -> Self {
        let api_key = env::var("OPENAI_API_KEY").ok();
        Self::new(api_key)
    }

    /// Process SMS message and extract intent
    pub async fn process_message(&self, message: &mut SmsMessage) -> Result<SmsIntentResult> {
        info!("Processing SMS message from {}", message.from_phone);

        let intent_result = if let Some(ref api_key) = self.openai_api_key {
            self.analyze_with_llm(&message.content, api_key).await?
        } else {
            self.analyze_fallback(&message.content)?
        };

        message.intent_result = Some(intent_result.clone());
        message.processed = true;

        debug!("SMS intent detected: {:?}", intent_result.intent);
        Ok(intent_result)
    }

    /// Analyze SMS content using OpenAI LLM
    async fn analyze_with_llm(&self, content: &str, api_key: &str) -> Result<SmsIntentResult> {
        let prompt = self.build_analysis_prompt(content);

        let response = self
            .client
            .post("https://api.openai.com/v1/chat/completions")
            .header("Authorization", format!("Bearer {}", api_key))
            .header("Content-Type", "application/json")
            .json(&serde_json::json!({
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": self.get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }))
            .send()
            .await?;

        if !response.status().is_success() {
            let error_text = response.text().await?;
            return Err(anyhow::anyhow!("OpenAI API error: {}", error_text));
        }

        let response_json: serde_json::Value = response.json().await?;
        let content = response_json["choices"][0]["message"]["content"]
            .as_str()
            .context("Missing content in response")?;

        let result: serde_json::Value = serde_json::from_str(content)?;
        Ok(self.parse_llm_response(result)?)
    }

    /// Fallback keyword-based analysis
    fn analyze_fallback(&self, content: &str) -> Result<SmsIntentResult> {
        let content_lower = content.to_lowercase();

        let (intent, confidence, reasoning) = if content_lower.contains("pay") || content_lower.contains("send") {
            (SmsIntent::Payment, 0.8, "Payment keywords detected")
        } else if content_lower.contains("balance") || content_lower.contains("how much") {
            (SmsIntent::Balance, 0.85, "Balance inquiry detected")
        } else if content_lower.contains("help") || content_lower.contains("what can") {
            (SmsIntent::Help, 0.9, "Help request detected")
        } else if content_lower.contains("register") || content_lower.contains("sign up") {
            (SmsIntent::Register, 0.85, "Registration request detected")
        } else if content_lower.contains("verify") || content_lower.contains("code") {
            (SmsIntent::Verify, 0.8, "Verification request detected")
        } else {
            (SmsIntent::Unknown, 0.5, "No clear intent detected")
        };

        Ok(SmsIntentResult {
            intent,
            confidence,
            parameters: HashMap::new(),
            reasoning: reasoning.to_string(),
        })
    }

    fn get_system_prompt(&self) -> &'static str {
        r#"You are an intelligent SMS analyzer for Overmanifold Protocol. Analyze SMS messages and determine user intent.

INTENT TYPES:
1. PAYMENT - User wants to send money or make a payment
2. BALANCE - User wants to check their account balance
3. HELP - User is asking for help or information
4. REGISTER - User wants to register or sign up
5. VERIFY - User is responding to verification or providing codes
6. UNKNOWN - Intent cannot be determined

ANALYSIS FORMAT:
Return JSON with this exact structure:
{
  "intent": "payment|balance|help|register|verify|unknown",
  "confidence": 0.0-1.0,
  "parameters": {
    "amount": "100.0",
    "recipient": "+1234567890",
    "currency": "USD"
  },
  "reasoning": "explain your analysis"
}

Extract relevant parameters like amount, recipient phone, currency, etc."#
    }

    fn build_analysis_prompt(&self, content: &str) -> String {
        format!("SMS Message: {}", content)
    }

    fn parse_llm_response(&self, response: serde_json::Value) -> Result<SmsIntentResult> {
        let intent_str = response["intent"]
            .as_str()
            .context("Missing intent field")?;

        let intent = match intent_str {
            "payment" => SmsIntent::Payment,
            "balance" => SmsIntent::Balance,
            "help" => SmsIntent::Help,
            "register" => SmsIntent::Register,
            "verify" => SmsIntent::Verify,
            _ => SmsIntent::Unknown,
        };

        let confidence = response["confidence"]
            .as_f64()
            .unwrap_or(0.5);

        let parameters: HashMap<String, String> = response["parameters"]
            .as_object()
            .map(|obj| {
                obj.iter()
                    .filter_map(|(k, v)| v.as_str().map(|s| (k.clone(), s.to_string())))
                    .collect()
            })
            .unwrap_or_default();

        let reasoning = response["reasoning"]
            .as_str()
            .unwrap_or("LLM analysis")
            .to_string();

        Ok(SmsIntentResult {
            intent,
            confidence,
            parameters,
            reasoning,
        })
    }

    /// Send SMS using custom gateway
    pub async fn send_sms(&self, to_phone: &str, message: &str) -> Result<bool> {
        self.sms_gateway.send_sms(to_phone, message).await
    }

    /// Generate verification code
    pub async fn generate_verification_code(&self, phone: &str) -> Result<String> {
        self.sms_gateway.generate_verification_code(phone).await
    }

    /// Get system health
    pub fn get_system_health(&self) -> SystemHealth {
        SystemHealth {
            status: "operational".to_string(),
            messages_processed: 0,
            active_sessions: 0,
            llm_available: self.openai_api_key.is_some(),
        }
    }
}

/// System health status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemHealth {
    pub status: String,
    pub messages_processed: u64,
    pub active_sessions: u64,
    pub llm_available: bool,
}

/// Custom SMS Gateway (No Twilio dependency)
pub struct CustomSmsGateway {
    verification_codes: HashMap<String, (String, DateTime<Utc>)>,
    client: Client,
}

impl CustomSmsGateway {
    pub fn new() -> Self {
        Self {
            verification_codes: HashMap::new(),
            client: Client::builder()
                .timeout(Duration::from_secs(30))
                .build()
                .expect("Failed to create HTTP client"),
        }
    }

    /// Send SMS using custom delivery methods
    pub async fn send_sms(&self, to_phone: &str, message: &str) -> Result<bool> {
        info!("Sending SMS to {} via custom gateway", to_phone);

        // In production, this would integrate with actual SMS providers
        // For now, we simulate successful delivery
        debug!("SMS content: {}", message);
        Ok(true)
    }

    /// Generate and store verification code
    pub async fn generate_verification_code(&self, phone: &str) -> Result<String> {
        let code = self.generate_secure_code(phone);
        let expiry = Utc::now() + chrono::Duration::minutes(10);

        // Store code (in production, use Redis or database)
        debug!("Generated verification code for {} (expires at {})", phone, expiry);

        Ok(code)
    }

    fn generate_secure_code(&self, phone: &str) -> String {
        use rand::Rng;
        let mut hasher = Sha256::new();
        let random_bytes: [u8; 4] = rand::thread_rng().gen();
        hasher.update(format!("{}{:x}{}", phone, hex::encode(random_bytes), Utc::now().timestamp()));
        
        let hash = hex::encode(hasher.finalize());
        let digits: String = hash.chars().filter(|c| c.is_ascii_digit()).take(6).collect();
        
        if digits.len() < 6 {
            format!("{}{}", digits, rand::thread_rng().gen_range(0..10))
        } else {
            digits
        }
    }

    /// Verify code (simulated)
    pub fn verify_code(&self, phone: &str, code: &str) -> Result<bool> {
        // In production, check against stored codes
        Ok(true)
    }
}

impl Default for CustomSmsGateway {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sms_message_creation() {
        let message = SmsMessage::new(
            "+1234567890".to_string(),
            "+0987654321".to_string(),
            "Send 100 USDC to +1555555555".to_string(),
        );

        assert!(!message.id.is_empty());
        assert!(!message.processed);
        assert_eq!(message.from_phone, "+1234567890");
    }

    #[test]
    fn test_fallback_analysis() {
        let processor = LlmSmsProcessor::new(None);
        
        let result = processor.analyze_fallback("Send 100 USDC to +1555555555").unwrap();
        assert_eq!(result.intent, SmsIntent::Payment);
        assert!(result.confidence > 0.5);
    }

    #[test]
    fn test_gateway_code_generation() {
        let gateway = CustomSmsGateway::new();
        let code = gateway.generate_secure_code("+1234567890");
        assert_eq!(code.len(), 6);
        assert!(code.chars().all(|c| c.is_ascii_digit()));
    }
}

fn main() {
    tracing_subscriber::fmt().init();
    
    let processor = LlmSmsProcessor::from_env();
    let health = processor.get_system_health();
    
    println!("Rust LLM SMS Processor Status: {}", health.status);
    println!("LLM Available: {}", health.llm_available);
}