# scripts/build_viva_pdfs.py
# Generates two publication-grade viva PDFs directly from CUConnect's codebase & syllabus docs:
#   1. docs/VIVA_QUESTIONNAIRE.pdf         — Complete Faculty Viva Questionnaire & Model Answers
#   2. docs/10MIN_CODE_EXPLANATION_GUIDE.pdf — Compact 10-Minute Viva Code Explanation Guide
# Course mapping: Formative Assessment Understanding & Viva (40 Marks) — Sessions 1–15.

import base64
from pathlib import Path
import sys
import tempfile

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DIAGRAMS = DOCS / "diagrams"
LOGO_PATH = ROOT / "ui" / "assets" / "cuconnect_logo.png"


def _img_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


BASE_CSS = """
@page {
    size: A4;
    margin: 14mm 13mm 15mm 13mm;
}
* {
    box-sizing: border-box;
}
body {
    font-family: 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1F2937;
    font-size: 9.2pt;
    line-height: 1.42;
    margin: 0;
    padding: 0;
    background: #FFFFFF;
}
h1, h2, h3, h4 {
    margin: 0;
    color: #540B0E;
    page-break-after: avoid;
    break-after: avoid;
}

/* Cover Header Banner */
.cover-banner {
    background: linear-gradient(125deg, #540B0E 0%, #832022 58%, #335C67 100%);
    color: #FFFFFF;
    padding: 16px 20px;
    border-radius: 12px;
    border-left: 6px solid #E09F3E;
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 12px;
}
.cover-logo {
    background: #FFF3B0;
    padding: 8px 10px;
    border-radius: 10px;
    flex-shrink: 0;
}
.cover-logo img {
    height: 54px;
    width: auto;
    display: block;
}
.cover-kicker {
    font-size: 7.8pt;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #FFF3B0;
    margin-bottom: 3px;
}
.cover-title {
    font-size: 16.5pt;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.15;
    margin-bottom: 4px;
}
.cover-sub {
    font-size: 9pt;
    color: #FDEFD1;
    line-height: 1.35;
}

/* Metadata Strip */
.meta-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 12px;
}
.meta-box {
    background: #FAF8F5;
    border: 1px solid #E5DDD0;
    border-top: 3px solid #335C67;
    border-radius: 8px;
    padding: 6px 9px;
}
.meta-box.gold { border-top-color: #E09F3E; }
.meta-box.auburn { border-top-color: #9E2A2B; }
.meta-label {
    font-size: 7pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #6B7280;
}
.meta-val {
    font-size: 8.7pt;
    font-weight: 700;
    color: #1F2937;
    margin-top: 1px;
}

/* Section Headers */
.sec-head {
    background: #FFF3B0;
    border-left: 5px solid #9E2A2B;
    border-radius: 6px;
    padding: 6px 11px;
    margin: 13px 0 8px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    page-break-after: avoid;
    break-after: avoid;
}
.sec-head h2 {
    font-size: 11pt;
    font-weight: 800;
    color: #540B0E;
}
.sec-tag {
    font-size: 7.4pt;
    font-weight: 700;
    color: #FFFFFF;
    background: #335C67;
    padding: 2px 8px;
    border-radius: 999px;
}

/* Q&A Cards */
.qa-card {
    border: 1px solid #E6DFD3;
    border-radius: 8px;
    padding: 7px 10px;
    margin-bottom: 7px;
    background: #FFFFFF;
    break-inside: avoid;
    page-break-inside: avoid;
}
.qa-q {
    font-weight: 800;
    color: #540B0E;
    font-size: 9.2pt;
    margin-bottom: 3px;
}
.qa-num {
    display: inline-block;
    background: #9E2A2B;
    color: #FFFFFF;
    font-size: 7.5pt;
    font-weight: 800;
    padding: 1px 6px;
    border-radius: 4px;
    margin-right: 5px;
    vertical-align: 1px;
}
.qa-a {
    color: #1F2937;
    font-size: 8.85pt;
    margin-bottom: 3px;
}
.qa-trap {
    background: #FAF8F5;
    border-left: 3px solid #E09F3E;
    padding: 3.5px 7px;
    border-radius: 0 5px 5px 0;
    font-size: 8.3pt;
    color: #374151;
    margin-top: 3px;
}
.qa-trap strong {
    color: #92400E;
}

/* Code Explanation Cards (10-Min Guide) */
.code-card {
    border: 1px solid #E2D9CB;
    border-radius: 9px;
    margin-bottom: 9px;
    overflow: hidden;
    background: #FFFFFF;
    break-inside: avoid;
    page-break-inside: avoid;
}
.code-card-head {
    background: #F6F2EA;
    border-bottom: 1px solid #E2D9CB;
    padding: 6px 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 5px;
}
.code-card-title {
    font-weight: 800;
    font-size: 9.6pt;
    color: #540B0E;
}
.code-file {
    font-family: 'Cascadia Code', Consolas, monospace;
    font-size: 8pt;
    background: #EAF2F4;
    color: #244751;
    padding: 1px 6px;
    border-radius: 4px;
    margin-left: 5px;
    font-weight: 700;
}
.pill-row {
    display: flex;
    gap: 4px;
    align-items: center;
    flex-wrap: wrap;
}
.badge {
    font-size: 7.2pt;
    font-weight: 700;
    padding: 1.5px 6px;
    border-radius: 999px;
}
.b-time { background: #9E2A2B; color: #FFFFFF; }
.b-sess { background: #335C67; color: #FFFFFF; }
.b-bigo { background: #FFF3B0; color: #540B0E; border: 1px solid #E09F3E; }
.b-owner { background: #E6F7EE; color: #166534; border: 1px solid #BBEAD0; }

.code-card-body {
    display: grid;
    grid-template-columns: 1.26fr 0.92fr;
    gap: 9px;
    padding: 7px 9px;
    align-items: start;
}
.code-card-body.single {
    grid-template-columns: 1fr;
}
pre {
    margin: 0;
    background: #1C2331;
    color: #E5EDF7;
    padding: 6px 8px;
    border-radius: 7px;
    font-family: 'Cascadia Code', Consolas, 'Courier New', monospace;
    font-size: 7.05pt;
    line-height: 1.36;
    white-space: pre-wrap;
    word-break: break-word;
}
.cm { color: #93C5FD; }
.kw { color: #F9A8D4; font-weight: 600; }
.hl { color: #FDE047; font-weight: 700; }

.say-box {
    font-size: 8.45pt;
    line-height: 1.4;
}
.say-box ul {
    margin: 0;
    padding-left: 14px;
}
.say-box li {
    margin-bottom: 3.5px;
}
.say-script {
    background: #FFFDF2;
    border: 1px dashed #E09F3E;
    border-radius: 6px;
    padding: 5px 7px;
    margin-top: 5px;
    font-size: 8.1pt;
    color: #3F2A0D;
}
.say-script strong {
    color: #9E2A2B;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 5px 0 8px 0;
    font-size: 7.9pt;
}
th {
    background: #540B0E;
    color: #FFFFFF;
    text-align: left;
    padding: 4px 6px;
    font-weight: 700;
    font-size: 7.6pt;
}
td {
    border-bottom: 1px solid #E5DDD0;
    padding: 3.5px 6px;
    vertical-align: top;
}
tr:nth-child(even) td {
    background: #FAF8F5;
}
tr {
    break-inside: avoid;
    page-break-inside: avoid;
}

/* Callouts & Cheat Strips */
.callout {
    background: #FFFDF0;
    border: 1px solid #E6D276;
    border-left: 4px solid #E09F3E;
    border-radius: 7px;
    padding: 7px 10px;
    margin: 7px 0;
    font-size: 8.4pt;
    break-inside: avoid;
    page-break-inside: avoid;
}
.callout.teal {
    background: #F2F8F9;
    border-color: #C2DBE0;
    border-left-color: #335C67;
}
.callout strong { color: #540B0E; }

code {
    font-family: 'Cascadia Code', Consolas, monospace;
    font-size: 8pt;
    background: #F3EFE8;
    color: #540B0E;
    padding: 0.5px 4px;
    border-radius: 3px;
}

.diagram-wrap {
    text-align: center;
    margin: 6px 0 8px 0;
    break-inside: avoid;
    page-break-inside: avoid;
}
.diagram-wrap img {
    max-width: 96%;
    max-height: 195px;
    border: 1px solid #E5DDD0;
    border-radius: 8px;
    padding: 3px;
    background: #FFFFFF;
}
.diagram-cap {
    font-size: 7.6pt;
    color: #4B5563;
    margin-top: 3px;
    font-style: italic;
}

.two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}
.three-col {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 7px;
}
.member-card {
    border: 1px solid #E2D9CB;
    border-top: 4px solid #9E2A2B;
    border-radius: 8px;
    padding: 7px 9px;
    background: #FAF8F5;
    font-size: 8.15pt;
    break-inside: avoid;
    page-break-inside: avoid;
}
.member-card.m2 { border-top-color: #335C67; }
.member-card.m3 { border-top-color: #E09F3E; }
.member-card h4 {
    font-size: 9.2pt;
    margin-bottom: 3px;
}
.member-card ul {
    margin: 3px 0 0 0;
    padding-left: 14px;
}
.member-card li {
    margin-bottom: 2.5px;
}
.page-break {
    page-break-before: always;
    break-before: page;
}
"""


def _qa(num: int, q: str, a: str, trap_q: str, trap_a: str) -> str:
    return f"""
    <div class="qa-card">
        <div class="qa-q"><span class="qa-num">Q{num}</span>{q}</div>
        <div class="qa-a"><strong>Answer:</strong> {a}</div>
        <div class="qa-trap"><strong>Likely Follow-Up:</strong> <em>{trap_q}</em> &rarr; {trap_a}</div>
    </div>
    """


def build_questionnaire_html() -> str:
    logo_uri = _img_data_uri(LOGO_PATH)
    logo_html = f'<div class="cover-logo"><img src="{logo_uri}" alt="CU Connect"/></div>' if logo_uri else ""

    sections = []

    # Section 1
    s1 = [
        _qa(
            1,
            "Explain the overall architecture of CUConnect and how you separated the Core Engine, Storage, and UI.",
            "CUConnect uses a strict 3-layer architecture: <code>ui/</code> (Console CLI &amp; Streamlit web app) calls only the single facade <code>CUConnectService</code> in <code>core/service.py</code>; <code>core/</code> runs all hand-written data structures and graph algorithms strictly in Python RAM; and <code>storage/repository.py</code> handles write-through SQLite CRUD only.",
            "How do you prove the UI never bypasses the facade or touches SQLite directly?",
            "Our AST verifier <code>scripts/check_rules.py</code> parses every file in <code>ui/</code> and fails if any file imports <code>core.ds</code> or <code>storage</code>."
        ),
        _qa(
            2,
            "Why did you avoid <code>networkx</code>, <code>heapq</code>, <code>collections.deque</code>, and Python's built-in <code>sorted()</code> inside <code>core/</code>?",
            "The project rubric awards 30 marks for Core Engine &amp; DSA Usage and 40 marks for Viva Understanding. Implementing all 8 structures from scratch using only Python's standard library proves we understand internal pointer manipulation, hashing, heap sifting, AVL rotations, and divide-and-conquer sorting.",
            "Which Python standard-library modules ARE used in <code>core/</code>?",
            "Only non-DSA utilities: <code>dataclasses</code>, <code>hashlib</code>, <code>hmac</code>, <code>os</code>, <code>re</code>, <code>time</code>, <code>uuid</code>, and <code>typing</code>."
        ),
        _qa(
            3,
            "What is Big-O notation, and what is the difference between worst-case, average-case, and amortized complexity in CUConnect?",
            "Big-O describes how runtime or memory grows with input size <em>n</em>. In our <code>HashTable</code>, <code>put()</code> is O(1) average and O(1) amortized across occasional O(n) table doublings, whereas worst-case (all keys colliding in one bucket) is O(n). Our <code>merge_sort</code> is O(n log n) in best, average, and worst cases.",
            "Why did we document <code>Time:</code> and <code>Space:</code> in every core method's docstring?",
            "Session 2 emphasizes complexity analysis, and <code>scripts/check_rules.py</code> automatically enforces that every public function/method in <code>core/</code> declares both."
        ),
        _qa(
            4,
            "Why did you add an injectable clock and monotonic sequence counter (<code>_seq</code>) to <code>CUConnectService</code>?",
            "When two posts, comments, or notifications occur within the same millisecond (such as during tests or seeding), timestamps alone tie. Pairing <code>(created_at, seq_id)</code> guarantees 100% deterministic ordering, while injecting a mock clock makes 7-day trending and feed tests completely repeatable.",
            "How is <code>_seq</code> restored after restarting the app?",
            "During <code>_hydrate_from_storage()</code>, we scan the maximum <code>seq_id</code> across loaded requests, posts, comments, and notifications and initialize <code>self._seq = max_seq</code>."
        ),
        _qa(
            5,
            "How did you verify that your hand-written structures behave identically to textbook specifications?",
            "We wrote 50 automated <code>pytest</code> tests across 16 test files, including randomized cross-checks: <code>HashTable</code> vs Python <code>dict</code> (800 ops), <code>MinHeap</code> vs <code>sorted()</code>, <code>Trie</code> vs linear prefix filter, <code>AVLTree</code> balance invariants (400 random insert/deletes), edge-case connection rules, and full SQLite restart persistence.",
            "How did you prove empirical performance matches theoretical Big-O?",
            "<code>scripts/benchmark.py</code> benchmarks 100, 1,000, and 5,000 synthetic users: BFS grows linearly with V+E (0.034 &rarr; 6.72 ms), while Home Feed stays sub-millisecond (0.088 ms at 5,000 users)."
        ),
    ]
    sections.append(("1. Architecture, Course Rules &amp; Complexity Foundations", "Sessions 1–2 &bull; Rubric", "".join(s1)))

    # Section 2
    s2 = [
        _qa(
            6,
            "How does your hand-written <code>HashTable</code> compute bucket indices without calling Python's built-in <code>hash()</code>?",
            "<code>_polynomial_hash()</code> iterates through every character using base 31 and prime modulus 10<sup>9</sup>+7: <code>h = (h * 31 + ord(ch)) % 1_000_000_007</code>, then compresses via <code>h % capacity</code>. Multiplying by prime 31 weights character positions so anagrams like <code>'abc'</code> and <code>'cba'</code> map to different buckets.",
            "Trace <code>_polynomial_hash('diya')</code> and its initial bucket (capacity 16).",
            "<code>(((100&times;31 + 105)&times;31 + 121)&times;31 + 97) = 3,083,689</code> &rarr; <code>3,083,689 % 16 = 9</code>."
        ),
        _qa(
            7,
            "Why did you choose Separate Chaining over Open Addressing (Linear/Quadratic Probing) for collision handling?",
            "CUConnect frequently deletes keys (unliking posts, removing connections, pruning Trie nodes, logging out). Open addressing requires deletion tombstones and suffers primary clustering; separate chaining cleanly unlinks a <code>_ChainNode</code> in O(1) once located.",
            "When and how does resizing happen, and what is the tricky line inside <code>_resize()</code>?",
            "When <code>load_factor = size / capacity &gt; 0.75</code>, we double capacity and rehash every node into <code>new_buckets</code>. We MUST save <code>next_node = current.next</code> before overwriting <code>current.next = new_buckets[index]</code> or we lose the rest of the old chain!"
        ),
        _qa(
            8,
            "Where is <code>HashTable</code> reused across CUConnect?",
            "In 7 subsystems: (1) <code>AccountManager</code> (<code>username &rarr; User</code> &amp; sessions), (2) <code>SocialGraph</code> (<code>username &rarr; sorted neighbors</code>), (3) <code>ConnectionManager</code> (incoming/outgoing queues), (4) <code>PostManager</code> (user lists &amp; <code>post_id &rarr; Post</code>), (5) <code>TrieNode.children</code>, (6) <code>NotificationManager</code>, and (7) <code>EngagementManager</code> (per-post likes &amp; comment lookup).",
            "What is the HashTable load factor on our 18 seeded students?",
            "<code>18 / 32 = 0.562</code> (started at 16 buckets, auto-resized to 32 once the 13th user pushed load factor to 13/16 = 0.8125 &gt; 0.75)."
        ),
        _qa(
            9,
            "How are passwords stored securely in <code>core/auth.py</code>? Why not plain <code>hashlib.sha256(password)</code>?",
            "Plain SHA-256 is too fast (billions of guesses/sec on GPUs) and identical passwords produce identical hashes (vulnerable to rainbow tables). Instead, <code>hash_password()</code> generates a unique 16-byte random salt via <code>os.urandom(16)</code> and runs 100,000 iterations of <code>hashlib.pbkdf2_hmac('sha256', ...)</code>, storing <code>pbkdf2_sha256$100000$&lt;salt&gt;$&lt;hash&gt;</code>.",
            "Why do we use <code>hmac.compare_digest()</code> and run a dummy PBKDF2 hash when a username doesn't exist?",
            "Both prevent timing side-channel attacks: constant-time comparison avoids byte-by-byte leaks, and running <code>_DUMMY_HASH</code> on missing usernames keeps response time identical so attackers cannot enumerate valid campus accounts."
        ),
        _qa(
            10,
            "How does <code>User.public_profile()</code> protect sensitive data, and how are usernames normalized?",
            "<code>public_profile()</code> returns a dictionary omitting <code>password_hash</code> so hashes never leak to logs or UI views. <code>normalize_username()</code> strips whitespace and lowercases input so <code>'Aarav'</code> and <code>'aarav'</code> refer to the same unique account.",
            "What happens if two students have the same full name (e.g., two 'Aarav Sharma's)?",
            "Usernames remain unique primary keys; <code>Trie</code> stores a set of matching usernames per token, and <code>AVLTree</code> keys on <code>(full_name.lower(), username)</code> so neither overwrites the other."
        ),
    ]
    sections.append(("2. Part 1: Accounts, Hand-Written HashTable &amp; Security", "Session 15 &bull; Part 1", "".join(s2)))

    # Section 3
    s3 = [
        _qa(
            11,
            "How is the CUConnect social network formally modelled as a graph G(V, E)?",
            "Each registered student is a vertex <em>v &isin; V</em>. Each accepted connection is an undirected edge <code>{u, v} &isin; E</code> stored symmetrically in both adjacency lists. Pending requests are directed edges <code>u &rarr; v</code> kept separately in request queues. G is a simple graph: no self-loops <code>(u, u)</code> and no duplicate/parallel edges.",
            "Why are pending requests NOT stored inside the undirected adjacency list?",
            "Because pending requests are one-way (asymmetric) and must never affect BFS degrees, shortest chains, mutual friends, Home Feeds, or Communities until accepted."
        ),
        _qa(
            12,
            "Why represent G(V, E) with sorted Adjacency Lists instead of an Adjacency Matrix?",
            "Social graphs are sparse (<code>deg(u) &lt;&lt; |V|</code>). At 5,000 students with average degree 10, an adjacency matrix wastes 25,000,000 cells (O(V&sup2;)) and scans 5,000 slots to list 10 friends. Adjacency lists use O(V + E) space (~55,000 entries) and iterate friends in O(deg(u)).",
            "What three benefits come specifically from keeping each adjacency list alphabetically SORTED?",
            "(1) O(log d) edge checks via our <code>binary_search</code>, (2) O(d<sub>u</sub> + d<sub>v</sub>) two-pointer mutual intersection without hashing, and (3) deterministic lexicographical BFS shortest chains."
        ),
        _qa(
            13,
            "Walk through how <code>mutual_connections(u, v)</code> works and state its Time and Space complexity.",
            "Because <code>adj[u]</code> and <code>adj[v]</code> are already sorted, we maintain two indices <code>i = 0, j = 0</code>. If <code>A[i] == B[j]</code>, record it and advance both; if <code>A[i] &lt; B[j]</code>, increment <code>i</code>; else increment <code>j</code>. Time is <strong>O(deg(u) + deg(v))</strong>, Space is <strong>O(min(deg(u), deg(v)))</strong>.",
            "Trace <code>mutual_connections('aarav', 'meera')</code> on our seed data.",
            "<code>N(aarav) = [ananya, diya, rohan]</code> and <code>N(meera) = [ananya, diya, rohan, vikram]</code> &rarr; matches all 3: <code>[ananya, diya, rohan]</code> in 3 comparisons!"
        ),
        _qa(
            14,
            "Why did you implement a linked-list <code>Queue</code> with <code>_head</code> and <code>_tail</code> pointers instead of using a Python <code>list</code>?",
            "Python's <code>list.pop(0)</code> shifts all remaining elements in O(n). Our linked-list <code>Queue</code> maintains both <code>_head</code> (front) and <code>_tail</code> (rear), giving strict O(1) <code>enqueue</code>, <code>dequeue</code>, and <code>peek</code> for BFS frontiers, connection requests, and notifications.",
            "Why did you add <code>remove_value()</code> to a FIFO Queue, and what bug must it avoid?",
            "Users can accept, reject, or cancel a connection request out of arrival order (middle or rear of the queue). If the removed node is <code>self._tail</code>, we MUST reset <code>self._tail = previous</code>, otherwise future <code>enqueue()</code> calls attach to a deleted ghost node!"
        ),
        _qa(
            15,
            "Explain all edge cases enforced by <code>ConnectionManager</code> (including reverse requests).",
            "It blocks unknown users (<code>UserNotFoundError</code>), self-requests (<code>ValidationError</code>), duplicate requests or requesting an existing friend (<code>ConnectionRuleError</code>), sender trying to accept/reject or receiver trying to cancel (<code>AuthorizationError</code>). If Bob already requested Alice and Alice requests Bob, <code>send_request</code> removes Bob&rarr;Alice from both queues, adds undirected edge {Alice, Bob}, and returns <code>'auto_accepted'</code>.",
            "What happens if a sender mistakenly calls <code>accept_request</code> on their own outgoing request?",
            "<code>accept_request</code> checks <code>has_pending_request(actor, sender)</code> and raises a specific <code>AuthorizationError('Only the receiver can accept...')</code> instead of a vague not-found error."
        ),
    ]
    sections.append(("3. Part 2A: Social Graph, Adjacency Lists &amp; Request Queues", "Sessions 3, 7, 11, 12 &bull; Part 2", "".join(s3)))

    # Section 4
    s4 = [
        _qa(
            16,
            "Why does Breadth-First Search (BFS) guarantee the shortest connection chain while DFS does not?",
            "In an unweighted graph, BFS expands vertices strictly in non-decreasing order of hop distance (layer 0, 1, 2, ...) using a FIFO <code>Queue</code>. Thus, the very first time <code>target</code> is discovered is provably a minimum-hop path. DFS plunges deep down one branch and could return a 5-hop detour instead of a 4-hop shortest chain.",
            "Why do we mark <code>visited.add(neighbor)</code> at ENQUEUE time instead of DEQUEUE time?",
            "Marking on enqueue prevents the same vertex from being pushed into the Queue multiple times by different parents in the same layer, keeping queue size bounded at O(V) and avoiding duplicate work."
        ),
        _qa(
            17,
            "How does <code>degree_and_shortest_path()</code> reconstruct the shortest chain and assign labels?",
            "Whenever BFS discovers an unvisited <code>neighbor</code> from <code>current</code>, it records <code>parent[neighbor] = current</code>. Once <code>target</code> is found, BFS exits early and backtracks <code>target &rarr; parent[target] &rarr; ... &rarr; source</code>, reversing the list. Labels map hops: 0=Self, 1=1st, 2=2nd, 3=3rd, &ge;4=3+, unreachable=Not connected.",
            "Trace <code>aarav &rarr; isha</code> and <code>aarav &rarr; pranav</code> on the seeded graph.",
            "<code>aarav &rarr; rohan &rarr; sneha &rarr; arjun &rarr; isha</code> (4 hops, label <code>'3+'</code>). For <code>pranav</code> (in Community #2), BFS exhausts Community #1 and returns <code>distance=None, label='Not connected', path=[]</code>."
        ),
        _qa(
            18,
            "Walk through the 3 stages of 'People You May Know' (<code>SuggestionEngine.recommend</code>).",
            "(1) Run depth-limited BFS (depth &le; 2) using our <code>Queue</code> to find all non-connected friends-of-friends; (2) Filter out users with pending requests and compute exact Jaccard similarity <code>J(u, v) = |N(u) &cap; N(v)| / (deg(u) + deg(v) - |N(u) &cap; N(v)|)</code> using <code>mutual_connections</code>; (3) Push into <code>MinHeap</code> keyed by <code>(-jaccard, -mutual_count, username)</code> and pop top-k.",
            "Why stop BFS at depth 2 with <code>if depth &gt;= 2: continue</code>?",
            "Depth 0 is self, depth 1 are existing connections, and depth &ge; 3 share 0 mutual friends (Jaccard = 0). Stopping expansion at depth 2 visits only O(d&sup2;) edges instead of the entire graph."
        ),
        _qa(
            19,
            "Why did you choose Jaccard Coefficient over raw mutual-friend count? Prove it using our seed numbers.",
            "Raw mutual count unfairly biases toward high-degree hubs. Jaccard normalizes mutuals by total union size. For <code>@aarav</code> (deg=3): <code>meera</code> has 3 mutuals / 4 union = <strong>0.7500</strong> (#1); <code>kabir</code> has 1 / 4 = <strong>0.2500</strong> (#2); <code>sneha</code> has 1 / 5 = <strong>0.2000</strong> (#3). Kabir beats Sneha despite both sharing 1 mutual because a higher fraction of Kabir's circle overlaps Aarav's!",
            "Why is <code>vikram</code> NOT shown in Aarav's People You May Know?",
            "Two reasons: (1) <code>vikram</code> is 3rd-degree (3 hops), and (2) <code>vikram &rarr; aarav</code> is already a pending incoming request, which <code>exclude_pending=True</code> filters out."
        ),
    ]
    sections.append(("4. Part 2B: BFS Shortest Chain &amp; Jaccard Suggestions", "Sessions 11 &amp; 15 &bull; Part 2", "".join(s4)))

    # Section 5
    s5 = [
        _qa(
            20,
            "Why are each student's posts stored in a <code>SinglyLinkedList</code> with head insertion instead of a Python list?",
            "Posts are always displayed newest-first. Prepending a new <code>ListNode</code> at <code>_head</code> runs in strict <strong>O(1)</strong> time (unlike <code>list.insert(0, x)</code> which shifts every element in O(P<sub>u</sub>)), keeps every student's list permanently sorted newest-first, and exposes the <code>head</code> pointer directly for k-way heap merging.",
            "What is the complexity of deleting an old post, and how is ownership enforced?",
            "<code>PostManager.delete_post(actor, post_id)</code> verifies <code>post.author == actor</code> (else raises <code>AuthorizationError</code>), unlinks the node in O(P<sub>author</sub>) via <code>delete_by_id()</code>, removes it from <code>_posts_by_id</code>, and cascades deletion of its likes and comments."
        ),
        _qa(
            21,
            "How does your k-way Home Feed merge work, and why is it vastly faster than sorting all posts?",
            "Because each of a user's <em>k</em> connections already has a newest-first <code>SinglyLinkedList</code>, <code>FeedEngine</code> seeds a <code>MinHeap</code> with only the <em>k</em> head <code>ListNode</code>s (keyed by <code>(-created_at, -seq_id)</code>). Each pop yields the next newest post globally and pushes only <code>top_node.next</code>. Time is <strong>O((k + offset + limit) log k)</strong> instead of O(P log P) to sort all P historical posts!",
            "What keeps the heap size &le; k even if friends have 10,000 old posts?",
            "We never push a friend's next node until their current head node is popped—so at most ONE pointer per connection lives in the heap at any moment. At N = 5,000 users, fetching top 10 takes just <strong>0.088 ms</strong>!"
        ),
        _qa(
            22,
            "How does ONE <code>MinHeap</code> class act as a Max-Heap for Home Feed, Suggestions, and Trending, and why store a 3-tuple <code>(priority, counter, item)</code>?",
            "<code>MinHeap</code> accepts an optional <code>key</code> function; negating timestamps or scores turns minimum extraction into maximum extraction without duplicating heap code. Wrapping each element as <code>(priority, self._counter, item)</code> solves two issues: (1) deterministic FIFO tie-breaking on equal priorities, and (2) Python never attempts <code>Post &lt; Post</code> (which would crash with <code>TypeError</code>!).",
            "Give the parent and child index formulas in our array-based binary heap.",
            "For 0-based index <code>i</code>: <code>parent = (i - 1) // 2</code>, <code>left = 2*i + 1</code>, <code>right = 2*i + 2</code>. Both <code>_sift_up</code> and <code>_sift_down</code> take O(log n)."
        ),
        _qa(
            23,
            "How did you implement Image Posts (Enhancement) without breaking O(1) linked lists or bloating RAM?",
            "We added an optional <code>image_path: str | None = None</code> field to the <code>Post</code> dataclass and a nullable <code>image_path TEXT</code> column to the SQLite <code>posts</code> table (with automatic <code>ALTER TABLE</code> migration for existing DBs). Uploaded images are stored on disk under <code>ui/uploads/</code> (and demo rover/certificate images under <code>ui/assets/</code>), while the in-memory <code>SinglyLinkedList</code> stores only the lightweight string path—keeping RAM O(1) per post!",
            "Does adding <code>image_path</code> break backward compatibility with the Console CLI or existing tests?",
            "No—<code>image_path</code> defaults to <code>None</code>, so every text-only post, console CLI command, and all 50 automated tests work seamlessly."
        ),
    ]
    sections.append(("5. Part 3: SinglyLinkedList Posts, Image Posts &amp; k-Way MinHeap Feed", "Sessions 4, 7 &amp; 15 &bull; Part 3 + Enhancement", "".join(s5)))

    # Section 6
    s6 = [
        _qa(
            24,
            "Why use a <code>Trie</code> (Prefix Tree) for as-you-type user search instead of scanning all users with <code>str.startswith()</code>?",
            "Scanning all V users takes O(V &middot; L) on every keystroke. A <code>Trie</code> walks character-by-character from root to the prefix node in <strong>O(L)</strong> time—completely independent of total campus size V—then collects only the matching subtree via iterative DFS (using our <code>Stack</code>) and sorts results with <code>merge_sort</code>.",
            "How does typing <code>'sh'</code> match BOTH Aarav Sharma and Pranav Shetty, and <code>'diy'</code> match Diya Nair?",
            "<code>UserSearchIndex</code> tokenizes and inserts both the lowercase username AND every word of <code>full_name</code> (<code>'aarav'</code>, <code>'sharma'</code>, <code>'pranav'</code>, <code>'shetty'</code>, <code>'diya'</code>, <code>'nair'</code>). Each <code>TrieNode</code> stores child links in a compact 4-bucket instance of our own <code>HashTable</code>."
        ),
        _qa(
            25,
            "What happens inside the <code>Trie</code> when a student edits their full name?",
            "<code>UserSearchIndex.reindex_user()</code> removes all old full-name tokens via <code>Trie.remove()</code>, inserts the updated name tokens, and re-ensures the username token remains indexed. Inside <code>Trie.remove()</code>, traversed <code>(parent, ch, child)</code> tuples are pushed onto our <code>Stack</code> so dead branches with no <code>user_ids</code> and no children are pruned bottom-up.",
            "Why return <code>[]</code> when the search prefix is empty?",
            "To prevent dumping the entire university directory whenever the search box is blank (which would degrade UI responsiveness and defeat prefix lookup)."
        ),
        _qa(
            26,
            "Why did you implement <code>merge_sort</code> instead of Quick Sort, Bubble Sort, or Heap Sort?",
            "Bubble/Insertion/Selection sort are O(n&sup2;). Quick Sort can degrade to O(n&sup2;) on sorted inputs and is not stable. Heap Sort is O(n log n) but not stable. <strong>Merge Sort</strong> guarantees <strong>O(n log n)</strong> in all cases AND is <strong>stable</strong>—achieved by using <code>&lt;=</code> (not <code>&lt;</code>) inside <code>_merge()</code> so ties keep original order.",
            "Where is <code>binary_search</code> from <code>core/ds/algorithms.py</code> called?",
            "In <code>SocialGraph.has_edge(u, v)</code> to verify membership on sorted adjacency lists in O(log d) time and O(1) space."
        ),
    ]
    sections.append(("6. Part 4: Trie Prefix Search, Merge Sort &amp; Binary Search", "Sessions 3, 8, 12, 14 &bull; Part 4", "".join(s6)))

    # Section 7
    s7 = [
        _qa(
            27,
            "How does CUConnect satisfy Part 5 ('Storage only keeps data; all graph computations run in Python memory')?",
            "<code>SQLiteRepository</code> manages 7 normalized tables using strictly plain <code>SELECT *</code>, <code>INSERT</code>, <code>UPDATE</code>, and <code>DELETE</code>. On startup, <code>_hydrate_from_storage()</code> loads all rows into our in-memory structures; thereafter every read/graph algorithm runs purely in RAM, and every write commits immediately to SQLite (<strong>write-through persistence</strong>).",
            "Why must startup hydration sort posts ASCENDING and comments by <code>seq_id</code> before loading?",
            "Posts are loaded via <code>insert_head()</code>, so inserting oldest-to-newest reverses them into newest-at-head! Comments reference <code>parent_comment_id</code>, so sorting by <code>seq_id</code> guarantees every parent comment exists in <code>_comments_by_id</code> before any nested reply is attached."
        ),
        _qa(
            28,
            "How are undirected edges stored in SQLite without duplicating <code>(aarav, diya)</code> and <code>(diya, aarav)</code>?",
            "<code>_canonical_pair(u, v)</code> always orders the lexicographically smaller username as <code>user_a</code> and larger as <code>user_b</code>, enforced by <code>PRIMARY KEY (user_a, user_b)</code>. On startup hydration, each row populates both <code>adj[user_a]</code> and <code>adj[user_b]</code> in memory.",
            "Why pass <code>check_same_thread=False</code> to <code>sqlite3.connect()</code>?",
            "Streamlit caches one live <code>CUConnectService</code> via <code>@st.cache_resource</code> across reruns that may execute on different worker threads; without it SQLite raises a thread-affinity error."
        ),
        _qa(
            29,
            "How do the Console CLI and the redesigned Streamlit Web App share the exact same engine?",
            "Both import only <code>CUConnectService</code> (and <code>ScreenNavigator</code> for CLI back-nav) from <code>core.service</code>. In Streamlit, Quick Student Search on the top right calls <code>svc.search_users()</code>, Live Campus Network calls <code>svc.get_engine_stats()</code>, and clicking <strong>View Profile &nearr;</strong> redirects cleanly to any student's profile, BFS chain, mutuals, and posts.",
            "How does Console CLI implement back-navigation without importing <code>core.ds.stack</code>?",
            "<code>core/service.py</code> exposes <code>ScreenNavigator</code>, a thin wrapper around our hand-written <code>Stack</code> providing <code>push()</code>, <code>back()</code>, <code>reset()</code>, and <code>breadcrumb()</code>."
        ),
    ]
    sections.append(("7. Parts 5 &amp; 6: Write-Through SQLite Persistence &amp; Dual UIs", "Parts 5 &amp; 6", "".join(s7)))

    # Section 8
    s8 = [
        _qa(
            30,
            "How do Likes and Threaded Comments (with nested replies) work in <code>core/engagement.py</code>?",
            "Likes use a nested <code>HashTable</code> (<code>post_id &rarr; HashTable[username &rarr; ts]</code>) so toggling, checking, and counting run in O(1) average with zero duplicates. Comments form an <strong>n-ary tree</strong> where replies attach to <code>parent.replies</code> (found in O(1) via <code>_comments_by_id</code>) and display via <strong>Pre-Order DFS</strong> with indentation depth.",
            "Why Pre-Order DFS instead of Post-Order DFS or BFS for displaying comments?",
            "Post-order prints replies <em>above</em> their parent (backwards), and BFS groups all depth-1 replies across different threads together, scrambling conversations. Only Pre-Order prints each reply immediately below its parent!"
        ),
        _qa(
            31,
            "How are Trending Posts computed, and what optimization avoids scanning old posts?",
            "<code>get_trending_posts()</code> scans each connection's newest-first <code>SinglyLinkedList</code>, scoring posts within the last 7 days as <code>likes + 2 &times; total_comments</code> and ranking top-k via <code>MinHeap</code>. Because lists are newest-first, as soon as <code>post.created_at &lt; cutoff</code>, we <code>break</code> immediately—skipping all older history!",
            "Why weight comments 2&times; higher than likes?",
            "Writing a comment or technical reply represents deeper engagement than a single-click like."
        ),
        _qa(
            32,
            "How does the Undo feature use a <code>Stack</code>, and how does it avoid corrupting graph state?",
            "<code>CUConnectService</code> maps each user to a hand-written LIFO <code>Stack</code> of <code>UndoAction</code>s (<code>send_request</code> / <code>remove_connection</code>). Undoing pops the top action in O(1), verifies the precondition still holds (e.g., request is still pending—not already accepted!), reverses it in RAM + SQLite, or raises a safe <code>ValidationError</code>.",
            "Does Undo history survive a full app restart?",
            "Intentionally no—undo is session-scoped in memory (like Ctrl+Z in an editor), while all committed social data survives via SQLite."
        ),
        _qa(
            33,
            "How does <code>CommunityDetector</code> find student communities, and why use Iterative DFS instead of Recursion?",
            "It iterates all vertices; for each unvisited user, it runs <strong>Iterative DFS</strong> using our hand-written <code>Stack</code> to discover its entire connected component in O(V + E), sorting members and ranking communities by descending size via <code>merge_sort</code> (O(V log V + E)). Iterative DFS prevents hitting Python's ~1,000-frame recursion limit on 5,000+ user graphs.",
            "What happens live in our demo when <code>@aarav</code> accepts <code>@pranav</code>'s incoming request?",
            "Seed communities have sizes <strong>10, 5, 3</strong>. Accepting <code>pranav &rarr; aarav</code> creates a bridge edge between Community #1 (10) and #2 (5), instantly merging them into one <strong>15-student</strong> community!"
        ),
        _qa(
            34,
            "Why build an <code>AVLTree</code> for 'Browse All Students' instead of a regular BST, and explain all 4 rotations.",
            "A plain BST degenerates to height O(V) (a linked list) if students register in alphabetical order. Our <code>AVLTree</code> enforces <code>|BF| = |h(left) - h(right)| &le; 1</code> at every node so height stays &le; 1.44 log<sub>2</sub>(V) (height <strong>5</strong> for 18 students) and <code>inorder()</code> yields exact A&ndash;Z order in O(V): <strong>LL</strong> (BF=+2, L&ge;0 &rarr; Right rotate), <strong>RR</strong> (BF=-2, R&le;0 &rarr; Left rotate), <strong>LR</strong> (Left rotate child, then Right), <strong>RL</strong> (Right rotate child, then Left).",
            "In <code>_rotate_right(y)</code>, why MUST <code>_update_height(y)</code> run BEFORE <code>_update_height(x)</code>?",
            "Because after rotating, <code>y</code> becomes the right child of <code>x</code>—so <code>x</code>'s new height depends on <code>y</code>'s already-recomputed height!"
        ),
        _qa(
            35,
            "How does <code>NotificationManager</code> work and prevent notifying users of their own actions?",
            "It keeps a per-user FIFO <code>Queue</code> inside a <code>HashTable</code> plus a <code>notification_id &rarr; Notification</code> <code>HashTable</code> for O(1) <code>mark_read()</code>. In <code>CUConnectService</code>, liking or commenting checks <code>if post.author != actor</code> (and tracks a <code>notified = {actor}</code> set on replies) so self-notifications and duplicate alerts never occur.",
            "What triggers notifications in CUConnect?",
            "Five events: <code>connection_request</code>, <code>request_accepted</code>, <code>post_like</code>, <code>post_comment</code>, and <code>comment_reply</code>."
        ),
    ]
    sections.append(("8. All 7 Enhancements (Notifications, Likes/Comments, Trending, Undo, Communities, AVL, Images)", "Sessions 6, 7, 8, 10, 11, 15", "".join(s8)))

    # Section 9
    s9 = [
        _qa(
            36,
            "What if CUConnect scaled from 5,000 students to 1,000,000 users? What would you change?",
            "(1) Replace single-source BFS with <strong>Bidirectional BFS</strong> (cuts explored nodes from <em>b<sup>d</sup></em> to <em>2b<sup>d/2</sup></em>); (2) Use hybrid <strong>fan-out-on-write</strong> (precomputed feeds for normal users) + <strong>fan-out-on-read</strong> (k-way merge for celebrities with 50k+ connections); (3) Partition/shard adjacency lists across servers.",
            "What if the graph became directed (like Instagram Follow) instead of undirected (LinkedIn Connect)?",
            "Store separate <code>out_adj</code> (following) and <code>in_adj</code> (followers) <code>HashTable</code>s, remove symmetry in <code>add_edge</code>/<code>remove_edge</code>, and replace connected components with Strongly Connected Components (Kosaraju/Tarjan)."
        ),
        _qa(
            37,
            "How would you add a 'Block User' feature without redesigning the graph?",
            "Add a per-user <code>blocked</code> <code>HashTable</code> (directed <code>blocker &rarr; blocked</code> so only blocker can unblock). Blocking removes any existing undirected edge and pending requests, blocks future requests, and filters blocked pairs out of Search, Suggestions, and Feed.",
            "How would you answer a range query like 'All students whose name starts between C and G'?",
            "Our <code>AVLTree</code> supports range queries <code>[low, high]</code> in O(log V + K) time by pruning subtrees outside the range—something a <code>HashTable</code> can never do efficiently!"
        ),
        _qa(
            38,
            "How does <code>AVLTree.delete()</code> handle deleting a node with TWO children (e.g., when a student changes their name)?",
            "It locates the in-order successor (<code>_min_node(node.right)</code>), copies the successor's <code>(key, value)</code> into the target node, recursively deletes the successor from the right subtree, and calls <code>_rebalance()</code> on every ancestor while unwinding the recursion.",
            "Why doesn't renaming a user break their connections or posts?",
            "Because connections, requests, posts, likes, and comments are all keyed by immutable <code>username</code>—only <code>Trie</code> and <code>AVLTree</code> (which index <code>full_name</code>) need re-indexing on rename!"
        ),
    ]
    sections.append(("9. Faculty 'What-If' Scaling, Design Trade-Offs &amp; Deep Probing Questions", "Viva High-Scorers (40 Marks)", "".join(s9)))

    body_sections = []
    for title, tag, content in sections:
        body_sections.append(f'<div class="sec-head"><h2>{title}</h2><span class="sec-tag">{tag}</span></div>{content}')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CUConnect — Faculty Viva Questionnaire</title>
<style>{BASE_CSS}</style>
</head>
<body>

<div class="cover-banner">
    {logo_html}
    <div>
        <div class="cover-kicker">Chanakya University, Bangalore &bull; School of Engineering &bull; III Sem B.Tech (2026&ndash;27)</div>
        <div class="cover-title">CUConnect — Faculty Viva Questionnaire &amp; Model Answers</div>
        <div class="cover-sub">38 High-Probability Viva Questions + Trap Follow-Ups Mapped to DSA Syllabus (Sessions 1&ndash;15) &amp; Mini-Project Rubric</div>
    </div>
</div>

<div class="meta-grid">
    <div class="meta-box auburn">
        <div class="meta-label">Course &amp; Faculty</div>
        <div class="meta-val">DSA (EAI212/EVE203/EEC203)<br>Prof. Nitish Hegde</div>
    </div>
    <div class="meta-box">
        <div class="meta-label">Team Members</div>
        <div class="meta-val">Dhruv Jha, Pranam Jogur,<br>Nihal N</div>
    </div>
    <div class="meta-box gold">
        <div class="meta-label">Rubric Weightage</div>
        <div class="meta-val">Viva: 40 | Core DSA: 30<br>Impl: 20 | Report: 10</div>
    </div>
    <div class="meta-box">
        <div class="meta-label">Verified Stats</div>
        <div class="meta-val">50/50 pytest Passed<br>0 AST Rule Violations</div>
    </div>
</div>

<div class="callout">
    <strong>Memorize These Exact Seed Dry-Run Numbers (<code>@aarav</code> / password <code>chanakya2026</code>):</strong>
    18 Students &bull; 23 Connections &bull; 14 Posts (incl. Rover &amp; Hackathon Certificate images) &bull; 3 Communities (sizes <strong>10, 5, 3</strong> &rarr; accepting <code>@pranav</code> merges 10+5 = <strong>15</strong>!) &bull;
    <strong>Aarav's 1st-degree:</strong> <code>ananya, diya, rohan</code> (deg=3) &bull;
    <strong>PYMK Jaccard:</strong> <code>meera = 3/4 (0.7500)</code>, <code>kabir = 1/4 (0.2500)</code>, <code>sneha = 1/5 (0.2000)</code> &bull;
    <strong>BFS:</strong> <code>diya=1st</code>, <code>meera=2nd</code>, <code>vikram=3rd</code>, <code>isha=3+ (4 hops: aarav&rarr;rohan&rarr;sneha&rarr;arjun&rarr;isha)</code>, <code>pranav=Not connected</code> &bull;
    <strong>AVL Height:</strong> 5 (Balanced=True) &bull; <strong>HashTable LF:</strong> 0.562 &bull;
    <strong>5,000-User Benchmarks:</strong> Feed <strong>0.09 ms</strong>, Trie <strong>2.18 ms</strong>, PYMK <strong>3.69 ms</strong>, BFS <strong>6.72 ms</strong>.
</div>

{"".join(body_sections)}

<div class="page-break"></div>
<div class="sec-head">
    <h2>10. Individual Team-Member Spotlight (Separate Student Evaluation)</h2>
    <span class="sec-tag">Rubric Note #1 &amp; #2</span>
</div>
<div class="callout teal">
    <strong>Remember Rubric Note #1 &amp; #2:</strong> <em>"Evaluation will be carried out for each student separately. You are answerable for every line you submit; code you cannot explain will not earn marks."</em> Everyone must know all 8 DSAs at a high level, plus master their owned modules below:
</div>
<div class="three-col">
    <div class="member-card">
        <h4>Dhruv Jha</h4>
        <div><strong>Owned:</strong> <code>HashTable</code>, <code>MinHeap</code>, <code>AVLTree</code>, <code>auth.py</code>, <code>feed.py</code>, <code>service.py</code>, Benchmarks</div>
        <ul>
            <li>Trace <code>_polynomial_hash</code> (base 31) &amp; <code>_resize</code> saving <code>next_node</code>.</li>
            <li>Explain <code>(priority, counter, item)</code> in <code>MinHeap</code> &amp; k-way feed loop.</li>
            <li>Draw LL, RR, LR, RL rotations &amp; why child height updates first.</li>
            <li>Explain PBKDF2 + salt + <code>hmac.compare_digest</code> + dummy hash.</li>
            <li>Explain <code>_hydrate_from_storage()</code> ordering &amp; Undo Stack safety guard.</li>
        </ul>
    </div>
    <div class="member-card m2">
        <h4>Pranam Jogur</h4>
        <div><strong>Owned:</strong> <code>graph.py</code>, <code>connections.py</code>, <code>suggestions.py</code>, <code>communities.py</code>, Seed Topology</div>
        <ul>
            <li>Contrast Adjacency List O(V+E) vs Matrix O(V&sup2;) &amp; sorted list benefits.</li>
            <li>Trace two-pointer <code>mutual_connections</code> in O(d<sub>u</sub>+d<sub>v</sub>).</li>
            <li>Trace BFS queue + <code>parent[]</code> for <code>aarav &rarr; isha</code> (4 hops, <code>3+</code>).</li>
            <li>Derive Jaccard <code>meera=0.75</code>, <code>kabir=0.25</code>, <code>sneha=0.20</code> + depth-2 cutoff.</li>
            <li>Explain reverse auto-accept &amp; Iterative DFS + Stack (10+5 &rarr; 15 merge!).</li>
        </ul>
    </div>
    <div class="member-card m3">
        <h4>Nihal N</h4>
        <div><strong>Owned:</strong> <code>SinglyLinkedList</code>, <code>Queue</code>, <code>Stack</code>, <code>Trie</code>, <code>algorithms.py</code>, <code>posts.py</code>, <code>engagement.py</code>, <code>repository.py</code>, UIs</div>
        <ul>
            <li>Explain O(1) <code>insert_head</code> &amp; optional <code>image_path</code> persistence.</li>
            <li>Explain <code>Queue.remove_value</code> fixing <code>_tail = previous</code>.</li>
            <li>Trace <code>Trie</code> <code>'sh'</code> / <code>'diy'</code> lookup &amp; bottom-up Stack pruning.</li>
            <li>Explain why <code>&lt;=</code> makes <code>merge_sort</code> stable &amp; <code>binary_search</code> O(log d).</li>
            <li>Explain Pre-Order DFS comment trees, 7-day Trending early exit &amp; CRUD-only SQL.</li>
        </ul>
    </div>
</div>

<div class="sec-head" style="margin-top:14px;">
    <h2>11. Rapid-Fire Master Complexity &amp; Live Demo Checklist</h2>
    <span class="sec-tag">Last-Minute Review</span>
</div>
<table>
    <thead>
        <tr>
            <th style="width:27%;">Operation</th>
            <th style="width:27%;">Hand-Written Structure / Algo</th>
            <th style="width:22%;">Time Complexity</th>
            <th style="width:24%;">Live Demo Verification</th>
        </tr>
    </thead>
    <tbody>
        <tr><td>Login / Profile Lookup</td><td><code>HashTable</code> + PBKDF2</td><td>O(1) avg (+ fixed PBKDF2)</td><td>Try wrong pw &rarr; uniform error</td></tr>
        <tr><td>Edge Check / Mutuals</td><td>Sorted Adj List + <code>binary_search</code> / 2-Ptr</td><td>O(log d) / O(d<sub>u</sub> + d<sub>v</sub>)</td><td>Mutuals(aarav, meera) = 3</td></tr>
        <tr><td>Degree &amp; Shortest Chain</td><td>BFS (<code>Queue</code> + <code>parent</code> map)</td><td>O(V + E)</td><td><code>isha</code> = <code>3+</code> (4 hops); <code>pranav</code> = None</td></tr>
        <tr><td>People You May Know</td><td>Depth-2 BFS + Jaccard + <code>MinHeap</code></td><td>O(d&sup2; + C log C)</td><td>Meera 0.75, Kabir 0.25, Sneha 0.20</td></tr>
        <tr><td>Create Post (+ Image) / Feed</td><td><code>SinglyLinkedList</code> + k-way <code>MinHeap</code></td><td>O(1) / O((k+N) log k)</td><td>Rover &amp; Cert images; 0.09 ms @ 5k</td></tr>
        <tr><td>Live Prefix User Search</td><td><code>Trie</code> (HashTable children) + <code>merge_sort</code></td><td>O(L + M + U log U)</td><td>Type <code>diy</code> &rarr; <strong>View Profile &nearr;</strong></td></tr>
        <tr><td>Likes / Comment Replies</td><td>Nested <code>HashTable</code> / Pre-Order DFS</td><td>O(1) / O(C)</td><td>Expand Rohan's 3-level thread</td></tr>
        <tr><td>Undo / Communities / Directory</td><td><code>Stack</code> / Iterative DFS / <code>AVLTree</code></td><td>O(1) / O(V log V+E) / O(V)</td><td>Accept pranav (10+5&rarr;15); AVL h=5</td></tr>
    </tbody>
</table>

<div class="callout">
    <strong>Commands Ready in VS Code Terminal:</strong>
    <code>.\.venv\Scripts\streamlit.exe run ui/streamlit_app.py</code> (Web UI) &bull;
    <code>.\.venv\Scripts\python.exe ui/console_app.py</code> (Console CLI) &bull;
    <code>.\.venv\Scripts\pytest.exe -v</code> (50 tests) &bull;
    <code>.\.venv\Scripts\python.exe scripts/check_rules.py</code> (0 violations)
</div>

</body>
</html>
"""
    return html


def build_10min_guide_html() -> str:
    logo_uri = _img_data_uri(LOGO_PATH)
    logo_html = f'<div class="cover-logo"><img src="{logo_uri}" alt="CU Connect"/></div>' if logo_uri else ""
    arch_uri = _img_data_uri(DIAGRAMS / "architecture.png")
    graph_uri = _img_data_uri(DIAGRAMS / "example_graph.png")
    feed_uri = _img_data_uri(DIAGRAMS / "heap_kway_merge.png")
    avl_uri = _img_data_uri(DIAGRAMS / "avl_rotations.png")
    bench_uri = _img_data_uri(DIAGRAMS / "benchmark_chart.png")

    def code_card(
        title: str,
        file_ref: str,
        speak_sec: str,
        session: str,
        bigo: str,
        owner: str,
        code_html: str,
        bullets: list[str],
        script: str,
    ) -> str:
        li_html = "".join(f"<li>{b}</li>" for b in bullets)
        return f"""
        <div class="code-card">
            <div class="code-card-head">
                <div><span class="code-card-title">{title}</span><span class="code-file">{file_ref}</span></div>
                <div class="pill-row">
                    <span class="badge b-time">{speak_sec}</span>
                    <span class="badge b-sess">{session}</span>
                    <span class="badge b-bigo">{bigo}</span>
                    <span class="badge b-owner">{owner}</span>
                </div>
            </div>
            <div class="code-card-body">
                <pre>{code_html}</pre>
                <div class="say-box">
                    <ul>{li_html}</ul>
                    <div class="say-script"><strong>Say in {speak_sec}:</strong> &ldquo;{script}&rdquo;</div>
                </div>
            </div>
        </div>
        """

    cards_ds = [
        code_card(
            "1. HashTable — Polynomial Hash, Chaining &amp; 2&times; Resize",
            "core/ds/hash_table.py (L43–129)",
            "45 sec",
            "Session 15",
            "O(1) avg | O(n) worst",
            "Dhruv",
            """<span class="kw">def</span> _polynomial_hash(self, key):
    h = 0
    <span class="kw">for</span> ch <span class="kw">in</span> str(key):
        h = (h * 31 + ord(ch)) % 1_000_000_007 <span class="hl"># no built-in hash()</span>
    <span class="kw">return</span> h

<span class="kw">def</span> put(self, key, value):
    idx = self._polynomial_hash(key) % self._capacity
    curr = self._buckets[idx]
    <span class="kw">while</span> curr:
        <span class="kw">if</span> curr.key == key: curr.value = value; <span class="kw">return</span>
        curr = curr.next
    self._buckets[idx] = _ChainNode(key, value, self._buckets[idx])
    self._size += 1
    <span class="kw">if</span> self._size / self._capacity &gt; 0.75:      <span class="hl"># rehash &amp; double</span>
        self._resize(self._capacity * 2)""",
            [
                "<strong>Why:</strong> Replaces Python <code>dict</code> for users, adj lists, post IDs, likes &amp; Trie children.",
                "<strong>Chaining vs Probing:</strong> Frequent deletes (unlike/disconnect/prune) need no tombstones.",
                "<strong>Tricky line in <code>_resize</code> (L77):</strong> Save <code>next_node = current.next</code> BEFORE relinking into <code>new_buckets</code>!",
            ],
            "We never call built-in hash(). Base-31 rolling hash separates anagrams, separate chaining handles frequent deletes cleanly, and doubling at load factor &gt; 0.75 keeps put/get O(1) amortized."
        ),
        code_card(
            "2. SinglyLinkedList &amp; Posts (+ Optional Image Path)",
            "core/ds/linked_list.py (L57–115) &amp; core/posts.py",
            "30 sec",
            "Session 4",
            "O(1) post | O(P_u) del",
            "Nihal",
            """<span class="kw">def</span> insert_head(self, value):                 <span class="hl"># O(1) newest-first!</span>
    self._head = ListNode(value, self._head)
    self._size += 1

<span class="kw">def</span> delete_by_id(self, target_id, id_getter):
    prev, curr = None, self._head
    <span class="kw">while</span> curr:
        <span class="kw">if</span> id_getter(curr.value) == target_id:
            <span class="kw">if</span> prev <span class="kw">is</span> None: self._head = curr.next
            <span class="kw">else</span>: prev.next = curr.next
            self._size -= 1; <span class="kw">return</span> True
        prev, curr = curr, curr.next
    <span class="kw">return</span> False""",
            [
                "<strong>Why:</strong> Prepending at head is O(1) (no array shift) and keeps posts naturally newest-first.",
                "<strong>Feed link:</strong> Exposing <code>.head</code> lets <code>FeedEngine</code> merge lists using pointers directly.",
                "<strong>Image Posts:</strong> <code>Post.image_path</code> stores only the file path (<code>ui/uploads/</code>), keeping RAM O(1) per post.",
            ],
            "Each student owns a SinglyLinkedList of Post objects. Prepending at head takes O(1) and keeps posts newest-first so our Home Feed merges directly from each friend's head pointer."
        ),
        code_card(
            "3. Linked-List Queue &amp; LIFO Stack",
            "core/ds/queue_ds.py (L37–120) &amp; core/ds/stack.py",
            "35 sec",
            "Sessions 6 &amp; 7",
            "O(1) enq/deq/push/pop",
            "Nihal",
            """<span class="kw">def</span> enqueue(self, value):                     <span class="hl"># O(1) via _tail</span>
    node = _QueueNode(value)
    <span class="kw">if</span> self._tail <span class="kw">is</span> None: self._head = self._tail = node
    <span class="kw">else</span>: self._tail.next = node; self._tail = node
    self._size += 1

<span class="kw">def</span> remove_value(self, target):               <span class="hl"># out-of-order cancel/accept</span>
    prev, curr = None, self._head
    <span class="kw">while</span> curr:
        <span class="kw">if</span> curr.value == target:
            <span class="kw">if</span> prev <span class="kw">is</span> None: self._head = curr.next
            <span class="kw">else</span>: prev.next = curr.next
            <span class="kw">if</span> curr <span class="kw">is</span> self._tail: self._tail = prev <span class="hl"># CRITICAL!</span>
            self._size -= 1; <span class="kw">return</span> True
        prev, curr = curr, curr.next""",
            [
                "<strong>Queue uses (3):</strong> BFS frontier, pending requests (in/out), per-user notifications.",
                "<strong>Tricky line (L111):</strong> Updating <code>_tail = prev</code> when removing the rear item prevents broken future enqueues.",
                "<strong>Stack uses (4):</strong> Undo history, Console back-nav, Trie pruning, Iterative DFS communities.",
            ],
            "Maintaining head and tail pointers gives O(1) enqueue/dequeue unlike list.pop(0). remove_value handles out-of-order request actions safely by fixing _tail. Our LIFO Stack powers Undo, CLI back-nav, Trie pruning, and DFS."
        ),
        code_card(
            "4. MinHeap (Array Binary Heap + Max-Heap Key Wrapper)",
            "core/ds/heap.py (L30–90)",
            "40 sec",
            "Session 15",
            "O(log n) push/pop | O(1) peek",
            "Dhruv",
            """<span class="kw">def</span> push(self, item):
    entry = (self._key_fn(item), self._counter, item) <span class="hl"># tie-break!</span>
    self._counter += 1
    self._data.append(entry)
    self._sift_up(len(self._data) - 1)

<span class="kw">def</span> _sift_up(self, i):
    <span class="kw">while</span> i &gt; 0:
        p = (i - 1) // 2
        <span class="kw">if</span> self._data[i] &lt; self._data[p]:
            self._data[i], self._data[p] = self._data[p], self._data[i]
            i = p
        <span class="kw">else</span>: <span class="kw">break</span>
<span class="cm"># pop(): swap root with last leaf, pop leaf, _sift_down(0) using 2i+1, 2i+2</span>""",
            [
                "<strong>Max-Heap trick:</strong> Passing negated keys like <code>(-created_at, -seq_id)</code> makes one MinHeap rank highest-first.",
                "<strong>Tricky line (L66):</strong> 3-tuple <code>(priority, counter, item)</code> breaks ties deterministically and prevents <code>Post &lt; Post</code> TypeError.",
                "<strong>Used in (3):</strong> Home Feed k-way merge, People You May Know top-k, Trending Posts.",
            ],
            "One array-based MinHeap powers Feed, Suggestions, and Trending. Negating keys turns it into a Max-Heap, and the monotonic counter breaks ties without ever comparing dataclass objects."
        ),
        code_card(
            "5. Trie (Prefix Tree) + Stable Merge Sort &amp; Binary Search",
            "core/ds/trie.py (L45–138) &amp; core/ds/algorithms.py",
            "40 sec",
            "Sessions 8, 12, 14",
            "O(L) walk | O(n log n) sort",
            "Nihal",
            """<span class="kw">def</span> prefix_search(self, prefix, limit=None):
    curr = self._root
    <span class="kw">for</span> ch <span class="kw">in</span> prefix.strip().lower():         <span class="hl"># O(L) hops, indep. of V</span>
        curr = curr.children.get(ch)          <span class="hl"># 4-bucket HashTable</span>
        <span class="kw">if</span> curr <span class="kw">is</span> None: <span class="kw">return</span> []
    matched, st = set(), Stack()
    st.push(curr)                             <span class="cm"># Iterative DFS subtree</span>
    <span class="kw">while not</span> st.is_empty():
        node = st.pop()
        matched.update(node.user_ids)
        <span class="kw">for</span> child <span class="kw">in</span> node.children.values(): st.push(child)
    <span class="kw">return</span> merge_sort(list(matched))[:limit]  <span class="hl"># stable '&lt;=' merge</span>""",
            [
                "<strong>Why:</strong> Prefix walk takes O(L) independent of user count V; indexes both username &amp; full-name words (<code>'sh'</code> &rarr; Sharma + Shetty; <code>'diy'</code> &rarr; Diya).",
                "<strong>Pruning:</strong> <code>Trie.remove()</code> tracks path on our <code>Stack</code> to delete empty branches on rename.",
                "<strong>Algorithms:</strong> <code>merge_sort</code> uses <code>&lt;=</code> for O(n log n) stability; <code>binary_search</code> checks edges in O(log d).",
            ],
            "Each TrieNode stores child links in our HashTable. Typing 'diy' walks 3 hops in O(L), gathers that subtree via Stack DFS, and sorts deterministically with our stable merge_sort."
        ),
        code_card(
            "6. Self-Balancing AVL Tree (LL, RR, LR, RL Rotations)",
            "core/ds/avl_tree.py (L59–125)",
            "45 sec",
            "Session 10",
            "O(log V) ins/del | O(V) A-Z",
            "Dhruv",
            """<span class="kw">def</span> _rotate_right(self, y):                   <span class="cm"># fixes LL</span>
    x, t2 = y.left, y.left.right
    x.right, y.left = y, t2
    self._update_height(y)                    <span class="hl"># update LOWER node first!</span>
    self._update_height(x)
    <span class="kw">return</span> x

<span class="kw">def</span> _rebalance(self, node):
    self._update_height(node)
    bf = self._balance_factor(node)           <span class="cm"># h(left) - h(right)</span>
    <span class="kw">if</span> bf &gt; 1:                                <span class="cm"># LL or LR</span>
        <span class="kw">if</span> self._balance_factor(node.left) &lt; 0:
            node.left = self._rotate_left(node.left)   <span class="hl"># LR step 1</span>
        <span class="kw">return</span> self._rotate_right(node)
    <span class="kw">if</span> bf &lt; -1:                               <span class="cm"># RR or RL</span>
        <span class="kw">if</span> self._balance_factor(node.right) &gt; 0:
            node.right = self._rotate_right(node.right)<span class="hl"># RL step 1</span>
        <span class="kw">return</span> self._rotate_left(node)
    <span class="kw">return</span> node""",
            [
                "<strong>Why vs plain BST:</strong> Sorted sign-ups skew a plain BST to O(V); AVL guarantees height &le; 1.44 log<sub>2</sub>V (height <strong>5</strong> for 18 students).",
                "<strong>Directory key:</strong> <code>(full_name.lower(), username)</code> avoids duplicate-name collisions; <code>inorder()</code> prints A&ndash;Z in O(V).",
                "<strong>Tricky line (L76):</strong> Recompute lower rotated node's height BEFORE the new root's height!",
            ],
            "Our AVLTree keeps 'Browse All Students' permanently sorted in O(log V) height. _rebalance handles all 4 textbook cases—LL, RR, LR, RL—always updating the lowered child's height before the new root."
        ),
    ]

    cards_domain = [
        code_card(
            "7. SocialGraph — Sorted Adj Lists, Mutuals &amp; BFS Shortest Chain",
            "core/graph.py (L69–272)",
            "55 sec",
            "Sessions 11 &amp; 12",
            "Mutuals O(d_u+d_v) | BFS O(V+E)",
            "Pranam",
            """<span class="cm"># Two-pointer mutuals on sorted adj lists (L178):</span>
<span class="kw">while</span> i &lt; len_a <span class="kw">and</span> j &lt; len_b:
    <span class="kw">if</span> a[i] == b[j]: mutuals.append(a[i]); i += 1; j += 1
    <span class="kw">elif</span> a[i] &lt; b[j]: i += 1
    <span class="kw">else</span>: j += 1

<span class="cm"># Unweighted BFS shortest path with Queue + parent map (L228):</span>
visited, parent, q = {source}, {source: None}, Queue()
q.enqueue(source)
<span class="kw">while not</span> q.is_empty():
    curr = q.dequeue()
    <span class="kw">for</span> nbr <span class="kw">in</span> self._require_user(curr):
        <span class="kw">if</span> nbr <span class="kw">in</span> visited: <span class="kw">continue</span>
        visited.add(nbr)                      <span class="hl"># mark AT ENQUEUE!</span>
        parent[nbr] = curr
        <span class="kw">if</span> nbr == target: <span class="kw">return</span> _backtrack(parent, target)
        q.enqueue(nbr)""",
            [
                "<strong>Sparse graph win:</strong> Adjacency lists in <code>HashTable</code> save ~450&times; memory over O(V&sup2;) matrix at 5,000 users.",
                "<strong>Sorted neighbors:</strong> Give O(log d) <code>binary_search</code> in <code>has_edge</code>, linear 2-pointer mutuals, and deterministic BFS.",
                "<strong>BFS Guarantee:</strong> Layer-by-layer FIFO queue finds provably shortest hops (<code>aarav&rarr;rohan&rarr;sneha&rarr;arjun&rarr;isha</code> = 4 hops / <code>3+</code>).",
            ],
            "Accepted edges live in sorted adjacency lists inside HashTable. Mutual connections run a 2-pointer linear scan, and BFS marks nodes visited on enqueue while recording parent pointers to backtrack the shortest chain."
        ),
        code_card(
            "8. People You May Know — Depth-2 BFS + Jaccard + MinHeap",
            "core/suggestions.py (L64–120)",
            "45 sec",
            "Sessions 11 &amp; 15",
            "O(d&sup2; + C log C)",
            "Pranam",
            """<span class="kw">while not</span> queue.is_empty():
    curr, depth = queue.dequeue()
    <span class="kw">if</span> depth &gt;= 2: <span class="kw">continue</span>                  <span class="hl"># stop at 2nd degree!</span>
    <span class="kw">for</span> nbr <span class="kw">in</span> self._graph.neighbors(curr):
        <span class="kw">if</span> nbr <span class="kw">in</span> visited: <span class="kw">continue</span>
        visited.add(nbr)
        <span class="kw">if</span> depth + 1 == 2: candidates.append(nbr)
        <span class="kw">else</span>: queue.enqueue((nbr, 1))

heap = MinHeap(key=<span class="kw">lambda</span> s: (-s.jaccard_score, -s.mutual_count, s.username))
<span class="kw">for</span> c <span class="kw">in</span> candidates:
    mutuals = self._graph.mutual_connections(u, c)
    union = deg(u) + deg(c) - len(mutuals)
    jaccard = len(mutuals) / union            <span class="hl"># normalized [0, 1]</span>
    heap.push(Suggestion(..., round(jaccard, 4)))""",
            [
                "<strong>Why Depth-2 only:</strong> Depth 1 are already friends; depth &ge; 3 have 0 mutuals.",
                "<strong>Why Jaccard:</strong> Normalizes by union size so <code>kabir (1/4=0.25)</code> ranks above <code>sneha (1/5=0.20)</code>, behind <code>meera (3/4=0.75)</code>.",
                "<strong>Pending filter:</strong> Skips candidates with an active incoming/outgoing request.",
            ],
            "We run depth-2 BFS to gather non-connected friends-of-friends, filter pending requests, compute Jaccard = mutuals / union using our 2-pointer intersection, and pop the top-k from MinHeap."
        ),
        code_card(
            "9. Paginated Home Feed — k-Way Merge with MinHeap",
            "core/feed.py (L57–83)",
            "40 sec",
            "Sessions 4, 7 &amp; 15",
            "O((k + N) log k)",
            "Dhruv",
            """heap = MinHeap(key=<span class="kw">lambda</span> n: (-n.value.created_at, -n.value.seq_id))
<span class="kw">for</span> author <span class="kw">in</span> sources:                        <span class="cm"># only k head pointers!</span>
    head = self._posts.get_user_post_head(author)
    <span class="kw">if</span> head <span class="kw">is not</span> None: heap.push(head)

page, skipped = [], 0
<span class="kw">while not</span> heap.is_empty() <span class="kw">and</span> len(page) &lt; limit:
    top_node = heap.pop()                     <span class="hl"># newest global post</span>
    <span class="kw">if</span> top_node.next <span class="kw">is not</span> None:
        heap.push(top_node.next)              <span class="hl"># heap size stays &le; k!</span>
    <span class="kw">if</span> skipped &lt; offset: skipped += 1
    <span class="kw">else</span>: page.append(top_node.value)
<span class="kw">return</span> page, (<span class="kw">not</span> heap.is_empty())""",
            [
                "<strong>Why k-way merge:</strong> Never sorts all P historical posts; only pushes 1 head <code>ListNode</code> per connection.",
                "<strong>Key invariant:</strong> Pushing <code>top_node.next</code> only after popping keeps heap size strictly &le; k.",
                "<strong>Benchmark proof:</strong> <strong>0.088 ms</strong> at 5,000 users (15,000 posts) — flat regardless of total V!",
            ],
            "Because each friend's linked list is already newest-first, we seed MinHeap with just k head nodes. Each pop emits the newest post and pushes node.next, giving O((k+N) log k) — 0.09 ms even at 5,000 users."
        ),
        code_card(
            "10. Communities (Iterative DFS), Comment Trees (Pre-Order DFS) &amp; Trending",
            "core/communities.py (L28–60) &amp; core/engagement.py",
            "45 sec",
            "Sessions 6, 8, 11, 15",
            "DFS O(V log V+E) | Likes O(1)",
            "Pranam &amp; Nihal",
            """<span class="cm"># Iterative DFS Connected Components (communities.py L28):</span>
visited.add(start); stack.push(start)
<span class="kw">while not</span> stack.is_empty():
    curr = stack.pop(); component.append(curr)
    <span class="kw">for</span> nbr <span class="kw">in</span> self._graph.neighbors(curr):
        <span class="kw">if</span> nbr <span class="kw">not in</span> visited:
            visited.add(nbr); stack.push(nbr) <span class="hl"># no recursion limit!</span>

<span class="cm"># Comment Tree Pre-Order DFS + Trending Early Exit (engagement.py):</span>
<span class="kw">def</span> _dfs(node, depth):                        <span class="hl"># parent BEFORE replies</span>
    out.append((node, depth))
    <span class="kw">for</span> child <span class="kw">in</span> node.replies: _dfs(child, depth + 1)
<span class="cm"># Trending: score = likes + 2*comments; if post.created_at &lt; cutoff: break!</span>""",
            [
                "<strong>Communities:</strong> Iterative DFS + <code>Stack</code> avoids Python's 1,000-frame recursion crash; demo merges 10+5 &rarr; 15 live!",
                "<strong>Likes &amp; Comments:</strong> Nested <code>HashTable</code> gives O(1) duplicate-free likes; Pre-Order DFS keeps replies directly beneath parents.",
                "<strong>Trending:</strong> Breaks early out of newest-first lists past the 7-day cutoff; ranks top-k in <code>MinHeap</code>.",
            ],
            "Communities run iterative DFS with our Stack so large graphs never overflow recursion. Likes use a nested HashTable in O(1), replies render via Pre-Order DFS, and Trending early-exits linked lists past 7 days."
        ),
        code_card(
            "11. Auth Security, Facade Hydration, Undo Stack &amp; Storage-Only SQLite",
            "core/auth.py, core/service.py &amp; storage/repository.py",
            "45 sec",
            "Parts 1, 5 &amp; 6",
            "Write-Through CRUD | O(1) Undo",
            "Dhruv &amp; Nihal",
            """<span class="cm"># Salted PBKDF2 + anti-enumeration login (auth.py):</span>
dk = hashlib.pbkdf2_hmac(<span class="hl">"sha256"</span>, pw.encode(), salt, 100_000)
hmac.compare_digest(expected_hex, dk.hex())   <span class="hl"># constant-time!</span>

<span class="cm"># Startup Hydration (service.py L164):</span>
<span class="cm"># 1. SELECT * from 7 SQLite tables (ZERO JOIN / ORDER BY / CTE!)</span>
<span class="cm"># 2. merge_sort posts ASC -&gt; load via insert_head() =&gt; newest at head!</span>
<span class="cm"># 3. merge_sort comments by seq_id =&gt; parent loads before child reply!</span>

<span class="cm"># Storage-only SQLite (repository.py):</span>
<span class="cm"># Canonical edge: (min(u,v), max(u,v)) | posts.image_path TEXT</span>""",
            [
                "<strong>Zero Graph SQL:</strong> SQLite stores raw rows only; every write updates RAM + SQLite atomically.",
                "<strong>Undo Stack:</strong> <code>undo_last_action()</code> checks state hasn't changed before cancelling request / restoring edge.",
                "<strong>UI Decoupling:</strong> Both Console CLI (<code>ScreenNavigator</code> Stack) and redesigned Streamlit UI (Quick Trie Search, View Profile &nearr;, Image Upload) call <code>CUConnectService</code> only.",
            ],
            "Passwords use 16-byte salted PBKDF2 with constant-time compare and a dummy hash on unknown users. On startup, CUConnectService hydrates all 7 CRUD-only SQLite tables into RAM, and both UIs talk exclusively to this facade."
        ),
    ]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CUConnect — 10-Minute Viva Code Explanation Guide</title>
<style>{BASE_CSS}</style>
</head>
<body>

<div class="cover-banner">
    {logo_html}
    <div>
        <div class="cover-kicker">Chanakya University &bull; DSA (EAI212/EVE203/EEC203) &bull; Prof. Nitish Hegde &bull; 40-Mark Viva</div>
        <div class="cover-title">CUConnect — 10-Minute Code Explanation Guide</div>
        <div class="cover-sub">Requirement-by-Requirement &amp; DSA-Mapped Code Walkthrough Designed to Explain Every Core File Clearly in Under 10 Minutes</div>
    </div>
</div>

<div class="sec-head">
    <h2>10-Minute Viva Pacing Plan (Minute-by-Minute Script)</h2>
    <span class="sec-tag">Total: 10:00 Mins</span>
</div>
<table>
    <thead>
        <tr>
            <th style="width:12%;">Time</th>
            <th style="width:14%;">Speaker</th>
            <th style="width:27%;">VS Code File / Screen to Open</th>
            <th style="width:47%;">Exact Points to Cover (Short &amp; High-Scoring)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>0:00&ndash;1:00</strong></td>
            <td><strong>Dhruv</strong></td>
            <td>Architecture + <code>core/service.py</code></td>
            <td>Problem G(V,E); 3-layer separation (Console + Streamlit &rarr; Facade &rarr; RAM DSA &rarr; CRUD-only SQLite); <code>check_rules.py</code> (0 violations) &amp; 50 passing tests.</td>
        </tr>
        <tr>
            <td><strong>1:00&ndash;2:30</strong></td>
            <td><strong>Dhruv</strong></td>
            <td><code>hash_table.py</code> &amp; <code>auth.py</code></td>
            <td>Base-31 polynomial rolling hash (no built-in <code>hash()</code>), separate chaining, 2&times; resize &gt; 0.75 (<code>next_node</code>), salted PBKDF2 + <code>hmac.compare_digest</code> + dummy hash.</td>
        </tr>
        <tr>
            <td><strong>2:30&ndash;4:15</strong></td>
            <td><strong>Pranam</strong></td>
            <td><code>graph.py</code> &amp; <code>connections.py</code></td>
            <td>Sorted adjacency lists O(V+E) vs matrix O(V&sup2;); <code>binary_search</code> O(log d); 2-pointer mutuals O(d<sub>u</sub>+d<sub>v</sub>); BFS Queue + <code>parent[]</code> (<code>aarav&rarr;isha</code> 4 hops <code>3+</code>); reverse auto-accept.</td>
        </tr>
        <tr>
            <td><strong>4:15&ndash;5:30</strong></td>
            <td><strong>Pranam</strong></td>
            <td><code>suggestions.py</code> &amp; <code>communities.py</code></td>
            <td>Depth-2 BFS + Jaccard (<code>meera=0.75</code>, <code>kabir=0.25</code>, <code>sneha=0.20</code>) + MinHeap; Iterative DFS + Stack (no recursion limit; live 10+5 &rarr; 15 community merge!).</td>
        </tr>
        <tr>
            <td><strong>5:30&ndash;7:00</strong></td>
            <td><strong>Dhruv</strong></td>
            <td><code>heap.py</code>, <code>feed.py</code> &amp; <code>avl_tree.py</code></td>
            <td><code>MinHeap</code> 3-tuple tie-breaker; k-way Home Feed merge O((k+N) log k) = <strong>0.09 ms</strong> at 5,000 users; AVL LL/RR/LR/RL rotations (height 5 for 18 students, A&ndash;Z in O(V)).</td>
        </tr>
        <tr>
            <td><strong>7:00&ndash;8:45</strong></td>
            <td><strong>Nihal</strong></td>
            <td><code>linked_list.py</code>, <code>queue_ds.py</code>, <code>trie.py</code>, <code>engagement.py</code></td>
            <td>O(1) <code>insert_head</code> + optional <code>image_path</code>; Queue <code>remove_value</code> fixing <code>_tail</code>; Trie <code>'diy'</code>/<code>'sh'</code> O(L) + Stack pruning; stable <code>merge_sort</code>; Pre-Order DFS comment trees + Trending early exit.</td>
        </tr>
        <tr>
            <td><strong>8:45&ndash;10:00</strong></td>
            <td><strong>All 3</strong></td>
            <td>Live Streamlit App + <code>repository.py</code></td>
            <td>Live demo: Feed with Rover/Certificate images, Quick Search <code>'diy'</code> &rarr; <strong>View Profile &nearr;</strong>, Undo Stack, write-through SQLite persistence &amp; Console CLI parity.</td>
        </tr>
    </tbody>
</table>

<div class="sec-head">
    <h2>Mini-Project PDF Requirements &rarr; Code File &rarr; DSA Syllabus Map</h2>
    <span class="sec-tag">100% Traceable</span>
</div>
<table>
    <thead>
        <tr>
            <th style="width:24%;">Mini-Project PDF Requirement</th>
            <th style="width:24%;">DSA Structure / Concept</th>
            <th style="width:24%;">Python File(s)</th>
            <th style="width:14%;">Complexity</th>
            <th style="width:14%;">Course Session</th>
        </tr>
    </thead>
    <tbody>
        <tr><td><strong>Part 1:</strong> Accounts &amp; Hashed Passwords</td><td>HashTable (Chaining, Poly Hash) + PBKDF2</td><td><code>ds/hash_table.py</code>, <code>auth.py</code></td><td>O(1) avg</td><td>Session 15</td></tr>
        <tr><td><strong>Part 2:</strong> Network, Mutuals, BFS Chain</td><td>Sorted Adj Lists, Binary Search, 2-Ptr, BFS</td><td><code>graph.py</code>, <code>ds/algorithms.py</code></td><td>O(log d) / O(V+E)</td><td>Sessions 3, 11, 12</td></tr>
        <tr><td><strong>Part 2:</strong> Pending Requests &amp; PYMK</td><td>Linked-list Queue; Depth-2 BFS + Jaccard + Heap</td><td><code>ds/queue_ds.py</code>, <code>connections.py</code>, <code>suggestions.py</code></td><td>O(1) enq / O(d&sup2;)</td><td>Sessions 7, 11, 15</td></tr>
        <tr><td><strong>Part 3:</strong> Posts (+ Images) &amp; Home Feed</td><td>SinglyLinkedList (head insert) + k-way MinHeap</td><td><code>ds/linked_list.py</code>, <code>posts.py</code>, <code>feed.py</code></td><td>O(1) / O((k+N)log k)</td><td>Sessions 4, 7, 15</td></tr>
        <tr><td><strong>Part 4:</strong> Live Prefix Search</td><td>Trie (HashTable children) + stable Merge Sort</td><td><code>ds/trie.py</code>, <code>search.py</code></td><td>O(L + M + U log U)</td><td>Sessions 8, 14, 15</td></tr>
        <tr><td><strong>Parts 5 &amp; 6:</strong> Persistence &amp; Dual UIs</td><td>Write-through SQLite CRUD + Facade + Stack Nav</td><td><code>repository.py</code>, <code>service.py</code>, <code>ui/*.py</code></td><td>O(1) writes</td><td>All Sessions</td></tr>
        <tr><td><strong>Enhancements (All 7):</strong> Images, Likes, Replies, Notifs, Trending, Undo, Communities, AVL</td><td>HashTable, N-ary Tree Pre-Order DFS, Queue, MinHeap, Stack, Iterative DFS, AVL (LL/RR/LR/RL)</td><td><code>engagement.py</code>, <code>notifications.py</code>, <code>communities.py</code>, <code>ds/stack.py</code>, <code>ds/avl_tree.py</code></td><td>O(1) / O(V+E) / O(log V)</td><td>Sessions 6, 7, 8, 10, 11, 15</td></tr>
    </tbody>
</table>

<div class="page-break"></div>
<div class="sec-head">
    <h2>Part A: Hand-Written Data Structures Explained (<code>core/ds/</code>)</h2>
    <span class="sec-tag">30 Marks Core Engine</span>
</div>
{"".join(cards_ds)}

<div class="page-break"></div>
<div class="sec-head">
    <h2>Part B: Core Algorithms, Persistence &amp; Enhancements Explained (<code>core/</code> &amp; <code>storage/</code>)</h2>
    <span class="sec-tag">High-Impact Viva Lines</span>
</div>
{"".join(cards_domain)}

<div class="callout teal" style="margin-top:8px;">
    <strong>Exact Seed Dry-Run Numbers to Quote While Explaining Code (<code>@aarav</code> / <code>chanakya2026</code>):</strong><br>
    &bull; <strong>Network:</strong> 18 Students, 23 Undirected Edges, 14 Posts (incl. Rover Demo &amp; Hackathon Certificate images), 3 Communities (sizes <strong>10, 5, 3</strong> &rarr; accepting <code>@pranav</code> merges to <strong>15</strong>).<br>
    &bull; <strong>PYMK (Jaccard):</strong> <code>meera = 3/4 (0.7500)</code> &gt; <code>kabir = 1/4 (0.2500)</code> &gt; <code>sneha = 1/5 (0.2000)</code>.<br>
    &bull; <strong>BFS Shortest Chain:</strong> <code>diya = 1st</code>, <code>meera = 2nd</code>, <code>vikram = 3rd</code>, <code>isha = 3+ (4 hops: aarav&rarr;rohan&rarr;sneha&rarr;arjun&rarr;isha)</code>, <code>pranav = Not connected</code>.<br>
    &bull; <strong>Trie / AVL / HashTable:</strong> <code>'sh'</code> &rarr; <code>aarav</code> (Sharma) &amp; <code>pranav</code> (Shetty); <code>'diy'</code> &rarr; <code>diya</code> &rarr; <strong>View Profile &nearr;</strong>; AVL Height = <strong>5</strong> (Balanced); HashTable LF = <strong>0.562</strong>.
</div>

<div class="callout">
    <strong>Last-Minute 15-Second Closing Punchline (If Examiner Asks &ldquo;Why Should This Project Get Full Marks?&rdquo;):</strong>
    &ldquo;Every single requirement and all 7 enhancements—including image posts—run strictly on our 8 hand-written Python data structures in memory with zero third-party DSA libraries and zero SQL graph queries. Every line is verified by 50 automated tests, our static AST rule checker (<code>check_rules.py</code>), and 5,000-user empirical benchmarks confirming O((k+N) log k) sub-millisecond feeds.&rdquo;
</div>

<div class="page-break"></div>
<div class="sec-head">
    <h2>Part C: Visual DSA Diagrams &amp; 5,000-User Benchmark Reference Sheet</h2>
    <span class="sec-tag">Show During Viva</span>
</div>
<div class="two-col">
    {f'<div class="diagram-wrap"><img src="{arch_uri}" alt="Architecture" style="max-height:175px;"/><div class="diagram-cap">Figure 1: Strict 3-Layer Decoupling (Zero Graph SQL).</div></div>' if arch_uri else ''}
    {f'<div class="diagram-wrap"><img src="{graph_uri}" alt="Seed Graph" style="max-height:175px;"/><div class="diagram-cap">Figure 2: Seed Graph G(V, E) — Solid = Accepted; Dashed = Pending.</div></div>' if graph_uri else ''}
    {f'<div class="diagram-wrap"><img src="{feed_uri}" alt="k-Way Feed Merge" style="max-height:175px;"/><div class="diagram-cap">Figure 3: Home Feed k-Way MinHeap Merge (Heap Size &le; k).</div></div>' if feed_uri else ''}
    {f'<div class="diagram-wrap"><img src="{avl_uri}" alt="AVL Rotations" style="max-height:175px;"/><div class="diagram-cap">Figure 4: AVL Rebalancing (LL, RR, LR, RL) — Height 5 for 18 Users.</div></div>' if avl_uri else ''}
</div>
{f'<div class="diagram-wrap" style="margin-top:8px;"><img src="{bench_uri}" alt="Empirical Benchmarks" style="max-height:220px;"/><div class="diagram-cap">Figure 5: Empirical Benchmarks (100 &rarr; 5,000 Users): Feed stays 0.09 ms, Trie 2.18 ms, PYMK 3.69 ms, BFS 6.72 ms.</div></div>' if bench_uri else ''}

</body>
</html>
"""
    return html


def _render_pdf(html: str, out_pdf: Path, footer_title: str) -> int:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
        tmp.write(html)
        tmp_path = Path(tmp.name)

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="msedge")
            except Exception:
                browser = p.chromium.launch(channel="chrome")
            page = browser.new_page()
            page.goto(tmp_path.as_uri(), wait_until="networkidle")
            page.pdf(
                path=str(out_pdf),
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template="<div></div>",
                footer_template=(
                    "<div style=\"width:100%;font-family:'Segoe UI',sans-serif;font-size:7.5pt;"
                    "color:#6B7280;padding:0 13mm;display:flex;justify-content:space-between;\">"
                    f"<span>{footer_title}</span>"
                    "<span>Page <span class='pageNumber'></span> of <span class='totalPages'></span></span>"
                    "</div>"
                ),
                margin={"top": "13mm", "bottom": "15mm", "left": "13mm", "right": "13mm"},
            )
            browser.close()
    finally:
        tmp_path.unlink(missing_ok=True)

    # Count pages lightly from PDF bytes (`/Type /Page` markers)
    raw = out_pdf.read_bytes()
    return raw.count(b"/Type /Page\n") + raw.count(b"/Type /Page ") + raw.count(b"/Type /Page/")


def main() -> int:
    q_pdf = DOCS / "VIVA_QUESTIONNAIRE.pdf"
    g_pdf = DOCS / "10MIN_CODE_EXPLANATION_GUIDE.pdf"

    _render_pdf(
        build_questionnaire_html(),
        q_pdf,
        "CUConnect — Faculty Viva Questionnaire (Chanakya University DSA)",
    )
    _render_pdf(
        build_10min_guide_html(),
        g_pdf,
        "CUConnect — 10-Minute Viva Code Explanation Guide (Chanakya University DSA)",
    )

    print(f"Generated: {q_pdf} ({q_pdf.stat().st_size // 1024} KB)")
    print(f"Generated: {g_pdf} ({g_pdf.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
