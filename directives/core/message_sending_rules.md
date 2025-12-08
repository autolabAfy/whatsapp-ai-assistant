# Message Sending Rules

## Goal
Send WhatsApp messages safely via Green API without duplication, rate limit violations, or mode violations.

## Hard Rules

### Rule 1: Mode Check
ALWAYS check conversation mode right before sending.
- If `mode = HUMAN`, DO NOT SEND
- Only send if `mode = AI`

### Rule 2: No Duplicates
- Track sent messages by `conversation_id + message_content + timestamp`
- Use Redis cache with 5-minute TTL
- If duplicate detected, skip send and log

### Rule 3: Rate Limiting
Green API has limits:
- Check Green API documentation for current limits
- Implement exponential backoff on 429 errors
- Queue messages if rate limit hit

### Rule 4: Message Format
- Plain text only for MVP
- Max length: 4096 characters (WhatsApp limit)
- If AI response exceeds limit, truncate gracefully with "..."

### Rule 5: Delivery Confirmation
- Log every send attempt
- Store Green API response
- Track delivery status if available

## Send Message Flow

1. **Pre-send checks**
   - Verify `mode = AI`
   - Check for duplicate
   - Check rate limit budget

2. **Send via Green API**
   - POST to Green API endpoint
   - Include:
     - `chatId` (recipient)
     - `message` (text)
     - `instance` (agent's WhatsApp instance ID)

3. **Post-send logging**
   - Log message_id
   - Store timestamp
   - Update conversation last_message_timestamp

4. **Error handling**
   - 429 (rate limit): Queue and retry with backoff
   - 401 (auth error): Alert agent, log critical error
   - 500 (Green API down): Queue for retry, alert agent
   - Other errors: Log and alert

## Green API Integration

### Required Environment Variables
```
GREEN_API_INSTANCE_ID
GREEN_API_TOKEN
GREEN_API_BASE_URL (default: https://api.green-api.com)
```

### Endpoint
```
POST {GREEN_API_BASE_URL}/waInstance{INSTANCE_ID}/sendMessage/{TOKEN}

Body:
{
  "chatId": "1234567890@c.us",
  "message": "Hello, how can I help?"
}
```

## Tools

- `execution/send_whatsapp_message.py` (main script)
- `execution/check_rate_limit.py`
- `execution/queue_message.py` (for retries)

## Logging Requirements

Every send attempt must log:
- timestamp
- conversation_id
- recipient (chatId)
- message_content (first 100 chars)
- green_api_response
- success/failure
- error_details (if failed)

## Recovery Strategy

If send fails:
1. Log error
2. Queue for retry (max 3 attempts)
3. If all retries fail, escalate to HUMAN mode automatically
4. Notify agent via UI
