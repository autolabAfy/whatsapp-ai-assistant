# AI ↔ Human Toggle Logic

## Goal
Handle instant, reliable switching between AI and Human control modes per conversation.

## Core Rules

1. **Per-conversation state**
   - Each conversation has its own `current_mode` field
   - Possible values: `AI` or `HUMAN`
   - Default for new conversations: `AI`

2. **Immediate effect**
   - Mode change takes effect instantly
   - No delayed transitions
   - No queued messages after toggle

3. **No overlap**
   - AI and Human NEVER both respond to same message
   - Mode is checked atomically before every response

## Toggle Operations

### Switch to HUMAN mode
**Trigger:** Agent taps "Take Over" button in UI

**Actions:**
1. Update `conversation.current_mode = HUMAN` in database
2. Cancel any pending AI follow-ups for this conversation
3. Flush any in-flight AI responses (if detected)
4. Update UI to show HUMAN mode active
5. Notify agent: "You're now in control"

**Script:** `execution/set_mode_human.py`

### Switch to AI mode
**Trigger:** Agent taps "Let AI Handle" button in UI

**Actions:**
1. Update `conversation.current_mode = AI` in database
2. Resume AI persona and context
3. Resume follow-up automation (if applicable)
4. Update UI to show AI mode active
5. Notify agent: "AI is now handling this chat"

**Script:** `execution/set_mode_ai.py`

## Edge Cases

### Mid-generation toggle
**Scenario:** AI is generating response, human switches to HUMAN mode

**Solution:**
- AI generation completes but response is NOT sent
- Right before sending, check mode again
- If `mode = HUMAN`, discard response and log

### Human sends message in AI mode
**Scenario:** Agent manually types message while AI mode is active

**Solution:**
- Human message takes precedence
- Automatically switch to HUMAN mode
- Log: "Agent took over mid-conversation"

### Rapid toggling
**Scenario:** Agent switches AI → HUMAN → AI quickly

**Solution:**
- Each toggle is idempotent
- No race conditions via database transactions
- Last toggle wins

## Database Schema Requirements

### Conversation table must have:
```
conversation_id (PK)
agent_id (FK)
contact_number
current_mode (ENUM: AI, HUMAN)
last_mode_change_timestamp
last_mode_changed_by (agent_id or 'SYSTEM')
```

## Tools

- `execution/set_mode_human.py`
- `execution/set_mode_ai.py`
- `execution/check_conversation_mode.py`
- `execution/cancel_followups.py`

## UI Requirements

- Toggle button visible in chat view
- Current mode clearly displayed
- Toggle responds in <500ms
- Visual confirmation of mode change
