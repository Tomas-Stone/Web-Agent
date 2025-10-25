"""Main web agent orchestrator"""

import asyncio
from typing import List, Optional, Dict
from pathlib import Path
import json
from datetime import datetime
import shutil

from browser import BrowserController
from inference import VisionLanguageModel
from actions import ActionParser, Action, ActionType
from config import VIEWPORT_WIDTH, VIEWPORT_HEIGHT, MAX_STEPS

class WebAgent:
    """Autonomous web navigation agent"""
    
    def __init__(self, headless: bool = False, record_video: bool = False):
        self.browser = BrowserController()
        self.model = VisionLanguageModel()
        self.headless = headless
        self.record_video = record_video
        self.history: List[str] = []
        
    async def start(self, video_dir: Optional[Path] = None):
        """Initialize browser"""
        await self.browser.start(
            headless=self.headless, 
            record_video=self.record_video,
            video_dir=video_dir
        )
        print("✅ Agent ready")
    
    async def stop(self) -> Optional[Path]:
        """Cleanup resources and return video path if recorded"""
        video_path = await self.browser.stop()
        print("✅ Agent stopped")
        return video_path
    
    async def run_task(
        self, 
        url: str, 
        task: str, 
        save_dir: Optional[Path] = None,
        video_path: Optional[Path] = None
    ) -> Dict:
        """
        Execute a task starting from given URL.
        
        Args:
            url: Starting URL
            task: Task description
            save_dir: Directory to save screenshots
            video_path: Path where video was saved (for metadata)
        
        Returns:
            dict with success, steps, trajectory, video_path, etc.
        """
        
        print(f"\n{'='*70}")
        print(f"🎯 TASK: {task}")
        print(f"🌐 URL: {url}")
        print(f"{'='*70}\n")
        
        # Navigate to starting page
        success = await self.browser.navigate(url)
        if not success:
            result = {
                "success": False, 
                "error": "Failed to load page", 
                "steps": 0,
                "trajectory": []
            }
            if video_path:
                result["video_path"] = str(video_path)
            return result
        
        self.history = []
        trajectory = []
        
        # Main agent loop
        for step in range(1, MAX_STEPS + 1):
            print(f"\n{'─'*70}")
            print(f"📍 Step {step}/{MAX_STEPS}")
            print(f"{'─'*70}")
            
            # Capture current state
            screenshot = await self.browser.get_screenshot()
            current_url = await self.browser.get_current_url()
            
            # Save screenshot if requested
            if save_dir:
                save_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = save_dir / f"step_{step:02d}.png"
                with open(screenshot_path, "wb") as f:
                    f.write(screenshot)
                print(f"💾 Saved: {screenshot_path.name}")
            
            # Get model prediction
            print("🤔 Thinking...")
            try:
                response = self.model.predict_action(
                    screenshot=screenshot,
                    task=task,
                    history=self.history,
                    url=current_url
                )
            except Exception as e:
                print(f"❌ Model error: {e}")
                result = {
                    "success": False,
                    "error": f"Model inference failed: {e}",
                    "steps": step - 1,
                    "trajectory": trajectory
                }
                if video_path:
                    result["video_path"] = str(video_path)
                return result
            
            print(f"\n📝 Response:\n{response}\n")
            
            # Parse action from response
            action = ActionParser.parse(response)
            if not action:
                print("⚠️  Could not parse action, skipping...")
                continue
            
            # Validate action
            valid, error_msg = ActionParser.validate_action(
                action, VIEWPORT_WIDTH, VIEWPORT_HEIGHT
            )
            if not valid:
                print(f"⚠️  Invalid action: {error_msg}")
                continue
            
            print(f"🎬 Action: {action}")
            if action.reasoning:
                print(f"💭 Thought: {action.reasoning}")
            
            # Check for terminal actions
            if action.type == ActionType.FINISH:
                print("\n✅ TASK COMPLETED!")
                trajectory.append({
                    "step": step,
                    "action": str(action),
                    "reasoning": action.reasoning,
                    "url": current_url
                })
                result = {
                    "success": True,
                    "steps": step,
                    "trajectory": trajectory
                }
                if video_path:
                    result["video_path"] = str(video_path)
                return result
            
            if action.type == ActionType.FAIL:
                reason = action.params.get("reason", "Unknown")
                print(f"\n❌ TASK FAILED: {reason}")
                trajectory.append({
                    "step": step,
                    "action": str(action),
                    "reasoning": action.reasoning,
                    "url": current_url
                })
                result = {
                    "success": False,
                    "error": reason,
                    "steps": step,
                    "trajectory": trajectory
                }
                if video_path:
                    result["video_path"] = str(video_path)
                return result
            
            # Execute action
            exec_success, exec_msg = await self.browser.execute_action(action)
            status = "✅" if exec_success else "❌"
            print(f"{status} {exec_msg}")
            
            if exec_success:
                # Add to history
                self.history.append(f"{action} - {action.reasoning}")
                trajectory.append({
                    "step": step,
                    "action": str(action),
                    "reasoning": action.reasoning,
                    "url": current_url,
                    "result": exec_msg
                })
            
            # Brief pause between actions
            await asyncio.sleep(1)
        
        # Max steps reached
        print(f"\n⚠️  Reached maximum steps ({MAX_STEPS})")
        result = {
            "success": False,
            "error": f"Max steps ({MAX_STEPS}) exceeded",
            "steps": MAX_STEPS,
            "trajectory": trajectory
        }
        if video_path:
            result["video_path"] = str(video_path)
        return result
