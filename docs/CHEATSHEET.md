# CUConnect — One-Page Last-Night Viva Cheatsheet

**Chanakya University | DSA (EAI212/EVE203/EEC203) | Prof. Nitish Hegde | Team: Dhruv Jha, Pranam Jogur, Nihal N**

## 1. Data Structures At-a-Glance

| Structure (`core/ds/`) | Where Used in CUConnect | Key Operations & Complexity | One-Sentence "Why" |
|---|---|---|---|
| **HashTable** (`hash_table.py`, Session 15) | Accounts (`username -> User`), Graph adj lists, Post ID index, Per-post Likes, Trie children | `put/get/remove/contains`: $O(1)$ avg, $O(n)$ worst; resize at LF $> 0.75$ | Separate chaining with base-31 polynomial rolling hash gives $O(1)$ lookup without built-in `hash()` or deletion tombstones. |
| **SinglyLinkedList** (`linked_list.py`, Session 4) | Per-user posts (`PostManager`) | `insert_head`: $O(1)$; `delete_by_id`: $O(P_u)$; `traverse`: $O(P_u)$ | Prepending at head in $O(1)$ keeps every student's posts naturally newest-first for pointer-based k-way feed merging. |
| **Queue** (`queue_ds.py`, Session 7) | Incoming/Outgoing request queues, BFS frontier, Notification queue | `enqueue/dequeue/peek`: $O(1)$; `remove_value`: $O(r)$ | Head/tail linked nodes avoid $O(n)$ `list.pop(0)` shifts, while `remove_value` handles out-of-order accept/reject/cancel. |
| **Stack** (`stack.py`, Session 6) | Engine undo history, Console back-navigation, Iterative DFS communities | `push/pop/peek`: $O(1)$ | LIFO reverses the most recent action or screen first and drives iterative DFS without hitting Python's recursion limit. |
| **MinHeap** (`heap.py`, Session 15) | Home Feed k-way merge, People You May Know top-k, Trending posts top-k | `push/pop`: $O(\log n)$; `peek`: $O(1)$ | Accepts a key function (negated keys = Max-Heap) and uses an insertion counter for crash-free deterministic tie-breaking. |
| **Trie** (`trie.py`, Session 8) | Live prefix user search (`UserSearchIndex`) | `insert/remove`: $O(L)$; `prefix_search`: $O(L + M + U \log U)$ | Walks the prefix in $O(L)$ independent of total user count $V$ and indexes both usernames and full-name words. |
| **AVLTree** (`avl_tree.py`, Session 10) | Alphabetical "Browse All Students" directory | `insert/delete/search`: $O(\log V)$; `inorder`: $O(V)$ | Explicit LL, RR, LR, RL rotations enforce $|BF| \le 1$ so height stays $\le 1.44 \log_2 V$ even on sorted sign-ups. |
| **merge_sort & binary_search** (`algorithms.py`, Sessions 12 & 14) | Sorted listings, startup hydration ordering, `SocialGraph.has_edge` | `merge_sort`: $O(n \log n)$ stable; `binary_search`: $O(\log d)$ | Guaranteed $O(n \log n)$ worst-case stability plus $O(\log d)$ edge checks on sorted adjacency lists. |

## 2. Core Graph & Algorithm Formulas

- **Graph Model**: $G(V, E)$ undirected simple graph (accepted connections in sorted adjacency lists, $O(V+E)$ space) + directed pending edges in per-user `Queue`s. No self-edges, no duplicate edges.
- **Mutual Connections**: Two-pointer intersection of sorted `adj[u]` and `adj[v]` $\rightarrow O(\deg(u) + \deg(v))$.
- **Degree & Shortest Chain (BFS)**: Uses `Queue` + `visited` (marked at enqueue!) + `parent` map $\rightarrow O(V+E)$ time, $O(V)$ space. Labels: `0=Self`, `1=1st`, `2=2nd`, `3=3rd`, `>=4=3+`, unreachable=`Not connected`.
- **Jaccard Coefficient (PYMK)**: $J(u,v) = \frac{|N(u) \cap N(v)|}{|N(u) \cup N(v)|} = \frac{m}{\deg(u) + \deg(v) - m}$ over Depth-2 BFS candidates, ranked by `MinHeap` on `(-J, -m, username)`.
- **Home Feed k-Way Merge**: Seed `MinHeap` with `head` `ListNode` of each of $k$ connections (key `(-created_at, -seq_id)`). Pop newest, push `node.next` $\rightarrow O((k + \text{offset} + N)\log k)$.
- **Trending Score**: $\text{score} = \text{likes} + 2 \times \text{total\_comments}$ over last 7 days (early-exits each friend's newest-first linked list).
- **Comments Tree**: Each `Comment` holds `replies: list[Comment]`; displayed with **Pre-Order DFS** (parent before nested replies).
- **Communities**: Connected components via **Iterative DFS + `Stack`** $\rightarrow O(V \log V + E)$.

## 3. Memorize These Exact Seed Graph Dry-Run Numbers (`@aarav`)

- **Aarav's Connections (1st degree)**: `ananya`, `diya`, `rohan` ($\deg = 3$).
- **People You May Know (2nd degree, exact fractions!)**:
  1. `meera`: 3 mutuals (`ananya`, `diya`, `rohan`), union $= 3+4-3 = 4 \implies J = \mathbf{3/4 = 0.7500}$
  2. `kabir`: 1 mutual (`diya`), union $= 3+2-1 = 4 \implies J = \mathbf{1/4 = 0.2500}$
  3. `sneha`: 1 mutual (`rohan`), union $= 3+3-1 = 5 \implies J = \mathbf{1/5 = 0.2000}$
- **BFS Degrees**: `diya` = `1st` (1) | `meera` = `2nd` (2) | `vikram` = `3rd` (3) | `isha` = `3+` (4 hops: `aarav -> rohan -> sneha -> arjun -> isha`) | `pranav` = `Not connected`.
- **Trie `"sh"`**: `aarav` (Sharma) + `pranav` (Shetty).
- **Communities**: 3 components of sizes **10, 5, 3** (accepting `pranav` merges 10 + 5 $\rightarrow$ **15**!).
- **AVL Tree**: 18 students $\rightarrow$ Height = **5**, Balanced = **True**; HashTable Load Factor = **0.562**.
- **Security**: Salted PBKDF2-SHA256 (`100,000` rounds, 16-byte random salt, `hmac.compare_digest`, dummy hash on missing user $\rightarrow$ uniform `"Invalid username or password."`).
- **Benchmarks (N = 5,000, E = 25,000)**: Feed = **0.09 ms**, Trie = **2.18 ms**, Suggestions = **3.69 ms**, BFS = **6.72 ms**.
