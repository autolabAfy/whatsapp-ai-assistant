"""
Push Notifications for Mobile App
Sends notifications when new messages arrive
"""
from typing import Optional, List
from loguru import logger
import httpx
from execution.database import get_db


# Firebase Cloud Messaging (FCM) - for production
FCM_SERVER_KEY = None  # Set via environment variable
FCM_URL = "https://fcm.googleapis.com/fcm/send"


def register_device_token(agent_id: str, device_token: str, platform: str = "ios"):
    """
    Register device token for push notifications

    Args:
        agent_id: Agent's UUID
        device_token: FCM/APNs token from mobile app
        platform: "ios" or "android"
    """
    try:
        db = get_db()

        # Store device token
        db.execute("""
            INSERT INTO device_tokens (agent_id, token, platform, last_updated)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (agent_id, token)
            DO UPDATE SET last_updated = NOW(), is_active = TRUE
        """, (agent_id, device_token, platform))

        logger.info(f"Registered device token for agent {agent_id}")

    except Exception as e:
        logger.error(f"Failed to register device token: {e}")
        raise


def unregister_device_token(device_token: str):
    """
    Unregister device token (on logout)
    """
    try:
        db = get_db()

        db.execute("""
            UPDATE device_tokens
            SET is_active = FALSE
            WHERE token = %s
        """, (device_token,))

        logger.info(f"Unregistered device token")

    except Exception as e:
        logger.error(f"Failed to unregister device token: {e}")


async def send_push_notification(
    agent_id: str,
    title: str,
    body: str,
    data: Optional[dict] = None
):
    """
    Send push notification to agent's devices

    Args:
        agent_id: Agent's UUID
        title: Notification title
        body: Notification body
        data: Additional data payload
    """
    try:
        db = get_db()

        # Get agent's device tokens
        tokens = db.execute("""
            SELECT token, platform
            FROM device_tokens
            WHERE agent_id = %s AND is_active = TRUE
        """, (agent_id,))

        if not tokens:
            logger.info(f"No device tokens for agent {agent_id}")
            return

        # Send to each device
        for token_info in tokens:
            await _send_fcm_notification(
                token=token_info['token'],
                title=title,
                body=body,
                data=data or {}
            )

    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")


async def _send_fcm_notification(
    token: str,
    title: str,
    body: str,
    data: dict
):
    """
    Send notification via Firebase Cloud Messaging
    """
    if not FCM_SERVER_KEY:
        logger.warning("FCM_SERVER_KEY not configured, skipping push notification")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                FCM_URL,
                headers={
                    "Authorization": f"key={FCM_SERVER_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "to": token,
                    "notification": {
                        "title": title,
                        "body": body,
                        "sound": "default",
                        "badge": 1
                    },
                    "data": data,
                    "priority": "high"
                }
            )

            if response.status_code == 200:
                logger.info(f"Push notification sent successfully")
            else:
                logger.error(f"Push notification failed: {response.text}")

    except Exception as e:
        logger.error(f"FCM request failed: {e}")


def notify_new_message(
    agent_id: str,
    contact_name: str,
    message_preview: str,
    conversation_id: str
):
    """
    Notify agent of new message

    Args:
        agent_id: Agent's UUID
        contact_name: Name of lead who sent message
        message_preview: First 100 chars of message
        conversation_id: Conversation UUID
    """
    import asyncio

    title = f"New message from {contact_name}"
    body = message_preview[:100]
    data = {
        "type": "new_message",
        "conversation_id": conversation_id,
        "screen": "chat"
    }

    # Run async function
    asyncio.create_task(
        send_push_notification(agent_id, title, body, data)
    )


# Migration to create device_tokens table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS device_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('ios', 'android')),
    is_active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id, token)
);

CREATE INDEX IF NOT EXISTS idx_device_tokens_agent ON device_tokens(agent_id);
CREATE INDEX IF NOT EXISTS idx_device_tokens_active ON device_tokens(is_active) WHERE is_active = TRUE;
"""


if __name__ == "__main__":
    print("Push Notifications Module")
    print("To use:")
    print("1. Set FCM_SERVER_KEY environment variable")
    print("2. Register device tokens from mobile app")
    print("3. Notifications sent automatically on new messages")
