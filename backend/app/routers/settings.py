"""Settings router — manage AI configuration."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AIConfig
from app.schemas import AIConfigUpdate, AIConfigOut
from app.prompts.sales_agent import DEFAULT_SYSTEM_PROMPT
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=AIConfigOut)
async def get_settings_config(db: AsyncSession = Depends(get_db)):
    """Get current AI configuration."""
    result = await db.execute(select(AIConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        # Create default config
        config = AIConfig(
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            temperature=0.7,
            model_name="gpt-4o-mini",
            max_tokens=500,
        )
        db.add(config)
        await db.flush()
        await db.commit()
        await db.refresh(config)

    return config


@router.put("", response_model=AIConfigOut)
async def update_settings(body: AIConfigUpdate, db: AsyncSession = Depends(get_db)):
    """Update AI configuration."""
    result = await db.execute(select(AIConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        config = AIConfig(
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            temperature=0.7,
            model_name="gpt-4o-mini",
            max_tokens=500,
        )
        db.add(config)
        await db.flush()

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    await db.flush()
    await db.commit()
    await db.refresh(config)
    logger.info("AI config updated: model=%s, temp=%s", config.model_name, config.temperature)
    return config


@router.get("/webhook-info")
async def get_webhook_info():
    """Get webhook configuration info for the settings page."""
    return {
        "webhook_url": f"{settings.app_url}/webhook",
        "verify_token": settings.webhook_verify_token,
        "page_id": settings.instagram_page_id,
        "page_id_configured": settings.instagram_page_id != "YOUR_PAGE_ID_HERE",
        "token_configured": settings.instagram_page_access_token != "YOUR_PAGE_ACCESS_TOKEN_HERE",
    }


@router.post("/reset-prompt", response_model=AIConfigOut)
async def reset_to_default_prompt(db: AsyncSession = Depends(get_db)):
    """Reset the system prompt to the current default from code.

    Useful when the prompt template has been updated and the stored
    DB version is stale.
    """
    result = await db.execute(select(AIConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        config = AIConfig(
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            temperature=0.7,
            model_name="gpt-4o-mini",
            max_tokens=500,
        )
        db.add(config)
    else:
        config.system_prompt = DEFAULT_SYSTEM_PROMPT

    await db.flush()
    await db.commit()
    await db.refresh(config)
    logger.info("System prompt reset to default")
    return config

