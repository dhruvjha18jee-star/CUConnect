# CUConnect — Comprehensive Viva Preparation Bank (100 Q&As + 10 Live-Coding Drills)

**Course**: Data Structures and Algorithms (`EAI212/EVE203/EEC203`) — Chanakya University  
**Faculty**: Prof. Nitish Hegde | **Team**: Dhruv Jha, Pranam Jogur, Nihal N  

Each question includes a crisp **Model Answer** plus a **Likely Follow-Up** with a short answer. Practice answering aloud in 20–40 seconds per question!

---

## 1. Project Overview & Architecture (Q1–Q6)

### Q1. What is CUConnect and what problem does it solve?
- **Answer**: CUConnect is a campus networking application for Chanakya University students (like a lightweight LinkedIn/Instagram for engineering projects) where students create profiles, connect across branches, share technical posts, discover peers, and explore campus communities. Every core feature is powered by hand-written Python data structures rather than external libraries or SQL queries.
- **Follow-up**: *Why did you build both a console app and a Streamlit web app?*
  - **Short Answer**: To prove clean architectural separation — both UIs call the exact same `CUConnectService` facade in `core/service.py` without duplicating any DSA logic or touching internal structures.

### Q2. Why is the core engine separated from the UI behind `CUConnectService`?
- **Answer**: Using the Facade pattern (`core/service.py`) keeps all graph invariants, security rules, data structure updates, and write-through SQLite commits in one place. Neither `console_app.py` nor `streamlit_app.py` can accidentally violate graph symmetry or forget to reindex the Trie.
- **Follow-up**: *How do you enforce that UIs never touch `core/ds/` directly?*
  - **Short Answer**: `scripts/check_rules.py` parses the AST of every file in `ui/` and fails if any file imports `core.ds` or `storage`.

### Q3. Why did you restrict the core engine to the Python standard library only?
- **Answer**: Because the project assesses our mastery of fundamental DSA (30 marks core engine + 40 marks viva). Hand-writing `HashTable`, `SinglyLinkedList`, `Queue`, `Stack`, `MinHeap`, `Trie`, `AVLTree`, `merge_sort`, and `binary_search` ensures we understand and can defend every single line.
- **Follow-up**: *Where are Python's built-in `list`, `dict`, and `set` still permitted?*
  - **Short Answer**: Only for incidental algorithm bookkeeping (like BFS `visited` set and `parent` map) and backing value arrays inside our hand-written structures.

### Q4. Why does `CUConnectService` take an injectable `clock` and maintain a `_seq` counter?
- **Answer**: Real wall-clock timestamps (`time.time()`) can collide within the same millisecond or fluctuate across runs, causing flaky tests. An injectable clock makes tests deterministic and lets us simulate 7-day trending windows instantaneously, while `_seq` breaks exact timestamp ties reliably.
- **Follow-up**: *How does `_seq` survive an app restart?*
  - **Short Answer**: Every post, request, comment, and notification persists its `seq_id` to SQLite; on startup `_hydrate_from_storage()` sets `self._seq` to the maximum loaded `seq_id`.

### Q5. Walk through what happens from the moment `CUConnectService("cuconnect.db")` is constructed.
- **Answer**: It opens `SQLiteRepository`, initializes all empty in-memory structures, reads all 7 SQLite tables via plain `SELECT *`, sorts historical sequences in Python via `merge_sort`, hydrates `AccountManager`, `SocialGraph`, `ConnectionManager`, `PostManager`, `EngagementManager`, `NotificationManager`, `UserSearchIndex` (`Trie`), and the `AVLTree` directory, and sets `_seq`.
- **Follow-up**: *What is the startup time complexity?*
  - **Short Answer**: $O(V \log V + E + P \log P + C \log C + N \log N)$ due to sorting persisted sequences and inserting users into the AVL tree.

### Q6. Which course sessions are visibly represented in CUConnect?
- **Answer**: Sessions 2 (Big-O & benchmarks), 3 (arrays/strings & two-pointer intersection), 4 (Singly Linked Lists for posts), 6 (Stacks for undo, CLI nav, iterative DFS), 7 (Queues for requests, BFS, notifications), 8 (Trees & Pre-Order DFS for comment threads & Trie), 9–10 (BST & AVL rotations LL/RR/LR/RL), 11 (Graphs, adjacency lists, BFS, DFS), 12 (Binary Search), 14 (Merge Sort), and 15 (MinHeap & HashTable).
- **Follow-up**: *Which enhancement did you intentionally skip and why?*
  - **Short Answer**: Image posts, as explicitly directed, so we could focus deeply on DSA-backed enhancements including the optional AVL Tree directory.

---

## 2. Graph & Adjacency Lists (Q7–Q13)

### Q7. How is the CUConnect network mathematically modelled as $G(V, E)$?
- **Answer**: Each registered user is a vertex $v \in V$. Each accepted connection is an undirected edge $\{u, v\} \in E$. Pending connection requests are directed edges $(u \to v)$ held separately in request queues until resolved. $G$ is a simple graph: no self-loops $(u, u)$ and no parallel edges.
- **Follow-up**: *Why are pending requests NOT stored directly in the undirected adjacency list?*
  - **Short Answer**: Because pending requests are asymmetric (one-way) and must not affect BFS degrees, mutual connections, home feeds, or connected components until accepted.

### Q8. Why did you represent $G(V, E)$ using adjacency lists instead of an adjacency matrix?
- **Answer**: Social networks are sparse ($\deg(u) \ll |V|$). For 5,000 students with average degree 10, an adjacency matrix needs $5,000^2 = 25,000,000$ entries ($O(V^2)$) and scans 5,000 slots just to list one user's 10 friends. Adjacency lists use only $O(V + E)$ space (~55,000 entries) and iterate a user's friends in $O(\deg(u))$.
- **Follow-up**: *When WOULD an adjacency matrix be preferable?*
  - **Short Answer**: On small, very dense graphs ($|E| \approx |V|^2$) or algorithms needing repeated $O(1)$ edge queries / matrix multiplication (like Floyd-Warshall).

### Q9. How are adjacency lists stored inside `SocialGraph`?
- **Answer**: `self._adj` is our hand-written `HashTable` mapping each `username` to a Python `list[str]` of neighbor usernames maintained in strict alphabetical order.
- **Follow-up**: *What three benefits do you gain by keeping each neighbor list sorted?*
  - **Short Answer**: (1) $O(\log d)$ edge checks via `binary_search`; (2) $O(d_u + d_v)$ two-pointer mutual connection intersection; (3) deterministic alphabetical BFS traversal.

### Q10. How does `SocialGraph.has_edge(u, v)` work and what is its complexity?
- **Answer**: After verifying both vertices exist via `_require_user` ($O(1)$ average), it calls our hand-written `binary_search(neighbors_a, v)` on `u`'s sorted adjacency list in $O(\log \deg(u))$ time and $O(1)$ space.
- **Follow-up**: *Could you make `has_edge` $O(1)$ average?*
  - **Short Answer**: Yes, by storing a `HashTable` per user instead of a sorted list — but we would lose $O(d_u + d_v)$ sorted two-pointer intersection and alphabetical iteration without sorting.

### Q11. How do you guarantee graph symmetry when adding or removing an edge?
- **Answer**: `add_edge(u, v)` inserts `v` into `adj[u]` AND `u` into `adj[v]` together, incrementing `_edge_count` by 1. `remove_edge(u, v)` removes `v` from `adj[u]` AND `u` from `adj[v]` together, decrementing `_edge_count` by 1.
- **Follow-up**: *How is the undirected edge stored in SQLite without duplicating rows?*
  - **Short Answer**: `SQLiteRepository._canonical_pair` orders `(user_a, user_b)` so `user_a < user_b` before inserting into `connections(user_a, user_b)` with a composite primary key.

### Q12. How does `mutual_connections(u, v)` work?
- **Answer**: It runs a two-pointer scan over sorted `adj[u]` and `adj[v]` (`i = 0, j = 0`). If `adj[u][i] == adj[v][j]`, it records the match and advances both pointers; otherwise it advances whichever pointer points to the smaller string.
- **Follow-up**: *What is its exact time and space complexity?*
  - **Short Answer**: Time $O(\deg(u) + \deg(v))$, Space $O(\min(\deg(u), \deg(v)))$ for the output list.

### Q13. What happens if someone calls `add_edge("aarav", "aarav")` or connects two already-connected students?
- **Answer**: `add_edge` checks `if user_a == user_b` first and raises `ValidationError`, then checks `binary_search(neighbors_a, user_b) != -1` and raises `ConnectionRuleError` — making self-edges and parallel edges impossible.
- **Follow-up**: *What if an unknown username is passed?*
  - **Short Answer**: `_require_user` detects `None` from `self._adj.get(username)` and raises `UserNotFoundError`.

---

## 3. Request Queues & Edge Cases (Q14–Q20)

### Q14. Why are pending connection requests stored in per-user `Queue`s?
- **Answer**: Connection requests arrive over time and naturally display oldest-first (FIFO). Storing a separate `incoming` `Queue` and `outgoing` `Queue` per user inside `HashTable`s lets us list a user's pending requests in $O(r)$ without scanning the whole network.
- **Follow-up**: *Why store every pending request in BOTH `sender.outgoing` and `receiver.incoming`?*
  - **Short Answer**: So both "view requests I received" and "view requests I sent" run instantaneously from the respective user's queue instead of scanning every user on campus.

### Q15. Why is our `Queue` implemented with a linked list instead of a Python `list`?
- **Answer**: Calling `list.pop(0)` shifts every remaining element left in $O(n)$ time. A linked list with `_head` (front) and `_tail` (rear) pointers achieves strict $O(1)$ `enqueue` and `dequeue`.
- **Follow-up**: *What happens to `_tail` when the last remaining element is dequeued?*
  - **Short Answer**: `dequeue()` checks `if self._head is None: self._tail = None` so `_tail` does not keep a dangling reference to the removed node.

### Q16. Why did we add `remove_value` / `remove_where` to a FIFO `Queue`?
- **Answer**: In a real networking app, a student might receive requests from Alice, Bob, and Carol, and decide to accept or reject Bob (middle) or Carol (rear) first! `remove_value` / `remove_where` unlinks any matching node cleanly in $O(r)$.
- **Follow-up**: *What is the subtle pointer bug to watch out for in `remove_value`?*
  - **Short Answer**: If the deleted node is `self._tail`, we MUST set `self._tail = previous`; otherwise the next `enqueue()` would attach to the deleted node and vanish!

### Q17. Explain the reverse-request auto-accept rule in `ConnectionManager.send_request`.
- **Answer**: If `B -> A` is already pending in `A.incoming` / `B.outgoing`, and `A` calls `send_request(A, B)`, both users clearly want to connect. We remove `B -> A` from both queues, add the undirected edge `{A, B}` to `SocialGraph`, delete the pending row from SQLite, persist the connection, notify both users, and return `"auto_accepted"`.
- **Follow-up**: *Does an auto-accepted `send_request` push onto `A`'s undo stack?*
  - **Short Answer**: No — only `"pending"` requests push `UndoAction("send_request", ...)` onto the undo stack, because an auto-accept immediately became a mutual accepted connection.

### Q18. How do you enforce that only the receiver can accept/reject and only the sender can cancel?
- **Answer**: `accept_request(actor, sender)` searches `actor.incoming` for `sender -> actor`. If absent, it checks whether `actor -> sender` exists; if so, it raises `AuthorizationError("Only the receiver can accept...")`. Symmetrically, `cancel_request(actor, receiver)` searches `actor.outgoing` and raises `AuthorizationError` if `actor` is actually the receiver.
- **Follow-up**: *What if no request exists in either direction?*
  - **Short Answer**: It raises `ResourceNotFoundError`.

### Q19. Why does `ConnectionRequest.__eq__` compare only `(sender, receiver)`?
- **Answer**: Because there can be at most one pending request for a given ordered pair `(sender, receiver)`, matching by endpoints allows `Queue.remove_value(req)` to remove the exact mirror entry from the counterpart queue cleanly.
- **Follow-up**: *What prevents duplicate pending requests from `A` to `B`?*
  - **Short Answer**: `send_request` calls `has_pending_request(sender, receiver)` before enqueuing and raises `ConnectionRuleError` if found.

### Q20. What happens if `A` and `B` disconnect and later send a new connection request?
- **Answer**: `remove_connection` removes both directions of `{A, B}` from `SocialGraph` and deletes the row from SQLite `connections`. Because no edge and no pending request exist anymore, either user can cleanly send a fresh request later.
- **Follow-up**: *What if someone tries to remove a connection with someone they are not connected to?*
  - **Short Answer**: `SocialGraph.remove_edge` finds `binary_search(...) == -1` and raises `ConnectionRuleError`.

---

## 4. BFS, Degrees & Shortest Chain (Q21–Q27)

### Q21. Why does BFS find the shortest connection chain in CUConnect?
- **Answer**: All accepted connections have equal weight (1 hop). Because BFS expands vertices via a FIFO `Queue`, it visits every vertex at distance $k$ before visiting any vertex at distance $k+1$. Therefore the very first time BFS reaches `target`, the path length is provably minimum.
- **Follow-up**: *Would BFS still find the shortest path if connections had different weights (e.g., closeness scores)?*
  - **Short Answer**: No — for non-negative weighted graphs we would use Dijkstra's algorithm with our `MinHeap`.

### Q22. Why must we add a vertex to `visited` when ENQUEUEING it rather than when DEQUEUEING it?
- **Answer**: Suppose both `ananya` and `diya` (at layer 1) connect to `meera` (at layer 2). If we only marked `visited` upon dequeue, `meera` would be enqueued twice (or up to $O(E)$ times in dense graphs), wasting memory and overwriting `parent[meera]`. Marking at enqueue ensures each vertex enters the `Queue` at most once.
- **Follow-up**: *What is the maximum size of the BFS Queue?*
  - **Short Answer**: At most $|V|$ vertices, so Space is strictly $O(V)$.

### Q23. How is the shortest chain reconstructed from the `parent` map?
- **Answer**: When `current` discovers an unvisited `neighbor`, we store `parent[neighbor] = current` (with `parent[source] = None`). When `neighbor == target`, we walk backwards (`node = parent[node]` until `None`), append to a list, and reverse it to obtain `[source, ..., target]`.
- **Follow-up**: *Why didn't we store the entire path list inside every Queue entry?*
  - **Short Answer**: Storing full paths in the queue could take $O(V^2)$ memory; a `parent` map uses only $O(V)$ space.

### Q24. Trace BFS from `aarav` to `isha` on our seeded campus graph.
- **Answer**: Layer 0: `aarav`. Layer 1 (`1st`): `ananya`, `diya`, `rohan`. Layer 2 (`2nd`): `meera` (from `ananya`), `kabir` (from `diya`), `sneha` (from `rohan`). Layer 3 (`3rd`): `vikram` (from `meera`), `arjun` (from `sneha`). Layer 4 (`3+`): `isha` (from `arjun`). Path: `aarav -> rohan -> sneha -> arjun -> isha` (distance 4, label `"3+"`).
- **Follow-up**: *What if there are two shortest paths of equal length (e.g., `aarav -> ananya -> meera` vs `aarav -> diya -> meera`)?*
  - **Short Answer**: Because adjacency lists are sorted alphabetically, `ananya` is dequeued before `diya`, so BFS deterministically returns `aarav -> ananya -> meera`.

### Q25. How are degree labels formatted for all edge cases?
- **Answer**: Distance `0` $\to$ `"Self"` (path `[source]`), `1` $\to$ `"1st"`, `2` $\to$ `"2nd"`, `3` $\to$ `"3rd"`, $\ge 4$ $\to$ `"3+"` (still returns exact distance and shortest chain!), unreachable $\to$ `"Not connected"` (distance `None`, path `[]`).
- **Follow-up**: *Can BFS return `"Not connected"` on our seed dataset?*
  - **Short Answer**: Yes — `aarav` (Community #1) to `pranav` (Community #2) or `riya` (Community #3) returns `"Not connected"`.

### Q26. What is the exact time and space complexity of `degree_and_shortest_path`?
- **Answer**: Time is $O(V + E)$ because every reachable vertex is enqueued at most once and every incident edge in its adjacency list is inspected at most twice (once from each endpoint). Space is $O(V)$ for `visited`, `parent`, and the `Queue`.
- **Follow-up**: *Does our empirical benchmark match $O(V+E)$?*
  - **Short Answer**: Yes — at fixed average degree 10, BFS grew linearly from 0.034 ms (100 users) $\to$ 0.362 ms (1,000) $\to$ 6.721 ms (5,000).

### Q27. Why does BFS break immediately upon discovering `target` instead of exploring the rest of the graph?
- **Answer**: Because the first discovery of `target` in BFS is already guaranteed optimal; stopping early avoids scanning deeper layers unnecessarily (cutting practical runtime significantly for 1st/2nd-degree queries!).
- **Follow-up**: *Does early exit change the worst-case Big-O?*
  - **Short Answer**: No — if `target` is unreachable or at the deepest layer, worst-case remains $O(V + E)$.

---

## 5. Jaccard Similarity & Suggestions (Q28–Q33)

### Q28. Explain how "People You May Know" works step by step.
- **Answer**: (1) Run BFS from `u` strictly up to depth 2 using our `Queue` to collect all 2nd-degree non-connected candidates. (2) Exclude anyone who already has a pending request with `u`. (3) For each candidate `v`, compute `mutuals = graph.mutual_connections(u, v)` and Jaccard $J(u, v) = \frac{|N(u)\cap N(v)|}{|N(u)| + |N(v)| - |N(u)\cap N(v)|}$. (4) Push into `MinHeap(key=lambda s: (-s.jaccard_score, -s.mutual_count, s.username))` and pop top-$k$.
- **Follow-up**: *Why don't we check 3rd-degree users for Jaccard suggestions?*
  - **Short Answer**: Any user at distance $\ge 3$ has zero common neighbors with `u`, so their Jaccard coefficient is guaranteed to be `0.0`.

### Q29. Why is Jaccard coefficient better than sorting simply by raw mutual-connection count?
- **Answer**: Raw mutual count biases toward super-connected campus influencers who know everyone. Jaccard normalizes by $|N(u) \cup N(v)|$. In our seed data, both `kabir` and `sneha` share 1 mutual with `aarav`, but `kabir` has degree 2 ($J = 1/4 = 0.25$) while `sneha` has degree 3 ($J = 1/5 = 0.20$), so `kabir` rightly ranks above `sneha`.
- **Follow-up**: *What is the range of Jaccard similarity?*
  - **Short Answer**: $[0.0, 1.0]$ — `0.0` means no shared neighbors; `1.0` means identical friend lists!

### Q30. Walk through the exact Jaccard scores for `aarav` on our seeded graph.
- **Answer**: $N(\text{aarav}) = \{\text{ananya}, \text{diya}, \text{rohan}\}$ (size 3). Depth-2 candidates:
  - `meera` (deg 4): 3 mutuals, union $= 3+4-3 = 4 \implies J = 3/4 = 0.7500$ (#1)
  - `kabir` (deg 2): 1 mutual (`diya`), union $= 3+2-1 = 4 \implies J = 1/4 = 0.2500$ (#2)
  - `sneha` (deg 3): 1 mutual (`rohan`), union $= 3+3-1 = 5 \implies J = 1/5 = 0.2000$ (#3).
- **Follow-up**: *Why doesn't `vikram` appear in `aarav`'s suggestions?*
  - **Short Answer**: Two reasons: `vikram` is at depth 3 (not depth 2), AND `vikram -> aarav` already has a pending request!

### Q31. How do you compute $|N(u) \cup N(v)|$ without constructing a union set?
- **Answer**: By the inclusion-exclusion principle: $|N(u) \cup N(v)| = |N(u)| + |N(v)| - |N(u) \cap N(v)| = \deg(u) + \deg(v) - \text{mutual\_count}$, which runs in $O(1)$ once mutual count is known!
- **Follow-up**: *Could `union_size` ever be zero?*
  - **Short Answer**: No for depth-2 candidates (both have degree $\ge 1$), and we still guard `if union_size > 0 else 0.0` defensively.

### Q32. What happens if two candidates have the exact same Jaccard score?
- **Answer**: Our `MinHeap` key tuple is `(-jaccard_score, -mutual_count, username)`. Equal Jaccard scores break ties in favor of more mutual connections, and if still tied, alphabetically by `username` — 100% deterministic!
- **Follow-up**: *Can you optimize top-$k$ heap selection from $O(C \log C)$ to $O(C \log k)$?*
  - **Short Answer**: Yes — keep a size-$k$ min-heap storing the $k$ best items seen so far and pop the smallest whenever `len(heap) > k`; for small $C$ (typical depth-2 candidates), pushing all into a max-heap is simpler and took only 3.69 ms at 5,000 users.

### Q33. What is an alternative link-prediction measure mentioned in the problem statement?
- **Answer**: **Katz's score**, which sums all paths of length $\ell$ between $u$ and $v$ weighted by $\beta^\ell$ ($\beta < 1$), giving shorter paths higher weight while also crediting longer paths (3+ hops).
- **Follow-up**: *Why did we choose Jaccard over Katz?*
  - **Short Answer**: Jaccard is local ($O(d^2)$ depth-2 BFS vs matrix powers/all-paths for Katz), bounded in $[0,1]$, and immediately explainable alongside mutual counts.

---

## 6. Hash Table & Authentication (Q34–Q41)

### Q34. Explain our custom string hash function in `HashTable._polynomial_hash`.
- **Answer**: It computes $h(s) = \left(\sum_{i=0}^{L-1} \text{ord}(s_i) \cdot 31^{L-1-i}\right) \bmod (10^9 + 7)$ iteratively via Horner's method: `h = (h * 31 + ord(ch)) % 1_000_000_007`, then maps to bucket `h % capacity`.
- **Follow-up**: *Why base 31 and modulus $10^9+7$?*
  - **Short Answer**: 31 is a small odd prime (classic Java `String.hashCode` base) that mixes character positions well and prevents anagram collisions; $10^9+7$ is a large prime that avoids integer bloat while remaining easy to hand-trace.

### Q35. Why does `HashTable` resize at load factor `> 0.75` and how does `_resize` work?
- **Answer**: Load factor $\alpha = n / \text{capacity}$ is the expected chain length under uniform hashing. Keeping $\alpha \le 0.75$ guarantees $O(1)$ average lookup. When $\alpha > 0.75$, `_resize` allocates `capacity * 2` buckets and re-inserts every existing `_ChainNode` at `hash(key) % new_capacity`.
- **Follow-up**: *If `_resize` takes $O(n)$, why is `put()` still $O(1)$ amortized?*
  - **Short Answer**: Because capacity doubles each time, after paying $O(n)$ to resize we get $0.75 \cdot n$ cheap $O(1)$ inserts before the next resize — spreading the cost to $O(1)$ per insert by the accounting/aggregate method.

### Q36. Why did we choose Separate Chaining over Open Addressing (linear/quadratic probing)?
- **Answer**: CUConnect deletes keys frequently (unliking posts, removing connections, pruning Trie nodes). Open addressing requires special "tombstone" markers on deletion (otherwise probe chains break!) and suffers clustering as $\alpha \to 1$. Separate chaining unlinks `_ChainNode`s cleanly in $O(1)$ once found.
- **Follow-up**: *What is one advantage open addressing DOES have over separate chaining?*
  - **Short Answer**: Better CPU cache locality and lower pointer overhead when keys are mostly static and load factor stays below ~0.5.

### Q37. What is the worst-case time complexity of `HashTable.get` and when does it occur?
- **Answer**: $O(n)$ if every single key hashes to the exact same bucket index, degenerating that bucket into a single linked list of length $n$. With a good rolling hash and load factor $\le 0.75$, average case is $O(1)$.
- **Follow-up**: *How do production languages like Java 8 mitigate worst-case hash-flooding?*
  - **Short Answer**: By converting long bucket chains (e.g., length $> 8$) into balanced Red-Black trees so worst-case lookup drops from $O(n)$ to $O(\log n)$.

### Q38. Why should passwords NEVER be hashed with plain `hashlib.sha256(password)`?
- **Answer**: Two fatal flaws: (1) Without a unique random salt, two students with the same password get identical hashes and fall instantly to precomputed rainbow tables. (2) SHA-256 is designed to be ultra-fast (billions of hashes/sec on GPUs), enabling brute-force cracking.
- **Follow-up**: *How does `core/auth.py` fix both flaws?*
  - **Short Answer**: It uses `os.urandom(16)` for a unique 128-bit salt per user and `hashlib.pbkdf2_hmac("sha256", ..., 100_000)` to deliberately stretch key derivation.

### Q39. Why do we compare hashes with `hmac.compare_digest` instead of `==`?
- **Answer**: Python's `==` on strings returns `False` at the **first mismatched byte**, leaking timing information about how many leading bytes matched. `hmac.compare_digest` always scans every byte in constant time.
- **Follow-up**: *Why does `AccountManager.login` also run a dummy PBKDF2 check when a username is missing?*
  - **Short Answer**: So an attacker cannot tell whether a username exists by measuring whether login failed in 0.1 ms (no user) vs 40 ms (PBKDF2 ran).

### Q40. Why must login errors NOT say "Username not found" vs "Wrong password"?
- **Answer**: Revealing which usernames exist enables user enumeration attacks (an attacker can harvest valid student accounts and target them with credential stuffing). Both failures raise the identical `AuthError("Invalid username or password.")`.
- **Follow-up**: *What about `sign_up`?*
  - **Short Answer**: `sign_up` must inform the user if a chosen username is already taken so they can pick a unique one.

### Q41. Why do we normalize usernames to lowercase (`strip().lower()`)?
- **Answer**: So `"Aarav"` and `"aarav"` cannot become two confusingly different accounts and users can log in cleanly regardless of caps lock.
- **Follow-up**: *Does `User.public_profile()` ever expose `password_hash`?*
  - **Short Answer**: Never — it returns a new dictionary containing only public profile fields.

---

## 7. MinHeap & Home Feed k-Way Merge (Q42–Q48)

### Q42. How is our binary `MinHeap` represented in memory without node pointers?
- **Answer**: As a complete binary tree stored compactly in a dynamic array `self._data`. For index `i`: parent is `(i - 1) // 2`, left child is `2 * i + 1`, and right child is `2 * i + 2`. No left/right pointer memory is needed!
- **Follow-up**: *Why does array representation work for heaps but NOT efficiently for general BSTs?*
  - **Short Answer**: Because a binary heap is guaranteed to be a **complete** binary tree (no gaps before the last level), whereas an unbalanced BST can have $2^h$ empty gaps.

### Q43. Trace `MinHeap.push` and `MinHeap.pop`.
- **Answer**: `push` appends the entry to the end of `_data` and calls `_sift_up` (swapping upward with its parent while smaller) in $O(\log n)$. `pop` saves `_data[0]`, moves the last leaf `_data.pop()` into index `0`, and calls `_sift_down` (swapping with the smaller child while larger) in $O(\log n)$.
- **Follow-up**: *Why does `pop` move the LAST element to index 0 instead of shifting the array left?*
  - **Short Answer**: Moving the last leaf preserves the complete-tree shape in $O(1)$ before sifting down in $O(\log n)$; shifting the array would cost $O(n)$ and break the heap property everywhere.

### Q44. How does a single `MinHeap` class work as a Max-Heap in CUConnect?
- **Answer**: `MinHeap.__init__(key=...)` computes a priority tuple for each pushed item. Passing a negated numeric key — e.g. `key=lambda n: (-n.value.created_at, -n.value.seq_id)` — makes the largest timestamp have the smallest negative key, so `pop()` returns the newest post first!
- **Follow-up**: *How do you avoid `TypeError: '<' not supported between instances of 'Post' and 'Post'` on ties?*
  - **Short Answer**: Every entry is stored as `(priority_key, self._counter, item)`. Since `_counter` is a unique strictly increasing integer, Python never reaches index 2 (`item`) during tuple comparison!

### Q45. Explain the k-way merge algorithm used by `FeedEngine.get_home_feed`.
- **Answer**: Each of a user's $k$ connections already owns a newest-first `SinglyLinkedList`. We push only each connection's `head` `ListNode` into `MinHeap` (size $\le k$). We loop: pop the newest `top_node`; if `top_node.next` is not `None`, push `top_node.next`; skip the first `offset` posts and collect the next `limit` posts. Return `(page, not heap.is_empty())`.
- **Follow-up**: *Why is `not heap.is_empty()` an exact `has_more` pagination flag?*
  - **Short Answer**: Because if any connection still had an unread older post, we pushed `top_node.next` right after popping, so the heap is non-empty if and only if at least one more post exists!

### Q46. Compare k-way heap merge vs collecting all connection posts and calling `merge_sort`.
- **Answer**: Suppose you have $k = 50$ friends with 100 posts each ($P = 5,000$ total posts), and you want the top $N = 10$ posts. Full sort takes $O(P \log P) \approx 5,000 \times 12 = 60,000$ ops and allocates 5,000 references. k-way merge takes $O((k + N)\log k) \approx 60 \times 6 = 360$ ops and keeps heap size $\le 50$!
- **Follow-up**: *What did our benchmark show at $N = 5,000$ total users?*
  - **Short Answer**: Top-10 Home Feed took just **0.088 ms** — virtually constant as campus size grew 50x!

### Q47. What if one connection has 0 posts while others have many?
- **Answer**: During heap initialization we check `if head_node is not None: heap.push(head_node)`, cleanly skipping silent friends without inserting `None` into the heap.
- **Follow-up**: *What if a user has 0 connections?*
  - **Short Answer**: `get_home_feed` returns `([], False)` immediately in $O(1)$.

### Q48. What is the complexity of building a heap from $n$ items by pushing one by one vs Floyd's bottom-up `heapify`?
- **Answer**: Pushing $n$ items one by one takes $O(n \log n)$ worst case. Floyd's bottom-up `heapify` (calling `_sift_down` from index `n//2 - 1` down to `0`) builds a heap in linear $O(n)$ time because most nodes live near the bottom with tiny height.
- **Follow-up**: *Which does `FeedEngine` use?*
  - **Short Answer**: Pushing $k$ connection heads takes $O(k \log k)$, which is tiny since $k$ is only one user's friend count.

---

## 8. Trie & Prefix Search (Q49–Q54)

### Q49. How does our `Trie` store child characters and user IDs?
- **Answer**: Each `TrieNode` holds `children: HashTable(initial_capacity=4)` mapping single lowercase characters to child `TrieNode`s, plus `user_ids: set[str]` storing the usernames of every student whose indexed word ends at that node.
- **Follow-up**: *Why use `HashTable(initial_capacity=4)` instead of a 26-element array per node?*
  - **Short Answer**: Usernames include digits and underscores (`a-z`, `0-9`, `_` = 37+ chars), and most Trie nodes have only 1–2 children — a small `HashTable` supports any character while saving substantial memory.

### Q50. Why do we index BOTH the username AND every word of `full_name`?
- **Answer**: So typing `"sh"` finds both **Aarav Sharma** (surname) and **Pranav Shetty** (surname), while typing `"aar"` finds `@aarav` (username + first name). Without word-level indexing, searching by last name would fail!
- **Follow-up**: *If `"aarav"` matches both the username `"aarav"` and the first name `"Aarav"`, how do you avoid returning Aarav twice?*
  - **Short Answer**: `Trie.prefix_search` collects matches into a `matched: set[str]`, deduplicating user IDs automatically before sorting with `merge_sort`.

### Q51. Walk through `Trie.remove(word, user_id)` and why branch pruning matters.
- **Answer**: As we walk down the characters of `word`, we push `(parent, ch, child)` onto our hand-written `Stack`. At the terminal node we remove `user_id` from `node.user_ids`. Then we pop the stack bottom-up: whenever a child has empty `user_ids` AND zero `children`, we remove `ch` from `parent.children`, stopping as soon as a node is still shared by another word.
- **Follow-up**: *When is `Trie.remove` triggered in CUConnect?*
  - **Short Answer**: Whenever a student edits their `full_name` via `update_profile()`, `UserSearchIndex.reindex_user` removes stale name tokens and inserts the new ones!

### Q52. What is the complexity of `Trie.prefix_search(prefix)`?
- **Answer**: Walking the prefix takes $O(L)$ where $L = \text{len}(\text{prefix})$. Collecting all matching users from the subtree takes $O(M)$ where $M$ is the number of nodes in that subtree, and sorting the $U$ unique matched users takes $O(U \log U)$ via `merge_sort`. Total: $O(L + M + U \log U)$.
- **Follow-up**: *Why is `Trie` much faster than scanning all $V$ users when the user types a 4-character prefix?*
  - **Short Answer**: As $L$ grows, the prefix subtree shrinks dramatically ($M \ll V$), whereas linear scanning always checks all $V$ users regardless of prefix length.

### Q53. What happens if someone searches an empty string `""` or whitespace `"   "`?
- **Answer**: `prefix_search` returns `[]` immediately so a blank search box does not dump the entire directory (for browsing everyone alphabetically, CUConnect provides the `AVLTree` directory instead!).
- **Follow-up**: *How do you handle uppercase input like `"SH"`?*
  - **Short Answer**: Both `insert` and `prefix_search` normalize strings with `.strip().lower()`, making search cleanly case-insensitive.

### Q54. Why did we collect subtree results in `Trie.prefix_search` using an explicit `Stack` instead of recursion?
- **Answer**: Iterative DFS with our hand-written `Stack` avoids recursion overhead on very long words and reuses our Session 6 `Stack` consistently across the engine.
- **Follow-up**: *How did we test `Trie` thoroughly?*
  - **Short Answer**: `tests/test_trie.py` inserts 150 random words, deletes 40, and cross-checks 100 random prefixes against a brute-force `word.startswith(prefix)` linear filter.

---

## 9. SinglyLinkedList & Posts (Q55–Q59)

### Q55. Why use a `SinglyLinkedList` for each user's posts instead of a Python list?
- **Answer**: Posts are created at the front (newest first). `insert_head` on a `SinglyLinkedList` is $O(1)$ without shifting any elements, and every node carries an explicit `.next` pointer that `FeedEngine` feeds directly into `MinHeap` for k-way merging.
- **Follow-up**: *What if we appended to the end of a Python list and read backwards?*
  - **Short Answer**: That works in $O(1)$ amortized, but a `SinglyLinkedList` directly exercises Session 4 pointer manipulation and gives `FeedEngine` self-contained `ListNode` cursors without tracking `(author, index)` pairs.

### Q56. Why does `PostManager` keep BOTH per-user `SinglyLinkedList`s AND a `post_id -> Post` `HashTable`?
- **Answer**: The linked list stores each author's timeline in newest-first order, while the `post_id` `HashTable` lets `like_post`, `add_comment`, and `delete_post` validate a post ID and check its author in $O(1)$ average time instead of scanning every user's linked list!
- **Follow-up**: *What happens to likes and comments when an author deletes their post?*
  - **Short Answer**: `CUConnectService.delete_post` calls `engagement.remove_post_engagement(post_id)` in RAM and `repo.delete_post(post_id)` in SQLite, removing all orphaned likes and comments atomically.

### Q57. How does `SinglyLinkedList.delete_by_id` handle deleting the head, middle, or tail node?
- **Answer**: It walks with `previous = None` and `current = self._head`. When `id_getter(current.value) == target_id`: if `previous is None` (deleting head), it sets `self._head = current.next`; otherwise it links `previous.next = current.next` (which works identically for middle and tail nodes since tail's `.next` is `None`).
- **Follow-up**: *Why can't another student delete Aarav's post?*
  - **Short Answer**: `PostManager.delete_post` checks `if post.author != actor: raise AuthorizationError("You can only delete your own posts.")`.

### Q58. How are posts hydrated from SQLite so the newest post still ends up at the head?
- **Answer**: `_hydrate_from_storage` loads all post rows with `SELECT * FROM posts`, sorts them **oldest-first** by `(created_at, seq_id)` via our `merge_sort`, and calls `posts.load_post(post)` (`insert_head`) for each. Because the newest post is inserted last at the head, it sits at `head`!
- **Follow-up**: *What would break if you sorted newest-first during hydration?*
  - **Short Answer**: Prepending newest-first would reverse the linked lists to oldest-first, breaking both "view own posts" and the k-way heap feed!

### Q59. What input validations protect `create_post`?
- **Answer**: `PostManager.create_post` strips whitespace, rejects empty posts, caps content at `MAX_CONTENT_LENGTH = 2000` characters, and verifies the author exists (`UserNotFoundError`).
- **Follow-up**: *What is the time complexity of `create_post` vs `delete_post`?*
  - **Short Answer**: `create_post` is $O(1)$ average; `delete_post` is $O(P_{\text{author}})$ to unlink from the author's linked list.

---

## 10. Stack, Undo, Back-Navigation & DFS Communities (Q60–Q65)

### Q60. List all four places where our hand-written `Stack` (`core/ds/stack.py`) is used.
- **Answer**: (1) Per-user undo history in `CUConnectService` (`send_request` and `remove_connection`); (2) Console CLI back-navigation via `ScreenNavigator`; (3) Iterative DFS connected-components discovery in `CommunityDetector`; (4) Bottom-up empty-node pruning and subtree DFS in `Trie`.
- **Follow-up**: *Why is `Stack` a natural fit for undo and navigation?*
  - **Short Answer**: Both follow strict Last-In-First-Out (LIFO) order — you always reverse the most recent action or return to the screen you just left.

### Q61. Walk through what happens when a user clicks Undo after `send_request` or `remove_connection`.
- **Answer**: `undo_last_action(username)` pops the top `UndoAction` from that user's `Stack`. For `"send_request"`, it verifies the request is still pending, cancels it from both queues, and deletes it from SQLite. For `"remove_connection"`, it verifies they are still disconnected, restores both directions of the undirected edge in `SocialGraph`, and re-inserts the row into SQLite.
- **Follow-up**: *What if the receiver already accepted the request before the sender clicks Undo?*
  - **Short Answer**: `has_pending_request` returns `False`, so `undo_last_action` refuses cleanly with `ValidationError("Cannot undo request ... it is no longer pending.")` instead of deleting an accepted friendship!

### Q62. How does console back-navigation work without importing `core.ds` inside `ui/console_app.py`?
- **Answer**: `core/service.py` exposes `ScreenNavigator`, a small helper backed by our `Stack`. Opening a submenu calls `nav.push("Suggestions")`; pressing `b` calls `nav.back()` (popping unless depth is 1); logging out calls `nav.reset("Auth")`.
- **Follow-up**: *How is the breadcrumb string `Home > Connections` generated from a top-down stack?*
  - **Short Answer**: `to_list()` returns `[top, ..., bottom]`, so `breadcrumb()` reverses that copy and joins with `" > "`.

### Q63. How does `CommunityDetector` find all campus communities using Iterative DFS?
- **Answer**: It iterates through every username in `graph.users()`. Whenever a user `u` is not in `visited`, it starts a new component: marks `u` visited, pushes `u` onto our `Stack`, and loops popping `current`, recording it, and pushing all unvisited neighbors. Each component is sorted alphabetically via `merge_sort`, and components are ranked by descending size via `merge_sort`.
- **Follow-up**: *Why use Iterative DFS instead of recursive DFS?*
  - **Short Answer**: Python's default recursion limit is ~1,000 frames; a long chain of 1,500 students would crash recursive DFS with `RecursionError`, whereas iterative DFS with our `Stack` easily handles 5,000+ nodes.

### Q64. What communities exist on the seeded dataset, and what happens when `aarav` accepts `pranav`?
- **Answer**: Initially there are 3 connected components: Community #1 (CSAI/Systems Hub, size 10), Community #2 (VLSI & Robotics Lab, size 5), and Community #3 (First-Year Builders Guild, size 3). Accepting `pranav -> aarav` adds a bridge edge between Communities #1 and #2, immediately merging them into one 15-student community!
- **Follow-up**: *Does adding an edge inside an already-connected component change the number of communities?*
  - **Short Answer**: No — an intra-component edge creates a cycle but leaves connected components unchanged.

### Q65. What is the complexity of `find_all_communities()`?
- **Answer**: Traversal visits every vertex once and every edge twice: $O(V + E)$. Sorting members and components alphabetically with `merge_sort` adds $O(V \log V)$. Total: Time $O(V \log V + E)$, Space $O(V)$.
- **Follow-up**: *Could BFS also find connected components?*
  - **Short Answer**: Yes — both BFS (`Queue`) and DFS (`Stack`) discover the exact same connected components in $O(V + E)$.

---

## 11. Comment Trees, Likes, Trending & AVL Directory (Q66–Q72)

### Q66. How are likes stored per post, and what is the complexity of liking or checking a like?
- **Answer**: `EngagementManager._likes_by_post` is a `HashTable` mapping `post_id -> HashTable(username -> timestamp)`. Adding, removing, checking (`has_liked`), and counting (`len(like_table)`) all run in $O(1)$ average time, and duplicate likes by the same student are structurally impossible.
- **Follow-up**: *Why didn't you store likers in a Python `list`?*
  - **Short Answer**: Checking whether a user already liked a viral post with 500 likes would take $O(L)$ linear scan instead of $O(1)$.

### Q67. How are threaded comments and nested replies modelled and rendered?
- **Answer**: Each `Comment` has `parent_comment_id` (`None` for top-level) and `replies: list[Comment]` (children in an n-ary tree). `EngagementManager` keeps `post_id -> root_comments` and `comment_id -> Comment` in `HashTable`s for $O(1)$ reply attachment. `get_comments_preorder(post_id)` traverses the forest with **Pre-Order DFS** (`visit node at depth`, then recurse on `node.replies` at `depth + 1`).
- **Follow-up**: *Why Pre-Order DFS instead of Post-Order or Level-Order (BFS)?*
  - **Short Answer**: Post-order prints replies *above* their parent comment (backwards!), and BFS groups all depth-1 replies from different threads together, scrambling conversations. Only Pre-Order places each reply right beneath its parent.

### Q68. Explain how Trending Posts are computed and why the linked-list early exit works.
- **Answer**: For each connection of `username`, `get_trending_posts` walks their `SinglyLinkedList` of posts. Because each list is newest-first, as soon as `post.created_at < now - window_seconds` (7 days), it `break`s early! Qualifying posts are scored as `likes + 2 * total_comments`, pushed into `MinHeap(key=lambda t: (-t.score, -t.post.created_at, -t.post.seq_id))`, and popped top-$k$.
- **Follow-up**: *Why weight comments 2x higher than likes?*
  - **Short Answer**: Writing a technical comment/reply signals deeper engagement than a one-click like (as specified: `score = likes + 2 * comments`).

### Q69. Why did we build an `AVLTree` for "Browse All Students" instead of a plain BST?
- **Answer**: A plain BST has worst-case height $O(V)$ if keys arrive in sorted order (e.g., batch-importing students alphabetically by name), degrading search/insert/delete to $O(V)$. An AVL tree enforces $|\text{height}(\text{left}) - \text{height}(\text{right})| \le 1$ at every node via rotations, guaranteeing height $\le 1.44 \log_2(V) = O(\log V)$ always.
- **Follow-up**: *What is the AVL tree height for our 18 seeded students?*
  - **Short Answer**: Height `5` (since $2^4 - 1 = 15 < 18 \le 31 = 2^5 - 1$), verified `is_balanced() == True`.

### Q70. Explain all four AVL rotation cases (LL, RR, LR, RL) from Session 10.
- **Answer**: Let `BF(node) = height(left) - height(right)`:
  - **LL** (`BF = +2`, `BF(left) >= 0`): single Right Rotation on `node`.
  - **RR** (`BF = -2`, `BF(right) <= 0`): single Left Rotation on `node`.
  - **LR** (`BF = +2`, `BF(left) < 0`): Left Rotation on `node.left`, then Right Rotation on `node`.
  - **RL** (`BF = -2`, `BF(right) > 0`): Right Rotation on `node.right`, then Left Rotation on `node`.
- **Follow-up**: *Why do we update heights of the lower rotated node BEFORE the new root of the rotation?*
  - **Short Answer**: Because the new root's height is computed from its children's heights — including the node that just moved down!

### Q71. What key does `CUConnectService` use inside `AVLTree` and how does it handle profile renames?
- **Answer**: The sort key is `(user.full_name.lower(), user.username)` so students appear in case-insensitive alphabetical order by full name, with unique `username` breaking identical-name ties. When `update_profile` changes `full_name`, `CUConnectService` calls `_directory.delete(old_key)` and `_directory.insert(new_key, updated)`.
- **Follow-up**: *How does `AVLTree.delete` handle deleting a node with TWO children?*
  - **Short Answer**: It finds the in-order successor (`_min_node(node.right)`), copies the successor's key and value into `node`, deletes the successor from `node.right`, and calls `_rebalance` all the way back up to the root.

### Q72. How does `NotificationManager` avoid notifying a user about their own actions?
- **Answer**: In `CUConnectService.like_post` and `add_comment`, we guard `if post.author != uname:` (and track a `notified = {uname}` set on comment replies so replying to a comment on your own post notifies only the other person, never yourself or twice!).
- **Follow-up**: *Are notifications persisted across restarts?*
  - **Short Answer**: Yes — every notification writes through to the `notifications` SQLite table, and `mark_read` / `mark_all_read` updates `is_read = 1` in SQLite immediately.

---

## 12. Persistence & SQLite Storage-Only Design (Q73–Q78)

### Q73. What does "write-through persistence" mean in CUConnect?
- **Answer**: Every read/query executes strictly in RAM against our hand-written structures, while every write operation (`sign_up`, `accept_connection_request`, `create_post`, `like_post`, etc.) immediately updates RAM AND commits to SQLite before returning.
- **Follow-up**: *What is the alternative ("write-back" / periodic flush), and why didn't we use it?*
  - **Short Answer**: Write-back batches writes in memory and flushes later — faster for heavy writes, but any crash or abrupt terminal exit loses recent student data. Write-through guarantees durability.

### Q74. Why is SQLite prohibited from running graph queries in this project?
- **Answer**: Both by project specification ("All graph computations must run in your Python code on data structures held in memory") and pedagogically — letting SQL `JOIN` or `ORDER BY` do the work would hide the exact DSA algorithms we are being graded on.
- **Follow-up**: *How do you prove there are no hidden SQL `JOIN`s or `ORDER BY`s in `storage/`?*
  - **Short Answer**: `scripts/check_rules.py` inspects every SQL string in `storage/` via AST and fails if `JOIN`, `RECURSIVE`, `GROUP BY`, `ORDER BY`, `COUNT(`, `SUM(`, `AVG(`, `MAX(`, or `MIN(` appears.

### Q75. Why are user skills stored as a JSON string in SQLite `users.skills`?
- **Answer**: Skills are a small list of strings belonging exclusively to one user profile and never queried via SQL. Serializing with stdlib `json.dumps` / `json.loads` keeps the schema clean (7 tables) while preserving exact list order.
- **Follow-up**: *How are undirected edges stored in the `connections` table so `(aarav, diya)` and `(diya, aarav)` don't create duplicate rows?*
  - **Short Answer**: `_canonical_pair` always places the alphabetically smaller username in `user_a` and larger in `user_b`, enforced by `PRIMARY KEY (user_a, user_b)`.

### Q76. Why must comments be sorted by `seq_id` during startup hydration before building the comment trees?
- **Answer**: A reply references `parent_comment_id` and attaches to `parent_node.replies`. Because a parent comment is always created before any reply to it, its `seq_id` is strictly smaller. Sorting loaded comments by `seq_id` via `merge_sort` guarantees every parent already exists in `_comments_by_id` when its child loads!
- **Follow-up**: *What would happen if SQLite returned a child reply row before its parent row?*
  - **Short Answer**: Without sorting by `seq_id`, `add_comment` would raise `ResourceNotFoundError` because the parent wouldn't be loaded yet.

### Q77. How does `tests/test_service.py::test_full_restart_persistence` prove persistence works?
- **Answer**: It creates `svc1` backed by a real SQLite file in a temp directory, creates 4 users, connections, a pending request, a post, a like, nested comments, and notifications, then calls `svc1.close()`. Next it creates a brand-new `svc2` against the same file and asserts login, connections, pending queues, BFS path, Jaccard suggestions, feed, likes, comment tree depth, notifications, Trie search, and AVL order are 100% intact.
- **Follow-up**: *Does undo history persist across restarts?*
  - **Short Answer**: Intentionally no — undo is session-scoped in memory (`DECISIONS.md`), just like Ctrl+Z in an editor!

### Q78. Why did we pass `check_same_thread=False` to `sqlite3.connect`?
- **Answer**: Streamlit caches `CUConnectService` with `@st.cache_resource` across browser reruns, which Streamlit may serve on different worker threads. Without `check_same_thread=False`, SQLite would raise a thread-affinity `ProgrammingError`.
- **Follow-up**: *How does `SQLiteRepository` keep multi-statement operations like `delete_post` atomic?*
  - **Short Answer**: Wrapping all three `DELETE` statements (`post_likes`, `comments`, `posts`) inside `with self._conn:` runs them in a single SQLite transaction (all-or-nothing).

---

## 13. Testing, Determinism & Rule Checking (Q79–Q83)

### Q79. What is "randomized cross-check testing" and where did you use it?
- **Answer**: Instead of only testing a few hand-picked inputs, we generate hundreds of random operations with a fixed seed (`random.Random(42)`) and assert our hand-written structure matches Python's battle-tested built-in after **every single step**: `HashTable` vs `dict` (800 ops), `MinHeap` vs `sorted` (25 random arrays), `Trie` vs linear `startswith` filter (100 random prefixes), `merge_sort` vs `sorted`, and `AVLTree` vs `sorted` + `is_balanced()` (400 random insert/delete ops).
- **Follow-up**: *Why pass a fixed seed to `random.Random(...)` in unit tests?*
  - **Short Answer**: So if a bug ever occurs, the exact failing sequence is 100% reproducible on every machine.

### Q80. What does `scripts/check_rules.py` check automatically?
- **Answer**: Using Python's `ast` module, it verifies: (1) zero forbidden imports (`heapq`, `collections`, `queue`, `networkx`, `sortedcontainers`, `bisect`) in `core/` and `storage/`; (2) zero calls to `sorted()`, `.sort()`, or built-in `hash()` in `HashTable`; (3) every public function/method in `core/` has `Time:` and `Space:` in its docstring; (4) zero `JOIN`/`ORDER BY`/`GROUP BY`/`RECURSIVE`/aggregates in `storage/` SQL; (5) UIs never import `core.ds` or `storage`.
- **Follow-up**: *Why use `ast` instead of simple regex text search?*
  - **Short Answer**: AST distinguishes real Python calls/imports/SQL strings from comments and docstrings, avoiding false positives and catching aliased imports cleanly.

### Q81. How do you guarantee deterministic output in feeds, BFS chains, and suggestions?
- **Answer**: Four mechanisms working together: (1) injectable clock + monotonic `_seq` counter; (2) `MinHeap` insertion counter breaking equal-key ties; (3) sorted adjacency lists making BFS explore neighbors alphabetically; (4) stable `merge_sort` everywhere sorted listings are produced.
- **Follow-up**: *What makes `merge_sort` stable in `core/ds/algorithms.py`?*
  - **Short Answer**: Using `<=` (`left_key <= right_key`) instead of `<` when merging, so equal elements from the left half always precede those from the right half.

### Q82. Name at least six edge cases explicitly tested for connection requests.
- **Answer**: (1) Unknown user → `UserNotFoundError`; (2) Self-request → `ValidationError`; (3) Request to already-connected user → `ConnectionRuleError`; (4) Duplicate pending request → `ConnectionRuleError`; (5) Reverse pending request → auto-accept; (6) Sender trying to accept/reject own outgoing request → `AuthorizationError`; (7) Receiver trying to cancel incoming request → `AuthorizationError`; (8) Out-of-order middle/tail queue removal.
- **Follow-up**: *Where are these tested?*
  - **Short Answer**: `tests/test_connections.py` and `tests/test_end_to_end.py`.

### Q83. How do you test `core/service.py` quickly without touching the real `cuconnect.db` file?
- **Answer**: Passing `db_path=":memory:"` opens an ephemeral in-RAM SQLite database for fast unit tests, and persistence tests use `tempfile.TemporaryDirectory()` so every test leaves the workspace completely clean.
- **Follow-up**: *Why do tests call `svc.close()` in a `finally` block?*
  - **Short Answer**: On Windows, open SQLite file handles lock the file and prevent `TemporaryDirectory` cleanup if not closed explicitly.

---

## 14. Complexity Analysis & Benchmarks (Q84–Q89)

### Q84. What did our synthetic benchmarks (100 → 1,000 → 5,000 users) reveal?
- **Answer**: At average degree 10 and 3 posts/user:
  - **BFS**: `0.034 ms` (100) → `0.362 ms` (1,000) → `6.721 ms` (5,000) — linear in $V + E$!
  - **Home Feed (top-10 k-way heap)**: `0.035 ms` → `0.172 ms` → **`0.088 ms`** — practically constant because it depends only on friend count $k$, not $V$!
  - **Suggestions (Depth-2 + Jaccard)**: `1.130 ms` → `2.441 ms` → `3.691 ms` — scales with $d^2$, barely growing from 1,000 to 5,000!
  - **Trie Search**: `0.080 ms` → `1.942 ms` → `2.179 ms` — sub-3ms even at 5,000 users!
- **Follow-up**: *Why was Home Feed actually slightly faster at 5,000 (0.088 ms) than at 1,000 (0.172 ms)?*
  - **Short Answer**: Both are sub-0.2ms noise fluctuations around constant $O((k+10)\log k)$ work since average degree $k = 10$ was held constant across all graph sizes!

### Q85. Explain the difference between worst-case, average-case, and amortized complexity using our `HashTable`.
- **Answer**: `HashTable.put` is $O(1)$ **average** (when keys spread uniformly), $O(n)$ **worst-case** (on a resize step OR if every key collides in one bucket), and $O(1)$ **amortized** over a sequence of $n$ inserts because expensive 2x resizes happen only after powers of 2 ($16, 32, 64, \dots$).
- **Follow-up**: *What is the total work of inserting $n$ distinct keys into an empty doubling HashTable?*
  - **Short Answer**: $n + n/2 + n/4 + \dots < 2n = O(n)$ total, hence $O(1)$ amortized per insertion!

### Q86. Why is the space complexity of `SocialGraph` $O(V + E)$ rather than $O(V \cdot E)$?
- **Answer**: Each vertex appears once as a key in `_adj` ($O(V)$), and each undirected edge $\{u, v\}$ appears exactly twice across all adjacency lists (once in `adj[u]` and once in `adj[v]`), totaling $2|E|$ entries. Hence total space is $\Theta(V + 2E) = O(V + E)$.
- **Follow-up**: *What is the sum of degrees of all vertices in any undirected graph (Handshaking Lemma)?*
  - **Short Answer**: $\sum_{v \in V} \deg(v) = 2|E|$.

### Q87. What is the time and space complexity of `merge_sort` and why can't comparison-based sorting beat $O(n \log n)$?
- **Answer**: `merge_sort` satisfies $T(n) = 2T(n/2) + O(n) \implies \Theta(n \log n)$ time and $O(n)$ auxiliary space. Any comparison sort must distinguish $n!$ permutations via a binary decision tree of height at least $\log_2(n!) = \Omega(n \log n)$ (Stirling's approximation).
- **Follow-up**: *How can Radix Sort or Counting Sort beat $O(n \log n)$?*
  - **Short Answer**: They are non-comparison sorts that exploit bounded integer keys or fixed-length digits, running in $O(n + k)$ or $O(d(n + b))$.

### Q88. Why does `SuggestionEngine.recommend` scale with $O(d^2)$ instead of $O(V)$ on sparse graphs?
- **Answer**: A student with degree $d$ has $d$ friends, and each friend has ~ $d$ friends, yielding at most $C \le d^2$ depth-2 candidates. BFS stops strictly at depth 2 without ever touching the rest of the $V$ students!
- **Follow-up**: *When could depth-2 BFS still touch almost the entire graph?*
  - **Short Answer**: If a student connects to a "celebrity" hub whose degree is $\Theta(V)$ — then $d_{\text{neighbor}} \approx V$!

### Q89. What is the space complexity of `AVLTree.inorder()` vs `AVLTree.search()`?
- **Answer**: `search()` is iterative (`while current is not None`) so it uses $O(1)$ extra space and $O(\log V)$ time. `inorder()` returns all $V$ students in a list (plus $O(\log V)$ recursion stack), so it takes $O(V)$ time and $O(V)$ space.
- **Follow-up**: *Could `inorder()` be written iteratively?*
  - **Short Answer**: Yes, using our `Stack` (push left spine, pop, visit, go right), with $O(\log V)$ stack space.

---

## 15. Comparisons with Course Topics (Q90–Q96)

### Q90. BFS vs. DFS — compare structures, behavior, and where CUConnect uses each.
- **Answer**: **BFS** uses a **FIFO Queue**, explores layer-by-layer, and guarantees shortest unweighted paths (used in `SocialGraph.degree_and_shortest_path` and depth-2 `SuggestionEngine`). **DFS** uses a **LIFO Stack** (or recursion), explores branch-by-branch deeply, and does NOT guarantee shortest paths — used in `CommunityDetector` (iterative DFS for connected components) and `EngagementManager` (pre-order DFS for nested comment trees).
- **Follow-up**: *Do BFS and DFS have the same Big-O time complexity on adjacency lists?*
  - **Short Answer**: Yes — both run in $O(V + E)$ time and $O(V)$ space!

### Q91. Plain BST vs. AVL Tree — compare height, operations, and trade-offs.
- **Answer**: Both maintain the BST order property (`left < root < right`) and give $O(n)$ in-order sorted traversal. A plain BST needs no rotation code or height fields, but degrades to $O(n)$ height on sorted inputs. An AVL tree stores a height per node and performs $O(1)$ rotations (LL, RR, LR, RL), guaranteeing $O(\log n)$ insert, delete, and search in ALL cases.
- **Follow-up**: *How do AVL trees compare to Red-Black trees?*
  - **Short Answer**: AVL trees are more strictly balanced (faster lookups), while Red-Black trees do fewer rotations on average during frequent insertions/deletions.

### Q92. Merge Sort vs. Quick Sort vs. Heap Sort (Sessions 13–14).
- **Answer**:
  - **Merge Sort** (ours): $O(n \log n)$ guaranteed worst-case, **stable**, $O(n)$ extra space.
  - **Quick Sort**: $O(n \log n)$ average, **$O(n^2)$ worst-case** (bad pivots), unstable, $O(\log n)$ stack space, fast cache locality.
  - **Heap Sort**: $O(n \log n)$ guaranteed worst-case, **unstable**, $O(1)$ in-place space.
  - We chose Merge Sort for guaranteed $O(n \log n)$ + stability!
- **Follow-up**: *When might Insertion Sort (Session 13) actually beat Merge Sort?*
  - **Short Answer**: On tiny arrays ($n \le 20$) or nearly sorted lists, where Insertion Sort runs in nearly $O(n)$ with minimal overhead (which is why Python's Timsort combines Merge Sort + Insertion Sort!).

### Q93. Array (Python `list`) vs. Singly Linked List vs. Doubly Linked List (Sessions 3–5).
- **Answer**: **Arrays** offer $O(1)$ random index access and great cache locality, but $O(n)$ front insertion/deletion. **Singly Linked Lists** offer $O(1)$ head insert/delete and pointer-based streaming (`FeedEngine`), but $O(n)$ random access and no backward pointer. **Doubly Linked Lists** add `prev` pointers enabling $O(1)$ deletion given a node reference and bidirectional traversal (e.g., LRU caches), at the cost of one extra pointer per node.
- **Follow-up**: *Where would a Doubly Linked List improve CUConnect if we wanted $O(1)$ removal?*
  - **Short Answer**: Storing a `HashTable` pointing directly to each request's doubly linked queue node would reduce `Queue.remove_value` from $O(r)$ to $O(1)$!

### Q94. Hash Table: Separate Chaining vs. Open Addressing (Linear / Quadratic Probing, Double Hashing).
- **Answer**: **Separate Chaining** (ours) stores colliding keys in per-bucket linked lists: simple deletions, works even at $\alpha > 1$ (though we resize at $0.75$), extra node pointers. **Open Addressing** stores all keys directly inside the bucket array: better cache locality, no node allocations, MUST keep $\alpha < 1$, suffers clustering (primary in linear probing, secondary in quadratic), and needs tombstones for deletions.
- **Follow-up**: *How does Double Hashing eliminate clustering in open addressing?*
  - **Short Answer**: It uses a second hash function $h_2(k)$ for the probe step size so two keys colliding at $h_1(k)$ follow different probe sequences.

### Q95. Stack vs. Queue vs. Priority Queue (`MinHeap`) (Sessions 6, 7 & 15).
- **Answer**: **Stack** = LIFO ($O(1)$ push/pop: undo, back-nav, DFS). **Queue** = FIFO ($O(1)$ enqueue/dequeue: requests, BFS, notifications). **Priority Queue / MinHeap** = smallest/highest priority out first ($O(\log n)$ push/pop, $O(1)$ peek: k-way feed merge, Jaccard top-$k$, trending posts).
- **Follow-up**: *What is a Circular Queue (Session 7) and why didn't we need one here?*
  - **Short Answer**: A fixed-capacity array queue using `(idx + 1) % cap` to wrap around without shifting; our linked-list Queue grows dynamically without a fixed cap and supports arbitrary `remove_value`.

### Q96. Linear Search vs. Binary Search vs. Hash Lookup vs. Trie Lookup (Sessions 12 & 15).
- **Answer**: **Linear Search**: $O(n)$, works on unsorted data. **Binary Search**: $O(\log n)$, requires sorted array (`SocialGraph.has_edge`). **HashTable**: $O(1)$ average, exact-key match only (cannot do prefix or range queries!). **Trie**: $O(L)$ prefix lookup independent of $V$ (`UserSearchIndex`).
- **Follow-up**: *Why couldn't we use `HashTable` alone for as-you-type user search?*
  - **Short Answer**: A hash function scrambles `"aar"` and `"aarav"` into completely unrelated buckets, so a HashTable cannot find all keys starting with `"aar"` without scanning all $V$ keys.

---

## 16. Design Trade-Offs & "What If" Scenarios (Q97–Q102)

### Q97. What if CUConnect grew to 1,000,000 students? What would break first and how would you redesign it?
- **Answer**: Single-machine RAM and single-source BFS ($O(V + E)$ scanning hundreds of thousands of nodes) would become bottlenecks. Redesign: (1) Replace BFS with **Bidirectional BFS** (expanding simultaneously from source and target cuts visited vertices from $b^d$ to $2 b^{d/2}$!). (2) Partition the graph across distributed shards (e.g., Redis/graph DB) by community/college. (3) Pre-compute/fan-out home feeds asynchronously for high-follower users while keeping k-way merge for normal users.
- **Follow-up**: *Why does Bidirectional BFS speed up a 6-hop search so dramatically?*
  - **Short Answer**: At branching factor $b = 10$, depth 6 visits $\sim 10^6$ nodes; two depth-3 searches meeting in the middle visit only $\sim 2 \times 10^3 = 2,000$ nodes — 500x fewer!

### Q98. What if CUConnect changed from undirected connections (LinkedIn) to directed "Follow" edges (Instagram)?
- **Answer**: `SocialGraph` would store two `HashTable`s: `following_adj[u]` (out-neighbors) and `followers_adj[u]` (in-neighbors). `add_edge(u, v)` would no longer be symmetric. BFS shortest path would traverse `following_adj`; "mutuals" could mean mutual follows (both follow each other) or common followees; Communities would use **Strongly Connected Components** (Tarjan's or Kosaraju's algorithm) instead of undirected connected components.
- **Follow-up**: *Would the Home Feed k-way merge still work unchanged?*
  - **Short Answer**: Yes — `FeedEngine` simply iterates `following_adj[u]` instead of `neighbors(u)`!

### Q99. How would you add a "Block User" feature cleanly into CUConnect?
- **Answer**: Add a per-user `blocked: HashTable` inside `CUConnectService` (persisted in a `user_blocks(blocker, blocked)` table). When `A` blocks `B`: (1) remove edge `{A, B}` if connected, (2) remove any pending requests in either direction, (3) reject future requests/comments between `A` and `B`, and (4) filter blocked users out of `SuggestionEngine`, `UserSearchIndex`, and BFS chains.
- **Follow-up**: *Should blocking be symmetric (hide both from each other) or asymmetric?*
  - **Short Answer**: Storing directed `(blocker -> blocked)` lets only `blocker` unblock later, while checking `is_blocked(u, v) or is_blocked(v, u)` enforces mutual invisibility.

### Q100. What if a celebrity user had 50,000 connections and posted frequently — how would `FeedEngine` and `Trending` behave?
- **Answer**: In our pull-based k-way merge, building the feed for a *normal* user following 1 celebrity is still instant ($O((k + N)\log k)$). Only the celebrity's *own* feed (where $k = 50,000$) would push 50,000 heads into the heap. Production systems use a hybrid **fan-out-on-write** (push normal users' posts into followers' precomputed feed caches) + **fan-out-on-read** (merge celebrity posts at read time).
- **Follow-up**: *How does `EngagementManager.get_trending_posts` already handle users with thousands of old posts?*
  - **Short Answer**: Early exit (`if post.created_at < cutoff: break`) skips all posts older than 7 days immediately!

### Q101. What if two students register with the exact same full name (e.g., two `"Aarav Sharma"`s)?
- **Answer**: Usernames are unique (`aarav_1`, `aarav_2`). In `Trie`, `node.user_ids` is a `set[str]` storing BOTH usernames under `"aarav"` and `"sharma"`. In `AVLTree`, the sort key is `(full_name.lower(), username)` — a tuple whose second element guarantees strict uniqueness so the second Aarav never overwrites the first!
- **Follow-up**: *What would have happened if `AVLTree` keyed ONLY on `full_name.lower()`?*
  - **Short Answer**: Inserting the second Aarav Sharma would have overwritten the first student in the directory!

### Q102. What if you needed to support "mutual friends of a friend" OR range queries like "all students whose name starts between C and G"?
- **Answer**: Our `AVLTree` naturally supports range queries `[low_key, high_key]` in $O(\log V + K)$ time (where $K$ is the number of returned students) by pruning left subtrees `< low_key` and right subtrees `> high_key` during traversal — something a `HashTable` can never do!
- **Follow-up**: *Could `Trie` also list names between C and G?*
  - **Short Answer**: Yes, if child characters at each node are visited in sorted order (`merge_sort(node.children.keys())`), a Trie also visits strings in lexicographical order.

---

## 17. Ten Live-Coding Drills (Whiteboard / IDE Practice)

Practice writing each of these from scratch in 3–5 minutes without peeking!

### Drill 1: BFS Shortest Path Using a Queue and Parent Map *(Session 11)*
```python
def bfs_shortest_path(adj: dict[str, list[str]], start: str, target: str) -> list[str]:
    if start == target:
        return [start]
    visited = {start}
    parent = {start: None}
    q = Queue()
    q.enqueue(start)
    while not q.is_empty():
        curr = q.dequeue()
        for nbr in adj[curr]:
            if nbr not in visited:
                visited.add(nbr)
                parent[nbr] = curr
                if nbr == target:
                    path = []
                    node = target
                    while node is not None:
                        path.append(node)
                        node = parent[node]
                    return path[::-1]
                q.enqueue(nbr)
    return []
# Time: O(V + E), Space: O(V)
```

### Drill 2: Binary MinHeap `push` (`_sift_up`) and `pop` (`_sift_down`) *(Session 15)*
```python
def heap_push(data: list[int], val: int) -> None:
    data.append(val)
    i = len(data) - 1
    while i > 0:
        p = (i - 1) // 2
        if data[i] < data[p]:
            data[i], data[p] = data[p], data[i]
            i = p
        else:
            break

def heap_pop(data: list[int]) -> int:
    root = data[0]
    last = data.pop()
    if data:
        data[0] = last
        i, n = 0, len(data)
        while True:
            l, r, smallest = 2 * i + 1, 2 * i + 2, i
            if l < n and data[l] < data[smallest]: smallest = l
            if r < n and data[r] < data[smallest]: smallest = r
            if smallest == i: break
            data[i], data[smallest] = data[smallest], data[i]
            i = smallest
    return root
# Time: O(log n) each, Space: O(1) extra
```

### Drill 3: Trie Insert and Prefix Search *(Session 8)*
```python
def trie_insert(root, word: str, uid: str) -> None:
    curr = root
    for ch in word.lower():
        if not curr.children.contains(ch):
            curr.children.put(ch, TrieNode())
        curr = curr.children.get(ch)
    curr.user_ids.add(uid)

def trie_prefix(root, prefix: str) -> list[str]:
    curr = root
    for ch in prefix.lower():
        curr = curr.children.get(ch)
        if curr is None:
            return []
    found, st = set(), Stack()
    st.push(curr)
    while not st.is_empty():
        node = st.pop()
        found.update(node.user_ids)
        for child in node.children.values():
            st.push(child)
    return merge_sort(list(found))
# Insert: O(L), Prefix Search: O(L + M + U log U)
```

### Drill 4: Reverse a Singly Linked List In-Place *(Session 4)*
```python
def reverse_linked_list(head: ListNode | None) -> ListNode | None:
    prev = None
    curr = head
    while curr is not None:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev
# Time: O(n), Space: O(1)
```

### Drill 5: Polynomial Rolling Hash + Separate-Chaining `put` *(Session 15)*
```python
def poly_hash(key: str, base: int = 31, mod: int = 1_000_000_007) -> int:
    h = 0
    for ch in key:
        h = (h * base + ord(ch)) % mod
    return h

# Inside HashTable.put(key, value):
idx = poly_hash(key) % self._capacity
curr = self._buckets[idx]
while curr is not None:
    if curr.key == key:
        curr.value = value
        return
    curr = curr.next
self._buckets[idx] = _ChainNode(key, value, self._buckets[idx])
self._size += 1
if self._size / self._capacity > 0.75:
    self._resize(self._capacity * 2)
# Time: O(1) amortized average
```

### Drill 6: Linked-List Queue `remove_value` Updating `_tail` Safely *(Session 7)*
```python
def remove_value(self, target) -> bool:
    prev, curr = None, self._head
    while curr is not None:
        if curr.value == target:
            if prev is None:
                self._head = curr.next
            else:
                prev.next = curr.next
            if curr is self._tail:      # Critical! Keep tail valid for future enqueues.
                self._tail = prev
            self._size -= 1
            return True
        prev, curr = curr, curr.next
    return False
# Time: O(n), Space: O(1)
```

### Drill 7: AVL Tree Single Right Rotation (LL Fix) *(Session 10)*
```python
def rotate_right(y: AVLNode) -> AVLNode:
    x = y.left
    t2 = x.right
    x.right = y
    y.left = t2
    # Update lower node y FIRST, then new root x!
    y.height = 1 + max(height(y.left), height(y.right))
    x.height = 1 + max(height(x.left), height(x.right))
    return x
# Time: O(1), Space: O(1)
```

### Drill 8: Two-Pointer Sorted Mutual-Connections Intersection *(Sessions 3 & 11)*
```python
def mutual_sorted(a: list[str], b: list[str]) -> list[str]:
    i = j = 0
    res = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            res.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return res
# Time: O(len(a) + len(b)), Space: O(min(len(a), len(b)))
```

### Drill 9: Iterative DFS Connected Components Using a Stack *(Sessions 6 & 11)*
```python
def connected_components(adj: dict[str, list[str]]) -> list[list[str]]:
    visited, comps = set(), []
    for start in adj:
        if start in visited:
            continue
        comp, st = [], Stack()
        visited.add(start)
        st.push(start)
        while not st.is_empty():
            u = st.pop()
            comp.append(u)
            for v in adj[u]:
                if v not in visited:
                    visited.add(v)
                    st.push(v)
        comps.append(comp)
    return comps
# Time: O(V + E), Space: O(V)
```

### Drill 10: Stable Merge Sort *(Session 14)*
```python
def merge_sort(arr: list[int]) -> list[int]:
    if len(arr) <= 1:
        return list(arr)
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    merged, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:       # '<=' guarantees stability!
            merged.append(left[i]); i += 1
        else:
            merged.append(right[j]); j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged
# Time: O(n log n) always, Space: O(n)
```
