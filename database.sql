-- Database Schema for Ehsan Charity Management System (MySQL/XAMPP)

CREATE DATABASE IF NOT EXISTS ehsan_db;
USE ehsan_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager', 'clerk') NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Beneficiaries Table
CREATE TABLE IF NOT EXISTS beneficiaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    national_id VARCHAR(12) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    family_size INT NOT NULL,
    case_type ENUM('orphan', 'widow', 'needy', 'patient') NOT NULL,
    income DECIMAL(10,2) NOT NULL,
    need_score FLOAT DEFAULT 0,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Aid Types Table
CREATE TABLE IF NOT EXISTS aid_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category ENUM('financial', 'food', 'medical') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    sponsor VARCHAR(255)
);

-- 4. Distributions Table
CREATE TABLE IF NOT EXISTS distributions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    beneficiary_id INT NOT NULL,
    aid_id INT NOT NULL,
    user_id INT NOT NULL,
    distribution_date DATE NOT NULL,
    FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id),
    FOREIGN KEY (aid_id) REFERENCES aid_types(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Initial Data
INSERT INTO users (username, password, role, name) VALUES 
('admin', 'admin123', 'admin', 'أدمن النظام'),
('manager', 'mngr123', 'manager', 'مدير الجمعية'),
('clerk', 'clrk123', 'clerk', 'موظف إدخال');

INSERT INTO aid_types (name, category, amount, sponsor) VALUES 
('منحة مالية عاجلة', 'financial', 500, 'الجمعية الرئيسية'),
('سلة غذائية', 'food', 150, 'متبرع فاعل خير');
