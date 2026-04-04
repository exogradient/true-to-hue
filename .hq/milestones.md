---
title: Milestones
description: Shipped capability inflection points — what became possible, what it proved, what it unblocked.
summary: "All five modes playable. Beta remaining: text-only share."
---

## Beta release `in-progress`

All five modes playable, polished UX. The game is worth sharing broadly.

**Will prove:** Full skill coverage — each of the five perceptual skills has a dedicated training mode.
**Will unblock:** Public launch, broader feedback, progression/tracking features.
**Will ship:** Scoring curve finalized, share results.

**Shipped so far:**
- All five modes playable (Play, Match It, Picture It, Call It, Split It)
- Scoring calibration pipeline (auto-grader, regression fixtures, population profiling)
- Homepage redesign, OG social preview, PWA icon suite
- Mobile hardening (viewport-fit=cover, safe-area insets, touch targets, iPhone Safari validated)
- Adaptive memorize overlay (pill contrast adapts to target brightness)

**Remaining:**
- Text-only share (navigator.share / clipboard + toast)

## 2026-03-30 — Alpha release `completed`

Client-driven architecture — color generation + CIEDE2000 scoring fully client-side, games start instantly with no server round-trip. Three modes playable (Play/Match It/Picture It). Per-color reveal with HSB slider visualization, hue-recovery bonus. Resilience shipped: error handling, localStorage hardening, reduced-motion, font fallback, mobile layout fixes. PostHog analytics live with 10-insight Alpha Analytics dashboard. Scoring calibration pipeline shipped — auto-grader, regression fixtures, parity checks, population profiling — and first tuning cycle produced the release-gated `effective_delta_guard` scorer.

**Proved:** The core loop is fun and teaches color perception without jargon.
**Unblocked:** Broader playtesting, feedback collection, remaining mode implementation.

## 2026-03-29 — v1 live on Vercel `completed`

Frontend design upgrade and Vercel deployment. The app is publicly reachable for the first time — anyone with the URL can play the core loop.

**Proved:** Single-file frontend + FastAPI backend deploys cleanly on Vercel's serverless Python runtime.
**Unblocked:** External playtesting, sharing, iteration with real users.

## 2026-03-28 — Project bootstrap `completed`

Repo from zero to working prototype in a single session. Backend (FastAPI/SQLite), frontend, CIEDE2000 scoring, five-skill model with scientific grounding, visual identity, user journey spec, competitive analysis of 6 color games.

**Proved:** Color perception training can be structured as a game with measurable skills — not just "guess the color."
**Unblocked:** All five game modes have a design foundation; frontend implementation can begin against a real backend.
