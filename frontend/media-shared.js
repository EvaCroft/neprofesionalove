/* ============================================================
   media-shared.js — sdílená logika pro vykreslování náhledů médií
   (foto/video/audio) z modulu Galerie médií (`MediaAsset`/`/media`).

   Používá: frontend/layout-media-galerie.html, tab "Moje média" v
   layout-user-profil.html, a posts-shared.js (příloha u příspěvku na Zdi).

   Cíl: JEDNO místo, které umí vzít asset (nebo jen media_id) a vyrenderovat
   z něj skutečný <img>/<video>/<audio> náhled - viz DEVLOG v22-BUG-01/02
   (dřív každá stránka měla vlastní, mírně jinou implementaci, což vedlo
   k tomu, že se stejná chyba (dekorativní gradient místo reálné fotky)
   musela opravovat na 3 různých místech místo jednoho).

   Container, do kterého se `thumbHTML()` vkládá, MUSÍ mít `position:relative`
   (nebo `absolute`/`fixed`) a `overflow:hidden` - náhled se vykresluje jako
   `position:absolute; inset:0`, aby respektoval libovolný tvar/velikost
   rodiče (čtvercová dlaždice, 16:9 post, kulatý avatar apod.).
============================================================ */
(function (global) {
  const PLAY_ICON_SVG = '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';
  const AUDIO_ICON_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V6l10-2v12"/><circle cx="6" cy="18" r="3"/><circle cx="16" cy="16" r="3"/></svg>';

  const _assetCache = {}; // media_id -> asset (sdílená napříč všemi stránkami, co soubor includují)

  function escapeAttr(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
  }

  /** Načte MediaAsset podle id (GET /media/{id}), s jednoduchou in-memory cache. */
  async function fetchAsset(mediaId, authHeaders) {
    if (_assetCache[mediaId]) return _assetCache[mediaId];
    try {
      const res = await fetch('/media/' + mediaId, { headers: authHeaders });
      if (!res.ok) return null;
      const data = await res.json();
      _assetCache[mediaId] = data;
      return data;
    } catch (e) {
      return null;
    }
  }

  /** Vrátí HTML náhledu pro už načtený asset - foto/video/audio, vždy `.media-shared-thumb`. */
  function thumbHTML(asset) {
    if (!asset) return '';
    if (asset.media_type === 'photo') {
      return `<img class="media-shared-thumb" loading="lazy" alt="${escapeAttr(asset.original_filename)}" src="${asset.url}" onerror="this.remove()">`;
    }
    if (asset.media_type === 'video' || asset.media_type === 'reel') {
      return `<video class="media-shared-thumb" src="${asset.url}" muted preload="metadata" playsinline></video><div class="media-shared-play">${PLAY_ICON_SVG}</div>`;
    }
    if (asset.media_type === 'audio') {
      return `<div class="media-shared-audio">${AUDIO_ICON_SVG}</div>`;
    }
    return '';
  }

  /**
   * Načte asset podle media_id a vloží jeho náhled do containeru.
   * `container` musí mít position:relative+overflow:hidden (viz hlavička souboru).
   * opts: { clickable=true (klik otevře originál v novém panelu) }
   * Vrací načtený asset (nebo null, pokud selhalo/nemá uživatel přístup).
   */
  async function renderInto(container, mediaId, authHeaders, opts) {
    opts = opts || {};
    const asset = await fetchAsset(mediaId, authHeaders);
    if (!asset) return null;
    container.innerHTML = thumbHTML(asset);
    if (opts.clickable !== false) {
      container.style.cursor = 'pointer';
      container.onclick = () => window.open(asset.url, '_blank', 'noopener');
    }
    return asset;
  }

  // Sdílené CSS se vkládá jednou při prvním načtení skriptu na stránce -
  // nezáleží, kolik stránek soubor includuje, pravidlo je vždy jen jedno
  // a stejné (viz v22-BUG-02: dřív snadno vzniklo zúžení selektoru jen
  // pro jednu z variant zobrazení).
  if (typeof document !== 'undefined' && !document.getElementById('media-shared-style')) {
    const style = document.createElement('style');
    style.id = 'media-shared-style';
    style.textContent = `
      .media-shared-thumb { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; display:block; z-index:0; }
      .media-shared-play { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; background:rgba(0,0,0,.18); pointer-events:none; }
      .media-shared-play svg { width:34px; height:34px; fill:#fff; opacity:.92; filter:drop-shadow(0 2px 6px rgba(0,0,0,.35)); }
      .media-shared-audio { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; background:rgba(0,0,0,.25); }
      .media-shared-audio svg { width:28px; height:28px; stroke:rgba(255,255,255,.85); }
    `;
    document.head.appendChild(style);
  }

  /** Vloží celý seznam už načtených assetů do cache (vyhne se zbytečnému refetchi). */
  function primeCache(assets) {
    (assets || []).forEach(a => { if (a && a.id != null) _assetCache[a.id] = a; });
  }

  /* ============================================================
     Sdílený prohlížeč médií (lightbox) — MediaShared.openViewer()

     Jedno místo pro otevírání/procházení/akce nad médiem, používané
     Galerií médií, Zdí (i tabem Zeď na profilu) a sekcí Moje média na
     profilu. Viz DEVLOG #042 — dřív měla každá stránka vlastní lightbox
     (Galerie: `#lightbox`+`_renderLightboxAsset`, Moje média:
     `#media-lightbox`+`openMediaLightbox`, Zeď: žádný, jen otevření
     originálu v novém panelu) — sjednoceno stejně, jako se to už udělalo
     pro náhledy dlaždic (`thumbHTML`) a příspěvky (`posts-shared.js`).

     Funkce, které zatím nemají backend (komentáře, To se mi líbí, poslání
     zprávou z prohlížeče, zařazení do galerie/alba, tagování uživatelů),
     mají tlačítko viditelné, ale neaktivní — klik ukáže malý dialog
     "zatím nedostupná funkce" místo tichého no-opu nebo chybějící ikony.
  ============================================================ */

  const ICONS = {
    close: '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg>',
    prev: '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>',
    next: '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>',
    download: '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12m0 0l-4-4m4 4l4-4M4 19h16"/></svg>',
    share: '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 10.5l6.8-3.9M8.6 13.5l6.8 3.9"/></svg>',
    message: '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 01-2 2H8l-5 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>',
    heart: '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.6l-1-1a5.5 5.5 0 00-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 000-7.8z"/></svg>',
    comment: '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/></svg>',
    album: '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/></svg>',
    tag: '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7"/></svg>',
    trash: '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2m2 0v14a2 2 0 01-2 2H8a2 2 0 01-2-2V6h12z"/></svg>',
  };

  const _authorCache = {};
  async function _authorName(userId, authHeaders) {
    if (_authorCache[userId]) return _authorCache[userId];
    try {
      const res = await fetch('/profile/' + userId, { headers: authHeaders });
      if (res.ok) {
        const p = await res.json();
        _authorCache[userId] = p.display_name || ('Uživatel #' + userId);
        return _authorCache[userId];
      }
    } catch (e) {}
    return 'Uživatel #' + userId;
  }

  function _fmtTime(iso) {
    const d = new Date(iso);
    return d.toLocaleDateString('cs-CZ', { day: 'numeric', month: 'short', year: 'numeric' }) + ' · ' +
      d.toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit' });
  }

  let _v = null; // reference na DOM elementy prohlížeče, vytvoří se lazy při prvním otevření
  let _ids = [];
  let _index = -1;
  let _cfg = {};

  function _ensureViewerDom() {
    if (_v) return _v;

    if (!document.getElementById('media-shared-viewer-style')) {
      const style = document.createElement('style');
      style.id = 'media-shared-viewer-style';
      style.textContent = `
        .msv-overlay { position:fixed; inset:0; background:rgba(0,0,0,.82); z-index:200; display:none; align-items:center; justify-content:center; padding:28px; font-family:var(--font-active,-apple-system,sans-serif); }
        .msv-overlay.open { display:flex; }
        .msv-card { width:100%; max-width:680px; max-height:92vh; display:flex; flex-direction:column; }
        .msv-stage { width:100%; aspect-ratio:4/3; border-radius:var(--radius,20px); background:linear-gradient(135deg,var(--accent,#635BFF),var(--accent-b,#FF6FB8)); margin-bottom:14px; position:relative; overflow:hidden; display:flex; align-items:center; justify-content:center; }
        .msv-stage img, .msv-stage video { width:100%; height:100%; object-fit:contain; background:#000; }
        .msv-stage audio { width:88%; }
        .msv-close, .msv-nav { position:absolute; border:none; border-radius:50%; background:rgba(255,255,255,.14); display:flex; align-items:center; justify-content:center; cursor:pointer; transition:background .15s; }
        .msv-close:hover, .msv-nav:hover { background:rgba(255,255,255,.26); }
        .msv-close { top:-46px; right:0; width:38px; height:38px; }
        .msv-close svg { width:16px; height:16px; stroke:#fff; }
        .msv-nav { top:50%; transform:translateY(-50%); width:44px; height:44px; }
        .msv-nav svg { width:20px; height:20px; stroke:#fff; }
        .msv-nav:disabled { opacity:.25; cursor:default; }
        .msv-nav:disabled:hover { background:rgba(255,255,255,.14); }
        .msv-prev { left:-56px; } .msv-next { right:-56px; }
        @media (max-width:760px) { .msv-prev { left:6px; } .msv-next { right:6px; } .msv-close { top:6px; right:6px; background:rgba(0,0,0,.35); } }
        .msv-meta { display:flex; align-items:center; justify-content:space-between; gap:10px; color:#fff; margin-bottom:12px; }
        .msv-meta-left b { font-size:.92rem; display:block; }
        .msv-meta-left span { font-size:.74rem; opacity:.68; }
        .msv-actions { display:flex; flex-wrap:wrap; gap:8px; background:rgba(255,255,255,.08); border:.5px solid rgba(255,255,255,.14); border-radius:100px; padding:8px; }
        .msv-action { display:flex; align-items:center; gap:6px; border:none; background:transparent; color:#fff; font-size:.74rem; font-weight:500; font-family:inherit; border-radius:100px; padding:8px 12px; cursor:pointer; transition:background .15s; white-space:nowrap; }
        .msv-action:hover { background:rgba(255,255,255,.16); }
        .msv-action svg { width:16px; height:16px; stroke:#fff; fill:none; flex-shrink:0; }
        .msv-action.msv-soon { opacity:.5; }
        .msv-action.msv-danger { color:#FF6B6B; }
        .msv-action.msv-danger svg { stroke:#FF6B6B; }
        .msv-action.msv-danger:hover { background:rgba(255,59,48,.16); }
        .msv-soon-dialog { position:fixed; left:50%; bottom:38px; transform:translateX(-50%) translateY(8px); background:var(--surface-solid,#1C1C1E); color:var(--text-1,#fff); border:.5px solid var(--hairline,rgba(255,255,255,.14)); box-shadow:var(--shadow,0 20px 50px rgba(0,0,0,.4)); border-radius:14px; padding:12px 18px; font-size:.82rem; z-index:220; opacity:0; pointer-events:none; transition:opacity .18s, transform .18s; max-width:88vw; text-align:center; }
        .msv-soon-dialog.open { opacity:1; transform:translateX(-50%) translateY(0); pointer-events:auto; }
      `;
      document.head.appendChild(style);
    }

    const overlay = document.createElement('div');
    overlay.className = 'msv-overlay';
    overlay.id = 'media-shared-viewer';
    overlay.innerHTML = `
      <div class="msv-card">
        <button class="msv-close" id="msv-close" aria-label="Zavřít">${ICONS.close}</button>
        <button class="msv-nav msv-prev" id="msv-prev" aria-label="Předchozí">${ICONS.prev}</button>
        <button class="msv-nav msv-next" id="msv-next" aria-label="Další">${ICONS.next}</button>
        <div class="msv-stage" id="msv-stage"></div>
        <div class="msv-meta">
          <div class="msv-meta-left"><b id="msv-author">—</b><span id="msv-meta-text">—</span></div>
        </div>
        <div class="msv-actions" id="msv-actions"></div>
      </div>
      <div class="msv-soon-dialog" id="msv-soon-dialog"></div>
    `;
    document.body.appendChild(overlay);

    overlay.querySelector('#msv-close').onclick = closeViewer;
    overlay.querySelector('#msv-prev').onclick = _prev;
    overlay.querySelector('#msv-next').onclick = _next;
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeViewer(); });

    document.addEventListener('keydown', (e) => {
      if (!overlay.classList.contains('open')) return;
      if (e.key === 'ArrowLeft') _prev();
      else if (e.key === 'ArrowRight') _next();
      else if (e.key === 'Escape') closeViewer();
    });

    _v = {
      overlay,
      stage: overlay.querySelector('#msv-stage'),
      author: overlay.querySelector('#msv-author'),
      metaText: overlay.querySelector('#msv-meta-text'),
      actions: overlay.querySelector('#msv-actions'),
      prevBtn: overlay.querySelector('#msv-prev'),
      nextBtn: overlay.querySelector('#msv-next'),
      soonDialog: overlay.querySelector('#msv-soon-dialog'),
    };
    return _v;
  }

  let _soonTimer = null;
  function _notAvailable(label) {
    const v = _ensureViewerDom();
    v.soonDialog.textContent = (label ? label + ' — ' : '') + 'tato funkce zatím není dostupná.';
    v.soonDialog.classList.add('open');
    clearTimeout(_soonTimer);
    _soonTimer = setTimeout(() => v.soonDialog.classList.remove('open'), 2600);
  }

  function _actionBtn(icon, label, opts) {
    opts = opts || {};
    const cls = ['msv-action'];
    if (opts.soon) cls.push('msv-soon');
    if (opts.danger) cls.push('msv-danger');
    return `<button class="${cls.join(' ')}" type="button" data-msv-action="${escapeAttr(opts.key || label)}">${icon}<span>${label}</span></button>`;
  }

  async function _download(asset) {
    try {
      const res = await fetch(asset.url);
      const blob = await res.blob();
      const objUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objUrl;
      a.download = asset.original_filename || ('media-' + asset.id);
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(objUrl), 4000);
    } catch (e) {
      window.open(asset.url, '_blank', 'noopener');
    }
  }

  async function _share(asset) {
    const absUrl = new URL(asset.url, window.location.href).href;
    if (navigator.share) {
      try { await navigator.share({ title: asset.original_filename || 'Médium', url: absUrl }); return; } catch (e) { return; }
    }
    try {
      await navigator.clipboard.writeText(absUrl);
      _toast('Odkaz na médium zkopírován do schránky.');
    } catch (e) {
      window.prompt('Zkopíruj odkaz na médium:', absUrl);
    }
  }

  function _toast(text) {
    const v = _ensureViewerDom();
    v.soonDialog.textContent = text;
    v.soonDialog.classList.add('open');
    clearTimeout(_soonTimer);
    _soonTimer = setTimeout(() => v.soonDialog.classList.remove('open'), 2600);
  }

  async function _renderCurrent() {
    const v = _ensureViewerDom();
    const id = _ids[_index];
    v.stage.innerHTML = '';
    v.author.textContent = '…';
    v.metaText.textContent = '—';

    const asset = await fetchAsset(id, _cfg.authHeaders);
    if (!asset || _ids[_index] !== id) return; // mezitím se přepnulo jinam / smazalo

    if (asset.media_type === 'photo') {
      v.stage.innerHTML = `<img src="${asset.url}" alt="${escapeAttr(asset.original_filename)}">`;
    } else if (asset.media_type === 'video' || asset.media_type === 'reel') {
      v.stage.innerHTML = `<video src="${asset.url}" controls autoplay playsinline></video>`;
    } else if (asset.media_type === 'audio') {
      v.stage.innerHTML = `<audio src="${asset.url}" controls></audio>`;
    }

    v.metaText.textContent = (asset.original_filename || '') + ' · ' + _fmtTime(asset.created_at);
    _authorName(asset.owner_id, _cfg.authHeaders).then(name => {
      if (_ids[_index] === id) v.author.textContent = name;
    });

    const canManage = asset.direction === 'uploaded' || asset.direction === 'sent';
    v.actions.innerHTML = [
      _actionBtn(ICONS.download, 'Stáhnout', { key: 'download' }),
      _actionBtn(ICONS.share, 'Sdílet', { key: 'share' }),
      _actionBtn(ICONS.message, 'Poslat zprávou', { key: 'message', soon: true }),
      _actionBtn(ICONS.heart, 'To se mi líbí', { key: 'like', soon: true }),
      _actionBtn(ICONS.comment, 'Komentáře', { key: 'comment', soon: true }),
      _actionBtn(ICONS.album, 'Zařadit do galerie', { key: 'album', soon: true }),
      _actionBtn(ICONS.tag, 'Označit uživatele', { key: 'tag', soon: true }),
      canManage ? _actionBtn(ICONS.trash, 'Smazat', { key: 'delete', danger: true }) : '',
    ].join('');

    v.actions.querySelectorAll('[data-msv-action]').forEach(btn => {
      const key = btn.getAttribute('data-msv-action');
      btn.onclick = () => {
        if (key === 'download') return _download(asset);
        if (key === 'share') return _share(asset);
        if (key === 'delete') return _deleteCurrent(asset);
        _notAvailable(btn.textContent.trim());
      };
    });

    v.prevBtn.disabled = _index <= 0;
    v.nextBtn.disabled = _index < 0 || _index >= _ids.length - 1;
  }

  async function _deleteCurrent(asset) {
    if (!window.confirm('Opravdu smazat toto médium? Tuto akci nejde vzít zpět.')) return;
    try {
      const res = await fetch('/media/' + asset.id, { method: 'DELETE', headers: _cfg.authHeaders });
      if (!res.ok && res.status !== 204) {
        window.alert('Smazání se nezdařilo.');
        return;
      }
    } catch (e) {
      window.alert('Nepodařilo se spojit se serverem. Zkus to znovu.');
      return;
    }
    delete _assetCache[asset.id];
    const deletedIndex = _index;
    _ids = _ids.filter(id => id !== asset.id);
    if (_cfg.onDelete) _cfg.onDelete(asset.id);
    if (!_ids.length) { closeViewer(); return; }
    _index = Math.min(deletedIndex, _ids.length - 1);
    _renderCurrent();
  }

  function _prev() { if (_index > 0) { _index--; _renderCurrent(); } }
  function _next() { if (_index >= 0 && _index < _ids.length - 1) { _index++; _renderCurrent(); } }

  /**
   * Otevře sdílený prohlížeč médií.
   * @param {number[]} ids - seznam id médií pro procházení šipkami (pořadí = pořadí procházení)
   * @param {number} startId - id média, které se má zobrazit jako první
   * @param {object} cfg - { authHeaders, onDelete(mediaId) - zavolá se po úspěšném smazání, ať volající stránka aktualizuje svůj seznam/grid }
   */
  function openViewer(ids, startId, cfg) {
    const v = _ensureViewerDom();
    _ids = (ids || []).filter((id, i, arr) => id != null && arr.indexOf(id) === i);
    _index = _ids.indexOf(startId);
    if (_index === -1 && _ids.length) _index = 0;
    if (_index === -1) { _ids = [startId]; _index = 0; }
    _cfg = cfg || {};
    v.overlay.classList.add('open');
    _renderCurrent();
  }

  function closeViewer() {
    if (!_v) return;
    _v.overlay.classList.remove('open');
    _v.stage.innerHTML = '';
    _v.soonDialog.classList.remove('open');
    _ids = []; _index = -1; _cfg = {};
  }

  global.MediaShared = { fetchAsset, thumbHTML, renderInto, primeCache, openViewer, closeViewer };
})(window);
