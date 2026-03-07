# Rapid UX Test
Use for this: Run a 5–10 minute usability test or heuristic evaluation to uncover friction before shipping.

Constraints: Never fabricate participant quotes or data. State sample size clearly. Focus on behavior, not opinions.
Agent note: Aim for observable facts ("user paused 8 seconds") not inferences ("user was confused"). Infer only when backed by observation.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## When to Use This
- Before shipping a new flow (pre-launch spot-check)
- After a bug report pointing to UX confusion
- Sprint retro question: "Why aren't users clicking X?"
- Designer / dev disagreement — resolve with real data

## 5-Minute Usability Test Script

```
SETUP (1 min):
"I'm going to show you this screen. Please think out loud as you go — 
there are no wrong answers. I'm testing the design, not you."

TASK (3–4 min):
Give ONE clear task: "You need to [do X]. Go ahead."
Do NOT help or hint. Observe silently. Note:
  → Where they hesitate
  → What they click first (right or wrong?)
  → What they say under their breath
  → Where they stop or give up

DEBRIEF (1 min):
"What was confusing, if anything?"
"What would you expect to happen when you clicked [X]?"
"On a scale of 1–5, how easy was that? Why?"
```

## Observation Checklist (note during test)

```
[ ] First click: correct target? [ Yes / No / Wrong area ]
[ ] Time to task completion: ___s (goal: < 30s for simple tasks)
[ ] Hesitation points: ___
[ ] Error recovery: did user find their way back? [ Yes / No ]
[ ] Verbal confusion signals: "where is...", "I expected...", "huh"
[ ] Rage clicks (multiple rapid clicks on same element): [ Yes / No ]
[ ] Abandonment: stopped before completing: [ Yes / No ]
```

## Heuristic Evaluation (solo — no participants needed)

Score each area 0 (fine) → 3 (major issue):

| Heuristic | Score | Notes |
|---|---|---|
| Visibility of system status | | Does user know what's happening? |
| Match with real world | | Does language match user's expectations? |
| User control & freedom | | Easy to undo / go back? |
| Error prevention | | Does UI prevent mistakes? |
| Recognition over recall | | Options visible, not memorized? |
| Consistency & standards | | Same patterns throughout? |
| Flexibility & efficiency | | Power-user shortcuts available? |
| Aesthetic & minimalism | | No unnecessary info competing for attention? |

## Findings Report Template

```
UX FLASH REPORT
Date: [date]  |  Feature: [name]  |  Participants: [n] (or solo heuristic)

TOP FINDINGS:

[P0 - Blocker]
Observation: [exact behavior]
Impact: [who is affected, how often]
Fix: [1-sentence fix recommendation]

[P1 - Significant]
Observation: [exact behavior]
Fix: [recommendation]

[P2 - Minor]
Observation: [exact behavior]
Fix: [recommendation]

QUICK WINS (< 1 hour to fix):
- [UX copy change, tooltip, visual cue]

ASSUMPTIONS / CAVEATS:
- Sample size: [n] — findings are directional, not statistically significant
- Testing environment: [device, browser]
```

## Prioritization Rule
- **P0**: User cannot complete the core task → fix before launch
- **P1**: User completes but with significant friction → fix this sprint
- **P2**: Minor confusion, easily worked around → backlog

## Anti-Patterns to Avoid
- Asking "Do you like this?" → opinion, not behavior
- Helping during the task → contaminates results
- Recruiting only internal team members → they know too much
- Testing with unrealistic tasks → "pretend you're buying X" with no context
