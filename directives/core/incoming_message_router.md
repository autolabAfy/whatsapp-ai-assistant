# Incoming Message Router

## Goal
Process every incoming WhatsApp message and route it correctly based on conversation mode.

## Input
- Webhook payload from Green API containing:
  - `chatId` (sender WhatsApp number)
  - `messageData.textMessageData.textMessage` (message text)
  - `timestamp`
  - `instanceId` (agent's WhatsApp instance)

## Decision Tree

1. **Identify or create conversation**
   - Look up conversation by `(agent_whatsapp_instance, contact_number)`
   - If not exists: create new conversation with `mode=AI` (default)

2. **Check conversation mode**
   - Load `current_mode` from database
   - This is atomic - use database lock if needed

3. **Route based on mode**

### IF mode = AI
   - Call `execution/generate_ai_response.py`
   - Send response via `execution/send_whatsapp_message.py`
   - Log interaction

### IF mode = HUMAN
   - Store message in database
   - Update inbox UI (via WebSocket or polling)
   - Do NOT generate AI response
   - Do NOT send anything

## Edge Cases

### Race condition: Mode changed during AI generation
- Always check mode AGAIN right before sending
- If mode switched to HUMAN mid-generation, discard the AI response
- Never send if mode is HUMAN

### Duplicate webhooks
- Green API may send duplicate webhooks
- Use `message_id` or `timestamp + chatId` to deduplicate
- Store processed message IDs in Redis with 5-minute TTL

### Message from unknown number
- Always create new conversation
- Default to AI mode
- Log as "new contact"

## Output
- Conversation record updated
- Message logged
- Response sent (if AI mode) OR message queued in inbox (if HUMAN mode)

## Tools to Use
- `execution/identify_conversation.py`
- `execution/check_conversation_mode.py`
- `execution/generate_ai_response.py` (conditional)
- `execution/send_whatsapp_message.py` (conditional)

## Logging
- Every message logged with:
  - timestamp
  - conversation_id
  - sender
  - mode_at_receipt
  - action_taken (AI_REPLIED | QUEUED_FOR_HUMAN)
