//! Rust Semantic Value Transfer Handlers
//! Handles SMS, email, link, domain, and endpoint semantic transfers

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc, Duration};
use regex::Regex;
use sha2::{Sha256, Digest};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Transfer channels
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TransferChannel {
    #[serde(rename = "sms")]
    Sms,
    #[serde(rename = "email")]
    Email,
    #[serde(rename = "link")]
    Link,
    #[serde(rename = "domain")]
    Domain,
    #[serde(rename = "endpoint")]
    Endpoint,
}

/// Semantic value types
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SemanticType {
    #[serde(rename = "payment")]
    Payment,
    #[serde(rename = "request")]
    Request,
    #[serde(rename = "invoice")]
    Invoice,
    #[serde(rename = "donation")]
    Donation,
    #[serde(rename = "subscription")]
    Subscription,
    #[serde(rename = "reward")]
    Reward,
    #[serde(rename = "refund")]
    Refund,
    #[serde(rename = "escrow")]
    Escrow,
    #[serde(rename = "multi_sig")]
    MultiSig,
    #[serde(rename = "time_locked")]
    TimeLocked,
    #[serde(rename = "conditional")]
    Conditional,
}

/// Semantic value structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SemanticValue {
    pub amount: f64,
    pub currency: String,
    pub semantic_type: SemanticType,
    pub sender: String,
    pub recipient: String,
    pub metadata: HashMap<String, String>,
    pub conditions: Vec<String>,
    pub expires_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}

impl SemanticValue {
    pub fn new(
        amount: f64,
        currency: String,
        semantic_type: SemanticType,
        sender: String,
        recipient: String,
    ) -> Self {
        Self {
            amount,
            currency,
            semantic_type,
            sender,
            recipient,
            metadata: HashMap::new(),
            conditions: Vec::new(),
            expires_at: None,
            created_at: Utc::now(),
        }
    }
}

/// Transfer payload
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransferPayload {
    pub semantic_value: SemanticValue,
    pub channel: TransferChannel,
    pub channel_address: String,
    pub signature: String,
    pub nonce: String,
    pub network_id: String,
    pub gas_limit: u64,
    pub gas_price: f64,
}

impl TransferPayload {
    pub fn new(semantic_value: SemanticValue, channel: TransferChannel, channel_address: String) -> Self {
        Self {
            semantic_value,
            channel,
            channel_address,
            signature: String::new(),
            nonce: Self::generate_nonce(),
            network_id: "membra-mainnet".to_string(),
            gas_limit: 21000,
            gas_price: 0.00001,
        }
    }
    
    fn generate_nonce() -> String {
        let mut hasher = Sha256::new();
        let timestamp = Utc::now().timestamp();
        let random: u64 = rand::random();
        hasher.update(format!("{}{}", timestamp, random).as_bytes());
        format!("{:x}", hasher.finalize())[..16].to_string()
    }
}

/// SMS Handler
pub struct SmsHandler {
    sms_pattern: Regex,
}

impl SmsHandler {
    pub fn new() -> Self {
        // @pay:100.USD:to:+1234567890:for:services:ref:INV-001
        let sms_pattern = Regex::new(r"@(\w+):([\d.]+)\.(\w+):to:([^\s:]+)(?::for:([^\s:]+))?(?::ref:([^\s:]+))?(?::exp:(\d+))?").unwrap();
        Self { sms_pattern }
    }
    
    pub fn parse(&self, sms_text: &str) -> Option<TransferPayload> {
        let captures = self.sms_pattern.captures(sms_text)?;
        
        let action = captures.get(1)?.as_str()?;
        let amount: f64 = captures.get(2)?.as_str()?.parse().ok()?;
        let currency = captures.get(3)?.as_str()?.to_string();
        let recipient = captures.get(4)?.as_str()?.to_string();
        let purpose = captures.get(5).map(|m| m.as_str().to_string());
        let reference = captures.get(6).map(|m| m.as_str().to_string());
        let expiry = captures.get(7).and_then(|m| m.as_str().parse::<i64>().ok());
        
        let mut semantic_value = SemanticValue::new(
            amount,
            currency,
            self.action_to_type(action),
            "unknown".to_string(),
            recipient.clone(),
        );
        
        if let Some(purpose) = purpose {
            semantic_value.metadata.insert("purpose".to_string(), purpose);
        }
        if let Some(reference) = reference {
            semantic_value.metadata.insert("reference".to_string(), reference);
        }
        
        if let Some(expiry_sec) = expiry {
            semantic_value.expires_at = Some(Utc::now() + Duration::seconds(expiry_sec));
        }
        
        Some(TransferPayload::new(semantic_value, TransferChannel::Sms, recipient))
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        let action = self.type_to_action(&payload.semantic_value.semantic_type);
        let purpose = payload.semantic_value.metadata.get("purpose").cloned().unwrap_or_default();
        let reference = payload.semantic_value.metadata.get("reference").cloned().unwrap_or_default();
        
        let mut parts = vec![
            format!("@{}", action),
            format!("{}.{}", payload.semantic_value.amount, payload.semantic_value.currency),
            format!("to:{}", payload.channel_address),
        ];
        
        if !purpose.is_empty() {
            parts.push(format!("for:{}", purpose));
        }
        if !reference.is_empty() {
            parts.push(format!("ref:{}", reference));
        }
        
        parts.join(":")
    }
    
    fn action_to_type(&self, action: &str) -> SemanticType {
        match action.to_lowercase().as_str() {
            "pay" => SemanticType::Payment,
            "request" => SemanticType::Request,
            "invoice" => SemanticType::Invoice,
            "donate" => SemanticType::Donation,
            "sub" => SemanticType::Subscription,
            "reward" => SemanticType::Reward,
            "refund" => SemanticType::Refund,
            "escrow" => SemanticType::Escrow,
            "multisig" => SemanticType::MultiSig,
            "timelock" => SemanticType::TimeLocked,
            "conditional" => SemanticType::Conditional,
            _ => SemanticType::Payment,
        }
    }
    
    fn type_to_action(&self, semantic_type: &SemanticType) -> &'static str {
        match semantic_type {
            SemanticType::Payment => "pay",
            SemanticType::Request => "request",
            SemanticType::Invoice => "invoice",
            SemanticType::Donation => "donate",
            SemanticType::Subscription => "sub",
            SemanticType::Reward => "reward",
            SemanticType::Refund => "refund",
            SemanticType::Escrow => "escrow",
            SemanticType::MultiSig => "multisig",
            SemanticType::TimeLocked => "timelock",
            SemanticType::Conditional => "conditional",
        }
    }
}

/// Email Handler
pub struct EmailHandler {
    email_pattern: Regex,
}

impl EmailHandler {
    pub fn new() -> Self {
        // pay://100.USD/to/+1234567890@domain.com/for/services/ref/INV-001
        let email_pattern = Regex::new(r"(\w+)://([\d.]+)\.(\w+)/to/([^\s/]+)(?:@([^\s/]+))?(?:/for/([^\s/]+))?(?:/ref/([^\s/]+))?(?:/exp/(\d+))?").unwrap();
        Self { email_pattern }
    }
    
    pub fn parse(&self, email_text: &str) -> Option<TransferPayload> {
        let captures = self.email_pattern.captures(email_text)?;
        
        let action = captures.get(1)?.as_str()?;
        let amount: f64 = captures.get(2)?.as_str()?.parse().ok()?;
        let currency = captures.get(3)?.as_str()?.to_string();
        let recipient = captures.get(4)?.as_str()?.to_string();
        let domain = captures.get(5).map(|m| m.as_str().to_string());
        let purpose = captures.get(6).map(|m| m.as_str().to_string());
        let reference = captures.get(7).map(|m| m.as_str().to_string());
        let expiry = captures.get(8).and_then(|m| m.as_str().parse::<i64>().ok());
        
        let mut semantic_value = SemanticValue::new(
            amount,
            currency,
            self.action_to_type(action),
            "unknown".to_string(),
            recipient.clone(),
        );
        
        if let Some(domain) = domain {
            semantic_value.metadata.insert("domain".to_string(), domain.clone());
        }
        if let Some(purpose) = purpose {
            semantic_value.metadata.insert("purpose".to_string(), purpose);
        }
        if let Some(reference) = reference {
            semantic_value.metadata.insert("reference".to_string(), reference);
        }
        
        if let Some(expiry_sec) = expiry {
            semantic_value.expires_at = Some(Utc::now() + Duration::seconds(expiry_sec));
        }
        
        let channel_address = if let Some(domain) = domain {
            format!("{}@{}", recipient, domain)
        } else {
            recipient.clone()
        };
        
        Some(TransferPayload::new(semantic_value, TransferChannel::Email, channel_address))
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        let action = self.type_to_action(&payload.semantic_value.semantic_type);
        let purpose = payload.semantic_value.metadata.get("purpose").cloned().unwrap_or_default();
        let reference = payload.semantic_value.metadata.get("reference").cloned().unwrap_or_default();
        let domain = payload.semantic_value.metadata.get("domain").cloned().unwrap_or_else(|| "membra.io".to_string());
        
        let mut parts = vec![
            format!("{}://", action),
            format!("{}.{}", payload.semantic_value.amount, payload.semantic_value.currency),
            format!("/to/{}", payload.channel_address),
            format!("@{}", domain),
        ];
        
        if !purpose.is_empty() {
            parts.push(format!("/for/{}", purpose));
        }
        if !reference.is_empty() {
            parts.push(format!("/ref/{}", reference));
        }
        
        parts.join("")
    }
    
    fn action_to_type(&self, action: &str) -> SemanticType {
        // Same as SMS handler
        match action.to_lowercase().as_str() {
            "pay" => SemanticType::Payment,
            "request" => SemanticType::Request,
            "invoice" => SemanticType::Invoice,
            "donate" => SemanticType::Donation,
            "sub" => SemanticType::Subscription,
            "reward" => SemanticType::Reward,
            "refund" => SemanticType::Refund,
            "escrow" => SemanticType::Escrow,
            "multisig" => SemanticType::MultiSig,
            "timelock" => SemanticType::TimeLocked,
            "conditional" => SemanticType::Conditional,
            _ => SemanticType::Payment,
        }
    }
    
    fn type_to_action(&self, semantic_type: &SemanticType) -> &'static str {
        // Same as SMS handler
        match semantic_type {
            SemanticType::Payment => "pay",
            SemanticType::Request => "request",
            SemanticType::Invoice => "invoice",
            SemanticType::Donation => "donate",
            SemanticType::Subscription => "sub",
            SemanticType::Reward => "reward",
            SemanticType::Refund => "refund",
            SemanticType::Escrow => "escrow",
            SemanticType::MultiSig => "multisig",
            SemanticType::TimeLocked => "timelock",
            SemanticType::Conditional => "conditional",
        }
    }
}

/// Link Handler
pub struct LinkHandler {
    link_pattern: Regex,
}

impl LinkHandler {
    pub fn new() -> Self {
        // https://pay.membra.io/100/USD/to/+1234567890/for/services/ref/INV-001
        let link_pattern = Regex::new(r"https?://([^.]+)\.membra\.io/([\d.]+)/(\w+)/to/([^\s/]+)(?:/for/([^\s/]+))?(?:/ref/([^\s/]+))?(?:/exp/(\d+))?").unwrap();
        Self { link_pattern }
    }
    
    pub fn parse(&self, link_url: &str) -> Option<TransferPayload> {
        let captures = self.link_pattern.captures(link_url)?;
        
        let subdomain = captures.get(1)?.as_str()?.to_string();
        let amount: f64 = captures.get(2)?.as_str()?.parse().ok()?;
        let currency = captures.get(3)?.as_str()?.to_string();
        let recipient = captures.get(4)?.as_str()?.to_string();
        let purpose = captures.get(5).map(|m| m.as_str().to_string());
        let reference = captures.get(6).map(|m| m.as_str().to_string());
        let expiry = captures.get(7).and_then(|m| m.as_str().parse::<i64>().ok());
        
        let mut semantic_value = SemanticValue::new(
            amount,
            currency,
            SemanticType::Payment, // Links default to payment
            "unknown".to_string(),
            recipient.clone(),
        );
        
        semantic_value.metadata.insert("subdomain".to_string(), subdomain);
        
        if let Some(purpose) = purpose {
            semantic_value.metadata.insert("purpose".to_string(), purpose);
        }
        if let Some(reference) = reference {
            semantic_value.metadata.insert("reference".to_string(), reference);
        }
        
        if let Some(expiry_sec) = expiry {
            semantic_value.expires_at = Some(Utc::now() + Duration::seconds(expiry_sec));
        }
        
        Some(TransferPayload::new(semantic_value, TransferChannel::Link, link_url.to_string()))
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        let subdomain = payload.semantic_value.metadata.get("subdomain").cloned().unwrap_or_else(|| "pay".to_string());
        let purpose = payload.semantic_value.metadata.get("purpose").cloned().unwrap_or_default();
        let reference = payload.semantic_value.metadata.get("reference").cloned().unwrap_or_default();
        
        let mut parts = vec![
            format!("https://{}.membra.io/", subdomain),
            payload.semantic_value.amount.to_string(),
            payload.semantic_value.currency.clone(),
            "to".to_string(),
            payload.channel_address.clone(),
        ];
        
        if !purpose.is_empty() {
            parts.push("for".to_string());
            parts.push(purpose);
        }
        if !reference.is_empty() {
            parts.push("ref".to_string());
            parts.push(reference);
        }
        
        parts.join("/")
    }
}

/// Domain Handler
pub struct DomainHandler {
    domain_pattern: Regex,
}

impl DomainHandler {
    pub fn new() -> Self {
        // 100.USD.pay.membra.io:+1234567890:services:INV-001
        let domain_pattern = Regex::new(r"([\d.]+)\.(\w+)\.([^.]+)\.membra\.io:([^\s:]+)(?::([^\s:]+))?(?::([^\s:]+))?").unwrap();
        Self { domain_pattern }
    }
    
    pub fn parse(&self, domain_text: &str) -> Option<TransferPayload> {
        let captures = self.domain_pattern.captures(domain_text)?;
        
        let amount: f64 = captures.get(1)?.as_str()?.parse().ok()?;
        let currency = captures.get(2)?.as_str()?.to_string();
        let action = captures.get(3)?.as_str()?;
        let recipient = captures.get(4)?.as_str()?.to_string();
        let purpose = captures.get(5).map(|m| m.as_str().to_string());
        let reference = captures.get(6).map(|m| m.as_str().to_string());
        
        let mut semantic_value = SemanticValue::new(
            amount,
            currency,
            self.action_to_type(action),
            "unknown".to_string(),
            recipient.clone(),
        );
        
        if let Some(purpose) = purpose {
            semantic_value.metadata.insert("purpose".to_string(), purpose);
        }
        if let Some(reference) = reference {
            semantic_value.metadata.insert("reference".to_string(), reference);
        }
        
        Some(TransferPayload::new(semantic_value, TransferChannel::Domain, domain_text.to_string()))
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        let action = self.type_to_action(&payload.semantic_value.semantic_type);
        let purpose = payload.semantic_value.metadata.get("purpose").cloned().unwrap_or_default();
        let reference = payload.semantic_value.metadata.get("reference").cloned().unwrap_or_default();
        
        let mut parts = vec![
            format!("{}.{}.{}.membra.io", 
                    payload.semantic_value.amount, 
                    payload.semantic_value.currency, 
                    action),
            payload.channel_address.clone(),
        ];
        
        if !purpose.is_empty() {
            parts.push(purpose);
        }
        if !reference.is_empty() {
            parts.push(reference);
        }
        
        parts.join(":")
    }
    
    fn action_to_type(&self, action: &str) -> SemanticType {
        match action.to_lowercase().as_str() {
            "pay" => SemanticType::Payment,
            "request" => SemanticType::Request,
            "invoice" => SemanticType::Invoice,
            "donate" => SemanticType::Donation,
            "sub" => SemanticType::Subscription,
            "reward" => SemanticType::Reward,
            "refund" => SemanticType::Refund,
            "escrow" => SemanticType::Escrow,
            "multisig" => SemanticType::MultiSig,
            "timelock" => SemanticType::TimeLocked,
            "conditional" => SemanticType::Conditional,
            _ => SemanticType::Payment,
        }
    }
    
    fn type_to_action(&self, semantic_type: &SemanticType) -> &'static str {
        match semantic_type {
            SemanticType::Payment => "pay",
            SemanticType::Request => "request",
            SemanticType::Invoice => "invoice",
            SemanticType::Donation => "donate",
            SemanticType::Subscription => "sub",
            SemanticType::Reward => "reward",
            SemanticType::Refund => "refund",
            SemanticType::Escrow => "escrow",
            SemanticType::MultiSig => "multisig",
            SemanticType::TimeLocked => "timelock",
            SemanticType::Conditional => "conditional",
        }
    }
}

/// Endpoint Handler
pub struct EndpointHandler;

impl EndpointHandler {
    pub fn new() -> Self {
        Self
    }
    
    pub fn parse(&self, endpoint_data: &str) -> Option<TransferPayload> {
        // Try to parse as JSON
        let data: serde_json::Value = serde_json::from_str(endpoint_data).ok()?;
        
        let amount = data.get("amount").and_then(|v| v.as_f64())?;
        let currency = data.get("currency").and_then(|v| v.as_str())?.to_string();
        let semantic_type_str = data.get("type").and_then(|v| v.as_str()).unwrap_or("payment");
        let sender = data.get("from").and_then(|v| v.as_str()).unwrap_or("unknown").to_string();
        let recipient = data.get("to").and_then(|v| v.as_str()).unwrap_or("unknown").to_string();
        let endpoint = data.get("endpoint").and_then(|v| v.as_str()).unwrap_or("/api/v1/transfer").to_string();
        
        let mut semantic_value = SemanticValue::new(
            amount,
            currency,
            self.string_to_type(semantic_type_str),
            sender,
            recipient.clone(),
        );
        
        // Add metadata from other fields
        if let Some(obj) = data.as_object() {
            for (key, value) in obj {
                if !["amount", "currency", "type", "from", "to", "endpoint"].contains(&key.as_str()) {
                    if let Some(str_val) = value.as_str() {
                        semantic_value.metadata.insert(key.clone(), str_val.to_string());
                    }
                }
            }
        }
        
        Some(TransferPayload::new(semantic_value, TransferChannel::Endpoint, endpoint))
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        let mut endpoint_data = serde_json::json!({
            "amount": payload.semantic_value.amount,
            "currency": payload.semantic_value.currency,
            "type": self.type_to_string(&payload.semantic_value.semantic_type),
            "from": payload.semantic_value.sender,
            "to": payload.channel_address,
            "endpoint": payload.channel_address,
            "nonce": payload.nonce,
            "network_id": payload.network_id
        });
        
        // Add metadata
        if let Some(obj) = endpoint_data.as_object_mut() {
            for (key, value) in &payload.semantic_value.metadata {
                obj.insert(key.clone(), serde_json::Value::String(value.clone()));
            }
        }
        
        endpoint_data.to_string()
    }
    
    fn string_to_type(&self, type_str: &str) -> SemanticType {
        match type_str.to_lowercase().as_str() {
            "payment" => SemanticType::Payment,
            "request" => SemanticType::Request,
            "invoice" => SemanticType::Invoice,
            "donation" => SemanticType::Donation,
            "subscription" => SemanticType::Subscription,
            "reward" => SemanticType::Reward,
            "refund" => SemanticType::Refund,
            "escrow" => SemanticType::Escrow,
            "multi_sig" => SemanticType::MultiSig,
            "time_locked" => SemanticType::TimeLocked,
            "conditional" => SemanticType::Conditional,
            _ => SemanticType::Payment,
        }
    }
    
    fn type_to_string(&self, semantic_type: &SemanticType) -> &'static str {
        match semantic_type {
            SemanticType::Payment => "payment",
            SemanticType::Request => "request",
            SemanticType::Invoice => "invoice",
            SemanticType::Donation => "donation",
            SemanticType::Subscription => "subscription",
            SemanticType::Reward => "reward",
            SemanticType::Refund => "refund",
            SemanticType::Escrow => "escrow",
            SemanticType::MultiSig => "multi_sig",
            SemanticType::TimeLocked => "time_locked",
            SemanticType::Conditional => "conditional",
        }
    }
}

/// Unified semantic transfer handler
pub struct SemanticTransferHandler {
    sms_handler: SmsHandler,
    email_handler: EmailHandler,
    link_handler: LinkHandler,
    domain_handler: DomainHandler,
    endpoint_handler: EndpointHandler,
}

impl SemanticTransferHandler {
    pub fn new() -> Self {
        Self {
            sms_handler: SmsHandler::new(),
            email_handler: EmailHandler::new(),
            link_handler: LinkHandler::new(),
            domain_handler: DomainHandler::new(),
            endpoint_handler: EndpointHandler::new(),
        }
    }
    
    pub fn parse(&self, input: &str, channel: TransferChannel) -> Option<TransferPayload> {
        match channel {
            TransferChannel::Sms => self.sms_handler.parse(input),
            TransferChannel::Email => self.email_handler.parse(input),
            TransferChannel::Link => self.link_handler.parse(input),
            TransferChannel::Domain => self.domain_handler.parse(input),
            TransferChannel::Endpoint => self.endpoint_handler.parse(input),
        }
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        match payload.channel {
            TransferChannel::Sms => self.sms_handler.generate(payload),
            TransferChannel::Email => self.email_handler.generate(payload),
            TransferChannel::Link => self.link_handler.generate(payload),
            TransferChannel::Domain => self.domain_handler.generate(payload),
            TransferChannel::Endpoint => self.endpoint_handler.generate(payload),
        }
    }
    
    pub fn auto_detect_channel(&self, input: &str) -> Option<TransferChannel> {
        if input.starts_with('@') && input.contains(':') {
            Some(TransferChannel::Sms)
        } else if input.starts_with("http://") || input.starts_with("https://") {
            if input.contains("membra.io") {
                Some(TransferChannel::Link)
            } else {
                Some(TransferChannel::Endpoint)
            }
        } else if input.contains("://") {
            Some(TransferChannel::Email)
        } else if input.contains(".membra.io:") {
            Some(TransferChannel::Domain)
        } else if input.starts_with('{') {
            Some(TransferChannel::Endpoint)
        } else {
            None
        }
    }
}

impl Default for SemanticTransferHandler {
    fn default() -> Self {
        Self::new()
    }
}

// ============================================================================
// SMART CONTRACT SYSTEM
// ============================================================================

/// Smart contract states
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ContractState {
    #[serde(rename = "deployed")]
    Deployed,
    #[serde(rename = "active")]
    Active,
    #[serde(rename = "paused")]
    Paused,
    #[serde(rename = "terminated")]
    Terminated,
}

/// Smart contract types
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ContractType {
    #[serde(rename = "token")]
    Token,
    #[serde(rename = "payment")]
    Payment,
    #[serde(rename = "escrow")]
    Escrow,
    #[serde(rename = "multi_sig")]
    MultiSig,
    #[serde(rename = "subscription")]
    Subscription,
    #[serde(rename = "reward")]
    Reward,
}

/// Contract call
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractCall {
    pub contract_address: String,
    pub function_name: String,
    pub parameters: serde_json::Value,
    pub caller: String,
    pub gas_limit: u64,
    pub gas_price: f64,
    pub nonce: String,
    pub timestamp: DateTime<Utc>,
}

/// Contract execution result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractResult {
    pub success: bool,
    pub return_value: serde_json::Value,
    pub gas_used: u64,
    pub events: Vec<serde_json::Value>,
    pub error_message: String,
    pub state_changes: serde_json::Value,
}

/// Base smart contract
#[derive(Debug, Clone)]
pub struct SmartContract {
    pub address: String,
    pub contract_type: ContractType,
    pub creator: String,
    pub state: ContractState,
    pub storage: Arc<RwLock<HashMap<String, serde_json::Value>>>,
    pub code_hash: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: Arc<RwLock<DateTime<Utc>>>,
}

impl SmartContract {
    pub fn new(address: String, contract_type: ContractType, creator: String) -> Self {
        let code_hash = Self::calculate_code_hash(&address, &contract_type);
        
        let mut storage = HashMap::new();
        storage.insert("owner".to_string(), serde_json::Value::String(creator.clone()));
        storage.insert("balances".to_string(), serde_json::Value::Object(HashMap::new()));
        storage.insert("allowances".to_string(), serde_json::Value::Object(HashMap::new()));
        storage.insert("total_supply".to_string(), serde_json::Value::Number(0));
        storage.insert("nonce".to_string(), serde_json::Value::Number(0));
        
        Self {
            address,
            contract_type,
            creator,
            state: ContractState::Deployed,
            storage: Arc::new(RwLock::new(storage)),
            code_hash,
            created_at: Utc::now(),
            updated_at: Arc::new(RwLock::new(Utc::now())),
        }
    }
    
    fn calculate_code_hash(address: &str, contract_type: &ContractType) -> String {
        let code = format!("{:?}{:?}", address, contract_type);
        let mut hasher = Sha256::new();
        hasher.update(code.as_bytes());
        format!("{:x}", hasher.finalize())
    }
    
    pub async fn execute(&self, call: ContractCall) -> ContractResult {
        if self.state != ContractState::Active {
            return ContractResult {
                success: false,
                return_value: serde_json::Value::Null,
                gas_used: 0,
                events: vec![],
                error_message: format!("Contract not active. Current state: {:?}", self.state),
                state_changes: serde_json::Value::Null,
            };
        }
        
        // Simulate function execution
        let return_value = match call.function_name.as_str() {
            "transfer" => self.execute_transfer(&call.parameters).await,
            "balance_of" => self.execute_balance_of(&call.parameters).await,
            "approve" => self.execute_approve(&call.parameters).await,
            "process_payment" => self.execute_process_payment(&call.parameters).await,
            "create_escrow" => self.execute_create_escrow(&call.parameters).await,
            "submit_proposal" => self.execute_submit_proposal(&call.parameters).await,
            "create_subscription" => self.execute_create_subscription(&call.parameters).await,
            _ => serde_json::Value::String("Unknown function".to_string()),
        };
        
        let gas_used = call.gas_limit;
        let events = vec![self.generate_event(&call.function_name, &call.parameters, &return_value)];
        
        // Update state
        let mut storage = self.storage.write().await;
        if let Some(nonce) = storage.get_mut("nonce") {
            if let serde_json::Value::Number(n) = nonce {
                *nonce = serde_json::Value::Number(n.as_i64().unwrap_or(0) + 1);
            }
        }
        let mut updated_at = self.updated_at.write().await;
        *updated_at = Utc::now();
        
        ContractResult {
            success: true,
            return_value,
            gas_used,
            events,
            error_message: String::new(),
            state_changes: serde_json::json!({"nonce": storage.get("nonce")}),
        }
    }
    
    async fn execute_transfer(&self, params: &serde_json::Value) -> serde_json::Value {
        let to = params["to"].as_str().unwrap_or("unknown");
        let amount = params["amount"].as_f64().unwrap_or(0.0);
        
        let mut storage = self.storage.write().await;
        
        // Simple transfer logic
        let balances = storage.get_mut("balances").unwrap().as_object_mut().unwrap();
        let from_balance = balances.get(self.creator).unwrap_or(&serde_json::Value::Number(0)).as_f64().unwrap_or(0.0);
        
        if from_balance < amount {
            return serde_json::json!({"error": "Insufficient balance"});
        }
        
        let to_balance = balances.get(to).unwrap_or(&serde_json::Value::Number(0)).as_f64().unwrap_or(0.0);
        
        balances.insert(self.creator.clone(), serde_json::Value::Number(from_balance - amount));
        balances.insert(to.to_string(), serde_json::Value::Number(to_balance + amount));
        
        serde_json::json!({"success": true, "from_balance": from_balance - amount, "to_balance": to_balance + amount})
    }
    
    async fn execute_balance_of(&self, params: &serde_json::Value) -> serde_json::Value {
        let account = params["account"].as_str().unwrap_or("unknown");
        
        let storage = self.storage.read().await;
        let balances = storage.get("balances").unwrap().as_object().unwrap();
        let balance = balances.get(account).unwrap_or(&serde_json::Value::Number(0)).as_f64().unwrap_or(0.0);
        
        serde_json::json!({"balance": balance})
    }
    
    async fn execute_approve(&self, params: &serde_json::Value) -> serde_json::Value {
        let spender = params["spender"].as_str().unwrap_or("unknown");
        let amount = params["amount"].as_f64().unwrap_or(0.0);
        
        let mut storage = self.storage.write().await;
        let allowances = storage.get_mut("allowances").unwrap().as_object_mut().unwrap();
        
        let owner_allowances = allowances.entry(self.creator.clone()).or_insert_with(HashMap::new);
        owner_allowances.insert(spender.to_string(), serde_json::Value::Number(amount));
        
        serde_json::json!({"success": true, "spender": spender, "amount": amount})
    }
    
    async fn execute_process_payment(&self, params: &serde_json::Value) -> serde_json::Value {
        let payload: TransferPayload = serde_json::from_value(params["payload"].clone()).unwrap();
        
        if payload.semantic_value.amount <= 0.0 {
            return serde_json::json!({"error": "Invalid amount"});
        }
        
        if let Some(expires_at) = payload.semantic_value.expires_at {
            if expires_at < Utc::now() {
                return serde_json::json!({"error": "Payment expired"});
            }
        }
        
        let mut storage = self.storage.write().await;
        let payment_count = storage.get("payment_count").unwrap_or(&serde_json::Value::Number(0)).as_i64().unwrap_or(0);
        let total_volume = storage.get("total_volume").unwrap_or(&serde_json::Value::Number(0.0)).as_f64().unwrap_or(0.0);
        
        storage.insert("payment_count".to_string(), serde_json::Value::Number(payment_count + 1));
        storage.insert("total_volume".to_string(), serde_json::Value::Number(total_volume + payload.semantic_value.amount));
        
        serde_json::json!({"success": true, "payment_count": payment_count + 1})
    }
    
    async fn execute_create_escrow(&self, params: &serde_json::Value) -> serde_json::Value {
        let payload: TransferPayload = serde_json::from_value(params["payload"].clone()).unwrap();
        let conditions: Vec<String> = serde_json::from_value(params["conditions"].clone()).unwrap_or_default();
        
        let mut storage = self.storage.write().await;
        let escrow_count = storage.get("escrow_count").unwrap_or(&serde_json::Value::Number(0)).as_i64().unwrap_or(0);
        
        let escrow_id = format!("escrow_{}", escrow_count + 1);
        
        let escrow_data = serde_json::json!({
            "payload": payload.to_dict(),
            "conditions": conditions,
            "status": "pending",
            "created_at": Utc::now().to_rfc3339(),
            "released_at": serde_json::Value::Null,
            "refunded_at": serde_json::Value::Null
        });
        
        let escrows = storage.entry("escrows".to_string()).or_insert_with(serde_json::Value::Object);
        if let Some(escrows_map) = escrows.as_object_mut() {
            escrows_map.insert(escrow_id.clone(), escrow_data);
        }
        
        storage.insert("escrow_count".to_string(), serde_json::Value::Number(escrow_count + 1));
        
        serde_json::json!({"success": true, "escrow_id": escrow_id})
    }
    
    async fn execute_submit_proposal(&self, params: &serde_json::Value) -> serde_json::Value {
        let payload: TransferPayload = serde_json::from_value(params["payload"].clone()).unwrap();
        let proposer = params["proposer"].as_str().unwrap_or("unknown");
        
        let mut storage = self.storage.write().await;
        let proposal_count = storage.get("proposal_count").unwrap_or(&serde_json::Value::Number(0)).as_i64().unwrap_or(0);
        
        let proposal_id = format!("proposal_{}", proposal_count + 1);
        
        let proposal_data = serde_json::json!({
            "payload": payload.to_dict(),
            "proposer": proposer,
            "approvals": vec![],
            "executed": false,
            "created_at": Utc::now().to_rfc3339()
        });
        
        let proposals = storage.entry("proposals".to_string()).or_insert_with(serde_json::Value::Object);
        if let Some(proposals_map) = proposals.as_object_mut() {
            proposals_map.insert(proposal_id.clone(), proposal_data);
        }
        
        storage.insert("proposal_count".to_string(), serde_json::Value::Number(proposal_count + 1));
        
        serde_json::json!({"success": true, "proposal_id": proposal_id})
    }
    
    async fn execute_create_subscription(&self, params: &serde_json::Value) -> serde_json::Value {
        let subscriber = params["subscriber"].as_str().unwrap_or("unknown");
        let amount = params["amount"].as_f64().unwrap_or(0.0);
        let interval_days = params["interval_days"].as_i64().unwrap_or(30);
        
        let mut storage = self.storage.write().await;
        let sub_count = storage.get("subscription_count").unwrap_or(&serde_json::Value::Number(0)).as_i64().unwrap_or(0);
        
        let subscription_id = format!("sub_{}", sub_count + 1);
        
        let subscription_data = serde_json::json!({
            "subscriber": subscriber,
            "amount": amount,
            "interval_days": interval_days,
            "next_payment": (Utc::now() + Duration::days(interval_days)).to_rfc3339(),
            "active": true,
            "created_at": Utc::now().to_rfc3339()
        });
        
        let subscriptions = storage.entry("subscriptions".to_string()).or_insert_with(serde_json::Value::Object);
        if let Some(subs_map) = subscriptions.as_object_mut() {
            subs_map.insert(subscription_id.clone(), subscription_data);
        }
        
        storage.insert("subscription_count".to_string(), serde_json::Value::Number(sub_count + 1));
        
        serde_json::json!({"success": true, "subscription_id": subscription_id})
    }
    
    fn generate_event(&self, function_name: &str, parameters: &serde_json::Value, result: &serde_json::Value) -> serde_json::Value {
        serde_json::json!({
            "event_type": format!("{}::{}", self.contract_type, function_name),
            "contract_address": self.address,
            "timestamp": Utc::now().to_rfc3339(),
            "parameters": parameters,
            "result": result
        })
    }
}

/// Custom network for managing smart contracts
pub struct CustomNetwork {
    pub network_id: String,
    pub contracts: Arc<RwLock<HashMap<String, SmartContract>>>,
    pub block_number: Arc<RwLock<u64>>,
    pub transaction_count: Arc<RwLock<u64>>,
    pub semantic_handler: SemanticTransferHandler,
}

impl CustomNetwork {
    pub fn new(network_id: String) -> Self {
        Self {
            network_id,
            contracts: Arc::new(RwLock::new(HashMap::new())),
            block_number: Arc::new(RwLock::new(0)),
            transaction_count: Arc::new(RwLock::new(0)),
            semantic_handler: SemanticTransferHandler::new(),
        }
    }
    
    pub async fn deploy_contract(&self, contract: SmartContract) -> String {
        let address = contract.address.clone();
        contract.state = ContractState::Active;
        
        let mut contracts = self.contracts.write().await;
        contracts.insert(address.clone(), contract);
        
        let mut block_number = self.block_number.write().await;
        *block_number += 1;
        
        address
    }
    
    pub async fn execute_contract(&self, call: ContractCall) -> ContractResult {
        let contracts = self.contracts.read().await;
        let contract = contracts.get(&call.contract_address);
        
        match contract {
            Some(contract) => {
                let result = contract.execute(call).await;
                if result.success {
                    let mut tx_count = self.transaction_count.write().await;
                    *tx_count += 1;
                }
                result
            }
            None => ContractResult {
                success: false,
                return_value: serde_json::Value::Null,
                gas_used: 0,
                events: vec![],
                error_message: "Contract not found".to_string(),
                state_changes: serde_json::Value::Null,
            }
        }
    }
    
    pub async fn process_semantic_transfer(&self, payload: TransferPayload) -> ContractResult {
        match payload.semantic_value.semantic_type {
            SemanticType::Payment => self._process_payment(payload).await,
            SemanticType::Escrow => self._process_escrow(payload).await,
            SemanticType::MultiSig => self._process_multi_sig(payload).await,
            SemanticType::Subscription => self._process_subscription(payload).await,
            _ => self._process_generic_transfer(payload).await,
        }
    }
    
    async fn _process_payment(&self, payload: TransferPayload) -> ContractResult {
        let payment_contract = self._get_or_create_payment_contract().await;
        
        let call = ContractCall {
            contract_address: payment_contract.address,
            function_name: "process_payment".to_string(),
            parameters: serde_json::json!({"payload": payload.to_dict()}),
            caller: payload.semantic_value.sender.clone(),
            gas_limit: 21000,
            gas_price: 0.00001,
            nonce: payload.nonce.clone(),
            timestamp: Utc::now(),
        };
        
        self.execute_contract(call).await
    }
    
    async fn _process_escrow(&self, payload: TransferPayload) -> ContractResult {
        let escrow_contract = self._get_or_create_escrow_contract().await;
        
        let call = ContractCall {
            contract_address: escrow_contract.address,
            function_name: "create_escrow".to_string(),
            parameters: serde_json::json!({
                "payload": payload.to_dict(),
                "conditions": payload.semantic_value.conditions
            }),
            caller: payload.semantic_value.sender.clone(),
            gas_limit: 21000,
            gas_price: 0.00001,
            nonce: payload.nonce.clone(),
            timestamp: Utc::now(),
        };
        
        self.execute_contract(call).await
    }
    
    async fn _process_multi_sig(&self, payload: TransferPayload) -> ContractResult {
        let multi_sig_contract = self._get_or_create_multi_sig_contract().await;
        
        let call = ContractCall {
            contract_address: multi_sig_contract.address,
            function_name: "submit_proposal".to_string(),
            parameters: serde_json::json!({
                "payload": payload.to_dict(),
                "proposer": payload.semantic_value.sender
            }),
            caller: payload.semantic_value.sender.clone(),
            gas_limit: 21000,
            gas_price: 0.01,
            nonce: payload.nonce.clone(),
            timestamp: Utc::now(),
        };
        
        self.execute_contract(call).await
    }
    
    async fn _process_subscription(&self, payload: TransferPayload) -> ContractResult {
        let subscription_contract = self._get_or_create_subscription_contract().await;
        
        let call = ContractCall {
            contract_address: subscription_contract.address,
            function_name: "create_subscription".to_string(),
            parameters: serde_json::json!({
                "subscriber": payload.semantic_value.recipient,
                "amount": payload.semantic_value.amount,
                "interval_days": 30
            }),
            caller: payload.semantic_value.sender.clone(),
            gas_limit: 21000,
            gas_price: 0.00001,
            nonce: payload.nonce.clone(),
            timestamp: Utc::now(),
        };
        
        self.execute_contract(call).await
    }
    
    async fn _process_generic_transfer(&self, payload: TransferPayload) -> ContractResult {
        let token_contract = self._get_or_create_token_contract().await;
        
        let call = ContractCall {
            contract_address: token_contract.address,
            function_name: "transfer".to_string(),
            parameters: serde_json::json!({
                "to": payload.semantic_value.recipient,
                "amount": payload.semantic_value.amount
            }),
            caller: payload.semantic_value.sender.clone(),
            gas_limit: 21000,
            gas_price: 0.00001,
            nonce: payload.nonce.clone(),
            timestamp: Utc::now(),
        };
        
        self.execute_contract(call).await
    }
    
    async fn _get_or_create_payment_contract(&self) -> SmartContract {
        let contracts = self.contracts.read().await;
        if let Some(contract) = contracts.get("payment_contract_001") {
            return contract.clone();
        }
        
        let token_contract = self._get_or_create_token_contract().await;
        let contract = SmartContract::new(
            "payment_contract_001".to_string(),
            ContractType::Payment,
            "network".to_string(),
        );
        self.deploy_contract(contract).await;
        contract
    }
    
    async fn _get_or_create_escrow_contract(&self) -> SmartContract {
        let contracts = self.contracts.read().await;
        if let Some(contract) = contracts.get("escrow_contract_001") {
            return contract.clone();
        }
        
        let contract = SmartContract::new(
            "escrow_contract_001".to_string(),
            ContractType::Escrow,
            "network".to_string(),
        );
        self.deploy_contract(contract).await;
        contract
    }
    
    async fn _get_or_create_multi_sig_contract(&self) -> SmartContract {
        let contracts = self.contracts.read().await;
        if let Some(contract) = contracts.get("multisig_contract_001") {
            return contract.clone();
        }
        
        let contract = SmartContract::new(
            "multisig_contract_001".to_string(),
            ContractType::MultiSig,
            "network".to_string(),
        );
        self.deploy_contract(contract).await;
        contract
    }
    
    async fn _get_or_create_subscription_contract(&self) -> SmartContract {
        let contracts = self.contracts.read().await;
        if let Some(contract) = contracts.get("subscription_contract_001") {
            return contract.clone();
        }
        
        let contract = SmartContract::new(
            "subscription_contract_001".to_string(),
            ContractType::Subscription,
            "network".to_string(),
        );
        self.deploy_contract(contract).await;
        contract
    }
    
    async fn _get_or_create_token_contract(&self) -> SmartContract {
        let contracts = self.contracts.read().await;
        if let Some(contract) = contracts.get("token_contract_001") {
            return contract.clone();
        }
        
        let contract = SmartContract::new(
            "token_contract_001".to_string(),
            ContractType::Token,
            "network".to_string(),
        );
        
        // Initialize with initial supply
        let mut storage = contract.storage.write().await;
        storage.insert("name".to_string(), serde_json::Value::String("Membra Token".to_string()));
        storage.insert("symbol".to_string(), serde_json::Value::String("MEMBRA".to_string()));
        storage.insert("decimals".to_string(), serde_json::Value::Number(18));
        storage.insert("total_supply".to_string(), serde_json::Value::Number(1000000000));
        
        let balances = storage.get_mut("balances").unwrap().as_object_mut().unwrap();
        balances.insert("network".to_string(), serde_json::Value::Number(1000000000));
        
        self.deploy_contract(contract).await;
        contract
    }
    
    pub async fn get_network_status(&self) -> serde_json::Value {
        let contracts = self.contracts.read().await;
        let block_number = *self.block_number.read().await;
        let transaction_count = *self.transaction_count.read().await;
        
        let contract_info: HashMap<String, serde_json::Value> = contracts
            .iter()
            .map(|(addr, contract)| {
                (
                    addr.clone(),
                    serde_json::json!({
                        "type": contract.contract_type,
                        "state": contract.state,
                        "creator": contract.creator,
                        "created_at": contract.created_at.to_rfc3339()
                    })
                )
            })
            .collect();
        
        serde_json::json!({
            "network_id": self.network_id,
            "block_number": block_number,
            "transaction_count": transaction_count,
            "contract_count": contracts.len(),
            "contracts": contract_info
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_sms_parsing() {
        let handler = SemanticTransferHandler::new();
        let sms = "@pay:100.USD:to:+1234567890:for:services:ref:INV-001";
        
        let payload = handler.parse(sms, TransferChannel::Sms).unwrap();
        assert_eq!(payload.semantic_value.amount, 100.0);
        assert_eq!(payload.semantic_value.currency, "USD");
        assert_eq!(payload.channel, TransferChannel::Sms);
    }
    
    #[test]
    fn test_sms_generation() {
        let handler = SemanticTransferHandler::new();
        
        let mut semantic_value = SemanticValue::new(100.0, "USD".to_string(), SemanticType::Payment, "sender".to_string(), "+1234567890".to_string());
        semantic_value.metadata.insert("purpose".to_string(), "services".to_string());
        semantic_value.metadata.insert("reference".to_string(), "INV-001".to_string());
        
        let payload = TransferPayload::new(semantic_value, TransferChannel::Sms, "+1234567890".to_string());
        let generated = handler.generate(&payload);
        
        assert!(generated.contains("@pay:100.USD"));
        assert!(generated.contains("to:+1234567890"));
    }
    
    #[test]
    fn test_auto_detection() {
        let handler = SemanticTransferHandler::new();
        
        assert_eq!(handler.auto_detect_channel("@pay:100.USD:to:+1234567890"), Some(TransferChannel::Sms));
        assert_eq!(handler.auto_detect_channel("https://pay.membra.io/100/USD/to/+1234567890"), Some(TransferChannel::Link));
        assert_eq!(handler.auto_detect_channel("pay://100.USD/to/+1234567890@membra.io"), Some(TransferChannel::Email));
    }
}