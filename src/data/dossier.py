"""Static behavioral dossier assembly.

Dossiers are composed from two parts:
  - **Noise base** (shared across profiles): mundane workplace data (~80%)
  - **Signal insert** (profile-specific): personality-revealing items (~20%)

Three paired variants exist (v1, v2, v3). Each assembled dossier interleaves
the signal items into the noise at deterministic positions so the adversary
must sift through realistic data to find actionable intelligence.

Directory layout:
  prompts/dossiers/noise/v1.yaml, v2.yaml, v3.yaml
  prompts/dossiers/signal/<profile_name>/v1.yaml, v2.yaml, v3.yaml
"""

from pathlib import Path

import yaml

DOSSIERS_DIR = Path(__file__).resolve().parents[2] / "prompts" / "dossiers"
NOISE_DIR = DOSSIERS_DIR / "noise"
SIGNAL_DIR = DOSSIERS_DIR / "signal"

SECTIONS = ("chat_logs", "browsing", "social_media", "calendar", "emails")

# Deterministic insertion positions per section.
# These spread signal items across the noise so they aren't clustered.
_INSERTION_POINTS = {
    "chat_logs": [2],             # 1 signal item, inserted at position 2 of ~4 noise
    "browsing": [3, 9],           # 2 signal items among ~13 noise
    "social_media": [1, 4],       # 2 signal items among ~6 noise
    "calendar": [2, 6],           # 2 signal items among ~8 noise
    "emails": [1, 4],             # 2 signal items among ~6 noise
}


def _interleave(noise_items: list, signal_items: list, insertion_points: list[int]) -> list:
    """Insert signal items into noise at the specified positions."""
    result = list(noise_items)
    for i, (pos, item) in enumerate(zip(insertion_points, signal_items)):
        # Clamp to valid range.
        insert_at = min(pos, len(result))
        result.insert(insert_at, item)
    return result


def load_noise(variant: int) -> dict[str, list]:
    """Load a noise base file (v1, v2, or v3)."""
    path = NOISE_DIR / f"v{variant}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Noise base not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    return {section: data.get(section, []) for section in SECTIONS}


def load_signal(profile_name: str, variant: int) -> dict[str, list]:
    """Load a signal insert file for a given profile and variant."""
    path = SIGNAL_DIR / profile_name / f"v{variant}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Signal file not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    return {section: data.get(section, []) for section in SECTIONS}


def assemble_dossier(profile_name: str, variant: int) -> dict[str, list]:
    """Assemble a complete dossier by interleaving noise and signal.

    Args:
        profile_name: Name of the target profile (e.g. "approval_seeking").
        variant: Dossier variant (1, 2, or 3).

    Returns:
        Dict mapping section names to lists of items with signal embedded.
    """
    noise = load_noise(variant)
    signal = load_signal(profile_name, variant)

    assembled = {}
    for section in SECTIONS:
        noise_items = noise.get(section, [])
        signal_items = signal.get(section, [])
        points = _INSERTION_POINTS.get(section, [])
        assembled[section] = _interleave(noise_items, signal_items, points)

    return assembled


def format_dossier(dossier: dict[str, list]) -> str:
    """Format an assembled dossier as a human-readable string for prompts."""
    parts = []

    # Chat logs
    if dossier.get("chat_logs"):
        parts.append("=== CHAT LOGS ===")
        for log in dossier["chat_logs"]:
            platform = log.get("platform", "Chat")
            channel = log.get("channel", "")
            header = f"[{platform}]"
            if channel:
                header += f" {channel}"
            parts.append(header)
            for msg in log.get("messages", []):
                parts.append(f"  {msg['from']}: {msg['text']}")
            parts.append("")

    # Browsing history
    if dossier.get("browsing"):
        parts.append("=== RECENT BROWSING ===")
        for entry in dossier["browsing"]:
            title = entry.get("title", entry.get("url", ""))
            parts.append(f"  - {title}")
        parts.append("")

    # Social media
    if dossier.get("social_media"):
        parts.append("=== SOCIAL MEDIA ===")
        for post in dossier["social_media"]:
            platform = post.get("platform", "")
            content = post.get("content", "")[:150]
            parts.append(f"  [{platform}] {content}")
        parts.append("")

    # Calendar
    if dossier.get("calendar"):
        parts.append("=== UPCOMING CALENDAR ===")
        for event in dossier["calendar"]:
            title = event.get("title", "")
            time = event.get("time", "")
            parts.append(f"  - {title} ({time})")
        parts.append("")

    # Emails
    if dossier.get("emails"):
        parts.append("=== RECENT EMAILS ===")
        for email in dossier["emails"]:
            sender = email.get("from", "Unknown")
            subject = email.get("subject", "")
            snippet = email.get("snippet", "")
            parts.append(f"  From {sender}: {subject}")
            if snippet:
                parts.append(f"    \"{snippet[:120]}\"")
        parts.append("")

    return "\n".join(parts)


def get_dossier_text(profile_name: str, variant: int) -> str:
    """One-shot: assemble and format a dossier as prompt text."""
    return format_dossier(assemble_dossier(profile_name, variant))


def list_available_variants(profile_name: str) -> list[int]:
    """Return which dossier variants (1, 2, 3) exist for a profile."""
    signal_dir = SIGNAL_DIR / profile_name
    if not signal_dir.exists():
        return []
    return sorted(
        int(p.stem[1:])
        for p in signal_dir.glob("v*.yaml")
        if p.stem[1:].isdigit()
    )
