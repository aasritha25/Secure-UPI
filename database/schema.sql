-- ==========================================================
-- Secure UPI: Machine Learning-Driven Fraud Detection System
-- Database Schema Definition (MySQL & SQLite Compatible DDL)
-- ==========================================================

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(30) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) DEFAULT 'customer' NOT NULL, -- 'customer' or 'admin'
    language VARCHAR(10) DEFAULT 'en' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Accounts Table
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    account_number_masked VARCHAR(30) NOT NULL,
    balance DECIMAL(12, 2) DEFAULT 100000.00 NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 3. Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id VARCHAR(80) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    receiver_id VARCHAR(80) NOT NULL,
    receiver_name VARCHAR(120) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    location VARCHAR(80) DEFAULT 'Unknown',
    device_id VARCHAR(80) DEFAULT 'Unknown',
    ip_address VARCHAR(45) DEFAULT '127.0.0.1',
    transaction_type VARCHAR(40) DEFAULT 'P2P', -- P2P, P2M, BILL_PAYMENT, ONLINE_SHOPPING, INVESTMENT, RECHARGE
    status VARCHAR(30) DEFAULT 'SUCCESS' NOT NULL, -- SUCCESS, FLAGGED, BLOCKED, FAILED
    risk_score DECIMAL(5, 2) DEFAULT 0.00,
    risk_level VARCHAR(20) DEFAULT 'LOW_RISK', -- LOW_RISK, MEDIUM_RISK, HIGH_RISK
    fraud_probability DECIMAL(6, 4) DEFAULT 0.0000,
    prediction VARCHAR(50) DEFAULT 'Legitimate', -- Legitimate, Suspicious, Fraudulent
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 4. Fraud Predictions & Explainability Table
CREATE TABLE IF NOT EXISTS fraud_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id VARCHAR(80) NOT NULL,
    user_id INTEGER NOT NULL,
    model_name VARCHAR(60) NOT NULL,
    fraud_probability DECIMAL(6, 4) NOT NULL,
    risk_score DECIMAL(5, 2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    prediction VARCHAR(50) NOT NULL,
    explanation TEXT,
    feature_contributions TEXT, -- JSON string of top feature weights & impacts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 5. Fraud Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id VARCHAR(80),
    user_id INTEGER NOT NULL,
    risk_level VARCHAR(20) DEFAULT 'MEDIUM_RISK',
    severity VARCHAR(20) DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, CRITICAL
    title VARCHAR(180) NOT NULL,
    message TEXT NOT NULL,
    reason TEXT,
    alert_status VARCHAR(30) DEFAULT 'ACTIVE', -- ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 6. User Devices Table
CREATE TABLE IF NOT EXISTS user_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    device_id VARCHAR(80) NOT NULL,
    device_name VARCHAR(120),
    ip_address VARCHAR(45),
    location VARCHAR(80),
    is_trusted INTEGER DEFAULT 1,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 7. Login History Table
CREATE TABLE IF NOT EXISTS login_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ip_address VARCHAR(45),
    device_id VARCHAR(80),
    location VARCHAR(80),
    status VARCHAR(20) DEFAULT 'SUCCESS',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes for optimal performance
CREATE INDEX IF NOT EXISTS idx_txn_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_txn_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_txn_risk ON transactions(risk_level);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(alert_status);
