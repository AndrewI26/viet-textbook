// Practice grids built from [[word]] buttons.
//
//   <tone-drill labels="ngang, sắc, huyền, hỏi, ngã, nặng">
//   [[ma]] [[má]] [[mà]] [[mả]] [[mã]] [[mạ]]
//   </tone-drill>
//
//   <minimal-pair labels="ghost, mother">
//   [[ma]] [[má]]
//   </minimal-pair>
//
//   <word-drill labels="a, ă, â">      (same grid, for vowel and consonant sets)
//   [[an]] [[ăn]] [[ân]]
//   </word-drill>
//
// "Play all" plays every word in order. "Quiz me" plays a random word and
// the reader clicks the one they heard.

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function pillButton(label, onClick) {
  const button = el("button", "btn btn-sm btn-ghost", label);
  button.type = "button";
  button.addEventListener("click", onClick);
  return button;
}

class ToneDrill extends HTMLElement {
  prompt = "Which one did you hear?";

  connectedCallback() {
    if (this.built) return;
    this.built = true;

    this.words = [...this.querySelectorAll(".say")];
    const labels = (this.getAttribute("labels") || "").split(",").map((s) => s.trim());
    const grid = el("div", "drill-grid");
    this.cells = this.words.map((word, i) => {
      const cell = el("div", "drill-cell");
      cell.append(word);
      if (labels[i]) cell.append(el("span", "drill-label", labels[i]));
      grid.append(cell);
      return cell;
    });

    this.playAllButton = pillButton("Play all", () => this.playAll());
    this.quizButton = pillButton("Quiz me", () => (this.quiz ? this.endQuiz() : this.nextQuestion()));
    this.replayButton = pillButton("Replay", () => this.quiz && Say.play(this.words[this.answer]));
    this.replayButton.hidden = true;
    this.status = el("span", "drill-status");
    const bar = el("div", "drill-bar");
    bar.append(this.playAllButton, this.quizButton, this.replayButton, this.status);
    this.replaceChildren(grid, bar);

    // Indexes of words that have audio; the quiz only asks about these.
    this.playable = this.words.flatMap((w, i) => (w.classList.contains("say--missing") ? [] : [i]));
    if (this.playable.length === 0) {
      this.playAllButton.disabled = true;
      this.quizButton.disabled = true;
      this.setStatus("Audio not generated yet");
    }

    // In quiz mode a click on a word is an answer, not a request to hear it.
    this.addEventListener("click", (event) => this.answerClick(event), true);
  }

  setStatus(text, tone = "") {
    this.status.textContent = text;
    this.status.className = `drill-status${tone ? ` is-${tone}` : ""}`;
  }

  clearMarks() {
    this.cells.forEach((c) => c.classList.remove("is-correct", "is-wrong"));
  }

  async playAll() {
    if (this.playingAll) {
      this.playingAll = false;
      Say.stop();
      return;
    }
    this.endQuiz();
    this.playingAll = true;
    this.playAllButton.textContent = "Stop";
    for (const i of this.playable) {
      if (!this.playingAll || !(await Say.play(this.words[i]))) break;
      await wait(250);
    }
    this.playingAll = false;
    this.playAllButton.textContent = "Play all";
  }

  nextQuestion() {
    this.playingAll = false;
    this.quiz = true;
    this.score ??= { right: 0, total: 0 };
    this.classList.add("is-quiz");
    this.quizButton.textContent = "End quiz";
    this.replayButton.hidden = false;
    this.clearMarks();

    let next;
    do {
      next = this.playable[Math.floor(Math.random() * this.playable.length)];
    } while (this.playable.length > 1 && next === this.answer);
    this.answer = next;
    this.answered = false;
    this.missedThisQuestion = false;
    this.setStatus(this.prompt);
    Say.play(this.words[next]);
  }

  answerClick(event) {
    if (!this.quiz) return;
    const cell = event.target.closest(".drill-cell");
    if (!cell) return;
    event.stopPropagation();
    if (this.answered) return;

    const choice = this.cells.indexOf(cell);
    if (choice === this.answer) {
      this.answered = true;
      cell.classList.add("is-correct");
      if (!this.missedThisQuestion) this.score.right += 1;
      this.score.total += 1;
      const praise = this.missedThisQuestion ? "That's the one." : "Correct!";
      this.setStatus(`${praise} ${this.score.right} of ${this.score.total} right first time`, "good");
      setTimeout(() => this.quiz && this.nextQuestion(), 1200);
    } else {
      this.missedThisQuestion = true;
      cell.classList.add("is-wrong");
      this.setStatus("Not quite. Listen again.", "bad");
      Say.play(this.words[this.answer]);
    }
  }

  endQuiz() {
    if (!this.quiz) return;
    this.quiz = false;
    this.classList.remove("is-quiz");
    this.quizButton.textContent = "Quiz me";
    this.replayButton.hidden = true;
    this.clearMarks();
    this.setStatus(this.score?.total ? `Last quiz: ${this.score.right} / ${this.score.total}` : "");
    this.score = null;
  }
}

class MinimalPair extends ToneDrill {
  prompt = "Which did you hear?";
}

class WordDrill extends ToneDrill {}

customElements.define("tone-drill", ToneDrill);
customElements.define("minimal-pair", MinimalPair);
customElements.define("word-drill", WordDrill);
