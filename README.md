DAZN, Kayo & Binge E2E Testing Suite
Robust end-to-end testing using DroidRun and LLMs.
Setup
python -m venv venv
source venv/bin/activate (or venv\Scripts\activate on Windows)
pip install -r requirements.txt
Update .env with your OpenAI API key and device ID.
Update credentials/dazn_creds.yaml with test accounts.
Run Tests
python -m runners.test_runner
