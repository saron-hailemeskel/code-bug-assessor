from pathlib import Path

import pandas as pd

from feature_extractor import FeatureExtractor


# Find the project root regardless of the current terminal directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = PROCESSED_DATA_DIR / "features.csv"

VALID_LABELS = {"low", "medium", "high"}


def build_dataset():
    """
    Extract features from labeled Python files and save them to a CSV.
    """

    extractor = FeatureExtractor()

    rows = []
    skipped_files = 0

    # Check whether the raw dataset directory exists.
    if not RAW_DATA_DIR.exists():
        print(f"Error: Dataset directory not found: {RAW_DATA_DIR}")
        return

    # Process each risk category.
    for label in sorted(VALID_LABELS):
        label_dir = RAW_DATA_DIR / label

        if not label_dir.exists():
            print(f"Warning: Missing category directory: {label_dir}")
            continue

        python_files = sorted(label_dir.rglob("*.py"))

        print(f"\nProcessing '{label}' examples: {len(python_files)} files")

        for file_path in python_files:
            try:
                code = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                print(f"Skipping {file_path.name}: {error}")
                skipped_files += 1
                continue

            features = extractor.extract(code)

            # Syntax errors cannot produce a valid feature row.
            if "error" in features:
                print(
                    f"Skipping {file_path.name}: "
                    f"{features['error']}"
                )
                skipped_files += 1
                continue

            # Attach the human-assigned label to the extracted features.
            features["label"] = label

            # Store the relative path to identify the source example.
            features["source_file"] = str(
                file_path.relative_to(PROJECT_ROOT)
            )

            rows.append(features)

    if not rows:
        print("\nNo valid Python examples were found.")
        print("Add Python files to data/raw/low, medium, or high.")
        return

    # Convert the extracted records into a tabular dataset.
    dataset = pd.DataFrame(rows)

    # Put the label and source path after the numerical features.
    metadata_columns = ["label", "source_file"]

    feature_columns = [
        column
        for column in dataset.columns
        if column not in metadata_columns
    ]

    dataset = dataset[feature_columns + metadata_columns]

    # Create the output directory if it does not exist.
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save the dataset.
    dataset.to_csv(OUTPUT_FILE, index=False)

    print("\nDataset built successfully!")
    print(f"Total valid examples: {len(dataset)}")
    print(f"Skipped files: {skipped_files}")
    print(f"Output file: {OUTPUT_FILE}")

    print("\nExamples per label:")
    print(dataset["label"].value_counts().sort_index())

    print("\nDataset preview:")
    print(dataset.head())


if __name__ == "__main__":
    build_dataset()