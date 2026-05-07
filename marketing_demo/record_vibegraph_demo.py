#!/usr/bin/env python3
"""Automated cinematic-style screen recording for VibeGraph marketing demo."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from playwright.async_api import async_playwright

APP_URL = "https://vibegraph.vercel.app"
DEMO_DIR = Path(__file__).resolve().parent / "demo_project"
DEMO_ZIP = Path(__file__).resolve().parent / "demo_project.zip"
OUTPUT = Path(__file__).resolve().parent / "output"


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


async def snap(page, name: str) -> None:
    path = OUTPUT / name
    await page.screenshot(path=str(path), type="png")


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


async def main() -> Path:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for old in OUTPUT.glob("scene-*.png"):
        old.unlink()
    for old in OUTPUT.glob("*.webm"):
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
            record_video_dir=str(OUTPUT),
            record_video_size={"width": 1920, "height": 1080},
            locale="en-US",
            ignore_https_errors=True,
        )
        page = await context.new_page()

        # [0:00–0:05] Empty state
        await page.goto(APP_URL, wait_until="load", timeout=120_000)
        await asyncio.sleep(2.0)
        await snap(page, "scene-01.png")

        got_it = page.get_by_role("button", name="Got it")
        if await got_it.count():
            await got_it.click()
            await asyncio.sleep(0.35)

        # [0:05–0:15] Upload (modal accepts folder or zip via hidden input — use zip files list)
        await page.get_by_role("button", name="Upload new project for analysis").click()
        await page.get_by_role("button", name="Select a project folder to analyze").wait_for(
            state="visible",
            timeout=15_000,
        )
        await asyncio.sleep(0.4)

        # Prefer uploading all demo sources so paths mirror the zip layout
        try:
            await page.locator('input[type="file"]').set_input_files(str(DEMO_DIR))
        except Exception:
            js_files = sorted(DEMO_DIR.glob("*.js"))
            await page.locator('input[type="file"]').set_input_files([str(f) for f in js_files])
        await snap(page, "scene-02.png")

        await page.get_by_text("Analyzing project").wait_for(state="visible", timeout=5_000)
        await asyncio.sleep(0.6)

        await page.locator(".react-flow__node").first.wait_for(state="visible", timeout=120_000)
        await asyncio.sleep(2.0)
        await asyncio.sleep(4.6)
        await snap(page, "scene-03.png")
        await asyncio.sleep(1.5)

        # Close modal if still open (upload success closes it)
        await asyncio.sleep(0.5)

        pane = page.locator(".react-flow__pane")
        box = await pane.bounding_box()
        assert box
        cx, cy = box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.48

        # [0:15–0:25] Pan / zoom / hover / click fetchUserData
        await drag_pan(page, cx - 80, cy + 40, cx + 120, cy - 30)
        await asyncio.sleep(0.35)
        await scroll_zoom(page, cx, cy, -280)
        await asyncio.sleep(0.45)

        target = page.locator('.react-flow__node:has-text("fetchUserData")').first
        await target.scroll_into_view_if_needed()
        tbox = await target.bounding_box()
        if tbox:
            tx = tbox["x"] + tbox["width"] / 2
            ty = tbox["y"] + tbox["height"] / 2
            await smooth_move(page, tx, ty - 18, steps=40)
            await asyncio.sleep(0.55)
        await target.click()
        await asyncio.sleep(1.0)
        await dismiss_ai_settings(page)
        await asyncio.sleep(0.6)
        await snap(page, "scene-04.png")

        # [0:25–0:40] Difficulty levels (AI copy depends on OpenRouter key)
        levels = page.get_by_role("group", name="Difficulty level")
        for lvl in ("beginner", "intermediate", "advanced"):
            btn = levels.get_by_role("button", name=lvl, exact=True)
            if await btn.count():
                await btn.click(force=True)
                await asyncio.sleep(0.35)
                await dismiss_ai_settings(page)
                await asyncio.sleep(2.0)
        await snap(page, "scene-05.png")

        # [0:40–0:55] Chat
        await dismiss_ai_settings(page)
        await page.get_by_label("Open Chat").click()
        await asyncio.sleep(0.6)
        q = "Which function is the best entry point to understand this codebase?"
        await page.get_by_label("Chat input").fill(q)
        await asyncio.sleep(0.35)
        await page.get_by_role("button", name="Send message").click()
        await asyncio.sleep(5.0)
        await dismiss_ai_settings(page)
        await snap(page, "scene-06.png")

        # [0:55–1:10] Ghost Runner play
        await dismiss_ai_settings(page)
        await page.get_by_label("Close Chat").click()
        await asyncio.sleep(0.45)

        play = page.get_by_label("Play simulation")
        await play.scroll_into_view_if_needed()
        await asyncio.sleep(0.3)
        await play.click()
        await asyncio.sleep(22.0)
        await snap(page, "scene-07.png")

        # [1:10–1:20] Pause + summary pane visible
        await page.get_by_label("Pause simulation").click()
        await asyncio.sleep(3.5)
        await snap(page, "scene-08.png")

        # [1:20–1:30] Wide graph + visited styling
        await scroll_zoom(page, cx, cy, -180)
        await drag_pan(page, cx + 60, cy - 20, cx - 100, cy + 40)
        await asyncio.sleep(3.5)
        await snap(page, "scene-09.png")
        await asyncio.sleep(4.0)

        await page.close()
        await context.close()
        await browser.close()

    videos = sorted(OUTPUT.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not videos:
        raise RuntimeError("No WebM video emitted by Playwright.")
    return videos[0]


if __name__ == "__main__":
    webm = asyncio.run(main())
    mp4 = OUTPUT / "vibegraph_demo.mp4"
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
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(mp4),
    ]
    r = shutil.which("ffmpeg")
    if not r:
        raise SystemExit("ffmpeg not found")
    import subprocess

    subprocess.run(cmd, check=True)
    print(webm)
    print(mp4)
