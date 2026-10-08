// In-page PDF viewer for PDF Serial Cross-Check.
// One pane for "open this document", two side-by-side panes for reviewing a ROMC row
// against the document that should contain it. Matching values are highlighted.
(function () {
  'use strict';

  const alnum = s => String(s || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  // ---- Shared PDF cache (a few documents open at once; oldest is closed) ----
  const cache = new Map(); // blob -> Promise<PDFDocumentProxy>
  const urls = new WeakMap(); // blob -> object URL for "open in new tab"
  function getPdf(blob) {
    if (cache.has(blob)) {
      const p = cache.get(blob);
      cache.delete(blob); cache.set(blob, p); // most recently used last
      return p;
    }
    const p = blob.arrayBuffer().then(buf => pdfjsLib.getDocument({ data: new Uint8Array(buf) }).promise);
    cache.set(blob, p);
    while (cache.size > 4) {
      const [oldBlob, oldP] = cache.entries().next().value;
      cache.delete(oldBlob);
      oldP.then(pdf => pdf.destroy()).catch(() => {});
    }
    return p;
  }
  function blobUrl(blob) {
    if (!urls.has(blob)) urls.set(blob, URL.createObjectURL(blob));
    return urls.get(blob);
  }

  // Rectangles (PDF user space) where `value` appears on a page: in the text layer,
  // in form field values, or in text typed onto the page as an annotation.
  async function findRects(page, value) {
    const t = alnum(value);
    if (t.length < 3) return [];
    const rects = [];
    const tc = await page.getTextContent();
    let concat = '';
    const spans = [];
    for (const it of tc.items) {
      const a = alnum(it.str);
      if (!a) continue;
      spans.push({ start: concat.length, end: concat.length + a.length, it });
      concat += a;
    }
    for (let idx = concat.indexOf(t); idx >= 0; idx = concat.indexOf(t, idx + t.length)) {
      const end = idx + t.length;
      for (const s of spans) {
        if (s.end <= idx || s.start >= end) continue;
        const tr = s.it.transform;
        const h = Math.hypot(tr[2], tr[3]) || 10;
        rects.push([tr[4] - 1, tr[5] - h * 0.3, tr[4] + (s.it.width || h) + 1, tr[5] + h * 0.95]);
      }
    }
    let annots = [];
    try { annots = await page.getAnnotations(); } catch (e) { /* none */ }
    for (const a of annots) {
      let v = a.fieldValue;
      if (Array.isArray(v)) v = v.join(' ');
      const text = [v, a.contentsObj && a.contentsObj.str].filter(Boolean).join(' ');
      if (text && alnum(text).includes(t)) rects.push(a.rect);
    }
    return rects;
  }

  // ---- One viewer pane ----
  function Pane(el, getDocs) {
    el.innerHTML =
      '<div class="pane-bar">' +
      '<select class="pane-doc" aria-label="Document"></select>' +
      '<span class="pane-nav"><button type="button" data-act="prev" title="Previous page">&#8249;</button>' +
      '<input class="pane-page" type="number" min="1" aria-label="Page"><span class="pane-of"></span>' +
      '<button type="button" data-act="next" title="Next page">&#8250;</button></span>' +
      '<span class="pane-nav"><button type="button" data-act="zout" title="Zoom out">&minus;</button>' +
      '<button type="button" data-act="zin" title="Zoom in">+</button></span>' +
      '<a class="pane-tab" target="_blank" rel="noopener" title="Open in the browser\'s PDF viewer">New tab &#8599;</a>' +
      '</div><div class="pane-msg"></div>' +
      '<div class="pane-body"><div class="pane-wrap"><canvas></canvas><div class="pane-hl"></div></div></div>';
    const q = s => el.querySelector(s);
    const sel = q('.pane-doc'), pageIn = q('.pane-page'), of = q('.pane-of'), body = q('.pane-body');
    const canvas = q('canvas'), hlLayer = q('.pane-hl'), msg = q('.pane-msg'), tab = q('.pane-tab');
    const st = { doc: -1, page: 1, hl: '', zoom: 1, pages: 0, token: 0, task: null, scrollToHl: false };

    function fillDocs() {
      const docs = getDocs();
      sel.innerHTML = docs.map((d, i) => d.error ? '' : `<option value="${i}">${esc(d.short || d.name)}</option>`).join('');
      sel.value = String(st.doc);
    }

    async function render() {
      const token = ++st.token;
      const d = getDocs()[st.doc];
      if (!d || !d.blob) { msg.textContent = 'Document not available.'; return; }
      msg.textContent = 'Loading…';
      let pdf;
      try { pdf = await getPdf(d.blob); } catch (e) { msg.textContent = 'Could not open: ' + e.message; return; }
      if (token !== st.token) return;
      st.pages = pdf.numPages;
      st.page = Math.min(Math.max(1, st.page), st.pages);
      pageIn.value = st.page; pageIn.max = st.pages; of.textContent = `/ ${st.pages}`;
      tab.href = blobUrl(d.blob) + '#page=' + st.page;

      const page = await pdf.getPage(st.page);
      if (token !== st.token) return;
      const base = page.getViewport({ scale: 1 });
      const fit = Math.max(200, body.clientWidth - 24) / base.width;
      const vp = page.getViewport({ scale: fit * st.zoom });
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(vp.width * dpr);
      canvas.height = Math.floor(vp.height * dpr);
      canvas.style.width = Math.floor(vp.width) + 'px';
      canvas.style.height = Math.floor(vp.height) + 'px';
      if (st.task) st.task.cancel();
      st.task = page.render({
        canvasContext: canvas.getContext('2d'), viewport: vp,
        transform: dpr !== 1 ? [dpr, 0, 0, dpr, 0, 0] : null,
        annotationMode: pdfjsLib.AnnotationMode.ENABLE,
      });
      try { await st.task.promise; } catch (e) { if (e && e.name === 'RenderingCancelledException') return; msg.textContent = 'Render failed: ' + e.message; return; }
      if (token !== st.token) return;

      hlLayer.innerHTML = '';
      const rects = st.hl ? await findRects(page, st.hl) : [];
      if (token !== st.token) return;
      let firstTop = null;
      for (const r of rects) {
        const [a, b, c, e] = vp.convertToViewportRectangle(r);
        const left = Math.min(a, c), top = Math.min(b, e);
        const box = document.createElement('div');
        box.className = 'hl';
        box.style.cssText = `left:${left}px;top:${top}px;width:${Math.abs(c - a)}px;height:${Math.abs(e - b)}px`;
        hlLayer.appendChild(box);
        if (firstTop == null || top < firstTop) firstTop = top;
      }
      if (st.hl && rects.length) msg.innerHTML = `Highlighted <code>${esc(st.hl)}</code>`;
      else if (st.hl) msg.innerHTML = `<code>${esc(st.hl)}</code> isn't in this page's text — look for it in the image`;
      else msg.textContent = '';
      if (st.scrollToHl) {
        body.scrollTop = firstTop != null ? Math.max(0, firstTop - 80) : 0;
        st.scrollToHl = false;
      }
    }

    el.addEventListener('click', e => {
      const act = e.target.closest('[data-act]');
      if (!act) return;
      const a = act.dataset.act;
      if (a === 'prev' && st.page > 1) { st.page--; st.scrollToHl = true; }
      else if (a === 'next' && st.page < st.pages) { st.page++; st.scrollToHl = true; }
      else if (a === 'zin') st.zoom = Math.min(4, st.zoom * 1.25);
      else if (a === 'zout') st.zoom = Math.max(0.4, st.zoom / 1.25);
      else return;
      render();
    });
    pageIn.addEventListener('change', () => { st.page = +pageIn.value || 1; st.scrollToHl = true; render(); });
    sel.addEventListener('change', () => { st.doc = +sel.value; st.page = 1; st.scrollToHl = true; render(); });

    return {
      el,
      show(spec) {
        st.doc = spec.doc; st.page = spec.page || 1; st.hl = spec.hl || ''; st.zoom = 1; st.scrollToHl = true;
        fillDocs();
        return render();
      },
      rerender: render,
    };
  }

  // ---- The overlay with one or two panes ----
  window.createSncViewer = function ({ getDocs, onMark, onStep, onClose }) {
    const root = document.createElement('div');
    root.className = 'snc-viewer';
    root.hidden = true;
    root.setAttribute('role', 'dialog');
    root.setAttribute('aria-modal', 'true');
    root.innerHTML =
      '<div class="viewer-box">' +
      '<div class="viewer-bar">' +
      '<div class="viewer-title"></div>' +
      '<div class="viewer-actions">' +
      '<span class="viewer-step"><button type="button" class="btn btn-small" data-v="prev">&#8249; Prev item</button>' +
      '<span class="viewer-count"></span>' +
      '<button type="button" class="btn btn-small" data-v="next">Next item &#8250;</button></span>' +
      '<span class="viewer-mark"><button type="button" class="btn btn-small mark-ok" data-v="verified">&#10003; Verified</button>' +
      '<button type="button" class="btn btn-small mark-bad" data-v="issue">&#9888; Issue</button></span>' +
      '<button type="button" class="btn btn-small" data-v="close" title="Close (Esc)">Close &#10005;</button>' +
      '</div></div>' +
      '<div class="viewer-panes"><div class="pane"></div><div class="pane"></div></div>' +
      '</div>';
    document.body.appendChild(root);
    const [elA, elB] = root.querySelectorAll('.pane');
    const paneA = Pane(elA, getDocs), paneB = Pane(elB, getDocs);
    const title = root.querySelector('.viewer-title');
    const markBox = root.querySelector('.viewer-mark'), stepBox = root.querySelector('.viewer-step');
    let current = null;
    let lastFocus = null;

    function setMarkButtons(status) {
      markBox.querySelector('.mark-ok').classList.toggle('active', status === 'verified');
      markBox.querySelector('.mark-bad').classList.toggle('active', status === 'issue');
    }

    function close() {
      root.hidden = true;
      document.body.classList.remove('snc-viewer-open');
      if (onClose) onClose();
      if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
    }

    root.addEventListener('click', e => {
      if (e.target === root) return close();
      const b = e.target.closest('[data-v]');
      if (!b) return;
      const v = b.dataset.v;
      if (v === 'close') close();
      else if ((v === 'prev' || v === 'next') && current && current.step) onStep(current.step.index + (v === 'next' ? 1 : -1));
      else if ((v === 'verified' || v === 'issue') && current && current.mark) {
        const next = current.mark.status === v ? null : v;
        current.mark.status = next;
        setMarkButtons(next);
        onMark(current.mark.key, next);
      }
    });
    document.addEventListener('keydown', e => {
      if (root.hidden) return;
      if (e.key === 'Escape') close();
    });
    let rt;
    window.addEventListener('resize', () => {
      if (root.hidden) return;
      clearTimeout(rt);
      rt = setTimeout(() => { paneA.rerender(); if (!elB.hidden) paneB.rerender(); }, 200);
    });

    return {
      // spec: { title (html), left:{doc,page,hl}, right?:{doc,page,hl}, mark?:{key,status}, step?:{index,total} }
      open(spec) {
        current = spec;
        if (root.hidden) lastFocus = document.activeElement;
        title.innerHTML = spec.title || '';
        markBox.hidden = !spec.mark;
        stepBox.hidden = !spec.step;
        if (spec.mark) setMarkButtons(spec.mark.status);
        if (spec.step) root.querySelector('.viewer-count').textContent = `${spec.step.index + 1} of ${spec.step.total}`;
        if (spec.step) {
          stepBox.querySelector('[data-v="prev"]').disabled = spec.step.index <= 0;
          stepBox.querySelector('[data-v="next"]').disabled = spec.step.index >= spec.step.total - 1;
        }
        elB.hidden = !spec.right;
        root.classList.toggle('split', !!spec.right);
        root.hidden = false;
        document.body.classList.add('snc-viewer-open');
        root.querySelector('[data-v="close"]').focus();
        // Panes size themselves to their width, so render after layout.
        requestAnimationFrame(() => {
          paneA.show(spec.left);
          if (spec.right) paneB.show(spec.right);
        });
      },
      close,
      reset() { cache.forEach(p => p.then(pdf => pdf.destroy()).catch(() => {})); cache.clear(); },
    };
  };
})();
