# WhatsApp AI Assistant MVP - Setup and Operation

## Purpose
This directive covers the setup, testing, and operation of the WhatsApp AI Assistant MVP. The system receives WhatsApp messages via webhooks, generates AI responses (with mock fallback), and maintains complete conversation history in PostgreSQL.

## Architecture Overview

**3-Layer System:**
- **Layer 1 (Directive):** This document - defines setup procedures, operational steps, and troubleshooting
- **Layer 2 (Orchestration):** FastAPI application orchestrates webhook processing, database operations, and AI response generation
- **Layer 3 (Execution):** Python scripts in `execution/` handle deterministic operations (database queries, message sending, AI generation)

**Key Components:**
- FastAPI server (`main.py`) - REST API and webhook endpoints
- PostgreSQL database - 9 tables for conversations, messages, properties, agents
- Redis - Caching, distributed locks, webhook deduplication
- Green API - WhatsApp Web API integration
- Anthropic Claude - AI response generation (with mock fallback)
- Cloudflare Tunnel - Public URL for webhook receiving

## Prerequisites

**System Requirements:**
- macOS (tested on Darwin 24.6.0)
- Python 3.9.6+
- Homebrew package manager
- PostgreSQL 14+
- Redis 8+

**API Credentials:**
- Green API instance ID and token (for WhatsApp integration)
- Anthropic API key (optional - mock mode works without it)

## Setup Steps

### 1. Install System Dependencies

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to PATH (ARM Mac)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Install PostgreSQL and Redis
brew install postgresql@14 redis

# Start services
brew services start postgresql@14
brew services start redis

# Verify installations
psql postgres -c "SELECT version();"
redis-cli ping  # Should return PONG
```

### 2. Create Python Virtual Environment

```bash
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant

# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Important:** If you get dependency conflicts, ensure `requirements.txt` has:
- `redis==4.6.0` (NOT 5.x, incompatible with Celery)
- `celery[redis]==5.3.4` (single entry, not duplicate)
- `anthropic==0.75.0` (upgraded for messages API)

### 3. Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required Configuration:**
```bash
# Database (local PostgreSQL)
DATABASE_URL=postgresql://localhost:5432/whatsapp_ai_assistant

# Redis (local)
REDIS_URL=redis://localhost:6379/0

# Green API (WhatsApp)
GREEN_API_BASE_URL=https://7105.api.green-api.com
GREEN_API_INSTANCE_ID=7105342242
GREEN_API_TOKEN=a4709845232254bd195fdf4ea47f23d6c87fc7809fb89447ea1

# Anthropic API (optional - mock mode works without it)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Environment
ENVIRONMENT=development  # Enables mock AI fallback
APP_HOST=0.0.0.0
APP_PORT=8000

# AI Configuration
AI_MODEL=claude-3-sonnet-20240229
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1024
```

### 4. Setup Database

```bash
# Create database
createdb whatsapp_ai_assistant

# Run migrations
psql whatsapp_ai_assistant < migrations/001_initial_schema.sql

# Verify tables created
psql whatsapp_ai_assistant -c "\dt"
```

**Expected Output:** 9 tables created
- agents
- conversations
- messages
- properties
- followups
- appointments
- webhook_logs
- escalations
- sent_messages_log

**Demo Data Created:**
- Demo agent: `email='demo@example.com'`, `agent_id='3b5ab91d-ddfb-48cb-a110-acb5144a89fa'`
- 2 sample properties (Marina Bay Condo, Orchard HDB)

### 5. Start the Application

```bash
# Activate venv (if not already activated)
source venv/bin/activate

# Create logs directory
mkdir -p logs

# Start server
python main.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     WhatsApp AI Assistant starting up...
INFO:     Database connected successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Access Points:**
- UI: http://localhost:8000/inbox
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 6. Setup Public URL (for Webhooks)

**Use Cloudflare Tunnel (recommended):**

```bash
# In a new terminal
brew install cloudflare/cloudflare/cloudflared

# Create tunnel
cloudflared tunnel --url http://localhost:8000
```

**Output:** Public URL like `https://gadgets-city-diving-blowing.trycloudflare.com`

**Configure Green API Webhook:**
1. Go to Green API dashboard
2. Navigate to Settings → Webhooks
3. Set webhook URL: `https://your-tunnel-url.trycloudflare.com/webhook/greenapi`
4. Enable "Incoming Messages"
5. Save

## MVP Operation

### Testing Without WhatsApp (Local UI Testing)

**Access UI:**
```bash
# Open in browser
http://localhost:8000/inbox
```

**Create Test Data:**
```sql
-- Connect to database
psql whatsapp_ai_assistant

-- Create test conversation
INSERT INTO conversations (agent_id, contact_number, contact_name, current_mode)
VALUES ('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', '1234567890', 'Test User', 'AI')
RETURNING conversation_id;

-- Add test messages (replace conversation_id)
INSERT INTO messages (conversation_id, sender_type, message_text)
VALUES
('conversation-id-here', 'USER', 'Hi! I want to rent a 3-bedroom condo in Marina Bay'),
('conversation-id-here', 'AI', 'Thank you for your interest! Let me check our available properties...');
```

**View in UI:** Refresh http://localhost:8000/inbox

### Testing with WhatsApp (Full End-to-End)

**Prerequisites:**
- Cloudflare tunnel running
- Green API webhook configured
- WhatsApp number connected to Green API instance

**Send Test Message:**
1. Send WhatsApp message to your Green API connected number
2. System receives webhook at `/webhook/greenapi`
3. AI generates response (mock or Claude API)
4. Response saved to database
5. System attempts to send response via WhatsApp

**Check Logs:**
```bash
# Terminal 1: Application logs
tail -f logs/app.log

# Terminal 2: Database logs
psql whatsapp_ai_assistant
SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 5;
SELECT * FROM messages ORDER BY timestamp DESC LIMIT 5;
```

### Mock AI Mode (Development)

When `ENVIRONMENT=development` in `.env`, the system uses intelligent mock responses if Claude API fails:

**Property Context Detection:**
- Detects location, property type, price, bedrooms from user message
- Searches database for matching properties
- Generates contextual response with property details

**Mock Response Examples:**

**With Properties Found:**
```
Thank you for your interest! I found a great property for you:

I found 1 property:
1. Marina Bay Condo
   Marina Bay - $1,200,000
   3 bed, 2 bath

This property matches what you're looking for. Would you like to schedule a viewing?
```

**No Properties Found:**
```
Thank you for reaching out! I'd be happy to help you find the perfect property.
Could you tell me a bit more about what you're looking for? For example, preferred
location, number of bedrooms, and your budget range?
```

### Database-First Response Pattern (Critical for MVP)

**Implementation:** `execution/webhook_handler.py`

The system saves AI responses to the database BEFORE attempting to send to WhatsApp. This ensures complete conversation history even if WhatsApp sending fails (e.g., expired Green API token).

**Flow:**
1. Receive webhook with user message
2. Save user message to database
3. Generate AI response (Claude or mock)
4. **Save AI response to database FIRST**
5. **Then** attempt to send via WhatsApp (may fail)
6. Return status indicating response saved

**Response Statuses:**
- `"response_sent": "sent"` - Successfully sent to WhatsApp
- `"response_sent": "failed"` - Saved to DB but WhatsApp send failed
- `"response_sent": "saved_only"` - Saved to DB, WhatsApp send not attempted

**Benefits:**
- Complete conversation history always preserved
- System continues working even when WhatsApp API fails
- No data loss on external service failures
- Can review and manually send failed messages later

## API Endpoints

### Health Check
```bash
GET /health
# Returns: {"status":"ok","database":"ok","environment":"development"}
```

### Conversations
```bash
# Get all conversations for an agent
GET /api/agents/{agent_id}/conversations

# Get single conversation
GET /api/conversations/{conversation_id}

# Get conversation messages
GET /api/conversations/{conversation_id}/messages

# Toggle conversation mode
POST /api/conversations/toggle-mode
Body: {"conversation_id": "...", "mode": "AI" or "HUMAN"}
```

### Properties
```bash
# Search properties
POST /api/properties/search
Body: {"agent_id": "...", "query": "Marina Bay 3 bedroom"}

# Get property details
GET /api/properties/{property_id}

# Get all properties for agent
GET /api/agents/{agent_id}/properties
```

### Webhooks
```bash
# Green API webhook (called by Green API, not manually)
POST /webhook/greenapi
```

## Troubleshooting

### Server Won't Start

**Check port 8000:**
```bash
lsof -i :8000
# If in use, kill process:
kill -9 {PID}
```

**Check Python errors:**
```bash
python main.py
# Look for stack trace in output
```

### Database Connection Error

**Check PostgreSQL running:**
```bash
brew services list | grep postgresql
# If not running:
brew services start postgresql@14
```

**Test connection:**
```bash
psql whatsapp_ai_assistant -c "SELECT 1;"
```

**Verify DATABASE_URL:**
```bash
cat .env | grep DATABASE_URL
```

### Redis Connection Error

**Check Redis running:**
```bash
redis-cli ping
# Should return PONG
```

**Start if not running:**
```bash
brew services start redis
```

### Messages Not Received

**Check webhook logs:**
```sql
psql whatsapp_ai_assistant -c "SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 5;"
```

**Verify Green API instance connected:**
```bash
curl "https://api.green-api.com/waInstance7105342242/getStateInstance/TOKEN"
# Should return: "authorized"
```

**Check webhook URL in Green API dashboard:**
- Must be: `https://your-tunnel-url.trycloudflare.com/webhook/greenapi`
- Cloudflare tunnel must be running

### AI Not Responding

**Check conversation mode:**
```sql
psql whatsapp_ai_assistant -c "SELECT conversation_id, current_mode FROM conversations WHERE contact_number = '1234567890';"
# Should be 'AI' not 'HUMAN'
```

**Check logs for errors:**
```bash
tail -f logs/app.log | grep ERROR
```

**Verify mock mode enabled:**
```bash
cat .env | grep ENVIRONMENT
# Should be: ENVIRONMENT=development
```

### WhatsApp Sending Fails (401 Unauthorized)

**This is expected with expired Green API tokens.**

**Workaround:** The database-first pattern ensures responses are saved even when sending fails.

**Check response saved:**
```sql
SELECT m.timestamp, m.sender_type, m.message_text
FROM messages m
WHERE m.conversation_id = 'conversation-id-here'
ORDER BY m.timestamp DESC;
```

**Get valid Green API token:**
1. Log into Green API dashboard
2. Navigate to API → Instance Settings
3. Copy new token
4. Update `.env` with `GREEN_API_TOKEN=new_token`
5. Restart server

## Common Operational Tasks

### Update Agent Persona

```sql
psql whatsapp_ai_assistant

UPDATE agents
SET assistant_name = 'Sarah',
    speaking_style = 'friendly',
    custom_instruction = 'You are warm and helpful. Focus on scheduling viewings.'
WHERE agent_id = '3b5ab91d-ddfb-48cb-a110-acb5144a89fa';
```

### Add Properties

```sql
INSERT INTO properties (agent_id, title, property_type, location, price, bedrooms, bathrooms, size_sqft)
VALUES (
    '3b5ab91d-ddfb-48cb-a110-acb5144a89fa',
    'Sentosa Cove Villa',
    'landed',
    'Sentosa',
    5000000,
    5,
    4,
    3500
);
```

### Toggle Conversation Mode

```bash
# Via API
curl -X POST http://localhost:8000/api/conversations/toggle-mode \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "...", "mode": "HUMAN"}'

# Or via SQL
UPDATE conversations
SET current_mode = 'HUMAN'
WHERE conversation_id = '...';
```

### View Recent Activity

```sql
-- Recent conversations
SELECT conversation_id, contact_name, current_mode, last_message_preview
FROM conversations
ORDER BY last_message_timestamp DESC
LIMIT 10;

-- Recent messages
SELECT c.contact_name, m.sender_type, m.message_text, m.timestamp
FROM messages m
JOIN conversations c ON m.conversation_id = c.conversation_id
ORDER BY m.timestamp DESC
LIMIT 20;

-- Recent webhook logs
SELECT webhook_id, instance_id, event_type, status, timestamp
FROM webhook_logs
ORDER BY timestamp DESC
LIMIT 10;
```

### Backup Database

```bash
# Full backup
pg_dump whatsapp_ai_assistant > backup_$(date +%Y%m%d).sql

# Restore
dropdb whatsapp_ai_assistant
createdb whatsapp_ai_assistant
psql whatsapp_ai_assistant < backup_20241208.sql
```

## MVP Success Criteria

**System is working correctly when:**
- ✅ Server starts without errors
- ✅ Health check returns `{"status":"ok"}`
- ✅ UI accessible at http://localhost:8000/inbox
- ✅ Cloudflare tunnel running with public URL
- ✅ Webhooks received and logged in `webhook_logs`
- ✅ User messages saved to `messages` table
- ✅ AI responses generated (mock or Claude)
- ✅ AI responses saved to `messages` table
- ✅ Conversations visible in UI
- ⏳ WhatsApp sending (requires valid Green API token)

**Known Limitations:**
- WhatsApp sending requires valid Green API token (may be expired)
- Claude API access may not be available (mock mode works)
- Cloudflare tunnel URL changes on restart (need to update Green API webhook)

## Next Steps Beyond MVP

**Immediate (Week 1-2):**
- Get valid Green API token for WhatsApp sending
- Test full end-to-end flow with real WhatsApp messages
- Add more sample properties for testing
- Customize agent persona

**Short-term (Month 1):**
- Implement authentication system
- Add property management UI
- Setup Sentry for error tracking
- Deploy to production (Railway, Render, or VPS)

**Medium-term (Month 2-3):**
- Follow-up automation (2h, 24h, 72h)
- Analytics dashboard
- Enhanced property matching (semantic search)
- Multi-language support

See `NEXT_STEPS.md` for complete roadmap.

## Support and Documentation

**Quick Reference:** `QUICK_REFERENCE.md` - Common commands and operations
**Architecture:** `ARCHITECTURE.md` - System design and component details
**Setup Guide:** `SETUP.md` - Detailed setup instructions
**Project Summary:** `PROJECT_SUMMARY.md` - Overview and features

## Key Learnings

**Database-First Pattern:**
Always save critical data (like AI responses) to the database BEFORE attempting external API calls. This prevents data loss when external services fail.

**Mock AI for Development:**
Implement intelligent mock responses for development and testing. This allows full system testing without dependency on external AI APIs.

**Graceful Degradation:**
System should continue working even when external services fail. Return status codes that indicate partial success (e.g., "saved_only" vs "sent").

**Timestamp Handling:**
Use `datetime.now()` for timestamp fields in database operations, not SQL string literals like "CURRENT_TIMESTAMP" in parameterized queries.

**Type Casting:**
Be explicit with type casting in SQL queries when comparing different types (e.g., `WHERE green_api_instance_id = %s::TEXT`).

**Dependencies:**
- redis 4.6.0 required for Celery compatibility (not 5.x)
- anthropic 0.75.0 required for messages API (not 0.7.8)
- Remove duplicate and deprecated packages from requirements.txt

**Public URLs:**
Cloudflare Tunnel is the most reliable free option for exposing local webhooks (ngrok requires auth, localtunnel has connection issues).
