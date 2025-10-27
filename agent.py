"""Main web agent orchestrator"""

import asyncio
from typing import List, Optional, Dict
from pathlib import Path
import json
from datetime import datetime
import shutil
import sys
import select

from browser import BrowserController
from inference import VisionLanguageModel
from reward import RewardModel
from actions import ActionParser, Action, ActionType
from config import VIEWPORT_WIDTH, VIEWPORT_HEIGHT, MAX_STEPS

class WebAgent:
    """Autonomous web navigation agent"""
    
    def __init__(self, headless: bool = False, record_video: bool = False, interactive: bool = False, use_reward_model: bool = False):
        self.browser = BrowserController()
        self.model = VisionLanguageModel()
        self.reward_model = RewardModel() if use_reward_model else None
        self.headless = headless
        self.record_video = record_video
        self.interactive = interactive
        self.use_reward_model = use_reward_model
        self.history: List[str] = []
        self.user_hints: List[str] = []
        
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
        
        # Track previous state for reward model
        prev_screenshot = None
        prev_url = None
        
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
            
            # Check for user input in interactive mode
            user_hint = None
            if self.interactive:
                print("\n💬 You can provide a hint (or press Enter to skip): ", end='', flush=True)
                
                # Non-blocking input check with timeout
                import sys
                import select
                
                # Wait up to 3 seconds for input
                if sys.platform != 'win32':
                    rlist, _, _ = select.select([sys.stdin], [], [], 3.0)
                    if rlist:
                        user_hint = sys.stdin.readline().strip()
                else:
                    # Windows fallback - just wait for input
                    import threading
                    user_input = []
                    
                    def get_input():
                        user_input.append(input())
                    
                    input_thread = threading.Thread(target=get_input)
                    input_thread.daemon = True
                    input_thread.start()
                    input_thread.join(timeout=3.0)
                    
                    if user_input:
                        user_hint = user_input[0].strip()
                    else:
                        print()  # New line if no input
                
                if user_hint:
                    self.user_hints.append(user_hint)
                    print(f"✅ Hint received: {user_hint}")
            
            # Get model prediction
            print("🤔 Thinking...")
            try:
                response = self.model.predict_action(
                    screenshot=screenshot,
                    task=task,
                    history=self.history,
                    url=current_url,
                    user_hint=user_hint
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
            
            # Get reward if enabled
            reward = None
            reward_explanation = None
            
            if exec_success:
                # Wait for page to settle
                await asyncio.sleep(1)
                
                # Get new state for reward model
                new_screenshot = await self.browser.get_screenshot()
                new_url = await self.browser.get_current_url()
                
                # Judge action with reward model
                if self.use_reward_model and prev_screenshot is not None:
                    try:
                        print("⚖️  Judging action...")
                        reward, reward_explanation = self.reward_model.judge_action(
                            screenshot_before=prev_screenshot,
                            action_taken=str(action),
                            screenshot_after=new_screenshot,
                            task=task,
                            url_before=prev_url,
                            url_after=new_url
                        )
                        
                        # Display reward
                        if reward > 0:
                            print(f"🟢 Reward: +{reward} - {reward_explanation}")
                        elif reward < 0:
                            print(f"🔴 Reward: {reward} - {reward_explanation}")
                        else:
                            print(f"⚪ Reward: {reward} - {reward_explanation}")
                    except Exception as e:
                        print(f"⚠️  Reward model error: {e}")
                        reward = 0.0
                        reward_explanation = "Error in judgment"
                
                # Update previous state
                prev_screenshot = new_screenshot
                prev_url = new_url
                
                # Add to history
                self.history.append(f"{action} - {action.reasoning}")
                
                # Save to trajectory
                step_data = {
                    "step": step,
                    "action": str(action),
                    "reasoning": action.reasoning,
                    "url": current_url,
                    "result": exec_msg
                }
                if reward is not None:
                    step_data["reward"] = reward
                    step_data["reward_explanation"] = reward_explanation
                
                trajectory.append(step_data)
            else:
                # Action failed, update state anyway
                prev_screenshot = screenshot
                prev_url = current_url
        
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
