// <sentence-builder>: a sentence split into swappable parts.
//
//   <sentence-builder vi="{who} tên là {name}." en="{who} name is {name}.">
//   who: Tôi = My | Anh = Your | Em = Your
//   name: Lan | Minh | Mark
//   </sentence-builder>
//
// Each line is a slot: its name, then options separated by "|", each written
// "Vietnamese = English" (or just one word when both are the same). The build
// (src/textbook/site.py) turns this into JSON and makes audio for every sentence.
//
// Click a highlighted word in the sentence to cycle it, or pick from the rows
// below. The English updates and the new sentence plays.

const SB_SPEAKER =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' +
  '<path d="M11 5 6 9H3v6h3l5 4V5z" fill="currentColor"/>' +
  '<path class="wave wave-1" d="M15.5 9a4.5 4.5 0 0 1 0 6"/>' +
  '<path class="wave wave-2" d="M18.5 6a8.5 8.5 0 0 1 0 12"/></svg>';

const tidy = (text) => text.normalize("NFC").replace(/\s+/g, " ").trim();

function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

class SentenceBuilder extends HTMLElement {
  connectedCallback() {
    if (this.built) return;
    const json = this.querySelector('script[type="application/json"]');
    if (!json) return;
    this.built = true;
    this.data = JSON.parse(json.textContent);
    this.picked = Object.fromEntries(this.data.slots.map((slot) => [slot.name, 0]));

    // The sentence, with a play button and a shuffle button.
    this.play = make("button", "say sb-play");
    this.play.type = "button";
    this.play.innerHTML = `<span class="say-icon" aria-hidden="true">${SB_SPEAKER}</span>`;
    this.sentence = make("p", "sb-sentence");
    this.english = make("p", "sb-english");
    const words = make("div", "sb-words");
    words.append(this.sentence, this.english);
    const top = make("div", "sb-top");
    top.append(this.play, words);

    // One row of options per slot.
    const rows = make("div", "sb-rows");
    this.buttons = {};
    for (const slot of this.data.slots) {
      const row = make("div", "sb-row");
      row.append(make("span", "sb-label", slot.name));
      this.buttons[slot.name] = slot.options.map((option, index) => {
        const button = make("button", "sb-option");
        button.type = "button";
        button.append(make("span", "", option.vi));
        if (option.en !== option.vi) button.append(make("small", "", option.en));
        button.addEventListener("click", () => this.pick(slot.name, index));
        row.append(button);
        return button;
      });
      row.addEventListener("mouseenter", () => this.highlight(slot.name));
      row.addEventListener("mouseleave", () => this.highlight(null));
      rows.append(row);
    }

    const shuffle = make("button", "btn btn-sm btn-ghost sb-shuffle", "Shuffle");
    shuffle.type = "button";
    shuffle.addEventListener("click", () => this.shuffle());
    rows.append(shuffle);

    this.replaceChildren(top, rows);
    this.render();
  }

  fill(template, field) {
    return tidy(template.replace(/\{(\w+)\}/g, (match, name) => {
      const slot = this.data.slots.find((s) => s.name === name);
      return slot ? slot.options[this.picked[name]][field] : match;
    }));
  }

  render() {
    // The sentence: fixed words as text, slots as clickable chips.
    this.sentence.replaceChildren();
    for (const part of this.data.vi.split(/(\{\w+\})/)) {
      const ref = part.match(/^\{(\w+)\}$/);
      const slot = ref && this.data.slots.find((s) => s.name === ref[1]);
      if (!slot) {
        if (part) this.sentence.append(part);
        continue;
      }
      const chip = make("button", "sb-chip", slot.options[this.picked[slot.name]].vi);
      chip.type = "button";
      chip.dataset.slot = slot.name;
      chip.title = `${slot.name}: click to change`;
      chip.addEventListener("click", () => this.pick(slot.name, (this.picked[slot.name] + 1) % slot.options.length));
      this.sentence.append(chip);
    }
    this.english.textContent = this.fill(this.data.en, "en");

    for (const [name, buttons] of Object.entries(this.buttons)) {
      buttons.forEach((b, i) => b.setAttribute("aria-pressed", String(i === this.picked[name])));
    }

    const vi = this.fill(this.data.vi, "vi");
    const src = this.data.audio[vi];
    this.play.dataset.src = src ?? "";
    this.play.classList.toggle("say--missing", !src);
    this.play.setAttribute("aria-label", `Play: ${vi}`);
  }

  pick(name, index) {
    this.picked[name] = index;
    this.render();
    this.highlight(name);
    Say.play(this.play);
  }

  shuffle() {
    for (const slot of this.data.slots) {
      this.picked[slot.name] = Math.floor(Math.random() * slot.options.length);
    }
    this.render();
    Say.play(this.play);
  }

  highlight(name) {
    this.sentence.querySelectorAll(".sb-chip").forEach((chip) => chip.classList.toggle("is-hot", chip.dataset.slot === name));
  }
}

customElements.define("sentence-builder", SentenceBuilder);
