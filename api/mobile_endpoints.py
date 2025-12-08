"""
Mobile App API Endpoints
Designed for RealtorAI Connect mobile app integration
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from execution.database import get_db
from execution.ai_router import generate_ai_response_auto
from execution.property_lookup import search_properties

router = APIRouter(prefix="/api/mobile", tags=["Mobile App"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SendMessageRequest(BaseModel):
    """Request to send a message and get AI response"""
    user_id: str  # Phone number or unique ID
    user_name: str  # Lead's name
    message: str  # User's message
    agent_id: str = "3b5ab91d-ddfb-48cb-a110-acb5144a89fa"  # Default agent


class SendMessageResponse(BaseModel):
    """Response with AI reply"""
    conversation_id: str
    user_message: str
    ai_response: str
    properties: Optional[List[dict]] = None
    timestamp: str
    lead_type: Optional[str] = None  # "Buyer", "Investor", "Renter"


class ConversationSummary(BaseModel):
    """Summary of a conversation for mobile list view"""
    conversation_id: str
    contact_name: str
    contact_number: str
    last_message: str
    last_message_time: str
    unread_count: int
    lead_type: Optional[str] = None
    status: str  # "active", "archived"


class MessageHistory(BaseModel):
    """Individual message in conversation"""
    message_id: str
    sender_type: str  # "USER" or "AI"
    message_text: str
    timestamp: str


class PropertyRecommendation(BaseModel):
    """Property recommendation for mobile display"""
    property_id: str
    title: str
    location: str
    property_type: str
    price: int
    bedrooms: int
    bathrooms: int
    size_sqft: Optional[int]
    description: Optional[str]
    image_url: Optional[str]


class AppointmentCreate(BaseModel):
    """Create new appointment"""
    conversation_id: str
    appointment_type: str  # "Viewing", "Meeting", "Call"
    scheduled_time: str  # ISO format datetime
    location: Optional[str]
    notes: Optional[str]


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@router.post("/chat/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """
    Send message from mobile app, get AI response

    This is the main endpoint for chat functionality:
    1. Receives user message from mobile app
    2. Creates/finds conversation
    3. Saves user message
    4. Generates AI response (using Gemini)
    5. Saves AI response
    6. Returns response to mobile app
    """
    try:
        db = get_db()

        # Find or create conversation
        conversation_query = """
            SELECT conversation_id, current_mode
            FROM conversations
            WHERE agent_id = %s AND contact_number = %s
        """
        conversation = db.execute_one(
            conversation_query,
            (request.agent_id, request.user_id)
        )

        if not conversation:
            # Create new conversation
            conversation_id = db.insert("conversations", {
                "agent_id": request.agent_id,
                "contact_number": request.user_id,
                "contact_name": request.user_name,
                "current_mode": "AI",
                "source": "mobile_app"
            })
            current_mode = "AI"
        else:
            conversation_id = conversation['conversation_id']
            current_mode = conversation['current_mode']

        # Save user message
        db.insert("messages", {
            "conversation_id": conversation_id,
            "sender_type": "USER",
            "message_text": request.message
        })

        # Generate AI response (only if in AI mode)
        if current_mode == "AI":
            ai_response = generate_ai_response_auto(
                conversation_id=conversation_id,
                user_message=request.message
            )

            # Save AI response
            db.insert("messages", {
                "conversation_id": conversation_id,
                "sender_type": "AI",
                "message_text": ai_response
            })
        else:
            ai_response = None  # Human mode - agent will respond manually

        # Check for property recommendations
        properties = None
        if "bedroom" in request.message.lower() or "condo" in request.message.lower():
            # Simple property search
            from execution.generate_ai_response import detect_property_intent
            intent = detect_property_intent(request.message)

            if any(intent.values()):
                props = search_properties(
                    agent_id=request.agent_id,
                    location=intent.get("location"),
                    property_type=intent.get("property_type"),
                    bedrooms=intent.get("bedrooms"),
                    limit=3
                )
                properties = props if props else None

        # Update conversation metadata
        db.update("conversations", {
            "last_message_timestamp": datetime.now(),
            "last_message_preview": request.message[:200]
        }, {"conversation_id": conversation_id})

        return SendMessageResponse(
            conversation_id=conversation_id,
            user_message=request.message,
            ai_response=ai_response or "Message received. An agent will respond shortly.",
            properties=properties,
            timestamp=datetime.now().isoformat(),
            lead_type=None  # TODO: Detect from conversation
        )

    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(
    agent_id: str = "3b5ab91d-ddfb-48cb-a110-acb5144a89fa",
    limit: int = 50
):
    """
    Get all conversations for mobile app inbox

    Returns list of conversations with:
    - Contact name
    - Last message preview
    - Unread count
    - Timestamp
    """
    try:
        db = get_db()

        query = """
            SELECT
                conversation_id,
                contact_name,
                contact_number,
                last_message_preview,
                last_message_timestamp,
                unread_count
            FROM conversations
            WHERE agent_id = %s
              AND is_archived = FALSE
            ORDER BY last_message_timestamp DESC
            LIMIT %s
        """

        conversations = db.execute(query, (agent_id, limit))

        return [
            ConversationSummary(
                conversation_id=c['conversation_id'],
                contact_name=c['contact_name'] or "Unknown",
                contact_number=c['contact_number'],
                last_message=c['last_message_preview'] or "",
                last_message_time=c['last_message_timestamp'].isoformat() if c['last_message_timestamp'] else "",
                unread_count=c['unread_count'] or 0,
                lead_type=None,  # TODO: Extract from tags
                status="active"
            )
            for c in conversations
        ]

    except Exception as e:
        logger.error(f"Error in get_conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageHistory])
async def get_conversation_messages(conversation_id: str, limit: int = 100):
    """
    Get message history for a conversation

    Used when user taps on conversation in mobile app
    """
    try:
        db = get_db()

        query = """
            SELECT
                message_id,
                sender_type,
                message_text,
                timestamp
            FROM messages
            WHERE conversation_id = %s
            ORDER BY timestamp ASC
            LIMIT %s
        """

        messages = db.execute(query, (conversation_id, limit))

        return [
            MessageHistory(
                message_id=m['message_id'],
                sender_type=m['sender_type'],
                message_text=m['message_text'],
                timestamp=m['timestamp'].isoformat()
            )
            for m in messages
        ]

    except Exception as e:
        logger.error(f"Error in get_conversation_messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROPERTY ENDPOINTS
# ============================================================================

@router.get("/properties/search", response_model=List[PropertyRecommendation])
async def search_properties_mobile(
    location: Optional[str] = None,
    property_type: Optional[str] = None,
    bedrooms: Optional[int] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    agent_id: str = "3b5ab91d-ddfb-48cb-a110-acb5144a89fa",
    limit: int = 10
):
    """
    Search properties from mobile app

    Used for property browsing and recommendations
    """
    try:
        properties = search_properties(
            agent_id=agent_id,
            location=location,
            property_type=property_type,
            bedrooms=bedrooms,
            min_price=min_price,
            max_price=max_price,
            limit=limit
        )

        return [
            PropertyRecommendation(
                property_id=p['property_id'],
                title=p['title'],
                location=p['location'],
                property_type=p['property_type'],
                price=p['price'],
                bedrooms=p['bedrooms'],
                bathrooms=p['bathrooms'],
                size_sqft=p.get('size_sqft'),
                description=p.get('description'),
                image_url=None  # TODO: Add image support
            )
            for p in properties
        ]

    except Exception as e:
        logger.error(f"Error in search_properties_mobile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/properties/{property_id}", response_model=PropertyRecommendation)
async def get_property_details(property_id: str):
    """Get detailed property information"""
    try:
        db = get_db()

        query = """
            SELECT * FROM properties WHERE property_id = %s
        """

        property = db.execute_one(query, (property_id,))

        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

        return PropertyRecommendation(
            property_id=property['property_id'],
            title=property['title'],
            location=property['location'],
            property_type=property['property_type'],
            price=property['price'],
            bedrooms=property['bedrooms'],
            bathrooms=property['bathrooms'],
            size_sqft=property.get('size_sqft'),
            description=property.get('description'),
            image_url=None
        )

    except Exception as e:
        logger.error(f"Error in get_property_details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# APPOINTMENT ENDPOINTS
# ============================================================================

@router.post("/appointments/create")
async def create_appointment(request: AppointmentCreate):
    """
    Create new appointment from mobile app

    Called when user schedules viewing, meeting, or call
    """
    try:
        db = get_db()

        appointment_id = db.insert("appointments", {
            "conversation_id": request.conversation_id,
            "appointment_type": request.appointment_type,
            "scheduled_time": request.scheduled_time,
            "location": request.location,
            "notes": request.notes,
            "status": "scheduled"
        })

        return {
            "appointment_id": appointment_id,
            "status": "created",
            "scheduled_time": request.scheduled_time
        }

    except Exception as e:
        logger.error(f"Error in create_appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/appointments")
async def get_appointments(
    agent_id: str = "3b5ab91d-ddfb-48cb-a110-acb5144a89fa",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get appointments for calendar view

    Returns upcoming viewings, meetings, calls
    """
    try:
        db = get_db()

        # TODO: Join with conversations to filter by agent
        query = """
            SELECT
                a.appointment_id,
                a.appointment_type,
                a.scheduled_time,
                a.location,
                a.status,
                c.contact_name
            FROM appointments a
            JOIN conversations c ON a.conversation_id = c.conversation_id
            WHERE c.agent_id = %s
              AND a.status != 'cancelled'
            ORDER BY a.scheduled_time ASC
        """

        appointments = db.execute(query, (agent_id,))

        return [{
            "appointment_id": a['appointment_id'],
            "type": a['appointment_type'],
            "scheduled_time": a['scheduled_time'].isoformat(),
            "location": a['location'],
            "contact_name": a['contact_name'],
            "status": a['status']
        } for a in appointments]

    except Exception as e:
        logger.error(f"Error in get_appointments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AGENT SETTINGS ENDPOINTS
# ============================================================================

@router.get("/agent/settings")
async def get_agent_settings(agent_id: str = "3b5ab91d-ddfb-48cb-a110-acb5144a89fa"):
    """
    Get AI agent configuration for mobile app

    Returns tone, response delay, custom instructions
    """
    try:
        db = get_db()

        query = """
            SELECT
                assistant_name,
                speaking_style,
                tone_slider,
                custom_instruction
            FROM agents
            WHERE agent_id = %s
        """

        agent = db.execute_one(query, (agent_id,))

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return {
            "assistant_name": agent['assistant_name'],
            "tone": agent['speaking_style'],  # "professional", "friendly", "casual"
            "response_delay": 30,  # Default 30 seconds
            "custom_instruction": agent['custom_instruction']
        }

    except Exception as e:
        logger.error(f"Error in get_agent_settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agent/settings")
async def update_agent_settings(
    agent_id: str,
    tone: Optional[str] = None,
    response_delay: Optional[int] = None,
    custom_instruction: Optional[str] = None
):
    """
    Update AI agent settings from mobile app

    Allows agent to customize AI behavior on-the-go
    """
    try:
        db = get_db()

        updates = {}
        if tone:
            updates['speaking_style'] = tone
        if custom_instruction is not None:
            updates['custom_instruction'] = custom_instruction

        if updates:
            db.update("agents", updates, {"agent_id": agent_id})

        return {"status": "updated", "agent_id": agent_id}

    except Exception as e:
        logger.error(f"Error in update_agent_settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# USAGE/ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/usage/stats")
async def get_usage_stats(agent_id: str = "3b5ab91d-ddfb-48cb-a110-acb5144a89fa"):
    """
    Get usage statistics for mobile dashboard

    Returns token usage, costs, conversation counts
    """
    try:
        db = get_db()

        # Count conversations
        conv_query = "SELECT COUNT(*) as count FROM conversations WHERE agent_id = %s"
        conv_count = db.execute_one(conv_query, (agent_id,))

        # Count messages
        msg_query = """
            SELECT COUNT(*) as count
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE c.agent_id = %s
        """
        msg_count = db.execute_one(msg_query, (agent_id,))

        # TODO: Track actual token usage
        # For now, estimate based on messages
        estimated_tokens = (msg_count['count'] or 0) * 100  # ~100 tokens per message

        return {
            "tokens_used": estimated_tokens,
            "estimated_cost": estimated_tokens * 0.00001,  # Rough estimate
            "conversations_count": conv_count['count'] or 0,
            "messages_count": msg_count['count'] or 0,
            "period": "all_time"
        }

    except Exception as e:
        logger.error(f"Error in get_usage_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# IMAGE UPLOAD ENDPOINTS
# ============================================================================

from fastapi import UploadFile, File
from execution.image_storage import save_property_image, get_image_url

@router.post("/properties/{property_id}/upload-image")
async def upload_property_image(
    property_id: str,
    image: UploadFile = File(...),
    image_type: str = "main"
):
    """
    Upload property image

    Args:
        property_id: Property UUID
        image: Image file
        image_type: "main", "thumbnail", or "gallery"
    """
    try:
        # Read image data
        image_data = await image.read()
        import base64
        image_base64 = base64.b64encode(image_data).decode()

        # Save image
        image_path = save_property_image(
            image_data=image_base64,
            property_id=property_id,
            image_type=image_type
        )

        # Update property with image path
        db = get_db()
        db.update("properties", {
            "image_url": image_path
        }, {"property_id": property_id})

        return {
            "status": "uploaded",
            "image_path": image_path,
            "image_url": f"/uploads/properties/{image_path.split('/')[-1]}"
        }

    except Exception as e:
        logger.error(f"Image upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/properties/create-with-image")
async def create_property_with_image(
    agent_id: str,
    title: str,
    location: str,
    property_type: str,
    price: int,
    bedrooms: int,
    bathrooms: int,
    image: Optional[UploadFile] = File(None),
    size_sqft: Optional[int] = None,
    description: Optional[str] = None
):
    """
    Create property with image upload

    Convenient endpoint for mobile app to create property with image in one call
    """
    try:
        db = get_db()

        # Create property
        property_id = db.insert("properties", {
            "agent_id": agent_id,
            "title": title,
            "location": location,
            "property_type": property_type,
            "price": price,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "size_sqft": size_sqft,
            "description": description
        })

        # Upload image if provided
        image_url = None
        if image:
            image_data = await image.read()
            import base64
            image_base64 = base64.b64encode(image_data).decode()

            image_path = save_property_image(
                image_data=image_base64,
                property_id=property_id,
                image_type="main"
            )

            # Update property with image
            db.update("properties", {
                "image_url": image_path
            }, {"property_id": property_id})

            image_url = image_path

        return {
            "property_id": property_id,
            "status": "created",
            "image_url": image_url
        }

    except Exception as e:
        logger.error(f"Create property error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PUSH NOTIFICATION ENDPOINTS
# ============================================================================

from execution.push_notifications import register_device_token as register_token

@router.post("/notifications/register")
async def register_notification_token(
    agent_id: str,
    device_token: str,
    platform: str = "ios"
):
    """
    Register device for push notifications

    Args:
        agent_id: Agent UUID
        device_token: FCM/APNs token
        platform: "ios" or "android"
    """
    try:
        register_token(agent_id, device_token, platform)

        return {
            "status": "registered",
            "device_token": device_token,
            "platform": platform
        }

    except Exception as e:
        logger.error(f"Token registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/test")
async def test_push_notification(agent_id: str):
    """
    Send test push notification

    For testing push notification setup
    """
    try:
        from execution.push_notifications import send_push_notification
        import asyncio

        await send_push_notification(
            agent_id=agent_id,
            title="Test Notification",
            body="Your push notifications are working!",
            data={"type": "test"}
        )

        return {"status": "sent"}

    except Exception as e:
        logger.error(f"Test notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

