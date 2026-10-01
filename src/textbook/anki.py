"""Build the Anki deck from cards/*.yaml into anki/vietnamese-southern.apkg.

Each chapter file becomes a subdeck, and each section a subdeck inside it:
    Vietnamese (Southern)::03 Tones::3.2 The six tone marks

Card types (the `type` of each card in the YAML):
    read    see the word, say it out loud, flip to hear it      needs: vi            optional: tip
    listen  hear a word, recall what it was                     needs: vi, answer
    vocab   two cards: Vietnamese → English and English → Vietnamese
                                                                needs: vi, en        optional: notes
    basic   a question and an answer                            needs: front, back

Text fields can use Markdown (*italic*, **bold**) and [[word]] (or [[shown :: spoken]])
to add that word's audio.
Re-importing the deck updates existing cards and keeps your review history.

Usage: uv run anki
"""

import hashlib
import html
import re
import sys
from pathlib import Path

import genanki
import markdown
import yaml

from .common import ANKI, AUDIO, CARDS, SAY_MARKUP, audio_filename, normalize, parse_say

DECK_NAME = "Vietnamese (Southern)"
OUTPUT = ANKI / "vietnamese-southern.apkg"

CSS = """
.card {
  font-family: -apple-system, BlinkMacSystemFont, Inter, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 20px;
  line-height: 1.5;
  text-align: center;
  color: #32302f;
  background: #fcfcfc;
  padding: 28px 16px;
}
.section {
  margin-bottom: 32px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #686664;
}
.vi {
  font-family: "Source Serif 4", Georgia, "Times New Roman", serif;
  font-size: 52px;
  line-height: 1.2;
  color: #09090a;
}
.en { font-size: 30px; color: #09090a; }
.prompt { margin-top: 18px; font-size: 15px; color: #686664; }
.answer { margin-top: 10px; font-size: 20px; }
.tip {
  max-width: 480px;
  margin: 24px auto 0;
  padding: 16px 20px;
  border-radius: 18px;
  background: #f6f4f1;
  font-size: 16px;
  text-align: left;
}
hr#answer { margin: 28px 0; border: 0; border-top: 1px solid #e4e2e1; }

.nightMode.card, .night_mode .card, .nightMode .card { color: #f3f1ee; background: #141312; }
.nightMode .vi, .night_mode .vi, .nightMode .en, .night_mode .en { color: #ffffff; }
.nightMode .section, .night_mode .section, .nightMode .prompt, .night_mode .prompt { color: #a3a09c; }
.nightMode .tip, .night_mode .tip { background: #1c1b1a; }
.nightMode hr#answer, .night_mode hr#answer { border-top-color: #2f2d2b; }
"""

SECTION = '<div class="section">{{Section}}</div>'


def model(model_id: int, name: str, fields: list[str], templates: list[tuple[str, str, str]]) -> genanki.Model:
    return genanki.Model(
        model_id,
        name,
        fields=[{"name": f} for f in fields],
        templates=[{"name": n, "qfmt": q, "afmt": a} for n, q, a in templates],
        css=CSS,
    )


# Fixed IDs: changing them would make Anki treat these as new note types.
READ = model(1720450001, "Tiếng Việt · Read aloud", ["Vietnamese", "Audio", "Tip", "Section"], [(
    "Read aloud",
    SECTION + '<div class="vi">{{Vietnamese}}</div><div class="prompt">Say it out loud, then flip</div>',
    SECTION + '<div class="vi">{{Vietnamese}}</div>{{Audio}}<hr id="answer">{{#Tip}}<div class="tip">{{Tip}}</div>{{/Tip}}',
)])

LISTEN = model(1720450002, "Tiếng Việt · Listen", ["Audio", "Vietnamese", "Answer", "Section"], [(
    "Listen",
    SECTION + '{{Audio}}<div class="prompt">What did you hear?</div>',
    SECTION + '{{Audio}}<hr id="answer"><div class="vi">{{Vietnamese}}</div><div class="answer">{{Answer}}</div>',
)])

VOCAB = model(1720450003, "Tiếng Việt · Vocabulary", ["Vietnamese", "English", "Audio", "Notes", "Section"], [
    (
        "Vietnamese → English",
        SECTION + '<div class="vi">{{Vietnamese}}</div>{{Audio}}',
        '{{FrontSide}}<hr id="answer"><div class="en">{{English}}</div>{{#Notes}}<div class="tip">{{Notes}}</div>{{/Notes}}',
    ),
    (
        "English → Vietnamese",
        SECTION + '<div class="en">{{English}}</div><div class="prompt">Say it in Vietnamese</div>',
        SECTION + '<div class="en">{{English}}</div><hr id="answer"><div class="vi">{{Vietnamese}}</div>{{Audio}}{{#Notes}}<div class="tip">{{Notes}}</div>{{/Notes}}',
    ),
])

BASIC = model(1720450004, "Tiếng Việt · Basic", ["Front", "Back", "Section"], [(
    "Basic",
    SECTION + '<div class="answer">{{Front}}</div>',
    '{{FrontSide}}<hr id="answer"><div class="answer">{{Back}}</div>',
)])

REQUIRED = {"read": ["vi"], "listen": ["vi", "answer"], "vocab": ["vi", "en"], "basic": ["front", "back"]}


class DeckBuilder:
    def __init__(self) -> None:
        self.media: set[str] = set()
        self.missing: set[str] = set()

    def sound(self, text: str) -> str:
        filename = audio_filename(text)
        if (AUDIO / filename).exists():
            self.media.add(filename)
            return f"[sound:{filename}]"
        self.missing.add(normalize(text))
        return ""

    def rich(self, value) -> str:
        """Field text: Markdown becomes HTML, and [[word]] becomes the word plus its audio."""

        def replace(m: re.Match) -> str:
            shown, spoken = parse_say(m.group(1))
            return f"<b>{html.escape(shown)}</b> {self.sound(spoken)}".rstrip()

        text = markdown.markdown(str(value or "").strip())
        if text.count("<p>") == 1 and text.startswith("<p>") and text.endswith("</p>"):
            text = text[3:-4]  # a single paragraph needs no <p> wrapper
        return SAY_MARKUP.sub(replace, text).strip()

    def note(self, card: dict, section: str, label: str, where: str) -> genanki.Note:
        kind = card.get("type")
        if kind not in REQUIRED:
            sys.exit(f"{where}: unknown card type {kind!r} (use read, listen, vocab or basic)")
        absent = [f for f in REQUIRED[kind] if not card.get(f)]
        if absent:
            sys.exit(f"{where}: {kind} card is missing {', '.join(absent)}")

        primary = normalize(str(card.get("vi") or card.get("front")))
        guid = genanki.guid_for(card.get("id") or f"{section}|{kind}|{primary}")
        tags = [kind]

        vi = html.escape(primary)
        label = html.escape(label)
        if kind == "read":
            fields = [vi, self.sound(primary), self.rich(card.get("tip")), label]
            return genanki.Note(READ, fields, guid=guid, tags=tags)
        if kind == "listen":
            fields = [self.sound(primary), vi, self.rich(card["answer"]), label]
            return genanki.Note(LISTEN, fields, guid=guid, tags=tags)
        if kind == "vocab":
            fields = [vi, self.rich(card["en"]), self.sound(primary), self.rich(card.get("notes")), label]
            return genanki.Note(VOCAB, fields, guid=guid, tags=tags)
        fields = [self.rich(card["front"]), self.rich(card["back"]), label]
        return genanki.Note(BASIC, fields, guid=guid, tags=tags)


def deck_id(name: str) -> int:
    return int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:12], 16)


def build() -> tuple[int, int, int, set[str]]:
    builder = DeckBuilder()
    decks = []
    note_count = card_count = 0
    for path in sorted(CARDS.glob("*.yaml")) if CARDS.exists() else []:
        data = yaml.safe_load(path.read_text("utf-8")) or {}
        chapter = int(data.get("chapter", 0))
        chapter_name = f"{DECK_NAME}::{chapter:02d} {data.get('title', path.stem)}"
        for s, section in enumerate(data.get("sections", []), 1):
            section_id = str(section.get("id", ""))  # e.g. "3.2"; leave out for "Vocabulary"
            title = section.get("title", "")
            name = f"{chapter_name}::{f'{section_id} {title}'.strip()}"
            deck = genanki.Deck(deck_id(name), name)
            label = f"{section_id} · {title}".strip(" ·")
            for c, card in enumerate(section.get("cards", []), 1):
                # Card identity uses the section number (not its title), so renaming a section keeps your progress.
                key = f"{chapter}|{section_id or title}"
                note = builder.note(card, key, label, f"{path.name}, {label}, card {c}")
                note.tags.append(f"ch{chapter:02d}")
                deck.add_note(note)
                note_count += 1
                card_count += 2 if card["type"] == "vocab" else 1
            decks.append(deck)

    if not decks:
        sys.exit("No cards found. Add cards/<chapter>.yaml files first.")
    ANKI.mkdir(exist_ok=True)
    package = genanki.Package(decks, media_files=[str(AUDIO / f) for f in sorted(builder.media)])
    package.write_to_file(OUTPUT)
    return note_count, card_count, len(decks), builder.missing


def main() -> None:
    notes, cards, decks, missing = build()
    print(f"Built {OUTPUT.relative_to(OUTPUT.parents[1])}: {notes} notes, {cards} cards, {decks} sections")
    if missing:
        print(f"{len(missing)} words on cards have no audio yet. Run `uv run audio`, then `uv run anki` again.")


if __name__ == "__main__":
    main()
