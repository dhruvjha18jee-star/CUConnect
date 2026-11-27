# scripts/generate_diagrams.py
# Generates crisp, publication-quality DSA and architecture diagrams for the report and slides.
# Course mapping: Visual explanations for Sessions 4, 6, 7, 8, 10, 11, 14, and 15.

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "diagrams"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NAVY = "#0F2A4A"
BLUE = "#1D4E89"
GOLD = "#D4A017"
TEAL = "#0D9488"
CORAL = "#DC2626"
SLATE = "#475569"
LIGHT_BG = "#F8FAFC"
LIGHT_BLUE = "#EBF3FA"
LIGHT_GOLD = "#FEF3C7"
LIGHT_TEAL = "#CCFBF1"
LIGHT_CORAL = "#FEE2E2"


def _box(ax, x, y, w, h, title, subtitle="", fc=LIGHT_BLUE, ec=NAVY, title_color=NAVY, fontsize=10, lw=1.6):
    rect = patches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.04",
        facecolor=fc, edgecolor=ec, linewidth=lw,
    )
    ax.add_patch(rect)
    if subtitle:
        ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=title_color)
        ax.text(x + w / 2, y + h * 0.28, subtitle, ha="center", va="center",
                fontsize=fontsize - 1.8, color=SLATE)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=title_color)


def _arrow(ax, x1, y1, x2, y2, color=NAVY, lw=1.8, style="-|>", rad=0.0, ls="-"):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, lw=lw, linestyle=ls,
                        connectionstyle=f"arc3,rad={rad}"),
    )


def draw_architecture() -> None:
    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=180)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5.4)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(5.5, 5.1, "CUConnect — Layered System Architecture (Zero Graph Logic in SQL)",
            ha="center", va="center", fontsize=13.5, fontweight="bold", color=NAVY)

    # Layer 1: UIs
    _box(ax, 0.5, 3.85, 4.4, 0.85, "Console App (ui/console_app.py)",
         "Menu CLI + Stack back-navigation", fc=LIGHT_BLUE, ec=BLUE)
    _box(ax, 6.1, 3.85, 4.4, 0.85, "Streamlit Web App (ui/streamlit_app.py)",
         "11 interactive views + Auth portal", fc=LIGHT_BLUE, ec=BLUE)

    # Layer 2: Facade
    _box(ax, 0.4, 2.55, 10.2, 0.82, "Core Engine Facade (core/service.py — CUConnectService)",
         "Single entry point | Injectable clock | Deterministic seq counter | Undo Stack | AVL Directory",
         fc=LIGHT_GOLD, ec=GOLD, title_color="#78350F")

    _arrow(ax, 2.7, 3.85, 3.8, 3.39, BLUE)
    _arrow(ax, 8.3, 3.85, 7.2, 3.39, BLUE)

    # Layer 3: Domain + DS
    domains = [
        ("Accounts\nHashTable\nPBKDF2", 0.4),
        ("SocialGraph\nAdj Lists\nBFS / Mutuals", 2.15),
        ("Requests &\nNotifs\nQueues", 3.9),
        ("Posts & Feed\nLinkedLists +\nMinHeap", 5.65),
        ("Search &\nBrowse\nTrie + AVL", 7.4),
        ("Engage &\nCommunities\nTree DFS/Stack", 9.15),
    ]
    for label, x in domains:
        _box(ax, x, 1.15, 1.5, 0.98, label, fc=LIGHT_TEAL, ec=TEAL, title_color=NAVY, fontsize=8.3)
        _arrow(ax, x + 0.75, 2.55, x + 0.75, 2.15, TEAL, lw=1.4)

    # Layer 4: Persistence
    _box(ax, 1.5, 0.15, 8.0, 0.68, "Storage-Only Repository (storage/repository.py — SQLite3)",
         "Startup full hydration -> In-memory execution | Write-through CRUD only (no JOIN / ORDER BY / CTE)",
         fc="#F1F5F9", ec=SLATE, title_color=NAVY, fontsize=9.5)
    _arrow(ax, 5.5, 1.15, 5.5, 0.85, SLATE, style="<->", lw=1.8)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "architecture.png", dpi=180)
    plt.close(fig)


def draw_example_graph() -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.6), dpi=180)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(5.25, 5.3, "CUConnect Core Example Graph G(V, E) — Undirected Accepted vs. Directed Pending Edges",
            ha="center", va="center", fontsize=12.5, fontweight="bold", color=NAVY)

    # Coordinates for 10 nodes in Community 1 + pranav (Comm 2)
    pos = {
        "aarav": (1.2, 2.7),
        "ananya": (3.0, 4.15),
        "diya": (3.0, 2.7),
        "rohan": (3.0, 1.25),
        "meera": (5.1, 3.15),
        "kabir": (5.1, 4.35),
        "sneha": (5.1, 1.25),
        "vikram": (7.1, 2.8),
        "arjun": (8.6, 1.7),
        "isha": (9.7, 3.3),
        "pranav": (1.2, 0.75),
    }

    undirected = [
        ("aarav", "ananya"), ("aarav", "diya"), ("aarav", "rohan"),
        ("ananya", "meera"), ("diya", "meera"), ("diya", "kabir"),
        ("rohan", "meera"), ("rohan", "sneha"),
        ("meera", "vikram"), ("kabir", "vikram"), ("sneha", "vikram"),
        ("vikram", "arjun"), ("sneha", "arjun"), ("arjun", "isha"),
    ]
    for u, v in undirected:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        ax.plot([x1, x2], [y1, y2], color=NAVY, linewidth=2.0, zorder=1)

    # Directed pending requests (dashed coral/gold arrows)
    _arrow(ax, pos["vikram"][0] - 0.12, pos["vikram"][1] + 0.40,
           pos["aarav"][0] + 0.15, pos["aarav"][1] + 0.42, color=CORAL, lw=1.7, rad=0.38, ls="--")
    ax.text(4.1, 4.92, "Incoming Pending: vikram → aarav", fontsize=8.5, color=CORAL, fontweight="bold", ha="center")

    _arrow(ax, pos["pranav"][0], pos["pranav"][1] + 0.42,
           pos["aarav"][0], pos["aarav"][1] - 0.44, color=CORAL, lw=1.7, ls="--")
    ax.text(0.45, 1.72, "Pending:\npranav\n→ aarav", fontsize=7.8, color=CORAL, fontweight="bold", ha="center")

    _arrow(ax, pos["aarav"][0] + 0.25, pos["aarav"][1] - 0.36,
           pos["isha"][0] - 0.15, pos["isha"][1] - 0.42, color=GOLD, lw=1.7, rad=0.36, ls="--")
    ax.text(6.65, 0.72, "Outgoing Pending: aarav → isha", fontsize=8.5, color="#92400E", fontweight="bold", ha="center")

    # Node colors by BFS degree from aarav
    colors = {
        "aarav": (NAVY, "white", "0 (Self)"),
        "ananya": (BLUE, "white", "1st"),
        "diya": (BLUE, "white", "1st"),
        "rohan": (BLUE, "white", "1st"),
        "meera": (TEAL, "white", "2nd (J=0.75)"),
        "kabir": (TEAL, "white", "2nd (J=0.25)"),
        "sneha": (TEAL, "white", "2nd (J=0.20)"),
        "vikram": (GOLD, NAVY, "3rd"),
        "arjun": (GOLD, NAVY, "3rd"),
        "isha": (CORAL, "white", "3+ (4 hops)"),
        "pranav": ("#CBD5E1", NAVY, "Comm #2"),
    }

    for node, (x, y) in pos.items():
        fc, tc, tag = colors[node]
        circle = patches.Circle((x, y), 0.42, facecolor=fc, edgecolor=NAVY, linewidth=1.6, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y + 0.05, node, ha="center", va="center", fontsize=8.8, fontweight="bold", color=tc, zorder=4)
        ax.text(x, y - 0.54, tag, ha="center", va="top", fontsize=7.5, color=SLATE, fontweight="bold")

    # Legend strip cleanly placed along top-right blank area
    legend_items = [
        patches.Patch(facecolor=NAVY, label="Source (aarav)"),
        patches.Patch(facecolor=BLUE, label="1st Degree"),
        patches.Patch(facecolor=TEAL, label="2nd (PYMK)"),
        patches.Patch(facecolor=GOLD, label="3rd Degree"),
        patches.Patch(facecolor=CORAL, label="3+ (4 hops)"),
        patches.Patch(facecolor="#CBD5E1", label="Comm #2"),
    ]
    ax.legend(handles=legend_items, loc="upper right", bbox_to_anchor=(0.99, 0.93), ncol=2, fontsize=7.8, frameon=True)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "example_graph.png", dpi=180)
    plt.close(fig)


def draw_hash_table() -> None:
    fig, ax = plt.subplots(figsize=(10.5, 4.6), dpi=180)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(5.25, 4.3, "Hand-Written HashTable — Polynomial Rolling Hash + Separate Chaining",
            ha="center", va="center", fontsize=12.5, fontweight="bold", color=NAVY)

    # Left: hash formula box
    _box(ax, 0.3, 2.35, 3.2, 1.55,
         "Polynomial Rolling Hash",
         "h = (h * 31 + ord(ch)) % (10^9 + 7)\nbucket = h % capacity\nNo Python built-in hash()",
         fc=LIGHT_GOLD, ec=GOLD, title_color="#78350F", fontsize=9.5)

    _box(ax, 0.3, 0.5, 3.2, 1.55,
         "Automatic Resize & Rehash",
         "Initial capacity = 16 buckets\nTrigger: load_factor = n/cap > 0.75\nAction: double cap & rehash all nodes",
         fc=LIGHT_TEAL, ec=TEAL, title_color=NAVY, fontsize=9.5)

    # Right: buckets + chains
    ax.text(4.65, 3.85, "Bucket Array", ha="center", va="center", fontsize=9.8, fontweight="bold", color=NAVY)
    buckets = [
        (0, []),
        (1, [("aarav", "User(Aarav)"), ("sneha", "User(Sneha)")]),
        (2, [("diya", "User(Diya)")]),
        (3, []),
        (4, [("rohan", "User(Rohan)")]),
        (5, [("meera", "User(Meera)"), ("kabir", "User(Kabir)")]),
    ]
    for row_i, (bidx, chain) in enumerate(buckets):
        y = 3.25 - row_i * 0.56
        _box(ax, 4.15, y, 1.0, 0.42, f"[{bidx}]", fc=LIGHT_BLUE, ec=NAVY, fontsize=9)
        cx = 5.55
        if not chain:
            ax.text(cx + 0.15, y + 0.21, "None", va="center", fontsize=8.5, color=SLATE, style="italic")
        else:
            _arrow(ax, 5.15, y + 0.21, cx, y + 0.21, NAVY, lw=1.4)
            for j, (k, v) in enumerate(chain):
                _box(ax, cx, y, 1.95, 0.42, f"{k} → {v}", fc="white", ec=BLUE, fontsize=7.8, lw=1.3)
                if j < len(chain) - 1:
                    _arrow(ax, cx + 1.95, y + 0.21, cx + 2.35, y + 0.21, BLUE, lw=1.4)
                    cx += 2.35
                else:
                    ax.text(cx + 2.08, y + 0.21, "→ None", va="center", fontsize=8, color=SLATE)

    _arrow(ax, 3.5, 3.15, 4.12, 2.9, GOLD, lw=2.0)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "hash_table_chaining.png", dpi=180)
    plt.close(fig)


def draw_request_queue_states() -> None:
    fig, ax = plt.subplots(figsize=(10.5, 4.5), dpi=180)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 4.5)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(5.25, 4.2, "Connection Lifecycle State Diagram & Per-User Request Queues",
            ha="center", va="center", fontsize=12.5, fontweight="bold", color=NAVY)

    _box(ax, 0.4, 2.1, 2.2, 0.9, "No Edge", "u, v disconnected", fc="#F1F5F9", ec=SLATE)
    _box(ax, 3.85, 2.1, 2.75, 0.9, "Pending Directed Edge", "u → v in u.outgoing & v.incoming Queues", fc=LIGHT_GOLD, ec=GOLD, title_color="#78350F", fontsize=9.2)
    _box(ax, 7.85, 2.1, 2.3, 0.9, "Connected (Undirected)", "u ↔ v in SocialGraph adj lists", fc=LIGHT_TEAL, ec=TEAL, fontsize=9.2)

    # Transitions
    _arrow(ax, 2.6, 2.72, 3.83, 2.72, BLUE, lw=2.0)
    ax.text(3.22, 2.92, "send(u, v)", ha="center", fontsize=8.5, fontweight="bold", color=BLUE)

    _arrow(ax, 3.83, 2.28, 2.6, 2.28, CORAL, lw=1.8)
    ax.text(3.22, 1.98, "reject(v) / cancel(u)\n(Queue.remove_value)", ha="center", fontsize=8, color=CORAL)

    _arrow(ax, 6.62, 2.72, 7.83, 2.72, TEAL, lw=2.0)
    ax.text(7.22, 3.12, "accept(v) OR\nreverse send(v, u)\n(auto-accept!)", ha="center", fontsize=8, fontweight="bold", color=TEAL)

    _arrow(ax, 8.95, 2.08, 1.5, 2.08, SLATE, lw=1.6, rad=-0.22, ls="--")
    ax.text(5.25, 0.90, "remove_connection(u, v) — removes both directions & pushes UndoAction onto Stack",
            ha="center", fontsize=8.8, fontweight="bold", color=NAVY)

    # Guard notes at bottom
    _box(ax, 0.7, 0.15, 9.1, 0.52,
         "Invariants: No self-request  |  No duplicates  |  Only receiver accepts/rejects  |  Only sender cancels",
         fc=LIGHT_BLUE, ec=BLUE, fontsize=8.8)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "request_queue_states.png", dpi=180)
    plt.close(fig)


def draw_heap_kway_merge() -> None:
    fig, ax = plt.subplots(figsize=(10.5, 4.8), dpi=180)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 4.8)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(5.25, 4.5, "Home Feed k-Way Merge: Per-User SinglyLinkedLists + Max-Heap (MinHeap on -timestamp)",
            ha="center", va="center", fontsize=11.8, fontweight="bold", color=NAVY)

    # 3 connections' linked lists on left
    lists = [
        ("rohan (head)", [("t=45h", "Rover demo"), ("t=4h", "SLAM map")], 3.45),
        ("ananya (head)", [("t=42h", "k-way merge"), ("t=8h", "AVL diagrams")], 2.25),
        ("diya (head)", [("t=38h", "HashTable 40%"), ("t=0h", "BPE tokenizer")], 1.05),
    ]
    for label, nodes, y in lists:
        ax.text(0.2, y + 0.25, label, ha="left", va="center", fontsize=8.6, fontweight="bold", color=NAVY)
        x = 1.5
        for idx, (ts, title) in enumerate(nodes):
            fc = LIGHT_GOLD if idx == 0 else "white"
            ec = GOLD if idx == 0 else SLATE
            _box(ax, x, y, 1.55, 0.5, f"{ts}: {title}", fc=fc, ec=ec, fontsize=7.6)
            if idx < len(nodes) - 1:
                _arrow(ax, x + 1.55, y + 0.25, x + 1.85, y + 0.25, NAVY, lw=1.4)
                x += 1.85
            else:
                ax.text(x + 1.63, y + 0.25, "→ None", va="center", fontsize=7.6, color=SLATE)

    # Center: MinHeap (size <= k = 3)
    _box(ax, 6.05, 1.5, 1.9, 2.2, "", fc=LIGHT_BLUE, ec=NAVY, lw=1.8)
    ax.text(7.0, 3.48, "MinHeap (size ≤ k)", ha="center", fontsize=9.2, fontweight="bold", color=NAVY)
    ax.text(7.0, 3.22, "key = (-ts, -seq)", ha="center", fontsize=7.8, color=SLATE)
    # Heap tree inside box
    c_root = patches.Circle((7.0, 2.75), 0.28, facecolor=CORAL, edgecolor=NAVY, lw=1.3)
    c_l = patches.Circle((6.53, 2.0), 0.25, facecolor=TEAL, edgecolor=NAVY, lw=1.3)
    c_r = patches.Circle((7.48, 2.0), 0.25, facecolor=TEAL, edgecolor=NAVY, lw=1.3)
    for c in (c_root, c_l, c_r):
        ax.add_patch(c)
    ax.plot([6.86, 6.63], [2.52, 2.22], color=NAVY, lw=1.3)
    ax.plot([7.14, 7.38], [2.52, 2.22], color=NAVY, lw=1.3)
    ax.text(7.0, 2.75, "45h", ha="center", va="center", fontsize=8, fontweight="bold", color="white")
    ax.text(6.53, 2.0, "42h", ha="center", va="center", fontsize=8, fontweight="bold", color="white")
    ax.text(7.48, 2.0, "38h", ha="center", va="center", fontsize=8, fontweight="bold", color="white")

    _arrow(ax, 5.55, 3.7, 6.03, 3.05, GOLD, lw=1.6)
    _arrow(ax, 5.55, 2.5, 6.03, 2.5, GOLD, lw=1.6)
    _arrow(ax, 5.55, 1.3, 6.03, 1.95, GOLD, lw=1.6)

    # Right: Output Feed Page
    _box(ax, 8.35, 1.05, 1.95, 3.0, "", fc=LIGHT_TEAL, ec=TEAL, lw=1.8)
    ax.text(9.32, 3.82, "Paged Home Feed", ha="center", fontsize=9.2, fontweight="bold", color=NAVY)
    feed_rows = ["1. rohan (45h)", "2. ananya (42h)", "3. diya (38h)", "4. ananya (8h)", "5. rohan (4h)"]
    for i, line in enumerate(feed_rows):
        ax.text(8.52, 3.35 - i * 0.48, line, ha="left", va="center", fontsize=8.4, color=NAVY, fontweight="bold" if i < 3 else "normal")
    _arrow(ax, 7.92, 2.65, 8.33, 2.65, CORAL, lw=2.0)

    ax.text(5.25, 0.35, "Pop newest node → push node.next into MinHeap → Time: O((k + N) log k) instead of O(P log P)",
            ha="center", fontsize=9.2, fontweight="bold", color=NAVY)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "heap_kway_merge.png", dpi=180)
    plt.close(fig)


def draw_trie_search() -> None:
    fig, ax = plt.subplots(figsize=(10.5, 4.7), dpi=180)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 4.7)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(5.25, 4.4, "Trie (Prefix Tree) Search Dry Run — Indexing Usernames & Name Words",
            ha="center", va="center", fontsize=12.3, fontweight="bold", color=NAVY)

    # Draw a clean mini-trie showing 'aarav', 'ananya', 'sharma' (-> aarav), 'shetty' (-> pranav)
    nodes = {
        "root": (5.2, 3.75, "ROOT", NAVY, "white"),
        "a": (2.6, 2.95, "a", BLUE, "white"),
        "aa": (1.5, 2.05, "a", TEAL, "white"),
        "aarav": (1.5, 0.95, "...rav\n{aarav}", LIGHT_TEAL, NAVY),
        "an": (3.6, 2.05, "n", TEAL, "white"),
        "ananya": (3.6, 0.95, "...anya\n{ananya}", LIGHT_TEAL, NAVY),
        "s": (7.7, 2.95, "s", GOLD, NAVY),
        "sh": (7.7, 2.05, "h", GOLD, NAVY),
        "sharma": (6.5, 0.95, "...arma\n{aarav}", LIGHT_GOLD, "#78350F"),
        "shetty": (8.9, 0.95, "...etty\n{pranav}", LIGHT_GOLD, "#78350F"),
    }
    edges = [
        ("root", "a"), ("a", "aa"), ("aa", "aarav"), ("a", "an"), ("an", "ananya"),
        ("root", "s"), ("s", "sh"), ("sh", "sharma"), ("sh", "shetty"),
    ]
    for u, v in edges:
        x1, y1 = nodes[u][0], nodes[u][1]
        x2, y2 = nodes[v][0], nodes[v][1]
        is_sh = (u in ("root", "s", "sh") and v in ("s", "sh", "sharma", "shetty"))
        ax.plot([x1, x2], [y1, y2], color=GOLD if is_sh else NAVY, lw=2.4 if is_sh else 1.7, zorder=1)

    for key, (x, y, label, fc, tc) in nodes.items():
        if "\n" in label:
            _box(ax, x - 0.85, y - 0.35, 1.7, 0.72, label, fc=fc, ec=NAVY, title_color=tc, fontsize=8.3)
        else:
            r = 0.32 if key == "root" else 0.27
            c = patches.Circle((x, y), r, facecolor=fc, edgecolor=NAVY, lw=1.6, zorder=3)
            ax.add_patch(c)
            ax.text(x, y, label, ha="center", va="center", fontsize=9, fontweight="bold", color=tc, zorder=4)

    _box(ax, 0.4, 0.08, 9.7, 0.45,
         'Example Query: prefix_search("sh") → walks root → s → h in O(2), collects subtree → [aarav, pranav]',
         fc=LIGHT_BLUE, ec=BLUE, fontsize=9)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "trie_search.png", dpi=180)
    plt.close(fig)


def draw_avl_rotations() -> None:
    fig, ax = plt.subplots(figsize=(10.5, 4.4), dpi=180)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 4.4)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(5.25, 4.1, "AVL Tree Rebalancing (LL, RR, LR, RL Rotations) — Alphabetical Student Directory",
            ha="center", va="center", fontsize=12, fontweight="bold", color=NAVY)

    cards = [
        (0.3, "LL Imbalance (BF = +2)", "Left-heavy on left child\n→ Single Right Rotation\nExample: 30, 20, 10 → root 20", LIGHT_BLUE, BLUE),
        (2.85, "RR Imbalance (BF = -2)", "Right-heavy on right child\n→ Single Left Rotation\nExample: 10, 20, 30 → root 20", LIGHT_TEAL, TEAL),
        (5.4, "LR Imbalance (BF = +2)", "Left child is right-heavy\n→ Left Rotate child, then Right\nExample: 30, 10, 20 → root 20", LIGHT_GOLD, GOLD),
        (7.95, "RL Imbalance (BF = -2)", "Right child is left-heavy\n→ Right Rotate child, then Left\nExample: 10, 30, 20 → root 20", LIGHT_CORAL, CORAL),
    ]
    for x, title, desc, fc, ec in cards:
        _box(ax, x, 1.35, 2.3, 2.35, title, desc, fc=fc, ec=ec, fontsize=9)

    _box(ax, 0.5, 0.25, 9.5, 0.78,
         "Guarantee: |balance_factor| ≤ 1 at every node → Height ≤ 1.44 log₂(n)",
         "On 18 CUConnect students: AVL height = 5 (balanced) | In-order traversal yields exact A→Z directory in O(V)",
         fc="#F8FAFC", ec=NAVY, fontsize=9.5)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "avl_rotations.png", dpi=180)
    plt.close(fig)


def main() -> None:
    draw_architecture()
    draw_example_graph()
    draw_hash_table()
    draw_request_queue_states()
    draw_heap_kway_merge()
    draw_trie_search()
    draw_avl_rotations()
    print(f"Generated 7 diagrams in {OUT_DIR}")


if __name__ == "__main__":
    main()
