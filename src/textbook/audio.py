"""Generate pronunciation audio into audio/ with VieNeu-TTS (a Southern voice).

Usage:
  uv run audio                         make clips for words that don't have one yet
  uv run audio --force "má" --force "ma"   remake specific clips
  uv run audio --all                   remake every clip (e.g. after changing the voice)
  uv run audio --prune                 also delete clips no page or card uses any more
  uv run audio --voice "Thục Đoan"     use another voice for the clips made in this run
  uv run audio --list-voices           show the Southern voices
  uv run audio --compare               make dist/voice-test.html to compare Southern voices

A real recording in recordings/ (named by the exact text, e.g. "má.mp3") always
replaces the AI clip for that word.
"""

import argparse
import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from .common import AUDIO, DIST, RECORDINGS, SITE, audio_filename, collect_texts, normalize

DEFAULT_VOICE = "Kim Thanh"
MODELS = Path.home() / ".cache" / "viet-textbook" / "models"
RECORDING_TYPES = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".aiff"}

# Words used by --compare: the six tones, Southern sound changes, and a few phrases.
COMPARE_SETS = {
    "Tones": ["ma", "má", "mà", "mả", "mã", "mạ"],
    "Southern sounds": ["vui", "dạ", "gì", "không", "bạn", "anh", "Việt"],
    "Phrases": ["xin chào", "cảm ơn", "Tôi tên là Lan.", "Rất vui được gặp chị."],
}


# ---------- Model ----------


def load_tts():
    """Load VieNeu-TTS v3 Turbo (CPU, ONNX).

    VieNeu normally reads its model files from the Hugging Face cache, where each
    file is a symlink into a different shared folder. Newer ONNX Runtime versions
    refuse to load weights from outside the model's own folder, so we download the
    files as real files into one folder per model instead.
    """
    import logging

    from huggingface_hub import hf_hub_download
    from huggingface_hub.utils import logging as hf_logging
    from vieneu import Vieneu
    from vieneu._v3_turbo_engine import onnx_runtime_lite

    def fetch(repo: str, files: list[str], subfolder: str | None) -> Path:
        target = MODELS / repo.replace("/", "--")
        last = None
        for name in files:
            try:
                last = hf_hub_download(repo, name, subfolder=subfolder or None, local_dir=target)
            except Exception:
                if name.endswith(".json"):
                    continue  # optional metadata
                raise
        return Path(last).parent

    onnx_runtime_lite.OnnxV3LiteEngine._fetch = staticmethod(fetch)
    logging.getLogger("vieneu").setLevel(logging.WARNING)
    hf_logging.set_verbosity_error()
    first_run = not MODELS.exists()
    print("Downloading the VieNeu voice model (~540 MB, first run only)…" if first_run else "Loading the voice model…")
    return Vieneu()


def southern_voices(tts) -> list[str]:
    """Preset voices with a Southern accent. Descriptions read "Nữ · Nam · …" (gender · region · style)."""

    def region(v: dict) -> str:
        parts = v.get("description", "").split(" · ")
        return v.get("region") or (parts[1] if len(parts) > 1 else "")

    return [name for name, v in tts._preset_voices.items() if region(v) == "Nam"]


# ---------- Audio processing ----------


def tidy(samples: np.ndarray, rate: int) -> np.ndarray:
    """Trim silence, even out loudness, and pad the ends slightly."""
    samples = np.asarray(samples, dtype=np.float32)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    loud = np.flatnonzero(np.abs(samples) > 10 ** (-45 / 20))
    if loud.size:
        keep = int(0.04 * rate)
        samples = samples[max(loud[0] - keep, 0) : loud[-1] + keep]
    rms = float(np.sqrt(np.mean(samples**2))) or 1e-9
    peak = float(np.max(np.abs(samples))) or 1e-9
    gain = min(10 ** (-18 / 20) / rms, 10 ** (-1 / 20) / peak)  # ~-18 dBFS RMS, peaks under -1 dB
    samples = samples * gain
    lead, tail = np.zeros(int(0.05 * rate), np.float32), np.zeros(int(0.1 * rate), np.float32)
    return np.concatenate([lead, samples, tail])


def write_mp3(samples: np.ndarray, rate: int, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "clip.wav"
        sf.write(wav, tidy(samples, rate), rate)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
             "-ac", "1", "-codec:a", "libmp3lame", "-b:a", "64k", str(out)],
            check=True,
        )


def read_recording(path: Path) -> tuple[np.ndarray, int]:
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "rec.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ac", "1", str(wav)],
            check=True,
        )
        samples, rate = sf.read(wav, dtype="float32")
    return samples, rate


# ---------- Commands ----------


def generate(voice: str, force: set[str], prune: bool, remake_all: bool = False) -> None:
    texts = {}
    for text in collect_texts():
        texts.setdefault(audio_filename(text), text)  # same file for "Má" and "má"
    AUDIO.mkdir(exist_ok=True)

    recordings = {}
    if RECORDINGS.exists():
        for path in RECORDINGS.iterdir():
            if path.suffix.lower() in RECORDING_TYPES:
                recordings[audio_filename(path.stem)] = path

    forced = {audio_filename(t) for t in force}
    todo = []
    used_recordings = 0
    for filename, text in sorted(texts.items(), key=lambda item: item[1].lower()):
        out = AUDIO / filename
        recording = recordings.get(filename)
        if recording:
            if filename in forced or not out.exists() or recording.stat().st_mtime > out.stat().st_mtime:
                write_mp3(*read_recording(recording), out)
                used_recordings += 1
            continue
        if remake_all or filename in forced or not out.exists():
            todo.append((filename, text))

    if todo:
        tts = load_tts()
        if voice not in tts._preset_voices:
            sys.exit(f"Unknown voice {voice!r}. Try: {', '.join(southern_voices(tts))}")
        for i, (filename, text) in enumerate(todo, 1):
            print(f"  [{i}/{len(todo)}] {text}")
            samples = tts.infer(text, voice=voice)
            write_mp3(samples, tts.sample_rate, AUDIO / filename)

    pruned = 0
    if prune:
        for clip in AUDIO.glob("*.mp3"):
            if clip.name not in texts:
                clip.unlink()
                pruned += 1
    unused = sum(1 for clip in AUDIO.glob("*.mp3") if clip.name not in texts)

    print(
        f"Audio: {len(texts)} words, {len(todo)} generated with {voice}, "
        f"{used_recordings} from recordings/"
        + (f", {pruned} unused clips deleted" if prune else "")
    )
    if unused:
        print(f"{unused} clips in audio/ are no longer used (run with --prune to delete them).")
    if todo or used_recordings:
        print("Run `uv run site` to rebuild the pages with the new audio.")


def compare(voices: list[str]) -> None:
    """Make dist/voice-test.html: the same words in several voices, side by side."""
    from .site import SPEAKER_ICON, fill

    tts = load_tts()
    voices = voices or southern_voices(tts)
    out_dir = DIST / "voice-test"
    out_dir.mkdir(parents=True, exist_ok=True)

    def button(text: str, src: str) -> str:
        return (
            f'<button type="button" class="say" data-src="{src}" '
            f'aria-label="Play pronunciation: {html.escape(text)}">'
            f'<span class="say-text">{html.escape(text)}</span>'
            f'<span class="say-icon" aria-hidden="true">{SPEAKER_ICON}</span></button>'
        )

    sections = []
    for voice in voices:
        meta = tts._preset_voices[voice]
        gender = "female" if meta.get("gender") == "female" else "male"
        slug = normalize(voice).lower().replace(" ", "-")
        print(f"{voice} ({gender})")
        blocks = []
        for title, words in COMPARE_SETS.items():
            buttons = []
            for text in words:
                src = f"voice-test/{slug}/{audio_filename(text)}"
                write_mp3(tts.infer(text, voice=voice), tts.sample_rate, DIST / src)
                buttons.append(button(text, src))
            tag = "tone-drill"
            labels = ' labels="ngang, sắc, huyền, hỏi, ngã, nặng"' if title == "Tones" else ""
            blocks.append(f"<h3>{title}</h3><{tag}{labels}>{' '.join(buttons)}</{tag}>")
        sections.append(
            f'<h2 id="{slug}">{html.escape(voice)}</h2>'
            f'<p class="caption">{gender} · <code>uv run audio --voice "{html.escape(voice)}"</code></p>'
            + "".join(blocks)
        )

    intro = (
        "<p class=\"lead\">The same words in each Southern voice. Use “Play all” on the tones, "
        "and listen for the Southern sounds: <em>v</em>, <em>d</em> and <em>gi</em> said like "
        "English “y”, and <em>-n</em> said like <em>-ng</em>.</p>"
    )
    sidebar = '<a class="nav-item" href="index.html">Home</a><p class="nav-label">Voices</p><ol class="nav-chapters">'
    sidebar += "".join(
        f'<li><a class="nav-item" href="#{normalize(v).lower().replace(" ", "-")}">{html.escape(v)}</a></li>'
        for v in voices
    )
    sidebar += "</ol>"
    components = sorted((SITE / "components").glob("*.js"))
    page = fill(
        (SITE / "template.html").read_text("utf-8"),
        base="",
        v="voice-test",
        doc_title="Voice test",
        site_name="Tiếng Việt",
        component_scripts="\n".join(f'<script src="assets/components/{f.name}" defer></script>' for f in components),
        sidebar=sidebar,
        eyebrow='<p class="eyebrow">Audio</p>',
        title="Pick a voice",
        content=intro + "".join(sections),
    )
    (DIST / "voice-test.html").write_text(page, "utf-8")
    print("Open http://localhost:8000/voice-test.html (it's removed by the next `uv run site`).")


def main() -> None:
    parser = argparse.ArgumentParser(prog="uv run audio", description="Generate pronunciation audio.")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"voice to use (default: {DEFAULT_VOICE})")
    parser.add_argument("--force", action="append", default=[], metavar="TEXT", help="remake this clip (repeatable)")
    parser.add_argument("--all", action="store_true", help="remake every clip (e.g. after changing the voice)")
    parser.add_argument("--prune", action="store_true", help="delete clips that nothing uses any more")
    parser.add_argument("--list-voices", action="store_true", help="list the Southern voices")
    parser.add_argument("--compare", nargs="*", metavar="VOICE", help="build dist/voice-test.html (all Southern voices by default)")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg is required: brew install ffmpeg")

    if args.list_voices:
        tts = load_tts()
        for name in southern_voices(tts):
            v = tts._preset_voices[name]
            print(f"  {name:<12} {v.get('gender', '')}")
    elif args.compare is not None:
        if not (DIST / "index.html").exists():
            sys.exit("Build the site first: uv run site")
        compare(args.compare)
    else:
        generate(args.voice, set(args.force), args.prune, remake_all=args.all)


if __name__ == "__main__":
    main()
