-- Run this to upgrade existing database to E-commerce schema
-- Run each statement; ignore errors if column/index already exists

USE openfeedback;

-- Add category column
ALTER TABLE feedback ADD COLUMN category VARCHAR(100) DEFAULT NULL AFTER product_name;

-- Add is_suspicious for fake review detection
ALTER TABLE feedback ADD COLUMN is_suspicious BOOLEAN DEFAULT FALSE AFTER created_at;

-- Add indexes (ignore if exists)
CREATE INDEX idx_product ON feedback(product_name);
CREATE INDEX idx_category ON feedback(category);
CREATE INDEX idx_created ON feedback(created_at);
