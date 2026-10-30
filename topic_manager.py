"""
Telegram Forum Topic Manager Module
Compatible with Pyrogram / PyroFork / Hydrogram
--------------------------------------------------
A robust, plug-and-play helper for managing topic
creation within forum-enabled supergroups. ⚝
"""

import asyncio
import logging
from typing import Optional, Union
from pyrogram import Client
from pyrogram.errors import (
    ChatAdminRequired,
    FloodWait,
    RPCError,
    TopicClosed
)

logger = logging.getLogger("TopicManager")

# Standard Telegram Topic Colors (RGB Integers)
TOPIC_COLORS = {
    "blue": 0x6FB9F0,
    "yellow": 0xFFD67E,
    "purple": 0xCB86DB,
    "green": 0x8EEE98,
    "pink": 0xFF93B2,
    "red": 0xFB6F5F,
}


async def create_forum_topic_safe(
    client: Client,
    chat_id: Union[int, str],
    title: str,
    color_name: str = "blue",
    icon_emoji_id: Optional[int] = None,
    max_retries: int = 3
) -> Optional[int]:
    """
    Creates a forum topic in a supergroup safely with retry logic,
    length truncation, and error boundary handling.

    :param client: Active Pyrogram Client instance.
    :param chat_id: Target forum group ID (e.g., -100xxxxxxxxxx).
    :param title: Topic title (Auto-trimmed to max 128 characters).
    :param color_name: Optional icon color ('blue', 'yellow', 'purple', 'green', 'pink', 'red').
    :param icon_emoji_id: Optional custom emoji ID (Telegram custom emoji).
    :param max_retries: Number of attempts if rate-limited.
    :return: message_thread_id (int) of the created topic, or None on failure.
    """
    clean_title = (title or "").strip()[:128]
    if not clean_title:
        clean_title = "General Topic"

    icon_color = TOPIC_COLORS.get(color_name.lower(), TOPIC_COLORS["blue"])

    for attempt in range(max_retries):
        try:
            topic = await client.create_forum_topic(
                chat_id=chat_id,
                title=clean_title,
                icon_color=icon_color,
                icon_emoji_id=icon_emoji_id
            )
            logger.info(f"Topic created: '{clean_title}' [ID: {topic.id}] in chat {chat_id}")
            return topic.id

        except FloodWait as e:
            wait_time = int(e.value) + 1
            logger.warning(f"Rate-limit hit. Sleeping for {wait_time}s (Attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(wait_time)

        except ChatAdminRequired:
            logger.error(f"Bot lacks 'can_manage_topics' admin rights in chat {chat_id}")
            return None

        except TopicClosed:
            logger.warning(f"Target forum topic or forum is closed in chat {chat_id}")
            return None

        except RPCError as e:
            logger.error(f"Telegram RPC error for '{clean_title}': {e}")
            break

        except Exception as e:
            logger.exception(f"Unexpected error creating topic '{clean_title}': {e}")
            break

    return None
