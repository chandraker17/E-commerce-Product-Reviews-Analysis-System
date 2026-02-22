-- ============================================================
-- E-commerce Product Reviews Analysis - MySQL Schema
-- Optimized for sentiment analysis and dashboard queries
-- ============================================================

CREATE DATABASE IF NOT EXISTS openfeedback;
USE openfeedback;

-- ------------------------------------------------------------
-- USERS TABLE
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    role VARCHAR(20) DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- REVIEWS (FEEDBACK) TABLE - E-commerce focused
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) DEFAULT NULL,
    feedback_text TEXT NOT NULL,
    rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_suspicious BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_product (product_name),
    INDEX idx_category (category),
    INDEX idx_rating (rating),
    INDEX idx_created (created_at),
    INDEX idx_product_rating (product_name, rating)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- SENTIMENT ANALYSIS RESULTS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sentiment_analysis (
    analysis_id INT AUTO_INCREMENT PRIMARY KEY,
    feedback_id INT NOT NULL,
    sentiment_label ENUM('Positive', 'Negative', 'Neutral') NOT NULL,
    sentiment_score FLOAT NOT NULL,
    subjectivity_score FLOAT DEFAULT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feedback_id) REFERENCES feedback(feedback_id) ON DELETE CASCADE,
    UNIQUE KEY unique_feedback_sentiment (feedback_id),
    INDEX idx_sentiment (sentiment_label)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- FEEDBACK SUMMARY (Materialized view-like, for dashboards)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback_summary (
    summary_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) DEFAULT NULL,
    average_rating FLOAT NOT NULL,
    total_reviews INT NOT NULL,
    positive_count INT DEFAULT 0,
    negative_count INT DEFAULT 0,
    neutral_count INT DEFAULT 0,
    pct_positive FLOAT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_product (product_name),
    INDEX idx_category (category),
    INDEX idx_avg_rating (average_rating)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Add category column if upgrading from old schema
-- ------------------------------------------------------------
-- Run these if migrating existing database:
-- ALTER TABLE feedback ADD COLUMN category VARCHAR(100) DEFAULT NULL AFTER product_name;
-- ALTER TABLE feedback ADD COLUMN is_suspicious BOOLEAN DEFAULT FALSE AFTER created_at;
-- ALTER TABLE feedback ADD INDEX idx_product (product_name);
-- ALTER TABLE feedback ADD INDEX idx_category (category);
-- ALTER TABLE feedback ADD INDEX idx_created (created_at);
