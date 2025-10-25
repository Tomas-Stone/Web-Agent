"""Configuration for test sites and agent settings"""

from dataclasses import dataclass
from typing import List

@dataclass
class TestSite:
    """Represents a website we can test on"""
    name: str
    url: str
    category: str
    sample_tasks: List[str]

# Test sites for different categories
TEST_SITES = [
    # Shopping
    TestSite(
        name="Amazon",
        url="https://www.amazon.com",
        category="shopping",
        sample_tasks=[
            "Search for wireless mouse",
            "Navigate to Electronics category",
        ]
    ),
    
    # E-commerce
    TestSite(
        name="Kelbillet",
        url="https://www.kelbillet.com/",
        category="ticket_booking",
        sample_tasks=[
            "Click on the search box to look for an event",
            "Find and click on a concert ticket",
        ]
    ),
    
    # Info search
    TestSite(
        name="Wikipedia",
        url="https://www.wikipedia.org",
        category="info_search",
        sample_tasks=[
            "Search for Artificial Intelligence",
            "Click on the English Wikipedia",
        ]
    ),
    TestSite(
        name="Google",
        url="https://www.google.com",
        category="info_search",
        sample_tasks=[
            "Search for Python tutorial",
        ]
    ),
    
    # Simple demos for testing
    TestSite(
        name="Example",
        url="https://example.com",
        category="demo",
        sample_tasks=[
            "Find the 'More information' link",
        ]
    ),
]

# Browser settings
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720
TIMEOUT_MS = 60000  # 60 seconds

# Agent settings
MAX_STEPS = 15
