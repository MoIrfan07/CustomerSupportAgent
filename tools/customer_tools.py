import re  #importing the regular expression module to use for string manipulation and pattern matching

CUSTOMERS = { #dictionary containing customer information
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
    "CUST-1003": {
            "customer_id": "CUST-1003",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "status": "Active",
            "plan": "Premium",
        },
}


def normalize_customer_input(   #normalizes customer input by stripping whitespace, converting to lowercase, and removing spaces, hyphens, and underscores
    value: str
) -> str:

    value = value.strip().lower()

    return re.sub(
        r"[\s\-_]+",
        "",
        value,
    )


def resolve_customer(  #Take whatever the user typed and figure out which customer they mean.
    customer_reference: str
) -> dict:

    normalized_input = ( 
        normalize_customer_input(
            customer_reference
        )
    )

    for customer in CUSTOMERS.values(): #iterates through each customer record in 
#the CUSTOMERS dictionary to find a match for the normalized input

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
        if normalized_input == normalized_id:   #checks if the normalized input matches the normalized customer ID

            return {
                "customer_id": customer["customer_id"],
                "name": customer["name"],
                "match_type": "customer_id",
            }

        # Ahmed Khan
        # Ahmed-Khan
        if normalized_input == normalized_name: #checks if the normalized input matches the normalized customer name

            return {
                "customer_id": customer["customer_id"],
                "name": customer["name"],
                "match_type": "full_name",
            }

        # 1001
        if (  #checks if the normalized input is a digit and if it matches the end of the normalized customer ID, 
#which allows for partial matching of customer IDs
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
) -> dict:  # retrieves the complete customer record

    resolved = resolve_customer(
        customer_id
    )  # uses the common customer-resolution logic

    if "error" in resolved:  # customer could not be identified
        return resolved

    return CUSTOMERS[
        resolved["customer_id"]
    ]  # returns the complete customer record