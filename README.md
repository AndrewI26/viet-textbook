# viet-textbook

Open source textbook for learning Vietnamese (Southern).

A small static website where every Vietnamese word can be clicked to hear it with a Southern (Saigon) accent, plus an Anki deck with flashcards for every chapter and section. Pronunciation comes first.

## Setup

```bash
brew install uv ffmpeg
uv sync
```

The first `uv run audio` downloads the VieNeu-TTS voice model (~540 MB) into `~/.cache/viet-textbook/models`.

## Commands

| Command | What it does |
|---|---|
| `uv run dev` | Build the pages and serve them at http://localhost:8000 |
| `uv run build` | Build everything into `dist/`: audio clips, Anki deck, pages |
| `uv run site` | Rebuild only the pages (under a second); refresh the browser to see changes |
| `uv run serve` | Serve the already-built `dist/` folder |
| `uv run audio` | Generate audio for any word that doesn't have a clip yet |
| `uv run anki` | Build `anki/vietnamese-southern.apkg` from `cards/` |
| `uv run clean` | Delete `dist/` |
| `uv run docker-test` | Build the Docker image and run it at http://localhost:8080 |

Audio options: `uv run audio --force "má"` remakes one clip, `--all` remakes every clip (after changing the voice), `--voice "Kim Thanh"` picks a voice, `--prune` deletes unused clips, `--list-voices` lists the Southern voices, and `--compare` builds `dist/voice-test.html` to compare them.

## Project layout

```
chapters/      the book: one .md (or .html) file per chapter, numbered
cards/         flashcards: one .yaml file per chapter
site/          page template, home page, style guide, CSS and JS
site/components/  reusable widgets (<tone-drill>, <minimal-pair>)
audio/         generated MP3s, committed to git
recordings/    real recordings that replace the AI audio (optional)
src/textbook/  the build commands
notes/         reading notes for writing chapters
dist/          build output (not committed)
```

## Writing chapters

Chapters are Markdown files in `chapters/`, ordered by their number (`03-tones.md`). The first `#` heading is the chapter title and each `##` heading is a section in the sidebar. A chapter can be a plain `.html` file instead; the template still adds the header, sidebar and navigation.

**Clickable words:** wrap any word or phrase in double brackets.

```markdown
Say [[xin chào]] to greet someone.
The letter [[đ :: đờ]] is called "đờ".   <!-- shown :: spoken -->
```

**HTML inside Markdown** works anywhere: start the block at the beginning of a line, with blank lines around it. Add `markdown="1"` to render Markdown inside it.

```markdown
<div class="tip" markdown="1">
Say each word **before** you click it.
</div>
```

Callout classes: `tip`, `south` (Southern pronunciation note), `warn`. Dialogue: a list inside `<div class="dialogue" markdown="1">`. Show/hide answers: `<details>` with a `<summary>`. See `site/styleguide.md` (served at `/styleguide.html`) for every component.

**Components** are plain-JS custom elements in `site/components/`. The build loads every file there on every page.

```markdown
<tone-drill labels="ngang, sắc, huyền, hỏi, ngã, nặng">
[[ma]] [[má]] [[mà]] [[mả]] [[mã]] [[mạ]]
</tone-drill>

<minimal-pair labels="big, bowl">
[[to]] [[tô]]
</minimal-pair>
```

## Writing flashcards

One YAML file per chapter in `cards/`. Each section becomes an Anki subdeck, e.g. `Vietnamese (Southern)::03 Tones::3.2 The six tone marks`.

```yaml
chapter: 3
title: Tones
sections:
  - id: "3.2"
    title: The six tone marks
    cards:
      - { type: read,   vi: má, tip: "Sắc: starts mid, rises sharply" }  # see it, say it, flip to hear it
      - { type: listen, vi: mà, answer: "huyền: low, falling" }         # hear it, recall what it was
      - { type: vocab,  vi: xin chào, en: hello }                       # makes 2 cards: VI→EN and EN→VI
      - { type: basic,  front: "Which tones merge in the South?", back: "[[hỏi]] and [[ngã]]" }
```

Text can use Markdown and `[[word]]` for audio. Cards keep their identity across rebuilds, so re-importing the deck into Anki updates existing cards and keeps your review history. Give a card an `id:` if you plan to change its main text.

## Real recordings

Put a recording in `recordings/` named after the exact text, e.g. `recordings/má.m4a`, and run `uv run audio`. It replaces the AI clip for that word (any common audio format works).

## Deploying

There is one Dockerfile and no Compose file, since the site is a single static service. The image builds the Anki deck and the pages from the committed audio clips, then serves `dist/` with nginx. It never installs the voice model.

```bash
docker build -t viet-textbook .
docker run -d -p 80:80 viet-textbook
```

The Docker build fails if any `[[word]]` has no audio clip. Run `uv run audio` locally and commit the new clips.

## Credits

- Some explanations are adapted from [*Basic Vietnamese*](https://openbooks.lib.msu.edu/vietnamese/) by Tung Hoang (Michigan State University Libraries, 2023), licensed [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Pronunciation notes are re-checked against the Southern accent. Reading notes are in `notes/`.
- Audio is generated with [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) (Apache 2.0).
