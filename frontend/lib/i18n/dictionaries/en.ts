/**
 * English UI strings: the reference dictionary. Every other language is typed
 * as `Dictionary`, so a key missing from a translation is a compile error.
 *
 * Writing rules for every language: short sentences, everyday words, no
 * technical terms. Never phrase a result as a definite diagnosis.
 */

import type { ClassText, KnownClass } from "@/lib/classes";

const classes: Record<KnownClass, ClassText> = {
  Apple___Apple_scab: { crop: "Apple", condition: "Apple scab" },
  Apple___Cedar_apple_rust: { crop: "Apple", condition: "Cedar apple rust" },
  Apple___healthy: { crop: "Apple", condition: "Healthy" },
  Blueberry___healthy: { crop: "Blueberry", condition: "Healthy" },
  "Cherry_(including_sour)___healthy": { crop: "Cherry", condition: "Healthy" },
  "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {
    crop: "Maize (corn)",
    condition: "Grey leaf spot",
  },
  "Corn_(maize)___Common_rust_": { crop: "Maize (corn)", condition: "Common rust" },
  "Corn_(maize)___Northern_Leaf_Blight": {
    crop: "Maize (corn)",
    condition: "Northern leaf blight",
  },
  Grape___Black_rot: { crop: "Grape", condition: "Black rot" },
  Grape___healthy: { crop: "Grape", condition: "Healthy" },
  Peach___healthy: { crop: "Peach", condition: "Healthy" },
  "Pepper,_bell___Bacterial_spot": { crop: "Bell pepper (capsicum)", condition: "Bacterial spot" },
  "Pepper,_bell___healthy": { crop: "Bell pepper (capsicum)", condition: "Healthy" },
  Potato___Early_blight: { crop: "Potato", condition: "Early blight" },
  Potato___healthy: { crop: "Potato", condition: "Healthy" },
  Potato___Late_blight: { crop: "Potato", condition: "Late blight" },
  Raspberry___healthy: { crop: "Raspberry", condition: "Healthy" },
  Soybean___healthy: { crop: "Soybean", condition: "Healthy" },
  Squash___Powdery_mildew: { crop: "Squash", condition: "Powdery mildew" },
  Strawberry___healthy: { crop: "Strawberry", condition: "Healthy" },
  Tomato___Bacterial_spot: { crop: "Tomato", condition: "Bacterial spot" },
  Tomato___Early_blight: { crop: "Tomato", condition: "Early blight" },
  Tomato___healthy: { crop: "Tomato", condition: "Healthy" },
  Tomato___Late_blight: { crop: "Tomato", condition: "Late blight" },
  Tomato___Leaf_Mold: { crop: "Tomato", condition: "Leaf mould" },
  Tomato___Septoria_leaf_spot: { crop: "Tomato", condition: "Septoria leaf spot" },
  Tomato___Tomato_mosaic_virus: { crop: "Tomato", condition: "Mosaic virus" },
  Tomato___Tomato_Yellow_Leaf_Curl_Virus: { crop: "Tomato", condition: "Yellow leaf curl virus" },
};

export const en = {
  app: {
    name: "AgriVision",
    homeLink: "AgriVision home",
  },
  upload: {
    title: "Check a crop leaf",
    intro: "Take a clear photo of one affected leaf. We will suggest what might be wrong.",
    takePhoto: "Take a photo",
    choosePhoto: "Choose a photo",
    dropHint: "or drag a photo here",
    dropActive: "Drop the photo here",
    changePhoto: "Use a different photo",
    previewAlt: "Your leaf photo",
    analyze: "Check this leaf",
    preparing: "Preparing your photo…",
    analyzing: "Checking the leaf. This can take a few seconds…",
  },
  tips: {
    title: "For the best result",
    singleLeaf: "One leaf only",
    closeUp: "Close up, leaf fills the photo",
    daylight: "Good daylight, no harsh shadow",
    plainBackground: "Plain background",
    inFocus: "Sharp, not blurry",
    centered: "Leaf in the middle",
  },
  disclaimer: {
    title: "AI suggestion only",
    body: "This is not a diagnosis. Confirm with your local agricultural extension officer before treating your crop.",
  },
  result: {
    pageTitle: "Result",
    likelyEyebrow: "Most likely",
    uncertainTitle: "Uncertain result",
    uncertainBody:
      "The photo did not give a clear answer. The model could not tell these possibilities apart.",
    betterPhotoTitle: "Please try a clearer photo",
    betterPhotoBody: "Follow the photo tips: one leaf, close up, in daylight, in focus.",
    confidenceLine: "Model confidence:",
    canBeWrong:
      "The model can be wrong, even when it seems sure, especially on photos taken in the field.",
    healthyCondition: "Healthy",
    photoHeading: "Your photo",
    showPhoto: "Photo",
    showFocus: "Model focus",
    focusExplanation: "The highlighted area is what the model focused on.",
    photoAlt: "The part of your photo the model checked",
    focusAlt: "Your photo with the areas the model focused on highlighted",
    centreNote: "Only the centre of your photo is checked, so keep the leaf in the middle.",
    possibleMatches: "Possible matches",
    possibleMatchesNote: "Percentages show how sure the model is, not how sick the plant is.",
    analyzeAnother: "Check another photo",
    tryAnotherPhoto: "Take a clearer photo",
    emptyTitle: "No photo checked yet",
    emptyBody: "Take or choose a photo of a leaf to get a suggestion.",
    emptyAction: "Check a leaf",
  },
  errors: {
    tryAgain: "Try again",
    network: {
      title: "No connection",
      body: "We could not reach AgriVision. Check your internet connection and try again.",
    },
    timeout: {
      title: "This is taking too long",
      body: "The connection may be slow. Please try again.",
    },
    serviceUnavailable: {
      title: "Service not available",
      body: "AgriVision is not available right now. Please try again in a few minutes.",
    },
    imageTooLarge: {
      title: "Photo is too large",
      body: "Please choose a smaller photo, or take a new one with your camera.",
    },
    imageType: {
      title: "This file cannot be used",
      body: "Please choose a photo (JPEG, PNG or WebP).",
    },
    imageUnreadable: {
      title: "We could not open this photo",
      body: "The file may be damaged or in an unusual format. Please take a new photo.",
    },
    analysisFailed: {
      title: "We could not check this photo",
      body: "Something went wrong on our side. Please try again.",
    },
    reportUnavailable: {
      title: "Advice is not available right now",
      body: "The result above is still shown. You can try loading the advice again.",
    },
    busy: {
      title: "Too many requests",
      body: "Please wait a minute and try again.",
    },
    feedbackRejected: {
      title: "We could not save your answer",
      body: "Please try again.",
    },
    unexpected: {
      title: "Something went wrong",
      body: "Please try again.",
    },
  },
  classes,
};

export type Dictionary = typeof en;
