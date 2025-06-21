-- Payment Processing Database Schema
-- This script initializes the database with necessary tables and indexes

-- Create application user first
CREATE USER payment_user WITH PASSWORD 'payment_password';

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Transactions table for core payment records
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    merchant_id VARCHAR(100) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    payment_method VARCHAR(50) NOT NULL,
    card_last_four VARCHAR(4),
    encrypted_card_data TEXT,
    authorization_id VARCHAR(100),
    capture_id VARCHAR(100),
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'authorized', 'captured', 'failed', 'cancelled', 'expired')),
    CONSTRAINT valid_currency CHECK (LENGTH(currency) = 3),
    CONSTRAINT valid_payment_method CHECK (payment_method IN ('credit_card', 'debit_card', 'bank_transfer', 'digital_wallet'))
);

-- Refunds table for refund tracking
CREATE TABLE refunds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    refund_id VARCHAR(100) UNIQUE NOT NULL,
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    amount DECIMAL(12, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    reason VARCHAR(100),
    external_refund_id VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT valid_refund_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_refund_currency CHECK (LENGTH(currency) = 3)
);

-- Audit log table for compliance
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID REFERENCES transactions(id) ON DELETE SET NULL,
    refund_id UUID REFERENCES refunds(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    user_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    correlation_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_event_type CHECK (event_type IN (
        'payment_created', 'payment_authorized', 'payment_captured', 'payment_failed',
        'refund_created', 'refund_processed', 'refund_failed',
        'security_event', 'configuration_change'
    ))
);

-- Indexes for optimal query performance
CREATE INDEX idx_transactions_transaction_id ON transactions(transaction_id);
CREATE INDEX idx_transactions_merchant_id ON transactions(merchant_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_updated_at ON transactions(updated_at);
CREATE INDEX idx_transactions_expires_at ON transactions(expires_at);
CREATE INDEX idx_transactions_metadata_gin ON transactions USING GIN(metadata);

CREATE INDEX idx_refunds_refund_id ON refunds(refund_id);
CREATE INDEX idx_refunds_transaction_id ON refunds(transaction_id);
CREATE INDEX idx_refunds_status ON refunds(status);
CREATE INDEX idx_refunds_created_at ON refunds(created_at);
CREATE INDEX idx_refunds_metadata_gin ON refunds USING GIN(metadata);

CREATE INDEX idx_audit_logs_transaction_id ON audit_logs(transaction_id);
CREATE INDEX idx_audit_logs_refund_id ON audit_logs(refund_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_correlation_id ON audit_logs(correlation_id);
CREATE INDEX idx_audit_logs_event_data_gin ON audit_logs USING GIN(event_data);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_refunds_updated_at
    BEFORE UPDATE ON refunds
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing (optional)
INSERT INTO transactions (transaction_id, merchant_id, amount, currency, status, payment_method, card_last_four, description, metadata)
VALUES 
    ('txn_sample_001', 'merchant_123', 99.99, 'USD', 'captured', 'credit_card', '1234', 'Sample transaction', '{"test": true}'),
    ('txn_sample_002', 'merchant_456', 149.99, 'USD', 'authorized', 'credit_card', '5678', 'Another sample', '{"test": true}');

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO payment_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO payment_user;