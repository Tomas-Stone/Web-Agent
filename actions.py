"""Action parsing and validation"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    """Available agent actions"""
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    PRESS = "press"
    FINISH = "finish"
    FAIL = "fail"

@dataclass
class Action:
    """Structured action with parameters"""
    type: ActionType
    params: dict
    reasoning: str = ""
    
    def __str__(self):
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.type.value}({params_str})"

class ActionParser:
    """Parse model output text into structured actions"""
    
    # Regex patterns for each action
    PATTERNS = {
        ActionType.CLICK: r"click\((\d+),\s*(\d+)\)",
        ActionType.TYPE: r"type\(['\"](.+?)['\"]\)",
        ActionType.SCROLL: r"scroll\((\w+)(?:,\s*(\d+))?\)",
        ActionType.WAIT: r"wait\((\d+(?:\.\d+)?)\)",
        ActionType.PRESS: r"press\(['\"](\w+)['\"]\)",
        ActionType.FINISH: r"finish\(\)",
        ActionType.FAIL: r"fail\(['\"](.+?)['\"]\)",
    }
    
    @classmethod
    def parse(cls, text: str) -> Optional[Action]:
        """
        Parse action from model output.
        
        Expected format:
        Thought: <reasoning>
        Action: <action_call>
        """
        # Extract reasoning/thought
        reasoning = ""
        thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|$)", text, re.DOTALL | re.IGNORECASE)
        if thought_match:
            reasoning = thought_match.group(1).strip()
        
        # Extract action line
        action_match = re.search(r"Action:\s*(.+?)(?=\n|$)", text, re.IGNORECASE)
        if not action_match:
            return None
        
        action_text = action_match.group(1).strip()
        
        # Try matching each action pattern
        for action_type, pattern in cls.PATTERNS.items():
            match = re.search(pattern, action_text, re.IGNORECASE)
            if match:
                return cls._create_action(action_type, match, reasoning)
        
        return None
    
    @classmethod
    def _create_action(cls, action_type: ActionType, match: re.Match, reasoning: str) -> Action:
        """Build Action object from regex match"""
        
        if action_type == ActionType.CLICK:
            x, y = int(match.group(1)), int(match.group(2))
            return Action(action_type, {"x": x, "y": y}, reasoning)
        
        elif action_type == ActionType.TYPE:
            text = match.group(1)
            return Action(action_type, {"text": text}, reasoning)
        
        elif action_type == ActionType.SCROLL:
            direction = match.group(1).lower()
            amount = int(match.group(2)) if match.group(2) else 500
            return Action(action_type, {"direction": direction, "amount": amount}, reasoning)
        
        elif action_type == ActionType.WAIT:
            seconds = float(match.group(1))
            return Action(action_type, {"seconds": seconds}, reasoning)
        
        elif action_type == ActionType.PRESS:
            key = match.group(1)
            return Action(action_type, {"key": key}, reasoning)
        
        elif action_type == ActionType.FINISH:
            return Action(action_type, {}, reasoning)
        
        elif action_type == ActionType.FAIL:
            reason = match.group(1)
            return Action(action_type, {"reason": reason}, reasoning)
        
        return None
    
    @staticmethod
    def validate_action(action: Action, viewport_width: int, viewport_height: int) -> Tuple[bool, str]:
        """Check if action parameters are valid"""
        
        if action.type == ActionType.CLICK:
            x, y = action.params["x"], action.params["y"]
            if not (0 <= x <= viewport_width and 0 <= y <= viewport_height):
                return False, f"Click coordinates ({x}, {y}) outside viewport {viewport_width}x{viewport_height}"
        
        elif action.type == ActionType.SCROLL:
            if action.params["direction"] not in ["up", "down"]:
                return False, f"Invalid scroll direction: {action.params['direction']}"
        
        elif action.type == ActionType.WAIT:
            if action.params["seconds"] > 10:
                return False, "Wait time too long (max 10s)"
        
        return True, ""
