# Escalation Triggers

## Goal
Automatically switch to HUMAN mode when AI should not handle the conversation.

## Hard Escalation Rules

AI MUST escalate immediately when:

### 1. Negotiation Intent Detected
**Triggers:**
- "Can you lower the price?"
- "What's your best offer?"
- "Is this negotiable?"
- "Can we discuss pricing?"

**Response + Action:**
```
Let me connect you with the agent directly to discuss pricing options.
[AUTO-SWITCH TO HUMAN MODE]
```

### 2. Objections or Concerns
**Triggers:**
- "I'm not sure about..."
- "I'm concerned that..."
- "What about [problem]?"
- "Is there an issue with..."

**Response + Action:**
```
I'll let the agent take over so they can address your concerns properly.
[AUTO-SWITCH TO HUMAN MODE]
```

### 3. Explicit Human Request
**Triggers:**
- "Can I speak to a person?"
- "I want to talk to the agent"
- "Connect me with someone"
- "Is this a bot?"

**Response + Action:**
```
Of course! Connecting you with the agent now.
[AUTO-SWITCH TO HUMAN MODE]
```

### 4. Legal or Contract Questions
**Triggers:**
- "What's in the contract?"
- "What are the terms?"
- "Legal requirements"
- "Tenancy agreement"

**Response + Action:**
```
I'll have the agent discuss the legal details with you directly.
[AUTO-SWITCH TO HUMAN MODE]
```

### 5. Custom Requests Outside Property Data
**Triggers:**
- "Can you arrange special financing?"
- "I need renovations included"
- "Can we customize the unit?"
- Anything requiring agent discretion

**Response + Action:**
```
Let me get the agent to help you with that request.
[AUTO-SWITCH TO HUMAN MODE]
```

### 6. Complaint or Dissatisfaction
**Triggers:**
- "I'm not happy with..."
- "This is disappointing"
- "I had a bad experience"
- Negative sentiment detected

**Response + Action:**
```
I'm sorry to hear that. Let me connect you with the agent right away.
[AUTO-SWITCH TO HUMAN MODE]
```

### 7. Multiple Failed Queries
**Trigger:**
- AI fails to find matching properties 3 times in a row
- User repeats same question 3 times

**Response + Action:**
```
I'm having trouble finding what you're looking for.
Let me have the agent assist you directly.
[AUTO-SWITCH TO HUMAN MODE]
```

## Soft Escalation (Optional, Agent Preference)

Agent can configure optional escalation for:
- All messages after 10 PM
- Weekends
- Specific keywords
- VIP contacts (flagged in database)

## Escalation Flow

1. **Detect trigger** in user message
2. **Generate handoff message** (per persona)
3. **Switch to HUMAN mode** via `execution/set_mode_human.py`
4. **Send handoff message**
5. **Cancel pending follow-ups**
6. **Notify agent** via UI with reason

## Escalation Logging

Every escalation must log:
- timestamp
- conversation_id
- trigger_type (negotiation, objection, explicit_request, etc.)
- triggering_message (user's message)
- ai_handoff_message (what AI said before switching)

## Tools

- `execution/detect_escalation_triggers.py`
- `execution/set_mode_human.py`
- `execution/send_handoff_message.py`

## Agent Override

Agent can configure escalation sensitivity:
- **Conservative** - Escalate on first hint of complexity
- **Balanced** - Escalate on clear triggers
- **Confident** - Minimal escalation, AI handles more

Default: **Balanced**

## Edge Cases

### User asks pricing question but not negotiating
**Example:** "How much is this property?"
- This is INFO request, not NEGOTIATION
- AI can answer with database price
- Do NOT escalate

**Example:** "Can you go lower on the price?"
- This IS negotiation
- Escalate immediately

### User asks generic legal question
**Example:** "Do I need a lawyer to buy property?"
- General question, not contract-specific
- AI can provide general info: "It's recommended to have legal advice for property transactions"
- Do NOT escalate

**Example:** "What are the clauses in this sale agreement?"
- Contract-specific
- Escalate immediately

## Testing Escalation Detection

Test phrases:
1. "What's available in Orchard?" → NO escalation
2. "Can you lower the price to $800k?" → ESCALATE
3. "Is this a bot?" → ESCALATE
4. "How many bedrooms?" → NO escalation
5. "I'm concerned about the location" → ESCALATE
6. "Thanks for the info!" → NO escalation
