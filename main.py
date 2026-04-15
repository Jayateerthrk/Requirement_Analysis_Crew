"""
main.py — Entry point for the Requirements Crew.
Supports paste input for one or multiple stories.
Run: python main.py
"""

import json
import sys
from rich.console import Console
from rich.prompt import Prompt, Confirm

from schema import Story
from crew import run_requirements_crew
from reporter import print_report, print_sprint_summary, save_reports

console = Console()


STORY_HELP = """
Paste your user story in this format (all fields except ID, title,
and description are optional):

  Story ID    : PROJ-101
  Title       : Product search for registered users
  Description : As a registered user I want to search for products
                so that I can find and purchase items quickly.
  AC          : Search returns results within 3 seconds
  AC          : Zero results shows a helpful empty state message
  Points      : 5
  Sprint      : Sprint 12

  Type END on a new line when done.
"""


def parse_pasted_story(raw: str) -> Story:
    """
    Parse a pasted story block into a Story object.
    Flexible — handles labelled format or plain text.
    """
    lines = raw.strip().splitlines()

    story_id    = "STORY-001"
    title       = ""
    description_lines = []
    acs         = []
    points      = None
    sprint      = None

    mode = None

    for line in lines:
        stripped = line.strip()
        lower    = stripped.lower()

        if lower.startswith("story id") and ":" in stripped:
            story_id = stripped.split(":", 1)[1].strip()
            mode = None
        elif lower.startswith("title") and ":" in stripped:
            title = stripped.split(":", 1)[1].strip()
            mode = None
        elif lower.startswith("description") and ":" in stripped:
            rest = stripped.split(":", 1)[1].strip()
            if rest:
                description_lines.append(rest)
            mode = "desc"
        elif lower.startswith("ac") and ":" in stripped:
            ac = stripped.split(":", 1)[1].strip()
            if ac:
                acs.append(ac)
            mode = "ac"
        elif lower.startswith("points") and ":" in stripped:
            try:
                points = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                pass
            mode = None
        elif lower.startswith("sprint") and ":" in stripped:
            sprint = stripped.split(":", 1)[1].strip()
            mode = None
        elif stripped and mode == "desc":
            description_lines.append(stripped)
        elif stripped and mode == "ac":
            acs.append(stripped)
        elif stripped and not title:
            # First non-empty unrecognised line becomes the title
            title = stripped
            mode = None
        elif stripped and not description_lines:
            description_lines.append(stripped)
            mode = "desc"

    description = " ".join(description_lines) if description_lines else title

    return Story(
        story_id=story_id,
        title=title or story_id,
        description=description,
        acceptance_criteria=acs,
        story_points=points,
        sprint=sprint,
    )


def collect_story() -> Story:
    console.print()
    console.print("[dim]" + STORY_HELP.strip() + "[/dim]")
    console.print()

    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().upper() == "END":
            break
        lines.append(line)

    raw = "\n".join(lines).strip()
    if not raw:
        console.print("[red]No story entered.[/red]")
        sys.exit(1)

    return parse_pasted_story(raw)


def run_single():
    console.print("\n[bold]Requirements Crew[/bold] — Single Story Mode")
    story = collect_story()
    console.print(f"\n[dim]Running crew on: {story.story_id} — {story.title}[/dim]\n")

    try:
        report = run_requirements_crew(story)
        print_report(report)
        save_reports([report], sprint_name=story.story_id)
    except Exception as e:
        console.print(f"[red]Crew failed: {e}[/red]")
        raise


def run_batch():
    console.print("\n[bold]Requirements Crew[/bold] — Sprint Batch Mode")
    console.print("[dim]You will be prompted to paste stories one by one.[/dim]\n")

    stories  = []
    reports  = []
    sprint   = Prompt.ask("Sprint name (used for output filename)", default="sprint")

    while True:
        console.print(f"\n[bold]Story {len(stories)+1}[/bold]")
        story = collect_story()
        stories.append(story)

        another = Confirm.ask("\nAdd another story?", default=False)
        if not another:
            break

    console.print(f"\n[dim]Running crew on {len(stories)} story/stories...[/dim]\n")

    for story in stories:
        console.print(f"[dim]Analysing {story.story_id}...[/dim]")
        try:
            report = run_requirements_crew(story)
            reports.append(report)
            print_report(report)
        except Exception as e:
            console.print(f"[red]Failed on {story.story_id}: {e}[/red]")

    if reports:
        print_sprint_summary(reports)
        save_reports(reports, sprint_name=sprint)


def main():
    console.print()
    console.rule("[bold cyan]TPM Requirements Crew[/bold cyan]")
    console.print("[dim]Powered by CrewAI + Groq (Llama 3 70B)[/dim]\n")

    mode = Prompt.ask(
        "Mode",
        choices=["single", "batch"],
        default="single"
    )

    if mode == "single":
        run_single()
    else:
        run_batch()


if __name__ == "__main__":
    main()