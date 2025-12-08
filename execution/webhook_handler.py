"""
Process incoming WhatsApp webhooks from Green API
Implements message routing and deduplication
"""
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional
from loguru import logger

from execution.database import get_db
from execution.redis_client import get_redis
from execution.config import settings
from execution.identify_conversation import identify_conversation, get_agent_by_whatsapp_instance
from execution.check_conversation_mode import check_conversation_mode
from execution.ai_router import generate_ai_response_auto as generate_ai_response
from execution.send_whatsapp_message import send_whatsapp_message


def generate_webhook_fingerprint(webhook_data: Dict) -> str:
    """Generate unique fingerprint for webhook deduplication"""
    # Use chatId, timestamp, and message content
    content = f"{webhook_data.get('senderData', {}).get('chatId', '')}:{webhook_data.get('timestamp', '')}:{webhook_data.get('messageData', {}).get('textMessageData', {}).get('textMessage', '')}"
    return hashlib.sha256(content.encode()).hexdigest()


def is_duplicate_webhook(fingerprint: str) -> bool:
    """Check if webhook already processed"""
    redis = get_redis()
    key = f"webhook:{fingerprint}"

    if redis.exists(key):
        return True

    # Mark as processed (5 minute TTL)
    redis.set_with_ttl(key, "1", settings.webhook_dedup_ttl)
    return False


def log_webhook(webhook_data: Dict, fingerprint: str, is_duplicate: bool = False):
    """Log webhook for debugging"""
    db = get_db()

    data = {
        "webhook_fingerprint": fingerprint,
        "payload": json.dumps(webhook_data),
        "processed": not is_duplicate,
        "is_duplicate": is_duplicate
    }

    db.insert("webhook_logs", data)


def extract_message_data(webhook_data: Dict) -> Optional[Dict]:
    """
    Extract relevant message data from Green API webhook

    Green API webhook structure:
    {
        "typeWebhook": "incomingMessageReceived",
        "instanceData": {"idInstance": "1234"},
        "timestamp": 1234567890,
        "idMessage": "msg_123",
        "senderData": {
            "chatId": "1234567890@c.us",
            "sender": "1234567890@c.us",
            "senderName": "John Doe"
        },
        "messageData": {
            "typeMessage": "textMessage",
            "textMessageData": {
                "textMessage": "Hello"
            }
        }
    }
    """
    try:
        # Only process incoming text messages
        if webhook_data.get("typeWebhook") != "incomingMessageReceived":
            return None

        message_type = webhook_data.get("messageData", {}).get("typeMessage")
        if message_type != "textMessage":
            logger.info(f"Skipping non-text message type: {message_type}")
            return None

        instance_id = webhook_data.get("instanceData", {}).get("idInstance")
        chat_id = webhook_data.get("senderData", {}).get("chatId", "")
        sender_name = webhook_data.get("senderData", {}).get("senderName", "")
        message_text = webhook_data.get("messageData", {}).get("textMessageData", {}).get("textMessage", "")
        message_id = webhook_data.get("idMessage")
        timestamp = webhook_data.get("timestamp")

        # Extract phone number from chatId (remove @c.us)
        contact_number = chat_id.replace("@c.us", "").replace("@g.us", "")

        return {
            "instance_id": instance_id,
            "contact_number": contact_number,
            "contact_name": sender_name,
            "message_text": message_text,
            "message_id": message_id,
            "timestamp": timestamp
        }

    except Exception as e:
        logger.error(f"Failed to extract message data: {e}")
        return None


def store_incoming_message(conversation_id: str, message_text: str, message_id: Optional[str] = None):
    """Store incoming user message in database"""
    db = get_db()

    data = {
        "conversation_id": conversation_id,
        "sender_type": "USER",
        "message_text": message_text,
        "whatsapp_message_id": message_id,
        "message_fingerprint": hashlib.sha256(f"{conversation_id}:{message_text}".encode()).hexdigest()
    }

    db.insert("messages", data)

    # Update conversation
    db.update(
        "conversations",
        {
            "last_message_timestamp": datetime.now(),
            "last_message_preview": message_text[:200]
        },
        {"conversation_id": conversation_id}
    )

    # Increment unread count separately (SQL expression)
    db.execute(
        "UPDATE conversations SET unread_count = unread_count + 1 WHERE conversation_id = %s",
        (conversation_id,)
    )


def process_webhook(webhook_data: Dict) -> Dict:
    """
    Main webhook processing function

    Args:
        webhook_data: Webhook payload from Green API

    Returns:
        Processing result dict

    Process:
        1. Deduplicate webhook
        2. Extract message data
        3. Identify/create conversation
        4. Store incoming message
        5. Check mode
        6. If AI mode: generate and send response
        7. If HUMAN mode: queue in inbox only
    """
    redis = get_redis()

    # Generate fingerprint
    fingerprint = generate_webhook_fingerprint(webhook_data)

    # Check for duplicate
    if is_duplicate_webhook(fingerprint):
        logger.info(f"Duplicate webhook ignored: {fingerprint}")
        log_webhook(webhook_data, fingerprint, is_duplicate=True)
        return {"status": "duplicate", "fingerprint": fingerprint}

    # Log webhook
    log_webhook(webhook_data, fingerprint)

    # Extract message data
    message_data = extract_message_data(webhook_data)

    if not message_data:
        logger.info("Webhook does not contain processable message")
        return {"status": "skipped", "reason": "not_text_message"}

    logger.info(f"Processing message from {message_data['contact_number']}: {message_data['message_text'][:50]}")

    # Get agent by instance ID
    agent = get_agent_by_whatsapp_instance(message_data['instance_id'])

    if not agent:
        logger.error(f"No agent found for instance {message_data['instance_id']}")
        return {"status": "error", "reason": "agent_not_found"}

    # Identify or create conversation
    conversation = identify_conversation(
        agent_id=agent['agent_id'],
        contact_number=message_data['contact_number'],
        contact_name=message_data['contact_name']
    )

    conversation_id = conversation['conversation_id']

    # Store incoming message
    store_incoming_message(
        conversation_id=conversation_id,
        message_text=message_data['message_text'],
        message_id=message_data['message_id']
    )

    # Use conversation lock to prevent race conditions
    with redis.lock(f"conversation:{conversation_id}"):

        # Check mode
        current_mode = check_conversation_mode(conversation_id)

        if current_mode == "AI":
            logger.info(f"Conversation {conversation_id} in AI mode - generating response")

            try:
                # Generate AI response
                ai_response = generate_ai_response(
                    conversation_id=conversation_id,
                    user_message=message_data['message_text']
                )

                # Save AI response to database FIRST (before sending to WhatsApp)
                db = get_db()
                db.insert("messages", {
                    "conversation_id": conversation_id,
                    "sender_type": "AI",
                    "message_text": ai_response
                })
                logger.info(f"AI response saved to database: {ai_response[:100]}...")

                # Try to send response via WhatsApp (may fail, but DB is already saved)
                try:
                    success = send_whatsapp_message(
                        conversation_id=conversation_id,
                        message=ai_response
                    )
                    send_status = "sent" if success else "failed"
                except Exception as send_error:
                    logger.warning(f"WhatsApp send failed (response saved in DB): {send_error}")
                    send_status = "saved_only"

                return {
                    "status": "ai_responded",
                    "conversation_id": conversation_id,
                    "response_sent": send_status,
                    "response_preview": ai_response[:100]
                }

            except Exception as e:
                logger.error(f"AI response generation failed: {e}")
                return {
                    "status": "error",
                    "conversation_id": conversation_id,
                    "error": str(e)
                }

        elif current_mode == "HUMAN":
            logger.info(f"Conversation {conversation_id} in HUMAN mode - queued for agent")

            return {
                "status": "queued_for_human",
                "conversation_id": conversation_id
            }

    return {"status": "unknown"}


if __name__ == "__main__":
    # Test with sample webhook
    sample_webhook = {
        "typeWebhook": "incomingMessageReceived",
        "instanceData": {"idInstance": "test123"},
        "timestamp": 1234567890,
        "idMessage": "msg_test",
        "senderData": {
            "chatId": "1234567890@c.us",
            "sender": "1234567890@c.us",
            "senderName": "Test User"
        },
        "messageData": {
            "typeMessage": "textMessage",
            "textMessageData": {
                "textMessage": "Show me properties in Orchard"
            }
        }
    }

    result = process_webhook(sample_webhook)
    print(f"Result: {result}")
