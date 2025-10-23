"""Browser automation using Playwright"""

import asyncio
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Browser, Page

from config import VIEWPORT_WIDTH, VIEWPORT_HEIGHT, TIMEOUT_MS
from actions import Action, ActionType

class BrowserController:
    """Manages web browser for agent interactions"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def start(self, headless: bool = False):
        """Launch browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page(
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
        )
        self.page.set_default_timeout(TIMEOUT_MS)
        
    async def stop(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def navigate(self, url: str) -> bool:
        """Go to URL"""
        try:
            await self.page.goto(url, wait_until="networkidle")
            return True
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            return False
    
    async def get_screenshot(self) -> bytes:
        """Capture current page as PNG bytes"""
        return await self.page.screenshot(type="png", full_page=False)
    
    async def get_current_url(self) -> str:
        """Get current page URL"""
        return self.page.url
    
    async def get_page_title(self) -> str:
        """Get current page title"""
        return await self.page.title()
    
    async def execute_action(self, action: Action) -> Tuple[bool, str]:
        """Execute an action on the page"""
        
        try:
            if action.type == ActionType.CLICK:
                x, y = action.params["x"], action.params["y"]
                await self.page.mouse.click(x, y)
                # Wait for page to settle after click
                await asyncio.sleep(0.5)
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=3000)
                except:
                    pass  # Sometimes page doesn't fully settle, that's ok
                return True, f"Clicked at ({x}, {y})"
            
            elif action.type == ActionType.TYPE:
                text = action.params["text"]
                await self.page.keyboard.type(text, delay=50)  # 50ms between keys
                return True, f"Typed: '{text}'"
            
            elif action.type == ActionType.SCROLL:
                direction = action.params["direction"]
                amount = action.params["amount"]
                delta_y = amount if direction == "down" else -amount
                await self.page.mouse.wheel(0, delta_y)
                await asyncio.sleep(0.3)
                return True, f"Scrolled {direction} {amount}px"
            
            elif action.type == ActionType.WAIT:
                seconds = action.params["seconds"]
                await asyncio.sleep(seconds)
                return True, f"Waited {seconds}s"
            
            elif action.type == ActionType.PRESS:
                key = action.params["key"]
                await self.page.keyboard.press(key)
                await asyncio.sleep(0.3)
                return True, f"Pressed {key}"
            
            elif action.type == ActionType.FINISH:
                return True, "Task complete"
            
            elif action.type == ActionType.FAIL:
                reason = action.params["reason"]
                return True, f"Failed: {reason}"
            
        except Exception as e:
            return False, f"Execution error: {str(e)}"
        
        return False, "Unknown action type"
