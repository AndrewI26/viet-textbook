# Cheat sheet

Southern Vietnamese as formulas. Each card states one rule precisely, gives an example you can click to hear, and links to the chapter that explains it.
{: .lead }

**Notation.** $\oplus$ joins words, $\varnothing$ means "nothing", and $S(x)$ is how the South pronounces a spelling $x$. Pitch is measured in semitones relative to your own normal (*ngang*) voice.

## Sounds

<section class="sheet-card" markdown="1">

### The syllable is a 4-tuple

$$\sigma = (C_1,\ V,\ C_2,\ T)$$

$$C_1 \in \{\varnothing\} \;\cup\; \{\text{b, c, d, đ, g, h, k, l, m, n, p, r, s, t, v, x}\}$$

$$\qquad \cup\; \{\text{ch, gh, gi, kh, ng, ngh, nh, ph, qu, th, tr}\}$$

$$C_2 \in \{\varnothing\} \;\cup\; \underbrace{\{\text{p, t, c, ch}\}}_{\text{stop}} \;\cup\; \underbrace{\{\text{m, n, ng, nh}\}}_{\text{hum}} \;\cup\; \underbrace{\{\text{i, y, o, u}\}}_{\text{glide}}$$

$$T \in \{\text{ngang, sắc, huyền, hỏi, ngã, nặng}\}$$

$V$ and $T$ always exist; $C_1$ and $C_2$ may be $\varnothing$. For example $\text{tiếng} = (\text{t}, \text{iê}, \text{ng}, \text{sắc})$ and $\text{ăn} = (\varnothing, \text{ă}, \text{n}, \text{ngang})$. Listen: [[tiếng]], [[ăn]].

<p class="chips"><a class="chip" href="chapters/01-how-vietnamese-works.html#1-3-anatomy-of-a-syllable">1.3 Anatomy of a syllable</a><a class="chip" href="chapters/05-final-sounds.html#5-5-how-to-read-any-word">5.5 How to read any word</a></p>
</section>

<section class="sheet-card" markdown="1">

### The stop constraint

$$C_2 \in \{\text{p}, \text{t}, \text{c}, \text{ch}\} \;\Longrightarrow\; T \in \{\text{sắc}, \text{nặng}\}$$

So a stopped syllable is a quick rise or a quick low drop: [[hát]] (to sing) vs [[hạt]] (seed). Something like *hàt* can't exist.

<p class="chips"><a class="chip" href="chapters/03-tones.html#3-3-each-tone-step-by-step">3.3 Each tone</a><a class="chip" href="chapters/05-final-sounds.html#5-1-endings-that-stop-p-t-c-ch">5.1 Endings that stop</a></p>
</section>

<section class="sheet-card" markdown="1">

### Tone marks, and the Southern quotient

$$\tau:\ \text{a} \mapsto \text{ngang},\quad \text{á} \mapsto \text{sắc},\quad \text{à} \mapsto \text{huyền},\quad \text{ả} \mapsto \text{hỏi},\quad \text{ã} \mapsto \text{ngã},\quad \text{ạ} \mapsto \text{nặng}$$

$$\text{South: } \text{hỏi} \sim \text{ngã} \quad\Longrightarrow\quad \lvert T/{\sim} \rvert = 5$$

Six spellings, five sounds: [[ma]] [[má]] [[mà]] [[mả]] [[mã]] [[mạ]]. In the South, the 4th and 5th sound the same.

<p class="chips"><a class="chip" href="chapters/01-how-vietnamese-works.html#1-4-two-kinds-of-marks">1.4 Two kinds of marks</a><a class="chip" href="chapters/03-tones.html#3-2-the-five-southern-tones">3.2 The five Southern tones</a></p>
</section>

<section class="sheet-card" markdown="1">

### Tones as pitch functions

Let $f\colon [0,1] \to \mathbb{R}$ be your pitch across the syllable. The Southern tones are piecewise-linear shapes through these points (measured from eight Southern voices):

$$f_{\text{ngang}}: (0, 0.2) \to (0.55, 0.3) \to (1, {{-1.2}}) \qquad \text{level}$$

$$f_{\text{sắc}}: (0, 0) \to (0.45, 0.2) \to (1, {{+6}}) \qquad \text{level, then rises}$$

$$f_{\text{huyền}}: (0, {{-1}}) \to (0.6, {{-3.9}}) \to (1, {{-4.2}}) \qquad \text{falls}$$

$$f_{\text{hỏi}} = f_{\text{ngã}}: (0, {{-1.5}}) \to (0.5, {{-3.4}}) \to (1, {{+3.5}}) \qquad \text{dips, then rises high}$$

$$f_{\text{nặng}}: (0, 0) \to (0.6, {{-3.6}}) \to (1, {{-1}}) \qquad \text{dips, rises a little}$$

The tone checker classifies your recording with these rules, checked top to bottom. Here $s = \bar f\,\big|_{[0,\,0.2]}$, $e = \bar f\,\big|_{[0.8,\,1]}$, $m = \min f$ and $t_m = \operatorname{argmin} f$:

$$\text{tone}(f) = \begin{cases} \text{hỏi} \equiv \text{ngã} & m \le {{-1.8}},\ \ e - m \ge 3.5,\ \ e \ge {{-1}} \\ \text{sắc} & e - s \ge 2.5 \\ \text{nặng} & e - m \ge 1.2,\ \ s - m \ge 1.5,\ \ t_m \in (0.3, 0.9),\ \ e < 0.5 \\ \text{huyền} & s - e \ge 2.5 \ \text{ or } \ \bar f \le {{-2.5}} \\ \text{ngang} & \text{otherwise} \end{cases}$$

For stopped syllables only two tones are possible, so the rule is simpler:

$$\text{tone}(f) = \begin{cases} \text{sắc} & \bar f \ge 1.5 \ \text{ or } \ e - s \ge 2.5 \\ \text{nặng} & \bar f \le {{-0.5}} \ \text{ or } \ s - e \ge 1.5 \end{cases}$$

<p class="chips"><a class="chip" href="chapters/03-tones.html#3-2-the-five-southern-tones">3.2 Tone chart</a><a class="chip" href="chapters/03-tones.html#3-3-each-tone-step-by-step">3.3 Try the tone checker</a></p>
</section>

<section class="sheet-card" markdown="1">

### Where the tone mark goes

Let $V = v_1 v_2 \ldots v_k$ be the vowels, with the *u* of *qu* and the *i* of *gi* removed. The first rule that applies wins:

$$\text{place}(V, C_2) = \begin{cases} v_1 & k = 1 \\ \text{the vowel in } \{\text{ă, â, ê, ô, ơ, ư}\} & \text{if } V \text{ has one (in ươ, the ơ)} \\ v_{k-1} & C_2 = \varnothing \\ v_k & C_2 \neq \varnothing \end{cases}$$

Examples: $\text{mía} \to v_1$, $\text{người} \to \text{ơ}$, $\text{toán} \to v_k$, $\text{ngoài} \to v_{k-1}$, $\text{quả} \to \text{a}$.

<p class="chips"><a class="chip" href="chapters/03-tones.html#3-4-where-the-mark-goes">3.4 Where the mark goes</a></p>
</section>

<section class="sheet-card" markdown="1">

### Vowels as coordinates

Every vowel is a point in (height × tongue position × lip rounding):

| | front (lips spread) | central | back (lips spread) | back (lips rounded) |
|---|---|---|---|---|
| close | [[i]] / y | | [[ư]] | [[u]] |
| mid | [[ê]] | [[ơ]], â | | [[ô]] |
| open-mid | [[e]] | | | [[o]] |
| open | | [[a]], ă | | |

Two short versions and one rounding switch:

$$\text{short}(\text{a}) = \text{ă}, \qquad \text{short}(\text{ơ}) = \text{â}, \qquad \text{ư} = \text{u} - \text{rounding}$$

<p class="chips"><a class="chip" href="chapters/02-vowels.html#2-1-the-single-vowels">2.1 The single vowels</a><a class="chip" href="chapters/02-vowels.html#2-2-vowels-that-are-easy-to-mix-up">2.2 Easy to mix up</a></p>
</section>

<section class="sheet-card" markdown="1">

### One sound, several spellings

The glide's spelling is a function of its neighbours:

$$\text{spell}(\text{ee-uh}) = \begin{cases} \text{yê} & C_1 = \varnothing \ \text{(or after the glide u)} \\ \text{ia} & C_2 = \varnothing \\ \text{iê} & \text{otherwise} \end{cases}$$

$$\text{spell}(\text{oo-uh}) = \begin{cases} \text{ua} & C_2 = \varnothing \\ \text{uô} & C_2 \neq \varnothing \end{cases} \qquad \text{spell}(\text{ư-uh}) = \begin{cases} \text{ưa} & C_2 = \varnothing \\ \text{ươ} & C_2 \neq \varnothing \end{cases}$$

Examples: [[yêu]], [[mía]], [[tiền]] · [[mua]], [[muốn]] · [[mưa]], [[nước]].

<p class="chips"><a class="chip" href="chapters/02-vowels.html#2-4-one-sound-two-spellings">2.4 One sound, two spellings</a></p>
</section>

<section class="sheet-card" markdown="1">

### Consonant spelling

With $v$ the first vowel after the consonant, and $F = \{\text{i}, \text{e}, \text{ê}\}$:

$$\text{spell}(/k/) = \begin{cases} \text{k} & v \in F \cup \{\text{y}\} \\ \text{qu} & \text{before a w-glide} \\ \text{c} & \text{otherwise} \end{cases}$$

$$\text{spell}(/g/) = \begin{cases} \text{gh} & v \in F \\ \text{g} & \text{otherwise} \end{cases} \qquad \text{spell}(/ŋ/) = \begin{cases} \text{ngh} & v \in F \\ \text{ng} & \text{otherwise} \end{cases}$$

Examples: [[kem]], [[quá]], [[cá]] · [[ghế]], [[gà]] · [[nghe]], [[ngủ]].

<p class="chips"><a class="chip" href="chapters/04-consonants.html#4-4-spelling-rules">4.4 Spelling rules</a></p>
</section>

<section class="sheet-card" markdown="1">

### Consonants as a matrix

Rows are how the air moves; columns are where your mouth closes.

| | lips | tongue tip | tongue middle | back of tongue |
|---|---|---|---|---|
| stop, no puff | b, p | t, đ | ch, tr | c / k / q |
| stop + puff | | th | | |
| hum (nasal) | m | n | nh | ng / ngh |
| hiss (fricative) | ph, v | x, s | | kh, g / gh |

$$\text{th} = \text{t} + \text{puff of air} \qquad (\text{stop} \ \text{vs} \ \text{top})$$

Listen: [[tôi]] vs [[thôi]] · [[cá]] vs [[khá]].

<p class="chips"><a class="chip" href="chapters/04-consonants.html#4-2-sounds-that-work-differently">4.2 Sounds that work differently</a></p>
</section>

<section class="sheet-card" markdown="1">

### Endings: a bijection

Stops and hums pair up by mouth position:

$$\varphi\colon \{\text{p}, \text{t}, \text{c}, \text{ch}\} \to \{\text{m}, \text{n}, \text{ng}, \text{nh}\}, \qquad \text{p} \mapsto \text{m},\ \ \text{t} \mapsto \text{n},\ \ \text{c} \mapsto \text{ng},\ \ \text{ch} \mapsto \text{nh}$$

$$V \in \{\text{o}, \text{ô}, \text{u}\} \ \wedge\ C_2 \in \{\text{c}, \text{ng}\} \;\Longrightarrow\; \text{the lips close}$$

Listen: [[gặp]], [[gặt]] · [[không]], [[học]].

<p class="chips"><a class="chip" href="chapters/05-final-sounds.html#5-1-endings-that-stop-p-t-c-ch">5.1 Stops</a><a class="chip" href="chapters/05-final-sounds.html#5-2-endings-that-hum-m-n-ng-nh">5.2 Hums</a><a class="chip" href="chapters/05-final-sounds.html#5-4-endings-that-close-your-lips">5.4 Lips</a></p>
</section>

<section class="sheet-card" markdown="1">

### The Southern accent as a map

$S$ sends a spelling to its Southern sound:

$$S(\text{d}) = S(\text{gi}) = S(\text{v}) = \text{“y”}, \qquad S(\text{qu}) = \text{“w”}$$

$$S(\text{-n}) = \text{-ng}, \quad S(\text{-t}) = \text{-c}, \quad S(\text{-nh}) = \text{-n}, \quad S(\text{-ch}) = \text{-t} \qquad (\text{except after i})$$

$$S(\text{ươi}) = \text{ưi}, \quad S(\text{uôi}) = \text{ui}, \quad S(\text{iêu}) = \text{iu}, \quad S(\text{ươu}) = \text{ưu} \qquad (\text{casual speech})$$

$$S(\text{hỏi}) = S(\text{ngã})$$

**Corollary:** $S$ is not injective. $S(\text{mắt}) = S(\text{mắc})$, so *eye* and *expensive* sound alike; context is the inverse. Example: $S(\text{Việt}) = \text{“Yiệc”}$.

Listen: [[mắt]], [[mắc]], [[Việt]].

<p class="chips"><a class="chip" href="chapters/04-consonants.html#4-3-southern-consonants">4.3 Southern consonants</a><a class="chip" href="chapters/05-final-sounds.html#5-3-southern-endings">5.3 Southern endings</a><a class="chip" href="chapters/02-vowels.html#2-5-three-vowels-together">2.5 Three vowels</a></p>
</section>

## Words and sentences

<section class="sheet-card" markdown="1">

### Pronouns are a function of relative age

Let $\Delta = \text{their age} - \text{your age}$ and $g$ their gender. Then "you" is:

$$\text{you}(\Delta, g) = \begin{cases} \text{em} & \Delta < 0 \\ \text{bạn} & \Delta \approx 0 \\ \text{anh} \ (g = \text{m}), \ \ \text{chị} \ (g = \text{f}) & \text{a few years older} \\ \text{chú} \ (\text{m}), \ \ \text{cô} \ (\text{f}) & \text{your parents' generation} \\ \text{ông} \ (\text{m}), \ \ \text{bà} \ (\text{f}) & \text{your grandparents' generation} \end{cases}$$

and "I" is determined by "you":

$$\text{I} = \begin{cases} \text{em} & \text{you} \in \{\text{anh}, \text{chị}\} \\ \text{anh} \mid \text{chị} & \text{you} = \text{em} \\ \text{con} & \text{you} \in \{\text{cô}, \text{chú}, \text{ông}, \text{bà}\} \\ \text{tôi} \mid \text{tui} \mid \text{mình} & \text{you} = \text{bạn} \end{cases}$$

Default for an adult you're unsure about: $(\text{you}, \text{I}) = (\text{anh} \mid \text{chị},\ \text{em})$.
Third person: $\text{he/she} = \text{you} \oplus \text{ấy}$, and in the South $\text{anh} \oplus \text{ấy} \to \text{ảnh}$ (the two words merge and take *hỏi*).

<p class="chips"><a class="chip" href="chapters/06-greetings.html#6-2-whos-who-words-for-i-and-you">6.2 Who's who</a></p>
</section>

<section class="sheet-card" markdown="1">

### Sentence formulas

$$\text{greet}(y) = \text{chào} \oplus y, \qquad \text{greet}_{\text{polite}}(y) = \text{I} \oplus \text{chào} \oplus y \oplus \text{ạ}, \qquad \text{call}(y) = y \oplus \text{ơi}$$

$$A \oplus \text{là} \oplus B \quad (\text{“A is B”, only for nouns})$$

Questions keep the word order and put the unknown where the answer goes. It's like solving for $x$:

$$\text{Anh tên } x\,? \quad x \in \{\text{gì}, \text{nào}, \text{bao nhiêu}, \text{mấy}\} \qquad \longrightarrow \qquad \text{Anh tên Mark.}$$

Listen: [[Chào anh!]] · [[Em chào chị ạ.]] · [[Cô ơi!]] · [[Anh tên gì?]]

<p class="chips"><a class="chip" href="chapters/06-greetings.html#6-1-saying-hello">6.1 Saying hello</a><a class="chip" href="chapters/06-greetings.html#6-3-introducing-yourself">6.3 Introductions</a><a class="chip" href="chapters/06-greetings.html#6-4-asking-someones-name">6.4 Questions</a></p>
</section>

<section class="sheet-card" markdown="1">

### Numbers

With the digit words

$$d\colon (0, 1, 2, 3, 4) \mapsto (\text{không, một, hai, ba, bốn})$$

$$\phantom{d\colon} (5, 6, 7, 8, 9) \mapsto (\text{năm, sáu, bảy, tám, chín})$$

write $n = 10a + b$ for $0 \le n \le 99$:

$$N(10a + b) = \begin{cases} d(b) & a = 0 \\ \text{mười} \oplus d_1(b) & a = 1 \\ d(a) \oplus \text{mươi} \oplus d_2(b) & a \ge 2 \end{cases}$$

where the ones digit changes slightly:

$$d_1(b) = \begin{cases} \varnothing & b = 0 \\ \text{lăm} & b = 5 \\ d(b) & \text{otherwise} \end{cases} \qquad d_2(b) = \begin{cases} \varnothing & b = 0 \\ \text{mốt} & b = 1 \\ \text{tư} & b = 4 \\ \text{lăm} & b = 5 \\ d(b) & \text{otherwise} \end{cases}$$

Hundreds and up:

$$N(100h + r) = d(h) \oplus \text{trăm} \oplus \begin{cases} \varnothing & r = 0 \\ \text{lẻ} \oplus d(r) & 0 < r < 10 \\ N(r) & r \ge 10 \end{cases}$$

$$N(10^3 k) = N(k) \oplus \text{ngàn}, \qquad N(10^6 k) = N(k) \oplus \text{triệu}$$

$$N(45) = \underbrace{\text{bốn}}_{4} \oplus \underbrace{\text{mươi}}_{\times 10} \oplus \underbrace{\text{lăm}}_{5} \qquad N(105) = \text{một} \oplus \text{trăm} \oplus \text{lẻ} \oplus \text{năm}$$

**Southern shortcuts:** $d(a) \oplus \text{mươi} \to d(a) \oplus \text{chục}$, $\ \text{hai mươi} \to \text{hăm}$, $\ \text{ba mươi} \to \text{băm}$. At the market a price $p = 10a + b$ thousand is said as just $d(a) \oplus d_1(b)$: $45{,}000 \to \text{bốn lăm}$.

Listen: [[bốn mươi lăm]] · [[một trăm lẻ năm]] · [[hăm lăm ngàn]] · [[bốn lăm]]

<p class="chips"><a class="chip" href="chapters/07-numbers.html#7-2-eleven-to-nineteen">7.2 11–19</a><a class="chip" href="chapters/07-numbers.html#7-3-twenty-to-ninety-nine">7.3 20–99</a><a class="chip" href="chapters/07-numbers.html#7-4-hundreds-thousands-millions">7.4 Big numbers</a><a class="chip" href="chapters/07-numbers.html#7-6-how-much-is-it">7.6 Prices</a></p>
</section>
