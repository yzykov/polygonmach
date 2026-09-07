import asyncio
import random

from playwright.async_api import Page

from .config import SETTINGS


CHALLENGE_MARKERS = (
    "please wait while your request is being verified",
    "one moment, please",
    "checking your browser",
)


async def open_page(page: Page, url: str) -> bool:
    backoffs = (10, 30, 60)

    for attempt, backoff in enumerate(backoffs, start=1):
        try:
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60_000,
            )

            await page.wait_for_timeout(1000)

            status = response.status if response else 0
            body = (await page.locator("body").inner_text()).lower()

            blocked = (
                status in {403, 429}
                or any(marker in body for marker in CHALLENGE_MARKERS)
            )

            if blocked:
                print(
                    f"  blocked/challenge, attempt {attempt}, "
                    f"sleep {backoff}s"
                )
                await asyncio.sleep(backoff)
                continue

            if status >= 400:
                print(f"  HTTP {status}")
                return False

            return True

        except Exception as exc:
            print(f"  browser error: {exc}")

            if attempt < len(backoffs):
                await asyncio.sleep(backoff)

    return False


async def polite_delay() -> None:
    await asyncio.sleep(
        random.uniform(
            SETTINGS.min_delay_sec,
            SETTINGS.max_delay_sec,
        )
    )
