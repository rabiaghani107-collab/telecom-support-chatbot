"""
Plan information tools — list plans, get details, compare plans.
"""

from langchain_core.tools import tool
from data.database import get_connection


@tool
def list_available_plans() -> str:
    """List all available TelcoMax plans with pricing.

    Returns:
        Summary of every available plan.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM plans ORDER BY monthly_price ASC")
        rows = cur.fetchall()
        if not rows:
            return "No plans found in the system."
        lines = ["📋 Available TelcoMax Plans:\n"]
        for r in rows:
            data = "Unlimited" if r["data_limit_gb"] >= 999 else f"{r['data_limit_gb']} GB"
            lines.append(
                f"• {r['plan_name']} ({r['plan_type']}) — ${r['monthly_price']:.2f}/mo\n"
                f"    Data: {data} | Calls: {r['call_minutes']} min | SMS: {r['sms_limit']}\n"
                f"    Features: {r['features']}\n"
            )
        return "\n".join(lines)
    finally:
        conn.close()


@tool
def get_plan_details(plan_name: str) -> str:
    """Get detailed information about a specific plan.

    Args:
        plan_name: Full or partial plan name (e.g. 'Premium', 'basic').

    Returns:
        Detailed plan information.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM plans WHERE plan_name LIKE ?",
            (f"%{plan_name}%",),
        )
        row = cur.fetchone()
        if not row:
            return f"No plan matching '{plan_name}' found. Use list_available_plans to see all options."
        data = "Unlimited" if row["data_limit_gb"] >= 999 else f"{row['data_limit_gb']} GB"
        calls = "Unlimited" if row["call_minutes"] >= 9999 else f"{row['call_minutes']} minutes"
        sms = "Unlimited" if row["sms_limit"] >= 9999 else str(row["sms_limit"])
        return (
            f"📱 {row['plan_name']}\n"
            f"  Type: {row['plan_type'].capitalize()}\n"
            f"  Price: ${row['monthly_price']:.2f}/month\n"
            f"  Data: {data}\n"
            f"  Calls: {calls}\n"
            f"  SMS: {sms}\n"
            f"  Features: {row['features']}"
        )
    finally:
        conn.close()


@tool
def compare_plans(plan_a: str, plan_b: str) -> str:
    """Compare two TelcoMax plans side by side.

    Args:
        plan_a: First plan name (or partial name).
        plan_b: Second plan name (or partial name).

    Returns:
        Side-by-side comparison.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        results = []
        for name in [plan_a, plan_b]:
            cur.execute("SELECT * FROM plans WHERE plan_name LIKE ?", (f"%{name}%",))
            row = cur.fetchone()
            if not row:
                return f"Plan '{name}' not found."
            results.append(row)
        a, b = results
        def fmt(r):
            data = "Unlimited" if r["data_limit_gb"] >= 999 else f"{r['data_limit_gb']} GB"
            calls = "Unlimited" if r["call_minutes"] >= 9999 else f"{r['call_minutes']} min"
            return data, calls
        ad, ac = fmt(a)
        bd, bc = fmt(b)
        return (
            f"⚖️ Plan Comparison\n"
            f"{'':>18} {'|':>1} {a['plan_name']:<25} | {b['plan_name']:<25}\n"
            f"{'Price':>18} | ${a['monthly_price']:<24.2f} | ${b['monthly_price']:<24.2f}\n"
            f"{'Data':>18} | {ad:<25} | {bd:<25}\n"
            f"{'Calls':>18} | {ac:<25} | {bc:<25}\n"
            f"{'Features':>18} | {a['features']:<25} | {b['features']:<25}"
        )
    finally:
        conn.close()
