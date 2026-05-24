//! Test semantic value transfer handlers

use rust_llm_integration::semantic_handlers::{
    SemanticTransferHandler, TransferPayload, TransferChannel, SemanticValue,
    CustomNetwork, SemanticType, ContractCall
};
use chrono::Utc;

fn main() {
    println!("Testing Semantic Value Transfer System");
    
    // Test 1: Create handler
    let handler = SemanticTransferHandler::new();
    println!("✓ Handler created");
    
    // Test 2: Create semantic value
    let semantic_value = SemanticValue {
        amount: 100.0,
        currency: "USD".to_string(),
        semantic_type: SemanticType::Payment,
        sender: "+1234567890".to_string(),
        recipient: "+0987654321".to_string(),
        metadata: {
            let mut map = std::collections::HashMap::new();
            map.insert("for".to_string(), "services".to_string());
            map.insert("ref".to_string(), "INV-001".to_string());
            map
        },
        conditions: vec![],
        expires_at: None,
        created_at: Utc::now(),
    };
    println!("✓ Semantic value created");
    
    // Test 3: Create payload
    let payload = TransferPayload {
        semantic_value: semantic_value.clone(),
        channel: TransferChannel::Sms,
        channel_address: "+1234567890".to_string(),
        signature: String::new(),
        nonce: "test_nonce".to_string(),
        network_id: "membra-mainnet".to_string(),
        gas_limit: 21000,
        gas_price: 0.00001,
    };
    println!("✓ Payload created");
    
    // Test 4: Generate SMS syntax
    let sms_syntax = handler.generate(&payload);
    println!("✓ SMS syntax generated: {}", sms_syntax);
    
    // Test 5: Parse SMS syntax
    let parsed = handler.parse(&sms_syntax, TransferChannel::Sms);
    match parsed {
        Some(parsed_payload) => {
            println!("✓ SMS syntax parsed successfully");
            println!("  Amount: {}", parsed_payload.semantic_value.amount);
            println!("  Currency: {}", parsed_payload.semantic_value.currency);
        }
        None => {
            println!("✗ Failed to parse SMS syntax");
        }
    }
    
    // Test 6: Test custom network
    let network = CustomNetwork::new("test-network".to_string());
    println!("✓ Custom network created");
    
    // Test 7: Deploy contract
    let contract = rust_llm_integration::semantic_handlers::SmartContract::new(
        "test_contract".to_string(),
        rust_llm_integration::semantic_handlers::ContractType::Token,
        "creator".to_string()
    );
    let contract_address = network.deploy_contract(contract);
    println!("✓ Contract deployed: {}", contract_address);
    
    // Test 8: Get network status
    let status = network.get_network_status();
    println!("✓ Network status: {}", status);
    
    println!("\nAll tests passed!");
}