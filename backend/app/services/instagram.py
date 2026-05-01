"""Instagram Graph API client for webhook verification and messaging."""

import hashlib
import hmac
import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify the X-Hub-Signature-256 header from Meta webhooks.

    Args:
        payload: Raw request body bytes.
        signature: The X-Hub-Signature-256 header value (e.g. 'sha256=abc123...').

    Returns:
        True if the signature is valid.
    """
    if not signature or not signature.startswith("sha256="):
        return False

    expected = hmac.new(
        settings.facebook_app_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    received = signature[7:]  # strip 'sha256=' prefix
    return hmac.compare_digest(expected, received)


async def send_message(
    recipient_id: str,
    text: str,
    reply_to_mid: Optional[str] = None,
) -> dict:
    """Send a message to an Instagram user via the Send API.

    Args:
        recipient_id: The Instagram-scoped user ID (IGSID).
        text: The message text to send.
        reply_to_mid: Optional message ID to reply to (threaded reply).

    Returns:
        The API response as a dict.
    """
    url = f"{settings.graph_api_base}/{settings.instagram_page_id}/messages"

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE",
        "access_token": settings.instagram_page_access_token,
    }

    if reply_to_mid:
        payload["reply_to"] = {"mid": reply_to_mid}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)

        if response.status_code != 200:
            logger.error(
                "Failed to send Instagram message: %s %s",
                response.status_code,
                response.text,
            )
            return {"error": response.text, "status_code": response.status_code}

        data = response.json()
        logger.info("Message sent successfully to %s: %s", recipient_id, data)
        return data


async def get_user_profile(user_id: str) -> dict:
    """Fetch a user's Instagram profile info.

    Args:
        user_id: The Instagram-scoped user ID.

    Returns:
        Dict with 'name' and 'profile_pic' if available.
    """
    url = f"{settings.graph_api_base}/{user_id}"
    params = {
        "fields": "name,profile_pic",
        "access_token": settings.instagram_page_access_token,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Could not fetch profile for %s: %s", user_id, response.text)
                return {}
        except Exception as e:
            logger.warning("Error fetching profile for %s: %s", user_id, e)
            return {}
