# CUConnect — File-by-File Code Walkthrough & 60-Second Viva Scripts

This guide walks through **every source file** in CUConnect in plain, student-friendly language so every teammate can confidently explain any file, function, or tricky line during the 40-mark individual viva.

---

## Part A: Hand-Written Data Structures (`core/ds/`)

### 1. `core/ds/hash_table.py` — `HashTable` *(Session 15: Heaps and Hash Tables)*
- **What it does**: Implements a key-value map from scratch using separate chaining, a custom polynomial rolling hash (`base = 31`, `mod = 1_000_000_007`), and automatic 2x resizing whenever `load_factor > 0.75`.
- **Why chosen**: Accounts (`username -> User`), graph adjacency lists (`username -> neighbors`), post IDs, per-post likes, and Trie child links all require $O(1)$ average lookup without importing external containers or calling Python's built-in `hash()`. Separate chaining was chosen over open addressing because deletions are frequent and chaining needs no tombstones.
- **Key functions step-by-step**:
  - `_polynomial_hash(key)`: loops over each character `ch`, computing `h = (h * 31 + ord(ch)) % 1_000_000_007`.
  - `put(key, value)`: computes bucket `index = hash % capacity`, walks `_ChainNode` chain to update in place if found; else prepends a new `_ChainNode`, increments `_size`, and calls `_resize(capacity * 2)` if `size / capacity > 0.75`.
  - `get(key, default)` / `contains(key)`: hashes to bucket and scans its short chain.
  - `remove(key)`: keeps `previous` and `current` pointers to unlink the matching node (updating `self._buckets[index]` if deleting the chain head).
  - `_resize(new_capacity)`: allocates a fresh bucket array and relinks every existing `_ChainNode` into its **new** bucket `hash % new_capacity`.
- **Tricky lines explained**:
  - `next_node = current.next` inside `_resize`: we **must** save `current.next` before overwriting `current.next = new_buckets[index]`, otherwise we would lose the rest of the old bucket chain!
  - `isinstance(key, int) and not isinstance(key, bool)`: in Python `bool` subclasses `int`, so checking `not isinstance(key, bool)` keeps boolean keys cleanly separated if ever passed.
- **Complexity**: `put/get/remove/contains`: $O(1)$ average ($O(n)$ worst case); `put` amortized $O(1)$ across resizes; `keys/values/items`: $O(n + \text{capacity})$; Space: $O(n + \text{capacity})$.
- **60-Second Spoken Explanation**:
  > *"Our `HashTable` in `core/ds/hash_table.py` replaces Python's dictionary for all core indexes — users, graph adjacency lists, post IDs, likes, and Trie children. We never call Python's built-in `hash()`. Instead, `_polynomial_hash` multiplies the running hash by prime 31 and adds each character's ASCII code modulo $10^9+7$, which ensures anagrams like `'abc'` and `'cba'` hash to different buckets. Collisions are handled with separate chaining using `_ChainNode` linked lists, because we delete entries often and chaining doesn't suffer from tombstone buildup like open addressing. Whenever `size / capacity` exceeds 0.75, `_resize` doubles the bucket array and rehashes every node into its new bucket index, keeping average lookup and insertion $O(1)$."*

---

### 2. `core/ds/linked_list.py` — `SinglyLinkedList` & `ListNode` *(Session 4: Singly Linked Lists)*
- **What it does**: Provides a singly linked list with `insert_head`, `delete_value`, `delete_by_id`, `traverse`, `head` pointer access, and `__len__`.
- **Why chosen**: Each student's posts are always displayed newest-first. Prepending at the head is $O(1)$ (unlike inserting at index 0 of a Python list, which shifts elements in $O(n)$) and keeps the list naturally sorted newest-first so `FeedEngine` can perform a direct pointer-based k-way merge.
- **Key functions step-by-step**:
  - `insert_head(value)`: creates `ListNode(value, self._head)`, sets `self._head = new_node`, increments `_size`.
  - `delete_by_id(target_id, id_getter)`: walks with `previous` and `current`; when `id_getter(current.value) == target_id`, bypasses `current` (handling `previous is None` for head removal).
  - `traverse()`: walks `current = current.next` until `None`, appending values into a Python list.
- **Tricky lines explained**:
  - Exposing `head` as a read-only `@property` lets `FeedEngine` push `ListNode` objects directly into `MinHeap` and advance via `top_node.next` without breaking encapsulation.
- **Complexity**: `insert_head`, `head`, `is_empty`, `__len__`: $O(1)$; `delete_value`, `delete_by_id`, `traverse`: $O(n)$; Space: $O(n)$.
- **60-Second Spoken Explanation**:
  > *"In `core/ds/linked_list.py`, `SinglyLinkedList` stores each student's text posts. Whenever a student publishes a post, `insert_head` prepends a new `ListNode` in strict $O(1)$ time with zero shifting. Because newer posts always go to the front, every student's list stays permanently sorted newest-first. Deleting a post uses `delete_by_id` with a `previous` and `current` pointer in $O(P_u)$ time, carefully updating `_head` if the newest post is deleted. Most importantly, exposing the `head` node allows our home feed engine to run a k-way merge by holding just one pointer per friend inside a `MinHeap`."*

---

### 3. `core/ds/queue_ds.py` — `Queue` *(Session 7: Queues)*
- **What it does**: Linked-list FIFO queue maintaining both `_head` (front) and `_tail` (rear) pointers, supporting `enqueue`, `dequeue`, `peek`, `is_empty`, `remove_value`, `remove_where`, and `to_list`.
- **Why chosen**: Used in three places — pending incoming/outgoing connection requests, BFS frontier traversal, and per-user notifications. Keeping `_head` and `_tail` gives strict $O(1)$ `enqueue` and `dequeue`, avoiding Python's $O(n)$ `list.pop(0)`. `remove_value` / `remove_where` is essential because users accept, reject, or cancel connection requests out of FIFO order.
- **Key functions step-by-step**:
  - `enqueue(value)`: appends a `_QueueNode` at `_tail.next` and moves `_tail`; if empty, sets both `_head` and `_tail`.
  - `dequeue()`: removes `_head`; if `_head` becomes `None`, resets `_tail = None` too.
  - `remove_value(target)` / `remove_where(predicate)`: walks `previous`/`current`, unlinks matching node, and updates `_tail = previous` if the rear node was removed.
- **Tricky lines explained**:
  - `if current is self._tail: self._tail = previous`: forgetting this line is a classic linked-queue bug — if you delete the last item and later call `enqueue`, the new node would attach to the deleted ghost node instead of the queue!
- **Complexity**: `enqueue`, `dequeue`, `peek`, `is_empty`, `__len__`: $O(1)$; `remove_value`, `remove_where`, `to_list`: $O(n)$; Space: $O(n)$.
- **60-Second Spoken Explanation**:
  > *"Our `Queue` in `core/ds/queue_ds.py` is backed by a singly linked list with both `_head` and `_tail` pointers so `enqueue` and `dequeue` run in strict $O(1)$ time — unlike a Python list where `pop(0)` shifts every item in $O(n)$. It powers three features: BFS level-order exploration, per-user notification queues, and pending connection request queues. Because a student can accept, reject, or cancel a connection request out of arrival order, we also wrote `remove_value` and `remove_where`, paying special attention to move `_tail` back to `previous` whenever the rear node is removed."*

---

### 4. `core/ds/stack.py` — `Stack` *(Session 6: Stacks)*
- **What it does**: LIFO stack backed by `_StackNode` links supporting `push`, `pop`, `peek`, `is_empty`, `clear`, `to_list`, and `__len__`.
- **Why chosen**: Powers engine Undo history (`send_request` / `remove_connection`), console app back-navigation (`ScreenNavigator`), Trie bottom-up branch pruning, and iterative DFS connected-components discovery.
- **Key functions step-by-step**:
  - `push(value)`: `self._top = _StackNode(value, self._top)` in $O(1)$.
  - `pop()`: reads `self._top.value`, advances `self._top = self._top.below`, decrements `_size`.
- **Tricky lines explained**:
  - `to_list()` walks from `_top` downward (most recent first), so `ScreenNavigator.breadcrumb()` calls `.reverse()` on the returned list to print `Home > Connections` left-to-right.
- **Complexity**: `push`, `pop`, `peek`, `is_empty`, `clear`, `__len__`: $O(1)$; `to_list`: $O(n)$; Space: $O(n)$.
- **60-Second Spoken Explanation**:
  > *"In `core/ds/stack.py`, `Stack` is a linked-node LIFO structure with strict $O(1)$ `push`, `pop`, and `peek`. We use the exact same `Stack` class in four places: reversing the user's most recent send-request or remove-connection action, powering back-navigation breadcrumbs in the console app, pruning empty nodes bottom-up in `Trie.remove`, and driving iterative DFS in `CommunityDetector` so large networks never hit Python's recursion limit."*

---

### 5. `core/ds/heap.py` — `MinHeap` *(Session 15: Heaps and Hash Tables & Session 7: Priority Queues)*
- **What it does**: Array-based binary min-heap accepting an optional `key` function (so negated keys create a Max-Heap) and providing `push`, `pop`, `peek`, `is_empty`, and `__len__`.
- **Why chosen**: Powers top-k ranking in `SuggestionEngine`, k-way feed merging in `FeedEngine`, and top-k recent post ranking in `EngagementManager.get_trending_posts`.
- **Key functions step-by-step**:
  - `push(item)`: wraps item as `(key_fn(item), self._counter, item)`, increments `_counter`, appends to `_data`, calls `_sift_up(last_index)`.
  - `pop()`: saves root item `_data[0][2]`, moves the last leaf into `_data[0]`, calls `_sift_down(0)`.
  - `_sift_up(i)`: swaps with `parent = (i - 1) // 2` while smaller.
  - `_sift_down(i)`: compares with `left = 2*i + 1` and `right = 2*i + 2`, swaps with the smaller child until heap order holds.
- **Tricky lines explained**:
  - Storing `(priority, self._counter, item)` solves **two** problems at once: (1) deterministic FIFO tie-breaking on equal keys, and (2) Python never attempts `Post < Post` (which would raise `TypeError` on non-ordered dataclasses!).
- **Complexity**: `push`, `pop`: $O(\log n)$; `peek`, `__len__`: $O(1)$; Space: $O(n)$.
- **60-Second Spoken Explanation**:
  > *"Our array-based `MinHeap` in `core/ds/heap.py` stores a complete binary tree inside a flat list using parent `(i-1)//2` and children `2i+1`, `2i+2`. It accepts a `key` function so negating scores or timestamps turns it into a Max-Heap for our Home Feed, People You May Know, and Trending Posts without duplicating code. Each entry stores a 3-tuple `(priority, counter, item)`: if two posts share the exact same timestamp, the monotonic counter breaks ties deterministically and prevents Python from crashing trying to compare dataclass objects. Push and pop both run in $O(\log n)$ via `_sift_up` and `_sift_down`."*

---

### 6. `core/ds/trie.py` — `Trie` & `TrieNode` *(Session 8: Trees & Session 3: Strings)*
- **What it does**: Case-insensitive prefix tree mapping lowercase words to sets of matching `user_id`s, supporting `insert`, `remove` (with empty-branch pruning), and `prefix_search(prefix, limit)`.
- **Why chosen**: As-you-type user search should scale with prefix length $L$ ($O(L)$), not total user count $V$.
- **Key functions step-by-step**:
  - `insert(word, user_id)`: walks each character using `TrieNode.children` (our compact `HashTable(initial_capacity=4)`), creating missing nodes, and adds `user_id` at the final node.
  - `remove(word, user_id)`: pushes `(parent, ch, child)` onto our `Stack` while descending; after removing `user_id`, pops the stack to prune any node with zero `user_ids` and zero children.
  - `prefix_search(prefix, limit)`: walks down to the prefix node in $O(L)$, then collects all `user_ids` in its subtree via iterative DFS using our `Stack`, returning them sorted with `merge_sort`.
- **Tricky lines explained**:
  - `HashTable(initial_capacity=4)` inside `TrieNode` keeps memory small even across 5,000 users (~25,000 nodes) while remaining 100% built on our hand-written `HashTable`.
  - Returning `[]` for an empty prefix avoids dumping the entire campus database when the search box is blank.
- **Complexity**: `insert` / `remove`: $O(L)$; `prefix_search`: $O(L + M + U \log U)$; Space: $O(\text{total unique prefixes})$.
- **60-Second Spoken Explanation**:
  > *"In `core/ds/trie.py`, `Trie` powers live search suggestions. Each `TrieNode` stores child edges in a compact 4-bucket instance of our own `HashTable` and keeps a set of `user_ids` matching the word ending there. Insertion walks character-by-character in $O(L)$. When a user edits their name, `remove` pushes the path onto our `Stack` and prunes dead branches bottom-up so stale tokens don't leak memory. `prefix_search` descends to the prefix node in $O(L)$ independent of total user count, collects all `user_ids` in that subtree via iterative DFS, and sorts them with our `merge_sort`."*

---

### 7. `core/ds/algorithms.py` — `merge_sort` & `binary_search` *(Sessions 12 & 14)*
- **What it does**: Provides stable top-down divide-and-conquer `merge_sort(items, key, reverse)` and iterative `binary_search(sorted_items, target, key)`.
- **Why chosen**: Replaces Python's built-in `sorted()` everywhere in `core/` (alphabetical listings, community ordering, startup hydration sorting) and gives $O(\log d)$ edge checks in `SocialGraph.has_edge`.
- **Key functions step-by-step**:
  - `merge_sort`: splits list at `mid = n // 2`, recursively sorts both halves, calls `_merge`.
  - `_merge`: uses `left_key <= right_key` (ascending) or `>=` (descending) to guarantee **stability**.
  - `binary_search`: maintains `low`/`high`, computes `mid = low + (high - low) // 2`, halves the search window each iteration.
- **Tricky lines explained**:
  - Using `<=` instead of `<` in `_merge` is what makes Merge Sort **stable** — when two items tie on key, the left item (which appeared earlier in input) is always emitted first.
- **Complexity**: `merge_sort`: $O(n \log n)$ time (best, avg, worst), $O(n)$ space; `binary_search`: $O(\log n)$ time, $O(1)$ space.
- **60-Second Spoken Explanation**:
  > *"Because built-in `sorted()` is disallowed in our core engine, we wrote `merge_sort` and `binary_search` in `core/ds/algorithms.py`. We chose Merge Sort over Quick Sort and Heap Sort because it guarantees $O(n \log n)$ even on already-sorted data and is stable — achieved by using `<=` during the merge step. `binary_search` runs in $O(\log n)$ time and $O(1)$ space, and is called directly by `SocialGraph.has_edge` to check whether two students are connected on our sorted adjacency lists."*

---

### 8. `core/ds/avl_tree.py` — `AVLTree` & `AVLNode` *(Session 10: AVL Trees)*
- **What it does**: Self-balancing Binary Search Tree storing `(key, value)` pairs with explicit `_rotate_right`, `_rotate_left`, `_rebalance` (LL, RR, LR, RL), `insert`, `delete`, `search`, `inorder`, `height`, and `is_balanced`.
- **Why chosen**: Maintains the alphabetical "Browse All Students" directory in permanently sorted order without re-sorting on every page view, avoiding the $O(V)$ skewed-tree worst case of a plain BST if students register alphabetically.
- **Key functions step-by-step**:
  - `_rebalance(node)`: updates `node.height`, computes `balance = height(left) - height(right)`:
    - `balance > 1`: if `balance(left) < 0` → left-rotate `node.left` (**LR**), then right-rotate `node` (**LL/LR**).
    - `balance < -1`: if `balance(right) > 0` → right-rotate `node.right` (**RL**), then left-rotate `node` (**RR/RL**).
  - `_delete_node`: handles 0, 1, or 2 children (replacing 2-child node with its in-order successor `_min_node(node.right)`) and rebalances on the unwind!
  - `inorder()`: Left → Root → Right traversal yielding exact alphabetical order in $O(V)$.
- **Tricky lines explained**:
  - In `_rotate_right(y)`, we **must** call `_update_height(y)` BEFORE `_update_height(x)` because `y` is now a child of `x`, so `x`'s height depends on `y`'s newly recomputed height!
- **Complexity**: `insert`, `delete`, `search`: $O(\log V)$; `inorder`: $O(V)$; Space: $O(V)$.
- **60-Second Spoken Explanation**:
  > *"In `core/ds/avl_tree.py`, `AVLTree` maintains our alphabetical 'Browse All Students' directory keyed by `(full_name.lower(), username)`. If students joined in alphabetical order, a regular BST would collapse into a linked list of height $V$. Our `_rebalance` helper checks `balance_factor = height(left) - height(right)` after every insert or delete and fixes all four textbook imbalances: LL with a single right rotation, RR with a single left rotation, LR with left-then-right, and RL with right-then-left. Height stays strictly logarithmic — just 5 for our 18 seeded students — and in-order traversal lists everyone A–Z in $O(V)$."*

---

## Part B: Core Domain Modules (`core/`)

### 9. `core/models.py` *(Sessions 1–2)*
- **What it does**: Defines all clean domain `@dataclass` entities (`User`, `ConnectionRequest`, `DegreeResult`, `Suggestion`, `Post`, `Comment`, `Notification`, `TrendingPost`, `CommunityInfo`, `UndoAction`) and the custom exception hierarchy (`CUConnectError`, `AuthError`, `UserNotFoundError`, `ValidationError`, `ConnectionRuleError`, `AuthorizationError`, `ResourceNotFoundError`).
- **Tricky line**: `ConnectionRequest.__eq__` compares only `(sender, receiver)` so `Queue.remove_value(req)` matches cleanly by directed edge endpoints.
- **60-Second Spoken Explanation**:
  > *"`core/models.py` holds our pure data containers and explicit exception types. Separating typed exceptions like `AuthorizationError` vs `ConnectionRuleError` lets both the console app and Streamlit display clear messages to users and lets our unit tests verify exact failure rules. `User.public_profile()` deliberately omits `password_hash` so sensitive hashes never leak to presentation code."*

### 10. `core/auth.py` — `AccountManager` *(Session 15)*
- **What it does**: Stores `username -> User` and active sessions in hand-written `HashTable`s; hashes passwords with salted PBKDF2-HMAC-SHA256 (`100,000` rounds, 16-byte `os.urandom` salt) and verifies in constant time with `hmac.compare_digest`.
- **Tricky line**: `_DUMMY_HASH` — when a username doesn't exist during `login()`, we still run `verify_password(password, self._DUMMY_HASH)` before raising `AuthError("Invalid username or password.")` so attackers cannot distinguish unknown usernames by response timing.
- **Complexity**: `register_user` / `login` / `logout` / `get_user`: $O(1)$ average HashTable + fixed PBKDF2 work.
- **60-Second Spoken Explanation**:
  > *"`core/auth.py` manages user accounts inside our hand-written `HashTable`. Every password gets its own 16-byte random salt and 100,000 iterations of PBKDF2-SHA256, stored as `pbkdf2_sha256$100000$<salt>$<hash>`. During login, we use `hmac.compare_digest` for constant-time comparison and even run a dummy PBKDF2 hash when a username isn't found, raising the exact same `'Invalid username or password.'` error either way so account existence is never leaked."*

### 11. `core/graph.py` — `SocialGraph` *(Sessions 11 & 12)*
- **What it does**: Models accepted connections $G(V, E)$ as a `HashTable` mapping `username -> sorted list[str]`. Implements `add_edge`, `remove_edge`, `has_edge` (via `binary_search`), `mutual_connections` (two-pointer sorted intersection), and `degree_and_shortest_path` (unweighted BFS using our `Queue` + `parent` map).
- **Tricky line**: In `degree_and_shortest_path`, we add `neighbor` to `visited` **at enqueue time** (not dequeue time) so the same vertex is never pushed into the `Queue` twice from different parents in the same layer.
- **Complexity**: `has_edge`: $O(\log d)$; `add_edge`/`remove_edge`/`mutual_connections`: $O(d_u + d_v)$; `degree_and_shortest_path`: $O(V + E)$ time, $O(V)$ space.
- **60-Second Spoken Explanation**:
  > *"`SocialGraph` in `core/graph.py` stores our undirected campus network as sorted adjacency lists inside our `HashTable`. Because social graphs are sparse, adjacency lists use $O(V+E)$ memory instead of $O(V^2)$. Keeping each neighbor list sorted lets `has_edge` run `binary_search` in $O(\log d)$, lets `mutual_connections` do a single-pass two-pointer intersection in $O(d_u + d_v)$, and makes BFS deterministic. For degrees and shortest chains, BFS uses our linked-list `Queue`, marks nodes visited on enqueue, records a `parent` pointer, stops early when the target is found, and backtracks to return the shortest chain plus label `'1st'`, `'2nd'`, `'3rd'`, or `'3+'`."*

### 12. `core/connections.py` — `ConnectionManager` *(Sessions 7 & 11)*
- **What it does**: Stores per-user incoming and outgoing pending request `Queue`s inside `HashTable`s and enforces every workflow invariant (no self-request, no duplicates, no already-connected, reverse auto-accept, receiver-only accept/reject, sender-only cancel, bidirectional disconnect).
- **Tricky line**: In `accept_request(actor, sender)`, if `(sender -> actor)` isn't found we check `has_pending_request(actor, sender)` so that if the *sender* mistakenly tries to accept their own outgoing request, we raise `AuthorizationError("Only the receiver can accept...")` rather than a generic not-found error!
- **Complexity**: `send_request` / `accept_request`: $O(\deg(u) + \deg(v) + r)$; `reject_request` / `cancel_request`: $O(r)$.
- **60-Second Spoken Explanation**:
  > *"`ConnectionManager` in `core/connections.py` models pending requests as directed edges stored in two per-user `Queue`s — the sender's outgoing queue and the receiver's incoming queue. Every rule in the specification is enforced explicitly: unknown users, self-requests, duplicate requests, and requests to existing connections all raise descriptive errors. If Bob already requested Alice and Alice requests Bob, `send_request` removes the reverse request from both queues, adds the undirected edge immediately, and returns `'auto_accepted'`. Accepting, rejecting, or cancelling out of FIFO order uses our Queue's `remove_where`/`remove_value`."*

### 13. `core/posts.py` — `PostManager` *(Sessions 4 & 15)*
- **What it does**: Maps `username -> SinglyLinkedList` (newest post at head) and `post_id -> Post` inside `HashTable`s. Supports `create_post`, `get_user_posts`, `get_user_post_head`, `get_post`, and author-only `delete_post`.
- **Complexity**: `create_post` / `get_post`: $O(1)$ avg; `get_user_posts` / `delete_post`: $O(P_u)$.
- **60-Second Spoken Explanation**:
  > *"`PostManager` gives each student a `SinglyLinkedList` stored inside a `HashTable`, plus a second `HashTable` indexing `post_id -> Post` for $O(1)$ lookup during likes, comments, and deletes. Creating a post validates non-empty text and calls `insert_head` in $O(1)$, keeping each user's timeline newest-first. Deletion checks `post.author == actor` before unlinking via `delete_by_id`."*

### 14. `core/feed.py` — `FeedEngine` *(Sessions 4, 7 & 15)*
- **What it does**: Runs a k-way merge across the `head` `ListNode` of each of a user's $k$ connections using `MinHeap(key=lambda n: (-n.value.created_at, -n.value.seq_id))`, supporting `limit` and `offset` pagination and returning `(page, has_more)`.
- **Tricky line**: Pushing `top_node.next` only after popping `top_node` keeps the heap size bounded at $\le k$ (number of connections), never growing to total post count $P$!
- **Complexity**: Time $O((k + \text{offset} + \text{limit}) \log k)$, Space $O(k + \text{limit})$.
- **60-Second Spoken Explanation**:
  > *"`FeedEngine` builds the newest-first home feed using a textbook k-way merge. Because every connection's `SinglyLinkedList` is already ordered newest-first, we only push the head `ListNode` of each of the user's $k$ connections into our `MinHeap` with negated `(created_at, seq_id)`. Each pop yields the next newest post globally and pushes `top_node.next` if it exists. That delivers paginated pages in $O((k + N)\log k)$ — measured at 0.09 milliseconds even on 5,000 users!"*

### 15. `core/suggestions.py` — `SuggestionEngine` *(Sessions 11 & 15)*
- **What it does**: Implements "People You May Know": Depth-2 BFS with our `Queue` finds all non-connected 2nd-degree candidates, filters pending requests, computes exact Jaccard coefficient $J(u,v) = \frac{|N(u)\cap N(v)|}{\deg(u)+\deg(v)-|N(u)\cap N(v)|}$, and ranks top-$k$ via `MinHeap`.
- **Tricky line**: `if depth >= 2: continue` ensures BFS never expands edges *leaving* depth-2 nodes, saving huge work on dense graphs while strictly capturing every 2nd-degree peer.
- **Complexity**: Time $O(\sum_{w \in N(u)} \deg(w) + C(\deg(u)+\deg(c)) + C \log C)$; Space $O(\deg(u) + C)$.
- **60-Second Spoken Explanation**:
  > *"`SuggestionEngine` runs a depth-2 BFS using our `Queue` to find every friend-of-a-friend not already connected to the user. For each candidate, we get the mutual connections using `SocialGraph.mutual_connections` and divide by the union size `deg(u) + deg(v) - mutuals` to get the Jaccard coefficient. Pushing into our `MinHeap` keyed by `(-jaccard, -mutual_count, username)` cleanly pops the top-$k$ suggestions with deterministic tie-breaking."*

### 16. `core/search.py` — `UserSearchIndex` *(Sessions 3, 8 & 14)*
- **What it does**: Wraps `Trie` to index both a user's lowercase username and every regex-tokenized word of their `full_name`, reindexing cleanly on profile renames and sorting results with `merge_sort`.
- **Tricky line**: In `reindex_user`, after removing old name tokens we re-insert `updated_user.username` in case an old name word happened to match the username (e.g., `"aarav"`).
- **Complexity**: `index_user`: $O(L_{\text{total}})$; `search`: $O(L + M + U \log U)$.
- **60-Second Spoken Explanation**:
  > *"`UserSearchIndex` feeds both each user's username and every word of their full name into our hand-written `Trie`. That's why typing `'sh'` finds both Aarav Sharma (by surname) and Pranav Shetty (by surname). If a student edits their name, `reindex_user` strips old tokens from the Trie and indexes the new ones automatically."*

### 17. `core/notifications.py` — `NotificationManager` *(Sessions 7 & 15)*
- **What it does**: Stores per-user FIFO `Queue`s of `Notification` records inside a `HashTable`, plus an ID lookup `HashTable` for $O(1)$ `mark_read`. Supports `unread_count` and `mark_all_read`.
- **Complexity**: `notify` / `mark_read`: $O(1)$ avg; `get_notifications` / `unread_count` / `mark_all_read`: $O(N_u)$.
- **60-Second Spoken Explanation**:
  > *"`NotificationManager` gives every student a FIFO `Queue` inside a `HashTable` to store connection requests, acceptances, likes, comments, and replies, paired with a `notification_id` `HashTable` so marking an individual alert as read takes $O(1)$ time."*

### 18. `core/engagement.py` — `EngagementManager` *(Sessions 8 & 15)*
- **What it does**: Handles three enhancements cleanly: (1) Per-post likes `HashTable` (`post_id -> HashTable[username -> ts]`); (2) N-ary `Comment` trees rendered via recursive **Pre-Order DFS** (`get_comments_preorder`); (3) Recent **Trending Posts** (`likes + 2 * total_comments` over 7 days) ranked top-$k$ using `MinHeap`.
- **Tricky line**: In `get_trending_posts`, `if post.created_at < cutoff: break` exits early out of each friend's `SinglyLinkedList` because all remaining nodes in that list are guaranteed older!
- **Complexity**: `like_post`/`has_liked`: $O(1)$ avg; `get_comments_preorder`: $O(C)$; `get_trending_posts`: $O(R \log R)$.
- **60-Second Spoken Explanation**:
  > *"`EngagementManager` implements likes, threaded comments, and trending posts. Likes use a nested `HashTable` per post so toggling is $O(1)$ and double-liking is impossible. Comments form an n-ary tree where replies attach to `parent.replies`; displaying them uses Pre-Order DFS so every reply prints directly under its parent with its exact indentation depth. Trending posts scans each connection's newest-first linked list only until the 7-day cutoff, computes `likes + 2 * comments`, and extracts the top-$k$ via `MinHeap`."*

### 19. `core/communities.py` — `CommunityDetector` *(Sessions 6 & 11)*
- **What it does**: Finds all connected components of `SocialGraph` using **iterative DFS with our hand-written `Stack`**, sorting members alphabetically and communities by descending size using `merge_sort`.
- **Tricky line**: Marking `visited.add(neighbor)` before `stack.push(neighbor)` keeps stack space bounded by $O(V)$ even on dense cliques.
- **Complexity**: Time $O(V \log V + E)$, Space $O(V)$.
- **60-Second Spoken Explanation**:
  > *"`CommunityDetector` partitions the campus graph into connected components using iterative DFS with our hand-written `Stack`. We deliberately chose iterative DFS over recursion so a 5,000-student graph never hits Python's recursion limit, and so we can directly contrast DFS (`Stack`) with BFS (`Queue`)."*

### 20. `core/service.py` — `CUConnectService` & `ScreenNavigator` *(All Sessions — Facade)*
- **What it does**: The single public facade used by both UIs. Coordinates startup hydration from SQLite, write-through commits on every mutation, injectable clock & sequence counter, per-user undo `Stack`, alphabetical `AVLTree` directory, and `ScreenNavigator` (console back-navigation `Stack`).
- **Tricky line**: During `_hydrate_from_storage()`, posts are sorted ascending by `(created_at, seq_id)` via `merge_sort` before calling `load_post` (which inserts at head) — reversing ascending order into exact newest-first linked lists! Similarly, comments are sorted by `seq_id` so every parent comment is guaranteed to exist in `_comments_by_id` before any reply referencing it is loaded!
- **60-Second Spoken Explanation**:
  > *"`CUConnectService` in `core/service.py` is the single doorway between the UI and our engine. On startup, `_hydrate_from_storage` loads all seven SQLite tables, sorts sequences with `merge_sort`, and populates every in-memory structure including our `AVLTree` student directory and per-user undo `Stack`. Every write updates memory and writes through to SQLite immediately, and `ScreenNavigator` exposes a `Stack` for console back-navigation so UIs never import `core.ds` directly."*

---

## Part C: Storage & User Interfaces

### 21. `storage/repository.py` — `SQLiteRepository` *(Part 5: Storage Only)*
- **What it does**: Manages 7 normalized SQLite3 tables with plain `SELECT *`, `INSERT`, `UPDATE`, and `DELETE` statements only. Stores undirected connections canonically (`user_a < user_b`).
- **Tricky line**: `check_same_thread=False` prevents SQLite thread-affinity errors across Streamlit rerun worker threads, while `delete_post` explicitly removes child `post_likes` and `comments` rows in one atomic `with self._conn:` transaction.
- **60-Second Spoken Explanation**:
  > *"`SQLiteRepository` is strictly a dumb persistence layer — seven clean tables and simple CRUD queries. Zero `JOIN`, `ORDER BY`, `GROUP BY`, or recursive SQL exists anywhere in the file, and our AST checker `scripts/check_rules.py` proves it automatically."*

### 22. `ui/console_app.py` — `ConsoleApp` *(Part 6 & Session 6)*
- **What it does**: Full-featured menu CLI calling only `CUConnectService` and `ScreenNavigator` (for `Stack`-based back-navigation with breadcrumb headers and `getpass` masked passwords).
- **60-Second Spoken Explanation**:
  > *"`ConsoleApp` demonstrates that our core engine is completely independent of any web framework. Every menu transition pushes onto `ScreenNavigator`'s `Stack` and pressing `'b'` pops back to the previous screen, supporting all core features and enhancements through `CUConnectService`."*

### 23. `ui/streamlit_app.py` *(Part 6)*
- **What it does**: 11-view Streamlit web app caching one live `CUConnectService` via `@st.cache_resource` so in-memory data structures persist across browser reruns while write-through SQLite guarantees durability across full restarts.
- **60-Second Spoken Explanation**:
  > *"`ui/streamlit_app.py` provides an interactive web frontend with 11 views — feed, composer, profiles, Trie search, connections & undo, Jaccard suggestions, BFS chain tool, notifications, trending, communities, and the AVL directory — calling strictly the same `CUConnectService` facade as our console app."*
