#!/usr/bin/env python3
"""Marketing-style screen recording: forced dark mode, eased motion, full product arc."""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

from playwright.async_api import async_playwright

APP_URL = os.environ.get("VIBEGRAPH_DEMO_URL", "https://vibegraph.vercel.app")
BASE = Path(__file__).resolve().parent
DEMO_DIR = BASE / "demo_project"
OUTPUT_DIR = BASE / "output"
OUT_MP4 = OUTPUT_DIR / "vibegraph_marketing_dark.mp4"

THEME_INIT_SCRIPT = """
() => {
  try {
    localStorage.setItem('vg_v1_theme', 'dark');
  } catch (e) {}
}
"""


async def smooth_move(page, x: float, y: float, *, steps: int = 42) -> None:
    vp = page.viewport_size or {"width": 1920, "height": 1080}
    cx, cy = vp["width"] / 2, vp["height"] / 2
    for i in range(1, steps + 1):
        t = i / steps
        ease = t * t * (3 - 2 * t)
        nx = cx + (x - cx) * ease
        ny = cy + (y - cy) * ease
        await page.mouse.move(nx, ny)
        await asyncio.sleep(0.014)


async def drag_pan(
    page,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    steps: int = 36,
) -> None:
    await smooth_move(page, x0, y0, steps=22)
    await page.mouse.down()
    for i in range(1, steps + 1):
        t = i / steps
        ease = t * t * (3 - 2 * t)
        await page.mouse.move(x0 + (x1 - x0) * ease, y0 + (y1 - y0) * ease)
        await asyncio.sleep(0.016)
    await page.mouse.up()


async def scroll_zoom(page, x: float, y: float, delta_y: float) -> None:
    await page.mouse.move(x, y)
    steps = max(8, int(abs(delta_y) / 70))
    for _ in range(steps):
        await page.mouse.wheel(0, delta_y / steps)
        await asyncio.sleep(0.055)


async def dismiss_ai_settings(page) -> None:
    for _ in range(6):
        overlay = page.locator(".ai-settings-overlay")
        if await overlay.count() == 0:
            return
        close = page.get_by_role("button", name="Close AI Settings")
        if await close.is_visible():
            await close.click()
        else:
            await page.keyboard.press("Escape")
        await asyncio.sleep(0.38)


async def ensure_dark_mode(page) -> None:
    """Theme toggle if localStorage init missed (cached shell, etc.)."""
    dark_toggle = page.get_by_role("button", name="Switch to dark mode")
    if await dark_toggle.count() and await dark_toggle.is_visible():
        await dark_toggle.click()
        await asyncio.sleep(0.45)
    await page.evaluate(
        """() => {
      try { localStorage.setItem('vg_v1_theme', 'dark'); } catch (e) {}
      document.documentElement.setAttribute('data-theme', 'dark');
    }"""
    )


async def record() -> Path:
    if not DEMO_DIR.is_dir():
        raise FileNotFoundError(f"Missing {DEMO_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUTPUT_DIR.glob("*.webm"):
        old.unlink()

    js_files = sorted(DEMO_DIR.glob("*.js"))
    if not js_files:
        raise FileNotFoundError(f"No .js files under {DEMO_DIR}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(OUTPUT_DIR),
            record_video_size={"width": 1920, "height": 1080},
            locale="en-US",
            color_scheme="dark",
            ignore_https_errors=True,
        )
        await context.add_init_script(THEME_INIT_SCRIPT)

        page = await context.new_page()
        await page.emulate_media(color_scheme="dark")
        await page.goto(APP_URL, wait_until="load", timeout=120_000)
        await ensure_dark_mode(page)

        # Hero beat — empty state, cinematic hold
        await asyncio.sleep(2.8)

        got_it = page.get_by_role("button", name="Got it")
        if await got_it.count():
            await got_it.click()
            await asyncio.sleep(0.4)

        await page.get_by_role("button", name="Upload new project for analysis").click()
        await page.get_by_role("button", name="Select a project folder to analyze").wait_for(
            state="visible",
            timeout=15_000,
        )
        await asyncio.sleep(0.55)
        try:
            await page.locator('input[type="file"]').set_input_files(str(DEMO_DIR))
        except Exception:
            await page.locator('input[type="file"]').set_input_files([str(f) for f in js_files])

        await page.get_by_text("Analyzing project").wait_for(state="visible", timeout=15_000)
        await asyncio.sleep(0.7)
        await page.locator(".react-flow__node").first.wait_for(state="visible", timeout=120_000)
        await asyncio.sleep(5.2)

        pane = page.locator(".react-flow__pane")
        box = await pane.bounding_box()
        assert box
        cx, cy = box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.46

        await drag_pan(page, cx - 90, cy + 55, cx + 130, cy - 35)
        await asyncio.sleep(0.55)
        await scroll_zoom(page, cx, cy, -340)
        await asyncio.sleep(0.65)

        target = page.locator('.react-flow__node:has-text("fetchUserData")').first
        await target.scroll_into_view_if_needed()
        tbox = await target.bounding_box()
        if tbox:
            await smooth_move(
                page,
                tbox["x"] + tbox["width"] / 2,
                tbox["y"] + tbox["height"] / 2 - 14,
                steps=48,
            )
            await asyncio.sleep(0.65)
        await target.click()
        await asyncio.sleep(1.1)
        await dismiss_ai_settings(page)
        await asyncio.sleep(1.0)

        levels = page.get_by_role("group", name="Difficulty level")
        for lvl in ("beginner", "intermediate", "advanced"):
            btn = levels.get_by_role("button", name=lvl, exact=True)
            if await btn.count():
                await btn.click(force=True)
                await asyncio.sleep(0.4)
                await dismiss_ai_settings(page)
                await asyncio.sleep(2.6)

        await dismiss_ai_settings(page)
        await page.get_by_label("Open Chat").click()
        await asyncio.sleep(0.75)
        await page.get_by_label("Chat input").fill(
            "Which function is the best entry point to understand this codebase?"
        )
        await asyncio.sleep(0.45)
        await page.get_by_role("button", name="Send message").click()
        await asyncio.sleep(5.5)
        await dismiss_ai_settings(page)

        await page.get_by_label("Close Chat").click()
        await asyncio.sleep(0.55)

        play = page.get_by_label("Play simulation")
        await play.scroll_into_view_if_needed()
        await asyncio.sleep(0.45)
        await play.click()
        await asyncio.sleep(20.0)

        await page.get_by_label("Pause simulation").click()
        await asyncio.sleep(3.5)

        await scroll_zoom(page, cx, cy, -200)
        await drag_pan(page, cx + 70, cy - 25, cx - 110, cy + 45)
        await asyncio.sleep(4.5)

        await page.close()
        await context.close()
        await browser.close()

    webms = sorted(OUTPUT_DIR.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not webms:
        raise RuntimeError("No WebM from Playwright.")
    return webms[0]


def transcode(webm: Path, mp4: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(webm),
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(mp4),
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    w = asyncio.run(record())
    transcode(w, OUT_MP4)
    print(OUT_MP4)
