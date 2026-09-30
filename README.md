# Crop Disease Diagnosis using Explainable AI

## Objective

Classify crop diseases from leaf images using deep learning, explain the prediction
with Grad-CAM, and turn it into advice a farmer can act on.

## Status

- **Done** — EfficientNet-B0 classifier (28 classes), Grad-CAM explainability, FastAPI
  inference backend, LLM report layer.
- **In progress** — field accuracy. The model scores ~96% on lab photos (PlantVillage)
  but only ~22% on real field photos (PlantDoc). See `HANDOVER.md`.
- **Future work** — frontend / web deployment, Hindi and Punjabi report languages.

## API

Run the backend:

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Liveness check |
| `GET /health` | Readiness: model loaded, device, CUDA availability |
| `POST /predict` | Leaf image → prediction, top-K, Grad-CAM heatmap |
| `POST /report` | Prediction → farmer-friendly report |

### Diagnose an image

```bash
curl -X POST http://localhost:8000/predict \
  -F 'image=@datasets/test/Tomato___Late_blight/example.jpg'
```

### Diagnose and get the report in one call

```bash
curl -X POST 'http://localhost:8000/predict?include_report=true' \
  -F 'image=@datasets/test/Tomato___Late_blight/example.jpg'
```

If report generation fails, the prediction is still returned, with the reason in
`report_error`. Add `&language=hi` to request another language.

### Generate a report from an existing prediction

```bash
curl -X POST http://localhost:8000/report \
  -H 'Content-Type: application/json' \
  -d '{
    "predicted_class": "Tomato___Late_blight",
    "confidence": 0.9821,
    "top_k": [
      {"class_name": "Tomato___Late_blight", "confidence": 0.9821},
      {"class_name": "Tomato___Early_blight", "confidence": 0.0112}
    ]
  }'
```

Below the configured confidence threshold the report is deliberately **not** a
diagnosis: `is_low_confidence` is set, `possible_alternatives` lists the other
candidates, and the text asks for a better photo instead of naming a disease. This is
intentional — the classifier is unreliable on real field photos, and confident-sounding
advice on a weak prediction is worse than no advice.

## LLM configuration

Settings live under `llm:` in `configs/config.yaml`; any of them can be overridden with
an `AGRIVISION_LLM_*` environment variable.

**API keys are read from the environment only, never from the YAML.**

Put them in a `.env` file (gitignored, loaded automatically from either the repo root
or `backend/`):

```
GEMINI_API_KEY=your-key-here
AGRIVISION_LLM_PROVIDER=gemini
```

Or export them in the shell, which takes precedence over the file:

```bash
export GEMINI_API_KEY=...                 # or OPENAI_API_KEY for the openai provider
export AGRIVISION_LLM_PROVIDER=gemini     # fake (default) | gemini | openai
uvicorn backend.app:app --port 8000
```

The default provider is `fake`, which returns clearly-labelled placeholder text so the
API runs with no keys at all. Selecting `gemini` or `openai` without the matching key
fails at startup rather than on the first request.

## Tests

```bash
pytest
```

The suite runs entirely against the fake provider — no network, no API keys, and no
trained checkpoint required.
