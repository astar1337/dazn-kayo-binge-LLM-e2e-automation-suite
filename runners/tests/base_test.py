import os
import subprocess
import yaml
from typing import Optional

from droidrun import (
    DroidAgent,
    DroidConfig,
    AgentConfig,
    FastAgentConfig,
    DeviceConfig,
    LoggingConfig,
    AppCardConfig,
    CredentialsConfig,
    ManagerConfig,
)
from config.settings import llm_settings, agent_settings, device_settings, log_settings
from models.test_results import TestCaseResult, TestStatus
from models.test_results import ExpectedCriteria

class BaseTest:
    APP_NAME: str = ""
    APP_PACKAGE: str = ""
    CREDENTIALS_FILE: str = ""

    def __init__(self, device_id: str, vpn_region: str = "de", language: str = "en_de"):
        self.device_id = device_id
        self.vpn_region = vpn_region
        self.language = language
        self.app_cards_dir = f"app_cards/{self.APP_NAME}/{self.vpn_region}"

        # Build LLMs based on provider
        self.standard_llm = self._build_llm()
        self.executor_llm = self._build_executor_llm()

    def _build_llm(self):
        """
        Builds the standard LLM based on the provider setting.
        Supports OpenAI, OpenRouter, and Anthropic.
        """
        if llm_settings.provider == "OpenRouter":
            from llama_index.llms.openai_like import OpenAILike

            return OpenAILike(
                model=llm_settings.model,
                api_key=llm_settings.openrouter_api_key,
                api_base=llm_settings.openrouter_base_url,
                temperature=llm_settings.temperature,
                max_tokens=llm_settings.max_tokens,
                is_chat_model=True,

            )
        elif llm_settings.provider == "OpenAI":
            from llama_index.llms.openai import OpenAI as LlamaOpenAI

            return LlamaOpenAI(
                model=llm_settings.model,
                api_key=llm_settings.openai_api_key,
                temperature=llm_settings.temperature,
                max_tokens=llm_settings.max_tokens,    
            )
        elif llm_settings.provider == "Anthropic":
            from llama_index.llms.anthropic import Anthropic

            return Anthropic(
                model=llm_settings.model,
                api_key=llm_settings.anthropic_api_key,
                temperature=llm_settings.temperature,
                max_tokens=llm_settings.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_settings.provider}")
    
    def _build_executor_llm(self):
        """Builds the executor LLM — uses VisionAwareOpenAI for OpenAI provider."""
        if llm_settings.provider == "OpenAI":
            from utils.llm_interceptor import VisionAwareOpenAI
            return VisionAwareOpenAI(
                model=llm_settings.model,
                api_key=llm_settings.openai_api_key,
                temperature=llm_settings.temperature,
            )
        return self._build_llm()
    
    def _get_device_serial(self) -> Optional[str]:
        """Returns the device serial. If 'auto', detects first available ADB device."""
        serial = self.device_id
        if serial == "auto":
            try:
                result = subprocess.run(
                    ["adb", "devices"], capture_output=True, text=True, check=True
                )
                lines = result.stdout.strip().split("\n")
                for line in lines[1:]:
                    if line.strip() and line.endswith("device"):
                        return line.split("\t")[0]
            except Exception:
                pass
            return None
        return serial

    def _load_credentials(self) -> dict:
        """Loads credentials from YAML file."""
        if self.CREDENTIALS_FILE and os.path.exists(self.CREDENTIALS_FILE):
            with open(self.CREDENTIALS_FILE, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _resolve_agent_mode(self, agent_mode: str = "default"):
        """Maps agent mode string to reasoning and vision settings."""
        if agent_mode == "fast":
            return False, False
        elif agent_mode == "manager":
            return True, False
        else:
            return None, None

    def _build_llms_dict(self) -> dict:
        return {
            "manager": self.standard_llm,
            "executor": self.executor_llm,
            "fast_agent": self.standard_llm,
            "text_manipulator": self.standard_llm,
            "app_opener": self.standard_llm,
            "scripter": self.standard_llm,
            "structured_output": self.standard_llm,
        }

    def _build_config(
        self,
        reasoning: bool = None,
        fast_agent_vision: bool = None,
        no_trajectory: bool = False,
        max_steps: int = None,
    ) -> DroidConfig:
        serial = self._get_device_serial()

        if no_trajectory:
            save_trajectory = "none"
            trajectory_gifs = False
        else:
            save_trajectory = log_settings.save_trajectory
            trajectory_gifs = log_settings.trajectory_gifs

        return DroidConfig(
            agent=AgentConfig(
                max_steps=max_steps if max_steps else agent_settings.max_steps,
                reasoning=reasoning,
                streaming=True,
                after_sleep_action=agent_settings.after_sleep_action,
                fast_agent=FastAgentConfig(
                    vision=fast_agent_vision,
                ),
                manager=ManagerConfig(
                    stateless=False,
                    vision=False,
                ),
                app_cards=AppCardConfig(
                    enabled=True,
                    mode="local",
                    app_cards_dir=self.app_cards_dir,
                ),
            ),
            device=DeviceConfig(
                serial=serial,
                platform=device_settings.platform,
                use_tcp=device_settings.use_tcp,
            ),
            logging=LoggingConfig(
                debug=log_settings.debug,
                save_trajectory=save_trajectory,
                trajectory_gifs=trajectory_gifs,
            ),
            credentials=CredentialsConfig(
                enabled=True,
                file_path=self.CREDENTIALS_FILE,
            ),
        )

    async def run_test(
        self,
        test_id: str,
        test_name: str,
        task_prompt: str,
        agent_mode: str = "default",
        no_trajectory: bool = False,
        expected_criteria: ExpectedCriteria = None,
        max_steps: int = None,
        ) -> TestCaseResult:
        formatted_task = f"[{test_id}] {test_name}\n\n{task_prompt}"
        if expected_criteria:
            criteria_prompt = "\n\nVALIDATION CRITERIA (you MUST address each in observations):"
            if expected_criteria.required_elements:
                elements = ", ".join(e.element for e in expected_criteria.required_elements)
                criteria_prompt += f"\n  Required elements (MUST be visible): {elements}"
            if expected_criteria.forbidden_elements:
                elements = ", ".join(e.element for e in expected_criteria.forbidden_elements)
                criteria_prompt += f"\n  Forbidden elements (must NOT be visible): {elements}"
            if expected_criteria.required_state:
                criteria_prompt += f"\n  Expected state: {expected_criteria.required_state}"
            formatted_task += criteria_prompt

        reasoning, fast_agent_vision = self._resolve_agent_mode(agent_mode)
        try:
            use_reasoning = (
                reasoning if reasoning is not None else agent_settings.reasoning
            )
            if fast_agent_vision is not None:
                use_vision = fast_agent_vision
            elif use_reasoning is False:
                use_vision = False
            else:
                use_vision = agent_settings.fast_agent_vision

            config = self._build_config(
                reasoning=use_reasoning,
                fast_agent_vision=use_vision,
                no_trajectory=no_trajectory,
                max_steps=max_steps,
            )

            agent = DroidAgent(
                goal=formatted_task,
                config=config,
                llms=self._build_llms_dict(),
                credentials=self._load_credentials(),
                output_model=TestCaseResult,
                timeout=1500,
            )

            result = await agent.run()

            parsed = None

            if hasattr(result, 'structured_output') and result.structured_output is not None:
                parsed = result
                if isinstance(result.structured_output, TestCaseResult):
                    data = result.structured_output.model_dump()
                    data.pop('expected_criteria', None)
                    parsed = result.structured_output
                elif isinstance(result.structured_output, dict):
                    result.structured_output.pop('expected_criteria', None)
                    parsed = TestCaseResult(**result.structured_output)

            elif isinstance(result, TestCaseResult):
                parsed = result
            elif isinstance(result, dict):
                result.pop('expected_criteria', None)
                parsed = TestCaseResult(**result)

            if parsed is None:
                parsed = TestCaseResult(
                    test_id=test_id,
                    test_name=test_name,
                    status=TestStatus.PASSED if getattr(result, 'success', False) else TestStatus.FAILED,
                    assertion_passed=getattr(result, 'success', False),
                    failure_reason=None if getattr(result, 'success', False) else getattr(result, 'reason', None),
                    observations=str(getattr(result, 'reason', '') or 'No observations available from agent.'),
                )

            # Always inject YOUR criteria and force correct test_id/test_name
            if expected_criteria:
                parsed.expected_criteria = expected_criteria
                parsed = TestCaseResult(**parsed.model_dump())

            parsed.test_id = test_id
            parsed.test_name = test_name

            return parsed

        except Exception as e:
            return TestCaseResult(
                test_id=test_id,
                test_name=test_name,
                status=TestStatus.ERROR,
                assertion_passed=False,
                failure_reason=str(e),
                observations="Agent crashed during test execution.",
            )
