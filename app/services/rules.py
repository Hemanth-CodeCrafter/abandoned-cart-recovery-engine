from datetime import timedelta

from app.utils import parse_dt


def is_abandoned(cart, now, inactivity_hours=24):
    if cart.get("purchased_at") or cart.get("status") in (
        "purchased",
        "recovered",
    ):
        return False

    return (
        bool(cart.get("last_activity_at"))
        and cart.get("status") in ("active", "abandoned")
        and parse_dt(now) - parse_dt(cart["last_activity_at"])
        >= timedelta(hours=inactivity_hours)
    )


def current_consent(consents, customer_id, channel, at):
    rows = [
        consent
        for consent in consents
        if consent["customer_id"] == customer_id
        and consent["channel"] == channel
        and parse_dt(consent["effective_at"]) <= parse_dt(at)
    ]

    return (
        bool(rows)
        and sorted(
            rows,
            key=lambda consent: (
                consent["effective_at"],
                consent["consent_id"],
            ),
        )[-1]["status"]
        == "opt_in"
    )


def frequency_cap_reached(
    sends,
    customer_id,
    channel,
    at,
    cap=3,
    window_days=7,
):
    current_time = parse_dt(at)
    window_start = current_time - timedelta(days=window_days)

    return sum(
        send["customer_id"] == customer_id
        and send["channel"] == channel
        and send["decision"] == "sent"
        and window_start <= parse_dt(send["scheduled_at"]) <= current_time
        for send in sends
    ) >= cap


def decide_send(cart, consents, sends, customer_id, channel, at):
    if cart.get("purchased_at") or cart.get("status") in (
        "purchased",
        "recovered",
    ):
        return {
            "decision": "suppressed",
            "reason": "purchased_or_recovered",
        }

    if not is_abandoned(cart, at):
        return {
            "decision": "suppressed",
            "reason": "cart_not_abandoned",
        }

    if not current_consent(consents, customer_id, channel, at):
        return {
            "decision": "suppressed",
            "reason": "no_consent",
        }

    if frequency_cap_reached(sends, customer_id, channel, at):
        return {
            "decision": "suppressed",
            "reason": "frequency_cap",
        }

    return {
        "decision": "sent",
        "reason": "eligible",
    }


def attribute_order(order, sends, events, window_days=7):
    sends_by_id = {
        send["send_id"]: send
        for send in sends
    }
    order_time = parse_dt(order["created_at"])
    candidates = []

    for event in events:
        send = sends_by_id.get(event["send_id"])

        if (
            event["event_type"] == "clicked"
            and send
            and send["decision"] == "sent"
            and send["customer_id"] == order["customer_id"]
        ):
            click_time = parse_dt(event["occurred_at"])

            if (
                click_time
                <= order_time
                <= click_time + timedelta(days=window_days)
            ):
                candidates.append((click_time, send["send_id"]))

    return min(candidates)[1] if candidates else None