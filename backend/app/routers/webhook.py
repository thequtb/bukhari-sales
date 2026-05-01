"""Instagram webhook router — handles verification and incoming message events."""

import json
import logging

from fastapi import APIRouter, Request, Response, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.services import instagram as ig_service
from app.services import conversation as conv_service
from app.services import ai_agent

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["webhook"])

# In-memory set of connected WebSocket clients (populated from main.py)
ws_clients: set = set()


@router.get("/webhook")
async def verify_webhook(request: Request):
    """Handle Meta webhook verification challenge.

    Meta sends a GET request with:
    - hub.mode = 'subscribe'
    - hub.verify_token = your custom token
    - hub.challenge = a random string to echo back
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.webhook_verify_token:
        logger.info("Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("Webhook verification failed: mode=%s, token=%s", mode, token)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming Instagram webhook events (messages, etc.).

    Flow:
    1. Verify X-Hub-Signature-256 header
    2. Parse the messaging event
    3. Store the incoming message
    4. Generate AI response via LangChain
    5. Send reply via Instagram Send API
    6. Store the bot response
    7. Notify WebSocket clients
    """
    # Verify signature
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not ig_service.verify_webhook_signature(body, signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Parse payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    logger.info("Webhook event received: %s", json.dumps(payload, indent=2)[:500])

    # Process messaging entries
    for entry in payload.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            await _process_messaging_event(db, messaging_event)

    # Always return 200 to acknowledge receipt
    return {"status": "ok"}


async def _process_messaging_event(db: AsyncSession, event: dict):
    """Process a single messaging event from the webhook payload."""
    sender_id = event.get("sender", {}).get("id")
    message_data = event.get("message", {})
    message_text = message_data.get("text")
    message_id = message_data.get("mid")

    # Skip if no text message (could be an attachment, reaction, etc.)
    if not sender_id or not message_text:
        logger.debug("Skipping non-text event: %s", event)
        return

    # Skip echo messages (messages sent by the page itself)
    if message_data.get("is_echo"):
        logger.debug("Skipping echo message")
        return

    logger.info("Processing message from %s: %s", sender_id, message_text[:100])

    try:
        # Fetch user profile info
        profile = await ig_service.get_user_profile(sender_id)
        username = profile.get("name")
        profile_pic = profile.get("profile_pic")

        # Get or create conversation
        conversation = await conv_service.get_or_create_conversation(
            db, sender_id, username=username, profile_pic_url=profile_pic
        )

        # Store incoming message
        await conv_service.add_message(
            db,
            conversation_id=conversation.id,
            sender="user",
            content=message_text,
            instagram_message_id=message_id,
        )

        # Get conversation history for context
        history = await conv_service.get_conversation_history(db, conversation.id)

        # Generate AI response
        ai_response = await ai_agent.generate_response(
            db=db,
            user_message=message_text,
            conversation_history=history,
            username=username,
        )

        # Send reply via Instagram
        send_result = await ig_service.send_message(
            recipient_id=sender_id,
            text=ai_response,
            reply_to_mid=message_id,
        )

        # Store bot response
        bot_mid = send_result.get("message_id")
        await conv_service.add_message(
            db,
            conversation_id=conversation.id,
            sender="bot",
            content=ai_response,
            instagram_message_id=bot_mid,
        )

        await db.commit()

        # Notify WebSocket clients
        await _broadcast_ws({
            "type": "new_message",
            "conversation_id": conversation.id,
            "sender": "user",
            "content": message_text,
            "bot_reply": ai_response,
            "username": username,
        })

        logger.info("Successfully processed and replied to message from %s", sender_id)

    except Exception as e:
        logger.error("Error processing message from %s: %s", sender_id, e, exc_info=True)


async def _broadcast_ws(data: dict):
    """Broadcast a message to all connected WebSocket clients."""
    import json
    message = json.dumps(data)
    dead_clients = set()
    for ws in ws_clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead_clients.add(ws)
    ws_clients -= dead_clients
