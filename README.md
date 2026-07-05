# Provenance-Guard

## Architecure Overview

[Client Request] 
       │
       ▼
[Flask-Limiter Gateway] ──(Exceeded)──► [HTTP 429: Rate Limit Block]
       │
   (Allowed)
       ▼
[POST /submit Router] 
       │
       ├──► Signal 1: Holistic Semantic Layout Parsing (Groq API LLM)
       └──► Signal 2: Stylometric String Analytics (Local Mathematical Token Engine)
       │
       ▼
[Confidence Scoring Fusion Matrix]
       │
       ├──► Is score gap > 0.65? ──(Yes)──► [Divergence Filter Intercept] ──► Score: 0.50 / "uncertain"
       │                                                                            │
    (No)                                                                            ▼
       └──► Weighted Scoring Aggregate: (Signal 1 * 0.7) + (Signal 2 * 0.3) ────────┤
                                                                                    │
                                                                                    ▼
                                                                        [Attribution Assignment]
                                                                                    │
       ┌────────────────────────────────────────────────────────────────────────────┤
       ▼                                            ▼                               ▼
[🟢 likely_human]                            [🟡 uncertain]                  [🔴 likely_ai]
       │                                            │                               │
       └────────────────────────────────────────────┴───────────────────────────────┘
                                                    │
                                                    ▼
                                    [Audit Record Committed to JSONL]
                                                    │
                                                    ▼
                                  [JSON Payload Output to Client]

**Ingestion & Rate Limiting:**
Request payloads land at POST /submit and are checked by the client IP rate limiter.

**Feature Extraction Processing:** 
The raw string runs through parallel analytics layers: high-level semantic pattern mapping (Signal 1) and raw lexical statistic variations (Signal 2).

**Fusion Logic Layer:**
The pipeline aggregates individual numeric vectors. If the two signal values exhibit extreme polarization, the engine triggers a safety fallback mechanism to protect human writers.

**State Persistence:**
The transaction records all computational sub-scores and issues a immutable trackable UUID token to audit_log.jsonl before responding.

## Detection Signals

### Signal 1: Semantic Analysis Layer (Groq API)

**What it measures:**
Evaluates text holistically for micro-signatures characteristic of language models, including over-indexing on transitional adverbs (furthermore, moreover, it is important to note), uniform paragraph density, and repetitive structural pacing.

**Why it was chosen:**
Large Language Models excel at identifying semantic distributions and rhetorical structures that local regex algorithms cannot detect.

**What it misses:**
It struggles with highly tailored, domain-specific prompt outputs or text blocks that have been post-processed with specialized phrasing variations.

### Signal 2: Stylometric Heuristics Layer

**What it measures:**
Evaluates raw linguistic complexity through two specific statistical calculations

**Why it was chosen:**
It provides a deterministic baseline that operates completely independently of API latency or semantic context.

**What it misses:**
It can easily flag highly disciplined, uniform human writing—such as academic papers or legal summaries—as machine-generated.

## Confidence Scoring & Validation

### Signal Fusion Strategy
The pipeline calculates a final score using a weighted average combined with an algorithmic safety switch:

**The Normal Path:**
If both analysis layers broadly agree, the final score uses a weighted distribution:
Final Confidence = (Signal1 x 0.7) + (Signal2 x 0.3)

**The Safety Switch:**
If the calculation layers strongly disagree (|Signal1 - Signal2| > 0.65), the engine safely overrides the output to 0.50 and classifies the item as uncertain. This design ensures that unique or unconventional human writing styles are protected against false positive flags.

## Real-World Validation Benchmarks
The effectiveness of this scoring configuration is demonstrated by two distinct test cases extracted from our system logs:

**Case A: Machine-Generated Document (High AI Confidence)**
- Input Text: "Furthermore, it is important to note that the paradigm shift in software development presents significant advantages. Therefore, developers must optimize structures. Consequently, efficiency increases."
- Metrics Matrix: llm_score: 0.8700, heuristic_score: 0.5000 (Gap: 0.3700≤0.65)
- Calculated Core Value: 0.7590
- Assigned Attribution: likely_ai
- System Label: 🔴 AI Generated
**Case B: Formulaic Academic Text (Divergence Guard Triggered)**
- Input Text: "The experimental data indicates a correlation between algorithmic optimization and processing latency. Consequently, the researchers concluded that architectural enhancements remain critical. Moreover, empirical evidence supports this paradigm."
- Metrics Matrix: llm_score: 0.1200, heuristic_score: 0.8400 (Gap: 0.7200>0.65)
- Calculated Core Value: Forced Fallback to 0.5000
- Assigned Attribution: uncertain
- System Label: 🟡 System Note: Unable to verify origin

## Transparency Labels
The platform translates numeric classifications into clear, informative user-facing alerts based on three categories:

| Assignment Status | Range Boundary  | Verbatim Transparency Label                                                                                                 |
|-------------------|-----------------|-----------------------------------------------------------------------------------------------------------------------------|
| Verified Human    | 0.00 ≤ x ≤ 0.34 | Verified Authentic: This piece exhibits the structural variation and natural voice characteristic of human creation.        |
| Uncertain Status  | 0.35 ≤ x ≤ 0.69 | System Note: Unable to verify origin. The text displays a mix of structured patterns and organic language choices.          |
| Detected AI       | 0.70 ≤ x ≤ 1.00 | AI Generated: Automated signatures detected. Content closely matches the structural profiles of language model generations. |

## Rate Limiting Configuration
The platform implements explicit rate limits applied directly through the Flask-Limiter layer:

**Submit Path Bounds:**
10 per minute; 100 per day

**Storage Provider Layout:**
storage_uri="memory://"

### Configuration Reasoning

The submission route handles complex semantic parsing via remote Groq LLM clusters. Setting a limit of 10 requests per minute protects the backend from API rate limits and connection pooling issues during high-traffic bursts, while the daily cap of 100 requests prevents resource misuse. The in-memory storage engine keeps the rate-limiting layer highly performant and clear of external dependency bottlenecks.

## Known Limitations

**The ESL and Academic Prose Blind Spot:**
This framework can misclassify original academic articles or essays written by non-native English (ESL) students. Technical style guides require highly disciplined transition structures (consequently, moreover, furthermore) and uniform sentence configurations. These structural patterns match the low-variance profiles of language models, which can cause the local heuristics engine to return an artificially high AI score. While the Divergence Filter often flags these items as uncertain, a highly polished and completely standardized academic text may still slip past the system as a false positive.

## Specific Reflection

### Guided Implementation
The Project Specification's mandate for a structured audit log (Option A) provided a reliable debugging foundation. Logging every transaction's independent llm_score and heuristic_score directly alongside the final confidence score made it easy to track down and fix math errors, showing exactly where and why the system was defaulting to an "uncertain" status.

### Real-World Divergence
The project requirements originally called for a simple combined average of the two detection signals. However, early validation testing revealed that combining an open-ended LLM score with a strict string-length calculation caused them to frequently cancel each other out, pulling almost every borderline response toward a generic middle score. To solve this, the production architecture was updated to use an asymmetrical weighted system (70% LLM / 30% Heuristics) alongside a strict divergence filter to catch edge cases.

## AI Usage Disclosure

**Instance 1: Initial Backend Setup and Heuristics Generation**
- AI Directive: Asked the assistant to generate a standard Flask API wrapper containing structural token functions for Type-Token Ratios and sentence variance.
- AI Output: Produced a functional Flask setup, but used an aggressive, uncalibrated multiplier for the TTR calculation that regularly dropped string scores to absolute zero.
- Human Overrides: Rewrote the statistical scaling logic in evaluate_stylometric_heuristics to use smooth boundary limits (1.2 - (ttr * 1.5)), ensuring the local math integrated accurately with the LLM scores.
**Instance 2: Automated Validation Test Suite Creation**
- AI Directive: Asked the assistant to write a standalone script using Python's native urllib library to validate the four required milestone text scenarios against the live API endpoints.
- AI Output: Generated a testing script that included internal formatting tags (``) directly inside active strings and function variables.
- Human Overrides: Cleaned out the misplaced inline tags from the script file to prevent SyntaxWarning and NameError exceptions, restoring the suite to a clean, runnable state.