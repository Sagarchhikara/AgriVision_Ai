# AgriVision_Ai — Handover

Last updated 2026-11-02. Written so someone picking this up can continue without re-deriving context from the code.

## 1. What this project is

Crop disease diagnosis from leaf photos: an EfficientNet-B0 classifier, Grad-CAM explainability, a FastAPI backend, and an LLM layer that turns a prediction into a farmer-readable report.

## 2. Current state

**Done:** training pipeline, Grad-CAM, FastAPI inference backend, LLM report layer (38 passing tests).
**Not done:** frontend / web deployment, and the field-accuracy problem below.
**The open problem:** the model is good on lab photos and mediocre-to-unreliable on real field photos.

- Trained model: EfficientNet-B0 (`timm`), 28 classes, two-stage transfer learning (frozen head → full fine-tune).
- **Lab photos (PlantVillage-sourced test split): 96% accuracy** (`outputs/predictions/classification_report.txt`).
- **Real field photos (PlantDoc-sourced, held out): 56.9%** (226/397) on the full held-out `pd_` set — see §5 for why this replaces the old 22% figure and why it is still not deployable.

## 3. Repo layout

```
main.py                    # training entry point (two-stage transfer learning)
evaluate.py                # standalone test-set evaluation (--prefix pd_ restricts to held-out field photos)
configs/config.yaml        # single source of truth: dataset, training, model, backend, llm

data/
  prepare_plantdoc.py      # PlantDoc flat files + _classes.txt -> class-subfolder layout
  pool_and_split.py        # CURRENT: pools PlantVillage+PlantDoc shared classes, phash-dedups, 70/15/15
  dedup_split.py           # earlier: phash dedup, PlantVillage only (superseded)
  split_dataset.py         # earliest: naive random split (superseded)
  dataset.py / dataloader.py / transforms.py

models/model.py            # CropDiseaseModel: timm wrapper, freeze/unfreeze, get_target_layer for Grad-CAM
engine/trainer.py          # train/eval loops, checkpointing, TensorBoard

utils/                     # gradcam.py, generate_heatmaps.py, generate_field_heatmaps.py, eda_generator.py

backend/
  app.py                   # app factory; lifespan loads model + LLM provider + report cache once
  core/config.py           # pydantic-settings; loads config.yaml + .env + AGRIVISION_* env overrides
  api/predict.py           # POST /predict  (+ ?include_report=true)
  api/report.py            # POST /report
  api/system.py            # GET / and /health
  api/deps.py              # DI accessors for the services on app.state
  services/inference.py    # loads checkpoint once, runs predictions
  services/gradcam_service.py
  services/preprocessing.py
  services/report_service.py   # variant selection, JSON parse + one retry, cache, server-stamped flags
  services/report_prompts.py   # versioned prompts (PROMPT_VERSION) + guardrails
  services/report_cache.py     # ReportCache protocol, InMemoryTTLCache, NullCache
  services/llm/            # base, fake, gemini, openai, factory
  schemas/                 # prediction.py, report.py, system.py
  utils/exceptions.py      # typed errors, each carrying error_code + status_code

tests/                     # 38 tests, all against FakeProvider (no network, no key, no checkpoint)
datasets/                  # gitignored
outputs/                   # gitignored
```

`datasets/` and `outputs/` — including the trained checkpoint `outputs/checkpoints/best.pt` — are gitignored. **A fresh clone has neither the data nor the model.**

## 4. Data pipeline

`prepare_plantdoc.py` runs first (converts PlantDoc's annotation format to class subfolders), then `pool_and_split.py` produces the `datasets/train|val|test` the model was actually trained on: shared classes only, phash-deduplicated across the combined pool, stratified 70/15/15. That pooling is why the model has 28 classes rather than PlantVillage's 38.

Files are prefixed by source: `pv_` (PlantVillage) and `pd_` (PlantDoc). The train split holds 27,673 images, 1,774 of them `pd_`.

**`datasets/PlantDoc/` is a source directory, not a test set.** Its images were redistributed into the pooled splits, so evaluating against `datasets/PlantDoc/test` scores the model on its own training data. Verified: `datasets/PlantDoc/test/Apple___Apple_scab/apples_apple-scab_01_zoom...jpg` also exists as `datasets/train/Apple___Apple_scab/pd_apples_apple-scab_01_zoom...jpg`, and the model scores it 99.99%.

**The valid held-out field set is the 397 `pd_`-prefixed images under `datasets/test`.**

## 5. Field accuracy — corrected

An earlier version of this document reported 22% on PlantDoc. That number came from `outputs/predictions_plantdoc/classification_report.txt`, which evaluated against raw `datasets/PlantDoc` with its 39 classes — most of which a 28-class model cannot emit, so it was scored as wrong on classes it was never trained to predict. Treat that file as invalid.

Measured properly on held-out `pd_` images in `datasets/test` (25-image sample, 2026-09-30):

- **13/25 correct (52%)**, versus 96% on lab photos.
- **8/25 fell below the 0.60 report threshold** and correctly produced non-definitive reports.
- **6/25 were wrong at 78–94% confidence.** This is the dangerous failure mode: the confidence threshold catches uncertainty, not overconfidence, so these produce confident, wrong advice.

**Full re-measurement (2026-11-02, all 397 held-out `pd_` images):** `python evaluate.py --split test --prefix pd_ --output_dir outputs/predictions_field_pd`

- **Accuracy 56.9%** (226/397); macro F1 0.53. The 25-image sample (52%) was a fair estimate.
- **171 wrong; 97 of them (24.4% of all images) at confidence >= 0.60**, 60 (15.1%) at >= 0.80, 37 (9.3%) at >= 0.90. Roughly 1 in 4 field photos gets a confident, wrong, non-hedged report.
- Weakest classes: Potato early blight (F1 0.07, mostly called late blight), Tomato mosaic virus (0.17), Tomato leaf mold (0.28), Tomato bacterial spot (0.29). Strong: Squash powdery mildew (0.95), Strawberry healthy (0.88).
- Outputs (report, confusion matrix, `misclassified.csv` sorted by confidence) are in `outputs/predictions_field_pd/`. `outputs/predictions_plantdoc/` remains invalid.

Also worth knowing: some PlantDoc images are web-scraped and oddly colored (one grape-leaf photo is purple-dominant, R=151/G=125/B=178). Verified this is the source files, not a channel-order bug in preprocessing.

## 6. LLM report layer

Turns a prediction into a report: summary, severity, symptoms to check, organic/chemical treatment, prevention, when to consult an expert, confidence caveat.

- **Providers** (`backend/services/llm/`): `gemini`, `openai`, and `fake`. Called over REST with `httpx` — no vendor SDKs. `fake` is the committed default so the API runs with no keys; it returns clearly-labelled placeholder text.
- **Confidence-aware.** Below `llm.confidence_threshold` (0.60) the service switches to a hedging prompt that refuses a definitive diagnosis, names the top-2/3 candidates, recommends no chemical treatment, and asks for a better photo. Low confidence is checked *before* the healthy-class case on purpose — a weak "this plant is healthy" is the false negative that costs a crop.
- **Server-stamped fields.** `is_low_confidence` and `possible_alternatives` are set after validation, so the model can't mark its own hedged report as confident.
- **Validation + retry.** Output is parsed and validated against `ReportSchema`; one corrective retry on malformed output, then `ReportParseError`. Provider errors (timeout, 429, 5xx) are not retried.
- **Caching.** Keyed on `(class, confidence bucket, language, top-k signature)`. The top-k signature matters for correctness, not just cost: hedged reports name their runner-up candidates. Swap `InMemoryTTLCache` for Redis by implementing the `ReportCache` protocol.
- **Prompts** live in `report_prompts.py`, versioned via `PROMPT_VERSION` (returned with every report). Guardrails: no dosages, no brand names, always defer chemical treatment to a local agricultural extension officer, simple language. Verified holding on real Gemini output.
- **Language** parameter defaults to English; `LANGUAGE_NAMES` already lists Hindi and Punjabi, so adding them is a config change, not code.

### Gemini setup

API keys are read from the environment only — never from `config.yaml`, which ignores an `llm.api_key` key and logs a warning if it finds one. `backend/core/config.py` loads `.env` from the repo root and from `backend/`; a real exported variable takes precedence.

The key currently lives in `backend/.env` (gitignored via the `*.env` rule):

```
GEMINI_API_KEY=...
AGRIVISION_LLM_PROVIDER=gemini
```

**Model note:** `gemini-2.0-flash` is retired (the API returns 404 saying so). `gemini-3.8-flash` and `gemini-3.7-flash` exist on this key but were returning 503 "high demand". Config is set to **`gemini-3.5-flash-lite`**, verified working at ~2.5s per report. Move up to `gemini-3.8-flash` when capacity allows.

## 7. How to run things

```bash
# Train (writes outputs/checkpoints/{best,last}.pt, TensorBoard logs to outputs/logs/)
python main.py

# Evaluate on the pooled test split
python evaluate.py --checkpoint outputs/checkpoints/best.pt

# Backend
uvicorn backend.app:app --host 0.0.0.0 --port 8000

# Tests (no network, no API key, no checkpoint required)
pytest
```

API: `GET /` · `GET /health` · `POST /predict` (add `?include_report=true`, optional `&language=`) · `POST /report`. Curl examples are in the README.

If report generation fails on `/predict?include_report=true`, the prediction still returns 200 with the reason in `report_error` — the LLM layer is never allowed to fail a diagnosis.

## 8. Likely next steps

1. ~~Re-measure field accuracy~~ — done, see §5. Delete the invalid `outputs/predictions_plantdoc/`.
2. **Attack the confident-wrong cases.** Raising the confidence threshold does not help — those predictions are wrong *above* it. Options: calibration (temperature scaling), heavier PlantDoc weighting during training, or field-condition augmentation (backgrounds, lighting, occlusion). `outputs/heatmaps_field_plantdoc/misclassified/` has Grad-CAM overlays worth a visual pass first.
3. Frontend / web deployment — nothing built yet.
4. Backend has not been load-tested, containerized, or deployed.

## 9. Gotchas

- **`utils/gradcam.py` and `backend/services/gradcam_service.py` are separate implementations** with different preprocessing. Changing one does not affect the other.
- **Class ordering is re-derived at startup** from `datasets/train`'s folder listing (`backend/services/inference.py: load_class_names`), not stored in the checkpoint. If you retrain with a different class set, the serving machine's `datasets/train` must match, or predictions are silently mislabeled.
- **Pre-existing logging bug (unfixed):** `backend/app.py` calls `get_logger()` at module import, which marks logging configured before `create_app()` calls `setup_logging(level, log_file)`. That path early-returns, so the rotating file handler is never attached and `outputs/logs/backend.log` is likely never written. Console logging works.
- **Git history is mostly unannotated `auto: update <timestamp>` commits** from an autosave process. Don't rely on commit messages for context.
