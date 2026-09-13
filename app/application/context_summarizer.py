from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

logger = logging.getLogger(__name__)


class ContextSummarizer:
    """
    Create a safe, structured summary of conversational context.

    This component is intentionally model-independent.

    It does NOT:
        - call an LLM
        - modify LangGraph state
        - perform authorization
        - approve or reject operations
        - replace authoritative business data

    Its responsibility is only to identify information that can be
    carried forward when older conversational messages are compressed.
    """

    PROTECTED_FIELDS = {
        "username",
        "user_role",
        "customer_id",
        "thread_id",
        "approval_id",
        "approval_state",
        "tool_call_id",
    }

    def summarize(
        self,
        state: dict[str, Any],
        *,
        messages_to_summarize: list[Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build a structured context summary.

        Args:
            state:
                Current agent state.

            messages_to_summarize:
                Optional subset of messages that should be summarized.
                If omitted, all messages are considered.

        Returns:
            A structured dictionary containing:
                - protected_context
                - active_workflow
                - conversation_history
                - tool_activity
        """
        messages = messages_to_summarize

        if messages is None:
            messages = state.get("messages", [])

        if not isinstance(messages, list):
            logger.warning(
                "CONTEXT SUMMARIZER | invalid messages state | type=%s",
                type(messages).__name__,
            )
            messages = []

        protected_context = self._extract_protected_context(state)
        active_workflow = self._extract_active_workflow(state, messages)
        conversation_history = self._summarize_conversation(messages)
        tool_activity = self._summarize_tool_activity(messages)

        result = {
            "protected_context": protected_context,
            "active_workflow": active_workflow,
            "conversation_history": conversation_history,
            "tool_activity": tool_activity,
        }

        logger.info(
            "CONTEXT SUMMARIZER | messages=%s | protected_fields=%s | "
            "conversation_items=%s | tool_items=%s",
            len(messages),
            list(protected_context.keys()),
            len(conversation_history),
            len(tool_activity),
        )

        return result

    def _extract_protected_context(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Extract security and identity information without transforming it.

        These values are copied exactly from state when present.
        """
        protected: dict[str, Any] = {}

        for field_name in self.PROTECTED_FIELDS:
            value = state.get(field_name)

            if value is not None:
                protected[field_name] = value

        approval_context = state.get("approval_context")

        if approval_context is not None:
            protected["approval_context"] = approval_context

        return protected

    def _extract_active_workflow(
        self,
        state: dict[str, Any],
        messages: list[Any],
    ) -> dict[str, Any]:
        """
        Capture information that may be relevant to an active workflow.

        This does not decide whether an operation is authorized or safe.
        It only records observable workflow information.
        """
        workflow: dict[str, Any] = {}

        approval_state = state.get("approval_state")

        if approval_state is not None:
            workflow["approval_state"] = approval_state

        pending_approval = state.get("pending_approval")

        if pending_approval is not None:
            workflow["pending_approval"] = pending_approval

        interrupt_state = state.get("__interrupt__")

        if interrupt_state:
            workflow["interrupt_present"] = True

        active_tool_calls = self._extract_active_tool_calls(messages)

        if active_tool_calls:
            workflow["active_tool_calls"] = active_tool_calls

        return workflow

    def _summarize_conversation(
        self,
        messages: list[Any],
    ) -> list[dict[str, str]]:
        """
        Produce a compact representation of conversational messages.

        This is deliberately extractive rather than generative.

        We do not ask an LLM to rewrite the conversation at this stage,
        because an LLM-generated summary could accidentally alter
        security-sensitive or business-critical information.
        """
        conversation: list[dict[str, str]] = []

        for message in messages:
            if isinstance(message, HumanMessage):
                content = self._content_to_text(message.content)

                if content:
                    conversation.append(
                        {
                            "role": "user",
                            "content": content,
                        }
                    )

            elif isinstance(message, AIMessage):
                content = self._content_to_text(message.content)

                if content:
                    conversation.append(
                        {
                            "role": "assistant",
                            "content": content,
                        }
                    )

        return conversation

    def _summarize_tool_activity(
        self,
        messages: list[Any],
    ) -> list[dict[str, Any]]:
        """
        Preserve observable tool activity.

        Tool results are not rewritten or interpreted. Their original
        content is retained so a later compression layer can decide
        how to handle them safely.
        """
        tool_activity: list[dict[str, Any]] = []

        for message in messages:
            if not isinstance(message, ToolMessage):
                continue

            tool_name = getattr(message, "name", None)
            tool_call_id = getattr(message, "tool_call_id", None)

            item: dict[str, Any] = {
                "tool_name": tool_name,
                "tool_call_id": tool_call_id,
                "content": self._content_to_text(message.content),
            }

            tool_activity.append(item)

        return tool_activity

    def _extract_active_tool_calls(
        self,
        messages: list[Any],
    ) -> list[dict[str, Any]]:
        """
        Extract currently observable tool calls from AI messages.

        Tool calls are retained as structured data rather than being
        converted into prose.
        """
        tool_calls: list[dict[str, Any]] = []

        for message in messages:
            if not isinstance(message, AIMessage):
                continue

            calls = getattr(message, "tool_calls", None)

            if not isinstance(calls, list):
                continue

            for call in calls:
                if not isinstance(call, dict):
                    continue

                tool_calls.append(
                    {
                        "id": call.get("id"),
                        "name": call.get("name"),
                        "args": call.get("args"),
                    }
                )

        return tool_calls

    @staticmethod
    def _content_to_text(content: Any) -> str:
        """
        Convert message content into text without attempting to interpret it.
        """
        if content is None:
            return ""

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            return str(content)

        return str(content)
