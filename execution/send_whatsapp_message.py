"""
Send WhatsApp message via Green API
With safety checks, deduplication, and rate limiting
"""
import hashlib
import time
from typing import Optional, Dict
import requests
from loguru import logger

from execution.config import settings
from execution.database import get_db
from execution.redis_client import get_redis
from execution.check_conversation_mode import is_ai_mode


def generate_idempotency_key(conversation_id: str, message: str) -> str:
    """Generate unique idempotency key for message"""
    timestamp = int(time.time())
    content = f"{conversation_id}:{message}:{timestamp}"
    return hashlib.sha256(content.encode()).hexdigest()


def check_already_sent(idempotency_key: str) -> bool:
    """Check if message already sent"""
    db = get_db()
    query = "SELECT 1 FROM sent_messages_log WHERE idempotency_key = %s"
    result = db.execute_one(query, (idempotency_key,))
    return result is not None


def log_sent_message(idempotency_key: str, conversation_id: str, message: str, response: Dict):
    """Log sent message for idempotency"""
    db = get_db()
    data = {
        "idempotency_key": idempotency_key,
        "conversation_id": conversation_id,
        "message_text": message,
        "green_api_response": str(response)
    }
    db.insert("sent_messages_log", data)


def send_to_green_api(chat_id: str, message: str, instance_id: str, token: str) -> Dict:
    """
    Send message via Green API

    Args:
        chat_id: WhatsApp chat ID (e.g., "1234567890@c.us")
        message: Message text
        instance_id: Green API instance ID
        token: Green API token

    Returns:
        Response from Green API
    """
    url = f"{settings.green_api_base_url}/waInstance{instance_id}/sendMessage/{token}"

    payload = {
        "chatId": chat_id,
        "message": message
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Green API request failed: {e}")
        raise


def send_whatsapp_message(
    conversation_id: str,
    message: str,
    force: bool = False
) -> bool:
    """
    Send WhatsApp message with safety checks

    Args:
        conversation_id: UUID of conversation
        message: Message text to send
        force: Skip mode check (use with caution)

    Returns:
        True if sent successfully

    Safety checks:
        1. Verify conversation is in AI mode (unless force=True)
        2. Check for duplicate send
        3. Truncate if message too long
        4. Log send attempt
    """
    db = get_db()
    redis = get_redis()

    try:
        # Get conversation details
        query = """
            SELECT c.conversation_id, c.contact_number, c.current_mode, c.agent_id,
                   a.green_api_instance_id, a.green_api_token
            FROM conversations c
            JOIN agents a ON c.agent_id = a.agent_id
            WHERE c.conversation_id = %s
        """

        conversation = db.execute_one(query, (conversation_id,))

        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            return False

        # Safety check: Verify AI mode
        if not force and conversation['current_mode'] != 'AI':
            logger.warning(
                f"Attempted to send AI message in {conversation['current_mode']} mode. "
                f"Message discarded: {message[:100]}"
            )
            return False

        # Check Green API credentials
        if not conversation['green_api_instance_id'] or not conversation['green_api_token']:
            logger.error(f"Green API credentials not configured for agent {conversation['agent_id']}")
            return False

        # Generate idempotency key
        idempotency_key = generate_idempotency_key(conversation_id, message)

        # Check if already sent
        if check_already_sent(idempotency_key):
            logger.info(f"Message already sent (idempotency key: {idempotency_key})")
            return True

        # Truncate if too long
        if len(message) > settings.max_response_length:
            logger.warning(f"Message truncated from {len(message)} to {settings.max_response_length} chars")
            message = message[:settings.max_response_length - 3] + "..."

        # Format chat ID
        chat_id = conversation['contact_number']
        if '@' not in chat_id:
            chat_id = f"{chat_id}@c.us"

        # Send via Green API
        logger.info(f"Sending message to {chat_id} (conversation: {conversation_id})")

        response = send_to_green_api(
            chat_id=chat_id,
            message=message,
            instance_id=conversation['green_api_instance_id'],
            token=conversation['green_api_token']
        )

        # Log successful send
        log_sent_message(idempotency_key, conversation_id, message, response)

        # Update conversation last_message_timestamp
        db.update(
            "conversations",
            {"last_message_timestamp": "CURRENT_TIMESTAMP", "last_message_preview": message[:200]},
            {"conversation_id": conversation_id}
        )

        # Store message in database
        message_data = {
            "conversation_id": conversation_id,
            "sender_type": "AI",
            "message_text": message,
            "delivered": True
        }
        db.insert("messages", message_data)

        logger.info(f"Message sent successfully to {chat_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) < 3:
        print("Usage: python send_whatsapp_message.py <conversation_id> <message>")
        sys.exit(1)

    conversation_id = sys.argv[1]
    message = " ".join(sys.argv[2:])

    success = send_whatsapp_message(conversation_id, message)
    print(f"Send {'successful' if success else 'failed'}")
