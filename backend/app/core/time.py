from datetime import datetime, timezone


def now_utc_naive() -> datetime:
    """Current UTC time as a naive datetime.

    The database columns are naive ``DateTime`` (no timezone), so every
    timestamp written must stay naive UTC. ``datetime.utcnow()`` is
    deprecated since Python 3.12 — use this helper instead.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
