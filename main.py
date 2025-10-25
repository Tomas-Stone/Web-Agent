#!/usr/bin/env python3
"""
Web Agent - Main entry point

Usage:
  python main.py task <site> <task>           # Run single task
  python main.py list                         # List available sites
  python main.py demo                         # Quick demo
"""

import asyncio
import sys
from pathlib import Path
import json
from datetime import datetime

from agent import WebAgent
from config import TEST_SITES

async def run_task(site_name: str, task: str, headless: bool = False, record_video: bool = True):
    """Run a single task on a site"""
    
    # Find the site
    site = next((s for s in TEST_SITES if s.name.lower() == site_name.lower()), None)
    if not site:
        print(f"❌ Site '{site_name}' not found")
        print(f"\nAvailable sites: {', '.join(s.name for s in TEST_SITES)}")
        print(f"Run 'python main.py list' to see all sites")
        return
    
    # Create save directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = Path(f"runs/{site_name.lower()}_{timestamp}")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize and run agent
    agent = WebAgent(headless=headless, record_video=record_video)
    await agent.start(video_dir=save_dir if record_video else None)
    
    try:
        result = await agent.run_task(site.url, task, save_dir)
        
        # Stop agent and get video path
        video_path = await agent.stop()
        
        # Move video to a better name if it exists
        final_video_path = None
        if video_path and video_path.exists():
            final_video_path = save_dir / "agent_recording.webm"
            video_path.rename(final_video_path)
            result["video_path"] = str(final_video_path)
            print(f"\n🎥 Video saved: {final_video_path}")
        
        # Save result
        with open(save_dir / "result.json", "w") as f:
            json.dump({
                "site": site.name,
                "url": site.url,
                "task": task,
                "timestamp": timestamp,
                **result
            }, f, indent=2)
        
        # Print summary
        print(f"\n{'='*70}")
        print("📊 SUMMARY")
        print(f"{'='*70}")
        print(f"Success: {'✅ Yes' if result['success'] else '❌ No'}")
        print(f"Steps taken: {result['steps']}")
        if not result['success'] and 'error' in result:
            print(f"Error: {result['error']}")
        print(f"Results saved: {save_dir}")
        if final_video_path:
            print(f"Video: {final_video_path}")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await agent.stop()

def list_sites():
    """Display all available test sites"""
    print("\n" + "="*70)
    print("🌐 AVAILABLE TEST SITES")
    print("="*70 + "\n")
    
    by_category = {}
    for site in TEST_SITES:
        if site.category not in by_category:
            by_category[site.category] = []
        by_category[site.category].append(site)
    
    for category, sites in by_category.items():
        print(f"📁 {category.upper().replace('_', ' ')}")
        for site in sites:
            print(f"\n  • {site.name}")
            print(f"    URL: {site.url}")
            print(f"    Sample tasks:")
            for task in site.sample_tasks:
                print(f"      - {task}")
        print()
    
    print("="*70)
    print("\nUsage: python main.py task <site_name> \"<task_description>\"")
    print("Example: python main.py task Wikipedia \"Search for Python\"")
    print("="*70 + "\n")

async def run_demo():
    """Quick demo on Kelbillet"""
    print("\n🚀 Running quick demo on Kelbillet...\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = Path(f"runs/demo_{timestamp}")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    agent = WebAgent(headless=False, record_video=True)
    await agent.start(video_dir=save_dir)
    
    try:
        result = await agent.run_task(
            url="https://www.kelbillet.com/",
            task="Find and click on the search box to look for tickets",
            save_dir=save_dir
        )
        
        # Stop agent and get video
        video_path = await agent.stop()
        
        # Move video to better name
        if video_path and video_path.exists():
            final_video_path = save_dir / "demo_recording.webm"
            video_path.rename(final_video_path)
            result["video_path"] = str(final_video_path)
            print(f"\n🎥 Video saved: {final_video_path}")
        
        # Save result
        with open(save_dir / "result.json", "w") as f:
            json.dump({
                "demo": True,
                "site": "Kelbillet",
                "url": "https://www.kelbillet.com/",
                "timestamp": timestamp,
                **result
            }, f, indent=2)
        
        print(f"\n✅ Demo complete! Results in {save_dir}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await agent.stop()

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_sites()
    
    elif command == "demo":
        asyncio.run(run_demo())
    
    elif command == "task":
        if len(sys.argv) < 4:
            print("Usage: python main.py task <site_name> \"<task_description>\"")
            print("Example: python main.py task Wikipedia \"Search for AI\"")
            return
        
        site_name = sys.argv[2]
        task = sys.argv[3]
        headless = "--headless" in sys.argv
        no_video = "--no-video" in sys.argv
        
        asyncio.run(run_task(site_name, task, headless, record_video=not no_video))
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()
