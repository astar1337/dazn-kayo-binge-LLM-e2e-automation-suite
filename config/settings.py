import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class LLMSettings:
    provider: str = os.getenv("LLM_PROVIDER", "OpenRouter")
    model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    temperature: float = 0.0
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    #LOCAL LLM SETTINGS#
    local_llm_base_url: str = os.getenv("LOCAL_LLM_BASE_URL", "http://192.168.x.x:8000/v1")
    local_llm_api_key: str = os.getenv("LOCAL_LLM_API_KEY", "not-needed")
    local_llm_model: str = os.getenv("LOCAL_LLM_MODEL", "your-model-name")



@dataclass
class AgentSettings:
    max_steps: int = int(os.getenv("DROIDRUN_MAX_STEPS", "10"))
    reasoning: bool = os.getenv("DROIDRUN_REASONING", "true").lower() == "true"
    after_sleep_action: float = float(os.getenv("DROIDRUN_AFTER_SLEEP_ACTION", "1.5"))
    fast_agent_vision: bool = os.getenv("DROIDRUN_FAST_AGENT_VISION", "true").lower() == "true"


@dataclass
class DeviceSettings:
    serial: str = os.getenv("DROIDRUN_DEVICE_SERIAL", "auto")
    platform: str = os.getenv("DROIDRUN_PLATFORM", "android")
    use_tcp: bool = os.getenv("DROIDRUN_USE_TCP", "false").lower() == "true"


@dataclass
class LogSettings:
    debug: bool = os.getenv("DROIDRUN_DEBUG", "true").lower() == "true"
    save_trajectory: str = os.getenv("DROIDRUN_SAVE_TRAJECTORY", "action")
    trajectory_gifs: bool = os.getenv("DROIDRUN_TRAJECTORY_GIFS", "true").lower() == "true"


@dataclass
class TestConfig:
    report_dir: str = os.getenv("REPORT_DIR", "./reports")
    retry_count: int = int(os.getenv("TEST_RETRY_COUNT", "1"))


llm_settings = LLMSettings()
agent_settings = AgentSettings()
device_settings = DeviceSettings()
log_settings = LogSettings()
test_config = TestConfig()
device_config = device_settings

@dataclass
class TestRailSettings:
    enabled: bool = os.getenv("TESTRAIL_ENABLED", "false").lower() == "true"
    url: str = os.getenv("TESTRAIL_URL", "")
    email: str = os.getenv("TESTRAIL_EMAIL", "")
    api_key: str = os.getenv("TESTRAIL_API_KEY", "")
    project_id: int = int(os.getenv("TESTRAIL_PROJECT_ID", "1"))
    suite_id: int = int(os.getenv("TESTRAIL_SUITE_ID", "1"))
    
testrail_settings = TestRailSettings()