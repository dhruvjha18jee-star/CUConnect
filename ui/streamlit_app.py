# ui/streamlit_app.py
# Streamlit web interface for CUConnect calling only CUConnectService (zero direct DS access).
# Course mapping: Presentation Layer decoupled from Core DSA Engine (Part 6: Interface).

import base64
from datetime import datetime
import html
import os
from pathlib import Path
import sys
import uuid

import streamlit as st

# Ensure project root is importable when invoked via `streamlit run ui/streamlit_app.py`.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.models import CUConnectError, Post, User
from core.service import CUConnectService

_ASSETS_DIR = _ROOT / "ui" / "assets"
_UPLOADS_DIR = _ROOT / "ui" / "uploads"
_LOGO_PATH = _ASSETS_DIR / "cuconnect_logo.png"

st.set_page_config(
    page_title="CUConnect — Chanakya University Network",
    page_icon=str(_LOGO_PATH) if _LOGO_PATH.exists() else "🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CUConnect Warm Academic Theme
# Palette: French Puce (#540B0E), Auburn (#9E2A2B), Hunyadi Yellow (#E09F3E),
#          Police Blue (#335C67), Vanilla (#FFF3B0)
st.markdown(
    """
    <style>
    :root {
        --cu-puce: #540B0E;
        --cu-auburn: #9E2A2B;
        --cu-gold: #E09F3E;
        --cu-slate: #335C67;
        --cu-vanilla: #FFF3B0;
        --cu-canvas: #FAF8F5;
        --cu-card-border: #E8E1D5;
    }

    /* Main canvas polish */
    [data-testid="stAppViewContainer"] {
        background-color: var(--cu-canvas);
    }
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    .block-container {
        padding-top: 3.6rem !important;
        padding-bottom: 3rem !important;
        max-width: 1380px;
    }

    /* =====================================================================
       LEFT SIDEBAR — Exact Vanilla Yellow (#FFF3B0) + Subtle Dark Scrollbar
       ===================================================================== */
    section[data-testid="stSidebar"] {
        background-color: #FFF3B0 !important;
        border-right: 1px solid #E6D276 !important;
        min-width: 285px !important;
        max-width: 315px !important;
    }
    section[data-testid="stSidebar"] > div:first-child,
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        background-color: #FFF3B0 !important;
        overflow-y: scroll !important;
        scrollbar-width: thin;
        scrollbar-color: rgba(84, 11, 14, 0.34) rgba(84, 11, 14, 0.05);
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar {
        width: 7px;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar-track {
        background: rgba(84, 11, 14, 0.05);
        border-radius: 999px;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {
        background: rgba(84, 11, 14, 0.32);
        border-radius: 999px;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb:hover {
        background: rgba(84, 11, 14, 0.55);
    }

    .cu-sidebar-logo {
        text-align: center;
        padding: 0.2rem 0.5rem 0.7rem 0.5rem;
    }
    .cu-sidebar-logo img {
        max-width: 170px;
        width: 100%;
        height: auto;
        display: inline-block;
    }
    .cu-sidebar-user {
        padding: 0.45rem 0.25rem 0.95rem 0.25rem;
        margin-bottom: 0.45rem;
        border-bottom: 1.5px solid rgba(84, 11, 14, 0.14);
    }
    .cu-sidebar-name {
        font-size: 1.48rem;
        font-weight: 800;
        color: #540B0E;
        line-height: 1.2;
        letter-spacing: -0.015em;
        margin-bottom: 0.4rem;
    }
    .cu-sidebar-meta {
        font-size: 0.95rem;
        color: #335C67;
        font-weight: 600;
        line-height: 1.45;
    }
    .cu-sidebar-handle {
        display: inline-block;
        background: rgba(51, 92, 103, 0.13);
        color: #1F4550;
        padding: 0.12rem 0.52rem;
        border-radius: 999px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 0.86rem;
        font-weight: 700;
        margin-right: 0.3rem;
    }

    /* Spacious Sidebar Navigation Items (Left-Aligned) */
    .st-key-cu_nav_list {
        gap: 0.26rem !important;
        padding-top: 0.2rem;
    }
    .st-key-cu_nav_list button {
        justify-content: flex-start !important;
        text-align: left !important;
        border-radius: 12px !important;
        padding: 0.58rem 0.95rem !important;
        min-height: 2.6rem !important;
        transition: all 0.16s ease !important;
    }
    .st-key-cu_nav_list button > div,
    .st-key-cu_nav_list button [data-testid="stMarkdownContainer"] {
        width: 100% !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }
    .st-key-cu_nav_list button p {
        font-size: 1rem !important;
        line-height: 1.3 !important;
        text-align: left !important;
    }
    /* Active Nav Item — Rounded Auburn (#9E2A2B) with White Text */
    .st-key-cu_nav_list button[kind="primary"],
    .st-key-cu_nav_list button[data-testid="stBaseButton-primary"] {
        background-color: #9E2A2B !important;
        border: 1px solid #821F20 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(84, 11, 14, 0.22) !important;
    }
    .st-key-cu_nav_list button[kind="primary"] p,
    .st-key-cu_nav_list button[data-testid="stBaseButton-primary"] p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    /* Inactive Nav Items */
    .st-key-cu_nav_list button[kind="secondary"],
    .st-key-cu_nav_list button[data-testid="stBaseButton-secondary"] {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        color: #540B0E !important;
        box-shadow: none !important;
    }
    .st-key-cu_nav_list button[kind="secondary"] p,
    .st-key-cu_nav_list button[data-testid="stBaseButton-secondary"] p {
        color: #540B0E !important;
        font-weight: 600 !important;
    }
    .st-key-cu_nav_list button[kind="secondary"]:hover,
    .st-key-cu_nav_list button[data-testid="stBaseButton-secondary"]:hover {
        background-color: rgba(158, 42, 43, 0.12) !important;
        border-color: rgba(158, 42, 43, 0.18) !important;
    }

    /* Sidebar Undo & Log Out Spacing */
    .cu-sidebar-footer-spacer {
        height: 1.2rem;
        margin-top: 0.9rem;
        border-top: 1.5px solid rgba(84, 11, 14, 0.14);
    }
    .st-key-cu_undo_box button {
        background-color: rgba(224, 159, 62, 0.28) !important;
        border: 1px solid #D4922F !important;
        color: #540B0E !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.6rem 0.9rem !important;
    }
    .st-key-cu_logout_box {
        margin-top: 0.45rem;
        padding-bottom: 1.4rem;
    }
    .st-key-cu_logout_box button {
        background-color: rgba(255, 255, 255, 0.85) !important;
        border: 1.5px solid #9E2A2B !important;
        color: #9E2A2B !important;
        border-radius: 12px !important;
        padding: 0.68rem 1rem !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 6px rgba(84, 11, 14, 0.08) !important;
        transition: all 0.16s ease !important;
    }
    .st-key-cu_logout_box button p {
        color: #9E2A2B !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }
    .st-key-cu_logout_box button:hover {
        background-color: #9E2A2B !important;
        color: #FFFFFF !important;
    }
    .st-key-cu_logout_box button:hover p {
        color: #FFFFFF !important;
    }

    /* =====================================================================
       BANNERS, HEADERS, CARDS, BADGES & RIGHT RAIL
       ===================================================================== */
    .cu-page-header {
        margin-bottom: 1.1rem;
    }
    .cu-page-title {
        font-size: 2.05rem;
        font-weight: 800;
        color: #540B0E;
        letter-spacing: -0.02em;
        margin: 0 0 0.25rem 0;
        line-height: 1.18;
    }
    .cu-page-sub {
        font-size: 0.95rem;
        color: #4B5563;
        margin: 0;
        line-height: 1.45;
    }

    .cu-banner {
        background: linear-gradient(125deg, #540B0E 0%, #7C1D20 55%, #335C67 100%);
        color: #FFFFFF;
        padding: 1.45rem 1.75rem;
        border-radius: 16px;
        border-left: 6px solid #E09F3E;
        margin-bottom: 1.35rem;
        box-shadow: 0 8px 24px rgba(84, 11, 14, 0.14);
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }
    .cu-banner-logo-wrap {
        background: #FFF3B0;
        padding: 0.55rem 0.75rem;
        border-radius: 12px;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
    }
    .cu-banner-logo-wrap img {
        height: 62px;
        width: auto;
        display: block;
    }
    .cu-banner h2 {
        margin: 0;
        color: #FFFFFF;
        font-size: 1.65rem;
        font-weight: 800;
    }
    .cu-banner p {
        margin: 0.3rem 0 0 0;
        color: #FDEFD1;
        font-size: 0.96rem;
    }

    /* Elevated rounded containers for feed cards, forms & right-rail panels */
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stForm"] {
        background: #FFFFFF !important;
        border: 1px solid #EAE2D6 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 16px rgba(84, 11, 14, 0.055) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.35rem 0.45rem !important;
        margin-bottom: 0.95rem !important;
    }

    /* Rounded post media */
    [data-testid="stImage"] img {
        border-radius: 12px !important;
        border: 1px solid #ECE6DC;
    }

    .cu-card {
        background: #FFFFFF;
        border: 1px solid #EAE2D6;
        border-radius: 14px;
        padding: 1.05rem 1.25rem;
        margin-bottom: 0.85rem;
        box-shadow: 0 3px 12px rgba(84, 11, 14, 0.05);
    }
    .cu-card-compact {
        background: #FAF8F5;
        border: 1px solid #E8DFD1;
        border-radius: 13px;
        padding: 0.9rem 1rem 0.75rem 1rem;
        margin-top: 0.6rem;
        margin-bottom: 0.55rem;
    }

    .cu-post-author {
        font-weight: 800;
        font-size: 1.08rem;
        color: #540B0E;
    }
    .cu-post-handle {
        display: inline-block;
        background: #F3EFE8;
        color: #335C67;
        padding: 0.08rem 0.48rem;
        border-radius: 999px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 0.83rem;
        font-weight: 700;
        margin: 0 0.25rem;
    }
    .cu-post-meta {
        color: #64748B;
        font-size: 0.88rem;
        font-weight: 500;
    }
    .cu-post-time {
        text-align: right;
        color: #6B7280;
        font-size: 0.84rem;
        font-weight: 500;
        padding-top: 0.15rem;
    }
    .cu-post-body {
        color: #1F2937;
        font-size: 1rem;
        line-height: 1.58;
        margin: 0.45rem 0 0.75rem 0;
    }

    .cu-pill {
        display: inline-block;
        background: #EAF2F4;
        color: #2A4D57;
        border: 1px solid #D3E4E8;
        padding: 0.16rem 0.62rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-right: 0.32rem;
        margin-top: 0.28rem;
    }
    .cu-badge-connected {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #E6F7EE;
        color: #166534;
        border: 1px solid #BBEAD0;
        padding: 0.36rem 0.85rem;
        border-radius: 999px;
        font-size: 0.84rem;
        font-weight: 700;
        width: 100%;
    }
    .cu-badge-pending {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
        padding: 0.36rem 0.85rem;
        border-radius: 999px;
        font-size: 0.84rem;
        font-weight: 700;
        width: 100%;
    }
    .cu-badge-self {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #F1F5F9;
        color: #475569;
        border: 1px solid #CBD5E1;
        padding: 0.36rem 0.85rem;
        border-radius: 999px;
        font-size: 0.84rem;
        font-weight: 700;
        width: 100%;
    }
    .cu-badge-gold {
        display: inline-block;
        background: #FFF3B0;
        color: #540B0E;
        border: 1px solid #E09F3E;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
    }
    .cu-chain {
        background: #FFFFFF;
        border: 1.5px dashed #335C67;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        font-size: 1.05rem;
        font-weight: 700;
        color: #540B0E;
        box-shadow: 0 2px 8px rgba(51, 92, 103, 0.08);
    }

    /* Right Sidebar: Live Campus Network Stats Card */
    .cu-rail-heading {
        font-size: 1.15rem;
        font-weight: 800;
        color: #540B0E;
        margin: 0 0 0.2rem 0;
        letter-spacing: -0.01em;
    }
    .cu-rail-sub {
        font-size: 0.82rem;
        color: #6B7280;
        margin: 0 0 0.7rem 0;
    }
    .cu-stat-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.7rem;
        margin-top: 0.4rem;
    }
    .cu-stat-tile {
        background: #FAF8F5;
        border: 1px solid #EBE3D5;
        border-top: 3px solid #335C67;
        border-radius: 12px;
        padding: 0.75rem 0.85rem;
    }
    .cu-stat-tile.gold-accent {
        border-top-color: #E09F3E;
    }
    .cu-stat-tile.auburn-accent {
        border-top-color: #9E2A2B;
    }
    .cu-stat-label {
        font-size: 0.8rem;
        font-weight: 700;
        color: #4B5563;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .cu-stat-value {
        font-size: 1.95rem;
        font-weight: 800;
        color: #1F2937;
        line-height: 1.15;
        margin-top: 0.15rem;
    }

    /* Prominent Auburn Primary Buttons (View Profile ↗, Publish, Connect, etc.) */
    button[kind="primary"],
    button[data-testid="stBaseButton-primary"] {
        background-color: #9E2A2B !important;
        border-color: #821F20 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
    }
    button[kind="primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover {
        background-color: #7D1D1E !important;
        border-color: #540B0E !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _db_path() -> str:
    return os.environ.get("CUCONNECT_DB", str(_ROOT / "cuconnect.db"))


@st.cache_resource
def get_service(db_path: str) -> CUConnectService:
    """Hold a single in-memory CUConnectService engine across Streamlit reruns."""
    return CUConnectService(db_path=db_path)


@st.cache_data
def _load_logo_b64() -> str | None:
    """Return base64-encoded PNG for the CU Connect node network logo."""
    if not _LOGO_PATH.exists():
        return None
    return base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")


def _fmt_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%d %b %Y, %I:%M %p")


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _set_flash(kind: str, message: str) -> None:
    """Store a one-time status banner so feedback remains visible right after st.rerun()."""
    st.session_state["cu_flash"] = (kind, message)


def _show_flash() -> None:
    """Display and clear any pending status banner."""
    flash = st.session_state.pop("cu_flash", None)
    if not flash:
        return
    kind, message = flash
    if kind == "success":
        st.success(message)
    elif kind == "warning":
        st.warning(message)
    elif kind == "error":
        st.error(message)
    else:
        st.info(message)


def _open_student_profile(target_username: str, return_to: str | None = None) -> None:
    """Redirect smoothly to a student's profile view."""
    if return_to is not None:
        st.session_state["profile_return_page"] = return_to
    elif "active_page" in st.session_state:
        st.session_state["profile_return_page"] = st.session_state["active_page"]
    st.session_state["viewing_student"] = target_username
    st.rerun()


def _resolve_post_image(image_path: str | None) -> Path | None:
    """Resolve a post's image_path relative to the project root if it exists on disk."""
    if not image_path:
        return None
    candidate = Path(image_path)
    if not candidate.is_absolute():
        candidate = _ROOT / candidate
    return candidate if candidate.exists() and candidate.is_file() else None


def _save_uploaded_image(uploaded_file) -> str:
    """Persist an uploaded post image under `ui/uploads/` and return its relative POSIX path."""
    _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        suffix = ".png"
    filename = f"post_{uuid.uuid4().hex[:12]}{suffix}"
    dest = _UPLOADS_DIR / filename
    dest.write_bytes(uploaded_file.getbuffer())
    return f"ui/uploads/{filename}"


def _render_page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="cu-page-header">
            <h1 class="cu-page-title">{_esc(title)}</h1>
            <p class="cu-page-sub">{_esc(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_skill_pills(skills: list[str]) -> str:
    if not skills:
        return "<span style='color:#64748B;font-size:0.82rem;'>No skills listed yet</span>"
    return "".join(f"<span class='cu-pill'>{_esc(s)}</span>" for s in skills)


def _render_user_card(user: User, extra_note: str = "") -> None:
    note_html = (
        f"<div style='margin-top:0.45rem;color:#334155;font-size:0.9rem;'>{extra_note}</div>"
        if extra_note
        else ""
    )
    st.markdown(
        f"""
        <div class="cu-card">
            <div style="font-weight:800;font-size:1.08rem;color:#540B0E;">
                {_esc(user.full_name)}
                <span class="cu-post-handle">@{_esc(user.username)}</span>
            </div>
            <div style="color:#335C67;font-size:0.9rem;font-weight:600;margin-top:0.18rem;">
                {_esc(user.programme)} &middot; Year {user.year}
            </div>
            <div style="color:#1F2937;font-size:0.93rem;margin-top:0.42rem;line-height:1.45;">
                {_esc(user.bio or "Chanakya University student.")}
            </div>
            <div style="margin-top:0.45rem;">{_render_skill_pills(user.skills)}</div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_post_media(post: Post) -> None:
    img_path = _resolve_post_image(post.image_path)
    if img_path is not None:
        st.image(str(img_path), width="stretch")


def _render_live_campus_network_card(svc: CUConnectService) -> None:
    """Right-sidebar Live Campus Network widget with crisp stat counters."""
    stats = svc.get_engine_stats()
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="cu-rail-heading">Live Campus Network</div>
            <div class="cu-rail-sub">Real-time in-memory graph &amp; DSA counters</div>
            <div class="cu-stat-grid">
                <div class="cu-stat-tile">
                    <div class="cu-stat-label">Students</div>
                    <div class="cu-stat-value">{stats["users"]}</div>
                </div>
                <div class="cu-stat-tile auburn-accent">
                    <div class="cu-stat-label">Connections</div>
                    <div class="cu-stat-value">{stats["connections"]}</div>
                </div>
                <div class="cu-stat-tile gold-accent">
                    <div class="cu-stat-label">Posts</div>
                    <div class="cu-stat-value">{stats["posts"]}</div>
                </div>
                <div class="cu-stat-tile">
                    <div class="cu-stat-label">Communities</div>
                    <div class="cu-stat-value">{stats["communities"]}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_quick_search_widget(svc: CUConnectService, current_user: str) -> None:
    """Top-right live Trie prefix search card with Connected badge and View Profile ↗ CTA."""
    with st.container(border=True):
        st.markdown(
            """
            <div class="cu-rail-heading">Quick Student Search</div>
            <div class="cu-rail-sub">O(L) live prefix lookup via hand-written Trie</div>
            """,
            unsafe_allow_html=True,
        )
        query = st.text_input(
            "Search Students (prefix search)...",
            placeholder="Search Students (prefix search)...",
            key="quick_search_query",
            label_visibility="collapsed",
        )

        if not query.strip():
            st.caption("Try typing `diy`, `sh`, or `ro` to jump straight to a student profile.")
            return

        results = svc.search_users(query, limit=5)
        if not results:
            st.warning(f"No students matched '{query}'.")
            return

        my_conns = set(svc.get_connection_usernames(current_user))
        my_out = {r.receiver for r in svc.get_outgoing_requests(current_user)}
        my_in = {r.sender for r in svc.get_incoming_requests(current_user)}

        for u in results:
            st.markdown(
                f"""
                <div class="cu-card-compact">
                    <div style="font-weight:800;font-size:1.02rem;color:#540B0E;">
                        {_esc(u.full_name)}
                        <span class="cu-post-handle">@{_esc(u.username)}</span>
                    </div>
                    <div style="color:#335C67;font-size:0.84rem;font-weight:600;margin-top:0.15rem;">
                        {_esc(u.programme)} &bull; Year {u.year}
                    </div>
                    <div style="margin-top:0.35rem;">{_render_skill_pills(u.skills)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            b_status, b_visit = st.columns([1, 1.15], gap="small")
            with b_status:
                if u.username == current_user:
                    st.markdown("<div class='cu-badge-self'>You</div>", unsafe_allow_html=True)
                elif u.username in my_conns:
                    st.markdown("<div class='cu-badge-connected'>✓ Connected</div>", unsafe_allow_html=True)
                elif u.username in my_out:
                    st.markdown("<div class='cu-badge-pending'>Request Sent</div>", unsafe_allow_html=True)
                elif u.username in my_in:
                    if st.button("Accept", key=f"qs_acc_{u.username}", width="stretch"):
                        svc.accept_connection_request(current_user, u.username)
                        _set_flash("success", f"Connected with @{u.username}!")
                        st.rerun()
                else:
                    if st.button("Connect", key=f"qs_req_{u.username}", width="stretch"):
                        try:
                            status = svc.send_connection_request(current_user, u.username)
                            _set_flash("success", f"Connection status with @{u.username}: {status}")
                            st.rerun()
                        except CUConnectError as exc:
                            st.error(str(exc))

            with b_visit:
                if st.button(
                    "View Profile ↗",
                    key=f"qs_view_{u.username}",
                    type="primary",
                    width="stretch",
                ):
                    _open_student_profile(u.username, return_to="Home Feed")


def _render_post_card(
    svc: CUConnectService,
    post: Post,
    current_user: str,
    key_prefix: str = "feed",
) -> None:
    """Render one feed/profile post card with optional inline image, likes, and nested comments."""
    author = svc.get_profile(post.author)
    like_cnt = svc.get_like_count(post.post_id)
    cmt_cnt = svc.get_comment_count(post.post_id)
    liked = svc.has_liked(post.post_id, current_user)

    with st.container(border=True):
        top_l, top_r = st.columns([4.2, 1.8])
        with top_l:
            st.markdown(
                f"""
                <div>
                    <span class="cu-post-author">{_esc(author.full_name)}</span>
                    <span class="cu-post-handle">@{_esc(author.username)}</span>
                    <span class="cu-post-meta">&middot; {_esc(author.programme)} (Year {author.year})</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with top_r:
            st.markdown(
                f"<div class='cu-post-time'>{_esc(_fmt_time(post.created_at))}</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<div class='cu-post-body'>{_esc(post.content)}</div>",
            unsafe_allow_html=True,
        )

        _render_post_media(post)

        act1, act2, act3 = st.columns([1.45, 1.85, 3.2])
        like_label = f"❤️ Liked ({like_cnt})" if liked else f"🤍 Like ({like_cnt})"
        if act1.button(like_label, key=f"like_{key_prefix}_{post.post_id}", width="stretch"):
            svc.toggle_like(post.post_id, current_user)
            st.rerun()
        act2.markdown(
            f"<div style='padding-top:0.45rem;color:#335C67;font-weight:700;font-size:0.93rem;'>"
            f"💬 {cmt_cnt} comment(s)</div>",
            unsafe_allow_html=True,
        )
        if author.username != current_user:
            with act3:
                _, btn_col = st.columns([2.2, 1.6])
                if btn_col.button(
                    "View Profile ↗",
                    key=f"author_prof_{key_prefix}_{post.post_id}",
                    width="stretch",
                ):
                    _open_student_profile(author.username)

        with st.expander(f"Comments & Replies ({cmt_cnt})", expanded=False):
            comments = svc.get_post_comments(post.post_id)
            if not comments:
                st.caption("No comments yet. Start the discussion!")
            for comment, depth in comments:
                pad = min(depth, 5) * 24
                border_col = "#E09F3E" if depth > 0 else "#335C67"
                st.markdown(
                    f"<div style='margin-left:{pad}px;padding:0.45rem 0.75rem;"
                    f"border-left:3.5px solid {border_col};"
                    f"background:#FAF8F5;border-radius:8px;margin-bottom:0.45rem;'>"
                    f"<strong style='color:#540B0E;'>@{_esc(comment.author)}</strong> "
                    f"<span style='color:#64748B;font-size:0.8rem;'>{_esc(_fmt_time(comment.created_at))}</span><br/>"
                    f"<span style='color:#1F2937;'>{_esc(comment.content)}</span></div>",
                    unsafe_allow_html=True,
                )

            with st.form(f"cmt_form_{key_prefix}_{post.post_id}", clear_on_submit=True):
                parent_options = {"(Top-level comment)": None}
                for comment, _ in comments:
                    snippet = comment.content[:35] + ("..." if len(comment.content) > 35 else "")
                    parent_options[f"Reply to @{comment.author}: {snippet}"] = comment.comment_id
                reply_choice = st.selectbox(
                    "Comment mode",
                    list(parent_options.keys()),
                    key=f"reply_sel_{key_prefix}_{post.post_id}",
                )
                cmt_text = st.text_input(
                    "Write a comment or reply",
                    key=f"cmt_in_{key_prefix}_{post.post_id}",
                )
                if st.form_submit_button("Post Comment", type="primary"):
                    try:
                        svc.add_comment(
                            post.post_id,
                            current_user,
                            cmt_text,
                            parent_comment_id=parent_options[reply_choice],
                        )
                        st.rerun()
                    except CUConnectError as exc:
                        st.error(str(exc))


def _render_auth_page(svc: CUConnectService) -> None:
    logo_b64 = _load_logo_b64()
    logo_html = (
        f"<div class='cu-banner-logo-wrap'><img src='data:image/png;base64,{logo_b64}' alt='CU Connect Logo'/></div>"
        if logo_b64
        else ""
    )
    st.markdown(
        f"""
        <div class="cu-banner">
            {logo_html}
            <div>
                <h2>CUConnect — Chanakya University Student Network</h2>
                <p>Share projects, exchange technical ideas, and connect across School of Engineering — powered by hand-written Python Data Structures &amp; Algorithms.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_main, col_side = st.columns([1.95, 1.05], gap="large")

    with col_main:
        tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

        with tab_login:
            with st.form("login_form"):
                uname = st.text_input("Username", placeholder="e.g. aarav")
                pw = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Log In", type="primary", width="stretch")
                if submitted:
                    try:
                        user = svc.login(uname, pw)
                        st.session_state["current_user"] = user.username
                        st.session_state["active_page"] = "Home Feed"
                        st.session_state.pop("viewing_student", None)
                        st.session_state["feed_limit"] = 5
                        st.rerun()
                    except CUConnectError as exc:
                        st.error(str(exc))

        with tab_signup:
            with st.form("signup_form"):
                c1, c2 = st.columns(2)
                su_user = c1.text_input("Username *", placeholder="e.g. priya_csai")
                su_pw = c2.text_input("Password (min 6 chars) *", type="password")
                su_name = c1.text_input("Full Name *", placeholder="e.g. Priya Kulkarni")
                su_prog = c2.selectbox(
                    "Programme *",
                    ["B.Tech CSAI", "B.Tech EVE", "B.Tech EECS", "B.Tech CSE", "B.Tech Data Science"],
                )
                su_year = c1.selectbox("Year *", [1, 2, 3, 4], index=1)
                su_skills = c2.text_input("Skills (comma-separated)", placeholder="Python, DSA, PyTorch")
                su_bio = st.text_area("Short Bio", placeholder="What projects or technical topics excite you?")
                created = st.form_submit_button("Create Account", type="primary", width="stretch")
                if created:
                    try:
                        skills_list = [s.strip() for s in su_skills.split(",") if s.strip()]
                        user = svc.sign_up(
                            username=su_user,
                            password=su_pw,
                            full_name=su_name,
                            programme=su_prog,
                            year=int(su_year),
                            bio=su_bio,
                            skills=skills_list,
                        )
                        svc.login(user.username, su_pw)
                        st.session_state["current_user"] = user.username
                        st.session_state["active_page"] = "Home Feed"
                        st.session_state.pop("viewing_student", None)
                        st.session_state["feed_limit"] = 5
                        st.success(f"Welcome to CUConnect, {user.full_name}!")
                        st.rerun()
                    except CUConnectError as exc:
                        st.error(str(exc))

    with col_side:
        _render_live_campus_network_card(svc)

        with st.expander("Demo Login Credentials (Seed Data)", expanded=True):
            st.markdown(
                """
                If you ran `scripts/seed_data.py`, try any account with password **`chanakya2026`**:
                - `aarav` — Aarav Sharma (CSAI, Year 2)
                - `diya` — Diya Nair (CSAI, Year 2)
                - `rohan` — Rohan Verma (EECS, Year 3)
                - `kabir` — Kabir Menon (EVE, Year 3)
                """
            )


def _render_student_profile_detail(
    svc: CUConnectService,
    current_user: str,
    target_username: str,
) -> None:
    """Dedicated student profile view reached by clicking any 'View Profile ↗' button."""
    return_page = st.session_state.get("profile_return_page", "Home Feed")
    if st.button(f"← Back to {return_page}", key="back_from_student_profile"):
        st.session_state.pop("viewing_student", None)
        st.rerun()

    try:
        other = svc.get_profile(target_username)
    except CUConnectError as exc:
        st.error(str(exc))
        st.session_state.pop("viewing_student", None)
        return

    _render_page_header(
        f"{other.full_name}",
        f"Student Profile • @{other.username} • {other.programme} (Year {other.year})",
    )

    col_left, col_right = st.columns([2.25, 1.05], gap="large")

    with col_left:
        my_conns = set(svc.get_connection_usernames(current_user))
        my_out = {r.receiver for r in svc.get_outgoing_requests(current_user)}
        my_in = {r.sender for r in svc.get_incoming_requests(current_user)}

        deg = svc.get_degree_and_chain(current_user, target_username)
        mutuals = svc.get_mutual_connections(current_user, target_username)

        _render_user_card(
            other,
            extra_note=(
                f"<span class='cu-badge-gold'>Degree: {_esc(deg.label)}</span> &nbsp; "
                f"<strong>{len(mutuals)}</strong> mutual connection(s) &middot; "
                f"<strong>{len(svc.get_connections(target_username))}</strong> total connection(s)"
            ),
        )

        # Connection action bar
        if target_username != current_user:
            a1, a2, _ = st.columns([1.4, 1.6, 3])
            with a1:
                if target_username in my_conns:
                    st.markdown("<div class='cu-badge-connected'>✓ Connected</div>", unsafe_allow_html=True)
                elif target_username in my_out:
                    st.markdown("<div class='cu-badge-pending'>Request Sent</div>", unsafe_allow_html=True)
                elif target_username in my_in:
                    if st.button("Accept Request", key=f"prof_acc_{target_username}", type="primary", width="stretch"):
                        svc.accept_connection_request(current_user, target_username)
                        _set_flash("success", f"Connected with @{target_username}!")
                        st.rerun()
                else:
                    if st.button("Connect", key=f"prof_req_{target_username}", type="primary", width="stretch"):
                        try:
                            status = svc.send_connection_request(current_user, target_username)
                            _set_flash("success", f"Request status with @{target_username}: {status}")
                            st.rerun()
                        except CUConnectError as exc:
                            st.error(str(exc))
            with a2:
                if target_username in my_conns:
                    if st.button("Remove Connection", key=f"prof_rm_{target_username}", width="stretch"):
                        svc.remove_connection(current_user, target_username)
                        _set_flash("warning", f"Removed connection with @{target_username}.")
                        st.rerun()
                elif target_username in my_out:
                    if st.button("Cancel Request", key=f"prof_can_{target_username}", width="stretch"):
                        svc.cancel_connection_request(current_user, target_username)
                        _set_flash("info", f"Cancelled request to @{target_username}.")
                        st.rerun()

        if deg.path and target_username != current_user:
            st.markdown("#### Shortest Connection Chain (BFS)")
            names = [f"{_esc(svc.get_profile(u).full_name)} (@{_esc(u)})" for u in deg.path]
            st.markdown(f"<div class='cu-chain'>{' &nbsp;→&nbsp; '.join(names)}</div>", unsafe_allow_html=True)

        if mutuals and target_username != current_user:
            st.markdown(f"#### Mutual Connections ({len(mutuals)})")
            m_pills = " ".join(
                f"<span class='cu-pill'>{_esc(m.full_name)} (@{_esc(m.username)})</span>"
                for m in mutuals
            )
            st.markdown(f"<div style='margin-bottom:0.8rem;'>{m_pills}</div>", unsafe_allow_html=True)

        other_posts = svc.get_user_posts(target_username)
        st.markdown(f"### Posts by {other.full_name} ({len(other_posts)})")
        if not other_posts:
            st.info(f"{other.full_name} hasn't published any posts yet.")
        for p in other_posts:
            _render_post_card(svc, p, current_user, key_prefix="stuprof")

    with col_right:
        _render_quick_search_widget(svc, current_user)
        _render_live_campus_network_card(svc)


def _render_feed_page(svc: CUConnectService, current_user: str) -> None:
    col_feed, col_right = st.columns([2.25, 1.05], gap="large")

    with col_feed:
        _render_page_header(
            "Home Feed",
            "Powered by k-way merge of your connections' SinglyLinkedList post streams using our hand-written MinHeap.",
        )

        if "feed_limit" not in st.session_state:
            st.session_state["feed_limit"] = 5

        limit = st.session_state["feed_limit"]
        posts, has_more = svc.get_home_feed(current_user, limit=limit, offset=0)

        if not posts:
            st.info("Your feed is quiet right now. Connect with fellow students or check People You May Know!")
        else:
            for post in posts:
                _render_post_card(svc, post, current_user, key_prefix="feed")

            if has_more:
                if st.button("Load More Posts", type="primary", width="stretch"):
                    st.session_state["feed_limit"] = limit + 5
                    st.rerun()
            else:
                st.caption("You have reached the end of your connections' posts.")

    with col_right:
        _render_quick_search_widget(svc, current_user)
        _render_live_campus_network_card(svc)


def _render_post_composer_page(svc: CUConnectService, current_user: str) -> None:
    _render_page_header(
        "Post Composer & My Posts",
        "Each student's posts are stored in a hand-written SinglyLinkedList with O(1) newest-at-head insertion — now supporting image attachments!",
    )

    with st.form("new_post_form", clear_on_submit=True):
        content = st.text_area(
            "Share a project update, hackathon certificate, rover demo, or technical note",
            height=110,
            placeholder="e.g. Delighted to share our prototype from the Chanakya University Hackathon!",
        )
        uploaded_img = st.file_uploader(
            "Attach an image (optional — PNG, JPG, WEBP)",
            type=["png", "jpg", "jpeg", "webp"],
        )
        if uploaded_img is not None:
            st.image(uploaded_img, caption="Image preview", width="stretch")

        if st.form_submit_button("Publish Post", type="primary"):
            try:
                img_rel_path: str | None = None
                if uploaded_img is not None:
                    img_rel_path = _save_uploaded_image(uploaded_img)
                svc.create_post(current_user, content, image_path=img_rel_path)
                _set_flash("success", "Post published!")
                st.rerun()
            except CUConnectError as exc:
                st.error(str(exc))

    st.subheader("Your Posts (Newest First)")
    my_posts = svc.get_user_posts(current_user)
    if not my_posts:
        st.info("You haven't published any posts yet.")
        return

    for post in my_posts:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.caption(f"{_fmt_time(post.created_at)}  •  ID: `{post.post_id}`")
            if c2.button("Delete", key=f"del_{post.post_id}", type="secondary", width="stretch"):
                svc.delete_post(current_user, post.post_id)
                _set_flash("info", "Post deleted.")
                st.rerun()
            st.markdown(f"<div class='cu-post-body'>{_esc(post.content)}</div>", unsafe_allow_html=True)
            _render_post_media(post)
            st.caption(
                f"❤️ {svc.get_like_count(post.post_id)} likes  •  💬 {svc.get_comment_count(post.post_id)} comments"
            )


def _render_profile_page(svc: CUConnectService, current_user: str) -> None:
    _render_page_header(
        "My Profile & Student Profiles",
        "Keep your profile synchronized across our hand-written HashTable, Trie search index, and self-balancing AVL directory.",
    )
    me = svc.get_profile(current_user)

    tab_me, tab_other = st.tabs(["My Profile & Edit", "View Any Student Profile"])

    with tab_me:
        _render_user_card(
            me,
            extra_note=f"Connections: <strong>{len(svc.get_connections(current_user))}</strong> | Posts: <strong>{len(svc.get_user_posts(current_user))}</strong>",
        )
        with st.form("edit_profile_form"):
            st.subheader("Edit Profile")
            c1, c2 = st.columns(2)
            new_name = c1.text_input("Full Name", value=me.full_name)
            new_prog = c2.text_input("Programme", value=me.programme)
            new_year = c1.number_input("Year", min_value=1, max_value=5, value=me.year, step=1)
            new_skills = c2.text_input("Skills (comma-separated)", value=", ".join(me.skills))
            new_bio = st.text_area("Bio", value=me.bio)
            if st.form_submit_button("Save Changes", type="primary"):
                try:
                    svc.update_profile(
                        current_user,
                        full_name=new_name,
                        programme=new_prog,
                        year=int(new_year),
                        bio=new_bio,
                        skills=[s.strip() for s in new_skills.split(",") if s.strip()],
                    )
                    _set_flash("success", "Profile updated (Trie and AVL Directory synchronized)!")
                    st.rerun()
                except CUConnectError as exc:
                    st.error(str(exc))

    with tab_other:
        all_students = svc.browse_all_students()
        choices = [u.username for u in all_students if u.username != current_user]
        if not choices:
            st.info("No other students registered yet.")
            return
        selected = st.selectbox("Select a student to inspect", choices)
        other = svc.get_profile(selected)
        deg = svc.get_degree_and_chain(current_user, selected)
        mutuals = svc.get_mutual_connections(current_user, selected)
        _render_user_card(
            other,
            extra_note=f"Degree of connection: <strong>{_esc(deg.label)}</strong> | Mutual connections: <strong>{len(mutuals)}</strong>",
        )
        other_posts = svc.get_user_posts(selected)
        st.subheader(f"Posts by {other.full_name} ({len(other_posts)})")
        for p in other_posts:
            _render_post_card(svc, p, current_user, key_prefix="otherprof")


def _render_search_page(svc: CUConnectService, current_user: str) -> None:
    _render_page_header(
        "Search Students",
        "Instant prefix search over usernames and full-name words using our hand-written Trie.",
    )

    query = st.text_input(
        "Type any prefix of a name or username",
        placeholder="e.g. aa, diy, shar, ver...",
    )
    if not query.strip():
        st.info("Start typing a prefix above to see live Trie suggestions.")
        return

    results = svc.search_users(query, limit=20)
    if not results:
        st.warning(f"No students matched prefix '{query}'.")
        return

    st.success(f"Found {len(results)} matching student(s):")
    my_conns = set(svc.get_connection_usernames(current_user))
    my_out = {r.receiver for r in svc.get_outgoing_requests(current_user)}
    my_in = {r.sender for r in svc.get_incoming_requests(current_user)}

    for u in results:
        c1, c2, c3 = st.columns([3.8, 1.15, 1.25], vertical_alignment="center")
        with c1:
            _render_user_card(u)
        with c2:
            if u.username == current_user:
                st.markdown("<div class='cu-badge-self'>This is you</div>", unsafe_allow_html=True)
            elif u.username in my_conns:
                st.markdown("<div class='cu-badge-connected'>✓ Connected</div>", unsafe_allow_html=True)
            elif u.username in my_out:
                st.markdown("<div class='cu-badge-pending'>Request Sent</div>", unsafe_allow_html=True)
            elif u.username in my_in:
                if st.button("Accept", key=f"s_acc_{u.username}", width="stretch"):
                    svc.accept_connection_request(current_user, u.username)
                    _set_flash("success", f"Connected with @{u.username}!")
                    st.rerun()
            else:
                if st.button("Connect", key=f"s_req_{u.username}", width="stretch"):
                    try:
                        status = svc.send_connection_request(current_user, u.username)
                        st.toast(f"Status with @{u.username}: {status}")
                        st.rerun()
                    except CUConnectError as exc:
                        st.error(str(exc))
        with c3:
            if st.button(
                "View Profile ↗",
                key=f"s_view_{u.username}",
                type="primary",
                width="stretch",
            ):
                _open_student_profile(u.username, return_to="Search Users")


def _render_connections_page(svc: CUConnectService, current_user: str) -> None:
    _render_page_header(
        "Connections & Request Queues",
        "Accepted connections live in undirected adjacency lists (HashTable); pending requests use per-user FIFO Queues.",
    )

    if svc.can_undo(current_user):
        if st.button("↩️ Undo Last Send-Request / Remove-Connection (Stack)", type="secondary"):
            try:
                msg = svc.undo_last_action(current_user)
                _set_flash("success", msg)
                st.rerun()
            except CUConnectError as exc:
                st.error(str(exc))

    tab_conn, tab_inc, tab_out, tab_mut = st.tabs([
        "My Connections",
        "Incoming Requests",
        "Outgoing Requests",
        "Mutual Connections",
    ])

    with tab_conn:
        conns = svc.get_connections(current_user)
        if not conns:
            st.info("You have no connections yet.")
        for u in conns:
            c1, c2, c3 = st.columns([3.8, 1.25, 1.05], vertical_alignment="center")
            with c1:
                _render_user_card(u)
            with c2:
                if st.button("View Profile ↗", key=f"conn_view_{u.username}", type="primary", width="stretch"):
                    _open_student_profile(u.username, return_to="Connections & Requests")
            with c3:
                if st.button("Remove", key=f"rm_{u.username}", width="stretch"):
                    svc.remove_connection(current_user, u.username)
                    _set_flash("warning", f"Removed connection with @{u.username}. Click Undo to restore!")
                    st.rerun()

    with tab_inc:
        incoming = svc.get_incoming_requests(current_user)
        if not incoming:
            st.info("No pending incoming requests.")
        for req in incoming:
            sender = svc.get_profile(req.sender)
            c1, c2, c3 = st.columns([3.5, 1.05, 1.05], vertical_alignment="center")
            with c1:
                _render_user_card(sender, extra_note=f"Requested on {_esc(_fmt_time(req.created_at))}")
            with c2:
                if st.button("Accept", key=f"acc_{req.sender}", type="primary", width="stretch"):
                    svc.accept_connection_request(current_user, req.sender)
                    _set_flash("success", f"Connected with @{req.sender}!")
                    st.rerun()
            with c3:
                if st.button("Reject", key=f"rej_{req.sender}", width="stretch"):
                    svc.reject_connection_request(current_user, req.sender)
                    _set_flash("info", f"Rejected request from @{req.sender}.")
                    st.rerun()

    with tab_out:
        all_users = [u.username for u in svc.browse_all_students() if u.username != current_user]
        if all_users:
            with st.form("send_req_form"):
                target = st.selectbox("Send a new connection request to:", all_users)
                if st.form_submit_button("Send Request", type="primary"):
                    try:
                        status = svc.send_connection_request(current_user, target)
                        if status == "auto_accepted":
                            _set_flash("success", f"Mutual request auto-accepted! You are now connected with @{target}.")
                        else:
                            _set_flash("success", f"Request sent to @{target}.")
                        st.rerun()
                    except CUConnectError as exc:
                        st.error(str(exc))
        else:
            st.info("No other students registered yet.")

        outgoing = svc.get_outgoing_requests(current_user)
        if not outgoing:
            st.info("No pending outgoing requests.")
        for req in outgoing:
            receiver = svc.get_profile(req.receiver)
            c1, c2 = st.columns([4, 1.2], vertical_alignment="center")
            with c1:
                _render_user_card(receiver, extra_note=f"Sent on {_esc(_fmt_time(req.created_at))}")
            with c2:
                if st.button("Cancel", key=f"can_{req.receiver}", width="stretch"):
                    svc.cancel_connection_request(current_user, req.receiver)
                    _set_flash("info", f"Cancelled request to @{req.receiver}.")
                    st.rerun()

    with tab_mut:
        others = [u.username for u in svc.browse_all_students() if u.username != current_user]
        if others:
            other = st.selectbox("Select another student to compare mutual connections:", others)
            mutuals = svc.get_mutual_connections(current_user, other)
            st.metric("Mutual Connections", len(mutuals))
            for u in mutuals:
                _render_user_card(u)


def _render_suggestions_page(svc: CUConnectService, current_user: str) -> None:
    _render_page_header(
        "People You May Know",
        "Depth-2 BFS + Jaccard coefficient |N(u) ∩ N(v)| / |N(u) ∪ N(v)| ranked with our hand-written MinHeap.",
    )

    recs = svc.get_people_you_may_know(current_user, k=10)
    if not recs:
        st.info("No 2nd-degree suggestions available right now.")
        return

    for rec in recs:
        u = svc.get_profile(rec.username)
        mutual_str = ", ".join(f"@{_esc(m)}" for m in rec.mutual_usernames)
        c1, c2, c3 = st.columns([3.7, 1.15, 1.25], vertical_alignment="center")
        with c1:
            _render_user_card(
                u,
                extra_note=(
                    f"<span class='cu-badge-gold'>Jaccard: {rec.jaccard_score:.4f}</span> "
                    f"&nbsp; <strong>{rec.mutual_count} mutual connection(s):</strong> {mutual_str}"
                ),
            )
        with c2:
            if st.button("Connect", key=f"pymk_{rec.username}", type="primary", width="stretch"):
                try:
                    svc.send_connection_request(current_user, rec.username)
                    _set_flash("success", f"Request sent to @{rec.username}!")
                    st.rerun()
                except CUConnectError as exc:
                    st.error(str(exc))
        with c3:
            if st.button("View Profile ↗", key=f"pymk_view_{rec.username}", width="stretch"):
                _open_student_profile(rec.username, return_to="People You May Know")


def _render_degree_page(svc: CUConnectService, current_user: str) -> None:
    _render_page_header(
        "Degree of Connection & Shortest Chain",
        "Unweighted Breadth-First Search (BFS) with our linked-list Queue and parent map.",
    )

    others = [u.username for u in svc.browse_all_students() if u.username != current_user]
    if not others:
        st.info("No other students to inspect yet.")
        return

    target = st.selectbox("Choose any student on campus:", others)
    result = svc.get_degree_and_chain(current_user, target)

    c1, c2 = st.columns(2)
    c1.metric("Degree of Connection", result.label)
    c2.metric("Shortest Hop Count", result.distance if result.distance is not None else "∞ (Unreachable)")

    if result.path:
        names = [f"{_esc(svc.get_profile(u).full_name)} (@{_esc(u)})" for u in result.path]
        chain_html = " &nbsp;→&nbsp; ".join(names)
        st.markdown(f"<div class='cu-chain'>{chain_html}</div>", unsafe_allow_html=True)
    else:
        st.warning(f"There is currently no connection chain between @{current_user} and @{target}.")


def _render_notifications_page(svc: CUConnectService, current_user: str) -> None:
    _render_page_header(
        "Notifications",
        "Per-user Notification Queue tracking connection requests, acceptances, likes, and comments.",
    )

    unread = svc.get_unread_notification_count(current_user)
    c1, c2 = st.columns([2, 1])
    c1.metric("Unread Notifications", unread)
    if unread > 0 and c2.button("Mark All as Read", type="primary"):
        svc.mark_all_notifications_read(current_user)
        st.rerun()

    only_unread = st.checkbox("Show unread only", value=False)
    notifs = svc.get_notifications(current_user, unread_only=only_unread)
    if not notifs:
        st.info("All caught up! No notifications to display.")
        return

    for n in notifs:
        with st.container(border=True):
            col_t, col_b = st.columns([4.5, 1.2], vertical_alignment="center")
            badge = "🔴 **NEW** — " if not n.is_read else "✅ "
            col_t.markdown(f"{badge}{n.message}")
            col_t.caption(f"{n.kind.replace('_', ' ').title()}  •  {_fmt_time(n.created_at)}")
            if not n.is_read:
                if col_b.button("Mark read", key=f"nr_{n.notification_id}", width="stretch"):
                    svc.mark_notification_read(current_user, n.notification_id)
                    st.rerun()


def _render_trending_page(svc: CUConnectService, current_user: str) -> None:
    _render_page_header(
        "Trending Posts Among Your Connections",
        "Recent posts (last 7 days) scored by likes + 2 × comments and ranked top-k via MinHeap.",
    )

    trending = svc.get_trending_posts(current_user, k=8)
    if not trending:
        st.info("No recent connection posts found in the past 7 days.")
        return

    for rank, item in enumerate(trending, start=1):
        author = svc.get_profile(item.post.author)
        with st.container(border=True):
            st.markdown(
                f"<span class='cu-badge-gold'>#{rank} Trending &middot; Score {item.score}</span> "
                f"&nbsp; <strong style='color:#540B0E;'>{_esc(author.full_name)}</strong> "
                f"<span class='cu-post-handle'>@{_esc(author.username)}</span> "
                f"&middot; <span style='color:#64748B;'>{_esc(_fmt_time(item.post.created_at))}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(f"<div class='cu-post-body'>{_esc(item.post.content)}</div>", unsafe_allow_html=True)
            _render_post_media(item.post)
            st.caption(
                f"Formula: {item.like_count} like(s) + 2 × {item.comment_count} comment(s) = {item.score}"
            )


def _render_communities_page(svc: CUConnectService, current_user: str) -> None:
    _render_page_header(
        "Student Communities",
        "Connected components computed via iterative Depth-First Search (DFS) using our hand-written Stack.",
    )

    mine = svc.get_user_community(current_user)
    st.success(f"You belong to **Community #{mine.community_id}** with **{mine.size}** connected student(s).")

    communities = svc.get_all_communities()
    for comm in communities:
        title = f"Community #{comm.community_id} — {comm.size} student(s)"
        if comm.community_id == mine.community_id:
            title += "  ⭐ (Your Community)"
        with st.expander(title, expanded=(comm.community_id == mine.community_id)):
            cols = st.columns(2)
            for idx, uname in enumerate(comm.members):
                u = svc.get_profile(uname)
                with cols[idx % 2]:
                    _render_user_card(u)


def _render_directory_page(svc: CUConnectService) -> None:
    _render_page_header(
        "Browse All Students (Alphabetical Directory)",
        "Maintained in sorted order by our hand-written Self-Balancing AVL Tree (LL, RR, LR, RL rotations).",
    )

    stats = svc.get_engine_stats()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Students", stats["users"])
    m2.metric("AVL Tree Height", stats["avl_height"])
    m3.metric("AVL Balanced", "Yes" if stats["avl_balanced"] else "No")
    m4.metric("HashTable Load Factor", stats["hash_table_load_factor"])

    students = svc.browse_all_students()
    cols = st.columns(2)
    for idx, u in enumerate(students):
        with cols[idx % 2]:
            _render_user_card(u)
            if st.button(
                f"View {u.full_name}'s Profile ↗",
                key=f"dir_view_{u.username}",
                width="stretch",
            ):
                _open_student_profile(u.username, return_to="Browse All Students (AVL)")


def main() -> None:
    svc = get_service(_db_path())

    current_user: str | None = st.session_state.get("current_user")
    if current_user is None:
        _render_auth_page(svc)
        return

    # Verify session user still exists in the active DB.
    try:
        me = svc.get_profile(current_user)
    except CUConnectError:
        st.session_state.pop("current_user", None)
        st.rerun()
        return

    unread = svc.get_unread_notification_count(current_user)
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "Home Feed"

    nav_items = [
        ("Home Feed", "Home Feed"),
        ("Post Composer", "Post Composer"),
        ("My Profile & Edit", "My Profile & Edit"),
        ("Search Users", "Search Users"),
        ("Connections & Requests", "Connections & Requests"),
        ("People You May Know", "People You May Know"),
        ("Degree & Chain Tool", "Degree & Chain Tool"),
        ("Notifications", f"Notifications ({unread})" if unread > 0 else "Notifications"),
        ("Trending Posts", "Trending Posts"),
        ("Communities", "Communities"),
        ("Browse All Students (AVL)", "Browse All Students (AVL)"),
    ]

    with st.sidebar:
        logo_b64 = _load_logo_b64()
        if logo_b64:
            st.markdown(
                f"<div class='cu-sidebar-logo'><img src='data:image/png;base64,{logo_b64}' alt='CU Connect'/></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("### 🎓 CU Connect")

        st.markdown(
            f"""
            <div class="cu-sidebar-user">
                <div class="cu-sidebar-name">{_esc(me.full_name)}</div>
                <div class="cu-sidebar-meta">
                    <span class="cu-sidebar-handle">@{_esc(me.username)}</span>
                    &bull; {_esc(me.programme)}, Y{me.year}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        active_page = st.session_state["active_page"]
        viewing_student = st.session_state.get("viewing_student")

        with st.container(key="cu_nav_list"):
            for page_id, label in nav_items:
                is_active = (viewing_student is None) and (active_page == page_id)
                if st.button(
                    label,
                    key=f"nav_btn_{page_id}",
                    type="primary" if is_active else "secondary",
                    width="stretch",
                ):
                    st.session_state["active_page"] = page_id
                    st.session_state.pop("viewing_student", None)
                    st.rerun()

        st.markdown("<div class='cu-sidebar-footer-spacer'></div>", unsafe_allow_html=True)

        if svc.can_undo(current_user):
            with st.container(key="cu_undo_box"):
                if st.button("↩️ Undo Last Action", width="stretch"):
                    try:
                        msg = svc.undo_last_action(current_user)
                        _set_flash("success", msg)
                        st.rerun()
                    except CUConnectError as exc:
                        st.error(str(exc))

        with st.container(key="cu_logout_box"):
            if st.button("Log Out", width="stretch"):
                svc.logout(current_user)
                st.session_state.pop("current_user", None)
                st.session_state.pop("viewing_student", None)
                st.session_state["active_page"] = "Home Feed"
                st.rerun()

    _show_flash()

    if viewing_student:
        _render_student_profile_detail(svc, current_user, viewing_student)
        return

    selected = st.session_state["active_page"]
    if selected == "Home Feed":
        _render_feed_page(svc, current_user)
    elif selected == "Post Composer":
        _render_post_composer_page(svc, current_user)
    elif selected == "My Profile & Edit":
        _render_profile_page(svc, current_user)
    elif selected == "Search Users":
        _render_search_page(svc, current_user)
    elif selected == "Connections & Requests":
        _render_connections_page(svc, current_user)
    elif selected == "People You May Know":
        _render_suggestions_page(svc, current_user)
    elif selected == "Degree & Chain Tool":
        _render_degree_page(svc, current_user)
    elif selected == "Notifications":
        _render_notifications_page(svc, current_user)
    elif selected == "Trending Posts":
        _render_trending_page(svc, current_user)
    elif selected == "Communities":
        _render_communities_page(svc, current_user)
    elif selected == "Browse All Students (AVL)":
        _render_directory_page(svc)


if __name__ == "__main__":
    main()
