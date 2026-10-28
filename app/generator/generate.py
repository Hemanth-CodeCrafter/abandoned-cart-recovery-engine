import argparse
import csv
import hashlib
import json
import random
import sqlite3
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

from app.utils import parse_dt, iso


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/generated"
TRUTH = ROOT / "data/ground_truth"
REF = parse_dt("2026-10-26T12:00:00Z")


def ident(prefix, n, width=6):
    return f"{prefix}{n:0{width}d}"


def generate(
    scale="starter",
    seed=20261022,
    out_dir=OUT,
    truth_dir=TRUTH,
):
    r = random.Random(seed)
    full = scale == "full"

    nc = 50000 if full else 500
    na = 20000 if full else 200
    ns = 10000 if full else 100
    ncu = max(100, nc // 2)

    out_dir = Path(out_dir)
    truth_dir = Path(truth_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    truth_dir.mkdir(parents=True, exist_ok=True)

    table_names = [
        "customers",
        "consents",
        "sessions",
        "carts",
        "cart_lines",
        "campaigns",
        "message_templates",
        "send_attempts",
        "send_events",
        "orders",
        "attributions",
    ]

    t = {name: [] for name in table_names}
    truth = []

    # ---------------------------------------------------------
    # 1. Customers and consent history
    # ---------------------------------------------------------
    for i in range(1, ncu + 1):
        t["customers"].append({
            "customer_id": ident("CUS-", i),
            "created_at": iso(
                REF - timedelta(days=r.randint(30, 900))
            ),
            "region": r.choice(["NA", "EU", "APAC"]),
            "lifecycle_state": (
                "active" if r.random() < 0.92 else "inactive"
            ),
            "issue_type": "",
        })

    for customer in t["customers"]:
        for channel in ["email", "sms"]:
            status = (
                "opt_in"
                if r.random() < (
                    0.82 if channel == "email" else 0.68
                )
                else "opt_out"
            )

            t["consents"].append({
                "consent_id": ident(
                    "CON-", len(t["consents"]) + 1
                ),
                "customer_id": customer["customer_id"],
                "channel": channel,
                "status": status,
                "effective_at": iso(
                    REF - timedelta(days=r.randint(15, 180))
                ),
                "source": "signup",
                "issue_type": "",
            })

            if status == "opt_in" and r.random() < 0.08:
                t["consents"].append({
                    "consent_id": ident(
                        "CON-", len(t["consents"]) + 1
                    ),
                    "customer_id": customer["customer_id"],
                    "channel": channel,
                    "status": "opt_out",
                    "effective_at": iso(
                        REF - timedelta(days=r.randint(0, 14))
                    ),
                    "source": "preferences",
                    "issue_type": "consent_withdrawal",
                })

    # ---------------------------------------------------------
    # 2. Sessions
    # ---------------------------------------------------------
    for i in range(1, nc + 1):
        customer = t["customers"][(i - 1) % ncu]

        start = REF - timedelta(
            days=r.randint(1, 30),
            hours=r.randint(0, 23),
        )
        end = start + timedelta(minutes=r.randint(1, 120))

        t["sessions"].append({
            "session_id": ident("SES-", i),
            "customer_id": customer["customer_id"],
            "device_id": (
                f"DEV-{r.randint(1, max(10, ncu // 5)):05d}"
            ),
            "started_at": iso(start),
            "ended_at": iso(end),
            "source": r.choice([
                "direct", "search", "social", "email", "sms"
            ]),
            "issue_type": "",
        })

    # ---------------------------------------------------------
    # 3. Carts and cart lines
    # ---------------------------------------------------------
    for i in range(1, nc + 1):
        customer = t["customers"][(i - 1) % ncu]
        session = t["sessions"][i - 1]

        created = parse_dt(session["started_at"])
        abandoned = i <= na

        last = REF - timedelta(
            hours=(
                r.randint(25, 120)
                if abandoned
                else r.randint(0, 23)
            )
        )

        updated = max(created, last)

        status = (
            "abandoned"
            if abandoned
            else r.choices(
                ["active", "recovered", "purchased"],
                [0.72, 0.17, 0.11],
            )[0]
        )

        cart_id = ident("CART-2026-", i)
        total = 0

        for j in range(1, r.randint(2, 5)):
            quantity = r.randint(1, 3)
            price = r.randint(500, 25000)
            line_total = quantity * price
            total += line_total

            t["cart_lines"].append({
                "cart_line_id": f"CL-{i:06d}-{j:02d}",
                "cart_id": cart_id,
                "sku": f"SKU-{r.randint(1, 4000):05d}",
                "quantity": quantity,
                "unit_price_cents": price,
                "line_total_cents": line_total,
                "issue_type": "",
            })

        purchased_at = (
            iso(
                min(
                    updated + timedelta(
                        minutes=r.randint(1, 180)
                    ),
                    REF,
                )
            )
            if status == "purchased"
            else ""
        )

        t["carts"].append({
            "cart_id": cart_id,
            "customer_id": customer["customer_id"],
            "session_id": session["session_id"],
            "created_at": iso(created),
            "updated_at": iso(updated),
            "last_activity_at": iso(last),
            "status": status,
            "currency": "USD",
            "total_cents": total,
            "purchased_at": purchased_at,
            "issue_type": "",
        })

    # ---------------------------------------------------------
    # 4. Campaigns and message templates
    # ---------------------------------------------------------
    ncmp = max(10, ns // 10)

    for i in range(1, ncmp + 1):
        channel = ["email", "sms"][(i - 1) % 2]
        start = REF - timedelta(days=r.randint(1, 20))
        campaign_id = ident("CMP-2026-", i)

        t["campaigns"].append({
            "campaign_id": campaign_id,
            "name": f"Cart Recovery {i:04d}",
            "channel": channel,
            "starts_at": iso(start),
            "ends_at": iso(REF + timedelta(days=14)),
            "attribution_window_days": 7,
            "status": "active",
        })

        for variant in ["A", "B"]:
            t["message_templates"].append({
                "template_id": f"TPL-{i:06d}-{variant}",
                "campaign_id": campaign_id,
                "variant": variant,
                "channel": channel,
                "message_key": (
                    f"cart-recovery-{i}-{variant.lower()}"
                ),
                "subject": (
                    "Your cart is waiting"
                    if channel == "email"
                    else ""
                ),
                "body": (
                    f"Reminder variant {variant}: "
                    "your items are waiting in your cart."
                ),
            })

    # ---------------------------------------------------------
    # 5. Send decisions and send events
    # ---------------------------------------------------------
    consent_history = defaultdict(list)

    for consent in t["consents"]:
        key = (consent["customer_id"], consent["channel"])
        consent_history[key].append(consent)

    for key in consent_history:
        consent_history[key].sort(
            key=lambda item: item["effective_at"]
        )

    cart_send_count = defaultdict(int)

    for i in range(1, ns + 1):
        cart = t["carts"][(i - 1) % na]
        campaign = t["campaigns"][(i - 1) % ncmp]

        template_index = (
            ((i - 1) % ncmp) * 2 + ((i - 1) % 2)
        )
        template = t["message_templates"][template_index]

        channel = campaign["channel"]

        scheduled_at = (
            parse_dt(cart["last_activity_at"])
            + timedelta(hours=24, minutes=i % 30)
        )

        history = [
            item
            for item in consent_history[
                (cart["customer_id"], channel)
            ]
            if parse_dt(item["effective_at"]) <= scheduled_at
        ]

        consent_status = (
            history[-1]["status"] if history else "opt_out"
        )

        recent_sends = [
            item
            for item in t["send_attempts"]
            if (
                item["customer_id"] == cart["customer_id"]
                and item["channel"] == channel
                and item["decision"] == "sent"
                and scheduled_at - timedelta(days=7)
                <= parse_dt(item["scheduled_at"])
                <= scheduled_at
            )
        ]

        if (
            cart["purchased_at"]
            or cart["status"] in ("purchased", "recovered")
        ):
            decision, reason = (
                "suppressed", "purchased_or_recovered"
            )

        elif (
            cart["status"] != "abandoned"
            or (
                REF - parse_dt(cart["last_activity_at"])
            ).total_seconds() < 86400
        ):
            decision, reason = (
                "suppressed", "cart_not_abandoned"
            )

        elif consent_status != "opt_in":
            decision, reason = "suppressed", "no_consent"

        elif len(recent_sends) >= 3:
            decision, reason = "suppressed", "frequency_cap"

        else:
            decision, reason = "sent", "eligible"

        cart_send_count[cart["cart_id"]] += 1
        send_id = ident("SEND-2026-", i)

        t["send_attempts"].append({
            "send_id": send_id,
            "message_id": (
                f"MSG-{cart['cart_id']}-"
                f"{cart_send_count[cart['cart_id']]:02d}"
            ),
            "customer_id": cart["customer_id"],
            "cart_id": cart["cart_id"],
            "campaign_id": campaign["campaign_id"],
            "template_id": template["template_id"],
            "channel": channel,
            "scheduled_at": iso(scheduled_at),
            "decision": decision,
            "decision_reason": reason,
            "issue_type": "",
        })

        if decision == "sent":
            t["send_events"].append({
                "event_id": ident(
                    "EVT-", len(t["send_events"]) + 1
                ),
                "send_id": send_id,
                "event_type": "sent",
                "occurred_at": iso(scheduled_at),
                "issue_type": "",
            })

            if r.random() < 0.96:
                t["send_events"].append({
                    "event_id": ident(
                        "EVT-", len(t["send_events"]) + 1
                    ),
                    "send_id": send_id,
                    "event_type": "delivered",
                    "occurred_at": iso(
                        scheduled_at + timedelta(minutes=1)
                    ),
                    "issue_type": "",
                })

                for event_type, probability in [
                    ("opened", 0.38),
                    ("clicked", 0.19),
                ]:
                    if r.random() < probability:
                        event_time = scheduled_at + timedelta(
                            hours=(
                                2 if event_type == "clicked" else 1
                            )
                        )

                        t["send_events"].append({
                            "event_id": ident(
                                "EVT-", len(t["send_events"]) + 1
                            ),
                            "send_id": send_id,
                            "event_type": event_type,
                            "occurred_at": iso(event_time),
                            "issue_type": "",
                        })

    # ---------------------------------------------------------
    # 6. Orders and attribution
    # ---------------------------------------------------------
    sends_by_id = {
        item["send_id"]: item
        for item in t["send_attempts"]
    }

    clicks = [
        event
        for event in t["send_events"]
        if event["event_type"] == "clicked"
    ]

    for cart in t["carts"]:
        if (
            cart["status"] in ("purchased", "recovered")
            or r.random() < 0.04
        ):
            base = parse_dt(cart["last_activity_at"])
            late = r.random() < 0.15

            created_at = base + timedelta(
                days=(
                    r.randint(1, 12)
                    if late
                    else r.randint(0, 5)
                ),
                hours=r.randint(0, 20),
            )

            created_at = min(
                created_at,
                REF - timedelta(minutes=1),
            )

            t["orders"].append({
                "order_id": ident(
                    "ORD-2026-", len(t["orders"]) + 1
                ),
                "customer_id": cart["customer_id"],
                "recovered_cart_id": (
                    cart["cart_id"]
                    if cart["status"] in (
                        "purchased", "recovered"
                    )
                    else ""
                ),
                "created_at": iso(created_at),
                "total_cents": cart["total_cents"],
                "status": "paid",
                "issue_type": "",
            })

    for order in t["orders"]:
        candidates = []

        for event in clicks:
            send = sends_by_id[event["send_id"]]
            click_time = parse_dt(event["occurred_at"])
            order_time = parse_dt(order["created_at"])

            if (
                send["customer_id"] == order["customer_id"]
                and send["decision"] == "sent"
                and click_time <= order_time
                <= click_time + timedelta(days=7)
            ):
                candidates.append(
                    (click_time, send["send_id"])
                )

        if candidates:
            _, send_id = min(candidates)

            t["attributions"].append({
                "attribution_id": ident(
                    "ATT-", len(t["attributions"]) + 1
                ),
                "order_id": order["order_id"],
                "send_id": send_id,
                "attributed_at": order["created_at"],
                "credit_cents": order["total_cents"],
                "model": "first_eligible_click",
                "issue_type": "",
            })

    # ---------------------------------------------------------
    # 7. Inject the four documented anomalies
    # ---------------------------------------------------------
    if t["send_attempts"]:
        send = next(
            (
                item
                for item in t["send_attempts"]
                if item["decision"] == "sent"
            ),
            t["send_attempts"][0],
        )

        send["issue_type"] = "message_sent_after_opt_out"

        t["consents"].append({
            "consent_id": ident(
                "CON-", len(t["consents"]) + 1
            ),
            "customer_id": send["customer_id"],
            "channel": send["channel"],
            "status": "opt_out",
            "effective_at": iso(
                parse_dt(send["scheduled_at"])
                - timedelta(minutes=1)
            ),
            "source": "preferences",
            "issue_type": "message_sent_after_opt_out",
        })

        truth.append({
            "case_id": "ANOM-001",
            "issue_type": "message_sent_after_opt_out",
            "entity": "SendAttempt",
            "record_id": send["send_id"],
            "expected_detection": (
                "Send was decided before the injected withdrawal "
                "but scheduled after opt-out effective time; "
                "should be flagged/suppressed."
            ),
            "severity": "high",
        })

        cart = t["carts"][na // 2]
        cart["status"] = "abandoned"
        cart["issue_type"] = (
            "cart_considered_abandoned_after_purchase"
        )
        cart["purchased_at"] = iso(
            parse_dt(cart["last_activity_at"])
            + timedelta(hours=1)
        )

        t["orders"].append({
            "order_id": ident(
                "ORD-2026-", len(t["orders"]) + 1
            ),
            "customer_id": cart["customer_id"],
            "recovered_cart_id": cart["cart_id"],
            "created_at": cart["purchased_at"],
            "total_cents": cart["total_cents"],
            "status": "paid",
            "issue_type": (
                "cart_considered_abandoned_after_purchase"
            ),
        })

        truth.append({
            "case_id": "ANOM-002",
            "issue_type": (
                "cart_considered_abandoned_after_purchase"
            ),
            "entity": "Cart",
            "record_id": cart["cart_id"],
            "expected_detection": (
                "Purchase timestamp conflicts with abandoned state."
            ),
            "severity": "high",
        })

        if t["attributions"]:
            attribution = dict(t["attributions"][0])
            attribution["attribution_id"] = ident(
                "ATT-", len(t["attributions"]) + 1
            )
            attribution["issue_type"] = (
                "attribution_double_counted_across_campaigns"
            )
            t["attributions"].append(attribution)

            truth.append({
                "case_id": "ANOM-003",
                "issue_type": (
                    "attribution_double_counted_across_campaigns"
                ),
                "entity": "Attribution",
                "record_id": attribution["attribution_id"],
                "expected_detection": (
                    "Order receives more than one attribution credit."
                ),
                "severity": "high",
            })

        line = t["cart_lines"][0]
        line["quantity"] += 1
        line["issue_type"] = (
            "cart_total_stale_after_quantity_update"
        )

        cart = next(
            item
            for item in t["carts"]
            if item["cart_id"] == line["cart_id"]
        )
        cart["issue_type"] = (
            "cart_total_stale_after_quantity_update"
        )

        truth.append({
            "case_id": "ANOM-004",
            "issue_type": "cart_total_stale_after_quantity_update",
            "entity": "Cart",
            "record_id": cart["cart_id"],
            "expected_detection": (
                "Cart total fails to reconcile after line quantity update."
            ),
            "severity": "medium",
        })

    # ---------------------------------------------------------
    # 8. Write CSV and JSON outputs
    # ---------------------------------------------------------
    manifest = {
        "seed": seed,
        "scale": scale,
        "reference_time": "2026-10-26T12:00:00Z",
        "row_counts": {},
        "sha256": {},
    }

    for name, rows in t.items():
        manifest["row_counts"][name] = len(rows)
        fields = list(rows[0]) if rows else []

        csv_path = out_dir / f"{name}.csv"

        with csv_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fields,
            )
            writer.writeheader()
            writer.writerows(rows)

        json_content = json.dumps(
            rows,
            indent=2,
            sort_keys=True,
        )

        json_path = out_dir / f"{name}.json"
        json_path.write_text(
            json_content,
            encoding="utf-8",
        )

        manifest["sha256"][csv_path.name] = (
            hashlib.sha256(csv_path.read_bytes()).hexdigest()
        )
        manifest["sha256"][json_path.name] = (
            hashlib.sha256(json_content.encode()).hexdigest()
        )

    (out_dir / "records.json").write_text(
        json.dumps(t, indent=2),
        encoding="utf-8",
    )

    # ---------------------------------------------------------
    # 9. Relational SQL schema
    # ---------------------------------------------------------
    schema = {
        "customers": {
            "pk": "customer_id",
            "columns": {
                "customer_id": "TEXT",
                "created_at": "TEXT NOT NULL",
                "region": (
                    "TEXT NOT NULL "
                    "CHECK (region IN ('NA','EU','APAC'))"
                ),
                "lifecycle_state": (
                    "TEXT NOT NULL "
                    "CHECK (lifecycle_state IN ('active','inactive'))"
                ),
                "issue_type": "TEXT NOT NULL DEFAULT ''",
            },
        },
        "consents": {
            "pk": "consent_id",
            "columns": {
                "consent_id": "TEXT",
                "customer_id": "TEXT NOT NULL",
                "channel": (
                    "TEXT NOT NULL "
                    "CHECK (channel IN ('email','sms'))"
                ),
                "status": (
                    "TEXT NOT NULL "
                    "CHECK (status IN ('opt_in','opt_out'))"
                ),
                "effective_at": "TEXT NOT NULL",
                "source": "TEXT NOT NULL",
                "issue_type": "TEXT NOT NULL DEFAULT ''",
            },
            "fk": [
                ("customer_id", "customers", "customer_id"),
            ],
        },
        "sessions": {
            "pk": "session_id",
            "columns": {
                "session_id": "TEXT",
                "customer_id": "TEXT NOT NULL",
                "device_id": "TEXT NOT NULL",
                "started_at": "TEXT NOT NULL",
                "ended_at": "TEXT NOT NULL",
                "source": "TEXT NOT NULL",
                "issue_type": "TEXT NOT NULL DEFAULT ''",
            },
            "fk": [
                ("customer_id", "customers", "customer_id"),
            ],
        },
        "carts": {
            "pk": "cart_id",
            "columns": {
                "cart_id": "TEXT",
                "customer_id": "TEXT NOT NULL",
                "session_id": "TEXT NOT NULL",
                "created_at": "TEXT NOT NULL",
                "updated_at": "TEXT NOT NULL",
                "last_activity_at": "TEXT NOT NULL",
                "status": (
                    "TEXT NOT NULL CHECK "
                    "(status IN ('active','abandoned','recovered','purchased'))"
                ),
                "currency": "TEXT NOT NULL",
                "total_cents": (
                    "INTEGER NOT NULL CHECK (total_cents >= 0)"
                ),
                "purchased_at": "TEXT",
                "issue_type": "TEXT NOT NULL DEFAULT ''",
            },
            "fk": [
                ("customer_id", "customers", "customer_id"),
                ("session_id", "sessions", "session_id"),
            ],
        },
        "cart_lines": {
            "pk": "cart_line_id",
            "columns": {
                "cart_line_id": "TEXT",
                "cart_id": "TEXT NOT NULL",
                "sku": "TEXT NOT NULL",
                "quantity": (
                    "INTEGER NOT NULL CHECK (quantity >= 1)"
                ),
                "unit_price_cents": (
                    "INTEGER NOT NULL CHECK (unit_price_cents >= 0)"
                ),
                "line_total_cents": (
                    "INTEGER NOT NULL CHECK (line_total_cents >= 0)"
                ),
                "issue_type": "TEXT NOT NULL DEFAULT ''",
            },
            "fk": [
                ("cart_id", "carts", "cart_id"),
            ],
        },
        "campaigns": {
            "pk": "campaign_id",
            "columns": {
                "campaign_id": "TEXT",
                "name": "TEXT NOT NULL",
                "channel": (
                    "TEXT NOT NULL CHECK (channel IN ('email','sms'))"
                ),
                "starts_at": "TEXT NOT NULL",
                "ends_at": "TEXT NOT NULL",
                "attribution_window_days": (
                    "INTEGER NOT NULL "
                    "CHECK (attribution_window_days > 0)"
                ),
                "status": "TEXT NOT NULL",
            },
        },
        "message_templates": {
            "pk": "template_id",
            "columns": {
                "template_id": "TEXT",
                "campaign_id": "TEXT NOT NULL",
                "variant": (
                    "TEXT NOT NULL CHECK (variant IN ('A','B'))"
                ),
                "channel": (
                    "TEXT NOT NULL CHECK (channel IN ('email','sms'))"
                ),
                "message_key": "TEXT NOT NULL UNIQUE",
                "subject": "TEXT NOT NULL",
                "body": "TEXT NOT NULL",
            },
            "fk": [
                ("campaign_id", "campaigns", "campaign_id"),
            ],
        },
        "send_attempts": {
            "pk": "send_id",
            "columns": {
                "send_id": "TEXT",
                "message_id": "TEXT NOT NULL UNIQUE",
                "customer_id": "TEXT NOT NULL",
                "cart_id": "TEXT NOT NULL",
                "campaign_id": "TEXT NOT NULL",
                "template_id": "TEXT NOT NULL",
                "channel": (
                    "TEXT NOT NULL CHECK (channel IN ('email','sms'))"
                ),
                "scheduled_at": "TEXT NOT NULL",
                "decision": (
                    "TEXT NOT NULL "
                    "CHECK (decision IN ('sent','suppressed'))"
                ),
                "decision_reason": "TEXT NOT NULL",
                "issue_type": "TEXT NOT NULL DEFAULT ''",
            },
            "fk": [
                ("customer_id", "customers", "customer_id"),
                ("cart_id", "carts", "cart_id"),
                ("campaign_id", "campaigns", "campaign_id"),
                ("template_id", "message_templates", "template_id"),
            ],
        },
        "send_events": {
            "pk": "event_id",
            "columns": {
                "event_id": "TEXT",
                "send_id": "TEXT NOT NULL",
                "event_type": (
                    "TEXT NOT NULL CHECK "
                    "(event_type IN "
                    "('sent','delivered','opened','clicked','bounced','unsubscribed'))"
                ),
                "occurred_at": "TEXT NOT NULL",
                "issue_type": "TEXT NOT NULL DEFAULT ''",
            },
            "fk": [
                ("send_id", "send_attempts", "send_id"),
            ],
        },
        "orders": {
            "pk": "order_id",
            "columns": {
                "order_id": "TEXT",
                "customer_id": "TEXT NOT NULL",
                "recovered_cart_id": "TEXT",
                "created_at": "TEXT NOT NULL",
                "total_cents": (
                    "INTEGER NOT NULL CHECK (total_cents >= 0)"
                ),
                "status": "TEXT NOT NULL",
                "issue_type": "TEXT NOT NULL DEFAULT ''",
            },
            "fk": [
                ("customer_id", "customers", "customer_id"),
                ("recovered_cart_id", "carts", "cart_id"),
            ],
        },
        "attributions": {
            "pk": "attribution_id",
            "columns": {
                "attribution_id": "TEXT",
                "order_id": "TEXT NOT NULL",
                "send_id": "TEXT NOT NULL",
                "attributed_at": "TEXT NOT NULL",
                "credit_cents": (
                    "INTEGER NOT NULL CHECK (credit_cents >= 0)"
                ),
                "model": "TEXT NOT NULL",
                "issue_type": "TEXT NOT NULL DEFAULT ''",
            },
            "fk": [
                ("order_id", "orders", "order_id"),
                ("send_id", "send_attempts", "send_id"),
            ],
        },
    }

    sql = [
        "PRAGMA foreign_keys = ON;",
        "BEGIN TRANSACTION;",
    ]

    for name, definition in schema.items():
        columns = definition["columns"]
        parts = []

        for column, column_type in columns.items():
            if column == definition["pk"]:
                parts.append(
                    f'"{column}" {column_type} PRIMARY KEY'
                )
            else:
                parts.append(
                    f'"{column}" {column_type}'
                )

        for local_col, parent_table, parent_col in (
            definition.get("fk", [])
        ):
            parts.append(
                f'FOREIGN KEY ("{local_col}") '
                f'REFERENCES "{parent_table}" ("{parent_col}")'
            )

        sql.append(
            f'CREATE TABLE IF NOT EXISTS "{name}" (\n  '
            + ",\n  ".join(parts)
            + "\n);"
        )

        for row in t[name]:
            row_columns = list(row.keys())
            column_sql = ", ".join(
                f'"{column}"' for column in row_columns
            )
            values = []

            for column in row_columns:
                value = row[column]

                nullable_fields = {
                    ("carts", "purchased_at"),
                    ("orders", "recovered_cart_id"),
                }

                if (
                    (value is None or value == "")
                    and (name, column) in nullable_fields
                ):
                    values.append("NULL")

                elif value is None:
                    values.append("NULL")

                elif isinstance(value, bool):
                    values.append("1" if value else "0")

                elif isinstance(value, (int, float)):
                    values.append(str(value))

                else:
                    escaped = str(value).replace("'", "''")
                    values.append(f"'{escaped}'")

            sql.append(
                f'INSERT INTO "{name}" ({column_sql}) '
                f"VALUES ({', '.join(values)});"
            )

    sql.append("COMMIT;")

    (out_dir / "seed.sql").write_text(
        "\n".join(sql) + "\n",
        encoding="utf-8",
    )

    # ---------------------------------------------------------
    # 10. Ground truth and manifest
    # ---------------------------------------------------------
    (truth_dir / "ground_truth.json").write_text(
        json.dumps({
            "seed": seed,
            "scale": scale,
            "anomalies": truth,
        }, indent=2),
        encoding="utf-8",
    )

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    return t, manifest, truth


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

    tables, manifest, anomalies = generate(
        scale=args.scale,
        seed=args.seed,
    )

    print(json.dumps({
        "scale": args.scale,
        "seed": args.seed,
        "row_counts": manifest["row_counts"],
        "anomalies": len(anomalies),
    }, indent=2))


if __name__ == "__main__":
    main()