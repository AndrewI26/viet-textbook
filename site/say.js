// Click-to-play pronunciation for every <button class="say"> on the page.
//
// For page scripts and components:
//   Say.play(button) -> Promise<boolean>  plays one word, resolves true when it finishes
//   Say.stop()                            stops whatever is playing
//   playAudio(src)                        plays any audio file by URL
(() => {
  const player = new Audio();
  let current = null;
  let finish = null;

  function done(ok) {
    if (current) current.classList.remove("say--playing");
    current = null;
    const resolve = finish;
    finish = null;
    if (resolve) resolve(ok);
  }

  function stop() {
    player.pause();
    done(false);
  }

  function play(button) {
    stop();
    if (!button || !button.dataset.src || button.classList.contains("say--missing")) {
      return Promise.resolve(false);
    }
    current = button;
    button.classList.add("say--playing");
    player.src = button.dataset.src;
    return new Promise((resolve) => {
      finish = resolve;
      player.play().catch(() => done(false));
    });
  }

  player.addEventListener("ended", () => done(true));
  player.addEventListener("error", () => done(false));

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".say");
    if (button) play(button);
  });

  window.Say = { play, stop };
  window.playAudio = (src) => {
    stop();
    player.src = src;
    return player.play();
  };
})();
