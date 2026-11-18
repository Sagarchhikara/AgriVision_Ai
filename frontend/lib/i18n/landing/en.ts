/**
 * Landing page strings. Kept apart from the app dictionary because that one is
 * sent to the browser on every screen, and only this page needs these.
 *
 * Claims here must stay true of the product: no user counts, accuracy figures,
 * testimonials or features that do not exist, and never a confirmed diagnosis.
 */

export const landingEn = {
  meta: {
    title: "AgriVision · Grow with clarity",
    description:
      "Turn a leaf photograph into a clearer understanding of possible crop diseases and practical next steps. AI-assisted, in English, Hindi and Punjabi.",
  },
  tagline: "Grow with clarity.",
  illustrative: "Illustrative example",
  nav: {
    label: "Main",
    howItWorks: "How it works",
    features: "Features",
    technology: "Technology",
    faq: "FAQ",
    cta: "Try AgriVision",
    menuTitle: "Menu",
    openMenu: "Open menu",
    closeMenu: "Close menu",
  },
  hero: {
    eyebrow: "Intelligence for healthier crops",
    headlineLead: "Know what your crops are",
    headlineAccent: "telling you.",
    body: "Turn a simple leaf photograph into a clearer understanding of potential crop diseases, symptoms, and practical next steps.",
    primaryCta: "Analyze a Crop",
    secondaryCta: "See How It Works",
    trust: "AI-assisted analysis · Multilingual support · Expert guidance encouraged",
    plateLabel: "Image analysis",
    mainAlt: "Tomato leaf with a pale brown late blight lesion, photographed outdoors",
    healthyAlt: "Healthy green tomato leaves",
    healthyLabel: "Healthy leaf",
    predictionsTitle: "Top predictions",
    caption:
      "Fig. 1. Tomato leaf with late blight, beside a healthy leaf. The percentages are illustrative, not a real result.",
  },
  value: {
    heading: "What AgriVision does",
    analysis: "AI-powered image analysis",
    predictions: "Top prediction results",
    languages: "English, Hindi and Punjabi",
    reports: "AI-generated explanatory reports",
  },
  problem: {
    heading: "A small change in a leaf can mean a big difference for a crop.",
    items: {
      recognise: {
        title: "Symptoms can be hard to recognize",
        body: "Early signs are often faint, and different diseases can look alike.",
      },
      timing: {
        title: "Timing matters",
        body: "When a problem is identified late, it can affect the health of the crop.",
      },
      meaning: {
        title: "A spot does not explain itself",
        body: "It is not always clear what you are looking at, or what it could mean.",
      },
      guidance: {
        title: "Clear guidance can be hard to find",
        body: "Good advice is not always close by, or in a language you are comfortable reading.",
      },
    },
    imageAlt: "Grape leaf covered in small pale spots with dark edges",
    detailAlt: "Close view of the same leaf, showing the spots in detail",
    caption: "Fig. 2. Black rot spots on a grape leaf, with one area enlarged.",
  },
  how: {
    heading: "From leaf to insight in three simple steps.",
    capture: {
      title: "Capture",
      body: "Take or upload a clear photograph of the affected leaf.",
      alt: "A hand holding up a yellowing tomato leaf with dark spots",
    },
    analyze: {
      title: "Analyze",
      body: "AgriVision's computer vision model examines the image and generates possible disease predictions.",
      alt: "A diseased tomato leaf framed for analysis",
    },
    understand: {
      title: "Understand",
      body: "Explore the results and an explanatory AI-generated report to understand possible next steps.",
    },
  },
  features: {
    heading: "More than a prediction. A clearer picture.",
    analysis: {
      title: "AI Image Analysis",
      body: "Analyze plant photographs with a computer vision model.",
      alt: "Tomato plant with spotted, yellowing leaves, seen through an analysis grid",
    },
    breakdown: {
      title: "Prediction Breakdown",
      body: "See the model's leading predictions and confidence information, not just one answer.",
    },
    visuals: {
      title: "Explainable Visuals",
      body: "Grad-CAM shows where the model focused. It highlights model attention. It does not prove a diagnosis.",
      photoAlt: "Close view of a tomato leaf with a lesion",
      focusAlt: "The same leaf with a heatmap over the lesion, showing where the model focused",
      source: "Real Grad-CAM output from the AgriVision model.",
    },
    reports: {
      title: "AI-Generated Reports",
      body: "Read what may be happening, which signs to check, safe steps and prevention, and when to ask an expert.",
    },
    languages: {
      title: "Multilingual Experience",
      body: "Use AgriVision in English, Hindi, or Punjabi.",
    },
    guidance: {
      title: "Responsible Guidance",
      body: "Every result is clear about its uncertainty and encourages expert confirmation before you act.",
    },
  },
  preview: {
    heading: "See what a clearer crop diagnosis looks like.",
    intro:
      "This example follows the layout of a real AgriVision result, including how it changes when the model is unsure.",
    status: "Analysis complete",
    variantLabel: "Choose an example result",
    likely: "Likely match",
    uncertain: "Uncertain result",
    summary:
      "Pale patches that turn brown can be a sign of late blight, especially in cool, wet weather.",
    signs: [
      "Dark, water-soaked patches on the leaf",
      "Pale growth under the leaf in damp weather",
      "Brown marks spreading on stems",
    ],
    steps: ["Remove badly affected leaves", "Keep leaves as dry as you can when watering"],
    note: "The Grad-CAM view is real model output for this photo. The percentages and advice text are illustrative.",
  },
  technology: {
    heading: "What is under the hood",
    model: {
      title: "Computer vision model",
      body: "An EfficientNet-B0 image classifier, trained on lab and field leaf photographs.",
    },
    coverage: {
      title: "28 classes, 13 crops",
      body: "It recognizes the diseases and healthy leaves it was trained on, and nothing beyond them.",
    },
    attention: {
      title: "Grad-CAM attention maps",
      body: "A heatmap of the image areas that most influenced the top prediction.",
    },
    reports: {
      title: "Language model reports",
      body: "Each prediction becomes a plain-language report, with rules against dosages and brand names.",
    },
  },
  responsible: {
    heading: "AI can guide the next step. Expertise makes the difference.",
    body: "AgriVision is an assistance tool, not a replacement for agricultural experts. Here is what to keep in mind every time you use it.",
    suggestion: {
      title: "Predictions are suggestions",
      body: "Every result is AI-generated. It is not a confirmed diagnosis.",
    },
    accuracy: {
      title: "Results may be inaccurate",
      body: "This is especially true of photographs taken in the field. The model can be wrong even when it seems sure.",
    },
    conditions: {
      title: "Conditions affect results",
      body: "Image quality, light, background and the environment can all change what the model sees.",
    },
    expert: {
      title: "Ask an expert before treating",
      body: "Consult an agricultural officer or qualified expert before making treatment decisions.",
    },
  },
  faq: {
    heading: "Questions, answered plainly.",
    diagnosis: {
      question: "Is this a diagnosis?",
      answer:
        "No. AgriVision gives AI-generated suggestions. Please confirm with an agricultural officer or qualified expert before you treat your crop.",
    },
    crops: {
      question: "Which crops does it cover?",
      answer:
        "The model was trained on these crops. For each one it knows only certain diseases, so a problem outside its training can be mistaken for something else:",
    },
    photos: {
      question: "What kind of photo works best?",
      answer:
        "One leaf, close up, in the middle of the photo, in good daylight, against a plain background. JPEG, PNG and WebP files up to 10 MB are accepted.",
    },
    uncertain: {
      question: "Why do some results say uncertain?",
      answer:
        "When the model's confidence is below 60%, AgriVision does not name a single disease. It shows the possibilities, asks for a clearer photo, and does not suggest chemical treatment.",
    },
    privacy: {
      question: "Is my photo saved?",
      answer:
        "No. Your photo is used to run the analysis and is not stored. If you answer the feedback question, your answer and the prediction are saved, without the photo.",
    },
    account: {
      question: "Do I need an account?",
      answer: "No. Open the page, add a photograph, and check your leaf.",
    },
  },
  final: {
    heading: "Give every leaf a closer look.",
    body: "Start with a photograph. Leave with a clearer understanding.",
    cta: "Analyze Your Crop",
    micro: "Simple. Multilingual. AI-assisted.",
    imageAlt: "Flowering potato crop in a hillside field in Idukki, Kerala",
  },
  footer: {
    description:
      "AI-assisted crop disease insights from a leaf photograph, for the people who grow our food.",
    navLabel: "Page sections",
    languageLabel: "Language options",
    credits: "Photo credits",
    creditsNote: "Photographs are cropped and resized from these originals.",
  },
};

export type LandingDictionary = typeof landingEn;
