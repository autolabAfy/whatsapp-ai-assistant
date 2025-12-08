"""
Generate AI response using Google Gemini
Applies agent persona and property context
"""
from typing import List, Dict, Optional
from loguru import logger
import google.generativeai as genai

from execution.config import settings
from execution.database import get_db
from execution.property_lookup import search_properties, format_property_response


# Import shared functions from Claude version
from execution.generate_ai_response import (
    load_agent_persona,
    build_system_prompt,
    get_conversation_history,
    detect_property_intent
)


def get_gemini_api_key() -> str:
    """Get Gemini API key from settings"""
    api_key = getattr(settings, 'gemini_api_key', None)
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")
    return api_key


def configure_gemini():
    """Configure Gemini with API key"""
    genai.configure(api_key=get_gemini_api_key())


def convert_history_to_gemini_format(history: List[Dict]) -> List[Dict]:
    """
    Convert conversation history to Gemini format

    Gemini uses 'user' and 'model' roles (not 'assistant')
    """
    gemini_history = []
    for msg in history:
        role = "user" if msg['role'] == "user" else "model"
        gemini_history.append({
            "role": role,
            "parts": [msg['content']]
        })
    return gemini_history


def generate_ai_response_gemini(conversation_id: str, user_message: str) -> str:
    """
    Generate AI response using Gemini

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
        5. Generate response via Gemini
        6. Return response
    """
    db = get_db()

    try:
        # Configure Gemini
        configure_gemini()

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

        # Convert to Gemini format
        gemini_history = convert_history_to_gemini_format(history)

        # Generate response
        logger.info(f"Generating Gemini AI response for conversation {conversation_id}")

        # MOCK MODE: Use mock response if API fails
        use_mock = settings.environment == "development"

        try:
            # Initialize Gemini model
            model = genai.GenerativeModel(
                model_name=getattr(settings, 'gemini_model', 'gemini-1.5-flash'),
                generation_config={
                    "temperature": settings.ai_temperature,
                    "max_output_tokens": settings.ai_max_tokens,
                }
            )

            # Start chat with history
            chat = model.start_chat(history=gemini_history)

            # Send message with system prompt prepended
            full_prompt = f"{system_prompt}\n\nUser message: {user_message}"
            response = chat.send_message(full_prompt)

            ai_response = response.text

        except Exception as api_error:
            if use_mock:
                logger.warning(f"Gemini API failed, using mock response: {api_error}")
                # Generate intelligent mock response
                if properties_context:
                    ai_response = f"Thank you for your interest! I found a great property for you:\n\n{properties_context}\n\nThis property matches what you're looking for. Would you like to schedule a viewing? I'm available to show it anytime this week!"
                else:
                    ai_response = "Thank you for reaching out! I'd be happy to help you find the perfect property. Could you tell me a bit more about what you're looking for? For example, preferred location, number of bedrooms, and your budget range?"
            else:
                raise

        logger.info(f"Gemini AI response generated: {ai_response[:100]}...")

        return ai_response

    except Exception as e:
        logger.error(f"Failed to generate Gemini AI response: {e}")
        raise


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) < 3:
        print("Usage: python generate_ai_response_gemini.py <conversation_id> <message>")
        sys.exit(1)

    conversation_id = sys.argv[1]
    message = " ".join(sys.argv[2:])

    response = generate_ai_response_gemini(conversation_id, message)
    print(f"Gemini AI Response:\n{response}")
