from app.generator.generate import generate
from app.services.validation import validate_tables


def test_starter_dataset(tmp_path):
    tables, manifest, ground_truth = generate(
        "starter",
        20261022,
        tmp_path / "out",
        tmp_path / "truth",
    )

    assert len(tables["carts"]) == 500
    assert len(ground_truth) == 4
    assert tables["carts"][0]["cart_id"] == "CART-2026-000001"

    validation = validate_tables(tables)
    assert not [
        error
        for error in validation["errors"]
        if "missing parent" in error
    ]