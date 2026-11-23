"""
Mood-driven theming.

Each mood in the sidebar dropdown maps to a MoodTheme: a colour palette, a
page gradient and a set of emojis that float softly in the page background.
`inject_theme()` turns the active theme into CSS variables (consumed by
assets/style.css) plus a fixed, click-through emoji layer.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class MoodTheme:
    key: str                       # mood id ("happy") or "default"
    emoji: str                     # main emoji shown in header / avatar / tab icon
    note: str                      # one-line message shown under the dropdown
    accent: str                    # buttons, slider, focus rings
    on_accent: str                 # text colour on top of `accent`
    deep: str                      # headings / small caps text on light backgrounds
    muted: str                     # secondary text
    line: str                      # borders
    bg: tuple[str, str, str]       # page gradient (top-left → bottom-right)
    floaters: tuple[str, ...]      # background emojis (first one is the mood emoji)


DEFAULT_THEME = MoodTheme(
    key="default", emoji="", note="",
    accent="#0D9488", on_accent="#FFFFFF", deep="#0F766E",
    muted="#5B6B73", line="#D8E3E0",
    bg=("#F8FAFC", "#F1F7F6", "#EAF4F2"),
    floaters=(),
)

MOOD_THEMES: dict[str, MoodTheme] = {
    "happy": MoodTheme(
        key="happy", emoji="😊",
        note="Lovely! Let's make the most of this sunshine.",
        accent="#F59E0B", on_accent="#3A2200", deep="#92400E",
        muted="#7A5A1E", line="#F3DDA0",
        bg=("#FFFBEB", "#FEF3C7", "#FFE8C7"),
        floaters=("😊", "☀️", "🌻", "✨", "🎈", "🌼", "😄"),
    ),
    "calm": MoodTheme(
        key="calm", emoji="😌",
        note="A peaceful mind is a great place to start.",
        accent="#15803D", on_accent="#FFFFFF", deep="#166534",
        muted="#4B6355", line="#C9E6D3",
        bg=("#F0FDF4", "#DCFCE7", "#D5F0F0"),
        floaters=("😌", "🌿", "🍃", "🌱", "🕊️", "🪷", "🌊"),
    ),
    "anxious": MoodTheme(
        key="anxious", emoji="😟",
        note="Take a slow breath. You're safe here.",
        accent="#7C3AED", on_accent="#FFFFFF", deep="#5B21B6",
        muted="#5E4F7A", line="#E2D4FA",
        bg=("#FAF5FF", "#F3E8FF", "#E6E8FF"),
        floaters=("😟", "🫧", "🌀", "🌬️", "💜", "🍵", "🦋"),
    ),
    "sad": MoodTheme(
        key="sad", emoji="😢",
        note="It's okay to feel this. I'm here with you.",
        accent="#1D4ED8", on_accent="#FFFFFF", deep="#1E40AF",
        muted="#475A7E", line="#C9D8F7",
        bg=("#EFF6FF", "#DBEAFE", "#E3E5F8"),
        floaters=("😢", "🌧️", "☔", "💧", "💙", "☁️", "🫂"),
    ),
    "angry": MoodTheme(
        key="angry", emoji="😠",
        note="Your anger is valid. Let's work through it together.",
        accent="#DC2626", on_accent="#FFFFFF", deep="#991B1B",
        muted="#7A4A4A", line="#F6CACA",
        bg=("#FEF2F2", "#FEE2E2", "#FFE4D6"),
        floaters=("😠", "🔥", "💢", "⚡", "🌋", "😤", "🧯"),
    ),
    "stressed": MoodTheme(
        key="stressed", emoji="😩",
        note="One thing at a time. We'll lighten the load.",
        accent="#C2410C", on_accent="#FFFFFF", deep="#9A3412",
        muted="#7C523A", line="#F8D5BD",
        bg=("#FFF7ED", "#FFEDD5", "#FDE2D2"),
        floaters=("😩", "⏳", "📚", "☕", "🍂", "🧘", "⏰"),
    ),
    "exhausted": MoodTheme(
        key="exhausted", emoji="😴",
        note="Rest is productive too. Be gentle with yourself.",
        accent="#64748B", on_accent="#FFFFFF", deep="#334155",
        muted="#546275", line="#D3DAE4",
        bg=("#F8FAFC", "#EEF2F7", "#E2E8F4"),
        floaters=("😴", "🌙", "💤", "⭐", "🛌", "🌌", "🧸"),
    ),
    "confused": MoodTheme(
        key="confused", emoji="🤔",
        note="Not sure yet? Let's untangle it together.",
        accent="#DB2777", on_accent="#FFFFFF", deep="#9D174D",
        muted="#7A4B62", line="#F7CFE0",
        bg=("#FDF2F8", "#FCE7F3", "#F3E8FF"),
        floaters=("🤔", "❓", "🧩", "💭", "🔍", "🌫️", "💡"),
    ),
}


def get_theme(mood: str | None) -> MoodTheme:
    """Return the theme for a mood id, or the neutral default."""
    return MOOD_THEMES.get(mood or "", DEFAULT_THEME)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _rgba(hex_colour: str, alpha: float) -> str:
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def _variables_css(t: MoodTheme) -> str:
    return (
        ":root{"
        f"--accent:{t.accent};"
        f"--on-accent:{t.on_accent};"
        f"--accent-deep:{t.deep};"
        f"--accent-soft:{_rgba(t.accent, 0.12)};"
        f"--accent-border:{_rgba(t.accent, 0.45)};"
        f"--accent-glow:{_rgba(t.accent, 0.28)};"
        f"--ink-soft:{t.muted};"
        f"--line:{t.line};"
        f"--bg-1:{t.bg[0]};--bg-2:{t.bg[1]};--bg-3:{t.bg[2]};"
        "}"
    )


def _floaters_html(t: MoodTheme) -> str:
    """A fixed, click-through layer of softly floating emojis (deterministic per mood)."""
    if not t.floaters:
        return ""

    rng = random.Random(t.key)
    pool = [t.floaters[0]] * 3 + list(t.floaters[1:]) * 2   # main mood emoji appears most
    cols, rows = 4, 4
    spans: list[str] = []
    for i in range(cols * rows):
        c, r = i % cols, i // cols
        left = (c + rng.uniform(0.15, 0.85)) / cols * 100
        top = (r + rng.uniform(0.15, 0.85)) / rows * 100
        if 22 < left < 78 and top < 26:          # keep the title band clear
            top += 26
        size = rng.uniform(2.0, 4.6)
        rot = rng.randint(-24, 24)
        dur = rng.uniform(9, 17)
        delay = -rng.uniform(0, dur)
        opacity = rng.uniform(0.16, 0.30)
        spans.append(
            f'<span style="left:{left:.1f}%;top:{top:.1f}%;font-size:{size:.1f}rem;'
            f'--r:{rot}deg;--d:{dur:.1f}s;--o:{opacity:.2f};animation-delay:{delay:.1f}s,0s">'
            f"{rng.choice(pool)}</span>"
        )
    return f'<div class="mood-bg-layer" aria-hidden="true">{"".join(spans)}</div>'


# ── Public API ──────────────────────────────────────────────────────────────

def inject_theme(theme: MoodTheme) -> None:
    """Apply the theme's colours and background emojis to the whole page."""
    st.markdown(
        f'<style class="mood-css">{_variables_css(theme)}</style>{_floaters_html(theme)}',
        unsafe_allow_html=True,
    )
