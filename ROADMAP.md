Web-Agent roadmap (concise, actionable)

This document gives a practical plan to move the project from the current MVP (vision-only agent + OpenRouter Qwen 2.5 VL, Playwright automation, simple reward model) to a production-capable self-improving web agent and dataset producer.

1. Goals (what success looks like)
- Build a robust vision-only web agent that can perform multi-step tasks on a small set of sites (shopping, search, ticketing).
- Provide safe, repeatable data collection of trajectories with action + screenshots + reward labels.
- Produce a training loop that allows self-improvement (BC bootstrap → reward supervision → policy optimization).

2. Current MVP (what exists now)
- Playwright-based `BrowserController` capturing screenshots, executing actions.
- `VisionLanguageModel` client to OpenRouter Qwen 2.5 VL (`inference.py`).
- Action parsing (`actions.py`) and combined `type(x,y,"text")` primitive.
- `agent.py` orchestrator, video recording, simple interactive mode.
- `reward.py` reward-judging model that compares before/after screenshots.

3. Minimal architecture (MVP -> production path)
- Components:
	- Browser sandbox (Playwright) — safe, resettable environment for running tasks.
	- Policy (VLM) — inputs: screenshot + task + history → outputs: CoT + single action.
	- Action parser & executor — normalizes actions (click/type/scroll/press/wait/finish/fail).
	- Reward model (VLM) — judges transitions and provides scalar reward + explanation.
	- Data store — trajectory records: [{state_t (png), action_t, state_t+1 (png), url_t, url_t+1, reward, metadata}].

4. Trajectory & dataset format (simple, actionable)
- Each trajectory step (JSON):
	- step, timestamp
	- state_before: path to PNG
	- action: {type, params, thought}
	- state_after: path to PNG
	- url_before, url_after
	- reward: float, reward_explanation

5. Training plan (three stages)
- Stage A — Behavior cloning (bootstrap)
	- Collect human or scripted demonstrations (1k–5k trajectories).
	- Fine-tune the VLM (or train small policy head / LoRA) to output actions from screenshot+task.
	- Goal: reach workable baseline (search, simple form fill).

- Stage B — Reward model & automated judging
	- Use `reward.py` to auto-label agent rollouts and produce preference pairs.
	- Periodically sample for human verification (5–10% of labels) to keep RM calibrated.

- Stage C — Policy improvement (DPO / PPO / offline RL)
	- Use DPO for stability (requires preference pairs) or PPO with RM as reward.
	- Use replay buffer with BC examples to avoid forgetting.
	- Add exploration bonuses (novelty, coverage) to encourage diverse data.

6. Evaluation & metrics
- Task success rate (per-task + aggregated)
- Step-wise correctness (per-action precision)
- Sample efficiency (trajectories per % improvement)
- Reward model calibration (AUC vs human labels)
- Safety checks: fraction of sessions with unexpected navigation / loop detection

7. Milestones (12-week plan, small team / single dev friendly)
- Week 0 (this week): Clean MVP, demo scripts, video recording, ensure dataset format (DONE)
- Week 1–2: Collect 1k seeded trajectories (mix of scripted, human, agent rollouts) and run BC training (LoRA).
- Week 3–4: Train/validate reward model. Add human verification UI for sampled pairs.
- Week 5–8: Run policy improvement cycles (DPO / offline RL). Add curriculum for tasks of increasing difficulty.
- Week 9–12: Scale: broaden site variety, increase demonstration count, prepare public dataset snapshot and simple baseline models.

8. Short-term improvements (low-risk, high-value)
- Add Set-of-Marks (SoM): overlay candidate element boxes from a lightweight detector so the model can output element IDs instead of raw coordinates.
- Improve prompts with few-shot CoT examples showing clicks/typing sequences and correct coordinate conventions.
- Add loop-detection and simple heuristics to penalize repeated identical actions (reduce stuck behavior).

9. Risks & mitigations
- Reward model drift / reward hacking — mitigation: human-in-the-loop sampling, conservative policy updates, keep BC buffer.
- Compute cost — mitigation: LoRA/adapter tuning, offline RL (less rollouts), narrow site distribution for early iterations.
- Model hallucinations (wrong coordinates) — mitigation: validate coordinates against viewport, optional element detector fallback.

10. How to run the current MVP (quick)
- Install deps and Playwright: see `requirements.txt` and run:
```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# add OPENROUTER_API_KEY in .env
```
- Demo (Kelbillet) with video:
```bash
python main.py demo
```
- Run a task with reward judging and interactive hints:
```bash
python main.py task Wikipedia "Search for Machine Learning" --reward --interactive
```

11. Files to look at (quick map)
- `main.py` — CLI & demo harness
- `agent.py` — orchestration loop, interactive options, reward integration
- `browser.py` — Playwright controller + video
- `inference.py` — VLM client (OpenRouter / Qwen 2.5 VL)
- `reward.py` — judgment model
- `actions.py` — parsing actions and `type(x,y,text)` primitive

12. Next steps (actionable tasks for next sprint)
- Collect 1k clean trajectories (scripted + human).  (owner: you)
- Add an element detector / SoM overlay and adjust prompt to prefer element IDs.  (owner: small PR)
- Implement human annotation UI for sampled rollouts (to validate RM).  (owner: optional)

If you want, I can now:
- (A) Replace this roadmap with an even more detailed week-by-week checklist and explicit commands for training loops and validation (include sample scripts), or
- (B) Start the collection script to gather 100–500 seed trajectories from the current MVP and save them in the trajectory format above.

Tell me which next step you prefer and I will execute it.

---

Last edit: concise, actionable roadmap to guide the next 12 weeks and convert the current prototype into a training-ready project.