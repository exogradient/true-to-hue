---
title: "Phase 1 Visual Foundation Brief"
date: 2026-03-29
---

# Phase 1 Visual Foundation Brief

Design brief that guided the visual upgrade. Core research on chromatic neutrality, depth-through-luminance strategy, and specific implementation decisions. All changes shipped — this is the frozen analysis, not a living spec.

## Core Constraint — Chromatic Neutrality During Gameplay

Research confirms that the UI of a color perception game **must remain achromatic during active gameplay**. This isn't a style preference — it's a perceptual requirement.

### Why

**Chromatic adaptation**: The human visual system adjusts to surrounding colors within seconds. If the UI has even a subtle blue tint, the player's perception of subsequent colors shifts toward yellow/warm — biasing their memory and matching. Research shows background hue can shift perceived color by **30+ degrees** ([ARVO Journals](https://jov.arvojournals.org/article.aspx?articleid=2121588)).

**Simultaneous contrast**: Colors appear different depending on their surround. A target swatch displayed next to a tinted panel will look different than the same swatch on neutral gray. This directly undermines scoring fairness ([Nature, Scientific Reports](https://www.nature.com/articles/s41598-020-77241-5)).

**Industry precedent**: Adobe Photoshop and Lightroom switched to neutral gray UI themes specifically to improve color accuracy for photographers ([Envato Tuts+](https://photography.tutsplus.com/tutorials/want-better-color-use-neutral-gray-themes-in-adobe-photoshop-and-lightroom--cms-23342)). The Farnsworth-Munsell 100 Hue Test (the closest professional analogue to this game) uses strictly neutral surrounds.

### Chromatic Rules by Phase

| Game phase | Chromatic accents allowed? | Rationale |
|---|---|---|
| Memorize | **No** | Player is encoding color into memory |
| Pick / Match / Picture | **No** | Player is recalling and comparing color |
| Countdown | **No** | Immediately precedes memorization |
| Reveal | **Minimal** — score tier only | Perception test is complete for this round |
| Results | **Yes** — score tiers, celebration | All perception work is done |
| Menu | **Cautious** — very desaturated only | Player may start a round immediately |
| History | **Yes** — replay context, not active perception | Reviewing past performance |

## Design Strategy: Depth Through Luminance

Without chromatic color, visual hierarchy comes from:

1. **Luminance hierarchy** — three panel depth levels (`--surface`, `--surface-raised`, `--surface-elevated`) with distinct luminance steps. On dark backgrounds, shadows are less visible, so depth comes from surface luminance and border brightness.
2. **Inner light simulation** — `inset box-shadow` with subtle white simulates light hitting panel edges ("glass card" effect).
3. **Typography weight contrast** — 400/500/600/700 weight range (was uniform 500/600).
4. **Spatial rhythm** — tight grouping within related elements, generous breathing room between sections.
5. **Score-tier color** — post-gameplay only. Desaturated accents for achievement tiers (amber/gold for elite, cool teal for strong, warm gray for solid).
