# Design

## Source of truth

- Status: Active
- Last refreshed: 2026-07-18
- Primary product surfaces: Local LiveKit demo and the standalone eight-section contributor-guide page.
- Evidence reviewed: `README.md`, `RUNBOOK.md`, `AGENTS.md`, `agents-guide.html`, `livekit/web/index.html`, `livekit/web/styles.css`, and `livekit/web/talk.js`.

## Brand

- Personality: Calm, practical, and workshop-friendly.
- Trust signals: Plain language, visible source text, and explicit local/offline guidance.
- Avoid: Decorative complexity, hidden interactions, and a dependency-heavy documentation stack.

## Product goals

- Goals: Make the full workshop and contributor guidance easy to scan, understand, and revisit without a server.
- Non-goals: Replace the source `AGENTS.md` or build a full documentation platform.
- Success signals: A contributor can navigate sections, track reading progress, and test their understanding from one page.

## Personas and jobs

- Primary personas: Workshop attendees and contributors new to this voice-agent repository.
- User jobs: Find the right command, understand folder ownership, and follow contribution expectations.
- Key contexts of use: Desktop or mobile, locally opened from the repository.

## Information architecture

- Primary navigation: Eight-section navigation list with a progress indicator and a completion check.
- Core routes/screens: `agents-guide.html` only.
- Content hierarchy: Repository map and architecture; offline development; guardrails and tools; providers, cost, and configuration; voice-loop behavior; LiveKit/SIP scope; validation; contribution and safety expectations.

## Design principles

- Keep the source guidance recognizable and never obscure it behind a quiz.
- Use progressive disclosure for detail while keeping important commands one click away.
- Tradeoffs: A standalone page favors portability over shared component reuse.

## Visual language

- Color: Dark-first navy surfaces, high-contrast off-white text, indigo actions, and green completion feedback.
- Typography: System sans-serif for fast, readable local rendering.
- Spacing/layout rhythm: Generous 16–24px spacing with a two-column desktop layout that collapses on mobile.
- Shape/radius/elevation: Subtle borders and 12px rounded cards; minimal shadow.
- Motion: Short, optional transitions; honor reduced-motion preferences.
- Imagery/iconography: Text and simple Unicode symbols only; no external assets.

## Components

- Existing components to reuse: None; the LiveKit UI is a separate operational surface.
- New/changed components: Eight navigation buttons, expandable guide cards, command copy buttons, reading checklist, and completion panel.
- Variants and states: Selected, expanded, copied, checked, and complete.
- Token/component ownership: Local CSS custom properties in `agents-guide.html`.

## Accessibility

- Target standard: Practical WCAG 2.1 AA baseline.
- Keyboard/focus behavior: Native buttons, semantic headings, visible focus outlines, and keyboard-operable expand/copy controls.
- Contrast/readability: High-contrast text, 16px body text, and no information conveyed by color alone.
- Screen-reader semantics: `aria-expanded`, live copied feedback, and labelled regions.
- Reduced motion and sensory considerations: Disable transitions when `prefers-reduced-motion` is enabled.

## Responsive behavior

- Supported breakpoints/devices: Modern desktop and mobile browsers.
- Layout adaptations: Sidebar becomes horizontal, content cards become single-column.
- Touch/hover differences: All interactions use tap/clickable buttons; hover is nonessential.

## Interaction states

- Loading: None; all guidance is embedded for offline use.
- Empty: No dynamic data sources.
- Error: Clipboard falls back to selecting text without blocking reading.
- Success: Copy confirmation and a reading-complete panel.
- Disabled: Completion action is disabled until all sections are marked read.

## Content voice

- Tone: Direct, instructional, and concise.
- Terminology: Match `AGENTS.md`, `README.md`, and `RUNBOOK.md` names for scripts, directories, configuration, and commands.
- Microcopy rules: State the action first and include the expected result where useful.

## Implementation constraints

- Framework/styling system: Single static HTML file with vanilla JavaScript and CSS.
- Design-token constraints: Local custom properties only; no new packages.
- Performance constraints: No network calls or build step.
- Compatibility constraints: Modern browsers with optional Clipboard API.
- Test/screenshot expectations: Open locally and verify keyboard navigation, expansion, copy feedback, and responsive layout.

## Open questions

- [ ] Whether the guide should later be linked from the main README / owner: maintainers / impact: discoverability.
