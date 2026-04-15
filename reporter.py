"""
reporter.py — Formats and prints the consolidated readiness report.
Uses Rich for clean, readable console output.
Also saves JSON to output/ folder.
"""

import json
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

console = Console()


STATUS_COLOURS = {
    "READY":                "green",
    "CONDITIONALLY_READY":  "yellow",
    "NOT_READY":            "red",
}

RISK_COLOURS = {
    "HIGH":   "red",
    "MEDIUM": "yellow",
    "LOW":    "green",
}


def _colour_status(status: str) -> Text:
    colour = STATUS_COLOURS.get(status, "white")
    return Text(status, style=f"bold {colour}")


def _colour_risk(risk: str) -> Text:
    colour = RISK_COLOURS.get(risk, "white")
    return Text(risk, style=f"bold {colour}")


def print_report(report: dict):
    story_id  = report.get("story_id", "Unknown")
    title     = report.get("title", "")
    status    = report.get("dor_status", "UNKNOWN")
    readiness = report.get("readiness_score", 0)
    risk      = report.get("overall_risk_level", "UNKNOWN")
    ambiguity = report.get("ambiguity_score", 0)

    console.print()
    console.rule(f"[bold]Requirements Crew Report  —  {story_id}[/bold]")
    console.print()

    # Header summary table
    summary_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    summary_table.add_column("Label", style="dim", width=22)
    summary_table.add_column("Value")

    summary_table.add_row("Story",           f"[bold]{story_id}[/bold] — {title}")
    summary_table.add_row("DoR Status",      _colour_status(status))
    summary_table.add_row("Readiness Score", f"{readiness}/100")
    summary_table.add_row("Risk Level",      _colour_risk(risk))
    summary_table.add_row("Ambiguity Score", f"{ambiguity}/100")
    console.print(summary_table)

    # Key blockers
    blockers = report.get("key_blockers", [])
    if blockers:
        console.print(Panel(
            "\n".join(f"  [red]•[/red] {b}" for b in blockers),
            title="[bold red]Key Blockers[/bold red]",
            border_style="red",
        ))

    # Key risks
    risks = report.get("key_risks", [])
    if risks:
        console.print(Panel(
            "\n".join(f"  [yellow]•[/yellow] {r}" for r in risks),
            title="[bold yellow]Key Risks[/bold yellow]",
            border_style="yellow",
        ))

    # Immediate actions
    actions = report.get("immediate_actions", [])
    if actions:
        console.print(Panel(
            "\n".join(f"  [cyan]→[/cyan] {a}" for a in actions),
            title="[bold cyan]Immediate Actions[/bold cyan]",
            border_style="cyan",
        ))

    # TPM summary
    summary = report.get("tpm_summary", "")
    if summary:
        console.print(Panel(
            f"  {summary}",
            title="[bold green]TPM Summary[/bold green]",
            border_style="green",
        ))

    console.print()


def print_sprint_summary(reports: list):
    """Print a summary table for multiple stories — sprint-level view."""
    console.print()
    console.rule("[bold]Sprint Readiness Summary[/bold]")
    console.print()

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Story ID",  width=12)
    table.add_column("Title",     width=28)
    table.add_column("DoR",       width=22)
    table.add_column("Risk",      width=10)
    table.add_column("Ambiguity", width=12)
    table.add_column("Readiness", width=12)

    for r in reports:
        status    = r.get("dor_status", "UNKNOWN")
        risk      = r.get("overall_risk_level", "UNKNOWN")
        s_colour  = STATUS_COLOURS.get(status, "white")
        r_colour  = RISK_COLOURS.get(risk, "white")

        table.add_row(
            r.get("story_id", ""),
            r.get("title", "")[:26],
            Text(status, style=f"bold {s_colour}"),
            Text(risk,   style=f"bold {r_colour}"),
            str(r.get("ambiguity_score", 0)),
            str(r.get("readiness_score", 0)) + "/100",
        )

    console.print(table)
    console.print()

    # Count readiness
    total     = len(reports)
    ready     = sum(1 for r in reports if r.get("dor_status") == "READY")
    not_ready = sum(1 for r in reports if r.get("dor_status") == "NOT_READY")
    cond      = total - ready - not_ready

    console.print(
        f"  [green]Ready: {ready}[/green]  "
        f"[yellow]Conditional: {cond}[/yellow]  "
        f"[red]Not Ready: {not_ready}[/red]  "
        f"[dim]of {total} stories[/dim]"
    )
    console.print()


def save_reports(reports: list, sprint_name: str = "sprint"):
    """Save all reports to output/ as JSON and HTML."""
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_file = f"output/{sprint_name}_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(reports, f, indent=2)

    from html_reporter import save_html_report
    html_file = save_html_report(reports, sprint_name, timestamp)

    console.print(f"  [dim]JSON saved → {json_file}[/dim]")
    console.print(f"  [dim]HTML saved → {html_file}[/dim]\n")
    return json_file