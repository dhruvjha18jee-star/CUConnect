# CUConnect — Implementation Plan

**Project**: CUConnect — Chanakya University Student Networking Platform  
**Course**: Data Structures and Algorithms (EAI212/EVE203/EEC203), III Semester B.Tech 2026-27  
**Faculty**: Nitish Hegde | **Submission Date**: 27-11-2026  
**Team**: Dhruv Jha, Pranam Jogur, Nihal N  

## Milestones and Build Order

1. **Milestone 1 — Hand-Written Data Structures (`core/ds/`)**
   - Implement `HashTable` (separate chaining, polynomial rolling hash, resize at LF > 0.75), `SinglyLinkedList`, `Queue` (linked-list based with `remove_value`), `Stack`, `MinHeap` (array-based with key function + deterministic tie-break), `Trie`, `merge_sort`, `binary_search`, and `AVLTree` (with LL, RR, LR, RL rotations).
   - Write unit tests + randomized cross-check tests against Python built-ins (`dict`, `sorted`, linear filter).

2. **Milestone 2 — Accounts, Graph, Connections & Requests**
   - Implement `core/models.py`, `core/auth.py` (PBKDF2-SHA256 salted hashing + `hmac.compare_digest`), `core/graph.py` (adjacency lists in `HashTable`), and `core/connections.py` (per-user incoming/outgoing `Queue`s + all edge-case rules including auto-accept).
   - Unit test all graph invariants and request edge cases.

3. **Milestone 3 — Graph Queries: Mutuals, BFS Degree/Chain, Suggestions**
   - Implement mutual connections (neighbour intersection), BFS degree (1st, 2nd, 3rd, 3+) and shortest chain using our `Queue`, and `core/suggestions.py` (depth-2 BFS + Jaccard coefficient + top-k `MinHeap`).
   - Unit test on small deterministic graphs and edge cases (disconnected, self, 4+ hops).

4. **Milestone 4 — Posts, Feed & Prefix Search**
   - Implement `core/posts.py` (per-user `SinglyLinkedList`, newest at head), `core/feed.py` (k-way merge of connections' lists with `MinHeap` + paging), and `core/search.py` (`Trie` indexing lowercase username and name tokens).
   - Unit test ordering, deletion, paging, and profile-rename reindexing.

5. **Milestone 5 — Enhancements & Facade**
   - Implement `core/notifications.py` (`Queue` per user, unread count, mark-as-read).
   - Implement `core/engagement.py` (likes in per-post `HashTable`, comments tree with pre-order DFS, trending posts via `MinHeap` with `likes + 2*comments` over recent window).
   - Implement `core/communities.py` (connected components via iterative DFS with `Stack`).
   - Integrate undo `Stack` (last send-request / last remove-connection) and `AVLTree` alphabetical student directory inside `core/service.py`.

6. **Milestone 6 — SQLite Write-Through Persistence**
   - Implement `storage/repository.py` (storage-only CRUD; zero graph/ranking SQL).
   - Connect `CUConnectService` for full startup load + write-through on every mutation.
   - Test full restart persistence (create rich state -> destroy service -> reload from same DB -> assert complete equality).

7. **Milestone 7 — User Interfaces**
   - Implement `ui/console_app.py` (menu app with `Stack`-based back navigation calling only `CUConnectService`).
   - Implement `ui/streamlit_app.py` (multi-view web app covering all core features + enhancements calling only `CUConnectService`).

8. **Milestone 8 — Seed Data, Benchmarks, Rule Checker & End-to-End Tests**
   - Implement `scripts/seed_data.py` (18 realistic Chanakya University students, 3 communities, an 8-student core example subgraph for dry runs, posts, comments, likes, pending requests, notifications).
   - Implement `scripts/benchmark.py` (100 / 1,000 / 5,000 users; benchmark chart).
   - Implement `scripts/check_rules.py` (AST verification of stdlib-only core, no forbidden imports/calls, no graph SQL, docstrings with Time/Space).
   - Implement `tests/test_end_to_end.py` verifying every user journey and persistence cycle.

9. **Milestone 9 — Diagrams, Screenshots, Report, Presentation & Study Docs**
   - Generate diagrams and capture real Streamlit screenshots.
   - Build `docs/REPORT.docx` and `docs/REPORT.pdf` (<= 15 pages).
   - Build `docs/PRESENTATION.pptx` (30–34 slides with speaker notes), render to PNGs, visually inspect every slide.
   - Write `docs/VIVA_QA.md` (90+ Q&As + 10 live-coding drills), `docs/CODE_WALKTHROUGH.md`, `docs/CHEATSHEET.md`, `docs/DEMO_SCRIPT.md`, `docs/REQUIREMENTS_TRACE.md`, and `README.md`.
