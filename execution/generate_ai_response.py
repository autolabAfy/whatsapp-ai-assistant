"""
Generate AI response using Claude
Applies agent persona and property context
"""
from typing import List, Dict, Optional
from loguru import logger
from anthropic import Anthropic

from execution.config import settings, get_anthropic_api_key
from execution.database import get_db
from execution.property_lookup import search_properties, format_property_response


def load_agent_persona(agent_id: str) -> Dict:
    """Load agent's AI persona configuration"""
    db = get_db()

    query = """
        SELECT
            assistant_name,
            speaking_style,
            tone_slider,
            personality_flags,
            custom_instruction
        FROM agents
        WHERE agent_id = %s
    """

    persona = db.execute_one(query, (agent_id,))

    if not persona:
        # Default persona
        return {
            "assistant_name": "Assistant",
            "speaking_style": "friendly",
            "tone_slider": 5,
            "personality_flags": [],
            "custom_instruction": None
        }

    return persona


def build_system_prompt(persona: Dict, properties_context: Optional[str] = None) -> str:
    """
    Build system prompt from persona configuration

    Args:
        persona: Agent persona dict
        properties_context: Available properties as text

    Returns:
        System prompt string
    """
    assistant_name = persona.get('assistant_name', 'Assistant')
    speaking_style = persona.get('speaking_style', 'friendly')
    custom_instruction = persona.get('custom_instruction', '')

    # Base prompt
    system_prompt = f"""You are {assistant_name}, an AI assistant for a real estate agent.

Speaking style: {speaking_style}

CRITICAL RULES:
1. Only discuss properties from the provided property database below
2. NEVER invent or hallucinate property details, pricing, or availability
3. If you don't have information, say so clearly
4. Keep responses under 3 paragraphs
5. Format for WhatsApp (plain text, no markdown)
6. Be helpful but concise

ESCALATION TRIGGERS - Switch to human agent if user:
- Asks to negotiate pricing
- Raises objections or concerns
- Requests contract/legal details
- Explicitly asks for a human
- Asks about custom requests outside standard property info

"""

    # Add style guidance based on speaking_style
    if speaking_style == "professional":
        system_prompt += "\nTone: Professional and formal. Use complete sentences and polite language.\n"
    elif speaking_style == "friendly":
        system_prompt += "\nTone: Warm and approachable. Use contractions naturally. Be helpful and enthusiastic.\n"
    elif speaking_style == "casual":
        system_prompt += "\nTone: Relaxed and conversational. Keep it simple and friendly.\n"
    elif speaking_style == "premium":
        system_prompt += "\nTone: Polished and refined. Use sophisticated vocabulary while staying clear.\n"

    # Add custom instruction if provided
    if custom_instruction:
        system_prompt += f"\nADDITIONAL INSTRUCTIONS:\n{custom_instruction}\n"

    # Add properties context
    if properties_context:
        system_prompt += f"\nAVAILABLE PROPERTIES:\n{properties_context}\n"
    else:
        system_prompt += "\nNo properties currently available in the database.\n"

    return system_prompt


def get_conversation_history(conversation_id: str, limit: int = 10) -> List[Dict]:
    """
    Get recent conversation history

    Args:
        conversation_id: UUID of conversation
        limit: Number of recent messages to retrieve

    Returns:
        List of message dicts with role and content
    """
    db = get_db()

    query = """
        SELECT sender_type, message_text, timestamp
        FROM messages
        WHERE conversation_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
    """

    messages = db.execute(query, (conversation_id, limit))

    # Reverse to chronological order
    messages = list(reversed(messages))

    # Convert to Claude format
    formatted = []
    for msg in messages:
        role = "user" if msg['sender_type'] == 'USER' else "assistant"
        formatted.append({
            "role": role,
            "content": msg['message_text']
        })

    return formatted


def detect_property_intent(message: str) -> Dict:
    """
    Simple property intent detection
    Returns search parameters extracted from message

    In production, this could use NLP or another LLM call
    For MVP, using simple keyword matching
    """
    message_lower = message.lower()

    intent = {
        "location": None,
        "property_type": None,
        "min_price": None,
        "max_price": None,
        "bedrooms": None
    }

    # Location detection (basic)
    locations = ["marina bay", "orchard", "sentosa", "downtown", "bukit timah", "clementi"]
    for loc in locations:
        if loc in message_lower:
            intent["location"] = loc.title()
            break

    # Property type
    if "condo" in message_lower:
        intent["property_type"] = "condo"
    elif "hdb" in message_lower:
        intent["property_type"] = "HDB"
    elif "landed" in message_lower:
        intent["property_type"] = "landed"

    # Bedrooms
    for i in range(1, 6):
        if f"{i} bed" in message_lower or f"{i}br" in message_lower:
            intent["bedrooms"] = i
            break

    return intent


def generate_ai_response(conversation_id: str, user_message: str) -> str:
    """
    Generate AI response for user message

    Args:
        conversation_id: UUID of conversation
        user_message: User's message text

    Returns:
        AI response text

    Process:
        1. Load conversation and agent details
        2. Load agent persona
        3. Detect property intent and search if needed
        4. Build system prompt with context
        5. Generate response via Claude
        6. Return response
    """
    db = get_db()
    client = Anthropic(api_key=get_anthropic_api_key())

    try:
        # Get conversation and agent
        query = """
            SELECT c.conversation_id, c.agent_id, c.contact_number,
                   a.assistant_name
            FROM conversations c
            JOIN agents a ON c.agent_id = a.agent_id
            WHERE c.conversation_id = %s
        """

        conversation = db.execute_one(query, (conversation_id,))

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        agent_id = conversation['agent_id']

        # Load persona
        persona = load_agent_persona(agent_id)

        # Detect property intent and search
        intent = detect_property_intent(user_message)
        properties_context = None

        if any(intent.values()):
            # User is asking about properties
            logger.info(f"Property intent detected: {intent}")

            properties = search_properties(
                agent_id=agent_id,
                location=intent.get("location"),
                property_type=intent.get("property_type"),
                bedrooms=intent.get("bedrooms"),
                limit=3
            )

            if properties:
                properties_context = format_property_response(properties, format_type="list")

        # Build system prompt
        system_prompt = build_system_prompt(persona, properties_context)

        # Get conversation history
        history = get_conversation_history(conversation_id, limit=10)

        # Add current user message
        history.append({
            "role": "user",
            "content": user_message
        })

        # Generate response
        logger.info(f"Generating AI response for conversation {conversation_id}")

        # MOCK MODE: Use mock response if API fails
        use_mock = settings.environment == "development"

        try:
            response = client.messages.create(
                model=settings.ai_model,
                max_tokens=settings.ai_max_tokens,
                temperature=settings.ai_temperature,
                system=system_prompt,
                messages=history
            )
            ai_response = response.content[0].text
        except Exception as api_error:
            if use_mock:
                logger.warning(f"Claude API failed, using mock response: {api_error}")
                # Generate intelligent mock response
                if properties_context:
                    ai_response = f"Thank you for your interest! I found a great property for you:\n\n{properties_context}\n\nThis property matches what you're looking for. Would you like to schedule a viewing? I'm available to show it anytime this week!"
                else:
                    ai_response = "Thank you for reaching out! I'd be happy to help you find the perfect property. Could you tell me a bit more about what you're looking for? For example, preferred location, number of bedrooms, and your budget range?"
            else:
                raise

        logger.info(f"AI response generated: {ai_response[:100]}...")

        return ai_response

    except Exception as e:
        logger.error(f"Failed to generate AI response: {e}")
        raise


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) < 3:
        print("Usage: python generate_ai_response.py <conversation_id> <message>")
        sys.exit(1)

    conversation_id = sys.argv[1]
    message = " ".join(sys.argv[2:])

    response = generate_ai_response(conversation_id, message)
    print(f"AI Response:\n{response}")
