from datetime import datetime, timezone


def parse_dt(s):
    return datetime.fromisoformat(
        s.replace("Z", "+00:00")
    ).astimezone(timezone.utc)


def iso(d):
    return (
        d.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )