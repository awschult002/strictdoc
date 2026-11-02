// One delegated click listener for every copy-to-clipboard button (node
// anchor, inline RST anchor, stable link, field content).

(() => {

  const SEL_BUTTON =
    '.copy_to_clipboard-button, .copy_stable_link-button, .anchor_button';
  const SEL_COVER = '.copy_to_clipboard-cover';
  const DONE_ICON = '#sdoc-icon-done';

  const SEL_FIELD = 'sdoc-field';
  const SEL_FIELD_SERVICE = 'sdoc-field-service';
  const SEL_FIELD_CONTENT = 'sdoc-field-content';

  function resolveURL(path) {
    // new URL(path, base) handles both cases without explicit absolute-check:
    // absolute URLs ignore the base and return as-is,
    // relative ones resolve against it.
    const resolved = new URL(path, window.location.href).href;
    // Expand folder to index if we run from the local file system.
    return (window.location.protocol === 'file:') ?
      resolved.replace(/#/, 'index.html?a=') :
      resolved.replace(/#/, '?a=');
  }

  function markMisconfigured(btn) {
    // Flags the button so the delegated click listener below leaves it
    // alone entirely - no preventDefault, as if no listener were attached.
    btn.dataset.copyClipboardMisconfigured = 'true';
    btn.title = 'Misconfigured: no sdoc-field context found';
    btn.style.cursor = 'not-allowed';
    btn.style.color = 'red';
    btn.style.background = 'rgb(255 0 0 / 10%)';
    btn.style.opacity = '1';
  }

  // A plain field-copy button (no data-anchor-id / data-path) only works
  // inside a sdoc-field. This is checked as soon as the button is inserted,
  // via StrictDoc.onInsert, not lazily on first click, so a misconfigured
  // button is visibly flagged right away instead of looking fine until
  // someone clicks it.
  window.StrictDoc.onInsert(SEL_BUTTON, (btn) => {
    if (btn.dataset.anchorId || btn.dataset.path) return;
    if (!btn.closest(SEL_FIELD)) markMisconfigured(btn);
  });

  // What to copy, and which element shows the copy/done feedback, depend on
  // which attributes are present on the button:
  //   data-anchor-id  -> anchor ID (node anchor or inline RST anchor)
  //   data-path       -> stable link URL (resolved at click time)
  //   neither         -> text content of the parent sdoc-field
  function textAndFeedbackRoot(btn) {
    if (btn.dataset.anchorId) {
      return [btn.dataset.anchorId, btn];
    }
    if (btn.dataset.path) {
      return [resolveURL(btn.dataset.path), btn];
    }
    const field = btn.closest(SEL_FIELD);
    const feedbackRoot = field.querySelector(SEL_FIELD_SERVICE) ?? btn;
    const text = field.querySelector(SEL_FIELD_CONTENT)?.innerText.trim() ?? '';
    return [text, feedbackRoot];
  }

  // The buttons carry only their normal icon(s). As feedback, each icon is
  // switched to the "done" icon and restored afterwards.
  function showDone(button, done) {
    if (!button) return;
    button.style.opacity = done ? 1 : '';
    for (const use of button.querySelectorAll('use')) {
      if (done) {
        use.dataset.icon ??= use.getAttribute('href');
        use.setAttribute('href', DONE_ICON);
      } else if (use.dataset.icon) {
        use.setAttribute('href', use.dataset.icon);
      }
    }
  }

  function feedback(root, button) {
    const cover = root.querySelector(SEL_COVER);
    showDone(button, true);

    if (cover) {
      // initial opacity
      let op = 1;
      cover.style.background = `rgba(242, 100, 42, ${op})`;
      const fadeTimer = setInterval(() => {
        // update cover
        cover.style.background = `rgba(242, 100, 42, ${op})`;
        if (op <= 0.1) {
          clearInterval(fadeTimer);
          // reset cover
          cover.style.background = '';
          showDone(button, false);
        }
        op -= op * 0.1;
      }, 30);
    } else {
      setTimeout(() => showDone(button, false), 1500);
    }
  }

  // Listening on document (not per-button) means a button inserted later -
  // e.g. a node added dynamically without a page reload - works with no
  // extra wiring: closest() below is resolved against the DOM as it is at
  // click time, not against some list captured up front.
  document.addEventListener('click', (event) => {
    const btn = event.target.closest?.(SEL_BUTTON);
    if (!btn) return;
    if (btn.dataset.copyClipboardMisconfigured) return;
    event.preventDefault();
    const [text, feedbackRoot] = textAndFeedbackRoot(btn);
    navigator.clipboard.writeText(text).then(
      () => feedback(feedbackRoot, btn),
      () => console.warn('Clipboard write failed')
    );
  });

})();
