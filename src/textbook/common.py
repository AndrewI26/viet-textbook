"""Paths and helpers shared by the build commands."""

import hashlib
import re
import unicodedata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CHAPTERS = ROOT / "chapters"
CARDS = ROOT / "cards"
SITE = ROOT / "site"
AUDIO = ROOT / "audio"
RECORDINGS = ROOT / "recordings"
ANKI = ROOT / "anki"
DIST = ROOT / "dist"

# [[shown]] or [[shown :: spoken]]
SAY_MARKUP = re.compile(r"\[\[([^\[\]\n]+?)\]\]")

# Source regions where [[…]] is shown literally rather than spoken.
_CODE = re.compile(
    r"```.*?```|`[^`\n]*`|<(pre|code|script|style)\b.*?</\1>", re.S
)


def normalize(text: str) -> str:
    """NFC-normalize and collapse whitespace so the same words always match."""
    return unicodedata.normalize("NFC", " ".join(text.split()))


def parse_say(inner: str) -> tuple[str, str]:
    """Split the inside of [[…]] into (shown, spoken)."""
    shown, _, spoken = inner.partition("::")
    shown = normalize(shown)
    return shown, normalize(spoken) or shown


def audio_filename(text: str) -> str:
    """Audio file for a word or phrase. Shared by the website and the Anki deck."""
    key = normalize(text).lower()
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12] + ".mp3"


def page_sources() -> list[Path]:
    pages = [p for p in SITE.glob("*") if p.suffix in (".md", ".html") and p.name != "template.html"]
    pages += [p for p in CHAPTERS.glob("*") if p.suffix in (".md", ".html")]
    return sorted(pages)


def collect_texts() -> set[str]:
    """Every word or phrase that needs audio: [[…]] on pages, plus `vi` on flashcards."""
    texts: set[str] = set()
    for page in page_sources():
        source = _CODE.sub("", page.read_text("utf-8"))
        for match in SAY_MARKUP.finditer(source):
            texts.add(parse_say(match.group(1))[1])
    for deck in sorted(CARDS.glob("*.yaml")) if CARDS.exists() else []:
        # BaseLoader keeps every value as text, so Vietnamese words like "no" (full) aren't read as booleans.
        data = yaml.load(deck.read_text("utf-8"), Loader=yaml.BaseLoader) or {}
        for section in data.get("sections", []):
            for card in section.get("cards", []):
                if card.get("vi"):
                    texts.add(normalize(str(card["vi"])))
                for value in card.values():
                    for match in SAY_MARKUP.finditer(str(value)):
                        texts.add(parse_say(match.group(1))[1])
    return {t for t in texts if t}
