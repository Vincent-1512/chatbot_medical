-- Kích hoạt extension pgvector (BẮT BUỘC để lưu embedding)
CREATE EXTENSION IF NOT EXISTS vector;

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
    embedding VECTOR(1024) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- MODULE 2: BỆNH NHÂN & CHAT
-- ==========================================

CREATE TABLE Patients (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE Chat_Sessions (
    id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES Patients(id),
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
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Session_Symptoms (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES Chat_Sessions(id) ON DELETE CASCADE,
    symptom_id INT NOT NULL REFERENCES Symptoms(id),
    is_present BOOLEAN NOT NULL,
    confidence FLOAT DEFAULT 0.8,
    source VARCHAR(20) DEFAULT 'user',
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Session_Disease_Scores (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES Chat_Sessions(id) ON DELETE CASCADE,
    disease_id INT NOT NULL REFERENCES Diseases(id),
    hybrid_score FLOAT NOT NULL,
    rank INT
);

CREATE TABLE Session_Recommendations (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES Chat_Sessions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);