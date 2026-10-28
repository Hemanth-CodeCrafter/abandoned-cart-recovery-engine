
from collections import Counter, defaultdict

from app.utils import parse_dt


def validate_tables(t):
    errors = []
    warnings = []

    # Primary-key definitions for every table.
    pk = {
        "customers": "customer_id",
        "consents": "consent_id",
        "sessions": "session_id",
        "carts": "cart_id",
        "cart_lines": "cart_line_id",
        "campaigns": "campaign_id",
        "message_templates": "template_id",
        "send_attempts": "send_id",
        "send_events": "event_id",
        "orders": "order_id",
        "attributions": "attribution_id",
    }

    # Check primary-key uniqueness and build ID sets for FK validation.
    ids = {}

    for table, field in pk.items():
        rows = t.get(table, [])
        vals = [row[field] for row in rows if field in row]

        if len(vals) != len(set(vals)):
            errors.append(f"{table}: duplicate primary key")

        if len(vals) != len(rows):
            errors.append(f"{table}: missing primary key")

        ids[table] = set(vals)

    # Foreign keys: (child table, child field, parent table, optional).
    fks = [
        ("consents", "customer_id", "customers", False),
        ("sessions", "customer_id", "customers", False),
        ("carts", "customer_id", "customers", False),
        ("carts", "session_id", "sessions", False),
        ("cart_lines", "cart_id", "carts", False),
        (
            "message_templates",
            "campaign_id",
            "campaigns",
            False,
        ),
        ("send_attempts", "customer_id", "customers", False),
        ("send_attempts", "cart_id", "carts", False),
        ("send_attempts", "campaign_id", "campaigns", False),
        (
            "send_attempts",
            "template_id",
            "message_templates",
            False,
        ),
        ("send_events", "send_id", "send_attempts", False),
        ("orders", "customer_id", "customers", False),
        ("orders", "recovered_cart_id", "carts", True),
        ("attributions", "order_id", "orders", False),
        ("attributions", "send_id", "send_attempts", False),
    ]

    for table, field, parent, optional in fks:
        for row in t.get(table, []):
            value = row.get(field)

            if optional and not value:
                continue

            if value not in ids[parent]:
                errors.append(
                    f"{table}.{field}: missing parent {value}"
                )

    # Validate session timestamps.
    for session in t.get("sessions", []):
        try:
            started_at = parse_dt(session["started_at"])
            ended_at = parse_dt(session["ended_at"])

            if ended_at < started_at:
                errors.append(
                    "session date ordering invalid: "
                    f"{session.get('session_id', 'unknown')}"
                )
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(
                "session timestamp invalid: "
                f"{session.get('session_id', 'unknown')} ({exc})"
            )

    # Validate cart-line quantities and arithmetic.
    lines_by_cart = defaultdict(list)
    mismatched_line_carts = set()

    for line in t.get("cart_lines", []):
        cart_id = line.get("cart_id")
        lines_by_cart[cart_id].append(line)

        quantity = line.get("quantity")
        unit_price = line.get("unit_price_cents")
        line_total = line.get("line_total_cents")
        line_id = line.get("cart_line_id", "unknown")

        if not isinstance(quantity, int) or quantity < 1:
            errors.append(f"cart line quantity invalid: {line_id}")
            continue

        if not isinstance(unit_price, int) or not isinstance(
            line_total, int
        ):
            errors.append(f"cart line price invalid: {line_id}")
            continue

        if line_total != quantity * unit_price:
            mismatched_line_carts.add(cart_id)
            message = f"cart line arithmetic mismatch: {line_id}"

            # A labelled mismatch is an intentional injected anomaly.
            if line.get("issue_type"):
                warnings.append(message)
            else:
                errors.append(message)

    # Validate cart totals. Avoid repeating the warning when a
    # cart already has a line-level arithmetic mismatch.
    for cart in t.get("carts", []):
        cart_id = cart.get("cart_id")
        expected_total = sum(
            line.get("line_total_cents", 0)
            for line in lines_by_cart.get(cart_id, [])
        )
        actual_total = cart.get("total_cents")

        if expected_total != actual_total:
            if cart_id not in mismatched_line_carts:
                warnings.append(f"cart total mismatch: {cart_id}")

    # Index orders by their recovered cart.
    orders_by_cart = defaultdict(list)

    for order in t.get("orders", []):
        cart_id = order.get("recovered_cart_id")

        if cart_id:
            orders_by_cart[cart_id].append(order)

    # Detect carts labelled abandoned despite evidence of purchase.
    for cart in t.get("carts", []):
        cart_id = cart.get("cart_id")

        if cart.get("status") != "abandoned":
            continue

        has_purchase_timestamp = bool(cart.get("purchased_at"))
        has_linked_order = bool(orders_by_cart.get(cart_id))

        if has_purchase_timestamp or has_linked_order:
            warnings.append(
                f"cart abandoned after purchase: {cart_id}"
            )

    # Detect duplicate attribution records for an order.
    attribution_counts = Counter(
        attribution.get("order_id")
        for attribution in t.get("attributions", [])
    )

    for order_id, count in attribution_counts.items():
        if count > 1:
            warnings.append(
                f"order attributed more than once: {order_id}"
            )

    # Group consent history by customer and communication channel.
    consent_history = defaultdict(list)

    for consent in t.get("consents", []):
        key = (
            consent.get("customer_id"),
            consent.get("channel"),
        )
        consent_history[key].append(consent)

    # Check successful sends against the latest consent effective
    # at the send's scheduled timestamp.
    for send in t.get("send_attempts", []):
        if send.get("decision") != "sent":
            continue

        customer_id = send.get("customer_id")
        channel = send.get("channel")
        scheduled_at = send.get("scheduled_at")
        send_id = send.get("send_id", "unknown")

        if not scheduled_at:
            errors.append(
                f"send missing scheduled_at: {send_id}"
            )
            continue

        try:
            send_time = parse_dt(scheduled_at)

            eligible_history = [
                consent
                for consent in consent_history[
                    (customer_id, channel)
                ]
                if parse_dt(consent["effective_at"]) <= send_time
            ]

            if not eligible_history:
                # No effective consent record means the validator
                # cannot establish that this send was consented to.
                warnings.append(
                    f"sent without prior consent record: {send_id}"
                )
                continue

            latest_consent = max(
                eligible_history,
                key=lambda consent: (
                    parse_dt(consent["effective_at"]),
                    consent.get("consent_id", ""),
                ),
            )

            if latest_consent.get("status") != "opt_in":
                warnings.append(
                    f"sent after opt-out: {send_id}"
                )

        except (KeyError, TypeError, ValueError) as exc:
            errors.append(
                f"send consent history invalid: {send_id} ({exc})"
            )

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            table: len(rows)
            for table, rows in t.items()
        },
    }
