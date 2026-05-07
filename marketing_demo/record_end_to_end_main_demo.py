#!/usr/bin/env python3
"""Record README demo: load app, upload docs/demo/main.py, explore graph, select nodes (code panel).

Writes docs/demo/vibegraph_end_to_end_demo.mp4 for embedding in README via HTML <video>.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

from playwright.async_api import async_playwright

THEME_INIT_SCRIPT = """
() => {
  try {
    localStorage.setItem('vg_v1_theme', 'dark');
  } catch (e) {}
}
"""

APP_URL = os.environ.get("VIBEGRAPH_DEMO_URL", "https://vibegraph.vercel.app")
ROOT = Path(__file__).resolve().parents[1]
MAIN_PY = ROOT / "docs" / "demo" / "main.py"
RECORD_TMP = ROOT / "docs" / "demo" / "_record_tmp"
OUT_MP4 = ROOT / "docs" / "demo" / "vibegraph_end_to_end_demo.mp4"


async def smooth_move(page, x: float, y: float, *, steps: int = 35) -> None:
    vp = page.viewport_size or {"width": 1280, "height": 720}
    cx, cy = vp["width"] / 2, vp["height"] / 2
    for i in range(1, steps + 1):
        t = i / steps
        ease = t * t * (3 - 2 * t)
        nx = cx + (x - cx) * ease
        ny = cy + (y - cy) * ease
        await page.mouse.move(nx, ny)
        await asyncio.sleep(0.012)


async def drag_pan(
    page,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    steps: int = 28,
) -> None:
    await smooth_move(page, x0, y0, steps=18)
    await page.mouse.down()
    for i in range(1, steps + 1):
        t = i / steps
        ease = t * t * (3 - 2 * t)
        await page.mouse.move(x0 + (x1 - x0) * ease, y0 + (y1 - y0) * ease)
        await asyncio.sleep(0.014)
    await page.mouse.up()


async def scroll_zoom(page, x: float, y: float, delta_y: float) -> None:
    await page.mouse.move(x, y)
    steps = max(6, int(abs(delta_y) / 80))
    for _ in range(steps):
        await page.mouse.wheel(0, delta_y / steps)
        await asyncio.sleep(0.05)


async def ensure_dark_mode(page) -> None:
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


async def dismiss_ai_settings(page) -> None:
    for _ in range(5):
        overlay = page.locator(".ai-settings-overlay")
        if await overlay.count() == 0:
            return
        close = page.get_by_role("button", name="Close AI Settings")
        if await close.is_visible():
            await close.click()
        else:
            await page.keyboard.press("Escape")
        await asyncio.sleep(0.35)


async def click_named_node(page, name: str) -> None:
    node = page.locator(f'.react-flow__node:has-text("{name}")').first
    await node.scroll_into_view_if_needed()
    box = await node.bounding_box()
    if box:
        await smooth_move(page, box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=38)
        await asyncio.sleep(0.35)
    await node.click()
    await asyncio.sleep(0.65)
    await dismiss_ai_settings(page)
    await asyncio.sleep(1.4)


async def record() -> Path:
    if not MAIN_PY.is_file():
        raise FileNotFoundError(f"Missing demo file: {MAIN_PY}")

    RECORD_TMP.mkdir(parents=True, exist_ok=True)
    for old in RECORD_TMP.glob("*.webm"):
        old.unlink()

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
            record_video_dir=str(RECORD_TMP),
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
        await asyncio.sleep(2.4)

        got_it = page.get_by_role("button", name="Got it")
        if await got_it.count():
            await got_it.click()
            await asyncio.sleep(0.35)

        await page.get_by_role("button", name="Upload new project for analysis").click()
        await page.get_by_role("button", name="Select a project folder to analyze").wait_for(
            state="visible",
            timeout=15_000,
        )
        await asyncio.sleep(0.45)
        await page.locator('input[type="file"]').set_input_files([str(MAIN_PY)])

        await page.get_by_text("Analyzing project").wait_for(state="visible", timeout=10_000)
        await page.locator(".react-flow__node").first.wait_for(state="visible", timeout=120_000)
        await asyncio.sleep(4.8)

        pane = page.locator(".react-flow__pane")
        box = await pane.bounding_box()
        assert box
        cx, cy = box["x"] + box["width"] * 0.52, box["y"] + box["height"] * 0.48

        await drag_pan(page, cx - 60, cy + 50, cx + 100, cy - 40)
        await asyncio.sleep(0.5)
        await scroll_zoom(page, cx, cy, -320)
        await asyncio.sleep(0.55)

        await click_named_node(page, "main")
        await click_named_node(page, "helper_beta")
        await click_named_node(page, "helper_alpha")

        await drag_pan(page, cx + 40, cy - 30, cx - 90, cy + 50)
        await asyncio.sleep(0.6)
        await scroll_zoom(page, cx, cy, -120)
        await asyncio.sleep(3.5)

        await page.close()
        await context.close()
        await browser.close()

    webms = sorted(RECORD_TMP.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not webms:
        raise RuntimeError("Playwright did not emit a WebM recording.")
    return webms[0]


def transcode(webm: Path, mp4: Path) -> None:
    mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(webm),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "22",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(mp4),
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    webm_path = asyncio.run(record())
    transcode(webm_path, OUT_MP4)
    print(OUT_MP4)
