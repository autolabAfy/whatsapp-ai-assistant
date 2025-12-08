-- WhatsApp AI Assistant Database Schema
-- PostgreSQL

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- AGENTS TABLE
-- ============================================
CREATE TABLE agents (
    agent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    whatsapp_number VARCHAR(50) UNIQUE,

    -- Green API credentials
    green_api_instance_id VARCHAR(100),
    green_api_token VARCHAR(255),

    -- AI Persona Configuration
    assistant_name VARCHAR(100) DEFAULT 'Assistant',
    speaking_style VARCHAR(20) DEFAULT 'friendly' CHECK (speaking_style IN ('professional', 'friendly', 'casual', 'premium')),
    tone_slider INT DEFAULT 5 CHECK (tone_slider BETWEEN 1 AND 10),
    personality_flags TEXT[] DEFAULT '{}',
    custom_instruction TEXT,

    -- Metadata
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_agents_email ON agents(email);
CREATE INDEX idx_agents_whatsapp ON agents(whatsapp_number);

-- ============================================
-- CONVERSATIONS TABLE
-- ============================================
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    contact_number VARCHAR(50) NOT NULL,
    contact_name VARCHAR(255),

    -- Control Mode
    current_mode VARCHAR(10) DEFAULT 'AI' CHECK (current_mode IN ('AI', 'HUMAN')),
    last_mode_change_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_mode_changed_by UUID REFERENCES agents(agent_id),

    -- Conversation State
    last_message_timestamp TIMESTAMP,
    last_message_preview TEXT,
    unread_count INT DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint: one conversation per agent + contact
    UNIQUE(agent_id, contact_number)
);

CREATE INDEX idx_conversations_agent ON conversations(agent_id);
CREATE INDEX idx_conversations_mode ON conversations(current_mode);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_timestamp DESC);

-- ============================================
-- MESSAGES TABLE
-- ============================================
CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    -- Message Details
    sender_type VARCHAR(10) NOT NULL CHECK (sender_type IN ('USER', 'AI', 'HUMAN')),
    message_text TEXT NOT NULL,

    -- WhatsApp Details
    whatsapp_message_id VARCHAR(255),

    -- Metadata
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered BOOLEAN DEFAULT FALSE,
    read_by_agent BOOLEAN DEFAULT FALSE,

    -- For deduplication
    message_fingerprint VARCHAR(64)
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, timestamp DESC);
CREATE INDEX idx_messages_fingerprint ON messages(message_fingerprint);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);

-- ============================================
-- PROPERTIES TABLE
-- ============================================
CREATE TABLE properties (
    property_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- Basic Details
    title VARCHAR(255) NOT NULL,
    property_type VARCHAR(50) NOT NULL CHECK (property_type IN ('condo', 'HDB', 'landed', 'commercial', 'other')),
    location VARCHAR(255) NOT NULL,
    price DECIMAL(12, 2) NOT NULL,

    -- Availability
    availability VARCHAR(20) DEFAULT 'available' CHECK (availability IN ('available', 'pending', 'sold', 'rented')),
    available_from DATE,

    -- Property Specs
    bedrooms INT,
    bathrooms INT,
    size_sqft INT,
    floor_level INT,

    -- Rich Details
    amenities TEXT[],
    key_selling_points TEXT,
    viewing_instructions TEXT,
    internal_notes TEXT,

    -- Media (for future)
    image_urls TEXT[],

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_archived BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_properties_agent ON properties(agent_id);
CREATE INDEX idx_properties_type ON properties(property_type);
CREATE INDEX idx_properties_location ON properties(location);
CREATE INDEX idx_properties_availability ON properties(availability);
CREATE INDEX idx_properties_price ON properties(price);

-- ============================================
-- FOLLOWUPS TABLE
-- ============================================
CREATE TABLE followups (
    followup_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    -- Schedule
    scheduled_for TIMESTAMP NOT NULL,
    followup_type VARCHAR(50) DEFAULT 'general' CHECK (followup_type IN ('general', 'viewing_reminder', 'no_response')),

    -- Message
    message_template TEXT,

    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'cancelled', 'failed')),
    sent_at TIMESTAMP,
    cancelled_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_followups_conversation ON followups(conversation_id);
CREATE INDEX idx_followups_scheduled ON followups(scheduled_for);
CREATE INDEX idx_followups_status ON followups(status);

-- Only one pending follow-up per conversation
CREATE UNIQUE INDEX idx_followups_unique_pending
ON followups(conversation_id)
WHERE status = 'pending';

-- ============================================
-- APPOINTMENTS TABLE
-- ============================================
CREATE TABLE appointments (
    appointment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    property_id UUID REFERENCES properties(property_id) ON DELETE SET NULL,
    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- Appointment Details
    contact_name VARCHAR(255),
    contact_number VARCHAR(50),
    scheduled_datetime TIMESTAMP NOT NULL,

    -- Status
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show')),

    -- Notes
    notes TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_appointments_agent ON appointments(agent_id);
CREATE INDEX idx_appointments_property ON appointments(property_id);
CREATE INDEX idx_appointments_datetime ON appointments(scheduled_datetime);
CREATE INDEX idx_appointments_status ON appointments(status);

-- ============================================
-- WEBHOOK_LOGS TABLE (for debugging)
-- ============================================
CREATE TABLE webhook_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_fingerprint VARCHAR(64),
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    is_duplicate BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_webhook_logs_fingerprint ON webhook_logs(webhook_fingerprint);
CREATE INDEX idx_webhook_logs_timestamp ON webhook_logs(timestamp DESC);

-- ============================================
-- ESCALATIONS TABLE (for analytics)
-- ============================================
CREATE TABLE escalations (
    escalation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    trigger_type VARCHAR(50) NOT NULL,
    triggering_message TEXT,
    ai_handoff_message TEXT,

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_escalations_conversation ON escalations(conversation_id);
CREATE INDEX idx_escalations_type ON escalations(trigger_type);
CREATE INDEX idx_escalations_timestamp ON escalations(timestamp DESC);

-- ============================================
-- SENT_MESSAGES_LOG (for idempotency)
-- ============================================
CREATE TABLE sent_messages_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    idempotency_key VARCHAR(255) UNIQUE NOT NULL,
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    green_api_response JSONB,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sent_messages_idempotency ON sent_messages_log(idempotency_key);
CREATE INDEX idx_sent_messages_conversation ON sent_messages_log(conversation_id);

-- ============================================
-- TRIGGER: Update updated_at timestamp
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_properties_updated_at BEFORE UPDATE ON properties
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- SAMPLE DATA (for testing)
-- ============================================

-- Sample Agent
INSERT INTO agents (email, password_hash, full_name, whatsapp_number, assistant_name, speaking_style)
VALUES (
    'demo@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYH.sa4sN9i', -- password: "demo123"
    'Demo Agent',
    '1234567890',
    'Sarah',
    'friendly'
);

-- Sample Properties
INSERT INTO properties (agent_id, title, property_type, location, price, bedrooms, bathrooms, size_sqft, availability, key_selling_points)
SELECT
    agent_id,
    'Marina Bay Condo',
    'condo',
    'Marina Bay',
    1200000,
    3,
    2,
    1200,
    'available',
    'Stunning sea view, swimming pool, 24/7 security, near MRT'
FROM agents WHERE email = 'demo@example.com'
LIMIT 1;

INSERT INTO properties (agent_id, title, property_type, location, price, bedrooms, bathrooms, size_sqft, availability, key_selling_points)
SELECT
    agent_id,
    'Orchard HDB',
    'HDB',
    'Orchard',
    650000,
    4,
    2,
    1000,
    'available',
    'Central location, renovated kitchen, near shopping district'
FROM agents WHERE email = 'demo@example.com'
LIMIT 1;

-- ============================================
-- VIEWS (for common queries)
-- ============================================

-- Active conversations view
CREATE VIEW active_conversations AS
SELECT
    c.conversation_id,
    c.agent_id,
    c.contact_number,
    c.contact_name,
    c.current_mode,
    c.last_message_timestamp,
    c.last_message_preview,
    c.unread_count,
    COUNT(m.message_id) as total_messages
FROM conversations c
LEFT JOIN messages m ON c.conversation_id = m.conversation_id
WHERE c.last_message_timestamp > NOW() - INTERVAL '7 days'
GROUP BY c.conversation_id;

-- Agent dashboard stats
CREATE VIEW agent_stats AS
SELECT
    a.agent_id,
    a.full_name,
    COUNT(DISTINCT c.conversation_id) as total_conversations,
    COUNT(DISTINCT p.property_id) as total_properties,
    COUNT(DISTINCT CASE WHEN c.current_mode = 'AI' THEN c.conversation_id END) as ai_mode_count,
    COUNT(DISTINCT CASE WHEN c.current_mode = 'HUMAN' THEN c.conversation_id END) as human_mode_count
FROM agents a
LEFT JOIN conversations c ON a.agent_id = c.agent_id
LEFT JOIN properties p ON a.agent_id = p.agent_id
GROUP BY a.agent_id, a.full_name;
