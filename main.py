"""
FastAPI Server for WhatsApp AI Assistant
Main application entry point
"""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict
from loguru import logger
import sys

from execution.config import settings
from execution.webhook_handler import process_webhook
from execution.database import get_db
from execution.set_mode_human import set_mode_human
from execution.set_mode_ai import set_mode_ai
from execution.property_lookup import search_properties, get_property_by_id


# Configure logging
logger.remove()
logger.add(sys.stderr, level=settings.log_level)
logger.add("logs/app.log", rotation="500 MB", level="INFO")

# Initialize FastAPI app
app = FastAPI(
    title="WhatsApp AI Assistant",
    description="Micro-SaaS for real estate agents",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
# app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================
# REQUEST MODELS
# ============================================

class WebhookPayload(BaseModel):
    """Green API webhook payload"""
    typeWebhook: str
    instanceData: Dict
    timestamp: Optional[int] = None
    idMessage: Optional[str] = None
    senderData: Optional[Dict] = None
    messageData: Optional[Dict] = None


class ToggleModeRequest(BaseModel):
    """Request to toggle conversation mode"""
    conversation_id: str
    mode: str  # 'AI' or 'HUMAN'
    agent_id: Optional[str] = None


class SendMessageRequest(BaseModel):
    """Request to send message manually"""
    conversation_id: str
    message: str


class PropertySearchRequest(BaseModel):
    """Property search request"""
    agent_id: str
    location: Optional[str] = None
    property_type: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    bedrooms: Optional[int] = None


# ============================================
# ROUTES
# ============================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "service": "WhatsApp AI Assistant",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    db = get_db()

    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "environment": settings.environment
    }


@app.get("/inbox", response_class=HTMLResponse)
@app.get("/templates/inbox.html", response_class=HTMLResponse)
async def get_inbox():
    """Serve the inbox UI"""
    try:
        with open("templates/inbox.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Inbox UI not found")


@app.post("/webhook/greenapi")
async def greenapi_webhook(payload: WebhookPayload):
    """
    Green API webhook endpoint

    Green API will POST to this endpoint when messages are received
    Configure this URL in your Green API dashboard
    """
    try:
        logger.info(f"Webhook received: {payload.typeWebhook}")

        result = process_webhook(payload.model_dump())

        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conversations/toggle-mode")
async def toggle_mode(request: ToggleModeRequest):
    """Toggle conversation between AI and HUMAN mode"""
    try:
        if request.mode == "HUMAN":
            success = set_mode_human(
                conversation_id=request.conversation_id,
                agent_id=request.agent_id,
                reason="api_toggle"
            )
        elif request.mode == "AI":
            success = set_mode_ai(
                conversation_id=request.conversation_id,
                agent_id=request.agent_id,
                reason="api_toggle"
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid mode. Use 'AI' or 'HUMAN'")

        return {
            "success": success,
            "conversation_id": request.conversation_id,
            "mode": request.mode
        }

    except Exception as e:
        logger.error(f"Toggle mode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details"""
    db = get_db()

    query = """
        SELECT
            c.conversation_id,
            c.contact_number,
            c.contact_name,
            c.current_mode,
            c.last_message_timestamp,
            c.last_message_preview,
            c.unread_count,
            a.full_name as agent_name
        FROM conversations c
        JOIN agents a ON c.agent_id = a.agent_id
        WHERE c.conversation_id = %s
    """

    conversation = db.execute_one(query, (conversation_id,))

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@app.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, limit: int = 50):
    """Get messages for a conversation"""
    db = get_db()

    query = """
        SELECT
            message_id,
            sender_type,
            message_text,
            timestamp,
            delivered
        FROM messages
        WHERE conversation_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
    """

    messages = db.execute(query, (conversation_id, limit))

    # Reverse to chronological order
    messages = list(reversed(messages))

    return {"messages": messages}


@app.get("/api/agents/{agent_id}/conversations")
async def get_agent_conversations(agent_id: str):
    """Get all conversations for an agent"""
    db = get_db()

    query = """
        SELECT
            conversation_id,
            contact_number,
            contact_name,
            current_mode,
            last_message_timestamp,
            last_message_preview,
            unread_count
        FROM conversations
        WHERE agent_id = %s
        ORDER BY last_message_timestamp DESC NULLS LAST
    """

    conversations = db.execute(query, (agent_id,))

    return {"conversations": conversations}


@app.post("/api/properties/search")
async def search_properties_api(request: PropertySearchRequest):
    """Search properties"""
    try:
        properties = search_properties(
            agent_id=request.agent_id,
            location=request.location,
            property_type=request.property_type,
            min_price=request.min_price,
            max_price=request.max_price,
            bedrooms=request.bedrooms
        )

        return {"properties": properties}

    except Exception as e:
        logger.error(f"Property search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/properties/{property_id}")
async def get_property(property_id: str):
    """Get single property"""
    property_data = get_property_by_id(property_id)

    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    return property_data


@app.get("/api/agents/{agent_id}/properties")
async def get_agent_properties(agent_id: str):
    """Get all properties for an agent"""
    db = get_db()

    query = """
        SELECT
            property_id,
            title,
            property_type,
            location,
            price,
            bedrooms,
            bathrooms,
            size_sqft,
            availability,
            created_at
        FROM properties
        WHERE agent_id = %s
          AND is_archived = FALSE
        ORDER BY created_at DESC
    """

    properties = db.execute(query, (agent_id,))

    return {"properties": properties}


# ============================================
# STARTUP / SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("WhatsApp AI Assistant starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url}")

    # Test database connection
    db = get_db()
    try:
        db.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("WhatsApp AI Assistant shutting down...")

    db = get_db()
    db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.environment == "development"),
        log_level=settings.log_level.lower()
    )

# ============================================
# MOBILE APP ENDPOINTS
# ============================================
from api.mobile_endpoints import router as mobile_router
app.include_router(mobile_router)

# Authentication endpoints
from api.auth_endpoints import router as auth_router
app.include_router(auth_router)

# Serve uploaded images
from fastapi.staticfiles import StaticFiles
import os
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
