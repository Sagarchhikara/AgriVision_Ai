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
