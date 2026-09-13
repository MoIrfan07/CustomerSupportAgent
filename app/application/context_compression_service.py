from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage

from app.application.business_fact_extractor import (
    BusinessFactExtractor,
)
from app.application.context_compression_policy import (
    ContextCompressionPolicy,
)
from app.application.context_message_classifier import (
    ClassifiedMessage,
    ContextMessageClassifier,
)
from app.application.context_summarizer import ContextSummarizer

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ContextCompressionResult:
    """
    Immutable result produced by the compression service.

    The service does not modify the original agent state.
    """

    eligible: bool
    reason: str
    original_message_count: int
    compressed_message_count: int
    preserved_message_count: int
    messages_to_compress: list[BaseMessage]
    preserved_messages: list[BaseMessage]
    summary: dict[str, Any]
    business_facts: list[dict[str, Any]]


class ContextCompressionService:
    """
    Prepare conversational context for future compression.

    This service coordinates:
        - context inspection metrics
        - compression policy
        - message classification
        - deterministic business-fact extraction
        - safe context extraction
        - deterministic compressed-message construction

    It does NOT:
        - modify LangGraph state
        - delete messages from LangGraph state
        - replace messages in LangGraph state
        - call an LLM
        - perform authorization
        - approve or reject operations

    Business tool results are not blindly treated as disposable.
    Their explicitly supported facts are extracted separately so a
    future compression layer can preserve those facts before removing
    verbose historical tool messages.
    """

    def __init__(
        self,
        policy: ContextCompressionPolicy | None = None,
        summarizer: ContextSummarizer | None = None,
        classifier: ContextMessageClassifier | None = None,
        business_fact_extractor: BusinessFactExtractor | None = None,
    ) -> None:
        self.policy = policy if policy is not None else ContextCompressionPolicy()

        self.summarizer = summarizer if summarizer is not None else ContextSummarizer()

        self.classifier = (
            classifier if classifier is not None else ContextMessageClassifier()
        )

        self.business_fact_extractor = (
            business_fact_extractor
            if business_fact_extractor is not None
            else BusinessFactExtractor()
        )

    def prepare(
        self,
        state: dict[str, Any],
        metrics: dict[str, Any],
    ) -> ContextCompressionResult:
        """
        Determine whether compression is appropriate and prepare the
        corresponding compression window.

        The returned result is observational and non-destructive.
        """
        messages = state.get("messages", [])

        if not isinstance(messages, list):
            logger.warning(
                "CONTEXT COMPRESSION | invalid messages state | type=%s",
                type(messages).__name__,
            )
            messages = []

        original_message_count = len(messages)

        if not self.policy.should_compress(metrics, state):
            logger.info(
                "CONTEXT COMPRESSION | not eligible | messages=%s",
                original_message_count,
            )

            return ContextCompressionResult(
                eligible=False,
                reason="compression_not_required_or_blocked",
                original_message_count=original_message_count,
                compressed_message_count=0,
                preserved_message_count=original_message_count,
                messages_to_compress=[],
                preserved_messages=list(messages),
                summary={},
                business_facts=[],
            )

        messages_to_compress = self.policy.compression_window(messages)

        if not messages_to_compress:
            logger.info(
                "CONTEXT COMPRESSION | threshold reached but no "
                "compression window available | messages=%s",
                original_message_count,
            )

            return ContextCompressionResult(
                eligible=False,
                reason="compression_window_empty",
                original_message_count=original_message_count,
                compressed_message_count=0,
                preserved_message_count=original_message_count,
                messages_to_compress=[],
                preserved_messages=list(messages),
                summary={},
                business_facts=[],
            )

        classified_messages = self.classifier.classify_messages(messages_to_compress)

        protected_messages = [
            item.message
            for item in classified_messages
            if not item.is_candidate_for_compression
        ]

        compression_candidates = [
            item.message
            for item in classified_messages
            if item.is_candidate_for_compression
        ]

        business_facts = self._extract_business_facts(classified_messages)

        preserved_messages = list(messages[len(messages_to_compress) :])

        preserved_messages.extend(protected_messages)

        summary = self.summarizer.summarize(
            state,
            messages_to_summarize=compression_candidates,
        )

        if business_facts:
            summary = dict(summary)
            summary["business_facts"] = business_facts

        result = ContextCompressionResult(
            eligible=True,
            reason="compression_ready",
            original_message_count=original_message_count,
            compressed_message_count=len(compression_candidates),
            preserved_message_count=len(preserved_messages),
            messages_to_compress=list(compression_candidates),
            preserved_messages=preserved_messages,
            summary=summary,
            business_facts=business_facts,
        )

        logger.info(
            "CONTEXT COMPRESSION | prepared | original=%s | "
            "compression_candidates=%s | protected=%s | "
            "preserved_recent=%s | business_fact_groups=%s",
            result.original_message_count,
            result.compressed_message_count,
            len(protected_messages),
            len(preserved_messages) - len(protected_messages),
            len(result.business_facts),
        )

        return result

    def build_compressed_messages(
        self,
        result: ContextCompressionResult,
    ) -> list[BaseMessage]:
        """
        Build the deterministic message sequence that would replace the
        compressed historical context.

        This method is pure and non-destructive.

        It does NOT:
            - modify the supplied result
            - modify LangGraph state
            - modify any existing message
            - call an LLM
            - perform authorization
            - perform approval

        The resulting order is:

            1. compression summary
            2. preserved recent context
            3. protected historical business/tool messages

        The preserved context order is intentionally retained from
        prepare(). No additional message reordering is performed here.

        The summary is represented as a SystemMessage because it is
        historical context supplied to the model rather than a new
        user or assistant turn.
        """
        if not result.eligible:
            return list(result.preserved_messages)

        summary_content = self._serialize_summary(result.summary)

        compressed_messages: list[BaseMessage] = [
            SystemMessage(
                content=(
                    "Historical conversation context has been compressed.\n\n"
                    f"{summary_content}"
                )
            )
        ]

        compressed_messages.extend(result.preserved_messages)

        logger.info(
            "CONTEXT COMPRESSION | compressed message set built | "
            "summary=1 | preserved=%s | total=%s",
            len(result.preserved_messages),
            len(compressed_messages),
        )

        return compressed_messages

    @staticmethod
    def _serialize_summary(summary: dict[str, Any]) -> str:
        """
        Convert the structured compression summary into deterministic text.

        The summary is intentionally serialized without another model call.
        """
        if not summary:
            return "No historical summary was produced."

        sections: list[str] = []

        protected_context = summary.get("protected_context")

        if isinstance(protected_context, dict) and protected_context:
            sections.append(
                "PROTECTED CONTEXT:\n"
                + "\n".join(
                    f"- {key}: {value}" for key, value in protected_context.items()
                )
            )

        conversation_summary = summary.get("conversation_summary")

        if conversation_summary:
            sections.append(f"CONVERSATION SUMMARY:\n{conversation_summary}")

        tool_activity = summary.get("tool_activity")

        if isinstance(tool_activity, list) and tool_activity:
            sections.append(
                "HISTORICAL TOOL ACTIVITY:\n"
                + "\n".join(
                    ContextCompressionService._serialize_tool_activity(item)
                    for item in tool_activity
                )
            )

        business_facts = summary.get("business_facts")

        if isinstance(business_facts, list) and business_facts:
            sections.append(
                "BUSINESS FACTS:\n"
                + "\n".join(
                    ContextCompressionService._serialize_business_fact(item)
                    for item in business_facts
                )
            )

        if not sections:
            return "Historical context was compressed."

        return "\n\n".join(sections)

    @staticmethod
    def _serialize_tool_activity(item: Any) -> str:
        if not isinstance(item, dict):
            return f"- {item}"

        tool_name = item.get("tool_name", "unknown")
        tool_call_id = item.get("tool_call_id", "unknown")
        content = item.get("content", "")

        return f"- {tool_name} ({tool_call_id}): {content}"

    @staticmethod
    def _serialize_business_fact(item: Any) -> str:
        if not isinstance(item, dict):
            return f"- {item}"

        tool_name = item.get("tool_name", "unknown")
        tool_call_id = item.get("tool_call_id", "unknown")
        facts = item.get("facts", {})

        return f"- {tool_name} ({tool_call_id}): {facts}"

    def _extract_business_facts(
        self,
        classified_messages: list[ClassifiedMessage],
    ) -> list[dict[str, Any]]:
        """
        Extract deterministic facts from business tool results.

        Only ToolMessage instances classified as business data are
        processed. Unknown or malformed results produce no facts.

        The original ToolMessage is never modified.
        """
        facts: list[dict[str, Any]] = []

        for item in classified_messages:
            if not item.is_business_data:
                continue

            if not isinstance(item.message, ToolMessage):
                continue

            tool_name = getattr(item.message, "name", None)

            extracted = self.business_fact_extractor.extract(
                tool_name,
                item.message.content,
            )

            if not extracted:
                continue

            facts.append(
                {
                    "tool_name": tool_name,
                    "tool_call_id": getattr(
                        item.message,
                        "tool_call_id",
                        None,
                    ),
                    "facts": extracted,
                }
            )

        return facts
