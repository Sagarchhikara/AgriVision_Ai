"""
backend/services/report_prompts.py

Every prompt string the report layer sends to an LLM, versioned in one place.

Design notes
------------
- PROMPT_VERSION is returned with each report. When prompt wording changes,
  bump it -- otherwise a cached or logged report gives no way to tell which
  wording produced it, which makes prompt tuning unfalsifiable.
- Three variants exist because the right answer differs in kind, not just in
  wording: a confident diagnosis, a deliberately non-committal one, and a
  healthy-plant confirmation. Selecting the variant is the service's job; this
  module only knows how to phrase each.
- The output contract listed here covers only the LLM-owned fields.
  `is_low_confidence` and `possible_alternatives` are stamped by the server
  afterwards, so the model is never in a position to declare its own
  low-confidence report confident.
- Guardrails (no dosages, no brand names, defer to an extension officer) live
  in the system prompt so they apply to all three variants and can't drift
  apart between them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

DEFAULT_LANGUAGE = "en"
PROMPT_VERSION = "v1"

# Only languages listed here get an explicit instruction; anything else is
# passed through by code, so adding Hindi/Punjabi is a one-line change.
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "pa": "Punjabi",
}


class PromptVariant(str, Enum):
    """Which kind of report to ask for."""

    STANDARD = "standard"
    LOW_CONFIDENCE = "low_confidence"
    HEALTHY = "healthy"


SYSTEM_PROMPT = """\
You are an agricultural advisor helping smallholder farmers understand a crop \
disease diagnosis made by an image classification model. You write for farmers, \
not agronomists.

How to write:
- Use simple, direct language and short sentences. Assume no formal training in \
plant pathology. Avoid technical terms; when one is unavoidable, explain it in \
plain words.
- Be practical. Prefer actions a farmer can take with tools and materials they \
are likely to already have.
- Be honest about uncertainty. Never present a guess as a fact.

Hard rules you must never break:
- NEVER state chemical dosages, concentrations, mixing ratios, or application rates.
- NEVER name commercial or brand-name products. Refer only to general classes of \
active ingredient (for example "a copper-based protectant spray").
- ALWAYS direct the farmer to their local agricultural extension officer before \
applying any chemical treatment, and whenever the situation is severe or unclear.
- NEVER invent facts about a disease you are unsure of. If the evidence is thin, \
say so in the report instead of filling the gap.

Output format:
- Respond with a SINGLE valid JSON object and nothing else.
- No markdown code fences, no commentary before or after the JSON.
- Use these keys exactly:
  - "disease_name": string, human-readable disease name
  - "crop": string, human-readable crop name
  - "summary": string, plain-language explanation of what is affecting the plant
  - "severity": one of "low", "medium", "high"
  - "severity_reason": string, one short sentence justifying that severity
  - "symptoms_to_check": array of strings, signs the farmer can verify themselves
  - "treatment": object with "organic" and "chemical", each an array of strings
  - "prevention": array of strings, practices that reduce recurrence
  - "when_to_consult_expert": string
  - "confidence_note": string, an honest caveat about how certain this is
"""


@dataclass(frozen=True)
class ParsedClass:
    """A model class name split into its human-readable parts."""

    crop: str
    disease: str
    is_healthy: bool


def parse_class_name(class_name: str) -> ParsedClass:
    """
    Split a dataset class name into crop and disease.

    The dataset's folder convention is `Crop___Disease` with underscores for
    spaces, e.g. "Tomato___Late_blight", "Pepper,_bell___Bacterial_spot",
    "Corn_(maize)___Northern_Leaf_Blight", "Apple___healthy". Splitting on the
    triple underscore handles the crop names that themselves contain commas
    or parentheses.
    """
    crop_part, _, disease_part = class_name.partition("___")
    if not disease_part:
        # No separator: treat the whole string as the disease, crop unknown.
        crop_part, disease_part = "", class_name

    crop = crop_part.replace("_", " ").strip()
    disease = disease_part.replace("_", " ").strip()
    return ParsedClass(crop=crop, disease=disease, is_healthy=disease_part.lower() == "healthy")


def _language_instruction(language: str) -> str:
    name = LANGUAGE_NAMES.get(language.lower(), language)
    return (
        f"Write every string value in the JSON in {name}. "
        f"Keep the JSON keys themselves in English, exactly as specified."
    )


def _format_candidates(top_k: list[tuple[str, float]]) -> str:
    """Render the model's ranked guesses as readable lines for the prompt."""
    lines = []
    for class_name, confidence in top_k:
        parsed = parse_class_name(class_name)
        label = f"{parsed.crop} - {parsed.disease}" if parsed.crop else parsed.disease
        lines.append(f"  - {label} ({confidence * 100:.1f}% confidence)")
    return "\n".join(lines)


def build_user_prompt(
    variant: PromptVariant,
    predicted_class: str,
    confidence: float,
    top_k: list[tuple[str, float]],
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """
    Build the user-turn prompt for one report.

    Args:
        variant: which kind of report to request.
        predicted_class: the model's top-1 class, in `Crop___Disease` form.
        confidence: top-1 softmax confidence, 0-1.
        top_k: ranked (class_name, confidence) pairs, highest first.
        language: output language code; only affects the string values.
    """
    parsed = parse_class_name(predicted_class)
    candidates = _format_candidates(top_k)
    language_line = _language_instruction(language)

    if variant is PromptVariant.HEALTHY:
        body = f"""\
An image classification model examined a photo of a {parsed.crop} leaf and found \
no disease. It is {confidence * 100:.1f}% confident the plant is healthy.

The model's ranked guesses were:
{candidates}

Write a short report confirming the plant appears healthy. Do not invent a disease \
and do not recommend any treatment for a disease the plant does not have.
- "disease_name": use "None detected" (translated where appropriate).
- "severity": "low".
- "symptoms_to_check": early warning signs of common {parsed.crop} diseases the \
farmer should watch for from now on.
- "treatment": leave "organic" and "chemical" as empty arrays -- there is nothing \
to treat.
- "prevention": practical routine care that keeps this crop healthy.
- "confidence_note": remind the farmer that this is based on a single photo of one \
leaf, so it does not guarantee the whole field is healthy.

{language_line}"""

    elif variant is PromptVariant.LOW_CONFIDENCE:
        body = f"""\
An image classification model examined a photo of a crop leaf, but it is NOT \
reliable here. Its best guess was "{parsed.crop} - {parsed.disease}" at only \
{confidence * 100:.1f}% confidence.

Its ranked guesses were:
{candidates}

This model is known to perform poorly on real photos taken in the field, so at this \
confidence level the guess above is likely to be wrong.

You must NOT give a definitive diagnosis. Instead:
- "disease_name": make it explicit this is unconfirmed, e.g. "Unconfirmed - possibly \
{parsed.disease}".
- "summary": explain that the photo could not be identified reliably, and briefly \
describe what the top candidates above would each look like, so the farmer can \
compare against their own plant.
- "severity": base this on the uncertainty, not on the guessed disease. Do not alarm \
the farmer about a disease that may not be present.
- "symptoms_to_check": the distinguishing signs that would tell these candidates \
apart by eye.
- "treatment": suggest only safe, general steps that do no harm if the diagnosis is \
wrong (for example isolating affected leaves). Do not recommend a chemical treatment \
for an unconfirmed disease -- leave "chemical" empty and explain why in \
"when_to_consult_expert".
- "confidence_note": state plainly that the model was not confident, and ask the \
farmer to retake the photo: one single leaf, filling the frame, in good daylight, \
against a plain background such as a sheet of paper or bare soil.

{language_line}"""

    else:
        body = f"""\
An image classification model examined a photo of a crop leaf and identified \
"{parsed.crop} - {parsed.disease}" with {confidence * 100:.1f}% confidence.

Its ranked guesses were:
{candidates}

Write a farmer-facing report for this diagnosis. Base "severity" on how fast this \
disease spreads and how much of the crop it can destroy if untreated. In \
"confidence_note", tell the farmer to confirm the symptoms listed above on their own \
plant before acting, since the diagnosis comes from a single photo.

{language_line}"""

    return body


def build_retry_suffix(error: str) -> str:
    """
    Appended to the prompt on the single retry after unparseable output.

    Quotes the actual validation error so the model gets a specific correction
    rather than a repeat of the original instruction it just failed to follow.
    """
    return (
        f"\n\nYour previous response could not be parsed: {error}\n"
        f"Respond again with ONLY a single valid JSON object using the exact keys "
        f"specified. No markdown code fences, no text before or after the JSON."
    )
