//! Rust LLM Unified Orchestration System
//! Coordinates all custom LLM-based systems

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::env;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::RwLock;
use tracing::{debug, error, info, warn};

use crate::sms_processor::LlmSmsProcessor;
use crate::email_system::LlmCustomEmailSystem;
use crate::blockchain::CustomBlockchain;
use crate::bridge::CustomMembraBridge;

/// Orchestration event types
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum OrchestrationEventType {
    UserAction,
    SystemEvent,
    TransactionEvent,
    BridgeEvent,
    AlertEvent,
    ComplianceEvent,
}

/// Orchestration event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrchestrationEvent {
    pub event_id: String,
    pub event_type: OrchestrationEventType,
    pub source: String,
    pub data: HashMap<String, String>,
    pub timestamp: DateTime<Utc>,
    pub priority: String,
    pub status: String,
    pub processed_by: Vec<String>,
    pub results: HashMap<String, serde_json::Value>,
}

impl OrchestrationEvent {
    pub fn new(
        event_type: OrchestrationEventType,
        source: String,
        data: HashMap<String, String>,
        priority: String,
    ) -> Self {
        let event_id = Self::generate_event_id(&event_type, &source);
        Self {
            event_id,
            event_type,
            source,
            data,
            timestamp: Utc::now(),
            priority,
            status: "pending".to_string(),
            processed_by: vec![],
            results: HashMap::new(),
        }
    }

    fn generate_event_id(event_type: &OrchestrationEventType, source: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(format!("{:?}{}{}", event_type, source, Utc::now().timestamp()));
        hex::encode(hasher.finalize())
    }
}

/// Orchestration action
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrchestrationAction {
    pub system: String,
    pub action: String,
    pub priority: String,
    pub parameters: HashMap<String, String>,
    pub reasoning: String,
}

/// Orchestration plan
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrchestrationPlan {
    pub recommended_actions: Vec<OrchestrationAction>,
    pub execution_order: Vec<u32>,
    pub total_cost_estimate: f64,
    pub estimated_time_seconds: u64,
    pub risk_assessment: String,
    pub requires_manual_approval: bool,
    pub optimization_suggestions: Vec<String>,
}

/// LLM orchestrator
pub struct LlmOrchestrator {
    openai_api_key: Option<String>,
    llm_client: Option<Client>,
    sms_system: Arc<LlmSmsProcessor>,
    email_system: Arc<RwLock<LlmCustomEmailSystem>>,
    blockchain: Arc<CustomBlockchain>,
    bridge: Arc<CustomMembraBridge>,
    events: Arc<RwLock<HashMap<String, OrchestrationEvent>>>,
    system_status: Arc<RwLock<HashMap<String, String>>>,
}

impl LlmOrchestrator {
    pub fn new(openai_api_key: Option<String>) -> Self {
        let llm_client = if openai_api_key.is_some() {
            Some(
                Client::builder()
                    .timeout(Duration::from_secs(30))
                    .build()
                    .expect("Failed to create HTTP client"),
            )
        } else {
            None
        };

        let mut system_status = HashMap::new();
        system_status.insert("sms".to_string(), "operational".to_string());
        system_status.insert("email".to_string(), "operational".to_string());
        system_status.insert("blockchain".to_string(), "operational".to_string());
        system_status.insert("bridge".to_string(), "operational".to_string());
        system_status.insert("orchestrator".to_string(), "operational".to_string());

        Self {
            openai_api_key,
            llm_client,
            sms_system: Arc::new(LlmSmsProcessor::new(openai_api_key.clone())),
            email_system: Arc::new(RwLock::new(LlmCustomEmailSystem::new(openai_api_key.clone()))),
            blockchain: Arc::new(CustomBlockchain::new(openai_api_key.clone(), "overmanifold-1".to_string())),
            bridge: Arc::new(CustomMembraBridge::new(openai_api_key.clone())),
            events: Arc::new(RwLock::new(HashMap::new())),
            system_status: Arc::new(RwLock::new(system_status)),
        }
    }

    pub fn from_env() -> Self {
        Self::new(env::var("OPENAI_API_KEY").ok())
    }

    pub async fn initialize(&self) -> Result<()> {
        self.blockchain.initialize().await?;
        self.bridge.initialize().await?;
        info!("Orchestrator initialized with all subsystems");
        Ok(())
    }

    /// Orchestrate an event across all systems
    pub async fn orchestrate_event(&self, event: OrchestrationEvent) -> Result<OrchestrationResult> {
        // Store event
        {
            let mut events = self.events.write().await;
            let mut event_clone = event.clone();
            event_clone.status = "processing".to_string();
            events.insert(event_clone.event_id.clone(), event_clone);
        }

        // Create orchestration plan
        let plan = self.create_orchestration_plan(&event).await?;

        if plan.recommended_actions.is_empty() {
            return Ok(OrchestrationResult {
                success: false,
                event_id: event.event_id.clone(),
                status: "no_actions".to_string(),
                orchestration_plan: plan,
                execution_results: vec![],
            });
        }

        // Execute plan
        let execution_results = self.execute_orchestration_plan(&event, &plan).await;

        // Update event status
        let all_success = execution_results.iter().all(|r| r.success);
        let status = if all_success {
            "completed".to_string()
        } else {
            "partial".to_string()
        };

        {
            let mut events = self.events.write().await;
            if let Some(e) = events.get_mut(&event.event_id) {
                e.status = status.clone();
                e.processed_by = execution_results.iter().map(|r| r.system.clone()).collect();
                e.results = execution_results.iter()
                    .map(|r| (r.system.clone(), serde_json::to_value(r).unwrap_or_default()))
                    .collect();
            }
        }

        Ok(OrchestrationResult {
            success: true,
            event_id: event.event_id.clone(),
            status,
            orchestration_plan: plan,
            execution_results,
        })
    }

    async fn create_orchestration_plan(&self, event: &OrchestrationEvent) -> Result<OrchestrationPlan> {
        if let Some(ref client) = self.llm_client {
            if let Some(ref api_key) = self.openai_api_key {
                return self.create_plan_with_llm(event, client, api_key).await;
            }
        }
        Ok(self.create_fallback_plan(event))
    }

    async fn create_plan_with_llm(
        &self,
        event: &OrchestrationEvent,
        client: &Client,
        api_key: &str,
    ) -> Result<OrchestrationPlan> {
        let system_status = self.system_status.read().await;
        
        let context = serde_json::json!({
            "event_type": event.event_type,
            "source": event.source,
            "priority": event.priority,
            "data": event.data,
            "system_status": *system_status,
            "timestamp": event.timestamp.to_rfc3339()
        });

        let response = client
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
                        "content": format!("Event: {}", context)
                    }
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }))
            .send()
            .await?;

        if !response.status().is_success() {
            let error_text = response.text().await?;
            error!("LLM orchestration failed: {}", error_text);
            return Ok(self.create_fallback_plan(event));
        }

        let response_json: serde_json::Value = response.json().await?;
        let content = response_json["choices"][0]["message"]["content"]
            .as_str()
            .context("Missing content in response")?;

        let result: serde_json::Value = serde_json::from_str(content)?;
        Ok(self.parse_orchestration_plan(result)?)
    }

    fn create_fallback_plan(&self, event: &OrchestrationEvent) -> OrchestrationPlan {
        let mut actions = vec![];

        match event.event_type {
            OrchestrationEventType::UserAction => {
                if let Some(action) = event.data.get("action") {
                    match action.as_str() {
                        "register" => {
                            if let Some(phone) = event.data.get("phone") {
                                actions.push(OrchestrationAction {
                                    system: "sms".to_string(),
                                    action: "send_verification".to_string(),
                                    priority: "high".to_string(),
                                    parameters: vec![("phone".to_string(), phone.clone())].into_iter().collect(),
                                    reasoning: "User registration requires SMS verification".to_string(),
                                });
                            }
                            if let Some(email) = event.data.get("email") {
                                actions.push(OrchestrationAction {
                                    system: "email".to_string(),
                                    action: "send_welcome".to_string(),
                                    priority: "medium".to_string(),
                                    parameters: vec![("email".to_string(), email.clone())].into_iter().collect(),
                                    reasoning: "Welcome email for new user".to_string(),
                                });
                            }
                        }
                        "payment" => {
                            actions.push(OrchestrationAction {
                                system: "blockchain".to_string(),
                                action: "process_transaction".to_string(),
                                priority: "high".to_string(),
                                parameters: event.data.clone(),
                                reasoning: "Process payment transaction".to_string(),
                            });
                            if let Some(phone) = event.data.get("phone") {
                                actions.push(OrchestrationAction {
                                    system: "sms".to_string(),
                                    action: "send_notification".to_string(),
                                    priority: "medium".to_string(),
                                    parameters: vec![("phone".to_string(), phone.clone())].into_iter().collect(),
                                    reasoning: "Notify user of payment".to_string(),
                                });
                            }
                        }
                        _ => {}
                    }
                }
            }
            OrchestrationEventType::TransactionEvent => {
                actions.push(OrchestrationAction {
                    system: "blockchain".to_string(),
                    action: "record_transaction".to_string(),
                    priority: "high".to_string(),
                    parameters: event.data.clone(),
                    reasoning: "Record transaction on blockchain".to_string(),
                });
                if let Some(email) = event.data.get("email") {
                    actions.push(OrchestrationAction {
                        system: "email".to_string(),
                        action: "send_receipt".to_string(),
                        priority: "medium".to_string(),
                        parameters: vec![("email".to_string(), email.clone())].into_iter().collect(),
                        reasoning: "Send transaction receipt".to_string(),
                    });
                }
            }
            _ => {}
        }

        let execution_order: Vec<u32> = (1..=actions.len() as u32).collect();

        OrchestrationPlan {
            recommended_actions: actions,
            execution_order,
            total_cost_estimate: 0.0,
            estimated_time_seconds: 60,
            risk_assessment: "low".to_string(),
            requires_manual_approval: false,
            optimization_suggestions: vec![],
        }
    }

    fn get_system_prompt(&self) -> &'static str {
        r#"You are the orchestration system for Overmanifold Protocol. Coordinate all systems (SMS, Email, Blockchain, Bridge) for optimal operation.

ORCHESTRATION FORMAT:
Return JSON with this exact structure:
{
  "recommended_actions": [
    {
      "system": "sms|email|blockchain|bridge",
      "action": "specific_action",
      "priority": "low|medium|high|urgent",
      "parameters": {},
      "reasoning": "explain why this action"
    }
  ],
  "execution_order": [1, 2, 3],
  "total_cost_estimate": 0.0,
  "estimated_time_seconds": 0,
  "risk_assessment": "low|medium|high",
  "requires_manual_approval": false|true,
  "optimization_suggestions": ["suggestion1", "suggestion2"]
}"#
    }

    fn parse_orchestration_plan(&self, response: serde_json::Value) -> Result<OrchestrationPlan> {
        let recommended_actions: Vec<OrchestrationAction> = response["recommended_actions"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| {
                        Some(OrchestrationAction {
                            system: v["system"].as_str()?.to_string(),
                            action: v["action"].as_str()?.to_string(),
                            priority: v["priority"].as_str()?.to_string(),
                            parameters: v["parameters"]
                                .as_object()?
                                .iter()
                                .filter_map(|(k, val)| val.as_str().map(|s| (k.clone(), s.to_string())))
                                .collect(),
                            reasoning: v["reasoning"].as_str()?.to_string(),
                        })
                    })
                    .collect()
            })
            .unwrap_or_default();

        let execution_order: Vec<u32> = response["execution_order"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_u64().map(|u| u as u32))
                    .collect()
            })
            .unwrap_or_default();

        let optimization_suggestions: Vec<String> = response["optimization_suggestions"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect()
            })
            .unwrap_or_default();

        Ok(OrchestrationPlan {
            recommended_actions,
            execution_order,
            total_cost_estimate: response["total_cost_estimate"].as_f64().unwrap_or(0.0),
            estimated_time_seconds: response["estimated_time_seconds"].as_u64().unwrap_or(60),
            risk_assessment: response["risk_assessment"]
                .as_str()
                .unwrap_or("low")
                .to_string(),
            requires_manual_approval: response["requires_manual_approval"].as_bool().unwrap_or(false),
            optimization_suggestions,
        })
    }

    async fn execute_orchestration_plan(
        &self,
        event: &OrchestrationEvent,
        plan: &OrchestrationPlan,
    ) -> Vec<ActionExecutionResult> {
        let mut results = vec![];

        let mut sorted_actions: Vec<(u32, &OrchestrationAction)> = plan
            .recommended_actions
            .iter()
            .zip(plan.execution_order.iter())
            .map(|(action, &order)| (order, action))
            .collect();
        sorted_actions.sort_by_key(|(order, _)| *order);

        for (order, action) in sorted_actions {
            let result = self.execute_system_action(action).await;
            debug!("Executed {}: {} (success: {})", action.system, action.action, result.success);
            results.push(result);
        }

        results
    }

    async fn execute_system_action(&self, action: &OrchestrationAction) -> ActionExecutionResult {
        match action.system.as_str() {
            "sms" => self.execute_sms_action(action).await,
            "email" => self.execute_email_action(action).await,
            "blockchain" => self.execute_blockchain_action(action).await,
            "bridge" => self.execute_bridge_action(action).await,
            _ => ActionExecutionResult {
                system: action.system.clone(),
                action: action.action.clone(),
                success: false,
                error: Some(format!("Unknown system: {}", action.system)),
                result: None,
            },
        }
    }

    async fn execute_sms_action(&self, action: &OrchestrationAction) -> ActionExecutionResult {
        match action.action.as_str() {
            "send_verification" => {
                let phone = action.parameters.get("phone").unwrap_or(&String::new());
                match self.sms_system.generate_verification_code(phone).await {
                    Ok(code) => {
                        match self.sms_system.send_sms(phone, &format!("Your verification code is: {}", code)).await {
                            Ok(success) => ActionExecutionResult {
                                system: "sms".to_string(),
                                action: action.action.clone(),
                                success,
                                error: None,
                                result: Some(serde_json::json!({"code": code, "phone": phone})),
                            },
                            Err(e) => ActionExecutionResult {
                                system: "sms".to_string(),
                                action: action.action.clone(),
                                success: false,
                                error: Some(e.to_string()),
                                result: None,
                            },
                        }
                    }
                    Err(e) => ActionExecutionResult {
                        system: "sms".to_string(),
                        action: action.action.clone(),
                        success: false,
                        error: Some(e.to_string()),
                        result: None,
                    },
                }
            }
            "send_notification" => {
                let phone = action.parameters.get("phone").unwrap_or(&String::new());
                let message = action.parameters.get("message").unwrap_or(&"Transaction completed".to_string());
                match self.sms_system.send_sms(phone, message).await {
                    Ok(success) => ActionExecutionResult {
                        system: "sms".to_string(),
                        action: action.action.clone(),
                        success,
                        error: None,
                        result: Some(serde_json::json!({"phone": phone})),
                    },
                    Err(e) => ActionExecutionResult {
                        system: "sms".to_string(),
                        action: action.action.clone(),
                        success: false,
                        error: Some(e.to_string()),
                        result: None,
                    },
                }
            }
            _ => ActionExecutionResult {
                system: "sms".to_string(),
                action: action.action.clone(),
                success: false,
                error: Some("Unknown SMS action".to_string()),
                result: None,
            },
        }
    }

    async fn execute_email_action(&self, action: &OrchestrationAction) -> ActionExecutionResult {
        match action.action.as_str() {
            "send_welcome" => {
                let email = action.parameters.get("email").unwrap_or(&String::new());
                let mut email_system = self.email_system.write().await;
                match email_system.send_custom_email(
                    email,
                    "Welcome to Overmanifold Protocol",
                    "Welcome to Overmanifold Protocol! Your account has been created successfully.",
                    "<html><body><h1>Welcome!</h1><p>Your account has been created successfully.</p></body></html>",
                    None,
                ).await {
                    Ok(result) => ActionExecutionResult {
                        system: "email".to_string(),
                        action: action.action.clone(),
                        success: result.success,
                        error: if result.success { None } else { Some(result.error_message) },
                        result: Some(serde_json::json!({"email": email})),
                    },
                    Err(e) => ActionExecutionResult {
                        system: "email".to_string(),
                        action: action.action.clone(),
                        success: false,
                        error: Some(e.to_string()),
                        result: None,
                    },
                }
            }
            "send_receipt" => {
                let email = action.parameters.get("email").unwrap_or(&String::new());
                let amount = action.parameters.get("amount").and_then(|a| a.parse::<f64>().ok()).unwrap_or(0.0);
                let sender = action.parameters.get("sender").unwrap_or(&"Unknown".to_string());
                let transaction_id = action.parameters.get("transaction_id").unwrap_or(&"Unknown".to_string());
                
                let mut email_system = self.email_system.write().await;
                match email_system.send_payment_notification(email, amount, sender, transaction_id).await {
                    Ok(result) => ActionExecutionResult {
                        system: "email".to_string(),
                        action: action.action.clone(),
                        success: result.success,
                        error: if result.success { None } else { Some(result.error_message) },
                        result: Some(serde_json::json!({"email": email, "amount": amount})),
                    },
                    Err(e) => ActionExecutionResult {
                        system: "email".to_string(),
                        action: action.action.clone(),
                        success: false,
                        error: Some(e.to_string()),
                        result: None,
                    },
                }
            }
            _ => ActionExecutionResult {
                system: "email".to_string(),
                action: action.action.clone(),
                success: false,
                error: Some("Unknown email action".to_string()),
                result: None,
            },
        }
    }

    async fn execute_blockchain_action(&self, action: &OrchestrationAction) -> ActionExecutionResult {
        match action.action.as_str() {
            "process_transaction" | "record_transaction" => {
                let from_address = action.parameters.get("from_address").unwrap_or(&String::new()).clone();
                let to_address = action.parameters.get("to_address").unwrap_or(&String::new()).clone();
                let amount = action.parameters.get("amount").and_then(|a| a.parse::<f64>().ok()).unwrap_or(0.0);

                let transaction = self.blockchain.create_transaction(
                    from_address,
                    to_address,
                    amount,
                    crate::blockchain::TransactionType::Payment,
                    String::new(),
                );

                let tx_id = self.blockchain.submit_transaction(transaction).await;
                match self.blockchain.validate_and_execute_transaction(&tx_id).await {
                    Ok(result) => ActionExecutionResult {
                        system: "blockchain".to_string(),
                        action: action.action.clone(),
                        success: result.success,
                        error: result.error,
                        result: Some(serde_json::json!({"tx_id": tx_id})),
                    },
                    Err(e) => ActionExecutionResult {
                        system: "blockchain".to_string(),
                        action: action.action.clone(),
                        success: false,
                        error: Some(e.to_string()),
                        result: None,
                    },
                }
            }
            _ => ActionExecutionResult {
                system: "blockchain".to_string(),
                action: action.action.clone(),
                success: false,
                error: Some("Unknown blockchain action".to_string()),
                result: None,
            },
        }
    }

    async fn execute_bridge_action(&self, action: &OrchestrationAction) -> ActionExecutionResult {
        match action.action.as_str() {
            "process_deposit" => {
                let from_chain = action.parameters.get("from_chain").unwrap_or(&"ethereum".to_string()).clone();
                let from_address = action.parameters.get("from_address").unwrap_or(&String::new()).clone();
                let to_address = action.parameters.get("to_address").unwrap_or(&String::new()).clone();
                let amount = action.parameters.get("amount").and_then(|a| a.parse::<f64>().ok()).unwrap_or(0.0);

                match self.bridge.deposit_to_overmanifold(from_chain, from_address, to_address, amount, "USDC".to_string()).await {
                    Ok(result) => ActionExecutionResult {
                        system: "bridge".to_string(),
                        action: action.action.clone(),
                        success: result.success,
                        error: None,
                        result: Some(serde_json::json!({"operation_id": result.operation_id})),
                    },
                    Err(e) => ActionExecutionResult {
                        system: "bridge".to_string(),
                        action: action.action.clone(),
                        success: false,
                        error: Some(e.to_string()),
                        result: None,
                    },
                }
            }
            _ => ActionExecutionResult {
                system: "bridge".to_string(),
                action: action.action.clone(),
                success: false,
                error: Some("Unknown bridge action".to_string()),
                result: None,
            },
        }
    }

    pub async fn get_system_status(&self) -> SystemStatus {
        let system_status = self.system_status.read().await;
        let sms_health = self.sms_system.get_system_health();
        let email_stats = {
            let email_system = self.email_system.read().await;
            email_system.get_email_statistics()
        };
        let blockchain_stats = self.blockchain.get_chain_stats().await;
        let bridge_stats = self.bridge.get_bridge_statistics().await;

        SystemStatus {
            orchestrator: system_status.get("orchestrator").unwrap_or(&"unknown".to_string()).clone(),
            subsystems: SubsystemStatus {
                sms: SubsystemInfo {
                    status: system_status.get("sms").unwrap_or(&"unknown".to_string()).clone(),
                    statistics: serde_json::to_value(sms_health).unwrap_or_default(),
                },
                email: SubsystemInfo {
                    status: system_status.get("email").unwrap_or(&"unknown".to_string()).clone(),
                    statistics: serde_json::to_value(email_stats).unwrap_or_default(),
                },
                blockchain: SubsystemInfo {
                    status: system_status.get("blockchain").unwrap_or(&"unknown".to_string()).clone(),
                    statistics: serde_json::to_value(blockchain_stats).unwrap_or_default(),
                },
                bridge: SubsystemInfo {
                    status: system_status.get("bridge").unwrap_or(&"unknown".to_string()).clone(),
                    statistics: serde_json::to_value(bridge_stats).unwrap_or_default(),
                },
            },
            total_events_processed: self.events.read().await.len() as u64,
        }
    }
}

/// Orchestration result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrchestrationResult {
    pub success: bool,
    pub event_id: String,
    pub status: String,
    pub orchestration_plan: OrchestrationPlan,
    pub execution_results: Vec<ActionExecutionResult>,
}

/// Action execution result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionExecutionResult {
    pub system: String,
    pub action: String,
    pub success: bool,
    pub error: Option<String>,
    pub result: Option<serde_json::Value>,
}

/// System status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemStatus {
    pub orchestrator: String,
    pub subsystems: SubsystemStatus,
    pub total_events_processed: u64,
}

/// Subsystem status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubsystemStatus {
    pub sms: SubsystemInfo,
    pub email: SubsystemInfo,
    pub blockchain: SubsystemInfo,
    pub bridge: SubsystemInfo,
}

/// Subsystem info
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubsystemInfo {
    pub status: String,
    pub statistics: serde_json::Value,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_event_creation() {
        let mut data = HashMap::new();
        data.insert("action".to_string(), "register".to_string());
        
        let event = OrchestrationEvent::new(
            OrchestrationEventType::UserAction,
            "registration".to_string(),
            data,
            "high".to_string(),
        );

        assert!(!event.event_id.is_empty());
        assert_eq!(event.status, "pending");
    }

    #[test]
    fn test_fallback_plan() {
        let orchestrator = LlmOrchestrator::new(None);
        let mut data = HashMap::new();
        data.insert("action".to_string(), "register".to_string());
        
        let event = OrchestrationEvent::new(
            OrchestrationEventType::UserAction,
            "registration".to_string(),
            data,
            "high".to_string(),
        );

        let plan = orchestrator.create_fallback_plan(&event);
        assert!(!plan.recommended_actions.is_empty());
    }
}

fn main() {
    tracing_subscriber::fmt().init();
    
    println!("Rust LLM Unified Orchestration System");
}