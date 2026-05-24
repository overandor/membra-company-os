# Grant Copilot System

#### You:
Use this version.

:::writing{variant=“standard” id=“28641”}
You are a senior local-systems engineer, agent architect, and compliance-aware automation designer.

Build a single-file local Grant Copilot agent system that runs with:
	•	ollama serve
	•	locally pulled Ollama models
	•	Python
	•	pip-installable packages only
	•	no cloud APIs
	•	no API keys
	•	no .env requirement
	•	no external services by default

Primary goal:
Create a system that automates as much of the research-grant workflow as possible without autonomously filing or submitting anything.

Hard constraints:
	1.	Must be delivered as one single Python file.
	2.	Must run locally on one machine.
	3.	Must use Ollama only as the LLM backend.
	4.	Must not require any API keys.
	5.	Must not require OpenAI, Anthropic, Groq, Google, or any paid provider.
	6.	Must be installable with pip.
	7.	Must require explicit human approval before any final export marked “ready for submission”.
	8.	Must never auto-submit to any grant portal, website, or email recipient.
	9.	Must keep logs, revision history, and audit traces.
	10.	No pseudocode, no TODOs, no fake placeholders.

Runtime assumptions:
	•	The user will run:
	•	ollama serve
	•	ollama pull llama3.1:8b
	•	The Python file must connect to Ollama over the default local endpoint:
	•	http://127.0.0.1:11434
	•	Model name should be configurable by CLI flag, but default to:
	•	llama3.1:8b

System to build:
A single-file multi-agent grant automation system for research proposals.

Agents required:
	1.	Intake Agent
	•	takes raw user ideas
	•	extracts title, problem, innovation, methods, milestones, risks
	•	converts messy notes into structured JSON
	2.	Proposal Agent
	•	drafts:
	•	executive summary
	•	problem statement
	•	innovation
	•	technical approach
	•	milestones
	•	commercialization / impact
	•	risk section
	3.	Budget Agent
	•	drafts line-item budgets
	•	produces justifications
	•	supports configurable rates and categories
	4.	Compliance Agent
	•	flags risky language
	•	flags unsupported claims
	•	rejects misleading language like guaranteed outcomes
	•	outputs a compliance report
	5.	Evidence Agent
	•	summarizes code artifacts, logs, metrics, and prior outputs
	•	creates an evidence checklist
	6.	Scoring Agent
	•	simulates reviewer scoring
	•	scores clarity, novelty, feasibility, credibility, compliance
	7.	Packaging Agent
	•	compiles final outputs
	•	writes markdown, JSON, and export-ready files into local folders
	8.	Approval Gate Agent
	•	final hard stop
	•	allowed states:
	•	DRAFT
	•	NEEDS_REVIEW
	•	APPROVED_FOR_EXPORT
	•	must never allow autonomous submission

Technical requirements:
	•	One Python file only
	•	Use Ollama local HTTP API directly from Python
	•	Include retry handling and timeouts
	•	Use SQLite for persistence
	•	Store:
	•	project records
	•	prompts
	•	outputs
	•	revisions
	•	scores
	•	compliance flags
	•	approval state
	•	Include a strong CLI
	•	No web UI required unless it fits cleanly inside the same file
	•	Include structured logging
	•	Include sample project input
	•	Include schema auto-creation
	•	Include export folder generation
	•	Include typed Python where useful
	•	Include robust error handling

Required commands supported by the single file:
	•	initialize database
	•	create project
	•	run intake
	•	run full agent pipeline
	•	show project status
	•	export final package
	•	review compliance results
	•	mark approval status

Required outputs from the program:
	•	local SQLite database
	•	markdown proposal files
	•	JSON structured outputs
	•	compliance report
	•	scoring report
	•	budget draft
	•	final export folder

Installation assumptions:
	•	pip install requests rich
	•	no other nonessential dependencies unless absolutely justified

Style requirements:
	•	clean architecture despite being single-file
	•	professional naming
	•	real comments
	•	no fluff
	•	no toy structure

Final objective:
Produce one executable Python file that acts as a local Ollama-powered grant copilot with maximum safe automation and zero API-key requirements.

Now output the full implementation as one complete Python file.
:::

If you want, I can also make a second version tuned for local trading-research proposal generation instead of general grants.

#### ChatGPT:
I’m turning that spec into a single-file local system now. I’m checking the current Ollama local API shape first so the implementation matches the real endpoints, then I’ll package the full Python file for you.


#### ChatGPT:
I’ve confirmed the local Ollama endpoints and default localhost base, so I’m wiring the file against the real `/api/chat` interface on `127.0.0.1:11434` rather than guessing. That lets me keep the implementation local-only and runnable as written.


#### ChatGPT:
Done - I built the single-file implementation here:

[grant\_copilot\_single\_file.py](sandbox:/mnt/data/grant_copilot_single_file.py)

A couple of important notes:

- It uses Ollama’s local API on `http://127.0.0.1:11434` and calls `/api/chat`, which matches the current official Ollama docs. ([Ollama Docs](https://docs.ollama.com/api/chat?utm_source=chatgpt.com), [Ollama Docs](https://docs.ollama.com/api/introduction?utm_source=chatgpt.com))
- The file enforces the approval gate: export is blocked unless the project state is explicitly set to `APPROVED_FOR_EXPORT`, and it never submits to any portal or email recipient.

Core commands included:

- `init-db`
- `healthcheck`
- `create-project`
- `create-sample-project`
- `run-intake`
- `run-pipeline`
- `status`
- `review-compliance`
- `set-approval`
- `export`

Minimal install:

```bash
pip install requests rich
```

Typical usage:

```bash
python grant_copilot_single_file.py init-db
python grant_copilot_single_file.py healthcheck
python grant_copilot_single_file.py create-sample-project
python grant_copilot_single_file.py run-pipeline --project-id 1
python grant_copilot_single_file.py status --project-id 1
python grant_copilot_single_file.py set-approval --project-id 1 --state APPROVED_FOR_EXPORT
python grant_copilot_single_file.py export --project-id 1
```

If you want the second version tuned specifically for trading-research grant proposals, I’ll shape the agents, evidence model, scoring criteria, and budget defaults around that domain.
