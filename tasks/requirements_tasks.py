"""
tasks/requirements_tasks.py
Task definitions for the Requirements Crew.
Each task has a precise expected_output schema — this is what the
next task (and the manager) reads from.
"""

from crewai import Task
from crewai import Agent


def ambiguity_task(agent: Agent, story_text: str) -> Task:
    return Task(
        description=f"""
Analyse the following user story for ambiguity and missing testable conditions.

STORY:
{story_text}

Check for ALL of these:
1. VAGUE_QUALIFIER — words like: quickly, easily, fast, reliably, appropriately,
   sufficient, relevant, user-friendly, simple, seamless, properly, correctly
2. UNDEFINED_ACTOR — "user" without role clarity (admin? guest? logged-in user?)
3. MISSING_AC — no measurable acceptance criterion, or AC that cannot be tested
4. MISSING_ERROR_PATH — no failure, exception, or negative scenario
5. BOUNDARY_MISSING — no numeric limits, thresholds, timeouts, or size constraints
6. UNCLEAR_OWNERSHIP — "system should" without specifying which system or component

Score ambiguity 0-100 where:
  0-30  = low ambiguity, mostly testable
  31-60 = medium, needs some clarification
  61-100 = high, not testable without BA input
""",
        expected_output="""
Valid JSON only. No markdown. No preamble. Exactly this structure:
{
  "story_id": "<from story>",
  "ambiguity_score": <0-100>,
  "overall_risk": "<HIGH|MEDIUM|LOW>",
  "issues": [
    {
      "type": "<VAGUE_QUALIFIER|UNDEFINED_ACTOR|MISSING_AC|MISSING_ERROR_PATH|BOUNDARY_MISSING|UNCLEAR_OWNERSHIP>",
      "phrase": "<exact phrase from story>",
      "explanation": "<why this is a testing problem>",
      "suggested_rewrite": "<concrete better version>"
    }
  ],
  "testable_conditions_missing": ["<condition 1>", "<condition 2>"],
  "summary": "<2 sentences for the BA or PO>"
}
""",
        agent=agent,
    )


def risk_task(agent: Agent, story_text: str, ambiguity_output: str) -> Task:
    return Task(
        description=f"""
Identify delivery, technical, and business risks in this user story.
You have the ambiguity analysis already done — use it to inform your risk assessment.

STORY:
{story_text}

AMBIGUITY ANALYSIS (already completed):
{ambiguity_output}

Assess risks across THREE categories:

DELIVERY risks — will this ship on time?
  - Missing estimates or unclear scope
  - Dependency on another story, team, or external system
  - Skills or tooling not confirmed available

TECHNICAL risks — will this work as built?
  - Integration points with third-party systems or APIs
  - Performance, security, or data concerns
  - Infrastructure assumptions not validated
  - Complexity underestimated

BUSINESS risks — what breaks if this is wrong?
  - User impact if feature ships broken
  - Regulatory or compliance exposure
  - Revenue or reputational impact
  - Downstream systems or teams affected

For each risk: rate likelihood AND impact as HIGH / MEDIUM / LOW.
Then propose a concrete mitigation action.
""",
        expected_output="""
Valid JSON only. No markdown. No preamble. Exactly this structure:
{
  "story_id": "<from story>",
  "overall_risk_level": "<HIGH|MEDIUM|LOW>",
  "risks": [
    {
      "category": "<DELIVERY|TECHNICAL|BUSINESS>",
      "description": "<what the risk is>",
      "likelihood": "<HIGH|MEDIUM|LOW>",
      "impact": "<HIGH|MEDIUM|LOW>",
      "mitigation": "<specific action to reduce this risk>"
    }
  ],
  "dependencies_identified": ["<dependency 1>", "<dependency 2>"],
  "summary": "<2 sentences for the TPM>"
}
""",
        agent=agent,
    )


def dor_task(
    agent: Agent,
    story_text: str,
    ambiguity_output: str,
    risk_output: str
) -> Task:
    return Task(
        description=f"""
Evaluate whether this user story meets Definition of Ready (DoR) for sprint entry.
You have ambiguity analysis and risk assessment already — use both.

STORY:
{story_text}

AMBIGUITY ANALYSIS:
{ambiguity_output}

RISK ASSESSMENT:
{risk_output}

Evaluate against this DoR checklist:
  [ ] Story is written in clear user story format (As a / I want / So that)
  [ ] Acceptance criteria are present and testable by someone who hasn't spoken to the BA
  [ ] All actors are clearly defined (role, permissions, context)
  [ ] Error paths and edge cases are addressed
  [ ] No critical external dependencies unresolved
  [ ] Story is estimable (no hidden unknowns that block sizing)
  [ ] Risks have been identified and acknowledged
  [ ] No HIGH ambiguity issues remaining
  [ ] Story is independently deliverable (not tightly coupled to an unready story)

Scoring:
  80-100 = READY
  50-79  = CONDITIONALLY_READY (list specific conditions)
  0-49   = NOT_READY (list blockers)

Be honest. A story that looks complete but has a HIGH-risk integration
with no mitigation is NOT_READY, even if every checkbox is ticked.
""",
        expected_output="""
Valid JSON only. No markdown. No preamble. Exactly this structure:
{
  "story_id": "<from story>",
  "dor_status": "<READY|NOT_READY|CONDITIONALLY_READY>",
  "readiness_score": <0-100>,
  "checklist": {
    "user_story_format": "<PASS|FAIL|PARTIAL>",
    "testable_ac": "<PASS|FAIL|PARTIAL>",
    "defined_actors": "<PASS|FAIL|PARTIAL>",
    "error_paths": "<PASS|FAIL|PARTIAL>",
    "no_blocking_dependencies": "<PASS|FAIL|PARTIAL>",
    "estimable": "<PASS|FAIL|PARTIAL>",
    "risks_acknowledged": "<PASS|FAIL|PARTIAL>",
    "no_high_ambiguity": "<PASS|FAIL|PARTIAL>",
    "independently_deliverable": "<PASS|FAIL|PARTIAL>"
  },
  "blockers": [
    {
      "criterion": "<which DoR criterion failed>",
      "status": "<MISSING|PARTIAL|UNCLEAR>",
      "what_is_needed": "<exactly what must be added or clarified>"
    }
  ],
  "conditions_to_proceed": ["<if CONDITIONALLY_READY, list conditions>"],
  "recommendation": "<1-2 sentences: what the team should do before sprint planning>"
}
""",
        agent=agent,
    )


def synthesis_task(
    agent: Agent,
    story_text: str,
    ambiguity_output: str,
    risk_output: str,
    dor_output: str
) -> Task:
    return Task(
        description=f"""
Synthesise the three specialist analyses into one consolidated sprint
readiness report for the TPM and Product Owner.

STORY:
{story_text}

AMBIGUITY ANALYSIS:
{ambiguity_output}

RISK ASSESSMENT:
{risk_output}

DEFINITION OF READY EVALUATION:
{dor_output}

Your job:
1. Extract the final DoR status and readiness score
2. Surface only the TOP 3 most critical blockers (not all of them)
3. Surface only the TOP 3 most critical risks
4. List the immediate actions the BA/PO must take before this story
   can enter the sprint — specific, actionable, owned
5. Write a plain-English TPM summary: 3 sentences maximum.
   Suitable for forwarding to a Product Owner or Delivery Manager.
   No jargon. No bullet points in the summary. Just clear prose.
""",
        expected_output="""
Valid JSON only. No markdown. No preamble. Exactly this structure:
{
  "story_id": "<from story>",
  "title": "<story title>",
  "dor_status": "<READY|NOT_READY|CONDITIONALLY_READY>",
  "readiness_score": <0-100>,
  "overall_risk_level": "<HIGH|MEDIUM|LOW>",
  "ambiguity_score": <0-100>,
  "key_blockers": [
    "<blocker 1 — specific and actionable>",
    "<blocker 2>",
    "<blocker 3>"
  ],
  "key_risks": [
    "<risk 1 with category and mitigation hint>",
    "<risk 2>",
    "<risk 3>"
  ],
  "immediate_actions": [
    "<action 1 — who needs to do what before sprint planning>",
    "<action 2>",
    "<action 3>"
  ],
  "tpm_summary": "<3 sentences max. Plain English. No bullet points.>"
}
""",
        agent=agent,
    )