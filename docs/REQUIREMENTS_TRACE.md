# CUConnect — Requirements Traceability Matrix

Every bullet from `Mini Project - DSA (CSAI-EVE-EECS).pdf` and the project specification is mapped below to its implementing source file, public class/function, and verifying automated test(s).

## Core Requirements

| # | Problem Statement Requirement | Implementing File(s) | Class / Function(s) | Verifying Test(s) |
|---|---|---|---|---|
| 1 | Graph model $G(V, E)$: users are nodes, accepted connections are undirected edges, pending requests are directed edges; no self edges, no multiple edges | `core/graph.py`, `core/connections.py` | `SocialGraph.add_edge`, `SocialGraph.remove_edge`, `ConnectionManager.send_request` | `tests/test_graph.py::test_undirected_invariants_no_self_or_duplicate_edges`, `tests/test_connections.py::test_edge_case_rules` |
| 2 | Part 1 — Sign up with unique username & password; log in and log out | `core/auth.py`, `core/service.py`, `core/ds/hash_table.py` | `AccountManager.register_user`, `login`, `logout`, `CUConnectService.sign_up`, `login`, `logout` | `tests/test_auth.py::test_register_login_logout_and_uniform_error`, `tests/test_end_to_end.py` |
| 3 | Part 1 — Store passwords only in hashed form, never plain text; timing-safe check & uniform login errors | `core/auth.py` | `hash_password` (`pbkdf2_hmac`), `verify_password` (`hmac.compare_digest`), `AccountManager.login` | `tests/test_auth.py::test_password_hashing_salted_and_never_plaintext`, `test_register_login_logout_and_uniform_error` |
| 4 | Part 1 — User profile (name, programme, year, short bio, skills) viewable by others & editable | `core/models.py`, `core/auth.py`, `core/service.py` | `User`, `User.public_profile`, `CUConnectService.get_profile`, `update_profile` | `tests/test_auth.py::test_profile_update_and_unknown_user`, `tests/test_service.py::test_avl_directory_and_profile_rename_sync` |
| 5 | Part 2 — Send, accept, reject, cancel connection requests (per-user Queues); remove existing connection | `core/connections.py`, `core/ds/queue_ds.py`, `core/service.py` | `ConnectionManager.send_request`, `accept_request`, `reject_request`, `cancel_request`, `remove_connection`, `Queue.remove_value` | `tests/test_queue_ds.py`, `tests/test_connections.py::test_edge_case_rules`, `test_reverse_request_auto_accepts`, `test_out_of_order_accept_reject_cancel` |
| 6 | Part 2 — Request edge cases: no self, no duplicate, no already-connected, reverse auto-accept, receiver-only accept/reject, sender-only cancel, bidirectional remove, unknown users error | `core/connections.py`, `core/graph.py` | `ConnectionManager.*`, `SocialGraph.*` | `tests/test_connections.py` (all 3 test methods), `tests/test_end_to_end.py` |
| 7 | Part 2 — View connections & mutual connections with another user | `core/graph.py`, `core/service.py` | `SocialGraph.neighbors`, `SocialGraph.mutual_connections`, `CUConnectService.get_connections`, `get_mutual_connections` | `tests/test_graph.py::test_mutual_connections`, `tests/test_end_to_end.py` |
| 8 | Part 2 — Show "People You May Know", ranked by Jaccard coefficient (depth-2 BFS + `MinHeap`) with mutual count | `core/suggestions.py`, `core/ds/heap.py`, `core/service.py` | `SuggestionEngine.recommend`, `CUConnectService.get_people_you_may_know` | `tests/test_suggestions.py::test_jaccard_ranking_and_mutual_counts`, `tests/test_end_to_end.py` |
| 9 | Part 2 — Degree of connection (1st, 2nd, 3rd, `3+`) and one shortest chain using BFS + `Queue` + parent map | `core/graph.py`, `core/ds/queue_ds.py`, `core/service.py` | `SocialGraph.degree_and_shortest_path`, `CUConnectService.get_degree_and_chain` | `tests/test_graph.py::test_bfs_degrees_labels_and_shortest_path`, `tests/test_end_to_end.py` |
| 10 | Part 2 — Store network using adjacency lists | `core/graph.py`, `core/ds/hash_table.py` | `SocialGraph._adj` (`HashTable` mapping `username -> sorted list[str]`) | `tests/test_graph.py`, `scripts/check_rules.py` |
| 11 | Part 3 — Create text posts, view own posts, delete own posts (per-user `SinglyLinkedList`, newest at head) | `core/posts.py`, `core/ds/linked_list.py`, `core/service.py` | `PostManager.create_post`, `get_user_posts`, `delete_post`, `SinglyLinkedList.insert_head`, `delete_by_id` | `tests/test_linked_list.py`, `tests/test_posts.py::test_create_view_and_delete_own_posts` |
| 12 | Part 3 — Home feed of posts from connections, newest first, via k-way merge with `MinHeap` + paging | `core/feed.py`, `core/ds/heap.py`, `core/service.py` | `FeedEngine.get_home_feed`, `CUConnectService.get_home_feed` | `tests/test_feed.py::test_k_way_merge_newest_first_and_paging`, `tests/test_end_to_end.py` |
| 13 | Part 4 — Search users by name or username with prefix suggestions (`Trie`) | `core/search.py`, `core/ds/trie.py`, `core/service.py` | `Trie.insert`, `remove`, `prefix_search`, `UserSearchIndex.search`, `reindex_user` | `tests/test_trie.py` (incl. randomized cross-check), `tests/test_search.py` |
| 14 | Part 5 — Persistence across restarts (SQLite write-through); zero graph computation in SQL | `storage/repository.py`, `core/service.py` | `SQLiteRepository.*`, `CUConnectService._hydrate_from_storage` | `tests/test_repository.py`, `tests/test_service.py::test_full_restart_persistence`, `scripts/check_rules.py` |
| 15 | Part 6 — Separate core engine from UI; both Console app and Streamlit app call `core/service.py` only | `core/service.py`, `ui/console_app.py`, `ui/streamlit_app.py` | `CUConnectService`, `ConsoleApp`, Streamlit views | `scripts/check_rules.py::check_ui_decoupling_rules`, live console & Playwright UI checks |

## Hand-Written Data Structures & Hard Rules

| # | Requirement | Implementing File(s) | Verifying Test / Check |
|---|---|---|---|
| 16 | `HashTable`: separate chaining, custom polynomial rolling hash (no `hash()`), resize > 0.75 | `core/ds/hash_table.py` | `tests/test_hash_table.py` (incl. 800-op random vs `dict`), `scripts/check_rules.py` |
| 17 | `SinglyLinkedList`, `Queue`, `Stack`, `MinHeap`, `Trie`, `merge_sort`, `binary_search` | `core/ds/*.py` | `tests/test_linked_list.py`, `test_queue_ds.py`, `test_stack.py`, `test_heap.py` (random vs `sorted`), `test_trie.py` (random vs filter), `test_algorithms.py` |
| 18 | Stdlib-only core, no `heapq`/`deque`/`queue`/`networkx`/`sorted(`, `Time:` & `Space:` docstrings | All `core/**/*.py`, `storage/repository.py` | `scripts/check_rules.py` (0 violations) |

## Enhancements Implemented

| # | Enhancement Requirement | Implementing File(s) | Class / Function(s) | Verifying Test(s) |
|---|---|---|---|---|
| E1 | Notifications for requests, acceptances, likes, comments (`Queue`, unread count, mark-as-read) | `core/notifications.py`, `core/service.py` | `NotificationManager.*`, `CUConnectService.get_notifications`, `get_unread_notification_count`, `mark_all_notifications_read` | `tests/test_notifications.py`, `tests/test_service.py`, `tests/test_end_to_end.py` |
| E2 | Likes (per-post `HashTable`) & Comments with nested replies (Tree + Pre-Order DFS) | `core/engagement.py`, `core/service.py` | `EngagementManager.like_post`, `unlike_post`, `add_comment`, `get_comments_preorder` | `tests/test_engagement.py::test_likes_and_nested_comment_preorder_dfs`, `tests/test_service.py` |
| E3 | Trending posts among connections (`likes + 2*comments`, recent window, top-k `MinHeap`) | `core/engagement.py`, `core/service.py` | `EngagementManager.get_trending_posts`, `CUConnectService.get_trending_posts` | `tests/test_engagement.py::test_trending_posts_formula_and_recency_window`, `tests/test_end_to_end.py` |
| E4 | Undo (`send_request`, `remove_connection`) and Console back-navigation using `Stack` | `core/ds/stack.py`, `core/service.py`, `ui/console_app.py` | `CUConnectService.undo_last_action`, `ScreenNavigator` | `tests/test_stack.py`, `tests/test_service.py::test_undo_send_request_and_remove_connection` |
| E5 | Communities (connected components via iterative DFS + `Stack`, user's community & size) | `core/communities.py`, `core/service.py` | `CommunityDetector.find_all_communities`, `get_user_community` | `tests/test_communities.py`, `tests/test_end_to_end.py` |
| E6 | Alphabetical "Browse All Students" using `AVLTree` with LL, RR, LR, RL rotations | `core/ds/avl_tree.py`, `core/service.py` | `AVLTree.insert`, `delete`, `_rebalance`, `inorder`, `CUConnectService.browse_all_students` | `tests/test_avl_tree.py` (LL/RR/LR/RL + 400-op random stress test), `tests/test_service.py` |

## Documentation, Benchmarks & Seeding Deliverables

| # | Deliverable | Path |
|---|---|---|
| D1 | Seed dataset (18 students, 3 communities, core dry-run graph, posts, likes, comments, requests) | `scripts/seed_data.py` |
| D2 | Synthetic benchmarks (100 / 1,000 / 5,000 users) + chart | `scripts/benchmark.py`, `docs/diagrams/benchmark_chart.png` |
| D3 | Static rule verifier | `scripts/check_rules.py` |
| D4 | Project Report (Word & PDF, 10 pages <= 15 limit, real screenshots) | `docs/REPORT.docx`, `docs/REPORT.pdf` |
| D5 | Presentation Deck (34 slides + speaker notes + visual QA) | `docs/PRESENTATION.pptx` |
| D6 | Viva Q&A (102 Q&As + 10 live-coding drills), Walkthrough, Cheatsheet, Demo Script, Decisions, Plan | `docs/VIVA_QA.md`, `docs/CODE_WALKTHROUGH.md`, `docs/CHEATSHEET.md`, `docs/DEMO_SCRIPT.md`, `docs/DECISIONS.md`, `docs/PLAN.md` |
