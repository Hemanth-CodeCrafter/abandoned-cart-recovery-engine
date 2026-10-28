import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.generator.generate import OUT, generate
from app.services.validation import validate_tables


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scale",
        choices=["starter", "full"],
        default="starter",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20261022,
    )
    args = parser.parse_args()

    tables, manifest, ground_truth = generate(
        args.scale,
        args.seed,
    )

    report = validate_tables(tables)
    report["ground_truth_anomaly_count"] = len(ground_truth)

    output_path = OUT / "validation_summary.json"
    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))

    raise SystemExit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()