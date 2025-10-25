# Web Agent 🤖

A minimal web navigation agent powered by vision-language models. The agent takes screenshots, reasons about what to do, and executes actions on websites.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Get Free API Key
1. Go to [OpenRouter](https://openrouter.ai/)
2. Sign up for free account
3. Get your API key
4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add: OPENROUTER_API_KEY=your_key_here
```

### 3. Run Demo
```bash
# Quick demo on Google Flights (with video recording!)
python main.py demo

# Run a task on Wikipedia
python main.py task Wikipedia "Search for Artificial Intelligence"

# List all available test sites
python main.py list

# Run without video recording
python main.py task Wikipedia "Search for AI" --no-video
```

## How It Works

```
Screenshot → Vision-Language Model → Action → Execute → Repeat
```

1. **Browser** captures screenshot of webpage (1280x720)
2. **Model** (Qwen 2.5 VL) sees screenshot + task, outputs next action
3. **Parser** extracts structured action (click, type, scroll, etc.)
4. **Browser** executes action on page
5. Repeat until task complete or max steps reached

## Project Structure

```
web_agent/
├── main.py          # Entry point - run tasks here
├── agent.py         # Main orchestrator (connects all pieces)
├── browser.py       # Playwright automation
├── inference.py     # OpenRouter API client
├── actions.py       # Action parsing & validation
├── config.py        # Test sites configuration
├── requirements.txt # Dependencies
└── .env            # Your API key (create from .env.example)
```

## Available Actions

- `click(x, y)` - Click at coordinates
- `type("text")` - Type text
- `scroll(direction, amount)` - Scroll up/down
- `wait(seconds)` - Wait
- `press("key")` - Press Enter, Tab, etc.
- `finish()` - Task complete
- `fail("reason")` - Cannot complete

## Test Sites

- **Shopping**: Amazon, eBay
- **Info Search**: Wikipedia, Google
- **Demo**: example.com (simple test site)

See all sites: `python main.py list`

## Output

Each run creates a folder in `runs/` with:
- 🎥 **Video recording** (`agent_recording.webm` or `demo_recording.webm`)
- Screenshots for each step (`step_01.png`, `step_02.png`, ...)
- `result.json` with full trajectory and outcome

## Examples

```bash
# Search on Wikipedia (show browser)
python main.py task Wikipedia "Search for Machine Learning"

# Amazon search (headless mode)
python main.py task Amazon "Search for laptop" --headless

# Google search
python main.py task Google "Search for Python tutorial"
```

## Next Steps

- [ ] Add more test sites
- [ ] Improve prompting with few-shot examples
- [ ] Add element highlighting (Set-of-Marks)
- [ ] Collect trajectories for training dataset
- [ ] Implement reward model for RL training

## Model

Currently using **Qwen 2.5 VL 7B** (free via OpenRouter). Easy to swap for other models:
- Edit `inference.py` → change `self.model` variable
- Try: `anthropic/claude-3.5-sonnet`, `google/gemini-flash-1.5-8b`, etc.