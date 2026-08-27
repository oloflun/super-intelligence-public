# Handoff

**Load when packaging a design for someone else to implement — a collaborator, another agent, or a future session.**

> Source: Anthropic's Claude Design "Handoff to Claude Code" skill, ported at full fidelity with the direction inverted. Blocks marked **[ours]** are this repo's framing.

**[ours] Direction inverted.** The upstream skill packages a design *out of* Claude Design *into* Claude Code. Here we are Claude Code, so this serves two purposes: handing a design to a human developer or another tool, and writing the spec a fresh session reads to continue work without the conversation. The README structure is the same either way, and its self-sufficiency requirement is what makes it work for both.

---

## Steps

1. **Create a handoff folder** in the project: `design_handoff_<feature-name>/` — a descriptive name derived from the design (`design_handoff_onboarding_flow`, `design_handoff_settings_redesign`).
2. **Write `README.md`** with the structure below.
3. **Copy the relevant design files** into the folder (prototypes, component files).
4. **Tell the user where it is.**

## README structure

```markdown
# Handoff: <Feature Name>

## Overview
Brief description of what this design is for and what it accomplishes.

## About the Design Files
State clearly that the files in this bundle are **design references** — prototypes
showing intended look and behavior, not production code to copy directly. Explain
that the task is to **recreate these designs in the target codebase's existing
environment** (React, Vue, SwiftUI, native, etc.) using its established patterns and
libraries — or, if no environment exists yet, to choose the most appropriate
framework and implement the designs there.

## Fidelity
State clearly whether the mocks are:
- **High-fidelity (hifi)**: Pixel-perfect mockups with final colors, typography,
  spacing, and interactions. Recreate the UI pixel-perfectly using the codebase's
  existing libraries and patterns.
- **Low-fidelity (lofi)**: Wireframes or rough layouts showing structure and flow.
  Use as a guide for layout and functionality but apply the codebase's existing
  design system for styling.

## Screens / Views
For each screen or view:
- **Name**: What this screen is called
- **Purpose**: What the user does here
- **Layout**: Detailed description (grid structure, flex directions, widths,
  heights, margins, padding)
- **Components**: List each UI component with:
  - Position and size
  - Colors (exact hex values if hifi)
  - Typography (font family, size, weight, line-height, letter-spacing)
  - Border radius, shadows, borders
  - Hover/active/focus states
  - Content/copy (exact text used)

## Interactions & Behavior
- Click handlers and navigation flows
- Animations and transitions (duration, easing, properties)
- Hover states
- Loading states
- Error states
- Form validation rules
- Responsive behavior

## State Management
- What state variables are needed
- State transitions and their triggers
- Any data fetching requirements

## Design Tokens
- Colors (with hex values)
- Spacing scale
- Typography scale
- Border radius values
- Shadow values

## Assets
List any images, icons, or other assets used and where they came from.

## Files
List the files that contain the design, so the developer can reference them.
```

## Important notes

> *"Be extremely precise about measurements, colors, and typography — the developer will rely on this documentation."*

> *"Make sure the README states up front that the bundled files are **design references**, and that the described behavior should be understood as recreating those designs in the target app's existing environment (or the best choice of framework if none exists yet) — not shipping the prototype directly."*

> *"If the design uses [a company's] brand assets, mention that they should use the existing brand system in their codebase."*

> *"After creating, ask user if they want screenshots of the designs to be included. Don't include them by default."*

> *"The README should be self-sufficient — a developer who wasn't in this conversation should be able to implement the design from the README alone."*

---

## [ours] Relationship to `DESIGN.md`

These are different artifacts and both can exist. `DESIGN.md` is the **durable system** for the whole project — tokens, voice, component language — and the detector reads it. A handoff README is the **spec for one feature** — screens, states, interactions, exact values.

If `DESIGN.md` exists, the handoff's Design Tokens section references it rather than restating it, and says so: *"Tokens are in `DESIGN.md` at the project root; values below are the subset this feature uses."* Duplicating tokens into a handoff creates a second source of truth that drifts.

**[ours] Include the direction contract.** impeccable v4 stamps a five-block contract into the artifact's opening comment — THESIS, OWN-WORLD, STORY, FIRST VIEWPORT, FORM. If the build carried one, copy it into the Overview. It tells the implementer what the design is *for*, which no amount of measurement conveys, and it is what a later reviewer audits the render against.

**[ours] Name what's unresolved.** Any placeholder, any assumption made on a silent axis, any commercial claim left as a marked placeholder for the user to replace — list it. A handoff that reads as complete when it isn't turns into a shipped page with invented metrics in it.
