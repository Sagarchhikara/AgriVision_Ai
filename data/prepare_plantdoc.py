"""
data/prepare_plantdoc.py

Script to parse PlantDoc dataset flat files and _classes.txt annotations,
organizing images into class subdirectories matching the 38-class PlantVillage structure.
"""

import os
import shutil
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PLANTDOC_DIR = BASE_DIR / "datasets" / "PlantDoc"

PLANTDOC_MAPPING = {
    "Apple Scab Leaf": "Apple___Apple_scab",
    "Apple leaf": "Apple___healthy",
    "Apple rust leaf": "Apple___Cedar_apple_rust",
    "Bell_pepper leaf": "Pepper,_bell___healthy",
    "Bell_pepper leaf spot": "Pepper,_bell___Bacterial_spot",
    "Blueberry leaf": "Blueberry___healthy",
    "Cherry leaf": "Cherry_(including_sour)___healthy",
    "Corn Gray leaf spot": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn leaf blight": "Corn_(maize)___Northern_Leaf_Blight",
    "Corn rust leaf": "Corn_(maize)___Common_rust_",
    "Peach leaf": "Peach___healthy",
    "Potato leaf": "Potato___healthy",
    "Potato leaf early blight": "Potato___Early_blight",
    "Potato leaf late blight": "Potato___Late_blight",
    "Raspberry leaf": "Raspberry___healthy",
    "Soyabean leaf": "Soybean___healthy",
    "Soybean leaf": "Soybean___healthy",
    "Squash Powdery mildew leaf": "Squash___Powdery_mildew",
    "Strawberry leaf": "Strawberry___healthy",
    "Tomato Early blight leaf": "Tomato___Early_blight",
    "Tomato Septoria leaf spot": "Tomato___Septoria_leaf_spot",
    "Tomato leaf": "Tomato___healthy",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot",
    "Tomato leaf late blight": "Tomato___Late_blight",
    "Tomato leaf mosaic virus": "Tomato___Tomato_mosaic_virus",
    "Tomato leaf yellow virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato mold leaf": "Tomato___Leaf_Mold",
    "Tomato two spotted spider mites leaf": "Tomato___Spider_mites Two-spotted_spider_mite",
    "grape leaf": "Grape___healthy",
    "grape leaf black rot": "Grape___Black_rot",
}

# The 38 canonical PlantVillage classes in exact order
ALL_38_CLASSES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]


def parse_classes_file(classes_path):
    if not classes_path.exists():
        return []
    with open(classes_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if not lines:
        return []

    header = lines[0].strip().split(",")
    class_names = [c.strip() for c in header[1:]]

    parsed = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.rsplit(",", len(class_names))
        fname = parts[0].strip()

        try:
            vals = [int(v.strip()) for v in parts[1:]]
        except ValueError:
            continue

        active_indices = [i for i, v in enumerate(vals) if v == 1]
        if active_indices:
            cls_name = class_names[active_indices[0]]
            parsed.append((fname, cls_name))

    return parsed


def organize_split(split_name="test"):
    split_dir = PLANTDOC_DIR / split_name
    classes_file = split_dir / "_classes.txt"

    if not classes_file.exists():
        print(f"No _classes.txt found in {split_dir}. Skipping.")
        return

    print(f"\nProcessing PlantDoc '{split_name}' split...")
    parsed_records = parse_classes_file(classes_file)
    print(f"Parsed {len(parsed_records)} image records from {classes_file.name}")

    # Create subfolders for ALL 38 classes so ImageFolder index alignment matches
    for cls in ALL_38_CLASSES:
        (split_dir / cls).mkdir(parents=True, exist_ok=True)

    moved_count = 0
    skipped_count = 0

    for fname, raw_class in parsed_records:
        src_path = split_dir / fname
        target_class_folder = PLANTDOC_MAPPING.get(raw_class)

        if not target_class_folder:
            skipped_count += 1
            continue

        dest_dir = split_dir / target_class_folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / fname

        if src_path.exists() and src_path.is_file():
            shutil.move(str(src_path), str(dest_path))
            moved_count += 1
        elif dest_path.exists():
            moved_count += 1
        else:
            skipped_count += 1

    print(f"Organized {moved_count} images into 38-class subdirectories for '{split_name}' split.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} images (unmapped or missing).")


def main():
    print(f"PlantDoc Directory: {PLANTDOC_DIR}")
    for split in ["test", "train"]:
        organize_split(split)


if __name__ == "__main__":
    main()
