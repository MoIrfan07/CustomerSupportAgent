def get_customer(customer_id: str) -> dict:
    """
    Look up a customer from our temporary
    customer database.
    """

    customers = {
        "CUST-1001": {
            "customer_id": "CUST-1001",
            "name": "Ahmed Khan",
            "email": "ahmed@example.com",
            "status": "Active",
            "plan": "Premium",
        },
        "CUST-1002": {
            "customer_id": "CUST-1002",
            "name": "John Smith",
            "email": "john@example.com",
            "status": "Suspended",
            "plan": "Basic",
        },
    }

    customer = customers.get(customer_id)

    if not customer:
        return {
            "error": f"Customer {customer_id} was not found."
        }

    return customer