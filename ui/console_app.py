# ui/console_app.py
# Interactive terminal interface for CUConnect using CUConnectService and Stack back-navigation.
# Course mapping: Session 6: Stacks (Back Navigation) & Core Engine Facade Separation.

import argparse
from datetime import datetime
import getpass
import sys
from pathlib import Path

# Allow running directly as `python ui/console_app.py` from the project root.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.models import CUConnectError
from core.service import CUConnectService, ScreenNavigator


def _fmt_time(ts: float) -> str:
    """Format a POSIX timestamp into a clean human-readable date/time string."""
    return datetime.fromtimestamp(ts).strftime("%d %b %Y, %I:%M %p")


class ConsoleApp:
    """Menu-driven CLI for CUConnect with Stack-powered screen back-navigation."""

    def __init__(self, db_path: str = "cuconnect.db") -> None:
        self._service = CUConnectService(db_path=db_path)
        self._nav = ScreenNavigator("Auth")
        self._current_user: str | None = None

    def _print_header(self, title: str) -> None:
        print("\n" + "=" * 66)
        print(f"  CUConnect | {title}")
        print(f"  Path: {self._nav.breadcrumb()}")
        if self._current_user:
            unread = self._service.get_unread_notification_count(self._current_user)
            print(f"  Signed in as: @{self._current_user} | Unread notifications: {unread}")
        print("=" * 66)

    def _prompt(self, label: str) -> str:
        return input(f"{label}: ").strip()

    def run(self) -> None:
        """Main loop dispatching on the top of the ScreenNavigator Stack."""
        print("\nWelcome to CUConnect - Chanakya University Student Network (Console)")
        try:
            while True:
                screen = self._nav.current()
                try:
                    if screen == "Auth":
                        if not self._screen_auth():
                            break
                    elif screen == "Home":
                        self._screen_home()
                    elif screen == "Feed":
                        self._screen_feed()
                    elif screen == "Posts":
                        self._screen_posts()
                    elif screen == "Profile":
                        self._screen_profile()
                    elif screen == "Search":
                        self._screen_search()
                    elif screen == "Connections":
                        self._screen_connections()
                    elif screen == "Suggestions":
                        self._screen_suggestions()
                    elif screen == "Degree":
                        self._screen_degree()
                    elif screen == "Notifications":
                        self._screen_notifications()
                    elif screen == "Trending":
                        self._screen_trending()
                    elif screen == "Communities":
                        self._screen_communities()
                    elif screen == "Directory":
                        self._screen_directory()
                    else:
                        self._nav.back()
                except CUConnectError as exc:
                    print(f"\n[Error] {exc}")
                except ValueError as exc:
                    print(f"\n[Input Error] {exc}")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting CUConnect. Goodbye!")
        finally:
            self._service.close()

    # --- Screens ---

    def _screen_auth(self) -> bool:
        self._print_header("Sign In / Sign Up")
        print("  1. Log In")
        print("  2. Sign Up (Create New Account)")
        print("  0. Exit")
        choice = self._prompt("Choose an option")

        if choice == "1":
            uname = self._prompt("Username")
            pw = getpass.getpass("Password: ")
            user = self._service.login(uname, pw)
            self._current_user = user.username
            self._nav.reset("Home")
            print(f"\nWelcome back, {user.full_name} (@{user.username})!")
        elif choice == "2":
            uname = self._prompt("Choose username (3-30 chars, a-z/0-9/_)")
            pw = getpass.getpass("Choose password (min 6 chars): ")
            full_name = self._prompt("Full name")
            programme = self._prompt("Programme (e.g. B.Tech CSAI)")
            year = int(self._prompt("Year (1-4)"))
            bio = self._prompt("Short bio (optional)")
            skills_raw = self._prompt("Skills (comma-separated, optional)")
            skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
            user = self._service.sign_up(uname, pw, full_name, programme, year, bio, skills)
            self._service.login(user.username, pw)
            self._current_user = user.username
            self._nav.reset("Home")
            print(f"\nAccount created and signed in as @{user.username}!")
        elif choice == "0":
            print("Goodbye!")
            return False
        else:
            print("Invalid choice. Please enter 1, 2, or 0.")
        return True

    def _screen_home(self) -> None:
        assert self._current_user is not None
        self._print_header("Main Menu")
        unread = self._service.get_unread_notification_count(self._current_user)
        undo_tag = " [available]" if self._service.can_undo(self._current_user) else ""
        print("   1. Home Feed (k-way MinHeap merge)")
        print("   2. My Posts (Create / View / Delete)")
        print("   3. My Profile & View Other Profiles")
        print("   4. Search Students (Trie prefix search)")
        print("   5. Connections & Pending Requests (Queues)")
        print("   6. People You May Know (Depth-2 BFS + Jaccard + MinHeap)")
        print("   7. Degree of Connection & Shortest Chain (BFS)")
        print(f"   8. Notifications ({unread} unread)")
        print("   9. Trending Posts Among Connections (MinHeap)")
        print("  10. Student Communities (Iterative DFS + Stack)")
        print("  11. Browse All Students Alphabetically (AVL Tree)")
        print(f"  12. Undo Last Connection Action (Stack){undo_tag}")
        print("  13. Engine Diagnostics (DSA Stats)")
        print("   0. Log Out")

        choice = self._prompt("Choose an option")
        routes = {
            "1": "Feed",
            "2": "Posts",
            "3": "Profile",
            "4": "Search",
            "5": "Connections",
            "6": "Suggestions",
            "7": "Degree",
            "8": "Notifications",
            "9": "Trending",
            "10": "Communities",
            "11": "Directory",
        }
        if choice in routes:
            self._nav.push(routes[choice])
        elif choice == "12":
            msg = self._service.undo_last_action(self._current_user)
            print(f"\n[Undo] {msg}")
        elif choice == "13":
            stats = self._service.get_engine_stats()
            print("\n--- In-Memory DSA Engine Stats ---")
            for k, v in stats.items():
                print(f"  {k}: {v}")
        elif choice == "0":
            self._service.logout(self._current_user)
            self._current_user = None
            self._nav.reset("Auth")
            print("\nLogged out successfully.")
        else:
            print("Invalid option.")

    def _screen_feed(self) -> None:
        assert self._current_user is not None
        offset = 0
        page_size = 5
        while True:
            self._print_header(f"Home Feed (offset={offset})")
            posts, has_more = self._service.get_home_feed(
                self._current_user, limit=page_size, offset=offset
            )
            if not posts:
                print("  No posts from your connections yet. Connect with peers or check back soon!")
            else:
                for idx, post in enumerate(posts, start=1):
                    author = self._service.get_profile(post.author)
                    likes = self._service.get_like_count(post.post_id)
                    cmts = self._service.get_comment_count(post.post_id)
                    liked_mark = " (Liked)" if self._service.has_liked(post.post_id, self._current_user) else ""
                    print(f"\n  [{idx}] {author.full_name} (@{post.author}) - {_fmt_time(post.created_at)}")
                    print(f"      ID: {post.post_id}")
                    print(f"      {post.content}")
                    print(f"      Likes: {likes}{liked_mark} | Comments: {cmts}")

            print("\nActions: [n] Next page | [p] Prev page | [l] Like/Unlike | [c] View/Add Comments | [b] Back")
            cmd = self._prompt("Action").lower()
            if cmd == "n":
                if has_more:
                    offset += page_size
                else:
                    print("Already at the end of your feed.")
            elif cmd == "p":
                offset = max(0, offset - page_size)
            elif cmd == "l":
                pid = self._prompt("Enter post ID to toggle like")
                now_liked = self._service.toggle_like(pid, self._current_user)
                print("Liked!" if now_liked else "Unliked.")
            elif cmd == "c":
                pid = self._prompt("Enter post ID to inspect/comment")
                self._show_comments_dialog(pid)
            elif cmd in ("b", "0"):
                self._nav.back()
                return
            else:
                print("Unknown command.")

    def _show_comments_dialog(self, post_id: str) -> None:
        assert self._current_user is not None
        comments = self._service.get_post_comments(post_id)
        print(f"\n--- Threaded Comments (Pre-Order DFS) for {post_id} ---")
        if not comments:
            print("  No comments yet.")
        for comment, depth in comments:
            indent = "  " * (depth + 1)
            prefix = "|- " if depth > 0 else ""
            print(f"{indent}{prefix}[{comment.comment_id}] @{comment.author}: {comment.content}")

        action = self._prompt("[a] Add comment | [r] Reply to comment | [Enter] Close").lower()
        if action == "a":
            text = self._prompt("Your comment")
            self._service.add_comment(post_id, self._current_user, text)
            print("Comment added!")
        elif action == "r":
            parent_id = self._prompt("Parent comment ID")
            text = self._prompt("Your reply")
            self._service.add_comment(post_id, self._current_user, text, parent_comment_id=parent_id)
            print("Reply added!")

    def _screen_posts(self) -> None:
        assert self._current_user is not None
        self._print_header("My Posts (SinglyLinkedList, Newest at Head)")
        my_posts = self._service.get_user_posts(self._current_user)
        if not my_posts:
            print("  You have not posted anything yet.")
        for post in my_posts:
            likes = self._service.get_like_count(post.post_id)
            cmts = self._service.get_comment_count(post.post_id)
            print(f"  - [{post.post_id}] ({_fmt_time(post.created_at)}) {post.content}")
            print(f"    Likes: {likes} | Comments: {cmts}")

        print("\n  1. Create a new text post")
        print("  2. Delete one of my posts")
        print("  3. View comments on a post")
        print("  b. Back")
        choice = self._prompt("Choose").lower()
        if choice == "1":
            text = self._prompt("Share a project or technical idea")
            post = self._service.create_post(self._current_user, text)
            print(f"Posted! ID: {post.post_id}")
        elif choice == "2":
            pid = self._prompt("Post ID to delete")
            self._service.delete_post(self._current_user, pid)
            print(f"Deleted post {pid}.")
        elif choice == "3":
            pid = self._prompt("Post ID")
            self._show_comments_dialog(pid)
        elif choice in ("b", "0"):
            self._nav.back()

    def _screen_profile(self) -> None:
        assert self._current_user is not None
        self._print_header("Profile")
        me = self._service.get_profile(self._current_user)
        print(f"  Name      : {me.full_name} (@{me.username})")
        print(f"  Programme : {me.programme}, Year {me.year}")
        print(f"  Bio       : {me.bio or '(none)'}")
        print(f"  Skills    : {', '.join(me.skills) if me.skills else '(none)'}")

        print("\n  1. Edit my profile")
        print("  2. View another student's profile")
        print("  b. Back")
        choice = self._prompt("Choose").lower()
        if choice == "1":
            print("(Press Enter to keep current value)")
            name = self._prompt(f"Full name [{me.full_name}]")
            prog = self._prompt(f"Programme [{me.programme}]")
            yr_str = self._prompt(f"Year [{me.year}]")
            bio = self._prompt(f"Bio [{me.bio}]")
            skills_raw = self._prompt(f"Skills comma-separated [{', '.join(me.skills)}]")
            self._service.update_profile(
                self._current_user,
                full_name=name or None,
                programme=prog or None,
                year=int(yr_str) if yr_str else None,
                bio=bio if bio != "" else None,
                skills=[s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else None,
            )
            print("Profile updated!")
        elif choice == "2":
            other = self._prompt("Enter username to view")
            u = self._service.get_profile(other)
            deg = self._service.get_degree_and_chain(self._current_user, u.username)
            mutuals = self._service.get_mutual_connections(self._current_user, u.username)
            print(f"\n  {u.full_name} (@{u.username}) - {u.programme}, Year {u.year}")
            print(f"  Bio     : {u.bio or '(none)'}")
            print(f"  Skills  : {', '.join(u.skills) if u.skills else '(none)'}")
            print(f"  Degree  : {deg.label} | Mutual connections: {len(mutuals)}")
            posts = self._service.get_user_posts(u.username)
            if posts:
                print(f"  Latest post: {posts[0].content}")
        elif choice in ("b", "0"):
            self._nav.back()

    def _screen_search(self) -> None:
        assert self._current_user is not None
        self._print_header("Search Students (Trie Prefix Search)")
        prefix = self._prompt("Enter name or username prefix (or 'b' to go back)")
        if prefix.lower() == "b":
            self._nav.back()
            return
        matches = self._service.search_users(prefix, limit=15)
        if not matches:
            print(f"  No students matched prefix '{prefix}'.")
        else:
            for u in matches:
                print(f"  - {u.full_name} (@{u.username}) | {u.programme}, Year {u.year}")
        again = self._prompt("Press Enter to search again or 'b' for Back").lower()
        if again == "b":
            self._nav.back()

    def _screen_connections(self) -> None:
        assert self._current_user is not None
        self._print_header("Connections & Request Queues")
        conns = self._service.get_connections(self._current_user)
        inc = self._service.get_incoming_requests(self._current_user)
        out = self._service.get_outgoing_requests(self._current_user)

        print(f"  Connections ({len(conns)}): " + (", ".join(f"@{u.username}" for u in conns) or "(none)"))
        print(f"  Incoming Queue ({len(inc)}): " + (", ".join(f"@{r.sender}" for r in inc) or "(none)"))
        print(f"  Outgoing Queue ({len(out)}): " + (", ".join(f"@{r.receiver}" for r in out) or "(none)"))

        print("\n  1. Send connection request")
        print("  2. Accept incoming request")
        print("  3. Reject incoming request")
        print("  4. Cancel outgoing request")
        print("  5. Remove existing connection")
        print("  6. View mutual connections with another user")
        print("  7. Undo last send-request / remove-connection")
        print("  b. Back")
        choice = self._prompt("Choose").lower()

        if choice == "1":
            target = self._prompt("Username to connect with")
            status = self._service.send_connection_request(self._current_user, target)
            if status == "auto_accepted":
                print(f"Mutual request detected — auto-accepted! You are now connected with @{target}.")
            else:
                print(f"Connection request sent to @{target}.")
        elif choice == "2":
            sender = self._prompt("Username of sender to accept")
            self._service.accept_connection_request(self._current_user, sender)
            print(f"Accepted request from @{sender}.")
        elif choice == "3":
            sender = self._prompt("Username of sender to reject")
            self._service.reject_connection_request(self._current_user, sender)
            print(f"Rejected request from @{sender}.")
        elif choice == "4":
            receiver = self._prompt("Username of receiver to cancel")
            self._service.cancel_connection_request(self._current_user, receiver)
            print(f"Cancelled request to @{receiver}.")
        elif choice == "5":
            target = self._prompt("Username to disconnect from")
            self._service.remove_connection(self._current_user, target)
            print(f"Removed connection with @{target}.")
        elif choice == "6":
            other = self._prompt("Compare mutual connections with username")
            mutuals = self._service.get_mutual_connections(self._current_user, other)
            print(f"  Mutual connections ({len(mutuals)}): " + (", ".join(f"@{u.username}" for u in mutuals) or "(none)"))
        elif choice == "7":
            print(self._service.undo_last_action(self._current_user))
        elif choice in ("b", "0"):
            self._nav.back()

    def _screen_suggestions(self) -> None:
        assert self._current_user is not None
        self._print_header("People You May Know (Jaccard + MinHeap)")
        recs = self._service.get_people_you_may_know(self._current_user, k=8)
        if not recs:
            print("  No 2nd-degree suggestions right now.")
        else:
            for idx, rec in enumerate(recs, start=1):
                mutual_str = ", ".join(f"@{m}" for m in rec.mutual_usernames)
                print(
                    f"  {idx}. {rec.full_name} (@{rec.username}) - {rec.programme}, Year {rec.year}\n"
                    f"     Jaccard: {rec.jaccard_score:.4f} | Mutuals ({rec.mutual_count}): {mutual_str}"
                )
        cmd = self._prompt("Enter username to send request, or 'b' for Back").lower()
        if cmd in ("b", "0", ""):
            self._nav.back()
        else:
            status = self._service.send_connection_request(self._current_user, cmd)
            print(f"Request status with @{cmd}: {status}")

    def _screen_degree(self) -> None:
        assert self._current_user is not None
        self._print_header("Degree of Connection & Shortest Chain (BFS)")
        target = self._prompt("Target username (or 'b' for Back)")
        if target.lower() == "b":
            self._nav.back()
            return
        res = self._service.get_degree_and_chain(self._current_user, target)
        print(f"  Degree : {res.label}" + (f" ({res.distance} hops)" if res.distance is not None else ""))
        if res.path:
            print("  Chain  : " + " -> ".join(f"@{u}" for u in res.path))
        else:
            print("  Chain  : No path exists between these students.")
        if self._prompt("Press Enter to check another or 'b' for Back").lower() == "b":
            self._nav.back()

    def _screen_notifications(self) -> None:
        assert self._current_user is not None
        self._print_header("Notifications (Per-User Queue)")
        notifs = self._service.get_notifications(self._current_user)
        if not notifs:
            print("  No notifications yet.")
        for n in notifs:
            badge = "[NEW]" if not n.is_read else "[read]"
            print(f"  {badge} [{n.notification_id}] ({_fmt_time(n.created_at)}) {n.message}")

        print("\n  1. Mark all as read")
        print("  2. Mark one notification as read")
        print("  b. Back")
        choice = self._prompt("Choose").lower()
        if choice == "1":
            cnt = self._service.mark_all_notifications_read(self._current_user)
            print(f"Marked {cnt} notification(s) as read.")
        elif choice == "2":
            nid = self._prompt("Notification ID")
            self._service.mark_notification_read(self._current_user, nid)
            print("Marked as read.")
        elif choice in ("b", "0"):
            self._nav.back()

    def _screen_trending(self) -> None:
        assert self._current_user is not None
        self._print_header("Trending Posts Among Connections (Score = Likes + 2*Comments)")
        trending = self._service.get_trending_posts(self._current_user, k=5)
        if not trending:
            print("  No recent posts from your connections in the past 7 days.")
        for idx, item in enumerate(trending, start=1):
            print(
                f"  #{idx} Score {item.score} (Likes: {item.like_count}, Comments: {item.comment_count})"
                f" - @{item.post.author}"
            )
            print(f"      {item.post.content}")
        self._prompt("Press Enter to return")
        self._nav.back()

    def _screen_communities(self) -> None:
        assert self._current_user is not None
        self._print_header("Student Communities (Iterative DFS Connected Components)")
        mine = self._service.get_user_community(self._current_user)
        print(f"  Your Community: Community #{mine.community_id} (size {mine.size})")
        print("  Members: " + ", ".join(f"@{m}" for m in mine.members))

        print("\n  All Campus Communities:")
        for comm in self._service.get_all_communities():
            marker = " <-- YOU" if comm.community_id == mine.community_id else ""
            print(f"  - Community #{comm.community_id} (size {comm.size}){marker}: {', '.join('@' + m for m in comm.members)}")
        self._prompt("Press Enter to return")
        self._nav.back()

    def _screen_directory(self) -> None:
        self._print_header("Browse All Students Alphabetically (AVL Tree In-Order)")
        students = self._service.browse_all_students()
        stats = self._service.get_engine_stats()
        print(f"  Total: {len(students)} | AVL Height: {stats['avl_height']} | Balanced: {stats['avl_balanced']}\n")
        for idx, u in enumerate(students, start=1):
            print(f"  {idx:2d}. {u.full_name:<22} (@{u.username:<14}) | {u.programme}, Year {u.year}")
        self._prompt("Press Enter to return")
        self._nav.back()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CUConnect console app.")
    parser.add_argument("--db", default="cuconnect.db", help="Path to SQLite database file.")
    args = parser.parse_args()
    app = ConsoleApp(db_path=args.db)
    app.run()


if __name__ == "__main__":
    main()
