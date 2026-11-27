# scripts/seed_data.py
# Seeds CUConnect with 18 realistic Chanakya University students, 3 communities, posts, likes, comments & requests.
# Course mapping: Demonstrates all DSA structures on a reproducible campus dataset (including the 8-node report graph).

import argparse
from pathlib import Path
import sys
import time

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.service import CUConnectService

DEFAULT_PASSWORD = "chanakya2026"

# 18 realistic Chanakya University students across 3 communities:
# - First 8 form the core example graph reused in report and slide dry runs.
# - Students 1-10 form Community #1 (CSAI / AI & Systems Hub, size 10).
# - Students 11-15 form Community #2 (VLSI & Robotics Lab, size 5).
# - Students 16-18 form Community #3 (First-Year Builders Guild, size 3).
SEED_STUDENTS = [
    # --- Core 8-node example graph (part of Community 1) ---
    ("aarav", "Aarav Sharma", "B.Tech CSAI", 2,
     "Exploring graph algorithms, PyTorch internals, and full-stack Python tools.",
     ["Python", "DSA", "PyTorch", "SQLite"]),
    ("diya", "Diya Nair", "B.Tech CSAI", 2,
     "Building custom tokenizers and studying transformer efficiency.",
     ["Python", "NLP", "Algorithms", "Linux"]),
    ("rohan", "Rohan Verma", "B.Tech EECS", 3,
     "Autonomous rover perception and ROS2 motion planning at CU Robotics.",
     ["C++", "ROS2", "OpenCV", "Embedded"]),
    ("meera", "Meera Iyer", "B.Tech CSAI", 3,
     "Interested in distributed systems, information retrieval, and graph ML.",
     ["Python", "Rust", "Graph ML", "Docker"]),
    ("kabir", "Kabir Menon", "B.Tech EVE", 3,
     "RTL design, RISC-V pipelining, and FPGA synthesis experiments.",
     ["Verilog", "FPGA", "SystemVerilog", "C"]),
    ("ananya", "Ananya Rao", "B.Tech CSAI", 2,
     "Competitive programmer and visual explainers creator for core DSA topics.",
     ["Python", "C++", "DSA", "Streamlit"]),
    ("vikram", "Vikram Kulkarni", "B.Tech EECS", 4,
     "Final-year capstone on real-time edge inference on ARM microcontrollers.",
     ["Embedded C", "RTOS", "TinyML", "PCB"]),
    ("sneha", "Sneha Joshi", "B.Tech CSE", 3,
     "Database internals, indexing trees (AVL/B-Tree), and backend engineering.",
     ["Python", "SQL", "Go", "Distributed Systems"]),
    # --- Remaining 2 members of Community 1 (gives 3rd and 4th / '3+' hops from aarav) ---
    ("arjun", "Arjun Deshmukh", "B.Tech Data Science", 2,
     "Statistical modelling, campus energy analytics, and data visualization.",
     ["Python", "Pandas", "Matplotlib", "Statistics"]),
    ("isha", "Isha Reddy", "B.Tech CSAI", 1,
     "First-year CSAI student learning Python, recursion, and web dev.",
     ["Python", "HTML", "Git"]),
    # --- Community 2: VLSI & Robotics Lab (size 5) ---
    ("pranav", "Pranav Shetty", "B.Tech EVE", 3,
     "Analog & mixed-signal IC verification and open-source SkyWater PDK flows.",
     ["SPICE", "Verilog", "Cadence", "Python"]),
    ("tanvi", "Tanvi Bhat", "B.Tech EVE", 2,
     "Sensor fusion, IMU calibration, and low-power wearable hardware.",
     ["C", "STM32", "KiCad", "DSP"]),
    ("siddharth", "Siddharth Hegde", "B.Tech EECS", 4,
     "Smart grid telemetry and motor control firmware for campus EV prototype.",
     ["Power Electronics", "MATLAB", "Embedded C", "CAN Bus"]),
    ("nisha", "Nisha Pillai", "B.Tech EECS", 3,
     "Drone flight controllers and real-time Kalman filtering.",
     ["C++", "Control Systems", "PX4", "Python"]),
    ("karthik", "Karthik Subramanian", "B.Tech EVE", 2,
     "Digital logic synthesis and custom ALU designs on Artix-7 FPGA boards.",
     ["VHDL", "Verilog", "Digital Logic", "FPGA"]),
    # --- Community 3: First-Year Builders Guild (size 3) ---
    ("riya", "Riya Kapoor", "B.Tech CSE", 1,
     "Building my first campus timetable organizer and studying linked lists.",
     ["Python", "JavaScript", "Git"]),
    ("dev", "Dev Malhotra", "B.Tech CSAI", 1,
     "Excited about hackathons, Arduino bots, and foundational algorithms.",
     ["Python", "Arduino", "C"]),
    ("aditya", "Aditya Gowda", "B.Tech Data Science", 1,
     "Exploring Kaggle datasets and open-source Python visualization libraries.",
     ["Python", "NumPy", "Data Analysis"]),
]

SEED_EDGES = [
    # Community 1 (10 students): core 8-node example graph + arjun & isha
    ("aarav", "diya"),
    ("aarav", "rohan"),
    ("aarav", "ananya"),
    ("diya", "meera"),
    ("diya", "kabir"),
    ("rohan", "meera"),
    ("rohan", "sneha"),
    ("ananya", "meera"),
    ("meera", "vikram"),
    ("kabir", "vikram"),
    ("sneha", "vikram"),
    ("vikram", "arjun"),
    ("sneha", "arjun"),
    ("arjun", "isha"),
    # Community 2 (5 students): VLSI & Robotics Lab
    ("pranav", "tanvi"),
    ("pranav", "siddharth"),
    ("tanvi", "karthik"),
    ("siddharth", "nisha"),
    ("nisha", "karthik"),
    ("siddharth", "karthik"),
    # Community 3 (3 students): First-Year Builders Guild
    ("riya", "dev"),
    ("dev", "aditya"),
    ("riya", "aditya"),
]

# Pending directed requests (leaving meera/kabir/sneha free so PYMK shows exact Jaccard 0.75, 0.25, 0.20!)
SEED_PENDING_REQUESTS = [
    ("vikram", "aarav"),  # Incoming to aarav (same community, 3rd degree)
    ("pranav", "aarav"),  # Incoming to aarav (Community 2 -> accepting bridges Comm 1 & 2!)
    ("aarav", "isha"),    # Outgoing from aarav (4th / '3+' degree)
    ("riya", "diya"),     # Cross-community request to diya
]


class _ScriptedClock:
    """Controllable clock producing realistic recent timestamps relative to `now`."""

    def __init__(self, base_time: float) -> None:
        self.current = base_time

    def set(self, ts: float) -> None:
        self.current = ts

    def advance(self, seconds: float) -> None:
        self.current += seconds

    def __call__(self) -> float:
        self.current += 1.0
        return self.current


def seed_database(db_path: str = "cuconnect.db", reset: bool = True) -> dict[str, object]:
    """Populate `db_path` with deterministic Chanakya University demo data."""
    target = Path(db_path)
    if reset and target.exists():
        target.unlink()

    now = time.time()
    # Start timestamps 4 days ago so every post is inside the 7-day trending window.
    clock = _ScriptedClock(now - 4 * 86400)
    svc = CUConnectService(db_path=str(target), clock=clock)

    try:
        # 1. Sign up all 18 students
        for uname, full_name, prog, year, bio, skills in SEED_STUDENTS:
            svc.sign_up(uname, DEFAULT_PASSWORD, full_name, prog, year, bio=bio, skills=skills)
            clock.advance(120)

        # 2. Establish accepted undirected connections
        clock.set(now - 3 * 86400)
        for u, v in SEED_EDGES:
            svc.send_connection_request(u, v)
            svc.accept_connection_request(v, u)
            clock.advance(60)

        # Clear setup notifications so demo accounts start with clean, meaningful alerts.
        for uname, *_ in SEED_STUDENTS:
            svc.mark_all_notifications_read(uname)

        # 3. Create 14 technical project posts across the past 48 hours
        clock.set(now - 48 * 3600)
        posts: dict[str, str] = {}

        post_specs = [
            ("diya_1", "diya", 0,
             "Benchmarked our byte-pair tokenizer on 50k Kannada+English technical sentences. Next step: integrating trie-based prefix caching!",
             None),
            ("rohan_1", "rohan", 4 * 3600,
             "Completed indoor SLAM mapping with our ROS2 rover in the School of Engineering corridor. Looking for CSAI folks interested in obstacle classification.",
             None),
            ("ananya_1", "ananya", 8 * 3600,
             "Published clean step-by-step dry-run diagrams for AVL tree LL, RR, LR, and RL rotations ahead of DSA viva week!",
             None),
            ("meera_1", "meera", 12 * 3600,
             "Comparing Jaccard similarity vs Adamic-Adar on sparse campus collaboration graphs — surprisingly close top-5 precision.",
             None),
            ("kabir_1", "kabir", 16 * 3600,
             "Synthesized a 5-stage pipelined RISC-V RV32I core on Artix-7 at 85 MHz with forwarding hazard unit working cleanly!",
             None),
            ("vikram_1", "vikram", 20 * 3600,
             "Quantized a keyword-spotting CNN to INT8 for Cortex-M4: RAM footprint dropped from 310 KB to 68 KB.",
             None),
            ("sneha_1", "sneha", 24 * 3600,
             "Implemented separate-chaining hash tables from scratch with polynomial rolling hash (base 31). Zero collisions on 18 student usernames!",
             None),
            ("aarav_1", "aarav", 28 * 3600,
             "Kicked off CUConnect with Pranam and Nihal — pure Python standard-library DSA engine with both Console and Streamlit UIs!",
             None),
            ("pranav_1", "pranav", 30 * 3600,
             "Simulated a two-stage CMOS op-amp in ngspice with 64-degree phase margin. Happy to share the netlist with EVE juniors.",
             None),
            ("siddharth_1", "siddharth", 32 * 3600,
             "Campus EV battery management telemetry dashboard is now streaming CAN bus frames at 50 Hz.",
             None),
            ("riya_1", "riya", 34 * 3600,
             "First-Year Builders Guild meetup this Saturday at 3 PM — we are building a study-group finder in Python!",
             None),
            ("diya_2", "diya", 38 * 3600,
             "Update on tokenizer project: switched lookup table to a hand-written HashTable and cut vocabulary lookup time by 40%.",
             None),
            ("ananya_2", "ananya", 42 * 3600,
             "Delighted to share our certificate of participation in the Chanakya University Hackathon!",
             "ui/assets/post_hackathon_cert.png"),
            ("rohan_2", "rohan", 45 * 3600,
             "Weekend Robotics Lab open demo: test-driving our autonomous rover with LiDAR + depth camera fusion. Drop by Block B!",
             "ui/assets/post_rover_demo.png"),
        ]

        base_post_ts = now - 48 * 3600
        for key, author, delta_s, text, img_path in post_specs:
            clock.set(base_post_ts + delta_s)
            post = svc.create_post(author, text, image_path=img_path)
            posts[key] = post.post_id

        # 4. Add realistic likes and nested threaded comments (depth 0, 1, 2)
        clock.set(now - 5 * 3600)
        # Make rohan_2 the #1 trending post for aarav (3 likes + 2*3 comments = score 9)
        svc.like_post(posts["rohan_2"], "aarav")
        svc.like_post(posts["rohan_2"], "meera")
        svc.like_post(posts["rohan_2"], "sneha")
        c_r1 = svc.add_comment(posts["rohan_2"], "aarav", "Count me in! Would love to test our vision model on the rover.")
        c_r2 = svc.add_comment(posts["rohan_2"], "rohan", "Awesome — bring your ONNX weights, we have a Jetson Nano mounted!", parent_comment_id=c_r1.comment_id)
        svc.add_comment(posts["rohan_2"], "meera", "I can help optimize the inference loop too!", parent_comment_id=c_r2.comment_id)

        # Make ananya_2 #2 trending post for aarav (2 likes + 2*2 comments = score 6)
        svc.like_post(posts["ananya_2"], "aarav")
        svc.like_post(posts["ananya_2"], "meera")
        c_a1 = svc.add_comment(posts["ananya_2"], "meera", "Congrats Ananya! Amazing effort from your team at the Chanakya University Hackathon!")
        svc.add_comment(posts["ananya_2"], "ananya", "Thank you Meera! Building our k-way feed prototype in 24 hours was a blast.", parent_comment_id=c_a1.comment_id)

        # Make diya_2 #3 trending post for aarav (2 likes + 2*1 comments = score 4)
        svc.like_post(posts["diya_2"], "aarav")
        svc.like_post(posts["diya_2"], "kabir")
        svc.add_comment(posts["diya_2"], "kabir", "Curious what load factor threshold you picked — 0.75?")

        # Engagement on aarav's own post so aarav sees unread notifications too!
        svc.like_post(posts["aarav_1"], "diya")
        svc.like_post(posts["aarav_1"], "rohan")
        c_aa = svc.add_comment(posts["aarav_1"], "ananya", "Love the clean separation between core engine and UI!")
        svc.add_comment(posts["aarav_1"], "diya", "Agreed — the AVL student directory is a great touch.", parent_comment_id=c_aa.comment_id)

        # 5. Add pending directed requests (triggers unread notifications for receivers)
        clock.set(now - 2 * 3600)
        for sender, receiver in SEED_PENDING_REQUESTS:
            svc.send_connection_request(sender, receiver)
            clock.advance(300)

        return svc.get_engine_stats()
    finally:
        svc.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the CUConnect SQLite database.")
    parser.add_argument("--db", default="cuconnect.db", help="Target SQLite database file.")
    parser.add_argument("--no-reset", action="store_true", help="Do not delete existing DB file first.")
    args = parser.parse_args()

    stats = seed_database(db_path=args.db, reset=not args.no_reset)
    print(f"Seeded CUConnect database at '{args.db}' successfully!")
    for key, val in stats.items():
        print(f"  {key}: {val}")
    print(f"Demo login: username 'aarav' (or any of the 18 students), password '{DEFAULT_PASSWORD}'")


if __name__ == "__main__":
    main()
