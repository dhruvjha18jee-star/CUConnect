# core/notifications.py
# Per-user Notification Queue with unread count and mark-as-read support.
# Course mapping: Session 7: Queues & Session 15: Heaps and Hash Tables.

import uuid

from core.ds.hash_table import HashTable
from core.ds.queue_ds import Queue
from core.models import Notification, ResourceNotFoundError, UserNotFoundError


class NotificationManager:
    """Stores per-user notifications in FIFO Queues inside a HashTable.

    Supports notifications for connection requests, accepted requests, post likes,
    post comments, and comment replies.
    """

    def __init__(self) -> None:
        """Create empty per-user notification queues and a notification ID lookup table.

        Time: O(1)
        Space: O(1)
        """
        self._queues: HashTable = HashTable(initial_capacity=32)
        self._by_id: HashTable = HashTable(initial_capacity=64)

    def register_user(self, username: str) -> None:
        """Initialize an empty notification Queue for a user.

        Time: O(1) average
        Space: O(1)
        """
        if not self._queues.contains(username):
            self._queues.put(username, Queue())

    def _require_queue(self, username: str) -> Queue:
        """Return a user's notification queue or raise UserNotFoundError."""
        q: Queue | None = self._queues.get(username)
        if q is None:
            raise UserNotFoundError(f"User '{username}' does not exist.")
        return q

    def notify(
        self,
        recipient: str,
        actor: str,
        kind: str,
        message: str,
        created_at: float,
        seq_id: int,
        ref_id: str | None = None,
        notification_id: str | None = None,
        is_read: bool = False,
    ) -> Notification:
        """Create and enqueue a new Notification for `recipient`.

        Time: O(1) average
        Space: O(1)
        """
        queue = self._require_queue(recipient)
        nid = notification_id if notification_id is not None else f"notif_{uuid.uuid4().hex[:10]}"
        notif = Notification(
            notification_id=nid,
            recipient=recipient,
            actor=actor,
            kind=kind,
            message=message,
            ref_id=ref_id,
            created_at=created_at,
            seq_id=seq_id,
            is_read=is_read,
        )
        queue.enqueue(notif)
        self._by_id.put(nid, notif)
        return notif

    def load_notification(self, notif: Notification) -> None:
        """Enqueue a persisted Notification during startup hydration.

        Time: O(1) average
        Space: O(1)
        """
        queue = self._require_queue(notif.recipient)
        queue.enqueue(notif)
        self._by_id.put(notif.notification_id, notif)

    def get_notifications(
        self,
        username: str,
        unread_only: bool = False,
        newest_first: bool = True,
    ) -> list[Notification]:
        """Return notifications for `username` (optionally filtered to unread only).

        Time: O(N_u), where N_u is the number of notifications for `username`
        Space: O(N_u)
        """
        queue = self._require_queue(username)
        items = queue.to_list()
        if unread_only:
            items = [n for n in items if not n.is_read]
        if newest_first:
            items.reverse()
        return items

    def unread_count(self, username: str) -> int:
        """Count unread notifications currently in `username`'s queue.

        Time: O(N_u)
        Space: O(1)
        """
        queue = self._require_queue(username)
        count = 0
        for notif in queue:
            if not notif.is_read:
                count += 1
        return count

    def mark_read(self, username: str, notification_id: str) -> Notification:
        """Mark one specific notification belonging to `username` as read.

        Time: O(1) average
        Space: O(1)
        """
        self._require_queue(username)
        notif: Notification | None = self._by_id.get(notification_id)
        if notif is None or notif.recipient != username:
            raise ResourceNotFoundError(
                f"Notification '{notification_id}' not found for '{username}'."
            )
        notif.is_read = True
        return notif

    def mark_all_read(self, username: str) -> list[str]:
        """Mark every unread notification for `username` as read and return their IDs.

        Time: O(N_u)
        Space: O(N_u)
        """
        queue = self._require_queue(username)
        marked_ids: list[str] = []
        for notif in queue:
            if not notif.is_read:
                notif.is_read = True
                marked_ids.append(notif.notification_id)
        return marked_ids
