import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.generator.generate import generate


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

    with (
        tempfile.TemporaryDirectory() as first_dir,
        tempfile.TemporaryDirectory() as second_dir,
    ):
        _, first_manifest, _ = generate(
            args.scale,
            args.seed,
            Path(first_dir) / "out",
            Path(first_dir) / "truth",
        )

        _, second_manifest, _ = generate(
            args.scale,
            args.seed,
            Path(second_dir) / "out",
            Path(second_dir) / "truth",
        )

        reproducible = (
            first_manifest["row_counts"] == second_manifest["row_counts"]
            and first_manifest["sha256"] == second_manifest["sha256"]
        )

        print(
            {
                "reproducible": reproducible,
                "seed": args.seed,
                "scale": args.scale,
            }
        )

        raise SystemExit(0 if reproducible else 1)


if __name__ == "__main__":
    main()