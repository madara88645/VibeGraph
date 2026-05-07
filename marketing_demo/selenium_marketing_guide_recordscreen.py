#!/usr/bin/env python3
"""
Marketing video guide automation for Cursor RecordScreen capture.

Uses Selenium + headed Chrome on DISPLAY=:1 — intentionally does NOT use Playwright.
RecordScreen captures the real desktop while this script drives the browser.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

APP_URL = os.environ.get("VIBEGRAPH_DEMO_URL", "https://vibegraph.vercel.app")
BASE = Path(__file__).resolve().parent
ZIP_PATH = BASE / "demo_project.zip"


def sleep(seconds: float) -> None:
    time.sleep(seconds)


def dismiss_ai_settings(driver: webdriver.Chrome) -> None:
    for _ in range(7):
        overlays = driver.find_elements(By.CSS_SELECTOR, ".ai-settings-overlay")
        visible = any(o.is_displayed() for o in overlays)
        if not visible:
            return
        try:
            driver.find_element(By.CSS_SELECTOR, "button.ai-settings-close").click()
        except Exception:
            driver.execute_script(
                "window.dispatchEvent(new KeyboardEvent('keydown', "
                "{key: 'Escape', keyCode: 27, bubbles: true}));"
            )
        sleep(0.35)


def ensure_dark(driver: webdriver.Chrome) -> None:
    driver.execute_script(
        """
        try { localStorage.setItem('vg_v1_theme', 'dark'); } catch (e) {}
        document.documentElement.setAttribute('data-theme', 'dark');
        """
    )
    try:
        for btn in driver.find_elements(By.CSS_SELECTOR, '[aria-label="Switch to dark mode"]'):
            if btn.is_displayed():
                btn.click()
                sleep(0.45)
                break
    except Exception:
        pass


def wheel_zoom(driver: webdriver.Chrome, delta_y: int, steps: int = 12) -> None:
    pane = driver.find_element(By.CSS_SELECTOR, ".react-flow__pane")
    step = int(delta_y / steps)
    for _ in range(steps):
        driver.execute_script(
            """
            const el = arguments[0];
            el.dispatchEvent(new WheelEvent('wheel', {
              bubbles: true,
              cancelable: true,
              deltaY: arguments[1],
              deltaMode: 0,
            }));
            """,
            pane,
            step,
        )
        sleep(0.055)


def drag_pane(driver: webdriver.Chrome, dx: int, dy: int, substeps: int = 32) -> None:
    pane = driver.find_element(By.CSS_SELECTOR, ".react-flow__pane")
    x0, y0 = -80, 45
    x1, y1 = x0 + dx, y0 + dy
    actions = ActionChains(driver)
    actions.move_to_element(pane).pause(0.15).move_by_offset(x0, y0).click_and_hold()
    px, py = x0, y0
    for i in range(1, substeps + 1):
        t = i / substeps
        ease = t * t * (3 - 2 * t)
        nx = int(x0 + (x1 - x0) * ease)
        ny = int(y0 + (y1 - y0) * ease)
        actions.move_by_offset(nx - px, ny - py).pause(0.016)
        px, py = nx, ny
    actions.release().perform()


def main() -> None:
    if not ZIP_PATH.is_file():
        raise FileNotFoundError(f"Missing {ZIP_PATH} (run: zip -rq demo_project.zip demo_project)")

    opts = Options()
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--window-position=0,0")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-infobars")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    wait = WebDriverWait(driver, 180)

    try:
        driver.get(APP_URL)
        sleep(1.2)
        ensure_dark(driver)
        sleep(1.0)

        try:
            got_it = driver.find_element(By.CSS_SELECTOR, "button.first-steps-dismiss")
            if got_it.is_displayed():
                got_it.click()
                sleep(0.4)
        except Exception:
            pass

        # [0:00–0:05] Empty state hero (dark)
        sleep(2.8)

        # [0:05–0:15] Upload zip
        driver.find_element(
            By.CSS_SELECTOR,
            'button[aria-label="Upload new project for analysis"]',
        ).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".upload-modal")))
        sleep(0.55)

        file_input = driver.find_element(By.CSS_SELECTOR, '.upload-modal input[type="file"]')
        driver.execute_script(
            """
            arguments[0].removeAttribute('webkitdirectory');
            arguments[0].removeAttribute('directory');
            """,
            file_input,
        )
        file_input.send_keys(str(ZIP_PATH.resolve()))

        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Analyzing project')]")))
        sleep(0.8)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".react-flow__node")))
        sleep(5.0)

        pane = driver.find_element(By.CSS_SELECTOR, ".react-flow__pane")

        # [0:15–0:25] Pan / zoom / fetchUserData
        drag_pane(driver, 220, -75)
        sleep(0.55)
        wheel_zoom(driver, -320)
        sleep(0.65)

        node = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(@class,'react-flow__node')]"
                    "[.//*[contains(normalize-space(text()), 'fetchUserData')]]",
                )
            )
        )
        ActionChains(driver).move_to_element(node).pause(0.55).click().perform()
        sleep(1.1)
        dismiss_ai_settings(driver)
        sleep(1.0)

        # [0:25–0:40] Difficulty levels
        for lvl in ("beginner", "intermediate", "advanced"):
            try:
                btn = driver.find_element(
                    By.XPATH,
                    f"//div[@aria-label='Difficulty level']//button[normalize-space()='{lvl}']",
                )
                driver.execute_script("arguments[0].click();", btn)
                sleep(0.4)
                dismiss_ai_settings(driver)
                sleep(2.6)
            except Exception:
                pass

        dismiss_ai_settings(driver)

        # [0:40–0:55] Chat
        driver.find_element(By.CSS_SELECTOR, "button.chat-fab").click()
        sleep(0.75)
        ta = driver.find_element(By.CSS_SELECTOR, "textarea.chat-input")
        ta.clear()
        ta.send_keys("Which function is the best entry point to understand this codebase?")
        sleep(0.45)
        driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Send message"]').click()
        sleep(5.5)
        dismiss_ai_settings(driver)

        driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Close Chat"]').click()
        sleep(0.6)

        # [0:55–1:10] Ghost Runner
        play = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[aria-label="Play simulation"]')))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", play)
        sleep(0.45)
        play.click()
        sleep(20.0)

        # [1:10–1:20] Pause + summary
        driver.find_element(By.CSS_SELECTOR, '[aria-label="Pause simulation"]').click()
        sleep(3.5)

        # [1:20–1:30] Wide shot + visited highlights
        wheel_zoom(driver, -200)
        sleep(0.35)
        drag_pane(driver, -200, 70)
        sleep(4.8)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
