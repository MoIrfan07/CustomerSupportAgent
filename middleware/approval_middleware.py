from langchain.agents.middleware import (
    AgentMiddleware,
)

from langgraph.types import interrupt   #used for human approval of sensitive operations


class CustomerApprovalMiddleware(
    AgentMiddleware
):

    SENSITIVE_TOOLS = {
        "refund_payment",
        "cancel_order",
    }    #sensitive operations that require human approval

    async def awrap_tool_call(
        self,
        request,
        handler,
    ):    #intercepts every tool call before the tool actually runs

        tool_name = request.tool_call[
            "name"
        ]   #gets the name of the tool being called
        
        
###normal tools which do not require human approval are allowed to run without interruption

        if tool_name not in self.SENSITIVE_TOOLS:

            return await handler(
                request
            )




        args = request.tool_call.get(
            "args",
            {}
        )   #args are the parameters passed to the tool call

        customer_id = args.get(
            "customer_id",
            "Unknown"
        ) #customer_id is extracted from the tool call args, if not present it defaults to "Unknown"

        payment_id = args.get(
            "payment_id",
            "Unknown"
        ) #same as above but for payment_id

        order_id = args.get(
            "order_id",
            "Unknown"
        )#same as above but for order_id



        # REFUND APPROVAL

        if tool_name == "refund_payment":

            approval_message = (
                "\n"
                "========================================\n"
                "        HUMAN APPROVAL REQUIRED\n"
                "========================================\n"
                f"Action: {tool_name}\n"
                f"Customer: {customer_id}\n"
                f"Payment: {payment_id}\n"
                "\n"
                "This operation is sensitive.\n"
                "Do you approve this action?\n"
                "========================================\n"
            )    #approval message is constructed with details of the sensitive operation for human review



#to approve or reject the sensitive operation, the interrupt function is called with the approval message. It will pause the execution and wait for user input.

        elif tool_name == "cancel_order":

            approval_message = (
                "\n"
                "========================================\n"
                "        HUMAN APPROVAL REQUIRED\n"
                "========================================\n"
                f"Action: {tool_name}\n"
                f"Customer: {customer_id}\n"
                f"Order: {order_id}\n"
                "\n"
                "This operation is sensitive.\n"
                "Do you approve this action?\n"
                "========================================\n"
            )   #simulates a human approval request for cancel_order operation with relevant details

        else:

            approval_message = (
                "Human approval is required "
                "for this operation."
            )   #this is a fallback message in case the tool name is not recognized, but still requires approval.


        approved = interrupt(
            approval_message
        )   #pauses the execution and waits for human approval. The interrupt function will return True if approved, False otherwise.


#NOT APPROVED
        if not approved:

            return {
                "success": False,
                "message": (
                    "The requested action "
                    "was rejected by the user."
                ),
            }

        # APPROVED

        return await handler(
            request
        )