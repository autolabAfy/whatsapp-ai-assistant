"""
Identify or create conversation from webhook
"""
from typing import Dict, Optional
from loguru import logger
from execution.database import get_db


def identify_conversation(agent_id: str, contact_number: str, contact_name: Optional[str] = None) -> Dict:
    """
    Identify existing conversation or create new one

    Args:
        agent_id: UUID of agent
        contact_number: WhatsApp number of contact
        contact_name: Name of contact (optional)

    Returns:
        Conversation dict with conversation_id and current_mode
    """
    db = get_db()

    # Try to find existing conversation
    query = """
        SELECT conversation_id, current_mode, contact_name
        FROM conversations
        WHERE agent_id = %s AND contact_number = %s
    """

    conversation = db.execute_one(query, (agent_id, contact_number))

    if conversation:
        logger.debug(f"Found existing conversation {conversation['conversation_id']}")

        # Update contact_name if provided and different
        if contact_name and contact_name != conversation.get('contact_name'):
            db.update(
                "conversations",
                {"contact_name": contact_name},
                {"conversation_id": conversation['conversation_id']}
            )

        return conversation

    # Create new conversation (default to AI mode)
    logger.info(f"Creating new conversation for agent {agent_id} and contact {contact_number}")

    data = {
        "agent_id": agent_id,
        "contact_number": contact_number,
        "contact_name": contact_name,
        "current_mode": "AI",
        "unread_count": 0
    }

    conversation = db.insert("conversations", data)

    return conversation


def get_agent_by_whatsapp_instance(instance_id: str) -> Optional[Dict]:
    """
    Get agent by Green API instance ID

    Args:
        instance_id: Green API instance ID

    Returns:
        Agent dict or None
    """
    db = get_db()

    query = """
        SELECT agent_id, email, full_name, green_api_instance_id
        FROM agents
        WHERE green_api_instance_id = %s::TEXT
          AND is_active = TRUE
    """

    return db.execute_one(query, (str(instance_id),))


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) < 3:
        print("Usage: python identify_conversation.py <agent_id> <contact_number> [contact_name]")
        sys.exit(1)

    agent_id = sys.argv[1]
    contact_number = sys.argv[2]
    contact_name = sys.argv[3] if len(sys.argv) > 3 else None

    conversation = identify_conversation(agent_id, contact_number, contact_name)
    print(f"Conversation: {conversation['conversation_id']} (Mode: {conversation['current_mode']})")
