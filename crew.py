"""
crew.py — Requirements Crew orchestrator.
Wires agents and tasks. Runs sequentially so each agent
can read the previous agent's output.
"""

import os
import json
import time
from dotenv import load_dotenv
from crewai import Crew, Process

from agents.ambiguity_agent import create_ambiguity_agent
from agents.risk_agent import create_risk_agent
from agents.dor_agent import create_dor_agent
from agents.manager_agent import create_manager_agent
from tasks.requirements_tasks import (
    ambiguity_task,
    risk_task,
    dor_task,
    synthesis_task,
)
from schema import Story

load_dotenv()

# CrewAI expects the API key as an env var and the LLM as a string
# LLM_MODEL = "groq/llama-3.3-70b-versatile"
LLM_MODEL = "huggingface/meta-llama/Llama-3.3-70B-Instruct"


def run_requirements_crew(story: Story) -> dict:
    """
    Run the full requirements crew for a single story.
    Returns the consolidated readiness report as a dict.
    """
    story_text = story.to_text()
    short_story_text = story.to_short_text()

    # --- Create agents (pass model string, not LangChain object) ---
    ambiguity_agent = create_ambiguity_agent(LLM_MODEL)
    risk_agent      = create_risk_agent(LLM_MODEL)
    dor_agent       = create_dor_agent(LLM_MODEL)
    manager_agent   = create_manager_agent(LLM_MODEL)

    # --- Create tasks (sequential — each passes output to next) ---
    task_ambiguity = ambiguity_task(ambiguity_agent, story_text)

    # Risk and DoR tasks reference prior outputs via context and use a compact story summary
    task_risk = risk_task(risk_agent, short_story_text, "{task_ambiguity_output}")
    task_risk.context = [task_ambiguity]

    task_dor = dor_task(dor_agent, short_story_text,
                        "{task_ambiguity_output}",
                        "{task_risk_output}")
    task_dor.context = [task_ambiguity, task_risk]

    task_synthesis = synthesis_task(manager_agent, short_story_text,
                                    "{task_ambiguity_output}",
                                    "{task_risk_output}",
                                    "{task_dor_output}")
    task_synthesis.context = [task_ambiguity, task_risk, task_dor]

    # --- Assemble crew ---
    crew = Crew(
        agents=[ambiguity_agent, risk_agent, dor_agent, manager_agent],
        tasks=[task_ambiguity, task_risk, task_dor, task_synthesis],
        process=Process.sequential,
        verbose=False,
    )

    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            result = crew.kickoff()
            break
        except Exception as e:
            message = str(e)
            if any(keyword in message.lower() for keyword in [
                "ratelimit",
                "rate limit",
                "rate limit reached",
                "too many requests",
                "groqexception",
            ]):
                if attempt == max_attempts:
                    raise
                delay = 10 * attempt
                time.sleep(delay)
                continue
            raise

    # Parse final JSON output
    raw = result.raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())