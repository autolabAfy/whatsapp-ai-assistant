# Integrating Custom UI with WhatsApp Backend

## Overview

This guide shows you how to connect your custom UI (built on Google AI Studio or elsewhere) with your WhatsApp AI Assistant backend.

---

## Integration Architecture Options

### Option 1: UI Calls Backend API Directly (Recommended)

```
┌─────────────────┐
│   Your Custom   │
│       UI        │
│  (AI Studio)    │
└────────┬────────┘
         │ HTTP Requests
         ↓
┌─────────────────┐
│  Your Backend   │
│  localhost:8000 │
│  (FastAPI)      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   PostgreSQL    │
│   (Database)    │
└─────────────────┘
```

**How it works:**
- Your UI makes HTTP POST/GET requests to backend API
- Backend handles all business logic
- Backend returns JSON responses
- UI displays the data

---

### Option 2: Backend Exposes REST API, UI Consumes It

```
┌──────────────┐       ┌──────────────────┐
│  Custom UI   │◄─────►│  Backend REST API│
│              │ JSON  │  localhost:8000  │
└──────────────┘       └────────┬─────────┘
                                │
                                ↓
                       ┌─────────────────┐
                       │  Business Logic │
                       │  • Gemini AI    │
                       │  • Properties   │
                       │  • Conversations│
                       └─────────────────┘
```

**Endpoints your UI can call:**
- `POST /api/chat/send` - Send message, get AI response
- `GET /api/conversations` - List conversations
- `GET /api/properties/search` - Search properties
- `POST /api/properties/recommend` - Get AI recommendations

---

### Option 3: Function Calling (If AI Studio Supports It)

```
┌─────────────────────┐
│  Google AI Studio   │
│  Gemini Agent       │
│  with Functions     │
└──────────┬──────────┘
           │ Function Calls
           ↓
┌──────────────────────┐
│  Backend Functions   │
│  • searchProperties  │
│  • getConversation   │
│  • saveMessage       │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│      Database        │
└──────────────────────┘
```

**How it works:**
- Define functions in your Gemini agent
- Functions call your backend API
- Backend returns structured data
- Gemini uses data to respond

---

## Implementation Guide

### Step 1: Create API Endpoints for UI

Let me create dedicated API endpoints for your custom UI:

```python
# File: main.py (add these endpoints)

@app.post("/api/chat/send")
async def send_chat_message(request: ChatRequest):
    """
    Send message and get AI response

    Request:
        {
            "user_id": "customer123",
            "message": "I want a 3-bedroom condo",
            "session_id": "optional-session-id"
        }

    Response:
        {
            "conversation_id": "uuid",
            "user_message": "I want a 3-bedroom condo",
            "ai_response": "I found 3 properties...",
            "properties": [...],
            "timestamp": "2025-12-08T..."
        }
    """
    pass


@app.get("/api/properties/recommend")
async def recommend_properties(
    location: str = None,
    bedrooms: int = None,
    max_price: int = None
):
    """
    Get property recommendations

    Query params:
        ?location=Marina Bay&bedrooms=3&max_price=1500000

    Response:
        {
            "properties": [
                {
                    "id": "...",
                    "title": "Marina Bay Condo",
                    "price": 1200000,
                    "bedrooms": 3,
                    "location": "Marina Bay"
                }
            ],
            "count": 1
        }
    """
    pass


@app.post("/api/ui/webhook")
async def ui_webhook(request: UIWebhookRequest):
    """
    Webhook endpoint for your UI to send events

    Request:
        {
            "event_type": "user_message",
            "user_id": "customer123",
            "data": {
                "message": "Hello",
                "context": {...}
            }
        }

    Response:
        {
            "status": "processed",
            "ai_response": "..."
        }
    """
    pass
```

---

## Google AI Studio Integration Patterns

### Pattern 1: Function Calling in Gemini

If your AI Studio UI supports function calling, define these functions:

```javascript
// In Google AI Studio - Define Functions

function searchProperties(location, bedrooms, maxPrice) {
    // Calls your backend
    const response = fetch('http://localhost:8000/api/properties/search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            location: location,
            bedrooms: bedrooms,
            max_price: maxPrice
        })
    });
    return response.json();
}

function saveConversation(userId, message, aiResponse) {
    // Saves to your backend
    const response = fetch('http://localhost:8000/api/chat/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            user_id: userId,
            user_message: message,
            ai_response: aiResponse
        })
    });
    return response.json();
}
```

---

### Pattern 2: Direct HTTP Calls from UI

If your UI is a web app, make direct API calls:

```javascript
// In your custom UI

async function sendMessage(userMessage) {
    const response = await fetch('http://localhost:8000/api/chat/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: getCurrentUserId(),
            message: userMessage,
            session_id: getSessionId()
        })
    });

    const data = await response.json();

    // Display AI response
    displayMessage(data.ai_response);

    // Show recommended properties
    if (data.properties) {
        displayProperties(data.properties);
    }
}
```

---

### Pattern 3: Webhook-Based Integration

Your UI sends webhooks to backend:

```javascript
// When user sends message in your UI
async function onUserMessage(message) {
    // Send to backend webhook
    const response = await fetch('http://localhost:8000/api/ui/webhook', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            event_type: 'user_message',
            user_id: 'customer123',
            data: {
                message: message,
                timestamp: new Date().toISOString()
            }
        })
    });

    const result = await response.json();
    return result.ai_response;
}
```

---

## Exposing Backend Publicly (For AI Studio Access)

If your UI is hosted on Google AI Studio, it can't access `localhost:8000`. You need to expose your backend:

### Option 1: Use Existing Cloudflare Tunnel

```bash
# Already running:
https://entitled-aggregate-advisors-commodities.trycloudflare.com

# Your UI can call:
https://entitled-aggregate-advisors-commodities.trycloudflare.com/api/chat/send
```

### Option 2: Deploy Backend to Cloud

Deploy your backend to:
- **Railway** (easiest, free tier)
- **Render** (free tier)
- **Fly.io** (free tier)
- **Heroku** (paid)

Then your UI calls: `https://your-app.railway.app/api/chat/send`

---

## Example: Complete Integration Flow

### Scenario: User asks for properties in your UI

**Step 1: User types in UI**
```
User: "I want a 3-bedroom condo in Marina Bay"
```

**Step 2: UI sends to backend**
```javascript
const response = await fetch('https://your-tunnel-url.trycloudflare.com/api/chat/send', {
    method: 'POST',
    body: JSON.stringify({
        user_id: 'customer123',
        message: 'I want a 3-bedroom condo in Marina Bay'
    })
});
```

**Step 3: Backend processes**
```python
# Backend receives request
# 1. Detects intent (Marina Bay, 3 bedrooms, condo)
# 2. Searches properties database
# 3. Generates AI response with Gemini
# 4. Saves to database
# 5. Returns response
```

**Step 4: Backend returns**
```json
{
    "conversation_id": "uuid-here",
    "user_message": "I want a 3-bedroom condo in Marina Bay",
    "ai_response": "I found 1 great property for you! The Marina Bay Condo is a luxurious 3-bedroom, 2-bathroom unit priced at $1,200,000. Would you like to schedule a viewing?",
    "properties": [
        {
            "id": "prop-123",
            "title": "Marina Bay Condo",
            "location": "Marina Bay",
            "bedrooms": 3,
            "bathrooms": 2,
            "price": 1200000,
            "image_url": null
        }
    ],
    "timestamp": "2025-12-08T12:34:56Z"
}
```

**Step 5: UI displays**
```javascript
// Show AI response
displayMessage(data.ai_response);

// Show property cards
data.properties.forEach(prop => {
    displayPropertyCard(prop);
});
```

---

## CORS Configuration (Important!)

If your UI is on a different domain, you need to enable CORS:

```python
# File: main.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aistudio.google.com",
        "https://makersuite.google.com",
        "http://localhost:3000",  # Your local dev
        "*"  # For testing only, restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Testing Integration

### Test 1: API Health Check from UI

```javascript
// In your UI console
fetch('http://localhost:8000/health')
    .then(r => r.json())
    .then(d => console.log(d));
// Should return: {"status":"ok","database":"ok","environment":"development"}
```

### Test 2: Send Message from UI

```javascript
fetch('http://localhost:8000/api/chat/send', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        user_id: 'test123',
        message: 'Hello, I want a condo'
    })
}).then(r => r.json()).then(d => console.log(d));
```

### Test 3: Search Properties from UI

```javascript
fetch('http://localhost:8000/api/properties/search?location=Marina Bay&bedrooms=3')
    .then(r => r.json())
    .then(d => console.log(d));
```

---

## Next Steps

**Tell me about your UI:**
1. Is it a web interface you built?
2. Is it a Gemini agent with custom actions?
3. Can you share a screenshot or describe what it looks like?

**Then I'll:**
1. Create the exact API endpoints you need
2. Write the integration code for your specific UI type
3. Help you test the connection
4. Deploy if needed (to make it accessible from AI Studio)

---

## Quick Setup Checklist

- [ ] Describe your UI type
- [ ] Determine if UI needs public URL (Cloudflare) or localhost works
- [ ] Add CORS configuration to backend
- [ ] Create API endpoints for UI needs
- [ ] Test connection between UI and backend
- [ ] Deploy (if needed)
- [ ] Full integration test

**Let me know about your UI and I'll create the exact integration code you need!** 🚀
