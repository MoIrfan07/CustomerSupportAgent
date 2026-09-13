from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

logger = logging.getLogger(__name__)


class ContextMessageCategory(str, Enum):
    """
    Classification used by the context-compression pipeline.
    """

    USER_MESSAGE = "user_message"
    ASSISTANT_MESSAGE = "assistant_message"
    TOOL_RESULT = "tool_result"
    ACTIVE_TOOL_CALL = "active_tool_call"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ClassifiedMessage:
    """
    Classification result for a single LangChain message.

    The original message is retained unchanged so that classification
    never alters the source conversation.
    """

    message: BaseMessage
    category: ContextMessageCategory
    is_business_data: bool
    is_active_workflow: bool
    is_candidate_for_compression: bool
    reason: str


class ContextMessageClassifier:
    """
    Classify conversation messages before compression.

    This component is deliberately deterministic and model-independent.

    It does NOT:
        - call an LLM
        - modify messages
        - perform authorization
        - decide whether business data is correct
        - delete or replace context

    Its purpose is to provide the compression pipeline with enough
    information to distinguish ordinary conversation from potentially
    important business/tool context.
    """

    BUSINESS_TOOL_NAMES = frozenset(
        {
            "resolve_customer",
            "get_customer",
            "list_customers",
            "get_customer_orders",
            "get_customer_invoices",
            "get_customer_payments",
            "get_customer_tickets",
            "cancel_order",
            "refund_payment",
        }
    )

    SENSITIVE_TOOL_NAMES = frozenset(
        {
            "cancel_order",
            "refund_payment",
        }
    )

    def classify(
        self,
        message: BaseMessage,
    ) -> ClassifiedMessage:
        """
        Classify one message.

        Tool results from known business tools are treated as business
        data and are not immediately considered safe to discard.

        Active tool calls and sensitive operations are treated as
        active workflow context.
        """
        if isinstance(message, ToolMessage):
            return self._classify_tool_result(message)

        if isinstance(message, AIMessage):
            return self._classify_ai_message(message)

        if isinstance(message, HumanMessage):
            return ClassifiedMessage(
                message=message,
                category=ContextMessageCategory.USER_MESSAGE,
                is_business_data=False,
                is_active_workflow=False,
                is_candidate_for_compression=True,
                reason="ordinary_user_message",
            )

        return ClassifiedMessage(
            message=message,
            category=ContextMessageCategory.UNKNOWN,
            is_business_data=False,
            is_active_workflow=False,
            is_candidate_for_compression=False,
            reason="unknown_message_type",
        )

    def classify_messages(
        self,
        messages: list[BaseMessage],
    ) -> list[ClassifiedMessage]:
        """
        Classify an entire message sequence without modifying it.
        """
        if not isinstance(messages, list):
            logger.warning(
                "CONTEXT CLASSIFIER | invalid messages | type=%s",
                type(messages).__name__,
            )
            return []

        return [self.classify(message) for message in messages]

    def _classify_tool_result(
        self,
        message: ToolMessage,
    ) -> ClassifiedMessage:
        tool_name = getattr(message, "name", None)

        if tool_name in self.SENSITIVE_TOOL_NAMES:
            return ClassifiedMessage(
                message=message,
                category=ContextMessageCategory.TOOL_RESULT,
                is_business_data=True,
                is_active_workflow=True,
                is_candidate_for_compression=False,
                reason="sensitive_business_tool_result",
            )

        if tool_name in self.BUSINESS_TOOL_NAMES:
            return ClassifiedMessage(
                message=message,
                category=ContextMessageCategory.TOOL_RESULT,
                is_business_data=True,
                is_active_workflow=False,
                is_candidate_for_compression=False,
                reason="business_tool_result",
            )

        return ClassifiedMessage(
            message=message,
            category=ContextMessageCategory.TOOL_RESULT,
            is_business_data=False,
            is_active_workflow=False,
            is_candidate_for_compression=True,
            reason="non_business_tool_result",
        )

    def _classify_ai_message(
        self,
        message: AIMessage,
    ) -> ClassifiedMessage:
        tool_calls = getattr(message, "tool_calls", None)

        if not isinstance(tool_calls, list) or not tool_calls:
            return ClassifiedMessage(
                message=message,
                category=ContextMessageCategory.ASSISTANT_MESSAGE,
                is_business_data=False,
                is_active_workflow=False,
                is_candidate_for_compression=True,
                reason="ordinary_assistant_message",
            )

        has_business_tool_call = False
        has_sensitive_tool_call = False

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue

            tool_name = tool_call.get("name")

            if tool_name in self.BUSINESS_TOOL_NAMES:
                has_business_tool_call = True

            if tool_name in self.SENSITIVE_TOOL_NAMES:
                has_sensitive_tool_call = True

        if has_sensitive_tool_call:
            return ClassifiedMessage(
                message=message,
                category=ContextMessageCategory.ACTIVE_TOOL_CALL,
                is_business_data=True,
                is_active_workflow=True,
                is_candidate_for_compression=False,
                reason="sensitive_business_tool_call",
            )

        if has_business_tool_call:
            return ClassifiedMessage(
                message=message,
                category=ContextMessageCategory.ACTIVE_TOOL_CALL,
                is_business_data=True,
                is_active_workflow=False,
                is_candidate_for_compression=False,
                reason="business_tool_call",
            )

        return ClassifiedMessage(
            message=message,
            category=ContextMessageCategory.ACTIVE_TOOL_CALL,
            is_business_data=False,
            is_active_workflow=False,
            is_candidate_for_compression=True,
            reason="non_business_tool_call",
        )

    @staticmethod
    def contains_business_data(
        classified_messages: list[ClassifiedMessage],
    ) -> bool:
        """
        Return True when any classified message contains business data.
        """
        return any(item.is_business_data for item in classified_messages)

    @staticmethod
    def contains_active_workflow(
        classified_messages: list[ClassifiedMessage],
    ) -> bool:
        """
        Return True when any classified message belongs to an active
        workflow.
        """
        return any(item.is_active_workflow for item in classified_messages)

    @staticmethod
    def compression_candidates(
        classified_messages: list[ClassifiedMessage],
    ) -> list[ClassifiedMessage]:
        """
        Return only messages currently marked as compression candidates.

        This does not mean they should be deleted. They may still contain
        information that needs to be represented in a future summary.
        """
        return [
            item for item in classified_messages if item.is_candidate_for_compression
        ]

    @staticmethod
    def _tool_call_names(
        message: BaseMessage,
    ) -> list[str]:
        """
        Return tool names from an AI message.

        This helper is intentionally defensive because LangChain message
        structures can contain unexpected values.
        """
        tool_calls: Any = getattr(message, "tool_calls", None)

        if not isinstance(tool_calls, list):
            return []

        names: list[str] = []

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue

            name = tool_call.get("name")

            if isinstance(name, str):
                names.append(name)

        return names