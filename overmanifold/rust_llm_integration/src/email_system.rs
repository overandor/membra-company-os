//! Rust LLM Email System
//! Custom email delivery without SendGrid dependencies

use anyhow::{Context, Result};
use async_trait::async_trait;
use chrono::{DateTime, Utc};
use lettre::message::{header, Mailbox, Message};
use lettre::transport::smtp::authentication::Credentials;
use lettre::{SmtpTransport, Transport};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::env;
use std::time::Duration;
use tracing::{debug, error, info, warn};
use uuid::Uuid;

/// Email delivery methods
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(rename_all = "lowercase")]
pub enum EmailDeliveryMethod {
    Smtp,
    Api,
    Queue,
    Direct,
}

/// Email message structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmailMessage {
    pub id: String,
    pub to_email: String,
    pub from_email: String,
    pub subject: String,
    pub body: String,
    pub html_body: String,
    pub priority: String,
    pub timestamp: DateTime<Utc>,
    pub delivery_method: EmailDeliveryMethod,
    pub status: String,
    pub delivery_attempts: u32,
    pub metadata: HashMap<String, String>,
}

impl EmailMessage {
    pub fn new(
        to_email: String,
        from_email: String,
        subject: String,
        body: String,
        html_body: String,
    ) -> Self {
        let id = Self::generate_message_id(&to_email, &from_email, &subject);
        Self {
            id,
            to_email,
            from_email,
            subject,
            body,
            html_body,
            priority: "normal".to_string(),
            timestamp: Utc::now(),
            delivery_method: EmailDeliveryMethod::Smtp,
            status: "pending".to_string(),
            delivery_attempts: 0,
            metadata: HashMap::new(),
        }
    }

    fn generate_message_id(to: &str, from: &str, subject: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(format!("{}{}{}{}", to, from, subject, Utc::now().timestamp()));
        hex::encode(hasher.finalize())
    }
}

/// Email delivery result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmailDeliveryResult {
    pub success: bool,
    pub message_id: String,
    pub delivery_method: EmailDeliveryMethod,
    pub cost: f64,
    pub status: String,
    pub error_message: String,
    pub delivery_timestamp: Option<DateTime<Utc>>,
    pub server_response: String,
}

/// Email delivery trait
#[async_trait]
pub trait EmailDelivery: Send + Sync {
    async fn send_email(&self, message: &EmailMessage) -> Result<EmailDeliveryResult>;
    async fn get_delivery_status(&self, message_id: &str) -> Result<HashMap<String, String>>;
}

/// SMTP email delivery
pub struct SmtpEmailDelivery {
    smtp_server: String,
    smtp_port: u16,
    smtp_user: Option<String>,
    smtp_password: Option<String>,
    use_tls: bool,
}

impl SmtpEmailDelivery {
    pub fn new(
        smtp_server: String,
        smtp_port: u16,
        smtp_user: Option<String>,
        smtp_password: Option<String>,
        use_tls: bool,
    ) -> Self {
        Self {
            smtp_server,
            smtp_port,
            smtp_user,
            smtp_password,
            use_tls,
        }
    }

    pub fn from_env() -> Self {
        Self::new(
            env::var("SMTP_SERVER").unwrap_or_else(|_| "localhost".to_string()),
            env::var("SMTP_PORT")
                .unwrap_or_else(|_| "587".to_string())
                .parse()
                .unwrap_or(587),
            env::var("SMTP_USERNAME").ok(),
            env::var("SMTP_PASSWORD").ok(),
            true,
        )
    }
}

#[async_trait]
impl EmailDelivery for SmtpEmailDelivery {
    async fn send_email(&self, message: &EmailMessage) -> Result<EmailDeliveryResult> {
        info!("Sending email via SMTP to {}", message.to_email);

        let from_mailbox: Mailbox = message.from_email.parse()?;
        let to_mailbox: Mailbox = message.to_email.parse()?;

        let email_builder = Message::builder()
            .from(from_mailbox)
            .to(to_mailbox)
            .subject(&message.subject);

        let email = if !message.html_body.is_empty() {
            email_builder
                .multipart(
                    lettre::message::MultiPart::alternative_plain_html(
                        message.body.clone(),
                        message.html_body.clone(),
                    ),
                )?
        } else {
            email_builder.body(message.body.clone())?
        };

        // Send via SMTP
        let mailer = if let (Some(user), Some(password)) = (&self.smtp_user, &self.smtp_password) {
            let creds = Credentials::new(user.clone(), password.clone());
            SmtpTransport::relay(&self.smtp_server)?
                .credentials(creds)
                .build()
        } else {
            SmtpTransport::builder_dangerous(&self.smtp_server).build()
        };

        match mailer.send(&email) {
            Ok(_) => {
                info!("Email sent successfully via SMTP");
                Ok(EmailDeliveryResult {
                    success: true,
                    message_id: message.id.clone(),
                    delivery_method: EmailDeliveryMethod::Smtp,
                    cost: 0.0,
                    status: "delivered".to_string(),
                    error_message: String::new(),
                    delivery_timestamp: Some(Utc::now()),
                    server_response: "Message sent successfully".to_string(),
                })
            }
            Err(e) => {
                error!("SMTP email delivery failed: {}", e);
                Ok(EmailDeliveryResult {
                    success: false,
                    message_id: message.id.clone(),
                    delivery_method: EmailDeliveryMethod::Smtp,
                    cost: 0.0,
                    status: "failed".to_string(),
                    error_message: e.to_string(),
                    delivery_timestamp: None,
                    server_response: String::new(),
                })
            }
        }
    }

    async fn get_delivery_status(&self, message_id: &str) -> Result<HashMap<String, String>> {
        let mut status = HashMap::new();
        status.insert("message_id".to_string(), message_id.to_string());
        status.insert("status".to_string(), "delivered".to_string());
        status.insert("method".to_string(), "smtp".to_string());
        status.insert("timestamp".to_string(), Utc::now().to_rfc3339());
        Ok(status)
    }
}

/// API email delivery
pub struct ApiEmailDelivery {
    api_endpoint: Option<String>,
    api_key: Option<String>,
    client: Client,
}

impl ApiEmailDelivery {
    pub fn new(api_endpoint: Option<String>, api_key: Option<String>) -> Self {
        Self {
            api_endpoint,
            api_key,
            client: Client::builder()
                .timeout(Duration::from_secs(30))
                .build()
                .expect("Failed to create HTTP client"),
        }
    }

    pub fn from_env() -> Self {
        Self::new(
            env::var("EMAIL_API_ENDPOINT").ok(),
            env::var("EMAIL_API_KEY").ok(),
        )
    }
}

#[async_trait]
impl EmailDelivery for ApiEmailDelivery {
    async fn send_email(&self, message: &EmailMessage) -> Result<EmailDeliveryResult> {
        info!("Sending email via API to {}", message.to_email);

        let endpoint = match &self.api_endpoint {
            Some(ep) => ep.clone(),
            None => {
                return Ok(EmailDeliveryResult {
                    success: false,
                    message_id: message.id.clone(),
                    delivery_method: EmailDeliveryMethod::Api,
                    cost: 0.0,
                    status: "no_api_configured".to_string(),
                    error_message: "No email API endpoint configured".to_string(),
                    delivery_timestamp: None,
                    server_response: String::new(),
                })
            }
        };

        let payload = serde_json::json!({
            "message_id": message.id,
            "to": message.to_email,
            "from": message.from_email,
            "subject": message.subject,
            "body": message.body,
            "html_body": message.html_body,
            "priority": message.priority,
            "timestamp": message.timestamp.to_rfc3339()
        });

        let mut request = self.client.post(&endpoint).json(&payload);

        if let Some(ref key) = self.api_key {
            request = request.header("Authorization", format!("Bearer {}", key));
        }

        match request.send().await {
            Ok(response) => {
                if response.status().is_success() {
                    let result: serde_json::Value = response.json().await?;
                    Ok(EmailDeliveryResult {
                        success: true,
                        message_id: message.id.clone(),
                        delivery_method: EmailDeliveryMethod::Api,
                        cost: result["cost"].as_f64().unwrap_or(0.0),
                        status: "delivered".to_string(),
                        error_message: String::new(),
                        delivery_timestamp: Some(Utc::now()),
                        server_response: result.to_string(),
                    })
                } else {
                    Ok(EmailDeliveryResult {
                        success: false,
                        message_id: message.id.clone(),
                        delivery_method: EmailDeliveryMethod::Api,
                        cost: 0.0,
                        status: "api_error".to_string(),
                        error_message: format!("API returned {}", response.status()),
                        delivery_timestamp: None,
                        server_response: String::new(),
                    })
                }
            }
            Err(e) => {
                error!("API email delivery failed: {}", e);
                Ok(EmailDeliveryResult {
                    success: false,
                    message_id: message.id.clone(),
                    delivery_method: EmailDeliveryMethod::Api,
                    cost: 0.0,
                    status: "failed".to_string(),
                    error_message: e.to_string(),
                    delivery_timestamp: None,
                    server_response: String::new(),
                })
            }
        }
    }

    async fn get_delivery_status(&self, message_id: &str) -> Result<HashMap<String, String>> {
        let mut status = HashMap::new();
        status.insert("message_id".to_string(), message_id.to_string());
        status.insert("status".to_string(), "delivered".to_string());
        status.insert("method".to_string(), "api".to_string());
        status.insert("timestamp".to_string(), Utc::now().to_rfc3339());
        Ok(status)
    }
}

/// LLM email analyzer
pub struct LlmEmailAnalyzer {
    openai_api_key: Option<String>,
    client: Client,
}

impl LlmEmailAnalyzer {
    pub fn new(openai_api_key: Option<String>) -> Self {
        Self {
            openai_api_key,
            client: Client::builder()
                .timeout(Duration::from_secs(30))
                .build()
                .expect("Failed to create HTTP client"),
        }
    }

    pub fn from_env() -> Self {
        Self::new(env::var("OPENAI_API_KEY").ok())
    }

    /// Analyze email content
    pub async fn analyze_email(
        &self,
        to_email: &str,
        subject: &str,
        body: &str,
        html_body: &str,
    ) -> Result<EmailAnalysis> {
        if let Some(ref api_key) = self.openai_api_key {
            self.analyze_with_llm(to_email, subject, body, html_body, api_key)
                .await
        } else {
            Ok(self.analyze_fallback(subject, body))
        }
    }

    async fn analyze_with_llm(
        &self,
        to_email: &str,
        subject: &str,
        body: &str,
        html_body: &str,
        api_key: &str,
    ) -> Result<EmailAnalysis> {
        let prompt = format!(
            "To: {}\nSubject: {}\nBody: {}\nHTML Body: {}",
            to_email,
            subject,
            body,
            if html_body.len() > 500 {
                &html_body[..500]
            } else {
                html_body
            }
        );

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

    fn analyze_fallback(&self, subject: &str, body: &str) -> EmailAnalysis {
        let subject_lower = subject.to_lowercase();
        let body_lower = body.to_lowercase();

        let (email_type, confidence, delivery_method) = if subject_lower.contains("verification")
            || subject_lower.contains("code")
        {
            ("verification", 0.8, "smtp")
        } else if subject_lower.contains("payment") || subject_lower.contains("transaction") {
            ("transaction", 0.75, "smtp")
        } else {
            ("notification", 0.6, "smtp")
        };

        EmailAnalysis {
            email_type: email_type.to_string(),
            confidence,
            urgency: "normal".to_string(),
            priority: "medium".to_string(),
            personalization_required: true,
            compliance_flags: vec![],
            recommended_delivery_method: delivery_method.to_string(),
            reasoning: "Keyword-based analysis".to_string(),
            estimated_cost: 0.0,
        }
    }

    fn get_system_prompt(&self) -> &'static str {
        r#"You are an intelligent email analysis system for Overmanifold Protocol. Analyze emails and determine optimal processing strategy.

ANALYSIS FORMAT:
Return JSON with this exact structure:
{
  "email_type": "transaction|verification|notification|support|marketing",
  "confidence": 0.0-1.0,
  "urgency": "normal|high|urgent",
  "priority": "low|medium|high",
  "personalization_required": true|false,
  "compliance_flags": [],
  "recommended_delivery_method": "smtp|api|queue|webhook|in_app",
  "reasoning": "explain analysis decision",
  "estimated_cost": 0.0
}"#
    }

    fn parse_llm_response(&self, response: serde_json::Value) -> Result<EmailAnalysis> {
        Ok(EmailAnalysis {
            email_type: response["email_type"]
                .as_str()
                .unwrap_or("notification")
                .to_string(),
            confidence: response["confidence"].as_f64().unwrap_or(0.5),
            urgency: response["urgency"]
                .as_str()
                .unwrap_or("normal")
                .to_string(),
            priority: response["priority"]
                .as_str()
                .unwrap_or("medium")
                .to_string(),
            personalization_required: response["personalization_required"]
                .as_bool()
                .unwrap_or(false),
            compliance_flags: response["compliance_flags"]
                .as_array()
                .map(|arr| {
                    arr.iter()
                        .filter_map(|v| v.as_str().map(|s| s.to_string()))
                        .collect()
                })
                .unwrap_or_default(),
            recommended_delivery_method: response["recommended_delivery_method"]
                .as_str()
                .unwrap_or("smtp")
                .to_string(),
            reasoning: response["reasoning"]
                .as_str()
                .unwrap_or("LLM analysis")
                .to_string(),
            estimated_cost: response["estimated_cost"].as_f64().unwrap_or(0.0),
        })
    }
}

/// Email analysis result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmailAnalysis {
    pub email_type: String,
    pub confidence: f64,
    pub urgency: String,
    pub priority: String,
    pub personalization_required: bool,
    pub compliance_flags: Vec<String>,
    pub recommended_delivery_method: String,
    pub reasoning: String,
    pub estimated_cost: f64,
}

/// LLM custom email system
pub struct LlmCustomEmailSystem {
    analyzer: LlmEmailAnalyzer,
    delivery_methods: HashMap<EmailDeliveryMethod, Box<dyn EmailDelivery>>,
    delivery_history: HashMap<String, EmailDeliveryResult>,
}

impl LlmCustomEmailSystem {
    pub fn new(openai_api_key: Option<String>) -> Self {
        let mut delivery_methods: HashMap<EmailDeliveryMethod, Box<dyn EmailDelivery>> = HashMap::new();
        delivery_methods.insert(EmailDeliveryMethod::Smtp, Box::new(SmtpEmailDelivery::from_env()));
        delivery_methods.insert(EmailDeliveryMethod::Api, Box::new(ApiEmailDelivery::from_env()));

        Self {
            analyzer: LlmEmailAnalyzer::new(openai_api_key),
            delivery_methods,
            delivery_history: HashMap::new(),
        }
    }

    pub fn from_env() -> Self {
        Self::new(env::var("OPENAI_API_KEY").ok())
    }

    /// Send custom email
    pub async fn send_custom_email(
        &mut self,
        to_email: &str,
        subject: &str,
        body: &str,
        html_body: &str,
        from_email: Option<&str>,
    ) -> Result<EmailDeliveryResult> {
        let from = from_email.unwrap_or_else(|| env::var("DEFAULT_FROM_EMAIL").unwrap_or_else(|_| "noreply@overmanifold.io".to_string()).as_str());

        let analysis = self
            .analyzer
            .analyze_email(to_email, subject, body, html_body)
            .await?;

        let delivery_method = match analysis.recommended_delivery_method.as_str() {
            "api" => EmailDeliveryMethod::Api,
            "queue" => EmailDeliveryMethod::Queue,
            "direct" => EmailDeliveryMethod::Direct,
            _ => EmailDeliveryMethod::Smtp,
        };

        let mut message = EmailMessage::new(
            to_email.to_string(),
            from.to_string(),
            subject.to_string(),
            body.to_string(),
            html_body.to_string(),
        );
        message.delivery_method = delivery_method.clone();
        message.priority = analysis.priority.clone();

        let delivery_interface = self
            .delivery_methods
            .get(&delivery_method)
            .unwrap_or_else(|| self.delivery_methods.get(&EmailDeliveryMethod::Smtp).unwrap());

        let result = delivery_interface.send_email(&message).await?;
        self.delivery_history.insert(message.id.clone(), result.clone());

        info!("Email sent via {:?}: {}", delivery_method, result.success);
        Ok(result)
    }

    /// Send verification email
    pub async fn send_verification_email(&mut self, email: &str) -> Result<String> {
        let code = self.generate_secure_code(email);

        let subject = "Overmanifold Verification Code";
        let body = format!(
            "Your verification code is: {}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this code, please ignore this email.",
            code
        );

        let html_body = format!(
            r#"<html><body><h2>Verification Code</h2><p>Your verification code is: <strong>{}</strong></p><p>This code will expire in 10 minutes.</p><p>If you did not request this code, please ignore this email.</p><hr><p><small>Overmanifold Protocol</small></p></body></html>"#,
            code
        );

        let result = self
            .send_custom_email(email, subject, &body, &html_body, None)
            .await?;

        if result.success {
            info!("Verification email sent to {}", email);
        } else {
            error!("Verification email failed: {}", result.error_message);
        }

        Ok(code)
    }

    fn generate_secure_code(&self, email: &str) -> String {
        use rand::Rng;
        let mut hasher = Sha256::new();
        let random_bytes: [u8; 4] = rand::thread_rng().gen();
        hasher.update(format!("{}{:x}{}", email, hex::encode(random_bytes), Utc::now().timestamp()));
        
        let hash = hex::encode(hasher.finalize());
        let digits: String = hash.chars().filter(|c| c.is_ascii_digit()).take(6).collect();
        
        if digits.len() < 6 {
            format!("{}{}", digits, rand::thread_rng().gen_range(0..10))
        } else {
            digits
        }
    }

    /// Get email statistics
    pub fn get_email_statistics(&self) -> EmailStatistics {
        let total_emails = self.delivery_history.len() as u64;
        let successful = self
            .delivery_history
            .values()
            .filter(|r| r.success)
            .count() as u64;
        let failed = total_emails - successful;

        let mut method_counts: HashMap<String, u64> = HashMap::new();
        for result in self.delivery_history.values() {
            let method = format!("{:?}", result.delivery_method);
            *method_counts.entry(method).or_insert(0) += 1;
        }

        let total_cost: f64 = self.delivery_history.values().map(|r| r.cost).sum();

        EmailStatistics {
            total_emails,
            successful,
            failed,
            success_rate: if total_emails > 0 {
                successful as f64 / total_emails as f64
            } else {
                0.0
            },
            method_distribution: method_counts,
            total_cost,
            average_cost_per_email: if total_emails > 0 {
                total_cost / total_emails as f64
            } else {
                0.0
            },
        }
    }
}

/// Email statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmailStatistics {
    pub total_emails: u64,
    pub successful: u64,
    pub failed: u64,
    pub success_rate: f64,
    pub method_distribution: HashMap<String, u64>,
    pub total_cost: f64,
    pub average_cost_per_email: f64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_email_message_creation() {
        let message = EmailMessage::new(
            "test@example.com".to_string(),
            "noreply@overmanifold.io".to_string(),
            "Test Subject".to_string(),
            "Test Body".to_string(),
            "<html>Test</html>".to_string(),
        );

        assert!(!message.id.is_empty());
        assert_eq!(message.status, "pending");
    }

    #[test]
    fn test_fallback_analysis() {
        let analyzer = LlmEmailAnalyzer::new(None);
        let analysis = analyzer.analyze_fallback("Verification Code", "Your code is 123456");
        
        assert_eq!(analysis.email_type, "verification");
        assert!(analysis.confidence > 0.5);
    }

    #[test]
    fn test_code_generation() {
        let system = LlmCustomEmailSystem::new(None);
        let code = system.generate_secure_code("test@example.com");
        assert_eq!(code.len(), 6);
        assert!(code.chars().all(|c| c.is_ascii_digit()));
    }
}

fn main() {
    tracing_subscriber::fmt().init();
    
    let email_system = LlmCustomEmailSystem::from_env();
    let stats = email_system.get_email_statistics();
    
    println!("Rust LLM Email System Statistics:");
    println!("Total Emails: {}", stats.total_emails);
    println!("Success Rate: {:.2}%", stats.success_rate * 100.0);
}