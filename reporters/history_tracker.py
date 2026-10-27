import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Optional
from rich.console import Console
from rich.table import Table
from config.settings import test_config
from models.test_results import TestStatus

console = Console()

DB_PATH = os.path.join(test_config.report_dir, "history.db")

#SQLite DB 
def _get_connection() -> sqlite3.Connection:
    """Creates or connects to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_tables(conn)
    return conn

#SQLite DB make table
def _ensure_tables(conn: sqlite3.Connection):
    """Creates the database tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            app TEXT NOT NULL,
            suite TEXT NOT NULL,
            vpn_region TEXT NOT NULL,
            language TEXT NOT NULL,
            agent_mode TEXT NOT NULL,
            device TEXT NOT NULL,
            total_tests INTEGER DEFAULT 0,
            passed INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            errors INTEGER DEFAULT 0,
            pass_rate REAL DEFAULT 0.0,
            duration_seconds REAL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            test_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            tags TEXT NOT NULL,
            status TEXT NOT NULL,
            assertion_passed INTEGER DEFAULT 0,
            failure_reason TEXT,
            observations TEXT,
            total_steps INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES runs(run_id)
        );
    """)
    conn.commit()


def start_run(app: str, suite: str, vpn_region: str, language: str, agent_mode: str, device: str) -> str:
    """Creates a new run record and returns the run_id."""
    run_id = str(uuid.uuid4())[:8]
    conn = _get_connection()
    conn.execute(
        """INSERT INTO runs (run_id, timestamp, app, suite, vpn_region, language, agent_mode, device)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, datetime.now().isoformat(), app, suite, vpn_region, language, agent_mode, device)
    )
    conn.commit()
    conn.close()
    return run_id


def save_test_result(run_id: str, test_id: str, test_name: str, tags: list, result):
    """Saves a single test result to the history database."""
    conn = _get_connection()
    conn.execute(
        """INSERT INTO test_results (run_id, test_id, test_name, tags, status, assertion_passed, 
           failure_reason, observations, total_steps, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            run_id,
            test_id,
            test_name,
            ",".join(tags),
            result.status.value if hasattr(result.status, 'value') else str(result.status),
            1 if result.assertion_passed else 0,
            result.failure_reason,
            result.observations,
            result.total_steps,
            datetime.now().isoformat(),
        )
    )
    conn.commit()
    conn.close()


def finish_run(run_id: str, results: list, duration_seconds: float = 0.0):
    """Updates the run record with final summary stats."""
    total = len(results)
    passed = sum(1 for r in results if r.status == TestStatus.PASSED)
    failed = sum(1 for r in results if r.status == TestStatus.FAILED)
    errors = sum(1 for r in results if r.status == TestStatus.ERROR)
    pass_rate = (passed / total * 100) if total > 0 else 0.0

    conn = _get_connection()
    conn.execute(
        """UPDATE runs SET total_tests=?, passed=?, failed=?, errors=?, pass_rate=?, duration_seconds=?
           WHERE run_id=?""",
        (total, passed, failed, errors, pass_rate, duration_seconds, run_id)
    )
    conn.commit()
    conn.close()


def show_history(days: int = 7):
    """Displays test run history and trends for the last N days."""
    conn = _get_connection()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    # Get run summary
    runs = conn.execute(
        "SELECT * FROM runs WHERE timestamp >= ? ORDER BY timestamp DESC", (cutoff,)
    ).fetchall()

    if not runs:
        console.print(f"\n[yellow]No test runs found in the last {days} days.[/yellow]")
        conn.close()
        return

    # Header
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold cyan]  Test Run History (Last {days} Days)[/bold cyan]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

    # Overall stats
    total_runs = len(runs)
    total_tests = sum(r["total_tests"] for r in runs)
    avg_pass_rate = sum(r["pass_rate"] for r in runs) / total_runs if total_runs > 0 else 0

    console.print(f"[bold]  Total Runs:     {total_runs}[/bold]")
    console.print(f"[bold]  Total Tests:    {total_tests}[/bold]")
    console.print(f"[bold]  Avg Pass Rate:  {avg_pass_rate:.0f}%[/bold]\n")

    # Run table
    table = Table(title="Recent Runs")
    table.add_column("Date", style="cyan")
    table.add_column("App")
    table.add_column("Region")
    table.add_column("Agent")
    table.add_column("Tests", justify="right")
    table.add_column("Passed", justify="right", style="green")
    table.add_column("Failed", justify="right", style="red")
    table.add_column("Pass Rate", justify="right")

    for run in runs[:20]:
        timestamp = run["timestamp"][:16].replace("T", " ")
        pass_rate = run["pass_rate"]
        rate_style = "green" if pass_rate >= 90 else "yellow" if pass_rate >= 70 else "red"
        table.add_row(
            timestamp,
            run["app"].upper(),
            run["vpn_region"].upper(),
            run["agent_mode"],
            str(run["total_tests"]),
            str(run["passed"]),
            str(run["failed"]),
            f"[{rate_style}]{pass_rate:.0f}%[/{rate_style}]",
        )

    console.print(table)

    # Most failed tests
    failed_tests = conn.execute(
        """SELECT test_id, test_name, COUNT(*) as fail_count
           FROM test_results 
           WHERE timestamp >= ? AND status = 'failed'
           GROUP BY test_id 
           ORDER BY fail_count DESC 
           LIMIT 5""",
        (cutoff,)
    ).fetchall()

    if failed_tests:
        console.print(f"\n[bold red]Most Failed Tests:[/bold red]")
        for t in failed_tests:
            total_runs_for_test = conn.execute(
                "SELECT COUNT(DISTINCT run_id) FROM test_results WHERE test_id = ? AND timestamp >= ?",
                (t["test_id"], cutoff)
            ).fetchone()[0]
            percentage = (t["fail_count"] / total_runs_for_test * 100) if total_runs_for_test > 0 else 0
            console.print(f"  {t['test_id']} - {t['test_name']}: Failed {t['fail_count']}/{total_runs_for_test} runs ({percentage:.0f}%)")

    # Pass rate by region
    regions = conn.execute(
        """SELECT vpn_region, AVG(pass_rate) as avg_rate, COUNT(*) as run_count
           FROM runs 
           WHERE timestamp >= ?
           GROUP BY vpn_region
           ORDER BY avg_rate DESC""",
        (cutoff,)
    ).fetchall()

    if regions:
        console.print(f"\n[bold cyan]Pass Rate by Region:[/bold cyan]")
        for r in regions:
            rate = r["avg_rate"]
            rate_style = "green" if rate >= 90 else "yellow" if rate >= 70 else "red"
            console.print(f"  {r['vpn_region'].upper()}: [{rate_style}]{rate:.0f}%[/{rate_style}] ({r['run_count']} runs)")

    console.print(f"\n[bold]{'='*60}[/bold]")
    conn.close()


def show_test_detail(test_id: str, days: int = 30):
    """Shows detailed history for a specific test case."""
    conn = _get_connection()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    results = conn.execute(
        """SELECT tr.*, r.vpn_region, r.agent_mode, r.device
           FROM test_results tr
           JOIN runs r ON tr.run_id = r.run_id
           WHERE tr.test_id = ? AND tr.timestamp >= ?
           ORDER BY tr.timestamp DESC
           LIMIT 20""",
        (test_id, cutoff)
    ).fetchall()

    if not results:
        console.print(f"\n[yellow]No history found for {test_id} in the last {days} days.[/yellow]")
        conn.close()
        return

    # Header
    test_name = results[0]["test_name"]
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold cyan]  History for {test_id}[/bold cyan]")
    console.print(f"[bold cyan]  {test_name}[/bold cyan]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

    # Stats
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    pass_rate = (passed / total * 100) if total > 0 else 0

    console.print(f"[bold]  Runs:       {total}[/bold]")
    console.print(f"[bold]  Pass Rate:  {pass_rate:.0f}%[/bold]\n")

    # Result table
    table = Table(title="Recent Results")
    table.add_column("Date", style="cyan")
    table.add_column("Region")
    table.add_column("Agent")
    table.add_column("Status")
    table.add_column("Steps", justify="right")
    table.add_column("Failure Reason", max_width=40)

    for r in results:
        timestamp = r["timestamp"][:16].replace("T", " ")
        status = r["status"]
        if status == "passed":
            status_display = "[green]PASSED[/green]"
        elif status == "failed":
            status_display = "[red]FAILED[/red]"
        else:
            status_display = "[red]ERROR[/red]"

        table.add_row(
            timestamp,
            r["vpn_region"].upper(),
            r["agent_mode"],
            status_display,
            str(r["total_steps"]),
            r["failure_reason"] or "",
        )

    console.print(table)

    # Show most common failure reasons
    failure_reasons = conn.execute(
        """SELECT failure_reason, COUNT(*) as count
           FROM test_results
           WHERE test_id = ? AND timestamp >= ? AND status = 'failed' AND failure_reason IS NOT NULL
           GROUP BY failure_reason
           ORDER BY count DESC
           LIMIT 3""",
        (test_id, cutoff)
    ).fetchall()

    if failure_reasons:
        console.print(f"\n[bold red]Most Common Failure Reasons:[/bold red]")
        for fr in failure_reasons:
            console.print(f"  ({fr['count']}x) {fr['failure_reason'][:80]}")

    console.print(f"\n[bold]{'='*60}[/bold]")
    conn.close()