from app.services.rules import (
    is_abandoned,
    current_consent,
    frequency_cap_reached,
    attribute_order,
    decide_send,
)


def test_abandonment():
    cart = {
        "last_activity_at": "2026-10-25T10:00:00Z",
        "status": "active",
        "purchased_at": "",
    }

    assert is_abandoned(cart, "2026-10-26T10:00:00Z")
    assert not is_abandoned(
        {**cart, "purchased_at": "2026-10-26T09:00:00Z"},
        "2026-10-26T12:00:00Z",
    )
    assert not is_abandoned(
        {**cart, "status": "recovered"},
        "2026-10-27T12:00:00Z",
    )


def test_consent_latest_event():
    history = [
        {
            "consent_id": "1",
            "customer_id": "c",
            "channel": "email",
            "status": "opt_in",
            "effective_at": "2026-10-01T00:00:00Z",
        },
        {
            "consent_id": "2",
            "customer_id": "c",
            "channel": "email",
            "status": "opt_out",
            "effective_at": "2026-10-25T00:00:00Z",
        },
    ]

    assert not current_consent(
        history, "c", "email", "2026-10-26T00:00:00Z"
    )
    assert current_consent(
        history, "c", "email", "2026-10-20T00:00:00Z"
    )


def test_consent_effective_exactly_at_send_time():
    history = [
        {
            "consent_id": "1",
            "customer_id": "c",
            "channel": "email",
            "status": "opt_out",
            "effective_at": "2026-10-26T12:00:00Z",
        }
    ]

    assert not current_consent(
        history, "c", "email", "2026-10-26T12:00:00Z"
    )


def test_consent_requires_matching_customer_and_channel():
    history = [
        {
            "consent_id": "1",
            "customer_id": "other",
            "channel": "email",
            "status": "opt_in",
            "effective_at": "2026-10-01T00:00:00Z",
        },
        {
            "consent_id": "2",
            "customer_id": "c",
            "channel": "sms",
            "status": "opt_in",
            "effective_at": "2026-10-01T00:00:00Z",
        },
    ]

    assert not current_consent(
        history, "c", "email", "2026-10-26T12:00:00Z"
    )


def test_frequency_cap():
    sends = [
        {
            "customer_id": "c",
            "channel": "email",
            "decision": "sent",
            "scheduled_at": f"2026-10-{day:02d}T00:00:00Z",
        }
        for day in [21, 22, 23]
    ]

    assert frequency_cap_reached(
        sends, "c", "email", "2026-10-24T00:00:00Z"
    )


def test_frequency_cap_ignores_other_customers_channels_and_suppressed():
    sends = [
        {
            "customer_id": "other",
            "channel": "email",
            "decision": "sent",
            "scheduled_at": "2026-10-23T00:00:00Z",
        },
        {
            "customer_id": "c",
            "channel": "sms",
            "decision": "sent",
            "scheduled_at": "2026-10-23T00:00:00Z",
        },
        {
            "customer_id": "c",
            "channel": "email",
            "decision": "suppressed",
            "scheduled_at": "2026-10-23T00:00:00Z",
        },
    ]

    assert not frequency_cap_reached(
        sends, "c", "email", "2026-10-24T00:00:00Z"
    )


def test_attribution_chooses_earliest_eligible_click():
    sends = [
        {"send_id": "s1", "customer_id": "c", "decision": "sent"},
        {"send_id": "s2", "customer_id": "c", "decision": "sent"},
    ]
    events = [
        {
            "send_id": "s2",
            "event_type": "clicked",
            "occurred_at": "2026-10-03T00:00:00Z",
        },
        {
            "send_id": "s1",
            "event_type": "clicked",
            "occurred_at": "2026-10-02T00:00:00Z",
        },
    ]

    order = {
        "customer_id": "c",
        "created_at": "2026-10-04T00:00:00Z",
    }

    assert attribute_order(order, sends, events) == "s1"


def test_attribution_rejects_click_after_order():
    sends = [
        {"send_id": "s1", "customer_id": "c", "decision": "sent"}
    ]
    events = [
        {
            "send_id": "s1",
            "event_type": "clicked",
            "occurred_at": "2026-10-05T00:00:00Z",
        }
    ]

    order = {
        "customer_id": "c",
        "created_at": "2026-10-04T00:00:00Z",
    }

    assert attribute_order(order, sends, events) is None


def test_attribution_rejects_click_from_another_customer():
    sends = [
        {"send_id": "s1", "customer_id": "other", "decision": "sent"}
    ]
    events = [
        {
            "send_id": "s1",
            "event_type": "clicked",
            "occurred_at": "2026-10-03T00:00:00Z",
        }
    ]

    order = {
        "customer_id": "c",
        "created_at": "2026-10-04T00:00:00Z",
    }

    assert attribute_order(order, sends, events) is None


def test_attribution_rejects_unsent_message():
    sends = [
        {"send_id": "s1", "customer_id": "c", "decision": "suppressed"}
    ]
    events = [
        {
            "send_id": "s1",
            "event_type": "clicked",
            "occurred_at": "2026-10-03T00:00:00Z",
        }
    ]

    order = {
        "customer_id": "c",
        "created_at": "2026-10-04T00:00:00Z",
    }

    assert attribute_order(order, sends, events) is None


def test_decide_send_suppresses_without_consent():
    cart = {
        "last_activity_at": "2026-10-25T10:00:00Z",
        "status": "abandoned",
        "purchased_at": "",
    }

    result = decide_send(
        cart=cart,
        consents=[],
        sends=[],
        customer_id="c",
        channel="email",
        at="2026-10-26T12:00:00Z",
    )

    assert result == {
        "decision": "suppressed",
        "reason": "no_consent",
    }
