# app/examples.py

FEW_SHOTS = [
    {
        "q": "Show total orders per city.",
        "sql": (
            "SELECT c.city, COUNT(*) AS total_orders "
            "FROM orders o JOIN customers c ON o.customer_id = c.customer_id "
            "GROUP BY c.city;"
        ),
    },
    {
        "q": "List all delivered orders with customer name.",
        "sql": (
            "SELECT o.order_id, c.name, o.amount_paid, o.order_date "
            "FROM orders o JOIN customers c ON o.customer_id = c.customer_id "
            "WHERE o.status = 'delivered';"
        ),
    },
]

def few_shot_block() -> str:
    # Formats as:
    # Q: ...
    # A: SELECT ...
    lines = []
    for ex in FEW_SHOTS:
        lines.append(f"Q: {ex['q']}\nA: {ex['sql']}")
    return "\n".join(lines)