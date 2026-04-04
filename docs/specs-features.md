---
title: Feature Specs
description: Committed feature specs — enough detail to implement
stability: evolving
responsibility: Committed feature specs — enough detail to implement
---

# Feature Specs

## Challenge Sharing

Share a game as a 6-char code so others play the same colors and compete on a leaderboard. Full design in `design-sharing`.

**Creator flow:** Finish game → Share button → enter name → POST creates challenge → show code + leaderboard. Copy code via clipboard.

**Joiner flow:** Enter code on home screen → GET fetches challenge → game starts with same mode + colors → finish → enter name → POST submits entry → leaderboard.

**Constraints:** Max 20 entries per challenge. Unique names per challenge (409 on duplicate). No auth — display names only. Client-side scoring (server trusts `total_score`). All 5 modes supported.

**Backend:** 3 endpoints (`POST /api/challenge`, `GET /api/challenge/{code}`, `POST /api/challenge/{code}`). Turso HTTP API in production, local SQLite fallback. `last_played_at` column for future TTL.

## Auto-Grader

No committed public/runtime feature spec yet. Current committed alpha scope is local-only tooling: `tools/calibration.jsx` for assisted collection and `make calibrate-release` for scorer gatekeeping. This is intentionally not a public runtime surface.

The research-grounded design for this work lives in `design-auto-grader.md`. Keep the volatile rationale, architecture, and evolution path there until the export schema and runner contracts harden enough to promote into specs without duplicating churn.
