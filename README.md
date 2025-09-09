Minimal Flet UVX Splash Launcher

Run a step-by-step preflight to ensure uv, git, and target repo are available, then execute a uvx command.

Usage
python main.py

Configuration (hardcoded in main.py)
- SHOW_CONSOLE: true to launch in separate terminal window, false to run silently

Flow
1. Check uv (offer install via official script)
2. Check git (offer install via winget if available)
3. Probe repository reachability (git ls-remote)
4. Launch uvx (prefers nocache when repo reachable; falls back to cached run otherwise)

If repo unreachable and cached launch fails, an error is shown with contact info.

All logic kept intentionally minimal per project style instructions.
