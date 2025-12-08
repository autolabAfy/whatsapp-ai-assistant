"""
Check conversation mode (AI or HUMAN)
Atomic mode verification to prevent race conditions
"""
from typing import Optional
from loguru import logger
from execution.database import get_db


def check_conversation_mode(conversation_id: str) -> str:
    """
    Check current mode for a conversation

    Args:
        conversation_id: UUID of conversation

    Returns:
        'AI' or 'HUMAN'

    Raises:
        ValueError: If conversation not found
    """
    db = get_db()

    query = """
        SELECT current_mode
        FROM conversations
        WHERE conversation_id = %s
    """

    result = db.execute_one(query, (conversation_id,))

    if not result:
        raise ValueError(f"Conversation {conversation_id} not found")

    mode = result['current_mode']
    logger.debug(f"Conversation {conversation_id} mode: {mode}")

    return mode


def is_ai_mode(conversation_id: str) -> bool:
    """
    Check if conversation is in AI mode

    Args:
        conversation_id: UUID of conversation

    Returns:
        True if AI mode, False if HUMAN mode
    """
    try:
        mode = check_conversation_mode(conversation_id)
        return mode == 'AI'
    except ValueError:
        logger.error(f"Conversation {conversation_id} not found")
        return False


def is_human_mode(conversation_id: str) -> bool:
    """
    Check if conversation is in HUMAN mode

    Args:
        conversation_id: UUID of conversation

    Returns:
        True if HUMAN mode, False if AI mode
    """
    return not is_ai_mode(conversation_id)


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) < 2:
        print("Usage: python check_conversation_mode.py <conversation_id>")
        sys.exit(1)

    conversation_id = sys.argv[1]
    mode = check_conversation_mode(conversation_id)
    print(f"Conversation {conversation_id} is in {mode} mode")
