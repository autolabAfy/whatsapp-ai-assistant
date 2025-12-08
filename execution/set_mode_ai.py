"""
Switch conversation to AI mode
Resumes AI handling of conversation
"""
from typing import Optional
from loguru import logger
from execution.database import get_db


def set_mode_ai(conversation_id: str, agent_id: Optional[str] = None, reason: str = "manual_toggle") -> bool:
    """
    Switch conversation to AI mode

    Args:
        conversation_id: UUID of conversation
        agent_id: UUID of agent making the change (optional)
        reason: Reason for mode change (for logging)

    Returns:
        True if successful

    Side effects:
        - Updates conversation.current_mode to AI
        - Logs mode change
        - AI will resume handling messages
    """
    db = get_db()

    try:
        update_query = """
            UPDATE conversations
            SET current_mode = 'AI',
                last_mode_change_timestamp = CURRENT_TIMESTAMP,
                last_mode_changed_by = %s
            WHERE conversation_id = %s
            RETURNING conversation_id, contact_number
        """

        result = db.execute_one(update_query, (agent_id, conversation_id))

        if not result:
            logger.error(f"Conversation {conversation_id} not found")
            return False

        logger.info(f"Conversation {conversation_id} switched to AI mode (reason: {reason})")
        return True

    except Exception as e:
        logger.error(f"Failed to set AI mode for {conversation_id}: {e}")
        raise


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) < 2:
        print("Usage: python set_mode_ai.py <conversation_id> [agent_id]")
        sys.exit(1)

    conversation_id = sys.argv[1]
    agent_id = sys.argv[2] if len(sys.argv) > 2 else None

    success = set_mode_ai(conversation_id, agent_id, reason="cli_test")
    print(f"Mode change {'successful' if success else 'failed'}")
