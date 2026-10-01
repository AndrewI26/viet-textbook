"""Build everything once into dist/: audio clips, then the Anki deck, then the website.

Usage: uv run build
"""

from . import anki, audio, site
from .common import CARDS


def main() -> None:
    audio.generate(audio.DEFAULT_VOICE, force=set(), prune=False)
    if CARDS.exists() and any(CARDS.glob("*.yaml")):
        anki.main()
    else:
        print("No cards yet, skipping the Anki deck.")
    site.main()


if __name__ == "__main__":
    main()
