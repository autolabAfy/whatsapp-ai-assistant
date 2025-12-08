# Race Condition Handling

## Goal
Prevent message duplication, mode conflicts, and state corruption when events happen simultaneously.

## Critical Race Conditions

### 1. Mode Toggle During AI Response Generation

**Scenario:**
1. User sends message at T=0
2. AI starts generating response (takes 2-3 seconds)
3. At T=1, agent toggles to HUMAN mode
4. At T=3, AI response completes

**Problem:** Without safeguards, AI sends response despite HUMAN mode being active.

**Solution:**
```python
# In send_whatsapp_message.py
def send_message(conversation_id, message):
    # Atomic check right before send
    current_mode = check_mode_atomic(conversation_id)

    if current_mode != 'AI':
        log_discarded_response(conversation_id, message)
        return False  # Do not send

    # Proceed with send
    green_api.send(message)
```

### 2. Simultaneous Messages from User

**Scenario:**
1. User sends "Show me condos" at T=0
2. User sends "In Orchard" at T=0.1
3. Two webhooks arrive nearly simultaneously

**Problem:** Two AI responses being generated in parallel.

**Solution:**
- Use conversation-level lock (Redis or database)
- Process messages sequentially per conversation
- Queue second message until first completes

```python
# In webhook handler
def handle_webhook(chat_id, message):
    lock_key = f"conversation_lock:{chat_id}"

    with redis_lock(lock_key, timeout=30):
        # Process message
        route_message(chat_id, message)
```

### 3. Duplicate Webhook Delivery

**Scenario:**
Green API sends same webhook twice due to network retry.

**Solution:**
- Generate unique message fingerprint: `hash(chatId + timestamp + message_text)`
- Store in Redis with 5-minute TTL
- Skip processing if fingerprint exists

```python
def is_duplicate_webhook(webhook_payload):
    fingerprint = hash_webhook(webhook_payload)

    if redis.exists(f"webhook:{fingerprint}"):
        return True

    redis.setex(f"webhook:{fingerprint}", 300, "1")
    return False
```

### 4. Human Sends Message While in AI Mode

**Scenario:**
1. Conversation is in AI mode
2. Agent manually types and sends message from UI
3. Meanwhile, user sends new message
4. Both AI and human responses might be generated

**Solution:**
- Human message ALWAYS switches mode to HUMAN automatically
- Cancel any in-flight AI responses for that conversation
- Log: "Agent took manual control"

```python
def handle_agent_message(conversation_id, message):
    # Immediate mode switch
    set_mode_human(conversation_id, reason="agent_manual_message")

    # Cancel AI processing if any
    cancel_ai_generation(conversation_id)

    # Send human message
    send_message(conversation_id, message)
```

### 5. Multiple Follow-up Schedules

**Scenario:**
1. AI schedules 24h follow-up
2. User replies before 24h
3. New conversation flow might schedule another follow-up
4. Risk: Multiple follow-ups active simultaneously

**Solution:**
- Cancel ALL existing follow-ups when user replies
- Only ONE active follow-up per conversation at any time
- Follow-up table has unique constraint on `(conversation_id, status=pending)`

```python
def schedule_followup(conversation_id, delay_hours):
    # Cancel any existing pending follow-ups
    cancel_existing_followups(conversation_id)

    # Create new follow-up
    create_followup(conversation_id, delay_hours)
```

## Database Transaction Rules

### Use transactions for:
1. Mode changes + follow-up cancellation (atomic)
2. Message send + conversation update (atomic)
3. Any operation that modifies multiple tables

### Example:
```python
def set_mode_human(conversation_id):
    with db.transaction():
        # Update mode
        db.execute(
            "UPDATE conversations SET current_mode = 'HUMAN' WHERE id = %s",
            (conversation_id,)
        )

        # Cancel follow-ups
        db.execute(
            "UPDATE followups SET status = 'cancelled' WHERE conversation_id = %s",
            (conversation_id,)
        )
```

## Redis Locks

Use Redis for distributed locks when:
- Processing messages per conversation
- Sending messages
- Toggling modes

```python
from redis import Redis
import redis.lock

redis_client = Redis()

def with_conversation_lock(conversation_id, func):
    lock = redis_client.lock(f"lock:conversation:{conversation_id}", timeout=30)

    with lock:
        return func()
```

## Idempotency Keys

For external API calls (Green API):
- Generate idempotency key per message
- Store in database
- Retry with same key if failure

```python
def send_with_idempotency(conversation_id, message):
    idempotency_key = f"{conversation_id}:{hash(message)}:{int(time.time())}"

    # Check if already sent
    if db.exists("sent_messages", idempotency_key):
        return True  # Already sent

    # Send message
    response = green_api.send(message, idempotency_key=idempotency_key)

    # Record
    db.insert("sent_messages", {
        "idempotency_key": idempotency_key,
        "conversation_id": conversation_id,
        "message": message,
        "response": response
    })
```

## Testing Race Conditions

### Test Cases:
1. Send message → toggle to HUMAN mid-generation → verify no AI message sent
2. Send two messages 100ms apart → verify both processed in order
3. Send duplicate webhook → verify only processed once
4. Agent sends manual message in AI mode → verify auto-switch to HUMAN
5. Schedule follow-up → user replies → verify follow-up cancelled

## Tools

- `execution/redis_lock.py` - Lock utilities
- `execution/deduplicate_webhook.py` - Webhook deduplication
- `execution/atomic_mode_check.py` - Atomic mode verification

## Logging

Log every race condition event:
- timestamp
- conversation_id
- event_type (mode_change_during_generation, duplicate_webhook, etc.)
- action_taken (discarded_message, cancelled_followup, etc.)
- details
