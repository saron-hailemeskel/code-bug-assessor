from pathlib import Path

import joblib
import pandas as pd


# Resolve paths relative to the project directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_FILE = PROJECT_ROOT / "data" / "processed" / "features.csv"
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_FILE = MODEL_DIR / "random_forest.joblib"

VALID_LABELS = {"low", "medium", "high"}

# Keep this baseline conservative: a tiny dataset must not
# produce a model that we present as meaningfully evaluated.
MIN_EXAMPLES_PER_CLASS = 10


def load_dataset():
    """Load and validate the generated feature dataset."""

    if not DATASET_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_FILE}\n"
            "Run: python src\\dataset_builder.py"
        )

    dataset = pd.read_csv(DATASET_FILE)

    if dataset.empty:
        raise ValueError("The dataset contains no examples.")

    required_columns = {"label", "source_file"}
    missing_columns = required_columns - set(dataset.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if dataset["label"].isna().any():
        raise ValueError("Some examples have missing labels.")

    unexpected_labels = set(dataset["label"].unique()) - VALID_LABELS

    if unexpected_labels:
        raise ValueError(
            f"Unexpected labels found: {sorted(unexpected_labels)}"
        )

    # Keep numerical features only. The label is the target,
    # while source_file is metadata, not a model feature.
    feature_columns = [
        column
        for column in dataset.columns
        if column not in {"label", "source_file"}
    ]

    if not feature_columns:
        raise ValueError("No feature columns were found.")

    features = dataset[feature_columns]

    if not all(
        pd.api.types.is_numeric_dtype(features[column])
        for column in feature_columns
    ):
        raise ValueError("All model features must be numerical.")

    if features.isna().any().any():
        raise ValueError("The dataset contains missing feature values.")

    labels = dataset["label"]

    return features, labels


def validate_dataset(labels):
    """Check whether there is enough data to attempt evaluation."""

    counts = labels.value_counts().reindex(
        sorted(VALID_LABELS),
        fill_value=0,
    )

    print("\nExamples per class:")
    print(counts.to_string())

    missing_classes = counts[counts == 0].index.tolist()

    if missing_classes:
        raise ValueError(
            "The dataset must contain all three classes. "
            f"Missing: {missing_classes}"
        )

    insufficient_classes = counts[
        counts < MIN_EXAMPLES_PER_CLASS
    ]

    if not insufficient_classes.empty:
        details = ", ".join(
            f"{label}: {count}"
            for label, count in insufficient_classes.items()
        )

        raise ValueError(
            "\nNot enough examples to proceed with model training.\n"
            f"Current counts — {details}\n"
            f"Minimum for this initial pipeline: "
            f"{MIN_EXAMPLES_PER_CLASS} examples per class.\n"
            "Add more labeled examples, rebuild the dataset, "
            "and run this script again."
        )


def main():
    print("Loading dataset...")

    features, labels = load_dataset()

    print(f"Dataset location: {DATASET_FILE}")
    print(f"Total examples: {len(features)}")
    print(f"Number of features: {features.shape[1]}")

    validate_dataset(labels)

    # Training and evaluation will be added after we have
    # sufficient data and a defensible labeling strategy.
    print(
        "\nDataset validation passed. "
        "The training and evaluation stages are not implemented yet."
    )


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as error:
        print(f"\nDataset validation failed:\n{error}")

