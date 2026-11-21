/* The HTML holds the collection. JavaScript handles lookup, the bench and field notes. */
"use strict";
const get = (id) => document.getElementById(id);
const library = new Map(instruments.map((item) => [item.slug, item]));
const base = document.body.dataset.base;
const values = new URLSearchParams(location.search);

function updateURL(params) {
  const next = new URL(location.href);
  next.search = params.toString();
  try {
    history.replaceState(history.state, "", next.href);
  } catch (_) {
    /* Some browsers disallow file-origin history changes. Controls still work. */
  }
}

function useCollection() {
  const search = get("search"),
    family = get("family");
  const entries = [...document.querySelectorAll(".index-list li")];
  search.value = values.get("q") || "";
  family.value = values.get("family") || "";
  if (family.selectedIndex === -1) family.value = "";
  function filter(sync = true) {
    const words = search.value
      .trim()
      .toLowerCase()
      .split(/\s+/)
      .filter(Boolean);
    let visible = 0;
    for (const row of entries) {
      row.hidden =
        !words.every((word) => row.dataset.search.includes(word)) ||
        Boolean(family.value && row.dataset.family !== family.value);
      if (!row.hidden) visible++;
    }
    get("empty").hidden = visible !== 0;
    get("result-count").textContent =
      visible + (visible === 1 ? " instrument" : " instruments");
    if (sync) {
      const next = new URLSearchParams();
      if (search.value) next.set("q", search.value);
      if (family.value) next.set("family", family.value);
      updateURL(next);
    }
  }
  get("lookup").addEventListener("submit", (e) => {
    e.preventDefault();
    filter();
  });
  search.addEventListener("input", () => filter());
  family.addEventListener("change", () => filter());
  get("clear-search").addEventListener("click", () => {
    search.value = "";
    family.value = "";
    filter();
    search.focus();
  });
  window.addEventListener("pageshow", () => filter(false));
  filter(false);
}

function useBench() {
  const left = get("left"),
    right = get("right");
  function known(value, fallback) {
    return library.has(value) ? value : fallback;
  }
  left.value = known(values.get("a"), "rain-catcher");
  right.value = known(values.get("b"), "dew-mirror");
  const alternative = (slug) =>
    instruments.find((item) => item.slug !== slug).slug;
  if (left.value === right.value) right.value = alternative(left.value);
  let previous = [left.value, right.value];
  function setBench(changed) {
    if (left.value === right.value) {
      if (changed === "left") right.value = previous[0];
      else left.value = previous[1];
    }
    const items = [library.get(left.value), library.get(right.value)];
    ["left", "right"].forEach((side, index) => {
      const item = items[index];
      const tray = document.querySelector('[data-side="' + side + '"]');
      tray.style.setProperty("--tint", item.color);
      const link = get(side + "-link");
      link.href = "objects/" + item.slug + ".html";
      link.setAttribute("aria-label", "Open " + item.name);
      const img = link.querySelector("img");
      img.src = item.image;
      img.alt = item.alt;
      document.querySelector('[data-heading="' + side + '"]').textContent =
        item.name;
      for (const cell of document.querySelectorAll('[data-col="' + side + '"]'))
        cell.textContent = item[cell.dataset.attr];
    });
    previous = [left.value, right.value];
    if (changed) {
      updateURL(new URLSearchParams({ a: left.value, b: right.value }));
      get("compare-status").textContent =
        "Comparing " + items[0].name + " with " + items[1].name + ".";
    }
  }
  left.addEventListener("change", () => setBench("left"));
  right.addEventListener("change", () => setBench("right"));
  setBench();
}

/* Scope field notes to this particular cabinet, including on a subpath or file URL.
   A tab-only copy carries a notebook between local files that isolate Web Storage.
   Only the next same-cabinet click receives it. Notes are never in addresses. */
function notebook() {
  const root = new URL(base || "./", location.href);
  root.search = "";
  root.hash = "";
  const key = "weather-cabinet.v1:" + root.pathname;
  const marker = key + "|";
  const stores = [];
  for (const name of ["localStorage", "sessionStorage"]) {
    try {
      const store = window[name],
        probe = key + ".probe";
      store.setItem(probe, "1");
      store.removeItem(probe);
      stores.push([name, store]);
    } catch (_) {
      /* This storage is unavailable. */
    }
  }
  let state = { version: 1, revision: 0, entries: {} };
  const validRows = (rows) =>
    rows &&
    typeof rows === "object" &&
    !Array.isArray(rows) &&
    Object.entries(rows).every(
      ([id, text]) =>
        library.has(id) &&
        typeof text === "string" &&
        text.trim().length > 0 &&
        text.length <= 2000,
    );
  function absorb(raw) {
    if (!raw) return;
    try {
      const data = JSON.parse(raw);
      if (
        data.version === 1 &&
        Number.isSafeInteger(data.revision) &&
        data.revision >= state.revision &&
        validRows(data.entries)
      )
        state = data;
    } catch (_) {
      /* An invalid local copy cannot erase a usable one. */
    }
  }
  function refresh() {
    for (const [, store] of stores) {
      try {
        absorb(store.getItem(key));
      } catch (_) {}
    }
  }
  const carried = location.protocol === "file:" || !stores.length;
  function rememberInHistory() {
    if (!carried) return;
    try {
      history.replaceState(
        { ...history.state, cabinet: key, snapshot: state },
        "",
      );
    } catch (_) {}
  }
  function writeCopies() {
    let persistent = false;
    for (const [name, store] of stores) {
      try {
        store.setItem(key, JSON.stringify(state));
        if (name === "localStorage") persistent = true;
      } catch (_) {}
    }
    rememberInHistory();
    return persistent;
  }
  refresh();
  if (carried && history.state?.cabinet === key)
    absorb(JSON.stringify(history.state.snapshot));
  if (window.name.startsWith(marker)) {
    absorb(window.name.slice(marker.length));
    window.name = "";
    writeCopies();
  }
  function commit(change) {
    refresh();
    const entries = { ...state.entries };
    change(entries);
    state = {
      version: 1,
      revision: Math.max(Date.now(), state.revision + 1),
      entries,
    };
    return writeCopies();
  }
  if (carried) {
    document.addEventListener("click", (event) => {
      const link = event.target.closest("a[href]");
      if (
        !link ||
        link.target ||
        event.ctrlKey ||
        event.metaKey ||
        event.shiftKey ||
        event.altKey ||
        event.defaultPrevented
      )
        return;
      const target = new URL(link.href, location.href);
      if (
        target.origin === root.origin &&
        target.pathname.startsWith(root.pathname) &&
        target.pathname !== location.pathname
      ) {
        refresh();
        window.name = marker + JSON.stringify(state);
      }
    });
  }
  const persistent = stores.some(([name]) => name === "localStorage");
  return {
    get entries() {
      refresh();
      return { ...state.entries };
    },
    commit,
    validRows,
    persistent,
  };
}

function useForm(book, id) {
  const textarea = get("observation"),
    message = get("note-status");
  textarea.value = book.entries[id] || "";
  if (!book.persistent)
    message.textContent =
      "Temporary notebook. Open Field notes to download a backup before closing this tab.";
  get("note-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const value = textarea.value.trim();
    if (!value) {
      textarea.setCustomValidity("Write an observation first.");
      textarea.reportValidity();
      return;
    }
    const saved = book.commit((rows) => {
      rows[id] = value;
    });
    message.textContent = saved
      ? "Field note saved."
      : "Field note saved for this tab. Open Field notes to download a backup.";
  });
  textarea.addEventListener("input", () => textarea.setCustomValidity(""));
}

function make(tag, text, props = {}) {
  const el = document.createElement(tag);
  if (text) el.textContent = text;
  Object.assign(el, props);
  return el;
}

function useNotes(book) {
  const host = get("entries"),
    status = get("notes-status"),
    undo = get("undo");
  const editing = new Map();
  let removed;
  if (!book.persistent) {
    get("storage-info").hidden = false;
    get("storage-info").textContent =
      "This notebook is temporary. Download a backup before closing the tab.";
  }
  function render() {
    host.replaceChildren();
    const rows = book.entries;
    const ids = instruments
      .map((s) => s.slug)
      .filter((id) => Object.hasOwn(rows, id));
    get("blank").hidden = ids.length > 0;
    get("notes-count").textContent =
      ids.length + (ids.length === 1 ? " observation" : " observations");
    get("export").disabled = ids.length === 0;
    for (const id of ids) {
      const item = library.get(id),
        article = make("article"),
        title = make("h2"),
        heading = make("a", item.name, { href: "objects/" + id + ".html" });
      title.append(heading);
      article.append(title);
      const actions = make("div", "", { className: "entry-actions" });
      if (editing.has(id)) {
        const input = make("textarea", "", {
          value: editing.get(id),
          rows: 4,
          maxLength: 2000,
          id: "edit-" + id,
        });
        input.setAttribute("aria-label", "Observation for " + item.name);
        const form = make("form"),
          save = make("button", "Save changes", { type: "submit" }),
          cancel = make("button", "Cancel", { type: "button" });
        input.required = true;
        input.addEventListener("input", () => {
          editing.set(id, input.value);
          input.setCustomValidity("");
        });
        form.addEventListener("submit", (e) => {
          e.preventDefault();
          if (!input.value.trim()) {
            input.setCustomValidity("Write an observation first.");
            input.reportValidity();
            return;
          }
          book.commit((all) => {
            all[id] = input.value.trim();
          });
          editing.delete(id);
          render();
          get("edit-button-" + id).focus();
          status.textContent = "Changes saved for " + item.name + ".";
        });
        cancel.addEventListener("click", () => {
          editing.delete(id);
          render();
          get("edit-button-" + id).focus();
        });
        actions.append(save, cancel);
        form.append(input, actions);
        article.append(form);
      } else {
        const edit = make("button", "Edit", {
            type: "button",
            id: "edit-button-" + id,
          }),
          remove = make("button", "Remove", { type: "button" });
        edit.setAttribute("aria-label", "Edit " + item.name + " note");
        remove.setAttribute("aria-label", "Remove " + item.name + " note");
        edit.addEventListener("click", () => {
          editing.set(id, book.entries[id]);
          render();
          get("edit-" + id).focus();
        });
        remove.addEventListener("click", () => {
          removed = { id, text: book.entries[id] };
          book.commit((all) => {
            delete all[id];
          });
          render();
          undo.hidden = false;
          undo.focus();
          status.textContent = "Removed " + item.name + " note.";
        });
        actions.append(edit, remove);
        article.append(
          make("p", rows[id], { className: "observation" }),
          actions,
        );
      }
      host.append(article);
    }
  }
  undo.addEventListener("click", () => {
    if (!removed) return;
    const id = removed.id;
    book.commit((rows) => {
      if (!Object.hasOwn(rows, id)) rows[id] = removed.text;
    });
    removed = null;
    undo.hidden = true;
    render();
    get("edit-button-" + id)?.focus();
    status.textContent = "Note restored.";
  });
  get("export").addEventListener("click", () => {
    const file = new Blob(
      [
        JSON.stringify(
          {
            format: "weather-cabinet-notes",
            version: 1,
            entries: book.entries,
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(file),
      link = make("a", "", {
        href: url,
        download: "weather-cabinet-notes.json",
      });
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = "Notebook backup downloaded.";
  });
  get("import-file").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      if (file.size > 1024 * 1024) throw Error();
      const data = JSON.parse(await file.text());
      if (
        data.format !== "weather-cabinet-notes" ||
        data.version !== 1 ||
        !book.validRows(data.entries)
      )
        throw Error();
      let added = 0;
      book.commit((rows) => {
        for (const [id, text] of Object.entries(data.entries)) {
          if (!Object.hasOwn(rows, id)) {
            rows[id] = text;
            added++;
          }
        }
      });
      render();
      status.textContent =
        "Imported " +
        added +
        " " +
        (added === 1 ? "note." : "notes.") +
        " Existing notes were kept.";
    } catch (_) {
      status.textContent =
        "This file is not a valid Weather Cabinet backup. Your notes are unchanged.";
    }
    e.target.value = "";
  });
  window.addEventListener("pageshow", () => {
    if (!editing.size) render();
  });
  window.addEventListener("storage", () => {
    if (!editing.size) render();
  });
  render();
}

const page = document.body.dataset.page;
const book = notebook();
if (page === "collection") useCollection();
if (page === "compare") useBench();
if (page === "object") useForm(book, document.body.dataset.id);
if (page === "notes") useNotes(book);
