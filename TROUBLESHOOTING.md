# WhatsApp AI Assistant MVP - Troubleshooting Guide

## Quick Diagnostics

Run these commands to quickly check system health:

```bash
# Check server running
curl http://localhost:8000/health

# Check PostgreSQL
psql whatsapp_ai_assistant -c "SELECT COUNT(*) FROM conversations;"

# Check Redis
redis-cli ping

# Check logs
tail -20 logs/app.log
```

---

## Server Issues

### Issue: Server Won't Start

**Symptoms:**
- `python main.py` hangs or shows error
- "Address already in use" error
- Import errors

**Diagnosis:**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Check for Python errors
python main.py
```

**Solutions:**

**Port Already in Use:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 {PID}

# Restart server
python main.py
```

**Import Errors:**
```bash
# Ensure venv activated
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list | grep -E "fastapi|uvicorn|psycopg2|redis|anthropic"
```

**Database Connection Error:**
See [Database Connection Issues](#issue-database-connection-error)

---

### Issue: 404 Not Found Errors

**Symptoms:**
- UI returns "not found in JSON"
- API endpoints return 404
- `/inbox` returns 404

**Diagnosis:**
```bash
# Check server logs
tail -f logs/app.log

# Test health endpoint
curl http://localhost:8000/health

# Test docs endpoint
curl http://localhost:8000/docs
```

**Solutions:**

**Missing HTML Routes:**
Ensure `main.py` has HTML serving routes:

```python
from fastapi.responses import HTMLResponse

@app.get("/inbox", response_class=HTMLResponse)
@app.get("/templates/inbox.html", response_class=HTMLResponse)
async def get_inbox():
    try:
        with open("templates/inbox.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Inbox UI not found")
```

**File Not Found:**
```bash
# Verify templates directory exists
ls -la templates/

# Verify inbox.html exists
cat templates/inbox.html | head -5
```

---

### Issue: Blank Screen in UI

**Symptoms:**
- UI loads but shows nothing
- No conversations visible
- Can't click anything

**Diagnosis:**
```bash
# Check browser console (F12) for JavaScript errors
# Check if API calls are working
curl http://localhost:8000/api/agents/3b5ab91d-ddfb-48cb-a110-acb5144a89fa/conversations

# Check database has data
psql whatsapp_ai_assistant -c "SELECT COUNT(*) FROM conversations;"
```

**Solutions:**

**No Test Data:**
```sql
-- Create test conversation
psql whatsapp_ai_assistant

INSERT INTO conversations (agent_id, contact_number, contact_name, current_mode)
VALUES ('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', '1234567890', 'Test User', 'AI')
RETURNING conversation_id;

-- Add test messages (use conversation_id from above)
INSERT INTO messages (conversation_id, sender_type, message_text)
VALUES
('conversation-id-here', 'USER', 'Hi! I need a property'),
('conversation-id-here', 'AI', 'I would be happy to help you find a property!');
```

**Wrong Agent ID:**
Update `templates/inbox.html`:
```javascript
// Line ~270
const agentId = '3b5ab91d-ddfb-48cb-a110-acb5144a89fa';  // Use actual agent ID
```

**JavaScript Error:**
- Open browser DevTools (F12)
- Check Console tab for errors
- Common issue: CORS errors (shouldn't happen on localhost)

---

## Database Issues

### Issue: Database Connection Error

**Symptoms:**
- "could not connect to server"
- "FATAL: database does not exist"
- "psycopg2.OperationalError"

**Diagnosis:**
```bash
# Check PostgreSQL running
brew services list | grep postgresql

# Check database exists
psql -l | grep whatsapp_ai_assistant

# Test connection
psql whatsapp_ai_assistant -c "SELECT 1;"

# Check .env configuration
cat .env | grep DATABASE_URL
```

**Solutions:**

**PostgreSQL Not Running:**
```bash
# Start PostgreSQL
brew services start postgresql@14

# Wait 5 seconds for startup
sleep 5

# Verify running
psql postgres -c "SELECT version();"
```

**Database Doesn't Exist:**
```bash
# Create database
createdb whatsapp_ai_assistant

# Run migrations
psql whatsapp_ai_assistant < migrations/001_initial_schema.sql

# Verify tables created
psql whatsapp_ai_assistant -c "\dt"
```

**Wrong DATABASE_URL:**
```bash
# Check .env
cat .env | grep DATABASE_URL
# Should be: DATABASE_URL=postgresql://localhost:5432/whatsapp_ai_assistant

# Update if wrong
nano .env
# Fix DATABASE_URL
# Save and restart server
```

---

### Issue: Type Mismatch Errors

**Symptoms:**
- "operator does not exist: character varying = bigint"
- "invalid input syntax for type timestamp"
- SQL errors in logs

**Diagnosis:**
```bash
# Check logs for SQL errors
tail -f logs/app.log | grep ERROR

# Common pattern:
# "WHERE green_api_instance_id = 7105342242"  <- integer
# But column type is VARCHAR
```

**Solutions:**

**Instance ID Type Mismatch:**

In `execution/identify_conversation.py`:
```python
# Use type casting
query = """
    SELECT agent_id, email, full_name, green_api_instance_id
    FROM agents
    WHERE green_api_instance_id = %s::TEXT
      AND is_active = TRUE
"""
return db.execute_one(query, (str(instance_id),))
```

**Timestamp String Literal:**

In `execution/webhook_handler.py`:
```python
# WRONG - String literal in parameterized query
db.update("conversations", {
    "last_message_timestamp": "CURRENT_TIMESTAMP",  # ❌
}, {"conversation_id": conversation_id})

# CORRECT - Use datetime object
from datetime import datetime

db.update("conversations", {
    "last_message_timestamp": datetime.now(),  # ✅
}, {"conversation_id": conversation_id})
```

---

## Redis Issues

### Issue: Redis Connection Error

**Symptoms:**
- "Error connecting to Redis"
- "Connection refused on localhost:6379"
- "redis.exceptions.ConnectionError"

**Diagnosis:**
```bash
# Check Redis running
redis-cli ping

# Check Redis port
lsof -i :6379

# Check .env configuration
cat .env | grep REDIS_URL
```

**Solutions:**

**Redis Not Running:**
```bash
# Start Redis
brew services start redis

# Verify running
redis-cli ping
# Should return: PONG

# Check version
redis-cli --version
```

**Wrong REDIS_URL:**
```bash
# Check .env
cat .env | grep REDIS_URL
# Should be: REDIS_URL=redis://localhost:6379/0

# Update if wrong
nano .env
# Fix REDIS_URL
# Save and restart server
```

**Clear Redis Cache (if corrupted):**
```bash
redis-cli FLUSHALL
# WARNING: This deletes all cached data
```

---

## Webhook Issues

### Issue: Messages Not Received

**Symptoms:**
- Send WhatsApp message, no response
- No webhook logs in database
- Green API shows messages but system doesn't process

**Diagnosis:**
```bash
# Check webhook logs
psql whatsapp_ai_assistant -c "SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 5;"

# Check Cloudflare tunnel running
# Should see output like: "https://gadgets-city-diving-blowing.trycloudflare.com"

# Test webhook manually
curl -X POST http://localhost:8000/webhook/greenapi \
  -H "Content-Type: application/json" \
  -d '{"typeWebhook":"incomingMessageReceived","senderData":{"sender":"1234567890@c.us","senderName":"Test"},"messageData":{"typeMessage":"textMessage","textMessageData":{"textMessage":"test"}},"instanceData":{"idInstance":"7105342242"}}'
```

**Solutions:**

**Cloudflare Tunnel Not Running:**
```bash
# Start tunnel
cloudflared tunnel --url http://localhost:8000

# Copy public URL (e.g., https://gadgets-city-diving-blowing.trycloudflare.com)
# Update Green API webhook URL
```

**Wrong Webhook URL in Green API:**
1. Go to Green API dashboard
2. Settings → Webhooks
3. Verify URL: `https://your-tunnel-url.trycloudflare.com/webhook/greenapi`
4. Enable "Incoming Messages"
5. Save

**Green API Instance Not Connected:**
```bash
# Check instance state
curl "https://api.green-api.com/waInstance7105342242/getStateInstance/TOKEN"

# Should return: "authorized"
# If "notAuthorized", scan QR code in Green API dashboard
```

**Server Not Running:**
```bash
# Check server status
curl http://localhost:8000/health

# If not running, start server
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant
source venv/bin/activate
python main.py
```

---

### Issue: Webhook Received but No Response

**Symptoms:**
- Webhook logged in database
- User message saved
- No AI response generated or sent

**Diagnosis:**
```bash
# Check webhook logs
psql whatsapp_ai_assistant -c "SELECT webhook_id, event_type, status, error_message FROM webhook_logs ORDER BY timestamp DESC LIMIT 3;"

# Check messages table
psql whatsapp_ai_assistant -c "SELECT conversation_id, sender_type, message_text FROM messages ORDER BY timestamp DESC LIMIT 5;"

# Check server logs
tail -f logs/app.log | grep ERROR
```

**Solutions:**

**Conversation in HUMAN Mode:**
```sql
-- Check conversation mode
SELECT conversation_id, current_mode FROM conversations WHERE contact_number = '1234567890';

-- If mode is 'HUMAN', toggle to 'AI'
UPDATE conversations SET current_mode = 'AI' WHERE conversation_id = 'conversation-id-here';
```

**AI Generation Failed:**
See [AI Not Responding](#issue-ai-not-responding)

**WhatsApp Send Failed:**
See [WhatsApp Sending Fails](#issue-whatsapp-sending-fails)

---

## AI Response Issues

### Issue: AI Not Responding

**Symptoms:**
- User message received
- No AI response generated
- Error logs show Anthropic API errors

**Diagnosis:**
```bash
# Check logs for AI errors
tail -f logs/app.log | grep -A 5 "Generating AI response"

# Check Anthropic API key
cat .env | grep ANTHROPIC_API_KEY

# Check environment setting
cat .env | grep ENVIRONMENT

# Test Anthropic API
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-sonnet-20240229","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

**Solutions:**

**Enable Mock Mode:**
```bash
# Edit .env
nano .env

# Set environment to development
ENVIRONMENT=development

# Save and restart server
```

**Mock mode will generate intelligent fallback responses when Claude API is unavailable.**

**Upgrade Anthropic SDK:**
```bash
source venv/bin/activate
pip install --upgrade anthropic

# Verify version
pip show anthropic | grep Version
# Should be 0.75.0 or higher
```

**Invalid API Key:**
```bash
# Update .env with valid key
nano .env
# Update: ANTHROPIC_API_KEY=sk-ant-api03-...

# Restart server
```

**Model Not Available:**
```bash
# Edit .env to use available model
nano .env

# Try these models in order:
# AI_MODEL=claude-3-sonnet-20240229
# AI_MODEL=claude-3-haiku-20240307
# AI_MODEL=claude-2.1

# Or use mock mode (ENVIRONMENT=development)
```

---

### Issue: Mock Responses Not Contextual

**Symptoms:**
- Mock AI working but responses generic
- Not mentioning properties
- Not using property context

**Diagnosis:**
```bash
# Check properties exist
psql whatsapp_ai_assistant -c "SELECT title, location FROM properties WHERE agent_id = '3b5ab91d-ddfb-48cb-a110-acb5144a89fa';"

# Check property search working
python execution/property_lookup.py 3b5ab91d-ddfb-48cb-a110-acb5144a89fa "Marina Bay"
```

**Solutions:**

**Add Sample Properties:**
```sql
psql whatsapp_ai_assistant

INSERT INTO properties (agent_id, title, property_type, location, price, bedrooms, bathrooms)
VALUES
('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', 'Marina Bay Luxury Condo', 'condo', 'Marina Bay', 1200000, 3, 2),
('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', 'Orchard Road Apartment', 'hdb', 'Orchard', 800000, 2, 1);
```

**Property Search Intent Detection:**
Review `execution/generate_ai_response.py` - should detect location, bedrooms, price from user message.

---

## WhatsApp Integration Issues

### Issue: WhatsApp Sending Fails

**Symptoms:**
- "401 Unauthorized"
- "Green API token expired"
- Response saved to database but not sent to WhatsApp

**Diagnosis:**
```bash
# Check sent messages log
psql whatsapp_ai_assistant -c "SELECT status, error_message FROM sent_messages_log ORDER BY timestamp DESC LIMIT 5;"

# Check server logs
tail -f logs/app.log | grep "WhatsApp send"

# Test Green API token
curl -X POST "https://7105.api.green-api.com/waInstance7105342242/sendMessage/TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chatId":"1234567890@c.us","message":"Test"}'
```

**Solutions:**

**System Already Handles This (Database-First Pattern):**

The MVP uses a database-first pattern where AI responses are saved BEFORE sending to WhatsApp. This means:
- ✅ Response is always saved to database
- ⏳ WhatsApp sending is attempted but may fail
- ✅ Conversation history is complete regardless

**Check Response Saved:**
```sql
SELECT m.timestamp, m.sender_type, m.message_text
FROM messages m
WHERE m.conversation_id = 'conversation-id-here'
ORDER BY m.timestamp DESC;
```

**Get New Green API Token:**
1. Log into Green API dashboard
2. Go to API → Instance Settings
3. Generate new token or copy existing
4. Update `.env`:
   ```bash
   nano .env
   # Update: GREEN_API_TOKEN=new_token_here
   ```
5. Restart server

**Verify Instance Connected:**
```bash
curl "https://api.green-api.com/waInstance7105342242/getStateInstance/TOKEN"
# Should return: "authorized"
```

---

### Issue: Messages Sent but User Doesn't Receive

**Symptoms:**
- logs show "sent successfully"
- Database shows response sent
- User doesn't receive WhatsApp message

**Diagnosis:**
```bash
# Check sent_messages_log
psql whatsapp_ai_assistant -c "SELECT message_preview, status, whatsapp_message_id FROM sent_messages_log ORDER BY timestamp DESC LIMIT 3;"

# Check Green API dashboard for delivery status
```

**Solutions:**

**Check WhatsApp Number Format:**
```python
# Should be: 1234567890@c.us
# NOT: +1234567890 or 1234567890
```

**Check Green API Instance:**
- Verify QR code scanned
- Check instance state: "authorized"
- Check phone has internet connection

**Check Message Queue:**
```bash
# Green API has message queue
# Messages may be delayed if connection issues
# Check Green API dashboard → Queue
```

---

## Dependency Issues

### Issue: Import Errors

**Symptoms:**
- "ModuleNotFoundError: No module named 'fastapi'"
- "ImportError: cannot import name 'X' from 'Y'"
- Version conflicts

**Diagnosis:**
```bash
# Check venv activated
which python
# Should show: .../whatsapp-ai-assistant/venv/bin/python

# Check packages installed
pip list

# Check specific packages
pip show fastapi uvicorn psycopg2-binary redis anthropic
```

**Solutions:**

**Virtual Environment Not Activated:**
```bash
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant
source venv/bin/activate
```

**Dependencies Not Installed:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Version Conflicts:**

Ensure `requirements.txt` has correct versions:
```
redis==4.6.0  # NOT 5.x (incompatible with Celery)
celery[redis]==5.3.4  # Single entry
anthropic==0.75.0  # For messages API
```

**Reinstall Dependencies:**
```bash
# Remove venv
rm -rf venv

# Recreate
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Issue: Anthropic SDK Errors

**Symptoms:**
- "'Anthropic' object has no attribute 'messages'"
- "anthropic.messages.create() not found"
- API format errors

**Diagnosis:**
```bash
# Check Anthropic version
pip show anthropic | grep Version

# Should be 0.75.0 or higher
```

**Solutions:**

**Upgrade Anthropic:**
```bash
source venv/bin/activate
pip install --upgrade anthropic

# Verify
pip show anthropic
```

**API Format (Old vs New):**

**Old SDK (0.7.8):**
```python
response = client.completion(
    prompt=f"Human: {message}\n\nAssistant:",
    model="claude-2",
    max_tokens_to_sample=1000
)
```

**New SDK (0.75.0):**
```python
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=[{"role": "user", "content": message}]
)
```

---

## Performance Issues

### Issue: Slow Response Times

**Symptoms:**
- Webhook takes >5 seconds to respond
- UI slow to load
- Database queries slow

**Diagnosis:**
```bash
# Check database query times
psql whatsapp_ai_assistant

\timing on
SELECT * FROM messages ORDER BY timestamp DESC LIMIT 100;

# Check server logs for slow operations
tail -f logs/app.log | grep -E "took|duration"

# Check Redis latency
redis-cli --latency
```

**Solutions:**

**Add Database Indexes:**
```sql
-- Check existing indexes
\di

-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversations_agent_id ON conversations(agent_id);
CREATE INDEX IF NOT EXISTS idx_properties_agent_id ON properties(agent_id);
```

**Optimize Database Queries:**
```sql
-- Use EXPLAIN ANALYZE to check query performance
EXPLAIN ANALYZE SELECT * FROM messages WHERE conversation_id = 'xxx';

-- Look for "Seq Scan" (bad) vs "Index Scan" (good)
```

**Clear Old Data:**
```sql
-- Archive old conversations
UPDATE conversations SET is_archived = TRUE WHERE last_message_timestamp < NOW() - INTERVAL '30 days';

-- Delete old webhook logs
DELETE FROM webhook_logs WHERE timestamp < NOW() - INTERVAL '7 days';
```

---

## Data Issues

### Issue: Duplicate Conversations

**Symptoms:**
- Multiple conversations with same contact
- Conversation history split across conversations

**Diagnosis:**
```sql
-- Find duplicate contacts
SELECT contact_number, COUNT(*) as count
FROM conversations
GROUP BY contact_number
HAVING COUNT(*) > 1;
```

**Solutions:**

**Merge Conversations (Manual):**
```sql
-- 1. Identify conversations to merge
SELECT conversation_id, contact_number, created_at
FROM conversations
WHERE contact_number = '1234567890'
ORDER BY created_at;

-- 2. Move messages to primary conversation
UPDATE messages
SET conversation_id = 'primary-conversation-id'
WHERE conversation_id IN ('duplicate-1-id', 'duplicate-2-id');

-- 3. Delete duplicate conversations
DELETE FROM conversations WHERE conversation_id IN ('duplicate-1-id', 'duplicate-2-id');
```

**Prevent Future Duplicates:**
Add unique constraint:
```sql
ALTER TABLE conversations ADD CONSTRAINT unique_agent_contact UNIQUE (agent_id, contact_number);
```

---

### Issue: Missing Messages

**Symptoms:**
- Conversation shows in UI but no messages
- Message count doesn't match database

**Diagnosis:**
```sql
-- Check message count
SELECT c.conversation_id, c.contact_name, COUNT(m.message_id) as message_count
FROM conversations c
LEFT JOIN messages m ON c.conversation_id = m.conversation_id
GROUP BY c.conversation_id, c.contact_name
HAVING COUNT(m.message_id) = 0;

-- Check for messages with NULL conversation_id
SELECT * FROM messages WHERE conversation_id IS NULL;
```

**Solutions:**

**Orphaned Messages:**
```sql
-- Find messages without conversation
SELECT message_id, message_text FROM messages WHERE conversation_id IS NULL;

-- Delete orphaned messages (if not needed)
DELETE FROM messages WHERE conversation_id IS NULL;
```

**Foreign Key Constraint:**
```sql
-- Ensure referential integrity
ALTER TABLE messages
ADD CONSTRAINT fk_messages_conversation
FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id);
```

---

## Environment Issues

### Issue: Environment Variables Not Loading

**Symptoms:**
- "GREEN_API_TOKEN not set"
- "DATABASE_URL not found"
- Config errors on startup

**Diagnosis:**
```bash
# Check .env exists
ls -la .env

# Check .env contents
cat .env

# Check env vars loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('DATABASE_URL'))"
```

**Solutions:**

**Create .env File:**
```bash
cp .env.example .env
nano .env
# Fill in all required values
```

**Load Environment:**
Ensure `config.py` has:
```python
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # Load .env file

class Settings(BaseSettings):
    database_url: str
    # ...
```

**Restart Server:**
```bash
# Environment variables loaded on startup
# Restart to pick up changes
# Ctrl+C then python main.py
```

---

## Common Error Messages

### "invalid input syntax for type timestamp: 'CURRENT_TIMESTAMP'"

**Solution:** Use `datetime.now()` instead of string literal
```python
from datetime import datetime
db.update("table", {"timestamp": datetime.now()}, {...})
```

### "operator does not exist: character varying = bigint"

**Solution:** Add type casting
```sql
WHERE green_api_instance_id = %s::TEXT
```

### "ModuleNotFoundError: No module named 'anthropic'"

**Solution:** Install dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Error code: 404 - model: claude-3-sonnet-20240229 not found"

**Solution:** Use mock mode
```bash
# Set in .env
ENVIRONMENT=development
```

### "401 Client Error: Unauthorized for url"

**Solution:** Database-first pattern already saves responses. Update Green API token when ready.

---

## Getting Help

### Check Logs
```bash
# Application logs
tail -f logs/app.log

# Database logs
psql whatsapp_ai_assistant -c "SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 5;"

# System logs
brew services list
```

### Review Documentation
- `QUICK_REFERENCE.md` - Common operations
- `SETUP.md` - Setup instructions
- `ARCHITECTURE.md` - System design
- `execution/README_DATABASE_FIRST_PATTERN.md` - Database-first pattern

### Common Diagnostic Commands
```bash
# Full system health check
curl http://localhost:8000/health
psql whatsapp_ai_assistant -c "SELECT 1;"
redis-cli ping
lsof -i :8000
brew services list

# Check recent activity
psql whatsapp_ai_assistant -c "SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 3;"
psql whatsapp_ai_assistant -c "SELECT * FROM messages ORDER BY timestamp DESC LIMIT 5;"
tail -20 logs/app.log
```

---

## MVP Status Checklist

Use this to verify MVP is working:

- [ ] Server starts without errors: `python main.py`
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] PostgreSQL running: `psql whatsapp_ai_assistant -c "SELECT 1;"`
- [ ] Redis running: `redis-cli ping`
- [ ] UI accessible: http://localhost:8000/inbox
- [ ] Database has demo data: `psql whatsapp_ai_assistant -c "SELECT COUNT(*) FROM conversations;"`
- [ ] Cloudflare tunnel running: Public URL accessible
- [ ] Webhook receives test message: Check `webhook_logs` table
- [ ] AI response generated: Check `messages` table for sender_type='AI'
- [ ] Response saved to database: Verify in `messages` table
- [ ] Mock mode working: `ENVIRONMENT=development` in `.env`

**Optional (requires valid Green API token):**
- [ ] WhatsApp sending works: Check `sent_messages_log` table

---

**Remember:** The MVP uses database-first pattern - AI responses are always saved even if WhatsApp sending fails. This ensures complete conversation history and system reliability.
