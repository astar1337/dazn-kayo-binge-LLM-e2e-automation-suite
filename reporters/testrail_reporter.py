import os
import yaml
import requests
from datetime import datetime
from rich.console import Console
from config.settings import testrail_settings
from models.test_results import TestStatus

console = Console()


class TestRailReporter:
    """Pushes test results to TestRail via their API."""

    STATUS_PASSED = 1
    STATUS_BLOCKED = 2
    STATUS_UNTESTED = 3
    STATUS_RETEST = 4
    STATUS_FAILED = 5

    def __init__(self):
        self.base_url = testrail_settings.url.rstrip("/")
        self.email = testrail_settings.email
        self.api_key = testrail_settings.api_key
        self.project_id = testrail_settings.project_id
        self.suite_id = testrail_settings.suite_id
        self.case_map = self._load_case_map()

    def _load_case_map(self) -> dict:
        """Loads the test ID to TestRail case ID mapping."""
        map_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config",
            "testrail_map.yaml"
        )
        if not os.path.exists(map_file):
            console.print("[yellow]  ⚠️  config/testrail_map.yaml not found[/yellow]")
            return {}

        try:
            with open(map_file, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            console.print(f"[yellow]  ⚠️  Error loading testrail_map.yaml: {e}[/yellow]")
            return {}

    def _api_request(self, method: str, endpoint: str, data: dict = None):
        """Makes an authenticated request to the TestRail API."""
        url = f"{self.base_url}/index.php?/api/v2/{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                auth=(self.email, self.api_key),
                headers={"Content-Type": "application/json"},
                json=data,
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()
            else:
                console.print(f"[red] TestRail API error {response.status_code}: {response.text[:200]}[/red]")
                return None

        except requests.exceptions.ConnectionError:
            console.print(f"[red] Cannot connect to TestRail at {self.base_url}[/red]")
            return None
        except requests.exceptions.Timeout:
            console.print("[red] TestRail API request timed out[/red]")
            return None
        except Exception as e:
            console.print(f"[red] TestRail API error: {e}[/red]")
            return None

    def _map_status(self, status: TestStatus) -> int:
        """Maps our TestStatus enum to TestRail status IDs."""
        if status == TestStatus.PASSED:
            return self.STATUS_PASSED
        elif status == TestStatus.FAILED:
            return self.STATUS_FAILED
        elif status == TestStatus.ERROR:
            return self.STATUS_BLOCKED
        else:
            return self.STATUS_UNTESTED

    def create_test_run(self, name: str, description: str = "", case_ids: list = None):
        """Creates a new test run in TestRail. Returns the run ID."""
        data = {
            "suite_id": self.suite_id,
            "name": name,
            "description": description,
            "include_all": False,
            "case_ids": case_ids or [],
        }

        result = self._api_request("POST", f"add_run/{self.project_id}", data)

        if result:
            run_id = result.get("id")
            console.print(f"[green] TestRail run created: #{run_id}[/green]")
            return run_id
        return None

    def add_result(self, run_id: int, test_id: str, result) -> bool:
        """Adds a single test result to a TestRail run."""
        case_id = self.case_map.get(test_id)
        if not case_id:
            console.print(f"[yellow] No TestRail mapping for {test_id}. Skipping.[/yellow]")
            return False

        # Build comment with details
        comment_parts = []

        if result.observations:
            comment_parts.append(f"**Observations:**\n{result.observations}")

        if result.failure_reason:
            comment_parts.append(f"**Failure Reason:**\n{result.failure_reason}")

        if result.actions_taken:
            actions_text = "\n".join(
                f"  {a.step_number}. [{a.action_type}] {a.target_element or 'N/A'} - {a.reasoning}"
                for a in result.actions_taken
            )
            comment_parts.append(f"**Actions Taken:**\n{actions_text}")

        comment = "\n\n".join(comment_parts) if comment_parts else "No details available."

        data = {
            "status_id": self._map_status(result.status),
            "comment": comment,
        }

        api_result = self._api_request(
            "POST",
            f"add_result_for_case/{run_id}/{case_id}",
            data
        )

        return api_result is not None

    def push_results(self, results: list, vpn_region: str, language: str, agent_mode: str, app: str = "dazn", device: str = "unknown", tag: str = None):
        """Creates a test run and pushes all results to TestRail."""
        if not self.case_map:
            console.print("[red] No TestRail case mappings found. Cannot push results.[/red]")
            return None

        # Collect case IDs for tests that have mappings
        case_ids = []
        for result in results:
            case_id = self.case_map.get(result.test_id)
            if case_id:
                case_ids.append(case_id)

        if not case_ids:
            console.print("[yellow] No test results have TestRail mappings. Nothing to push.[/yellow]")
            return None

        # Create the test run
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        tag_part = f" [{tag.upper()}]" if tag else ""

        run_name = f"E2E LLM Android Automation - {app.upper()} - {vpn_region.upper()} ({language}){tag_part} - {device} - {timestamp}"

        run_description = (
            f"Automated E2E test run\n"
            f"App: {app.upper()}\n"
            f"Region: {vpn_region.upper()}\n"
            f"Language: {language}\n"
            f"Tag: {tag or 'All'}\n"
            f"Device: {device}\n"
            f"Agent Mode: {agent_mode}\n"
            f"Timestamp: {timestamp}"
        )

        run_id = self.create_test_run(run_name, run_description, case_ids)
        if not run_id:
            return None

        # Push each result
        pushed = 0
        skipped = 0
        for result in results:
            success = self.add_result(run_id, result.test_id, result)
            if success:
                pushed += 1
            else:
                skipped += 1

        console.print(f"[green] Pushed {pushed} results to TestRail (skipped {skipped})[/green]")
        console.print(f"[dim] View run: {self.base_url}/index.php?/runs/view/{run_id}[/dim]")

        return run_id