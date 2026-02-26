from __future__ import annotations

from datetime import datetime, timezone


def _indian_comma_grouping(n: int) -> str:
    """Format an integer with Indian comma grouping: 1,23,456."""
    s = str(n)
    if len(s) <= 3:
        return s
    # Last 3 digits, then groups of 2
    last3 = s[-3:]
    rest = s[:-3]
    groups = []
    while rest:
        groups.append(rest[-2:])
        rest = rest[:-2]
    groups.reverse()
    return ",".join(groups) + "," + last3


def format_inr(value: float, show_sign: bool = False) -> str:
    """Format as Indian Rupees: '₹1,23,456'."""
    abs_val = abs(value)
    sign = "+" if value >= 0 and show_sign else ("-" if value < 0 else "")
    formatted = _indian_comma_grouping(round(abs_val))
    return f"{sign}₹{formatted}"


def format_lakhs_crores(value: float) -> str:
    """Format in lakhs/crores: '₹12.34L' or '₹1.23Cr'."""
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 10_000_000:
        return f"{sign}₹{abs_val / 10_000_000:.2f}Cr"
    elif abs_val >= 100_000:
        return f"{sign}₹{abs_val / 100_000:.2f}L"
    elif abs_val >= 1000:
        return f"{sign}₹{abs_val / 1000:.1f}K"
    return f"{sign}₹{round(abs_val)}"


def format_percent(value: float, show_sign: bool = False) -> str:
    """Format percentage: '+5.25%'."""
    sign = "+" if value >= 0 and show_sign else ""
    return f"{sign}{value:.2f}%"


def time_ago(dt: datetime) -> str:
    """Human-readable relative time: '5m ago', '2h ago'."""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    diff_mins = int(diff.total_seconds() / 60)
    diff_hours = int(diff.total_seconds() / 3600)

    if diff_mins < 1:
        return "Just now"
    if diff_mins < 60:
        return f"{diff_mins}m ago"
    if diff_hours < 24:
        return f"{diff_hours}h ago"
    return dt.strftime("%d-%b")
