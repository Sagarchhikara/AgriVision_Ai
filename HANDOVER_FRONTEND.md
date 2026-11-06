# AgriVision_Ai: Web Frontend Handover

Last updated 2026-11-05. Covers the web frontend and the backend changes made to support it. For the model, data pipeline, and LLM layer, read `HANDOVER.md`; this document overrides it where the two disagree (see §10).

## 1. Current state

Phases 0 to 4 of 6 are done. The app works end to end in English, Hindi, and Punjabi against the real model. **It is not ready for farmers**: see §8.

| Phase | Scope | Status |
| --- | --- | --- |
| 0 | API contract review | Done |
| 1 | Backend support, frontend scaffold, typed API client | Done |
| 2 | Upload screen, photo preparation, `/predict`, basic result | Done |
| 3 | Report, uncertain layout, feedback, error states | Done |
| 4 | Hindi and Punjabi, accessibility, responsive polish | Done |
| 5 | Dockerfiles, `docker-compose.yml`, deployment notes | **Next, not started** |

**Where the code is:** branch `feature/frontend`, 11 commits ahead of `main`. Not pushed, not merged.

**Uncommitted work that is not part of this branch:** `HANDOVER.md` and `evaluate.py` have local edits from before the frontend work started. They have deliberately been left out of every commit.

## 2. How the work is run

The owner reviews each phase before the next starts. After a phase: summarize it, list what changed, give steps to verify it, and wait for approval.

- Do not touch `models/`, `engine/`, `data/`, `main.py`, `evaluate.py`, or `backend/services/report_prompts.py`. Do not retrain or refactor the model.
- Ask before adding a major dependency or changing the architecture.
- If the spec and the code disagree, trust the code and say so.
- Small commits with real messages, never `auto:`.
- Report problems rather than working around them silently.

## 3. Product rules

The model is 96% accurate on lab photos and **56.9% on real field photos**, and about 1 in 4 field photos gets a confident, wrong answer. A confidence threshold cannot catch those. So the UI must never present a diagnosis as authoritative. These rules follow from that and should not be relaxed without the owner's agreement:

- The "AI suggestion only" notice appears on every result, at any confidence.
- All top-k predictions are shown, never just the first.
- Confidence never reads 100%. Near-certain values show as `>99%`, because softmax saturates on wrong predictions too (`lib/format.ts`).
- Treatment advice on a confident result sits under "If your officer confirms this".
- Dosages and brand names are never displayed. The backend prompts forbid them; the UI adds none.

The report changes by variant, because the same fields mean different things (`components/result/report-view.tsx`):

| | Standard | Uncertain | Healthy |
| --- | --- | --- | --- |
| Headline | "Most likely: X" | "Uncertain result", no disease named | "Most likely: Healthy" |
| Urgency | Shown | **Hidden**: it rates the uncertainty, so "Low" would falsely reassure | Hidden |
| `disease_name` | Not used; the headline comes from the class label | **Hidden** | Not used |
| Chemical list | Shown, plus a fixed "speak to your officer" note | **Never shown**, even if the LLM writes one; a fixed "do not spray yet" note replaces it | No treatment section |

Uncertain applies if either `/predict` or the report flags low confidence. Low confidence is checked before healthy, on purpose: a weak "healthy" is the false negative that costs a crop.

## 4. Running it

```bash
# Backend (terminal 1), from the repo root
source .venv/bin/activate
AGRIVISION_LLM_PROVIDER=fake uvicorn backend.app:app --port 8000

# Frontend (terminal 2)
cd frontend
cp .env.example .env.local      # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm install
npm run dev                     # http://localhost:3000
```

`backend/.env` sets `AGRIVISION_LLM_PROVIDER` and a real `GEMINI_API_KEY`, so **omitting the `fake` override spends real Gemini calls**. The fake provider always answers in English, so translated reports need a real provider.

Requires Node 22 or newer. To reach it from a phone, point `NEXT_PUBLIC_API_BASE_URL` at the machine's LAN IP and add that frontend origin to `AGRIVISION_CORS_ORIGINS`. The camera button only appears on touch devices.

| Command | Purpose |
| --- | --- |
| `pytest` (repo root) | Backend tests, no network, key, or checkpoint needed |
| `npm test` | Frontend unit tests |
| `npm run lint`, `typecheck`, `format:check`, `build` | Static checks |
| `npm run gen:api` | Regenerate `openapi.json` and `lib/api-types.ts`. Run it with the venv active after any backend schema change, and commit both files. Needs no server, checkpoint, or dataset. |

## 5. Backend changes

| Change | Detail |
| --- | --- |
| `GET /meta` | Class list, languages, default language, upload limits |
| `POST /feedback` | `verdict` yes/no/unsure and optional `correct_class`, appended to `outputs/feedback/feedback-YYYY-MM-DD.jsonl`. No photo is received or stored. The prediction is sent back by value, because `/predict` keeps no record. |
| `/predict` | Adds `is_low_confidence`, from the same `Settings.is_low_confidence()` the report layer uses |
| Upload limits | JPEG, PNG, or WebP only, checked on the declared type and the decoded format. Chunked read capped at `max_upload_bytes` (10 MB). |
| New errors | `image_too_large` (413), `unsupported_image_type` (415), `invalid_feedback` (422) |
| `language` | Restricted to `en`, `hi`, `pa`; anything else is a 422 |
| `ErrorResponse.error` | Now a closed list, so generated TypeScript types enumerate every code. A test fails if an exception class is missing from it. |
| CORS | Default origin `http://localhost:3000` instead of `*`, no credentials, GET and POST only. `AGRIVISION_CORS_ORIGINS` must be a JSON list: `'["https://app.example"]'`. |
| `create_app()` | Accepts a `Settings` override, for tests |
| `backend/openapi_export.py` | Writes the OpenAPI schema without starting the app |

The error code travels in the JSON field `error`, not `error_code`.

`test_plain_predict_has_no_report_fields` was changed to expect `is_low_confidence`. Its checks that no report keys appear are unchanged.

**`report_error` is unused by the frontend.** That field only exists on `/predict?include_report=true`. The app calls `/predict` and `/report` separately so the result appears without waiting for the LLM, so report failures arrive as error responses from `/report`.

## 6. Frontend

Next.js 16 (App Router), React 19, Tailwind 4, shadcn/ui on Radix, strict TypeScript. No TanStack Query, no `next-intl`, no image library.

```
frontend/
  proxy.ts                  # sends locale-less paths to the saved or browser language
  app/
    layout.tsx              # root: <html>, AnalysisProvider. Above [locale] on purpose (§7)
    globals.css             # theme tokens; light only, for use outdoors
    shadcn-variants.css     # copied variants (§7)
    landing.css             # landing-only motion and display type; imported by (marketing)
    [locale]/               # layout (I18nProvider only)
      (marketing)/          # / : landing page, with its own nav and footer
      (app)/                # AppShell: /diagnose (upload), /result, 404
  assets/landing/           # landing photos; sources and licences in components/landing/photo-credits.ts
  components/
    landing/                # landing page sections
    upload/  result/  ui/   # screens and shadcn primitives
    language-switcher.tsx  locale-html.tsx  backend-status.tsx  error-alert.tsx
  hooks/                    # use-report, use-health, use-class-list
  lib/
    api.ts                  # typed client; every failure is an ApiError with a code
    api-types.ts            # GENERATED, never edit
    errors.ts               # error code -> message; a new backend code breaks the build until mapped
    image.ts                # validate, orient, resize, crop
    classes.ts              # display names for the 28 classes
    i18n/                   # config, server-only dictionary loader, en/hi/pa
      landing/              # landing strings, kept out of the dictionary sent to every screen
  state/analysis-context.tsx  # photo, prediction, feedbackSent; in memory only
```

**Request flow:** choosing a photo prepares it straight away (validate, apply EXIF rotation, resize to 1024px JPEG at 0.85, crop the model's view). "Check this leaf" calls `/predict` and moves to `/result`, which renders immediately. `/report` then loads under a skeleton in the current language.

**Why photos are re-encoded in the browser:** the backend does not apply EXIF orientation and Pillow cannot read HEIC, so this does more than save bandwidth. A 9.6 MB test photo became about 195 KB.

## 7. Gotchas

- **Never `@import "shadcn/tailwind.css"`.** With `@tailwindcss/turbopack` it silently drops the rest of `globals.css`: all colours vanish and the build still passes. `app/shadcn-variants.css` holds the variants the components need. After `npx shadcn add`, confirm the theme is still in the build, and that the command did not add the import.
- **Keep `AnalysisProvider` above `[locale]`.** Everything under `[locale]` remounts on a language switch. The Next.js docs suggest a root layout inside the locale segment; that was avoided so the in-memory photo survives. `components/locale-html.tsx` sets `<html lang>` from the URL because a server layout up there cannot see the locale.
- **Grad-CAM covers only the model's crop.** The heatmap is the centred 224/255 of the short side, so the result page shows the same crop rather than the full photo. `MODEL_CROP_FRACTION` in `lib/image.ts` mirrors `data/transforms.py`. Change one, change the other.
- **Other values copied by hand:** `KNOWN_CLASSES` in `lib/classes.ts` mirrors the model's classes (unknown classes fall back to a cleaned raw name), and `SupportedLanguage` mirrors `LANGUAGE_NAMES` (a backend test keeps those in sync).
- **The server-rendered 404 is an empty page.** The status is correct and the browser fills in the translated content, so it needs JavaScript. A server-side `<html>` was not tried, so whether the client-rendered `<html>` is the cause is unknown.
- **Landing images are static imports, not `public/` files.** `proxy.ts` would redirect a `public/` path to a locale; `/_next/static` is already skipped. The credit list in `components/landing/photo-credits.ts` is a licence requirement: keep it in step with the photos.
- **The landing page's percentages and advice are samples**, labelled as such. Its Grad-CAM images are real model output, from running those photos through `/predict`.
- **`proxy.ts` needs a running Next server.** The frontend cannot be deployed as a static export.
- **`NEXT_PUBLIC_API_BASE_URL` is fixed at build time.** It is compiled into the browser bundle.
- **`npm audit` shows moderate issues in dev tooling only.** `npm audit --omit=dev` reports 0. Do not run `npm audit fix --force`; it would downgrade ESLint.
- **Next warns about a `package-lock.json` in the home directory.** It is outside the repo and ignored.

## 8. Before this reaches farmers

1. **Review the translations. This is the main blocker.** `lib/i18n/dictionaries/hi.ts` and `pa.ts`, and `lib/i18n/landing/hi.ts` and `pa.ts`, are unreviewed drafts, marked as such at the top. A native speaker with agronomy knowledge should check the disease names in `classes`, the term for extension officer (कृषि विस्तार अधिकारी, ਖੇਤੀਬਾੜੀ ਪਸਾਰ ਅਫ਼ਸਰ), and the disclaimer.
2. **Test on real phones.** Camera capture, low-end Android performance, and iPhone HEIC photos are all unverified. Everything so far used Chromium's mobile emulation.
3. **Test with a real screen reader.** Only automated checks have run.
4. **Decide about LLM tone.** Real reports can sound definite: one Hindi report opens with "this is a very dangerous fungal disease". The wording comes from the prompts, which are off-limits without the owner's say-so.
5. **Mismatched terms.** The LLM's spelling can differ from the dictionary (`पिछेती` vs `पछेती`, `ਪਛਾਤਾ` vs `ਪਛੇਤਾ`), and Punjabi uncertain reports sometimes spell out English names, so a result heading and its report can disagree.
6. **Guardrails rest on the prompt alone.** Nothing checks LLM output for dosages or brand names after generation.
7. **The field accuracy problem itself is unsolved.** See `HANDOVER.md` §8.

## 9. What has been verified

Last full run 2026-11-05, on the final Phase 4 code:

| Check | Result |
| --- | --- |
| Backend tests | 67 pass |
| Frontend unit tests | 36 pass |
| Lint, Prettier, `next build`, production `npm audit` | Clean |
| Browser suite, Phase 3 flows and every forced failure | 54 of 54 |
| Browser suite, Phase 4 routing, axe, keyboard, overflow, tap targets | 56 of 56 |
| Hindi and Punjabi guardrail spot-check | 6 real Gemini reports: no dosages or brands, uncertain reports left `chemical` empty. A small sample, not proof. |

**The browser suites are not in the repo.** They were throwaway Playwright scripts outside the project, because Playwright was not an approved dependency. Treat those two rows as a record of one run, not as tests you can re-run. Adding a real end-to-end suite is an open decision for the owner.

Limits of that testing:

- Most browser runs used the fake provider or hand-written report text, and failures were simulated by intercepting requests. Real reports were rendered only for one standard Hindi and one uncertain Punjabi case.
- Drag-and-drop has not been tested.
- One run timed out waiting for the 404 page. It did not recur and the cause was never found.

## 10. Stale information elsewhere

Not fixed yet, because these were outside the frontend work:

| Where | Says | Actually |
| --- | --- | --- |
| `HANDOVER.md` §2, §8 | Frontend not built | Built, see above |
| `HANDOVER.md` §3 | Lists 38 tests and no frontend | 67 tests, `frontend/` exists |
| `README.md:13`, `configs/config.yaml:37` | ~22% on field photos | 56.9% |
| `README.md:14` | Frontend and Hindi/Punjabi are future work | Built, translations in draft |

The logging bug in `HANDOVER.md` §9 is also still open.

## 11. Next: Phase 5

Scope: Dockerfiles for backend and frontend, `docker-compose.yml` for local development, and a deployment notes document. Must-haves from the brief and from this work:

- **`outputs/checkpoints/best.pt` (47 MB) and `datasets/train` are gitignored and must be supplied to the backend container.** Flag this clearly and propose how to handle it. Class order is derived from `datasets/train`'s folder listing, so a wrong or partial listing mislabels predictions silently.
- **Idea to verify:** `load_class_names` only lists directories, so the 28 empty class folders may be enough, which would avoid shipping the dataset. Read-only volume mounts for the checkpoint and that listing are the likely starting point. Confirm by running it.
- **Keep `outputs/feedback/` on a persistent volume**, or feedback is lost when the container is replaced. It uses one local file per day, so it suits one backend instance, not several.
- **Frontend image:** must run `next start` (see §7) and take `NEXT_PUBLIC_API_BASE_URL` as a build argument.
- **Set `AGRIVISION_CORS_ORIGINS`** to the real origin. Keep API keys in environment variables, and out of images and compose files.
- **A reverse proxy should enforce a body size limit.** The backend's cap runs only after the multipart upload has been received. The client already maps a bare proxy 413 to `image_too_large`.
- **Not done yet on the backend:** load testing, and any rate limiting, including on `/feedback`.
- **PyTorch makes the backend image large**, and the host needs a decision on CPU or GPU. The checks here ran on CUDA; CPU latency has not been measured.
