"""
Cancel pending follow-ups for a conversation
"""
from loguru import logger
from execution.database import get_db


def cancel_conversation_followups(conversation_id: str) -> int:
    """
    Cancel all pending follow-ups for a conversation

    Args:
        conversation_id: UUID of conversation

    Returns:
        Number of follow-ups cancelled
    """
    db = get_db()

    try:
        query = """
            UPDATE followups
            SET status = 'cancelled',
                cancelled_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s
              AND status = 'pending'
            RETURNING followup_id
        """

        results = db.execute(query, (conversation_id,))
        count = len(results)

        if count > 0:
            logger.info(f"Cancelled {count} follow-ups for conversation {conversation_id}")
        else:
            logger.debug(f"No pending follow-ups to cancel for conversation {conversation_id}")

        return count

    except Exception as e:
        logger.error(f"Failed to cancel follow-ups for {conversation_id}: {e}")
        raise


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) < 2:
        print("Usage: python cancel_followups.py <conversation_id>")
        sys.exit(1)

    conversation_id = sys.argv[1]
    count = cancel_conversation_followups(conversation_id)
    print(f"Cancelled {count} follow-up(s)")
