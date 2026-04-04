---
title: Ideas & Raw Thoughts
description: What we might do — actionable, speculative, or raw. Append-only.
stability: volatile
responsibility: Prioritized direction — what we might build, ordered by readiness
---

## Beta — shipped

All five modes playable with full visual identity. Adaptive memorize overlay, challenge sharing (`design-sharing`).

**Ongoing:**
- Scoring drift monitoring: continue tuning against `auto-grader` verdicts, revisit edge cases if fresh exports show disagreement

## Planned

### Insights (diagnostic) `advanced`

Hidden power-user feature — no visible UI toggle. Activated via URL param, keyboard shortcut, or similar discovery mechanic.

Lens on Play data. Decomposes where errors come from and routes to the right mode.

### Sharing + Leaderboard

Core social loop. v1 shipped (`design-sharing`): challenge codes, per-challenge leaderboard (max 20), name entry.

**Remaining:**
- **Share results** — shareable text card after each game (score, mode, color swatches). No image gen
- **Daily challenge** — same colors for everyone, compare scores
- **Server-side scoring** — CIEDE2000 re-validation to prevent score spoofing
- **Global leaderboard** — filterable by mode (needs persistent DB, which Turso enables)

### Progression

Personal best tracking per mode (prominent on menu), streak tracking (games per day/week), improvement-over-time visualization. localStorage history already captures game data — confirm schema supports everything needed before adding new modes.

## Worth Exploring

### Feedback messages — tone and personality

Current messages are generic and encouraging ("Perfect!", "Great", "Keep practicing").

**Voice:** Honest, direct, fun. Not brutal/snarky (that's dialed's voice and doesn't match our warm visual identity). Not encouraging/generic (that's boring). A sparring partner — specific about what happened, personality in the delivery.

**Voice varies by mode context:**
- **Play:** Sharper, more personality. You're testing yourself. "You saw teal. You played cyan." Fun to fail at without being mean.
- **Skill modes** (Match It, Call It, Split It, Picture It): Coach. Constructive, specific. "Hue spot-on, saturation 20% high." The feedback teaches.

No user-facing tone toggle — the mode selection is the toggle.

**Scope:** ~150 hand-crafted messages across per-color and per-round banks, multiple variants per score tier.

No design-log decision yet — voice direction above is the working spec.

### Snap It — image color explorer `learning`

Pure learning mode, no scoring. Load an image, drag a selector across pixels. At each position show HSB values and XKCD color name. Builds color intuition by connecting real-world visuals to the HSB/naming vocabulary the other modes test.

No game loop — this is a reference tool. Could use camera input (mobile) or photo upload. Reuses the XKCD name-lookup already in Call It.

### Educational (nearly free)
- Real-world color examples ("this is the same hue as a school bus") — contextual to gameplay

### Onboarding `v2`

3-screen guided first-play: (1) "You'll see a color for 5 seconds," (2) "Recreate it from memory," (3) "Let's try one." Interactive, skippable. The card-stack home screen may already solve cold start — revisit if analytics show high first-session drop-off.

### Desktop differentiation

27" monitors expose the mobile-first void around the 1180px content shell. Ambient treatment for surrounding space: noise texture at 2-3% opacity or slow gradient. Makes desktop feel intentional, not "mobile on a big screen."

## Raw / Unfiltered

### Educational (needs evidence)
- Color theory tips contextual to mistakes

### Deferred
- Multiplayer real-time
- Cultural/historical color context
- Synesthesia associations, cross-domain connections
- Progress charts and trend analysis (covered by Progression above)
