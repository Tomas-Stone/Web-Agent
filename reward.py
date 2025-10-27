"""Reward model to evaluate agent actions"""

import os
import base64
import requests
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()

class RewardModel:
    """
    Evaluates whether an action moved closer to the goal.
    Uses a vision-language model to judge progress.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY required")
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        # Using same model for consistency
        self.model = "qwen/qwen2.5-vl-32b-instruct:free"
    
    def judge_action(
        self,
        screenshot_before: bytes,
        action_taken: str,
        screenshot_after: bytes,
        task: str,
        url_before: str,
        url_after: str
    ) -> Tuple[float, str]:
        """
        Judge if action helped accomplish the task.
        
        Args:
            screenshot_before: Screenshot before action
            action_taken: The action that was executed
            screenshot_after: Screenshot after action
            task: The overall task/goal
            url_before: URL before action
            url_after: URL after action
            
        Returns:
            (reward, explanation)
            reward: +1.0 (good progress), 0.0 (no change), -1.0 (bad/regress)
            explanation: Why this reward was given
        """
        
        # Encode screenshots
        before_b64 = base64.b64encode(screenshot_before).decode('utf-8')
        after_b64 = base64.b64encode(screenshot_after).decode('utf-8')
        
        system_prompt = self._build_system_prompt()
        user_message = self._build_user_message(
            action_taken, task, url_before, url_after
        )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "BEFORE action:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{before_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": user_message
                        },
                        {
                            "type": "text",
                            "text": "AFTER action:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{after_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Now judge the action and provide your reward and explanation."
                        }
                    ]
                }
            ],
            "max_tokens": 300,
            "temperature": 0.3,  # Lower temperature for more consistent judging
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            judgment = result["choices"][0]["message"]["content"]
            
            # Parse reward and explanation
            reward, explanation = self._parse_judgment(judgment)
            return reward, explanation
            
        except Exception as e:
            # On error, return neutral reward
            return 0.0, f"Error judging action: {str(e)}"
    
    def _build_system_prompt(self) -> str:
        """System prompt for the reward model"""
        return """You are a reward model that judges web navigation actions.

Your job: Compare two screenshots (BEFORE and AFTER an action) and judge if the action helped accomplish the task.

REWARD SCALE:
+1.0 = GOOD - Action clearly moved toward the goal (new page loaded, form filled, search executed, etc.)
 0.0 = NEUTRAL - Action did nothing visible or result unclear
-1.0 = BAD - Action moved away from goal (wrong click, error page, closed useful popup, etc.)

OUTPUT FORMAT (must follow exactly):
Reward: [+1.0 or 0.0 or -1.0]
Explanation: <brief 1-2 sentence explanation>

GUIDELINES:
- Compare the two screenshots carefully
- Did the page change meaningfully?
- Did we get closer to completing the task?
- Repeated identical actions are usually BAD (-1.0)
- Closing cookie popups is GOOD (+1.0) if it reveals the main content
- Clicking a search box is GOOD (+1.0) if it activates/focuses it
- If nothing changed between screenshots, give 0.0"""

    def _build_user_message(
        self, 
        action: str, 
        task: str, 
        url_before: str, 
        url_after: str
    ) -> str:
        """Build user message with context"""
        url_changed = "✓ URL changed" if url_before != url_after else "✗ URL same"
        
        return f"""TASK: {task}

ACTION TAKEN: {action}

URL: {url_changed}
- Before: {url_before}
- After: {url_after}

Look at both screenshots and judge if this action helped accomplish the task."""

    def _parse_judgment(self, judgment: str) -> Tuple[float, str]:
        """Parse reward and explanation from model output"""
        
        reward = 0.0
        explanation = judgment.strip()
        
        # Try to extract reward value
        if "Reward:" in judgment:
            lines = judgment.split('\n')
            for line in lines:
                if line.strip().startswith("Reward:"):
                    reward_text = line.split("Reward:")[1].strip()
                    # Parse +1.0, 0.0, -1.0
                    if "+1" in reward_text or "1.0" in reward_text and "+" in reward_text:
                        reward = 1.0
                    elif "-1" in reward_text or "1.0" in reward_text and "-" in reward_text:
                        reward = -1.0
                    else:
                        reward = 0.0
                elif line.strip().startswith("Explanation:"):
                    explanation = line.split("Explanation:")[1].strip()
                    break
        
        return reward, explanation
