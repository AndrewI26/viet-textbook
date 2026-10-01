# Style guide

Every building block the textbook uses, on one page. Use the moon/sun button in the top-right corner to check both themes.
{: .lead }

## Colors

<div class="swatches">
<div class="swatch"><span style="background:var(--bg)"></span><code>--bg</code></div>
<div class="swatch"><span style="background:var(--surface)"></span><code>--surface</code></div>
<div class="swatch"><span style="background:var(--surface-2)"></span><code>--surface-2</code></div>
<div class="swatch"><span style="background:var(--border)"></span><code>--border</code></div>
<div class="swatch"><span style="background:var(--muted)"></span><code>--muted</code></div>
<div class="swatch"><span style="background:var(--text)"></span><code>--text</code></div>
<div class="swatch"><span style="background:var(--btn-bg)"></span><code>--btn-bg</code></div>
<div class="swatch"><span style="background:var(--south)"></span><code>--south</code></div>
<div class="swatch"><span style="background:var(--good)"></span><code>--good</code></div>
<div class="swatch"><span style="background:var(--bad)"></span><code>--bad</code></div>
</div>

## Typography

<p class="eyebrow">Eyebrow label</p>

<h1>Heading one</h1>

### Heading three

Body text is set in Inter at 16px. Vietnamese has stacked accents like *ế*, *ộ* and *ữ*, so the line height leaves room for them: Tiếng Việt có sáu dấu thanh. Here is [a link](#typography), some **bold text**, some *italic text* and a bit of `inline code`.

A lead paragraph introduces a chapter and is slightly larger and softer.
{: .lead }

<p class="caption">Captions and helper text use the muted color at 14px.</p>

> Học, học nữa, học mãi. (Study, study more, study forever.)

- Unordered list item
- Another item with a clickable word: [[cảm ơn]]
- A third item

1. First step
2. Second step
3. Third step

```
[[xin chào]]          a clickable word
[[đ :: đờ]]           shown as "đ", spoken as "đờ"
```

---

## Clickable words

Inline in a sentence: say [[xin chào]] to greet someone and [[cảm ơn]] to say thank you. Longer phrases work too: [[Tôi tên là Lan.]]

<div class="state-row">
<div class="demo-normal">[[má]]<span class="caption">Normal</span></div>
<div class="demo-hover">[[má]]<span class="caption">Hover</span></div>
<div class="demo-playing">[[má]]<span class="caption">Playing</span></div>
<div>[[má]]<span class="caption">No audio yet</span></div>
</div>

When the spoken form differs from what's shown, like a letter name: the letter [[đ :: đờ]] is called *đờ*.

## Buttons

<div class="btn-row">
<a class="btn btn-primary" href="#buttons">Start chapter 1</a>
<a class="btn btn-secondary" href="#buttons">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>
Download Anki deck
</a>
<button type="button" class="btn btn-ghost">Ghost button</button>
</div>

<div class="btn-row">
<button type="button" class="btn btn-primary btn-sm">Small primary</button>
<button type="button" class="btn btn-secondary btn-sm">Small secondary</button>
<button type="button" class="btn btn-ghost btn-sm">Small ghost</button>
<button type="button" class="btn btn-primary btn-sm" disabled>Disabled</button>
<button type="button" class="icon-btn" aria-label="Play"><svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></button>
</div>

## Callouts

<div class="tip" markdown="1">
Say each word out loud **before** you click it, then compare. Guessing first trains your ear much faster than just listening.
</div>

<div class="south" markdown="1">
In Saigon, [[v]] is said like the English *y* in "yes", so [[vui]] (happy) sounds like "yui".
</div>

<div class="warn" markdown="1">
[[mả]] and [[mã]] sound the same in the South, but they're still **spelled differently**, so learn both marks.
</div>

## Tables

| Vietnamese | Sounds like | English |
|---|---|---|
| [[xin chào]] | sin chow | hello |
| [[cảm ơn]] | gahm uhn | thank you |
| [[xin lỗi]] | sin loy | sorry |
| [[dạ]] | yah | yes (polite, Southern) |
| [[không]] | khohm | no |

| Tone | Word | Meaning |
|---|---|---|
| ngang | [[ma]] | ghost |
| sắc | [[má]] | mother |
| huyền | [[mà]] | but |
| hỏi | [[mả]] | grave |
| ngã | [[mã]] | horse |
| nặng | [[mạ]] | rice seedling |

## Cards

<div class="card-grid">
<a class="card card-link" href="#cards"><span class="eyebrow">Chapter 1</span><span class="card-title">How Vietnamese works</span><span class="card-meta">5 sections</span></a>
<a class="card card-link" href="#cards"><span class="eyebrow">Chapter 2</span><span class="card-title">Vowels</span><span class="card-meta">5 sections</span></a>
<a class="card card-link" href="#cards"><span class="eyebrow">Chapter 3</span><span class="card-title">Tones</span><span class="card-meta">5 sections</span></a>
</div>

<div class="card" markdown="1">
<span class="card-title">A plain card</span>

Cards hold grouped content without a link. No shadows: they sit on a slightly warmer surface instead.
</div>

## Dialogue

<div class="dialogue" markdown="1">
- **Lan:** [[Xin chào!]] *Hello!*
- **Minh:** [[Chào chị. Chị tên gì?]] *Hi. What's your name?*
- **Lan:** [[Tôi tên là Lan.]] *My name is Lan.*
- **Minh:** [[Rất vui được gặp chị.]] *Nice to meet you.*
</div>

## Reveal

<details markdown="1">
<summary>Show the answer</summary>

The word is **mạ**, with the *nặng* tone: low, short and heavy.
</details>

<details markdown="1">
<summary>Why are there only five tones in the South?</summary>

Southern speakers pronounce *hỏi* and *ngã* the same way, so in practice you hear five tones, not six.
</details>

## Components

### Tone drill

<tone-drill labels="ngang, sắc, huyền, hỏi, ngã, nặng">
[[ma]] [[má]] [[mà]] [[mả]] [[mã]] [[mạ]]
</tone-drill>

### Minimal pair

<minimal-pair labels="big, bowl">
[[to]] [[tô]]
</minimal-pair>

## Forms

<input class="input" type="text" placeholder="Type what you hear…" aria-label="Type what you hear">

<div class="choices" role="radiogroup" aria-label="Which tone?">
<label class="choice"><input type="radio" name="tone" checked> ngang</label>
<label class="choice"><input type="radio" name="tone"> sắc</label>
<label class="choice"><input type="radio" name="tone"> huyền</label>
<label class="choice"><input type="radio" name="tone"> hỏi / ngã</label>
<label class="choice"><input type="radio" name="tone"> nặng</label>
</div>
