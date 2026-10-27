import asyncio
from rich.console import Console
from models.test_results import TestStatus

console = Console()


def split_tests_across_devices(tests: list, devices: list) -> dict:
    """
    Splits tests evenly across available devices.
    Returns a dict mapping device serial to list of tests.
    """
    assignments = {device: [] for device in devices}
    
    for i, test in enumerate(tests):
        device = devices[i % len(devices)]
        assignments[device].append(test)
    
    return assignments


async def run_test_on_device(test: dict, device_id: str, vpn_region: str, language: str, agent_mode: str, no_trajectory: bool) -> dict:
    """
    Runs a single test on a specific device.
    Returns a dict with the test info and result.
    """
    try:
        result = await test["func"](device_id, vpn_region, language, agent_mode, no_trajectory)
        return {
            "test": test,
            "device": device_id,
            "result": result,
            "error": None,
        }
    except Exception as e:
        return {
            "test": test,
            "device": device_id,
            "result": None,
            "error": str(e),
        }


async def run_device_queue(device_id: str, tests: list, vpn_region: str, language: str, agent_mode: str, no_trajectory: bool) -> list:
    """
    Runs a queue of tests sequentially on a single device.
    Each device gets its own queue and runs them one by one.
    Multiple devices run their queues in parallel.
    """
    results = []
    
    for test in tests:
        console.print(f"[yellow]  ▶ [{device_id}] {test['id']}: {test['name']}...[/yellow]")
        
        outcome = await run_test_on_device(
            test, device_id, vpn_region, language, agent_mode, no_trajectory
        )
        results.append(outcome)
        
        if outcome["result"]:
            if outcome["result"].status == TestStatus.PASSED:
                console.print(f"[green][{device_id}] PASSED[/green]")
            elif outcome["result"].status == TestStatus.FAILED:
                console.print(f"[red][{device_id}] FAILED: {outcome['result'].failure_reason}[/red]")
            else:
                console.print(f"[red][{device_id}] ERROR: {outcome['result'].failure_reason}[/red]")
        else:
            console.print(f"[red][{device_id}] CRASH: {outcome['error']}[/red]")
    
    return results


async def run_parallel(tests: list, devices: list, vpn_region: str, language: str, agent_mode: str, no_trajectory: bool) -> list:
    """
    Main parallel execution function.
    Splits tests across devices and runs them simultaneously.
    """
    # Split tests across devices
    assignments = split_tests_across_devices(tests, devices)
    
    # Print assignment summary
    console.print(f"\n[bold cyan]Parallel Execution Plan:[/bold cyan]")
    for device, device_tests in assignments.items():
        test_ids = [t["id"] for t in device_tests]
        console.print(f"  [bold]{device}[/bold]: {len(device_tests)} tests")
        for tid in test_ids:
            console.print(f"    - {tid}")
    console.print()
    
    # Run all device queues in parallel
    tasks = []
    for device, device_tests in assignments.items():
        if device_tests:  # Only create task if device has tests
            task = run_device_queue(
                device, device_tests, vpn_region, language, agent_mode, no_trajectory
            )
            tasks.append(task)
    
    # Wait for all devices to finish
    all_results = await asyncio.gather(*tasks)
    
    # Flatten results from all devices into one list
    flat_results = []
    for device_results in all_results:
        flat_results.extend(device_results)
    
    return flat_results