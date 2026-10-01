"""Build the website into dist/.

Pages come from site/index.md, site/styleguide.md and chapters/*.md|*.html.
Markdown pages are converted with Python-Markdown; .html pages are used as written.
Every page is then wrapped in site/template.html.

Usage: uv run site [--strict]
"""

import argparse
import html
import re
import shutil
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import markdown

from .common import ANKI, AUDIO, CHAPTERS, DIST, SAY_MARKUP, SITE, audio_filename, parse_say

SITE_NAME = "Tiếng Việt"

SPEAKER_ICON = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M11 5 6 9H3v6h3l5 4V5z" fill="currentColor"/>'
    '<path class="wave wave-1" d="M15.5 9a4.5 4.5 0 0 1 0 6"/>'
    '<path class="wave wave-2" d="M18.5 6a8.5 8.5 0 0 1 0 12"/>'
    "</svg>"
)

# [[shown]] or [[shown :: spoken]], skipped inside code, pre, script and style.
SAY_OR_SKIP = re.compile(
    r"(<(pre|code|script|style)\b.*?</\2>)|\[\[([^\[\]\n]+?)\]\]", re.S
)
H1 = re.compile(r"<h1\b[^>]*>(.*?)</h1>\s*", re.S)
H2 = re.compile(r"<h2\b([^>]*)>(.*?)</h2>", re.S)
ID_ATTR = re.compile(r'\bid="([^"]*)"')
TAG = re.compile(r"<[^>]+>")
COMPONENT_DEFINE = re.compile(
    r"""customElements\.define\(\s*["']([a-z][a-z0-9]*-[a-z0-9-]*)["']"""
)
CHAPTER_CARDS_MARKER = "<!-- chapters -->"


@dataclass
class Page:
    source: Path
    out: str  # path inside dist/, e.g. "chapters/01-sample.html"
    eyebrow: str = ""
    number: int | None = None
    title: str = ""
    body: str = ""
    sections: list[tuple[str, str]] = field(default_factory=list)  # (id, label)

    @property
    def base(self) -> str:
        """Relative prefix from this page back to the site root."""
        return "../" * self.out.count("/")

    @property
    def title_text(self) -> str:
        return plain_text(self.title)


def slugify(value: str, separator: str = "-") -> str:
    value = value.replace("đ", "d").replace("Đ", "D").replace(".", " ")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[\s_-]+", separator, value)


def plain_text(fragment: str) -> str:
    """Strip tags and [[…]] markup, leaving the text a reader sees."""
    text = SAY_MARKUP.sub(lambda m: parse_say(m.group(1))[0], fragment)
    return html.unescape(TAG.sub("", text)).strip()


def find_components() -> tuple[list[Path], list[str]]:
    files = sorted((SITE / "components").glob("*.js"))
    tags = [tag for f in files for tag in COMPONENT_DEFINE.findall(f.read_text("utf-8"))]
    return files, tags


def find_pages() -> list[Page]:
    pages = []
    for stem, eyebrow in (("index", "Southern Vietnamese · Open textbook"), ("styleguide", "Design system")):
        source = next((p for p in (SITE / f"{stem}.md", SITE / f"{stem}.html") if p.exists()), None)
        if source:
            pages.append(Page(source, f"{stem}.html", eyebrow))

    seen = {}
    for source in sorted(CHAPTERS.glob("*")):
        if source.suffix not in (".md", ".html"):
            continue
        if source.stem in seen:
            sys.exit(f"error: both {seen[source.stem].name} and {source.name} exist; keep one")
        seen[source.stem] = source
        match = re.match(r"(\d+)", source.stem)
        number = int(match.group(1)) if match else None
        eyebrow = f"Chapter {number}" if number is not None else ""
        pages.append(Page(source, f"chapters/{source.stem}.html", eyebrow, number))
    return pages


def render(page: Page, md: markdown.Markdown) -> None:
    text = page.source.read_text("utf-8")
    if page.source.suffix == ".md":
        md.reset()
        body = md.convert(text)
    else:
        body = text

    match = H1.search(body)
    if match:
        page.title = match.group(1).strip()
        body = body[: match.start()] + body[match.end() :]
    else:
        page.title = page.source.stem.replace("-", " ").title()

    def add_section(m: re.Match) -> str:
        attrs, inner = m.group(1), m.group(2)
        id_match = ID_ATTR.search(attrs)
        if id_match:
            section_id = id_match.group(1)
        else:
            section_id = slugify(plain_text(inner))
            attrs = f' id="{section_id}"{attrs}'
        page.sections.append((section_id, plain_text(inner)))
        return f"<h2{attrs}>{inner}</h2>"

    body = H2.sub(add_section, body)
    body = re.sub(r"<table\b", '<div class="table-wrap"><table', body)
    body = body.replace("</table>", "</table></div>")
    page.body = body


def link_words(fragment: str, base: str, missing: set[str]) -> str:
    """Turn every [[…]] into a clickable pronunciation button."""

    def replace(m: re.Match) -> str:
        if m.group(1):
            return m.group(1)
        shown, spoken = parse_say(html.unescape(m.group(3)))
        filename = audio_filename(spoken)
        attrs = f'class="say" data-src="{base}audio/{filename}"'
        if not (AUDIO / filename).exists():
            missing.add(spoken)
            attrs = (
                f'class="say say--missing" data-src="{base}audio/{filename}" '
                'aria-disabled="true" title="Audio not generated yet"'
            )
        return (
            f'<button type="button" {attrs} '
            f'aria-label="Play pronunciation: {html.escape(spoken)}">'
            f'<span class="say-text">{html.escape(shown)}</span>'
            f'<span class="say-icon" aria-hidden="true">{SPEAKER_ICON}</span>'
            "</button>"
        )

    return SAY_OR_SKIP.sub(replace, fragment)


def chapter_cards(chapters: list[Page], base: str) -> str:
    cards = []
    for p in chapters:
        count = len(p.sections)
        cards.append(
            f'<a class="card card-link" href="{base}{p.out}">'
            f'<span class="eyebrow">{p.eyebrow}</span>'
            f'<span class="card-title">{html.escape(p.title_text)}</span>'
            f'<span class="card-meta">{count} section{"s" if count != 1 else ""}</span>'
            "</a>"
        )
    return f'<div class="card-grid">{"".join(cards)}</div>'


def sidebar(chapters: list[Page], styleguide: Page | None, current: Page) -> str:
    b = current.base

    def item(p: Page, label: str, num: str = "") -> str:
        active = p is current
        cls = "nav-item is-active" if active else "nav-item"
        aria = ' aria-current="page"' if active else ""
        num_html = f'<span class="nav-num">{num}</span>' if num else ""
        return f'<a class="{cls}" href="{b}{p.out}"{aria}>{num_html}<span>{html.escape(label)}</span></a>'

    parts = [f'<a class="nav-item{" is-active" if current.out == "index.html" else ""}" href="{b}index.html">Home</a>']
    parts.append('<p class="nav-label">Chapters</p><ol class="nav-chapters">')
    for p in chapters:
        num = f"{p.number:02d}" if p.number is not None else ""
        sections = ""
        if p is current and p.sections:
            links = "".join(
                f'<li><a href="#{sid}">{html.escape(label)}</a></li>' for sid, label in p.sections
            )
            sections = f'<ul class="nav-sections">{links}</ul>'
        parts.append(f"<li>{item(p, p.title_text, num)}{sections}</li>")
    parts.append("</ol>")
    if styleguide:
        parts.append(f'<div class="nav-footer">{item(styleguide, "Style guide")}</div>')
    return "".join(parts)


def pager(sequence: list[Page], current: Page) -> str:
    if current not in sequence:
        return ""
    i = sequence.index(current)
    b = current.base
    links = []
    if i > 0:
        prev = sequence[i - 1]
        label = "Home" if prev.out == "index.html" else prev.title_text
        links.append(
            f'<a class="pager-link pager-prev" href="{b}{prev.out}">'
            f'<span class="pager-label">Previous</span>'
            f'<span class="pager-title">{html.escape(label)}</span></a>'
        )
    if i < len(sequence) - 1:
        nxt = sequence[i + 1]
        links.append(
            f'<a class="pager-link pager-next" href="{b}{nxt.out}">'
            f'<span class="pager-label">Next</span>'
            f'<span class="pager-title">{html.escape(nxt.title_text)}</span></a>'
        )
    return "".join(links)


def fill(template: str, **values: str) -> str:
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: values.get(m.group(1), ""), template)


def copy_assets(component_files: list[Path]) -> None:
    assets = DIST / "assets"
    for f in SITE.rglob("*"):
        if f.is_file() and f.suffix != ".md" and f.name != "template.html":
            target = assets / f.relative_to(SITE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
    if AUDIO.exists():
        shutil.copytree(AUDIO, DIST / "audio")
    for deck in ANKI.glob("*.apkg") if ANKI.exists() else []:
        (DIST / "anki").mkdir(exist_ok=True)
        shutil.copy2(deck, DIST / "anki" / deck.name)


def build() -> tuple[int, set[str]]:
    component_files, component_tags = find_components()
    md = markdown.Markdown(
        extensions=["tables", "toc", "md_in_html", "attr_list", "fenced_code", "sane_lists"],
        extension_configs={"toc": {"slugify": slugify}},
    )
    md.block_level_elements.extend(component_tags)

    pages = find_pages()
    for page in pages:
        render(page, md)

    home = next((p for p in pages if p.out == "index.html"), None)
    styleguide = next((p for p in pages if p.out == "styleguide.html"), None)
    chapters = [p for p in pages if p.out.startswith("chapters/")]
    sequence = ([home] if home else []) + chapters
    template = (SITE / "template.html").read_text("utf-8")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    version = str(int(time.time()))  # cache-buster for asset URLs
    missing: set[str] = set()
    for page in pages:
        b = page.base
        body = page.body.replace(CHAPTER_CARDS_MARKER, chapter_cards(chapters, b))
        body = link_words(body, b, missing)
        title = link_words(page.title, b, missing)
        scripts = "\n".join(
            f'<script src="{b}assets/components/{f.name}?v={version}" defer></script>'
            for f in component_files
        )
        doc_title = SITE_NAME if page is home else f"{page.title_text} · {SITE_NAME}"
        eyebrow = f'<p class="eyebrow">{html.escape(page.eyebrow)}</p>' if page.eyebrow else ""
        output = fill(
            template,
            base=b,
            v=version,
            doc_title=html.escape(doc_title),
            site_name=SITE_NAME,
            component_scripts=scripts,
            sidebar=sidebar(chapters, styleguide, page),
            eyebrow=eyebrow,
            title=title,
            content=body,
            pager=pager(sequence, page),
        )
        target = DIST / page.out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output, "utf-8")

    copy_assets(component_files)
    return len(pages), missing


def main() -> None:
    parser = argparse.ArgumentParser(prog="uv run site", description="Build the website into dist/.")
    parser.add_argument("--strict", action="store_true", help="fail if any [[word]] has no audio file")
    args = parser.parse_args()

    count, missing = build()
    print(f"Built {count} pages into dist/")
    if missing:
        print(f"{len(missing)} words have no audio yet (they show as dimmed on the site).")
        if args.strict:
            for word in sorted(missing):
                print(f"  missing audio: {word}")
            sys.exit("error: --strict build with missing audio")


if __name__ == "__main__":
    main()
