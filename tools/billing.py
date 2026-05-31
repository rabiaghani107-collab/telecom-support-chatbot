"""
Billing tools — look up bills, payment status, and outstanding balances.
"""

from langchain_core.tools import tool
from data.database import get_connection


@tool
def get_bill_details(customer_id: str, billing_month: str = "") -> str:
    """Look up billing details for a customer.

    Args:
        customer_id: The customer ID (e.g. CUST-1001).
        billing_month: Optional YYYY-MM filter. If omitted, returns the latest bill.

    Returns:
        Formatted billing information or an error message.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        if billing_month:
            cur.execute(
                "SELECT * FROM bills WHERE customer_id = ? AND billing_month = ?",
                (customer_id, billing_month),
            )
        else:
            cur.execute(
                "SELECT * FROM bills WHERE customer_id = ? ORDER BY billing_month DESC LIMIT 1",
                (customer_id,),
            )
        row = cur.fetchone()
        if not row:
            return f"No bill found for customer {customer_id}" + (
                f" for {billing_month}" if billing_month else ""
            )
        return (
            f"📄 Bill for {row['billing_month']}\n"
            f"  Amount: ${row['amount']:.2f}\n"
            f"  Due Date: {row['due_date']}\n"
            f"  Status: {row['status'].upper()}\n"
            f"  Breakdown: {row['breakdown']}"
        )
    finally:
        conn.close()


@tool
def get_payment_history(customer_id: str) -> str:
    """Retrieve payment history for a customer (last 6 bills).

    Args:
        customer_id: The customer ID.

    Returns:
        Tabulated payment history.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT billing_month, amount, status FROM bills "
            "WHERE customer_id = ? ORDER BY billing_month DESC LIMIT 6",
            (customer_id,),
        )
        rows = cur.fetchall()
        if not rows:
            return f"No payment history found for {customer_id}."
        lines = [f"💳 Payment History for {customer_id}:"]
        for r in rows:
            emoji = "✅" if r["status"] == "paid" else "❌"
            lines.append(f"  {r['billing_month']}  ${r['amount']:.2f}  {emoji} {r['status']}")
        return "\n".join(lines)
    finally:
        conn.close()


@tool
def get_outstanding_balance(customer_id: str) -> str:
    """Check if a customer has any unpaid bills and return total outstanding.

    Args:
        customer_id: The customer ID.

    Returns:
        Outstanding balance summary.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT SUM(amount) as total, COUNT(*) as cnt FROM bills "
            "WHERE customer_id = ? AND status = 'unpaid'",
            (customer_id,),
        )
        row = cur.fetchone()
        if not row or row["cnt"] == 0:
            return f"✅ Customer {customer_id} has no outstanding balance."
        return (
            f"⚠️ Customer {customer_id} has {row['cnt']} unpaid bill(s) "
            f"totalling ${row['total']:.2f}."
        )
    finally:
        conn.close()
