# scripts/build_ppt.py
# Builds docs/PRESENTATION.pptx (34 slides, 16:9, speaker notes on every slide) and exports slide PNGs via PowerPoint COM.
# Course mapping: Presentation & Viva Defense Deck for CUConnect.

from pathlib import Path
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DIAGRAMS = DOCS / "diagrams"
SHOTS = DIAGRAMS / "screenshots"
SLIDE_PNGS = DOCS / "diagrams" / "slides_preview"

NAVY = RGBColor(0x0F, 0x2A, 0x4A)
BLUE = RGBColor(0x1D, 0x4E, 0x89)
GOLD = RGBColor(0xD4, 0xA0, 0x17)
GOLD_DARK = RGBColor(0x92, 0x40, 0x0E)
TEAL = RGBColor(0x0D, 0x94, 0x88)
CORAL = RGBColor(0xDC, 0x26, 0x26)
DARK = RGBColor(0x1E, 0x29, 0x3B)
MUTED = RGBColor(0x47, 0x55, 0x69)
LIGHT_BG = RGBColor(0xF8, 0xFA, 0xFC)
LIGHT_BLUE = RGBColor(0xEB, 0xF3, 0xFA)
LIGHT_GOLD = RGBColor(0xFE, 0xF3, 0xC7)
LIGHT_TEAL = RGBColor(0xE6, 0xFA, 0xF5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BORDER = RGBColor(0xCB, 0xD5, 0xE1)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def _new_slide(prs: Presentation, title: str, subtitle: str, notes: str, slide_num: int, total: int = 34):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
    # Crisp light background
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = WHITE

    # Top Navy Header Bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), SLIDE_W, Inches(1.02))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()

    # Gold accent stripe under header
    stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.02), SLIDE_W, Inches(0.06))
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = GOLD
    stripe.line.fill.background()

    # Title text
    tb = slide.shapes.add_textbox(Inches(0.55), Inches(0.10), Inches(11.6), Inches(0.55))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = title
    r.font.name = "Calibri"
    r.font.size = Pt(24)
    r.font.bold = True
    r.font.color.rgb = WHITE

    # Subtitle text
    if subtitle:
        sb = slide.shapes.add_textbox(Inches(0.55), Inches(0.62), Inches(11.6), Inches(0.35))
        stf = sb.text_frame
        stf.word_wrap = True
        stf.margin_left = stf.margin_right = stf.margin_top = stf.margin_bottom = 0
        sp = stf.paragraphs[0]
        sr = sp.add_run()
        sr.text = subtitle
        sr.font.name = "Calibri"
        sr.font.size = Pt(12.5)
        sr.font.color.rgb = RGBColor(0xFD, 0xE6, 0x8A)

    # Footer
    ft = slide.shapes.add_textbox(Inches(0.55), Inches(7.12), Inches(12.2), Inches(0.3))
    ftf = ft.text_frame
    ftf.margin_left = ftf.margin_right = ftf.margin_top = ftf.margin_bottom = 0
    fp = ftf.paragraphs[0]
    fr = fp.add_run()
    fr.text = f"CUConnect  |  Chanakya University — Data Structures & Algorithms (2026–27)                                                                             Slide {slide_num} / {total}"
    fr.font.name = "Calibri"
    fr.font.size = Pt(9.5)
    fr.font.color.rgb = MUTED

    # Speaker notes
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def _card(slide, left, top, width, height, title, bullets, fill=LIGHT_BG, border=BORDER, title_color=NAVY, font_size=13.5):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    box.adjustments[0] = 0.04
    box.fill.solid()
    box.fill.fore_color.rgb = fill
    box.line.color.rgb = border
    box.line.width = Pt(1.2)

    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = Inches(0.2)
    tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.14)
    tf.margin_bottom = Inches(0.12)

    if title:
        p0 = tf.paragraphs[0]
        p0.alignment = PP_ALIGN.LEFT
        p0.space_after = Pt(6)
        r0 = p0.add_run()
        r0.text = title
        r0.font.name = "Calibri"
        r0.font.size = Pt(font_size + 2)
        r0.font.bold = True
        r0.font.color.rgb = title_color
        start_new = True
    else:
        start_new = False

    for idx, item in enumerate(bullets):
        p = tf.add_paragraph() if (start_new or idx > 0) else tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(5)
        if isinstance(item, tuple):
            lead, rest = item
            r1 = p.add_run()
            r1.text = "• " + lead
            r1.font.name = "Calibri"
            r1.font.size = Pt(font_size)
            r1.font.bold = True
            r1.font.color.rgb = NAVY
            r2 = p.add_run()
            r2.text = rest
            r2.font.name = "Calibri"
            r2.font.size = Pt(font_size)
            r2.font.color.rgb = DARK
        else:
            r = p.add_run()
            r.text = "• " + item
            r.font.name = "Calibri"
            r.font.size = Pt(font_size)
            r.font.color.rgb = DARK


def _add_table(slide, left, top, width, height, headers, rows, col_ratios=None, font_size=11.0):
    tbl_shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(left), Inches(top), Inches(width), Inches(height))
    tbl = tbl_shape.table

    if col_ratios:
        total_r = sum(col_ratios)
        for j, ratio in enumerate(col_ratios):
            tbl.columns[j].width = Inches(width * (ratio / total_r))

    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = Inches(0.08)
        cell.margin_right = Inches(0.08)
        cell.margin_top = Inches(0.04)
        cell.margin_bottom = Inches(0.04)
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = h
        r.font.name = "Calibri"
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = WHITE

    for i, row in enumerate(rows):
        bg = LIGHT_BG if i % 2 == 1 else WHITE
        for j, val in enumerate(row):
            cell = tbl.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run()
            r.text = val
            r.font.name = "Calibri"
            r.font.size = Pt(font_size)
            r.font.bold = (j == 0)
            r.font.color.rgb = NAVY if j == 0 else DARK


def _add_picture_fit(slide, img_path: Path, left: float, top: float, max_w: float, max_h: float):
    from PIL import Image

    with Image.open(img_path) as im:
        w_px, h_px = im.size
    aspect = w_px / h_px
    box_aspect = max_w / max_h
    if aspect > box_aspect:
        final_w = max_w
        final_h = max_w / aspect
        x = left
        y = top + (max_h - final_h) / 2
    else:
        final_h = max_h
        final_w = max_h * aspect
        x = left + (max_w - final_w) / 2
        y = top
    slide.shapes.add_picture(str(img_path), Inches(x), Inches(y), width=Inches(final_w), height=Inches(final_h))


def _viva_slide(prs: Presentation, slide_num: int, set_num: int, topic: str, qa_pairs: list[tuple[str, str]], notes: str):
    slide = _new_slide(
        prs,
        f"Sample Viva Q&A (Set {set_num}/6) — {topic}",
        "Concise examiner-ready questions and crisp model answers",
        notes,
        slide_num,
    )
    rows = [[f"Q{idx + 1}. {q}", a] for idx, (q, a) in enumerate(qa_pairs)]
    _add_table(
        slide,
        left=0.5,
        top=1.22,
        width=12.33,
        height=5.72,
        headers=["Viva Question", "Model Answer"],
        rows=rows,
        col_ratios=[4.3, 6.0],
        font_size=11.0,
    )


def build_presentation(out_path: Path) -> None:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s1.background.fill
    bg.solid()
    bg.fore_color.rgb = NAVY

    gold_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.28), SLIDE_H)
    gold_bar.fill.solid()
    gold_bar.fill.fore_color.rgb = GOLD
    gold_bar.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(0.95), Inches(0.95), Inches(11.5), Inches(5.8))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    r0 = p0.add_run()
    r0.text = "CHANAKYA UNIVERSITY, BANGALORE  •  SCHOOL OF ENGINEERING"
    r0.font.name = "Calibri"
    r0.font.size = Pt(15)
    r0.font.bold = True
    r0.font.color.rgb = RGBColor(0xFD, 0xE6, 0x8A)

    p1 = tf.add_paragraph()
    p1.space_before = Pt(18)
    r1 = p1.add_run()
    r1.text = "CUConnect"
    r1.font.name = "Calibri"
    r1.font.size = Pt(52)
    r1.font.bold = True
    r1.font.color.rgb = WHITE

    p2 = tf.add_paragraph()
    p2.space_before = Pt(8)
    r2 = p2.add_run()
    r2.text = "A Campus Student Networking Platform Built on Hand-Written Python Data Structures & Algorithms"
    r2.font.name = "Calibri"
    r2.font.size = Pt(20)
    r2.font.color.rgb = RGBColor(0xDC, 0xE6, 0xF2)

    # Metadata pill box
    meta = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.95), Inches(4.25), Inches(11.3), Inches(2.35))
    meta.adjustments[0] = 0.05
    meta.fill.solid()
    meta.fill.fore_color.rgb = RGBColor(0x16, 0x39, 0x62)
    meta.line.color.rgb = GOLD
    meta.line.width = Pt(1.5)
    mtf = meta.text_frame
    mtf.word_wrap = True
    mtf.margin_left = Inches(0.3)
    mtf.margin_top = Inches(0.2)
    lines = [
        ("Course: ", "Data Structures and Algorithms (EAI212 / EVE203 / EEC203) — III Semester B.Tech., 2026–27"),
        ("Faculty: ", "Prof. Nitish Hegde   |   Submission Date: 27-11-2026"),
        ("Team: ", "Dhruv Jha, Pranam Jogur, Nihal N"),
        ("Repository: ", "https://github.com/dhruvjha18jee-star"),
    ]
    for i, (k, v) in enumerate(lines):
        mp = mtf.paragraphs[0] if i == 0 else mtf.add_paragraph()
        mp.space_after = Pt(8)
        rk = mp.add_run()
        rk.text = k
        rk.font.name = "Calibri"
        rk.font.size = Pt(15)
        rk.font.bold = True
        rk.font.color.rgb = RGBColor(0xFD, 0xE6, 0x8A)
        rv = mp.add_run()
        rv.text = v
        rv.font.name = "Calibri"
        rv.font.size = Pt(15)
        rv.font.color.rgb = WHITE

    s1.notes_slide.notes_text_frame.text = (
        "Good morning everyone and Prof. Nitish Hegde. We are Dhruv Jha, Pranam Jogur, and Nihal N presenting "
        "CUConnect — our III Semester DSA mini-project for Chanakya University. Every data structure and graph "
        "algorithm in CUConnect is hand-written in pure Python standard library code so we can trace and explain every line."
    )

    # =========================================================================
    # SLIDE 2: PROBLEM STATEMENT & GOALS
    # =========================================================================
    s2 = _new_slide(
        prs,
        "Problem Statement, Goals & Assessment Focus",
        "Networking Chanakya University students through explicit DSA engineering",
        "Here is why we built CUConnect the way we did. The rubric awards 30 marks to core DSA usage and 40 marks to "
        "viva understanding, so we prioritized clean, explainable, hand-written structures over flashy UI shortcuts.",
        2,
    )
    _card(s2, 0.55, 1.32, 6.0, 5.55, "What CUConnect Solves", [
        ("Campus Networking Graph G(V, E): ", "Students share projects and technical ideas across CSAI, EVE, EECS, CSE, and Data Science."),
        ("Strict Graph Rules: ", "Undirected accepted edges, directed pending edges, zero self-loops, zero duplicate edges."),
        ("Pure Python Core: ", "Zero networkx, heapq, deque, sortedcontainers, or Python built-in sorted()/hash() inside core/."),
        ("In-Memory DSA Only: ", "SQLite stores data only — all BFS, DFS, Jaccard, feed merges, and prefix searches run in Python RAM."),
        ("All 6 Enhancements Included: ", "Notifications, likes & threaded comments, trending posts, undo/navigation stacks, communities, and AVL directory."),
    ], fill=LIGHT_BLUE, border=BLUE, font_size=13.5)

    _card(s2, 6.8, 1.32, 5.95, 2.65, "Rubric Weighting (100 Marks)", [
        ("Understanding & Viva — 40 Marks: ", "Short functions, clear comments, exact Big-O docstrings."),
        ("Core Engine & DSA — 30 Marks: ", "8 hand-written structures directly mapped to Sessions 1–15."),
        ("Implementation — 20 Marks: ", "49 automated tests + AST rule verifier + Console & Streamlit UIs."),
        ("Report — 10 Marks: ", "Concise 10-page design & benchmark report."),
    ], fill=LIGHT_GOLD, border=GOLD, title_color=GOLD_DARK, font_size=13)

    _card(s2, 6.8, 4.18, 5.95, 2.69, "Engineering Guarantees", [
        ("Injectable Clock & Sequence Counter: ", "100% deterministic feed, suggestions, and repeatable tests."),
        ("Salted PBKDF2 Authentication: ", "Zero plain-text passwords; timing-safe login errors."),
        ("Write-Through Persistence: ", "Every mutation survives full restart with zero data loss."),
    ], fill=LIGHT_TEAL, border=TEAL, font_size=13)

    # =========================================================================
    # SLIDE 3: ARCHITECTURE
    # =========================================================================
    s3 = _new_slide(
        prs,
        "System Architecture — Strict 3-Layer Decoupling",
        "Console CLI and Streamlit Web UI share one facade (core/service.py) and never touch DS or SQL",
        "This diagram shows our clean separation. Neither the console app nor Streamlit ever imports core.ds or storage. "
        "Both talk strictly to CUConnectService. At startup, SQLite hydrates all in-memory structures; after that, every "
        "change writes through immediately while every query runs strictly in RAM.",
        3,
    )
    _add_picture_fit(s3, DIAGRAMS / "architecture.png", 0.55, 1.22, 12.2, 5.7)

    # =========================================================================
    # SLIDE 4: GRAPH MODEL
    # =========================================================================
    s4 = _new_slide(
        prs,
        "The Graph Model G(V, E) — Example Campus Subgraph",
        "Undirected accepted edges (solid) vs. directed pending requests (dashed) — reused in all dry runs",
        "Every dry run in our report and slides uses this exact seeded subgraph centered on Aarav Sharma. Solid navy lines "
        "are accepted undirected connections stored in adjacency lists. Dashed arrows are directed pending requests stored in "
        "per-user queues. Notice distances from Aarav span 1st, 2nd, 3rd, 3+ (4 hops to Isha), and disconnected (Pranav).",
        4,
    )
    _add_picture_fit(s4, DIAGRAMS / "example_graph.png", 0.5, 1.18, 12.3, 5.8)

    # =========================================================================
    # SLIDE 5: FEATURE-TO-DS MAP (PART 1)
    # =========================================================================
    s5 = _new_slide(
        prs,
        "Feature → Data Structure → Course Session Map (Core)",
        "Direct traceability between mandatory project features and Chanakya University DSA syllabus",
        "Every single mandatory feature in the problem statement maps cleanly to a named session from Prof. Nitish Hegde's "
        "course outline — from Singly Linked Lists in Session 4 to Heaps and Hash Tables in Session 15.",
        5,
    )
    _add_table(
        s5, 0.5, 1.25, 12.33, 5.6,
        ["Core Feature", "Hand-Written Structure / Algorithm", "Module", "Course Session"],
        [
            ["Accounts & Profiles", "HashTable (separate chaining, poly hash)", "core/ds/hash_table.py", "Session 15: Heaps & Hash Tables"],
            ["Accepted Network G(V, E)", "Sorted Adjacency Lists in HashTable + binary_search", "core/graph.py", "Sessions 11 & 12: Graphs & Search"],
            ["Pending Connection Requests", "Linked-list Queue with remove_value", "core/connections.py", "Session 7: Queues"],
            ["Mutual Connections", "Two-pointer sorted list intersection", "core/graph.py", "Sessions 3 & 11: Arrays & Graphs"],
            ["Degree & Shortest Chain", "Breadth-First Search (Queue + parent map)", "core/graph.py", "Session 11: Graphs (BFS)"],
            ["People You May Know", "Depth-2 BFS + Jaccard + MinHeap (top-k)", "core/suggestions.py", "Sessions 11 & 15: Graphs & Heaps"],
            ["User Text Posts", "Per-user SinglyLinkedList (newest at head)", "core/posts.py", "Session 4: Singly Linked Lists"],
            ["Paginated Home Feed", "k-way merge using MinHeap (-ts, -seq)", "core/feed.py", "Sessions 4, 7 & 15"],
            ["As-You-Type User Search", "Trie (HashTable children) + merge_sort", "core/search.py", "Sessions 8, 14 & 15"],
        ],
        col_ratios=[2.5, 3.8, 2.2, 2.8],
        font_size=11.5,
    )

    # =========================================================================
    # SLIDE 6: FEATURE-TO-DS MAP (PART 2 — ENHANCEMENTS)
    # =========================================================================
    s6 = _new_slide(
        prs,
        "Feature → Data Structure → Course Session Map (Enhancements)",
        "All six enhancements backed by textbook DSA structures from Sessions 6, 7, 8, 10, 11, and 15",
        "Beyond the core requirements, we implemented all six enhancements — including the optional AVL Tree directory — "
        "so our project showcases Trees, AVL rotations, Iterative DFS, Stacks, Priority Queues, and Hash Tables end to end.",
        6,
    )
    _add_table(
        s6, 0.5, 1.35, 12.33, 5.2,
        ["Enhancement", "Hand-Written Structure / Algorithm", "Module", "Course Session"],
        [
            ["1. Notifications", "Per-user FIFO Queue inside HashTable", "core/notifications.py", "Session 7: Queues"],
            ["2a. Post Likes", "Per-post HashTable (username -> timestamp)", "core/engagement.py", "Session 15: Hash Tables"],
            ["2b. Threaded Comments", "N-ary Comment Tree displayed via Pre-Order DFS", "core/engagement.py", "Session 8: Trees (Traversals)"],
            ["3. Trending Posts", "Recent-window scan + MinHeap (likes + 2*comments)", "core/engagement.py", "Session 15: Heaps"],
            ["4. Undo & Back Navigation", "Linked-node LIFO Stack (service + CLI)", "core/ds/stack.py", "Session 6: Stacks"],
            ["5. Campus Communities", "Connected Components via Iterative DFS + Stack", "core/communities.py", "Sessions 6 & 11: Stacks & DFS"],
            ["6. Browse All Students", "Self-Balancing AVL Tree (LL, RR, LR, RL rotations)", "core/ds/avl_tree.py", "Session 10: AVL Trees"],
        ],
        col_ratios=[2.4, 3.9, 2.2, 2.8],
        font_size=12.0,
    )

    # =========================================================================
    # SLIDE 7: HASH TABLE
    # =========================================================================
    s7 = _new_slide(
        prs,
        "HashTable — Polynomial Rolling Hash, Chaining & Resizing",
        "Session 15: O(1) average lookup without calling Python's built-in hash()",
        "Our HashTable uses a base-31 polynomial rolling hash modulo 10^9 + 7 so anagrams like 'abc' and 'cba' land in "
        "different buckets. Separate chaining stores colliding nodes in short linked lists, avoiding deletion tombstones. "
        "Whenever size/capacity exceeds 0.75, capacity doubles and every node is rehashed.",
        7,
    )
    _add_picture_fit(s7, DIAGRAMS / "hash_table_chaining.png", 0.45, 1.2, 12.4, 4.45)
    _card(s7, 0.55, 5.72, 12.2, 1.25, "", [
        ("Example Trace: ", "hash('diya') = (((100*31 + 105)*31 + 121)*31 + 97) % 1_000_000_007 = 3,083,689  →  bucket = 3,083,689 % 16 = 9."),
        ("Verified Randomly: ", "Cross-checked against Python dict over 800 random put/get/remove/contains operations with 100% parity."),
    ], fill=LIGHT_BLUE, border=BLUE, font_size=12.2)

    # =========================================================================
    # SLIDE 8: PASSWORD SECURITY
    # =========================================================================
    s8 = _new_slide(
        prs,
        "Authentication & Password Security (core/auth.py)",
        "Defense-in-depth using Python standard library hashlib, os.urandom, and hmac",
        "Security is never an afterthought. Passwords are never stored or printed in plain text. Every user gets a fresh "
        "16-byte random salt with 100,000 PBKDF2-SHA256 iterations, compared in constant time via hmac.compare_digest.",
        8,
    )
    _card(s8, 0.55, 1.35, 6.0, 5.4, "Storage Format & Hashing Pipeline", [
        ("Unique Random Salt: ", "16 bytes from os.urandom(16) per account defeats precomputed rainbow tables."),
        ("Key Stretching: ", "hashlib.pbkdf2_hmac('sha256', pw, salt, 100_000) makes offline brute-force ~100,000x slower."),
        ("Self-Describing Format: ", "pbkdf2_sha256$100000$<salt_hex>$<hash_hex> stored in SQLite users table."),
        ("Safe Profile Projection: ", "User.public_profile() strips password_hash before sharing data."),
    ], fill=LIGHT_BLUE, border=BLUE, font_size=13.5)

    _card(s8, 6.8, 1.35, 5.95, 5.4, "Anti-Enumeration Login Verification", [
        ("Constant-Time Compare: ", "hmac.compare_digest() avoids character-by-character timing leaks."),
        ("Dummy Hash on Missing User: ", "If username is absent, login still runs PBKDF2 against a dummy hash so response latency stays uniform."),
        ("Uniform Error Message: ", "Both wrong password and unknown username raise the exact same AuthError('Invalid username or password.')."),
        ("Session Tracking: ", "Active logins stored in a HashTable supporting login, logout, and is_logged_in in O(1)."),
    ], fill=LIGHT_GOLD, border=GOLD, title_color=GOLD_DARK, font_size=13.5)

    # =========================================================================
    # SLIDE 9: ADJACENCY LISTS
    # =========================================================================
    s9 = _new_slide(
        prs,
        "Network Storage — Sorted Adjacency Lists (core/graph.py)",
        "Session 11 & Session 12: Why adjacency lists beat adjacency matrices for social networks",
        "Social networks are sparse: even with 5,000 students, each connects to only 10–50 peers. An adjacency matrix would "
        "waste 25 million cells, whereas our HashTable of sorted adjacency lists uses O(V + E) memory and lets us run "
        "binary_search for O(log d) edge checks.",
        9,
    )
    _add_table(
        s9, 0.55, 1.35, 12.2, 2.8,
        ["Operation / Metric", "Adjacency List (Ours, Sorted)", "Adjacency Matrix", "Winner for CUConnect"],
        [
            ["Space (V=5,000, E=25,000)", "O(V + E) ≈ 55,000 refs", "O(V²) = 25,000,000 cells", "Adjacency List (~450x smaller)"],
            ["Check edge has_edge(u, v)", "O(log deg(u)) via binary_search", "O(1)", "Both instant (< 0.005 ms)"],
            ["Iterate neighbors of u (BFS/Feed)", "O(deg(u)) ≈ 10 steps", "O(V) = 5,000 scans", "Adjacency List (~500x faster)"],
            ["Add new student vertex", "O(1) avg HashTable put", "O(V²) matrix reallocation", "Adjacency List"],
        ],
        col_ratios=[2.8, 3.0, 2.8, 2.8],
        font_size=11.8,
    )
    _card(s9, 0.55, 4.45, 12.2, 2.35, "Graph Invariants Strictly Enforced in SocialGraph", [
        ("No Self-Edges: ", "add_edge(u, u) raises ValidationError immediately."),
        ("No Duplicate Edges: ", "Checks binary_search(adj[u], v) != -1 before inserting; raises ConnectionRuleError on duplicates."),
        ("Guaranteed Symmetry: ", "add_edge and remove_edge always update BOTH adj[u] and adj[v] atomically."),
        ("Deterministic Order: ", "Keeping each neighbor list alphabetically sorted guarantees reproducible BFS chains and O(d_u + d_v) mutuals."),
    ], fill=LIGHT_TEAL, border=TEAL, font_size=13.0)

    # =========================================================================
    # SLIDE 10: REQUEST QUEUES & STATE MACHINE
    # =========================================================================
    s10 = _new_slide(
        prs,
        "Pending Request Queues & Connection Lifecycle",
        "Session 7: Linked-list Queue with O(1) enqueue/dequeue and out-of-order remove_value",
        "Pending requests are directed edges stored in both the sender's outgoing Queue and the receiver's incoming Queue. "
        "Because students don't always respond to the oldest request first, our Queue provides remove_value / remove_where "
        "to unlink any node cleanly while keeping tail pointers consistent. Reverse requests automatically accept!",
        10,
    )
    _add_picture_fit(s10, DIAGRAMS / "request_queue_states.png", 0.5, 1.22, 12.3, 5.65)

    # =========================================================================
    # SLIDE 11: MUTUAL CONNECTIONS
    # =========================================================================
    s11 = _new_slide(
        prs,
        "Mutual Connections — Two-Pointer Sorted Intersection",
        "Session 3 & Session 11: Linear-time intersection without allocating temporary hash sets",
        "Because every adjacency list is kept alphabetically sorted, finding mutual connections between two students is "
        "identical to the merge step of Merge Sort: advance two pointers i and j in O(deg(u) + deg(v)) time.",
        11,
    )
    _card(s11, 0.55, 1.32, 5.7, 5.45, "Algorithm Walkthrough", [
        ("Inputs: ", "Sorted neighbor lists A = adj[u], B = adj[v]."),
        ("Initialize: ", "i = 0, j = 0, mutuals = []."),
        ("Compare A[i] vs B[j]: ", "If equal → append A[i], increment both i and j."),
        ("Advance Smaller: ", "If A[i] < B[j] → i += 1; else → j += 1."),
        ("Complexity: ", "Time O(deg(u) + deg(v)), Extra Space O(min(deg(u), deg(v)))."),
        ("Bonus Reuse: ", "Directly feeds Jaccard numerator |N(u) ∩ N(v)| in People You May Know!"),
    ], fill=LIGHT_BLUE, border=BLUE, font_size=13.2)

    _add_table(
        s11, 6.5, 1.32, 6.3, 4.1,
        ["Step", "A = N(aarav)", "B = N(meera)", "Comparison & Action"],
        [
            ["1", "[ananya], diya, rohan", "[ananya], diya, rohan, vikram", "ananya == ananya → MATCH! i=1, j=1"],
            ["2", "ananya, [diya], rohan", "ananya, [diya], rohan, vikram", "diya == diya → MATCH! i=2, j=2"],
            ["3", "ananya, diya, [rohan]", "ananya, diya, [rohan], vikram", "rohan == rohan → MATCH! i=3, j=3"],
            ["4", "i == len(A) (done)", "vikram unread", "Loop stops → Result: [ananya, diya, rohan]"],
        ],
        col_ratios=[0.7, 2.0, 2.2, 2.8],
        font_size=11.0,
    )
    _card(s11, 6.5, 5.58, 6.3, 1.18, "", [
        ("Output: ", "3 mutual connections between @aarav and @meera: @ananya, @diya, @rohan — already sorted alphabetically!"),
    ], fill=LIGHT_GOLD, border=GOLD, font_size=12.5)

    # =========================================================================
    # SLIDE 12: BFS DEGREE & SHORTEST CHAIN DRY RUN
    # =========================================================================
    s12 = _new_slide(
        prs,
        "BFS Degree of Connection & Shortest Chain — Dry Run",
        "Session 11: Unweighted Breadth-First Search using our hand-written Queue and parent map",
        "BFS explores vertices strictly in order of hop distance: 0, 1, 2, 3, 4. That is why the very first time we discover "
        "the target vertex, we are guaranteed a shortest chain. Tracing from Aarav to Isha discovers Isha at distance 4, "
        "which CUConnect labels '3+' while still showing the complete 4-hop chain.",
        12,
    )
    _add_table(
        s12, 0.5, 1.25, 12.33, 4.15,
        ["Layer / Hop", "Dequeued", "Newly Discovered (parent pointer set)", "Frontier Queue After Step"],
        [
            ["Init (0)", "—", "visited = {aarav}, parent[aarav] = None", "[aarav]"],
            ["0 → 1 (1st)", "aarav", "ananya, diya, rohan (parent = aarav)", "[ananya, diya, rohan]"],
            ["1 → 2 (2nd)", "ananya", "meera (parent = ananya)", "[diya, rohan, meera]"],
            ["1 → 2 (2nd)", "diya", "kabir (parent = diya); meera skipped (visited)", "[rohan, meera, kabir]"],
            ["1 → 2 (2nd)", "rohan", "sneha (parent = rohan)", "[meera, kabir, sneha]"],
            ["2 → 3 (3rd)", "meera, kabir, sneha", "vikram (parent = meera), arjun (parent = sneha)", "[vikram, arjun]"],
            ["3 → 4 (3+)", "vikram, arjun", "isha (parent = arjun) → TARGET FOUND! Early exit", "stops immediately"],
        ],
        col_ratios=[1.5, 1.8, 4.5, 3.0],
        font_size=11.0,
    )
    _card(s12, 0.5, 5.55, 12.33, 1.35, "Path Reconstruction & Complexity", [
        ("Backtrack parent[]: ", "isha ← arjun ← sneha ← rohan ← aarav   ⇒   Reversed Shortest Chain: aarav → rohan → sneha → arjun → isha (Label: '3+', 4 hops)."),
        ("Why Not DFS? ", "DFS could detour through aarav → ananya → meera → vikram → arjun → isha (5 hops, NOT shortest!). BFS guarantees optimal O(V + E) shortest paths."),
    ], fill=LIGHT_TEAL, border=TEAL, font_size=12.4)

    # =========================================================================
    # SLIDE 13: JACCARD & PEOPLE YOU MAY KNOW
    # =========================================================================
    s13 = _new_slide(
        prs,
        "People You May Know — Depth-2 BFS + Jaccard + MinHeap",
        "Sessions 11 & 15: Ranking 2nd-degree peers by neighborhood overlap normalized by union",
        "Why use Jaccard instead of raw mutual count? Raw mutual count biases toward super-connected hubs. Jaccard divides "
        "mutual connections by total combined neighborhood size |N(u) U N(v)|. Here on Aarav's graph, Meera scores 3/4 = 0.75, "
        "Kabir scores 1/4 = 0.25, and Sneha scores 1/5 = 0.20 — exact, clean fractions ranked by our MinHeap.",
        13,
    )
    _card(s13, 0.5, 1.25, 12.33, 1.15, "", [
        ("Formula: ", "J(u, v) = |N(u) ∩ N(v)| / |N(u) ∪ N(v)|   where   |N(u) ∪ N(v)| = deg(u) + deg(v) − |N(u) ∩ N(v)|   (exact range [0, 1])."),
        ("3-Stage Pipeline: ", "(1) Depth-2 BFS with Queue finds non-connected friends-of-friends → (2) Compute Jaccard → (3) Rank top-k in MinHeap keyed by (-J, -mutuals, username)."),
    ], fill=LIGHT_GOLD, border=GOLD, font_size=12.5)

    _add_table(
        s13, 0.5, 2.58, 12.33, 2.85,
        ["Candidate v", "N(v)", "Mutuals with aarav", "Union Size", "Jaccard J", "MinHeap Priority Key & Rank"],
        [
            ["meera", "{ananya, diya, rohan, vikram}", "3: ananya, diya, rohan", "3 + 4 − 3 = 4", "3 / 4 = 0.7500", "(-0.75, -3, 'meera')  →  Rank #1"],
            ["kabir", "{diya, vikram}", "1: diya", "3 + 2 − 1 = 4", "1 / 4 = 0.2500", "(-0.25, -1, 'kabir')  →  Rank #2"],
            ["sneha", "{arjun, rohan, vikram}", "1: rohan", "3 + 3 − 1 = 5", "1 / 5 = 0.2000", "(-0.20, -1, 'sneha')  →  Rank #3"],
        ],
        col_ratios=[1.2, 2.7, 2.2, 1.4, 1.5, 2.7],
        font_size=11.5,
    )
    _card(s13, 0.5, 5.62, 12.33, 1.28, "Why Kabir (0.25) Beats Sneha (0.20) Despite Both Having 1 Mutual", [
        ("Fair Normalization: ", "Both Kabir and Sneha share 1 mutual friend with Aarav, but Kabir has degree 2 vs Sneha's degree 3 — a higher fraction of Kabir's circle overlaps Aarav's!"),
        ("Pending Filter: ", "Users who already have a pending request with Aarav (vikram, pranav, isha) are excluded so we never re-suggest them."),
    ], fill=LIGHT_BLUE, border=BLUE, font_size=12.4)

    # =========================================================================
    # SLIDE 14: LINKED-LIST POSTS
    # =========================================================================
    s14 = _new_slide(
        prs,
        "Text Posts — Per-User SinglyLinkedList (core/posts.py)",
        "Session 4: O(1) newest-at-head insertion unlocks pointer-driven k-way feed merging",
        "Each student owns a SinglyLinkedList of Post nodes stored inside a HashTable. When a student posts, insert_head "
        "prepends a new ListNode in O(1) without shifting any memory. Because every new post lands at the head, the list "
        "is permanently sorted newest-first — ready for our feed heap.",
        14,
    )
    _card(s14, 0.55, 1.32, 5.95, 5.45, "How PostManager Works", [
        ("Storage: ", "HashTable maps username → SinglyLinkedList of Post objects, plus a secondary HashTable maps post_id → Post in O(1)."),
        ("Create Post — O(1): ", "Validates non-empty content (<= 2000 chars), calls list.insert_head(post), writes through to SQLite."),
        ("View Own Posts — O(P_u): ", "Traverses from head to tail — already newest-first!"),
        ("Delete Own Post — O(P_u): ", "Checks post.author == actor (raises AuthorizationError otherwise), unlinks via delete_by_id, purges likes & comments."),
        ("Startup Hydration: ", "Loads posts from SQLite, sorts oldest-first via merge_sort, then prepends each so newest ends up at head."),
    ], fill=LIGHT_BLUE, border=BLUE, font_size=13.2)

    _card(s14, 6.75, 1.32, 6.0, 5.45, "Why SinglyLinkedList Instead of Dynamic Array?", [
        ("Zero Front-Insert Shifting: ", "Inserting newest posts at index 0 of a Python list takes O(P_u) shifts; SinglyLinkedList.insert_head is always O(1)."),
        ("Direct Node Pointer for k-Way Merge: ", "FeedEngine pushes each connection's head ListNode directly into MinHeap and advances via top_node.next in O(1)."),
        ("No Full-List Copy on Paging: ", "Fetching page 1 of a feed never touches older posts deep in any friend's linked list."),
        ("Trade-Off Accepted: ", "Deleting an older post is O(P_u) linear scan — completely acceptable because deletions are rare compared to reads and creations."),
    ], fill=LIGHT_TEAL, border=TEAL, font_size=13.2)

    # =========================================================================
    # SLIDE 15: HEAP K-WAY MERGE FEED
    # =========================================================================
    s15 = _new_slide(
        prs,
        "Home Feed — k-Way Merge with MinHeap (core/feed.py)",
        "Sessions 4, 7 & 15: Paginated newest-first feed in O((k + offset + N) log k)",
        "Instead of copying all posts from all connections and running an O(P log P) sort, we push only the head ListNode "
        "of each of your k connections into our MinHeap configured as a max-heap on (-created_at, -seq_id). Every pop yields "
        "the globally newest post and advances only that one connection's linked-list pointer.",
        15,
    )
    _add_picture_fit(s15, DIAGRAMS / "heap_kway_merge.png", 0.45, 1.2, 12.4, 4.55)
    _card(s15, 0.55, 5.82, 12.2, 1.12, "", [
        ("Empirical Proof: ", "At N = 5,000 users (15,000 posts), fetching a 10-post Home Feed page takes just 0.088 ms — independent of total network size!"),
    ], fill=LIGHT_GOLD, border=GOLD, font_size=12.8)

    # =========================================================================
    # SLIDE 16: TRIE SEARCH
    # =========================================================================
    s16 = _new_slide(
        prs,
        "As-You-Type User Search — Prefix Tree / Trie (core/search.py)",
        "Sessions 8, 14 & 15: O(L) prefix walk independent of total users, indexing username & name words",
        "Each TrieNode uses our own compact HashTable (initial_capacity=4) to map characters to child nodes. When a student "
        "signs up or edits their name, we index their lowercase username AND every word of their full name. Searching 'sh' "
        "walks just 2 hops and instantly finds Aarav Sharma and Pranav Shetty.",
        16,
    )
    _add_picture_fit(s16, DIAGRAMS / "trie_search.png", 0.45, 1.2, 12.4, 4.45)
    _card(s16, 0.55, 5.72, 12.2, 1.22, "", [
        ("Dynamic Profile Edits: ", "update_profile() calls reindex_user() — removes stale name words (pruning empty branches via Stack) and inserts new tokens."),
        ("Deterministic Output: ", "Collected user IDs are deduplicated and sorted alphabetically via our hand-written merge_sort."),
    ], fill=LIGHT_BLUE, border=BLUE, font_size=12.2)

    # =========================================================================
    # SLIDE 17: PERSISTENCE DESIGN
    # =========================================================================
    s17 = _new_slide(
        prs,
        "Persistence Design — Write-Through SQLite Storage Only",
        "Part 5 Rule: Zero graph computation in SQL — storage keeps raw data; DSA executes in RAM",
        "Our repository layer (storage/repository.py) uses only plain SELECT *, INSERT, UPDATE, and DELETE across 7 tables. "
        "Our automated AST checker scripts/check_rules.py fails the build if ANY SQL string ever contains JOIN, ORDER BY, "
        "GROUP BY, COUNT, or WITH RECURSIVE.",
        17,
    )
    _add_table(
        s17, 0.5, 1.25, 12.33, 3.85,
        ["SQLite Table", "Primary Key", "Stored Columns", "In-Memory Target Structure"],
        [
            ["users", "username", "password_hash, full_name, programme, year, bio, skills (JSON)", "AccountManager HashTable, Trie, AVLTree"],
            ["connections", "(user_a, user_b)", "Canonical pair (user_a < user_b), created_at", "SocialGraph sorted adjacency lists"],
            ["connection_requests", "(sender, receiver)", "created_at, seq_id", "Per-user incoming & outgoing Queues"],
            ["posts", "post_id", "author, content, created_at, seq_id", "Per-user SinglyLinkedList + post_id HashTable"],
            ["post_likes", "(post_id, username)", "created_at", "Per-post likes HashTable"],
            ["comments", "comment_id", "post_id, author, parent_comment_id, content, seq_id", "Per-post Comment Trees + comment_id HashTable"],
            ["notifications", "notification_id", "recipient, actor, kind, message, ref_id, is_read, seq_id", "Per-user Notification Queue"],
        ],
        col_ratios=[2.0, 2.0, 4.3, 3.5],
        font_size=10.8,
    )
    _card(s17, 0.5, 5.28, 12.33, 1.62, "Lifecycle Guarantee (Verified by test_full_restart_persistence)", [
        ("Startup Hydration: ", "Reads all 7 tables → sorts requests/posts/comments/notifications in Python via merge_sort → populates every structure in O(V log V + E + P log P)."),
        ("Write-Through Safety: ", "Every mutation updates RAM and commits a SQLite transaction immediately; restarting CUConnectService restores 100% identical state."),
    ], fill=LIGHT_TEAL, border=TEAL, font_size=12.4)

    # =========================================================================
    # SLIDE 18: INTERFACE SCREENSHOTS 1 (LOGIN & FEED)
    # =========================================================================
    s18 = _new_slide(
        prs,
        "Live Interface — Authentication Portal & Paginated Home Feed",
        "Real Streamlit screenshots captured directly against our seeded 18-student Chanakya University DB",
        "Left: The Login and Sign Up portal displays live in-memory campus counts (18 students, 23 connections, 14 posts, "
        "3 communities) plus demo credentials. Right: Aarav's Home Feed merges his 3 connections' linked lists using MinHeap, "
        "with inline Like buttons and expandable threaded comments.",
        18,
    )
    _add_picture_fit(s18, SHOTS / "ui_login.png", 0.45, 1.25, 6.05, 5.05)
    _add_picture_fit(s18, SHOTS / "ui_home_feed.png", 6.82, 1.25, 6.05, 5.05)
    _card(s18, 0.45, 6.38, 6.05, 0.56, "", ["Login / Sign-Up Portal (PBKDF2 + HashTable)"], fill=LIGHT_BLUE, border=BLUE, font_size=11.5)
    _card(s18, 6.82, 6.38, 6.05, 0.56, "", ["Home Feed (k-Way MinHeap Merge + Likes & Comments)"], fill=LIGHT_BLUE, border=BLUE, font_size=11.5)

    # =========================================================================
    # SLIDE 19: INTERFACE SCREENSHOTS 2 (SUGGESTIONS & DEGREE CHAIN)
    # =========================================================================
    s19 = _new_slide(
        prs,
        "Live Interface — People You May Know & BFS Shortest Chain",
        "Exact visual confirmation of our dry-run numbers right inside the running application",
        "Left: People You May Know shows Meera (Jaccard 0.7500, 3 mutuals), Kabir (0.2500, 1 mutual), and Sneha (0.2000, "
        "1 mutual) — matching our manual calculations to 4 decimal places. Right: BFS Degree & Chain displays '3+' (4 hops) "
        "and the exact path Aarav → Rohan → Sneha → Arjun → Isha.",
        19,
    )
    _add_picture_fit(s19, SHOTS / "ui_suggestions.png", 0.45, 1.25, 6.05, 5.05)
    _add_picture_fit(s19, SHOTS / "ui_degree_chain.png", 6.82, 1.25, 6.05, 5.05)
    _card(s19, 0.45, 6.38, 6.05, 0.56, "", ["People You May Know (Jaccard 0.75, 0.25, 0.20)"], fill=LIGHT_TEAL, border=TEAL, font_size=11.5)
    _card(s19, 6.82, 6.38, 6.05, 0.56, "", ["Degree & Chain Tool (BFS '3+' / 4-hop chain to @isha)"], fill=LIGHT_TEAL, border=TEAL, font_size=11.5)

    # =========================================================================
    # SLIDE 20: INTERFACE SCREENSHOTS 3 (TRIE SEARCH & CONSOLE CLI)
    # =========================================================================
    s20 = _new_slide(
        prs,
        "Live Interface — Trie Prefix Search & Console CLI App",
        "Both interfaces invoke the exact same CUConnectService facade with 100% feature parity",
        "Left: Typing 'sh' in Search Students instantly traverses our Trie and returns Aarav Sharma and Pranav Shetty "
        "with a one-click Accept button for Pranav's incoming request. Right: Our terminal Console App provides full parity "
        "plus Stack-powered breadcrumb back-navigation (e.g. Path: Home > Suggestions).",
        20,
    )
    _add_picture_fit(s20, SHOTS / "ui_search_trie.png", 0.45, 1.25, 6.4, 5.5)
    _card(s20, 7.1, 1.32, 5.7, 5.4, "Console App (ui/console_app.py)", [
        ("Zero Direct DS Imports: ", "Imports only CUConnectService and ScreenNavigator from core.service."),
        ("Stack Back-Navigation: ", "Every menu choice pushes onto ScreenNavigator's Stack; pressing 'b' pops cleanly to the prior screen."),
        ("Breadcrumb Header: ", "Always displays live path (e.g., Home > Connections) and unread notification count."),
        ("Masked Password Input: ", "Uses getpass.getpass() so credentials never echo to the terminal."),
        ("All 13 Actions Supported: ", "Feed paging, posts, profile edit, Trie search, requests, PYMK, BFS, notifications, trending, communities, AVL browse, undo, and live DSA stats."),
    ], fill=LIGHT_BG, border=NAVY, font_size=12.6)

    # =========================================================================
    # SLIDE 21: ENHANCEMENTS 1 & 2 (NOTIFICATIONS, LIKES & COMMENT TREE)
    # =========================================================================
    s21 = _new_slide(
        prs,
        "Enhancements 1 & 2 — Notifications Queue, Likes & Comment Trees",
        "Sessions 7, 8 & 15: FIFO notification queues, O(1) like tables, and Pre-Order DFS threaded replies",
        "Enhancement 1 tracks every connection request, acceptance, like, comment, and reply in a per-user Queue with live "
        "unread counts. Enhancement 2 stores likes in a per-post HashTable (preventing duplicate likes in O(1)) and models "
        "nested comment replies as an n-ary tree traversed with pre-order DFS so replies render directly under their parent.",
        21,
    )
    _card(s21, 0.55, 1.32, 5.95, 5.45, "Enhancement 1: Notifications (Queue)", [
        ("Structure: ", "HashTable maps username → FIFO Queue of Notification objects; secondary HashTable maps notification_id → Notification."),
        ("Triggered Events: ", "connection_request, request_accepted, post_like, post_comment, comment_reply."),
        ("Unread Tracking: ", "unread_count() scans the user's queue; mark_read() updates in O(1) and writes through to SQLite."),
        ("Self-Suppression: ", "Liking or commenting on your own post never generates noisy self-notifications."),
    ], fill=LIGHT_BLUE, border=BLUE, font_size=13.2)

    _card(s21, 6.8, 1.32, 5.95, 5.45, "Enhancement 2: Likes & Threaded Comments", [
        ("Likes — Per-Post HashTable: ", "Maps post_id → HashTable(username → timestamp). Toggle/check runs in O(1) average; duplicate likes impossible."),
        ("Comments — Tree of Replies: ", "Each Comment node stores parent_comment_id and replies: list[Comment]."),
        ("Pre-Order DFS Rendering: ", "Visit(comment, depth) → recursively visit each child at depth+1. Guarantees every reply sits immediately beneath its parent."),
        ("Seed Example (Rohan's Rover Post): ", "Depth 0: @aarav → Depth 1: @rohan reply → Depth 2: @meera nested reply!"),
    ], fill=LIGHT_GOLD, border=GOLD, title_color=GOLD_DARK, font_size=13.2)

    # =========================================================================
    # SLIDE 22: ENHANCEMENTS 3 & 4 (TRENDING POSTS & UNDO STACK)
    # =========================================================================
    s22 = _new_slide(
        prs,
        "Enhancements 3 & 4 — Trending Posts (MinHeap) & Undo Stack",
        "Sessions 6 & 15: Engagement-ranked recent posts + reversible connection history",
        "Left: Trending Posts scans each connection's newest-first linked list only until the 7-day cutoff, scores each post "
        "as likes + 2*comments, and extracts top-k via MinHeap. Right: Every send_request and remove_connection pushes an "
        "UndoAction onto the user's LIFO Stack so mistakes reverse in one click.",
        22,
    )
    _add_picture_fit(s22, SHOTS / "ui_trending.png", 0.45, 1.25, 6.45, 5.5)
    _card(s22, 7.15, 1.32, 5.65, 5.4, "Enhancement 4: Undo & Nav Stack (LIFO)", [
        ("Per-User Undo Stack: ", "HashTable maps username → hand-written Stack of UndoAction."),
        ("Undo send_request: ", "Verifies request is still pending → cancels it from both Queues and SQLite."),
        ("Undo remove_connection: ", "Verifies edge is still absent → restores both directions in SocialGraph and SQLite."),
        ("Safe State Guard: ", "If receiver already accepted before sender clicks Undo, raises a clear ValidationError instead of corrupting the graph!"),
        ("Console Back-Navigation: ", "ScreenNavigator wraps the exact same Stack class for menu history."),
    ], fill=LIGHT_TEAL, border=TEAL, font_size=12.8)

    # =========================================================================
    # SLIDE 23: ENHANCEMENT 5 (COMMUNITIES VIA ITERATIVE DFS)
    # =========================================================================
    s23 = _new_slide(
        prs,
        "Enhancement 5 — Campus Communities (Iterative DFS + Stack)",
        "Sessions 6 & 11: Connected components without recursion limit risk",
        "CommunityDetector discovers connected components by iterating over all users and running iterative DFS with our "
        "hand-written Stack whenever an unvisited vertex is found. On our seeded campus graph, it cleanly discovers three "
        "communities: CSAI/Systems Hub (10), VLSI & Robotics Lab (5), and First-Year Builders Guild (3).",
        23,
    )
    _add_picture_fit(s23, SHOTS / "ui_communities.png", 0.45, 1.25, 6.5, 5.5)
    _card(s23, 7.2, 1.32, 5.6, 5.4, "Iterative DFS Algorithm & Demo Twist", [
        ("Algorithm: ", "For each unvisited u in graph.users(), push u onto Stack; pop current, mark & push unvisited neighbors."),
        ("Why Iterative Instead of Recursive? ", "Avoids Python's default 1,000-frame recursion limit on large graphs AND visually contrasts DFS (Stack) with BFS (Queue)."),
        ("Complexity: ", "Time O(V log V + E) including alphabetical sorting via merge_sort; Space O(V)."),
        ("Live Viva Demo Moment: ", "Before accepting @pranav's request, communities are [10, 5, 3]. Accepting merges Community #1 and #2 into size 15 right before your eyes!"),
    ], fill=LIGHT_BLUE, border=BLUE, font_size=12.8)

    # =========================================================================
    # SLIDE 24: ENHANCEMENT 6 (AVL TREE DIRECTORY)
    # =========================================================================
    s24 = _new_slide(
        prs,
        "Enhancement 6 — Alphabetical Directory via AVL Tree",
        "Session 10: Self-balancing BST with explicit LL, RR, LR, and RL rotations",
        "Rather than re-sorting all students on every directory view, CUConnect maintains an AVL Tree keyed by "
        "(full_name.lower(), username). Every insert, delete, and name update rebalances in O(log V) via LL, RR, LR, or RL "
        "rotations. On 18 students, height is just 5 (verified balanced), and in-order traversal outputs A–Z in O(V).",
        24,
    )
    _add_picture_fit(s24, DIAGRAMS / "avl_rotations.png", 0.45, 1.22, 6.2, 5.5)
    _add_picture_fit(s24, SHOTS / "ui_avl_directory.png", 6.8, 1.22, 6.05, 5.5)

    # =========================================================================
    # SLIDE 25: COMPLEXITY SUMMARY TABLE
    # =========================================================================
    s25 = _new_slide(
        prs,
        "Master Time & Space Complexity Summary",
        "Session 2: Every public function in core/ documents exact Big-O bounds (enforced by check_rules.py)",
        "This master cheat-table summarizes the exact time and space complexity of every core operation. Notice how the "
        "most frequent real-time actions — login, profile lookup, posting, liking, and paginated feed loading — all avoid "
        "scanning the full user base V.",
        25,
    )
    _add_table(
        s25, 0.45, 1.22, 12.43, 5.7,
        ["Operation", "Underlying DS / Algo", "Time Complexity", "Space Complexity"],
        [
            ["Sign up / Login / Profile lookup", "HashTable + PBKDF2", "O(1) avg (+ fixed PBKDF2)", "O(1)"],
            ["Add / Remove connection edge", "Sorted Adj Lists in HashTable", "O(deg(u) + deg(v))", "O(1)"],
            ["Check connection has_edge(u, v)", "binary_search on sorted adj[u]", "O(log deg(u))", "O(1)"],
            ["Send / Accept / Reject / Cancel request", "Per-user linked-list Queue", "O(1) enq; O(r) remove_value", "O(1)"],
            ["Mutual connections", "Two-pointer sorted intersection", "O(deg(u) + deg(v))", "O(min(deg(u), deg(v)))"],
            ["Degree & Shortest Chain", "BFS with Queue + parent map", "O(V + E)", "O(V)"],
            ["People You May Know (top-k)", "Depth-2 BFS + Jaccard + MinHeap", "O(d² + C log C)", "O(d + C)"],
            ["Create post / Delete own post", "Per-user SinglyLinkedList", "O(1) create / O(P_u) delete", "O(1)"],
            ["Home Feed page (size N from k friends)", "k-way merge with MinHeap", "O((k + offset + N) log k)", "O(k + N)"],
            ["Prefix user search (len L)", "Trie + iterative DFS + merge_sort", "O(L + M + U log U)", "O(M + U)"],
            ["Like post / Render comment thread", "Per-post HashTable / Pre-Order DFS", "O(1) like / O(C) comments", "O(1) / O(C)"],
            ["Communities / Browse All Students", "Iterative DFS (Stack) / AVL In-Order", "O(V log V + E) / O(V)", "O(V)"],
        ],
        col_ratios=[3.3, 3.2, 3.1, 2.0],
        font_size=10.8,
    )

    # =========================================================================
    # SLIDE 26: TESTING & BENCHMARK RESULTS
    # =========================================================================
    s26 = _new_slide(
        prs,
        "Testing, Rule Verification & Empirical Benchmarks (100 → 5,000 Users)",
        "49 passing automated tests + AST rule verifier + empirical proof of theoretical Big-O scaling",
        "Look at the benchmark chart: BFS grows linearly with V+E (0.03 ms → 6.72 ms), confirming O(V+E). Meanwhile, "
        "Home Feed stays at 0.09 ms even at 5,000 users because k-way heap merge depends only on your friend count k, "
        "not the total campus size! All 49 unit, randomized cross-check, E2E, and restart-persistence tests pass.",
        26,
    )
    _add_picture_fit(s26, DIAGRAMS / "benchmark_chart.png", 0.45, 1.18, 12.4, 4.45)
    _card(s26, 0.5, 5.7, 12.33, 1.25, "", [
        ("49/49 Tests Pass (pytest): ", "Randomized cross-checks (HashTable vs dict, MinHeap vs sorted, Trie vs linear filter, AVL vs sorted + balance), edge-case request rules, and full restart persistence."),
        ("Static AST Checker (scripts/check_rules.py): ", "0 violations — proves stdlib-only core, zero heapq/deque/sorted/built-in hash(), zero graph SQL, and Time/Space docstrings on every public core method."),
    ], fill=LIGHT_TEAL, border=TEAL, font_size=11.8)

    # =========================================================================
    # SLIDE 27: DESIGN DECISIONS, LIMITATIONS & TEAM CONTRIBUTIONS
    # =========================================================================
    s27 = _new_slide(
        prs,
        "Design Trade-Offs, Limitations & Team Contributions",
        "Conscious engineering choices and balanced ownership across all three team members",
        "Every design involves trade-offs. Separate chaining beat open addressing because deletions are frequent. In-memory "
        "structures deliver sub-millisecond performance up to ~50k users, while million-user scale would need graph sharding "
        "and bidirectional BFS. All three team members reviewed and can explain every file in the codebase.",
        27,
    )
    _card(s27, 0.5, 1.25, 5.95, 3.05, "Key Trade-Offs Made", [
        ("Chaining vs Open Addressing: ", "Chaining handles frequent deletes cleanly without tombstones."),
        ("Sorted Adj Lists vs HashSet: ", "Enables O(d_u + d_v) two-pointer mutuals & deterministic BFS order."),
        ("k-Way Heap vs Full Sort: ", "Avoids sorting all P historical posts when only top 10 are needed."),
        ("Write-Through vs Batch Flush: ", "Slightly slower writes, but zero data loss on crash/restart."),
    ], fill=LIGHT_BLUE, border=BLUE, font_size=12.0)

    _card(s27, 6.75, 1.25, 6.05, 3.05, "Limitations & Future Work", [
        ("Single-Process RAM: ", "Ideal for campus scale (< 50k users); web-scale needs distributed graph storage."),
        ("Community Granularity: ", "Connected components split disconnected subgraphs; Louvain modularity could find clusters inside one giant component."),
        ("Future Extensions: ", "Bidirectional BFS for million-node graphs, user blocking (negative edges), and media attachment URLs."),
    ], fill=LIGHT_GOLD, border=GOLD, title_color=GOLD_DARK, font_size=12.0)

    _add_table(
        s27, 0.5, 4.48, 12.3, 2.42,
        ["Team Member", "Primary Ownership", "Shared Deliverables"],
        [
            ["Dhruv Jha", "HashTable, MinHeap, AVLTree, Auth (PBKDF2), FeedEngine, Service Facade, Benchmarks", "Code reviews, E2E tests, Report & Viva Prep"],
            ["Pranam Jogur", "SocialGraph (Adj Lists, BFS, Mutuals), ConnectionManager, Suggestions (Jaccard), Communities", "Seed topology, Edge-case tests, Dry runs"],
            ["Nihal N", "SinglyLinkedList, Queue, Stack, Trie, merge_sort/binary_search, Posts, Engagement, Console & Streamlit UIs", "SQLite Repository, UI Screenshots, Docs"],
        ],
        col_ratios=[1.8, 6.2, 3.5],
        font_size=11.0,
    )

    # =========================================================================
    # SLIDE 28: LIVE DEMO SCRIPT
    # =========================================================================
    s28 = _new_slide(
        prs,
        "5-Minute Live Demo Flow (Seeded Campus Dataset)",
        "Reproducible step-by-step walkthrough showcasing every DSA structure live",
        "During our live demo we run against the seeded 18-student database and walk through seven quick stops in under "
        "five minutes, ending with a live restart proving SQLite write-through persistence.",
        28,
    )
    _add_table(
        s28, 0.5, 1.25, 12.33, 5.65,
        ["Time", "Screen / Action", "What to Highlight to Examiner (DSA Link)"],
        [
            ["0:00–0:40", "Login as aarav / chanakya2026 (try wrong password first)", "Uniform error message (no user enumeration) + PBKDF2 + HashTable O(1) lookup."],
            ["0:40–1:30", "Home Feed → Like post → Expand threaded comments → Reply", "k-way MinHeap merge of SinglyLinkedLists, per-post HashTable like, Pre-Order DFS tree."],
            ["1:30–2:15", "People You May Know → Show Meera (0.75), Kabir (0.25), Sneha (0.20)", "Depth-2 BFS + exact Jaccard fractions + mutual lists + MinHeap top-k ranking."],
            ["2:15–2:55", "Degree & Chain Tool → Select isha (3+, 4 hops), then pranav (Not connected)", "Unweighted BFS with Queue + parent map reconstructing shortest chain."],
            ["2:55–3:35", "Search Users → Type 'sh' → Show Aarav Sharma & Pranav Shetty", "Trie indexing both usernames and name tokens in O(L) hops."],
            ["3:35–4:20", "Connections → Accept pranav → Check Communities → Remove & Undo!", "Queue remove_value, Communities merge 10+5→15 (Iterative DFS), Undo via LIFO Stack."],
            ["4:20–5:00", "Browse All Students (AVL Height=5) + Restart Streamlit / Run Console CLI", "AVL in-order A–Z directory + write-through SQLite persistence + shared service facade."],
        ],
        col_ratios=[1.2, 4.3, 5.8],
        font_size=11.2,
    )

    # =========================================================================
    # SLIDES 29–34: SIX SLIDES OF SAMPLE VIVA Q&A (5 QUESTIONS EACH = 30 Q&As)
    # =========================================================================
    _viva_slide(
        prs, 29, 1, "Hash Tables, Authentication & Complexity",
        [
            ("Why write a polynomial rolling hash instead of summing ASCII values?",
             "Summing ASCII hashes anagrams ('abc', 'cba') to the same bucket. Multiplying by prime base 31 weights each character's position, spreading keys evenly."),
            ("Why resize when load factor exceeds 0.75?",
             "Above 0.75, average chain length grows and lookups degrade toward O(n). Doubling buckets and rehashing restores short chains and O(1) amortized put/get."),
            ("Why separate chaining instead of open addressing (linear probing)?",
             "CUConnect deletes keys often (unliking, removing edges, Trie pruning). Open addressing requires tombstones and suffers primary clustering; chaining unlinks nodes cleanly."),
            ("Why PBKDF2 with random salt instead of hashlib.sha256(password)?",
             "Plain SHA-256 is fast (billions of guesses/sec on GPUs) and vulnerable to rainbow tables. A 16-byte random salt + 100,000 PBKDF2 iterations blocks both."),
            ("Why run a dummy PBKDF2 hash when a username doesn't exist?",
             "Prevents timing side-channel attacks: if missing users returned instantly while wrong passwords took ~50ms, attackers could enumerate valid campus usernames."),
        ],
        "Set 1 covers Session 15 Hash Tables and security. Emphasize WHY we chose base 31, 0.75 load factor, separate chaining, and PBKDF2.",
    )

    _viva_slide(
        prs, 30, 2, "Graphs, Adjacency Lists & Request Queues",
        [
            ("How does CUConnect model accepted vs pending relationships?",
             "Accepted connections are undirected edges {u, v} in SocialGraph adjacency lists; pending requests are directed edges u → v in u.outgoing and v.incoming Queues."),
            ("Why store each user's adjacency list in sorted order?",
             "Allows O(log d) edge checks with our binary_search, O(d_u + d_v) two-pointer mutual intersection, and deterministic alphabetical BFS shortest paths."),
            ("Why use a linked-list Queue instead of a Python list for requests and BFS?",
             "Python list.pop(0) shifts all remaining items in O(n). Our linked-list Queue keeps head & tail pointers so both enqueue and dequeue run in strict O(1)."),
            ("Why does our Queue have a remove_value method?",
             "Connection requests arrive FIFO, but a student can accept, reject, or cancel a request in the middle of the queue; remove_value unlinks it and fixes tail if needed."),
            ("What happens if Bob sent Alice a request and Alice sends Bob one?",
             "ConnectionManager detects the reverse pending request (Bob → Alice), removes it from both queues, adds undirected edge {Alice, Bob}, and returns 'auto_accepted'."),
        ],
        "Set 2 focuses on Session 7 Queues and Session 11 Graphs. Be ready to explain how Queue.remove_value updates self._tail when removing the rear node.",
    )

    _viva_slide(
        prs, 31, 3, "BFS, Degrees, Mutual Connections & Jaccard",
        [
            ("Why does BFS guarantee the shortest connection chain while DFS does not?",
             "BFS expands vertices strictly by hop count (layer 0, 1, 2, ...) via a FIFO Queue, so the first visit to target is provably minimum hops. DFS dives deep arbitrarily."),
            ("How is the shortest chain reconstructed after BFS reaches the target?",
             "Each time we discover an unvisited neighbor w from current, we set parent[w] = current. Once target is reached, we backtrack parent[] to source and reverse."),
            ("Why do we mark a node visited when enqueueing rather than when dequeueing?",
             "Marking on enqueue prevents the same vertex from being pushed into the Queue multiple times by different neighbors in the same layer, keeping Space O(V)."),
            ("Why use Jaccard coefficient instead of raw mutual-friend count?",
             "Raw mutual count favors high-degree hubs. Jaccard = |N(u)∩N(v)| / |N(u)∪N(v)| normalizes overlap by neighborhood size, ranking tighter circles higher."),
            ("Why run BFS only to depth 2 for People You May Know?",
             "Depth 0 is self and depth 1 are already connected. Depth 2 captures every user who shares at least one mutual connection (non-zero Jaccard) in O(d²) time."),
        ],
        "Set 3 covers BFS and Suggestions. Examiners love asking why visited is set at enqueue time and why Jaccard normalizes by the union.",
    )

    _viva_slide(
        prs, 32, 4, "Linked Lists, MinHeap k-Way Feed & Trie Search",
        [
            ("Why store each user's posts in a SinglyLinkedList with head insertion?",
             "Prepending at head takes O(1) and keeps posts naturally sorted newest-first, so k-way feed merging can read straight from each friend's head pointer."),
            ("How does one MinHeap act as a Max-Heap for our Home Feed and Trending?",
             "MinHeap accepts a key function. Passing key=lambda n: (-n.value.created_at, -n.value.seq_id) negates timestamps so the newest post has the smallest key and pops first."),
            ("Why is k-way heap merge better than collecting all posts and calling merge_sort?",
             "Collecting & sorting all P posts from k friends takes O(P log P). k-way merge keeps heap size ≤ k and fetches a page of N posts in O((k + N) log k) — 0.09 ms at 5,000 users!"),
            ("How does our MinHeap break ties deterministically without crashing on objects?",
             "Each heap entry stores (priority_key, insertion_counter, item). Equal priority keys compare the integer counter and never call '<' on Post or Suggestion dataclasses."),
            ("Why use a Trie instead of scanning all users with str.startswith()?",
             "Scanning all users is O(V * L). A Trie walks the prefix in O(L) hops independent of V, and indexes every word of a student's name so 'sh' finds 'Aarav Sharma'."),
        ],
        "Set 4 covers Sessions 4, 8, and 15. Highlight the exact 0.09 ms benchmark result for k-way heap feed at 5,000 users!",
    )

    _viva_slide(
        prs, 33, 5, "Stacks, Trees, AVL Rotations & DFS",
        [
            ("How are comment replies stored and why use Pre-Order DFS to display them?",
             "Each Comment holds a list of child replies (an n-ary tree). Pre-Order DFS visits parent before children, placing every nested reply immediately beneath its parent."),
            ("Why use Iterative DFS with our own Stack for Communities?",
             "Avoids Python's 1,000-frame recursion limit on large graphs and cleanly demonstrates how swapping a Queue (BFS) for a Stack (DFS) changes traversal order."),
            ("What problem with plain BSTs does our AVL Tree solve?",
             "If students sign up in alphabetical order, a plain BST degenerates into a skewed linked list with O(V) height. AVL rotations keep height ≤ 1.44 log₂(V) = O(log V)."),
            ("Explain the 4 AVL rotation cases (LL, RR, LR, RL).",
             "LL (BF=+2, left BF≥0): right rotate. RR (BF=-2, right BF≤0): left rotate. LR (BF=+2, left BF<0): left rotate child then right rotate. RL: right rotate child then left rotate."),
            ("How does Undo prevent corrupting the graph if state changed meanwhile?",
             "Before undoing send_request, CUConnectService checks the request is still pending (not already accepted). If state changed, it pops safely and raises ValidationError."),
        ],
        "Set 5 covers Sessions 6, 8, 10, and 11. Make sure every teammate can draw the LL, RR, LR, and RL AVL rotations on the board!",
    )

    _viva_slide(
        prs, 34, 6, "Persistence, Comparisons & 'What If' Scaling",
        [
            ("Why keep all DSA in Python RAM instead of running SQL JOINs?",
             "The project tests our DSA engine directly (and avoids DB round-trips per hop). SQLite handles durability via write-through CRUD while Python runs O(1)/O(V+E) DSA."),
            ("Merge Sort vs Quick Sort vs Heap Sort — why did we implement Merge Sort?",
             "Merge Sort guarantees O(n log n) worst-case (Quick Sort can hit O(n²)) AND is stable (Heap Sort is not), preserving deterministic order on equal keys."),
            ("What if CUConnect scaled to 1 million users?",
             "Replace single-source BFS with Bidirectional BFS (cuts visited nodes from b^d to 2*b^(d/2)), shard adjacency lists across servers, and cache hot feeds."),
            ("What if the network became directed (like Instagram followers)?",
             "Store separate out_adj (following) and in_adj (followers) HashTables; remove symmetry in add_edge/remove_edge; communities become Strongly Connected Components (Kosaraju/Tarjan)."),
            ("How would you add a 'Block User' feature?",
             "Add a per-user blocked HashTable; on block, remove any existing edge & pending requests, reject future requests, and filter blocked users in Suggestions & Search."),
        ],
        "Final slide! Thank Prof. Nitish Hegde and invite live questions or hands-on inspection of the code and Streamlit app. Repository: https://github.com/dhruvjha18jee-star",
    )
    # Add thank-you / GitHub subtitle on Slide 34 cleanly
    s34 = prs.slides[-1]
    for shape in s34.shapes:
        if shape.has_text_frame and "Concise examiner-ready" in shape.text_frame.text:
            shape.text_frame.paragraphs[0].runs[0].text = "Thank you!  •  GitHub: https://github.com/dhruvjha18jee-star  •  Dhruv Jha, Pranam Jogur, Nihal N"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    print(f"Saved PowerPoint deck ({len(prs.slides)} slides) to {out_path}")


def export_slides_to_png(pptx_path: Path, out_dir: Path) -> list[Path]:
    """Render every slide of PRESENTATION.pptx to PNG using installed PowerPoint COM automation."""
    import win32com.client

    out_dir.mkdir(parents=True, exist_ok=True)
    for existing in out_dir.glob("*.png"):
        existing.unlink()

    ppt = win32com.client.DispatchEx("PowerPoint.Application")
    try:
        pres = ppt.Presentations.Open(str(pptx_path.resolve()), ReadOnly=True, Untitled=False, WithWindow=False)
        try:
            # Export all slides as 1280x720 PNGs
            pres.Export(str(out_dir.resolve()), "PNG", 1280, 720)
        finally:
            pres.Close()
    finally:
        ppt.Quit()

    pngs = sorted(out_dir.glob("*.PNG"), key=lambda p: int("".join(ch for ch in p.stem if ch.isdigit()) or 0))
    if not pngs:
        pngs = sorted(out_dir.glob("*.png"), key=lambda p: int("".join(ch for ch in p.stem if ch.isdigit()) or 0))
    print(f"Exported {len(pngs)} slide PNGs to {out_dir}")
    return pngs


def main() -> None:
    pptx_path = DOCS / "PRESENTATION.pptx"
    build_presentation(pptx_path)
    export_slides_to_png(pptx_path, SLIDE_PNGS)


if __name__ == "__main__":
    main()
