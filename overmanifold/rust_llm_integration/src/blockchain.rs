//! Rust LLM Custom Blockchain System
//! Proprietary blockchain without Web3 dependencies

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::env;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tokio::sync::RwLock;
use tracing::{debug, error, info, warn};
use uuid::Uuid;

/// Transaction types
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum TransactionType {
    Payment,
    Verification,
    Registration,
    Sponsorship,
    Governance,
    Reward,
    SmartContract,
}

/// Transaction status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum TransactionStatus {
    Pending,
    Validated,
    Executed,
    Confirmed,
    Failed,
    Reverted,
}

/// Transaction structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub tx_id: String,
    pub from_address: String,
    pub to_address: String,
    pub amount: f64,
    pub transaction_type: TransactionType,
    pub timestamp: DateTime<Utc>,
    pub status: TransactionStatus,
    pub gas_limit: u64,
    pub gas_used: u64,
    pub gas_price: f64,
    pub data: String,
    pub signature: String,
    pub block_number: u64,
    pub confirmation_count: u64,
    pub metadata: HashMap<String, String>,
}

impl Transaction {
    pub fn new(
        from_address: String,
        to_address: String,
        amount: f64,
        transaction_type: TransactionType,
        data: String,
    ) -> Self {
        let tx_id = Self::generate_tx_id(&from_address, &to_address, amount);
        Self {
            tx_id,
            from_address,
            to_address,
            amount,
            transaction_type,
            timestamp: Utc::now(),
            status: TransactionStatus::Pending,
            gas_limit: 21000,
            gas_used: 0,
            gas_price: 0.00001,
            data,
            signature: String::new(),
            block_number: 0,
            confirmation_count: 0,
            metadata: HashMap::new(),
        }
    }

    fn generate_tx_id(from: &str, to: &str, amount: f64) -> String {
        let mut hasher = Sha256::new();
        hasher.update(format!("{}{}{}{}", from, to, amount, Utc::now().timestamp()));
        hex::encode(hasher.finalize())
    }
}

/// Block structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Block {
    pub block_number: u64,
    pub timestamp: DateTime<Utc>,
    pub transactions: Vec<String>,
    pub parent_hash: String,
    pub block_hash: String,
    pub state_root: String,
    pub validator: String,
    pub gas_used: u64,
    pub gas_limit: u64,
}

impl Block {
    pub fn new(
        block_number: u64,
        parent_hash: String,
        validator: String,
        transactions: Vec<String>,
    ) -> Self {
        let timestamp = Utc::now();
        let block_hash = Self::calculate_block_hash(block_number, &parent_hash, &transactions, &validator);
        
        Self {
            block_number,
            timestamp,
            transactions,
            parent_hash,
            block_hash,
            state_root: String::new(),
            validator,
            gas_used: 0,
            gas_limit: 1_000_000,
        }
    }

    fn calculate_block_hash(
        block_number: u64,
        parent_hash: &str,
        transactions: &[String],
        validator: &str,
    ) -> String {
        let mut hasher = Sha256::new();
        let txs_hash: String = transactions.join("");
        hasher.update(format!("{}{}{}{}", block_number, parent_hash, txs_hash, validator));
        hex::encode(hasher.finalize())
    }
}

/// Account structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Account {
    pub address: String,
    pub balance: f64,
    pub nonce: u64,
    pub storage: HashMap<String, String>,
    pub code: String,
    pub created_at: DateTime<Utc>,
}

impl Account {
    pub fn new(address: Option<String>, balance: f64) -> Self {
        let addr = address.unwrap_or_else(|| Self::generate_address());
        Self {
            address: addr,
            balance,
            nonce: 0,
            storage: HashMap::new(),
            code: String::new(),
            created_at: Utc::now(),
        }
    }

    fn generate_address() -> String {
        use rand::Rng;
        let random_bytes: [u8; 20] = rand::thread_rng().gen();
        let mut hasher = Sha256::new();
        hasher.update(format!("overmanifold{}{}", hex::encode(random_bytes), Utc::now().timestamp()));
        format!("0x{}", &hex::encode(hasher.finalize())[..40])
    }
}

/// Transaction validation result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResult {
    pub is_valid: bool,
    pub confidence: f64,
    pub validation_checks: HashMap<String, bool>,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
    pub reasoning: String,
    pub gas_estimate: u64,
}

/// LLM transaction validator
pub struct LlmTransactionValidator {
    openai_api_key: Option<String>,
    client: Client,
}

impl LlmTransactionValidator {
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

    /// Validate transaction using LLM
    pub async fn validate_transaction(
        &self,
        transaction: &Transaction,
        sender_balance: f64,
        sender_nonce: u64,
    ) -> Result<ValidationResult> {
        if let Some(ref api_key) = self.openai_api_key {
            self.validate_with_llm(transaction, sender_balance, sender_nonce, api_key)
                .await
        } else {
            Ok(self.validate_fallback(transaction, sender_balance, sender_nonce))
        }
    }

    async fn validate_with_llm(
        &self,
        transaction: &Transaction,
        sender_balance: f64,
        sender_nonce: u64,
        api_key: &str,
    ) -> Result<ValidationResult> {
        let context = serde_json::json!({
            "transaction_type": transaction.transaction_type,
            "from_address": transaction.from_address,
            "to_address": transaction.to_address,
            "amount": transaction.amount,
            "gas_limit": transaction.gas_limit,
            "gas_price": transaction.gas_price,
            "data": &transaction.data[..200.min(transaction.data.len())],
            "sender_balance": sender_balance,
            "sender_nonce": sender_nonce,
            "timestamp": transaction.timestamp.to_rfc3339()
        });

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
                        "content": format!("Transaction: {}", context)
                    }
                ],
                "temperature": 0.1,
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
        Ok(self.parse_validation_result(result)?)
    }

    fn validate_fallback(
        &self,
        transaction: &Transaction,
        sender_balance: f64,
        sender_nonce: u64,
    ) -> ValidationResult {
        let mut validation_checks = HashMap::new();
        let mut errors = Vec::new();
        let mut warnings = Vec::new();

        // Validate amount
        let amount_valid = transaction.amount > 0.0 && transaction.amount <= 1_000_000.0;
        validation_checks.insert("amount_valid".to_string(), amount_valid);
        if !amount_valid {
            errors.push("Invalid amount".to_string());
        }

        // Validate balance
        let balance_sufficient = sender_balance >= transaction.amount;
        validation_checks.insert("balance_sufficient".to_string(), balance_sufficient);
        if !balance_sufficient {
            errors.push("Insufficient balance".to_string());
        }

        // Validate nonce
        let nonce_valid = transaction.nonce == sender_nonce;
        validation_checks.insert("nonce_valid".to_string(), nonce_valid);
        if !nonce_valid {
            errors.push("Invalid nonce".to_string());
        }

        // Validate addresses
        let sender_valid = self.validate_address(&transaction.from_address);
        let recipient_valid = self.validate_address(&transaction.to_address);
        validation_checks.insert("sender_valid".to_string(), sender_valid);
        validation_checks.insert("recipient_valid".to_string(), recipient_valid);

        if !sender_valid {
            errors.push("Invalid sender address".to_string());
        }
        if !recipient_valid {
            errors.push("Invalid recipient address".to_string());
        }

        // Validate gas
        let gas_sufficient = transaction.gas_limit >= 21000;
        validation_checks.insert("gas_sufficient".to_string(), gas_sufficient);
        if !gas_sufficient {
            warnings.push("Low gas limit".to_string());
        }

        let is_valid = validation_checks.values().all(|&v| v) && errors.is_empty();

        ValidationResult {
            is_valid,
            confidence: 0.85,
            validation_checks,
            errors,
            warnings,
            reasoning: "Rule-based validation".to_string(),
            gas_estimate: transaction.gas_limit,
        }
    }

    fn validate_address(&self, address: &str) -> bool {
        address.starts_with("0x") && address.len() == 42
    }

    fn get_system_prompt(&self) -> &'static str {
        r#"You are an intelligent transaction validator for Overmanifold Protocol. Validate blockchain transactions for security and correctness.

VALIDATION FORMAT:
Return JSON with this exact structure:
{
  "is_valid": true|false,
  "confidence": 0.0-1.0,
  "validation_checks": {
    "sender_valid": true|false,
    "recipient_valid": true|false,
    "amount_valid": true|false,
    "balance_sufficient": true|false,
    "nonce_valid": true|false,
    "signature_valid": true|false,
    "data_safe": true|false,
    "gas_sufficient": true|false,
    "type_valid": true|false,
    "compliance_ok": true|false
  },
  "errors": ["error1", "error2"],
  "warnings": ["warning1", "warning2"],
  "reasoning": "explain validation decision",
  "gas_estimate": 0
}"#
    }

    fn parse_validation_result(&self, response: serde_json::Value) -> Result<ValidationResult> {
        let mut validation_checks = HashMap::new();
        if let Some(checks) = response["validation_checks"].as_object() {
            for (key, value) in checks {
                if let Some(bool_val) = value.as_bool() {
                    validation_checks.insert(key.clone(), bool_val);
                }
            }
        }

        let errors: Vec<String> = response["errors"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect()
            })
            .unwrap_or_default();

        let warnings: Vec<String> = response["warnings"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect()
            })
            .unwrap_or_default();

        Ok(ValidationResult {
            is_valid: response["is_valid"].as_bool().unwrap_or(false),
            confidence: response["confidence"].as_f64().unwrap_or(0.5),
            validation_checks,
            errors,
            warnings,
            reasoning: response["reasoning"]
                .as_str()
                .unwrap_or("LLM validation")
                .to_string(),
            gas_estimate: response["gas_estimate"].as_u64().unwrap_or(21000),
        })
    }
}

/// Custom blockchain implementation
pub struct CustomBlockchain {
    chain_id: String,
    openai_api_key: Option<String>,
    validator: LlmTransactionValidator,
    accounts: Arc<RwLock<HashMap<String, Account>>>,
    blocks: Arc<RwLock<HashMap<u64, Block>>>,
    transactions: Arc<RwLock<HashMap<String, Transaction>>>,
    pending_transactions: Arc<Mutex<Vec<String>>>,
    block_number: Arc<Mutex<u64>>,
    miner_address: String,
    is_running: Arc<Mutex<bool>>,
}

impl CustomBlockchain {
    pub fn new(openai_api_key: Option<String>, chain_id: String) -> Self {
        let validator = LlmTransactionValidator::new(openai_api_key.clone());
        
        Self {
            chain_id,
            openai_api_key,
            validator,
            accounts: Arc::new(RwLock::new(HashMap::new())),
            blocks: Arc::new(RwLock::new(HashMap::new())),
            transactions: Arc::new(RwLock::new(HashMap::new())),
            pending_transactions: Arc::new(Mutex::new(Vec::new())),
            block_number: Arc::new(Mutex::new(0)),
            miner_address: "0x0000000000000000000000000000000000000001".to_string(),
            is_running: Arc::new(Mutex::new(false)),
        }
    }

    pub fn from_env() -> Self {
        Self::new(env::var("OPENAI_API_KEY").ok(), "overmanifold-1".to_string())
    }

    pub async fn initialize(&self) -> Result<()> {
        // Create genesis block
        let genesis_block = Block::new(
            0,
            "0".repeat(64),
            "genesis".to_string(),
            vec![],
        );

        {
            let mut blocks = self.blocks.write().await;
            blocks.insert(0, genesis_block);
        }

        // Create genesis accounts
        {
            let mut accounts = self.accounts.write().await;
            accounts.insert(
                "0x0000000000000000000000000000000000000001".to_string(),
                Account::new(None, 1_000_000.0),
            );
            accounts.insert(
                "0x0000000000000000000000000000000000000002".to_string(),
                Account::new(None, 1_000_000.0),
            );
            accounts.insert(
                "0x0000000000000000000000000000000000000003".to_string(),
                Account::new(None, 1_000_000.0),
            );
        }

        {
            let mut block_number = self.block_number.lock().await;
            *block_number = 1;
        }

        info!("Genesis block and accounts initialized");
        Ok(())
    }

    pub async fn get_balance(&self, address: &str) -> f64 {
        let accounts = self.accounts.read().await;
        accounts.get(address).map(|acc| acc.balance).unwrap_or(0.0)
    }

    pub async fn create_transaction(
        &self,
        from_address: String,
        to_address: String,
        amount: f64,
        transaction_type: TransactionType,
        data: String,
    ) -> Transaction {
        Transaction::new(from_address, to_address, amount, transaction_type, data)
    }

    pub async fn submit_transaction(&self, transaction: Transaction) -> String {
        let tx_id = transaction.tx_id.clone();
        
        {
            let mut transactions = self.transactions.write().await;
            transactions.insert(tx_id.clone(), transaction);
        }

        {
            let mut pending = self.pending_transactions.lock().await;
            pending.push(tx_id.clone());
        }

        info!("Transaction submitted: {}", tx_id);
        tx_id
    }

    pub async fn validate_and_execute_transaction(&self, tx_id: &str) -> Result<ExecutionResult> {
        let mut transactions = self.transactions.write().await;
        
        let transaction = transactions.get(tx_id)
            .context("Transaction not found")?
            .clone();

        let accounts = self.accounts.read().await;
        let sender = accounts.get(&transaction.from_address)
            .context("Sender account not found")?;

        let validation = self.validator.validate_transaction(&transaction, sender.balance, sender.nonce).await?;

        if !validation.is_valid {
            transaction.status = TransactionStatus::Failed;
            return Ok(ExecutionResult {
                success: false,
                tx_id: tx_id.to_string(),
                error: Some("Transaction validation failed".to_string()),
                gas_used: 0,
                tx_cost: 0.0,
            });
        }

        // Execute transaction
        let mut accounts = self.accounts.write().await;
        
        let sender = accounts.get_mut(&transaction.from_address).unwrap();
        sender.balance -= transaction.amount;
        sender.nonce += 1;

        let recipient = accounts.get_mut(&transaction.to_address).unwrap();
        recipient.balance += transaction.amount;

        transaction.status = TransactionStatus::Executed;
        transaction.gas_used = validation.gas_estimate;

        let tx_cost = transaction.gas_used as f64 * transaction.gas_price;
        sender.balance -= tx_cost;

        // Remove from pending
        {
            let mut pending = self.pending_transactions.lock().await;
            if let Some(pos) = pending.iter().position(|x| x == tx_id) {
                pending.remove(pos);
            }
        }

        let updated_tx = transaction.clone();
        transactions.insert(tx_id.to_string(), updated_tx);

        info!("Transaction executed: {}", tx_id);

        Ok(ExecutionResult {
            success: true,
            tx_id: tx_id.to_string(),
            error: None,
            gas_used: transaction.gas_used,
            tx_cost,
        })
    }

    pub async fn produce_block(&self, validator_address: Option<String>) -> Result<Block> {
        let validator = validator_address.unwrap_or_else(|| self.miner_address.clone());

        let pending = {
            let pending = self.pending_transactions.lock().await;
            pending.clone()
        };

        let selected_txs = if pending.is_empty() {
            vec![]
        } else {
            // Simple fee-based selection
            let txs = {
                let transactions = self.transactions.read().await;
                pending.iter()
                    .filter_map(|tx_id| transactions.get(tx_id).cloned())
                    .collect::<Vec<_>>()
            };

            let mut sorted_txs = txs;
            sorted_txs.sort_by(|a, b| b.gas_price.partial_cmp(&a.gas_price).unwrap());
            
            sorted_txs.into_iter().take(10).map(|tx| tx.tx_id).collect()
        };

        let last_block_number = {
            let block_number = self.block_number.lock().await;
            *block_number - 1
        };

        let parent_hash = {
            let blocks = self.blocks.read().await;
            blocks.get(&last_block_number)
                .map(|b| b.block_hash.clone())
                .unwrap_or_else(|| "0".repeat(64))
        };

        let mut new_block = Block::new(
            {
                let block_number = self.block_number.lock().await;
                *block_number
            },
            parent_hash,
            validator,
            selected_txs.clone(),
        );

        // Execute transactions
        for tx_id in &selected_txs {
            if let Err(e) = self.validate_and_execute_transaction(tx_id).await {
                error!("Failed to execute transaction {}: {}", tx_id, e);
            }
        }

        // Calculate gas used
        let gas_used: u64 = {
            let transactions = self.transactions.read().await;
            selected_txs.iter()
                .filter_map(|tx_id| transactions.get(tx_id))
                .map(|tx| tx.gas_used)
                .sum()
        };
        new_block.gas_used = gas_used;

        {
            let mut blocks = self.blocks.write().await;
            let block_number = {
                let mut bn = self.block_number.lock().await;
                let current = *bn;
                *bn += 1;
                current
            };
            blocks.insert(block_number, new_block.clone());
        }

        // Reward validator
        let block_reward = 2.0;
        let mut accounts = self.accounts.write().await;
        if let Some(validator_account) = accounts.get_mut(&validator) {
            validator_account.balance += block_reward;
        }

        info!("Block {} produced with {} transactions", new_block.block_number, selected_txs.len());

        Ok(new_block)
    }

    pub async fn get_chain_stats(&self) -> ChainStats {
        let transactions = self.transactions.read().await;
        let accounts = self.accounts.read().await;
        let blocks = self.blocks.read().await;
        let block_number = *self.block_number.lock().await;

        let total_supply: f64 = accounts.values().map(|acc| acc.balance).sum();

        ChainStats {
            chain_id: self.chain_id.clone(),
            block_number,
            total_transactions: transactions.len() as u64,
            pending_transactions: self.pending_transactions.lock().await.len() as u64,
            total_accounts: accounts.len() as u64,
            total_supply,
            latest_block_hash: blocks.get(&(block_number - 1)).map(|b| b.block_hash.clone()),
            difficulty: 1,
            block_time: 15,
        }
    }
}

/// Transaction execution result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionResult {
    pub success: bool,
    pub tx_id: String,
    pub error: Option<String>,
    pub gas_used: u64,
    pub tx_cost: f64,
}

/// Chain statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChainStats {
    pub chain_id: String,
    pub block_number: u64,
    pub total_transactions: u64,
    pub pending_transactions: u64,
    pub total_accounts: u64,
    pub total_supply: f64,
    pub latest_block_hash: Option<String>,
    pub difficulty: u64,
    pub block_time: u64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_transaction_creation() {
        let tx = Transaction::new(
            "0x1234567890abcdef1234567890abcdef12345678".to_string(),
            "0x0987654321fedcba0987654321fedcba09876543".to_string(),
            100.0,
            TransactionType::Payment,
            String::new(),
        );

        assert!(!tx.tx_id.is_empty());
        assert_eq!(tx.status, TransactionStatus::Pending);
    }

    #[test]
    fn test_account_creation() {
        let account = Account::new(None, 1000.0);
        assert!(account.address.starts_with("0x"));
        assert_eq!(account.balance, 1000.0);
    }

    #[test]
    fn test_address_validation() {
        let validator = LlmTransactionValidator::new(None);
        assert!(validator.validate_address("0x1234567890abcdef1234567890abcdef12345678"));
        assert!(!validator.validate_address("invalid"));
    }
}

fn main() {
    tracing_subscriber::fmt().init();
    
    println!("Rust LLM Custom Blockchain System");
    println!("Chain ID: overmanifold-1");
}