//! FFI bindings to the C++ consensus core

use libc::{c_char, c_void, size_t, uint64_t};
use std::ffi::CString;

// Opaque pointer to C++ GenesisNode
pub enum GenesisNode {}

#[repr(C)]
pub struct CTransaction {
    pub tx_hash: [u8; 32],
    pub from: [u8; 32],
    pub to: [u8; 32],
    pub amount: u64,
    pub nonce: u64,
    pub timestamp: u64,
    pub tx_type: u8,
    pub data: [u8; 256],
}

#[repr(C)]
pub struct CInferenceProof {
    pub prompt_hash: [u8; 32],
    pub response_hash: [u8; 32],
    pub proof_hash: [u8; 32],
    pub token_count: u64,
    pub confidence: f64,
    pub timestamp: u64,
}

extern "C" {
    pub fn membra_genesis_create(node_id: *const c_char) -> *mut GenesisNode;
    pub fn membra_genesis_destroy(genesis: *mut GenesisNode);
    
    pub fn membra_tx_verify(genesis: *mut GenesisNode, tx: *const CTransaction) -> bool;
    pub fn membra_tx_submit(genesis: *mut GenesisNode, tx: *const CTransaction);
    pub fn membra_tx_pool_size(genesis: *mut GenesisNode) -> u64;
    
    pub fn membra_batch_form(
        genesis: *mut GenesisNode,
        txs: *const CTransaction,
        count: size_t,
    ) -> *mut c_void;
    pub fn membra_proof_submit(
        genesis: *mut GenesisNode,
        batch: *mut c_void,
        proof: *const CInferenceProof,
    );
    pub fn membra_consensus_check(genesis: *mut GenesisNode, batch: *mut c_void) -> bool;
    pub fn membra_batch_finalize(genesis: *mut GenesisNode, batch: *mut c_void);
    pub fn membra_finalized_count(genesis: *mut GenesisNode) -> u64;
    
    pub fn membra_balance_get(genesis: *mut GenesisNode, address: *const [u8; 32]) -> u64;
    pub fn membra_balance_credit(genesis: *mut GenesisNode, address: *const [u8; 32], amount: u64);
    pub fn membra_balance_debit(genesis: *mut GenesisNode, address: *const [u8; 32], amount: u64) -> bool;
    
    pub fn membra_merkle_root(leaves: *const [u8; 32], count: size_t, out: *mut [u8; 32]);
    
    pub fn membra_stats(
        genesis: *mut GenesisNode,
        total_tx: *mut u64,
        total_tokens: *mut u64,
        finalized: *mut u64,
    );
}

/// Safe wrapper around the C++ GenesisNode
pub struct GenesisWrapper {
    ptr: *mut GenesisNode,
}

impl GenesisWrapper {
    pub fn new(node_id: &str) -> Self {
        let c_id = CString::new(node_id).unwrap();
        let ptr = unsafe { membra_genesis_create(c_id.as_ptr()) };
        assert!(!ptr.is_null());
        Self { ptr }
    }
    
    pub fn submit_tx(&self, tx: &CTransaction) {
        unsafe { membra_tx_submit(self.ptr, tx) }
    }
    
    pub fn pool_size(&self) -> u64 {
        unsafe { membra_tx_pool_size(self.ptr) }
    }
    
    pub fn credit(&self, address: &[u8; 32], amount: u64) {
        unsafe { membra_balance_credit(self.ptr, address, amount) }
    }
    
    pub fn debit(&self, address: &[u8; 32], amount: u64) -> bool {
        unsafe { membra_balance_debit(self.ptr, address, amount) }
    }
    
    pub fn balance(&self, address: &[u8; 32]) -> u64 {
        unsafe { membra_balance_get(self.ptr, address) }
    }
    
    pub fn stats(&self) -> (u64, u64, u64) {
        let mut total_tx = 0u64;
        let mut total_tokens = 0u64;
        let mut finalized = 0u64;
        unsafe {
            membra_stats(self.ptr, &mut total_tx, &mut total_tokens, &mut finalized);
        }
        (total_tx, total_tokens, finalized)
    }
    
    pub fn finalized_count(&self) -> u64 {
        unsafe { membra_finalized_count(self.ptr) }
    }
}

impl Drop for GenesisWrapper {
    fn drop(&mut self) {
        unsafe { membra_genesis_destroy(self.ptr) }
    }
}

unsafe impl Send for GenesisWrapper {}
unsafe impl Sync for GenesisWrapper {}
