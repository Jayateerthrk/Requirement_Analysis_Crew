"""
pdf_parser.py — Extracts user stories from an uploaded PDF file.

Supports two PDF formats:
1. Structured format — each story has labelled fields
   (Story ID, Title, Description, AC, Points, Sprint)
2. Plain format — stories separated by blank lines or dashes,
   parsed as best-effort using LLM-style heuristics

Returns a list of Story objects ready for the crew.
"""

import re
import pdfplumber
from typing import List
from schema import Story


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract all text from a PDF file object.
    pdf_file can be a file path string or a file-like object
    (Streamlit uploaded files are file-like objects).
    """
    full_text = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text.strip())
    return "\n\n".join(full_text)


def _split_into_blocks(text: str) -> List[str]:
    """
    Split raw PDF text into individual story blocks.
    Tries multiple splitting strategies.
    """
    # Strategy 1: Split on "Story ID" label — most reliable
    if re.search(r"Story\s*ID\s*:", text, re.IGNORECASE):
        parts = re.split(r"(?=Story\s*ID\s*:)", text, flags=re.IGNORECASE)
        blocks = [p.strip() for p in parts if p.strip()]
        if len(blocks) >= 1:
            return blocks

    # Strategy 2: Split on common Jira-style story headers
    # e.g. "PROJ-101", "US-001", "STORY-1"
    if re.search(r"\b[A-Z]+-\d+\b", text):
        parts = re.split(r"(?=\b[A-Z]+-\d+\b)", text)
        blocks = [p.strip() for p in parts if p.strip()]
        if len(blocks) >= 1:
            return blocks

    # Strategy 3: Split on separator lines (---, ===, ***)
    parts = re.split(r"\n[-=*]{3,}\n", text)
    blocks = [p.strip() for p in parts if len(p.strip()) > 30]
    if len(blocks) >= 1:
        return blocks

    # Strategy 4: Split on double blank lines
    parts = re.split(r"\n\s*\n\s*\n", text)
    blocks = [p.strip() for p in parts if len(p.strip()) > 30]
    if len(blocks) >= 1:
        return blocks

    # Fallback: treat entire text as one story
    return [text.strip()]


def _parse_block(block: str, index: int) -> Story:
    """
    Parse a single story text block into a Story object.
    Handles both labelled format and plain prose format.
    """
    lines = block.strip().splitlines()

    story_id    = f"STORY-{index+1:03d}"
    title       = ""
    desc_lines  = []
    acs         = []
    points      = None
    sprint      = None
    mode        = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()

        # Labelled field detection
        if re.match(r"story\s*id\s*:", lower):
            story_id = stripped.split(":", 1)[1].strip()
            mode = None
        elif re.match(r"title\s*:", lower):
            title = stripped.split(":", 1)[1].strip()
            mode = None
        elif re.match(r"description\s*:", lower):
            rest = stripped.split(":", 1)[1].strip()
            if rest:
                desc_lines.append(rest)
            mode = "desc"
        elif re.match(r"ac\s*:", lower) or re.match(r"acceptance criteria\s*:", lower):
            rest = stripped.split(":", 1)[1].strip()
            if rest:
                acs.append(rest)
            mode = "ac"
        elif re.match(r"points\s*:", lower) or re.match(r"story points\s*:", lower):
            try:
                points = int(re.search(r"\d+", stripped).group())
            except (AttributeError, ValueError):
                pass
            mode = None
        elif re.match(r"sprint\s*:", lower):
            sprint = stripped.split(":", 1)[1].strip()
            mode = None

        # Continuation lines
        elif mode == "desc":
            desc_lines.append(stripped)
        elif mode == "ac":
            # AC continuation — lines starting with - or * or numbers
            if re.match(r"^[-*•]\s+", stripped):
                acs.append(re.sub(r"^[-*•]\s+", "", stripped))
            elif re.match(r"^\d+[\.\)]\s+", stripped):
                acs.append(re.sub(r"^\d+[\.\)]\s+", "", stripped))
            else:
                acs.append(stripped)

        # Plain text fallback — first non-empty line is title if not set
        elif not title:
            title = stripped
        elif not desc_lines:
            desc_lines.append(stripped)
            mode = "desc"

    # Auto-detect Jira ID from first line if not labelled
    if story_id == f"STORY-{index+1:03d}":
        match = re.match(r"^([A-Z]+-\d+)\b", block.strip())
        if match:
            story_id = match.group(1)

    description = " ".join(desc_lines).strip()
    if not description and title:
        description = title

    return Story(
        story_id=story_id,
        title=title or story_id,
        description=description,
        acceptance_criteria=acs,
        story_points=points,
        sprint=sprint,
    )


def parse_stories_from_pdf(pdf_file) -> List[Story]:
    """
    Main entry point. Takes a PDF file (path or file-like object)
    and returns a list of Story objects.
    """
    raw_text = extract_text_from_pdf(pdf_file)
    blocks   = _split_into_blocks(raw_text)
    stories  = [_parse_block(block, i) for i, block in enumerate(blocks)]

    # Filter out any blocks that are too short to be real stories
    stories = [s for s in stories if len(s.description) > 20]

    return stories


def stories_to_preview_text(stories: List[Story]) -> str:
    """
    Format parsed stories as readable preview text for the UI.
    Lets user verify parsing before running the crew.
    """
    lines = []
    for i, s in enumerate(stories, 1):
        lines.append(f"{'─'*50}")
        lines.append(f"Story {i}: {s.story_id} — {s.title}")
        lines.append(f"Description: {s.description[:120]}{'...' if len(s.description) > 120 else ''}")
        if s.acceptance_criteria:
            lines.append(f"ACs: {len(s.acceptance_criteria)} found")
        if s.story_points:
            lines.append(f"Points: {s.story_points}")
        if s.sprint:
            lines.append(f"Sprint: {s.sprint}")
    lines.append(f"{'─'*50}")
    lines.append(f"Total stories parsed: {len(stories)}")
    return "\n".join(lines)