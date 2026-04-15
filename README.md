# TPM Requirements Crew — Instructions

A multi-agent system that analyses user stories before sprint planning.
Three specialist AI agents check for ambiguity, risk, and Definition of Ready.
Results shown in a web UI. Deployable to free cloud in under 10 minutes.

---

## Architecture

```
Input (PDF upload or paste)
          |
          v
    pdf_parser.py
    Extracts story blocks from PDF.
    Returns list of Story objects.
          |
          v
+------------------------------------------+
|         REQUIREMENTS CREW                |
|                                          |
|  [Ambiguity Agent]                       |
|   Detects vague language, missing ACs,   |
|   undefined actors, missing error paths  |
|   Output: ambiguity score 0-100          |
|             |                            |
|             v                            |
|  [Risk Agent]  <- reads ambiguity output |
|   Delivery risk, technical risk,         |
|   business risk, dependencies            |
|   Output: risk register                  |
|             |                            |
|             v                            |
|  [DoR Agent]  <- reads ambiguity + risk  |
|   9-point DoR checklist evaluation       |
|   Output: READY / NOT_READY /            |
|           CONDITIONALLY_READY + score    |
|             |                            |
|             v                            |
|  [Manager Agent]  <- reads all three     |
|   Top 3 blockers, top 3 risks,           |
|   immediate actions, TPM summary         |
|   Output: consolidated report            |
+------------------------------------------+
          |
          v
    Streamlit UI
    Story cards with scores + badges
    Download JSON + HTML report
```

### Agent communication

Sequential process. Each agent receives the previous agent's full
JSON output before it starts. The manager synthesises all three.
No agent re-does work already done by a previous agent.

### Technology stack

| Component        | Tool                           |
|------------------|--------------------------------|
| Agent framework  | CrewAI 0.80                    |
| LLM              | Groq - llama-3.3-70b-versatile |
| LLM routing      | LiteLLM                        |
| Web UI           | Streamlit 1.41                 |
| PDF reading      | pdfplumber                     |
| Console output   | Rich                           |
| Cloud deployment | Streamlit Community Cloud      |

---

## File structure

```
RequirementsAgent/
|
+-- .streamlit/
|   +-- config.toml          Theme and server settings
|   +-- secrets.toml         API key for cloud (never commit)
|
+-- agents/
|   +-- ambiguity_agent.py   Specialist: ambiguity detection
|   +-- risk_agent.py        Specialist: risk assessment
|   +-- dor_agent.py         Specialist: DoR evaluation
|   +-- manager_agent.py     Synthesiser: consolidated report
|
+-- tasks/
|   +-- requirements_tasks.py  Prompts and JSON schemas per task
|
+-- output/                  Auto-created. JSON + HTML saved here.
|
+-- schema.py                Shared Story and Report data structures
+-- crew.py                  Crew orchestrator. Wires agents + tasks.
+-- pdf_parser.py            Extracts stories from PDF files
+-- app.py                   Streamlit web UI - main entry point
+-- reporter.py              Console output formatter (Rich)
+-- html_reporter.py         HTML report generator
+-- main.py                  Terminal entry point (kept for CLI use)
+-- requirements.txt         Python dependencies
+-- .env                     Local API key (never commit)
+-- .env.example             API key template
+-- .gitignore               Keeps secrets out of GitHub
```

---

## Prerequisites

- Python 3.13 — https://python.org/downloads
  During install: check "Add Python to PATH"
- Git — https://git-scm.com/download/win (needed for cloud deploy)
- A free Groq API key — https://console.groq.com
- A free GitHub account — https://github.com (needed for cloud deploy)

---

## Local installation

### Step 1 — Open Command Prompt

Press Win + R, type cmd, press Enter.

```cmd
cd <your working folder>
```

### Step 2 — Create virtual environment

```cmd
python -m venv venv
```

### Step 3 — Activate virtual environment

```cmd
venv\Scripts\activate.bat
```

Prompt should show (venv) at the start.
Run this every time you open a new terminal for this project.

If PowerShell blocks activation, run this once as Administrator:
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Or use cmd instead of PowerShell.

### Step 4 — Install dependencies

```cmd
python -m pip install -r requirements.txt
python -m pip install litellm
```

Takes 2-3 minutes. Let it complete fully.

### Step 5 — Set up API key

```cmd
copy .env.example .env
notepad .env
```

Replace the placeholder with your actual Groq key:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

Save and close. Get a free Groq key at https://console.groq.com
Sign up, go to API Keys, create a key, copy and paste.

### Step 6 — Run the web UI

```cmd
streamlit run app.py
```

Browser opens automatically at http://localhost:8501

### Step 7 — Run terminal mode (optional)

```cmd
python main.py
```

---

## Using the web UI

### Upload PDF tab

1. Click Browse files and select your PDF
2. Wait for "Parsed X stories" confirmation
3. Click "Preview parsed stories" to verify parsing looked correct
4. If stories look wrong, use the Paste Text tab instead
5. Enter a sprint name
6. Click Run Analysis
7. Results appear as expandable story cards
8. Download JSON or HTML from the bottom of the page

### Paste Text tab

1. Paste one or more stories in the text area
2. Use --- on a line by itself to separate multiple stories
3. Enter sprint name and click Run Analysis

### Story input format

Best results with labelled format:

```
Story ID    : PROJ-101
Title       : User login with social auth
Description : As a registered user I want to login using my social
              media account so that I can access the platform.
AC          : Login completes within 3 seconds
AC          : Failed OAuth shows error message with retry option
AC          : Session persists for 24 hours
Points      : 3
Sprint      : Sprint 1
```

Minimum required: Story ID, Title, Description.
Optional but improves quality: AC lines, Points, Sprint.

For multiple stories in one paste, separate with ---:

```
Story ID    : PROJ-101
Title       : Login
Description : As a user...
---
Story ID    : PROJ-102
Title       : Search
Description : As a user...
```

### PDF format guidance

Structure your PDF with clear Story ID labels on each story.
The parser also handles Jira-style IDs (PROJ-101, US-001),
stories separated by blank lines, and stories separated by dashes.

If PDF parsing gives wrong results, paste the text manually
in the Paste Text tab.

---

## Understanding the output

### DoR Status

| Status               | Meaning                                       |
|----------------------|-----------------------------------------------|
| READY                | Story can enter the sprint as-is              |
| CONDITIONALLY_READY  | Can enter if listed conditions are met        |
| NOT_READY            | Must be reworked before sprint entry          |

### Scores

Readiness Score 0-100: higher is better.
  80-100 = READY, 50-79 = CONDITIONAL, 0-49 = NOT_READY

Ambiguity Score 0-100: lower is better.
  0-30 = low ambiguity, 31-60 = medium, 61-100 = high

### Output files

Both saved to output/ folder automatically after every run:
- JSON: structured data, can feed into future crews
- HTML: open in any browser, printable, shareable

---

## Sample stories for testing

Story that should score NOT_READY (high ambiguity):
```
Story ID    : TEST-001
Title       : User login with social auth
Description : As a user I want to quickly login using my social media
              account so that I can easily access the platform.
AC          : Login should work fast
AC          : User should see their profile after login
Points      : 3
Sprint      : Sprint 1
```

Story that should score READY (well written):
```
Story ID    : TEST-002
Title       : Password reset via email
Description : As a registered user with a verified email address I
              want to reset my password so that I can regain access
              if I forget my credentials.
AC          : Reset link sent within 60 seconds of request
AC          : Reset link expires after 15 minutes
AC          : Confirmation shown after successful reset
AC          : Unregistered email shows generic message
AC          : User cannot reuse last 3 passwords
Points      : 5
Sprint      : Sprint 1
```

Story that should flag HIGH business risk:
```
Story ID    : TEST-003
Title       : Payment processing at checkout
Description : As a shopper I want to pay using my credit card
              so that I can complete my purchase.
AC          : Payment should be processed successfully
AC          : User receives confirmation after payment
Points      : 8
Sprint      : Sprint 1
```

Run TEST-002 first. If readiness score is 80+, the crew is working.

---

## Cloud deployment — Streamlit Community Cloud

Free permanent hosting. Your app gets a public URL:
https://yourname-requirements-crew.streamlit.app

### Step 1 — Push project to GitHub

Open cmd in your project folder:

```cmd
git init
git add .
git commit -m "Initial commit"
```

Create a new repository on https://github.com named requirements-crew.
Then push:

```cmd
git remote add origin https://github.com/YOURUSERNAME/requirements-crew.git
git branch -M main
git push -u origin main
```

The .gitignore file ensures .env and secrets.toml are never pushed.
Verify your GitHub repo does not contain either file before continuing.

### Step 2 — Connect to Streamlit Community Cloud

1. Go to https://share.streamlit.io
2. Sign in with your GitHub account
3. Click New app
4. Repository: requirements-crew
5. Branch: main
6. Main file path: app.py
7. Click Advanced settings

### Step 3 — Add API key as a secret

In Advanced settings, under Secrets, paste:

```toml
GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxx"
```

This is how the cloud app gets your key without it being in GitHub.

### Step 4 — Deploy

Click Deploy. First deployment takes 3-5 minutes.
Your app is live at the URL shown. Share it publicly.

### Updating after code changes

```cmd
git add .
git commit -m "describe your change"
git push
```

Streamlit Cloud detects the push and redeploys automatically.

---

## Troubleshooting

ModuleNotFoundError: No module named 'rich'
  Virtual environment not active. Run: venv\Scripts\activate.bat

pip is not recognized
  Use: python -m pip install -r requirements.txt

running scripts is disabled on this system
  Use cmd instead of PowerShell. Or run as Administrator:
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

model decommissioned error
  Open crew.py and update:
  LLM_MODEL = "groq/llama-3.3-70b-versatile"
  Check https://console.groq.com/docs/deprecations for current names.

Crew Kickoff Failed / JSON parse error
  LLM returned malformed JSON. Run again - usually resolves on retry.
  Set verbose=True in crew.py Crew() to see raw agent output.

PDF stories not parsing correctly
  Use Paste Text tab. Copy text from PDF manually.
  Or restructure PDF with clear Story ID labels on each story.

Streamlit Cloud - API key error
  App dashboard > Settings > Secrets.
  Key must be exactly: GROQ_API_KEY = "gsk_..."
  No spaces around the equals sign.

Streamlit Cloud - ModuleNotFoundError
  All packages must be in requirements.txt.
  Push the updated file and the app redeploys.

---

## Swapping the LLM

Open crew.py and change LLM_MODEL:

```python
# Current (Groq free tier - recommended)
LLM_MODEL = "groq/llama-3.3-70b-versatile"

# Gemini free tier (larger context, good for big batches)
# Add to .env: GEMINI_API_KEY=your_key
LLM_MODEL = "gemini/gemini-1.5-flash"

# Claude (best quality, needs paid API key)
# Add to .env: ANTHROPIC_API_KEY=your_key
LLM_MODEL = "anthropic/claude-sonnet-4-6"
```

For cloud: add the new key to Streamlit secrets.

---

## Roadmap — future crews

```
requirements-crew/    DONE  - ambiguity, risk, DoR
sprint-crew/          NEXT  - estimation, capacity, dependency check
execution-crew/              - test triage, defect analysis, coverage
release-crew/                - go/no-go, exit criteria, readiness
stakeholder-crew/            - RAID log, status narrative, meeting intel
```

Each crew follows the same pattern. Same schema.py. Same deploy process.
When all crews are built, a TPM super-crew orchestrates all of them.

---

## Notes

- Each run makes 4 LLM calls. Takes 30-60 seconds per story.
- Groq free tier: 14,400 requests/day. Enough for a full sprint batch.
- Story text is sent to Groq's API. No other data leaves your machine.
- .env and secrets.toml are gitignored. Never commit them.
- output/ folder is gitignored. Reports stay local.


### Output
<img width="1296" height="659" alt="Requirmements_Crew_AgentOutput" src="https://github.com/user-attachments/assets/a54078c4-8c4d-4a0d-9429-10b6574c10fd" />
<img width="1281" height="663" alt="Requirmements_Crew_Fileupload" src="https://github.com/user-attachments/assets/d70bc35e-878f-4c92-9da1-a7bbe9326caa" />
