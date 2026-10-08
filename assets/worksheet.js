/* Shared script of every worksheet (see CLAUDE.md): actions menu, answer key button, Enter key, saved work
   (answers and questions drawn stay in this browser; index.html lists them) and helpers.
   Loaded at the end of <body>, before the worksheet's own <script>, which uses window.Worksheet:
   - it makes the fields it needs with Worksheet.answerInput(label, extra);
   - then calls Worksheet.start() (fixed questions), or, for a random worksheet,
     Worksheet.start({ drawVersion, generate, render, isValidDraw }) (see exercices-phrases-mots.html). */
window.Worksheet = (() => {
  // ---- Actions menu: below 1200px, the toolbar is a sidebar opened and closed by the ☰ button ----
  const toggle = document.querySelector(".menu-toggle");
  const menu = toggle && document.getElementById(toggle.getAttribute("aria-controls"));
  if (menu) {
    const isOpen = () => toggle.getAttribute("aria-expanded") === "true";
    const setOpen = open => {
      if (!open && menu.contains(document.activeElement)) toggle.focus();   // the focus would be lost in the hidden menu
      toggle.setAttribute("aria-expanded", open);
    };
    toggle.addEventListener("click", () => setOpen(!isOpen()));
    // A chosen action closes the menu, to show its effect; so do Escape, a press (mouse, finger) or the focus
    // beside the menu. pointerdown, not click: Safari on iPhone and iPad may send no click for a tap on plain text
    menu.addEventListener("click", e => { if (isOpen() && e.target.closest("a, button")) setOpen(false); });
    document.addEventListener("keydown", e => { if (e.key === "Escape" && isOpen()) setOpen(false); });
    document.addEventListener("pointerdown", e => {
      if (isOpen() && !menu.contains(e.target) && !toggle.contains(e.target)) setOpen(false);
    });
    menu.addEventListener("focusout", e => {
      const to = e.relatedTarget;
      if (isOpen() && to && to !== toggle && !menu.contains(to)) setOpen(false);
    });
    // Back to a wide window: the toolbar is shown as usual
    matchMedia("(max-width: 1199.98px)").addEventListener?.("change", () => setOpen(false));
  }

  // ---- Answer key and keyboard ----
  document.getElementById("btn-answers")?.addEventListener("click", e => {
    const on = document.body.classList.toggle("show-answers");
    e.currentTarget.setAttribute("aria-pressed", on);
    e.currentTarget.textContent = on ? "Masquer le corrigé" : "Afficher le corrigé";
  });
  // Enter moves to the next input field, like Tab
  document.addEventListener("keydown", e => {
    if (e.key !== "Enter" || !e.target.classList.contains("answer-input")) return;
    e.preventDefault();
    const fields = [...document.querySelectorAll(".answer-input")];
    fields[fields.indexOf(e.target) + 1]?.focus();
  });

  // ---- Helpers for the worksheet's script ----
  // Imported work is untrusted: every drawn string is escaped before going into the HTML
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const isText = (s, max) => typeof s === "string" && s.length > 0 && s.length <= max;
  const isList = (a, n, ok) => Array.isArray(a) && a.length === n && a.every(ok);

  // Transparent keyboard input field, laid over the area where the pupil writes
  // (label escaped: it may contain a drawn word)
  const answerInput = (label, extra = "") => `<input class="answer-input" type="text" aria-label="${esc(label)}"${extra}`
    + ` autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false">`;

  const rand = n => Math.floor(Math.random() * n);
  const shuffle = list => {
    const a = list.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = rand(i + 1);
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  };
  const sample = (list, k) => shuffle(list).slice(0, k);

  // ---- Saved work: answers (and drawn questions) stay in this browser; index.html lists them ----
  // Key: path of the worksheet from the site root, as in catalog.js ("arbres.html", "Arbres/x.html"),
  // found from the back link: same key on GitHub Pages (even without ".html"), on a local server or from disk
  const storageKey = (() => {
    try {
      const root = decodeURIComponent(new URL(".", document.querySelector(".back-link").href).pathname);
      let path = decodeURIComponent(location.pathname);
      path = path.startsWith(root) ? path.slice(root.length) : path.slice(path.lastIndexOf("/") + 1);
      return `exercices-scolaires:${path.endsWith(".html") ? path : `${path}.html`}`;
    } catch (e) { return null; }
  })();
  const storage = (() => { try { return storageKey ? window.localStorage : null; } catch (e) { return null; } })();
  // Preview in index.html (#preview, or any same-origin frame): show the saved work, never change it
  const readOnly = location.hash === "#preview" || !!window.frameElement;
  let lastJson = null;   // last value read or written here, to notice changes made elsewhere

  function readWork() {
    if (!storage) return null;
    try {
      lastJson = storage.getItem(storageKey);
      const work = JSON.parse(lastJson);
      return work && work.v === 1 && Array.isArray(work.fields) ? work : null;
    } catch (e) { return null; }   // storage blocked, or not JSON
  }

  function writeWork(work) {
    if (readOnly || !storage) return;
    try {
      const json = work ? JSON.stringify({ v: 1, updated: new Date().toISOString(), ...work }) : null;
      if (json) storage.setItem(storageKey, json);
      else storage.removeItem(storageKey);
      lastJson = json;
    } catch (e) { /* storage full or blocked: the worksheet works as before */ }
  }

  const answerFields = () => [...document.querySelectorAll(".answer-input")];
  const hasAnswers = () => answerFields().some(f => f.value.trim());
  const answerList = () => answerFields().map(f => [f.getAttribute("aria-label"), f.value]);

  // Each field takes back the first unused saved answer with the same aria-label,
  // so the answers survive a field added or removed elsewhere in the worksheet
  function restoreAnswers(work) {
    const saved = (work ? work.fields : []).filter(a => Array.isArray(a) && typeof a[0] === "string" && typeof a[1] === "string");
    answerFields().forEach(f => {
      const k = saved.findIndex(([label]) => label === f.getAttribute("aria-label"));
      f.value = k < 0 ? "" : saved.splice(k, 1)[0][1];
    });
  }

  let options = null;   // what Worksheet.start() received; random worksheet: drawVersion, generate, render, isValidDraw
  let draw = null;      // random worksheet: the questions on screen, as plain data (see generate())

  // Fixed questions: nothing is kept once every field is empty. Random worksheet: the questions drawn
  // are saved with the answers (drawVersion: change it when the shape or meaning of the draw changes,
  // older saves then get new questions)
  function saveWork() {
    if (options.generate) writeWork({ fields: answerList(), draw, drawVersion: options.drawVersion });
    else writeWork(hasAnswers() ? { fields: answerList() } : null);
  }

  // Saved questions and answers come back; without usable saved questions, new ones are drawn and saved at once
  function loadWork() {
    const work = readWork();
    if (!options.generate) return restoreAnswers(work);
    const saved = work && work.drawVersion === options.drawVersion && options.isValidDraw(work.draw) ? work.draw : null;
    if (saved && JSON.stringify(saved) !== JSON.stringify(draw)) {
      try { options.render(saved); draw = saved; } catch (e) { draw = null; }
    }
    if (!draw) {
      options.render(draw = options.generate());
      saveWork();
    } else restoreAnswers(saved && work);   // deleted elsewhere: same questions, empty answers
  }

  // Called once by the worksheet, after it has made its fields: never save before restoring
  function start(settings = {}) {
    if (options) return;
    options = settings;

    if (options.generate) document.getElementById("btn-new")?.addEventListener("click", () => {
      if (hasAnswers() && !confirm("Tes réponses seront effacées. Tirer de nouveaux exercices ?")) return;
      options.render(draw = options.generate());
      saveWork();
    });
    document.addEventListener("input", e => { if (e.target.classList.contains("answer-input")) saveWork(); });
    document.getElementById("btn-clear")?.addEventListener("click", () => {
      if (hasAnswers() && !confirm("Effacer toutes tes réponses ?")) return;
      answerFields().forEach(f => { f.value = ""; });
      saveWork();
    });
    // Saved work changed in another tab, or in the dialog of index.html
    window.addEventListener("storage", e => {
      if (storage && e.storageArea === storage && (e.key === storageKey || e.key === null)) loadWork();
    });
    // Back on this page from the back/forward cache: take the changes made in the meantime
    window.addEventListener("pageshow", e => {
      if (!e.persisted || !storage) return;
      try { if (storage.getItem(storageKey) !== lastJson) loadWork(); } catch (err) { /* storage blocked */ }
    });

    loadWork();
  }

  return {
    esc, isText, isList, answerInput, rand, shuffle, sample, start,
    save: () => { if (options) saveWork(); },   // random worksheet: after changing the draw on screen
    get draw() { return draw; },
  };
})();
