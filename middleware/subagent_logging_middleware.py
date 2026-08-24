from datetime import datetime

from langchain.agents.middleware import AgentMiddleware


class SubagentLoggingMiddleware(AgentMiddleware): #custom middleware for logging subagent requests and responses in the customer support agent

    def _timestamp(self) -> str:
        return datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    async def awrap_tool_call(  
        self,
        request,
        handler,
    ): #intercepts every tool call before the tool actually runs, allowing for logging of subagent requests and responses

        tool_name = request.tool_call.get(
            "name",
            "unknown",
        )#gets the name of the tool being called, defaults to "unknown" if not present

        args = request.tool_call.get(
            "args",
            {},
        ) #args are the parameters passed to the tool call, which may include information about the subagent being invoked

      

        if tool_name == "task": #checks if the tool being called is a "task", which indicates that a subagent is being invoked
#This is DeepAgents --- subagent delegation
            subagent_name = args.get(
                "subagent_type",
                "unknown",
            ) #gets the type of subagent being invoked from the tool call args, defaults to "unknown" if not present

            print()
            print(
                f"[{self._timestamp()}] "
                f"[SUBAGENT] START → {subagent_name}"
            ) #prints the start of a subagent request, indicating which subagent is being invoked

            try: 

                result = await handler(
                    request
                ) #calls the next handler in the middleware chain, which will eventually invoke the subagent and return its result

                print(
                    f"[{self._timestamp()}] "
                    f"[SUBAGENT] END   → {subagent_name}"
                )

                return result

            except Exception as e:

                print(
                    f"[{self._timestamp()}] "
                    f"[SUBAGENT] ERROR → {subagent_name}"
                )

                print(
                    f"[SUBAGENT] {str(e)}"
                )

                raise

      

        print(
            f"[{self._timestamp()}] "
            f"[TOOL] {tool_name}"
        ) #prints the name of the tool being called, which may or may not be a subagent invocation

        try:

            result = await handler(
                request
            )

            print(
                f"[{self._timestamp()}] "
                f"[TOOL] END → {tool_name}"
            )

            return result

        except Exception as e:

            print(
                f"[{self._timestamp()}] "
                f"[TOOL] ERROR → {tool_name}"
            )

            print(
                f"[TOOL] {str(e)}"
            )

            raise