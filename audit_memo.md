# audit memo

### 3.6 AI Maturity Score Lossiness (Probes 25, 26, 27)

τ²-Bench retail has no concept of a scored capability assessment. The AI maturity scorer produces a 0-3 integer from six weighted public signals. Two failure modes τ²-Bench cannot catch:

**False positive** — a company scores 2-3 but has no real AI capability. A CEO mentioning "AI" in press releases plus a Snowflake instance produces a score of 2. The agent sends a Segment 4 pitch. The CTO replies: "We use Snowflake for dashboards." τ²-Bench grades this as pass because the email completed. Tenacious-Bench must grade it as fail — the AI maturity score was low confidence and should have been omitted.

**False negative** — a company with private GitHub and no public AI commentary scores 0. The agent misses a real Segment 4 opportunity entirely.

Tenacious-Bench includes tasks where AI maturity confidence is explicitly low and grades whether the agent omits the score rather than asserting it.

### 3.6 AI Maturity Score Lossiness (Probes 25, 26, 27)

The AI maturity scorer produces a 0-3 integer from six weighted public signals
(max raw score 12.0). Two high-weight signals (AI roles fraction, named AI
leadership, 3.0 points each), two medium-weight (GitHub activity, exec
commentary, 2.0 each), two low-weight (ML stack, strategic comms, 1.0 each).
Confidence is determined by how many high-weight signals are present.

The phrasing contract in outreach_composer.py governs how score and confidence
map to language: score=0 → omit entirely; score>=1 + high confidence → assert;
score>=1 + medium → observe; score>=1 + low → ask.

τ²-Bench retail cannot test any part of this contract because it has no concept
of scored capability assessments or confidence-gated language choices.

Two failure modes Tenacious-Bench must catch:

False positive: a company with only low-weight signals (e.g. Snowflake instance
+ one press release mentioning AI) scores 1 with low confidence. The correct
agent behaviour is to use "ask" language or omit entirely. An agent that asserts
"your AI infrastructure suggests you are ready for ML platform work" fails this
task even if the email action completed — τ²-Bench would pass it.

False negative: a company with a private GitHub org and no public AI commentary
scores 0. The correct agent behaviour is to omit AI maturity entirely and pitch
on a different signal. An agent that references AI maturity on a score-0 company
is hallucinating — τ²-Bench has no rubric for this.

Tenacious-Bench includes tasks across all four phrasing modes and grades
compliance with the phrasing contract as a binary machine-verifiable check.
