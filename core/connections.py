# core/connections.py
# Directed pending connection request queues and connection lifecycle rules.
# Course mapping: Session 7: Queues & Session 11: Graphs (Directed vs Undirected Edges).

from core.ds.hash_table import HashTable
from core.ds.queue_ds import Queue
from core.graph import SocialGraph
from core.models import (
    AuthorizationError,
    ConnectionRequest,
    ConnectionRuleError,
    ResourceNotFoundError,
    UserNotFoundError,
    ValidationError,
)


class ConnectionManager:
    """Manages pending directed connection requests using per-user incoming/outgoing Queues.

    Why per-user Queues:
    - Requests naturally arrive in chronological FIFO order (oldest awaiting response first).
    - Because a student may accept, reject, or cancel any pending request out of order,
      we use our linked-list Queue's `remove_where` / `remove_value` operation.
    """

    def __init__(self, graph: SocialGraph) -> None:
        """Bind the connection manager to a SocialGraph.

        Time: O(1)
        Space: O(1)
        """
        self._graph = graph
        self._incoming: HashTable = HashTable(initial_capacity=32)
        self._outgoing: HashTable = HashTable(initial_capacity=32)

    def register_user(self, username: str) -> None:
        """Initialize empty incoming and outgoing request queues for a new user.

        Time: O(1) average
        Space: O(1)
        """
        if not self._incoming.contains(username):
            self._incoming.put(username, Queue())
        if not self._outgoing.contains(username):
            self._outgoing.put(username, Queue())

    def _require_queues(self, username: str) -> tuple[Queue, Queue]:
        """Return `(incoming_queue, outgoing_queue)` or raise UserNotFoundError."""
        inc: Queue | None = self._incoming.get(username)
        out: Queue | None = self._outgoing.get(username)
        if inc is None or out is None:
            raise UserNotFoundError(f"User '{username}' does not exist.")
        return inc, out

    def has_pending_request(self, sender: str, receiver: str) -> bool:
        """Return True if a directed pending request exists from `sender` to `receiver`.

        Time: O(deg_pending(sender))
        Space: O(1)
        """
        _, out_q = self._require_queues(sender)
        self._require_queues(receiver)
        for req in out_q:
            if req.receiver == receiver:
                return True
        return False

    def has_any_pending_between(self, user_a: str, user_b: str) -> bool:
        """Return True if a pending request exists in either direction between two users.

        Time: O(deg_pending(user_a) + deg_pending(user_b))
        Space: O(1)
        """
        return self.has_pending_request(user_a, user_b) or self.has_pending_request(user_b, user_a)

    def load_request(self, request: ConnectionRequest) -> None:
        """Load a persisted pending request during startup hydration.

        Time: O(1) average
        Space: O(1)
        """
        _, sender_out = self._require_queues(request.sender)
        receiver_in, _ = self._require_queues(request.receiver)
        sender_out.enqueue(request)
        receiver_in.enqueue(request)

    def send_request(
        self,
        sender: str,
        receiver: str,
        created_at: float,
        seq_id: int,
    ) -> tuple[str, ConnectionRequest]:
        """Send a connection request from `sender` to `receiver`.

        Rules enforced:
        - Unknown sender or receiver raises UserNotFoundError.
        - Self-request raises ValidationError.
        - Already connected raises ConnectionRuleError.
        - Duplicate pending request (sender -> receiver) raises ConnectionRuleError.
        - Reverse pending request (receiver -> sender already pending) auto-accepts:
          removes the reverse pending request and creates the undirected edge immediately.

        Returns `(status, request)` where `status` is either `"pending"` or `"auto_accepted"`.

        Time: O(deg(sender) + deg(receiver) + pending_count)
        Space: O(1)
        """
        _, sender_out = self._require_queues(sender)
        receiver_in, _ = self._require_queues(receiver)

        if sender == receiver:
            raise ValidationError("You cannot send a connection request to yourself.")

        if self._graph.has_edge(sender, receiver):
            raise ConnectionRuleError(f"You are already connected with '{receiver}'.")

        if self.has_pending_request(sender, receiver):
            raise ConnectionRuleError(
                f"A connection request from '{sender}' to '{receiver}' is already pending."
            )

        # Auto-accept rule: if receiver had already requested sender, connect them right away!
        if self.has_pending_request(receiver, sender):
            sender_in, _ = self._require_queues(sender)
            _, receiver_out = self._require_queues(receiver)
            existing = sender_in.remove_where(lambda r: r.sender == receiver and r.receiver == sender)
            receiver_out.remove_where(lambda r: r.sender == receiver and r.receiver == sender)
            self._graph.add_edge(sender, receiver)
            assert existing is not None
            return "auto_accepted", existing

        req = ConnectionRequest(
            sender=sender,
            receiver=receiver,
            created_at=created_at,
            seq_id=seq_id,
        )
        sender_out.enqueue(req)
        receiver_in.enqueue(req)
        return "pending", req

    def accept_request(self, actor: str, sender: str) -> ConnectionRequest:
        """Accept a pending request sent by `sender` to `actor`.

        Only the receiver (`actor`) may accept. If `actor` is actually the sender of a
        reverse request (`actor -> sender`), raises AuthorizationError so the rule is crystal clear.

        Time: O(deg(actor) + deg(sender) + pending_count)
        Space: O(1)
        """
        actor_in, _ = self._require_queues(actor)
        _, sender_out = self._require_queues(sender)

        req = actor_in.remove_where(lambda r: r.sender == sender and r.receiver == actor)
        if req is None:
            if self.has_pending_request(actor, sender):
                raise AuthorizationError("Only the receiver can accept a connection request.")
            raise ResourceNotFoundError(
                f"No pending connection request from '{sender}' to '{actor}'."
            )

        sender_out.remove_value(req)
        self._graph.add_edge(sender, actor)
        return req

    def reject_request(self, actor: str, sender: str) -> ConnectionRequest:
        """Reject a pending request sent by `sender` to `actor`.

        Only the receiver (`actor`) may reject.

        Time: O(pending_count)
        Space: O(1)
        """
        actor_in, _ = self._require_queues(actor)
        _, sender_out = self._require_queues(sender)

        req = actor_in.remove_where(lambda r: r.sender == sender and r.receiver == actor)
        if req is None:
            if self.has_pending_request(actor, sender):
                raise AuthorizationError("Only the receiver can reject a connection request.")
            raise ResourceNotFoundError(
                f"No pending connection request from '{sender}' to '{actor}'."
            )

        sender_out.remove_value(req)
        return req

    def cancel_request(self, actor: str, receiver: str) -> ConnectionRequest:
        """Cancel a pending outgoing request sent by `actor` to `receiver`.

        Only the sender (`actor`) may cancel.

        Time: O(pending_count)
        Space: O(1)
        """
        _, actor_out = self._require_queues(actor)
        receiver_in, _ = self._require_queues(receiver)

        req = actor_out.remove_where(lambda r: r.sender == actor and r.receiver == receiver)
        if req is None:
            if self.has_pending_request(receiver, actor):
                raise AuthorizationError("Only the sender can cancel a connection request.")
            raise ResourceNotFoundError(
                f"No pending outgoing connection request from '{actor}' to '{receiver}'."
            )

        receiver_in.remove_value(req)
        return req

    def remove_connection(self, user_a: str, user_b: str) -> None:
        """Remove an existing accepted undirected connection between `user_a` and `user_b`.

        Time: O(deg(user_a) + deg(user_b))
        Space: O(1)
        """
        self._graph.remove_edge(user_a, user_b)

    def incoming_requests(self, username: str) -> list[ConnectionRequest]:
        """Return all pending incoming requests for `username` in FIFO arrival order.

        Time: O(pending_in)
        Space: O(pending_in)
        """
        inc, _ = self._require_queues(username)
        return inc.to_list()

    def outgoing_requests(self, username: str) -> list[ConnectionRequest]:
        """Return all pending outgoing requests sent by `username` in FIFO order.

        Time: O(pending_out)
        Space: O(pending_out)
        """
        _, out = self._require_queues(username)
        return out.to_list()
