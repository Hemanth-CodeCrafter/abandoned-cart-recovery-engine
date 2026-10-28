# Data Dictionary

This document describes the entities, key fields, validation rules, and relationships used by the Abandoned Cart Recovery & Attribution Engine.

## Conventions

- **Identifiers:** All IDs are immutable strings.
- **Timestamps:** UTC in ISO 8601 format.
- **Currency:** Monetary amounts are stored as integer cents.
- **Relationships:** Foreign-key references connect related entities.
- **Anomaly labels:** `issue_type` identifies intentionally injected anomalies where applicable.

## Entities and Relationships

| Entity | Primary Key | Required Fields and Validation | Relationships |
|---|---|---|---|
| Customer | `customer_id` | `created_at`, `region` (`NA`, `EU`, `APAC`), `lifecycle_state` (`active`, `inactive`) | One customer can have multiple consent records, sessions, carts, and orders. |
| Consent | `consent_id` | `customer_id`, `channel` (`email`, `sms`), `status` (`opt_in`, `opt_out`), `effective_at`, `source` | Belongs to one customer. Consent changes are maintained as append-only history. |
| Session | `session_id` | `customer_id`, `device_id`, `started_at`, `ended_at` greater than or equal to `started_at`, `source` | Belongs to one customer and can be associated with multiple carts. |
| Cart | `cart_id` | `customer_id`, `session_id`, creation, update, and last-activity timestamps, `status`, `currency`, `total_cents` | Belongs to a customer and session; contains multiple cart lines and may be associated with a purchase. |
| CartLine | `cart_line_id` | `cart_id`, `sku`, `quantity` greater than or equal to 1, `unit_price_cents` greater than or equal to 0, `line_total_cents` equal to quantity multiplied by unit price | Belongs to one cart. |
| Campaign | `campaign_id` | `name`, `channel`, `starts_at`, `ends_at`, `attribution_window_days`, `status` | Can have multiple message templates and send attempts. |
| MessageTemplate | `template_id` | `campaign_id`, variant (`A`, `B`), `channel`, unique `message_key`, `body` | Belongs to one campaign. |
| SendAttempt | `send_id` | Unique `message_id`, customer, cart, campaign, and template IDs; `channel`, `scheduled_at`, `decision`, `reason` | Belongs to a customer, cart, campaign, and template; can have multiple send events. |
| SendEvent | `event_id` | `send_id`, `event_type`, `occurred_at` | Belongs to one send attempt. Events preserve the message activity history. |
| Order | `order_id` | `customer_id`, optional `recovered_cart_id`, `created_at`, `total_cents`, `status` | Belongs to one customer and may reference a recovered cart. |
| Attribution | `attribution_id` | `order_id`, `send_id`, `attributed_at`, `credit_cents`, `model` | References one order and one send attempt. The baseline model allows at most one credited attribution per order. |

## Allowed Values

### Cart status

- `active`
- `abandoned`
- `recovered`
- `purchased`

### Send decision

- `sent`
- `suppressed`

### Send event types

- `sent`
- `delivered`
- `opened`
- `clicked`
- `bounced`
- `unsubscribed`

### Customer region

- `NA`
- `EU`
- `APAC`

### Consent channel and status

| Field | Allowed values |
|---|---|
| `channel` | `email`, `sms` |
| `status` | `opt_in`, `opt_out` |

### Message template variant

- `A`
- `B`

## Data Integrity Rules

1. Entity identifiers must be unique and stable.
2. Foreign-key references must point to existing records.
3. Session end times must not precede session start times.
4. Cart-line quantities must be positive integers.
5. Cart-line totals must equal quantity multiplied by unit price.
6. Monetary values must use integer cents.
7. Consent eligibility is evaluated using the effective consent for the customer and channel at send time.
8. Send decisions must respect the implemented abandonment and frequency-cap rules.
9. Attribution must follow the configured attribution window and qualifying-click rules.
10. Intentional anomalies are identified using `issue_type` where applicable and are evaluated separately from unexpected integrity errors.

## Time and Attribution

Timestamps use UTC ISO 8601 representations. The engine uses the effective consent state at the time of a send decision and applies the attribution rules documented in the project README.

The baseline attribution model allows at most one credited attribution per order. Attribution records connect orders to the send attempts that qualify under the implemented rules.

## Anomaly Labels

The generated dataset contains four intentional anomaly categories:

1. A message sent after opt-out.
2. A cart marked abandoned after purchase.
3. An order attributed more than once across campaigns.
4. A stale cart total after a quantity update.

These records are included to exercise validation behavior. Their labels are maintained separately from the normal campaign decision inputs.

## Related Documentation

- [`README.md`](../README.md) — Project overview, setup, business rules, API, and execution instructions.
- [`PROMPT_HISTORY.md`](../PROMPT_HISTORY.md) — AI assistance disclosure and prompt history.
