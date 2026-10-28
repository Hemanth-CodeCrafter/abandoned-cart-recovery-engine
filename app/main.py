import json

from fastapi import FastAPI, HTTPException, Query

from app.generator.generate import OUT, generate
from app.services.validation import validate_tables


app = FastAPI(
    title="Abandoned Cart Recovery & Attribution Engine",
    version="1.0.0",
)


def load():
    path = OUT / "records.json"

    if not path.exists():
        return generate("starter", 20261022)[0]

    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    tables = load()
    sends = tables["send_attempts"]
    sent = sum(item["decision"] == "sent" for item in sends)
    attributions = tables["attributions"]
    orders = tables["orders"]

    return {
        "carts": len(tables["carts"]),
        "abandoned_carts": sum(
            item["status"] == "abandoned"
            for item in tables["carts"]
        ),
        "campaigns": len(tables["campaigns"]),
        "send_attempts": len(sends),
        "sent": sent,
        "suppressed": len(sends) - sent,
        "orders": len(orders),
        "attributed_orders": len(
            {item["order_id"] for item in attributions}
        ),
        "attribution_records": len(attributions),
    }


@app.get("/carts/{cart_id}")
def cart(cart_id: str):
    tables = load()

    matching_carts = [
        item
        for item in tables["carts"]
        if item["cart_id"] == cart_id
    ]

    if not matching_carts:
        raise HTTPException(status_code=404, detail="Cart not found")

    return {
        "cart": matching_carts[0],
        "lines": [
            item
            for item in tables["cart_lines"]
            if item["cart_id"] == cart_id
        ],
        "send_attempts": [
            item
            for item in tables["send_attempts"]
            if item["cart_id"] == cart_id
        ],
    }


@app.get("/campaign-decisions")
def decisions(limit: int = Query(100, ge=1, le=1000)):
    tables = load()
    sends = tables["send_attempts"]

    return {
        "count": min(limit, len(sends)),
        "items": sends[:limit],
    }


@app.post("/validate")
def validate():
    return validate_tables(load())