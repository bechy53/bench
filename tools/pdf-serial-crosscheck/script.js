(function () {
  'use strict';
  pdfjsLib.GlobalWorkerOptions.workerSrc =
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

  const $ = id => document.getElementById(id);
  const state = { docs: [], rows: [] }; // docs: {name, pages, fields:{name:Set}, text, error}

  // ---------- PDF extraction ----------
  async function extract(file) {
    const doc = { name: file.name, pages: 0, fields: {}, text: '', error: null };
    try {
      const data = new Uint8Array(await file.arrayBuffer());
      const pdf = await pdfjsLib.getDocument({ data }).promise;
      doc.pages = pdf.numPages;

      // Fillable form fields (AcroForm)
      try {
        const objs = await pdf.getFieldObjects();
        if (objs) {
          for (const [name, widgets] of Object.entries(objs)) {
            for (const w of widgets) {
              let v = w.value;
              if (v == null || v === '' || v === 'Off') continue;
              if (Array.isArray(v)) v = v.join(', ');
              (doc.fields[name] ||= new Set()).add(String(v).trim());
            }
          }
        }
      } catch (e) { console.warn('Field read failed', file.name, e); }

      // Page text, keeping line breaks so patterns can stay on one line
      const parts = [];
      for (let p = 1; p <= pdf.numPages; p++) {
        const page = await pdf.getPage(p);
        const tc = await page.getTextContent();
        for (const it of tc.items) parts.push(it.str, it.hasEOL ? '\n' : ' ');
        parts.push('\n');
        page.cleanup();
      }
      doc.text = parts.join('');
      await pdf.destroy();
    } catch (e) {
      doc.error = e.message || String(e);
    }
    return doc;
  }

  // ---------- Options ----------
  function opts() {
    return {
      useFields: $('snc-usefields').checked,
      useText: $('snc-usetext').checked,
      minTwo: $('snc-mintwo').checked,
      ignoreCase: $('snc-ignorecase').checked,
      ignoreSep: $('snc-ignoresep').checked,
      fieldFilter: $('snc-fieldfilter').value.trim(),
    };
  }
  const normName = s => String(s).toLowerCase().replace(/[^a-z0-9]/g, '');

  function parseAliases() {
    const map = new Map(); // normalized alias -> canonical label
    for (const line of $('snc-aliases').value.split('\n')) {
      const i = line.indexOf('=');
      if (i < 0) continue;
      const canon = line.slice(0, i).trim();
      if (!canon) continue;
      map.set(normName(canon), canon);
      for (const a of line.slice(i + 1).split(',')) if (a.trim()) map.set(normName(a), canon);
    }
    return map;
  }

  function parseRules() {
    const rules = [], errs = [];
    $('snc-rules').value.split('\n').forEach((line, n) => {
      if (!line.trim()) return;
      const i = line.indexOf('|');
      if (i < 0) { errs.push(`Line ${n + 1}: missing "|"`); return; }
      const label = line.slice(0, i).trim(), src = line.slice(i + 1).trim();
      try { rules.push({ label, re: new RegExp(src, 'gi') }); }
      catch (e) { errs.push(`Line ${n + 1}: ${e.message}`); }
    });
    $('snc-ruleerr').textContent = errs.join(' · ');
    return rules;
  }

  // ---------- Comparison ----------
  function compare() {
    const o = opts();
    const norm = v => {
      let s = String(v).trim().replace(/\s+/g, ' ');
      if (o.ignoreCase) s = s.toUpperCase();
      if (o.ignoreSep) s = s.replace(/[\s\-_\/.]/g, '');
      return s;
    };
    const docs = state.docs.filter(d => !d.error);
    const rows = new Map();
    // Form fields and text rules share one key space: a field aliased to a text rule's
    // label lands in the same row, so fillable and flat PDFs are compared together.
    const row = (label, src) => {
      const key = normName(label);
      if (!rows.has(key)) rows.set(key, { label, srcs: new Set(), cells: docs.map(() => []) });
      const r = rows.get(key);
      r.srcs.add(src);
      return r;
    };
    const add = (r, di, v) => { if (v && !r.cells[di].includes(v)) r.cells[di].push(v); };

    if (o.useFields) {
      let filt = null;
      try { filt = o.fieldFilter ? new RegExp(o.fieldFilter, 'i') : null; } catch { filt = null; }
      const aliases = parseAliases();
      docs.forEach((d, di) => {
        for (const [name, vals] of Object.entries(d.fields)) {
          const canon = aliases.get(normName(name));
          if (!canon && filt && !filt.test(name)) continue;
          const r = row(canon || name, 'Form field');
          for (const v of vals) add(r, di, v);
        }
      });
    }

    if (o.useText) {
      for (const rule of parseRules()) {
        const r = row(rule.label, 'Text pattern');
        docs.forEach((d, di) => {
          for (const m of d.text.matchAll(rule.re)) add(r, di, (m[1] ?? m[0]).trim());
        });
      }
    }

    const sig = set => [...set].sort().join('\u0000');
    const out = [];
    for (const r of rows.values()) {
      r.normSets = r.cells.map(c => new Set(c.map(norm)));
      const have = r.normSets.map((s, i) => ({ i, s })).filter(x => x.s.size);
      r.src = [...r.srcs].sort().join(' + ');
      if (o.minTwo && !r.srcs.has('Text pattern') && have.length < 2) continue;
      if (have.length === 0) r.status = 'missing';
      else if (have.length === 1) r.status = docs.length > 1 ? 'single' : 'match';
      else if (!have.every(x => sig(x.s) === sig(have[0].s))) r.status = 'mismatch';
      else r.status = have.length < docs.length ? 'missing' : 'match';
      r.norm = norm;
      out.push(r);
    }
    const order = { mismatch: 0, missing: 1, single: 2, match: 3 };
    out.sort((a, b) => order[a.status] - order[b.status] || a.label.localeCompare(b.label));
    state.rows = out;
    state.cmpDocs = docs;
    render();
  }

  // ---------- Rendering ----------
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const LABEL = { match: 'MATCH', mismatch: 'MISMATCH', missing: 'MISSING', single: 'ONLY 1 DOC' };

  function render() {
    const docs = state.cmpDocs || [];
    const t = $('snc-table');
    $('snc-csv').disabled = !state.rows.length;
    if (docs.length < 1) { t.innerHTML = ''; $('snc-summary').innerHTML = ''; return; }

    const counts = { mismatch: 0, missing: 0, single: 0, match: 0 };
    state.rows.forEach(r => counts[r.status]++);
    $('snc-summary').innerHTML =
      `<p><span class="st-mismatch">${counts.mismatch} mismatch</span>` +
      `<span class="st-missing">${counts.missing + counts.single} missing / one doc only</span>` +
      `<span class="st-match">${counts.match} match</span></p>`;

    let h = '<thead><tr><th>Status</th><th>Item</th>' +
      docs.map(d => `<th>${esc(d.name)}</th>`).join('') + '</tr></thead><tbody>';
    if (!state.rows.length) {
      h += `<tr><td colspan="${docs.length + 2}" class="none">No serial numbers found. Check the field filter or text patterns.</td></tr>`;
    }
    for (const r of state.rows) {
      h += `<tr><td><span class="st st-${r.status}">${LABEL[r.status]}</span></td>` +
           `<td>${esc(r.label)}<div class="src">${r.src}</div></td>`;
      r.cells.forEach((vals, di) => {
        if (!vals.length) { h += '<td class="none">—</td>'; return; }
        // Green = in every document that has this item; amber = in most of them;
        // red = the outlier (or no majority either way).
        const have = r.normSets.filter(s => s.size);
        h += '<td>' + vals.map(v => {
          const n = r.norm(v);
          const count = have.filter(s => s.has(n)).length;
          const cls = count === have.length ? 'ok' : count > have.length / 2 ? 'warn' : 'bad';
          const tip = { ok: 'Found in every document', warn: `Found in ${count} of ${have.length} documents (majority)`, bad: `Found in only ${count} of ${have.length} documents` }[cls];
          return `<span class="chip ${cls}" title="${tip}">${esc(v)}</span>`;
        }).join('') + '</td>';
      });
      h += '</tr>';
    }
    t.innerHTML = h + '</tbody>';
  }

  function renderDocs() {
    $('snc-docs').innerHTML = state.docs.map((d, i) => {
      if (d.error) return `<li><strong>${esc(d.name)}</strong> <span class="err">Could not read: ${esc(d.error)}</span></li>`;
      const nf = Object.keys(d.fields).length;
      return `<li><strong>${esc(d.name)}</strong> <span class="meta">${d.pages} page(s) · ${nf} filled form field(s) · ${d.text.trim() ? 'text layer found' : 'no text layer (scanned?)'}</span>
        <details><summary class="meta">View extracted text and fields</summary>
        <textarea readonly>${esc(
          (nf ? '--- FORM FIELDS ---\n' + Object.entries(d.fields).map(([k, v]) => `${k}: ${[...v].join(', ')}`).join('\n') + '\n\n' : '') +
          '--- PAGE TEXT ---\n' + d.text)}</textarea></details>
        <button class="btn btn-small" data-rm="${i}">Remove</button></li>`;
    }).join('');
  }

  // ---------- Events ----------
  async function addFiles(files) {
    const pdfs = [...files].filter(f => /\.pdf$/i.test(f.name) || f.type === 'application/pdf');
    if (!pdfs.length) return;
    $('snc-summary').innerHTML = '<p>Reading PDFs…</p>';
    const docs = await Promise.all(pdfs.map(extract));
    state.docs.push(...docs);
    renderDocs();
    compare();
  }

  const drop = $('snc-drop'), input = $('snc-file');
  drop.addEventListener('click', () => input.click());
  input.addEventListener('change', () => { addFiles(input.files); input.value = ''; });
  ['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', e => addFiles(e.dataTransfer.files));

  $('snc-docs').addEventListener('click', e => {
    const i = e.target.dataset.rm;
    if (i === undefined) return;
    state.docs.splice(+i, 1);
    renderDocs(); compare();
  });
  $('snc-clear').addEventListener('click', () => { state.docs = []; renderDocs(); compare(); });

  let timer;
  ['snc-usefields', 'snc-usetext', 'snc-mintwo', 'snc-ignorecase', 'snc-ignoresep',
   'snc-fieldfilter', 'snc-aliases', 'snc-rules'].forEach(id =>
    $(id).addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(compare, 250); }));

  $('snc-csv').addEventListener('click', () => {
    const docs = state.cmpDocs || [];
    const q = s => `"${String(s).replace(/"/g, '""')}"`;
    const lines = [['Status', 'Source', 'Item', ...docs.map(d => d.name)].map(q).join(',')];
    for (const r of state.rows) lines.push([LABEL[r.status], r.src, r.label, ...r.cells.map(c => c.join('; '))].map(q).join(','));
    const blob = new Blob(['\ufeff' + lines.join('\r\n')], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `serial-crosscheck-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  });

  compare();
})();
