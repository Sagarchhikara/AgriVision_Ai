/**
 * Display names for the model's classes.
 *
 * Raw class names are dataset folder names ("Corn_(maize)___Common_rust_"), so
 * every known class gets a translated crop and condition in each dictionary.
 * Anything not listed (e.g. after a retrain adds a class) falls back to a
 * cleaned-up version of the raw name rather than failing.
 */

import type { Dictionary } from "@/lib/i18n/dictionaries/en";

export const KNOWN_CLASSES = [
  "Apple___Apple_scab",
  "Apple___Cedar_apple_rust",
  "Apple___healthy",
  "Blueberry___healthy",
  "Cherry_(including_sour)___healthy",
  "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
  "Corn_(maize)___Common_rust_",
  "Corn_(maize)___Northern_Leaf_Blight",
  "Grape___Black_rot",
  "Grape___healthy",
  "Peach___healthy",
  "Pepper,_bell___Bacterial_spot",
  "Pepper,_bell___healthy",
  "Potato___Early_blight",
  "Potato___healthy",
  "Potato___Late_blight",
  "Raspberry___healthy",
  "Soybean___healthy",
  "Squash___Powdery_mildew",
  "Strawberry___healthy",
  "Tomato___Bacterial_spot",
  "Tomato___Early_blight",
  "Tomato___healthy",
  "Tomato___Late_blight",
  "Tomato___Leaf_Mold",
  "Tomato___Septoria_leaf_spot",
  "Tomato___Tomato_mosaic_virus",
  "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
] as const;

export type KnownClass = (typeof KNOWN_CLASSES)[number];

export interface ClassText {
  crop: string;
  condition: string;
}

export interface ClassLabel extends ClassText {
  healthy: boolean;
}

const SEPARATOR = "___";

function isKnownClass(className: string): className is KnownClass {
  return (KNOWN_CLASSES as readonly string[]).includes(className);
}

function humanize(part: string): string {
  return part.replace(/_/g, " ").replace(/\s+/g, " ").trim();
}

export function classLabel(className: string, t: Dictionary): ClassLabel {
  const healthy = className.toLowerCase().endsWith(`${SEPARATOR}healthy`);
  if (isKnownClass(className)) {
    return { ...t.classes[className], healthy };
  }

  const separatorIndex = className.indexOf(SEPARATOR);
  if (separatorIndex === -1) {
    return { crop: "", condition: humanize(className), healthy };
  }
  return {
    crop: humanize(className.slice(0, separatorIndex)),
    condition: healthy
      ? t.result.healthyCondition
      : humanize(className.slice(separatorIndex + SEPARATOR.length)),
    healthy,
  };
}
