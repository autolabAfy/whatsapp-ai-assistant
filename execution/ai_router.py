"""
AI Router - Selects which AI provider to use based on configuration
Supports: Anthropic Claude, Google Gemini, and Mock responses
"""
from loguru import logger
from execution.config import settings


def generate_ai_response_auto(conversation_id: str, user_message: str) -> str:
    """
    Route to appropriate AI provider based on settings

    Args:
        conversation_id: UUID of conversation
        user_message: User's message text

    Returns:
        AI response text
    """
    provider = settings.ai_provider.lower()

    logger.info(f"Using AI provider: {provider}")

    if provider == "gemini":
        from execution.generate_ai_response_gemini import generate_ai_response_gemini
        return generate_ai_response_gemini(conversation_id, user_message)

    elif provider == "anthropic" or provider == "claude":
        from execution.generate_ai_response import generate_ai_response
        return generate_ai_response(conversation_id, user_message)

    elif provider == "mock":
        # Use mock response
        from execution.generate_ai_response import (
            detect_property_intent,
            load_agent_persona,
            search_properties,
            format_property_response,
            get_db
        )

        db = get_db()
        query = "SELECT agent_id FROM conversations WHERE conversation_id = %s"
        result = db.execute_one(query, (conversation_id,))
        agent_id = result['agent_id'] if result else None

        # Detect intent and search
        intent = detect_property_intent(user_message)
        properties_context = None

        if any(intent.values()) and agent_id:
            properties = search_properties(
                agent_id=agent_id,
                location=intent.get("location"),
                property_type=intent.get("property_type"),
                bedrooms=intent.get("bedrooms"),
                limit=3
            )
            if properties:
                properties_context = format_property_response(properties, format_type="list")

        # Generate mock response
        if properties_context:
            return f"Thank you for your interest! I found a great property for you:\n\n{properties_context}\n\nThis property matches what you're looking for. Would you like to schedule a viewing? I'm available to show it anytime this week!"
        else:
            return "Thank you for reaching out! I'd be happy to help you find the perfect property. Could you tell me a bit more about what you're looking for? For example, preferred location, number of bedrooms, and your budget range?"

    else:
        raise ValueError(f"Unknown AI provider: {provider}. Options: gemini, anthropic, mock")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python ai_router.py <conversation_id> <message>")
        sys.exit(1)

    conversation_id = sys.argv[1]
    message = " ".join(sys.argv[2:])

    response = generate_ai_response_auto(conversation_id, message)
    print(f"AI Response ({settings.ai_provider}):\n{response}")
