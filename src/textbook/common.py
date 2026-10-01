"""Paths and helpers shared by the build commands."""

import hashlib
import itertools
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


# <sentence-builder vi="{who} tên là {name}." en="{who} name is {name}.">
# who: Tôi = My | Anh = Your
# name: Lan | Minh
# </sentence-builder>
BUILDER = re.compile(r"<sentence-builder\b([^>]*)>(.*?)</sentence-builder>", re.S)
_ATTR = re.compile(r'([\w-]+)="([^"]*)"')
SLOT_REF = re.compile(r"\{(\w+)\}")


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


def parse_builder(attrs: str, body: str) -> dict:
    """A sentence builder: templates plus, for each slot, a list of (Vietnamese, English) options."""
    values = dict(_ATTR.findall(attrs))
    slots = []
    for line in body.strip().splitlines():
        name, colon, options = line.partition(":")
        if not colon:
            continue
        choices = []
        for option in options.split("|"):
            vi, _, en = option.partition("=")
            choices.append((normalize(vi), normalize(en) or normalize(vi)))
        slots.append((name.strip(), choices))
    return {"vi": values.get("vi", ""), "en": values.get("en", ""), "slots": slots}


def fill_template(template: str, words: dict[str, str]) -> str:
    return normalize(SLOT_REF.sub(lambda m: words.get(m.group(1), m.group(0)), template))


def builder_sentences(builder: dict) -> list[tuple[str, str]]:
    """Every (Vietnamese, English) sentence a builder can make."""
    names = [name for name, _ in builder["slots"]]
    sentences = []
    for combo in itertools.product(*(choices for _, choices in builder["slots"])):
        vi = fill_template(builder["vi"], {n: c[0] for n, c in zip(names, combo)})
        en = fill_template(builder["en"], {n: c[1] for n, c in zip(names, combo)})
        sentences.append((vi, en))
    return sentences


def page_sources() -> list[Path]:
    pages = [p for p in SITE.glob("*") if p.suffix in (".md", ".html") and p.name != "template.html"]
    pages += [p for p in CHAPTERS.glob("*") if p.suffix in (".md", ".html")]
    return sorted(pages)


def load_cards(path: Path) -> dict:
    """Read a cards/*.yaml file. Every value stays text, so Vietnamese words like "no" (full)
    aren't read as booleans. A syntax error stops with the file and line, not a traceback."""
    try:
        return yaml.load(path.read_text("utf-8"), Loader=yaml.BaseLoader) or {}
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        where = f"{path.name}, line {mark.line + 1}" if mark else path.name
        raise SystemExit(
            f"error: can't read {where}: {getattr(error, 'problem', error)}\n"
            "Tip: put quotes around text containing : ? , { } [ ] or #, e.g. vi: \"Anh tên gì?\""
        ) from None


def collect_texts() -> set[str]:
    """Every word or phrase that needs audio: [[…]] on pages, plus `vi` on flashcards."""
    texts: set[str] = set()
    for page in page_sources():
        source = _CODE.sub("", page.read_text("utf-8"))
        for match in SAY_MARKUP.finditer(source):
            texts.add(parse_say(match.group(1))[1])
        for match in BUILDER.finditer(source):
            texts.update(vi for vi, _ in builder_sentences(parse_builder(match.group(1), match.group(2))))
    for deck in sorted(CARDS.glob("*.yaml")) if CARDS.exists() else []:
        data = load_cards(deck)
        for section in data.get("sections", []):
            for card in section.get("cards", []):
                if card.get("vi"):
                    texts.add(normalize(str(card["vi"])))
                for value in card.values():
                    for match in SAY_MARKUP.finditer(str(value)):
                        texts.add(parse_say(match.group(1))[1])
    return {t for t in texts if t}
