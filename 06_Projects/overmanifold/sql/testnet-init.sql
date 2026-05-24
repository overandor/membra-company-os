-- Overmanifold Testnet v0.1 Database Initialization
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Testnet-specific tables
CREATE TABLE IF NOT EXISTS testnet_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tx_hash TEXT NOT NULL,
    chain TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL,
    observed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    merkle_root TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS testnet_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id TEXT UNIQUE NOT NULL,
    approval_type TEXT NOT NULL,
    status TEXT NOT NULL,
    operation_data JSONB,
    requester_id TEXT,
    approver_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    decision_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_testnet_tx_hash ON testnet_transactions(tx_hash);
CREATE INDEX idx_testnet_approvals_status ON testnet_approvals(status);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO overmanifold_testnet;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO overmanifold_testnet;
