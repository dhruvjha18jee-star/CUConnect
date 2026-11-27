# tests/test_connections.py
# Unit tests for core.connections.ConnectionManager covering all required edge cases.

import unittest

from core.connections import ConnectionManager
from core.graph import SocialGraph
from core.models import (
    AuthorizationError,
    ConnectionRuleError,
    ResourceNotFoundError,
    UserNotFoundError,
    ValidationError,
)


class TestConnectionManager(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = SocialGraph()
        self.cm = ConnectionManager(self.graph)
        for u in ["alice", "bob", "carol", "dave"]:
            self.graph.add_user(u)
            self.cm.register_user(u)

    def test_edge_case_rules(self) -> None:
        # Unknown user
        with self.assertRaises(UserNotFoundError):
            self.cm.send_request("alice", "ghost", 1.0, 1)

        # Self request
        with self.assertRaises(ValidationError):
            self.cm.send_request("alice", "alice", 1.0, 1)

        # Send valid request
        status, _ = self.cm.send_request("alice", "bob", 1.0, 1)
        self.assertEqual(status, "pending")

        # Duplicate request rejected
        with self.assertRaises(ConnectionRuleError):
            self.cm.send_request("alice", "bob", 2.0, 2)

        # Only receiver can accept or reject
        with self.assertRaises(AuthorizationError):
            self.cm.accept_request("alice", "bob")
        with self.assertRaises(AuthorizationError):
            self.cm.reject_request("alice", "bob")

        # Only sender can cancel
        with self.assertRaises(AuthorizationError):
            self.cm.cancel_request("bob", "alice")

        # Receiver accepts -> undirected edge added
        self.cm.accept_request("bob", "alice")
        self.assertTrue(self.graph.has_edge("alice", "bob"))
        self.assertTrue(self.graph.has_edge("bob", "alice"))
        self.assertEqual(self.cm.incoming_requests("bob"), [])
        self.assertEqual(self.cm.outgoing_requests("alice"), [])

        # Request to already connected user fails
        with self.assertRaises(ConnectionRuleError):
            self.cm.send_request("alice", "bob", 3.0, 3)

        # Removing connection removes both directions
        self.cm.remove_connection("alice", "bob")
        self.assertFalse(self.graph.has_edge("alice", "bob"))
        self.assertFalse(self.graph.has_edge("bob", "alice"))

    def test_reverse_request_auto_accepts(self) -> None:
        status1, _ = self.cm.send_request("bob", "alice", 1.0, 1)
        self.assertEqual(status1, "pending")

        # Alice sends a request to Bob while Bob -> Alice is pending => auto-accept!
        status2, _ = self.cm.send_request("alice", "bob", 2.0, 2)
        self.assertEqual(status2, "auto_accepted")
        self.assertTrue(self.graph.has_edge("alice", "bob"))
        self.assertEqual(self.cm.incoming_requests("alice"), [])
        self.assertEqual(self.cm.outgoing_requests("bob"), [])

    def test_out_of_order_accept_reject_cancel(self) -> None:
        self.cm.send_request("alice", "dave", 1.0, 1)
        self.cm.send_request("bob", "dave", 2.0, 2)
        self.cm.send_request("carol", "dave", 3.0, 3)

        # Dave rejects middle request (bob) out of order
        self.cm.reject_request("dave", "bob")
        self.assertEqual([r.sender for r in self.cm.incoming_requests("dave")], ["alice", "carol"])

        # Carol cancels tail request
        self.cm.cancel_request("carol", "dave")
        self.assertEqual([r.sender for r in self.cm.incoming_requests("dave")], ["alice"])

        # Missing request raises ResourceNotFoundError
        with self.assertRaises(ResourceNotFoundError):
            self.cm.accept_request("dave", "bob")


if __name__ == "__main__":
    unittest.main()
