"""OpenRouter API client for Qwen 2.5 VL"""

import os
import base64
import requests
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

class VisionLanguageModel:
    """Client for Qwen 2.5 VL via OpenRouter"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. "
                "Get a free key at https://openrouter.ai/ and add to .env file"
            )
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        # Using Qwen 2.5 VL - free model with vision capabilities
        self.model = "qwen/qwen2.5-vl-32b-instruct:free"
        
    def predict_action(
        self, 
        screenshot: bytes,
        task: str,
        history: List[str],
        url: str
    ) -> str:
        """
        Get next action from vision-language model.
        
        Args:
            screenshot: PNG screenshot bytes
            task: Task to accomplish
            history: Previous actions taken
            url: Current page URL
            
        Returns:
            Model response with thought + action
        """
        
        # Encode screenshot to base64
        screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
        
        # Build prompt
        system_prompt = self._build_system_prompt()
        user_message = self._build_user_message(task, url, history)
        
        # Prepare API request
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
                            "text": user_message
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7,
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected API response format: {str(e)}")
    
    def _build_system_prompt(self) -> str:
        """System prompt defining the agent's behavior"""
        return """You are a web navigation agent. Given a screenshot and a task, output the next action.

AVAILABLE ACTIONS:
- click(x, y): Click at pixel coordinates
- type("text"): Type text into focused element
- scroll(direction, amount): Scroll up/down (amount in pixels, default 500)
- wait(seconds): Wait (max 10 seconds)
- press("key"): Press key (Enter, Tab, Escape, etc.)
- finish(): Task completed successfully
- fail("reason"): Task cannot be completed

OUTPUT FORMAT:
Thought: <brief reasoning about what you see and what to do next>
Action: <single action call>

IMPORTANT:
- Viewport is 1280x720 pixels (coordinates must be within this range)
- Only output ONE action at a time
- Be precise with coordinates - look carefully at the screenshot
- After typing in a search box, remember to press("Enter") to submit

EXAMPLE:
Thought: I can see a search box in the center of the page at approximately (640, 300). I need to click it first.
Action: click(640, 300)"""

    def _build_user_message(self, task: str, url: str, history: List[str]) -> str:
        """User message with task context"""
        
        history_text = "None"
        if history:
            history_text = "\n".join([f"{i+1}. {h}" for i, h in enumerate(history[-5:])])  # Last 5 actions
        
        return f"""TASK: {task}

CURRENT URL: {url}

PREVIOUS ACTIONS:
{history_text}

Look at the screenshot and decide the next action to accomplish the task.
Output your thought process, then a single action."""
