"""Southern tone analysis for audio clips.

A Python copy of the pitch tracking and tone rules in site/components/say-it.js,
so `uv run audio` judges clips exactly the way the in-browser tone checker
judges learners. If you change the rules in one place, change them in both.
"""

import unicodedata

import numpy as np
from scipy.signal import resample_poly

RATE = 16000
TONE_MARKS = {"́": "sac", "̀": "huyen", "̉": "hoi", "̃": "nga", "̣": "nang"}
NAMES = {"ngang": "ngang", "sac": "sắc", "huyen": "huyền", "hoi": "hỏi", "nga": "ngã", "nang": "nặng"}

# Southern tone shapes (semitones relative to the speaker's ngang level), for scoring
# how close a near miss is. Hỏi and ngã share one shape in the South.
SHAPES = {
    "ngang": [(0, 0.2), (0.55, 0.3), (1, -1.2)],
    "sac": [(0, 0), (0.45, 0.2), (1, 6)],
    "huyen": [(0, -1), (0.6, -3.9), (1, -4.2)],
    "hoi": [(0, -1.5), (0.5, -3.4), (1, 3.5)],
    "nang": [(0, 0), (0.25, -0.5), (0.6, -3.6), (1, -1)],
}


def tone_of(word: str) -> str:
    """The tone a word is written with: ngang, sac, huyen, hoi, nga or nang."""
    for ch in unicodedata.normalize("NFD", word):
        if ch in TONE_MARKS:
            return TONE_MARKS[ch]
    return "ngang"


def is_single_syllable(text: str) -> bool:
    return len(text.split()) == 1 and any(ch.isalpha() for ch in text)


def is_checked(word: str) -> bool:
    """A "stopped" syllable ends in -p, -t, -c or -ch. These can only carry sắc or nặng,
    and they're short, so their tones look different (see classify)."""
    plain = "".join(c for c in unicodedata.normalize("NFD", word.lower()) if not unicodedata.combining(c))
    return plain.replace("đ", "d").rstrip(".!?,").endswith(("p", "t", "c", "ch"))


def to_rate(samples: np.ndarray, rate: int) -> np.ndarray:
    samples = np.asarray(samples, dtype=np.float64).reshape(-1)
    return resample_poly(samples, RATE, rate) if rate != RATE else samples


# ---------- Pitch tracking (YIN), same settings as the browser ----------


def yin(samples: np.ndarray, frame=1024, hop=160, fmin=65, fmax=500, threshold=0.2):
    tau_min = RATE // fmax
    tau_max = int(np.ceil(RATE / fmin))
    width = frame - tau_max
    frames = []
    for start in range(0, len(samples) - frame + 1, hop):
        x = samples[start : start + frame]
        rms = float(np.sqrt(np.mean(x**2)))
        head = x[:width]
        diff = np.array([np.sum((head - x[tau : tau + width]) ** 2) for tau in range(1, tau_max + 1)])
        running = np.cumsum(diff)
        cmnd = np.ones(tau_max + 1)
        with np.errstate(divide="ignore", invalid="ignore"):
            cmnd[1:] = np.where(running > 0, diff * np.arange(1, tau_max + 1) / running, 1)

        best = -1
        deepest = tau_min
        tau = tau_min
        while tau <= tau_max:
            if cmnd[tau] < cmnd[deepest]:
                deepest = tau
            if cmnd[tau] < threshold:
                while tau + 1 <= tau_max and cmnd[tau + 1] < cmnd[tau]:
                    tau += 1
                best = tau
                break
            tau += 1
        if best < 0 and cmnd[deepest] < 0.35:
            best = deepest

        f0 = confidence = 0.0
        if best > 0:
            a, b = cmnd[best - 1], cmnd[best]
            c = cmnd[best + 1] if best + 1 <= tau_max else b
            denominator = 2 * (a - 2 * b + c) or 1
            shift = (a - c) / denominator
            f0 = RATE / (best + (shift if abs(shift) < 1 else 0))
            confidence = 1 - b
        frames.append((f0, confidence, rms))
    return frames


def voiced_pitch(frames) -> list[float]:
    """Pitch of the syllable in Hz: whole voiced span, octave-fixed, gaps filled low, smoothed."""
    if not frames:
        return []
    loudest = max(f[2] for f in frames) or 1e-9
    voiced = [f0 > 0 and conf > 0.6 and rms > loudest * 0.1 for f0, conf, rms in frames]
    if True not in voiced:
        return []
    first = voiced.index(True)
    last = len(voiced) - 1 - voiced[::-1].index(True)
    if last - first < 10:
        return []
    span = [frames[i][0] if voiced[i] else 0.0 for i in range(first, last + 1)]
    if sum(1 for v in span if v) < 8:
        return []

    raw = list(span)
    for i, value in enumerate(span):
        if not value:
            continue
        local = float(np.median([v for v in raw[max(0, i - 5) : i + 6] if v]))
        while span[i] > local * 1.6:
            span[i] /= 2
        while span[i] < local / 1.6:
            span[i] *= 2

    i = 0
    while i < len(span):
        if span[i]:
            i += 1
            continue
        j = i
        while not span[j]:
            j += 1
        low = min(span[i - 1], span[j])
        for k in range(i, j):
            span[k] = low
        i = j

    smooth = [float(np.median(span[max(0, i - 2) : i + 3])) for i in range(len(span))]
    return smooth[max(1, round(len(smooth) * 0.06)) :]


def pitch(samples: np.ndarray, rate: int) -> list[float]:
    return voiced_pitch(yin(to_rate(samples, rate)))


# ---------- Tone rules, same as the browser ----------


def resample(values, n=24) -> np.ndarray:
    return np.interp(np.linspace(0, len(values) - 1, n), np.arange(len(values)), values)


def measure(contour: np.ndarray) -> dict:
    n = len(contour)
    low = float(contour.min())
    start = float(contour[: int(np.ceil(n * 0.2))].mean())
    end = float(contour[int(n * 0.8) :].mean())
    return {
        "start": start,
        "end": end,
        "low": low,
        "low_at": int(contour.argmin()) / (n - 1),
        "dip": start - low,
        "rise": end - low,
        "average": float(contour.mean()),
    }


def classify(contour: np.ndarray, checked: bool = False) -> str:
    m = measure(contour)
    if checked:
        # Stopped syllables: sắc sits high and rises; nặng sits low and drops, with no rise.
        if m["average"] >= 1.5 or m["end"] - m["start"] >= 2.5:
            return "sac"
        if m["average"] <= -0.5 or m["start"] - m["end"] >= 1.5:
            return "nang"
        return "ngang"
    if m["low"] <= -1.8 and m["rise"] >= 3.5 and m["end"] >= -1:
        return "hoi"
    if m["end"] - m["start"] >= 2.5:
        return "sac"
    if m["rise"] >= 1.2 and m["dip"] >= 1.5 and 0.3 < m["low_at"] < 0.9 and m["end"] < 0.5:
        return "nang"
    if m["start"] - m["end"] >= 2.5 or m["average"] <= -2.5:
        return "huyen"
    return "ngang"


def shape_distance(contour: np.ndarray, tone: str) -> float:
    points = SHAPES["hoi" if tone == "nga" else tone]
    xs, ys = zip(*points)
    target = np.interp(np.linspace(0, 1, len(contour)), xs, ys)
    offset = float(np.clip((contour - target).mean(), -1.5, 1.5))
    return float(np.sqrt(np.mean((contour - target - offset) ** 2)))


def check(samples: np.ndarray, rate: int, baseline_hz: float, expected: str, checked: bool = False) -> tuple[bool, str, float]:
    """Does this clip sound like the expected tone? Returns (ok, heard, distance to the expected shape)."""
    hz = pitch(samples, rate)
    if not hz:
        return False, "none", float("inf")
    contour = resample(12 * np.log2(np.array(hz) / baseline_hz))
    heard = classify(contour, checked)
    target = "hoi" if expected == "nga" else expected
    return heard == target, heard, shape_distance(contour, expected)


def baseline(samples_list: list[tuple[np.ndarray, int]]) -> float:
    """A speaker's ngang level: the median pitch over some flat-tone clips."""
    values = [hz for samples, rate in samples_list for hz in pitch(samples, rate)]
    return float(np.median(values)) if values else 0.0
