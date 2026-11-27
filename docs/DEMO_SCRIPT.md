# CUConnect — 5-Minute Live Demo Script

**Setup before the examiner arrives** (run from project root):
```powershell
.\.venv\Scripts\python.exe scripts/seed_data.py
.\.venv\Scripts\streamlit.exe run ui/streamlit_app.py
```
Keep a second terminal ready for `pytest`, `check_rules.py`, and `ui/console_app.py`.

---

## Minute 0:00 – 0:45 | Authentication, Security & Live Campus Stats

1. **What to show**: Start on the Streamlit **Login / Sign Up** page. Point to the right-hand card showing `18 Students`, `23 Connections`, `14 Posts`, `3 Communities`.
2. **Click**: Enter `aarav` and an **incorrect** password (`wrongpass`), click **Log In**.
   - **What to say**: *"Notice it returns `'Invalid username or password.'` — the exact same message and timing as a non-existent username, because `core/auth.py` runs a dummy PBKDF2 hash and uses `hmac.compare_digest` so usernames cannot be enumerated. Every account lives in our hand-written separate-chaining `HashTable` using a base-31 polynomial rolling hash."*
3. **Click**: Enter `aarav` / `chanakya2026` and click **Log In**.

---

## Minute 0:45 – 1:35 | Home Feed (k-Way MinHeap), Likes & Threaded Comments

1. **What to show**: **Home Feed** opens automatically with Rohan's, Ananya's, and Diya's newest posts.
   - **What to say**: *"Each student's posts live in a `SinglyLinkedList` with O(1) head insertion, so every friend's list is already newest-first. Instead of copying and sorting all posts, `FeedEngine` pushes only each connection's head `ListNode` into our `MinHeap` keyed by `(-timestamp, -seq_id)` — giving O((k + N) log k) pagination. In our 5,000-user benchmark, this runs in 0.09 ms."*
2. **Click**: Toggle the **Like** button on Rohan's post (per-post `HashTable`), then expand **Comments & Replies (3)**.
   - **What to say**: *"Likes sit in a per-post `HashTable` for O(1) toggle and zero duplicates. Comments are stored as a tree where each reply attaches to `parent.replies` and renders via Pre-Order DFS — notice depth 0 (`@aarav`), depth 1 (`@rohan`), and depth 2 (`@meera`)."*
3. **Click**: Post a quick reply to `@meera`, then navigate to **Trending Posts** to show the score (`likes + 2 * comments`) jumped immediately!

---

## Minute 1:35 – 2:25 | People You May Know (Depth-2 BFS + Jaccard + MinHeap)

1. **Click**: **People You May Know** in the sidebar.
2. **What to show**: Three cards ranked in exact order:
   - **Meera Iyer (`@meera`)** — `Jaccard: 0.7500`, `3 mutuals: @ananya, @diya, @rohan`
   - **Kabir Menon (`@kabir`)** — `Jaccard: 0.2500`, `1 mutual: @diya`
   - **Sneha Joshi (`@sneha`)** — `Jaccard: 0.2000`, `1 mutual: @rohan`
3. **What to say**: *"We run BFS strictly to depth 2 with our linked-list `Queue`. Why Jaccard instead of raw mutual count? Look at Kabir vs Sneha: both share 1 mutual friend with Aarav, but Kabir has degree 2 (union 4 → 0.25) while Sneha has degree 3 (union 5 → 0.20), so Kabir ranks higher in our `MinHeap`."*

---

## Minute 2:25 – 3:05 | Degree of Connection & Shortest Chain (BFS)

1. **Click**: **Degree & Chain Tool** in the sidebar.
2. **Click**: Select **`isha`**.
   - **What to show**: `Degree: 3+`, `Shortest Hop Count: 4`, chain: `Aarav Sharma → Rohan Verma → Sneha Joshi → Arjun Deshmukh → Isha Reddy`.
3. **Click**: Select **`pranav`**.
   - **What to show**: `Degree: Not connected`, `Shortest Hop Count: ∞ (Unreachable)`.
   - **What to say**: *"BFS uses our FIFO `Queue` and a `parent` map to guarantee the shortest unweighted chain in O(V + E). Because Pranav is in Community #2 (VLSI Lab), there is no accepted edge path yet — only a pending directed request."*

---

## Minute 3:05 – 4:10 | Trie Search, Request Queues, Communities (DFS) & Undo Stack

1. **Click**: **Search Users**, type **`sh`** and press Enter.
   - **What to show**: Instantly matches **Aarav Sharma** and **Pranav Shetty** (proving our `Trie` indexes both usernames and every word of a student's full name in $O(L)$ time).
2. **Click**: Click **Accept** next to **Pranav Shetty** (or accept from **Connections & Requests → Incoming Requests**).
   - **What to say**: *"Pending requests live in per-user incoming and outgoing `Queue`s; accepting removes the directed edge via `Queue.remove_value` and inserts both directions of the undirected edge into `SocialGraph`."*
3. **Click**: Open **Communities**!
   - **What to show**: Community #1 just grew from **10 → 15 students** because iterative DFS (`Stack`) now bridges Community #1 and Community #2 through the new `aarav ↔ pranav` edge!
4. **Click**: Open **Connections & Requests → My Connections**, click **Remove** next to `pranav`, then click **↩️ Undo Last Action** in the sidebar!
   - **What to say**: *"Our per-user LIFO `Stack` records `send_request` and `remove_connection` actions and restores the undirected edge in both RAM and SQLite."*

---

## Minute 4:10 – 5:00 | AVL Tree Directory, Persistence Restart & Console App

1. **Click**: **Browse All Students (AVL)**.
   - **What to show**: 18 students in strict A→Z order with live metrics: `AVL Tree Height: 5`, `AVL Balanced: Yes`, `HashTable Load Factor: 0.562`.
   - **What to say**: *"Our AVL tree implements all four rotations — LL, RR, LR, and RL — so alphabetical listings stay O(V) via in-order traversal without re-sorting."*
2. **Switch to Terminal** (30 seconds):
   - Run `.\.venv\Scripts\python.exe scripts/check_rules.py` → `ALL RULES PASSED!`
   - Run `.\.venv\Scripts\pytest.exe -q` → `48 passed`
   - Optionally launch `.\.venv\Scripts\python.exe ui/console_app.py`, log in as `aarav` / `chanakya2026`, press `5` (Connections) to prove the newly accepted `@pranav` connection persisted across apps via SQLite, and press `b` to show Console `Stack` back-navigation!
