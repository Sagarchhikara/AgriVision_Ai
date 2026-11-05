# AgriVision frontend

Next.js (App Router) client for the AgriVision FastAPI backend in the repo root.

## Setup

```bash
cp .env.example .env.local   # point NEXT_PUBLIC_API_BASE_URL at the backend
npm install
npm run dev                  # http://localhost:3000
```

The backend must allow this origin: its default CORS origin is
`http://localhost:3000`; set `AGRIVISION_CORS_ORIGINS` (a JSON list) for anything else.

## Scripts

| Script                            | Purpose                                                              |
| --------------------------------- | -------------------------------------------------------------------- |
| `npm run dev` / `build` / `start` | Next.js                                                              |
| `npm test`                        | Vitest unit tests (`lib/*.test.ts`)                                  |
| `npm run lint`                    | ESLint                                                               |
| `npm run typecheck`               | `tsc --noEmit`                                                       |
| `npm run format` / `format:check` | Prettier                                                             |
| `npm run gen:api`                 | Regenerate `openapi.json` and `lib/api-types.ts` from the backend    |
| `npm run gen:types`               | Regenerate `lib/api-types.ts` from the committed `openapi.json` only |

## API types

`lib/api-types.ts` is generated, never edited by hand. `gen:api` exports the
schema straight from the FastAPI app (`python -m backend.openapi_export`), so it
needs the backend's Python dependencies but not a running server, the model
checkpoint, or the dataset. Activate the repo's virtualenv first, or set
`PYTHON=/path/to/python`.

Re-run it after any backend schema change and commit both files; the diff to
`openapi.json` is the API contract change.

## UI components

`components/ui/` holds shadcn/ui components, restyled for large touch targets.
Add more with `npx shadcn@latest add <name>`. Do not `@import "shadcn/tailwind.css"`:
with `@tailwindcss/turbopack` it silently drops the rest of `globals.css` (see
`app/shadcn-variants.css`). If an added component needs a variant that is not in
that file, copy it in. After `shadcn add`, check the build still contains the theme.

## Languages

English, Hindi, and Punjabi, under `/en`, `/hi`, and `/pa`. `proxy.ts` sends a path
without a locale to the saved choice (`NEXT_LOCALE` cookie) or the browser's language.

- Strings live in `lib/i18n/dictionaries/`. `en.ts` is the reference; the others are
  typed as `Dictionary`, so a missing key fails the build.
- **`hi.ts` and `pa.ts` are unreviewed drafts.** A native speaker with agronomy
  knowledge must check them, especially disease names, before they reach farmers.
- The locale is also sent to `/report` as `language`. The fake LLM provider always
  answers in English, so translated reports need a real provider.
- The analysis state sits in the root layout, above `[locale]`, so that switching
  language keeps the photo. Keep it there: anything under `[locale]` remounts on a
  switch, and `<html lang>` is set by `components/locale-html.tsx` for the same reason.
