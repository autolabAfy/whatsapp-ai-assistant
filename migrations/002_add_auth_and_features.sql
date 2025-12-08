-- Migration: Add Authentication, Images, and Push Notifications
-- Run this after deploying to Railway

-- Add password hash column to agents table
ALTER TABLE agents ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Add image_url column to properties table
ALTER TABLE properties ADD COLUMN IF NOT EXISTS image_url TEXT;

-- Create device_tokens table for push notifications
CREATE TABLE IF NOT EXISTS device_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('ios', 'android')),
    is_active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id, token)
);

CREATE INDEX IF NOT EXISTS idx_device_tokens_agent ON device_tokens(agent_id);
CREATE INDEX IF NOT EXISTS idx_device_tokens_active ON device_tokens(is_active) WHERE is_active = TRUE;

-- Update demo agent with password (password: demo123)
UPDATE agents
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYVXp.wO.6m'
WHERE email = 'demo@example.com';

-- Add some sample property images (placeholder paths)
UPDATE properties
SET image_url = 'uploads/properties/sample_' || property_id::text || '.jpg'
WHERE image_url IS NULL
LIMIT 2;

COMMENT ON TABLE device_tokens IS 'Device tokens for push notifications';
COMMENT ON COLUMN agents.password_hash IS 'Bcrypt hashed password for authentication';
COMMENT ON COLUMN properties.image_url IS 'Relative path to property image file';
