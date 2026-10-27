# App AI Automation in this example for DAZN / Kayo / Binge LLM E2E Automation Suite

LLM-driven end-to-end test automation for mobile streaming apps (DAZN, Kayo, Binge), built on top of the [Mobilerun](https://github.com/droidrun/mobilerun) agent.

Instead of maintaining brittle selectors and page objects, test scenarios are written in natural language. The agent looks at the screen, decides the next action (tap, type, scroll, etc.) and repeats until the scenario is done or a step limit is hit.

> Unofficial project. Not affiliated with or endorsed by DAZN, Kayo, Binge or Mobilerun.

## How it works

1. A scenario is defined as a plain-language prompt (and optionally a structured output schema for pass/fail checks).
2. The framework connects to an Android device or emulator over ADB.
3. The Mobilerun agent runs the loop: observe the screen, plan, act, repeat.
4. The result is collected and reported as pass/fail with the agent's output.

## Requirements

- Python 3.11 to 3.13 (Mobilerun does not support 3.14 yet)
- [ADB](https://developer.android.com/tools/adb) installed and on your `PATH`
- Android device or emulator with Developer options and USB debugging enabled
- API key for your chosen LLM provider (OpenAI, Anthropic, Gemini, etc.)
- Test accounts for the apps under test

## Setup

```bash
git clone https://github.com/astar1337/dazn-kayo-binge-LLM-e2e-automation-suite.git
cd dazn-kayo-binge-LLM-e2e-automation-suite

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

Install the Mobilerun Portal on the device and configure your LLM provider:

```bash
mobilerun setup
mobilerun configure
```

Create a `.env` file in the project root (never commit it):

```env
# LLM provider key, e.g.
OPENAI_API_KEY=...
GOOGLE_API_KEY=...

# Test account credentials
TEST_USER_EMAIL=...
TEST_USER_PASSWORD=...
```

## Running tests

```bash
# list connected devices
adb devices

# run the suite
<your run command here, e.g. pytest tests/ or python main.py>

# run a single scenario
<your single-scenario command here>
```

## Project structure

```
<fill in, e.g.>
├── scenarios/     # natural-language test scenarios
├── config/        # device and LLM configuration
├── reports/       # run output
└── ...
```

## Writing a scenario

Be specific. Say what to open, what to do, and what the pass condition is.

```text
Open the DAZN app, search for "boxing", open the first result and
confirm the video player starts. Report PASS if playback begins,
otherwise FAIL with the reason.
```

Tips:

- Use vision mode for anything where the UI state matters.
- Set a sensible max step limit so a stuck run does not burn tokens.
- Keep one assertion per scenario so failures are easy to read.

## Known limitations

- LLM runs are non-deterministic. Expect occasional flakiness and review failures before treating them as real bugs.
- Each run costs tokens and is slower than a scripted test.
- DRM-protected video may not render in screenshots on some devices or emulators, which can affect playback checks.

## License

<add license>
