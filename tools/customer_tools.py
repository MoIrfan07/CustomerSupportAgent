import re


CUSTOMERS = {
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


def normalize_customer_input(
    value: str
) -> str:

    value = value.strip().lower()

    return re.sub(
        r"[\s\-_]+",
        "",
        value,
    )


def resolve_customer(
    customer_reference: str
) -> dict:

    normalized_input = (
        normalize_customer_input(
            customer_reference
        )
    )

    for customer in CUSTOMERS.values():

        normalized_id = (
            normalize_customer_input(
                customer["customer_id"]
            )
        )

        normalized_name = (
            normalize_customer_input(
                customer["name"]
            )
        )

        # CUST-1001
        # CUST 1001
        # cust1001
        if normalized_input == normalized_id:

            return {
                "customer_id": customer["customer_id"],
                "name": customer["name"],
                "match_type": "customer_id",
            }

        # Ahmed Khan
        # Ahmed-Khan
        if normalized_input == normalized_name:

            return {
                "customer_id": customer["customer_id"],
                "name": customer["name"],
                "match_type": "full_name",
            }

        # 1001
        if (
            normalized_input.isdigit()
            and normalized_id.endswith(
                normalized_input
            )
        ):

            return {
                "customer_id": customer["customer_id"],
                "name": customer["name"],
                "match_type": "customer_number",
            }

        # Ahmed
        first_name = (
            normalized_name.split()[0]
        )

        if normalized_input == first_name:

            return {
                "customer_id": customer["customer_id"],
                "name": customer["name"],
                "match_type": "first_name",
            }

    return {
        "error": (
            f"Could not identify customer "
            f"'{customer_reference}'."
        )
    }


def get_customer(
    customer_id: str
) -> dict:

    normalized_input = (
        normalize_customer_input(
            customer_id
        )
    )

    for customer in CUSTOMERS.values():

        normalized_id = (
            normalize_customer_input(
                customer["customer_id"]
            )
        )

        normalized_name = (
            normalize_customer_input(
                customer["name"]
            )
        )

        if normalized_input == normalized_id:
            return customer

        if normalized_input == normalized_name:
            return customer

        if (
            normalized_input.isdigit()
            and normalized_id.endswith(
                normalized_input
            )
        ):
            return customer

        first_name = (
            normalized_name.split()[0]
        )

        if normalized_input == first_name:
            return customer

    return {
        "error": (
            f"Customer '{customer_id}' "
            "was not found."
        )
    }