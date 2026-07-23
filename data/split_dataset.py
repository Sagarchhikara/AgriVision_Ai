from pathlib import Path
import shutil
import random

random.seed(42)

SOURCE_DIR = Path("datasets/PlantVillage")

OUTPUT_DIR = Path("datasets")

TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15


def split_dataset():

    classes = [folder for folder in SOURCE_DIR.iterdir() if folder.is_dir()]

    for cls in classes:

        images = list(cls.glob("*"))

        random.shuffle(images)

        total = len(images)

        train_end = int(total * TRAIN_RATIO)
        val_end = train_end + int(total * VAL_RATIO)

        splits = {
            "train": images[:train_end],
            "val": images[train_end:val_end],
            "test": images[val_end:]
        }

        for split_name, split_images in splits.items():

            destination = OUTPUT_DIR / split_name / cls.name

            destination.mkdir(parents=True, exist_ok=True)

            for image in split_images:

                shutil.copy(image, destination / image.name)


if __name__ == "__main__":
    split_dataset()