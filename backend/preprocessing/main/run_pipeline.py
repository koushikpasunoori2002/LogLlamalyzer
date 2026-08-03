"""
run_pipeline.py

Execute the preprocessing pipeline.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.preprocessing.pipeline import (
    PreprocessingPipeline,
)


def main():

    pipeline = PreprocessingPipeline()

    file_path = (
        PROJECT_ROOT
        / "dataset"
        / "raw"
        / "auth"
        / "auth.log"
    )

    info, records = (
        pipeline.process_with_metadata(file_path)
    )

    print("=" * 70)
    print("PIPELINE EXECUTION")
    print("=" * 70)

    print("Log type:", info.log_type)
    print("Records:", len(records))

    if records:
        print("\nFirst record:")
        print(records[0])


if __name__ == "__main__":
    main()