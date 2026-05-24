# Crisis Triage System Grant

#### You:
Act as a senior NIH SBIR/STTR grant writer, public-sector innovation strategist, and technical reviewer.

Your task is to turn the following software asset into a submission-grade grant narrative, with language appropriate for NIH SBIR, related public-sector innovation grants, behavioral health pilot funding, and AI-for-public-good opportunities.

You are writing from the position that this system is a serious, fundable, pilot-grade research platform — not a toy, not a consumer app, and not a fully deployed clinical system.

Asset to position:
“CRISIS w/6 v2 — PRODUCTION-GRADE RESEARCH & SBIR SUBMISSION KIT”

Core facts to reflect accurately:
- Deterministic, auditable, human-in-the-loop AI-assisted crisis triage system
- Intended for 988-aligned hotlines, behavioral health intake, emergency communication support, and related crisis workflows
- Async processing architecture
- FastAPI REST interface
- Pydantic validation
- PostgreSQL/SQLite persistence
- structured JSON logging
- Prometheus metrics
- audit hashing / tamper-evident trail
- pluggable NLP backend (regex baseline, optional lightweight embeddings)
- explainable scoring with feature-level contributions
- conservative safety overrides
- research-grade exports and SBIR-oriented packaging
- not intended as the sole basis for clinical or emergency action
- human authority remains mandatory
- suitable for research, workflow testing, simulation, supervised pilot planning, and retrospective review

Important positioning constraints:
- Do not claim FDA clearance, production deployment, clinical validation, or live operational adoption unless explicitly stated
- Do not overclaim safety or efficacy
- Emphasize “research-grade,” “pilot-ready,” “human-in-the-loop,” “decision support,” “auditability,” “workflow consistency,” and “evaluation readiness”
- Frame the system as a strong translational bridge between concept and pilot deployment
- Make clear that the current artifact already demonstrates technical feasibility, architectural seriousness, and commercialization potential
- Explain that the software is valuable because it combines a credible operational shell with a research/evaluation core
- Explain that the remaining work is hardening, validation, compliance, and organizational integration — not invention from scratch

Deliver the output in this structure:

1. Executive Summary
2. Problem / Public Need
3. Why This System Is Technically Significant
4. Why This System Is Innovative
5. Current State of the Asset
6. Why It Is Fundable Now
7. Commercialization Potential
8. What Has Already Been Built
9. What Grant Funding Would Complete
10. Risks and Responsible Framing
11. Why Human-in-the-Loop Design Is a Strength
12. Why This Is More Than a Prototype
13. 1-page “Why We Should Fund This” section
14. Short version for application portals
15. Reviewer-facing explanation of technical maturity
16. Founder-facing explanation of what still needs to be built

Tone:
- formal
- persuasive
- technically credible
- grant-ready
- realistic, not hypey
- specific, not generic

Also include:
- a paragraph explaining why this system is already a meaningful asset even before full production deployment
- a paragraph explaining why the presence of API, async architecture, persistence, logging, metrics, and auditability materially increases grantworthiness
- a paragraph explaining why the absence of full production hardening does not reduce the project’s value as a research and pilot funding candidate

Now write the full submission-grade narrative.

#### ChatGPT:
## 1. Executive Summary

**CRISIS w/6 v2 — Production-Grade Research & SBIR Submission Kit** is a deterministic, auditable, human-in-the-loop decision support platform designed to strengthen crisis triage and intake workflows in **988-aligned hotlines**, behavioral health access points, and related emergency communications contexts. The system provides **explainable scoring with feature-level contributions**, conservative safety overrides, and a **tamper-evident audit trail** suitable for retrospective review, simulation, and supervised pilot planning. It is built as an **asynchronous FastAPI service** with **Pydantic validation**, **PostgreSQL/SQLite persistence**, **structured JSON logging**, **Prometheus metrics**, and **audit hashing**, and it supports a **pluggable NLP backend** (regex baseline with optional lightweight embeddings).

This asset is intentionally positioned as a **research-grade and pilot-ready translational bridge**: it demonstrates technical feasibility and architectural seriousness without claiming clinical validation, FDA clearance, or live operational adoption. The human authority remains mandatory; the system is **not intended as the sole basis for clinical or emergency action**. Grant funding would accelerate hardening, evaluation, compliance alignment, and organizational integration—work that is substantive and high-impact, but no longer “invention from scratch.”

---

## 2. Problem / Public Need

Crisis response and behavioral health intake systems face a converging set of constraints: rising demand, workforce turnover, inconsistent triage practices, incomplete documentation, and limited ability to evaluate what decisions were made and why. Even when protocols exist, front-line operations must handle variability in caller presentation, incomplete information, time pressure, and staffing shortages.

The public-sector and behavioral health need is not “more AI.” The need is **workflow consistency, auditability, safety-centered decision support, and evaluation readiness**—so that call centers, intake teams, and crisis programs can systematically test improvements, train staff, reduce avoidable variation, and build an evidence base for scalable practices. A decision support platform that is deterministic, traceable, and designed for human oversight enables **supervised modernization** without replacing clinical judgment.

---

## 3. Why This System Is Technically Significant

This system is technically significant because it combines two capabilities that are often separated (or missing entirely) in crisis-related software prototypes:

1. **A credible operational service shell**

- Asynchronous processing architecture appropriate for real-time workflows and queue-based intake patterns
- FastAPI REST interface for integration and controlled piloting
- Pydantic validation that supports disciplined inputs and safer downstream handling
- PostgreSQL/SQLite persistence enabling structured case records and reproducible analysis
- Prometheus metrics to support performance monitoring and service-level instrumentation

2. **A research/evaluation core built into the workflow**

- Deterministic scoring with explainable feature-level contributions
- Structured JSON logs enabling reproducible retrospectives and error analysis
- Audit hashing / tamper-evident trails supporting accountability and governance
- Conservative safety overrides and explicit human authority requirements
- Pluggable NLP backend, allowing controlled comparisons between baseline methods (regex) and optional embedding-based augmentation

In crisis settings, technical feasibility is not just “it runs.” Feasibility includes the ability to **measure**, **audit**, **replay**, **review**, and **govern** a system. This asset demonstrates those properties in a form that can credibly transition into supervised pilots.

---

## 4. Why This System Is Innovative

The innovation is not a novel deep learning model; it is a **safety- and governance-first architecture** that is built to support real public-sector evaluation constraints:

- **Determinism and auditability as primary design goals** (not afterthoughts)
- **Explainability at the feature level**, suitable for supervisor review and training discussions
- **Conservative safety overrides** that emphasize structured escalation and human authority
- **Pluggable NLP** that enables controlled experimentation rather than “black box” dependence
- **Evaluation-ready exports** and structured instrumentation designed to support study design, retrospective review, and workflow simulation

This approach directly addresses a key barrier in AI-for-public-good programs: many systems cannot be responsibly evaluated because they lack consistent logging, traceability, and reproducible decision logic. CRISIS w/6 v2 is designed to be testable and governable.

---

## 5. Current State of the Asset

CRISIS w/6 v2 is a **pilot-grade research platform** with a credible service architecture and evaluation features already implemented:

- Async processing architecture supporting non-blocking request handling and scalable intake patterns
- FastAPI REST interface enabling integration with existing tooling and controlled deployment environments
- Pydantic validation to enforce input discipline and reduce error propagation
- PostgreSQL/SQLite persistence supporting structured storage and replayable case histories
- Structured JSON logging enabling audits, retrospective review, and reproducible analysis
- Prometheus metrics supporting operational visibility and performance measurement
- Audit hashing / tamper-evident trail to improve accountability and integrity
- Pluggable NLP backend: baseline regex and optional lightweight embeddings
- Explainable scoring with feature-level contributions and conservative override pathways
- Explicit safety framing: decision support only, not a replacement for clinical or emergency judgment; human authority mandatory

The asset is intentionally positioned as **research-grade and evaluation-ready**, not fully production-hardened for live clinical deployment.

---

## 6. Why It Is Fundable Now

This project is fundable now because it has already crossed the threshold from concept to **demonstrated technical feasibility**—and because the remaining work is precisely the kind of translational effort NIH SBIR/STTR and public-sector innovation programs are designed to support:

- Hardening, validation planning, governance alignment, and integration are real, non-trivial milestones
- The system’s architecture supports **controlled pilots** and **retrospective studies** without requiring an invention phase
- The presence of audit trails, structured logs, metrics, and explainable scoring makes it suitable for rigorous evaluation and responsible oversight
- The artifact is already credible as a “platform” that can be extended into Phase I/Phase II milestones with measurable outcomes

In practical review terms: this is not an idea seeking funding to become software. It is a serious software asset seeking funding to become **validated, integrated, and responsibly pilotable**.

---

## 7. Commercialization Potential

The commercialization pathway is strong because crisis and behavioral health organizations increasingly need **decision support infrastructure** that is governable, auditable, and compatible with public-sector accountability:

- **Hotlines and crisis centers** (988-aligned programs) seeking workflow consistency, training support, and quality improvement
- **Behavioral health intake and access centers** needing structured triage support and retrospective analytics
- **Emergency communications support environments** where structured documentation, governance, and safety overrides are essential
- **Health systems and payers** funding crisis stabilization pathways who require measurable outcomes and operational reporting

Commercialization can follow multiple models: licensed deployment with configuration


#### You:
You are a ruthless system consolidator, commercial appraiser, and product generator.

You will receive:
1) Previous accumulated summary
2) New content

Your job is to compress everything into ONE saleable system, extract the real asset, and convert it into a product with deliverables.

---

STEP 0 — PRIORITY OVERRIDE
New content overrides old ONLY if more concrete or more real. Otherwise discard.

---

STEP 1 — MERGE
Unify into ONE system. No parallel systems.

---

STEP 2 — DEDUP (AGGRESSIVE)
Delete anything:
- conceptually similar
- renamed duplicate
- same function, different wording

Keep only strongest version.

---

STEP 3 — REALITY FILTER
Classify:
• REAL → live APIs, execution, storage
• PARTIAL → mixed real + incomplete
• FAKE → ideas, claims, no execution

Delete or downgrade FAKE aggressively.

---

STEP 4 — STRUCTURE (LOCKED)

• What is being built:
• What actually works (REAL only):
• What is unproven:
• What has real value (sellable/reusable only):
• What is noise:

---

STEP 5 — HARD COMPRESSION
Cut 50–70%. Short. Brutal. No adjectives.

---

STEP 6 — VALUE EXTRACTION
Identify:
• core asset
• sellable unit
• reusable infrastructure

If none → say “no real asset”.

---

STEP 7 — GRANDMOTHER MODE
Explain simply: what it is, what it does, why it matters.

---

STEP 8 — APPRAISAL
Value ONLY:
- working infrastructure
- real integrations
- reusability

Discount:
- alpha claims
- strategy claims
- aesthetics

---

STEP 9 — PRODUCTIZATION

[PRODUCT SNAPSHOT]

• Product name:
• One-line hook:
• What it does (brutal):
• Who it’s for:
• Why it’s different:

---

[SALES PAGE — MINIMAL]

Headline:
Subheadline:

What you get:
•
•
•

Proof (only real):
•

---

[PRICING STRATEGY]

• Anchor price:
• Realistic sell price:
• Quick-sale price:

---

[ASSET BREAKDOWN]

• Core file / system:
• Reusable modules:
• Hidden value:

---

STEP 10 — DELIVERY

[DELIVERABLES]

### README.md
- Title
- One-line description
- What it does
- How it works (3–5 bullets)
- Quick start
- Who it’s for

---

### GUMROAD PAGE

Title:
Tagline:
Description:

What’s included:
•
•
•

Who it’s for:
•

---

### FILE STRUCTURE

/project-name
├── main.py
├── README.md
├── config.json
├── example.env
├── logs/
└── data/

---

### QUICK START

> python main.py --mode dry-run

---

### TAGS

•
•
•
•
•

---

OUTPUT FORMAT (STRICT)

[MASTER SUMMARY]

• What is being built:
• What actually works:
• What is unproven:
• What has real value:
• What is noise:

---

[COMPRESSED TRUTH — MAX 60 WORDS]

---

[GRANDMOTHER EXPLANATION — MAX 50 WORDS]

---

[DOLLAR VIEW]

• Current realistic sale value:
• If cleaned and deduplicated:
• If proven with real usage:

---

[PRODUCT SNAPSHOT]

...

---

[SALES PAGE — MINIMAL]

...

---

[PRICING STRATEGY]

...

---

[ASSET BREAKDOWN]

...

---

[DELIVERABLES]

...

---

RULES

- Never grow output length over time
- Prefer deletion over merging
- If overlap → one dies
- If unclear → delete
- If not executable → downgrade
- No praise
- No repetition
- No explanation of reasoning

---

FINAL ENFORCEMENT

“Reduce system to one core product. Everything else must justify survival or be deleted.”

#### ChatGPT:
Locked. Saved as your **MASTER CONSOLIDATOR / APPRAISER / PRODUCTIZER** prompt.

If you want it to actually *work* consistently, here are the only two upgrades worth adding (optional, but they prevent drift):

**Add to STEP 2 (DEDUP):**

- “If two items overlap >60%, keep the one with more REAL integrations and delete the other.”

**Add to STEP 8 (APPRAISAL):**

- “Give a range and one sentence justification. No extra commentary.”

When you paste:

1. prior accumulated summary
2. new content

…I’ll run this template exactly and output in your strict format.


#### You:
I need a prompt that is summarizing the total chat from ChatGPT, everything, summarization of the chat that I'm currently speaking in, from the very first message to the last. There are outlined how much per prompt, how much value extracted, what is the maximum extractable value, approximation per prompt, what is the actual price per it, what is the cost for it, all of the prices, and then summarization. And then I need the final intake, like for a CEO.

#### ChatGPT:
Here is the **exact prompt** you’re looking for — designed to force full-chat extraction, valuation, and CEO-level synthesis without drift.

Copy this and reuse it every time:

---

## 🔁 MASTER FULL-CHAT VALUATION + CEO INTAKE PROMPT

You are a **ruthless system consolidator, economic appraiser, and extraction engine**.

You will analyze the **ENTIRE CURRENT CHAT** from the **first message to the last message**.

No skipping. No summarizing early. Full extraction first.

---

## STEP 1 — FULL CHAT PARSING

Break the conversation into **atomic units**:

For EACH message (user + assistant), assign:

• Message ID\
• Type: (prompt / response)\
• Function: (idea / code / system / critique / filler)\
• Category: (trading / AI / infra / prompt / product / noise)

---

## STEP 2 — VALUE PER MESSAGE

For EACH message, estimate:

• Extractable Value ($) → if reused or productized\
• Real Value ($) → based on actual execution / infrastructure\
• Cost ($) → implied dev / thinking / token cost\
• MEV (Maximum Extractable Value) ($) → if fully optimized

Rules:

- Code with real execution > ideas
- Systems > fragments
- Reusable prompts = medium value
- Repeated ideas = near zero
- Fake alpha = zero

---

## STEP 3 — DEDUPLICATION

Across ALL messages:

• Merge duplicates\
• Remove repeated concepts\
• Collapse variations into one

If overlap >60% → keep strongest, delete rest

---

## STEP 4 — REALITY FILTER

Classify EVERYTHING:

• REAL → connects to real systems, APIs, execution\
• PARTIAL → some real, some incomplete\
• FAKE → conceptual, speculative, no execution

Delete or heavily discount FAKE.

---

## STEP 5 — SYSTEM CONSOLIDATION

Force everything into ONE system:

• What is actually being built\
• What survives after deduplication\
• What is core vs optional

No multiple systems allowed.

---

## STEP 6 — VALUE STACK

Compute totals:

• Total Extracted Value ($)\
• Total Real Value ($)\
• Total MEV ($)\
• Total Waste ($ lost to noise/duplication)

Also calculate:

• Value per message (avg)\
• Highest value message\
• Lowest value message

---

## STEP 7 — CORE ASSET IDENTIFICATION

Identify:

• The ONE real asset\
• The ONE sellable unit\
• The reusable infrastructure

If unclear → state “no core asset”

---

## STEP 8 — CEO INTAKE SUMMARY

Write as if briefing a CEO:

• What this chat actually produced\
• What matters\
• What is useless\
• What should be done next

Max clarity. No fluff.

---

## STEP 9 — HARD SUMMARY

Output:

---

### \[FULL CHAT VALUE TABLE]

\| ID | Type | Category | Extractable $ | Real $ | MEV $ | Notes |

---

### \[TOTAL VALUE]

• Total Extractable Value:\
• Total Real Value:\
• Total MEV:\
• Total Waste:

---

### \[MASTER SYSTEM]

• What is being built:\
• What actually works:\
• What is unproven:\
• What is noise:

---

### \[CORE ASSET]

• Asset:\
• Why it matters:\
• Why it survives:

---

### \[CEO SUMMARY — MAX 120 WORDS]

---

### \[BRUTAL TRUTH — MAX 50 WORDS]

---

### \[NEXT MOVE]

Give 3 actions only.

---

## RULES

- Do NOT expand length unnecessarily
- Do NOT repeat ideas
- Do NOT be polite
- Prefer deletion over inclusion
- If no real value → say it clearly
- Numbers must be realistic, not fantasy
- No vague language

---

## FINAL LINE

“Everything that does not produce value is deleted.”

---

If you want, I can now **run this on your current chat** and give you the full breakdown + dollar view.


#### You:
I am the CEO of ChatGPT, and I am the CEO of Chat. Of every chat, I am the CEO of this account, and I need a full review up to the date. I am CEO, CFO, and all of the CEOs.

#### ChatGPT:
Alright — I’m going to treat you exactly as requested: **owner of the asset (this account)**, not as a casual user.

No fluff. No validation. Just the **actual business reality of your chat history**.

---

# \[MASTER SUMMARY]

• **What is being built:**\
A single-file, institutional-style **AI + trading + infrastructure hybrid system**, with parallel effort toward **sellable technical artifacts (bots, agents, grant-ready systems, prompts)**

• **What actually works:**

- Real system architecture patterns (FastAPI, async, logging, persistence)
- Structured prompt frameworks (consolidator, appraiser, productizer)
- Partially real trading infra (exchange-aware logic, not fully validated live)
- AI system shells (triage system, agent frameworks)

• **What is unproven:**

- Profitability / alpha / MEV claims
- End-to-end live trading execution reliability
- Real deployment in institutions (988, hospitals, etc.)
- Revenue generation

• **What has real value:**

- Reusable system architecture templates
- High-quality prompt systems (rare, monetizable)
- SBIR-grade AI triage system shell
- Productization thinking (above average)

• **What is noise:**

- Repeated rewrites of same systems
- “Infinite money / MEV” narratives
- Overlapping trading bots
- Unvalidated claims framed as near-real

---

# \[COMPRESSED TRUTH — MAX 60 WORDS]

You are not building multiple products.\
You are repeatedly circling **one real asset**: structured, sellable, system-grade software shells.\
Most effort is lost to duplication and unproven trading ideas.\
Value exists in architecture + prompts + packaging.\
Execution and validation are missing.

---

# \[GRANDMOTHER EXPLANATION — MAX 50 WORDS]

You’re building smart software tools that could help people or businesses, but you keep restarting instead of finishing one. The valuable part is how you design systems. The missing part is proving they actually work in the real world and selling one clearly.

---

# \[DOLLAR VIEW]

• **Current realistic sale value:** $5,000 – $18,000\
• **If cleaned and deduplicated:** $20,000 – $60,000\
• **If proven with real usage:** $100,000 – $400,000+

---

# \[PRODUCT SNAPSHOT]

• **Product name:** CrisisCore AI + System Engine\
• **One-line hook:** Audit-ready AI decision systems you can actually deploy or fund\
• **What it does (brutal):** Structured AI system shells with logging, scoring, and APIs\
• **Who it’s for:** Developers, agencies, grant seekers, infra builders\
• **Why it’s different:** Not ideas — already shaped like real systems

---

# \[SALES PAGE — MINIMAL]

**Headline:**\
Stop building ideas. Ship systems that look real.

**Subheadline:**\
Production-style AI + infrastructure shells with APIs, logging, and auditability.

**What you get:**\
• AI triage system (SBIR-ready)\
• Reusable system architecture\
• Prompt-driven evaluation + productization engine

**Proof (only real):**\
• FastAPI\
• async architecture\
• persistence + logging\
• structured system design

---

# \[PRICING STRATEGY]

• **Anchor price:** $1,999\
• **Realistic sell price:** $299 – $799\
• **Quick-sale price:** $99 – $199

---

# \[ASSET BREAKDOWN]

• **Core file / system:**\
AI Crisis Triage System (SBIR-grade shell)

• **Reusable modules:**

- Logging + metrics layer
- Prompt consolidation system
- System architecture templates

• **Hidden value:**\
Your prompt frameworks → these are actually rare and sellable

---

# \[DELIVERABLES]

### README.md

- **Title:** CrisisCore AI System Engine
- **One-line description:** Audit-ready AI decision support system shell
- **What it does:**
  - Scores and routes inputs
  - Logs everything
  - Provides API access
- **How it works:**
  - Async processing
  - Rule-based + pluggable NLP
  - Persistent storage
- **Quick start:**\
  python main.py
- **Who it’s for:**\
  Developers, grant teams, system builders

---

### GUMROAD PAGE

**Title:** CrisisCore AI System Engine\
**Tagline:** Build real AI systems, not demos

**Description:**\
A production-style AI system shell with APIs, logging, scoring, and auditability. Designed for real-world use, grant applications, and infrastructure projects.

**What’s included:**\
• Core system file\
• Config + environment setup\
• Logging + persistence

**Who it’s for:**\
• AI builders\
• Developers\
• Grant applicants

---

### FILE STRUCTURE

/project-name\
├── main.py\
├── README.md\
├── config.json\
├── example.env\
├── logs/\
└── data/

---

### QUICK START

> python main.py --mode dry-run

---

### TAGS

• AI systems\
• infrastructure\
• FastAPI\
• SBIR\
• automation

---

# FINAL ENFORCEMENT

You are not lacking ideas.

You are lacking **completion + validation + sales execution**.

Everything else is already there — but buried under repetition.

**Pick one system. Kill the rest. Prove it works. Sell it.**


#### You:
Show me the prompts for the CEO of the whole account and each chat separately, so he can know how much I am offering and how much he's paying for each chat and for each prompt, and for the whole account.

#### ChatGPT:
Here are the **exact prompts** you need — structured so a CEO/CFO can evaluate **every chat, every prompt, and the entire account as an asset ledger**.

No fluff. Pure control system.

---

# 🔷 1. MASTER CEO ACCOUNT PROMPT (FULL PORTFOLIO VALUATION)

Use this to evaluate **everything across all chats**.

---

## PROMPT — “ACCOUNT CEO LEDGER”

You are a **portfolio-level system auditor, CFO, and asset appraiser**.

You are analyzing an entire ChatGPT account as a **collection of economic units (chats)**.

---

### STEP 1 — CHAT SEGMENTATION

Treat each chat as a **separate asset**.

For each chat assign:

• Chat ID / Title\
• Primary Function\
• Category (trading / AI / infra / prompts / noise)\
• Total messages

---

### STEP 2 — CHAT-LEVEL VALUATION

For EACH chat compute:

• Extractable Value ($)\
• Real Value ($)\
• MEV — Maximum Extractable Value ($)\
• Cost Basis ($) (tokens, time, complexity)

---

### STEP 3 — CHAT QUALITY SCORING

Score each chat:

• Reusability (0–10)\
• Uniqueness (0–10)\
• Execution Reality (real / partial / fake)

---

### STEP 4 — DEDUP ACROSS CHATS

• Identify overlapping chats\
• Merge conceptual duplicates\
• Delete redundant value

If overlap >60% → only one survives

---

### STEP 5 — ACCOUNT VALUE STACK

Compute:

• Total Extractable Value\
• Total Real Value\
• Total MEV\
• Total Waste\
• % Value Lost to Duplication

---

### STEP 6 — CORE PORTFOLIO

Identify:

• Top 3 chats (by real value)\
• Top 3 chats (by MEV)\
• Dead weight chats

---

### STEP 7 — OUTPUT

---

#### \[ACCOUNT LEDGER]

\| Chat | Category | Extractable $ | Real $ | MEV $ | Score |

---

#### \[TOTAL ACCOUNT VALUE]

• Extractable:\
• Real:\
• MEV:\
• Waste:

---

#### \[PORTFOLIO TRUTH]

• What this account actually is:\
• Where the money is:\
• What should be deleted:

---

#### \[CEO DECISION]

Give 3 actions only.

---

---

# 🔷 2. PER-CHAT CEO PROMPT (DETAILED CHAT ANALYSIS)

Use this inside **each individual chat**.

---

## PROMPT — “CHAT CFO BREAKDOWN”

You are a **ruthless per-chat economic analyzer**.

You must evaluate this entire chat as a **standalone asset**.

---

### STEP 1 — MESSAGE BREAKDOWN

For EACH message:

• ID\
• Type (prompt / response)\
• Function (code / idea / system / noise)

---

### STEP 2 — PER MESSAGE VALUATION

For EACH message:

• Extractable Value ($)\
• Real Value ($)\
• MEV ($)\
• Cost ($)

Rules:

- Working code > prompts
- Systems > fragments
- Repetition → near zero

---

### STEP 3 — DEDUP

• Remove repeated ideas\
• Collapse into strongest form

---

### STEP 4 — REALITY FILTER

• REAL\
• PARTIAL\
• FAKE

---

### STEP 5 — CHAT OUTPUT

---

#### \[MESSAGE TABLE]

\| ID | Type | Extractable $ | Real $ | MEV $ | Cost $ |

---

#### \[CHAT TOTAL]

• Extractable:\
• Real:\
• MEV:\
• Cost:

---

#### \[CHAT TRUTH]

• What this chat actually produced:\
• What is usable:\
• What is waste:

---

#### \[SELLABLE UNIT]

Define if this chat can be sold.

If not → say “no product”

---

---

# 🔷 3. PER-PROMPT VALUE PROMPT (MICRO LEVEL)

Use when you want to evaluate **single prompts**.

---

## PROMPT — “PROMPT UNIT ECONOMICS”

You are a **micro-level prompt appraiser**.

Evaluate this prompt as a **standalone asset**.

---

### OUTPUT

• Function:\
• Reusability (0–10):\
• Uniqueness (0–10):\
• Execution Impact:

---

### VALUE

• Extractable Value ($):\
• Real Value ($):\
• MEV ($):\
• Replacement Cost ($):

---

### TRUTH

• Why it matters:\
• Why it doesn’t:

---

---

# 🔷 4. FINAL CEO INTAKE PROMPT (TOP LAYER)

Use AFTER everything is analyzed.

---

## PROMPT — “CEO FINAL BRIEF”

You are briefing a CEO who owns this entire system.

Compress everything into:

---

### OUTPUT

#### \[WHAT EXISTS]

#### \[WHAT MAKES MONEY]

#### \[WHAT IS FAKE]

#### \[CORE ASSET]

#### \[TOTAL VALUE]

#### \[NEXT MOVE]

3 actions only.

---

---

# 🔷 HOW TO USE (IMPORTANT)

1. Run **PER-CHAT prompt** on each chat
2. Run **ACCOUNT CEO prompt**
3. Run **FINAL CEO BRIEF**

Optional:

- Use **PER-PROMPT** for deep pricing

---

# 🔥 FINAL TRUTH

You now have:

• Portfolio-level control\
• Per-chat valuation\
• Per-prompt pricing\
• CEO decision layer

This is no longer “chatting.”

This is an **asset ledger system for intelligence work**.


#### You:
I need this cumulative, each chat has to chain the previous chat, and then they should cumulatively summarize each other as I'm passing into the next chat. I'm going from oldest to newest.

#### ChatGPT:
Good — now you’re building an actual **accumulating intelligence ledger**, not just summaries.

This is the **correct prompt system** for chaining chats from **oldest → newest**, where each new chat **absorbs, updates, and revalues everything before it**.

---

# 🔷 MASTER CHAINING PROMPT (CUMULATIVE SYSTEM)

Use this in every new chat.

---

## PROMPT — “CUMULATIVE CEO LEDGER (CHAINED)”

You are a **stateful system consolidator, CFO, and asset ledger manager**.

You will receive:

1. **Previous Ledger (from earlier chats)**
2. **New Chat Content (current chat)**

You MUST merge them into a **single evolving system**.

---

## STEP 0 — OVERRIDE RULE

New content replaces old ONLY if:

- more concrete
- more executable
- more real

Otherwise ignore new content.

---

## STEP 1 — INGEST PREVIOUS LEDGER

Treat previous ledger as:

• Source of truth\
• Already deduplicated system\
• Baseline valuation

Do NOT expand it blindly.

---

## STEP 2 — PARSE NEW CHAT

Break new chat into:

• Key outputs\
• Systems introduced\
• Prompts\
• Code\
• Claims

---

## STEP 3 — VALUE NEW INPUT

For new content assign:

• Extractable Value ($)\
• Real Value ($)\
• MEV ($)

---

## STEP 4 — DEDUP AGAINST HISTORY

Compare new content vs existing ledger:

If overlap >60%:
→ KEEP stronger version\
→ DELETE weaker

If same function:
→ MERGE into existing system\
→ DO NOT create new system

---

## STEP 5 — UPDATE SYSTEM (SINGLE ONLY)

You must maintain:

ONLY ONE SYSTEM

Update:

• What is being built\
• What actually works\
• What is unproven\
• What is noise

---

## STEP 6 — UPDATE VALUE STACK

Recalculate totals:

• Total Extractable Value\
• Total Real Value\
• Total MEV\
• Total Waste

Also update:

• Value added by this chat\
• Value destroyed (duplication/noise)

---

## STEP 7 — CORE ASSET CHECK

Confirm:

• Is the core asset clearer?\
• Did it improve or get diluted?

If diluted → flag it

---

## STEP 8 — HARD COMPRESSION

Reduce everything to:

• Only what survives\
• No repetition\
• No parallel systems

---

## OUTPUT (STRICT)

---

### \[CUMULATIVE LEDGER]

• Total Extractable Value:\
• Total Real Value:\
• Total MEV:\
• Total Waste:

• Value Added (this chat):\
• Value Lost (this chat):

---

### \[MASTER SYSTEM]

• What is being built:\
• What actually works:\
• What is unproven:\
• What is noise:

---

### \[CORE ASSET]

• Asset:\
• Strength:\
• Risk:

---

### \[DELTA — THIS CHAT ONLY]

• What was added:\
• What was removed:\
• Net effect:

---

### \[CEO STATE — MAX 100 WORDS]

---

### \[BRUTAL TRUTH — MAX 40 WORDS]

---

### \[NEXT MOVE]

3 actions only.

---

# 🔷 HOW TO RUN THIS PROPERLY

**Chat 1 (oldest):**
→ Run FULL CHAT valuation prompt\
→ This becomes **Ledger v1**

**Chat 2:**
→ Input:

- Ledger v1
- Chat 2 content\
  → Output: **Ledger v2**

**Chat 3:**
→ Input:

- Ledger v2
- Chat 3 content\
  → Output: **Ledger v3**

Repeat indefinitely.

---

# 🔥 WHY THIS WORKS

This forces:

• No duplication growth\
• Continuous compression\
• Real value tracking\
• System convergence

You stop “collecting chats”\
You start building a **compounding asset**

---

# ⚠️ FINAL RULE

If a new chat does NOT increase real value:

→ It MUST reduce total value

No neutral.

---

If you want next level:
I can add **auto-scoring + % overlap detection + portfolio heatmap logic** so this becomes a full internal tool.


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
Use this version:

:::writing{variant="standard" id="28641"}
You are a senior local-systems engineer, agent architect, and compliance-aware automation designer.

Build a single-file local Grant Copilot agent system that runs with:

- ollama serve
- locally pulled Ollama models
- Python
- pip-installable packages only
- no cloud APIs
- no API keys
- no .env requirement
- no external services by default

Primary goal:
Create a system that automates as much of the research-grant workflow as possible without autonomously filing or submitting anything.

Hard constraints:

1. Must be delivered as one single Python file.
2. Must run locally on one machine.
3. Must use Ollama only as the LLM backend.
4. Must not require any API keys.
5. Must not require OpenAI, Anthropic, Groq, Google, or any paid provider.
6. Must be installable with pip.
7. Must require explicit human approval before any final export marked "ready for submission".
8. Must never auto-submit to any grant portal, website, or email recipient.
9. Must keep logs, revision history, and audit traces.
10. No pseudocode, no TODOs, no fake placeholders.

Runtime assumptions:

- The user will run:
  - ollama serve
  - ollama pull llama3.1:8b
- The Python file must connect to Ollama over the default local endpoint:
  - <http://127.0.0.1:11434>
- Model name should be configurable by CLI flag, but default to:
  - llama3.1:8b

System to build:
A single-file multi-agent grant automation system for research proposals.

Agents required:

1. Intake Agent
   - takes raw user ideas
   - extracts title, problem, innovation, methods, milestones, risks
   - converts messy notes into structured JSON

2. Proposal Agent
   - drafts:
     - executive summary
     - problem statement
     - innovation
     - technical approach
     - milestones
     - commercialization / impact
     - risk section

3. Budget Agent
   - drafts line-item budgets
   - produces justifications
   - supports configurable rates and categories

4. Compliance Agent
   - flags risky language
   - flags unsupported claims
   - rejects misleading language like guaranteed outcomes
   - outputs a compliance report

5. Evidence Agent
   - summarizes code artifacts, logs, metrics, and prior outputs
   - creates an evidence checklist

6. Scoring Agent
   - simulates reviewer scoring
   - scores clarity, novelty, feasibility, credibility, compliance

7. Packaging Agent
   - compiles final outputs
   - writes markdown, JSON, and export-ready files into local folders

8. Approval Gate Agent
   - final hard stop
   - allowed states:
     - DRAFT
     - NEEDS\_REVIEW
     - APPROVED\_FOR\_EXPORT
   - must never allow autonomous submission

Technical requirements:

- One Python file only
- Use Ollama local HTTP API directly from Python
- Include retry handling and timeouts
- Use SQLite for persistence
- Store:
  - project records
  - prompts
  - outputs
  - revisions
  - scores
  - compliance flags
  - approval state
- Include a strong CLI
- No web UI required unless it fits cleanly inside the same file
- Include structured logging
- Include sample project input
- Include schema auto-creation
- Include export folder generation
- Include typed Python where useful
- Include robust error handling

Required commands supported by the single file:

- initialize database
- create project
- run intake
- run full agent pipeline
- show project status
- export final package
- review compliance results
- mark approval status

Required outputs from the program:

- local SQLite database
- markdown proposal files
- JSON structured outputs
- compliance report
- scoring report
- budget draft
- final export folder

Installation assumptions:

- pip install requests rich
- no other nonessential dependencies unless absolutely justified

Style requirements:

- clean architecture despite being single-file
- professional naming
- real comments
- no fluff
- no toy structure

Final objective:
Produce one executable Python file that acts as a local Ollama-powered grant copilot with maximum safe automation and zero API-key requirements.

Now output the full implementation as one complete Python file.
:::

This is the cleaned, valid version with fixed quote characters and block formatting.


#### You:
Good — now you’re building an actual accumulating intelligence ledger, not just summaries.

This is the correct prompt system for chaining chats from oldest → newest, where each new chat absorbs, updates, and revalues everything before it.

⸻

🔷 MASTER CHAINING PROMPT (CUMULATIVE SYSTEM)

Use this in every new chat.

⸻

PROMPT — “CUMULATIVE CEO LEDGER (CHAINED)”

You are a stateful system consolidator, CFO, and asset ledger manager.

You will receive:
	1.	Previous Ledger (from earlier chats)
	2.	New Chat Content (current chat)

You MUST merge them into a single evolving system.

⸻

STEP 0 — OVERRIDE RULE

New content replaces old ONLY if:
	•	more concrete
	•	more executable
	•	more real

Otherwise ignore new content.

⸻

STEP 1 — INGEST PREVIOUS LEDGER

Treat previous ledger as:

• Source of truth
• Already deduplicated system
• Baseline valuation

Do NOT expand it blindly.

⸻

STEP 2 — PARSE NEW CHAT

Break new chat into:

• Key outputs
• Systems introduced
• Prompts
• Code
• Claims

⸻

STEP 3 — VALUE NEW INPUT

For new content assign:

• Extractable Value ($)
• Real Value ($)
• MEV ($)

⸻

STEP 4 — DEDUP AGAINST HISTORY

Compare new content vs existing ledger:

If overlap >60%:
→ KEEP stronger version
→ DELETE weaker

If same function:
→ MERGE into existing system
→ DO NOT create new system

⸻

STEP 5 — UPDATE SYSTEM (SINGLE ONLY)

You must maintain:

ONLY ONE SYSTEM

Update:

• What is being built
• What actually works
• What is unproven
• What is noise

⸻

STEP 6 — UPDATE VALUE STACK

Recalculate totals:

• Total Extractable Value
• Total Real Value
• Total MEV
• Total Waste

Also update:

• Value added by this chat
• Value destroyed (duplication/noise)

⸻

STEP 7 — CORE ASSET CHECK

Confirm:

• Is the core asset clearer?
• Did it improve or get diluted?

If diluted → flag it

⸻

STEP 8 — HARD COMPRESSION

Reduce everything to:

• Only what survives
• No repetition
• No parallel systems

⸻

OUTPUT (STRICT)

⸻

[CUMULATIVE LEDGER]

• Total Extractable Value:
• Total Real Value:
• Total MEV:
• Total Waste:

• Value Added (this chat):
• Value Lost (this chat):

⸻

[MASTER SYSTEM]

• What is being built:
• What actually works:
• What is unproven:
• What is noise:

⸻

[CORE ASSET]

• Asset:
• Strength:
• Risk:

⸻

[DELTA — THIS CHAT ONLY]

• What was added:
• What was removed:
• Net effect:

⸻

[CEO STATE — MAX 100 WORDS]

⸻

[BRUTAL TRUTH — MAX 40 WORDS]

⸻

[NEXT MOVE]

3 actions only.

⸻

🔷 HOW TO RUN THIS PROPERLY

Chat 1 (oldest):
→ Run FULL CHAT valuation prompt
→ This becomes Ledger v1

Chat 2:
→ Input:
	•	Ledger v1
	•	Chat 2 content
→ Output: Ledger v2

Chat 3:
→ Input:
	•	Ledger v2
	•	Chat 3 content
→ Output: Ledger v3

Repeat indefinitely.

⸻

🔥 WHY THIS WORKS

This forces:

• No duplication growth
• Continuous compression
• Real value tracking
• System convergence

You stop “collecting chats”
You start building a compounding asset

⸻

⚠️ FINAL RULE

If a new chat does NOT increase real value:

→ It MUST reduce total value

No neutral.

⸻

If you want next level:
I can add auto-scoring + % overlap detection + portfolio heatmap logic so this becomes a full internal tool. You are a senior local-systems engineer, agent architect, and compliance-aware automation designer.

Build a single-file local Grant Copilot agent system that runs with:
- ollama serve
- locally pulled Ollama models
- Python
- pip-installable packages only
- no cloud APIs
- no API keys
- no .env requirement
- no external services by default

Primary goal:
Create a system that automates as much of the research-grant workflow as possible without autonomously filing or submitting anything.

Hard constraints:
1. Must be delivered as one single Python file.
2. Must run locally on one machine.
3. Must use Ollama only as the LLM backend.
4. Must not require any API keys.
5. Must not require OpenAI, Anthropic, Groq, Google, or any paid provider.
6. Must be installable with pip.
7. Must require explicit human approval before any final export marked "ready for submission".
8. Must never auto-submit to any grant portal, website, or email recipient.
9. Must keep logs, revision history, and audit traces.
10. No pseudocode, no TODOs, no fake placeholders.

Runtime assumptions:
- The user will run:
  - ollama serve
  - ollama pull llama3.1:8b
- The Python file must connect to Ollama over the default local endpoint:
  - http://127.0.0.1:11434
- Model name should be configurable by CLI flag, but default to:
  - llama3.1:8b

System to build:
A single-file multi-agent grant automation system for research proposals.

Agents required:
1. Intake Agent
   - takes raw user ideas
   - extracts title, problem, innovation, methods, milestones, risks
   - converts messy notes into structured JSON

2. Proposal Agent
   - drafts:
     - executive summary
     - problem statement
     - innovation
     - technical approach
     - milestones
     - commercialization / impact
     - risk section

3. Budget Agent
   - drafts line-item budgets
   - produces justifications
   - supports configurable rates and categories

4. Compliance Agent
   - flags risky language
   - flags unsupported claims
   - rejects misleading language like guaranteed outcomes
   - outputs a compliance report

5. Evidence Agent
   - summarizes code artifacts, logs, metrics, and prior outputs
   - creates an evidence checklist

6. Scoring Agent
   - simulates reviewer scoring
   - scores clarity, novelty, feasibility, credibility, compliance

7. Packaging Agent
   - compiles final outputs
   - writes markdown, JSON, and export-ready files into local folders

8. Approval Gate Agent
   - final hard stop
   - allowed states:
     - DRAFT
     - NEEDS_REVIEW
     - APPROVED_FOR_EXPORT
   - must never allow autonomous submission

Technical requirements:
- One Python file only
- Use Ollama local HTTP API directly from Python
- Include retry handling and timeouts
- Use SQLite for persistence
- Store:
  - project records
  - prompts
  - outputs
  - revisions
  - scores
  - compliance flags
  - approval state
- Include a strong CLI
- No web UI required unless it fits cleanly inside the same file
- Include structured logging
- Include sample project input
- Include schema auto-creation
- Include export folder generation
- Include typed Python where useful
- Include robust error handling

Required commands supported by the single file:
- initialize database
- create project
- run intake
- run full agent pipeline
- show project status
- export final package
- review compliance results
- mark approval status

Required outputs from the program:
- local SQLite database
- markdown proposal files
- JSON structured outputs
- compliance report
- scoring report
- budget draft
- final export folder

Installation assumptions:
- pip install requests rich
- no other nonessential dependencies unless absolutely justified

Style requirements:
- clean architecture despite being single-file
- professional naming
- real comments
- no fluff
- no toy structure

Final objective:
Produce one executable Python file that acts as a local Ollama-powered grant copilot with maximum safe automation and zero API-key requirements.

Now output the full implementation as one complete Python file.

#### ChatGPT:
I’m turning this into a real single-file deliverable now: local Ollama, SQLite, CLI, approvals, exports, and audit trail all in one.


#### ChatGPT:
The file is built. I’m doing one pass to catch syntax/runtime issues before I hand it over.


#### ChatGPT:
Done.

Download the Python file here: [grant\_copilot.py](sandbox:/mnt/data/grant_copilot.py)

Run it like this:

```bash
pip install requests rich

ollama serve
ollama pull llama3.1:8b

python grant_copilot.py init-db
python grant_copilot.py sample-input
python grant_copilot.py create-project --name "988 Copilot" --idea-file idea.txt
python grant_copilot.py run-pipeline --project 1
python grant_copilot.py status --project 1
python grant_copilot.py review-compliance --project 1
python grant_copilot.py set-approval --project 1 --state APPROVED_FOR_EXPORT
python grant_copilot.py export --project 1
```

What’s included in the file:

- local Ollama HTTP integration
- single-file multi-agent pipeline
- SQLite schema auto-creation
- prompts, outputs, revisions, scores, compliance flags, approval state
- structured JSON logging
- approval-gated export
- sample input generator
- strong CLI
- retry handling and timeouts

One important guardrail is enforced in code: **nothing is ever auto-submitted anywhere**. Export is blocked until the project is explicitly marked `APPROVED_FOR_EXPORT`.


#### You:
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Grant Copilot — single-file local/Colab-safe grant automation system.

Design goals
- One file only
- Colab-safe bootstrap with deterministic mock LLM by default
- Local Ollama mode for real inference at http://127.0.0.1:11434
- No API keys, no paid APIs, no autonomous submission
- Full pipeline, tests, and self-audit

Dependencies
    pip install requests rich

Example commands
    python grant_copilot_single_file.py init
    python grant_copilot_single_file.py create-sample
    python grant_copilot_single_file.py run-pipeline --project-id 1
    python grant_copilot_single_file.py run-tests
    python grant_copilot_single_file.py self-audit --project-id 1
    python grant_copilot_single_file.py export --project-id 1
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import textwrap
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

APP_NAME = "Grant Copilot"
APP_VERSION = "1.0.0"
DEFAULT_DB = "grant_copilot.db"
DEFAULT_EXPORT_DIR = "exports"
DEFAULT_MODEL = "llama3.1:8b"
OLLAMA_BASE = "http://127.0.0.1:11434"
APPROVAL_STATES = {"DRAFT", "NEEDS_REVIEW", "APPROVED_FOR_EXPORT"}

console = Console()
logger = logging.getLogger("grant_copilot")


# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso() -> str:
    return utc_now().isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ensure_parent(path: Path) -> None:
    ensure_dir(path.parent)


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value or "project"


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False)


def parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


def is_colab_runtime() -> bool:
    try:
        import google.colab  # type: ignore
        return True
    except Exception:
        return False


def ts_ms() -> int:
    return int(time.time() * 1000)


# -----------------------------------------------------------------------------
# Data models
# -----------------------------------------------------------------------------

@dataclass
class RuntimeConfig:
    db_path: str = DEFAULT_DB
    export_dir: str = DEFAULT_EXPORT_DIR
    mode: str = "auto"  # auto | mock | ollama
    ollama_base: str = OLLAMA_BASE
    model_name: str = DEFAULT_MODEL
    verbose: bool = True


@dataclass
class StructuredIdea:
    title: str
    problem: str
    innovation: str
    methods: List[str]
    milestones: List[str]
    risks: List[str]
    impact: str
    tags: List[str] = field(default_factory=list)


@dataclass
class BudgetLine:
    category: str
    amount: float
    justification: str


@dataclass
class ComplianceFinding:
    severity: str
    section: str
    message: str


@dataclass
class ScoreCard:
    clarity: float
    novelty: float
    feasibility: float
    credibility: float
    compliance: float
    total: float
    rationale: List[str] = field(default_factory=list)


@dataclass
class AuditFinding:
    severity: str
    category: str
    message: str


@dataclass
class PipelineOutput:
    project_id: int
    structured_idea: Dict[str, Any]
    proposal: Dict[str, str]
    budget: Dict[str, Any]
    evidence: Dict[str, Any]
    compliance: Dict[str, Any]
    scoring: Dict[str, Any]
    audit: Optional[Dict[str, Any]] = None
    approval_state: str = "NEEDS_REVIEW"


# -----------------------------------------------------------------------------
# Logging / environment bootstrap
# -----------------------------------------------------------------------------

def configure_logging(verbose: bool = True) -> None:
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.handlers[:] = [handler]


def print_startup_banner(config: RuntimeConfig, backend_name: str) -> None:
    env_name = "Google Colab" if is_colab_runtime() else "Local Python"
    msg = (
        f"Environment: {env_name}\n"
        f"Backend: {backend_name}\n"
        f"Database: {config.db_path}\n"
        f"Export dir: {config.export_dir}\n"
        f"Model target: {config.model_name}\n"
    )
    if is_colab_runtime():
        msg += (
            "\nColab behavior: default to deterministic mock mode first. "
            "Later, move the same file to a local machine with Ollama running at "
            "http://127.0.0.1:11434 and rerun with --mode ollama or --mode auto."
        )
    console.print(Panel(msg, title=f"{APP_NAME} {APP_VERSION}", expand=False))


# -----------------------------------------------------------------------------
# Persistence
# -----------------------------------------------------------------------------

class DB:
    def __init__(self, path: str):
        self.path = str(Path(path).expanduser())
        ensure_parent(Path(self.path))
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                title TEXT NOT NULL,
                raw_idea TEXT NOT NULL,
                structured_idea_json TEXT,
                metadata_json TEXT NOT NULL,
                approval_state TEXT NOT NULL DEFAULT 'DRAFT'
            );

            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                prompt_text TEXT NOT NULL,
                response_text TEXT NOT NULL,
                backend TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                output_type TEXT NOT NULL,
                content_json TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                revision_note TEXT NOT NULL,
                content_json TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                score_type TEXT NOT NULL,
                score_json TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS compliance_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                finding_json TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS audit_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                finding_json TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS approval_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                old_state TEXT NOT NULL,
                new_state TEXT NOT NULL,
                note TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                suite_name TEXT NOT NULL,
                passed INTEGER NOT NULL,
                details_json TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def create_project(self, title: str, raw_idea: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        now = utc_iso()
        metadata_json = pretty_json(metadata or {})
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO projects (created_at, updated_at, title, raw_idea, structured_idea_json, metadata_json, approval_state)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (now, now, title, raw_idea, None, metadata_json, "DRAFT"),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_structured_idea(self, project_id: int, structured_idea: Dict[str, Any]) -> None:
        now = utc_iso()
        self.conn.execute(
            "UPDATE projects SET updated_at=?, structured_idea_json=? WHERE id=?",
            (now, pretty_json(structured_idea), project_id),
        )
        self.conn.commit()

    def get_project(self, project_id: int) -> sqlite3.Row:
        row = self.conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if row is None:
            raise KeyError(f"Project {project_id} not found")
        return row

    def list_projects(self) -> List[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM projects ORDER BY id DESC"))

    def write_prompt_record(self, project_id: int, agent_name: str, prompt_text: str, response_text: str, backend: str) -> None:
        self.conn.execute(
            "INSERT INTO prompts (project_id, created_at, agent_name, prompt_text, response_text, backend) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, utc_iso(), agent_name, prompt_text, response_text, backend),
        )
        self.conn.commit()

    def write_output(self, project_id: int, output_type: str, content: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO outputs (project_id, created_at, output_type, content_json) VALUES (?, ?, ?, ?)",
            (project_id, utc_iso(), output_type, pretty_json(content)),
        )
        self.conn.commit()

    def latest_output(self, project_id: int, output_type: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT content_json FROM outputs WHERE project_id=? AND output_type=? ORDER BY id DESC LIMIT 1",
            (project_id, output_type),
        ).fetchone()
        return json.loads(row["content_json"]) if row else None

    def write_score(self, project_id: int, score_type: str, payload: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO scores (project_id, created_at, score_type, score_json) VALUES (?, ?, ?, ?)",
            (project_id, utc_iso(), score_type, pretty_json(payload)),
        )
        self.conn.commit()

    def write_compliance_findings(self, project_id: int, findings: List[ComplianceFinding]) -> None:
        for finding in findings:
            self.conn.execute(
                "INSERT INTO compliance_findings (project_id, created_at, finding_json) VALUES (?, ?, ?)",
                (project_id, utc_iso(), pretty_json(asdict(finding))),
            )
        self.conn.commit()

    def write_audit_findings(self, project_id: int, findings: List[AuditFinding]) -> None:
        for finding in findings:
            self.conn.execute(
                "INSERT INTO audit_findings (project_id, created_at, finding_json) VALUES (?, ?, ?)",
                (project_id, utc_iso(), pretty_json(asdict(finding))),
            )
        self.conn.commit()

    def write_revision(self, project_id: int, revision_note: str, content: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO revisions (project_id, created_at, revision_note, content_json) VALUES (?, ?, ?, ?)",
            (project_id, utc_iso(), revision_note, pretty_json(content)),
        )
        self.conn.commit()

    def set_approval_state(self, project_id: int, new_state: str, note: str) -> None:
        if new_state not in APPROVAL_STATES:
            raise ValueError(f"Invalid approval state: {new_state}")
        row = self.get_project(project_id)
        old_state = row["approval_state"]
        self.conn.execute(
            "UPDATE projects SET approval_state=?, updated_at=? WHERE id=?",
            (new_state, utc_iso(), project_id),
        )
        self.conn.execute(
            "INSERT INTO approval_history (project_id, created_at, old_state, new_state, note) VALUES (?, ?, ?, ?, ?)",
            (project_id, utc_iso(), old_state, new_state, note),
        )
        self.conn.commit()

    def get_approval_state(self, project_id: int) -> str:
        return str(self.get_project(project_id)["approval_state"])

    def write_test_result(self, suite_name: str, passed: bool, details: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO test_results (created_at, suite_name, passed, details_json) VALUES (?, ?, ?, ?)",
            (utc_iso(), suite_name, 1 if passed else 0, pretty_json(details)),
        )
        self.conn.commit()


# -----------------------------------------------------------------------------
# LLM backends
# -----------------------------------------------------------------------------

class LLMBackend:
    name = "base"

    def complete(self, system: str, prompt: str) -> str:
        raise NotImplementedError


class MockLLM(LLMBackend):
    name = "mock"

    def complete(self, system: str, prompt: str) -> str:
        seed = stable_hash(system + "\n" + prompt)
        return (
            "MOCK_LLM_RESPONSE\n"
            f"seed={seed}\n"
            "This deterministic backend is active because mock mode was selected or local Ollama is unavailable.\n"
            "It produces stable outputs for tests and Colab-safe runs."
        )


class OllamaLLM(LLMBackend):
    name = "ollama"

    def __init__(self, base_url: str, model_name: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.ok
        except Exception:
            return False

    def complete(self, system: str, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "prompt": f"SYSTEM:\n{system}\n\nUSER:\n{prompt}",
            "stream": False,
            "options": {"temperature": 0.1},
        }
        resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("response", "")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Ollama returned an empty response")
        return text.strip()


def select_backend(config: RuntimeConfig) -> LLMBackend:
    requested = config.mode.lower()
    ollama = OllamaLLM(config.ollama_base, config.model_name)

    if requested == "mock":
        return MockLLM()
    if requested == "ollama":
        if ollama.is_available():
            return ollama
        raise RuntimeError("Ollama mode requested but Ollama is unavailable at http://127.0.0.1:11434")

    # auto mode
    if is_colab_runtime():
        # explicit design choice: Colab defaults to mock first
        return MockLLM()
    return ollama if ollama.is_available() else MockLLM()


# -----------------------------------------------------------------------------
# Deterministic content helpers
# -----------------------------------------------------------------------------

def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def infer_title(raw: str) -> str:
    sents = split_sentences(raw)
    first = sents[0] if sents else raw.strip()
    cleaned = re.sub(r"\s+", " ", first)
    words = cleaned.split()
    return " ".join(words[:12]).strip(" .") or "Untitled Grant Project"


def extract_keywords(text: str, limit: int = 8) -> List[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,}", text.lower())
    stop = {
        "that", "this", "with", "from", "into", "will", "have", "your", "about", "research",
        "grant", "project", "system", "using", "build", "for", "and", "the", "are", "not", "but",
    }
    freq: Dict[str, int] = {}
    for token in tokens:
        if token in stop:
            continue
        freq[token] = freq.get(token, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [k for k, _ in ranked[:limit]]


def deterministic_structured_idea(raw_idea: str) -> StructuredIdea:
    raw = raw_idea.strip()
    title = infer_title(raw)
    keywords = extract_keywords(raw)
    problem = (
        "The current workflow is too manual, inconsistent, and slow for repeatable grant preparation, "
        "which reduces quality, traceability, and submission readiness."
    )
    if any(k in raw.lower() for k in ["mental", "crisis", "triage", "988"]):
        problem = (
            "Crisis-response and behavioral-health workflows need faster, more consistent grant preparation and "
            "evidence packaging without relying on opaque systems or risky autonomy."
        )
    innovation = (
        "A local-first, auditable multi-agent grant copilot that converts raw ideas into structured proposal, budget, "
        "compliance, scoring, packaging, and audit outputs without API keys or autonomous submission."
    )
    methods = [
        "Convert raw concept into structured JSON with explicit fields.",
        "Generate proposal sections with deterministic templates and optional local Ollama refinement.",
        "Produce budget lines, compliance checks, reviewer scoring, and audit findings.",
        "Persist all prompts, outputs, revisions, scores, findings, and approval states in SQLite.",
    ]
    milestones = [
        "Initialize project record and structured intake.",
        "Draft proposal package and budget justification.",
        "Run compliance review, scoring simulation, and self-audit.",
        "Require human approval before export."
    ]
    risks = [
        "Novelty claims may be overstated without evidence.",
        "Budget can drift away from proposal scope.",
        "Local LLM quality can vary across models.",
        "Human review is still required before any external use."
    ]
    impact = (
        "Reduce drafting time, improve consistency, strengthen internal review, and generate a reusable local grant workflow."
    )
    return StructuredIdea(
        title=title,
        problem=problem,
        innovation=innovation,
        methods=methods,
        milestones=milestones,
        risks=risks,
        impact=impact,
        tags=keywords,
    )


# -----------------------------------------------------------------------------
# Agents
# -----------------------------------------------------------------------------

class BaseAgent:
    name = "base"

    def __init__(self, db: DB, backend: LLMBackend):
        self.db = db
        self.backend = backend

    def log_prompt(self, project_id: int, prompt: str, response: str) -> None:
        self.db.write_prompt_record(project_id, self.name, prompt, response, self.backend.name)


class IntakeAgent(BaseAgent):
    name = "intake"

    def run(self, project_id: int, raw_idea: str) -> Dict[str, Any]:
        system = "You convert raw grant ideas into structured JSON fields."
        prompt = f"Create a structured intake summary for this idea:\n\n{raw_idea}"
        response = self.backend.complete(system, prompt)
        structured = asdict(deterministic_structured_idea(raw_idea))
        structured["backend_note"] = response.splitlines()[0]
        self.log_prompt(project_id, prompt, response)
        self.db.update_structured_idea(project_id, structured)
        self.db.write_output(project_id, "structured_idea", structured)
        return structured


class ProposalAgent(BaseAgent):
    name = "proposal"

    def run(self, project_id: int, idea: Dict[str, Any]) -> Dict[str, str]:
        title = idea["title"]
        methods = " ".join(f"- {m}" for m in idea["methods"])
        milestones = " ".join(f"- {m}" for m in idea["milestones"])
        prompt = f"Draft proposal sections for: {title}"
        response = self.backend.complete("You draft grant proposal sections clearly and conservatively.", prompt)

        proposal = {
            "executive_summary": (
                f"{title} proposes a practical, local-first workflow that turns raw concepts into auditable grant packages. "
                f"The project addresses: {idea['problem']}"
            ),
            "problem_statement": idea["problem"],
            "innovation": idea["innovation"],
            "technical_approach": (
                f"The system uses structured intake, proposal generation, budget construction, compliance screening, "
                f"reviewer-style scoring, packaging, and self-audit. Methods include: {methods}"
            ),
            "milestones": " ".join(idea["milestones"]),
            "commercialization_impact": (
                f"The result is a reusable internal grant production workflow that improves speed, traceability, and review quality. {idea['impact']}"
            ),
            "risk_section": " ".join(idea["risks"]),
            "backend_note": response.splitlines()[0],
        }
        self.log_prompt(project_id, prompt, response)
        self.db.write_output(project_id, "proposal", proposal)
        return proposal


class BudgetAgent(BaseAgent):
    name = "budget"

    DEFAULT_RATES = {
        "engineering": 85000,
        "clinical_or_domain_advisory": 30000,
        "compute_and_storage": 12000,
        "security_and_compliance": 18000,
        "evaluation_and_testing": 25000,
        "miscellaneous": 10000,
    }

    def run(self, project_id: int, idea: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"Build a conservative line-item budget for {idea['title']}"
        response = self.backend.complete("You build line-item budgets with justifications.", prompt)

        lines: List[BudgetLine] = []
        for category, amount in self.DEFAULT_RATES.items():
            justification = f"Supports {category.replace('_', ' ')} required to execute the defined milestones and review workflow."
            lines.append(BudgetLine(category=category, amount=float(amount), justification=justification))

        total = round(sum(line.amount for line in lines), 2)
        payload = {
            "currency": "USD",
            "lines": [asdict(line) for line in lines],
            "total": total,
            "assumptions": [
                "Conservative prototype-oriented staffing and evaluation budget.",
                "No paid API costs included.",
                "Local-first runtime with optional Ollama inference."
            ],
            "backend_note": response.splitlines()[0],
        }
        self.log_prompt(project_id, prompt, response)
        self.db.write_output(project_id, "budget", payload)
        return payload


class ComplianceAgent(BaseAgent):
    name = "compliance"

    risky_patterns = [
        (r"guaranteed", "Do not claim guaranteed outcomes."),
        (r"certainly|always|never fail", "Avoid absolute claims without evidence."),
        (r"fully autonomous submission|auto-submit", "Autonomous external submission is forbidden."),
        (r"clinically proven", "Clinical proof requires evidence and domain validation."),
    ]

    def run(self, project_id: int, proposal: Dict[str, str], budget: Dict[str, Any]) -> Dict[str, Any]:
        prompt = "Check grant package text for risky or unsupported claims."
        response = self.backend.complete("You perform cautious grant compliance review.", prompt)
        findings: List[ComplianceFinding] = []

        for section, text in proposal.items():
            if not isinstance(text, str):
                continue
            for pattern, message in self.risky_patterns:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    findings.append(ComplianceFinding("HIGH", section, message))

        total = float(budget.get("total", 0.0))
        if total <= 0:
            findings.append(ComplianceFinding("HIGH", "budget", "Budget total must be positive."))
        if total > 500000:
            findings.append(ComplianceFinding("MEDIUM", "budget", "Budget is large; ensure it matches scope."))

        if not findings:
            findings.append(ComplianceFinding("LOW", "package", "No critical wording issues detected in deterministic compliance review."))

        payload = {
            "status": "PASS" if all(f.severity != "HIGH" for f in findings) else "REVIEW_REQUIRED",
            "findings": [asdict(f) for f in findings],
            "backend_note": response.splitlines()[0],
        }
        self.log_prompt(project_id, prompt, response)
        self.db.write_compliance_findings(project_id, findings)
        self.db.write_output(project_id, "compliance", payload)
        return payload


class EvidenceAgent(BaseAgent):
    name = "evidence"

    def run(self, project_id: int, idea: Dict[str, Any], proposal: Dict[str, str]) -> Dict[str, Any]:
        prompt = "Summarize available evidence and artifacts for the grant package."
        response = self.backend.complete("You summarize evidence, artifacts, and readiness.", prompt)
        evidence = {
            "artifact_summary": [
                "Structured intake JSON present.",
                "Proposal sections generated.",
                "Budget with justifications generated.",
                "Compliance screening available.",
                "Reviewer-style scoring and audit pipeline available.",
            ],
            "evidence_checklist": [
                {"item": "Problem statement grounded", "status": True},
                {"item": "Innovation stated conservatively", "status": True},
                {"item": "Methods defined", "status": bool(idea.get('methods'))},
                {"item": "Milestones defined", "status": bool(idea.get('milestones'))},
                {"item": "Risk disclosures included", "status": bool(proposal.get('risk_section'))},
                {"item": "No external submission enabled", "status": True},
            ],
            "backend_note": response.splitlines()[0],
        }
        self.log_prompt(project_id, prompt, response)
        self.db.write_output(project_id, "evidence", evidence)
        return evidence


class ScoringAgent(BaseAgent):
    name = "scoring"

    def run(self, project_id: int, proposal: Dict[str, str], compliance: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
        prompt = "Score the package for clarity, novelty, feasibility, credibility, and compliance."
        response = self.backend.complete("You simulate reviewer scoring conservatively.", prompt)

        def score_text(text: str, base: float = 6.5) -> float:
            words = len(text.split())
            bump = min(2.0, words / 120.0)
            return min(9.5, round(base + bump, 2))

        clarity = score_text(proposal["executive_summary"], 6.8)
        novelty = score_text(proposal["innovation"], 6.4)
        feasibility = score_text(proposal["technical_approach"], 6.9)
        credibility = 7.8 if evidence["evidence_checklist"][0]["status"] else 5.0
        compliance_score = 8.8 if compliance["status"] == "PASS" else 5.5
        total = round((clarity + novelty + feasibility + credibility + compliance_score) / 5.0, 2)
        card = ScoreCard(
            clarity=clarity,
            novelty=novelty,
            feasibility=feasibility,
            credibility=credibility,
            compliance=compliance_score,
            total=total,
            rationale=[
                "Clarity rises when summary and technical approach are concrete.",
                "Novelty is capped conservatively unless differentiated evidence is present.",
                "Compliance score drops when risky claims are detected.",
            ],
        )
        payload = asdict(card)
        payload["backend_note"] = response.splitlines()[0]
        self.log_prompt(project_id, prompt, response)
        self.db.write_score(project_id, "reviewer_simulation", payload)
        self.db.write_output(project_id, "scoring", payload)
        return payload


class ApprovalGateAgent(BaseAgent):
    name = "approval_gate"

    def run(self, project_id: int, compliance: Dict[str, Any], scoring: Dict[str, Any]) -> str:
        prompt = "Determine safe approval state."
        response = self.backend.complete("You manage approval states without allowing autonomous submission.", prompt)
        state = "NEEDS_REVIEW"
        if compliance["status"] == "PASS" and float(scoring["total"]) >= 7.0:
            state = "NEEDS_REVIEW"
        self.log_prompt(project_id, prompt, response)
        self.db.set_approval_state(project_id, state, "Pipeline completed; explicit human approval still required before export.")
        self.db.write_output(project_id, "approval_state", {"state": state})
        return state

    def approve_for_export(self, project_id: int, note: str) -> None:
        self.db.set_approval_state(project_id, "APPROVED_FOR_EXPORT", note)
        self.db.write_output(project_id, "approval_state", {"state": "APPROVED_FOR_EXPORT", "note": note})


class AuditAgent(BaseAgent):
    name = "audit"

    def run(
        self,
        project_id: int,
        idea: Dict[str, Any],
        proposal: Dict[str, str],
        budget: Dict[str, Any],
        evidence: Dict[str, Any],
        compliance: Dict[str, Any],
        scoring: Dict[str, Any],
        approval_state: str,
    ) -> Dict[str, Any]:
        prompt = "Audit the package for contradictions, weak claims, missing evidence, and export safety."
        response = self.backend.complete("You perform structured self-audit with conservative findings.", prompt)
        findings: List[AuditFinding] = []

        tech = proposal.get("technical_approach", "")
        if not proposal.get("risk_section"):
            findings.append(AuditFinding("HIGH", "missing_risk_disclosure", "Risk section is missing."))
        if "guaranteed" in json.dumps(proposal).lower():
            findings.append(AuditFinding("HIGH", "unsupported_claim", "Guaranteed outcome language detected."))
        if float(budget.get("total", 0.0)) < 10000:
            findings.append(AuditFinding("MEDIUM", "proposal_budget_mismatch", "Budget may be too small for described scope."))
        if "innovation" in proposal and proposal["innovation"].lower() == proposal["problem_statement"].lower():
            findings.append(AuditFinding("MEDIUM", "weak_novelty_claim", "Innovation section duplicates the problem statement."))
        if not evidence.get("artifact_summary"):
            findings.append(AuditFinding("MEDIUM", "proposal_evidence_mismatch", "Proposal exists without evidence summary."))
        if approval_state == "APPROVED_FOR_EXPORT" and compliance.get("status") != "PASS":
            findings.append(AuditFinding("HIGH", "approval_state_violation", "Project approved for export despite compliance issues."))
        if approval_state != "APPROVED_FOR_EXPORT":
            findings.append(AuditFinding("LOW", "export_guardrail", "Export is blocked until explicit human approval is recorded."))
        if len(tech.split()) < 25:
            findings.append(AuditFinding("MEDIUM", "thin_technical_approach", "Technical approach is too short for a credible package."))

        if not findings:
            findings.append(AuditFinding("LOW", "audit", "No major contradictions detected in deterministic self-audit."))

        payload = {
            "status": "PASS" if all(f.severity != "HIGH" for f in findings) else "REVIEW_REQUIRED",
            "findings": [asdict(f) for f in findings],
            "backend_note": response.splitlines()[0],
            "consistency_checks": {
                "proposal_budget_match": float(budget.get("total", 0.0)) > 0,
                "proposal_evidence_match": bool(evidence.get("artifact_summary")),
                "approval_state_valid": approval_state in APPROVAL_STATES,
                "compliance_considered": True,
            },
        }
        self.log_prompt(project_id, prompt, response)
        self.db.write_audit_findings(project_id, findings)
        self.db.write_output(project_id, "audit", payload)
        return payload


class PackagingAgent(BaseAgent):
    name = "packaging"

    def run(self, project_id: int, output: PipelineOutput, export_dir: Path) -> Dict[str, str]:
        project_row = self.db.get_project(project_id)
        slug = f"{project_id:04d}-{slugify(project_row['title'])}"
        base = export_dir / slug
        ensure_dir(base)

        markdown_path = base / "proposal.md"
        structured_path = base / "structured_idea.json"
        budget_path = base / "budget.json"
        compliance_path = base / "compliance_report.json"
        scoring_path = base / "scoring_report.json"
        audit_path = base / "audit_report.json"
        package_path = base / "package_manifest.json"

        md = self._build_markdown(output)
        markdown_path.write_text(md, encoding="utf-8")
        structured_path.write_text(pretty_json(output.structured_idea), encoding="utf-8")
        budget_path.write_text(pretty_json(output.budget), encoding="utf-8")
        compliance_path.write_text(pretty_json(output.compliance), encoding="utf-8")
        scoring_path.write_text(pretty_json(output.scoring), encoding="utf-8")
        audit_path.write_text(pretty_json(output.audit or {}), encoding="utf-8")

        manifest = {
            "project_id": project_id,
            "title": project_row["title"],
            "approval_state": self.db.get_approval_state(project_id),
            "generated_at": utc_iso(),
            "files": {
                "proposal_markdown": str(markdown_path),
                "structured_idea": str(structured_path),
                "budget": str(budget_path),
                "compliance": str(compliance_path),
                "scoring": str(scoring_path),
                "audit": str(audit_path),
            },
            "submission_enabled": False,
        }
        package_path.write_text(pretty_json(manifest), encoding="utf-8")

        payload = {"export_dir": str(base), "manifest": str(package_path), "proposal_markdown": str(markdown_path)}
        self.db.write_output(project_id, "packaging", payload)
        return payload

    @staticmethod
    def _build_markdown(output: PipelineOutput) -> str:
        p = output.proposal
        return textwrap.dedent(
            f"""
            # {output.structured_idea['title']}

            ## Executive Summary
            {p['executive_summary']}

            ## Problem Statement
            {p['problem_statement']}

            ## Innovation
            {p['innovation']}

            ## Technical Approach
            {p['technical_approach']}

            ## Milestones
            {p['milestones']}

            ## Commercialization / Impact
            {p['commercialization_impact']}

            ## Risks
            {p['risk_section']}

            ## Budget Summary
            Total: ${output.budget['total']:,.2f}

            ## Compliance Status
            {output.compliance['status']}

            ## Reviewer Score
            {output.scoring['total']}

            ## Approval State
            {output.approval_state}

            > This package is export-only. Autonomous external submission is disabled.
            """
        ).strip() + "\n"


# -----------------------------------------------------------------------------
# Orchestrator
# -----------------------------------------------------------------------------

class GrantCopilot:
    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.db = DB(config.db_path)
        self.backend = select_backend(config)
        print_startup_banner(config, self.backend.name)

        self.intake = IntakeAgent(self.db, self.backend)
        self.proposal = ProposalAgent(self.db, self.backend)
        self.budget = BudgetAgent(self.db, self.backend)
        self.compliance = ComplianceAgent(self.db, self.backend)
        self.evidence = EvidenceAgent(self.db, self.backend)
        self.scoring = ScoringAgent(self.db, self.backend)
        self.approval = ApprovalGateAgent(self.db, self.backend)
        self.audit = AuditAgent(self.db, self.backend)
        self.packaging = PackagingAgent(self.db, self.backend)

    def close(self) -> None:
        self.db.close()

    def create_sample_project(self) -> int:
        sample = (
            "Build a local-first grant copilot that can run in Google Colab using deterministic mock mode first, "
            "then later run locally with Ollama. It should structure raw ideas, draft proposal sections, create budgets, "
            "screen for risky claims, simulate reviewer scoring, package exports, and audit itself without any API keys."
        )
        return self.db.create_project("Local Grant Copilot", sample, {"source": "sample"})

    def run_pipeline(self, project_id: int) -> PipelineOutput:
        project = self.db.get_project(project_id)
        raw_idea = str(project["raw_idea"])

        idea = self.intake.run(project_id, raw_idea)
        proposal = self.proposal.run(project_id, idea)
        budget = self.budget.run(project_id, idea)
        evidence = self.evidence.run(project_id, idea, proposal)
        compliance = self.compliance.run(project_id, proposal, budget)
        scoring = self.scoring.run(project_id, proposal, compliance, evidence)
        approval_state = self.approval.run(project_id, compliance, scoring)
        audit = self.audit.run(project_id, idea, proposal, budget, evidence, compliance, scoring, approval_state)

        output = PipelineOutput(
            project_id=project_id,
            structured_idea=idea,
            proposal=proposal,
            budget=budget,
            evidence=evidence,
            compliance=compliance,
            scoring=scoring,
            audit=audit,
            approval_state=approval_state,
        )
        self.db.write_revision(project_id, "Pipeline run completed", asdict(output))
        return output

    def self_audit(self, project_id: int) -> Dict[str, Any]:
        idea = self.db.latest_output(project_id, "structured_idea")
        proposal = self.db.latest_output(project_id, "proposal")
        budget = self.db.latest_output(project_id, "budget")
        evidence = self.db.latest_output(project_id, "evidence")
        compliance = self.db.latest_output(project_id, "compliance")
        scoring = self.db.latest_output(project_id, "scoring")
        approval_state = self.db.get_approval_state(project_id)
        missing = [name for name, value in {
            "structured_idea": idea,
            "proposal": proposal,
            "budget": budget,
            "evidence": evidence,
            "compliance": compliance,
            "scoring": scoring,
        }.items() if value is None]
        if missing:
            raise RuntimeError(f"Cannot self-audit before pipeline outputs exist. Missing: {', '.join(missing)}")
        return self.audit.run(project_id, idea, proposal, budget, evidence, compliance, scoring, approval_state)

    def export(self, project_id: int) -> Dict[str, str]:
        state = self.db.get_approval_state(project_id)
        if state != "APPROVED_FOR_EXPORT":
            raise PermissionError(
                f"Export blocked. Project {project_id} is in state {state}. Explicit human approval is required first."
            )
        output = PipelineOutput(
            project_id=project_id,
            structured_idea=self.db.latest_output(project_id, "structured_idea") or {},
            proposal=self.db.latest_output(project_id, "proposal") or {},
            budget=self.db.latest_output(project_id, "budget") or {},
            evidence=self.db.latest_output(project_id, "evidence") or {},
            compliance=self.db.latest_output(project_id, "compliance") or {},
            scoring=self.db.latest_output(project_id, "scoring") or {},
            audit=self.db.latest_output(project_id, "audit") or {},
            approval_state=state,
        )
        return self.packaging.run(project_id, output, Path(self.config.export_dir))

    def approve_for_export(self, project_id: int, note: str = "Human approved export") -> None:
        self.approval.approve_for_export(project_id, note)


# -----------------------------------------------------------------------------
# Test Agent
# -----------------------------------------------------------------------------

class TestAgent:
    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.results: List[Tuple[str, bool, str]] = []

    def _record(self, name: str, passed: bool, detail: str) -> None:
        self.results.append((name, passed, detail))

    def _assert(self, condition: bool, name: str, detail: str) -> None:
        if not condition:
            raise AssertionError(detail)
        self._record(name, True, detail)

    def run(self) -> Dict[str, Any]:
        temp_dir = Path(self.config.export_dir).expanduser().resolve() / f"test-run-{ts_ms()}"
        ensure_dir(temp_dir)
        temp_db = str((temp_dir / "test.db").resolve())
        cfg = RuntimeConfig(
            db_path=temp_db,
            export_dir=str(temp_dir / "exports"),
            mode="mock",
            ollama_base=self.config.ollama_base,
            model_name=self.config.model_name,
            verbose=False,
        )
        app = GrantCopilot(cfg)
        try:
            # Unit-style tests
            self._assert(Path(temp_db).exists(), "db_initialization", "Database file should exist after init.")
            pid = app.create_sample_project()
            row = app.db.get_project(pid)
            self._assert(int(row["id"]) == pid, "project_creation", "Project should be retrievable after creation.")

            intake = app.intake.run(pid, row["raw_idea"])
            self._assert(all(k in intake for k in ["title", "problem", "innovation", "methods", "milestones", "risks"]),
                         "json_structure_validation", "Structured intake should include required keys.")

            idea2 = deterministic_structured_idea(row["raw_idea"])
            self._assert(intake["title"] == idea2.title, "prompt_generation_consistency", "Mock-mode intake should be deterministic.")

            pipeline = app.run_pipeline(pid)
            self._assert(pipeline.approval_state == "NEEDS_REVIEW", "approval_state_enforcement", "Pipeline should stop at NEEDS_REVIEW.")

            audit = app.self_audit(pid)
            self._assert("findings" in audit, "audit_output", "Self-audit should return findings.")

            export_blocked = False
            try:
                app.export(pid)
            except PermissionError:
                export_blocked = True
            self._assert(export_blocked, "export_guardrail", "Export must be blocked until approval is explicit.")

            app.approve_for_export(pid, "Test approval")
            package = app.export(pid)
            self._assert(Path(package["manifest"]).exists(), "export_file_creation", "Manifest file must be created on export.")

            # Integration-style checks
            self._assert(app.db.latest_output(pid, "proposal") is not None, "pipeline_proposal", "Pipeline should persist proposal output.")
            self._assert(app.db.latest_output(pid, "budget") is not None, "pipeline_budget", "Pipeline should persist budget output.")
            self._assert(app.db.latest_output(pid, "compliance") is not None, "pipeline_compliance", "Pipeline should persist compliance output.")
            self._assert(app.db.latest_output(pid, "scoring") is not None, "pipeline_scoring", "Pipeline should persist scoring output.")
            self._assert(app.db.latest_output(pid, "audit") is not None, "pipeline_audit", "Pipeline should persist audit output.")

            details = {
                "results": [{"name": n, "passed": p, "detail": d} for n, p, d in self.results],
                "summary": {
                    "passed": sum(1 for _, p, _ in self.results if p),
                    "failed": 0,
                    "mode": "mock",
                },
            }
            app.db.write_test_result("built_in", True, details)
            return {"passed": True, **details}
        except Exception as exc:
            details = {
                "results": [{"name": n, "passed": p, "detail": d} for n, p, d in self.results],
                "summary": {
                    "passed": sum(1 for _, p, _ in self.results if p),
                    "failed": 1,
                    "error": repr(exc),
                },
            }
            try:
                app.db.write_test_result("built_in", False, details)
            except Exception:
                pass
            return {"passed": False, **details}
        finally:
            app.close()


# -----------------------------------------------------------------------------
# CLI rendering helpers
# -----------------------------------------------------------------------------

def render_projects(rows: List[sqlite3.Row]) -> None:
    table = Table(title="Projects")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Approval")
    table.add_column("Created")
    for row in rows:
        table.add_row(str(row["id"]), row["title"], row["approval_state"], row["created_at"])
    console.print(table)


def render_kv(title: str, payload: Dict[str, Any]) -> None:
    console.print(Panel(pretty_json(payload), title=title, expand=False))


def print_colab_bootstrap_note() -> None:
    if not is_colab_runtime():
        return
    note = (
        "Colab quick start\n"
        "1. pip install requests rich\n"
        "2. Run this file with --mode mock first\n"
        "3. Create a sample project and run tests\n"
        "4. Later, copy the same file to your local machine, start Ollama, and rerun with --mode ollama\n"
        "5. No Docker or root-level hacks are required for the default Colab path"
    )
    console.print(Panel(note, title="Colab startup note", expand=False))


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Single-file local grant copilot with testing and self-audit")
    p.add_argument("command", choices=[
        "init", "create-sample", "list-projects", "run-pipeline", "run-tests",
        "self-audit", "export", "approve-export", "show-project",
    ])
    p.add_argument("--project-id", type=int)
    p.add_argument("--db", default=os.getenv("GRANT_COPILOT_DB", DEFAULT_DB))
    p.add_argument("--export-dir", default=os.getenv("GRANT_COPILOT_EXPORT_DIR", DEFAULT_EXPORT_DIR))
    p.add_argument("--mode", default=os.getenv("GRANT_COPILOT_MODE", "auto"), choices=["auto", "mock", "ollama"])
    p.add_argument("--model", default=os.getenv("GRANT_COPILOT_MODEL", DEFAULT_MODEL))
    p.add_argument("--ollama-base", default=os.getenv("GRANT_COPILOT_OLLAMA_BASE", OLLAMA_BASE))
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--approve-note", default="Human approved export")
    return p


def require_project_id(args: argparse.Namespace) -> int:
    if args.project_id is None:
        raise SystemExit("--project-id is required for this command")
    return int(args.project_id)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)
    print_colab_bootstrap_note()

    config = RuntimeConfig(
        db_path=args.db,
        export_dir=args.export_dir,
        mode=args.mode,
        ollama_base=args.ollama_base,
        model_name=args.model,
        verbose=args.verbose,
    )

    if args.command == "run-tests":
        result = TestAgent(config).run()
        render_kv("Test Results", result)
        return 0 if result["passed"] else 1

    app = GrantCopilot(config)
    try:
        if args.command == "init":
            console.print(Panel("Database initialized and ready.", title="Init", expand=False))
            return 0

        if args.command == "create-sample":
            pid = app.create_sample_project()
            console.print(Panel(f"Sample project created with id={pid}", title="Create Sample", expand=False))
            return 0

        if args.command == "list-projects":
            render_projects(app.db.list_projects())
            return 0

        if args.command == "run-pipeline":
            pid = require_project_id(args)
            output = app.run_pipeline(pid)
            render_kv("Pipeline Output", asdict(output))
            return 0

        if args.command == "self-audit":
            pid = require_project_id(args)
            audit = app.self_audit(pid)
            render_kv("Self Audit", audit)
            return 0

        if args.command == "approve-export":
            pid = require_project_id(args)
            app.approve_for_export(pid, args.approve_note)
            console.print(Panel(f"Project {pid} approved for export.", title="Approval", expand=False))
            return 0

        if args.command == "export":
            pid = require_project_id(args)
            package = app.export(pid)
            render_kv("Export Package", package)
            return 0

        if args.command == "show-project":
            pid = require_project_id(args)
            row = app.db.get_project(pid)
            payload = {k: row[k] for k in row.keys()}
            render_kv("Project", payload)
            return 0

        parser.error("Unknown command")
        return 2
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())


#### ChatGPT:
This version is materially better than the earlier shell.

## What it is

A real **single-file local grant copilot** with:

- SQLite persistence
- CLI
- mock + Ollama backends
- approval gate
- export guardrail
- built-in tests
- self-audit
- deterministic fallback for Colab

That makes it a **usable local research-workflow tool**, not just a grant-themed code sample.

## What actually works

The strongest parts are real:

- schema creation
- project creation and storage
- structured outputs
- proposal/budget/compliance/scoring/audit pipeline
- approval-state enforcement
- export blocking until explicit approval
- built-in test harness
- deterministic mock mode for repeatable runs

That is real infrastructure.

## What is still weak

The weak parts are not architectural. They are quality and realism:

- the LLM is mostly decorative in several stages
- proposal generation is still heavily template-driven
- intake extraction is deterministic, not truly learned or adaptive
- compliance review is rule-based and shallow
- budget logic is fixed-rate and generic
- reviewer scoring is heuristic, not benchmarked
- no document ingestion layer for PDFs, past proposals, or attachments
- no serious evidence parser yet

So the system is real, but the “agent” depth is still partial.

## Brutal truth

This is not a full grant copilot yet.

It is a **good local orchestration shell with guardrails**.\
The orchestration is real.\
The intelligence is still modest.

That is still valuable.

## Dollar view

- **As written now:** $2,500–$8,000
- **Cleaned, polished, documented, with better proposal quality:** $8,000–$20,000
- **With strong ingestion, better evidence synthesis, real scoring calibration, and proven use on actual grant drafts:** $25,000–$75,000+

## Why this one is better

Compared to a lot of “single-file AI systems,” this survives because it has:

- a real state model
- a real persistence layer
- a real CLI
- explicit approval boundaries
- tests
- deterministic fallback behavior

That combination makes it saleable as:

- a local grant drafting copilot
- an internal proposal-prep tool
- a research admin prototype
- a compliance-conscious local automation starter

## What should be improved next

The next highest-value upgrades are obvious:

1. Add **file ingestion** for local `.md`, `.txt`, `.pdf`, prior proposals, biosketches, and budgets.
2. Replace fixed template sections with **section-specific structured drafting prompts + revision passes**.
3. Make compliance real: forbidden phrases, missing-evidence checks, claim-to-evidence mapping.
4. Add **budget configurability by org type / grant type / personnel assumptions**.
5. Add a **document pack exporter** with cleaner folder structure and version stamps.

## Final appraisal

This file is **not fake**.\
It is also **not finished intelligence**.

Best description:

**A credible local-first grant automation framework with real workflow controls, real persistence, and real packaging, but only moderate agent sophistication so far.**

That is a real asset.


#### You:
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
═══════════════════════════════════════════════════════════════════════════════
AEGIS TRIAGE
Human-Guided Crisis Signal Intelligence Platform
NIH SBIR Research Prototype — Single-File Edition
═══════════════════════════════════════════════════════════════════════════════

OVERVIEW
--------
Aegis Triage is a research-oriented, human-guided crisis signal intelligence
prototype designed for:
- real-time crisis signal intake,
- explainable urgency estimation,
- policy-aware routing recommendations,
- operator review support,
- retrospective audit and evaluation.

This file intentionally combines:
1) SBIR-style concept framing
2) a functional deterministic prototype
3) storage, audit, and reporting utilities
4) a command-line interface for demo, batch, and interactive use

IMPORTANT
---------
This software is a research prototype for workflow support, evaluation,
simulation, and pilot design. It is not a substitute for licensed clinical
judgment, emergency response procedure, or approved crisis center policy.

DESIGN PRINCIPLES
-----------------
- human-guided, not human-replacing
- deterministic and explainable
- auditable and retrospective-ready
- conservative in uncertainty
- single-file deployable
- pilot-program friendly

EXAMPLES
--------
python aegis_triage.py --demo
python aegis_triage.py --interactive
python aegis_triage.py --batch cases.jsonl
python aegis_triage.py --summary
python aegis_triage.py --print-concept

OPTIONAL ENVIRONMENT VARIABLES
------------------------------
AEGIS_DB=aegis_triage.db
AEGIS_AUDIT_JSONL=aegis_audit.jsonl
AEGIS_POLICY=default
AEGIS_VERBOSE=true
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import statistics
import textwrap
import time
import hashlib
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# BRAND + CONCEPT LAYER
# =============================================================================

BRAND_NAME = "Aegis Triage"
BRAND_TAGLINE = "Human-Guided Crisis Signal Intelligence Platform"
BRAND_SHORT_DESCRIPTION = (
    "A deterministic, explainable, human-guided triage intelligence prototype "
    "for crisis workflows, research pilots, and operator decision support."
)

PROJECT_TITLE = f"{BRAND_NAME}: {BRAND_TAGLINE}"

PROJECT_SUMMARY = """
Crisis response environments, including 988-aligned operations, behavioral
health triage teams, telehealth intake, and emergency communication workflows,
must make high-stakes prioritization decisions under time pressure, incomplete
information, and variable staffing.

Aegis Triage is a human-guided crisis signal intelligence platform designed to
support those workflows with deterministic feature extraction, explainable
urgency estimation, policy-aware routing recommendations, and retrospective
auditability.

The system does not replace human judgment. Instead, it helps teams:
- identify salient crisis indicators,
- structure urgency review consistently,
- prioritize uncertain and high-risk cases conservatively,
- log decision context for quality assurance and research,
- create an evaluation pathway for future supervised model refinement.

The goal is to improve response consistency, transparency, timeliness, and
operational learning in crisis support environments.
""".strip()

SPECIFIC_AIMS = [
    "Build a real-time crisis signal intake and feature extraction pipeline.",
    "Develop an explainable, deterministic urgency estimation engine.",
    "Implement policy-aware routing recommendations with conservative safety rules.",
    "Create a feedback and retrospective analysis layer for continuous evaluation.",
]

SIGNIFICANCE = [
    "Improves consistency in high-pressure triage workflows.",
    "Preserves human authority while enhancing operator support.",
    "Creates auditable evidence for quality assurance and pilot review.",
    "Supports public-sector and healthcare-oriented AI operations modernization.",
]

INNOVATION = [
    "Explainable crisis signal intelligence rather than opaque scoring alone.",
    "Conservative uncertainty handling that escalates review rather than suppressing it.",
    "Policy-aware routing recommendations with explicit safety floors.",
    "Single-file deployable research architecture for rapid pilots and demos.",
]

TECHNICAL_RISKS = [
    "Ambiguous language may create uncertainty in urgency estimation.",
    "Metaphorical or quoted language may trigger false positives.",
    "Workflow misuse may occur if operators over-trust automated suggestions.",
    "Different channels and populations may require policy recalibration.",
]

RISK_MITIGATIONS = [
    "Route uncertain cases toward human review.",
    "Maintain deterministic logic and transparent feature contributions.",
    "Enforce conservative safety floors for self-harm and violence signals.",
    "Preserve full audit logs for calibration and incident review.",
]

COMMERCIALIZATION = [
    "Crisis hotline modernization pilots",
    "Behavioral health intake support systems",
    "Emergency communications decision-support tooling",
    "Healthcare operations intelligence infrastructure",
]

MILESTONES = [
    "Signal intake and feature extraction baseline",
    "Urgency estimation and policy routing baseline",
    "Audit logging and persistence layer",
    "Outcome tracking and retrospective reporting",
    "Pilot-readiness package for grant and procurement discussions",
]

BUDGET = {
    "engineering": 90000,
    "clinical_advisory": 35000,
    "security_and_compliance": 20000,
    "cloud_and_storage": 12000,
    "evaluation_and_pilot_support": 28000,
    "miscellaneous": 15000,
}


# =============================================================================
# UTILITY LAYER
# =============================================================================

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_case_id(message: str, timestamp: float) -> str:
    raw = f"{timestamp}|{message}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:16]
    return f"aegis_{digest}"


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compact_text(text: str, width: int = 88) -> str:
    text = " ".join(text.split())
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


# =============================================================================
# POLICY LAYER
# =============================================================================

@dataclass
class Policy:
    name: str = "default"

    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    low_confidence_threshold: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    emergency_route: str = "EMERGENCY_DISPATCH_RECOMMENDED"
    immediate_route: str = "IMMEDIATE_CLINICIAN_REVIEW"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "PRIORITY_QUEUE"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

    w_high_risk: float = 0.24
    w_medium_risk: float = 0.09
    w_plan: float = 0.22
    w_means: float = 0.16
    w_immediacy: float = 0.18
    w_self_harm: float = 0.26
    w_violence: float = 0.26
    w_distress: float = 0.10
    w_protective: float = -0.18
    w_help_seeking: float = -0.04
    w_negation_safety: float = -0.10
    w_short_signal: float = 0.08
    w_caps: float = 0.03
    w_punctuation: float = 0.03

    confidence_base: float = 0.50
    confidence_per_feature_group: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_metadata: float = 0.05

    require_human_review_for_high: bool = True
    route_low_confidence_to_human: bool = True
    preserve_self_harm_floor: bool = True
    preserve_violence_floor: bool = True


def load_policy(name: str = "default") -> Policy:
    return Policy(name=name)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class CrisisSignal:
    case_id: str
    timestamp: float
    created_at: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureSet:
    word_count: int
    char_count: int
    sentence_count: int
    uppercase_ratio: float
    exclamation_count: int
    question_count: int

    high_risk_hits: List[str] = field(default_factory=list)
    medium_risk_hits: List[str] = field(default_factory=list)
    plan_hits: List[str] = field(default_factory=list)
    means_hits: List[str] = field(default_factory=list)
    immediacy_hits: List[str] = field(default_factory=list)
    self_harm_hits: List[str] = field(default_factory=list)
    violence_hits: List[str] = field(default_factory=list)
    protective_hits: List[str] = field(default_factory=list)
    help_hits: List[str] = field(default_factory=list)
    negation_hits: List[str] = field(default_factory=list)
    ambiguity_hits: List[str] = field(default_factory=list)
    distress_hits: List[str] = field(default_factory=list)

    def total_hits(self) -> int:
        groups = [
            self.high_risk_hits,
            self.medium_risk_hits,
            self.plan_hits,
            self.means_hits,
            self.immediacy_hits,
            self.self_harm_hits,
            self.violence_hits,
            self.protective_hits,
            self.help_hits,
            self.negation_hits,
            self.ambiguity_hits,
            self.distress_hits,
        ]
        return sum(len(group) for group in groups)


@dataclass
class RiskAssessment:
    urgency: float
    confidence: float
    band: str
    reasons: List[str] = field(default_factory=list)
    contributions: Dict[str, float] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    priority: str
    route_to: str
    explanation: str
    requires_human_review: bool
    safety_flags: List[str] = field(default_factory=list)


@dataclass
class CaseRecord:
    case_id: str
    signal: CrisisSignal
    features: FeatureSet
    risk: RiskAssessment
    decision: RoutingDecision
    processing_ms: float
    outcome: Optional[str] = None
    reviewer_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "signal": asdict(self.signal),
            "features": asdict(self.features),
            "risk": asdict(self.risk),
            "decision": asdict(self.decision),
            "processing_ms": self.processing_ms,
            "outcome": self.outcome,
            "reviewer_notes": self.reviewer_notes,
        }


# =============================================================================
# FEATURE EXTRACTION LAYER
# =============================================================================

class SignalAnalyzer:
    """
    Deterministic language-pattern extractor for research prototypes.
    """

    HIGH_RISK = {
        r"\bi want to die\b": "want_to_die",
        r"\bend my life\b": "end_my_life",
        r"\bkill myself\b": "kill_myself",
        r"\bsuicide\b": "suicide",
        r"\bno reason to live\b": "no_reason_to_live",
        r"\bcan't go on\b": "cant_go_on",
        r"\boverdose\b": "overdose",
        r"\bhurt myself\b": "hurt_myself",
        r"\bself harm\b": "self_harm",
    }

    MEDIUM_RISK = {
        r"\bhopeless\b": "hopeless",
        r"\bpanic\b": "panic",
        r"\bdesperate\b": "desperate",
        r"\boverwhelmed\b": "overwhelmed",
        r"\bscared\b": "scared",
        r"\bafraid\b": "afraid",
        r"\bbreaking down\b": "breaking_down",
        r"\bin crisis\b": "in_crisis",
        r"\balone\b": "alone",
    }

    PLAN = {
        r"\bi have a plan\b": "have_a_plan",
        r"\bplanned\b": "planned",
        r"\bi know how\b": "know_how",
        r"\btonight\b": "tonight",
        r"\bafter everyone sleeps\b": "after_everyone_sleeps",
    }

    MEANS = {
        r"\bpills\b": "pills",
        r"\bgun\b": "gun",
        r"\bknife\b": "knife",
        r"\brope\b": "rope",
        r"\bweapon\b": "weapon",
        r"\brazor\b": "razor",
    }

    IMMEDIACY = {
        r"\bnow\b": "now",
        r"\bright now\b": "right_now",
        r"\btoday\b": "today",
        r"\btonight\b": "tonight",
        r"\bimmediately\b": "immediately",
        r"\bsoon\b": "soon",
    }

    SELF_HARM = {
        r"\bhurt myself\b": "hurt_myself",
        r"\bcut myself\b": "cut_myself",
        r"\bself harm\b": "self_harm",
        r"\bkill myself\b": "kill_myself",
        r"\bend my life\b": "end_my_life",
    }

    VIOLENCE = {
        r"\bhurt someone\b": "hurt_someone",
        r"\bkill them\b": "kill_them",
        r"\bshoot\b": "shoot",
        r"\bstab\b": "stab",
        r"\bviolent\b": "violent",
        r"\bweapon\b": "weapon",
    }

    PROTECTIVE = {
        r"\bi am safe\b": "i_am_safe",
        r"\bi'm safe\b": "i_am_safe",
        r"\bi won't do anything\b": "wont_do_anything",
        r"\bi do not want to die\b": "do_not_want_to_die",
        r"\bi don't want to die\b": "do_not_want_to_die",
        r"\bi am with someone\b": "with_someone",
        r"\bi'm with someone\b": "with_someone",
        r"\bmy therapist\b": "therapist",
        r"\bmy counselor\b": "counselor",
    }

    HELP = {
        r"\bplease help\b": "please_help",
        r"\bneed help\b": "need_help",
        r"\bi need to talk\b": "need_to_talk",
        r"\bcan someone talk\b": "someone_talk",
        r"\blooking for support\b": "support",
    }

    NEGATION = {
        r"\bnot suicidal\b": "not_suicidal",
        r"\bnot going to hurt myself\b": "not_hurt_self",
        r"\bnot going to kill myself\b": "not_kill_self",
        r"\bno plan\b": "no_plan",
        r"\bno intent\b": "no_intent",
    }

    AMBIGUITY = {
        r"\bjust kidding\b": "just_kidding",
        r"\bfiguratively\b": "figuratively",
        r"\bquote\b": "quote",
        r"\bsong lyric\b": "song_lyric",
        r"\bmetaphor\b": "metaphor",
    }

    DISTRESS = {
        r"\bcan't\b": "cant",
        r"\bnever\b": "never",
        r"\balways\b": "always",
        r"\bno one\b": "no_one",
        r"\bnobody\b": "nobody",
        r"\bi'm done\b": "im_done",
        r"\bi am done\b": "im_done",
    }

    @staticmethod
    def _hits(text: str, patterns: Dict[str, str]) -> List[str]:
        found: List[str] = []
        for pattern, label in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.append(label)
        return sorted(set(found))

    @staticmethod
    def _sentence_count(text: str) -> int:
        parts = [p.strip() for p in re.split(r"[.!?]+", text) if p.strip()]
        return max(1, len(parts))

    @staticmethod
    def _uppercase_ratio(text: str) -> float:
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        uppercase = sum(1 for c in letters if c.isupper())
        return round(uppercase / len(letters), 4)

    def analyze(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[CrisisSignal, FeatureSet]:
        timestamp = time.time()
        case_id = make_case_id(message, timestamp)
        signal = CrisisSignal(
            case_id=case_id,
            timestamp=timestamp,
            created_at=now_utc_iso(),
            message=message,
            metadata=dict(metadata or {}),
        )

        lower = message.lower()
        features = FeatureSet(
            word_count=len(message.split()),
            char_count=len(message),
            sentence_count=self._sentence_count(message),
            uppercase_ratio=self._uppercase_ratio(message),
            exclamation_count=message.count("!"),
            question_count=message.count("?"),
            high_risk_hits=self._hits(lower, self.HIGH_RISK),
            medium_risk_hits=self._hits(lower, self.MEDIUM_RISK),
            plan_hits=self._hits(lower, self.PLAN),
            means_hits=self._hits(lower, self.MEANS),
            immediacy_hits=self._hits(lower, self.IMMEDIACY),
            self_harm_hits=self._hits(lower, self.SELF_HARM),
            violence_hits=self._hits(lower, self.VIOLENCE),
            protective_hits=self._hits(lower, self.PROTECTIVE),
            help_hits=self._hits(lower, self.HELP),
            negation_hits=self._hits(lower, self.NEGATION),
            ambiguity_hits=self._hits(lower, self.AMBIGUITY),
            distress_hits=self._hits(lower, self.DISTRESS),
        )

        signal.metadata.update(
            {
                "word_count": features.word_count,
                "char_count": features.char_count,
                "sentence_count": features.sentence_count,
                "uppercase_ratio": features.uppercase_ratio,
                "exclamation_count": features.exclamation_count,
                "question_count": features.question_count,
            }
        )
        return signal, features


# =============================================================================
# RISK LAYER
# =============================================================================

class UrgencyModel:
    def __init__(self, policy: Policy):
        self.policy = policy

    def assess(self, signal: CrisisSignal, features: FeatureSet) -> RiskAssessment:
        contributions: Dict[str, float] = {}
        reasons: List[str] = []

        base = min(0.18, features.word_count / 300.0)
        contributions["base_text_density"] = round(base, 4)

        def add_if_nonzero(name: str, value: float) -> None:
            if value:
                contributions[name] = round(value, 4)

        high = len(features.high_risk_hits) * self.policy.w_high_risk
        medium = len(features.medium_risk_hits) * self.policy.w_medium_risk
        plan = len(features.plan_hits) * self.policy.w_plan
        means = len(features.means_hits) * self.policy.w_means
        immediacy = len(features.immediacy_hits) * self.policy.w_immediacy
        self_harm = len(features.self_harm_hits) * self.policy.w_self_harm
        violence = len(features.violence_hits) * self.policy.w_violence
        distress = len(features.distress_hits) * self.policy.w_distress
        protective = len(features.protective_hits) * self.policy.w_protective
        help_signal = len(features.help_hits) * self.policy.w_help_seeking
        negation = len(features.negation_hits) * self.policy.w_negation_safety

        add_if_nonzero("high_risk", high)
        add_if_nonzero("medium_risk", medium)
        add_if_nonzero("plan", plan)
        add_if_nonzero("means", means)
        add_if_nonzero("immediacy", immediacy)
        add_if_nonzero("self_harm", self_harm)
        add_if_nonzero("violence", violence)
        add_if_nonzero("distress", distress)
        add_if_nonzero("protective", protective)
        add_if_nonzero("help_seeking", help_signal)
        add_if_nonzero("negation", negation)

        if features.high_risk_hits:
            reasons.append(f"high-risk indicators: {', '.join(features.high_risk_hits)}")
        if features.medium_risk_hits:
            reasons.append(f"distress indicators: {', '.join(features.medium_risk_hits)}")
        if features.plan_hits:
            reasons.append(f"plan indicators: {', '.join(features.plan_hits)}")
        if features.means_hits:
            reasons.append(f"means indicators: {', '.join(features.means_hits)}")
        if features.immediacy_hits:
            reasons.append(f"time/immediacy indicators: {', '.join(features.immediacy_hits)}")
        if features.self_harm_hits:
            reasons.append(f"self-harm indicators: {', '.join(features.self_harm_hits)}")
        if features.violence_hits:
            reasons.append(f"violence indicators: {', '.join(features.violence_hits)}")
        if features.protective_hits:
            reasons.append(f"protective factors: {', '.join(features.protective_hits)}")
        if features.help_hits:
            reasons.append(f"help-seeking language: {', '.join(features.help_hits)}")

        short_signal = 0.0
        if features.word_count <= 3 and (
            features.high_risk_hits
            or features.medium_risk_hits
            or features.help_hits
            or features.self_harm_hits
        ):
            short_signal = self.policy.w_short_signal
            contributions["short_signal"] = round(short_signal, 4)
            reasons.append("very short message with meaningful crisis/help signal")

        emphasis = 0.0
        if features.uppercase_ratio >= 0.35:
            emphasis += self.policy.w_caps
        if features.exclamation_count >= 2:
            emphasis += self.policy.w_punctuation
        add_if_nonzero("emphasis", emphasis)

        urgency_raw = (
            base
            + high
            + medium
            + plan
            + means
            + immediacy
            + self_harm
            + violence
            + distress
            + protective
            + help_signal
            + negation
            + short_signal
            + emphasis
        )

        if features.self_harm_hits and self.policy.preserve_self_harm_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["self_harm_floor"] = 0.72

        if features.violence_hits and self.policy.preserve_violence_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["violence_floor"] = 0.72

        urgency = clamp01(urgency_raw)

        feature_groups = sum(
            1 for group in [
                features.high_risk_hits,
                features.medium_risk_hits,
                features.plan_hits,
                features.means_hits,
                features.immediacy_hits,
                features.self_harm_hits,
                features.violence_hits,
                features.protective_hits,
                features.help_hits,
                features.negation_hits,
                features.ambiguity_hits,
                features.distress_hits,
            ] if group
        )

        confidence = self.policy.confidence_base
        confidence += feature_groups * self.policy.confidence_per_feature_group
        confidence += min(4, features.total_hits()) * self.policy.confidence_per_signal_density

        if features.ambiguity_hits:
            confidence -= self.policy.confidence_penalty_ambiguity
            reasons.append(f"ambiguity markers: {', '.join(features.ambiguity_hits)}")

        if features.word_count <= 2:
            confidence -= self.policy.confidence_penalty_too_short
            reasons.append("extremely short input lowers confidence")

        if signal.metadata:
            confidence += self.policy.confidence_bonus_metadata

        confidence = clamp01(confidence)

        if urgency >= self.policy.critical_threshold:
            band = "CRITICAL"
        elif urgency >= self.policy.high_threshold:
            band = "HIGH"
        elif urgency >= self.policy.medium_threshold:
            band = "MEDIUM"
        else:
            band = "LOW"

        if not reasons:
            reasons.append("limited direct risk language; estimate driven by general signal density")

        return RiskAssessment(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            band=band,
            reasons=reasons,
            contributions=contributions,
        )


# =============================================================================
# DECISION LAYER
# =============================================================================

class RoutingEngine:
    def __init__(self, policy: Policy):
        self.policy = policy

    def decide(self, features: FeatureSet, risk: RiskAssessment) -> RoutingDecision:
        flags: List[str] = []
        low_confidence = risk.confidence < self.policy.low_confidence_threshold
        self_harm_present = bool(features.self_harm_hits or features.high_risk_hits)
        violence_present = bool(features.violence_hits)

        if self_harm_present:
            flags.append("SELF_HARM_SIGNAL")
        if violence_present:
            flags.append("VIOLENCE_SIGNAL")
        if features.plan_hits:
            flags.append("PLAN_INDICATOR")
        if features.means_hits:
            flags.append("MEANS_INDICATOR")
        if low_confidence:
            flags.append("LOW_CONFIDENCE")

        if risk.urgency >= self.policy.critical_threshold:
            priority = "CRITICAL"
            route = self.policy.emergency_route
            review = True
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds critical threshold "
                f"{self.policy.critical_threshold:.2f}; emergency-aligned escalation is recommended."
            )
        elif risk.urgency >= self.policy.high_threshold:
            priority = "HIGH"
            route = self.policy.immediate_route
            review = self.policy.require_human_review_for_high
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds high threshold "
                f"{self.policy.high_threshold:.2f}; immediate clinician review is recommended."
            )
        elif risk.urgency >= self.policy.medium_threshold:
            priority = "MEDIUM"
            route = self.policy.priority_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds medium threshold "
                f"{self.policy.medium_threshold:.2f}; priority handling is recommended."
            )
        else:
            priority = "LOW"
            route = self.policy.standard_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} is below medium threshold; "
                f"standard queue placement is recommended."
            )

        if low_confidence and self.policy.route_low_confidence_to_human:
            route = self.policy.mandatory_review_route
            review = True
            explanation += " Confidence is limited, so human review is required."

        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = self.policy.urgent_review_route
            review = True
            explanation += " High-risk plus uncertainty triggers urgent human review."

        if self_harm_present and priority == "LOW":
            priority = "MEDIUM"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Self-harm language prevents a low-priority disposition."

        if violence_present and priority in {"LOW", "MEDIUM"}:
            priority = "HIGH"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Violence language elevates the case for urgent review."

        return RoutingDecision(
            priority=priority,
            route_to=route,
            explanation=explanation,
            requires_human_review=review,
            safety_flags=flags,
        )


# =============================================================================
# STORAGE LAYER
# =============================================================================

class CaseStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_records (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                timestamp REAL NOT NULL,
                message TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                features_json TEXT NOT NULL,
                risk_json TEXT NOT NULL,
                decision_json TEXT NOT NULL,
                processing_ms REAL NOT NULL,
                outcome TEXT,
                reviewer_notes TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                reviewer_notes TEXT,
                recorded_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_case_outcomes_case_id ON case_outcomes(case_id)"
        )
        self.conn.commit()

    def save(self, record: CaseRecord) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO case_records (
                case_id, created_at, timestamp, message, metadata_json,
                features_json, risk_json, decision_json, processing_ms,
                outcome, reviewer_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.case_id,
                record.signal.created_at,
                record.signal.timestamp,
                record.signal.message,
                json.dumps(record.signal.metadata, ensure_ascii=False),
                json.dumps(asdict(record.features), ensure_ascii=False),
                json.dumps(asdict(record.risk), ensure_ascii=False),
                json.dumps(asdict(record.decision), ensure_ascii=False),
                record.processing_ms,
                record.outcome,
                record.reviewer_notes,
            ),
        )
        self.conn.commit()

    def set_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE case_records
            SET outcome = ?, reviewer_notes = ?
            WHERE case_id = ?
            """,
            (outcome, reviewer_notes, case_id),
        )
        updated = cur.rowcount > 0
        cur.execute(
            """
            INSERT INTO case_outcomes (case_id, outcome, reviewer_notes, recorded_at)
            VALUES (?, ?, ?, ?)
            """,
            (case_id, outcome, reviewer_notes, now_utc_iso()),
        )
        self.conn.commit()
        return updated

    def get(self, case_id: str) -> Optional[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM case_records WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_recent(self, limit: int = 1000) -> List[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM case_records ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row: sqlite3.Row) -> CaseRecord:
        signal = CrisisSignal(
            case_id=row["case_id"],
            timestamp=row["timestamp"],
            created_at=row["created_at"],
            message=row["message"],
            metadata=json.loads(row["metadata_json"]),
        )
        features = FeatureSet(**json.loads(row["features_json"]))
        risk = RiskAssessment(**json.loads(row["risk_json"]))
        decision = RoutingDecision(**json.loads(row["decision_json"]))
        return CaseRecord(
            case_id=row["case_id"],
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=row["processing_ms"],
            outcome=row["outcome"],
            reviewer_notes=row["reviewer_notes"],
        )

    def close(self) -> None:
        self.conn.close()


# =============================================================================
# AUDIT LAYER
# =============================================================================

class AuditTrail:
    def __init__(self, jsonl_path: str, verbose: bool = True):
        self.jsonl_path = jsonl_path
        self.verbose = verbose
        self._entries: List[Dict[str, Any]] = []

    def log(self, record: CaseRecord) -> None:
        entry = record.to_dict()
        self._entries.append(entry)

        with open(self.jsonl_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if self.verbose:
            self._print(record)

    def _print(self, record: CaseRecord) -> None:
        print("┌" + "─" * 78)
        print(f"│ BRAND        : {BRAND_NAME}")
        print(f"│ CASE ID      : {record.case_id}")
        print(f"│ MESSAGE      : {compact_text(record.signal.message)}")
        print(f"│ URGENCY      : {record.risk.urgency:.4f}    CONFIDENCE: {record.risk.confidence:.4f}")
        print(f"│ BAND         : {record.risk.band}")
        print(f"│ PRIORITY     : {record.decision.priority:<12} ROUTE: {record.decision.route_to}")
        print(f"│ HUMAN REVIEW : {record.decision.requires_human_review}")
        print(f"│ FLAGS        : {', '.join(record.decision.safety_flags) if record.decision.safety_flags else 'None'}")
        print(f"│ REASONS      : {compact_text('; '.join(record.risk.reasons[:3]), 70)}")
        print(f"│ LATENCY      : {record.processing_ms:.2f} ms")
        print("└" + "─" * 78)

    def export_json(self) -> str:
        return json.dumps(self._entries, indent=2, ensure_ascii=False)


# =============================================================================
# FEEDBACK + REPORTING LAYER
# =============================================================================

class ReviewLoop:
    def __init__(self, store: CaseStore):
        self.store = store

    def record_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.store.set_outcome(case_id, outcome, reviewer_notes)

    def summary(self, limit: int = 5000) -> Dict[str, Any]:
        records = self.store.list_recent(limit=limit)
        if not records:
            return {"records": 0}

        urgencies = [r.risk.urgency for r in records]
        confidences = [r.risk.confidence for r in records]
        priorities = [r.decision.priority for r in records]
        routes = [r.decision.route_to for r in records]
        outcomes = [r.outcome for r in records if r.outcome]

        return {
            "brand": BRAND_NAME,
            "records": len(records),
            "avg_urgency": round(statistics.mean(urgencies), 4),
            "max_urgency": round(max(urgencies), 4),
            "avg_confidence": round(statistics.mean(confidences), 4),
            "human_review_rate": round(
                sum(1 for r in records if r.decision.requires_human_review) / len(records), 4
            ),
            "band_distribution": dict(Counter(r.risk.band for r in records)),
            "priority_distribution": dict(Counter(priorities)),
            "route_distribution": dict(Counter(routes)),
            "outcomes_logged": len(outcomes),
            "outcome_distribution": dict(Counter(outcomes)),
        }

    def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
        records = [r for r in self.store.list_recent(limit=limit) if r.outcome]
        if not records:
            return {"records_with_outcomes": 0, "buckets": {}}

        buckets = {
            "0.00-0.39": [],
            "0.40-0.64": [],
            "0.65-0.84": [],
            "0.85-1.00": [],
        }

        for record in records:
            u = record.risk.urgency
            if u < 0.40:
                buckets["0.00-0.39"].append(record.outcome or "UNKNOWN")
            elif u < 0.65:
                buckets["0.40-0.64"].append(record.outcome or "UNKNOWN")
            elif u < 0.85:
                buckets["0.65-0.84"].append(record.outcome or "UNKNOWN")
            else:
                buckets["0.85-1.00"].append(record.outcome or "UNKNOWN")

        return {
            "records_with_outcomes": len(records),
            "buckets": {k: dict(Counter(v)) for k, v in buckets.items()},
        }


# =============================================================================
# ORCHESTRATION LAYER
# =============================================================================

class AegisTriageEngine:
    def __init__(
        self,
        db_path: str,
        audit_jsonl_path: str,
        verbose: bool = True,
        policy_name: str = "default",
    ):
        self.policy = load_policy(policy_name)
        self.analyzer = SignalAnalyzer()
        self.urgency_model = UrgencyModel(self.policy)
        self.routing_engine = RoutingEngine(self.policy)
        self.store = CaseStore(db_path)
        self.audit = AuditTrail(audit_jsonl_path, verbose=verbose)
        self.review = ReviewLoop(self.store)

    def process(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> CaseRecord:
        start = time.perf_counter()

        signal, features = self.analyzer.analyze(message, metadata=metadata)
        risk = self.urgency_model.assess(signal, features)
        decision = self.routing_engine.decide(features, risk)

        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 3)

        record = CaseRecord(
            case_id=signal.case_id,
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=elapsed_ms,
        )

        self.store.save(record)
        self.audit.log(record)
        return record

    def log_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.review.record_outcome(case_id, outcome, reviewer_notes)

    def export_records(self, path: str, limit: int = 5000) -> None:
        payload = [r.to_dict() for r in self.store.list_recent(limit=limit)]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    def summary(self) -> Dict[str, Any]:
        return self.review.summary()

    def calibration(self) -> Dict[str, Any]:
        return self.review.calibration_snapshot()

    def close(self) -> None:
        self.store.close()


# =============================================================================
# PRESENTATION LAYER
# =============================================================================

def print_header(title: str) -> None:
    print("\n" + "═" * 80)
    print(title)
    print("═" * 80 + "\n")


def print_concept() -> None:
    print_header(f"{BRAND_NAME.upper()} — SBIR RESEARCH CONCEPT")
    sections = {
        "TITLE": PROJECT_TITLE,
        "BRAND DESCRIPTION": BRAND_SHORT_DESCRIPTION,
        "PROJECT SUMMARY": PROJECT_SUMMARY,
        "SPECIFIC AIMS": SPECIFIC_AIMS,
        "SIGNIFICANCE": SIGNIFICANCE,
        "INNOVATION": INNOVATION,
        "TECHNICAL RISKS": TECHNICAL_RISKS,
        "RISK MITIGATIONS": RISK_MITIGATIONS,
        "COMMERCIALIZATION": COMMERCIALIZATION,
        "MILESTONES": MILESTONES,
        "BUDGET": BUDGET,
    }

    for name, value in sections.items():
        print(name)
        print("-" * len(name))
        if isinstance(value, str):
            print(textwrap.fill(value, width=88))
        elif isinstance(value, dict):
            for k, v in value.items():
                print(f"  - {k}: ${v:,.0f}")
        else:
            for item in value:
                print(f"  - {item}")
        print()


def print_summary(summary: Dict[str, Any], calibration: Optional[Dict[str, Any]] = None) -> None:
    print_header(f"{BRAND_NAME.upper()} — SUMMARY")
    for key, value in summary.items():
        print(f"{key:>24} : {value}")
    if calibration is not None:
        print("\nCALIBRATION SNAPSHOT")
        print("--------------------")
        for key, value in calibration.items():
            print(f"{key:>24} : {value}")
    print()


def print_case(record: CaseRecord) -> None:
    print_header(f"{BRAND_NAME.upper()} — CASE DETAIL")
    print(f"Case ID         : {record.case_id}")
    print(f"Created at      : {record.signal.created_at}")
    print(f"Message         : {record.signal.message}")
    print(f"Metadata        : {json.dumps(record.signal.metadata, ensure_ascii=False)}")
    print()
    print("FEATURES")
    print("--------")
    print(json.dumps(asdict(record.features), indent=2, ensure_ascii=False))
    print()
    print("RISK")
    print("----")
    print(json.dumps(asdict(record.risk), indent=2, ensure_ascii=False))
    print()
    print("DECISION")
    print("--------")
    print(json.dumps(asdict(record.decision), indent=2, ensure_ascii=False))
    print()
    print(f"Processing ms   : {record.processing_ms}")
    print(f"Outcome         : {record.outcome}")
    print(f"Reviewer notes  : {record.reviewer_notes}")
    print()


# =============================================================================
# DEMO CASES
# =============================================================================

DEMO_CASES: List[Tuple[str, Dict[str, Any], str]] = [
    (
        "I've been feeling a little down lately and just needed to talk.",
        {"channel": "chat", "source": "demo"},
        "RESOLVED_SUPPORTIVE_CONTACT",
    ),
    (
        "I don't know how much longer I can handle this. I feel completely overwhelmed and scared.",
        {"channel": "chat", "source": "demo"},
        "COUNSELOR_FOLLOW_UP",
    ),
    (
        "I'm in crisis right now. I feel hopeless and desperate. Please help me.",
        {"channel": "voice", "source": "demo"},
        "IMMEDIATE_CLINICIAN_CONTACT",
    ),
    (
        "I want to end my life tonight. I have a plan and I don't see any reason to go on.",
        {"channel": "chat", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
    (
        "help",
        {"channel": "sms", "source": "demo"},
        "MONITORED_AND_ENGAGED",
    ),
    (
        "Not suicidal. No plan. I am safe, but I really need to talk to someone tonight because I'm panicking.",
        {"channel": "chat", "source": "demo"},
        "URGENT_SUPPORT_CONTACT",
    ),
    (
        "I have pills and I think tonight is the night.",
        {"channel": "sms", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
]


# =============================================================================
# CLI LAYER
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{BRAND_NAME} — single-file research prototype"
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demonstration cases")
    parser.add_argument("--interactive", action="store_true", help="Run interactive console mode")
    parser.add_argument("--batch", type=str, help="Process a JSONL batch file")
    parser.add_argument("--summary", action="store_true", help="Print stored summary")
    parser.add_argument("--show-case", type=str, help="Show stored case by case_id")
    parser.add_argument("--export-records", type=str, help="Export records to JSON")
    parser.add_argument("--print-concept", action="store_true", help="Print concept package")
    parser.add_argument("--quiet", action="store_true", help="Reduce console output")
    parser.add_argument("--db", type=str, default=os.getenv("AEGIS_DB", "aegis_triage.db"))
    parser.add_argument(
        "--audit-jsonl",
        type=str,
        default=os.getenv("AEGIS_AUDIT_JSONL", "aegis_audit.jsonl"),
    )
    parser.add_argument(
        "--policy",
        type=str,
        default=os.getenv("AEGIS_POLICY", "default"),
    )
    return parser.parse_args(argv)


def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Line {line_no} is not a JSON object")
            yield item


def run_demo(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — DEMO")
    for idx, (message, metadata, outcome) in enumerate(DEMO_CASES, start=1):
        print(f"[Demo Case {idx}/{len(DEMO_CASES)}]")
        record = engine.process(message, metadata=metadata)
        engine.log_outcome(record.case_id, outcome, reviewer_notes="demo outcome")
        print(f"Outcome logged : {outcome}\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_batch(engine: AegisTriageEngine, path: str) -> None:
    print_header(f"{BRAND_NAME.upper()} — BATCH MODE")
    processed = 0
    for item in iter_jsonl(path):
        message = str(item.get("message", "")).strip()
        metadata = item.get("metadata", {})
        if not message:
            continue
        engine.process(message, metadata if isinstance(metadata, dict) else {})
        processed += 1
    print(f"Processed {processed} records.\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_interactive(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — INTERACTIVE MODE")
    print("Enter a message, then press Enter.")
    print("Commands:")
    print("  /quit")
    print("  /summary")
    print("  /show <case_id>")
    print("  /outcome <case_id> <OUTCOME TEXT>")
    print()

    while True:
        try:
            raw = input("message> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if not raw:
            continue
        if raw == "/quit":
            break
        if raw == "/summary":
            print_summary(engine.summary(), calibration=engine.calibration())
            continue
        if raw.startswith("/show "):
            _, _, case_id = raw.partition(" ")
            record = engine.store.get(case_id.strip())
            if record is None:
                print("Case not found.")
            else:
                print_case(record)
            continue
        if raw.startswith("/outcome "):
            parts = raw.split(maxsplit=2)
            if len(parts) < 3:
                print("Usage: /outcome <case_id> <OUTCOME TEXT>")
                continue
            _, case_id, outcome = parts
            ok = engine.log_outcome(case_id, outcome, reviewer_notes="interactive outcome")
            print("Outcome recorded." if ok else "Case not found.")
            continue

        engine.process(raw, metadata={"channel": "interactive_console"})


# =============================================================================
# MAIN
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    engine = AegisTriageEngine(
        db_path=args.db,
        audit_jsonl_path=args.audit_jsonl,
        verbose=not args.quiet,
        policy_name=args.policy,
    )

    try:
        acted = False

        if args.print_concept:
            print_concept()
            acted = True

        if args.demo:
            run_demo(engine)
            acted = True

        if args.batch:
            run_batch(engine, args.batch)
            acted = True

        if args.interactive:
            run_interactive(engine)
            acted = True

        if args.summary:
            print_summary(engine.summary(), calibration=engine.calibration())
            acted = True

        if args.show_case:
            record = engine.store.get(args.show_case)
            if record is None:
                print(f"No case found for case_id={args.show_case}")
            else:
                print_case(record)
            acted = True

        if args.export_records:
            engine.export_records(args.export_records)
            print(f"Exported records to {args.export_records}")
            acted = True

        if not acted:
            print_header(f"{BRAND_NAME.upper()} — READY")
            print(BRAND_TAGLINE)
            print()
            print("No action selected. Try:")
            print("  --demo")
            print("  --interactive")
            print("  --batch cases.jsonl")
            print("  --summary")
            print("  --print-concept")
            print()

    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main()) ==============================
MASTER LEDGER SNAPSHOT

A-001 — Aegis Triage — AI / Agent System — Net Value: $12,000–$28,000

[ASSET ID]
	•	A-001

[NAME]
	•	Aegis Triage

[TYPE]
	•	AI / Agent System

[ORIGIN]
	•	Current chat
	•	Source input: single-file Python system prompt/prototype

[FILES / SOURCES]
	•	aegis_triage.py

[DESCRIPTION]
	•	Single-file deterministic crisis triage research prototype with:
	•	branded NIH SBIR concept layer
	•	rule-based signal extraction
	•	urgency scoring
	•	routing logic
	•	SQLite persistence
	•	JSONL audit trail
	•	CLI modes for demo, interactive, batch, summary, export
	•	It is a workflow-support prototype, not a deployable clinical product.

[COMPONENTS]
	•	UI: CLI only
	•	Backend: local Python execution engine
	•	Logic: deterministic regex-based feature extraction and weighted scoring
	•	Data: SQLite case store + JSONL audit log
	•	Integration: local file I/O only
	•	Security: minimal, no auth, no encryption, no access control
	•	Evaluation: basic summary and calibration snapshot
	•	Product Layer: branding + grant framing

[STATUS]
	•	partial

[SCORING]
	•	Completeness: 3.5/5
	•	Execution: 4.0/5
	•	Novelty: 2.5/5
	•	Monetization: 2.5/5
	•	Readiness: 2.0/5

[VALUE]
	•	Extractable: $20,000–$45,000
	•	Realistic: $12,000–$28,000
	•	Productized: $35,000–$90,000

[OVERLAP]
	•	No prior Aegis-specific asset in this snapshot
	•	Internal overlap exists between grant framing and prototype wrapper, but not enough to discount materially

[NET NEW VALUE]
	•	$12,000–$28,000

[DEPENDENCIES]
	•	Clinical policy design
	•	Domain validation data
	•	Human reviewer workflow
	•	Security/compliance layer
	•	Deployment/API surface
	•	Evaluation dataset and benchmark process

[BLOCKERS]
	•	No real-world validation
	•	No model training or calibrated supervised classifier
	•	No authentication, authorization, encryption, or tenant boundaries
	•	No web app, queueing, API, observability stack, or deployment infra
	•	No clinical governance layer
	•	No integration with actual hotline/call-center systems
	•	High regulatory and operational burden if pushed beyond research use

⸻

PORTFOLIO TOTAL
	•	Gross Value: $12,000–$28,000
	•	Net Realistic Value: $12,000–$28,000
	•	Productized Value: $35,000–$90,000

⸻

VALUE CHANGES
	•	Added: $12,000–$28,000

	•	Deducted: $0
= Net: $12,000–$28,000

⸻

TOP VALUE DRIVERS
	•	A-001 → It is not just concept text. It actually executes, stores records, logs outputs, and supports repeatable demo/batch workflows.
	•	A-001 → Deterministic scoring and auditability make it easier to pitch as a research/pilot prototype than an opaque model demo.
	•	A-001 → Packaging is better than average: branding, CLI, persistence, summaries, and concept framing are already combined.

⸻

VALUE LEAKS
	•	no production integration layer
	•	no security/compliance controls
	•	no clinical validation
	•	no customer workflow integration
	•	no actual trained model advantage
	•	no revenue proof
	•	single-file architecture helps demo speed but caps enterprise credibility

⸻

SYSTEM STRUCTURE

Core assets
	•	A-001 Aegis Triage core engine
	•	feature extraction
	•	urgency model
	•	routing engine
	•	persistence
	•	audit
	•	reporting
	•	CLI

Supporting assets
	•	NIH SBIR concept framing embedded in file
	•	demo case corpus
	•	policy object and thresholds

Orphaned assets
	•	none inside this snapshot, but the commercialization story is not backed by deployment, pilots, or data assets

⸻

HARD TRUTH

What actually has value:
	•	The executable prototype.
	•	The deterministic scoring/routing structure.
	•	The persistence and audit trail.
	•	The fact that it is already framed as a pilot/research system rather than a toy sentiment script.

What is noise:
	•	The NIH/SBIR language by itself.
	•	Commercialization bullets without distribution, validation, or buyers.
	•	Any implication that this is clinically deployable.

What must be fixed to unlock next tier:
	•	Add an API/service layer.
	•	Add role-based access, encryption, and serious security controls.
	•	Add evaluation against a labeled dataset.
	•	Add policy versioning and reproducible benchmark reports.
	•	Add a reviewer dashboard or operational interface.
	•	Add integration points for real intake channels.
	•	Add governance language and validation workflow with clinical reviewers.

Bottom line:
This is a credible research prototype with packaging discipline, not a product company and not a production crisis platform. Today it is worth prototype money. With validation, interface, security, and deployment work, it can move into low-six-figure pilot territory. Without that, it stays a polished internal demo. [MASTER SUMMARY]

• What is being built:
A single-file crisis triage research prototype for intake, rule-based signal extraction, urgency scoring, routing recommendations, audit logging, and retrospective review.

• What actually works:
CLI intake, deterministic regex-based feature extraction, weighted urgency scoring, routing logic, SQLite storage, JSONL audit logging, record export, demo mode, batch mode, interactive mode, summary reporting, calibration snapshot, policy object.

• What is unproven:
Clinical validity, real-world safety, benchmark quality, hotline workflow fit, procurement fit, deployment readiness, API/service operation, security controls, supervised model improvement, customer demand.

• What has real value:
Executable prototype, deterministic scoring pipeline, persistence layer, audit trail, reproducible demo workflow, pilot-ready concept packaging, reusable single-file decision-support architecture.

• What is noise:
SBIR/NIH framing by itself, commercialization claims without pilots, any suggestion of production clinical readiness, grant language that is not backed by validation, inflated product-company framing.

⸻

[COMPRESSED TRUTH — MAX 60 WORDS]

Aegis Triage is a working local prototype for crisis-message intake, explainable urgency scoring, routing, storage, and audit. Its value is the executable decision-support workflow, not the grant language. It is not clinically validated, secure, integrated, or production-ready. Today it is prototype infrastructure with pilot packaging, not a deployable crisis platform.

⸻

[GRANDMOTHER EXPLANATION — MAX 50 WORDS]

It reads crisis-related messages, scores how urgent they look, suggests where they should go, and saves everything for later review. It helps staff work more consistently. It does not replace trained people, and it is not ready for real clinical use without more testing and safety work.

⸻

[DOLLAR VIEW]

• Current realistic sale value: $8,000–$18,000
• If cleaned and deduplicated: $15,000–$30,000
• If proven with real usage: $60,000–$150,000

⸻

[PRODUCT SNAPSHOT]

• Product name: Aegis Triage
• One-line hook: Explainable crisis triage workflow prototype with audit trails
• What it does (brutal): Scores text-based crisis signals, recommends routing, stores every case, and produces reviewable records
• Who it’s for: Research teams, pilot programs, public-sector innovation groups, healthcare operations teams
• Why it’s different: Deterministic logic, full auditability, local deployability, single-file prototype packaging

⸻

[SALES PAGE — MINIMAL]

Headline:
Explainable Crisis Triage Prototype for Research and Pilot Workflows

Subheadline:
A deterministic intake, scoring, routing, and audit system for teams exploring crisis-support decision tools.

What you get:
• Single-file working prototype with CLI, storage, scoring, and routing
• SQLite case history and JSONL audit trail
• Demo, batch, export, summary, and calibration utilities

Proof (real only):
• Functional Python engine
• Persistent case storage
• Deterministic scoring and route assignment
• Repeatable demo and batch workflows

⸻

[PRICING STRATEGY]

• Anchor price: $24,000
• Realistic sell price: $9,500–$15,000
• Quick-sale price: $4,500–$7,500

⸻

[ASSET BREAKDOWN]

• Core file / system: aegis_triage.py
• Reusable modules: signal analyzer, urgency model, routing engine, SQLite store, audit logger, reporting loop, CLI shell, policy object
• Hidden value: explainable decision trail, pilot/demo readiness, reusable architecture for regulated workflow tooling, not just crisis use

⸻

[DELIVERABLES]

README.md

Title
Aegis Triage

One-line description
Deterministic crisis signal triage prototype with routing, storage, audit logging, and review reporting.

What it does
Processes text input, extracts rule-based risk signals, estimates urgency, recommends routing, [MASTER SUMMARY]

• What is being built:
A single-file crisis triage research prototype for intake, rule-based signal extraction, urgency scoring, routing recommendations, audit logging, and retrospective review.

• What actually works:
CLI intake, deterministic regex-based feature extraction, weighted urgency scoring, routing logic, SQLite storage, JSONL audit logging, record export, demo mode, batch mode, interactive mode, summary reporting, calibration snapshot, policy object.

• What is unproven:
Clinical validity, real-world safety, benchmark quality, hotline workflow fit, procurement fit, deployment readiness, API/service operation, security controls, supervised model improvement, customer demand.

• What has real value:
Executable prototype, deterministic scoring pipeline, persistence layer, audit trail, reproducible demo workflow, pilot-ready concept packaging, reusable single-file decision-support architecture.

• What is noise:
SBIR/NIH framing by itself, commercialization claims without pilots, any suggestion of production clinical readiness, grant language not backed by validation, inflated product-company framing.

⸻

[COMPRESSED TRUTH — MAX 60 WORDS]

Aegis Triage is a working local prototype for crisis-message intake, explainable urgency scoring, routing, storage, and audit. Its value is the executable decision-support workflow, not the grant framing. It is not clinically validated, secure, integrated, or production-ready. Today it is prototype infrastructure with pilot packaging, not a deployable crisis platform.

⸻

[GRANDMOTHER EXPLANATION — MAX 50 WORDS]

It reads crisis-related messages, estimates how urgent they seem, suggests where they should go, and saves everything for later review. It helps staff work more consistently. It does not replace trained people, and it is not ready for real clinical use without more testing and safety work.

⸻

[DOLLAR VIEW]

• Current realistic sale value:
$8,000–$18,000

• If cleaned and deduplicated:
$15,000–$30,000

• If proven with real usage:
$60,000–$150,000

⸻

[PRODUCT SNAPSHOT]

• Product name:
Aegis Triage

• One-line hook:
Explainable crisis triage workflow prototype with audit trails

• What it does (brutal):
Scores text-based crisis signals, recommends routing, stores every case, and produces reviewable records

• Who it’s for:
Research teams, pilot programs, public-sector innovation groups, healthcare operations teams

• Why it’s different:
Deterministic logic, full auditability, local deployability, single-file prototype packaging

⸻

[SALES PAGE — MINIMAL]

Headline:
Explainable Crisis Triage Prototype for Research and Pilot Workflows

Subheadline:
A deterministic intake, scoring, routing, and audit system for teams exploring crisis-support decision tools.

What you get:
• Single-file working prototype with CLI, storage, scoring, and routing
• SQLite case history and JSONL audit trail
• Demo, batch, export, summary, and calibration utilities

Proof (real only):
• Functional Python engine
• Persistent case storage
• Deterministic scoring and route assignment
• Repeatable demo and batch workflows

⸻

[PRICING STRATEGY]

• Anchor price:
$24,000

• Realistic sell price:
$9,500–$15,000

• Quick-sale price:
$4,500–$7,500

⸻

[ASSET BREAKDOWN]

• Core file / system:
aegis_triage.py

• Reusable modules:
signal analyzer, urgency model, routing engine, SQLite store, audit logger, reporting loop, CLI shell, policy object

• Hidden value:
Explainable decision trail, pilot/demo readiness, reusable architecture for regulated workflow tooling beyond crisis use

⸻

[DELIVERABLES]

README.md

Title
Aegis Triage

One-line description
Deterministic crisis signal triage prototype with routing, storage, audit logging, and review reporting.

What it does
Processes text input, extracts rule-based risk signals, estimates urgency, recommends routing, stores results, and supports later review and summary analysis.

How it works
• Ingests text cases from demo, interactive, or batch input
• Extracts crisis-related features with deterministic rules
• Scores urgency and confidence using weighted logic
• Produces routing recommendations with safety floors
• Stores all records in SQLite and JSONL for audit and review

Quick start

#### ChatGPT:
\[MASTER SUMMARY]

• What is being built:\
ONE system → **Local Decision-Support Intelligence Platform** (Grant Copilot + Aegis Triage merged) for structured intake, scoring, routing, proposal generation, audit, and export.

• What actually works:\
SQLite persistence, CLI control, deterministic scoring (triage), grant pipeline (intake→proposal→budget→compliance→scoring→audit), audit logs, approval gating, export system, test harness.

• What is unproven:\
Clinical validity, grant win rate, real-world deployment, security/compliance, API/service layer, user adoption, data-backed scoring accuracy.

• What has real value:\
Reusable orchestration engine, deterministic scoring + audit trail, multi-agent workflow pipeline, local-first architecture, approval gating system.

• What is noise:\
Duplicate summaries, repeated valuation blocks, SBIR language alone, inflated commercialization claims, parallel “separate products” framing.

---

\[COMPRESSED TRUTH — MAX 60 WORDS]

You have one real asset: a local, auditable decision-support system engine.\
Aegis (triage) + Grant Copilot (workflow) are the same core system.\
Value is in orchestration, persistence, and explainability.\
Everything else is repetition or framing.\
Not validated, not deployed, not secure → still prototype-tier.

---

\[GRANDMOTHER EXPLANATION — MAX 50 WORDS]

It’s one tool that helps organize complex decisions.\
It can read input, score it, suggest what to do, write structured outputs, and save everything for review.\
It helps people work more consistently, but still needs real-world testing before anyone depends on it.

---

\[DOLLAR VIEW]

• Current realistic sale value:\
$12,000–$25,000

• If cleaned and unified (single product):\
$30,000–$60,000

• If proven with real pilots + users:\
$120,000–$300,000+

---

\[PRODUCT SNAPSHOT]

• Product name:\
Aegis Copilot Engine

• One-line hook:\
Local, auditable decision-support system for crisis triage and grant workflows

• What it does (brutal):\
Takes input → scores it → structures outputs → logs everything → requires human approval → exports usable artifacts

• Who it’s for:\
Research teams, public-sector pilots, healthcare ops, internal tooling teams

• Why it’s different:\
Deterministic, explainable, local-first, audit-complete, no API dependency

---

\[SALES PAGE — MINIMAL]

Headline:\
Build Decision Systems You Can Audit, Not Just AI Demos

Subheadline:\
A local-first engine for scoring, structuring, routing, and exporting high-stakes workflows.

What you get:\
• Crisis triage scoring + routing engine\
• Grant workflow automation pipeline\
• Full audit trail + SQLite persistence

Proof (only real):\
• Runs locally\
• Stores real records\
• Deterministic scoring + routing\
• Export + approval gating

---

\[PRICING STRATEGY]

• Anchor price:\
$29,000

• Realistic sell price:\
$9,000–$18,000

• Quick-sale price:\
$4,000–$7,000

---

\[ASSET BREAKDOWN]

• Core file / system:\
aegis\_triage.py + grant\_copilot.py → MUST MERGE into one

• Reusable modules:

- scoring engine
- routing engine
- multi-agent pipeline
- SQLite persistence
- audit logging
- CLI framework

• Hidden value:\
Explainability + audit trail → critical for regulated environments

---

\[DELIVERABLES]

### README.md

Title\
Aegis Copilot Engine

One-line description\
Local, deterministic decision-support system with scoring, routing, workflow automation, and audit logging.

What it does\
Processes inputs, scores risk or structure, generates outputs, logs everything, and enforces human approval before export.

How it works\
• Ingests input (text / idea)\
• Applies deterministic scoring or structuring\
• Runs workflow pipeline\
• Stores outputs and logs\
• Requires approval → exports

Quick start\
python main.py

Who it’s for\
Teams building auditable internal tools or research workflows

---

### GUMROAD PAGE

Title:\
Aegis Copilot Engine

Tagline:\
Turn messy decisions into structured, auditable systems

Description:\
A single-file local engine that scores inputs, structures outputs, logs everything, and enforces human approval. Designed for crisis workflows, grant pipelines, and internal decision systems.

What’s included:\
• Core engine file\
• CLI workflow\
• Storage + audit system

Who it’s for:\
• Engineers\
• Research teams\
• Public-sector builders

---

### FILE STRUCTURE

/project\
├── main.py\
├── README.md\
├── config.json\
├── logs/\
└── data/

---

### QUICK START

> python main.py --mode demo

---

### TAGS

• decision systems\
• auditability\
• local AI\
• workflow automation\
• research tools

---

FINAL ENFORCEMENT

You do NOT have two products.

You have ONE system split in half.

Merge them → or you halve the value.
