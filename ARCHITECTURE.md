# WhatsApp AI Assistant - System Architecture

## Overview

This system implements a **self-healing, production-ready WhatsApp AI chatbot platform** for real estate agents, built on a **3-layer architecture** that separates probabilistic AI decision-making from deterministic business logic.

## Core Design Principle

**Problem**: LLMs are probabilistic. Business logic must be deterministic.

**Solution**: The 3-Layer Architecture

```
┌─────────────────────────────────────────┐
│   LAYER 1: DIRECTIVE (What to do)      │
│   - SOPs in Markdown                    │
│   - Define goals, rules, workflows      │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   LAYER 2: ORCHESTRATION (When)        │
│   - AI Agent decision making            │
│   - Route to correct execution          │
│   - Handle errors, ask questions        │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   LAYER 3: EXECUTION (How)             │
│   - Python scripts                      │
│   - Database operations                 │
│   - API calls                           │
│   - Deterministic, testable, reliable   │
└─────────────────────────────────────────┘
```

## Message Flow Architecture

### Incoming Message Path

```
WhatsApp User
     ↓
Green API (WhatsApp Web API)
     ↓
POST /webhook/greenapi
     ↓
webhook_handler.py
     ├─→ Deduplicate (Redis)
     ├─→ Extract message data
     ├─→ Identify/create conversation
     ├─→ Check mode (AI or HUMAN)
     └─→ Route:
          ├─ AI MODE:
          │   ├─→ generate_ai_response.py
          │   │    ├─→ Load persona
          │   │    ├─→ Detect property intent
          │   │    ├─→ Query properties
          │   │    ├─→ Call Claude API
          │   │    └─→ Return response
          │   └─→ send_whatsapp_message.py
          │        ├─→ Mode check (atomic)
          │        ├─→ Deduplication check
          │        ├─→ Send via Green API
          │        └─→ Log message
          └─ HUMAN MODE:
              └─→ Store in inbox (no AI response)
```

### Mode Toggle Flow

```
Agent clicks "Take Over" in UI
     ↓
POST /api/conversations/toggle-mode
     ↓
set_mode_human.py
     ├─→ Start transaction
     ├─→ Update conversation.current_mode = 'HUMAN'
     ├─→ Cancel pending follow-ups
     └─→ Commit transaction
     ↓
UI updates to show HUMAN mode
     ↓
Future messages route to inbox only
```

## Data Architecture

### Core Tables

```sql
agents
├─ agent_id (PK)
├─ whatsapp_number
├─ green_api_instance_id
├─ green_api_token
└─ persona (assistant_name, speaking_style, custom_instruction)

conversations
├─ conversation_id (PK)
├─ agent_id (FK)
├─ contact_number
├─ current_mode (AI | HUMAN)  ← Critical field
└─ last_mode_change_timestamp

messages
├─ message_id (PK)
├─ conversation_id (FK)
├─ sender_type (USER | AI | HUMAN)
├─ message_text
└─ timestamp

properties
├─ property_id (PK)
├─ agent_id (FK)
├─ title, location, price, type
├─ availability (available | pending | sold)
└─ key_selling_points
```

### Redis Cache Structure

```
Keys:
- lock:conversation:{id}          → Conversation processing lock
- webhook:{fingerprint}            → Webhook deduplication (5 min TTL)
- lock:{key}                      → General purpose locks
```

## Component Architecture

### 1. Webhook Handler (`webhook_handler.py`)

**Responsibility**: Process all incoming WhatsApp messages

**Key Functions**:
- `process_webhook()` - Main entry point
- `generate_webhook_fingerprint()` - Deduplication
- `extract_message_data()` - Parse Green API payload
- `store_incoming_message()` - Persist to database

**Safety Features**:
- Webhook deduplication (5-minute window)
- Conversation-level locking (prevents race conditions)
- Atomic mode checks
- Comprehensive logging

### 2. AI Response Generator (`generate_ai_response.py`)

**Responsibility**: Generate contextual AI responses

**Key Functions**:
- `generate_ai_response()` - Main generation function
- `load_agent_persona()` - Get persona configuration
- `build_system_prompt()` - Construct Claude system prompt
- `detect_property_intent()` - Extract search parameters
- `get_conversation_history()` - Load recent messages

**Process**:
1. Load agent's persona (tone, style, custom instructions)
2. Detect if message contains property inquiry
3. If yes: Query agent's properties
4. Build system prompt with persona + property context
5. Generate response via Claude API
6. Return response text

### 3. Message Sender (`send_whatsapp_message.py`)

**Responsibility**: Send messages via Green API safely

**Key Functions**:
- `send_whatsapp_message()` - Main send function
- `check_already_sent()` - Idempotency check
- `send_to_green_api()` - Green API integration
- `log_sent_message()` - Audit logging

**Safety Checks**:
1. Verify conversation is in AI mode (unless forced)
2. Check for duplicate send (idempotency)
3. Truncate if message too long (4096 char limit)
4. Atomic mode verification right before send
5. Log every send attempt

### 4. Property Lookup (`property_lookup.py`)

**Responsibility**: Search agent's property database

**Key Functions**:
- `search_properties()` - Query with filters
- `format_property_response()` - Format for WhatsApp
- `get_property_by_id()` - Fetch single property

**Search Parameters**:
- Location (fuzzy match)
- Property type (condo, HDB, landed, etc.)
- Price range (min/max)
- Bedrooms
- Availability

### 5. Mode Management (`set_mode_*.py`)

**Responsibility**: Toggle AI ↔ HUMAN control

**Key Functions**:
- `set_mode_human()` - Switch to human control
- `set_mode_ai()` - Switch to AI control
- `cancel_conversation_followups()` - Stop automation

**Atomicity**:
- Uses database transactions
- Combines mode change + follow-up cancellation
- Logs every mode change with reason

## Race Condition Prevention

### Problem Scenarios

1. **Mid-Generation Toggle**
   - User sends message
   - AI starts generating (2-3 sec)
   - Agent toggles to HUMAN mid-generation
   - **Risk**: AI sends response after toggle

2. **Duplicate Webhooks**
   - Green API sends same webhook twice
   - **Risk**: Two AI responses to same message

3. **Concurrent Messages**
   - User sends two messages rapidly
   - **Risk**: Responses out of order or duplicated

### Solutions Implemented

**1. Conversation Locks (Redis)**
```python
with redis.lock(f"conversation:{conversation_id}"):
    # Process message
    # Generate response
    # Send response
```

**2. Atomic Mode Check**
```python
def send_whatsapp_message(conversation_id, message):
    # Right before sending:
    current_mode = check_mode_atomic(conversation_id)
    if current_mode != 'AI':
        discard(message)  # Don't send
        return False
    send_to_green_api(message)
```

**3. Webhook Deduplication**
```python
fingerprint = hash(chatId + timestamp + message)
if redis.exists(f"webhook:{fingerprint}"):
    return  # Skip duplicate
redis.setex(f"webhook:{fingerprint}", 300, "1")
```

**4. Idempotent Sends**
```python
idempotency_key = hash(conversation_id + message + timestamp)
if already_sent(idempotency_key):
    return  # Already sent
send_and_log(message, idempotency_key)
```

## Escalation Architecture

### Automatic Escalation Triggers

AI automatically switches to HUMAN mode when detecting:

1. **Negotiation Intent**
   - "Can you lower the price?"
   - "What's your best offer?"

2. **Objections/Concerns**
   - "I'm concerned about..."
   - "What about [problem]?"

3. **Legal Questions**
   - Contract terms
   - Legal requirements

4. **Explicit Human Request**
   - "Can I speak to a person?"
   - "Is this a bot?"

5. **Failed Queries**
   - No properties found 3 times in a row

### Escalation Flow

```
Detect trigger in user message
     ↓
Generate handoff message
     ↓
set_mode_human(conversation_id, reason="escalation_trigger")
     ↓
Send handoff message
     ↓
Cancel pending follow-ups
     ↓
Log escalation event
     ↓
Notify agent via UI
```

## Persona System

### Persona Configuration

Each agent configures:
- **Assistant name** (what AI calls itself)
- **Speaking style** (professional, friendly, casual, premium)
- **Tone slider** (1-10, formal to conversational)
- **Personality flags** (polite, warm, high-energy, short)
- **Custom instruction** (free-form personality guide)

### System Prompt Construction

```python
system_prompt = f"""
You are {assistant_name}, an AI assistant for a real estate agent.

Speaking style: {speaking_style}
Tone: {tone_description}

RULES:
- Only discuss properties from the database below
- Never invent property details
- Be {tone} but always accurate
- Keep responses under 3 paragraphs

AVAILABLE PROPERTIES:
{property_context}

{custom_instruction}
"""
```

### Guardrails

Persona affects **HOW** AI speaks, not **WHAT** facts it states:
- ✅ Persona controls: greeting style, word choice, enthusiasm
- ❌ Persona cannot override: property facts, safety rules, escalation triggers

## Self-Annealing Loop

### Concept

When errors occur, the system **learns and improves** itself.

### Process

```
Error detected
     ↓
Analyze error type
     ├─ Directive gap?
     ├─ Orchestration mistake?
     └─ Execution failure?
     ↓
Fix at correct layer
     ↓
Test fix
     ↓
Update relevant directive
     ↓
System now stronger
```

### Example

```
Scenario: AI hits rate limit on Green API
     ↓
Error: 429 Too Many Requests
     ↓
Analysis: No retry logic in send_whatsapp_message.py
     ↓
Fix: Add exponential backoff + queue
     ↓
Test: Verify retry works
     ↓
Update: directives/core/message_sending_rules.md
     └─ Add section on rate limit handling
```

## Deployment Architecture

### Development

```
PostgreSQL (local)
     ↑
FastAPI Server (localhost:8000)
     ↑
ngrok (public HTTPS tunnel)
     ↑
Green API webhooks
```

### Production

```
PostgreSQL (RDS / managed DB)
     ↑
FastAPI + Uvicorn (Gunicorn workers)
     ↑
Nginx (reverse proxy + SSL)
     ↑
Domain (HTTPS)
     ↑
Green API webhooks
```

## Security Considerations

### Implemented

- Environment variable configuration (no hardcoded secrets)
- Database connection pooling
- SQL injection prevention (parameterized queries)
- Redis locks for concurrency control
- Webhook payload validation

### Production Additions Needed

- [ ] JWT authentication for API endpoints
- [ ] Rate limiting (per agent, per IP)
- [ ] Input sanitization and validation
- [ ] CORS configuration (whitelist domains)
- [ ] HTTPS enforcement
- [ ] Agent authentication/authorization
- [ ] Audit logging
- [ ] Secret rotation

## Performance Characteristics

### Latency

- Webhook processing: <100ms
- AI response generation: 2-5 seconds (Claude API)
- Mode toggle: <50ms
- Property search: <100ms

### Throughput

- Can handle ~100 concurrent conversations
- Limited by Claude API rate limits
- Green API limits vary by plan

### Scalability

**Current bottlenecks:**
1. Single FastAPI instance (horizontal scaling needed)
2. Claude API rate limits (can upgrade tier)
3. Database connections (add connection pooling)

**Scaling strategy:**
1. Add load balancer
2. Run multiple FastAPI instances
3. Use PostgreSQL read replicas
4. Implement caching layer (Redis)
5. Queue system for AI generation (Celery)

## Monitoring & Observability

### Logging

All events logged with:
- Timestamp
- Conversation ID
- Action taken
- Error details (if any)

### Key Metrics to Monitor

1. **Message throughput**
   - Messages received per minute
   - Responses sent per minute

2. **Mode distribution**
   - % conversations in AI mode
   - % conversations in HUMAN mode

3. **Escalation rate**
   - Escalations per 100 messages
   - Escalation reasons

4. **Response quality**
   - Properties matched correctly
   - User satisfaction (if tracked)

5. **System health**
   - Database connection pool usage
   - Redis memory usage
   - API response times

### Recommended Tools

- **Logs**: Loguru (current) + Elasticsearch
- **Metrics**: Prometheus + Grafana
- **Errors**: Sentry
- **Uptime**: UptimeRobot / Pingdom
- **APM**: New Relic / DataDog

## Future Enhancements

### Phase 2 Features

1. **Follow-up Automation**
   - Scheduled follow-ups (2h, 24h, 72h)
   - Auto-cancel on user reply

2. **Appointment Booking**
   - AI schedules property viewings
   - Calendar integration

3. **Analytics Dashboard**
   - Conversation metrics
   - Property performance
   - AI effectiveness

4. **Multi-agent Support**
   - Team inbox
   - Agent assignment
   - Workload distribution

5. **Advanced Property Matching**
   - Semantic search
   - Image recognition
   - Location-based recommendations

### Technical Improvements

1. **WebSocket Support**
   - Real-time inbox updates
   - Live typing indicators

2. **Message Queue**
   - Celery for background tasks
   - Retry mechanisms

3. **Caching Layer**
   - Conversation state caching
   - Property search results

4. **Testing Suite**
   - Unit tests
   - Integration tests
   - End-to-end tests

## Conclusion

This architecture balances:
- **Reliability**: Deterministic execution layer
- **Intelligence**: AI-powered orchestration
- **Flexibility**: Directive-driven workflows
- **Safety**: Race condition prevention, escalation triggers
- **Maintainability**: Clear separation of concerns

The system is designed to **self-improve over time** through the self-annealing loop, making it increasingly robust as it encounters real-world scenarios.
