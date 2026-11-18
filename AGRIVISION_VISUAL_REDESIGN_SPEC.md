# AgriVision — Visual Redesign Specification
Version 1.0 | 2026-11-05

## Identity
**Direction:** Hybrid scientific SaaS × Earth palette × Balanced density  
**Brand line:** Grow with clarity.  
Positioning: a trustworthy crop-health intelligence platform that makes AI-assisted plant diagnosis understandable and useful.

The interface should feel earthy, not rustic; scientific, not clinical; premium, not flashy; friendly, not childish; information-rich, never cluttered.

## Design principles
1. Trust before delight: never make a prediction look more certain than the model warrants.
2. Evidence is visible: submitted image, model crop, Grad-CAM and ranked predictions belong in one coherent hierarchy.
3. One primary action per screen.
4. Readable outdoors: strong contrast, large touch targets, restrained decoration and light default theme.
5. Progressive disclosure: useful result first, technical detail available without overwhelming the user.
6. Responsive by design: mobile is first-class, not a compressed desktop.

## Color tokens
| Token | Hex | Use |
|---|---|---|
| Forest | #354B35 | Primary brand, primary buttons |
| Olive | #77815A | Secondary brand, selected states |
| Terracotta | #C47B55 | Warm accent |
| Sand | #E8DDC7 | Soft surfaces, chips |
| Canvas | #F7F4EC | Main background |
| Charcoal | #282B25 | Primary text |
| Stone | #B9A88B | Borders, muted accents |
| Harvest | #D7A84B | Caution / attention |
| Surface | #FFFFFF | Cards |
| Muted | #6E7168 | Secondary text |

Use semantic status colors for healthy, uncertain, error and informational states. Never communicate status through color alone. Validate contrast to WCAG AA.

## Typography
- Headings: Manrope or Plus Jakarta Sans.
- Body/UI: Inter.
- Numeric metrics: tabular numerals.
- Suggested scale: display 40–48px desktop / 32–36px mobile; H1 32/28px; H2 24px; H3 18–20px; body 16px; supporting 14px.
- Avoid tiny uppercase labels for essential information.

## Layout and components
- Main content max width around 1280px.
- Balanced density: spacious sections, useful information above the fold.
- Desktop: one consistent sidebar or top-navigation pattern.
- Mobile: compact top bar and bottom navigation where useful.
- Spacing: 4, 8, 12, 16, 24, 32, 48, 64px.
- Cards: 14–18px radius; controls: 10–12px radius.
- Warm neutral borders, restrained shadows, 150–220ms motion; respect reduced-motion settings.

Shared components: wordmark, app shell, responsive navigation, page header, buttons, cards, metric cards, status badges, upload/dropzone, camera action, image preview, prediction rows, confidence indicator, Grad-CAM viewer, report sections, callouts, skeletons, empty/loading/error states, language switcher, feedback controls, accessible dialogs/tooltips/toasts.

Reuse existing shadcn/Radix primitives. No major dependency without approval.

## Screen specifications

### Dashboard / home
- Greeting and concise product promise.
- Prominent New Diagnosis action.
- Recent diagnoses only if backed by persisted data.
- Photo-taking guidance and short explanation of AI limitations.
- If history persistence is absent, show a useful first-run state; never invent statistics or history.

### Diagnosis workspace
- Large upload canvas with supported formats and size limit.
- Camera capture on supported touch devices.
- Preview, remove and replace actions.
- Photo tips: focus on one affected leaf, use daylight, avoid busy backgrounds.
- One dominant Check this leaf action.
- Preserve current validation, EXIF correction, resizing and model crop behavior.

### Results
- Persistent AI suggestion only notice.
- Original image and exact model crop.
- Grad-CAM with explanation: attention visualization, not proof.
- All top-k predictions in ranked order.
- Confidence must never display 100%.
- Preserve distinct uncertain and healthy variants.
- Confident-result treatment advice remains under “If your officer confirms this”.
- Uncertain results must not show chemical recommendations.
- Keep feedback visible and easy to use.

### Detailed report
- Clear disease/healthy/uncertain context.
- Sections for symptoms, possible causes, precautions and next steps only where supplied by API.
- Retain expert-confirmation framing.
- No invented dosage or brand-name advice.
- Print-friendly layout; export/share only if implemented and supported.

### History / insights (future, requires persistence/API support)
- Previous diagnosis cards, dates and status.
- Search/filter only when backed by stored data.
- Reopen report and show feedback/correction status.
- No fabricated charts or aggregate statistics.

## Responsive and accessibility
- Test 360, 390, 768, 1024 and 1440px widths.
- Aim for 44×44px interactive targets.
- Visible keyboard focus, logical heading structure and landmarks.
- Accessible names for icon-only controls.
- Announce asynchronous result/report updates to assistive technology.
- Keyboard-operable upload, dialogs and image comparisons.
- Real screen-reader and physical Android/iOS testing before release.

## Non-regression constraints
- Do not change API contracts or request sequencing.
- Prediction remains visible before the separately requested LLM report.
- English, Hindi and Punjabi continue to work.
- Photo survives language switching.
- JPEG, PNG and WebP validation remains intact.
- Preserve EXIF orientation, resize and model-aligned crop.
- Show all top-k predictions and AI-suggestion disclaimer on every result.
- Never show 100% confidence.
- Preserve current uncertain-result rules: hide urgency and disease naming; never show chemical recommendations.
- Healthy results do not show a treatment section.
- Feedback behavior and no-photo-storage policy remain unchanged.
- Preserve understandable errors, loading states and report failures.

## Phase V1 — Design foundation
1. Inspect current frontend tokens, app shell and reusable primitives.
2. Add semantic earth-palette tokens.
3. Establish typography and global hierarchy.
4. Establish spacing, radius, border, shadow and focus tokens.
5. Update shared buttons, cards, inputs, badges and navigation styling.
6. Add responsive app-shell primitives without changing routes.
7. Capture before/after screenshots and run existing checks.

### Out of scope
No backend/model changes, API changes, invented dashboard data, new major dependencies, diagnosis safety changes or translation changes. Do not redesign every page in V1.

### Acceptance criteria
- Existing routes render.
- Upload, prediction, report and feedback flows still work.
- Existing tests, lint, typecheck and production build pass.
- No horizontal overflow at target widths.
- Focus states and contrast are acceptable.
- Shared components use semantic tokens, not duplicated hard-coded palette values.
- Before/after screenshots are recorded.

## Workflow
Use small commits. After each phase, summarize changed files and decisions, list actual checks and results, provide manual verification steps, disclose unverified behavior, and wait for owner approval before the next phase.

**Implementation note:** This is the design target, not an assumption about the repository. Inspect actual source files before changing them; do not overwrite project conventions based on guessed paths.
