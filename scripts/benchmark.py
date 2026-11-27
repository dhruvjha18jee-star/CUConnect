# scripts/benchmark.py
# Benchmarks BFS, Jaccard suggestions, k-way heap feed, and Trie search on 100, 1,000, and 5,000 users.
# Course mapping: Session 2: Time and Space Complexity (Empirical Verification of Big-O Bounds).

import argparse
import json
from pathlib import Path
import random
import sys
import time

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.auth import AccountManager
from core.connections import ConnectionManager
from core.feed import FeedEngine
from core.graph import SocialGraph
from core.models import User
from core.posts import PostManager
from core.search import UserSearchIndex
from core.suggestions import SuggestionEngine

FIRST_NAMES = [
    "Aarav", "Diya", "Rohan", "Meera", "Kabir", "Ananya", "Vikram", "Sneha",
    "Arjun", "Isha", "Pranav", "Tanvi", "Siddharth", "Nisha", "Karthik", "Riya",
    "Dev", "Aditya", "Priya", "Nikhil", "Kavya", "Harsh", "Pooja", "Varun",
]
LAST_NAMES = [
    "Sharma", "Nair", "Verma", "Iyer", "Menon", "Rao", "Kulkarni", "Joshi",
    "Deshmukh", "Reddy", "Shetty", "Bhat", "Hegde", "Pillai", "Kapoor", "Gowda",
]


def _build_synthetic_engine(n_users: int, avg_degree: int = 10, posts_per_user: int = 3) -> dict:
    """Build an in-memory CUConnect engine of `n_users` directly (skipping PBKDF2 hashing)."""
    rng = random.Random(2026 + n_users)
    accounts = AccountManager()
    graph = SocialGraph()
    connections = ConnectionManager(graph)
    posts = PostManager()
    search = UserSearchIndex(accounts)

    usernames: list[str] = []
    for i in range(n_users):
        uname = f"stu_{i:05d}"
        full_name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        user = User(
            username=uname,
            password_hash="benchmark_placeholder_hash",
            full_name=full_name,
            programme="B.Tech CSAI",
            year=(i % 4) + 1,
            created_at=float(i),
        )
        accounts.load_user(user)
        graph.add_user(uname)
        connections.register_user(uname)
        posts.register_user(uname)
        search.index_user(user)
        usernames.append(uname)

    # First link a ring so the graph is connected, then add random edges to reach avg_degree.
    for i in range(n_users):
        u = usernames[i]
        v = usernames[(i + 1) % n_users]
        if u != v and not graph.has_edge(u, v):
            graph.add_edge(u, v)

    target_edges = (n_users * avg_degree) // 2
    attempts = 0
    while graph.edge_count() < target_edges and attempts < target_edges * 4:
        u = rng.choice(usernames)
        v = rng.choice(usernames)
        attempts += 1
        if u != v and not graph.has_edge(u, v):
            graph.add_edge(u, v)

    # Create posts_per_user posts across users in chronological order.
    seq = 0
    for round_idx in range(posts_per_user):
        for i, uname in enumerate(usernames):
            seq += 1
            ts = 1_700_000_000.0 + round_idx * 100_000.0 + rng.uniform(0, 50_000.0)
            posts.create_post(uname, f"Technical post #{round_idx + 1} by {uname}", ts, seq)

    return {
        "usernames": usernames,
        "graph": graph,
        "feed": FeedEngine(graph, posts),
        "suggestions": SuggestionEngine(graph, accounts, connections),
        "search": search,
    }


def _time_ms(fn, trials: int) -> float:
    start = time.perf_counter()
    for _ in range(trials):
        fn()
    elapsed = (time.perf_counter() - start) * 1000.0
    return round(elapsed / trials, 3)


def run_benchmarks(sizes: list[int], trials: int = 15) -> list[dict[str, object]]:
    """Run timing benchmarks across graph sizes and return structured measurements."""
    results: list[dict[str, object]] = []
    rng = random.Random(99)

    for n in sizes:
        print(f"Building synthetic graph with N={n} users...")
        t0 = time.perf_counter()
        env = _build_synthetic_engine(n)
        build_s = round(time.perf_counter() - t0, 3)
        usernames = env["usernames"]
        graph: SocialGraph = env["graph"]
        feed: FeedEngine = env["feed"]
        suggestions: SuggestionEngine = env["suggestions"]
        search: UserSearchIndex = env["search"]

        sample_pairs = [(rng.choice(usernames), rng.choice(usernames)) for _ in range(trials)]
        sample_users = [rng.choice(usernames) for _ in range(trials)]
        prefixes = ["aa", "di", "ro", "sha", "ver", "stu_00"]

        idx = {"bfs": 0, "sug": 0, "feed": 0, "trie": 0}

        def do_bfs() -> None:
            u, v = sample_pairs[idx["bfs"] % trials]
            idx["bfs"] += 1
            graph.degree_and_shortest_path(u, v)

        def do_suggestions() -> None:
            u = sample_users[idx["sug"] % trials]
            idx["sug"] += 1
            suggestions.recommend(u, k=5)

        def do_feed() -> None:
            u = sample_users[idx["feed"] % trials]
            idx["feed"] += 1
            feed.get_home_feed(u, limit=10, offset=0)

        def do_trie() -> None:
            p = prefixes[idx["trie"] % len(prefixes)]
            idx["trie"] += 1
            search.search(p, limit=10)

        row = {
            "users": n,
            "edges": graph.edge_count(),
            "build_sec": build_s,
            "bfs_ms": _time_ms(do_bfs, trials),
            "suggestions_ms": _time_ms(do_suggestions, trials),
            "feed_ms": _time_ms(do_feed, trials),
            "trie_ms": _time_ms(do_trie, trials),
        }
        results.append(row)
        print(
            f"  N={n:>5} (E={row['edges']:>5}) | BFS={row['bfs_ms']:>7.3f} ms | "
            f"Suggestions={row['suggestions_ms']:>7.3f} ms | Feed={row['feed_ms']:>6.3f} ms | "
            f"Trie={row['trie_ms']:>7.3f} ms"
        )

    return results


def save_chart(results: list[dict[str, object]], out_path: Path) -> None:
    """Save a clean multi-panel Matplotlib benchmark chart for the report and slides."""
    import matplotlib.pyplot as plt

    out_path.parent.mkdir(parents=True, exist_ok=True)
    xs = [int(r["users"]) for r in results]
    x_labels = [f"{x:,}" for x in xs]
    x_pos = list(range(len(xs)))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.4), dpi=180)
    fig.patch.set_facecolor("white")

    # Left panel: Line plot of all four core operations (log-y scale shows orders of magnitude clearly)
    ax1.plot(x_pos, [r["bfs_ms"] for r in results], marker="o", linewidth=2.4, color="#0F2A4A", label="BFS Degree & Chain O(V+E)")
    ax1.plot(x_pos, [r["trie_ms"] for r in results], marker="s", linewidth=2.4, color="#D4A017", label="Trie Prefix Search O(L+M)")
    ax1.plot(x_pos, [r["suggestions_ms"] for r in results], marker="^", linewidth=2.4, color="#0D9488", label="Suggestions (Depth-2 + Jaccard)")
    ax1.plot(x_pos, [r["feed_ms"] for r in results], marker="D", linewidth=2.4, color="#DC2626", label="Home Feed (k-way MinHeap)")

    ax1.set_yscale("log")
    all_vals = [
        float(r[k]) for r in results for k in ("bfs_ms", "trie_ms", "suggestions_ms", "feed_ms")
    ]
    ax1.set_ylim(min(all_vals) * 0.5, max(all_vals) * 6.0)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(x_labels, fontsize=10)
    ax1.set_xlabel("Number of Users (avg degree = 10)", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Mean Latency (ms, log scale)", fontsize=10, fontweight="bold")
    ax1.set_title("Scaling Across 100 → 5,000 Users", fontsize=11.5, fontweight="bold", color="#0F2A4A")
    ax1.grid(True, linestyle="--", alpha=0.35)
    ax1.legend(frameon=True, fontsize=8.5, loc="upper left")

    # Right panel: Grouped bar chart at N = 5,000 (or largest size)
    last = results[-1]
    ops = ["Feed\n(k-way Heap)", "Suggestions\n(Depth-2)", "BFS\n(Shortest Path)", "Trie\n(Prefix Search)"]
    vals = [float(last["feed_ms"]), float(last["suggestions_ms"]), float(last["bfs_ms"]), float(last["trie_ms"])]
    colors = ["#DC2626", "#0D9488", "#0F2A4A", "#D4A017"]

    bars = ax2.bar(ops, vals, color=colors, width=0.58, edgecolor="#1E293B", linewidth=0.6)
    for bar, val in zip(bars, vals):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(vals) * 0.025,
            f"{val:.2f} ms",
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold",
            color="#0F2A4A",
        )
    ax2.set_ylim(0, max(vals) * 1.18)
    ax2.set_ylabel("Mean Latency (ms)", fontsize=10, fontweight="bold")
    ax2.set_title(f"Operation Latency at N = {int(last['users']):,} Users", fontsize=11.5, fontweight="bold", color="#0F2A4A")
    ax2.grid(True, axis="y", linestyle="--", alpha=0.35)
    ax2.tick_params(axis="x", labelsize=9)

    fig.suptitle("CUConnect Core Engine Empirical Performance Benchmarks", fontsize=13, fontweight="bold", color="#0F2A4A", y=0.99)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    print(f"Saved benchmark chart to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark CUConnect core algorithms.")
    parser.add_argument("--sizes", nargs="+", type=int, default=[100, 1000, 5000])
    parser.add_argument("--trials", type=int, default=15)
    parser.add_argument("--chart", default="docs/diagrams/benchmark_chart.png")
    parser.add_argument("--json-out", default="docs/diagrams/benchmark_results.json")
    args = parser.parse_args()

    results = run_benchmarks(args.sizes, trials=args.trials)
    json_path = Path(args.json_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    save_chart(results, Path(args.chart))


if __name__ == "__main__":
    main()
