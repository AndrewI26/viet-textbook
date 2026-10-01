"""Build the website into dist/.

Pages come from site/index.md, site/styleguide.md and chapters/*.md|*.html.
Markdown pages are converted with Python-Markdown; .html pages are used as written.
Every page is then wrapped in site/template.html.

Math: $…$ (inline) and $$…$$ (display) are LaTeX, converted to MathML at build
time, so pages need no math library. Write \\$ for a literal dollar sign.

Usage: uv run site [--strict]
"""

import argparse
import html
import json
import posixpath
import re
import shutil
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import markdown
import yaml
from latex2mathml.converter import convert as latex_to_mathml

from .common import (
    ANKI,
    AUDIO,
    BUILDER,
    CHAPTERS,
    DIST,
    SAY_MARKUP,
    SITE,
    audio_filename,
    builder_sentences,
    parse_builder,
    parse_say,
)

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
DISPLAY_MATH = re.compile(r"\$\$(.+?)\$\$", re.S)
INLINE_MATH = re.compile(r"(?<![\\$])\$(?=\S)(.+?)(?<=\S)(?<!\\)\$(?!\$)")
MATH_TOKEN = re.compile(r"(?:<p>)?MATHTOKEN(\d+)X(?:</p>)?")
HREF = re.compile(r'<a\b[^>]*\bhref="([^"]+)"')


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
    for stem, eyebrow in (
        ("index", "Southern Vietnamese · Open textbook"),
        ("cheatsheet", "Reference"),
        ("styleguide", "Design system"),
    ):
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


def protect_math(text: str) -> tuple[str, list[str]]:
    """Swap LaTeX for plain tokens so Markdown can't touch it; return the MathML for each."""
    rendered: list[str] = []

    def display(m: re.Match) -> str:
        rendered.append(f'<div class="math-display">{latex_to_mathml(m.group(1).strip(), display="block")}</div>')
        return f"\n\nMATHTOKEN{len(rendered) - 1}X\n\n"

    def inline(m: re.Match) -> str:
        rendered.append(latex_to_mathml(m.group(1)))
        return f"MATHTOKEN{len(rendered) - 1}X"

    return INLINE_MATH.sub(inline, DISPLAY_MATH.sub(display, text)), rendered


def restore_math(body: str, rendered: list[str]) -> str:
    return MATH_TOKEN.sub(lambda m: rendered[int(m.group(1))], body).replace("\\$", "$")


def render(page: Page, md: markdown.Markdown) -> None:
    text, maths = protect_math(page.source.read_text("utf-8"))
    if page.source.suffix == ".md":
        md.reset()
        body = md.convert(text)
    else:
        body = text
    body = restore_math(body, maths)

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


def load_parts() -> dict[int, str]:
    """Part names from chapters/parts.yaml, keyed by the chapter each part starts at."""
    path = CHAPTERS / "parts.yaml"
    if not path.exists():
        return {}
    data = yaml.load(path.read_text("utf-8"), Loader=yaml.BaseLoader) or {}
    return {int(number): name for number, name in data.items()}


def grouped(chapters: list[Page], parts: dict[int, str]) -> list[tuple[str, list[Page]]]:
    """Chapters grouped by part: [(part name, chapters)]. One unnamed group if there are no parts."""
    groups: list[tuple[str, list[Page]]] = []
    for p in chapters:
        if p.number in parts or not groups:
            groups.append((parts.get(p.number, ""), []))
        groups[-1][1].append(p)
    return groups


def render_builders(body: str, base: str, missing: set[str]) -> str:
    """Turn each <sentence-builder> into JSON for site/components/sentence-builder.js,
    including the audio file for every sentence it can make."""

    def replace(m: re.Match) -> str:
        builder = parse_builder(html.unescape(m.group(1)), html.unescape(m.group(2)))
        audio = {}
        for vi, _ in builder_sentences(builder):
            filename = audio_filename(vi)
            if (AUDIO / filename).exists():
                audio[vi] = f"{base}audio/{filename}"
            else:
                missing.add(vi)
        data = {
            "vi": builder["vi"],
            "en": builder["en"],
            "slots": [
                {"name": name, "options": [{"vi": vi, "en": en} for vi, en in choices]}
                for name, choices in builder["slots"]
            ],
            "audio": audio,
        }
        payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
        return f'<sentence-builder><script type="application/json">{payload}</script></sentence-builder>'

    return BUILDER.sub(replace, body)


def table_of_contents(chapters: list[Page], parts: dict[int, str], base: str) -> str:
    """The home page's contents: each chapter with its numbered sections listed below, grouped by part."""
    out = ['<div class="toc">']
    for index, (name, pages) in enumerate(grouped(chapters, parts), 1):
        if name:
            out.append(f'<p class="toc-part">Part {index} · {html.escape(name)}</p>')
        out.append('<ol class="toc-list">')
        for p in pages:
            num = f"{p.number:02d}" if p.number is not None else ""
            sections = []
            for sid, label in p.sections:
                number, _, title = label.partition(" ")
                if not number[:1].isdigit():
                    continue  # numbered sections only, not Vocabulary / Flashcards
                sections.append(
                    f'<li><a class="toc-link" href="{base}{p.out}#{sid}">'
                    f'<span class="toc-snum">{html.escape(number)}</span>'
                    f'<span>{html.escape(title)}</span></a></li>'
                )
            out.append(
                '<li class="toc-chapter">'
                f'<a class="toc-link toc-title" href="{base}{p.out}">'
                f'<span class="toc-num">{num}</span><span class="toc-name">{html.escape(p.title_text)}</span></a>'
                f'<ul class="toc-sections">{"".join(sections)}</ul>'
                "</li>"
            )
        out.append("</ol>")
    out.append("</div>")
    return "".join(out)


def sidebar(chapters: list[Page], parts: dict[int, str], extras: dict[str, Page], current: Page) -> str:
    b = current.base

    def item(p: Page, label: str, num: str = "") -> str:
        active = p is current
        cls = "nav-item is-active" if active else "nav-item"
        aria = ' aria-current="page"' if active else ""
        num_html = f'<span class="nav-num">{num}</span>' if num else ""
        return f'<a class="{cls}" href="{b}{p.out}"{aria}>{num_html}<span>{html.escape(label)}</span></a>'

    out = [f'<a class="nav-item{" is-active" if current.out == "index.html" else ""}" href="{b}index.html">Home</a>']
    if "cheatsheet" in extras:
        out.append(item(extras["cheatsheet"], "Cheat sheet"))
    for name, pages in grouped(chapters, parts):
        out.append(f'<p class="nav-label">{html.escape(name or "Chapters")}</p><ol class="nav-chapters">')
        for p in pages:
            num = f"{p.number:02d}" if p.number is not None else ""
            sections = ""
            if p is current and p.sections:
                links = "".join(
                    f'<li><a href="#{sid}">{html.escape(label)}</a></li>' for sid, label in p.sections
                )
                sections = f'<ul class="nav-sections">{links}</ul>'
            out.append(f"<li>{item(p, p.title_text, num)}{sections}</li>")
        out.append("</ol>")
    if "styleguide" in extras:
        out.append(f'<div class="nav-footer">{item(extras["styleguide"], "Style guide")}</div>')
    return "".join(out)


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
    extras = {p.out.removesuffix(".html"): p for p in pages if p.out in ("cheatsheet.html", "styleguide.html")}
    chapters = [p for p in pages if p.out.startswith("chapters/")]
    sequence = ([home] if home else []) + chapters
    parts = load_parts()
    template = (SITE / "template.html").read_text("utf-8")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    version = str(int(time.time()))  # cache-buster for asset URLs
    missing: set[str] = set()
    written: dict[str, str] = {}
    for page in pages:
        b = page.base
        body = page.body.replace(CHAPTER_CARDS_MARKER, table_of_contents(chapters, parts, b))
        body = render_builders(body, b, missing)
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
            sidebar=sidebar(chapters, parts, extras, page),
            eyebrow=eyebrow,
            title=title,
            content=body,
            pager=pager(sequence, page),
        )
        target = DIST / page.out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output, "utf-8")
        written[page.out] = output

    copy_assets(component_files)
    return len(pages), missing, broken_links(written)


def broken_links(written: dict[str, str]) -> list[str]:
    """Internal links (and #anchors) that point nowhere."""
    ids = {out: set(re.findall(r'\bid="([^"]+)"', text)) for out, text in written.items()}
    problems = []
    for out, text in written.items():
        for href in HREF.findall(text):
            if re.match(r"[a-z][a-z0-9+.-]*:|//", href):
                continue  # external
            path, _, anchor = html.unescape(href).partition("#")
            target = posixpath.normpath(posixpath.join(posixpath.dirname(out), path)) if path else out
            if target in written:
                if anchor and anchor not in ids[target]:
                    problems.append(f"{out}: #{anchor} not found in {target}")
            elif not (DIST / target).exists():
                problems.append(f"{out}: {href} does not exist")
    return sorted(set(problems))


def main() -> None:
    parser = argparse.ArgumentParser(prog="uv run site", description="Build the website into dist/.")
    parser.add_argument("--strict", action="store_true", help="fail if any [[word]] has no audio file or any link is broken")
    args = parser.parse_args()

    count, missing, broken = build()
    print(f"Built {count} pages into dist/")
    if broken:
        print(f"{len(broken)} broken links:")
        for problem in broken:
            print(f"  {problem}")
        if args.strict:
            sys.exit("error: --strict build with broken links")
    if missing:
        print(f"{len(missing)} words have no audio yet (they show as dimmed on the site).")
        if args.strict:
            for word in sorted(missing):
                print(f"  missing audio: {word}")
            sys.exit("error: --strict build with missing audio")


if __name__ == "__main__":
    main()
