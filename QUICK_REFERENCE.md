# Quick Reference Guide

Essential commands and operations for WhatsApp AI Assistant.

## Starting the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
python main.py

# Server runs on: http://localhost:8000
```

## Common Operations

### Check System Health

```bash
# API health check
curl http://localhost:8000/health

# Check database
psql whatsapp_ai_assistant -c "SELECT COUNT(*) FROM conversations;"

# Check Redis
redis-cli ping
```

### Manage Conversations

```bash
# Get all conversations for an agent
curl http://localhost:8000/api/agents/{agent_id}/conversations

# Get single conversation
curl http://localhost:8000/api/conversations/{conversation_id}

# Get conversation messages
curl http://localhost:8000/api/conversations/{conversation_id}/messages

# Toggle to HUMAN mode
python execution/set_mode_human.py {conversation_id}

# Toggle to AI mode
python execution/set_mode_ai.py {conversation_id}
```

### Manage Properties

```bash
# Add property
python execution/manage_properties.py {agent_id}

# Search properties
python execution/property_lookup.py {agent_id} "Orchard"

# Via SQL
psql whatsapp_ai_assistant
```

```sql
-- List all properties
SELECT property_id, title, location, price FROM properties;

-- Add property
INSERT INTO properties (agent_id, title, property_type, location, price, bedrooms)
VALUES ('agent-uuid', 'Test Property', 'condo', 'Marina Bay', 1000000, 3);

-- Update property
UPDATE properties SET availability = 'sold' WHERE property_id = 'property-uuid';

-- Delete property (soft)
UPDATE properties SET is_archived = TRUE WHERE property_id = 'property-uuid';
```

### Check Logs

```bash
# Tail application logs
tail -f logs/app.log

# View recent webhook logs
psql whatsapp_ai_assistant -c "SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 10;"

# View recent messages
psql whatsapp_ai_assistant -c "SELECT * FROM messages ORDER BY timestamp DESC LIMIT 10;"
```

## Database Queries

### Useful SQL Commands

```sql
-- Connect to database
psql whatsapp_ai_assistant

-- List all tables
\dt

-- Get agent details
SELECT * FROM agents WHERE email = 'demo@example.com';

-- Get conversations in AI mode
SELECT conversation_id, contact_number, last_message_preview
FROM conversations
WHERE current_mode = 'AI'
ORDER BY last_message_timestamp DESC;

-- Get recent escalations
SELECT * FROM escalations ORDER BY timestamp DESC LIMIT 10;

-- Count messages by sender type
SELECT sender_type, COUNT(*) FROM messages GROUP BY sender_type;

-- Get properties by availability
SELECT title, location, price, availability
FROM properties
WHERE agent_id = 'agent-uuid'
ORDER BY created_at DESC;

-- View conversation history
SELECT m.timestamp, m.sender_type, m.message_text
FROM messages m
JOIN conversations c ON m.conversation_id = c.conversation_id
WHERE c.contact_number = '1234567890'
ORDER BY m.timestamp;
```

## Redis Commands

```bash
# Connect to Redis
redis-cli

# List all keys
KEYS *

# Check specific lock
GET "lock:conversation:uuid-here"

# Check webhook dedup
KEYS "webhook:*"

# Clear all keys (DANGEROUS - dev only)
FLUSHALL

# Exit
exit
```

## Green API Operations

### Check Instance Status

```bash
# Get instance state
curl "https://api.green-api.com/waInstance{INSTANCE_ID}/getStateInstance/{TOKEN}"

# Response: "authorized" (connected) or "notAuthorized" (disconnected)
```

### Send Test Message

```bash
# Via API
curl -X POST "https://api.green-api.com/waInstance{INSTANCE_ID}/sendMessage/{TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "chatId": "1234567890@c.us",
    "message": "Test message"
  }'
```

### Configure Webhook

1. Go to Green API dashboard
2. Navigate to Settings → Webhooks
3. Set webhook URL: `https://your-domain.com/webhook/greenapi`
4. Enable "Incoming Messages"
5. Save

## Troubleshooting

### Server won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 {PID}

# Check for Python errors
python main.py  # Look for stack trace
```

### Database connection error

```bash
# Check PostgreSQL is running
# macOS:
brew services list | grep postgresql

# Linux:
sudo systemctl status postgresql

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test connection
psql whatsapp_ai_assistant -c "SELECT 1;"
```

### Redis connection error

```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Start if not running
# macOS:
brew services start redis

# Linux:
sudo systemctl start redis-server
```

### Messages not received

```bash
# Check webhook logs
psql whatsapp_ai_assistant -c "SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 5;"

# Verify Green API instance is connected
curl "https://api.green-api.com/waInstance{INSTANCE_ID}/getStateInstance/{TOKEN}"

# Check webhook URL in Green API dashboard
# Must be: https://your-domain.com/webhook/greenapi
```

### AI not responding

```bash
# Check conversation mode
psql whatsapp_ai_assistant -c "SELECT conversation_id, current_mode FROM conversations WHERE contact_number = '1234567890';"

# Check Anthropic API key
echo $ANTHROPIC_API_KEY

# Test API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "Hi"}]
  }'

# Check logs
tail -f logs/app.log | grep ERROR
```

## Configuration

### Update Agent Persona

```sql
psql whatsapp_ai_assistant

UPDATE agents
SET assistant_name = 'Sarah',
    speaking_style = 'friendly',
    custom_instruction = 'You are warm and helpful. Focus on scheduling viewings.'
WHERE agent_id = 'agent-uuid';
```

### Update Green API Credentials

```bash
# Edit .env
nano .env

# Update:
GREEN_API_INSTANCE_ID=new_instance_id
GREEN_API_TOKEN=new_token

# Restart server
# Ctrl+C to stop, then:
python main.py
```

## API Endpoints

### Health & Status

```bash
GET /health
GET /
```

### Webhooks

```bash
POST /webhook/greenapi
```

### Conversations

```bash
GET /api/conversations/{id}
GET /api/conversations/{id}/messages
GET /api/agents/{agent_id}/conversations
POST /api/conversations/toggle-mode
```

### Properties

```bash
POST /api/properties/search
GET /api/properties/{id}
GET /api/agents/{agent_id}/properties
```

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://localhost:5432/whatsapp_ai_assistant
REDIS_URL=redis://localhost:6379/0
GREEN_API_INSTANCE_ID=your_instance_id
GREEN_API_TOKEN=your_token
ANTHROPIC_API_KEY=your_key

# Optional (with defaults)
APP_HOST=0.0.0.0
APP_PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Backup & Restore

### Backup Database

```bash
# Full backup
pg_dump whatsapp_ai_assistant > backup_$(date +%Y%m%d).sql

# Backup schema only
pg_dump --schema-only whatsapp_ai_assistant > schema.sql

# Backup data only
pg_dump --data-only whatsapp_ai_assistant > data.sql
```

### Restore Database

```bash
# Drop and recreate database
dropdb whatsapp_ai_assistant
createdb whatsapp_ai_assistant

# Restore from backup
psql whatsapp_ai_assistant < backup_20231201.sql
```

## Development

### Reset Database

```bash
# WARNING: This deletes all data

# Drop database
dropdb whatsapp_ai_assistant

# Recreate
createdb whatsapp_ai_assistant

# Run migrations
psql whatsapp_ai_assistant < migrations/001_initial_schema.sql
```

### Clear Redis Cache

```bash
redis-cli FLUSHALL
```

### View Real-time Logs

```bash
# Terminal 1: Server logs
tail -f logs/app.log

# Terminal 2: Database logs
psql whatsapp_ai_assistant
\watch 1  -- Refresh every second
SELECT * FROM messages ORDER BY timestamp DESC LIMIT 5;
```

## Production Deployment

### Pre-deployment Checklist

```bash
# 1. Update .env for production
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@prod-db:5432/whatsapp_ai_assistant
REDIS_URL=redis://prod-redis:6379/0

# 2. Generate secure JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# 4. Run migrations
psql $DATABASE_URL < migrations/001_initial_schema.sql

# 5. Update Green API webhook URL
# Dashboard → Settings → Webhooks → https://your-domain.com/webhook/greenapi

# 6. Start server with Gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Support

### Get Help

- Check logs: `tail -f logs/app.log`
- Check database: `psql whatsapp_ai_assistant`
- Check Redis: `redis-cli`
- Review documentation: README.md, SETUP.md, ARCHITECTURE.md

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `lsof -i :8000` then `kill -9 {PID}` |
| DB connection error | Check PostgreSQL running, verify DATABASE_URL |
| Redis error | `redis-cli ping`, restart if needed |
| Webhook not received | Check Green API dashboard, verify webhook URL |
| AI not responding | Check mode (should be AI), verify API key |
| Properties not found | Check agent_id matches, verify properties exist |

---

**Quick tip**: Keep this file bookmarked for daily operations!
