import httpx
import asyncio
import logging
from typing import Optional, Dict
from bot.config import NASA_API_KEY

log = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

APOD_URL = "https://api.nasa.gov/planetary/apod"


async def fetch_apod_by_date(date_str: str, retries: int = 4) -> Optional[Dict]:
    """Fetch a single NASA APOD entry for a specific date (YYYY-MM-DD).

    Uses exponential backoff for 5xx/429 errors; returns None silently for 404.
    """
    params = {"api_key": NASA_API_KEY, "date": date_str, "thumbs": "true"}
    headers = {"User-Agent": "NASA-Kosmos-Bot/1.0"}

    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                r = await client.get(APOD_URL, params=params)

            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            if r.status_code in (429, 500, 502, 503, 504):
                if attempt < retries:
                    backoff = min(2 ** attempt, 15)
                    await asyncio.sleep(backoff)
                    continue
                log.debug(f"NASA {date_str}: server busy ({r.status_code})")
                return None
            log.debug(f"NASA {date_str}: status {r.status_code}")
            return None

        except (httpx.TimeoutException, httpx.ConnectError):
            if attempt < retries:
                await asyncio.sleep(2.0 * (attempt + 1))
                continue
            return None
        except Exception:
            return None
    return None


def is_valid_image(item: Dict) -> bool:
    if not item:
        return False
    media = item.get("media_type")
    if media == "image" and item.get("url"):
        return True
    if media == "video" and item.get("thumbnail_url"):
        item["url"] = item["thumbnail_url"]
        return True
    return False
