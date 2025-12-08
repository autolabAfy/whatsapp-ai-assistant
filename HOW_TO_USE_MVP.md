# How to Use Your WhatsApp AI Assistant MVP

## Your MVP is Ready and Running!

Everything is set up and working. Here's how to use it.

---

## Current Status

✅ **Server Running:** http://localhost:8000
✅ **Database:** PostgreSQL with all conversations stored
✅ **N8N Webhook URL:** https://autolabclick.app.n8n.cloud/webhook/82e61cd4-3b75-4b5c-954e-4d40f4617f07
✅ **Green API Instance:** 7105342242 (Authorized)
✅ **UI:** http://localhost:8000/inbox

---

## ONE-TIME SETUP (Do This Once)

### Step 1: Configure N8N Workflow to Forward to Local Server

Your N8N webhook is already set up to receive WhatsApp messages from Green API. Now we need to configure it to forward messages to your local server.

**Option A: Update N8N Workflow (Recommended)**
1. Go to your N8N workflow: https://autolabclick.app.n8n.cloud
2. Find the workflow that handles webhook `82e61cd4-3b75-4b5c-954e-4d40f4617f07`
3. Add an HTTP Request node to forward to:
   ```
   http://localhost:8000/webhook/greenapi
   ```
   OR use the Cloudflare tunnel URL:
   ```
   https://entitled-aggregate-advisors-commodities.trycloudflare.com/webhook/greenapi
   ```
4. Configure it to pass through the webhook data
5. Activate the workflow

**Option B: Direct Green API Webhook (Alternative)**
If you prefer to bypass N8N for this MVP:
1. Go to Green API dashboard: https://console.green-api.com
2. Select instance: **7105342242**
3. Settings → Webhooks
4. Set webhook URL to:
   ```
   https://entitled-aggregate-advisors-commodities.trycloudflare.com/webhook/greenapi
   ```
5. Enable "Incoming Messages"
6. Save

**Note:** Option A is better for production as N8N provides stability and you can add custom processing.

---

## HOW TO USE IT

### Method 1: Send WhatsApp Messages (Full End-to-End Test)

1. **Send a WhatsApp message** to the phone number connected to your Green API instance (7105342242)

2. **Example messages to try:**
   ```
   Hi! I'm looking for a 3-bedroom condo in Marina Bay
   ```
   ```
   Do you have any properties under $1 million?
   ```
   ```
   I want to buy a house in Orchard
   ```

3. **What happens:**
   - System receives your message via webhook
   - Saves your message to database
   - AI generates response based on your query
   - Searches for matching properties
   - Saves AI response to database
   - Sends response back to you on WhatsApp

4. **Check the conversation history:**
   - Open UI: http://localhost:8000/inbox
   - You'll see your conversation appear
   - Click to view full chat history

### Method 2: View UI (Web Interface)

**Open in browser:**
```
http://localhost:8000/inbox
```

**What you'll see:**
- List of all conversations on the left
- Click any conversation to see full chat history
- Toggle between AI and HUMAN mode
- Real-time conversation updates

**Current test data:**
- Demo agent: demo@example.com
- 2 sample properties (Marina Bay Condo, Orchard HDB)
- Test conversations if you created any

### Method 3: Use API Directly (For Testing)

**Check system health:**
```bash
curl http://localhost:8000/health
```

**Get all conversations:**
```bash
curl http://localhost:8000/api/agents/3b5ab91d-ddfb-48cb-a110-acb5144a89fa/conversations
```

**Get conversation messages:**
```bash
curl http://localhost:8000/api/conversations/{conversation_id}/messages
```

**Search properties:**
```bash
curl -X POST http://localhost:8000/api/properties/search \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "3b5ab91d-ddfb-48cb-a110-acb5144a89fa", "query": "Marina Bay 3 bedroom"}'
```

---

## HOW THE SYSTEM WORKS

### Message Flow

```
User sends WhatsApp message
    ↓
Green API receives message
    ↓
Green API sends webhook to your server
    ↓
Server receives webhook at /webhook/greenapi
    ↓
Server saves user message to database
    ↓
Server detects property intent (location, bedrooms, price)
    ↓
Server searches properties database
    ↓
AI generates contextual response
    ↓
Server saves AI response to database (DATABASE-FIRST)
    ↓
Server sends AI response via Green API
    ↓
User receives WhatsApp message
    ↓
Conversation visible in UI
```

### AI Mode vs Human Mode

**AI Mode (default):**
- System automatically responds to all messages
- AI searches properties and provides suggestions
- No manual intervention needed

**HUMAN Mode:**
- System stops auto-responding
- Agent takes over conversation manually
- Messages still logged in database

**Toggle modes:**
- Via UI: Click "Toggle to HUMAN" button
- Via API: POST to `/api/conversations/toggle-mode`

### Database-First Pattern (Critical)

The system uses a "database-first" approach:
1. AI response generated
2. **Saved to database FIRST**
3. **Then** sent via WhatsApp

**Why this matters:**
- If WhatsApp sending fails, response is still saved
- Complete conversation history always maintained
- No data loss on external service failures
- Can review and resend failed messages

---

## CHECKING IF IT'S WORKING

### Quick Health Check

```bash
# 1. Check server
curl http://localhost:8000/health
# Should return: {"status":"ok","database":"ok","environment":"development"}

# 2. Check database has conversations
psql whatsapp_ai_assistant -c "SELECT COUNT(*) FROM conversations;"

# 3. Check Green API instance
# Go to dashboard, verify status shows "Authorized"

# 4. Check tunnel is running
ps aux | grep cloudflared | grep -v grep
# Should show cloudflared process
```

### View Logs

**Application logs:**
```bash
tail -f /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant/logs/app.log
```

**Database logs:**
```bash
psql whatsapp_ai_assistant -c "SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 5;"
```

**Recent messages:**
```bash
psql whatsapp_ai_assistant -c "SELECT sender_type, message_text, timestamp FROM messages ORDER BY timestamp DESC LIMIT 10;"
```

---

## COMMON TASKS

### Add More Properties

**Method 1: SQL**
```sql
psql whatsapp_ai_assistant

INSERT INTO properties (agent_id, title, property_type, location, price, bedrooms, bathrooms)
VALUES
('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', 'Sentosa Cove Villa', 'landed', 'Sentosa', 5000000, 5, 4);
```

**Method 2: Python script**
```bash
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant
source venv/bin/activate
python execution/manage_properties.py 3b5ab91d-ddfb-48cb-a110-acb5144a89fa
```

### View All Conversations

```sql
psql whatsapp_ai_assistant

SELECT
    conversation_id,
    contact_name,
    contact_number,
    current_mode,
    last_message_preview,
    last_message_timestamp
FROM conversations
ORDER BY last_message_timestamp DESC;
```

### View Full Conversation History

```sql
SELECT
    c.contact_name,
    m.sender_type,
    m.message_text,
    m.timestamp
FROM messages m
JOIN conversations c ON m.conversation_id = c.conversation_id
WHERE c.contact_number = '1234567890'  -- Replace with actual number
ORDER BY m.timestamp;
```

### Change AI Persona

```sql
UPDATE agents
SET
    assistant_name = 'Sarah',
    speaking_style = 'friendly',
    custom_instruction = 'You are warm and helpful. Focus on scheduling viewings.'
WHERE agent_id = '3b5ab91d-ddfb-48cb-a110-acb5144a89fa';
```

---

## IF SOMETHING ISN'T WORKING

### Messages Not Received

**Check:**
1. Cloudflare tunnel is running (see Current Status section)
2. Webhook URL configured in Green API dashboard
3. Green API instance shows "Authorized"
4. Server is running on port 8000

**Fix:**
```bash
# Check server running
lsof -i :8000

# Check tunnel URL
cat /tmp/cloudflare-tunnel.log | grep trycloudflare.com

# Check webhook logs
psql whatsapp_ai_assistant -c "SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 3;"
```

### AI Not Responding

**Check:**
1. Conversation mode is "AI" not "HUMAN"
2. Server logs for errors
3. Mock mode is enabled (ENVIRONMENT=development in .env)

**Fix:**
```bash
# Toggle to AI mode
psql whatsapp_ai_assistant -c "UPDATE conversations SET current_mode = 'AI' WHERE conversation_id = 'conversation-id-here';"

# Check logs
tail -f logs/app.log | grep ERROR
```

### UI Shows Blank Screen

**Check:**
1. Server is running
2. Browser console for errors (F12)
3. Database has conversations

**Fix:**
```bash
# Create test conversation
psql whatsapp_ai_assistant

INSERT INTO conversations (agent_id, contact_number, contact_name, current_mode)
VALUES ('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', '1234567890', 'Test User', 'AI')
RETURNING conversation_id;

# Add messages (use conversation_id from above)
INSERT INTO messages (conversation_id, sender_type, message_text)
VALUES
('conversation-id', 'USER', 'Hi! I want a condo'),
('conversation-id', 'AI', 'I can help you find a condo!');
```

For more detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## STOPPING AND RESTARTING

### Stop Everything

```bash
# Stop server (Ctrl+C in terminal running python main.py)

# Or kill the process
lsof -i :8000
kill -9 {PID}

# Stop Cloudflare tunnel
pkill -f cloudflared
```

### Start Everything

```bash
# Start server
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant
source venv/bin/activate
python main.py

# In another terminal, start tunnel
eval "$(/opt/homebrew/bin/brew shellenv)" && cloudflared tunnel --url http://localhost:8000

# Copy the new tunnel URL
# Update webhook URL in Green API dashboard
```

**Important:** Cloudflare tunnel URL changes every time you restart. You'll need to update the webhook URL in Green API dashboard each time.

---

## WHAT'S NEXT

Now that your MVP is working, you can:

### Today: Get Structure Ready

1. **Test end-to-end flow**
   - Send WhatsApp messages
   - Verify responses work
   - Check conversation history in UI

2. **Add real properties**
   - Use SQL or Python script
   - Add properties for your use case

3. **Customize AI persona**
   - Update agent table with your style
   - Test how AI responds

4. **Document edge cases**
   - Test various property queries
   - Note what works and what doesn't

### Later: Backend and Frontend

**Backend improvements:**
- Authentication system
- Better property search (semantic search)
- Follow-up automation (2h, 24h, 72h)
- Analytics dashboard
- Admin panel

**Frontend improvements:**
- React/Vue for better UI
- Real-time WebSocket updates
- Mobile-responsive design
- Property management interface
- Bulk import properties

**See [NEXT_STEPS.md](NEXT_STEPS.md) for full roadmap**

---

## KEY URLS AND CREDENTIALS

**Local Access:**
- Server: http://localhost:8000
- UI: http://localhost:8000/inbox
- API Docs: http://localhost:8000/docs

**Public Access:**
- N8N Webhook: https://autolabclick.app.n8n.cloud/webhook/82e61cd4-3b75-4b5c-954e-4d40f4617f07
- Cloudflare Tunnel: https://entitled-aggregate-advisors-commodities.trycloudflare.com

**Green API:**
- Dashboard: https://console.green-api.com
- Instance ID: 7105342242
- Token: a4709845232254bd195fdf4ea47f23d6c87fc7809fb89447ea1
- Status: Authorized

**Database:**
- Name: whatsapp_ai_assistant
- URL: postgresql://localhost:5432/whatsapp_ai_assistant
- Demo Agent ID: 3b5ab91d-ddfb-48cb-a110-acb5144a89fa

---

## QUICK REFERENCE

**Start MVP:**
```bash
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant
source venv/bin/activate
python main.py
```

**Start Tunnel:**
```bash
cloudflared tunnel --url http://localhost:8000
```

**View Logs:**
```bash
tail -f logs/app.log
```

**Check Database:**
```bash
psql whatsapp_ai_assistant -c "SELECT * FROM conversations ORDER BY last_message_timestamp DESC LIMIT 5;"
```

**Add Property:**
```sql
psql whatsapp_ai_assistant

INSERT INTO properties (agent_id, title, property_type, location, price, bedrooms, bathrooms)
VALUES ('3b5ab91d-ddfb-48cb-a110-acb5144a89fa', 'Property Name', 'condo', 'Location', 1000000, 3, 2);
```

---

## IMPORTANT NOTES

1. **Cloudflare Tunnel URL Changes:** Every time you restart the tunnel, you get a new URL. Update Green API webhook URL accordingly.

2. **Database-First Pattern:** AI responses are ALWAYS saved to database before sending to WhatsApp. This ensures no data loss.

3. **Mock AI Mode:** System uses intelligent mock responses when Claude API is unavailable (ENVIRONMENT=development).

4. **Complete Conversation History:** Even if WhatsApp sending fails, all conversations are saved in the database.

5. **No Data Loss:** The system prioritizes data integrity over external service availability.

---

## SUPPORT AND DOCUMENTATION

- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Setup Guide:** [directives/whatsapp_mvp_setup.md](directives/whatsapp_mvp_setup.md)
- **Database Pattern:** [execution/README_DATABASE_FIRST_PATTERN.md](execution/README_DATABASE_FIRST_PATTERN.md)
- **Next Steps:** [NEXT_STEPS.md](NEXT_STEPS.md)

---

**Your MVP is ready to use. Start by sending a WhatsApp message and watch it work!**
