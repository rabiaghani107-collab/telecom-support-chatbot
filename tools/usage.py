"""
Usage tracking tools — data, calls, SMS consumption analysis.
"""

from langchain_core.tools import tool
from data.database import get_connection


@tool
def get_usage_summary(customer_id: str, days: int = 7) -> str:
    """Get a summary of data, call, and SMS usage over the specified period.

    Args:
        customer_id: The customer ID.
        days: Number of past days to summarise (default 7).

    Returns:
        Aggregated usage statistics.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT SUM(data_used_gb) as total_data, "
            "SUM(calls_minutes) as total_calls, "
            "SUM(sms_sent) as total_sms, "
            "COUNT(*) as record_days "
            "FROM usage_records WHERE customer_id = ? "
            "ORDER BY record_date DESC LIMIT ?",
            (customer_id, days),
        )
        row = cur.fetchone()
        if not row or row["record_days"] == 0:
            return f"No usage records found for {customer_id}."

        # Fetch plan limits for context
        cur.execute(
            "SELECT p.data_limit_gb, p.call_minutes, p.sms_limit, p.plan_name "
            "FROM customers c JOIN plans p ON c.plan_id = p.plan_id "
            "WHERE c.customer_id = ?",
            (customer_id,),
        )
        plan = cur.fetchone()
        plan_info = ""
        if plan:
            data_pct = (row["total_data"] / plan["data_limit_gb"] * 100) if plan["data_limit_gb"] > 0 else 0
            plan_info = (
                f"\n  📊 Plan: {plan['plan_name']}\n"
                f"  Data used: {data_pct:.1f}% of {plan['data_limit_gb']} GB limit"
            )

        return (
            f"📈 Usage Summary for {customer_id} (last {row['record_days']} days):\n"
            f"  Data Used: {row['total_data']:.2f} GB\n"
            f"  Calls: {row['total_calls']} minutes\n"
            f"  SMS Sent: {row['total_sms']}"
            f"{plan_info}"
        )
    finally:
        conn.close()


@tool
def get_daily_usage(customer_id: str) -> str:
    """Get daily usage breakdown for the last 7 days.

    Args:
        customer_id: The customer ID.

    Returns:
        Day-by-day usage table.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM usage_records WHERE customer_id = ? "
            "ORDER BY record_date DESC LIMIT 7",
            (customer_id,),
        )
        rows = cur.fetchall()
        if not rows:
            return f"No daily usage records for {customer_id}."
        lines = [f"📅 Daily Usage for {customer_id}:"]
        lines.append(f"  {'Date':<12} {'Data (GB)':>10} {'Calls (min)':>12} {'SMS':>6}")
        lines.append("  " + "-" * 44)
        for r in rows:
            lines.append(
                f"  {r['record_date']:<12} {r['data_used_gb']:>10.2f} "
                f"{r['calls_minutes']:>12} {r['sms_sent']:>6}"
            )
        return "\n".join(lines)
    finally:
        conn.close()
