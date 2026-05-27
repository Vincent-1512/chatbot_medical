-- Kích hoạt extension pgvector (BẮT BUỘC để lưu embedding)
CREATE EXTENSION IF NOT EXISTS vector;

-- Dọn dẹp bảng cũ nếu có
DROP TABLE IF EXISTS System_Configs CASCADE;
DROP TABLE IF EXISTS Staff_Accounts CASCADE;
DROP TABLE IF EXISTS Session_Recommendations CASCADE;
DROP TABLE IF EXISTS Session_Disease_Scores CASCADE;
DROP TABLE IF EXISTS Session_Symptoms CASCADE;
DROP TABLE IF EXISTS Message_Logs CASCADE;
DROP TABLE IF EXISTS Chat_Sessions CASCADE;
DROP TABLE IF EXISTS Medical_Profiles CASCADE;
DROP TABLE IF EXISTS Patients CASCADE;
DROP TABLE IF EXISTS Knowledge_Chunks CASCADE;
DROP TABLE IF EXISTS Knowledge_Rules CASCADE;
DROP TABLE IF EXISTS Diseases CASCADE;
DROP TABLE IF EXISTS Symptom_Synonyms CASCADE;
DROP TABLE IF EXISTS Symptoms CASCADE;
DROP TABLE IF EXISTS Specialties CASCADE;

-- ==========================================
-- MODULE 1: HỆ TRI THỨC (KNOWLEDGE BASE)
-- ==========================================

CREATE TABLE Specialties (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE Symptoms (
    id SERIAL PRIMARY KEY,
    code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    question_text VARCHAR(200),
    is_red_flag BOOLEAN DEFAULT FALSE,
    embedding VECTOR(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE Symptom_Synonyms (
    id SERIAL PRIMARY KEY,
    symptom_id INT NOT NULL REFERENCES Symptoms(id) ON DELETE CASCADE,
    synonym VARCHAR(120) NOT NULL
);

CREATE TABLE Diseases (
    id SERIAL PRIMARY KEY,
    specialty_id INT NOT NULL REFERENCES Specialties(id),
    icd_code VARCHAR(20) UNIQUE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    embedding VECTOR(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE Knowledge_Rules (
    id SERIAL PRIMARY KEY,
    disease_id INT NOT NULL REFERENCES Diseases(id) ON DELETE CASCADE,
    symptom_id INT NOT NULL REFERENCES Symptoms(id) ON DELETE CASCADE,
    weight FLOAT NOT NULL,
    is_mandatory BOOLEAN DEFAULT FALSE,
    is_exclusion BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE Knowledge_Chunks (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(30),
    source_id INT,
    chunk_text TEXT NOT NULL,
    mapped_symptoms TEXT,
    embedding VECTOR(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- ==========================================
-- MODULE 2: BỆNH NHÂN, HỒ SƠ & CHAT
-- ==========================================

CREATE TABLE Patients (
    id SERIAL PRIMARY KEY,
    external_patient_id VARCHAR(255) UNIQUE, -- Đồng bộ từ hệ thống Web phòng khám
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    gender VARCHAR(10),
    dob DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE Medical_Profiles (
    id SERIAL PRIMARY KEY,
    patient_id INT UNIQUE NOT NULL REFERENCES Patients(id) ON DELETE CASCADE,
    height FLOAT,
    weight FLOAT,
    blood_type VARCHAR(5),
    allergies TEXT,
    underlying_conditions TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Chat_Sessions (
    id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES Patients(id) ON DELETE CASCADE,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'in_progress',
    initial_complaint TEXT,
    suggested_specialty_id INT REFERENCES Specialties(id),
    triage_urgency VARCHAR(20),
    disclaimer_shown BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Message_Logs (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES Chat_Sessions(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL,
    message_text TEXT NOT NULL,
    metadata JSONB,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Session_Symptoms (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES Chat_Sessions(id) ON DELETE CASCADE,
    symptom_id INT NOT NULL REFERENCES Symptoms(id) ON DELETE CASCADE,
    is_present BOOLEAN NOT NULL,
    confidence FLOAT DEFAULT 0.8,
    source VARCHAR(20),
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Session_Disease_Scores (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES Chat_Sessions(id) ON DELETE CASCADE,
    disease_id INT NOT NULL REFERENCES Diseases(id) ON DELETE CASCADE,
    hybrid_score FLOAT NOT NULL,
    rank INT,
    is_doctor_verified BOOLEAN,
    actual_disease_id INT REFERENCES Diseases(id)
);

CREATE TABLE Session_Recommendations (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES Chat_Sessions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- MODULE 3: TÀI KHOẢN & HỆ THỐNG
-- ==========================================

CREATE TABLE Staff_Accounts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    specialty_id INT REFERENCES Specialties(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE System_Configs (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value VARCHAR(200) NOT NULL,
    description TEXT,
    updated_by INT REFERENCES Staff_Accounts(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);