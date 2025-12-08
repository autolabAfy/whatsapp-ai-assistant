# RealtorAI Connect - Mobile App Integration Guide

## Overview

Your **RealtorAI Connect** mobile app is now fully integrated with the backend! This guide shows you how to connect all the features.

---

## Architecture

```
┌─────────────────────────┐
│  RealtorAI Connect      │
│  (Mobile App)           │
│  - Google AI Studio     │
└──────────┬──────────────┘
           │ HTTPS REST API
           ↓
┌─────────────────────────┐
│  Backend API            │
│  localhost:8000         │
│  /api/mobile/*          │
└──────────┬──────────────┘
           │
           ↓
┌─────────────────────────┐
│  PostgreSQL Database    │
│  - Conversations        │
│  - Properties           │
│  - Appointments         │
└─────────────────────────┘
```

---

## API Endpoints Created

### 1. Chat Endpoints

#### **POST /api/mobile/chat/send**
Send message and get AI response

**Request:**
```json
{
  "user_id": "+6591234567",
  "user_name": "Sarah Jenkins",
  "message": "Hi! I want a 3-bedroom condo in Marina Bay",
  "agent_id": "3b5ab91d-ddfb-48cb-a110-acb5144a89fa"
}
```

**Response:**
```json
{
  "conversation_id": "uuid-here",
  "user_message": "Hi! I want a 3-bedroom condo in Marina Bay",
  "ai_response": "I found 1 great property for you! The Marina Bay Condo...",
  "properties": [
    {
      "property_id": "...",
      "title": "Marina Bay Condo",
      "location": "Marina Bay",
      "bedrooms": 3,
      "price": 1200000
    }
  ],
  "timestamp": "2025-12-08T12:34:56Z",
  "lead_type": "Buyer"
}
```

**Use in app:** When user sends message in chat screen

---

#### **GET /api/mobile/conversations**
Get all conversations for inbox

**Request:**
```
GET /api/mobile/conversations?agent_id=3b5ab91d-ddfb-48cb-a110-acb5144a89fa&limit=50
```

**Response:**
```json
[
  {
    "conversation_id": "...",
    "contact_name": "Sarah Jenkins",
    "contact_number": "+6591234567",
    "last_message": "Yes, is Saturday available?",
    "last_message_time": "2025-12-08T00:10:00Z",
    "unread_count": 1,
    "lead_type": "Buyer",
    "status": "active"
  }
]
```

**Use in app:** Load chat list on "Chats" screen

---

#### **GET /api/mobile/conversations/{conversation_id}/messages**
Get message history

**Request:**
```
GET /api/mobile/conversations/abc-123/messages?limit=100
```

**Response:**
```json
[
  {
    "message_id": "...",
    "sender_type": "USER",
    "message_text": "Hi! I want a condo",
    "timestamp": "2025-12-08T12:00:00Z"
  },
  {
    "message_id": "...",
    "sender_type": "AI",
    "message_text": "I'd be happy to help!",
    "timestamp": "2025-12-08T12:00:30Z"
  }
]
```

**Use in app:** Load messages when user taps conversation

---

### 2. Property Endpoints

#### **GET /api/mobile/properties/search**
Search properties

**Request:**
```
GET /api/mobile/properties/search?location=Marina+Bay&bedrooms=3&max_price=1500000
```

**Response:**
```json
[
  {
    "property_id": "...",
    "title": "Marina Bay Condo",
    "location": "Marina Bay",
    "property_type": "condo",
    "price": 1200000,
    "bedrooms": 3,
    "bathrooms": 2,
    "size_sqft": 1400,
    "description": "Luxury condo with sea views",
    "image_url": null
  }
]
```

**Use in app:** Property browsing, knowledge base

---

#### **GET /api/mobile/properties/{property_id}**
Get property details

**Use in app:** When user taps on property card

---

### 3. Appointment Endpoints

#### **POST /api/mobile/appointments/create**
Create appointment

**Request:**
```json
{
  "conversation_id": "...",
  "appointment_type": "Viewing",
  "scheduled_time": "2025-12-09T14:00:00Z",
  "location": "12 Maple Ave, Springfield",
  "notes": "Client prefers afternoon viewings"
}
```

**Response:**
```json
{
  "appointment_id": "...",
  "status": "created",
  "scheduled_time": "2025-12-09T14:00:00Z"
}
```

**Use in app:** Calendar screen - create viewings, meetings, calls

---

#### **GET /api/mobile/appointments**
Get all appointments

**Request:**
```
GET /api/mobile/appointments?agent_id=3b5ab91d-ddfb-48cb-a110-acb5144a89fa
```

**Response:**
```json
[
  {
    "appointment_id": "...",
    "type": "Viewing",
    "scheduled_time": "2025-12-09T14:00:00Z",
    "location": "12 Maple Ave, Springfield",
    "contact_name": "Sarah Jenkins",
    "status": "scheduled"
  }
]
```

**Use in app:** Calendar screen - show all appointments

---

### 4. Agent Settings Endpoints

#### **GET /api/mobile/agent/settings**
Get AI settings

**Response:**
```json
{
  "assistant_name": "Alex",
  "tone": "professional",
  "response_delay": 30,
  "custom_instruction": "Always mention property investment potential"
}
```

**Use in app:** Agent settings screen - display current settings

---

#### **PUT /api/mobile/agent/settings**
Update AI settings

**Request:**
```json
{
  "agent_id": "3b5ab91d-ddfb-48cb-a110-acb5144a89fa",
  "tone": "casual",
  "response_delay": 10,
  "custom_instruction": "Be very friendly and enthusiastic"
}
```

**Use in app:** Agent settings screen - save changes

---

### 5. Usage/Analytics Endpoints

#### **GET /api/mobile/usage/stats**
Get usage statistics

**Response:**
```json
{
  "tokens_used": 124000,
  "estimated_cost": 4.12,
  "conversations_count": 45,
  "messages_count": 230,
  "period": "all_time"
}
```

**Use in app:** Usage & Costs screen

---

## Integration Steps

### Step 1: Get Public URL

Your backend needs to be accessible from the internet for your mobile app to connect.

**Option A: Use Cloudflare Tunnel (Already Running)**
```
https://entitled-aggregate-advisors-commodities.trycloudflare.com
```

**Option B: Deploy to Cloud (Production)**
- Railway: https://railway.app
- Render: https://render.com
- Fly.io: https://fly.io

---

### Step 2: Update Mobile App API Base URL

In your RealtorAI Connect app, set the base URL:

**Development (Local):**
```javascript
const API_BASE_URL = "https://entitled-aggregate-advisors-commodities.trycloudflare.com";
```

**Production:**
```javascript
const API_BASE_URL = "https://your-app.railway.app";
```

---

### Step 3: Connect Each Screen

#### **Chats Screen**

```javascript
// Load conversations
async function loadConversations() {
    const response = await fetch(
        `${API_BASE_URL}/api/mobile/conversations?agent_id=${AGENT_ID}`
    );
    const conversations = await response.json();

    // Display in UI
    displayConversationList(conversations);
}

// Send message
async function sendMessage(userId, userName, message) {
    const response = await fetch(
        `${API_BASE_URL}/api/mobile/chat/send`,
        {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: userId,
                user_name: userName,
                message: message,
                agent_id: AGENT_ID
            })
        }
    );

    const data = await response.json();

    // Display AI response
    displayMessage(data.ai_response);

    // Show properties if any
    if (data.properties) {
        displayPropertyCards(data.properties);
    }
}

// Load message history
async function loadMessages(conversationId) {
    const response = await fetch(
        `${API_BASE_URL}/api/mobile/conversations/${conversationId}/messages`
    );
    const messages = await response.json();

    // Display chat history
    displayChatHistory(messages);
}
```

---

#### **Agent Settings Screen**

```javascript
// Load settings
async function loadAgentSettings() {
    const response = await fetch(
        `${API_BASE_URL}/api/mobile/agent/settings?agent_id=${AGENT_ID}`
    );
    const settings = await response.json();

    // Update UI
    toneSelector.value = settings.tone;
    responseDelaySlider.value = settings.response_delay;
}

// Save settings
async function saveAgentSettings(tone, responseDelay) {
    const response = await fetch(
        `${API_BASE_URL}/api/mobile/agent/settings`,
        {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                agent_id: AGENT_ID,
                tone: tone,
                response_delay: responseDelay
            })
        }
    );

    return await response.json();
}
```

---

#### **Knowledge Base (Docs) Screen**

The docs screen shows property listings. Connect to property search:

```javascript
// Load properties for knowledge base
async function loadProperties() {
    const response = await fetch(
        `${API_BASE_URL}/api/mobile/properties/search?agent_id=${AGENT_ID}&limit=50`
    );
    const properties = await response.json();

    // Display as documents
    displayAsDocuments(properties);
}
```

---

#### **Calendar Screen**

```javascript
// Load appointments
async function loadAppointments() {
    const response = await fetch(
        `${API_BASE_URL}/api/mobile/appointments?agent_id=${AGENT_ID}`
    );
    const appointments = await response.json();

    // Display on calendar
    displayOnCalendar(appointments);
}

// Create appointment
async function createAppointment(conversationId, type, dateTime, location) {
    const response = await fetch(
        `${API_BASE_URL}/api/mobile/appointments/create`,
        {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                conversation_id: conversationId,
                appointment_type: type,
                scheduled_time: dateTime,
                location: location
            })
        }
    );

    return await response.json();
}
```

---

#### **Usage Screen**

```javascript
// Load usage stats
async function loadUsageStats() {
    const response = await fetch(
        `${API_BASE_URL}/api/mobile/usage/stats?agent_id=${AGENT_ID}`
    );
    const stats = await response.json();

    // Display stats
    tokensUsedEl.textContent = stats.tokens_used;
    estimatedCostEl.textContent = `$${stats.estimated_cost}`;
}
```

---

## Testing Integration

### Test 1: Send Message

```bash
curl -X POST https://entitled-aggregate-advisors-commodities.trycloudflare.com/api/mobile/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "+6591234567",
    "user_name": "Test User",
    "message": "Hi! I want a 3-bedroom condo",
    "agent_id": "3b5ab91d-ddfb-48cb-a110-acb5144a89fa"
  }'
```

**Expected:** JSON with conversation_id and AI response

---

### Test 2: Get Conversations

```bash
curl https://entitled-aggregate-advisors-commodities.trycloudflare.com/api/mobile/conversations
```

**Expected:** Array of conversations

---

### Test 3: Search Properties

```bash
curl "https://entitled-aggregate-advisors-commodities.trycloudflare.com/api/mobile/properties/search?bedrooms=3"
```

**Expected:** Array of 3-bedroom properties

---

## Mobile App Feature Mapping

| Mobile App Screen | Backend Endpoint | Purpose |
|------------------|------------------|---------|
| **Chats** | `/api/mobile/conversations` | Load conversation list |
| **Chats** | `/api/mobile/chat/send` | Send message, get AI reply |
| **Chats** | `/api/mobile/conversations/{id}/messages` | Load chat history |
| **Agent** | `/api/mobile/agent/settings` | Get/update AI settings |
| **Docs** | `/api/mobile/properties/search` | Load property listings |
| **Calendar** | `/api/mobile/appointments` | Load appointments |
| **Calendar** | `/api/mobile/appointments/create` | Create new appointment |
| **Usage** | `/api/mobile/usage/stats` | Get token usage and costs |
| **Profile** | (Coming soon) | Agent profile management |

---

## Next Steps

1. **Update your mobile app** with the API base URL
2. **Test each screen** with the endpoints above
3. **Deploy backend** to production (Railway/Render) for stable URL
4. **Add authentication** (JWT tokens) for security
5. **Add image support** for property photos
6. **Add push notifications** for new messages

---

## Production Deployment

When ready to deploy:

### Option 1: Railway (Recommended)

```bash
# Install Railway CLI
brew install railway

# Login
railway login

# Initialize project
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant
railway init

# Add PostgreSQL
railway add

# Deploy
railway up

# Get URL
railway domain
```

### Option 2: Render

1. Go to https://render.com
2. Connect GitHub repo
3. Create new Web Service
4. Add PostgreSQL database
5. Set environment variables from `.env`
6. Deploy

---

## Security Considerations

**Current Setup:** No authentication (OK for MVP testing)

**Production:** Add JWT authentication
```javascript
// In mobile app, add auth header
headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
}
```

---

## Support

**API Documentation:** http://localhost:8000/docs (or your deployed URL)

**Test Endpoints:** Use the FastAPI interactive docs to test all endpoints

**Backend Logs:**
```bash
tail -f logs/app.log
```

---

**Your mobile app is now ready to connect to the full backend!** 🚀

All features from your RealtorAI Connect app now have corresponding backend APIs.
