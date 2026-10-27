import asyncio
import argparse
import sys
import os
import json
import subprocess
import time
import yaml
import logging

from datetime import datetime
from models.test_results import TestStatus, TestCaseResult, Verbosity

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.test_results import Droidrun_Output
from rich.console import Console
from config.settings import test_config
from runners.test_registry import TEST_REGISTRY
from runners.parallel_runner import run_parallel
from reporters.history_tracker import start_run, save_test_result, finish_run
from config.settings import testrail_settings

console = Console()

# DEVICE & PORTAL VALIDATION

def check_adb_installed() -> bool:
    try:
        subprocess.run(["adb", "version"], capture_output=True, text=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def get_connected_devices() -> list:
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        devices = []
        for line in lines[1:]:
            if line.strip() and line.endswith("device"):
                devices.append(line.split("\t")[0])
        return devices
    except Exception:
        return []


def check_portal_installed(serial: str) -> bool:
    try:
        result = subprocess.run(
            ["adb", "-s", serial, "shell", "pm", "list", "packages", "com.droidrun.portal"],
            capture_output=True, text=True, check=True
        )
        return "com.droidrun.portal" in result.stdout
    except Exception:
        return False


def check_portal_responsive() -> bool:
    try:
        result = subprocess.run(
            ["droidrun", "ping"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False

# Determine logging level for droidrun and droidrun.agent

def set_droidrun_verbosity(level: int) -> None:
    """Set droidrun logging verbosity based on CLI flag value (0-4)."""
    log_level = DROIDRUN_LOG_LEVELS.get(level, logging.WARNING)
    logging.getLogger("droidrun").setLevel(log_level)
    logging.getLogger("droidrun.agent").setLevel(log_level)

DROIDRUN_LOG_LEVELS = {
    Droidrun_Output.ERROR: logging.ERROR,  # effectively suppresses all output
    Droidrun_Output.CRITICAL: logging.CRITICAL,
    Droidrun_Output.WARNING: logging.WARNING,
    Droidrun_Output.INFO: logging.INFO,
    Droidrun_Output.DEBUG: logging.DEBUG,
}

def _get_device_pin(serial: str) -> str:
    pin_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "device_pins.yaml")
    if not os.path.exists(pin_file):
        return ""
    try:
        with open(pin_file, "r") as f:
            pins = yaml.safe_load(f) or {}
        return str(pins.get(serial, ""))
    except Exception:
        return ""


def validate_device_setup(wake: bool = True) -> str:
    console.print("[dim]Checking ADB installation...[/dim]")
    if not check_adb_installed():
        console.print("[red] ADB is not installed or not in your system PATH.[/red]")
        sys.exit(1)
    console.print("[green] ▶ ADB found[/green]")

    console.print("[dim]Scanning for connected devices...[/dim]")
    devices = get_connected_devices()
    if not devices:
        console.print("[red] No connected Android devices found![/red]")
        sys.exit(1)
    console.print(f"[green] ▶ Found {len(devices)} device(s): {', '.join(devices)}[/green]")

    serial = devices[0]

    console.print(f"[dim]Checking DroidRun Portal on {serial}...[/dim]")
    if not check_portal_installed(serial):
        console.print("[red] DroidRun Portal is not installed on the device![/red]")
        sys.exit(1)
    console.print("[green] ▶ DroidRun Portal installed[/green]")

    console.print("[dim]Pinging DroidRun Portal...[/dim]")
    if not check_portal_responsive():
        console.print("[yellow]DroidRun Portal not responding to ping.[/yellow]")
        try:
            subprocess.run(["adb", "-s", serial, "shell", "input", "keyevent", "82"], check=True)
        except Exception:
            pass
    else:
        console.print("[green] ▶ DroidRun Portal responsive[/green]")

    if wake:
        console.print("[dim]Waking up device...[/dim]")
        try:
            subprocess.run(["adb", "-s", serial, "shell", "input", "keyevent", "KEYCODE_WAKEUP"], capture_output=True, check=True)
            subprocess.run(["adb", "-s", serial, "shell", "input", "keyevent", "82"], capture_output=True, check=True)

            pin = _get_device_pin(serial)
            if pin:
                time.sleep(1)
                subprocess.run(["adb", "-s", serial, "shell", "input", "text", pin], capture_output=True, check=True)
                subprocess.run(["adb", "-s", serial, "shell", "input", "keyevent", "66"], capture_output=True, check=True)
                console.print("[green]Device awake and unlocked with PIN[/green]")
            else:
                subprocess.run(["adb", "-s", serial, "shell", "input", "keyevent", "82"], capture_output=True, check=True)
                console.print("[green]Device awake and unlocked (no PIN)[/green]")

            subprocess.run(["adb", "-s", serial, "shell", "settings", "put", "system", "screen_off_timeout", "1800000"], capture_output=True, check=True)
        except Exception:
            console.print("[yellow]Could not wake device.[/yellow]")
    else:
        console.print("[dim]...Skipping device wake[/dim]")

    return serial


def check_api_key() -> bool:
    from config.settings import llm_settings

    if llm_settings.provider == "OpenRouter":
        return bool(llm_settings.openrouter_api_key and llm_settings.openrouter_api_key != "sk-or-your-key-here")
    elif llm_settings.provider == "OpenAI":
        return bool(llm_settings.openai_api_key and llm_settings.openai_api_key != "sk-your-api-key-here")
    elif llm_settings.provider == "Anthropic":
        return bool(llm_settings.anthropic_api_key and llm_settings.anthropic_api_key != "sk-ant-your-key-here")
    return False


# REPORT SAVING

def save_report_locally(result, test_id, vpn_region, language):
    os.makedirs(test_config.report_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_id}_{vpn_region}_{language}_{timestamp}.json"
    filepath = os.path.join(test_config.report_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=4, default=str)

    console.print(f"[dim] Report saved to: {filepath}[/dim]")


# VIEW PAST RESULTS 

def find_latest_result(test_id: str) -> str:
    report_dir = test_config.report_dir
    if not os.path.exists(report_dir):
        console.print(f"[red]No reports directory found at {report_dir}[/red]")
        sys.exit(1)

    matches = sorted(
        [f for f in os.listdir(report_dir) if f.startswith(test_id) and f.endswith(".json")],
        reverse=True
    )

    if not matches:
        console.print(f"[red]No results found for {test_id}[/red]")
        console.print(f"[dim]Looking in: {report_dir}[/dim]")

        all_files = [f for f in os.listdir(report_dir) if f.endswith(".json")]
        if all_files:
            test_ids = sorted(set("_".join(f.split("_")[:4]) for f in all_files))
            console.print("[dim]Available results:[/dim]")
            for tid in test_ids[:20]:
                console.print(f"[dim]  {tid}[/dim]")
        sys.exit(1)

    return os.path.join(report_dir, matches[0])


def view_result(test_id: str, verbosity: Verbosity):
    filepath = find_latest_result(test_id)

    with open(filepath, "r") as f:
        data = json.load(f)

    result = TestCaseResult(**data)
    output = result.display(verbosity)
    if output:
        console.print(output)
    console.print(f"\n[dim]  📁 Source: {filepath}[/dim]")


# TEST SELECTION

def get_tests_to_run(app: str, suite: str, test_id_filter: str = None, tag_filter: str = None) -> list:
    tests = []
    if app == "all":
        apps_to_run = list(TEST_REGISTRY.keys())
    elif app in TEST_REGISTRY:
        apps_to_run = [app]
    else:
        console.print(f"[red]Unknown app: {app}[/red]")
        console.print(f"[dim]Available apps: {', '.join(TEST_REGISTRY.keys())}, all[/dim]")
        sys.exit(1)

    for app_name in apps_to_run:
        app_suites = TEST_REGISTRY[app_name]

        if suite == "all":
            suites_to_run = list(app_suites.keys())
        elif suite in app_suites:
            suites_to_run = [suite]
        else:
            console.print(f"[red]Unknown suite '{suite}' for app '{app_name}'[/red]")
            sys.exit(1)

        for suite_name in suites_to_run:
            for entry in app_suites[suite_name]:
                tests.append({
                    "app": app_name,
                    "suite": suite_name,
                    "id": entry[0],
                    "name": entry[1],
                    "func": entry[2],
                    "tags": entry[3],
                })

    if test_id_filter:
        filtered = [t for t in tests if t["id"] == test_id_filter]
        if not filtered:
            console.print(f"[red]Test '{test_id_filter}' not found.[/red]")
            for t in tests:
                console.print(f"[dim]  {t['id']} - {t['name']} [{', '.join(t['tags'])}][/dim]")
            sys.exit(1)
        return filtered

    if tag_filter:
        filtered = [t for t in tests if tag_filter in t["tags"]]
        if not filtered:
            console.print(f"[red]No tests found with tag '{tag_filter}'[/red]")
            sys.exit(1)
        return filtered

    return tests


def print_available_tests():
    console.print("\n[bold cyan]Available Tests:[/bold cyan]\n")
    for app_name, suites in TEST_REGISTRY.items():
        console.print(f"  [bold]{app_name.upper()}[/bold]")
        for suite_name, tests in suites.items():
            console.print(f"    {suite_name}:")
            for test in tests:
                console.print(f"      {test[0]} - {test[1]} [dim][{', '.join(test[3])}][/dim]")
        console.print()

    all_tags = set()
    for app_name, suites in TEST_REGISTRY.items():
        for suite_name, tests in suites.items():
            for test in tests:
                all_tags.update(test[3])

    console.print("[bold cyan]Available Tags:[/bold cyan]\n")
    for tag in sorted(all_tags):
        count = sum(
            1 for suites in TEST_REGISTRY.values()
            for tests in suites.values()
            for test in tests
            if tag in test[3]
        )
        console.print(f"  {tag}: {count} tests")
    console.print()



# CLI PARSER

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="test_runner",
        description="DAZN / Kayo / Binge E2E LLM Test Automation Suite"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # FLAGS
    run_parser = subparsers.add_parser("run", help="Execute tests")
    run_parser.add_argument("--app", default="dazn", help="App to test: dazn, kayo, binge, all")
    run_parser.add_argument("--suite", default="all", help="Test suite: login, playback, navigation, search, all")
    run_parser.add_argument("--device-id", default="auto", help="Device serial or 'auto' to detect")
    run_parser.add_argument("--vpn-region", default="de", help="Target vpn_region: uk, de, japan, australia")
    run_parser.add_argument("--language", default="en_gb", help="Target language: en_gb, de_de, en_de, ja_jp, en_au")
    run_parser.add_argument("--list", action="store_true", help="List all available tests and exit")
    run_parser.add_argument("--skip-pre-test-checks", action="store_true", help="Skip device and portal validation")
    run_parser.add_argument("--test", default=None, help="Run a specific test by ID")
    run_parser.add_argument("--fastagent", action="store_true", help="Force FastAgent mode")
    run_parser.add_argument("--manageragent", action="store_true", help="Force Manager+Executor mode")
    run_parser.add_argument("--no-trajectory", action="store_true", help="Skip trajectory recording")
    run_parser.add_argument("--no-wake", action="store_true", help="Skip device wake")
    run_parser.add_argument("--smoke", action="store_true", help="Run only smoke tests")
    run_parser.add_argument("--regression", action="store_true", help="Run only regression tests")
    run_parser.add_argument("--critical", action="store_true", help="Run only critical tests")
    run_parser.add_argument("--tag", default=None, help="Filter by custom tag name")
    run_parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    run_parser.add_argument("--push-testrail", action="store_true", help="Push results to TestRail")
    run_parser.add_argument("--history", type=int, nargs="?", const=7, default=None, help="Show history for last N days")
    run_parser.add_argument("--history-detail", default=None, help="Show detailed history for a test ID")
    run_parser.add_argument("--summary", default=None, help="Show summary for a test ID")
    run_parser.add_argument("-v", "--verbosity",type=int, choices=[0, 1, 2, 3], default=1,help="Output verbosity: 0=silent, 1=summary (default), 2=compact, 3=detailed")
    run_parser.add_argument("--show-droidr-output",type=int, choices=[0, 1, 2, 3, 4], default=0, help="Droidrun output verbosity: 0=silent, 1=critical, 2=warning, 3=info, 4=debug")

    #'view' command
    view_parser = subparsers.add_parser("view", help="View a past test result")
    view_parser.add_argument("test_id", help="Test case ID, e.g. TC-DAZN-LOGIN-001")
    return parser

# MAIN

async def main():
    parser = build_parser()
    args = parser.parse_args()
    set_droidrun_verbosity(args.show_droidr_output)

    # No command provided
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # VIEW command 
    if args.command == "view":
        view_result(args.test_id, Verbosity(args.verbosity))
        return

    # RUN command
    verbosity = Verbosity(args.verbosity)

    # List mode
    if args.list:
        print_available_tests()
        sys.exit(0)
        
    # History mode
    if args.history is not None:
        from reporters.history_tracker import show_history
        show_history(days=args.history)
        sys.exit(0)

    if args.history_detail:
        from reporters.history_tracker import show_test_detail
        show_test_detail(test_id=args.history_detail)
        sys.exit(0)

    # Agent mode
    if args.fastagent and args.manageragent:
        console.print("[red] Cannot use both --fastagent and --manageragent together[/red]")
        sys.exit(1)

    if args.fastagent:
        agent_mode = "fast"
    elif args.manageragent:
        agent_mode = "manager"
    else:
        agent_mode = "default"

    tag_filter = None
    if args.smoke:
        tag_filter = "Smoke"
    elif args.regression:
        tag_filter = "Regression"
    elif args.critical:
        tag_filter = "Critical"
    elif args.tag:
        tag_filter = args.tag

    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold cyan]  DAZN / Kayo / Binge E2E Test Runner[/bold cyan]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

    # Pre-test checks
    if not args.skip_pre_test_checks:
        console.print("[dim]Checking API key...[/dim]")
        if not check_api_key():
            console.print("[red]API key not configured![/red]")
            sys.exit(1)
        console.print("[green] ▶ API key configured[/green]")
        target_device = validate_device_setup(wake=not args.no_wake)
    else:
        console.print("[yellow]Skipping pre-test checks[/yellow]")
        target_device = args.device_id

    if args.device_id != "auto":
        target_device = args.device_id

    tests_to_run = get_tests_to_run(args.app, args.suite, args.test, tag_filter)

    agent_display = {"fast": "FastAgent", "manager": "Manager+Executor", "default": "Default (.env)"}
    verbosity_display = {0: "Silent", 1: "Quick Summary", 2: "Compact Summary", 3: "Detailed Summary"}
    verbosity_droidrun = {0: "DEBUG = logging everything — debug details, info, warnings, errors", 1: "INFO logging = Logging info messages + warnings + errors", 2: "WARNING = logging warnings + errors", 3: "ERROR = only logging errors + criticals ", 4: "CRITICAL = logging only critical failures"}

    
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold cyan]  Running Tests[/bold cyan]")
    console.print(f"[bold cyan]  Device:     {target_device}[/bold cyan]")
    console.print(f"[bold cyan]  App:        {args.app.upper()}[/bold cyan]")
    console.print(f"[bold cyan]  Suite:      {args.suite}[/bold cyan]")
    console.print(f"[bold cyan]  Region:     {args.vpn_region.upper()}[/bold cyan]")
    console.print(f"[bold cyan]  Language:   {args.language.upper()}[/bold cyan]")
    console.print(f"[bold cyan]  Agent:      {agent_display.get(agent_mode, 'Default')}[/bold cyan]")
    console.print(f"[bold cyan]  Tests:      {len(tests_to_run)}[/bold cyan]")
    console.print(f"[bold cyan]  Tag:        {tag_filter if tag_filter else 'All'}[/bold cyan]")
    console.print(f"[bold cyan]  Verbosity:  {verbosity_display[args.verbosity]} (-v {args.verbosity})[/bold cyan]")
    console.print(f"[bold cyan]  Droidrun:   {verbosity_droidrun[args.show_droidr_output]} (--show-droidr-output {args.show_droidr_output})[/bold cyan]")
    console.print(f"[bold cyan]  Trajectory: {'OFF - will [red]NOT[/red] be saved' if args.no_trajectory else 'ON - will be saved'}[/bold cyan]")
    console.print(f"[bold cyan]  Wake Up:    {'OFF - device will [red]NOT[/red] be woken up first' if args.no_wake else 'ON - will wake up device first before testing'}[/bold cyan]")
    console.print(f"[bold cyan]  Parallel:   {'ON' if args.parallel else 'OFF'}[/bold cyan]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]")

    if tag_filter:
        console.print(f"\n[bold cyan]Tests tagged as '{tag_filter}':[/bold cyan]")
        for test in tests_to_run:
            console.print()
            console.print(f"  {test['id']} - {test['name']} [dim][{', '.join(test['tags'])}][/dim]")
        console.print()

    # Start history tracking
    run_start_time = datetime.now()
    run_id = start_run(
        app=args.app,
        suite=args.suite,
        vpn_region=args.vpn_region,
        language=args.language,
        agent_mode=agent_mode,
        device=target_device,
    )

    # Run all tests
    results = []

    if args.parallel:
        devices = get_connected_devices()
        if len(devices) < 2:
            console.print("[yellow]Only 1 device connected. Falling back to sequential mode.[/yellow]\n")
            args.parallel = False
        else:
            console.print(f"[bold cyan]  Mode: Parallel ({len(devices)} devices)[/bold cyan]")

            parallel_results = await run_parallel(
                tests_to_run, devices, args.vpn_region, args.language, agent_mode, args.no_trajectory
            )

            for outcome in parallel_results:
                if outcome["result"]:
                    save_report_locally(outcome["result"], outcome["test"]["id"], args.vpn_region, args.language)
                    save_test_result(run_id, outcome["test"]["id"], outcome["test"]["name"], outcome["test"]["tags"], outcome["result"])

                    output = outcome["result"].display(verbosity)
                    if output:
                        console.print(output)

                    results.append(outcome["result"])

    if not args.parallel:
        for test in tests_to_run:
            console.print(
                f"\n[yellow]▶ [{test['app'].upper()}] {test['id']}:[/yellow] "
                f"[bold white]{test['name']}[/bold white] "
                f"[dim][{', '.join(test['tags'])}][/dim]"
            )

            try:
                result = await test["func"](
                    target_device, args.vpn_region, args.language, agent_mode, args.no_trajectory
                )
                save_report_locally(result, test["id"], args.vpn_region, args.language)
                save_test_result(run_id, test["id"], test["name"], test["tags"], result)

                output = result.display(verbosity)
                if output:
                    console.print(output)

                results.append(result)

            except Exception as e:
                console.print(f"[red] CRASH: {str(e)}[/red]")

    # Print summary
    total = len(results)
    passed = sum(1 for r in results if r.status == TestStatus.PASSED)
    failed = sum(1 for r in results if r.status == TestStatus.FAILED)
    errors = sum(1 for r in results if r.status == TestStatus.ERROR)

    console.print(f"\n[bold]{'='*60}[/bold]")
    console.print(f"[bold]  RESULTS SUMMARY[/bold]")
    console.print(f"[bold]{'='*60}[/bold]")
    console.print(f"[bold]  Total:     {total}[/bold]")
    console.print(f"[green]  Passed:    {passed}[/green]")
    console.print(f"[red]  Failed:    {failed}[/red]")
    console.print(f"[red]  Errors:    {errors}[/red]")
    console.print(f"[bold]  Pass Rate: {(passed / total * 100) if total else 0:.0f}%[/bold]")
    if args.parallel:
        console.print(f"[bold]  Devices:   {len(get_connected_devices())}[/bold]")
    console.print(f"[bold]{'='*60}[/bold]")

    # Push to TestRail
    if args.push_testrail:
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold cyan]  Pushing to TestRail[/bold cyan]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]")

        if not testrail_settings.url or not testrail_settings.api_key:
            console.print("[red] TestRail not configured.[/red]")
        elif not results:
            console.print("[yellow] No results to push.[/yellow]")
        else:
            from reporters.testrail_reporter import TestRailReporter
            reporter = TestRailReporter()
            reporter.push_results(results, args.vpn_region, args.language, agent_mode, target_device, args.app)

    duration = (datetime.now() - run_start_time).total_seconds()
    finish_run(run_id, results, duration)
    console.print(f"[dim] ▶ History saved (run: {run_id})[/dim]")


if __name__ == "__main__":
    asyncio.run(main())