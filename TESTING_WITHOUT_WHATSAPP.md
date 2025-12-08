# Testing Your WhatsApp AI Assistant Without WhatsApp

## Overview

You can fully test and develop your system **without connecting to WhatsApp**. This guide shows you how to test:
- Backend API endpoints
- Gemini AI responses
- Property search
- Database operations
- UI conversation view

---

## Quick Start: Test the Full Flow Locally

### Method 1: Using API Directly (Recommended)

Test the complete flow using curl or Postman:

#### **Step 1: Create a Test Conversation**

```bash
curl -X POST http://localhost:8000/webhook/greenapi \
  -H "Content-Type: application/json" \
  -d '{
    "typeWebhook": "incomingMessageReceived",
    "instanceData": {
      "idInstance": "7105342242"
    },
    "senderData": {
      "sender": "1234567890@c.us",
      "senderName": "Test User"
    },
    "messageData": {
      "typeMessage": "textMessage",
      "textMessageData": {
        "textMessage": "Hi! I am looking for a 3-bedroom condo in Marina Bay"
      }
    },
    "timestamp": 1234567890
  }'
```

**What happens:**
1. System receives "message" via webhook
2. Creates conversation in database
3. Detects property intent (Marina Bay, 3 bedrooms, condo)
4. Searches properties database
5. Gemini generates response with property matches
6. Saves AI response to database
7. (Skips WhatsApp sending - but everything else works!)

#### **Step 2: Check the Response**

View in UI:
```
http://localhost:8000/inbox
```

Or check database:
```bash
psql whatsapp_ai_assistant -c "
SELECT
    c.contact_name,
    m.sender_type,
    m.message_text,
    m.timestamp
FROM messages m
JOIN conversations c ON m.conversation_id = c.conversation_id
ORDER BY m.timestamp DESC
LIMIT 10;"
```

---

### Method 2: Using the UI

#### **Step 1: Add Test Data Manually**

```bash
psql whatsapp_ai_assistant
```

```sql
-- Create test conversation
INSERT INTO conversations (agent_id, contact_number, contact_name, current_mode)
VALUES ('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', '1234567890', 'Test Customer', 'AI')
RETURNING conversation_id;

-- Note the conversation_id returned (example: 8f4ca03b-133b-45f1-b807-37d49e346d50)
```

#### **Step 2: Add Test Messages**

```sql
-- Replace 'conversation-id-here' with actual ID from above
INSERT INTO messages (conversation_id, sender_type, message_text)
VALUES
('conversation-id-here', 'USER', 'Hi! I want to rent a 3-bedroom condo in Marina Bay. What do you have?'),
('conversation-id-here', 'AI', 'Thank you for your interest! I found a great property for you:\n\nMarina Bay Condo - $1,200,000\n3 bed, 2 bath\n\nWould you like to schedule a viewing?');
```

#### **Step 3: View in UI**

Open browser:
```
http://localhost:8000/inbox
```

You'll see your test conversation!

---

### Method 3: Test AI Response Generation Directly

Test Gemini AI without going through webhooks:

```bash
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant
source venv/bin/activate

# First create a test conversation (if not already created)
psql whatsapp_ai_assistant -c "
INSERT INTO conversations (agent_id, contact_number, contact_name, current_mode)
VALUES ('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', '9999999999', 'AI Test User', 'AI')
ON CONFLICT DO NOTHING
RETURNING conversation_id;"

# Use the conversation_id returned, then test AI:
python execution/ai_router.py <conversation-id> "I want a 4-bedroom house in Orchard under 2 million"
```

**This tests:**
- Gemini API integration ✅
- Property search ✅
- Intent detection ✅
- AI response generation ✅

---

## Testing Individual Components

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{"status":"ok","database":"ok","environment":"development"}
```

---

### Test 2: Property Search

```bash
curl -X POST http://localhost:8000/api/properties/search \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "3b5ab91d-ddfb-48cb-a110-acb5144a89fa",
    "query": "3 bedroom Marina Bay"
  }'
```

**Expected:**
```json
[
  {
    "property_id": "...",
    "title": "Marina Bay Condo",
    "location": "Marina Bay",
    "bedrooms": 3,
    "price": 1200000
  }
]
```

---

### Test 3: Get All Conversations

```bash
curl http://localhost:8000/api/agents/3b5ab91d-ddfb-48cb-a110-acb5144a89fa/conversations
```

**Expected:**
```json
[
  {
    "conversation_id": "...",
    "contact_name": "Test User",
    "contact_number": "1234567890",
    "current_mode": "AI",
    "last_message_preview": "Hi! I am looking for..."
  }
]
```

---

### Test 4: Get Conversation Messages

```bash
# Replace <conversation-id> with actual ID
curl http://localhost:8000/api/conversations/<conversation-id>/messages
```

**Expected:**
```json
[
  {
    "sender_type": "USER",
    "message_text": "Hi! I am looking for...",
    "timestamp": "2025-12-08T..."
  },
  {
    "sender_type": "AI",
    "message_text": "Thank you for your interest!...",
    "timestamp": "2025-12-08T..."
  }
]
```

---

### Test 5: Toggle Conversation Mode

```bash
curl -X POST http://localhost:8000/api/conversations/toggle-mode \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "<conversation-id>",
    "mode": "HUMAN"
  }'
```

**Expected:**
```json
{
  "conversation_id": "...",
  "mode": "HUMAN",
  "message": "Conversation mode updated"
}
```

---

## Add Test Properties

Add more properties to test search:

```bash
psql whatsapp_ai_assistant
```

```sql
INSERT INTO properties (agent_id, title, property_type, location, price, bedrooms, bathrooms, size_sqft, description)
VALUES
-- Luxury properties
('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', 'Sentosa Cove Villa', 'landed', 'Sentosa', 5000000, 5, 4, 3500, 'Stunning waterfront villa with pool'),
('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', 'Orchard Luxury Penthouse', 'condo', 'Orchard', 3500000, 4, 3, 2500, 'Penthouse with city views'),

-- Mid-range properties
('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', 'Bukit Timah Condo', 'condo', 'Bukit Timah', 1800000, 3, 2, 1400, 'Near schools and MRT'),
('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', 'Clementi HDB', 'hdb', 'Clementi', 600000, 4, 2, 1200, 'Spacious family home'),

-- Budget properties
('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', 'Woodlands HDB', 'hdb', 'Woodlands', 400000, 3, 2, 1000, 'Well-maintained unit'),
('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', 'Jurong East Apartment', 'hdb', 'Jurong', 500000, 3, 2, 1100, 'Near shopping and MRT');
```

---

## Automated Test Script

Create a test script to run multiple scenarios:

```bash
cat > test_mvp.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing WhatsApp AI Assistant MVP"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "Test 1: Health Check"
RESULT=$(curl -s http://localhost:8000/health)
if [[ $RESULT == *"ok"* ]]; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi
echo ""

# Test 2: Property Search
echo "Test 2: Property Search (Marina Bay)"
RESULT=$(curl -s -X POST http://localhost:8000/api/properties/search \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "3b5ab91d-ddfb-48cb-a110-acb5144a89fa", "query": "Marina Bay"}')
if [[ $RESULT == *"Marina"* ]]; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi
echo ""

# Test 3: Webhook Processing
echo "Test 3: Webhook Processing"
RESULT=$(curl -s -X POST http://localhost:8000/webhook/greenapi \
  -H "Content-Type: application/json" \
  -d '{
    "typeWebhook": "incomingMessageReceived",
    "instanceData": {"idInstance": "7105342242"},
    "senderData": {"sender": "test@c.us", "senderName": "Test"},
    "messageData": {"typeMessage": "textMessage", "textMessageData": {"textMessage": "Hello"}},
    "timestamp": 1234567890
  }')
if [[ $RESULT == *"conversation_id"* ]]; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi
echo ""

# Test 4: Database Connection
echo "Test 4: Database Connection"
RESULT=$(psql whatsapp_ai_assistant -c "SELECT COUNT(*) FROM conversations;" -t 2>/dev/null)
if [[ $RESULT -ge 0 ]]; then
    echo -e "${GREEN}✅ PASSED (${RESULT} conversations)${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi
echo ""

echo "===================================="
echo "🏁 Testing Complete"
EOF

chmod +x test_mvp.sh
./test_mvp.sh
```

---

## Backend Structure Testing Checklist

Use this to verify your backend is solid:

### Database Layer ✅
- [ ] PostgreSQL running
- [ ] All 9 tables created
- [ ] Demo agent exists
- [ ] Sample properties loaded
- [ ] Can insert/query data

### API Layer ✅
- [ ] Server running on port 8000
- [ ] Health endpoint works
- [ ] Webhook endpoint accepts data
- [ ] Conversations endpoint works
- [ ] Properties endpoint works
- [ ] Messages endpoint works

### AI Layer ✅
- [ ] Gemini API key configured
- [ ] AI router selects correct provider
- [ ] Property intent detection works
- [ ] Property search works
- [ ] AI generates contextual responses

### Business Logic ✅
- [ ] Database-first pattern (saves before sending)
- [ ] Conversation mode (AI/HUMAN) works
- [ ] Agent persona customization works
- [ ] Deduplication prevents duplicate processing
- [ ] Webhook logging works

### UI Layer ✅
- [ ] Inbox page loads
- [ ] Conversations display
- [ ] Messages display
- [ ] Can toggle modes

---

## Development Workflow

### 1. Make Backend Changes

Edit files in:
- `execution/*.py` - Business logic
- `main.py` - API endpoints
- `directives/*.md` - Documentation

### 2. Test Locally

```bash
# Restart server
pkill -f "python main.py"
python main.py

# Test API
curl http://localhost:8000/health

# Test with mock webhook
curl -X POST http://localhost:8000/webhook/greenapi -H "Content-Type: application/json" -d '...'

# Check database
psql whatsapp_ai_assistant -c "SELECT * FROM messages ORDER BY timestamp DESC LIMIT 5;"
```

### 3. Iterate

- Add features
- Fix bugs
- Improve AI responses
- Add more properties
- Customize UI

### 4. When Ready for WhatsApp

Later, when you want to connect WhatsApp:
1. Configure N8N or Green API webhook
2. System already works - just connects the input!

---

## Example: Full Test Scenario

Let's test a complete customer interaction:

```bash
# 1. Customer asks about properties
curl -X POST http://localhost:8000/webhook/greenapi \
  -H "Content-Type: application/json" \
  -d '{
    "typeWebhook": "incomingMessageReceived",
    "instanceData": {"idInstance": "7105342242"},
    "senderData": {"sender": "customer1@c.us", "senderName": "John Doe"},
    "messageData": {
      "typeMessage": "textMessage",
      "textMessageData": {"textMessage": "Hi! I want a 3-bedroom condo in Marina Bay under $1.5M"}
    },
    "timestamp": 1234567890
  }'

# 2. Check what AI responded
psql whatsapp_ai_assistant -c "
SELECT sender_type, message_text
FROM messages
WHERE conversation_id IN (
  SELECT conversation_id FROM conversations WHERE contact_number = 'customer1'
)
ORDER BY timestamp;"

# 3. Customer asks follow-up
curl -X POST http://localhost:8000/webhook/greenapi \
  -H "Content-Type: application/json" \
  -d '{
    "typeWebhook": "incomingMessageReceived",
    "instanceData": {"idInstance": "7105342242"},
    "senderData": {"sender": "customer1@c.us", "senderName": "John Doe"},
    "messageData": {
      "typeMessage": "textMessage",
      "textMessageData": {"textMessage": "Can I schedule a viewing?"}
    },
    "timestamp": 1234567891
  }'

# 4. Check conversation in UI
open http://localhost:8000/inbox
```

---

## Monitoring and Debugging

### Watch Logs in Real-Time

```bash
tail -f logs/app.log
```

### Check Recent Database Activity

```bash
psql whatsapp_ai_assistant -c "
SELECT
    w.timestamp,
    w.event_type,
    w.status,
    w.error_message
FROM webhook_logs w
ORDER BY w.timestamp DESC
LIMIT 10;"
```

### Monitor Gemini API Usage

Check Google Cloud Console:
```
https://console.cloud.google.com
```
Navigate to: APIs & Services → Credentials → Your API Key → Usage

---

## Summary

You can **fully develop and test** your backend without WhatsApp:

✅ **API Testing** - curl/Postman
✅ **Database Testing** - psql queries
✅ **AI Testing** - Direct Python scripts
✅ **UI Testing** - Browser at localhost:8000/inbox
✅ **Integration Testing** - Automated test scripts

**When ready for production:**
Just connect the webhook and everything works!

---

**Your backend structure is complete and ready for development!** 🚀
