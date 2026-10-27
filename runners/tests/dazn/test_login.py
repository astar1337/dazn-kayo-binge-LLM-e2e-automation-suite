# tests/dazn/login.py

from tests.base_test import BaseTest
from tests.dazn.critera.login import LOGIN_CRITERIA
from utils.prompt_builder import PromptBuilder


class DAZNLogin(BaseTest):
    APP_NAME = "dazn"
    APP_PACKAGE = "com.dazn"
    CREDENTIALS_FILE = "credentials/dazn_creds.yaml"


async def run_valid_login(
    device_id: str,
    vpn_region: str,
    language: str,
    agent_mode: str = "default",
    no_trajectory: bool = False,
):
    test = DAZNLogin(device_id=device_id, vpn_region=vpn_region, language=language)

    pb = PromptBuilder(
        credentials=test._load_credentials(),
        language=language,
    )

    prompt = f"""
You MUST execute each step one at a time on the device.
Do NOT skip steps. Do NOT predict outcomes. Do NOT call complete() until all steps are physically executed.

1. Open app: com.dazn
2. Wait 5s
3. {pb.tap("login_button")}
4. {pb.type_secret("email", "dazn_standard_email_de")}
5. {pb.tap("get_started")}
6. {pb.type_secret("password", "dazn_standard_password1")}
7. {pb.tap("sign_in")}
8. Wait 5s

After all steps: report what tabs are in the bottom navigation bar and any error messages.
Expected tabs: {pb.nav_tabs()}
"""

    return await test.run_test(
        test_id="TC-DAZN-LOGIN-001",
        test_name="Valid Login",
        task_prompt=prompt,
        agent_mode=agent_mode,
        no_trajectory=no_trajectory,
        expected_criteria=LOGIN_CRITERIA,
        max_steps=10,
    )


async def run_invalid_password(device_id: str, vpn_region: str, language: str, agent_mode: str = "default", no_trajectory: bool = False):
    """TC-DAZN-LOGIN-002: Invalid password shows error message."""
    test = DAZNLogin(device_id=device_id, vpn_region=vpn_region, language=language)

    prompt = """

    """

    return await test.run_test(
        test_id="TC-DAZN-LOGIN-002",
        test_name="Invalid Password",
        task_prompt=prompt,
        agent_mode=agent_mode,
        no_trajectory=no_trajectory                
    )


async def run_empty_fields(device_id: str, vpn_region: str, language: str, agent_mode: str = "default",no_trajectory: bool = False):
    """TC-DAZN-LOGIN-003: Empty fields show validation."""
    test = DAZNLogin(device_id=device_id, vpn_region=vpn_region, language=language)

    prompt = """

    """

    return await test.run_test(
        test_id="TC-DAZN-LOGIN-003",
        test_name="Empty Fields Validation",
        task_prompt=prompt,
        agent_mode=agent_mode,
        no_trajectory=no_trajectory

    )


async def run_logout(device_id: str, vpn_region: str, language: str, agent_mode: str = "default",no_trajectory: bool = False):
    """TC-DAZN-LOGIN-004: User can log out successfully."""
    test = DAZNLogin(device_id=device_id, vpn_region=vpn_region, language=language)

    prompt = """
   
    """

    return await test.run_test(
        test_id="TC-DAZN-LOGIN-004",
        test_name="Logout Flow",
        task_prompt=prompt,
        agent_mode=agent_mode,
        no_trajectory=no_trajectory
    )