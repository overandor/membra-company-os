//! Rust LLM Integration - Main Entry Point
//! 
//! This is the main entry point for the Rust LLM integration system.
//! It demonstrates the usage of all custom LLM-based systems.

use rust_llm_integration::{
    initialize_from_env,
    LlmOrchestrator,
    OrchestrationEvent,
    OrchestrationEventType,
};
use std::collections::HashMap;
use tracing::{info, Level};
use tracing_subscriber;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_max_level(Level::INFO)
        .init();

    info!("Starting Rust LLM Integration System v{}", rust_llm_integration::VERSION);

    // Initialize orchestrator
    let orchestrator = initialize_from_env();
    orchestrator.initialize().await?;

    info!("LLM Integration Systems initialized successfully");

    // Get system status
    let status = orchestrator.get_system_status().await;
    info!("System Status: {}", status.orchestrator);
    info!("SMS Status: {}", status.subsystems.sms.status);
    info!("Email Status: {}", status.subsystems.email.status);
    info!("Blockchain Status: {}", status.subsystems.blockchain.status);
    info!("Bridge Status: {}", status.subsystems.bridge.status);

    // Example: Handle user registration
    let mut registration_data = HashMap::new();
    registration_data.insert("action".to_string(), "register".to_string());
    registration_data.insert("phone".to_string(), "+1234567890".to_string());
    registration_data.insert("email".to_string(), "user@example.com".to_string());

    let registration_event = OrchestrationEvent::new(
        OrchestrationEventType::UserAction,
        "registration".to_string(),
        registration_data,
        "high".to_string(),
    );

    info!("Processing user registration event...");
    let result = orchestrator.orchestrate_event(registration_event).await?;
    info!("Registration event processed: {}", result.success);

    // Example: Handle payment
    let mut payment_data = HashMap::new();
    payment_data.insert("action".to_string(), "payment".to_string());
    payment_data.insert("from_address".to_string(), "0x1234567890abcdef1234567890abcdef12345678".to_string());
    payment_data.insert("to_address".to_string(), "0x0987654321fedcba0987654321fedcba09876543".to_string());
    payment_data.insert("amount".to_string(), "100.0".to_string());
    payment_data.insert("phone".to_string(), "+1234567890".to_string());

    let payment_event = OrchestrationEvent::new(
        OrchestrationEventType::TransactionEvent,
        "payment".to_string(),
        payment_data,
        "high".to_string(),
    );

    info!("Processing payment event...");
    let result = orchestrator.orchestrate_event(payment_event).await?;
    info!("Payment event processed: {}", result.success);

    info!("Rust LLM Integration System demo completed successfully");
    
    Ok(())
}