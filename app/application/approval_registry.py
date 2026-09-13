from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from threading import Lock


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """
    Represents a human approval request for a sensitive operation.

    The request remains in the registry while LangGraph is paused.
    Once a decision is submitted, the decision is stored on the
    same approval record so the graph can safely resume using
    the original approval ID.
    """

    approval_id: str
    username: str
    role: str
    customer_id: str | None
    thread_id: str
    tool_name: str
    tool_call_id: str | None
    created_at: datetime
    decision: bool | None = None
    decided_at: datetime | None = None


class ApprovalRegistry:
    """
    Application-level registry for human approval requests.

    The registry stores approval metadata and the human decision.
    It does not execute business operations and does not itself
    resume LangGraph.

    The current implementation is intentionally in-memory and
    suitable for the current single-process application.

    In a production multi-instance deployment this abstraction
    should be backed by a shared persistent store such as Redis
    or a database.
    """

    def __init__(self) -> None:
        self._approvals: dict[str, ApprovalRequest] = {}
        self._lock = Lock()

    def create(
        self,
        *,
        approval_id: str,
        username: str,
        role: str,
        customer_id: str | None,
        thread_id: str,
        tool_name: str,
        tool_call_id: str | None = None,
    ) -> ApprovalRequest:
        """
        Create and store a new approval request.

        tool_call_id identifies the exact LangGraph tool call that
        caused the approval. This allows the same approval to be
        found reliably when the graph is replayed.
        """

        approval = ApprovalRequest(
            approval_id=approval_id,
            username=username,
            role=role,
            customer_id=customer_id,
            thread_id=thread_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            created_at=datetime.now(timezone.utc),
        )

        with self._lock:
            self._approvals[approval_id] = approval

        return approval

    def get(
        self,
        approval_id: str,
    ) -> ApprovalRequest | None:
        """
        Retrieve an approval request by ID.
        """

        with self._lock:
            return self._approvals.get(approval_id)

    def find_for_tool_call(
        self,
        *,
        thread_id: str,
        tool_name: str,
        tool_call_id: str | None,
    ) -> ApprovalRequest | None:
        """
        Find the approval belonging to a specific LangGraph tool call.

        The lookup intentionally does NOT require decision to be None.

        This is important because the API stores the human decision
        BEFORE Command(resume=...) is called. When LangGraph replays
        the interrupted execution, the approval therefore already
        contains the decision.

        Matching the tool_call_id prevents two separate sensitive
        operations using the same tool in the same thread from
        accidentally sharing an approval.
        """

        with self._lock:
            for approval in self._approvals.values():
                if (
                    approval.thread_id == thread_id
                    and approval.tool_name == tool_name
                    and approval.tool_call_id == tool_call_id
                ):
                    return approval

        return None

    def find_pending(
        self,
        *,
        thread_id: str,
        tool_name: str,
    ) -> ApprovalRequest | None:
        """
        Find an existing pending approval for the same LangGraph
        thread and sensitive tool.

        This method is retained for compatibility with existing
        code and tests.

        Unlike find_for_tool_call(), this method only returns an
        approval that has not received a decision yet.
        """

        with self._lock:
            for approval in self._approvals.values():
                if (
                    approval.thread_id == thread_id
                    and approval.tool_name == tool_name
                    and approval.decision is None
                ):
                    return approval

        return None

    def set_decision(
        self,
        approval_id: str,
        approved: bool,
    ) -> ApprovalRequest | None:
        """
        Atomically record the first human decision.

        Returns the updated approval when the decision is recorded
        for the first time.

        If the approval already has a decision, the existing record
        is returned unchanged.

        The caller can therefore compare the returned record's
        decision/decided_at state to determine whether this request
        made the first decision.
        """

        with self._lock:
            approval = self._approvals.get(approval_id)

            if approval is None:
                return None

            if approval.decision is not None:
                return approval

            updated = replace(
                approval,
                decision=approved,
                decided_at=datetime.now(timezone.utc),
            )

            self._approvals[approval_id] = updated

            return updated

    def remove(
        self,
        approval_id: str,
    ) -> ApprovalRequest | None:
        """
        Consume and remove an approval request.

        This should happen after the resumed LangGraph operation
        has completed successfully.
        """

        with self._lock:
            return self._approvals.pop(approval_id, None)

    def contains(
        self,
        approval_id: str,
    ) -> bool:
        """
        Check whether an approval request currently exists.
        """

        with self._lock:
            return approval_id in self._approvals

    def clear(self) -> None:
        """
        Remove all approval requests.

        Primarily useful during application shutdown and tests.
        """

        with self._lock:
            self._approvals.clear()
