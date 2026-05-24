//! Rust LLM Integration Library
//! Custom LLM-based solutions for Overmanifold Protocol
//! 
//! This library provides proprietary implementations of:
//! - SMS processing system (no Twilio dependency)
//! - Email system (no SendGrid dependency)  
//! - Blockchain system (no Web3 dependency)
//! - Bridge system (no external API dependency)
//! - Unified orchestration system
//! - Semantic value transfer handlers (SMS, email, link, domain, endpoint)

pub mod sms_processor;
pub mod email_system;
pub mod blockchain;
pub mod bridge;
pub mod orchestrator;
pub mod semantic_handlers;

pub use sms_processor::{
    LlmSmsProcessor,
    CustomSmsGateway,
    SmsMessage,
    SmsIntent,
    SmsIntentResult,
    SmsPaymentRequest,
    SystemHealth,
};

pub use email_system::{
    LlmCustomEmailSystem,
    EmailMessage,
    EmailDeliveryMethod,
    EmailDeliveryResult,
    EmailAnalysis,
    EmailStatistics,
    SmtpEmailDelivery,
    ApiEmailDelivery,
};

pub use blockchain::{
    CustomBlockchain,
    Transaction,
    TransactionType,
    TransactionStatus,
    Block,
    Account,
    ValidationResult,
    ExecutionResult,
    ChainStats,
    LlmTransactionValidator,
};

pub use bridge::{
    CustomMembraBridge,
    BridgeOperation,
    BridgeOperationType,
    BridgeStatus,
    BridgePool,
    BridgeAnalysis,
    BridgeStatistics,
    LlmBridgeAnalyzer,
};

pub use orchestrator::{
    LlmOrchestrator,
    OrchestrationEvent,
    OrchestrationEventType,
    OrchestrationPlan,
    OrchestrationAction,
    OrchestrationResult,
    ActionExecutionResult,
    SystemStatus,
};

pub use semantic_handlers::{
    SemanticTransferHandler,
    TransferChannel,
    SemanticType,
    SemanticValue,
    TransferPayload,
    SmsHandler,
    EmailHandler,
    LinkHandler,
    DomainHandler,
    EndpointHandler,
    ContractState,
    ContractType,
    ContractCall,
    ContractResult,
    SmartContract,
    CustomNetwork,
};

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Initialize all LLM systems with optional OpenAI API key
pub fn initialize_llm_systems(openai_api_key: Option<String>) -> LlmOrchestrator {
    LlmOrchestrator::new(openai_api_key)
}

/// Initialize all LLM systems from environment variables
pub fn initialize_from_env() -> LlmOrchestrator {
    LlmOrchestrator::from_env()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version() {
        assert!(!VERSION.is_empty());
    }

    #[test]
    fn test_initialization() {
        let orchestrator = initialize_llm_systems(None);
        // Just test that it doesn't panic
        let _ = orchestrator;
    }
}