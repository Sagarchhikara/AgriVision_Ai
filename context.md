# AgriVision AI — Project Context

> **Purpose of this file.** A single, self-contained description of the whole project. Give it to an LLM to generate college deliverables (project report, abstract, synopsis, PPT outline, viva Q&A, literature survey, testing chapter, etc.), or hand it to a teammate to get up to speed.
>
> **Facts here come from the repo** (code, `HANDOVER.md`, `HANDOVER_FRONTEND.md`, `configs/config.yaml`, evaluation outputs), last checked 2026-11-18. Where something is **not done, not measured, or unreviewed**, this file says so. **Do not "improve" those facts when writing reports.** See §20 for instructions to an LLM using this file.

---

## 1. One-paragraph summary

**AgriVision AI** is an explainable AI system for crop disease diagnosis from leaf photos. A farmer uploads a photo of a leaf. An **EfficientNet-B0** deep-learning classifier identifies the most likely disease (or "healthy") among **28 classes** across 13 crops. **Grad-CAM** produces a heatmap showing which part of the leaf drove the prediction. An **LLM layer** (Google Gemini or OpenAI) converts the prediction into a plain-language advice report with symptoms, organic and chemical treatment approaches, prevention and when to consult an expert. It is available in **English, Hindi and Punjabi**. A **FastAPI** backend serves it and a **Next.js** web app is the user interface. The system is deliberately designed to **never present a diagnosis as authoritative**, because the model is excellent on lab images (96%) but only moderate on real field images (56.9%).

**Tagline / brand line:** *"Grow with clarity."*
**Repo/project names:** `AgriVision_Ai`; README title "Crop Disease Diagnosis using Explainable AI".

---

## 2. Problem statement and motivation

- Crop diseases cause major yield loss. Smallholder farmers often cannot reach an agronomist quickly, and misdiagnosis leads to wrong or excessive pesticide use.
- Many existing "plant disease AI" demos report 95%+ accuracy, but those numbers come from clean, single-leaf lab photos (e.g. PlantVillage) and **do not hold up on real field photos** (cluttered backgrounds, lighting, multiple leaves). This project measures and openly reports that gap.
- Farmers are not served by a bare class label. They need: *what is it, how sure is the AI, why does it think so, what should I do, and when must I ask an expert* — in their own language.
- Black-box predictions are hard to trust, so the project adds visual explainability (Grad-CAM) and uncertainty-aware reporting.

**Objectives**
1. Classify leaf disease from an image with a deep CNN using transfer learning.
2. Explain each prediction visually (Grad-CAM).
3. Turn predictions into actionable, farmer-readable advice using an LLM, with safety guardrails.
4. Be honest about uncertainty: hedge when confidence is low and never overstate certainty.
5. Deliver it as a usable multilingual web application (English / Hindi / Punjabi).
6. Measure real-world (field) performance honestly, not only lab performance.

---

## 3. Key results at a glance

| Metric | Value | Source |
| --- | --- | --- |
| Model | EfficientNet-B0 (timm), ImageNet-pretrained | `models/model.py` |
| Classes | 28 (13 crops; disease and healthy classes) | `datasets/train` listing |
| Dataset sizes (pooled, deduplicated) | train **27,673**, val **5,935**, test **5,963** images | `datasets/` |
| **Lab-photo accuracy** (PlantVillage-sourced test split) | **96%** (macro F1 0.95, 5,963 images) | `outputs/predictions/classification_report.txt` |
| **Field-photo accuracy** (PlantDoc-sourced held-out `pd_` images) | **56.9%** (226/397), macro F1 **0.53** | `outputs/predictions_field_pd/` |
| Confident-but-wrong on field photos | 97/397 (**24.4%**) wrong at confidence ≥ 0.60; 60 (15.1%) at ≥ 0.80; 37 (9.3%) at ≥ 0.90 | `HANDOVER.md` §5 |
| Weakest field classes (F1) | Potato early blight 0.07, Tomato mosaic virus 0.17, Tomato leaf mold 0.28, Tomato bacterial spot 0.29 | same |
| Strongest field classes (F1) | Squash powdery mildew 0.95, Strawberry healthy 0.88 | same |
| Backend tests | 67 passing (no network, key or checkpoint needed) | `HANDOVER_FRONTEND.md` §9 |
| Frontend unit tests | 36 passing | same |
| Report latency (Gemini flash-lite) | about 2.5 s per report | `config.yaml` / `HANDOVER.md` |
| Checkpoint size | about 47 MB | `HANDOVER_FRONTEND.md` §11 |

> **The central honest finding:** 96% on lab images vs 56.9% on field images. About 1 in 4 field photos receives a confident, wrong answer that a confidence threshold cannot catch. This drives the whole UI/product design (§11).
>
> **Stale numbers to ignore:** an older "~22% field accuracy" appears in `README.md` and a `config.yaml` comment. It came from an invalid evaluation (the model was scored on 39 PlantDoc classes it cannot emit). The correct figure is **56.9%**. `outputs/predictions_plantdoc/` is invalid.

---

## 4. System architecture

```
 ┌──────────────┐   photo    ┌────────────────────────────── FastAPI backend ──────────────────────────────┐
 │  Next.js web │ ─────────► │ POST /predict                                                                 │
 │  app (React) │            │   preprocessing → EfficientNet-B0 → softmax top-k → Grad-CAM heatmap         │
 │  EN / HI / PA│ ◄───────── │   returns prediction, confidence, top-k, is_low_confidence, heatmap (base64) │
 │              │            │                                                                               │
 │              │ prediction │ POST /report                                                                  │
 │              │ ─────────► │   choose prompt variant (standard / hedged-low-confidence / healthy)          │
 │              │            │   → LLM provider (Gemini | OpenAI | Fake) → JSON → validate (+1 retry) → cache│
 │              │ ◄───────── │   returns structured farmer report                                            │
 │              │ feedback   │ POST /feedback → appended to daily JSONL file (no photo stored)               │
 └──────────────┘            └───────────────────────────────────────────────────────────────────────────────┘
        Training side (offline): data prep → pooled/deduped split → two-stage transfer learning → best.pt
```

**Design choices worth explaining in a report**
- **Single model load.** The model, LLM provider and report cache are created once at startup (FastAPI lifespan) and shared through dependency injection.
- **Separate `/predict` and `/report`.** The frontend shows the diagnosis immediately, then loads the LLM report under a skeleton, so a slow or failed LLM never blocks the diagnosis. If the report fails on the combined `/predict?include_report=true`, the prediction still returns HTTP 200 with the reason in `report_error`.
- **Provider abstraction.** LLM providers implement one base interface. `fake` is the default, so the API and tests run with no API keys.
- **Typed contract.** The backend OpenAPI schema generates TypeScript types for the frontend (`npm run gen:api`), so front and back cannot drift silently.

---

## 5. Technology stack

**ML / data**
- Python, PyTorch 2.x, torchvision, **timm** (EfficientNet-B0), **pytorch-grad-cam**
- scikit-learn (metrics, stratified splitting), pandas, numpy, OpenCV, Pillow, matplotlib, seaborn
- **imagehash (phash)** for perceptual-hash deduplication
- TensorBoard for training logs; Jupyter notebook `notebooks/EDA.ipynb`
- Trained on an NVIDIA GPU (CUDA); the backend selects the device automatically (`device: auto`)

**Backend**
- **FastAPI**, Uvicorn, Pydantic v2 and pydantic-settings, python-multipart, httpx (REST calls to LLMs, with no vendor SDKs), PyYAML, python-dotenv
- Tests: pytest, pytest-asyncio

**LLM**
- Google **Gemini** (`gemini-3.5-flash-lite` currently configured), **OpenAI** (alternative), and a **Fake** provider for tests and offline use

**Frontend**
- **Next.js 16** (App Router), **React 19**, **Tailwind CSS 4**, **shadcn/ui** on Radix, strict TypeScript
- Vitest for unit tests, ESLint, Prettier, `openapi-typescript`
- Fonts: Inter and Manrope (self-hosted at build time), with Noto/system fonts for Devanagari and Gurmukhi
- No TanStack Query, no `next-intl` (own lightweight i18n), no image library

---

## 6. Datasets

Two public datasets were **pooled** so the model sees both lab and field imagery.

| Dataset | Type | Size | Classes | Role |
| --- | --- | --- | --- | --- |
| **PlantVillage** | Lab: single leaf, plain background | 54,305 images | 38 | Bulk of training data. Files prefixed `pv_` |
| **PlantDoc** | Field/real-world: scraped web photos, messy backgrounds | 2,567 images | 39 (annotation format) | Small, realistic set. Files prefixed `pd_` |

- Only the **classes shared** by both datasets were kept, which is why the model has **28 classes** rather than PlantVillage's 38.
- The final train split holds 27,673 images, **1,774 of them from PlantDoc**.
- **Imbalance:** the smallest class has about 150 images and the largest about 3,200 (noted in `data/transforms.py`). Handled with augmentation and an optional `WeightedRandomSampler` (`use_weighted_sampler: true` in config).
- Some PlantDoc photos are web-scraped and oddly coloured (e.g. a purple-dominant grape leaf). This was verified as a source-data quirk, not a preprocessing bug.
- EDA artefacts are in `outputs/eda_figures/` (class distributions, resolution comparison, sample grid, source-ratio breakdown, split distribution).

**The 28 classes (folder names, `Crop___Condition`)**
Apple: Apple scab, Cedar apple rust, healthy · Blueberry: healthy · Cherry (incl. sour): healthy · Corn (maize): Cercospora leaf spot / Gray leaf spot, Common rust, Northern leaf blight · Grape: Black rot, healthy · Peach: healthy · Pepper (bell): Bacterial spot, healthy · Potato: Early blight, Late blight, healthy · Raspberry: healthy · Soybean: healthy · Squash: Powdery mildew · Strawberry: healthy · Tomato: Bacterial spot, Early blight, Late blight, Leaf mold, Septoria leaf spot, Tomato yellow leaf curl virus, Tomato mosaic virus, healthy.

(13 crops: apple, blueberry, cherry, corn, grape, peach, pepper, potato, raspberry, soybean, squash, strawberry, tomato.)

---

## 7. Data pipeline (preprocessing and splitting)

Scripts in `data/`:

1. `prepare_plantdoc.py`: converts PlantDoc's flat files and `_classes.txt` into a class-subfolder layout.
2. **`pool_and_split.py` (current):** pools PlantVillage + PlantDoc shared classes, **perceptual-hash (phash) clusters** near-duplicate images, then does a **stratified 70 / 15 / 15** train/val/test split at the *cluster* level (seed 42), so near-duplicates cannot leak across splits.
3. Earlier, superseded versions are kept for history: `dedup_split.py` (phash dedup, PlantVillage only) and `split_dataset.py` (naive random split).
4. `dataset.py`, `dataloader.py` and `transforms.py` hold the PyTorch `Dataset`, loaders and transforms.

**Why dedup matters:** PlantVillage contains many near-identical photos of the same leaf. A naive random split would put copies in both train and test and inflate accuracy. Deduplicating before splitting gives a more honest test number.

**Critical data gotcha (a real mistake caught during the project):** `datasets/PlantDoc/` is a *source directory*, not a test set. Its images were redistributed into the pooled splits, so evaluating on `datasets/PlantDoc/test` scores the model on its own training data (verified: one file scored 99.99%). The valid field test set is the **397 `pd_`-prefixed images under `datasets/test`**.

**Transforms (`data/transforms.py`)**
- *Train:* RandomResizedCrop(224, scale 0.8–1.0), horizontal flip (p 0.5), vertical flip (p 0.2, since leaves have no fixed "up"), rotation ±20°, ColorJitter (brightness/contrast/saturation 0.2, hue 0.05), ToTensor, ImageNet normalisation.
- *Val/Test:* deterministic. Resize to about 256 (224×1.14), CenterCrop 224, normalise with ImageNet mean/std (0.485, 0.456, 0.406 / 0.229, 0.224, 0.225).
- Consequence: the model only "sees" the **centre crop (224/255 ≈ 88% of the short side)**. The UI reflects this (§10.3).

---

## 8. Model and training

**Architecture:** `CropDiseaseModel` (`models/model.py`), a thin wrapper around `timm.create_model("efficientnet_b0", pretrained=True, num_classes=28)`. EfficientNet-B0 was chosen as a small, accurate, efficient CNN suited to deployment (the code notes ResNet50 / MobileViT as easy swaps for comparison, via one string). Grad-CAM target layer: `backbone.conv_head` (last convolutional layer).

**Two-stage transfer learning** (`main.py`, `engine/trainer.py`, `configs/config.yaml`)

| | Stage 1 | Stage 2 |
| --- | --- | --- |
| What trains | Only the new classifier head (backbone frozen) | Whole network fine-tuned end to end |
| Epochs | 5 | 15 (20 total) |
| Learning rate | 3e-4 | 3e-5 |
| Optimizer / schedule | AdamW, CosineAnnealingLR (T_max = stage epochs) | same |

- Loss: `CrossEntropyLoss`. Batch size 32. Image size 224. Seed 42. Weighted sampler on.
- Checkpointing: `best.pt` is saved only when validation accuracy improves; `last.pt` is saved too. Logs go to TensorBoard (`outputs/logs/`).
- The trainer keeps the same checkpoint/best-accuracy state across the optimizer swap between stages.

**Evaluation** (`evaluate.py`)
- Standalone test-set evaluation producing a classification report, confusion matrix and `misclassified.csv`.
- `--prefix pd_` restricts to held-out field photos: `python evaluate.py --split test --prefix pd_ --output_dir outputs/predictions_field_pd`
- Outputs: `outputs/predictions/` (lab) and `outputs/predictions_field_pd/` (field).

---

## 9. Explainability (Grad-CAM)

- **Grad-CAM** (Gradient-weighted Class Activation Mapping) highlights the regions of the image that most influenced the predicted class, by weighting the last conv layer's feature maps with gradients.
- Two separate implementations exist (deliberate, with different purposes):
  - `utils/gradcam.py`: standalone script utility for offline heatmap generation (`generate_heatmaps.py`, `generate_field_heatmaps.py`).
  - `backend/services/gradcam_service.py`: request-serving version. It reuses the already-loaded model and the already-computed prediction, and runs one extra grad-enabled forward and backward pass per request (inference itself runs under `torch.inference_mode()`).
- The backend returns the overlay as a **base64 image** in `/predict`.
- Offline heatmap galleries: `outputs/heatmaps/{correct,curated,misclassified}` and `outputs/heatmaps_field_plantdoc/`.
- **Caveat shown in the UI:** a heatmap shows where the model looked, not proof that it is right. It also covers only the model's centre crop.

---

## 10. Backend (FastAPI)

### 10.1 Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Liveness check |
| `GET /health` | Readiness: model loaded, device, CUDA availability |
| `GET /meta` | Class list, supported languages, default language, upload limits |
| `POST /predict` | Image → `prediction`, `confidence`, `is_low_confidence`, `top_predictions` (top-3), `heatmap`. Optional `?include_report=true&language=` |
| `POST /report` | Prediction JSON → structured farmer report (`language` = `en`/`hi`/`pa`) |
| `POST /feedback` | `verdict` (yes/no/unsure) + optional `correct_class`, appended to `outputs/feedback/feedback-YYYY-MM-DD.jsonl`. **No photo is received or stored.** |

### 10.2 Layout (`backend/`)
`app.py` (app factory + lifespan) · `core/config.py` (pydantic-settings: `config.yaml` + `.env` + `AGRIVISION_*` env overrides) · `core/logging.py` · `api/{predict,report,feedback,system,deps}.py` · `services/{inference,gradcam_service,preprocessing,report_service,report_prompts,report_cache,feedback_store}.py` · `services/llm/{base,factory,fake,gemini,openai}.py` · `schemas/` · `utils/exceptions.py` · `openapi_export.py`.

### 10.3 Robustness and security features
- **Upload limits:** JPEG, PNG or WebP only, validated on both declared MIME type and decoded format; chunked read capped at 10 MB. Errors: `image_too_large` (413), `unsupported_image_type` (415).
- **Typed errors:** every exception carries an `error_code` and HTTP status; the JSON field is `error`. `ErrorResponse.error` is a closed literal list (`invalid_image`, `image_too_large`, `unsupported_image_type`, `invalid_feedback`, `inference_error`, `report_error`, `report_disabled`, `llm_configuration_error`, `llm_provider_error`, `llm_timeout`, `llm_rate_limited`, `report_parse_error`, `validation_error`, `internal_error`). A test fails if an exception class is missing from the list.
- **CORS:** default allowed origin `http://localhost:3000` only, with no credentials and GET/POST only. Configure with `AGRIVISION_CORS_ORIGINS='["https://app.example"]'`.
- **Secrets:** API keys come from the environment / `.env` only, never from `config.yaml` (which logs a warning if it finds a key). A missing key for the selected provider fails at **startup**, not at first request.
- **Language** is restricted to `en`, `hi`, `pa`; anything else is a 422.
- **Class order** is derived at startup from the folder listing of `datasets/train` (not stored in the checkpoint). A mismatching listing would silently mislabel predictions.

---

## 11. LLM report layer

Turns a prediction into a farmer-readable report. Fields (`ReportSchema`): summary, severity (low / medium / high), symptoms to check, treatment split into **organic** and **chemical** lists, prevention, when to consult an expert, and a confidence caveat. The JSON schema is embedded in the prompt *and* used to validate the output.

**Behaviours**
- **Confidence-aware prompt variants.** Below `confidence_threshold` (0.60) the service switches to a **hedging prompt**: no definitive diagnosis, names the top 2–3 candidates, recommends **no chemical treatment**, asks for a better photo. Three variants: *standard*, *uncertain*, *healthy*. Low-confidence is checked **before** healthy, on purpose: a weak "healthy" is the false negative that costs a crop.
- **Server-stamped flags.** `is_low_confidence` and `possible_alternatives` are set *after* validation, so the LLM cannot mark its own hedged report as confident.
- **Validation + retry.** Output is parsed and validated; one corrective retry on malformed output, then `ReportParseError`. Timeouts, 429s and 5xx are *not* retried.
- **Caching.** In-memory TTL cache (24 h, 512 entries) keyed on (class, confidence bucket of 10, language, top-k signature). The top-k signature matters for correctness because hedged reports name runner-ups. A `ReportCache` protocol allows swapping in Redis.
- **Guardrails in prompts** (`report_prompts.py`, versioned via `PROMPT_VERSION`): no dosages, no brand names, always defer chemical treatment to a local agricultural extension officer, simple language.
- **Providers:** Gemini and OpenAI (REST via httpx), Fake (labelled placeholder text, always English). Config: timeout 30 s, max 1,200 output tokens, temperature 0.3.
- **Known limitation:** guardrails rest on the prompt alone; nothing checks the LLM output for dosages or brand names after generation. A 6-report Hindi/Punjabi spot-check showed no violations, which is a small sample and not proof.

---

## 12. Frontend (Next.js web app)

**Pages (per locale: `/en`, `/hi`, `/pa`)**
- `/[locale]` is the **landing page** (hero, problem, how it works, features, product preview, responsible-AI section, FAQ, CTA). Its percentages and advice are labelled samples; its Grad-CAM images are real model output.
- `/[locale]/diagnose` is the **upload workspace**: choose or drag a photo (camera button on touch devices), photo tips, backend status banner.
- `/[locale]/result` is the **result and report**: photo with Grad-CAM toggle ("Your photo" / "Model's view" / "Model focus"), top-k predictions, the report, a feedback form, a disclaimer and a **printable report** (starts on its own page).

**Request flow:** choosing a photo prepares it immediately in the browser (validate → apply EXIF rotation → resize to 1024 px JPEG at 0.85 → crop the model's view). "Check this leaf" calls `/predict` and navigates to `/result`, which renders at once; `/report` then loads under a skeleton in the current language. Photos are re-encoded in the browser because the backend does not apply EXIF orientation and Pillow cannot read HEIC; a 9.6 MB test photo became about 195 KB.

**Languages:** English, **Hindi**, **Punjabi** via a custom typed dictionary system. `proxy.ts` redirects locale-less paths to the saved or browser language. **Hindi and Punjabi strings are unreviewed drafts**, marked as such in the source, and need native-speaker/agronomy review.

**Visual design:** "Hybrid scientific SaaS × Earth palette" per `AGRIVISION_VISUAL_REDESIGN_SPEC.md`. Palette: Forest `#354B35`, Olive `#77815A`, Terracotta `#C47B55`, Sand `#E8DDC7`, Canvas `#F7F4EC`, Charcoal `#282B25`, Stone `#B9A88B`, Harvest `#D7A84B`, Muted `#6E7168`. Light theme only (readable outdoors), large touch targets, WCAG AA contrast, status never conveyed by colour alone. Before/after redesign screenshots are in `docs/redesign/` (v1, v2, v3) and a sample printed report is `docs/redesign/v3/report-print-sample.pdf`.

**Responsible-AI product rules (the heart of the UX; do not relax)**
1. An "AI suggestion only" notice appears on **every** result, at any confidence.
2. **All top-k predictions are shown**, never just the first.
3. Confidence **never reads 100%**: near-certain values display as `>99%`, because softmax saturates on wrong predictions too.
4. Treatment advice on a confident result sits under **"If your officer confirms this."**
5. **Dosages and brand names are never displayed.**

| | Standard | Uncertain | Healthy |
| --- | --- | --- | --- |
| Headline | "Most likely: X" | "Uncertain result" (no disease named) | "Most likely: Healthy" |
| Urgency | Shown | **Hidden** (a "Low" rating would falsely reassure) | Hidden |
| Chemical list | Shown, plus a fixed "speak to your officer" note | **Never shown**; fixed "do not spray yet" note | No treatment section |

State (photo, prediction, feedback status) lives **in memory only**, with no accounts, no database and no stored photos, which is a privacy-by-design choice.

---

## 13. Testing and verification

| Check | Result (last full run 2026-11-05) |
| --- | --- |
| Backend tests (pytest) | **67 pass**, with no network, API key or checkpoint needed (the Fake provider is used). Files: `test_cors`, `test_error_codes`, `test_feedback`, `test_languages`, `test_low_confidence_flag`, `test_meta`, `test_predict_report_integration`, `test_report_cache`, `test_report_endpoint`, `test_report_service`, `test_upload_limits` |
| Frontend unit tests (vitest) | **36 pass** |
| Lint, Prettier, `next build`, production `npm audit` | Clean |
| Browser suite (Phase 3 flows + every forced failure) | 54 / 54 |
| Browser suite (Phase 4 routing, axe accessibility, keyboard, overflow, tap targets) | 56 / 56 |
| Hindi/Punjabi guardrail spot-check | 6 real Gemini reports: no dosages or brands; uncertain reports left `chemical` empty |

**Honest limits:** the browser suites were throwaway Playwright scripts **not kept in the repo**, so they are a record of one run, not re-runnable tests. Most browser runs used the fake provider or hand-written report text. Drag-and-drop is untested. Tested only on Chromium mobile emulation, **not** on real phones, low-end Android, iPhone HEIC photos or a real screen reader. No load testing, no rate limiting.

---

## 14. Known limitations and risks (use for the "Limitations" chapter)

1. **Field accuracy gap:** 96% (lab) vs 56.9% (field). Roughly 24% of field photos get a confident, wrong, un-hedged report. Raising the confidence threshold does not help, because those predictions are wrong *above* it.
2. Weak classes on field photos: potato early blight (mostly called late blight), tomato mosaic virus, tomato leaf mold, tomato bacterial spot.
3. Only **28 classes / 13 crops**; anything outside them will still be forced into one of the 28 classes (no "unknown / not a leaf" class).
4. Hindi and Punjabi translations are **unreviewed drafts**. LLM spelling can differ from the dictionary terms, and real reports can sound too definite (one Hindi report called a disease "very dangerous").
5. Guardrails against dosages and brand names are prompt-only, with no output filter.
6. Grad-CAM covers only the central crop, and shows model attention, not correctness.
7. No persistence, so there is no history or insights screen (deliberately skipped, because it needs a database and the spec forbids invented data). No bottom navigation, since there is only one destination.
8. Not containerised, deployed or load-tested; CPU latency unmeasured (checks ran on CUDA).
9. Known bug (unfixed): `backend/app.py` calls `get_logger()` at import before `setup_logging`, so the rotating file handler is likely never attached and `outputs/logs/backend.log` is probably never written. Console logging works.
10. `datasets/` and `outputs/` (including the trained checkpoint) are gitignored, so **a fresh clone has neither data nor model**.
11. Feedback storage is one local file per day and suits only a single backend instance.

---

## 15. Future work

- **Fix field accuracy:** temperature-scaling calibration; heavier PlantDoc weighting or more field data; field-condition augmentation (backgrounds, lighting, occlusion); visual review of the misclassified Grad-CAMs; compare other backbones (ResNet50, MobileViT) via the single-string model swap.
- Add an "unknown / not a leaf" detector or out-of-distribution rejection.
- Native-speaker review of Hindi/Punjabi; post-generation output filter for dosages/brands; tune LLM tone.
- **Phase 5:** Dockerfiles (backend and frontend), `docker-compose.yml`, deployment notes. The checkpoint and the class-folder listing must be supplied to the container as read-only mounts. Feedback needs a persistent volume. Add a reverse proxy with a body-size limit, rate limiting, `AGRIVISION_CORS_ORIGINS`, and decide CPU vs GPU.
- Real-device and screen-reader testing; a committed end-to-end test suite; load testing.
- Farmer-facing pilot with extension officers; history/insights once persistence exists; more languages and crops; on-device/offline model.

---

## 16. Repository map

```
main.py                 training entry point (two-stage transfer learning)
evaluate.py             test-set evaluation (--prefix pd_ for field-only)
configs/config.yaml     single source of truth: dataset, training, model, llm, backend
data/                   prepare_plantdoc, pool_and_split (current), dedup_split, split_dataset, dataset, dataloader, transforms
models/model.py         CropDiseaseModel (timm wrapper, freeze/unfreeze, Grad-CAM target layer)
engine/trainer.py       train/eval loops, checkpointing, TensorBoard
utils/                  gradcam.py, generate_heatmaps.py, generate_field_heatmaps.py, eda_generator.py
notebooks/EDA.ipynb     exploratory data analysis
backend/                FastAPI app (see §10)
frontend/               Next.js app (see §12); frontend/lib, components, hooks, state, app
tests/                  67 backend tests
docs/redesign/          before/after UI screenshots and sample printed report PDF
outputs/                (gitignored) checkpoints, logs, plots, predictions, heatmaps, eda_figures, feedback
datasets/               (gitignored) train / val / test, each with 28 class folders
HANDOVER.md             model, data, LLM layer (partly stale; see HANDOVER_FRONTEND.md §10)
HANDOVER_FRONTEND.md    frontend + backend changes, gotchas, verification, Phase 5 plan
AGRIVISION_VISUAL_REDESIGN_SPEC.md   visual design spec
```

---

## 17. How to run

```bash
# --- ML ---
python main.py                                            # train → outputs/checkpoints/{best,last}.pt
python evaluate.py --checkpoint outputs/checkpoints/best.pt                       # lab test split
python evaluate.py --split test --prefix pd_ --output_dir outputs/predictions_field_pd   # field-only

# --- Backend (needs checkpoint + datasets/train folder listing) ---
source .venv/bin/activate
AGRIVISION_LLM_PROVIDER=fake uvicorn backend.app:app --port 8000
#   real LLM: put GEMINI_API_KEY=... and AGRIVISION_LLM_PROVIDER=gemini in backend/.env

# --- Frontend (Node 22+) ---
cd frontend && cp .env.example .env.local     # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm install && npm run dev                    # http://localhost:3000

# --- Tests / checks ---
pytest                                        # backend
npm test; npm run lint; npm run typecheck; npm run build     # frontend
npm run gen:api                               # regenerate API types after backend schema changes
```

---

## 18. Project timeline (from git history)

- **2026-07-24:** model trained (EfficientNet-B0).
- **2026-07-30:** FastAPI backend (inference + Grad-CAM).
- **2026-09-30:** LLM report layer; first field-accuracy measurement (25-image sample, 52%) revealing the lab-vs-field gap.
- **2026-11-02:** full field re-measurement (397 images → 56.9%); backend support for the frontend (limits, `/meta`, `/feedback`, CORS); frontend scaffold.
- **2026-11-05:** upload and result screens, report layout and feedback, Hindi/Punjabi drafts, accessibility pass, frontend handover.
- **2026-11-06:** visual redesign (earth palette, landing page, diagnosis workspace, results/report redesign, printable report).
- **Next:** Phase 5, containerisation and deployment.

Frontend phases: 0 API contract review · 1 backend support + scaffold + typed client · 2 upload + `/predict` + basic result · 3 report, uncertain layout, feedback, errors · 4 Hindi/Punjabi, accessibility, responsive polish · 5 Docker/deployment *(not started)*.

---

## 19. Suggested report structure and what to emphasise

A typical college project report can be built from this file as:

1. Abstract · 2. Introduction and problem statement (§2) · 3. Objectives (§2) · 4. Literature survey *(not in the repo; see §20)* · 5. Dataset description and EDA (§6) · 6. Methodology: preprocessing, augmentation, deduplication and splitting (§7) · 7. Model and training (§8) · 8. Explainability (§9) · 9. System design: architecture, API, LLM layer (§4, §10, §11) · 10. Frontend and UX design (§12) · 11. Results and evaluation: lab vs field, confusion matrices, per-class tables (§3) · 12. Testing (§13) · 13. Limitations (§14) · 14. Conclusion and future scope (§15) · Appendices: API reference, config, repo map, screenshots.

**Strong talking points for viva/presentation**
- *Why 96% vs 56.9%?* Domain shift: training is dominated by clean lab images; field photos have clutter and varied lighting. We measured it honestly, after catching an invalid evaluation that gave 22%.
- *Why dedup before splitting?* To avoid train/test leakage from near-duplicate PlantVillage photos.
- *Why two-stage transfer learning?* Train the new head first so random head weights don't wreck pretrained features, then fine-tune everything at a 10× lower learning rate.
- *Why Grad-CAM?* Trust and debuggability; it shows what the model looked at.
- *Why does the UI hedge?* A confident wrong diagnosis of a crop disease is worse than none; about 1 in 4 field photos is confidently wrong, and a threshold can't catch that.
- *Why an LLM?* The classifier outputs a label; the LLM turns it into multilingual, structured advice, constrained by a schema, validated, retried, cached and guarded.
- *Why no dosages or brands?* Safety and liability: chemical use must be confirmed by a local extension officer.
- *Why is the LLM never able to fail a diagnosis?* `/predict` and `/report` are separate, and `report_error` is non-fatal.

---

## 20. Instructions for an LLM using this file

- Treat this file as the **ground truth**. Do not invent metrics, datasets, accuracy numbers, user studies, deployment status or team members. If something is not here (e.g. literature survey citations, team names, guide name, university, formal timelines, hardware specs, training curves or exact best epoch), **ask the user or leave a clearly marked placeholder** like `[TO BE FILLED]`.
- **Never claim the system is production-ready or farmer-validated.** Always state the lab 96% vs field 56.9% distinction, never quote 96% alone.
- Literature survey: you may cite well-known public works (e.g. Mohanty et al. 2016 on PlantVillage; PlantDoc by Singh et al. 2020; EfficientNet by Tan & Le 2019; Grad-CAM by Selvaraju et al. 2017) but tell the user to verify each reference before submitting.
- Use the exact terminology above: "EfficientNet-B0", "Grad-CAM", "two-stage transfer learning", "phash deduplication", "confidence threshold 0.60".
- Keep the "AI suggestion only / not authoritative" framing in any user-facing or conclusion text.
- When asked for diagrams, use §4 (architecture), §8 (training stages) and the request flow in §12.
- Tailor length and formality to the requested deliverable (e.g. 2-page synopsis vs 60-page report vs 10-slide deck).

### Items the project owner should fill in before generating reports
- Project title as registered, team members and roles, guide/mentor, institution, department, academic year
- Training hardware (GPU model), best epoch and training/validation curves (TensorBoard logs are in `outputs/logs/`)
- Literature-survey references and any plagiarism-check requirements
- Screenshots to include (available in `docs/redesign/`)
