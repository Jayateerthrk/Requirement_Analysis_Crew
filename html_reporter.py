"""
html_reporter.py — Generates a clean HTML report from crew output.
Saved alongside the JSON in the output/ folder.
"""

import os
import json
from datetime import datetime


STATUS_COLOURS = {
    "READY":                ("#1a7f4b", "#e6f4ed"),
    "CONDITIONALLY_READY":  ("#92650a", "#fef8e7"),
    "NOT_READY":            ("#c0392b", "#fdf0ee"),
}

RISK_COLOURS = {
    "HIGH":   ("#c0392b", "#fdf0ee"),
    "MEDIUM": ("#92650a", "#fef8e7"),
    "LOW":    ("#1a7f4b", "#e6f4ed"),
}


def _badge(text: str, colour_map: dict, default=("#444", "#f0f0f0")) -> str:
    fg, bg = colour_map.get(text, default)
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 10px;'
        f'border-radius:4px;font-weight:600;font-size:13px;">{text}</span>'
    )


def _score_bar(score: int, colour: str = "#378ADD") -> str:
    return f"""
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="flex:1;background:#e8e8e8;border-radius:4px;height:10px;">
        <div style="width:{score}%;background:{colour};border-radius:4px;height:10px;"></div>
      </div>
      <span style="font-weight:600;font-size:14px;min-width:36px;">{score}/100</span>
    </div>"""


def _section(title: str, colour: str, items: list, icon: str = "•") -> str:
    if not items:
        return ""
    rows = "".join(
        f'<li style="margin:6px 0;line-height:1.5;">{icon} {item}</li>'
        for item in items
    )
    return f"""
    <div style="margin:16px 0;padding:16px;border-left:4px solid {colour};
                background:{colour}18;border-radius:0 8px 8px 0;">
      <div style="font-weight:600;font-size:14px;color:{colour};
                  margin-bottom:8px;text-transform:uppercase;
                  letter-spacing:0.5px;">{title}</div>
      <ul style="margin:0;padding:0;list-style:none;">{rows}</ul>
    </div>"""


def generate_story_card(report: dict) -> str:
    story_id  = report.get("story_id", "Unknown")
    title     = report.get("title", "")
    status    = report.get("dor_status", "UNKNOWN")
    readiness = report.get("readiness_score", 0)
    risk      = report.get("overall_risk_level", "UNKNOWN")
    ambiguity = report.get("ambiguity_score", 0)
    summary   = report.get("tpm_summary", "")
    blockers  = report.get("key_blockers", [])
    risks     = report.get("key_risks", [])
    actions   = report.get("immediate_actions", [])

    status_fg, status_bg = STATUS_COLOURS.get(status, ("#444", "#f0f0f0"))
    risk_fg,   risk_bg   = RISK_COLOURS.get(risk,   ("#444", "#f0f0f0"))

    # Ambiguity bar colour
    amb_colour = "#c0392b" if ambiguity >= 60 else "#92650a" if ambiguity >= 30 else "#1a7f4b"
    read_colour = "#1a7f4b" if readiness >= 80 else "#92650a" if readiness >= 50 else "#c0392b"

    blockers_html = _section("Key Blockers",        "#c0392b", blockers, "✗")
    risks_html    = _section("Key Risks",            "#92650a", risks,    "⚠")
    actions_html  = _section("Immediate Actions",    "#185FA5", actions,  "→")

    summary_html = f"""
    <div style="margin:16px 0;padding:16px;background:#f7f9fc;
                border-radius:8px;border:1px solid #dde3ec;">
      <div style="font-weight:600;font-size:13px;color:#555;
                  margin-bottom:6px;text-transform:uppercase;
                  letter-spacing:0.5px;">TPM Summary</div>
      <p style="margin:0;line-height:1.6;color:#333;">{summary}</p>
    </div>""" if summary else ""

    return f"""
    <div style="background:#fff;border:1px solid #dde3ec;border-radius:12px;
                margin:20px 0;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">

      <!-- Story header -->
      <div style="display:flex;align-items:flex-start;
                  justify-content:space-between;flex-wrap:wrap;gap:8px;
                  margin-bottom:16px;padding-bottom:16px;
                  border-bottom:1px solid #eee;">
        <div>
          <span style="font-size:12px;color:#888;font-weight:500;">{story_id}</span>
          <h2 style="margin:4px 0 0;font-size:18px;font-weight:600;
                     color:#1a1a1a;">{title}</h2>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
          {_badge(status, STATUS_COLOURS)}
          {_badge(risk + " RISK", RISK_COLOURS, ("#444","#f0f0f0"))}
        </div>
      </div>

      <!-- Scores -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
        <div>
          <div style="font-size:12px;color:#888;margin-bottom:4px;font-weight:500;">
            READINESS SCORE</div>
          {_score_bar(readiness, read_colour)}
        </div>
        <div>
          <div style="font-size:12px;color:#888;margin-bottom:4px;font-weight:500;">
            AMBIGUITY SCORE</div>
          {_score_bar(ambiguity, amb_colour)}
        </div>
      </div>

      {blockers_html}
      {risks_html}
      {actions_html}
      {summary_html}
    </div>"""


def generate_sprint_summary_table(reports: list) -> str:
    rows = ""
    for r in reports:
        status   = r.get("dor_status", "UNKNOWN")
        risk     = r.get("overall_risk_level", "UNKNOWN")
        sfg, sbg = STATUS_COLOURS.get(status, ("#444", "#f0f0f0"))
        rfg, rbg = RISK_COLOURS.get(risk,   ("#444", "#f0f0f0"))

        rows += f"""
        <tr style="border-bottom:1px solid #eee;">
          <td style="padding:10px 12px;font-weight:600;color:#333;">
            {r.get("story_id","")}</td>
          <td style="padding:10px 12px;color:#444;">
            {r.get("title","")}</td>
          <td style="padding:10px 12px;">
            <span style="background:{sbg};color:{sfg};padding:2px 8px;
                         border-radius:4px;font-size:12px;font-weight:600;">
              {status}</span></td>
          <td style="padding:10px 12px;">
            <span style="background:{rbg};color:{rfg};padding:2px 8px;
                         border-radius:4px;font-size:12px;font-weight:600;">
              {risk}</span></td>
          <td style="padding:10px 12px;text-align:center;color:#555;">
            {r.get("ambiguity_score",0)}</td>
          <td style="padding:10px 12px;text-align:center;font-weight:600;color:#333;">
            {r.get("readiness_score",0)}/100</td>
        </tr>"""

    total     = len(reports)
    ready     = sum(1 for r in reports if r.get("dor_status") == "READY")
    not_ready = sum(1 for r in reports if r.get("dor_status") == "NOT_READY")
    cond      = total - ready - not_ready

    return f"""
    <div style="background:#fff;border:1px solid #dde3ec;border-radius:12px;
                padding:24px;margin-bottom:24px;
                box-shadow:0 1px 4px rgba(0,0,0,0.06);">
      <h2 style="margin:0 0 16px;font-size:18px;font-weight:600;color:#1a1a1a;">
        Sprint Summary</h2>

      <!-- Stat pills -->
      <div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;">
        <div style="background:#e6f4ed;color:#1a7f4b;padding:8px 16px;
                    border-radius:8px;font-weight:600;">
          {ready} Ready</div>
        <div style="background:#fef8e7;color:#92650a;padding:8px 16px;
                    border-radius:8px;font-weight:600;">
          {cond} Conditional</div>
        <div style="background:#fdf0ee;color:#c0392b;padding:8px 16px;
                    border-radius:8px;font-weight:600;">
          {not_ready} Not Ready</div>
        <div style="background:#f0f0f0;color:#555;padding:8px 16px;
                    border-radius:8px;font-weight:600;">
          {total} Total</div>
      </div>

      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <thead>
          <tr style="background:#f7f9fc;border-bottom:2px solid #dde3ec;">
            <th style="padding:10px 12px;text-align:left;color:#555;
                       font-weight:600;">Story ID</th>
            <th style="padding:10px 12px;text-align:left;color:#555;
                       font-weight:600;">Title</th>
            <th style="padding:10px 12px;text-align:left;color:#555;
                       font-weight:600;">DoR Status</th>
            <th style="padding:10px 12px;text-align:left;color:#555;
                       font-weight:600;">Risk</th>
            <th style="padding:10px 12px;text-align:center;color:#555;
                       font-weight:600;">Ambiguity</th>
            <th style="padding:10px 12px;text-align:center;color:#555;
                       font-weight:600;">Readiness</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


def save_html_report(reports: list, sprint_name: str = "sprint",
                     timestamp: str = None) -> str:
    """Generate and save full HTML report. Returns the file path."""

    os.makedirs("output", exist_ok=True)
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"output/{sprint_name}_{timestamp}.html"

    story_cards = "".join(generate_story_card(r) for r in reports)
    summary_table = generate_sprint_summary_table(reports) if len(reports) > 1 else ""

    generated_at = datetime.now().strftime("%d %b %Y, %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Requirements Crew Report — {sprint_name}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                   Roboto, sans-serif;
      background: #f4f6fa;
      margin: 0;
      padding: 24px;
      color: #333;
    }}
    .container {{ max-width: 860px; margin: 0 auto; }}
    h1 {{ font-size: 24px; font-weight: 700; color: #1a1a1a; margin: 0; }}
    .header {{
      background: #fff;
      border: 1px solid #dde3ec;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .meta {{
      font-size: 13px;
      color: #888;
      margin-top: 6px;
    }}
    @media print {{
      body {{ background: #fff; padding: 0; }}
      .container {{ max-width: 100%; }}
    }}
  </style>
</head>
<body>
  <div class="container">

    <div class="header">
      <h1>TPM Requirements Crew Report</h1>
      <div class="meta">
        Sprint: <strong>{sprint_name}</strong> &nbsp;|&nbsp;
        Generated: <strong>{generated_at}</strong> &nbsp;|&nbsp;
        Stories analysed: <strong>{len(reports)}</strong>
      </div>
    </div>

    {summary_table}
    {story_cards}

    <div style="text-align:center;color:#aaa;font-size:12px;
                margin-top:32px;padding-bottom:24px;">
      Generated by TPM Requirements Crew · CrewAI + Groq
    </div>

  </div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    return filename