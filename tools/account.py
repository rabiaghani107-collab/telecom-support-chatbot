"""
Account management tools — profile lookup, status changes, ticket management.
"""

from langchain_core.tools import tool
from data.database import get_connection


@tool
def get_customer_profile(customer_id: str) -> str:
    """Retrieve a customer's profile and current plan.

    Args:
        customer_id: The customer ID (e.g. CUST-1001).

    Returns:
        Profile summary with plan details.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT c.*, p.plan_name, p.monthly_price "
            "FROM customers c LEFT JOIN plans p ON c.plan_id = p.plan_id "
            "WHERE c.customer_id = ?",
            (customer_id,),
        )
        row = cur.fetchone()
        if not row:
            return f"Customer {customer_id} not found in our system."
        status_emoji = "🟢" if row["account_status"] == "active" else "🔴"
        return (
            f"👤 Customer Profile\n"
            f"  ID: {row['customer_id']}\n"
            f"  Name: {row['name']}\n"
            f"  Email: {row['email']}\n"
            f"  Phone: {row['phone']}\n"
            f"  Plan: {row['plan_name']} (${row['monthly_price']:.2f}/mo)\n"
            f"  Status: {status_emoji} {row['account_status'].capitalize()}\n"
            f"  Member since: {row['created_at']}"
        )
    finally:
        conn.close()


@tool
def lookup_customer_by_name(name: str) -> str:
    """Search for a customer by name (partial match).

    Args:
        name: Full or partial customer name.

    Returns:
        Matching customer IDs and names.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT customer_id, name, account_status FROM customers WHERE name LIKE ?",
            (f"%{name}%",),
        )
        rows = cur.fetchall()
        if not rows:
            return f"No customers found matching '{name}'."
        lines = [f"🔍 Customers matching '{name}':"]
        for r in rows:
            lines.append(f"  • {r['customer_id']} — {r['name']} ({r['account_status']})")
        return "\n".join(lines)
    finally:
        conn.close()


@tool
def create_support_ticket(customer_id: str, category: str, description: str) -> str:
    """Create a new support ticket for a customer.

    Args:
        customer_id: The customer ID.
        category: Ticket category — billing, technical, account, or general.
        description: Description of the issue.

    Returns:
        Confirmation with ticket ID.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verify customer exists
        cur.execute("SELECT 1 FROM customers WHERE customer_id = ?", (customer_id,))
        if not cur.fetchone():
            return f"Customer {customer_id} not found. Cannot create ticket."
        cur.execute(
            "INSERT INTO support_tickets (customer_id, category, description) VALUES (?,?,?)",
            (customer_id, category, description),
        )
        conn.commit()
        ticket_id = cur.lastrowid
        return (
            f"🎫 Support ticket created successfully!\n"
            f"  Ticket ID: #{ticket_id}\n"
            f"  Customer: {customer_id}\n"
            f"  Category: {category}\n"
            f"  Status: Open\n"
            f"  Our team will review this shortly."
        )
    finally:
        conn.close()


@tool
def get_open_tickets(customer_id: str) -> str:
    """List open support tickets for a customer.

    Args:
        customer_id: The customer ID.

    Returns:
        Open tickets summary.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM support_tickets WHERE customer_id = ? AND status = 'open' "
            "ORDER BY created_at DESC",
            (customer_id,),
        )
        rows = cur.fetchall()
        if not rows:
            return f"No open tickets for {customer_id}."
        lines = [f"🎫 Open Tickets for {customer_id}:"]
        for r in rows:
            lines.append(
                f"  #{r['ticket_id']} [{r['category']}] — {r['description']}\n"
                f"      Created: {r['created_at']}"
            )
        return "\n".join(lines)
    finally:
        conn.close()
