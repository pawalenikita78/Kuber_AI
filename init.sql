-- init.sql
CREATE DATABASE IF NOT EXISTS gold_investments;
USE gold_investments;

CREATE USER IF NOT EXISTS 'gold_user'@'%' IDENTIFIED BY '12345niki';
GRANT ALL PRIVILEGES ON gold_investments.* TO 'gold_user'@'%';
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS django_migrations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied DATETIME(6) NOT NULL
);

CREATE TABLE IF NOT EXISTS gold_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    plan_type VARCHAR(50) NOT NULL,     -- 'Digital','ETF','SGB','SIP','MutualFund'
    duration_months INT NULL,           -- NULL for flexible
    min_investment FLOAT NOT NULL,      -- Rupees
    returns VARCHAR(100) NULL,          -- e.g., "2.5% + market appreciation"
    description TEXT NULL
);

INSERT INTO gold_plans (name, plan_type, duration_months, min_investment, returns, description)
VALUES
('Digital Gold - EasyBuy', 'Digital', NULL, 50.0, 'Market appreciation', 'Start your investment in 24k 99.99% pure gold – securely stored and insured.'),
('Digital Gold Monthly', 'Digital', 3, 25.0, 'Market appreciation', 'Start your investment in 24k 99.99% pure gold – securely stored and insured.');


